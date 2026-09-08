#!/usr/bin/env python3
"""Dedicated R5-C event-density mechanism validation on reusable DEV/VALIDATION.

The model family is frozen in the dedicated protocol.  This runner reads only
through 2025-12-31 and cannot access the reusable 2026 BLACKBOX.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from bisect import bisect_left
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R5C_reusable_validation_protocol_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R5C_reusable_validation_receipt_v1.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R5C_reusable_parameter_freeze_v1.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_START = "2015-01-05"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
HORIZON = 1200
DENSITY_BARS = 240
NORM_HISTORY = 100
BASE_FEATURES = ["severity", "wave_duration_bars", "bars_since_prev_confirmation"]
CAND_FEATURES = BASE_FEATURES + ["event_density_z"]
SCALES = ("S1", "S2")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def validate_protocol() -> dict:
    p = load_json(PROTOCOL)
    if p["research_identity"] != "rmr_event_density_state_reversal_v2":
        raise RuntimeError("R5-C identity drifted")
    if p["event_density"]["trailing_bars"] != DENSITY_BARS:
        raise RuntimeError("R5-C density window drifted")
    if p["event_density"]["normalization"]["history"] != "preceding_100_same_scale_property_observations":
        raise RuntimeError("R5-C normalization drifted")
    fam = p["model_family"]
    if fam["baseline_features"] != BASE_FEATURES or fam["candidate_features"] != CAND_FEATURES:
        raise RuntimeError("R5-C model family drifted")
    if fam["exact_model_count"] != 2 or fam["hyperparameter_search"] is not False:
        raise RuntimeError("R5-C model budget drifted")
    if p["VALIDATION_pass_requires_both_scales"] is not True:
        raise RuntimeError("R5-C cross-scale gate drifted")
    return p


def read_source(path: Path) -> pd.DataFrame:
    if sha256(path) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("R5-C source SHA mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].min()) != DEV_START or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("R5-C detailed source boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("R5-C DEV/VALIDATION runner read BLACKBOX")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("R5-C invalid closes")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def density_series(confirm_idxs: list[int]) -> np.ndarray:
    out = np.empty(len(confirm_idxs), dtype=float)
    for i, idx in enumerate(confirm_idxs):
        left = bisect_left(confirm_idxs, idx - (DENSITY_BARS - 1), 0, i + 1)
        out[i] = (i - left + 1) / float(DENSITY_BARS)
    return out


def causal_mad_z(values: np.ndarray, history: int = NORM_HISTORY) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    out = np.full(len(x), np.nan, dtype=float)
    for i in range(history, len(x)):
        past = x[i - history : i]
        if not np.isfinite(past).all() or not np.isfinite(x[i]):
            continue
        med = float(np.median(past))
        mad = float(np.median(np.abs(past - med)))
        if not np.isfinite(mad) or mad <= 0.0:
            continue
        out[i] = (x[i] - med) / mad
    return out


def wave_observations(waves: list[common.Wave], threshold: float, days: np.ndarray) -> pd.DataFrame:
    confirms = [int(w.confirm_idx) for w in waves]
    densities = density_series(confirms)
    z = causal_mad_z(densities)
    rows = []
    for i, wave in enumerate(waves):
        if i == 0 or not np.isfinite(z[i]):
            continue
        duration = int(wave.end_idx - wave.start_idx)
        spacing = int(wave.confirm_idx - waves[i - 1].confirm_idx)
        if duration <= 0 or spacing <= 0:
            continue
        rows.append({
            "wave_i": int(i),
            "day": str(days[wave.confirm_idx]),
            "confirm_idx": int(wave.confirm_idx),
            "direction": int(wave.direction),
            "severity": float(abs(wave.move) / threshold),
            "wave_duration_bars": float(duration),
            "bars_since_prev_confirmation": float(spacing),
            "event_density": float(densities[i]),
            "event_density_z": float(z[i]),
        })
    return pd.DataFrame(rows)


def first_passage_symmetric(
    prices: np.ndarray,
    start_idx: int,
    direction: int,
    threshold: float,
    max_end_idx: int,
) -> tuple[str, int]:
    anchor = float(prices[start_idx])
    if direction > 0:
        reversion = anchor * (1.0 - threshold)
        extension = anchor * (1.0 + threshold)
    else:
        reversion = anchor * (1.0 + threshold)
        extension = anchor * (1.0 - threshold)
    end = min(max_end_idx, start_idx + HORIZON)
    for j in range(start_idx + 1, end + 1):
        x = float(prices[j])
        if direction > 0:
            r = x <= reversion
            e = x >= extension
        else:
            r = x >= reversion
            e = x <= extension
        if r and e:
            return "censored", j
        if r:
            return "reversion", j
        if e:
            return "extension", j
    return "censored", end


def role_events(
    observations: pd.DataFrame,
    prices: np.ndarray,
    threshold: float,
    role_start: str,
    role_end: str,
    max_end_idx: int,
) -> pd.DataFrame:
    rows = []
    next_allowed = -1
    role = observations.loc[observations["day"].between(role_start, role_end)].copy()
    for row in role.itertuples(index=False):
        if int(row.confirm_idx) <= next_allowed:
            continue
        outcome, resolved = first_passage_symmetric(
            prices, int(row.confirm_idx), int(row.direction), threshold, max_end_idx
        )
        next_allowed = int(resolved)
        if outcome not in {"reversion", "extension"}:
            continue
        rows.append({
            "day": str(row.day),
            "severity": float(row.severity),
            "wave_duration_bars": float(row.wave_duration_bars),
            "bars_since_prev_confirmation": float(row.bars_since_prev_confirmation),
            "event_density_z": float(row.event_density_z),
            "y": int(outcome == "reversion"),
        })
    return pd.DataFrame(rows)


def fit_logit(frame: pd.DataFrame, features: list[str]) -> Pipeline:
    if len(frame) < 30 or frame["y"].nunique() < 2:
        raise RuntimeError("R5-C insufficient DEV sample")
    model = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000)),
    ])
    model.fit(frame[features].to_numpy(float), frame["y"].to_numpy(int))
    return model


def model_snapshot(model: Pipeline, features: list[str]) -> dict:
    sc: StandardScaler = model.named_steps["sc"]
    lr: LogisticRegression = model.named_steps["lr"]
    return {
        "features": list(features),
        "scaler": {
            "mean": [float(x) for x in sc.mean_],
            "scale": [float(x) for x in sc.scale_],
            "var": [float(x) for x in sc.var_],
        },
        "logistic": {
            "C": 1.0,
            "coef": [float(x) for x in lr.coef_[0]],
            "intercept": float(lr.intercept_[0]),
            "classes": [int(x) for x in lr.classes_],
        },
    }


def metrics(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> dict:
    if frame.empty:
        return {"n": 0, "brier": None, "logloss": None, "event_rate": None}
    y = frame["y"].to_numpy(int)
    p = model.predict_proba(frame[features].to_numpy(float))[:, 1]
    return {
        "n": int(len(frame)),
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "event_rate": float(np.mean(y)),
    }


def validate_scale(dev: pd.DataFrame, val: pd.DataFrame, scale: str, protocol: dict) -> tuple[dict, dict]:
    base = fit_logit(dev, BASE_FEATURES)
    cand = fit_logit(dev, CAND_FEATURES)
    pooled_base = metrics(base, val, BASE_FEATURES)
    pooled_cand = metrics(cand, val, CAND_FEATURES)
    annual = {}
    positive_years = 0
    each_year_min_ok = True
    min_year = int(protocol["VALIDATION_gates_each_scale"]["minimum_resolved_each_year"][scale])
    for year in range(2021, 2026):
        yf = val.loc[val["day"].str.startswith(str(year))]
        b = metrics(base, yf, BASE_FEATURES)
        c = metrics(cand, yf, CAND_FEATURES)
        delta = None if b["brier"] is None else float(b["brier"] - c["brier"])
        if delta is not None and delta > 0.0:
            positive_years += 1
        if len(yf) < min_year:
            each_year_min_ok = False
        annual[str(year)] = {"baseline": b, "candidate": c, "baseline_minus_candidate_brier": delta}
    min_pool = int(protocol["VALIDATION_gates_each_scale"]["minimum_resolved"][scale])
    gates = {
        "minimum_resolved": len(val) >= min_pool,
        "minimum_resolved_each_year": each_year_min_ok,
        "pooled_brier_better": pooled_cand["brier"] < pooled_base["brier"],
        "pooled_logloss_better": pooled_cand["logloss"] < pooled_base["logloss"],
        "annual_brier_improvement_ge_4_of_5": positive_years >= 4,
    }
    result = {
        "inventory": {"DEV_resolved": int(len(dev)), "VALIDATION_resolved": int(len(val))},
        "baseline": pooled_base,
        "candidate": pooled_cand,
        "baseline_minus_candidate_brier": float(pooled_base["brier"] - pooled_cand["brier"]),
        "baseline_minus_candidate_logloss": float(pooled_base["logloss"] - pooled_cand["logloss"]),
        "annual": annual,
        "candidate_event_density_z_coef": float(cand.named_steps["lr"].coef_[0][-1]),
        "gates": gates,
        "passed": bool(all(gates.values())),
    }
    snapshots = {
        "baseline_model": model_snapshot(base, BASE_FEATURES),
        "candidate_model": model_snapshot(cand, CAND_FEATURES),
    }
    return result, snapshots


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    args = ap.parse_args()

    protocol = validate_protocol()
    frame = read_source(args.source.resolve())
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    day_series = frame["trading_day"].astype(str)
    dev_end_idx = int(np.flatnonzero(day_series.to_numpy() <= DEV_END)[-1])
    val_end_idx = len(frame) - 1

    validation = {}
    scale_data = {}
    thresholds = {s: float(protocol["scales"][s]) for s in SCALES}
    for scale in SCALES:
        waves = common.detect_waves(prices, thresholds[scale])
        obs = wave_observations(waves, thresholds[scale], days)
        dev = role_events(obs, prices, thresholds[scale], DEV_START, DEV_END, dev_end_idx)
        val = role_events(obs, prices, thresholds[scale], VAL_START, VAL_END, val_end_idx)
        result, snapshots = validate_scale(dev, val, scale, protocol)
        validation[scale] = result
        scale_data[scale] = {"observations": obs, "snapshots": snapshots}

    passed = bool(all(validation[s]["passed"] for s in SCALES))
    receipt = {
        "schema_id": "factorlab_rmr_R5C_reusable_validation_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_event_density_state_reversal_v2",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "DEV_window": {"start": DEV_START, "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_opened": False,
        "validation": validation,
        "validation_passed": passed,
        "final_refit_performed": passed,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not passed:
        print("R5C_REUSABLE_VALIDATION_FAIL")
        return 2

    freeze = {
        "schema_id": "factorlab_rmr_R5C_reusable_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_event_density_state_reversal_v2",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": DEV_START, "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "density_bars": DENSITY_BARS,
        "normalization_history": NORM_HISTORY,
        "baseline_features": BASE_FEATURES,
        "candidate_features": CAND_FEATURES,
        "thresholds": thresholds,
        "pairings": {},
        "blackbox_minimum_resolved": protocol["BLACKBOX"]["minimum_resolved"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    for scale in SCALES:
        obs = scale_data[scale]["observations"]
        full = role_events(obs, prices, thresholds[scale], DEV_START, VAL_END, val_end_idx)
        base = fit_logit(full, BASE_FEATURES)
        cand = fit_logit(full, CAND_FEATURES)
        freeze["pairings"][scale] = {
            "n_final_fit": int(len(full)),
            "baseline_model": model_snapshot(base, BASE_FEATURES),
            "candidate_model": model_snapshot(cand, CAND_FEATURES),
        }
    freeze["parameter_bundle_sha256"] = json_digest(dict(freeze))
    dump_json(args.freeze.resolve(), freeze)
    print("R5C_REUSABLE_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
