#!/usr/bin/env python3
"""One-shot local repeat-only validation for frozen Gap-Fill Prediction V2 v1.

The model parameters, validation window, metrics and confirmation gates are frozen
before this runner opens any 2026 target row. This script never refits the model,
scaler, calibration layer, threshold or feature set. Raw 2026 rows are never
written to the repository.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_gap_fill_v2_target_ledger as targetmod

PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_2026_repeat_protocol_v1.json"
PARAMETERS = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
OUT = ROOT / "docs/research/cloud_session_20260906_local_gap_fill_v2_2026_repeat_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_session_20260906_gap_fill_v2_2026_repeat_data_usage_v1.json"

VAL_START = "2026-01-05"
VAL_END = "2026-08-21"
HISTORY_START = "2025-10-01"
EXPECTED_ARCH_SHA = "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
EXPECTED_PARAMETER_BUNDLE_SHA = "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"
EXPECTED_PARAMETER_BLOB = "eef7a9af6d42ee2faf53dbd16dce0b15ebfd10ed"
EPS = 1e-15
MATERIAL = {"gt10bp": 0.001, "gt30bp": 0.003}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require_local_path(env_name: str) -> Path:
    raw = os.environ.get(env_name)
    if not raw:
        raise RuntimeError(f"required environment variable is not set: {env_name}")
    path = Path(raw).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"local source does not exist: {env_name}={path}")
    return path


def parameter_bundle_digest(bundle: dict) -> str:
    raw = json.dumps(bundle, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def load_local_panel(path: Path) -> pd.DataFrame:
    cols = ["trading_day", "open_0931", "prev_close", "close_1500", "overnight_gap"]
    frame = pd.read_parquet(
        path,
        filters=[("trading_day", ">=", HISTORY_START), ("trading_day", "<=", VAL_END)],
        columns=cols,
    )
    if frame.empty:
        raise RuntimeError("local annotated panel returned no rows")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].max() > VAL_END:
        raise RuntimeError("post-frozen-end panel row entered repeat validation")
    if frame["trading_day"].min() > "2025-12-01":
        raise RuntimeError("insufficient pre-2026 history to compute frozen rvol20")
    frame = frame.sort_values("trading_day", kind="mergesort").drop_duplicates("trading_day", keep="last").reset_index(drop=True)
    close = pd.to_numeric(frame["close_1500"], errors="coerce")
    frame["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    gap_calc = pd.to_numeric(frame["open_0931"], errors="coerce") / pd.to_numeric(frame["prev_close"], errors="coerce") - 1.0
    stored = pd.to_numeric(frame["overnight_gap"], errors="coerce")
    valid_gap = gap_calc.notna() & stored.notna()
    gap_match_max_abs = float((gap_calc.loc[valid_gap] - stored.loc[valid_gap]).abs().max()) if valid_gap.any() else None
    if gap_match_max_abs is None or gap_match_max_abs > 1e-12:
        raise RuntimeError(f"local panel gap identity mismatch: {gap_match_max_abs}")
    frame["gap"] = gap_calc
    frame["abs_gap"] = gap_calc.abs()
    frame["abs_gap_over_rvol20"] = frame["abs_gap"] / pd.to_numeric(frame["rvol20"], errors="coerce")
    frame.attrs["gap_match_max_abs"] = gap_match_max_abs
    return frame


def load_local_minutes(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(
        path,
        filters=[
            ("symbol", "==", targetmod.SYMBOL),
            ("trading_day", ">=", VAL_START),
            ("trading_day", "<=", VAL_END),
        ],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError("local 2026 minute source returned no rows")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].min() < VAL_START or frame["trading_day"].max() > VAL_END:
        raise RuntimeError("minute source crossed frozen repeat-validation boundary")
    return frame


def build_targets(panel: pd.DataFrame, minutes: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    val_panel = panel.loc[(panel["trading_day"] >= VAL_START) & (panel["trading_day"] <= VAL_END)].copy()
    if val_panel.empty:
        raise RuntimeError("frozen 2026 panel slice is empty")
    groups = {d: g.copy() for d, g in minutes.groupby("trading_day", sort=False)}
    clocks = targetmod.expected_clocks()
    rows: list[dict] = []
    invalid: list[dict] = []
    for _, row in val_panel.sort_values("trading_day").iterrows():
        day = str(row["trading_day"])
        if day not in groups:
            invalid.append({"trading_day": day, "reason": "missing_day_minutes"})
            continue
        day_row = pd.Series({
            "trading_day": day,
            "open_0931": row["open_0931"],
            "prev_close": row["prev_close"],
            "overnight_gap": row["gap"],
        })
        result = targetmod.compute_day(day_row, groups[day], clocks)
        if result is None or not bool(result.get("target_valid", False)):
            invalid.append({"trading_day": day, "reason": None if result is None else result.get("invalid_reason")})
            continue
        rows.append(result)
    targets = pd.DataFrame(rows)
    if targets.empty:
        raise RuntimeError("no valid 2026 repeat-validation targets")
    if int((targets["fill_15m"] & (~targets["fill_60m"])).sum()) != 0 or int((targets["fill_60m"] & (~targets["fill_eod"])).sum()) != 0:
        raise RuntimeError("nested fill target invariant failed in 2026 repeat validation")
    audit = {
        "n_panel_validation_days": int(len(val_panel)),
        "n_target_valid": int(len(targets)),
        "n_target_invalid": int(len(invalid)),
        "invalid_reason_counts": {},
        "validation_min_day": str(targets["trading_day"].min()),
        "validation_max_day": str(targets["trading_day"].max()),
    }
    for item in invalid:
        key = str(item["reason"])
        audit["invalid_reason_counts"][key] = int(audit["invalid_reason_counts"].get(key, 0) + 1)
    return targets, audit


def apply_stage(stage: dict, x: np.ndarray) -> np.ndarray:
    mean = np.asarray(stage["scaler"]["mean"], dtype=float)
    scale = np.asarray(stage["scaler"]["scale"], dtype=float)
    coef = np.asarray(stage["logistic"]["coef"], dtype=float)
    intercept = float(stage["logistic"]["intercept"])
    if mean.shape != (2,) or scale.shape != (2,) or coef.shape != (2,) or np.any(scale <= 0):
        raise RuntimeError("sealed stage parameter shape invalid")
    z = (x - mean) / scale
    return expit(intercept + z @ coef)


def cumulative_probs(head: dict, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    h15 = apply_stage(head["stages"]["15m"], x)
    h60 = apply_stage(head["stages"]["60m"], x)
    heod = apply_stage(head["stages"]["eod"], x)
    p15 = h15
    p60 = 1.0 - (1.0 - h15) * (1.0 - h60)
    peod = 1.0 - (1.0 - h15) * (1.0 - h60) * (1.0 - heod)
    return p15, p60, peod


def benchmark_probs(protocol: dict, sign: str, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    b = protocol["fixed_development_empirical_benchmark"][sign]
    h15, h60, heod = float(b["h15"]), float(b["h60"]), float(b["hEOD"])
    return (
        np.full(n, h15, dtype=float),
        np.full(n, 1.0 - (1.0 - h15) * (1.0 - h60), dtype=float),
        np.full(n, 1.0 - (1.0 - h15) * (1.0 - h60) * (1.0 - heod), dtype=float),
    )


def calibration_descriptive(y: np.ndarray, p: np.ndarray) -> tuple[float | None, float | None]:
    if len(y) < 20 or np.unique(y).size < 2:
        return None, None
    q = np.clip(p.astype(float), 1e-9, 1.0 - 1e-9)
    logit = np.log(q / (1.0 - q))
    yy = y.astype(float)
    def objective(theta: np.ndarray) -> float:
        eta = theta[0] + theta[1] * logit
        prob = expit(eta)
        return float(-np.sum(yy * np.log(np.clip(prob, EPS, 1.0)) + (1.0 - yy) * np.log(np.clip(1.0 - prob, EPS, 1.0))))
    res = minimize(objective, np.asarray([0.0, 1.0]), method="BFGS")
    if not res.success or not np.all(np.isfinite(res.x)):
        return None, None
    return float(res.x[0]), float(res.x[1])


def horizon_metrics(y: np.ndarray, p: np.ndarray, include_deciles: bool = True) -> dict:
    if len(y) == 0:
        return {"n": 0}
    yy = y.astype(int)
    pp = np.clip(p.astype(float), EPS, 1.0 - EPS)
    auc = None if np.unique(yy).size < 2 else float(roc_auc_score(yy, pp))
    pr = None if np.unique(yy).size < 2 else float(average_precision_score(yy, pp))
    ci, cs = calibration_descriptive(yy, pp)
    out = {
        "n": int(len(yy)),
        "event_rate": float(np.mean(yy)),
        "mean_probability": float(np.mean(pp)),
        "brier_score": float(np.mean((pp - yy) ** 2)),
        "log_loss": float(-np.mean(yy * np.log(pp) + (1 - yy) * np.log(1.0 - pp))),
        "roc_auc": auc,
        "pr_auc": pr,
        "calibration_intercept": ci,
        "calibration_slope": cs,
    }
    deciles = []
    if include_deciles and len(yy) >= 40:
        order = pd.Series(pp).rank(method="first")
        bins = pd.qcut(order, 10, labels=False) + 1
        for d in range(1, 11):
            mask = np.asarray(bins == d)
            deciles.append({
                "decile": d,
                "n": int(mask.sum()),
                "mean_predicted": float(np.mean(pp[mask])),
                "observed_fill_rate": float(np.mean(yy[mask])),
            })
    out["probability_deciles"] = deciles
    return out


def evaluate_cohort(part: pd.DataFrame, probs: tuple[np.ndarray, np.ndarray, np.ndarray], include_deciles: bool = True) -> dict:
    p15, p60, peod = probs
    ys = [part["fill_15m"].to_numpy(dtype=int), part["fill_60m"].to_numpy(dtype=int), part["fill_eod"].to_numpy(dtype=int)]
    names = ["fill_15m", "fill_60m", "fill_eod"]
    ps = [p15, p60, peod]
    horizons = {name: horizon_metrics(y, p, include_deciles=include_deciles) for name, y, p in zip(names, ys, ps)}
    return {
        "n": int(len(part)),
        "horizons": horizons,
        "integrated_brier": float(np.mean([horizons[n]["brier_score"] for n in names])) if len(part) else None,
        "integrated_log_loss": float(np.mean([horizons[n]["log_loss"] for n in names])) if len(part) else None,
    }


def subset_probs(mask: np.ndarray, probs: tuple[np.ndarray, np.ndarray, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return tuple(p[mask] for p in probs)  # type: ignore[return-value]


def evaluate_sign(frame: pd.DataFrame, bundle: dict, protocol: dict, sign: str) -> dict:
    part = frame.loc[frame["gap_sign"] == sign].copy().reset_index(drop=True)
    if part.empty:
        raise RuntimeError(f"no repeat-validation rows for sign {sign}")
    x = part[["abs_gap", "abs_gap_over_rvol20"]].to_numpy(dtype=float)
    model_probs = cumulative_probs(bundle["heads"][sign], x)
    bench_probs = benchmark_probs(protocol, sign, len(part))
    monotonicity = int(np.sum((model_probs[0] > model_probs[1] + 1e-12) | (model_probs[1] > model_probs[2] + 1e-12)))
    if monotonicity != 0:
        raise RuntimeError(f"sealed V2 probabilities violate monotonicity for {sign}")

    cohort_masks = {
        "all": np.ones(len(part), dtype=bool),
        "gt10bp": part["abs_gap"].to_numpy(dtype=float) > MATERIAL["gt10bp"],
        "gt30bp": part["abs_gap"].to_numpy(dtype=float) > MATERIAL["gt30bp"],
    }
    model_eval, bench_eval = {}, {}
    for name, mask in cohort_masks.items():
        sub = part.loc[mask].reset_index(drop=True)
        model_eval[name] = evaluate_cohort(sub, subset_probs(mask, model_probs), include_deciles=True)
        bench_eval[name] = evaluate_cohort(sub, subset_probs(mask, bench_probs), include_deciles=False)

    monthly = {}
    months = pd.to_datetime(part["trading_day"]).dt.to_period("M").astype(str)
    for month in sorted(months.unique()):
        mask = np.asarray(months == month)
        monthly[month] = {
            "model": evaluate_cohort(part.loc[mask].reset_index(drop=True), subset_probs(mask, model_probs), include_deciles=False),
            "benchmark": evaluate_cohort(part.loc[mask].reset_index(drop=True), subset_probs(mask, bench_probs), include_deciles=False),
        }

    def imp(cohort: str, metric: str) -> float:
        return float(bench_eval[cohort][metric] - model_eval[cohort][metric])

    horizon_improvements = {
        h: float(bench_eval["gt10bp"]["horizons"][h]["brier_score"] - model_eval["gt10bp"]["horizons"][h]["brier_score"])
        for h in ["fill_15m", "fill_60m", "fill_eod"]
    }
    gates = {
        "pooled_all_integrated_brier_strictly_lower_than_frozen_empirical_benchmark": imp("all", "integrated_brier") > 0.0,
        "pooled_all_integrated_log_loss_strictly_lower_than_frozen_empirical_benchmark": imp("all", "integrated_log_loss") > 0.0,
        "pooled_gt10_integrated_brier_strictly_lower_than_frozen_empirical_benchmark": imp("gt10bp", "integrated_brier") > 0.0,
        "pooled_gt30_integrated_brier_not_higher_than_frozen_empirical_benchmark": imp("gt30bp", "integrated_brier") >= 0.0,
        "gt10_at_least_2_of_3_horizon_brier_scores_strictly_lower_than_benchmark": sum(v > 0.0 for v in horizon_improvements.values()) >= 2,
        "monotonicity_violations_zero": monotonicity == 0,
    }
    return {
        "n": int(len(part)),
        "n_gt10bp": int(cohort_masks["gt10bp"].sum()),
        "n_gt30bp": int(cohort_masks["gt30bp"].sum()),
        "model": model_eval,
        "benchmark": bench_eval,
        "improvement_vs_benchmark": {
            "all_integrated_brier": imp("all", "integrated_brier"),
            "all_integrated_log_loss": imp("all", "integrated_log_loss"),
            "gt10_integrated_brier": imp("gt10bp", "integrated_brier"),
            "gt30_integrated_brier": imp("gt30bp", "integrated_brier"),
            "gt10_horizon_brier": horizon_improvements,
        },
        "monotonicity_violations": monotonicity,
        "repeat_confirmation_gates": gates,
        "repeat_confirmed": bool(all(gates.values())),
        "monthly": monthly,
    }


def main() -> int:
    protocol = load_json(PROTOCOL)
    frozen = load_json(PARAMETERS)
    bundle = frozen["parameter_bundle"]
    if protocol["scientific_role"] != "repeat_only_not_fresh":
        raise RuntimeError("repeat protocol scientific role drifted")
    if protocol["validation_window"] != {"start": VAL_START, "end": VAL_END, "endpoint_is_frozen": True, "post_2026_08_21": "must_not_be_loaded"}:
        raise RuntimeError("repeat validation window drifted")
    if frozen["selected_architecture_sha256"] != EXPECTED_ARCH_SHA or protocol["frozen_model"]["selected_architecture_sha256"] != EXPECTED_ARCH_SHA:
        raise RuntimeError("selected V2 architecture identity drifted")
    digest = parameter_bundle_digest(bundle)
    if digest != EXPECTED_PARAMETER_BUNDLE_SHA or frozen["parameter_bundle_sha256"] != EXPECTED_PARAMETER_BUNDLE_SHA or protocol["frozen_model"]["parameter_bundle_sha256"] != EXPECTED_PARAMETER_BUNDLE_SHA:
        raise RuntimeError(f"sealed parameter bundle identity drifted: {digest}")
    if protocol["frozen_model"]["parameter_artifact_git_blob_sha"] != EXPECTED_PARAMETER_BLOB:
        raise RuntimeError("parameter artifact Git blob binding drifted")
    if bundle["features"] != ["abs_gap", "abs_gap_over_rvol20"]:
        raise RuntimeError("sealed V2 features drifted")

    annotated = require_local_path("OVERNIGHT_ANNOTATED_PANEL")
    minute_path = require_local_path("OVERNIGHT_DATAHUB_1M")
    panel = load_local_panel(annotated)
    minutes = load_local_minutes(minute_path)
    targets, target_audit = build_targets(panel, minutes)

    features = panel.loc[(panel["trading_day"] >= VAL_START) & (panel["trading_day"] <= VAL_END), ["trading_day", "gap", "abs_gap", "rvol20", "abs_gap_over_rvol20"]].copy()
    merged = targets.merge(features, on="trading_day", how="left", validate="one_to_one", suffixes=("_target", ""))
    if merged.empty:
        raise RuntimeError("repeat target/feature merge is empty")
    merged["gap_sign"] = np.where(pd.to_numeric(merged["gap"], errors="coerce") > 0.0, "high", "low")
    complete = merged[["abs_gap", "rvol20", "abs_gap_over_rvol20"]].apply(pd.to_numeric, errors="coerce").notna().all(axis=1)
    complete &= pd.to_numeric(merged["rvol20"], errors="coerce") > 0.0
    if int((~complete).sum()) != 0:
        raise RuntimeError(f"repeat validation contains {int((~complete).sum())} incomplete geometry rows; do not impute or change the frozen mask")
    merged = merged.loc[complete].copy().reset_index(drop=True)
    if merged["trading_day"].min() < VAL_START or merged["trading_day"].max() > VAL_END:
        raise RuntimeError("merged repeat inventory crossed frozen boundary")

    results = {sign: evaluate_sign(merged, bundle, protocol, sign) for sign in ["high", "low"]}
    confirmed = [s for s in ["high", "low"] if results[s]["repeat_confirmed"]]
    if len(confirmed) == 2:
        decision = "gap_fill_v2_2026_repeat_robustly_confirmed"
    elif len(confirmed) == 1:
        decision = "gap_fill_v2_2026_repeat_partially_confirmed"
    else:
        decision = "gap_fill_v2_2026_repeat_not_confirmed"

    receipt = {
        "schema_id": "overnight_open_gap_fill_v2_2026_repeat_receipt@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_prediction_v2",
        "scientific_role": "repeat_only_not_fresh",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "parameter_artifact": str(PARAMETERS.relative_to(ROOT)),
        "selected_architecture_sha256": EXPECTED_ARCH_SHA,
        "parameter_bundle_sha256": EXPECTED_PARAMETER_BUNDLE_SHA,
        "validation_window": {"start": VAL_START, "end": VAL_END},
        "target_audit": target_audit,
        "n_repeat_rows": int(len(merged)),
        "n_repeat_high": int((merged["gap_sign"] == "high").sum()),
        "n_repeat_low": int((merged["gap_sign"] == "low").sum()),
        "results": results,
        "repeat_confirmed_heads": confirmed,
        "decision": decision,
        "source_hashes": {
            "local_annotated_panel": sha256(annotated),
            "local_datahub_1m": sha256(minute_path),
            "protocol": sha256(PROTOCOL),
            "parameter_artifact": sha256(PARAMETERS),
            "runner": sha256(Path(__file__)),
        },
        "local_source_paths": {
            "annotated_panel": str(annotated),
            "datahub_1m": str(minute_path),
        },
        "model_refit_performed": False,
        "scaler_refit_performed": False,
        "feature_selection_performed": False,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_layer_fit_or_applied": False,
        "descriptive_calibration_regression_performed": True,
        "trading_return_used": False,
        "2026_repeat_validation_opened": True,
        "post_2026_08_21_rows_loaded": False,
        "raw_2026_rows_written_to_repo": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    usage = {
        "schema_id": "overnight_open_gap_fill_v2_2026_repeat_data_usage@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_prediction_v2",
        "window": "2026-01-05_to_2026-08-21",
        "role": "repeat_only_not_fresh",
        "2026_repeat_validation_opened": True,
        "post_2026_08_21": "not_loaded_true_fresh_reserved",
        "model_refit_performed": False,
        "parameter_search_performed": False,
        "raw_2026_rows_persisted_in_repo": False,
        "aggregate_receipt_only": True,
        "production_authority": False,
    }
    dump_json(USAGE, usage)
    print("GAP_FILL_V2_2026_REPEAT_RESULT", json.dumps({
        "n_repeat_rows": receipt["n_repeat_rows"],
        "n_repeat_high": receipt["n_repeat_high"],
        "n_repeat_low": receipt["n_repeat_low"],
        "repeat_confirmed_heads": receipt["repeat_confirmed_heads"],
        "decision": receipt["decision"],
        "fresh_oos": False,
        "post_2026_08_21_rows_loaded": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
