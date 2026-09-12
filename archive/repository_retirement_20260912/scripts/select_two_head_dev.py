#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from select_clock_candidates_dev import add_us_interval_features, feature_sets

ROOT = Path(__file__).resolve().parents[1]
DEV_END = pd.Timestamp("2018-12-31")


def fit_predict(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    cols: list[str],
    alpha: float,
    target_abs: bool = False,
) -> pd.Series:
    x_tr = train[cols].apply(pd.to_numeric, errors="coerce")
    y_tr = pd.to_numeric(train["gap"], errors="coerce")
    x_va = valid[cols].apply(pd.to_numeric, errors="coerce")
    m_tr = x_tr.notna().all(axis=1) & y_tr.notna()
    m_va = x_va.notna().all(axis=1) & pd.to_numeric(valid["gap"], errors="coerce").notna()
    target = y_tr.loc[m_tr].abs() if target_abs else y_tr.loc[m_tr]
    pipe = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    pipe.fit(x_tr.loc[m_tr], target)
    return pd.Series(pipe.predict(x_va.loc[m_va]), index=x_va.loc[m_va].index)


def mag_metrics(y: np.ndarray, mag: np.ndarray) -> dict:
    actual = np.abs(y)
    if len(actual) < 3 or np.std(actual) == 0 or np.std(mag) == 0:
        corr = None
    else:
        corr = float(np.corrcoef(actual, mag)[0, 1])
    err = actual - mag
    return {
        "n": int(len(actual)),
        "corr_abs_gap": corr,
        "mae_abs_gap": float(np.mean(np.abs(err))),
        "rmse_abs_gap": float(np.sqrt(np.mean(err ** 2))),
    }


def signed_metrics(y: np.ndarray, pred: np.ndarray, direction: np.ndarray) -> dict:
    err = y - pred
    return {
        "ic": float(np.corrcoef(y, pred)[0, 1]),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "direction_hit": float(np.mean(direction == (y >= 0.0))),
    }


def main() -> int:
    family = json.loads((ROOT / "docs/governance/cloud_session_20260906_two_head_family_v1.json").read_text())
    baseline = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
    freeze = json.loads((ROOT / "docs/governance/cloud_session_20260906_selected_spec_v1.json").read_text())
    clock_spec = freeze["selected_spec"]
    assert family["candidate_count"] == 2
    assert family["promotion_eligibility_from_2015_2020"] is False
    assert clock_spec["features"] == feature_sets()[clock_spec["feature_set"]]

    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    frame = add_us_interval_features(panel, us)
    day = pd.to_datetime(frame["trading_day"])
    dev = frame.loc[day <= DEV_END].copy()
    years = pd.to_datetime(dev["trading_day"]).dt.year

    names = ["abs_frozen_clock_signed_prediction", "direct_abs_gap_clock_ridge"]
    folds: list[dict] = []
    pooled = {"y": [], "base_pred": [], names[0]: [], names[1]: []}

    for valid_year in [2016, 2017, 2018]:
        train = dev.loc[years < valid_year]
        valid = dev.loc[years == valid_year]
        base_pred = fit_predict(train, valid, baseline["features"], 1.0, target_abs=False)
        clock_signed = fit_predict(train, valid, clock_spec["features"], float(clock_spec["alpha"]), target_abs=False)
        direct_mag_raw = fit_predict(train, valid, clock_spec["features"], float(clock_spec["alpha"]), target_abs=True)
        common = base_pred.index.intersection(clock_signed.index).intersection(direct_mag_raw.index)
        y = pd.to_numeric(valid.loc[common, "gap"], errors="coerce").to_numpy(dtype=float)
        b = base_pred.loc[common].to_numpy(dtype=float)
        c = clock_signed.loc[common].to_numpy(dtype=float)
        d_raw = direct_mag_raw.loc[common].to_numpy(dtype=float)
        direction = b >= 0.0
        direction_sign = np.where(direction, 1.0, -1.0)

        baseline_mag = np.abs(b)
        mag1 = np.abs(c)
        mag2 = np.maximum(d_raw, 0.0)
        signed1 = direction_sign * mag1
        signed2 = direction_sign * mag2

        fold = {
            "year": valid_year,
            "baseline": {
                "magnitude": mag_metrics(y, baseline_mag),
                "signed": signed_metrics(y, b, direction),
            },
            names[0]: {
                "magnitude": mag_metrics(y, mag1),
                "signed": signed_metrics(y, signed1, direction),
            },
            names[1]: {
                "magnitude": mag_metrics(y, mag2),
                "signed": signed_metrics(y, signed2, direction),
                "raw_negative_magnitude_predictions": int(np.sum(d_raw < 0.0)),
            },
        }
        folds.append(fold)
        pooled["y"].append(y)
        pooled["base_pred"].append(b)
        pooled[names[0]].append(signed1)
        pooled[names[1]].append(signed2)

    summaries = {}
    for name in ["baseline", *names]:
        if name == "baseline":
            mag_by_fold = [f["baseline"]["magnitude"] for f in folds]
        else:
            mag_by_fold = [f[name]["magnitude"] for f in folds]
        summaries[name] = {
            "mean_corr_abs_gap": float(np.mean([m["corr_abs_gap"] for m in mag_by_fold])),
            "mean_mae_abs_gap": float(np.mean([m["mae_abs_gap"] for m in mag_by_fold])),
            "mean_rmse_abs_gap": float(np.mean([m["rmse_abs_gap"] for m in mag_by_fold])),
            "worst_year_corr_abs_gap": float(np.min([m["corr_abs_gap"] for m in mag_by_fold])),
            "mean_direction_hit": float(np.mean([
                f["baseline"]["signed"]["direction_hit"] if name == "baseline" else f[name]["signed"]["direction_hit"]
                for f in folds
            ])),
        }

    base = summaries["baseline"]
    attempts = []
    for name in names:
        s = summaries[name]
        admissible = (
            abs(s["mean_direction_hit"] - base["mean_direction_hit"]) < 1e-12
            and s["mean_mae_abs_gap"] <= base["mean_mae_abs_gap"]
            and s["mean_rmse_abs_gap"] <= base["mean_rmse_abs_gap"]
            and s["worst_year_corr_abs_gap"] > 0.0
        )
        attempts.append({"name": name, "admissible": admissible, **s})
    admissible = [a for a in attempts if a["admissible"]]
    winner = None
    if admissible:
        winner = sorted(
            admissible,
            key=lambda a: (a["mean_rmse_abs_gap"], a["mean_mae_abs_gap"], -a["mean_corr_abs_gap"], a["name"]),
        )[0]

    y_all = np.concatenate(pooled["y"])
    b_all = np.concatenate(pooled["base_pred"])
    direction_all = b_all >= 0.0
    pooled_results = {
        "baseline": {
            "magnitude": mag_metrics(y_all, np.abs(b_all)),
            "signed": signed_metrics(y_all, b_all, direction_all),
        }
    }
    for name in names:
        signed = np.concatenate(pooled[name])
        pooled_results[name] = {
            "magnitude": mag_metrics(y_all, np.abs(signed)),
            "signed": signed_metrics(y_all, signed, direction_all),
        }

    selected_spec = None
    if winner is not None:
        selected_spec = {
            "architecture": "two_head_direction_magnitude@1.0",
            "direction_head": {
                "features": baseline["features"],
                "alpha": 1.0,
                "target": "gap",
                "output": "prediction>=0",
            },
            "magnitude_head": {
                "variant": winner["name"],
                "features": clock_spec["features"],
                "alpha": float(clock_spec["alpha"]),
                "target": "gap" if winner["name"] == names[0] else "abs(gap)",
                "transform": "abs(prediction)" if winner["name"] == names[0] else "max(prediction,0)",
            },
            "recombination": "direction_sign * magnitude",
            "selection_window": "2015-2018_time_ordered_OOF",
            "eligible_validation": "local_2021_2025_only",
        }
        digest = hashlib.sha256(json.dumps(selected_spec, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        selected_spec["sha256"] = digest

    result = {
        "schema_id": "overnight_open_two_head_dev_selection@1.0",
        "evidence_role": "post_hoc_architecture_development_selection_not_promotion",
        "folds": folds,
        "year_equal_summaries": summaries,
        "attempts": attempts,
        "selected_spec": selected_spec,
        "pooled_oof": pooled_results,
        "candidate_count": 2,
        "holdout_2019_2020_used": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    print("TWO_HEAD_DEV_SELECTION_RESULT", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
