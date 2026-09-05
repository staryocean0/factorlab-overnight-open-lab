#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_global_spillover_v3_complete_clock as v3
import research_global_spillover_v4_cnh as v4

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/governance/baseline_receipt.json"
PREREG_PATH = ROOT / "docs/governance/global_spillover_v6_daily_a50_preregistration.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
HKMA_PATH = ROOT / "data/development/hkma_usdcny_cross.parquet"
HOLIDAY_A50_PATH = ROOT / "data/development/sgx_a50_holiday_endpoints.parquet"
ORDINARY_A50_PATH = ROOT / "data/development/sgx_a50_ordinary_preauction_endpoints.parquet"
ORDINARY_MANIFEST_PATH = ROOT / "docs/governance/external_sgx_a50_ordinary_preauction_2015_2020_manifest.json"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v6_daily_a50_results.json"


def compare_predictions(a: pd.DataFrame, b: pd.DataFrame, mask: pd.Series) -> dict:
    x = a.loc[mask].reset_index(drop=True)
    yb = b.loc[mask].reset_index(drop=True)
    if not x["trading_day"].equals(yb["trading_day"]):
        raise AssertionError("v6 subset prediction alignment mismatch")
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
    panel = pd.read_parquet(PANEL_PATH).copy().sort_values("trading_day").reset_index(drop=True)
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    df = v3.add_complete_clock_features(panel, v3._load_us())
    hkma = pd.read_parquet(HKMA_PATH)
    df = v4.add_hkma_closure_return(df, hkma)

    holiday_a50 = pd.read_parquet(HOLIDAY_A50_PATH).copy()
    holiday_a50["trading_day"] = pd.to_datetime(holiday_a50["trading_day"], errors="raise").dt.normalize()
    if holiday_a50["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 frozen holiday A50 row detected")
    h = holiday_a50[["trading_day", "a50_holiday_closure_return", "a50_holiday_preopen_return", "target_end_time"]].rename(columns={"target_end_time": "a50_holiday_target_end_time"})
    df = df.merge(h, on="trading_day", how="left", validate="one_to_one")

    ordinary_a50 = pd.read_parquet(ORDINARY_A50_PATH).copy()
    ordinary_a50["trading_day"] = pd.to_datetime(ordinary_a50["trading_day"], errors="raise").dt.normalize()
    if ordinary_a50["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 ordinary A50 row detected")
    o = ordinary_a50[["trading_day", "a50_ordinary_preauction_closure_return", "target_end_time", "contract"]].rename(columns={"target_end_time": "a50_ordinary_target_end_time", "contract": "a50_ordinary_contract"})
    df = df.merge(o, on="trading_day", how="left", validate="one_to_one")

    holiday = pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    holiday_available = holiday & df["a50_holiday_closure_return"].notna() & df["a50_holiday_preopen_return"].notna()
    ordinary_available = (~holiday) & df["a50_ordinary_preauction_closure_return"].notna()
    if df.loc[holiday_available, "a50_holiday_target_end_time"].astype(str).ge("092500").any():
        raise AssertionError("frozen holiday A50 target endpoint at or after 09:25")
    if df.loc[ordinary_available, "a50_ordinary_target_end_time"].astype(str).str.zfill(6).ge("091500").any():
        raise AssertionError("ordinary A50 target endpoint at or after 09:15")
    df.loc[~holiday, "a50_holiday_closure_return"] = 0.0
    df.loc[holiday, "a50_ordinary_preauction_closure_return"] = 0.0
    common = holiday_available | ordinary_available

    train_all = df["trading_day"].le(pd.Timestamp("2018-12-31"))
    hold_all = df["trading_day"].between(pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31"))
    train_coverage = float((common & train_all).sum() / train_all.sum())
    hold_coverage = float((common & hold_all).sum() / hold_all.sum())
    if train_coverage < 0.9 or hold_coverage < 0.9:
        raise AssertionError(("v6 common-row coverage gate failed", train_coverage, hold_coverage))

    stats = {
        "all_rows": int(len(df)),
        "common_rows": int(common.sum()),
        "train_rows_total": int(train_all.sum()),
        "train_rows_common": int((common & train_all).sum()),
        "train_common_coverage": train_coverage,
        "holdout_rows_total": int(hold_all.sum()),
        "holdout_rows_common": int((common & hold_all).sum()),
        "holdout_common_coverage": hold_coverage,
        "holiday_rows_total": int(holiday.sum()),
        "holiday_rows_common": int(holiday_available.sum()),
        "ordinary_rows_total": int((~holiday).sum()),
        "ordinary_rows_common": int(ordinary_available.sum()),
    }
    return df.loc[common].copy().reset_index(drop=True), stats


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text())
    if prereg["status"] != "result_free_before_daily_SGX_A50_bulk_extraction_and_v6_model_execution":
        raise AssertionError("v6 preregistration status drift")
    if prereg["multiplicity"]["new_selectable_candidates"] != 1:
        raise AssertionError("v6 selectable candidate count drift")
    ordinary_manifest = json.loads(ORDINARY_MANIFEST_PATH.read_text())
    guards = ordinary_manifest["guards"]
    if guards["post_2020_rows"] != 0 or guards["target_ticks_at_or_after_091500"] != 0 or guards["settlement_S_used_as_trade"]:
        raise AssertionError("ordinary A50 external manifest violates frozen guards")

    baseline = json.loads(BASELINE_PATH.read_text())
    df, common_stats = build_frame()
    v4_features = list(baseline["features"]) + ["us_nasdaq_closure_extra", "us_vix_closure_extra", "hkma_usdcny_closure_return"]
    feature_sets = {
        "V5A_common_sample_comparator": v4_features + ["a50_holiday_closure_return"],
        "V6A_plus_ordinary_A50_preauction_closure": v4_features + ["a50_holiday_closure_return", "a50_ordinary_preauction_closure_return"],
    }
    if list(feature_sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v6 attempt family differs from preregistration")

    metrics: dict[str, dict] = {}
    preds: dict[str, pd.DataFrame] = {}
    for cid, features in feature_sets.items():
        metrics[cid], preds[cid] = v3._fit_predict(df, features)
    p0 = preds["V5A_common_sample_comparator"].reset_index(drop=True)
    p1 = preds["V6A_plus_ordinary_A50_preauction_closure"].reset_index(drop=True)
    if not p0["trading_day"].equals(p1["trading_day"]):
        raise AssertionError("v6 candidates do not share identical holdout rows")

    holiday_mask = pd.to_numeric(p0["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    ordinary_mask = ~holiday_mask
    subsets = {
        "ordinary": compare_predictions(p0, p1, ordinary_mask),
        "holiday": compare_predictions(p0, p1, holiday_mask),
        "by_year": {},
        "by_quarter": {},
    }
    for year in [2019, 2020]:
        m = p0["trading_day"].dt.year.eq(year)
        subsets["by_year"][str(year)] = compare_predictions(p0, p1, m)
    quarter_labels = p0["trading_day"].dt.to_period("Q").astype(str)
    for q in sorted(quarter_labels.unique()):
        subsets["by_quarter"][q] = compare_predictions(p0, p1, quarter_labels.eq(q))
    if len(subsets["by_quarter"]) != 8:
        raise AssertionError(("expected exactly eight consumed-holdout quarters", sorted(subsets["by_quarter"])))

    c0 = metrics["V5A_common_sample_comparator"]
    c1 = metrics["V6A_plus_ordinary_A50_preauction_closure"]
    new_coef = float(c1["standardized_coefficients"]["a50_ordinary_preauction_closure_return"])
    annual_sse_ok = all(subsets["by_year"][str(y)]["sse_improvement"] >= -1e-12 for y in [2019, 2020])
    q_improvements = np.array([x["sse_improvement"] for x in subsets["by_quarter"].values()], dtype=float)
    quarter_nonnegative = int(np.sum(q_improvements >= -1e-12))
    progression_conditions = {
        "r2_improves": bool(c1["holdout_r2"] > c0["holdout_r2"]),
        "sse_improves": bool(c1["holdout_sse"] < c0["holdout_sse"]),
        "ic_improves": bool(c1["holdout_ic"] > c0["holdout_ic"]),
        "sign_within_one_point": bool(c1["holdout_sign_hit"] >= c0["holdout_sign_hit"] - 0.01),
        "economic_sign_positive": bool(new_coef > 0),
        "ordinary_sse_improves": bool(subsets["ordinary"]["sse_improvement"] > 0),
        "ordinary_ic_not_worse": bool(subsets["ordinary"]["candidate_ic"] >= subsets["ordinary"]["comparator_ic"]),
        "both_years_sse_not_worse": bool(annual_sse_ok),
        "median_quarterly_sse_improvement_positive": bool(float(np.median(q_improvements)) > 0),
        "at_least_five_of_eight_quarters_nonnegative_sse": bool(quarter_nonnegative >= 5),
        "holiday_sse_preserved": bool(subsets["holiday"]["sse_improvement"] >= -1e-12),
    }
    progression = bool(all(progression_conditions.values()))
    for m in metrics.values():
        m["delta_r2_vs_common_v5a"] = float(m["holdout_r2"] - c0["holdout_r2"])
        m["delta_ic_vs_common_v5a"] = float(m["holdout_ic"] - c0["holdout_ic"])
        m["sse_improvement_vs_common_v5a"] = float(c0["holdout_sse"] - m["holdout_sse"])
        m["sign_hit_delta_vs_common_v5a"] = float(m["holdout_sign_hit"] - c0["holdout_sign_hit"])

    report = {
        "schema_id": "overnight_open_global_spillover_v6_daily_a50_results@1.0",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "external_manifest": str(ORDINARY_MANIFEST_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_repeat_audit_not_fresh", "fresh_oos": False},
        "common_sample": common_stats,
        "candidates": metrics,
        "subsets": subsets,
        "quarterly_summary": {
            "median_sse_improvement": float(np.median(q_improvements)),
            "nonnegative_sse_improvement_quarters": quarter_nonnegative,
            "quarter_count": 8,
        },
        "adjudication": {
            "progression_conditions": progression_conditions,
            "progression_rule_pass": progression,
            "selected_progression_candidate": "V6A_plus_ordinary_A50_preauction_closure" if progression else None,
            "new_feature_standardized_coefficient": new_coef,
            "R2_aspiration_25_35_used_for_selection": False,
            "scientific_status": "ordinary_A50_preauction_price_discovery_progression_material" if progression else "ordinary_A50_increment_not_supported_under_frozen_phase6_gate",
            "baseline_replacement": False,
            "fresh_oos": False,
        },
        "authority": {"production": False, "registry_mutation": False, "runtime_routing": False, "merge_main": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
