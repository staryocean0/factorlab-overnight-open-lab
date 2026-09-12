#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from select_clock_candidates_dev import add_us_interval_features, feature_sets

ROOT = Path(__file__).resolve().parents[1]
TRAIN_END = pd.Timestamp("2018-12-31")
HOLD_START = pd.Timestamp("2019-01-01")
HOLD_END = pd.Timestamp("2020-12-31")
TAIL = 0.003


def fit_series(frame: pd.DataFrame, cols: list[str], alpha: float) -> tuple[pd.Series, pd.Series]:
    day = pd.to_datetime(frame["trading_day"])
    train = frame.loc[day <= TRAIN_END]
    hold = frame.loc[(day >= HOLD_START) & (day <= HOLD_END)]
    x_tr = train[cols].apply(pd.to_numeric, errors="coerce")
    y_tr = pd.to_numeric(train["gap"], errors="coerce")
    x_te = hold[cols].apply(pd.to_numeric, errors="coerce")
    y_te = pd.to_numeric(hold["gap"], errors="coerce")
    m_tr = x_tr.notna().all(axis=1) & y_tr.notna()
    m_te = x_te.notna().all(axis=1) & y_te.notna()
    pipe = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    pipe.fit(x_tr.loc[m_tr], y_tr.loc[m_tr])
    pred = pd.Series(pipe.predict(x_te.loc[m_te]), index=x_te.loc[m_te].index, name="pred")
    y = y_te.loc[m_te].astype(float)
    return y, pred


def safe_ic(y: np.ndarray, p: np.ndarray) -> float | None:
    if len(y) < 3 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def score(y: pd.Series, p: pd.Series) -> dict:
    yy = y.to_numpy(dtype=float)
    pp = p.to_numpy(dtype=float)
    err = yy - pp
    return {
        "n": int(len(yy)),
        "ic": safe_ic(yy, pp),
        "sign_hit": float(np.mean((pp >= 0.0) == (yy >= 0.0))) if len(yy) else None,
        "mae": float(np.mean(np.abs(err))) if len(yy) else None,
        "rmse": float(np.sqrt(np.mean(err ** 2))) if len(yy) else None,
        "actual_up_share_ge0": float(np.mean(yy >= 0.0)) if len(yy) else None,
        "pred_up_share_ge0": float(np.mean(pp >= 0.0)) if len(yy) else None,
        "exact_zero_count": int(np.sum(yy == 0.0)),
    }


def slice_score(diag: pd.DataFrame, mask: pd.Series) -> dict:
    d = diag.loc[mask]
    c = score(d["gap"], d["candidate_pred"])
    b = score(d["gap"], d["baseline_pred"])
    return {
        "candidate": c,
        "baseline": b,
        "delta_sign_hit": None if c["sign_hit"] is None else c["sign_hit"] - b["sign_hit"],
        "delta_mae": None if c["mae"] is None else c["mae"] - b["mae"],
        "delta_rmse": None if c["rmse"] is None else c["rmse"] - b["rmse"],
        "delta_ic": None if c["ic"] is None or b["ic"] is None else c["ic"] - b["ic"],
    }


def disagreement_summary(diag: pd.DataFrame, mask: pd.Series) -> dict:
    d = diag.loc[mask]
    if d.empty:
        return {"n": 0}
    abs_gap = d["gap"].abs()
    return {
        "n": int(len(d)),
        "mean_abs_gap": float(abs_gap.mean()),
        "median_abs_gap": float(abs_gap.median()),
        "tail_share_abs_gt_30bp": float((abs_gap > TAIL).mean()),
        "holiday_reopen_share": float((pd.to_numeric(d["holiday_reopen"], errors="coerce") > 0).mean()),
        "zero_us_session_share": float((d["us_session_count"] == 0).mean()),
        "multi_us_session_share": float((d["us_session_count"] > 1).mean()),
    }


def main() -> int:
    scope = json.loads((ROOT / "docs/governance/cloud_session_20260906_posthoc_diagnostic_scope_v1.json").read_text())
    receipt = json.loads((ROOT / "docs/governance/cloud_session_20260906_holdout_repeat_audit_receipt_v1.json").read_text())
    freeze = json.loads((ROOT / "docs/governance/cloud_session_20260906_selected_spec_v1.json").read_text())
    base_receipt = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
    spec = freeze["selected_spec"]

    assert scope["evidence_role"] == "post_hoc_root_cause_only"
    assert scope["may_select_or_promote_new_parameters"] is False
    assert receipt["candidate_sha256"] == spec["sha256"] == scope["candidate_sha256"]
    assert spec["features"] == feature_sets()[spec["feature_set"]]

    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    frame = add_us_interval_features(panel, us)
    day = pd.to_datetime(frame["trading_day"])
    hold = frame.loc[(day >= HOLD_START) & (day <= HOLD_END)].copy()

    y_c, p_c = fit_series(frame, spec["features"], float(spec["alpha"]))
    y_b, p_b = fit_series(frame, base_receipt["features"], 1.0)
    common = y_c.index.intersection(y_b.index)
    assert len(common) == int(receipt["n_holdout"])
    assert np.allclose(y_c.loc[common].to_numpy(), y_b.loc[common].to_numpy())

    diag = hold.loc[common].copy()
    diag["gap"] = y_c.loc[common]
    diag["candidate_pred"] = p_c.loc[common]
    diag["baseline_pred"] = p_b.loc[common]
    diag["candidate_correct"] = (diag["candidate_pred"] >= 0.0) == (diag["gap"] >= 0.0)
    diag["baseline_correct"] = (diag["baseline_pred"] >= 0.0) == (diag["gap"] >= 0.0)
    diag["year"] = pd.to_datetime(diag["trading_day"]).dt.year
    diag["abs_gap"] = diag["gap"].abs()
    diag["us_session_count"] = pd.to_numeric(diag["us_session_count"], errors="coerce")

    slices = {
        "overall": pd.Series(True, index=diag.index),
        "year_2019": diag["year"] == 2019,
        "year_2020": diag["year"] == 2020,
        "ordinary_open_abs_le_30bp": diag["abs_gap"] <= TAIL,
        "tail_open_abs_gt_30bp": diag["abs_gap"] > TAIL,
        "high_open_tail_gt_30bp": diag["gap"] > TAIL,
        "low_open_tail_lt_minus_30bp": diag["gap"] < -TAIL,
        "holiday_reopen": pd.to_numeric(diag["holiday_reopen"], errors="coerce") > 0,
        "non_holiday": pd.to_numeric(diag["holiday_reopen"], errors="coerce") <= 0,
        "zero_new_us_session": diag["us_session_count"] == 0,
        "one_new_us_session": diag["us_session_count"] == 1,
        "multiple_new_us_sessions": diag["us_session_count"] > 1,
    }
    slice_results = {name: slice_score(diag, mask) for name, mask in slices.items()}

    candidate_only = diag["candidate_correct"] & ~diag["baseline_correct"]
    baseline_only = diag["baseline_correct"] & ~diag["candidate_correct"]
    both_correct = diag["candidate_correct"] & diag["baseline_correct"]
    both_wrong = ~diag["candidate_correct"] & ~diag["baseline_correct"]

    zero_count = int((diag["gap"] == 0.0).sum())
    legacy_majority = float(receipt["legacy_receipt_comparators"]["majority_down_hit_field"])
    strict_down = float((diag["gap"] < 0.0).mean())
    nonpositive = float((diag["gap"] <= 0.0).mean())

    result = {
        "schema_id": "overnight_open_clock_posthoc_root_cause@1.0",
        "candidate_sha256": spec["sha256"],
        "evidence_role": "post_hoc_root_cause_only_not_eligible_for_promotion",
        "n": int(len(diag)),
        "fixed_tail_cut_abs_gap": TAIL,
        "slices": slice_results,
        "sign_disagreements": {
            "candidate_correct_baseline_wrong": disagreement_summary(diag, candidate_only),
            "baseline_correct_candidate_wrong": disagreement_summary(diag, baseline_only),
            "both_correct": disagreement_summary(diag, both_correct),
            "both_wrong": disagreement_summary(diag, both_wrong),
            "net_candidate_minus_baseline_correct_count": int(candidate_only.sum() - baseline_only.sum()),
        },
        "zero_gap_semantics_audit": {
            "exact_zero_count": zero_count,
            "strict_negative_share": strict_down,
            "nonpositive_share": nonpositive,
            "legacy_majority_down_hit_field": legacy_majority,
            "legacy_equals_nonpositive_share": bool(abs(legacy_majority - nonpositive) < 1e-12),
            "legacy_equals_strict_negative_share": bool(abs(legacy_majority - strict_down) < 1e-12),
        },
        "selection_or_retuning_performed": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    print("POSTHOC_ROOT_CAUSE_RESULT", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
