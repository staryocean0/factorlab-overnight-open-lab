#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DEV_END = pd.Timestamp("2018-12-31")
BASE_DOMESTIC = [
    "r1", "r20", "abs_r1", "prev_gap", "overnight_trend_5",
    "prev_daytime", "prev_last_hour", "prev_afternoon", "rvol20",
    "weekend", "holiday_reopen",
]
ALPHAS = [0.1, 1.0, 10.0, 100.0]


def add_us_interval_features(panel: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy().sort_values("trading_day").reset_index(drop=True)
    days = pd.to_datetime(out["trading_day"]).to_numpy(dtype="datetime64[ns]")
    prev_days = np.empty_like(days)
    prev_days[0] = np.datetime64("NaT")
    prev_days[1:] = days[:-1]

    u = us.copy().sort_values("date").reset_index(drop=True)
    u_days = pd.to_datetime(u["date"]).to_numpy(dtype="datetime64[ns]")
    nasdaq = pd.to_numeric(u["nasdaq"], errors="coerce").to_numpy(dtype=float)
    vix = pd.to_numeric(u["vix"], errors="coerce").to_numpy(dtype=float)

    cur_idx = np.searchsorted(u_days, days, side="left") - 1
    base_idx = np.full(len(out), -1, dtype=int)
    valid_prev = ~pd.isna(prev_days)
    base_idx[valid_prev] = np.searchsorted(u_days, prev_days[valid_prev], side="left") - 1
    valid = (cur_idx >= 0) & (base_idx >= 0)

    n_int = np.full(len(out), np.nan)
    v_int = np.full(len(out), np.nan)
    count = np.full(len(out), np.nan)
    n_int[valid] = nasdaq[cur_idx[valid]] / nasdaq[base_idx[valid]] - 1.0
    v_int[valid] = vix[cur_idx[valid]] / vix[base_idx[valid]] - 1.0
    count[valid] = cur_idx[valid] - base_idx[valid]

    out["us_nasdaq_interval"] = n_int
    out["us_vix_interval"] = v_int
    out["us_session_count"] = count
    out["us_nasdaq_interval_x_holiday"] = out["us_nasdaq_interval"] * pd.to_numeric(out["holiday_reopen"], errors="coerce")
    out["us_vix_interval_x_holiday"] = out["us_vix_interval"] * pd.to_numeric(out["holiday_reopen"], errors="coerce")
    out["us_nasdaq_pos"] = np.maximum(out["us_nasdaq_interval"], 0.0)
    out["us_nasdaq_neg"] = np.minimum(out["us_nasdaq_interval"], 0.0)
    out["us_vix_pos"] = np.maximum(out["us_vix_interval"], 0.0)
    out["us_vix_neg"] = np.minimum(out["us_vix_interval"], 0.0)
    out["us_nasdaq_x_us_vix"] = out["us_nasdaq_interval"] * out["us_vix_interval"]
    return out


def feature_sets() -> dict[str, list[str]]:
    baseline = BASE_DOMESTIC + ["us_nasdaq", "us_vix_chg"]
    clock_replace = BASE_DOMESTIC + ["us_nasdaq_interval", "us_vix_interval"]
    clock_count = clock_replace + ["us_session_count"]
    return {
        "baseline": baseline,
        "clock_replace": clock_replace,
        "clock_count": clock_count,
        "clock_holiday_interaction": clock_count + ["us_nasdaq_interval_x_holiday", "us_vix_interval_x_holiday"],
        "clock_piecewise": clock_count + ["us_nasdaq_pos", "us_nasdaq_neg", "us_vix_pos", "us_vix_neg", "us_nasdaq_x_us_vix"],
        "clock_both": baseline + ["us_nasdaq_interval", "us_vix_interval", "us_session_count"],
    }


def score_one(frame: pd.DataFrame, cols: list[str], alpha: float) -> dict:
    fold_metrics = []
    pooled_y = []
    pooled_pred = []
    for valid_year in [2016, 2017, 2018]:
        years = pd.to_datetime(frame["trading_day"]).dt.year
        tr = frame.loc[years < valid_year]
        va = frame.loc[years == valid_year]
        x_tr = tr[cols].apply(pd.to_numeric, errors="coerce")
        y_tr = pd.to_numeric(tr["gap"], errors="coerce")
        x_va = va[cols].apply(pd.to_numeric, errors="coerce")
        y_va = pd.to_numeric(va["gap"], errors="coerce")
        m_tr = x_tr.notna().all(axis=1) & y_tr.notna()
        m_va = x_va.notna().all(axis=1) & y_va.notna()
        pipe = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
        pipe.fit(x_tr.loc[m_tr], y_tr.loc[m_tr])
        pred = pipe.predict(x_va.loc[m_va])
        y = y_va.loc[m_va].to_numpy(dtype=float)
        ic = float(np.corrcoef(y, pred)[0, 1])
        hit = float(np.mean((pred >= 0.0) == (y >= 0.0)))
        fold_metrics.append({"year": valid_year, "n": int(len(y)), "ic": ic, "sign_hit": hit})
        pooled_y.append(y)
        pooled_pred.append(pred)
    py = np.concatenate(pooled_y)
    pp = np.concatenate(pooled_pred)
    return {
        "folds": fold_metrics,
        "mean_ic": float(np.mean([m["ic"] for m in fold_metrics])),
        "mean_sign_hit": float(np.mean([m["sign_hit"] for m in fold_metrics])),
        "worst_year_ic": float(np.min([m["ic"] for m in fold_metrics])),
        "pooled_oof_ic": float(np.corrcoef(py, pp)[0, 1]),
        "pooled_oof_sign_hit": float(np.mean((pp >= 0.0) == (py >= 0.0))),
        "pooled_n": int(len(py)),
    }


def main() -> int:
    prereg = json.loads((ROOT / "docs/governance/cloud_session_20260906_candidate_family_v1.json").read_text())
    assert prereg["multiplicity"] == 24
    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    frame = add_us_interval_features(panel, us)
    day = pd.to_datetime(frame["trading_day"])
    dev = frame.loc[day <= DEV_END].copy()
    assert pd.to_datetime(dev["trading_day"]).max() <= DEV_END

    sets = feature_sets()
    attempts = []
    for name, cols in sets.items():
        for alpha in ALPHAS:
            metrics = score_one(dev, cols, alpha)
            attempts.append({
                "name": name,
                "alpha": alpha,
                "n_features": len(cols),
                "features": cols,
                **metrics,
            })
    assert len(attempts) == 24
    base = next(a for a in attempts if a["name"] == "baseline" and a["alpha"] == 1.0)
    for a in attempts:
        a["admissible"] = (
            a["mean_sign_hit"] >= base["mean_sign_hit"] - 0.005
            and a["worst_year_ic"] > 0.0
        )
    admissible = [a for a in attempts if a["admissible"]]
    assert admissible
    winner = sorted(
        admissible,
        key=lambda a: (
            -a["mean_ic"],
            -a["mean_sign_hit"],
            a["n_features"],
            abs(math.log10(a["alpha"])),
            a["name"],
        ),
    )[0]
    frozen_spec = {
        "feature_set": winner["name"],
        "alpha": winner["alpha"],
        "features": winner["features"],
        "feature_engineering_version": "us_interval_since_previous_cn_session@1.0",
        "train_window": "2015-01-05_to_2018-12-31",
        "selection_rule": prereg["selection_rule"],
    }
    spec_bytes = json.dumps(frozen_spec, sort_keys=True, separators=(",", ":")).encode()
    frozen_spec["sha256"] = hashlib.sha256(spec_bytes).hexdigest()

    print("US_INTERVAL_DEV_DIAGNOSTICS", {
        "count_zero_share": float((pd.to_numeric(dev["us_session_count"], errors="coerce") == 0).mean()),
        "count_gt1_share": float((pd.to_numeric(dev["us_session_count"], errors="coerce") > 1).mean()),
        "corr_interval_gap": float(np.corrcoef(pd.to_numeric(dev.loc[dev["us_nasdaq_interval"].notna() & dev["gap"].notna(), "us_nasdaq_interval"]), pd.to_numeric(dev.loc[dev["us_nasdaq_interval"].notna() & dev["gap"].notna(), "gap"]))[0, 1]),
    })
    print("BASELINE_DEV_CV", json.dumps(base, sort_keys=True))
    print("TOP_ATTEMPTS", json.dumps(sorted(attempts, key=lambda a: (-a["mean_ic"], -a["mean_sign_hit"]))[:10], sort_keys=True))
    print("SELECTED_SPEC", json.dumps(frozen_spec, sort_keys=True))
    print("HOLDOUT_TARGET_USED", False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
