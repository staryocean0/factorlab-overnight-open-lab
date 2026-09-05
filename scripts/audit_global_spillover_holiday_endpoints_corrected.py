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
OUT_PATH = ROOT / "artifacts/research/global_spillover_holiday_endpoint_audit_corrected.json"


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


def _series_exact(panel: pd.DataFrame, us: pd.DataFrame, level_col: str, panel_col: str) -> pd.Series:
    s = us.loc[us[level_col].notna(), ["date", level_col]].copy().reset_index(drop=True)
    s["pct"] = s[level_col].pct_change(fill_method=None)
    dates = s["date"].to_numpy(dtype="datetime64[ns]")
    target = panel["trading_day"].to_numpy(dtype="datetime64[ns]")
    idx = np.searchsorted(dates, target, side="left") - 1
    recon = np.full(len(panel), np.nan)
    valid = idx >= 1
    recon[valid] = s["pct"].to_numpy(dtype=float)[idx[valid]]
    actual = pd.to_numeric(panel[panel_col], errors="coerce").to_numpy(dtype=float)
    return pd.Series(np.isfinite(recon) & np.isfinite(actual) & (np.abs(recon - actual) <= 1e-10), index=panel.index)


def _intervening_weekdays(start: pd.Timestamp, end_exclusive: pd.Timestamp) -> list[str]:
    first = start + pd.Timedelta(days=1)
    last = end_exclusive - pd.Timedelta(days=1)
    if first > last:
        return []
    return [str(x.date()) for x in pd.date_range(first, last, freq="B")]


def main() -> None:
    panel = pd.read_parquet(PANEL_PATH).copy().sort_values("trading_day").reset_index(drop=True)
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    raw_us = _load_raw_us()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31") or raw_us["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 row detected")

    target_exact = _series_exact(panel, raw_us, "nasdaq", "us_nasdaq") & _series_exact(panel, raw_us, "vix", "us_vix_chg")
    v1 = _load_v1()
    joint = v1._load_us()
    df = v1._add_unabsorbed_us(panel, joint)
    joint_dates = joint["us_date"].to_numpy(dtype="datetime64[ns]")
    joint_lookup = joint.set_index("us_date")

    hold = df.loc[(df["trading_day"] >= pd.Timestamp("2019-01-01")) & pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0).eq(1)].copy()
    rows: list[dict] = []
    for idx, r in hold.iterrows():
        prev_china = pd.Timestamp(r["previous_china_day"])
        target_china = pd.Timestamp(r["trading_day"])
        start = pd.Timestamp(r["_us_start_date"])
        end = pd.Timestamp(r["_us_end_date"])
        start_i = int(np.searchsorted(joint_dates, np.datetime64(prev_china), side="left") - 1)
        end_i = int(np.searchsorted(joint_dates, np.datetime64(target_china), side="left") - 1)
        expected_start = pd.Timestamp(joint_dates[start_i])
        expected_end = pd.Timestamp(joint_dates[end_i])
        start_levels_present = bool(start in joint_lookup.index and np.isfinite(joint_lookup.loc[start, "nasdaq_level"]) and np.isfinite(joint_lookup.loc[start, "vix_level"]))
        end_levels_present = bool(end in joint_lookup.index and np.isfinite(joint_lookup.loc[end, "nasdaq_level"]) and np.isfinite(joint_lookup.loc[end, "vix_level"]))
        start_between = _intervening_weekdays(start, prev_china)
        end_between = _intervening_weekdays(end, target_china)
        nas_recalc = float(joint_lookup.loc[end, "nasdaq_level"] / joint_lookup.loc[start, "nasdaq_level"] - 1.0)
        vix_recalc = float(joint_lookup.loc[end, "vix_level"] / joint_lookup.loc[start, "vix_level"] - 1.0)
        recalc_exact = abs(nas_recalc - float(r["us_nasdaq_unabsorbed_cum"])) <= 1e-12 and abs(vix_recalc - float(r["us_vix_unabsorbed_cum"])) <= 1e-12
        supported = bool(
            start_levels_present
            and end_levels_present
            and start == expected_start
            and end == expected_end
            and len(start_between) == 0
            and len(end_between) == 0
            and bool(target_exact.loc[idx])
            and recalc_exact
        )
        rows.append({
            "target_china_day": str(target_china.date()),
            "previous_china_day": str(prev_china.date()),
            "start_us_date": str(start.date()),
            "end_us_date": str(end.date()),
            "start_levels_present": start_levels_present,
            "end_levels_present": end_levels_present,
            "start_is_latest_packaged_joint_date": bool(start == expected_start),
            "end_is_latest_packaged_joint_date": bool(end == expected_end),
            "intervening_weekdays_start_to_previous_china": start_between,
            "intervening_weekdays_end_to_target_china": end_between,
            "target_daily_alignment_exact": bool(target_exact.loc[idx]),
            "endpoint_recalc_exact": bool(recalc_exact),
            "joint_us_interval_count": int(end_i - start_i),
            "cumulative_nasdaq": float(r["us_nasdaq_unabsorbed_cum"]),
            "cumulative_vix": float(r["us_vix_unabsorbed_cum"]),
            "gap": float(r["gap"]),
            "corrected_endpoint_supported": supported,
        })

    report = {
        "schema_id": "overnight_open_global_spillover_holiday_endpoint_audit_corrected@1.0",
        "plan": "docs/governance/global_spillover_holiday_endpoint_audit_correction_plan.json",
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020 consumed_internal"},
        "summary": {
            "holiday_rows": len(rows),
            "corrected_endpoint_supported_n": int(sum(x["corrected_endpoint_supported"] for x in rows)),
            "all_corrected_endpoints_supported": bool(rows and all(x["corrected_endpoint_supported"] for x in rows)),
            "target_daily_alignment_exact_n": int(sum(x["target_daily_alignment_exact"] for x in rows)),
            "endpoint_recalc_exact_n": int(sum(x["endpoint_recalc_exact"] for x in rows)),
            "rows_with_intervening_weekday_before_start_boundary": int(sum(bool(x["intervening_weekdays_start_to_previous_china"]) for x in rows)),
            "rows_with_intervening_weekday_before_target_boundary": int(sum(bool(x["intervening_weekdays_end_to_target_china"]) for x in rows)),
        },
        "rows": rows,
        "interpretation": "measurement validity only; no model refit, candidate selection, holiday routing or baseline promotion",
        "authority": {"fresh_oos": False, "candidate_selection": False, "baseline_replacement": False, "production": False, "registry_mutation": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
