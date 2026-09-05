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
PREREG_PATH = ROOT / "docs/governance/global_spillover_v7_domestic_night_preregistration.json"
SCOPE_CORRECTION_PATH = ROOT / "docs/governance/global_spillover_v7_domestic_night_holiday_scope_correction.json"
DOMESTIC_PATH = ROOT / "data/development/shfe_cu_rb_night_endpoints.parquet"
DOMESTIC_MANIFEST_PATH = ROOT / "docs/governance/external_shfe_cu_rb_night_2015_2020_manifest.json"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v7_domestic_night_results.json"


def compare_predictions(a: pd.DataFrame, b: pd.DataFrame, mask: pd.Series) -> dict:
    x = a.loc[mask].reset_index(drop=True)
    yb = b.loc[mask].reset_index(drop=True)
    if not x["trading_day"].equals(yb["trading_day"]):
        raise AssertionError("v7 prediction subset misalignment")
    y = x["y"].to_numpy(dtype=float)
    p0 = x["pred"].to_numpy(dtype=float)
    p1 = yb["pred"].to_numpy(dtype=float)
    sse0 = float(np.sum((y - p0) ** 2))
    sse1 = float(np.sum((y - p1) ** 2))
    return {
        "n": int(len(x)),
        "comparator_ic": v3._corr(y, p0),
        "candidate_ic": v3._corr(y, p1),
        "delta_ic": float(v3._corr(y, p1) - v3._corr(y, p0)) if len(x) >= 3 else float("nan"),
        "comparator_sign_hit": float(np.mean((p0 >= 0) == (y >= 0))) if len(x) else float("nan"),
        "candidate_sign_hit": float(np.mean((p1 >= 0) == (y >= 0))) if len(x) else float("nan"),
        "comparator_sse": sse0,
        "candidate_sse": sse1,
        "sse_improvement": float(sse0 - sse1),
    }


def build_frame() -> tuple[pd.DataFrame, dict]:
    v6_df, v6_stats = v6.build_frame()
    domestic = pd.read_parquet(DOMESTIC_PATH).copy()
    domestic["trading_day"] = pd.to_datetime(domestic["trading_day"], errors="raise").dt.normalize()
    if domestic["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 domestic-night row")
    required = ["trading_day", "domestic_night_cyclical_return", "cu_cu_night_return", "rb_rb_night_return"]
    missing = [c for c in required if c not in domestic.columns]
    if missing:
        raise AssertionError(("domestic-night data missing required columns", missing))
    if domestic["trading_day"].duplicated().any():
        raise AssertionError("duplicate domestic-night target day")

    use = domestic[required].copy()
    df = v6_df.merge(use, on="trading_day", how="left", validate="one_to_one")
    holiday = pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    if df.loc[holiday, "domestic_night_cyclical_return"].notna().any():
        raise AssertionError("domestic-night composite present on holiday_reopen row despite frozen scope correction")
    common = (~holiday) & df["domestic_night_cyclical_return"].notna()
    out = df.loc[common].copy().reset_index(drop=True)
    if out.empty:
        raise AssertionError("v7 common sample empty")

    train_v6_ordinary = (~holiday) & df["trading_day"].le(pd.Timestamp("2018-12-31"))
    hold_v6_ordinary = (~holiday) & df["trading_day"].between(pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31"))
    train_joint = common & df["trading_day"].le(pd.Timestamp("2018-12-31"))
    hold_joint = common & df["trading_day"].between(pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31"))
    stats = {
        "v6_parent_common": v6_stats,
        "v6_ordinary_rows_train": int(train_v6_ordinary.sum()),
        "v6_ordinary_rows_holdout": int(hold_v6_ordinary.sum()),
        "v7_joint_rows_train_before_base_complete_case": int(train_joint.sum()),
        "v7_joint_rows_holdout_before_base_complete_case": int(hold_joint.sum()),
        "joint_coverage_vs_v6_ordinary_train": float(train_joint.sum() / train_v6_ordinary.sum()),
        "joint_coverage_vs_v6_ordinary_holdout": float(hold_joint.sum() / hold_v6_ordinary.sum()),
        "holiday_rows_in_v7_common": int(pd.to_numeric(out["holiday_reopen"], errors="coerce").fillna(0).ne(0).sum()),
    }
    if stats["joint_coverage_vs_v6_ordinary_train"] < 0.80 or stats["joint_coverage_vs_v6_ordinary_holdout"] < 0.80:
        raise AssertionError(("v7 common coverage below frozen 80% gate", stats))
    return out, stats


def component_diagnostics(df: pd.DataFrame, comparator_predictions: pd.DataFrame) -> dict:
    hold = df.loc[df["trading_day"].between(pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31")), [
        "trading_day", "gap", "domestic_night_cyclical_return", "cu_cu_night_return", "rb_rb_night_return"
    ]].copy()
    merged = comparator_predictions[["trading_day", "pred"]].merge(hold, on="trading_day", how="left", validate="one_to_one")
    if merged[["gap", "domestic_night_cyclical_return", "cu_cu_night_return", "rb_rb_night_return"]].isna().any().any():
        raise AssertionError("component diagnostic merge missing values")
    target = merged["gap"].to_numpy(dtype=float)
    residual = target - merged["pred"].to_numpy(dtype=float)
    return {
        "composite_target_corr": v3._corr(merged["domestic_night_cyclical_return"].to_numpy(dtype=float), target),
        "CU_target_corr": v3._corr(merged["cu_cu_night_return"].to_numpy(dtype=float), target),
        "RB_target_corr": v3._corr(merged["rb_rb_night_return"].to_numpy(dtype=float), target),
        "CU_RB_corr": v3._corr(merged["cu_cu_night_return"].to_numpy(dtype=float), merged["rb_rb_night_return"].to_numpy(dtype=float)),
        "composite_comparator_residual_corr": v3._corr(merged["domestic_night_cyclical_return"].to_numpy(dtype=float), residual),
        "direct_composite_sign_hit": float(np.mean((merged["domestic_night_cyclical_return"].to_numpy(dtype=float) >= 0) == (target >= 0))),
    }


def fixed_prediction_rows(df: pd.DataFrame, p0: pd.DataFrame, p1: pd.DataFrame) -> list[dict]:
    detail = df.loc[df["trading_day"].between(pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31")), [
        "trading_day", "gap", "domestic_night_cyclical_return", "cu_cu_night_return", "rb_rb_night_return"
    ]].copy()
    fixed = p0[["trading_day", "pred"]].rename(columns={"pred": "V6_pred"}).merge(
        p1[["trading_day", "pred"]].rename(columns={"pred": "V7_pred"}), on="trading_day", validate="one_to_one"
    ).merge(detail, on="trading_day", validate="one_to_one")
    if fixed.isna().any().any():
        raise AssertionError("fixed-prediction ledger contains missing values")
    fixed["V6_sse"] = (fixed["gap"] - fixed["V6_pred"]) ** 2
    fixed["V7_sse"] = (fixed["gap"] - fixed["V7_pred"]) ** 2
    fixed["sse_improvement"] = fixed["V6_sse"] - fixed["V7_sse"]
    rows = []
    for _, r in fixed.sort_values("trading_day").iterrows():
        rows.append({
            "trading_day": str(pd.Timestamp(r["trading_day"]).date()),
            "y": float(r["gap"]),
            "V6_pred": float(r["V6_pred"]),
            "V7_pred": float(r["V7_pred"]),
            "domestic_night_cyclical_return": float(r["domestic_night_cyclical_return"]),
            "cu_night_return": float(r["cu_cu_night_return"]),
            "rb_night_return": float(r["rb_rb_night_return"]),
            "V6_sse": float(r["V6_sse"]),
            "V7_sse": float(r["V7_sse"]),
            "sse_improvement": float(r["sse_improvement"]),
        })
    return rows


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text())
    correction = json.loads(SCOPE_CORRECTION_PATH.read_text())
    manifest = json.loads(DOMESTIC_MANIFEST_PATH.read_text())
    if prereg["status"] != "result_free_before_bulk_CU_RB_extraction_and_any_v7_target_model_execution":
        raise AssertionError("v7 preregistration status drift")
    if prereg["multiplicity"]["new_selectable_candidates"] != 1:
        raise AssertionError("v7 candidate count drift")
    if correction["status"] != "result_free_before_bulk_CU_RB_extraction_and_any_v7_target_model_execution":
        raise AssertionError("v7 holiday scope correction status drift")
    if manifest["guards"]["post_2020_market_fields_parsed"] != 0 or manifest["guards"]["holiday_rows_in_joint_dataset"] != 0:
        raise AssertionError("domestic-night manifest violates frozen guards")
    if manifest["coverage"]["train_2015_2018"]["coverage"] < 0.80 or manifest["coverage"]["holdout_2019_2020"]["coverage"] < 0.80:
        raise AssertionError("domestic-night external joint coverage gate failed")

    baseline = json.loads(BASELINE_PATH.read_text())
    df, common_stats = build_frame()
    v4_features = list(baseline["features"]) + ["us_nasdaq_closure_extra", "us_vix_closure_extra", "hkma_usdcny_closure_return"]
    v6_features = v4_features + ["a50_holiday_closure_return", "a50_ordinary_preauction_closure_return"]
    feature_sets = {
        "V6A_common_sample_comparator": v6_features,
        "V7A_plus_domestic_night_cyclical": v6_features + ["domestic_night_cyclical_return"],
    }
    if list(feature_sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v7 attempt family differs from preregistration")

    metrics: dict[str, dict] = {}
    predictions: dict[str, pd.DataFrame] = {}
    for cid, features in feature_sets.items():
        metrics[cid], predictions[cid] = v3._fit_predict(df, features)
    p0 = predictions["V6A_common_sample_comparator"].reset_index(drop=True)
    p1 = predictions["V7A_plus_domestic_night_cyclical"].reset_index(drop=True)
    if not p0["trading_day"].equals(p1["trading_day"]):
        raise AssertionError("v7 candidates do not share identical holdout rows")
    if pd.to_numeric(p0["holiday_reopen"], errors="coerce").fillna(0).ne(0).any():
        raise AssertionError("holiday row reached formal v7 adjudication")

    subsets = {"by_year": {}, "by_quarter": {}}
    for year in [2019, 2020]:
        mask = p0["trading_day"].dt.year.eq(year)
        subsets["by_year"][str(year)] = compare_predictions(p0, p1, mask)
    qlabels = p0["trading_day"].dt.to_period("Q").astype(str)
    for q in sorted(qlabels.unique()):
        subsets["by_quarter"][q] = compare_predictions(p0, p1, qlabels.eq(q))
    if len(subsets["by_quarter"]) != 8:
        raise AssertionError(("expected eight 2019-2020 quarters", sorted(subsets["by_quarter"])))

    c0 = metrics["V6A_common_sample_comparator"]
    c1 = metrics["V7A_plus_domestic_night_cyclical"]
    q_improvements = np.array([x["sse_improvement"] for x in subsets["by_quarter"].values()], dtype=float)
    quarter_nonnegative = int(np.sum(q_improvements >= -1e-12))
    annual_sse_ok = all(subsets["by_year"][str(y)]["sse_improvement"] >= -1e-12 for y in [2019, 2020])
    conditions = {
        "r2_improves": bool(c1["holdout_r2"] > c0["holdout_r2"]),
        "sse_improves": bool(c1["holdout_sse"] < c0["holdout_sse"]),
        "ic_improves": bool(c1["holdout_ic"] > c0["holdout_ic"]),
        "sign_within_one_point": bool(c1["holdout_sign_hit"] >= c0["holdout_sign_hit"] - 0.01),
        "both_years_sse_not_worse": bool(annual_sse_ok),
        "quarter_total_sse_improvement_positive": bool(float(q_improvements.sum()) > 0),
        "median_quarterly_sse_improvement_positive": bool(float(np.median(q_improvements)) > 0),
        "at_least_five_of_eight_quarters_nonnegative_sse": bool(quarter_nonnegative >= 5),
    }
    progression = bool(all(conditions.values()))
    for m in metrics.values():
        m["delta_r2_vs_common_v6a"] = float(m["holdout_r2"] - c0["holdout_r2"])
        m["delta_ic_vs_common_v6a"] = float(m["holdout_ic"] - c0["holdout_ic"])
        m["sse_improvement_vs_common_v6a"] = float(c0["holdout_sse"] - m["holdout_sse"])
        m["sign_hit_delta_vs_common_v6a"] = float(m["holdout_sign_hit"] - c0["holdout_sign_hit"])

    diagnostics = component_diagnostics(df, p0)
    fixed_rows = fixed_prediction_rows(df, p0, p1)
    report = {
        "schema_id": "overnight_open_global_spillover_v7_domestic_night_results@1.1",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "holiday_scope_correction": str(SCOPE_CORRECTION_PATH.relative_to(ROOT)),
        "external_manifest": str(DOMESTIC_MANIFEST_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_repeat_audit_not_fresh", "fresh_oos": False},
        "common_sample": common_stats,
        "candidates": metrics,
        "subsets": subsets,
        "quarterly_summary": {
            "quarter_count": 8,
            "nonnegative_sse_improvement_quarters": quarter_nonnegative,
            "median_sse_improvement": float(np.median(q_improvements)),
            "total_sse_improvement": float(q_improvements.sum()),
            "negative_quarters": [q for q, x in subsets["by_quarter"].items() if x["sse_improvement"] < -1e-12],
        },
        "fixed_holdout_predictions": fixed_rows,
        "post_adjudication_nonselection_component_diagnostics": diagnostics,
        "adjudication": {
            "progression_conditions": conditions,
            "progression_rule_pass": progression,
            "selected_progression_candidate": "V7A_plus_domestic_night_cyclical" if progression else None,
            "composite_standardized_coefficient": float(c1["standardized_coefficients"]["domestic_night_cyclical_return"]),
            "coefficient_sign_used_as_gate": False,
            "component_diagnostics_used_for_selection": False,
            "fixed_prediction_ledger_used_for_primary_selection": False,
            "fresh_oos": False,
            "baseline_replacement": False,
            "scientific_status": "domestic_night_cyclical_progression_material_waiting_separate_fallback_and_unseen_confirmation" if progression else "domestic_night_cyclical_increment_not_supported_under_frozen_v7_gate",
        },
        "authority": {"production": False, "registry_mutation": False, "runtime_routing": False, "merge_main": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
