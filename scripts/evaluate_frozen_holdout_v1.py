#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from select_clock_candidates_dev import add_us_interval_features, feature_sets

ROOT = Path(__file__).resolve().parents[1]
TRAIN_END = pd.Timestamp("2018-12-31")
HOLD_START = pd.Timestamp("2019-01-01")
HOLD_END = pd.Timestamp("2020-12-31")
FIRST_HOLDOUT_RUN_ID = 34009974373


def fit_predict(frame: pd.DataFrame, cols: list[str], alpha: float) -> tuple[np.ndarray, np.ndarray, int, int]:
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
    pred = pipe.predict(x_te.loc[m_te])
    y = y_te.loc[m_te].to_numpy(dtype=float)
    return y, pred, int(m_tr.sum()), int(m_te.sum())


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    return {
        "ic": float(np.corrcoef(y, pred)[0, 1]),
        "sign_hit": float(np.mean((pred >= 0.0) == (y >= 0.0))),
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
    }


def main() -> int:
    baseline_receipt = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
    freeze = json.loads((ROOT / "docs/governance/cloud_session_20260906_selected_spec_v1.json").read_text())
    incident = json.loads((ROOT / "docs/governance/cloud_session_20260906_holdout_incident_v1.json").read_text())
    spec = freeze["selected_spec"]

    assert incident["holdout_consumed"] is True
    assert incident["run_id"] == FIRST_HOLDOUT_RUN_ID
    assert incident["candidate_or_parameter_changed_after_consumption"] is False
    assert incident["candidate_sha256"] == spec["sha256"]
    assert freeze["holdout_protocol"]["no_retuning_after_open"] is True

    expected_sha = spec["sha256"]
    digest_payload = {k: v for k, v in spec.items() if k != "sha256"}
    actual_sha = hashlib.sha256(json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert actual_sha == expected_sha, (actual_sha, expected_sha)
    assert spec["features"] == feature_sets()[spec["feature_set"]]

    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    frame = add_us_interval_features(panel, us)
    day = pd.to_datetime(frame["trading_day"])
    assert day.max() <= HOLD_END

    # Frozen candidate: no candidate/parameter change is allowed after the first holdout opening.
    y_c, p_c, ntr_c, nte_c = fit_predict(frame, spec["features"], float(spec["alpha"]))
    cand = metrics(y_c, p_c)

    # Frozen baseline comparator. This must exactly reproduce the historical receipt.
    base_cols = baseline_receipt["features"]
    y_b, p_b, ntr_b, nte_b = fit_predict(frame, base_cols, 1.0)
    base = metrics(y_b, p_b)
    assert ntr_b == int(baseline_receipt["metrics"]["n_train"])
    assert nte_b == int(baseline_receipt["metrics"]["n_test"])
    assert abs(base["ic"] - float(baseline_receipt["metrics"]["ridge_ic"])) < 1e-6
    assert abs(base["sign_hit"] - float(baseline_receipt["metrics"]["ridge_sign_hit"])) < 1e-12
    assert nte_c == nte_b

    # The historical receipt's us_nasdaq_ic is retained as a frozen comparator number.
    # The first execution proved that its historical sample-mask/recipe is not identical
    # to a newly reconstructed one-variable regression. Do not rewrite history to force equality.
    frozen_receipt_us_nasdaq_ic = float(baseline_receipt["metrics"]["us_nasdaq_ic"])

    # Also report an explicitly named, reproducible same-run one-variable Ridge comparator.
    y_u, p_u, ntr_u, nte_u = fit_predict(frame, ["us_nasdaq"], 1.0)
    us_same_run = metrics(y_u, p_u)

    majority_down_hit = float(np.mean(y_c < 0.0))
    assert abs(majority_down_hit - float(baseline_receipt["metrics"]["majority_down_hit"])) < 1e-12

    result = {
        "schema_id": "overnight_open_frozen_holdout_repeat_audit_receipt@1.0",
        "evaluation_role": "repeat_audit_recovery_after_comparator_incident",
        "first_holdout_run_id": FIRST_HOLDOUT_RUN_ID,
        "candidate_sha256": expected_sha,
        "candidate_mutated_after_first_holdout_open": False,
        "retuned_after_holdout": False,
        "train": "2015-01-05_to_2018-12-31",
        "holdout": "2019-01-01_to_2020-12-31",
        "n_train": ntr_c,
        "n_holdout": nte_c,
        "candidate": cand,
        "frozen_baseline_ridge": base,
        "frozen_receipt_us_nasdaq_ic": frozen_receipt_us_nasdaq_ic,
        "same_run_us_nasdaq_ridge": {
            "n_train": ntr_u,
            "n_holdout": nte_u,
            **us_same_run,
        },
        "majority_down_hit": majority_down_hit,
        "deltas": {
            "ic_vs_baseline_ridge": cand["ic"] - base["ic"],
            "sign_hit_vs_baseline_ridge": cand["sign_hit"] - base["sign_hit"],
            "sign_hit_vs_majority_down": cand["sign_hit"] - majority_down_hit,
            "ic_vs_frozen_receipt_us_nasdaq": cand["ic"] - frozen_receipt_us_nasdaq_ic,
            "ic_vs_same_run_us_nasdaq_ridge": cand["ic"] - us_same_run["ic"],
            "sign_hit_vs_same_run_us_nasdaq_ridge": cand["sign_hit"] - us_same_run["sign_hit"],
            "r2_vs_baseline_ridge": cand["r2"] - base["r2"],
            "mae_vs_baseline_ridge": cand["mae"] - base["mae"],
            "rmse_vs_baseline_ridge": cand["rmse"] - base["rmse"],
        },
        "strict_baseline_win": bool(cand["ic"] > base["ic"] and cand["sign_hit"] > base["sign_hit"]),
        "beats_frozen_receipt_us_nasdaq_on_ic": bool(cand["ic"] > frozen_receipt_us_nasdaq_ic),
        "fresh_oos": False,
        "production_authority": False,
    }
    print("FROZEN_HOLDOUT_REPEAT_AUDIT_RESULT", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
