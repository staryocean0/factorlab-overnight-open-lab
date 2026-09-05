#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_global_spillover_v3_complete_clock as v3
import research_global_spillover_v6_daily_a50 as v6

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/governance/baseline_receipt.json"
PLAN_PATH = ROOT / "docs/governance/global_spillover_v6_forensic_diagnostic_plan.json"
ORDINARY_PATH = ROOT / "data/development/sgx_a50_ordinary_preauction_endpoints.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v6_daily_a50_forensics.json"


def corr(a: pd.Series | np.ndarray, b: pd.Series | np.ndarray) -> float:
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.std(x[m]) == 0 or np.std(y[m]) == 0:
        return float("nan")
    return float(np.corrcoef(x[m], y[m])[0, 1])


def sign(v: float) -> int:
    return 1 if v > 0 else (-1 if v < 0 else 0)


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text())
    if plan["status"] != "post_hoc_nonselection_after_v6_progression_result":
        raise AssertionError("v6 forensic plan status drift")

    baseline = json.loads(BASELINE_PATH.read_text())
    df, common_stats = v6.build_frame()
    v4_features = list(baseline["features"]) + [
        "us_nasdaq_closure_extra",
        "us_vix_closure_extra",
        "hkma_usdcny_closure_return",
    ]
    feature_sets = {
        "V5A_common_sample_comparator": v4_features + ["a50_holiday_closure_return"],
        "V6A_plus_ordinary_A50_preauction_closure": v4_features + [
            "a50_holiday_closure_return",
            "a50_ordinary_preauction_closure_return",
        ],
    }
    metrics: dict[str, dict] = {}
    preds: dict[str, pd.DataFrame] = {}
    for cid, features in feature_sets.items():
        metrics[cid], preds[cid] = v3._fit_predict(df, features)

    p0 = preds["V5A_common_sample_comparator"].reset_index(drop=True)
    p1 = preds["V6A_plus_ordinary_A50_preauction_closure"].reset_index(drop=True)
    if not p0["trading_day"].equals(p1["trading_day"]):
        raise AssertionError("forensic prediction alignment mismatch")

    hold_features = df.loc[
        df["trading_day"].isin(p1["trading_day"]),
        [
            "trading_day",
            "holiday_reopen",
            "a50_ordinary_preauction_closure_return",
            "us_nasdaq",
            "us_vix_chg",
            "us_nasdaq_closure_extra",
            "us_vix_closure_extra",
            "hkma_usdcny_closure_return",
            "prev_gap",
            "r1",
            "r20",
            "rvol20",
        ],
    ].copy().sort_values("trading_day").reset_index(drop=True)
    diag = p0[["trading_day", "y", "pred"]].rename(columns={"pred": "comparator_pred"}).merge(
        p1[["trading_day", "pred"]].rename(columns={"pred": "candidate_pred"}),
        on="trading_day",
        validate="one_to_one",
    ).merge(hold_features, on="trading_day", validate="one_to_one")
    if len(diag) != len(p1):
        raise AssertionError("forensic feature join changed fixed holdout rows")

    ordinary = pd.to_numeric(diag["holiday_reopen"], errors="coerce").fillna(0).eq(0)
    od = diag.loc[ordinary].copy().reset_index(drop=True)
    f = pd.to_numeric(od["a50_ordinary_preauction_closure_return"], errors="raise")
    y = pd.to_numeric(od["y"], errors="raise")
    residual = y - pd.to_numeric(od["comparator_pred"], errors="raise")
    direct_sign_hit = float(np.mean((f >= 0).to_numpy() == (y >= 0).to_numpy()))

    alignment = {
        "same_row_corr_feature_target": corr(f, y),
        "lead_one_row_corr_feature_t_target_t_plus_1": corr(f.iloc[:-1], y.shift(-1).iloc[:-1]),
        "lag_one_row_corr_feature_t_target_t_minus_1": corr(f.iloc[1:], y.shift(1).iloc[1:]),
        "corr_feature_comparator_residual": corr(f, residual),
        "direct_feature_target_sign_hit": direct_sign_hit,
        "ordinary_fixed_holdout_n": int(len(od)),
    }

    od["sse_improvement"] = (
        (od["y"] - od["comparator_pred"]) ** 2
        - (od["y"] - od["candidate_pred"]) ** 2
    )
    ranked_pos = od.loc[od["sse_improvement"] > 0].sort_values("sse_improvement", ascending=False).copy()
    pos_sum = float(ranked_pos["sse_improvement"].sum())
    neg_sum = float(od.loc[od["sse_improvement"] < 0, "sse_improvement"].sum())
    total = float(od["sse_improvement"].sum())

    def top_share(k: int) -> float:
        if pos_sum <= 0:
            return float("nan")
        return float(ranked_pos.head(k)["sse_improvement"].sum() / pos_sum)

    def remaining_after_top(k: int) -> float:
        return float(total - ranked_pos.head(k)["sse_improvement"].sum())

    concentration = {
        "fixed_prediction_total_ordinary_sse_improvement": total,
        "positive_row_count": int((od["sse_improvement"] > 0).sum()),
        "negative_row_count": int((od["sse_improvement"] < 0).sum()),
        "zero_row_count": int((od["sse_improvement"] == 0).sum()),
        "positive_sse_improvement_sum": pos_sum,
        "negative_sse_improvement_sum": neg_sum,
        "top1_share_of_positive_gain": top_share(1),
        "top5_share_of_positive_gain": top_share(5),
        "top10_share_of_positive_gain": top_share(10),
        "remaining_total_improvement_after_removing_top1_positive_row": remaining_after_top(1),
        "remaining_total_improvement_after_removing_top5_positive_rows": remaining_after_top(5),
        "remaining_total_improvement_after_removing_top10_positive_rows": remaining_after_top(10),
        "top10_positive_rows": [
            {
                "trading_day": str(r["trading_day"].date()),
                "target_gap": float(r["y"]),
                "a50_return": float(r["a50_ordinary_preauction_closure_return"]),
                "sse_improvement": float(r["sse_improvement"]),
            }
            for _, r in ranked_pos.head(10).iterrows()
        ],
    }

    redundancy_features = [
        "us_nasdaq",
        "us_vix_chg",
        "us_nasdaq_closure_extra",
        "us_vix_closure_extra",
        "hkma_usdcny_closure_return",
        "prev_gap",
        "r1",
        "r20",
        "rvol20",
    ]
    correlations = {
        name: corr(f, pd.to_numeric(od[name], errors="coerce"))
        for name in redundancy_features
    }
    finite_corr = {k: v for k, v in correlations.items() if np.isfinite(v)}
    max_abs_name = max(finite_corr, key=lambda k: abs(finite_corr[k])) if finite_corr else None

    c0coef = metrics["V5A_common_sample_comparator"]["standardized_coefficients"]
    c1coef = metrics["V6A_plus_ordinary_A50_preauction_closure"]["standardized_coefficients"]
    flips = []
    for name in sorted(set(c0coef) & set(c1coef)):
        if sign(float(c0coef[name])) != sign(float(c1coef[name])):
            flips.append({
                "feature": name,
                "comparator_coefficient": float(c0coef[name]),
                "candidate_coefficient": float(c1coef[name]),
            })
    redundancy = {
        "correlation_with_existing_features_on_fixed_ordinary_holdout": correlations,
        "max_absolute_existing_feature_correlation": {
            "feature": max_abs_name,
            "correlation": finite_corr.get(max_abs_name) if max_abs_name is not None else None,
        },
        "coefficient_sign_flips_comparator_to_candidate": flips,
    }

    ordinary_ep = pd.read_parquet(ORDINARY_PATH).copy()
    ordinary_ep["trading_day"] = pd.to_datetime(ordinary_ep["trading_day"], errors="raise").dt.normalize()
    selected_ep = ordinary_ep.loc[ordinary_ep["trading_day"].isin(od["trading_day"])].copy()
    if len(selected_ep) != len(od):
        raise AssertionError("fixed ordinary holdout endpoint count mismatch")
    start_time = pd.to_numeric(selected_ep["start_time"], errors="raise").astype(int)
    end_time = pd.to_numeric(selected_ep["target_end_time"], errors="raise").astype(int)
    if (start_time > 150000).any() or (end_time >= 91500).any():
        raise AssertionError("causal clock invalidated in forensic audit")
    returns = pd.to_numeric(selected_ep["a50_ordinary_preauction_closure_return"], errors="raise")
    causal_clock = {
        "fixed_holdout_endpoint_rows": int(len(selected_ep)),
        "start_after_150000_count": int((start_time > 150000).sum()),
        "target_at_or_after_091500_count": int((end_time >= 91500).sum()),
        "target_end_time_min": int(end_time.min()),
        "target_end_time_median": float(end_time.median()),
        "target_end_time_max": int(end_time.max()),
        "target_end_exact_091459_count": int((end_time == 91459).sum()),
        "a50_return_quantiles": {
            str(q): float(returns.quantile(q))
            for q in [0.0, 0.01, 0.05, 0.5, 0.95, 0.99, 1.0]
        },
        "max_absolute_a50_return": float(returns.abs().max()),
    }

    report = {
        "schema_id": "overnight_open_global_spillover_v6_daily_a50_forensics@1.0",
        "role": "post-hoc nonselection fixed-candidate diagnostic",
        "plan": str(PLAN_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "fresh_oos": False},
        "common_sample": common_stats,
        "replayed_metrics": metrics,
        "causal_clock": causal_clock,
        "incremental_information": alignment,
        "concentration": concentration,
        "redundancy": redundancy,
        "authority": {
            "candidate_reselection": False,
            "baseline_replacement": False,
            "fresh_oos": False,
            "production": False,
            "registry_mutation": False,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
