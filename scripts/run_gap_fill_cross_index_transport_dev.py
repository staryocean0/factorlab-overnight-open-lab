#!/usr/bin/env python3
"""CT-DEV: cross-index Gap-Fill V2 transport on CSI300/CSI500 development history only.

Opens only the preregistered external-index DEV windows. Audit A/B and CSI1000
post-2026-08-21 outcomes are never loaded. T1 applies frozen CSI1000 V2 v1
parameters unchanged. T2 refits only the already-frozen geometry architecture
on each external index's DEV history and evaluates it by expanding-year OOF.

Only aggregate metrics and final index-specific parameters are persisted.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_gap_fill_v2_target_ledger as targetmod
import evaluate_local_gap_fill_v2_2026_repeat as evalbase

PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_cross_index_transport_protocol_v1.json"
CSI1000_PARAMETERS = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
OUT = ROOT / "docs/research/local_gap_fill_cross_index_transport_dev_receipt_v1.json"
PARAM_OUT = ROOT / "docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json"
USAGE = ROOT / "docs/governance/local_gap_fill_cross_index_transport_dev_data_usage_v1.json"

FEATURES = ["abs_gap", "abs_gap_over_rvol20"]
MATERIAL = {"all": 0.0, "gt10bp": 0.001, "gt30bp": 0.003}
ADMITTED_DATASET_VERSION = "bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
ADMITTED_DATASET_SHA256 = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
EXPECTED_CSI1000_ARCH_SHA = "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
EXPECTED_CSI1000_BUNDLE_SHA = "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def require_source() -> Path:
    raw = os.environ.get("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE")
    if not raw:
        raise RuntimeError("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE is required")
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"historical 1m source does not exist: {path}")
    if ADMITTED_DATASET_VERSION not in str(path):
        raise RuntimeError("historical source path is not the HE-00 admitted dataset identity")
    return path


def read_symbol(source: Path, symbol: str, start: str, end: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        source,
        filters=[("symbol", "==", symbol), ("trading_day", ">=", start), ("trading_day", "<=", end)],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError(f"no DEV rows for {symbol}")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].min() < start or frame["trading_day"].max() > end:
        raise RuntimeError(f"{symbol} source crossed CT-DEV boundary")
    if frame.duplicated(["trading_day", "timestamp"]).any():
        raise RuntimeError(f"{symbol} duplicate timestamp in CT-DEV source")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def build_development_frame(source: Path, name: str, spec: dict) -> tuple[pd.DataFrame, dict]:
    symbol = spec["symbol"]
    start = spec["development_window"]["start"]
    end = spec["development_window"]["end"]
    minutes = read_symbol(source, symbol, start, end)
    clocks = targetmod.expected_clocks()
    expected = clocks["eod"]
    expected_set = set(expected)

    groups = {day: g.copy() for day, g in minutes.groupby("trading_day", sort=True)}
    days = sorted(groups)
    daily_rows = []
    exact_240 = {}
    for day in days:
        g = groups[day]
        present = g["clock"].tolist()
        exact = len(g) == 240 and len(set(present)) == 240 and set(present) == expected_set
        exact_240[day] = bool(exact)
        gg = g.set_index("clock")
        close_1500 = np.nan
        open_0931 = np.nan
        if "15:00" in gg.index:
            close_1500 = pd.to_numeric(pd.Series([gg.loc["15:00", "close"]]), errors="coerce").iloc[0]
        if "09:31" in gg.index:
            open_0931 = pd.to_numeric(pd.Series([gg.loc["09:31", "open"]]), errors="coerce").iloc[0]
        daily_rows.append({
            "trading_day": day,
            "close_1500": close_1500,
            "open_0931": open_0931,
            "exact_240": bool(exact),
        })

    daily = pd.DataFrame(daily_rows).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    daily["prev_close"] = pd.to_numeric(daily["close_1500"], errors="coerce").shift(1)
    close = pd.to_numeric(daily["close_1500"], errors="coerce")
    daily["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    daily["gap"] = pd.to_numeric(daily["open_0931"], errors="coerce") / pd.to_numeric(daily["prev_close"], errors="coerce") - 1.0
    daily["abs_gap"] = daily["gap"].abs()
    daily["abs_gap_over_rvol20"] = daily["abs_gap"] / pd.to_numeric(daily["rvol20"], errors="coerce")

    target_rows = []
    invalid_reasons: dict[str, int] = {}
    for _, row in daily.iterrows():
        day = str(row["trading_day"])
        if not bool(row["exact_240"]):
            invalid_reasons["not_exact_complete_240_clocks"] = invalid_reasons.get("not_exact_complete_240_clocks", 0) + 1
            continue
        numeric = [row["open_0931"], row["prev_close"], row["gap"], row["rvol20"], row["abs_gap_over_rvol20"]]
        if not all(np.isfinite(float(v)) for v in numeric) or float(row["rvol20"]) <= 0.0:
            invalid_reasons["incomplete_gap_or_rvol20"] = invalid_reasons.get("incomplete_gap_or_rvol20", 0) + 1
            continue
        day_row = pd.Series({
            "trading_day": day,
            "open_0931": float(row["open_0931"]),
            "prev_close": float(row["prev_close"]),
            "overnight_gap": float(row["gap"]),
        })
        result = targetmod.compute_day(day_row, groups[day], clocks)
        if result is None or not bool(result.get("target_valid", False)):
            reason = "target_invalid" if result is None else str(result.get("invalid_reason"))
            invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1
            continue
        result["rvol20"] = float(row["rvol20"])
        result["abs_gap_over_rvol20"] = float(row["abs_gap_over_rvol20"])
        target_rows.append(result)

    frame = pd.DataFrame(target_rows)
    if frame.empty:
        raise RuntimeError(f"{name} has no CT-DEV target-valid complete rows")
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if frame["trading_day"].min() < start or frame["trading_day"].max() > end:
        raise RuntimeError(f"{name} target inventory crossed DEV boundary")
    if int((frame["fill_15m"].astype(bool) & ~frame["fill_60m"].astype(bool)).sum()) != 0:
        raise RuntimeError(f"{name} 15m/60m nesting violation")
    if int((frame["fill_60m"].astype(bool) & ~frame["fill_eod"].astype(bool)).sum()) != 0:
        raise RuntimeError(f"{name} 60m/EOD nesting violation")
    if not set(frame["gap_sign"].unique()).issubset({"high", "low"}):
        raise RuntimeError(f"{name} unexpected gap sign")

    audit = {
        "symbol": symbol,
        "development_window": {"start": start, "end": end},
        "minute_rows_loaded": int(len(minutes)),
        "trading_days_loaded": int(len(days)),
        "exact_240_days": int(sum(exact_240.values())),
        "target_valid_geometry_complete_rows": int(len(frame)),
        "invalid_reason_counts": invalid_reasons,
        "target_min_day": str(frame["trading_day"].min()),
        "target_max_day": str(frame["trading_day"].max()),
        "audit_a_or_later_rows_loaded": False,
    }
    return frame, audit


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


def stage_risk(frame: pd.DataFrame, stage: str) -> tuple[pd.Series, pd.Series]:
    if stage == "15m":
        return pd.Series(True, index=frame.index), frame["fill_15m"].astype(int)
    if stage == "60m":
        return ~frame["fill_15m"].astype(bool), frame["fill_60m"].astype(int)
    if stage == "eod":
        return ~frame["fill_60m"].astype(bool), frame["fill_eod"].astype(int)
    raise ValueError(stage)


def fit_stage(frame: pd.DataFrame, stage: str) -> tuple[Pipeline, dict]:
    risk, target = stage_risk(frame, stage)
    part = frame.loc[risk].copy()
    y = target.loc[risk].to_numpy(dtype=int)
    if len(part) == 0 or np.unique(y).size != 2:
        raise RuntimeError(f"{stage} risk set lacks both classes")
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise RuntimeError(f"nonfinite {stage} feature")
    pipe = make_pipeline()
    pipe.fit(x, y)
    sc = pipe.named_steps["sc"]
    model = pipe.named_steps["model"]
    params = {
        "stage": stage,
        "training_min_day": str(part["trading_day"].min()),
        "training_max_day": str(part["trading_day"].max()),
        "n_train_risk": int(len(part)),
        "event_count": int(y.sum()),
        "event_rate": float(y.mean()),
        "feature_names": FEATURES,
        "scaler": {
            "mean": [float(v) for v in np.asarray(sc.mean_, dtype=float)],
            "scale": [float(v) for v in np.asarray(sc.scale_, dtype=float)],
            "var": [float(v) for v in np.asarray(sc.var_, dtype=float)],
            "n_features_in": int(sc.n_features_in_),
            "n_samples_seen": int(np.asarray(sc.n_samples_seen_).item()),
        },
        "logistic": {
            "coef": [float(v) for v in np.asarray(model.coef_[0], dtype=float)],
            "intercept": float(np.asarray(model.intercept_, dtype=float)[0]),
            "classes": [int(v) for v in np.asarray(model.classes_, dtype=int)],
            "n_iter": [int(v) for v in np.asarray(model.n_iter_, dtype=int)],
            "n_features_in": int(model.n_features_in_),
        },
    }
    return pipe, params


def pipe_probs(pipes: dict[str, Pipeline], x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    h15 = pipes["15m"].predict_proba(x)[:, 1]
    h60 = pipes["60m"].predict_proba(x)[:, 1]
    heod = pipes["eod"].predict_proba(x)[:, 1]
    return (
        h15,
        1.0 - (1.0 - h15) * (1.0 - h60),
        1.0 - (1.0 - h15) * (1.0 - h60) * (1.0 - heod),
    )


def empirical_stage_probs(train: pd.DataFrame, sign: str, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    part = train.loc[train["gap_sign"] == sign]
    hazards = {}
    for stage in ["15m", "60m", "eod"]:
        risk, target = stage_risk(part, stage)
        yy = target.loc[risk].to_numpy(dtype=int)
        if len(yy) == 0:
            raise RuntimeError(f"empty empirical risk set {sign} {stage}")
        hazards[stage] = float(np.mean(yy))
    h15, h60, heod = hazards["15m"], hazards["60m"], hazards["eod"]
    return (
        np.full(n, h15),
        np.full(n, 1.0 - (1.0 - h15) * (1.0 - h60)),
        np.full(n, 1.0 - (1.0 - h15) * (1.0 - h60) * (1.0 - heod)),
    )


def attach_probs(part: pd.DataFrame, probs: tuple[np.ndarray, np.ndarray, np.ndarray], prefix: str) -> pd.DataFrame:
    out = part.copy()
    out[f"{prefix}_p15"] = probs[0]
    out[f"{prefix}_p60"] = probs[1]
    out[f"{prefix}_peod"] = probs[2]
    return out


def eval_scored(frame: pd.DataFrame, prefix: str) -> dict:
    result = {}
    for sign in ["high", "low"]:
        sign_part = frame.loc[frame["gap_sign"] == sign].copy()
        sign_result = {}
        for cohort, threshold in MATERIAL.items():
            part = sign_part if threshold == 0.0 else sign_part.loc[sign_part["abs_gap"] > threshold].copy()
            probs = (
                part[f"{prefix}_p15"].to_numpy(dtype=float),
                part[f"{prefix}_p60"].to_numpy(dtype=float),
                part[f"{prefix}_peod"].to_numpy(dtype=float),
            )
            sign_result[cohort] = evalbase.evaluate_cohort(part, probs, include_deciles=False)
        arr = sign_part[[f"{prefix}_p15", f"{prefix}_p60", f"{prefix}_peod"]].to_numpy(dtype=float)
        sign_result["monotonicity_violations"] = int(np.sum((arr[:, 0] > arr[:, 1] + 1e-15) | (arr[:, 1] > arr[:, 2] + 1e-15))) if len(arr) else 0
        sign_result["counts"] = {
            "all": int(len(sign_part)),
            "gt10bp": int((sign_part["abs_gap"] > 0.001).sum()),
            "gt30bp": int((sign_part["abs_gap"] > 0.003).sum()),
        }
        result[sign] = sign_result
    return result


def annual_summary(frame: pd.DataFrame, prefix: str) -> dict:
    out = {}
    for year, part in frame.groupby(frame["trading_day"].str.slice(0, 4), sort=True):
        out[str(year)] = eval_scored(part, prefix)
    return out


def t1_exact_transport(frame: pd.DataFrame, csi_bundle: dict) -> tuple[dict, dict]:
    scored_parts = []
    for sign in ["high", "low"]:
        part = frame.loc[frame["gap_sign"] == sign].copy()
        x = part[FEATURES].to_numpy(dtype=float)
        probs = evalbase.cumulative_probs(csi_bundle["heads"][sign], x)
        scored_parts.append(attach_probs(part, probs, "t1"))
    scored = pd.concat(scored_parts, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
    return eval_scored(scored, "t1"), annual_summary(scored, "t1")


def t2_oof(frame: pd.DataFrame, validation_years: list[int]) -> tuple[pd.DataFrame, list[dict]]:
    folds = []
    scored_parts = []
    for year in validation_years:
        train = frame.loc[frame["trading_day"] < f"{year}-01-01"].copy()
        val = frame.loc[frame["trading_day"].str.startswith(str(year))].copy()
        if train.empty or val.empty:
            raise RuntimeError(f"empty T2 fold {year}")
        fold_info = {"validation_year": int(year), "train_n": int(len(train)), "validation_n": int(len(val)), "by_sign": {}}
        for sign in ["high", "low"]:
            tr = train.loc[train["gap_sign"] == sign].copy()
            va = val.loc[val["gap_sign"] == sign].copy()
            if tr.empty or va.empty:
                raise RuntimeError(f"empty sign in T2 fold {year} {sign}")
            pipes = {}
            for stage in ["15m", "60m", "eod"]:
                pipes[stage], _ = fit_stage(tr, stage)
            x = va[FEATURES].to_numpy(dtype=float)
            model_probs = pipe_probs(pipes, x)
            bench_probs = empirical_stage_probs(train, sign, len(va))
            vv = attach_probs(va, model_probs, "t2")
            vv = attach_probs(vv, bench_probs, "bench")
            scored_parts.append(vv)
            fold_info["by_sign"][sign] = {"train_n": int(len(tr)), "validation_n": int(len(va))}
        folds.append(fold_info)
    scored = pd.concat(scored_parts, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
    expected_years = sorted(set(int(y) for y in validation_years))
    got_years = sorted(set(pd.to_numeric(scored["trading_day"].str.slice(0, 4)).astype(int).tolist()))
    if got_years != expected_years:
        raise RuntimeError(f"T2 OOF year inventory drifted: {got_years}")
    return scored, folds


def final_index_bundle(frame: pd.DataFrame, name: str, spec: dict) -> dict:
    heads = {}
    for sign in ["high", "low"]:
        part = frame.loc[frame["gap_sign"] == sign].copy()
        stages = {}
        for stage in ["15m", "60m", "eod"]:
            _, stages[stage] = fit_stage(part, stage)
        heads[sign] = {
            "features": FEATURES,
            "n_sign_rows": int(len(part)),
            "min_day": str(part["trading_day"].min()),
            "max_day": str(part["trading_day"].max()),
            "stages": stages,
        }
    bundle = {
        "index": name,
        "symbol": spec["symbol"],
        "development_window": spec["development_window"],
        "features": FEATURES,
        "estimator": {
            "pipeline": "StandardScaler + LogisticRegression",
            "StandardScaler": {"with_mean": True, "with_std": True},
            "LogisticRegression": {"C": 1.0, "penalty": "l2", "solver": "lbfgs", "class_weight": None, "fit_intercept": True, "max_iter": 1000},
            "probability_calibration": "none",
            "binary_threshold": None,
        },
        "hazard_probability_contract": {
            "p15": "h15",
            "p60": "1-(1-h15)*(1-h60)",
            "pEOD": "1-(1-h15)*(1-h60)*(1-hEOD)",
        },
        "heads": heads,
    }
    return bundle


def main() -> int:
    protocol = load_json(PROTOCOL)
    if protocol["research_identity"] != "gap_fill_cross_index_transport_v1" or protocol["stage"] != "CT-DEV_external_index_development_transport":
        raise RuntimeError("cross-index protocol identity/stage drifted")
    if protocol["transport_modes"]["T2_architecture_transport"]["alternative_model_or_hyperparameter_search"] is not False:
        raise RuntimeError("CT-DEV unexpectedly permits model search")

    csi_freeze = load_json(CSI1000_PARAMETERS)
    if csi_freeze["selected_architecture_sha256"] != EXPECTED_CSI1000_ARCH_SHA:
        raise RuntimeError("CSI1000 architecture identity drifted")
    if csi_freeze["parameter_bundle_sha256"] != EXPECTED_CSI1000_BUNDLE_SHA:
        raise RuntimeError("CSI1000 parameter bundle identity drifted")
    csi_bundle = csi_freeze["parameter_bundle"]
    if evalbase.parameter_bundle_digest(csi_bundle) != EXPECTED_CSI1000_BUNDLE_SHA:
        raise RuntimeError("CSI1000 parameter bundle canonical digest drifted")

    source = require_source()
    index_receipts = {}
    external_bundles = {}
    source_audits = {}

    for name in ["CSI300", "CSI500"]:
        spec = protocol["indices"][name]
        frame, source_audit = build_development_frame(source, name, spec)
        source_audits[name] = source_audit

        t1_metrics, t1_annual = t1_exact_transport(frame, csi_bundle)

        oof, folds = t2_oof(frame, [int(y) for y in spec["oof_validation_years"]])
        t2_metrics = eval_scored(oof, "t2")
        bench_metrics = eval_scored(oof, "bench")
        t2_annual = annual_summary(oof, "t2")
        bench_annual = annual_summary(oof, "bench")

        external_bundle = final_index_bundle(frame, name, spec)
        external_bundles[name] = {
            "parameter_bundle": external_bundle,
            "parameter_bundle_sha256": canonical_digest(external_bundle),
        }

        index_receipts[name] = {
            "symbol": spec["symbol"],
            "development_window": spec["development_window"],
            "development_inventory": {
                "n": int(len(frame)),
                "high": int((frame["gap_sign"] == "high").sum()),
                "low": int((frame["gap_sign"] == "low").sum()),
                "gt10bp": int((frame["abs_gap"] > 0.001).sum()),
                "gt30bp": int((frame["abs_gap"] > 0.003).sum()),
            },
            "T1_exact_parameter_transport": {
                "refit": False,
                "metrics": t1_metrics,
                "annual": t1_annual,
            },
            "T2_architecture_transport_expanding_OOF": {
                "validation_years": [int(y) for y in spec["oof_validation_years"]],
                "folds": folds,
                "model_metrics": t2_metrics,
                "benchmark_metrics": bench_metrics,
                "model_annual": t2_annual,
                "benchmark_annual": bench_annual,
                "model_selection_performed": False,
            },
            "final_T2_parameter_bundle_sha256": external_bundles[name]["parameter_bundle_sha256"],
        }

    parameter_payload = {
        "schema_id": "overnight_open_gap_fill_cross_index_transport_dev_parameter_freeze@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "stage": "CT-DEV_final_index_specific_parameter_freeze_before_Audit_A",
        "source_dataset_version": ADMITTED_DATASET_VERSION,
        "source_dataset_sha256_from_HE00": ADMITTED_DATASET_SHA256,
        "CSI1000_frozen_reference": {
            "architecture_sha256": EXPECTED_CSI1000_ARCH_SHA,
            "parameter_bundle_sha256": EXPECTED_CSI1000_BUNDLE_SHA,
        },
        "external_index_bundles": external_bundles,
        "audit_a_opened": False,
        "audit_b_opened": False,
        "csi1000_2026q4_fresh_opened": False,
        "model_selection_performed": False,
        "hyperparameter_search_performed": False,
        "production_authority": False,
    }
    dump_json(PARAM_OUT, parameter_payload)

    receipt = {
        "schema_id": "overnight_open_gap_fill_cross_index_transport_dev_receipt@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "stage": "CT-DEV_completed",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source_dataset_version": ADMITTED_DATASET_VERSION,
        "source_dataset_sha256_from_HE00": ADMITTED_DATASET_SHA256,
        "source_path": str(source),
        "source_audits": source_audits,
        "indices": index_receipts,
        "T1_refit_performed": False,
        "T2_refit_only_on_external_DEV": True,
        "feature_search_performed": False,
        "model_class_search_performed": False,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_performed": False,
        "audit_a_opened": False,
        "audit_b_opened": False,
        "supporting_crosscheck_opened": False,
        "csi1000_post_2026_08_21_outcomes_opened": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)

    usage = {
        "schema_id": "overnight_open_gap_fill_cross_index_transport_dev_data_usage@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "opened": {
            "CSI300_DEV_2005-04-08_to_2010-12-31": True,
            "CSI500_DEV_2007-01-15_to_2010-12-31": True,
        },
        "sealed": {
            "Audit_A_2011_2012": True,
            "Audit_B_2013_to_2014-10-16": True,
            "supporting_crosscheck_2014-10-17_to_2014-12-31": True,
            "CSI1000_2026Q4_true_fresh": True,
        },
        "raw_rows_written_to_repo": False,
        "aggregate_outputs_only": True,
        "production_authority": False,
    }
    dump_json(USAGE, usage)

    print("GAP_FILL_CROSS_INDEX_CT_DEV_RESULT", json.dumps({
        "CSI300_n": index_receipts["CSI300"]["development_inventory"]["n"],
        "CSI500_n": index_receipts["CSI500"]["development_inventory"]["n"],
        "CSI300_parameter_sha": external_bundles["CSI300"]["parameter_bundle_sha256"],
        "CSI500_parameter_sha": external_bundles["CSI500"]["parameter_bundle_sha256"],
        "audit_a_opened": False,
        "audit_b_opened": False,
        "csi1000_2026q4_fresh_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
