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
DEV_END = pd.Timestamp("2018-12-31")


def fit_fold(train: pd.DataFrame, valid: pd.DataFrame, cols: list[str], alpha: float) -> pd.Series:
    x_tr = train[cols].apply(pd.to_numeric, errors="coerce")
    y_tr = pd.to_numeric(train["gap"], errors="coerce")
    x_va = valid[cols].apply(pd.to_numeric, errors="coerce")
    y_va = pd.to_numeric(valid["gap"], errors="coerce")
    m_tr = x_tr.notna().all(axis=1) & y_tr.notna()
    m_va = x_va.notna().all(axis=1) & y_va.notna()
    pipe = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    pipe.fit(x_tr.loc[m_tr], y_tr.loc[m_tr])
    return pd.Series(pipe.predict(x_va.loc[m_va]), index=x_va.loc[m_va].index)


def score(y: pd.Series, p: pd.Series) -> dict:
    yy = y.to_numpy(dtype=float)
    pp = p.to_numpy(dtype=float)
    return {
        "n": int(len(yy)),
        "ic": float(np.corrcoef(yy, pp)[0, 1]),
        "sign_hit": float(np.mean((pp >= 0.0) == (yy >= 0.0))),
        "mae": float(np.mean(np.abs(yy - pp))),
        "rmse": float(np.sqrt(np.mean((yy - pp) ** 2))),
    }


def main() -> int:
    hyp = json.loads((ROOT / "docs/governance/cloud_session_20260906_clock_gate_hypothesis_v1.json").read_text())
    freeze = json.loads((ROOT / "docs/governance/cloud_session_20260906_selected_spec_v1.json").read_text())
    baseline = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
    spec = freeze["selected_spec"]
    assert hyp["promotion_eligibility_from_2015_2020"] is False
    assert hyp["runtime_gate"]["grid_searched"] is False
    assert spec["features"] == feature_sets()[spec["feature_set"]]
    assert spec["sha256"] == hyp["component_specs"]["clock_candidate_sha256"]

    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    frame = add_us_interval_features(panel, us)
    day = pd.to_datetime(frame["trading_day"])
    dev = frame.loc[day <= DEV_END].copy()
    years = pd.to_datetime(dev["trading_day"]).dt.year

    fold_results = []
    pooled = {"y": [], "baseline": [], "clock": [], "gate": [], "count": []}
    for valid_year in [2016, 2017, 2018]:
        train = dev.loc[years < valid_year]
        valid = dev.loc[years == valid_year]
        b = fit_fold(train, valid, baseline["features"], 1.0)
        c = fit_fold(train, valid, spec["features"], float(spec["alpha"]))
        common = b.index.intersection(c.index)
        y = pd.to_numeric(valid.loc[common, "gap"], errors="coerce")
        count = pd.to_numeric(valid.loc[common, "us_session_count"], errors="coerce")
        b = b.loc[common]
        c = c.loc[common]
        gate = b.copy()
        exceptional = count != 1
        gate.loc[exceptional] = c.loc[exceptional]

        fold = {
            "year": valid_year,
            "exceptional_n": int(exceptional.sum()),
            "standard_n": int((~exceptional).sum()),
            "baseline": score(y, b),
            "clock": score(y, c),
            "gate": score(y, gate),
        }
        if int(exceptional.sum()) >= 3:
            fold["exceptional_slice"] = {
                "baseline": score(y.loc[exceptional], b.loc[exceptional]),
                "clock": score(y.loc[exceptional], c.loc[exceptional]),
                "gate": score(y.loc[exceptional], gate.loc[exceptional]),
            }
        fold_results.append(fold)
        pooled["y"].append(y.to_numpy(dtype=float))
        pooled["baseline"].append(b.to_numpy(dtype=float))
        pooled["clock"].append(c.to_numpy(dtype=float))
        pooled["gate"].append(gate.to_numpy(dtype=float))
        pooled["count"].append(count.to_numpy(dtype=float))

    y_all = pd.Series(np.concatenate(pooled["y"]))
    b_all = pd.Series(np.concatenate(pooled["baseline"]))
    c_all = pd.Series(np.concatenate(pooled["clock"]))
    g_all = pd.Series(np.concatenate(pooled["gate"]))
    count_all = pd.Series(np.concatenate(pooled["count"]))
    exceptional_all = count_all != 1

    mean_metrics = {}
    for model in ["baseline", "clock", "gate"]:
        mean_metrics[model] = {
            "mean_ic": float(np.mean([f[model]["ic"] for f in fold_results])),
            "mean_sign_hit": float(np.mean([f[model]["sign_hit"] for f in fold_results])),
            "worst_year_ic": float(np.min([f[model]["ic"] for f in fold_results])),
        }

    result = {
        "schema_id": "overnight_open_clock_gate_retrospective_corroboration@1.0",
        "evidence_role": "post_hoc_retrospective_corroboration_not_promotion",
        "gate_rule": "us_session_count == 1 -> baseline; otherwise -> frozen clock model",
        "folds": fold_results,
        "year_equal_means": mean_metrics,
        "pooled_oof": {
            "baseline": score(y_all, b_all),
            "clock": score(y_all, c_all),
            "gate": score(y_all, g_all),
            "exceptional_n": int(exceptional_all.sum()),
            "standard_n": int((~exceptional_all).sum()),
            "exceptional_baseline": score(y_all.loc[exceptional_all], b_all.loc[exceptional_all]),
            "exceptional_clock": score(y_all.loc[exceptional_all], c_all.loc[exceptional_all]),
            "exceptional_gate": score(y_all.loc[exceptional_all], g_all.loc[exceptional_all]),
        },
        "corroborated": bool(
            mean_metrics["gate"]["mean_ic"] >= mean_metrics["baseline"]["mean_ic"]
            and mean_metrics["gate"]["mean_sign_hit"] >= mean_metrics["baseline"]["mean_sign_hit"]
            and (
                mean_metrics["gate"]["mean_ic"] > mean_metrics["baseline"]["mean_ic"]
                or mean_metrics["gate"]["mean_sign_hit"] > mean_metrics["baseline"]["mean_sign_hit"]
            )
        ),
        "selection_or_parameter_search_performed": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    print("CLOCK_GATE_CORROBORATION_RESULT", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
