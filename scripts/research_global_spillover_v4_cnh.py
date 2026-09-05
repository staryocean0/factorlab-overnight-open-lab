#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_global_spillover_v3_complete_clock as v3

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/governance/baseline_receipt.json"
PREREG_PATH = ROOT / "docs/governance/global_spillover_v4_cnh_preregistration.json"
SOURCE_SUB_PATH = ROOT / "docs/governance/global_spillover_v4_hkma_source_substitution.json"
CLOCK_CORR_PATH = ROOT / "docs/governance/global_spillover_v4_hkma_clock_correction.json"
FX_MANIFEST_PATH = ROOT / "docs/governance/external_hkma_usdcny_2014_2020_manifest.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
FX_PATH = ROOT / "data/development/hkma_usdcny_cross.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v4_cnh_results.json"


def add_hkma_closure_return(df: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("trading_day").reset_index(drop=True)
    if "previous_china_day" not in out.columns:
        out["previous_china_day"] = out["trading_day"].shift(1)

    x = fx.copy()
    x["date"] = pd.to_datetime(x["date"], errors="raise").dt.normalize()
    x["usdcny_hk"] = pd.to_numeric(x["usdcny_hk"], errors="coerce")
    x = x.dropna(subset=["date", "usdcny_hk"]).drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    if x.empty:
        raise AssertionError("empty HKMA FX history")
    if x["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 HKMA FX row detected")

    dates = x["date"].to_numpy(dtype="datetime64[ns]")
    levels = x["usdcny_hk"].to_numpy(dtype=float)
    target = out["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev = out["previous_china_day"].to_numpy(dtype="datetime64[ns]")

    # Same-time-zone clock correction:
    # start at the latest HKMA end-of-day level ON OR BEFORE the previous China day;
    # end at the latest HKMA end-of-day level STRICTLY BEFORE the target China day.
    start_idx = np.full(len(out), -1, dtype=int)
    valid_prev = out["previous_china_day"].notna().to_numpy()
    start_idx[valid_prev] = np.searchsorted(dates, prev[valid_prev], side="right") - 1
    end_idx = np.searchsorted(dates, target, side="left") - 1
    valid = valid_prev & (start_idx >= 0) & (end_idx >= start_idx)

    count = np.full(len(out), np.nan, dtype=float)
    ret = np.full(len(out), np.nan, dtype=float)
    start_date = np.full(len(out), np.datetime64("NaT"), dtype="datetime64[ns]")
    end_date = np.full(len(out), np.datetime64("NaT"), dtype="datetime64[ns]")
    count[valid] = end_idx[valid] - start_idx[valid]
    ret[valid] = levels[end_idx[valid]] / levels[start_idx[valid]] - 1.0
    start_date[valid] = dates[start_idx[valid]]
    end_date[valid] = dates[end_idx[valid]]

    zero = valid & (count == 0)
    if np.any(np.abs(ret[zero]) > 1e-12):
        raise AssertionError("HKMA zero-interval return identity failed")
    if np.any(end_date[valid] >= target[valid]):
        raise AssertionError("target-date HKMA observation leaked into v4")
    if np.any(start_date[valid] > prev[valid]):
        raise AssertionError("HKMA start boundary is after previous China day")

    out["hkma_interval_count"] = count
    out["hkma_start_date"] = pd.to_datetime(start_date)
    out["hkma_end_date"] = pd.to_datetime(end_date)
    out["hkma_usdcny_closure_return"] = ret
    return out


def subset_compare(c0: pd.DataFrame, c1: pd.DataFrame, mask: pd.Series) -> dict:
    a = c0.loc[mask].reset_index(drop=True)
    b = c1.loc[mask].reset_index(drop=True)
    if not a["trading_day"].equals(b["trading_day"]):
        raise AssertionError("prediction subset misaligned")
    y = a["y"].to_numpy(dtype=float)
    p0 = a["pred"].to_numpy(dtype=float)
    p1 = b["pred"].to_numpy(dtype=float)
    return {
        "n": int(len(a)),
        "v3_ic": v3._corr(y, p0),
        "v4_ic": v3._corr(y, p1),
        "delta_ic": float(v3._corr(y, p1) - v3._corr(y, p0)) if len(a) >= 3 else float("nan"),
        "v3_sign_hit": float(np.mean((p0 >= 0) == (y >= 0))) if len(a) else float("nan"),
        "v4_sign_hit": float(np.mean((p1 >= 0) == (y >= 0))) if len(a) else float("nan"),
        "sse_improvement_v4_vs_v3": float(np.sum((y - p0) ** 2) - np.sum((y - p1) ** 2)),
    }


def main() -> None:
    prereg = json.loads(PREREG_PATH.read_text())
    source_sub = json.loads(SOURCE_SUB_PATH.read_text())
    clock_corr = json.loads(CLOCK_CORR_PATH.read_text())
    fx_manifest = json.loads(FX_MANIFEST_PATH.read_text())
    if source_sub["new_data_contract"]["provider"] != "Hong Kong Monetary Authority public API":
        raise AssertionError("unexpected v4 source substitution")
    if clock_corr["status"] != "result_free_before_HKMA_download_and_v4_execution":
        raise AssertionError("HKMA clock correction was not frozen result-free")
    if fx_manifest["guards"]["post_2020_rows"] != 0 or fx_manifest["guards"]["forward_fill"]:
        raise AssertionError("HKMA FX manifest violates v4 boundary")

    baseline = json.loads(BASELINE_PATH.read_text())
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")

    df = v3.add_complete_clock_features(panel, v3._load_us())
    fx = pd.read_parquet(FX_PATH)
    df = add_hkma_closure_return(df, fx)

    base = list(baseline["features"])
    sets = {
        "V3_US_closure_comparator": base + ["us_nasdaq_closure_extra", "us_vix_closure_extra"],
        "V4_US_plus_CNH_closure": base + ["us_nasdaq_closure_extra", "us_vix_closure_extra", "hkma_usdcny_closure_return"],
    }
    if list(sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v4 attempt IDs differ from preregistration")

    metrics: dict[str, dict] = {}
    preds: dict[str, pd.DataFrame] = {}
    for key, features in sets.items():
        metrics[key], preds[key] = v3._fit_predict(df, features)

    v3m = metrics["V3_US_closure_comparator"]
    v4m = metrics["V4_US_plus_CNH_closure"]
    if abs(v3m["holdout_ic"] - 0.5206571801111871) > 1e-9:
        raise AssertionError(("v3 comparator drift", v3m["holdout_ic"]))
    if abs(v3m["holdout_sse"] - 0.027762222368322282) > 1e-12:
        raise AssertionError(("v3 SSE drift", v3m["holdout_sse"]))

    p3 = preds["V3_US_closure_comparator"].reset_index(drop=True)
    p4 = preds["V4_US_plus_CNH_closure"].reset_index(drop=True)
    if not p3["trading_day"].equals(p4["trading_day"]):
        raise AssertionError("v4 holdout predictions misaligned")

    clock = df[["trading_day", "hkma_interval_count"]].drop_duplicates("trading_day")
    p3 = p3.merge(clock, on="trading_day", how="left", validate="one_to_one")
    p4 = p4.merge(clock, on="trading_day", how="left", validate="one_to_one")
    accumulated = p3["hkma_interval_count"] > 0
    holiday = pd.to_numeric(p3["holiday_reopen"], errors="coerce").fillna(0) != 0
    ordinary = ~accumulated
    subsets = {
        "hkma_accumulation_rows": subset_compare(p3, p4, accumulated),
        "holiday_reopen": subset_compare(p3, p4, holiday),
        "ordinary_rows": subset_compare(p3, p4, ordinary),
    }

    v4m["delta_ic_vs_v3"] = float(v4m["holdout_ic"] - v3m["holdout_ic"])
    v4m["sse_improvement_vs_v3"] = float(v3m["holdout_sse"] - v4m["holdout_sse"])
    coef = v4m.get("standardized_coefficients", {}).get("hkma_usdcny_closure_return")
    progression = (
        v4m["holdout_ic"] > v3m["holdout_ic"]
        and v4m["holdout_sse"] < v3m["holdout_sse"]
        and subsets["hkma_accumulation_rows"]["sse_improvement_v4_vs_v3"] > 0
    )

    report = {
        "schema_id": "overnight_open_global_spillover_v4_hkma_fx_results@1.0",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "source_substitution": str(SOURCE_SUB_PATH.relative_to(ROOT)),
        "clock_correction": str(CLOCK_CORR_PATH.relative_to(ROOT)),
        "external_manifest": str(FX_MANIFEST_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_internal"},
        "clock": {
            "hkma_accumulation_holdout_n": int(accumulated.sum()),
            "holiday_reopen_n": int(holiday.sum()),
            "ordinary_zero_interval_n": int(ordinary.sum()),
        },
        "v3_comparator": v3m,
        "v4_candidate": v4m,
        "mechanism_subsets": subsets,
        "economic_sign_diagnostic": {
            "hkma_usdcny_closure_return_standardized_coefficient": coef,
            "expected_if_RMB_depreciation_is_risk_off": "negative",
        },
        "adjudication": {
            "progression_rule_pass": bool(progression),
            "scientific_status": "progress_HKMA_China_FX_increment_to_unseen_confirmation" if progression else "do_not_progress_HKMA_China_FX_increment",
            "baseline_replacement": False,
            "fresh_oos": False,
        },
        "authority": {"production": False, "registry_mutation": False, "holiday_runtime_routing": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
