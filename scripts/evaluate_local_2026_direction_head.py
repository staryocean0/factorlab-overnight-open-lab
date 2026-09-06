#!/usr/bin/env python3
"""One-shot local 2026 direction-head challenge.

The model family and 2026 endpoint are frozen in
`docs/governance/cloud_session_20260906_direction_2026_fresh_protocol_v1.json`.
Fit both fixed direction heads on 2015-2025 before loading/scoring the frozen
2026 challenge. Do not tune on 2026. Raw 2026 rows must not be committed.
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
from sklearn.linear_model import QuantileRegressor, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_local_2021_2025_two_head as local

# Allow local-controller path overrides without changing model semantics.
local.ANNOTATED_PANEL = Path(os.environ.get("OVERNIGHT_ANNOTATED_PANEL", str(local.ANNOTATED_PANEL)))
local.DATAHUB_1M = Path(os.environ.get("OVERNIGHT_DATAHUB_1M", str(local.DATAHUB_1M)))
local.FRED_NDQ = Path(os.environ.get("OVERNIGHT_FRED_NASDAQ", str(local.FRED_NDQ)))
local.FRED_VIX = Path(os.environ.get("OVERNIGHT_FRED_VIX", str(local.FRED_VIX)))

ANNOTATED_PANEL = local.ANNOTATED_PANEL
DATAHUB_1M = local.DATAHUB_1M
FRED_NDQ = local.FRED_NDQ
FRED_VIX = local.FRED_VIX

FIT_START = "2015-01-05"
FIT_END = "2025-12-31"
VAL_START = "2026-01-05"
VAL_END = "2026-08-21"
SELECTED_PATH = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
PROTOCOL_PATH = ROOT / "docs/governance/cloud_session_20260906_direction_2026_fresh_protocol_v1.json"
FIT_FREEZE_PATH = ROOT / "docs/research/cloud_session_20260906_local_2026_direction_fit_freeze_v1.json"
RECEIPT_PATH = ROOT / "docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json"
DATA_USAGE_PATH = ROOT / "docs/governance/local_session_20260906_2026_direction_data_usage.json"
SELECTED_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"


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


def spec_digest(spec: dict) -> str:
    raw = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def complete_mask(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    return x.notna().all(axis=1) & y.notna()


def ridge_pipe() -> Pipeline:
    return Pipeline([("sc", StandardScaler()), ("model", Ridge(alpha=1.0))])


def median_pipe() -> Pipeline:
    return Pipeline(
        [
            ("sc", StandardScaler()),
            ("model", QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")),
        ]
    )


def pack_model(pipe: Pipeline, cols: list[str], n_train: int, name: str) -> dict:
    scaler: StandardScaler = pipe.named_steps["sc"]
    model = pipe.named_steps["model"]
    return {
        "name": name,
        "features": cols,
        "n_train": int(n_train),
        "scaler_mean": [float(x) for x in scaler.mean_],
        "scaler_scale": [float(x) for x in scaler.scale_],
        "coef": [float(x) for x in np.asarray(model.coef_).reshape(-1)],
        "intercept": float(np.asarray(model.intercept_).reshape(-1)[0]),
    }


def score_metrics(y: np.ndarray, pred_up: np.ndarray, score: np.ndarray) -> dict:
    actual_up = y >= 0.0
    correct = pred_up == actual_up
    tp = int(np.sum(pred_up & actual_up))
    fn = int(np.sum((~pred_up) & actual_up))
    tn = int(np.sum((~pred_up) & (~actual_up)))
    fp = int(np.sum(pred_up & (~actual_up)))
    recall_up = tp / (tp + fn) if (tp + fn) else None
    recall_down = tn / (tn + fp) if (tn + fp) else None
    balanced = None if recall_up is None or recall_down is None else 0.5 * (recall_up + recall_down)
    auc = None
    if np.unique(actual_up.astype(int)).size == 2:
        # Rank AUC without adding another model or threshold.
        order = pd.Series(score).rank(method="average").to_numpy(dtype=float)
        n_pos = int(actual_up.sum())
        n_neg = int((~actual_up).sum())
        rank_sum_pos = float(order[actual_up].sum())
        auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return {
        "n": int(len(y)),
        "direction_hit": float(np.mean(correct)),
        "correct_count": int(correct.sum()),
        "balanced_accuracy": float(balanced) if balanced is not None else None,
        "recall_up": float(recall_up) if recall_up is not None else None,
        "recall_down": float(recall_down) if recall_down is not None else None,
        "actual_up_share": float(np.mean(actual_up)),
        "pred_up_share": float(np.mean(pred_up)),
        "roc_auc": float(auc) if auc is not None else None,
        "tp": tp,
        "fn": fn,
        "tn": tn,
        "fp": fp,
    }


def exact_mcnemar_p(candidate_only_correct: int, baseline_only_correct: int) -> float:
    n = candidate_only_correct + baseline_only_correct
    if n == 0:
        return 1.0
    k = min(candidate_only_correct, baseline_only_correct)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2.0**n)
    return float(min(1.0, 2.0 * tail))


def monthly_metrics(days: pd.Series, y: np.ndarray, pred_up: np.ndarray, score: np.ndarray) -> dict:
    months = pd.to_datetime(days).dt.to_period("M").astype(str).to_numpy()
    result: dict[str, dict] = {}
    for month in sorted(set(months)):
        mask = months == month
        result[month] = score_metrics(y[mask], pred_up[mask], score[mask])
    return result


def build_local(start: str, end: str) -> pd.DataFrame:
    raw = pd.read_parquet(
        ANNOTATED_PANEL,
        filters=[("trading_day", ">=", start), ("trading_day", "<=", end)],
    )
    raw["trading_day"] = raw["trading_day"].astype(str)
    hours = local.load_hours(DATAHUB_1M, start, end)
    us = local.load_us(FRED_NDQ, FRED_VIX, max_date=end)
    frame = local.add_domestic_features(raw, hours)
    frame = local.attach_us(frame, us)
    return frame


def main() -> int:
    selected = load_json(SELECTED_PATH)
    protocol = load_json(PROTOCOL_PATH)
    spec = selected["selected_spec"]
    digest = spec_digest(spec)
    if digest != SELECTED_SHA or selected["selected_spec_sha256"] != SELECTED_SHA or protocol["candidate_spec_sha256"] != SELECTED_SHA:
        raise RuntimeError(f"frozen direction candidate SHA mismatch: {digest}")
    if spec["name"] != "median_quantile_sign":
        raise RuntimeError("unexpected selected direction candidate")
    cols = list(spec["direction_features"])

    # Identity audit of the previously frozen 2015-2020 development material.
    frozen = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    reconstruction = local.assert_dev_reconstruction(frozen)

    # FIT/FREEZE PHASE: no 2026 row is loaded here.
    fit_frame = build_local(FIT_START, FIT_END)
    fit_days = pd.to_datetime(fit_frame["trading_day"])
    fit_frame = fit_frame.loc[(fit_days >= FIT_START) & (fit_days <= FIT_END)].copy()
    fit_mask = complete_mask(fit_frame, cols)
    x_fit = fit_frame.loc[fit_mask, cols].apply(pd.to_numeric, errors="coerce")
    y_fit = pd.to_numeric(fit_frame.loc[fit_mask, "gap"], errors="coerce").to_numpy(dtype=float)

    baseline = ridge_pipe()
    candidate = median_pipe()
    baseline.fit(x_fit, y_fit)
    candidate.fit(x_fit, y_fit)

    fit_freeze = {
        "schema_id": "overnight_open_local_2026_direction_fit_freeze@1.0",
        "candidate_spec_sha256": digest,
        "fit_window": {"start": FIT_START, "end": FIT_END},
        "validation_window_not_opened": {"start": VAL_START, "end": VAL_END},
        "n_fit_rows": int(len(fit_frame)),
        "n_fit_complete": int(fit_mask.sum()),
        "baseline": pack_model(baseline, cols, int(fit_mask.sum()), "ridge_mean_sign"),
        "candidate": pack_model(candidate, cols, int(fit_mask.sum()), "median_quantile_sign"),
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "annotated_panel": sha256(ANNOTATED_PANEL),
            "datahub_1m_export": sha256(DATAHUB_1M),
            "fred_nasdaq": sha256(FRED_NDQ),
            "fred_vix": sha256(FRED_VIX),
            "selected_candidate": sha256(SELECTED_PATH),
            "protocol": sha256(PROTOCOL_PATH),
            "runner": sha256(Path(__file__)),
        },
        "fresh_oos": false,
        "production_authority": false,
        "note": "Both fixed direction heads were fit on 2015-2025 before any 2026 target row was loaded/scored.",
    }
    dump_json(FIT_FREEZE_PATH, fit_freeze)

    # FRESH-OPEN PHASE: model objects are already frozen above.
    full = build_local(FIT_START, VAL_END)
    days = pd.to_datetime(full["trading_day"])
    val = full.loc[(days >= VAL_START) & (days <= VAL_END)].copy()
    if val.empty:
        raise RuntimeError("frozen 2026 validation window is empty")
    if str(pd.to_datetime(val["trading_day"]).min().date()) < VAL_START or str(pd.to_datetime(val["trading_day"]).max().date()) > VAL_END:
        raise RuntimeError("2026 validation slice crossed the frozen endpoint")

    usable = complete_mask(val, cols)
    if int((~usable).sum()) != 0:
        raise RuntimeError(f"2026 validation has {int((~usable).sum())} incomplete rows; do not change the frozen mask silently")
    x_val = val.loc[usable, cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(val.loc[usable, "gap"], errors="coerce").to_numpy(dtype=float)
    baseline_score = np.asarray(baseline.predict(x_val), dtype=float)
    candidate_score = np.asarray(candidate.predict(x_val), dtype=float)
    baseline_up = baseline_score >= 0.0
    candidate_up = candidate_score >= 0.0

    baseline_metrics = score_metrics(y, baseline_up, baseline_score)
    candidate_metrics = score_metrics(y, candidate_up, candidate_score)
    actual_up = y >= 0.0
    baseline_correct = baseline_up == actual_up
    candidate_correct = candidate_up == actual_up
    candidate_only = int(np.sum(candidate_correct & (~baseline_correct)))
    baseline_only = int(np.sum(baseline_correct & (~candidate_correct)))
    correct_delta = int(candidate_correct.sum() - baseline_correct.sum())

    raw_confirmed = bool(
        candidate_metrics["direction_hit"] > baseline_metrics["direction_hit"]
        and correct_delta > 0
    )
    robust_confirmed = bool(
        raw_confirmed
        and candidate_metrics["balanced_accuracy"] is not None
        and baseline_metrics["balanced_accuracy"] is not None
        and candidate_metrics["balanced_accuracy"] >= baseline_metrics["balanced_accuracy"]
        and candidate_metrics["recall_up"] is not None
        and candidate_metrics["recall_down"] is not None
        and candidate_metrics["recall_up"] > 0.5
        and candidate_metrics["recall_down"] > 0.5
    )
    if robust_confirmed:
        decision = "direction_candidate_2026_robustly_confirmed"
    elif raw_confirmed:
        decision = "direction_candidate_2026_raw_hit_only_retain_ridge"
    else:
        decision = "direction_candidate_2026_not_confirmed_retain_ridge"

    val_days = val.loc[usable, "trading_day"]
    receipt = {
        "schema_id": "overnight_open_local_2026_direction_fresh_receipt@1.0",
        "session_date": "2026-09-06",
        "candidate": str(SELECTED_PATH.relative_to(ROOT)),
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "fit_freeze": str(FIT_FREEZE_PATH.relative_to(ROOT)),
        "candidate_spec_sha256": digest,
        "fit_window": {"start": FIT_START, "end": FIT_END},
        "validation_window": {"start": VAL_START, "end": VAL_END},
        "validation_min_day": str(pd.to_datetime(val_days).min().date()),
        "validation_max_day": str(pd.to_datetime(val_days).max().date()),
        "n_validation_rows": int(len(val)),
        "n_validation_complete": int(usable.sum()),
        "n_validation_dropped_missing": int((~usable).sum()),
        "baseline": baseline_metrics,
        "candidate": candidate_metrics,
        "candidate_minus_baseline_correct_count": correct_delta,
        "paired_disagreement_counts": {
            "candidate_correct_baseline_wrong": candidate_only,
            "baseline_correct_candidate_wrong": baseline_only,
            "total_disagreements": candidate_only + baseline_only,
        },
        "mcnemar_exact_p_value": exact_mcnemar_p(candidate_only, baseline_only),
        "monthly": {
            "baseline": monthly_metrics(val_days, y, baseline_up, baseline_score),
            "candidate": monthly_metrics(val_days, y, candidate_up, candidate_score),
        },
        "raw_hit_confirmation": raw_confirmed,
        "robust_confirmation": robust_confirmed,
        "decision": decision,
        "fresh_oos": true,
        "production_authority": false,
        "parameter_search_after_open": false,
        "trading_return_used_in_gate": false,
        "raw_2026_rows_written_to_bounded_repo": false,
        "source_hashes": fit_freeze["source_hashes"],
        "local_source_paths": {
            "annotated_panel": str(ANNOTATED_PANEL),
            "datahub_1m_export": str(DATAHUB_1M),
            "fred_nasdaq": str(FRED_NDQ),
            "fred_vix": str(FRED_VIX),
        },
    }
    dump_json(RECEIPT_PATH, receipt)
    data_usage = {
        "schema_id": "overnight_open_local_2026_direction_data_usage@1.0",
        "session_date": "2026-09-06",
        "2015-01-05_to_2025-12-31": "fit_only_for_fixed_ridge_and_median_direction_heads",
        "2026-01-05_to_2026-08-21": "fresh_direction_challenge_opened_once_after_fit_freeze",
        "post_2026-08-21": "unread_for_this_candidate_identity",
        "raw_validation_rows_persisted_in_bounded_repo": false,
        "fresh_oos": true,
        "production_authority": false,
    }
    dump_json(DATA_USAGE_PATH, data_usage)
    print("DIRECTION_2026_FRESH_RESULT", json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
