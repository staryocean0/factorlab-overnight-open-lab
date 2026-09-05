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
PREREG_PATH = ROOT / "docs/governance/global_spillover_v5_a50_preregistration.json"
A50_MANIFEST_PATH = ROOT / "docs/governance/external_sgx_a50_holiday_2015_2020_manifest.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
HKMA_PATH = ROOT / "data/development/hkma_usdcny_cross.parquet"
A50_PATH = ROOT / "data/development/sgx_a50_holiday_endpoints.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v5_a50_results.json"


def subset_compare(c0: pd.DataFrame, cx: pd.DataFrame, mask: pd.Series) -> dict:
    a = c0.loc[mask].reset_index(drop=True)
    b = cx.loc[mask].reset_index(drop=True)
    if not a["trading_day"].equals(b["trading_day"]):
        raise AssertionError("v5 prediction subset misaligned")
    y = a["y"].to_numpy(dtype=float)
    p0 = a["pred"].to_numpy(dtype=float)
    px = b["pred"].to_numpy(dtype=float)
    return {
        "n": int(len(a)),
        "comparator_ic": v3._corr(y, p0),
        "candidate_ic": v3._corr(y, px),
        "delta_ic": float(v3._corr(y, px) - v3._corr(y, p0)) if len(a) >= 3 else float("nan"),
        "comparator_sign_hit": float(np.mean((p0 >= 0) == (y >= 0))) if len(a) else float("nan"),
        "candidate_sign_hit": float(np.mean((px >= 0) == (y >= 0))) if len(a) else float("nan"),
        "sse_improvement": float(np.sum((y - p0) ** 2) - np.sum((y - px) ** 2)),
    }


def build_research_frame() -> tuple[pd.DataFrame, dict]:
    manifest = json.loads(A50_MANIFEST_PATH.read_text())
    cov = manifest["coverage"]
    if float(cov["train_event_coverage"]) < 0.8:
        raise AssertionError(("A50 train coverage gate failed", cov))
    if int(cov["holdout_event_usable"]) < 10:
        raise AssertionError(("A50 holdout count gate failed", cov))

    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    df = v3.add_complete_clock_features(panel, v3._load_us())
    fx = pd.read_parquet(HKMA_PATH)
    df = v4.add_hkma_closure_return(df, fx)

    a50 = pd.read_parquet(A50_PATH).copy()
    a50["trading_day"] = pd.to_datetime(a50["trading_day"], errors="raise").dt.normalize()
    if a50["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 A50 endpoint row detected")
    use = a50[["trading_day", "a50_holiday_closure_return", "a50_holiday_preopen_return", "contract", "target_end_time"]].copy()
    df = df.merge(use, on="trading_day", how="left", validate="one_to_one")
    holiday = pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0) != 0
    df.loc[~holiday, "a50_holiday_closure_return"] = 0.0
    df.loc[~holiday, "a50_holiday_preopen_return"] = 0.0
    # Missing holiday records stay missing: there is no mid-window contract switch or imputation.
    if df.loc[holiday & df["a50_holiday_closure_return"].notna(), "target_end_time"].astype(str).ge("092500").any():
        raise AssertionError("A50 target endpoint violates 09:24:59 cutoff")
    return df, manifest


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text())
    if prereg["status"] != "result_free_before_bulk_SGX_A50_extraction_and_v5_execution":
        raise AssertionError("v5 was not frozen result-free")
    baseline = json.loads(BASELINE_PATH.read_text())
    df, a50_manifest = build_research_frame()

    base = list(baseline["features"])
    v4_features = base + ["us_nasdaq_closure_extra", "us_vix_closure_extra", "hkma_usdcny_closure_return"]
    sets = {
        "V4_US_HKMA_comparator": v4_features,
        "V5A_plus_A50_closure": v4_features + ["a50_holiday_closure_return"],
        "V5B_plus_A50_closure_and_preopen": v4_features + ["a50_holiday_closure_return", "a50_holiday_preopen_return"],
    }
    if list(sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v5 attempt family differs from preregistration")

    metrics: dict[str, dict] = {}
    preds: dict[str, pd.DataFrame] = {}
    for cid, features in sets.items():
        metrics[cid], preds[cid] = v3._fit_predict(df, features)

    v4m = metrics["V4_US_HKMA_comparator"]
    if abs(v4m["holdout_ic"] - 0.527052181310477) > 1e-9:
        raise AssertionError(("v4 comparator drift", v4m["holdout_ic"]))
    if abs(v4m["holdout_sse"] - 0.02747801591136969) > 1e-12:
        raise AssertionError(("v4 SSE drift", v4m["holdout_sse"]))

    p4 = preds["V4_US_HKMA_comparator"].reset_index(drop=True)
    p5a = preds["V5A_plus_A50_closure"].reset_index(drop=True)
    p5b = preds["V5B_plus_A50_closure_and_preopen"].reset_index(drop=True)
    if not p4["trading_day"].equals(p5a["trading_day"]) or not p4["trading_day"].equals(p5b["trading_day"]):
        raise AssertionError("A50 coverage caused unequal holdout rows; v5 cannot be adjudicated fairly")

    holiday = pd.to_numeric(p4["holiday_reopen"], errors="coerce").fillna(0) != 0
    by_year = {}
    for year in [2019, 2020]:
        mask = p4["trading_day"].dt.year == year
        by_year[str(year)] = {
            "V5A_vs_V4": subset_compare(p4, p5a, mask),
            "V5B_vs_V5A": subset_compare(p5a, p5b, mask),
        }

    subsets = {
        "holiday": {
            "V5A_vs_V4": subset_compare(p4, p5a, holiday),
            "V5B_vs_V5A": subset_compare(p5a, p5b, holiday),
        },
        "by_year": by_year,
    }

    v5a = metrics["V5A_plus_A50_closure"]
    v5b = metrics["V5B_plus_A50_closure_and_preopen"]
    pass_a = (
        v5a["holdout_ic"] > v4m["holdout_ic"]
        and v5a["holdout_sse"] < v4m["holdout_sse"]
        and subsets["holiday"]["V5A_vs_V4"]["sse_improvement"] > 0
        and v5a["holdout_sign_hit"] >= v4m["holdout_sign_hit"] - 0.01
    )
    pass_b = (
        v5b["holdout_ic"] > v5a["holdout_ic"]
        and v5b["holdout_sse"] < v5a["holdout_sse"]
        and subsets["holiday"]["V5B_vs_V5A"]["sse_improvement"] > 0
        and v5b["holdout_sign_hit"] >= v5a["holdout_sign_hit"] - 0.01
    )
    selected = "V5B_plus_A50_closure_and_preopen" if pass_a and pass_b else ("V5A_plus_A50_closure" if pass_a else None)

    for cid, m in metrics.items():
        m["delta_ic_vs_v4"] = float(m["holdout_ic"] - v4m["holdout_ic"])
        m["sse_improvement_vs_v4"] = float(v4m["holdout_sse"] - m["holdout_sse"])

    event_predictions = []
    for i in np.flatnonzero(holiday.to_numpy()):
        event_predictions.append({
            "trading_day": str(p4.loc[i, "trading_day"].date()),
            "y": float(p4.loc[i, "y"]),
            "V4_pred": float(p4.loc[i, "pred"]),
            "V5A_pred": float(p5a.loc[i, "pred"]),
            "V5B_pred": float(p5b.loc[i, "pred"]),
        })

    report = {
        "schema_id": "overnight_open_global_spillover_v5_a50_results@1.0",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "external_manifest": str(A50_MANIFEST_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_internal"},
        "coverage": a50_manifest["coverage"],
        "candidates": metrics,
        "subsets": subsets,
        "event_predictions": event_predictions,
        "adjudication": {
            "V5A_progression_rule_pass": bool(pass_a),
            "V5B_progression_over_V5A_pass": bool(pass_b),
            "selected_progression_candidate": selected,
            "fresh_oos": False,
            "baseline_replacement": False,
            "scientific_status": "A50_progression_material_waiting_fixed_prediction_LOO_and_unseen_controller" if selected else "A50_increment_not_supported_on_consumed_holdout",
        },
        "authority": {"holiday_runtime_routing": False, "production": False, "registry_mutation": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
