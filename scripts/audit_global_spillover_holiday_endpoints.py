#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
V1_SCRIPT = ROOT / "scripts/research_global_spillover_v1.py"
OUT_PATH = ROOT / "artifacts/research/global_spillover_holiday_endpoint_audit.json"


def _load_v1():
    spec = importlib.util.spec_from_file_location("spillover_v1", V1_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _find_col(columns: list[str], exact: tuple[str, ...], contains: tuple[str, ...]) -> str:
    lower = {str(c).lower(): str(c) for c in columns}
    for name in exact:
        if name.lower() in lower:
            return lower[name.lower()]
    for c in columns:
        lc = str(c).lower()
        if any(token.lower() in lc for token in contains):
            return str(c)
    raise KeyError((columns, exact, contains))


def _load_raw_us() -> pd.DataFrame:
    raw = pd.read_parquet(US_PATH).copy()
    cols = [str(c) for c in raw.columns]
    d = _find_col(cols, ("date", "trading_day"), ("date", "day"))
    n = _find_col(cols, ("NASDAQCOM", "nasdaq"), ("nasdaq",))
    v = _find_col(cols, ("VIXCLS", "vix"), ("vix",))
    return pd.DataFrame({
        "date": pd.to_datetime(raw[d], errors="coerce").dt.normalize(),
        "nasdaq": pd.to_numeric(raw[n], errors="coerce"),
        "vix": pd.to_numeric(raw[v], errors="coerce"),
    }).dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _series_alignment(panel: pd.DataFrame, us: pd.DataFrame, level_col: str, panel_col: str) -> pd.Series:
    s = us.loc[us[level_col].notna(), ["date", level_col]].copy().reset_index(drop=True)
    s["pct"] = s[level_col].pct_change(fill_method=None)
    dates = s["date"].to_numpy(dtype="datetime64[ns]")
    target = panel["trading_day"].to_numpy(dtype="datetime64[ns]")
    idx = np.searchsorted(dates, target, side="left") - 1
    recon = np.full(len(panel), np.nan)
    valid = idx >= 1
    recon[valid] = s["pct"].to_numpy(dtype=float)[idx[valid]]
    p = pd.to_numeric(panel[panel_col], errors="coerce").to_numpy(dtype=float)
    exact = np.isfinite(recon) & np.isfinite(p) & (np.abs(recon - p) <= 1e-10)
    return pd.Series(exact, index=panel.index, dtype=bool)


def main() -> None:
    panel = pd.read_parquet(PANEL_PATH).copy().sort_values("trading_day").reset_index(drop=True)
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    raw_us = _load_raw_us()
    if raw_us["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 US row detected")

    nas_exact = _series_alignment(panel, raw_us, "nasdaq", "us_nasdaq")
    vix_exact = _series_alignment(panel, raw_us, "vix", "us_vix_chg")
    both_exact = nas_exact & vix_exact

    v1 = _load_v1()
    joint_us = v1._load_us()
    df = v1._add_unabsorbed_us(panel, joint_us)
    joint_dates = joint_us["us_date"].to_numpy(dtype="datetime64[ns]")

    hold = df.loc[(df["trading_day"] >= pd.Timestamp("2019-01-01")) & (pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0).eq(1))].copy()
    rows: list[dict] = []
    for idx, r in hold.iterrows():
        if idx <= 0:
            raise AssertionError("holiday row has no previous China row")
        prev_idx = idx - 1
        previous_china_day = panel.loc[prev_idx, "trading_day"]
        if pd.Timestamp(r["previous_china_day"]) != previous_china_day:
            raise AssertionError("previous China day mismatch")

        target_day = pd.Timestamp(r["trading_day"])
        expected_start_i = int(np.searchsorted(joint_dates, np.datetime64(previous_china_day), side="left") - 1)
        expected_end_i = int(np.searchsorted(joint_dates, np.datetime64(target_day), side="left") - 1)
        if expected_start_i < 0 or expected_end_i < 0:
            raise AssertionError("missing endpoint index")
        expected_start = pd.Timestamp(joint_dates[expected_start_i])
        expected_end = pd.Timestamp(joint_dates[expected_end_i])
        actual_start = pd.Timestamp(r["_us_start_date"])
        actual_end = pd.Timestamp(r["_us_end_date"])
        start_date_consistent = actual_start == expected_start
        end_date_consistent = actual_end == expected_end
        interval_count = expected_end_i - expected_start_i

        nas_cum = float(r["us_nasdaq_unabsorbed_cum"])
        vix_cum = float(r["us_vix_unabsorbed_cum"])
        endpoint_nas_recalc = float(joint_us.loc[expected_end_i, "nasdaq_level"] / joint_us.loc[expected_start_i, "nasdaq_level"] - 1.0)
        endpoint_vix_recalc = float(joint_us.loc[expected_end_i, "vix_level"] / joint_us.loc[expected_start_i, "vix_level"] - 1.0)
        endpoint_values_exact = abs(nas_cum - endpoint_nas_recalc) <= 1e-12 and abs(vix_cum - endpoint_vix_recalc) <= 1e-12

        rows.append({
            "target_china_day": str(target_day.date()),
            "previous_china_day": str(previous_china_day.date()),
            "target_daily_alignment_exact": bool(both_exact.loc[idx]),
            "start_boundary_previous_china_alignment_exact": bool(both_exact.loc[prev_idx]),
            "v1_start_us_date": str(actual_start.date()),
            "v1_end_us_date": str(actual_end.date()),
            "start_date_consistent": bool(start_date_consistent),
            "end_date_consistent": bool(end_date_consistent),
            "endpoint_values_exact": bool(endpoint_values_exact),
            "joint_us_interval_count": int(interval_count),
            "cumulative_nasdaq": nas_cum,
            "cumulative_vix": vix_cum,
            "gap": float(r["gap"]),
        })

    n = len(rows)
    all_target = all(x["target_daily_alignment_exact"] for x in rows)
    all_start = all(x["start_boundary_previous_china_alignment_exact"] for x in rows)
    all_dates = all(x["start_date_consistent"] and x["end_date_consistent"] for x in rows)
    all_values = all(x["endpoint_values_exact"] for x in rows)
    internally_supported = bool(n > 0 and all_target and all_start and all_dates and all_values)
    intervals = [x["joint_us_interval_count"] for x in rows]

    report = {
        "schema_id": "overnight_open_global_spillover_holiday_endpoint_audit@1.0",
        "audit_plan": "docs/governance/global_spillover_holiday_endpoint_audit_plan.json",
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020 consumed_internal"},
        "summary": {
            "holiday_rows": n,
            "target_endpoint_exact_count": int(sum(x["target_daily_alignment_exact"] for x in rows)),
            "start_boundary_exact_count": int(sum(x["start_boundary_previous_china_alignment_exact"] for x in rows)),
            "date_consistency_count": int(sum(x["start_date_consistent"] and x["end_date_consistent"] for x in rows)),
            "endpoint_value_recalc_exact_count": int(sum(x["endpoint_values_exact"] for x in rows)),
            "min_joint_us_interval_count": int(min(intervals)) if intervals else None,
            "max_joint_us_interval_count": int(max(intervals)) if intervals else None,
            "median_joint_us_interval_count": float(np.median(intervals)) if intervals else None,
            "all_holiday_cumulative_endpoints_internally_supported": internally_supported,
        },
        "rows": rows,
        "interpretation": "measurement forensic only; even a full pass does not permit holiday routing or baseline promotion on consumed holdout",
        "authority": {"fresh_oos": False, "candidate_selection": False, "baseline_replacement": False, "production": False, "registry_mutation": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
