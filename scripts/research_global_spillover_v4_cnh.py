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
CNH_MANIFEST_PATH = ROOT / "docs/governance/external_cnh_yahoo_2014_2020_manifest.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
CNH_PATH = ROOT / "data/development/usdcnh_yahoo.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v4_cnh_results.json"


def add_cnh_closure_extra(df: pd.DataFrame, cnh: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values("trading_day").reset_index(drop=True)
    if "previous_china_day" not in out.columns:
        out["previous_china_day"] = out["trading_day"].shift(1)
    x = cnh.copy()
    x["date"] = pd.to_datetime(x["date"], errors="raise").dt.normalize()
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    x = x.dropna(subset=["date", "close"]).drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    if x["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 CNH row detected")

    dates = x["date"].to_numpy(dtype="datetime64[ns]")
    levels = x["close"].to_numpy(dtype=float)
    target = out["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev = out["previous_china_day"].to_numpy(dtype="datetime64[ns]")
    end_idx = np.searchsorted(dates, target, side="left") - 1
    start_idx = np.full(len(out), -1, dtype=int)
    valid_prev = out["previous_china_day"].notna().to_numpy()
    start_idx[valid_prev] = np.searchsorted(dates, prev[valid_prev], side="left") - 1
    clock_valid = valid_prev & (start_idx >= 0) & (end_idx >= start_idx)
    positive = clock_valid & (end_idx > start_idx) & (end_idx >= 1)
    zero = clock_valid & (end_idx == start_idx)

    count = np.full(len(out), np.nan, dtype=float)
    cumulative = np.full(len(out), np.nan, dtype=float)
    daily = np.full(len(out), np.nan, dtype=float)
    extra = np.full(len(out), np.nan, dtype=float)
    count[clock_valid] = end_idx[clock_valid] - start_idx[clock_valid]
    cumulative[zero] = 0.0
    extra[zero] = 0.0
    cumulative[positive] = levels[end_idx[positive]] / levels[start_idx[positive]] - 1.0
    daily[positive] = levels[end_idx[positive]] / levels[end_idx[positive] - 1] - 1.0
    extra[positive] = cumulative[positive] - daily[positive]
    at_most_one = clock_valid & (count <= 1)
    if np.any(np.abs(extra[at_most_one]) > 1e-12):
        raise AssertionError("CNH closure-extra <=1 interval identity failed")

    out["cnh_interval_count"] = count
    out["usdcnh_complete_cum"] = cumulative
    out["usdcnh_complete_daily"] = daily
    out["usdcnh_closure_extra"] = extra
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
    cnh_manifest = json.loads(CNH_MANIFEST_PATH.read_text())
    if cnh_manifest["guards"]["post_2020_rows"] != 0 or cnh_manifest["guards"]["forward_fill"]:
        raise AssertionError("CNH manifest violates preregistration")

    baseline = json.loads(BASELINE_PATH.read_text())
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    df = v3.add_complete_clock_features(panel, v3._load_us())
    cnh = pd.read_parquet(CNH_PATH)
    df = add_cnh_closure_extra(df, cnh)

    base = list(baseline["features"])
    sets = {
        "V3_US_closure_comparator": base + ["us_nasdaq_closure_extra", "us_vix_closure_extra"],
        "V4_US_plus_CNH_closure": base + ["us_nasdaq_closure_extra", "us_vix_closure_extra", "usdcnh_closure_extra"],
    }
    if list(sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v4 attempt family differs from preregistration")

    metrics = {}
    preds = {}
    for key, features in sets.items():
        metrics[key], preds[key] = v3._fit_predict(df, features)

    v3m = metrics["V3_US_closure_comparator"]
    v4m = metrics["V4_US_plus_CNH_closure"]
    # Exact reproduction guard against silent v3 comparator drift.
    if abs(v3m["holdout_ic"] - 0.5206571801111871) > 1e-9:
        raise AssertionError(("v3 comparator drift", v3m["holdout_ic"]))
    if abs(v3m["holdout_sse"] - 0.027762222368322282) > 1e-12:
        raise AssertionError(("v3 SSE drift", v3m["holdout_sse"]))

    p3 = preds["V3_US_closure_comparator"].reset_index(drop=True)
    p4 = preds["V4_US_plus_CNH_closure"].reset_index(drop=True)
    if not p3["trading_day"].equals(p4["trading_day"]):
        raise AssertionError("v4 holdout predictions misaligned")
    # Restore the CNH interval count from the feature frame by date.
    clock = df[["trading_day", "cnh_interval_count"]].drop_duplicates("trading_day")
    p3 = p3.merge(clock, on="trading_day", how="left", validate="one_to_one")
    p4 = p4.merge(clock, on="trading_day", how="left", validate="one_to_one")
    multi = p3["cnh_interval_count"] > 1
    holiday = pd.to_numeric(p3["holiday_reopen"], errors="coerce").fillna(0) != 0
    subsets = {
        "multiple_cnh_intervals": subset_compare(p3, p4, multi),
        "holiday_reopen": subset_compare(p3, p4, holiday),
        "ordinary_cnh_intervals": subset_compare(p3, p4, ~multi),
    }

    v4m["delta_ic_vs_v3"] = float(v4m["holdout_ic"] - v3m["holdout_ic"])
    v4m["sse_improvement_vs_v3"] = float(v3m["holdout_sse"] - v4m["holdout_sse"])
    coef = v4m.get("standardized_coefficients", {}).get("usdcnh_closure_extra")
    progression = (
        v4m["holdout_ic"] > v3m["holdout_ic"]
        and v4m["holdout_sse"] < v3m["holdout_sse"]
        and subsets["multiple_cnh_intervals"]["sse_improvement_v4_vs_v3"] > 0
    )

    report = {
        "schema_id": "overnight_open_global_spillover_v4_cnh_results@1.0",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "external_manifest": str(CNH_MANIFEST_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_internal"},
        "clock": {
            "multiple_cnh_interval_holdout_n": int(multi.sum()),
            "holiday_reopen_n": int(holiday.sum()),
        },
        "v3_comparator": v3m,
        "v4_candidate": v4m,
        "mechanism_subsets": subsets,
        "economic_sign_diagnostic": {
            "usdcnh_closure_extra_standardized_coefficient": coef,
            "expected_if_RMB_depreciation_is_risk_off": "negative",
        },
        "adjudication": {
            "progression_rule_pass": bool(progression),
            "scientific_status": "progress_CNH_increment_to_unseen_confirmation" if progression else "do_not_progress_CNH_increment",
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
