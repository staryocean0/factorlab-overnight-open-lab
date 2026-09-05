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
V6_RECEIPT_PATH = ROOT / "docs/governance/global_spillover_v6_daily_a50_receipt.json"
PREREG_PATH = ROOT / "docs/governance/global_spillover_v8_regime_preregistration.json"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v8_regime_results.json"
INTERACTION = "a50_ordinary_x_rvol20"


def add_interaction(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    a50 = pd.to_numeric(out["a50_ordinary_preauction_closure_return"], errors="raise")
    state = pd.to_numeric(out["rvol20"], errors="raise")
    out[INTERACTION] = a50 * state
    holiday = pd.to_numeric(out["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    if not np.allclose(out.loc[holiday, INTERACTION].to_numpy(dtype=float), 0.0, atol=0.0, rtol=0.0):
        raise AssertionError("v8 interaction must be exactly zero on holiday rows")
    return out


def compare_predictions(a: pd.DataFrame, b: pd.DataFrame, mask: pd.Series) -> dict:
    x = a.loc[mask].reset_index(drop=True)
    yb = b.loc[mask].reset_index(drop=True)
    if not x["trading_day"].equals(yb["trading_day"]):
        raise AssertionError("v8 prediction subset misalignment")
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


def assert_v6_replay(metrics: dict, receipt: dict) -> None:
    sealed = receipt["candidates"]["V6A_plus_ordinary_A50_preauction_closure"]
    if int(metrics["n_train"]) != int(sealed["n_train"]) or int(metrics["n_holdout"]) != int(sealed["n_holdout"]):
        raise AssertionError(("v6 replay sample drift", metrics["n_train"], metrics["n_holdout"], sealed["n_train"], sealed["n_holdout"]))
    checks = {
        "holdout_r2": 1e-12,
        "holdout_ic": 1e-12,
        "holdout_sign_hit": 1e-15,
        "holdout_sse": 1e-15,
    }
    for field, tol in checks.items():
        if abs(float(metrics[field]) - float(sealed[field])) > tol:
            raise AssertionError(("v6 sealed comparator replay drift", field, metrics[field], sealed[field], tol))


def fixed_prediction_rows(df: pd.DataFrame, p0: pd.DataFrame, p1: pd.DataFrame) -> list[dict]:
    detail = df.loc[df["trading_day"].between(pd.Timestamp("2019-01-01"), pd.Timestamp("2020-12-31")), [
        "trading_day", "gap", "holiday_reopen", "a50_ordinary_preauction_closure_return", "rvol20", INTERACTION
    ]].copy()
    fixed = p0[["trading_day", "pred"]].rename(columns={"pred": "V6_pred"}).merge(
        p1[["trading_day", "pred"]].rename(columns={"pred": "V8_pred"}), on="trading_day", validate="one_to_one"
    ).merge(detail, on="trading_day", validate="one_to_one")
    if fixed.isna().any().any():
        raise AssertionError("v8 fixed-prediction ledger contains missing values")
    fixed["V6_sse"] = (fixed["gap"] - fixed["V6_pred"]) ** 2
    fixed["V8_sse"] = (fixed["gap"] - fixed["V8_pred"]) ** 2
    fixed["sse_improvement"] = fixed["V6_sse"] - fixed["V8_sse"]
    rows = []
    for _, r in fixed.sort_values("trading_day").iterrows():
        rows.append({
            "trading_day": str(pd.Timestamp(r["trading_day"]).date()),
            "y": float(r["gap"]),
            "holiday_reopen": float(r["holiday_reopen"]),
            "V6_pred": float(r["V6_pred"]),
            "V8_pred": float(r["V8_pred"]),
            "a50_ordinary_preauction_closure_return": float(r["a50_ordinary_preauction_closure_return"]),
            "rvol20": float(r["rvol20"]),
            INTERACTION: float(r[INTERACTION]),
            "V6_sse": float(r["V6_sse"]),
            "V8_sse": float(r["V8_sse"]),
            "sse_improvement": float(r["sse_improvement"]),
        })
    return rows


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text())
    receipt = json.loads(V6_RECEIPT_PATH.read_text())
    if prereg["status"] != "result_free_before_any_v8_target_model_execution":
        raise AssertionError("v8 preregistration status drift")
    if prereg["multiplicity"]["new_selectable_candidates"] != 1:
        raise AssertionError("v8 selectable candidate count drift")
    if receipt["scientific_status"] != "ordinary_A50_preauction_price_discovery_strong_progression_candidate_waiting_genuinely_unseen_confirmation":
        raise AssertionError("unexpected v6 parent scientific status")

    baseline = json.loads(BASELINE_PATH.read_text())
    df, common_stats = v6.build_frame()
    df = add_interaction(df)
    base = list(baseline["features"])
    v6_features = base + [
        "us_nasdaq_closure_extra",
        "us_vix_closure_extra",
        "hkma_usdcny_closure_return",
        "a50_holiday_closure_return",
        "a50_ordinary_preauction_closure_return",
    ]
    sets = {
        "V6A_frozen_common_sample_comparator": v6_features,
        "V8A_plus_A50_x_rvol20": v6_features + [INTERACTION],
    }
    if list(sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v8 attempt family differs from preregistration")

    metrics: dict[str, dict] = {}
    predictions: dict[str, pd.DataFrame] = {}
    for cid, features in sets.items():
        metrics[cid], predictions[cid] = v3._fit_predict(df, features)
    c0 = metrics["V6A_frozen_common_sample_comparator"]
    c1 = metrics["V8A_plus_A50_x_rvol20"]
    assert_v6_replay(c0, receipt)

    p0 = predictions["V6A_frozen_common_sample_comparator"].reset_index(drop=True)
    p1 = predictions["V8A_plus_A50_x_rvol20"].reset_index(drop=True)
    if not p0["trading_day"].equals(p1["trading_day"]):
        raise AssertionError("v8 candidates do not share identical holdout rows")
    holiday = pd.to_numeric(p0["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    ordinary = ~holiday
    subsets = {
        "ordinary": compare_predictions(p0, p1, ordinary),
        "holiday": compare_predictions(p0, p1, holiday),
        "by_year": {},
        "by_quarter": {},
    }
    for year in [2019, 2020]:
        mask = p0["trading_day"].dt.year.eq(year)
        subsets["by_year"][str(year)] = compare_predictions(p0, p1, mask)
    qlabels = p0["trading_day"].dt.to_period("Q").astype(str)
    for q in sorted(qlabels.unique()):
        subsets["by_quarter"][q] = compare_predictions(p0, p1, qlabels.eq(q))
    if len(subsets["by_quarter"]) != 8:
        raise AssertionError(("expected eight consumed-holdout quarters", sorted(subsets["by_quarter"])))

    q_imp = np.array([x["sse_improvement"] for x in subsets["by_quarter"].values()], dtype=float)
    annual_sse_ok = all(subsets["by_year"][str(y)]["sse_improvement"] >= -1e-12 for y in [2019, 2020])
    quarter_nonnegative = int(np.sum(q_imp >= -1e-12))
    conditions = {
        "r2_improves": bool(c1["holdout_r2"] > c0["holdout_r2"]),
        "sse_improves": bool(c1["holdout_sse"] < c0["holdout_sse"]),
        "ic_improves": bool(c1["holdout_ic"] > c0["holdout_ic"]),
        "sign_within_one_point": bool(c1["holdout_sign_hit"] >= c0["holdout_sign_hit"] - 0.01),
        "ordinary_sse_improves": bool(subsets["ordinary"]["sse_improvement"] > 0),
        "ordinary_ic_not_worse": bool(subsets["ordinary"]["candidate_ic"] >= subsets["ordinary"]["comparator_ic"]),
        "both_years_sse_not_worse": bool(annual_sse_ok),
        "quarter_total_sse_improvement_positive": bool(float(q_imp.sum()) > 0),
        "median_quarterly_sse_improvement_positive": bool(float(np.median(q_imp)) > 0),
        "at_least_five_of_eight_quarters_nonnegative_sse": bool(quarter_nonnegative >= 5),
        "holiday_sse_preserved": bool(subsets["holiday"]["sse_improvement"] >= -1e-12),
    }
    progression = bool(all(conditions.values()))
    for m in metrics.values():
        m["delta_r2_vs_v6"] = float(m["holdout_r2"] - c0["holdout_r2"])
        m["delta_ic_vs_v6"] = float(m["holdout_ic"] - c0["holdout_ic"])
        m["sse_improvement_vs_v6"] = float(c0["holdout_sse"] - m["holdout_sse"])
        m["sign_hit_delta_vs_v6"] = float(m["holdout_sign_hit"] - c0["holdout_sign_hit"])

    report = {
        "schema_id": "overnight_open_global_spillover_v8_regime_results@1.0",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "parent_receipt": str(V6_RECEIPT_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_repeat_audit_not_fresh", "fresh_oos": False},
        "common_sample": common_stats,
        "interaction": {
            "name": INTERACTION,
            "formula": "a50_ordinary_preauction_closure_return * rvol20",
            "holiday_interaction_exact_zero": True,
            "coefficient_sign_used_as_gate": False,
        },
        "candidates": metrics,
        "subsets": subsets,
        "quarterly_summary": {
            "quarter_count": 8,
            "nonnegative_sse_improvement_quarters": quarter_nonnegative,
            "median_sse_improvement": float(np.median(q_imp)),
            "total_sse_improvement": float(q_imp.sum()),
            "negative_quarters": [q for q, x in subsets["by_quarter"].items() if x["sse_improvement"] < -1e-12],
        },
        "fixed_holdout_predictions": fixed_prediction_rows(df, p0, p1),
        "adjudication": {
            "progression_conditions": conditions,
            "progression_rule_pass": progression,
            "selected_progression_candidate": "V8A_plus_A50_x_rvol20" if progression else None,
            "interaction_standardized_coefficient": float(c1["standardized_coefficients"][INTERACTION]),
            "fresh_oos": False,
            "baseline_replacement": False,
            "scientific_status": "continuous_A50_pass_through_regime_progression_material_waiting_fixed_prediction_forensics_and_unseen_confirmation" if progression else "continuous_A50_pass_through_regime_increment_not_supported_under_frozen_v8_gate",
        },
        "authority": {"production": False, "registry_mutation": False, "runtime_routing": False, "merge_main": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
