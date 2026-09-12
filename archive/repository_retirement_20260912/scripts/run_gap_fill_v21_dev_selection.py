#!/usr/bin/env python3
"""Execute the frozen V21 DEV expanding-OOF P2 candidate ladder.

This runner is authorized only after cloud acceptance of V21-SA1 and V21-SA2.
It opens CSI300/CSI500 OHLC only inside the frozen 2015-01-01..2018-12-31
DEV block, re-verifies the admitted session-complete-239 metadata inventory,
fits the same-era geometry control in expanding natural-year folds, then tests
exactly the frozen P2 candidate ladder in complexity order and stops at the
first eligible candidate. Audit A/B, the external reserve, 2014Q4 supporting
crosscheck and CSI1000 post-2026-08-21 outcomes remain sealed.

Only compact aggregate receipts and an optional selected full-DEV parameter
freeze are written to the repository. No raw or row-level market data is saved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_gap_fill_v2_target_ledger as targetmod
import evaluate_local_gap_fill_v2_2026_repeat as evalbase
import v21_evaluation_kernel as ev
import v21_p2_overlay as p2
import v21_session_complete_239_gate as gate

AUTH = ROOT / "docs/governance/cloud_session_20260908_gap_fill_v21_dev_open_authorization_v1.json"
FAMILY = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_candidate_family_v1.json"
SELECTION_PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_dev_selection_protocol_v1.json"
STATE = ROOT / "docs/governance/gap_fill_v21_state_v1.json"
OUT = ROOT / "docs/research/local_gap_fill_v21_dev_selection_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_gap_fill_v21_dev_data_usage_v1.json"
PARAM_OUT = ROOT / "docs/governance/local_gap_fill_v21_dev_parameter_freeze_v1.json"

DEV_START = "2015-01-01"
DEV_END = "2018-12-31"
DEV_VALIDATION_YEARS = (2016, 2017, 2018)
EXPECTED_PARENT_SHA = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
SYMBOLS = {"CSI300": "000300.SH", "CSI500": "000905.SH"}
FEATURES = ["abs_gap", "abs_gap_over_rvol20"]
COHORTS = {"all_nonzero_gap": 0.0, "abs_gap_gt_10bp": 0.001, "abs_gap_gt_30bp": 0.003}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def command_string() -> str:
    return " ".join(sys.argv)


def require_source(raw: str | None) -> Path:
    value = raw or os.environ.get("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE")
    if not value:
        raise RuntimeError("--source or OVERNIGHT_HISTORICAL_INDEX_1M_LAKE is required")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"V21 DEV OHLC source does not exist: {path}")
    return path


def validate_authority(parent_sha: str) -> tuple[dict, dict, dict, dict]:
    auth = load_json(AUTH)
    family = load_json(FAMILY)
    protocol = load_json(SELECTION_PROTOCOL)
    state = load_json(STATE)
    if auth["decision"] != "V21_DEV_open_authorized_after_SA1_SA2_cloud_review":
        raise RuntimeError("V21 DEV-open authorization identity drifted")
    if auth["source_identity"]["parent_he00_v8_sha256"] != EXPECTED_PARENT_SHA or parent_sha != EXPECTED_PARENT_SHA:
        raise RuntimeError("parent HE-00 v8 identity mismatch")
    if auth["V21_DEV_outcomes_open_authorized"] is not True:
        raise RuntimeError("authorization does not open V21 DEV")
    if auth["successor_model_fit_authorized"] is not True or auth["successor_model_selection_authorized"] is not True:
        raise RuntimeError("authorization does not permit frozen DEV fit/selection")
    if auth["Audit_A_outcomes_open_authorized"] is not False or auth["Audit_B_outcomes_open_authorized"] is not False:
        raise RuntimeError("authorization unexpectedly opens future audit")
    if state.get("DEV_open_authorization") != str(AUTH.relative_to(ROOT)):
        raise RuntimeError("repository state is not bound to the V21 DEV-open authorization")
    if state.get("successor_model_fit_authorized") is not True or state.get("successor_model_selection_authorized") is not True:
        raise RuntimeError("repository state still denies DEV fit/selection")
    if state["sealed"]["V21_DEV_outcomes"] is not False:
        raise RuntimeError("repository state still seals V21 DEV")
    for key in ["V21_AUDIT_A_outcomes", "V21_AUDIT_B_outcomes", "V21_EXTERNAL_RESERVE_outcomes", "CSI1000_2026Q4_true_fresh"]:
        if state["sealed"][key] is not True:
            raise RuntimeError(f"repository state unexpectedly unsealed {key}")
    if family["V21_DEV_outcomes_open_authorized"] is not False:
        raise RuntimeError("frozen family was rewritten after DEV open")
    if protocol["stage"] != "V21_DEV_selection_preregistered_but_unopened":
        raise RuntimeError("frozen DEV selection protocol stage drifted")
    if tuple(protocol["candidate_execution"]["order"]) != p2.CANDIDATE_LADDER:
        raise RuntimeError("candidate ladder drifted")
    if protocol["candidate_execution"]["stop_at_first_eligible"] is not True:
        raise RuntimeError("candidate ladder no longer stops at first eligible")
    return auth, family, protocol, state


def read_metadata(source: Path) -> pd.DataFrame:
    frame = pd.read_parquet(source, columns=["symbol", "trading_day", "timestamp"])
    if frame.empty:
        raise RuntimeError("V21 DEV source metadata is empty")
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame = frame.loc[(frame["trading_day"] >= DEV_START) & (frame["trading_day"] <= DEV_END)].copy()
    if frame.empty:
        raise RuntimeError("V21 DEV source has no rows in frozen window")
    unexpected = sorted(set(frame["symbol"]) - set(SYMBOLS.values()))
    if unexpected:
        raise RuntimeError(f"unexpected symbol in V21 DEV source: {unexpected}")
    return frame.sort_values(["symbol", "trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def metadata_inventory(frame: pd.DataFrame) -> dict:
    by_symbol: dict[str, dict] = {}
    for index_name, symbol in SYMBOLS.items():
        part = frame.loc[frame["symbol"].eq(symbol)].copy()
        if part.empty:
            raise RuntimeError(f"missing V21 DEV symbol {symbol}")
        complete = 0
        incomplete = 0
        reasons: Counter[str] = Counter()
        optional = 0
        missing_rows = 0
        for _, day in part.groupby("trading_day", sort=True):
            result = gate.evaluate_session_complete_239(day["timestamp"].tolist())
            reasons[result.reason] += 1
            optional += int(result.optional_1459_present)
            missing_rows += len(result.missing_required_clocks)
            if result.accepted:
                complete += 1
            else:
                incomplete += 1
        by_symbol[symbol] = {
            "index": index_name,
            "observed_days": int(part["trading_day"].nunique()),
            "session_complete_days": int(complete),
            "incomplete_days": int(incomplete),
            "optional_1459_present_days": int(optional),
            "missing_required_clock_rows": int(missing_rows),
            "reason_counts": dict(sorted(reasons.items())),
            "min_day": str(part["trading_day"].min()),
            "max_day": str(part["trading_day"].max()),
        }
    return {"rows": int(len(frame)), "by_symbol": by_symbol}


def verify_metadata_preflight(source: Path, auth: dict) -> dict:
    frame = read_metadata(source)
    audit = metadata_inventory(frame)
    expected = auth["DEV_metadata_admission"]["per_symbol"]
    for symbol in SYMBOLS.values():
        got = audit["by_symbol"][symbol]
        exp = expected[symbol]
        for got_key, exp_key in [
            ("observed_days", "observed_days"),
            ("session_complete_days", "session_complete_days"),
            ("incomplete_days", "incomplete_days"),
        ]:
            if int(got[got_key]) != int(exp[exp_key]):
                raise RuntimeError(
                    f"DEV metadata preflight mismatch {symbol} {got_key}: {got[got_key]} != {exp[exp_key]}"
                )
        if got["min_day"] < DEV_START or got["max_day"] > DEV_END:
            raise RuntimeError(f"DEV metadata preflight crossed frozen window for {symbol}")
    return audit


def read_symbol_ohlc(source: Path, symbol: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        source,
        filters=[("symbol", "==", symbol), ("trading_day", ">=", DEV_START), ("trading_day", "<=", DEV_END)],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError(f"no V21 DEV OHLC rows for {symbol}")
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    if set(frame["symbol"]) != {symbol}:
        raise RuntimeError(f"unexpected symbol while reading {symbol}")
    if frame["trading_day"].min() < DEV_START or frame["trading_day"].max() > DEV_END:
        raise RuntimeError(f"{symbol} OHLC crossed V21 DEV boundary")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def _one_numeric_at_clock(day: pd.DataFrame, clock: str, column: str) -> float:
    part = day.loc[day["clock"].eq(clock), column]
    if len(part) != 1:
        return float("nan")
    value = pd.to_numeric(part, errors="coerce").iloc[0]
    return float(value) if np.isfinite(value) else float("nan")


def target_clocks_for_day(optional_1459_present: bool) -> dict[str, list[str]]:
    base = targetmod.expected_clocks()
    eod = list(gate.legacy_expected_240_clocks()) if optional_1459_present else list(gate.required_session_complete_239_clocks())
    return {"15m": list(base["15m"]), "60m": list(base["60m"]), "eod": eod}


def build_index_frame(minutes: pd.DataFrame, index_name: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    symbol = SYMBOLS[index_name]
    groups = {str(day): g.copy() for day, g in minutes.groupby("trading_day", sort=True)}
    days = sorted(groups)
    daily_rows: list[dict] = []
    gate_results: dict[str, gate.SessionGateResult] = {}
    for day in days:
        g = groups[day]
        result = gate.evaluate_session_complete_239(g["timestamp"].tolist())
        gate_results[day] = result
        daily_rows.append({
            "trading_day": day,
            "open_0931": _one_numeric_at_clock(g, "09:31", "open"),
            "close_1500": _one_numeric_at_clock(g, "15:00", "close"),
            "session_complete_239": bool(result.accepted),
            "optional_1459_present": bool(result.optional_1459_present),
            "gate_reason": result.reason,
        })
    daily = pd.DataFrame(daily_rows).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    daily["prev_close"] = pd.to_numeric(daily["close_1500"], errors="coerce").shift(1)
    close = pd.to_numeric(daily["close_1500"], errors="coerce")
    daily["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    daily["gap"] = pd.to_numeric(daily["open_0931"], errors="coerce") / pd.to_numeric(daily["prev_close"], errors="coerce") - 1.0
    daily["abs_gap"] = daily["gap"].abs()
    daily["abs_gap_over_rvol20"] = daily["abs_gap"] / pd.to_numeric(daily["rvol20"], errors="coerce")

    rows: list[dict] = []
    invalid: Counter[str] = Counter()
    for _, row in daily.iterrows():
        day = str(row["trading_day"])
        result = gate_results[day]
        if not result.accepted:
            invalid[result.reason] += 1
            continue
        numeric = [row["open_0931"], row["prev_close"], row["gap"], row["rvol20"], row["abs_gap_over_rvol20"]]
        if not all(np.isfinite(float(v)) for v in numeric) or float(row["rvol20"]) <= 0.0:
            invalid["incomplete_gap_or_rvol20"] += 1
            continue
        day_row = pd.Series({
            "trading_day": day,
            "open_0931": float(row["open_0931"]),
            "prev_close": float(row["prev_close"]),
            "overnight_gap": float(row["gap"]),
        })
        clocks = target_clocks_for_day(bool(result.optional_1459_present))
        target = targetmod.compute_day(day_row, groups[day], clocks)
        if target is None or not bool(target.get("target_valid", False)):
            invalid["target_invalid" if target is None else str(target.get("invalid_reason"))] += 1
            continue
        target["rvol20"] = float(row["rvol20"])
        target["abs_gap_over_rvol20"] = float(row["abs_gap_over_rvol20"])
        target["optional_1459_present"] = bool(result.optional_1459_present)
        rows.append(target)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"{index_name} has no V21 DEV target-valid rows")
    frame["year"] = frame["trading_day"].str.slice(0, 4).astype(int)
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if int((frame["fill_15m"].astype(bool) & ~frame["fill_60m"].astype(bool)).sum()) != 0:
        raise RuntimeError(f"{index_name} fill15/fill60 nesting violation")
    if int((frame["fill_60m"].astype(bool) & ~frame["fill_eod"].astype(bool)).sum()) != 0:
        raise RuntimeError(f"{index_name} fill60/fillEOD nesting violation")
    audit = {
        "symbol": symbol,
        "minute_rows_loaded": int(len(minutes)),
        "trading_days_loaded": int(len(days)),
        "session_complete_days": int(sum(x.accepted for x in gate_results.values())),
        "target_valid_rows": int(len(frame)),
        "invalid_reason_counts": dict(sorted(invalid.items())),
        "target_min_day": str(frame["trading_day"].min()),
        "target_max_day": str(frame["trading_day"].max()),
    }
    return frame, daily, audit


def attach_p2(index_frames: dict[str, pd.DataFrame], daily_frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for index_name, other_name in [("CSI300", "CSI500"), ("CSI500", "CSI300")]:
        frame = index_frames[index_name].copy()
        other = daily_frames[other_name][["trading_day", "gap"]].rename(columns={"gap": "other_gap"})
        frame = frame.merge(other, how="left", on="trading_day", validate="one_to_one")
        frame["p2_raw"] = np.sign(frame["gap"].to_numpy(dtype=float)) * (
            frame["gap"].to_numpy(dtype=float) - pd.to_numeric(frame["other_gap"], errors="coerce").to_numpy(dtype=float)
        ) / frame["rvol20"].to_numpy(dtype=float)
        frame["p2_available"] = np.isfinite(frame["p2_raw"].to_numpy(dtype=float))
        out[index_name] = frame
    return out


def make_pipeline() -> Pipeline:
    return Pipeline([
        ("sc", StandardScaler(with_mean=True, with_std=True)),
        ("model", LogisticRegression(
            C=1.0,
            penalty="l2",
            solver="lbfgs",
            class_weight=None,
            fit_intercept=True,
            max_iter=1000,
        )),
    ])


def stage_risk(frame: pd.DataFrame, stage: str) -> tuple[np.ndarray, np.ndarray]:
    if stage == "15m":
        risk = np.ones(len(frame), dtype=bool)
        target = frame["fill_15m"].to_numpy(dtype=int)
    elif stage == "60m":
        risk = ~frame["fill_15m"].to_numpy(dtype=bool)
        target = frame["fill_60m"].to_numpy(dtype=int)
    elif stage == "eod":
        risk = ~frame["fill_60m"].to_numpy(dtype=bool)
        target = frame["fill_eod"].to_numpy(dtype=int)
    else:
        raise ValueError(stage)
    return risk, target


def _serialize_pipeline(pipe: Pipeline, stage: str, train: pd.DataFrame) -> dict:
    sc = pipe.named_steps["sc"]
    model = pipe.named_steps["model"]
    return {
        "stage": stage,
        "n_training_sign_rows": int(len(train)),
        "training_min_day": str(train["trading_day"].min()),
        "training_max_day": str(train["trading_day"].max()),
        "feature_names": FEATURES,
        "scaler": {
            "mean": [float(v) for v in np.asarray(sc.mean_, dtype=float)],
            "scale": [float(v) for v in np.asarray(sc.scale_, dtype=float)],
            "var": [float(v) for v in np.asarray(sc.var_, dtype=float)],
        },
        "logistic": {
            "coef": [float(v) for v in np.asarray(model.coef_[0], dtype=float)],
            "intercept": float(np.asarray(model.intercept_, dtype=float)[0]),
            "classes": [int(v) for v in np.asarray(model.classes_, dtype=int)],
            "n_iter": [int(v) for v in np.asarray(model.n_iter_, dtype=int)],
        },
    }


def fit_geometry_stage(frame: pd.DataFrame, stage: str) -> tuple[Pipeline, dict]:
    risk, target = stage_risk(frame, stage)
    part = frame.loc[risk].copy()
    y = target[risk]
    if len(part) == 0 or np.unique(y).size != 2:
        raise RuntimeError(f"geometry {stage} risk set lacks both classes")
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise RuntimeError(f"geometry {stage} has nonfinite features")
    pipe = make_pipeline()
    pipe.fit(x, y)
    params = _serialize_pipeline(pipe, stage, part)
    params["n_train_risk"] = int(len(part))
    params["event_count"] = int(np.sum(y))
    params["event_rate"] = float(np.mean(y))
    return pipe, params


def predict_stage_hazards(pipes: dict[str, Pipeline], frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = frame[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise RuntimeError("geometry prediction received nonfinite feature")
    return (
        pipes["15m"].predict_proba(x)[:, 1],
        pipes["60m"].predict_proba(x)[:, 1],
        pipes["eod"].predict_proba(x)[:, 1],
    )


def empirical_hazards(train: pd.DataFrame) -> tuple[float, float, float]:
    values: list[float] = []
    for stage in ["15m", "60m", "eod"]:
        risk, target = stage_risk(train, stage)
        y = target[risk]
        if len(y) == 0:
            raise RuntimeError(f"empty empirical {stage} risk set")
        values.append(float(np.mean(y)))
    return values[0], values[1], values[2]


def constant_cumulative(hazards: tuple[float, float, float], n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    h15, h60, heod = hazards
    return p2.cumulative_probs(np.full(n, h15), np.full(n, h60), np.full(n, heod))


def fit_fold_base(frame: pd.DataFrame, validation_year: int, sign: str) -> dict:
    train = frame.loc[(frame["year"] < validation_year) & frame["gap_sign"].eq(sign)].copy()
    valid = frame.loc[(frame["year"] == validation_year) & frame["gap_sign"].eq(sign)].copy()
    if sign == "high":
        train = train.loc[train["p2_available"]].copy()
        valid = valid.loc[valid["p2_available"]].copy()
    if train.empty or valid.empty:
        raise RuntimeError(f"empty V21 fold {validation_year} {sign}")
    pipes: dict[str, Pipeline] = {}
    params: dict[str, dict] = {}
    for stage in ["15m", "60m", "eod"]:
        pipes[stage], params[stage] = fit_geometry_stage(train, stage)
    train_h = predict_stage_hazards(pipes, train)
    valid_h = predict_stage_hazards(pipes, valid)
    control = p2.cumulative_probs(*valid_h)
    benchmark = constant_cumulative(empirical_hazards(train), len(valid))
    scaler = None
    train_z = None
    valid_z = None
    if sign == "high":
        scaler = p2.fit_standardizer(train["p2_raw"].to_numpy(dtype=float))
        train_z = scaler.transform(train["p2_raw"].to_numpy(dtype=float))
        valid_z = scaler.transform(valid["p2_raw"].to_numpy(dtype=float))
    return {
        "validation_year": int(validation_year),
        "train": train.reset_index(drop=True),
        "valid": valid.reset_index(drop=True),
        "pipes": pipes,
        "geometry_params": params,
        "train_hazards": train_h,
        "valid_hazards": valid_h,
        "control_probs": control,
        "benchmark_probs": benchmark,
        "p2_scaler": scaler,
        "train_z": train_z,
        "valid_z": valid_z,
    }


def beta_cells(base: dict, stages: Iterable[str]) -> list[p2.OffsetCell]:
    train = base["train"]
    z = np.asarray(base["train_z"], dtype=float)
    h15, h60, _ = base["train_hazards"]
    out: list[p2.OffsetCell] = []
    for stage in stages:
        risk, target = stage_risk(train, stage)
        if stage == "15m":
            hazard = h15[risk]
        elif stage == "60m":
            hazard = h60[risk]
        else:
            raise ValueError("P2 beta may affect only 15m/60m")
        out.append(p2.OffsetCell(hazard, z[risk], target[risk]))
    return out


def fit_candidate_betas(candidate_id: str, bases: dict[str, dict]) -> dict:
    if candidate_id == "P2_XI_SHARED_1B":
        cells = beta_cells(bases["CSI300"], ["15m", "60m"]) + beta_cells(bases["CSI500"], ["15m", "60m"])
        fit = p2.fit_shared_beta(cells)
        if not fit["success"]:
            raise RuntimeError("shared cross-index beta optimizer failed")
        return {"shared": fit}
    if candidate_id == "P2_CSI500_SHARED_1B":
        fit = p2.fit_shared_beta(beta_cells(bases["CSI500"], ["15m", "60m"]))
        if not fit["success"]:
            raise RuntimeError("CSI500 shared beta optimizer failed")
        return {"shared": fit}
    if candidate_id == "P2_CSI500_STAGE_2B":
        fit15 = p2.fit_shared_beta(beta_cells(bases["CSI500"], ["15m"]))
        fit60 = p2.fit_shared_beta(beta_cells(bases["CSI500"], ["60m"]))
        if not fit15["success"] or not fit60["success"]:
            raise RuntimeError("CSI500 stage beta optimizer failed")
        return {"beta15": fit15, "beta60": fit60}
    raise ValueError(candidate_id)


def candidate_probs(candidate_id: str, index_name: str, base: dict, beta_fits: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    h15, h60, heod = base["valid_hazards"]
    z = np.asarray(base["valid_z"], dtype=float)
    affected = candidate_id == "P2_XI_SHARED_1B" or index_name == "CSI500"
    if not affected:
        return base["control_probs"]
    if candidate_id in {"P2_XI_SHARED_1B", "P2_CSI500_SHARED_1B"}:
        beta15 = beta60 = float(beta_fits["shared"]["beta"])
    elif candidate_id == "P2_CSI500_STAGE_2B":
        beta15 = float(beta_fits["beta15"]["beta"])
        beta60 = float(beta_fits["beta60"]["beta"])
    else:
        raise ValueError(candidate_id)
    cand_h15 = p2.apply_beta(h15, z, beta15)
    cand_h60 = p2.apply_beta(h60, z, beta60)
    return p2.cumulative_probs(cand_h15, cand_h60, heod)


def scored_frame(base: dict, candidate: tuple[np.ndarray, np.ndarray, np.ndarray]) -> pd.DataFrame:
    frame = base["valid"].copy().reset_index(drop=True)
    control = base["control_probs"]
    bench = base["benchmark_probs"]
    for prefix, probs in [("candidate", candidate), ("control", control), ("benchmark", bench)]:
        frame[f"{prefix}_p15"] = probs[0]
        frame[f"{prefix}_p60"] = probs[1]
        frame[f"{prefix}_peod"] = probs[2]
    return frame


def probability_tuple(frame: pd.DataFrame, prefix: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        frame[f"{prefix}_p15"].to_numpy(dtype=float),
        frame[f"{prefix}_p60"].to_numpy(dtype=float),
        frame[f"{prefix}_peod"].to_numpy(dtype=float),
    )


def descriptive_metrics(frame: pd.DataFrame, prefix: str) -> dict:
    out: dict[str, dict] = {}
    for cohort, threshold in COHORTS.items():
        part = frame if threshold == 0.0 else frame.loc[frame["abs_gap"] > threshold].copy()
        if part.empty:
            out[cohort] = {"n": 0}
            continue
        probs = probability_tuple(part, prefix)
        out[cohort] = evalbase.evaluate_cohort(part, probs, include_deciles=False)
    probs_all = probability_tuple(frame, prefix)
    out["monotonicity_violations"] = p2.monotonicity_violations(*probs_all)
    return out


def evaluate_candidate(candidate_id: str, high_bases: dict[tuple[str, int], dict]) -> dict:
    beta_history: dict[str, list[float]] = {}
    fold_records: list[dict] = []
    scored_by_index: dict[str, list[pd.DataFrame]] = {"CSI300": [], "CSI500": []}
    for year in DEV_VALIDATION_YEARS:
        bases = {name: high_bases[(name, year)] for name in SYMBOLS}
        fits = fit_candidate_betas(candidate_id, bases)
        for key, fit in fits.items():
            beta_history.setdefault(key, []).append(float(fit["beta"]))
        fold_info = {
            "validation_year": int(year),
            "betas": {k: {"beta": float(v["beta"]), "objective": float(v["objective"]), "success": bool(v["success"]), "n_cells": int(v["n_cells"])} for k, v in fits.items()},
            "by_index": {},
        }
        for index_name in SYMBOLS:
            base = bases[index_name]
            probs = candidate_probs(candidate_id, index_name, base, fits)
            scored = scored_frame(base, probs)
            scored_by_index[index_name].append(scored)
            fold_info["by_index"][index_name] = {
                "train_high_n": int(len(base["train"])),
                "validation_high_n": int(len(base["valid"])),
                "validation_gt10_n": int((base["valid"]["abs_gap"] > 0.001).sum()),
                "p2_scaler": {"mean": float(base["p2_scaler"].mean), "scale": float(base["p2_scaler"].scale)},
            }
        fold_records.append(fold_info)

    pooled = {name: pd.concat(parts, ignore_index=True).sort_values("trading_day").reset_index(drop=True) for name, parts in scored_by_index.items()}
    csi500 = pooled["CSI500"]
    eval_primary = ev.evaluate_dev_primary(
        y15=csi500["fill_15m"].to_numpy(dtype=int),
        y60=csi500["fill_60m"].to_numpy(dtype=int),
        abs_gap=csi500["abs_gap"].to_numpy(dtype=float),
        years=csi500["year"].to_numpy(dtype=int),
        candidate15=csi500["candidate_p15"].to_numpy(dtype=float),
        candidate60=csi500["candidate_p60"].to_numpy(dtype=float),
        control15=csi500["control_p15"].to_numpy(dtype=float),
        control60=csi500["control_p60"].to_numpy(dtype=float),
        benchmark15=csi500["benchmark_p15"].to_numpy(dtype=float),
        benchmark60=csi500["benchmark_p60"].to_numpy(dtype=float),
        beta_histories=beta_history,
        monotonicity_violations=p2.monotonicity_violations(
            csi500["candidate_p15"].to_numpy(dtype=float),
            csi500["candidate_p60"].to_numpy(dtype=float),
            csi500["candidate_peod"].to_numpy(dtype=float),
        ),
    )
    extra_gate = None
    eligible = bool(eval_primary["eligible"])
    if candidate_id == "P2_XI_SHARED_1B":
        csi300 = pooled["CSI300"]
        extra_gate = ev.evaluate_cross_index_shared_nonharm(
            y15=csi300["fill_15m"].to_numpy(dtype=int),
            y60=csi300["fill_60m"].to_numpy(dtype=int),
            abs_gap=csi300["abs_gap"].to_numpy(dtype=float),
            candidate15=csi300["candidate_p15"].to_numpy(dtype=float),
            candidate60=csi300["candidate_p60"].to_numpy(dtype=float),
            control15=csi300["control_p15"].to_numpy(dtype=float),
            control60=csi300["control_p60"].to_numpy(dtype=float),
        )
        eligible = eligible and bool(extra_gate["passed"])

    return {
        "candidate_id": candidate_id,
        "eligible": bool(eligible),
        "primary_evaluation": eval_primary,
        "candidate_specific_extra_gate": extra_gate,
        "beta_history": beta_history,
        "folds": fold_records,
        "descriptive_high": {
            name: {
                "candidate": descriptive_metrics(frame, "candidate"),
                "geometry_control": descriptive_metrics(frame, "control"),
                "empirical_benchmark": descriptive_metrics(frame, "benchmark"),
            }
            for name, frame in pooled.items()
        },
    }


def build_geometry_oof_descriptive(frames: dict[str, pd.DataFrame]) -> tuple[dict, dict[tuple[str, int], dict]]:
    high_bases: dict[tuple[str, int], dict] = {}
    result: dict[str, dict] = {}
    for index_name, frame in frames.items():
        result[index_name] = {"high": {}, "low": {}}
        for sign in ["high", "low"]:
            scored_parts: list[pd.DataFrame] = []
            fold_info: list[dict] = []
            for year in DEV_VALIDATION_YEARS:
                base = fit_fold_base(frame, year, sign)
                if sign == "high":
                    high_bases[(index_name, year)] = base
                scored = base["valid"].copy().reset_index(drop=True)
                for prefix, probs in [("control", base["control_probs"]), ("benchmark", base["benchmark_probs"])]:
                    scored[f"{prefix}_p15"] = probs[0]
                    scored[f"{prefix}_p60"] = probs[1]
                    scored[f"{prefix}_peod"] = probs[2]
                scored_parts.append(scored)
                fold_info.append({
                    "validation_year": int(year),
                    "train_n": int(len(base["train"])),
                    "validation_n": int(len(base["valid"])),
                    "validation_gt10_n": int((base["valid"]["abs_gap"] > 0.001).sum()),
                    "geometry_params": base["geometry_params"],
                })
            pooled = pd.concat(scored_parts, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
            result[index_name][sign] = {
                "folds": fold_info,
                "geometry_control": descriptive_metrics(pooled, "control"),
                "empirical_benchmark": descriptive_metrics(pooled, "benchmark"),
                "annual": {
                    str(year): {
                        "geometry_control": descriptive_metrics(pooled.loc[pooled["year"].eq(year)].copy(), "control"),
                        "empirical_benchmark": descriptive_metrics(pooled.loc[pooled["year"].eq(year)].copy(), "benchmark"),
                    }
                    for year in DEV_VALIDATION_YEARS
                },
            }
    return result, high_bases


def fit_full_geometry(frame: pd.DataFrame, sign: str) -> tuple[dict[str, Pipeline], dict]:
    part = frame.loc[frame["gap_sign"].eq(sign)].copy()
    if sign == "high":
        part = part.loc[part["p2_available"]].copy()
    if part.empty:
        raise RuntimeError(f"full DEV {sign} geometry frame is empty")
    pipes: dict[str, Pipeline] = {}
    params: dict[str, dict] = {}
    for stage in ["15m", "60m", "eod"]:
        pipes[stage], params[stage] = fit_geometry_stage(part, stage)
    return pipes, {"n_sign_rows": int(len(part)), "stages": params}


def fit_full_selected(candidate_id: str, frames: dict[str, pd.DataFrame], source_audit: dict, parent_sha: str) -> dict:
    geometry_params: dict[str, dict] = {}
    high_bases: dict[str, dict] = {}
    empirical: dict[str, dict] = {}
    for index_name, frame in frames.items():
        geometry_params[index_name] = {}
        empirical[index_name] = {}
        for sign in ["high", "low"]:
            pipes, params = fit_full_geometry(frame, sign)
            geometry_params[index_name][sign] = params
            part = frame.loc[frame["gap_sign"].eq(sign)].copy()
            if sign == "high":
                part = part.loc[part["p2_available"]].copy()
            empirical[index_name][sign] = {
                stage: rate for stage, rate in zip(["15m", "60m", "eod"], empirical_hazards(part))
            }
            if sign == "high":
                scaler = p2.fit_standardizer(part["p2_raw"].to_numpy(dtype=float))
                train_h = predict_stage_hazards(pipes, part)
                high_bases[index_name] = {
                    "train": part.reset_index(drop=True),
                    "train_hazards": train_h,
                    "train_z": scaler.transform(part["p2_raw"].to_numpy(dtype=float)),
                    "p2_scaler": scaler,
                }
    fits = fit_candidate_betas(candidate_id, high_bases)
    beta_values = {name: float(item["beta"]) for name, item in fits.items()}
    all_positive = bool(beta_values and all(v > 0.0 for v in beta_values.values()))
    if not all_positive:
        raise RuntimeError(f"selected candidate full-DEV beta sign gate failed: {beta_values}")
    parameter_bundle = {
        "selected_candidate": candidate_id,
        "source_parent_he00_v8_sha256": parent_sha,
        "source_metadata_inventory": source_audit,
        "DEV_window": {"start": DEV_START, "end": DEV_END},
        "geometry": geometry_params,
        "P2_standardizers": {
            index_name: {
                "mean": float(base["p2_scaler"].mean),
                "scale": float(base["p2_scaler"].scale),
            }
            for index_name, base in high_bases.items()
        },
        "P2_beta_fits": {
            name: {
                "beta": float(item["beta"]),
                "objective": float(item["objective"]),
                "success": bool(item["success"]),
                "n_cells": int(item["n_cells"]),
                "bounds": [float(x) for x in item["bounds"]],
            }
            for name, item in fits.items()
        },
        "selected_beta_components_all_strictly_positive": all_positive,
        "full_DEV_empirical_benchmark_stage_hazards": empirical,
    }
    freeze = {
        "schema_id": "overnight_open_gap_fill_v21_dev_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "stage": "V21_DEV_selected_full_fit_freeze_before_Audit_A",
        "parameter_bundle": parameter_bundle,
        "parameter_bundle_sha256": canonical_digest(parameter_bundle),
        "Audit_A_outcomes_opened": False,
        "Audit_B_outcomes_opened": False,
        "External_Reserve_outcomes_opened": False,
        "production_authority": False,
    }
    return freeze


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", help="authoritative full-OHLC HE-00 v8 or equivalent V21 DEV parquet dataset")
    parser.add_argument("--parent-source-sha256", default=EXPECTED_PARENT_SHA)
    parser.add_argument("--receipt-out", type=Path, default=OUT)
    parser.add_argument("--usage-out", type=Path, default=USAGE)
    parser.add_argument("--parameter-out", type=Path, default=PARAM_OUT)
    args = parser.parse_args()

    auth, family, protocol, _ = validate_authority(args.parent_source_sha256)
    source = require_source(args.source)
    source_audit = verify_metadata_preflight(source, auth)

    index_frames: dict[str, pd.DataFrame] = {}
    daily_frames: dict[str, pd.DataFrame] = {}
    build_audits: dict[str, dict] = {}
    for index_name, symbol in SYMBOLS.items():
        minutes = read_symbol_ohlc(source, symbol)
        frame, daily, audit = build_index_frame(minutes, index_name)
        index_frames[index_name] = frame
        daily_frames[index_name] = daily
        build_audits[index_name] = audit
    frames = attach_p2(index_frames, daily_frames)

    geometry_descriptive, high_bases = build_geometry_oof_descriptive(frames)

    attempts: list[dict] = []
    selected: str | None = None
    for candidate_id in p2.CANDIDATE_LADDER:
        attempt = evaluate_candidate(candidate_id, high_bases)
        attempts.append(attempt)
        if attempt["eligible"]:
            selected = candidate_id
            break

    if selected is None:
        decision = "V21_DEV_no_P2_successor"
        parameter_payload = None
    else:
        decision = "V21_DEV_first_eligible_P2_successor_selected_pending_cloud_review"
        parameter_payload = fit_full_selected(selected, frames, source_audit, args.parent_source_sha256)
        dump_json(args.parameter_out.resolve(), parameter_payload)

    receipt = {
        "schema_id": "overnight_open_gap_fill_v21_dev_selection_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "stage": "local_V21_DEV_selection_complete_pending_cloud_review",
        "decision": decision,
        "code_commit": git_head(),
        "command": command_string(),
        "authorization": str(AUTH.relative_to(ROOT)),
        "candidate_family": str(FAMILY.relative_to(ROOT)),
        "selection_protocol": str(SELECTION_PROTOCOL.relative_to(ROOT)),
        "runner_sha256": sha256(Path(__file__)),
        "P2_math_sha256": sha256(ROOT / "scripts/v21_p2_overlay.py"),
        "evaluation_kernel_sha256": sha256(ROOT / "scripts/v21_evaluation_kernel.py"),
        "session_gate_sha256": sha256(ROOT / "scripts/v21_session_complete_239_gate.py"),
        "source_path": str(source),
        "parent_he00_v8_sha256": args.parent_source_sha256,
        "metadata_preflight": source_audit,
        "build_audits": build_audits,
        "inventory": {
            index_name: {
                "target_valid_rows": int(len(frame)),
                "high_rows": int(frame["gap_sign"].eq("high").sum()),
                "low_rows": int(frame["gap_sign"].eq("low").sum()),
                "high_p2_available_rows": int((frame["gap_sign"].eq("high") & frame["p2_available"]).sum()),
                "high_gt10_p2_available_rows": int((frame["gap_sign"].eq("high") & frame["p2_available"] & (frame["abs_gap"] > 0.001)).sum()),
            }
            for index_name, frame in frames.items()
        },
        "geometry_control_expanding_OOF": geometry_descriptive,
        "candidate_order": list(p2.CANDIDATE_LADDER),
        "attempted_candidate_count": int(len(attempts)),
        "attempts": attempts,
        "selected_candidate": selected,
        "stop_at_first_eligible_respected": True,
        "full_DEV_parameter_freeze_written": parameter_payload is not None,
        "full_DEV_parameter_bundle_sha256": None if parameter_payload is None else parameter_payload["parameter_bundle_sha256"],
        "feature_search_performed": False,
        "candidate_addition_or_reordering_performed": False,
        "model_class_search_performed": False,
        "hyperparameter_search_performed": False,
        "beta_bound_or_regularizer_search_performed": False,
        "probability_calibration_performed": False,
        "binary_threshold_selection_performed": False,
        "trading_return_used": False,
        "Audit_A_outcomes_opened": False,
        "Audit_B_outcomes_opened": False,
        "External_Reserve_outcomes_opened": False,
        "supporting_crosscheck_2014Q4_opened": False,
        "CSI1000_post_2026_08_21_outcomes_opened": False,
        "raw_or_row_level_outputs_written_to_repo": False,
        "production_authority": False,
    }
    dump_json(args.receipt_out.resolve(), receipt)

    usage = {
        "schema_id": "overnight_open_gap_fill_v21_dev_data_usage@1.0",
        "session_date": "2026-09-08",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "opened": {
            "V21_DEV_CSI300_CSI500_2015-01-01_to_2018-12-31": True
        },
        "sealed": {
            "V21_AUDIT_A_2019-01-01_to_2021-12-31": True,
            "V21_AUDIT_B_2022-01-01_to_2024-12-31": True,
            "V21_EXTERNAL_RESERVE_2025-01-01_to_2026-08-21": True,
            "supporting_crosscheck_2014Q4": True,
            "CSI1000_post_2026_08_21_true_fresh": True
        },
        "source_parent_he00_v8_sha256": args.parent_source_sha256,
        "raw_rows_written_to_repo": False,
        "aggregate_outputs_only": True,
        "trading_return_used": False,
        "production_authority": False
    }
    dump_json(args.usage_out.resolve(), usage)

    print("V21_DEV_SELECTION_RESULT", json.dumps({
        "decision": decision,
        "attempted_candidate_count": len(attempts),
        "selected_candidate": selected,
        "parameter_freeze_written": parameter_payload is not None,
        "Audit_A_outcomes_opened": False,
        "Audit_B_outcomes_opened": False,
        "External_Reserve_outcomes_opened": False
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
