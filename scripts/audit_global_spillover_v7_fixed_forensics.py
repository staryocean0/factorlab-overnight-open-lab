#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_global_spillover_v3_complete_clock as v3
import research_global_spillover_v6_daily_a50 as v6

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/development/shfe_cu_rb_night_endpoints.parquet"
PLAN_PATH = ROOT / "docs/governance/global_spillover_v7_forensic_diagnostic_plan.json"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v7_fixed_forensics.json"
RB_Q0 = pd.Timestamp("2016-04-26")
RB_Q1 = pd.Timestamp("2016-05-03")


def corr(a: np.ndarray, b: np.ndarray) -> float:
    return v3._corr(np.asarray(a, dtype=float), np.asarray(b, dtype=float))


def causal_clock_check(data: pd.DataFrame, dates: set[pd.Timestamp]) -> dict:
    d = data.loc[data["trading_day"].isin(dates)].copy()
    if len(d) != len(dates):
        raise AssertionError(("fixed holdout dates missing from domestic data", len(d), len(dates)))
    d["previous_china_day"] = pd.to_datetime(d["previous_china_day"]).dt.normalize()
    d["cu_night_end_datetime"] = pd.to_datetime(d["cu_night_end_datetime"], errors="raise")
    d["rb_night_end_datetime"] = pd.to_datetime(d["rb_night_end_datetime"], errors="raise")
    bad_cu = []
    bad_rb = []
    for _, r in d.iterrows():
        p = pd.Timestamp(r["previous_china_day"]).normalize()
        cu = pd.Timestamp(r["cu_night_end_datetime"])
        rb = pd.Timestamp(r["rb_night_end_datetime"])
        cu_ok = (
            (cu.normalize() == p and cu.strftime("%H%M%S") >= "210000")
            or (cu.normalize() == p + pd.Timedelta(days=1) and cu.strftime("%H%M%S") <= "010000")
        )
        if not cu_ok:
            bad_cu.append((str(r["trading_day"]), str(p), str(cu)))
        if RB_Q0 <= p <= RB_Q1:
            rb_ok = False
        elif p < RB_Q0:
            rb_ok = (
                (rb.normalize() == p and rb.strftime("%H%M%S") >= "210000")
                or (rb.normalize() == p + pd.Timedelta(days=1) and rb.strftime("%H%M%S") <= "010000")
            )
        else:
            rb_ok = rb.normalize() == p and "210000" <= rb.strftime("%H%M%S") <= "230000"
        if not rb_ok:
            bad_rb.append((str(r["trading_day"]), str(p), str(rb)))
    return {
        "fixed_holdout_rows": int(len(d)),
        "cu_bad_clock_rows": len(bad_cu),
        "rb_bad_clock_rows": len(bad_rb),
        "cu_min_positive_night_bars": int(pd.to_numeric(d["cu_night_positive_volume_bar_count"]).min()),
        "rb_min_positive_night_bars": int(pd.to_numeric(d["rb_night_positive_volume_bar_count"]).min()),
        "cu_night_end_min": str(d["cu_night_end_datetime"].min()),
        "cu_night_end_max": str(d["cu_night_end_datetime"].max()),
        "rb_night_end_min": str(d["rb_night_end_datetime"].min()),
        "rb_night_end_max": str(d["rb_night_end_datetime"].max()),
        "all_clock_checks_pass": bool(not bad_cu and not bad_rb),
        "bad_cu_examples": bad_cu[:5],
        "bad_rb_examples": bad_rb[:5],
    }


def concentration(frame: pd.DataFrame) -> dict:
    imp = frame["sse_improvement"].to_numpy(dtype=float)
    positive = np.sort(imp[imp > 0])[::-1]
    total_positive = float(positive.sum())
    def share(n: int) -> float:
        if total_positive <= 0:
            return float("nan")
        return float(positive[:n].sum() / total_positive)
    total = float(imp.sum())
    return {
        "positive_row_count": int(np.sum(imp > 0)),
        "negative_row_count": int(np.sum(imp < 0)),
        "zero_row_count": int(np.sum(imp == 0)),
        "total_fixed_prediction_sse_improvement": total,
        "top1_share_of_positive_gain": share(1),
        "top5_share_of_positive_gain": share(5),
        "top10_share_of_positive_gain": share(10),
        "remaining_total_improvement_after_removing_top1_positive_row": float(total - positive[:1].sum()),
        "remaining_total_improvement_after_removing_top5_positive_rows": float(total - positive[:5].sum()),
        "remaining_total_improvement_after_removing_top10_positive_rows": float(total - positive[:10].sum()),
    }


def redundancy(formal: dict, fixed: pd.DataFrame) -> dict:
    v6_df, _ = v6.build_frame()
    v6_df = v6_df.copy()
    v6_df["trading_day"] = pd.to_datetime(v6_df["trading_day"]).dt.normalize()
    comparator = formal["candidates"]["V6A_common_sample_comparator"]
    candidate = formal["candidates"]["V7A_plus_domestic_night_cyclical"]
    existing_features = list(comparator["standardized_coefficients"])
    merged = fixed[["trading_day", "domestic_night_cyclical_return"]].merge(
        v6_df[["trading_day"] + existing_features], on="trading_day", how="left", validate="one_to_one"
    )
    corrs = {}
    for feature in existing_features:
        a = pd.to_numeric(merged["domestic_night_cyclical_return"], errors="coerce")
        b = pd.to_numeric(merged[feature], errors="coerce")
        mask = a.notna() & b.notna()
        corrs[feature] = corr(a[mask].to_numpy(), b[mask].to_numpy()) if int(mask.sum()) >= 3 else float("nan")
    finite = {k: v for k, v in corrs.items() if np.isfinite(v)}
    max_feature = max(finite, key=lambda k: abs(finite[k])) if finite else None
    flips = []
    shifts = {}
    for feature, c0 in comparator["standardized_coefficients"].items():
        c1 = candidate["standardized_coefficients"][feature]
        shifts[feature] = float(c1 - c0)
        if c0 != 0 and c1 != 0 and np.sign(c0) != np.sign(c1):
            flips.append(feature)
    return {
        "existing_feature_correlations": corrs,
        "max_absolute_existing_feature_correlation": {
            "feature": max_feature,
            "correlation": finite.get(max_feature) if max_feature is not None else None,
        },
        "shared_feature_coefficient_shifts": shifts,
        "shared_feature_coefficient_sign_flips": flips,
        "domestic_composite_standardized_coefficient": float(candidate["standardized_coefficients"]["domestic_night_cyclical_return"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal-result", required=True)
    args = ap.parse_args()
    formal_path = Path(args.formal_result)
    if not formal_path.is_absolute():
        formal_path = ROOT / formal_path
    plan = json.loads(PLAN_PATH.read_text())
    formal = json.loads(formal_path.read_text())
    if plan["status"] != "result_free_before_formal_v7_model_execution":
        raise AssertionError("v7 forensic plan was not result-free")
    if formal["schema_id"] != "overnight_open_global_spillover_v7_domestic_night_results@1.1":
        raise AssertionError("unexpected formal v7 schema")
    rows = formal.get("fixed_holdout_predictions", [])
    if not rows:
        raise AssertionError("formal v7 result lacks fixed holdout predictions")
    fixed = pd.DataFrame(rows)
    fixed["trading_day"] = pd.to_datetime(fixed["trading_day"], errors="raise").dt.normalize()
    fixed = fixed.sort_values("trading_day").reset_index(drop=True)
    if len(fixed) != int(formal["candidates"]["V6A_common_sample_comparator"]["n_holdout"]):
        raise AssertionError("fixed prediction count differs from formal holdout n")

    f = fixed["domestic_night_cyclical_return"].to_numpy(dtype=float)
    y = fixed["y"].to_numpy(dtype=float)
    time_shift = {
        "same_row_corr_feature_t_target_t": corr(f, y),
        "lead_one_row_corr_feature_t_target_t_plus_1": corr(f[:-1], y[1:]),
        "lag_one_row_corr_feature_t_target_t_minus_1": corr(f[1:], y[:-1]),
    }
    residual = y - fixed["V6_pred"].to_numpy(dtype=float)
    incremental = {
        "corr_composite_with_V6_fixed_residual": corr(f, residual),
        "direct_composite_sign_hit": float(np.mean((f >= 0) == (y >= 0))),
        "CU_target_corr": corr(fixed["cu_night_return"].to_numpy(dtype=float), y),
        "RB_target_corr": corr(fixed["rb_night_return"].to_numpy(dtype=float), y),
        "CU_RB_corr": corr(fixed["cu_night_return"].to_numpy(dtype=float), fixed["rb_night_return"].to_numpy(dtype=float)),
    }

    data = pd.read_parquet(DATA_PATH).copy()
    data["trading_day"] = pd.to_datetime(data["trading_day"], errors="raise").dt.normalize()
    report = {
        "schema_id": "overnight_open_global_spillover_v7_fixed_forensics@1.0",
        "forensic_plan": str(PLAN_PATH.relative_to(ROOT)),
        "formal_result_source": str(formal_path),
        "formal_progression_rule_pass": bool(formal["adjudication"]["progression_rule_pass"]),
        "refit_or_reselection_performed": False,
        "fixed_prediction_rows": int(len(fixed)),
        "causal_clock": causal_clock_check(data, set(fixed["trading_day"])),
        "time_shift_placebo": time_shift,
        "incremental_information": incremental,
        "fixed_prediction_concentration": concentration(fixed),
        "redundancy": redundancy(formal, fixed),
        "interpretation": {
            "primary_verdict_unchanged": True,
            "diagnostics_can_promote_failed_v7": False,
            "scientific_read": "If same-row target correlation exists but correlation with V6 fixed residual is near zero and fixed SSE improvement is nonpositive, the domestic-night block is informative in isolation but redundant after the frozen v6 offshore-China/global information set."
        },
        "authority": {
            "candidate_selection": False,
            "fresh_oos": False,
            "baseline_replacement": False,
            "production": False,
            "registry_mutation": False,
            "merge_main": False
        }
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
