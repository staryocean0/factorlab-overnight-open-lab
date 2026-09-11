#!/usr/bin/env python3
"""Build connector-readable 2015-2020 A50/HKMA driver carrier.

This is deterministic data engineering only. It reads no post-2020 rows into a
DataFrame, creates no 2021-2025 text shards, and does not inspect opening-return
outcomes. A50 endpoint semantics match the frozen V6A source contract; HKMA
closure-return timing matches the frozen V6A controller.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

DEV_START = pd.Timestamp("2015-01-05")
DEV_END = pd.Timestamp("2020-12-31")
YEARS = tuple(range(2015, 2021))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_runtime_days(root: Path) -> pd.DataFrame:
    parts = []
    for year in YEARS:
        path = root / f"factor_panel_{year}.csv"
        x = pd.read_csv(path, usecols=["trading_day", "holiday_reopen"])
        x["trading_day"] = pd.to_datetime(x["trading_day"], errors="raise").dt.normalize()
        if not x["trading_day"].dt.year.eq(year).all():
            raise RuntimeError(f"factor shard crosses year boundary: {year}")
        parts.append(x)
    out = pd.concat(parts, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
    if out["trading_day"].min() != DEV_START or out["trading_day"].max() != DEV_END:
        raise RuntimeError("unexpected development trading-day boundary")
    if out["trading_day"].duplicated().any():
        raise RuntimeError("duplicate trading_day in runtime factor carrier")
    out["previous_china_day"] = out["trading_day"].shift(1)
    return out


def load_a50(path: Path, value_col: str) -> pd.DataFrame:
    cols = ["trading_day", value_col, "target_end_time"]
    x = pd.read_parquet(
        path,
        columns=cols,
        filters=[("trading_day", ">=", "2015-01-01"), ("trading_day", "<=", "2020-12-31")],
    ).copy()
    x["trading_day"] = pd.to_datetime(x["trading_day"], errors="raise").dt.normalize()
    x[value_col] = pd.to_numeric(x[value_col], errors="coerce")
    x["target_end_time"] = pd.to_numeric(x["target_end_time"], errors="raise").round().astype("int64")
    if x["trading_day"].max() > DEV_END:
        raise RuntimeError("post-2020 A50 row loaded")
    if x["trading_day"].duplicated().any():
        raise RuntimeError(f"duplicate A50 endpoint row: {value_col}")
    return x


def attach_a50(days: pd.DataFrame, ordinary_path: Path, holiday_path: Path) -> tuple[pd.DataFrame, dict]:
    ordinary = load_a50(ordinary_path, "a50_ordinary_preauction_closure_return")
    holiday = load_a50(holiday_path, "a50_holiday_closure_return")
    ordinary = ordinary.rename(columns={"target_end_time": "ordinary_end_time"})
    holiday = holiday.rename(columns={"target_end_time": "holiday_end_time"})
    out = days.merge(ordinary, on="trading_day", how="left", validate="one_to_one")
    out = out.merge(holiday, on="trading_day", how="left", validate="one_to_one")
    is_holiday = pd.to_numeric(out["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    ordinary_available = (~is_holiday) & out["a50_ordinary_preauction_closure_return"].notna()
    holiday_available = is_holiday & out["a50_holiday_closure_return"].notna()

    if ordinary_available.any() and not bool((out.loc[ordinary_available, "ordinary_end_time"] < 91500).all()):
        raise RuntimeError("ordinary A50 cutoff violation")
    if holiday_available.any() and not bool((out.loc[holiday_available, "holiday_end_time"] < 92500).all()):
        raise RuntimeError("holiday A50 cutoff violation")

    out["a50_channel_mode"] = np.where(is_holiday, "holiday", "ordinary")
    out["a50_channel_return"] = np.where(
        is_holiday,
        out["a50_holiday_closure_return"],
        out["a50_ordinary_preauction_closure_return"],
    )
    out["a50_target_end_time"] = np.where(is_holiday, out["holiday_end_time"], out["ordinary_end_time"])
    integrity = {
        "ordinary_cutoff_lt_091500": True,
        "holiday_cutoff_lt_092500": True,
        "mode_selected_from_holiday_reopen_only": True,
        "future_volume_or_oi_selection": False,
        "mid_window_roll": False,
        "forward_fill_or_interpolation": False,
    }
    return out, integrity


def attach_hkma(days: pd.DataFrame, hkma_path: Path) -> tuple[pd.DataFrame, dict]:
    x = pd.read_parquet(
        hkma_path,
        columns=["date", "usdcny_hk"],
        filters=[("date", ">=", "2014-01-01"), ("date", "<=", "2020-12-31")],
    ).copy()
    x["date"] = pd.to_datetime(x["date"], errors="raise").dt.normalize()
    x["usdcny_hk"] = pd.to_numeric(x["usdcny_hk"], errors="coerce")
    x = x.dropna(subset=["date", "usdcny_hk"]).drop_duplicates("date", keep="last").sort_values("date")
    if x["date"].max() > DEV_END:
        raise RuntimeError("post-2020 HKMA row loaded")

    out = days.copy()
    dates = x["date"].to_numpy(dtype="datetime64[ns]")
    levels = x["usdcny_hk"].to_numpy(float)
    target = out["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev = out["previous_china_day"].to_numpy(dtype="datetime64[ns]")
    start_idx = np.full(len(out), -1, dtype=int)
    valid_prev = out["previous_china_day"].notna().to_numpy()
    start_idx[valid_prev] = np.searchsorted(dates, prev[valid_prev], side="right") - 1
    end_idx = np.searchsorted(dates, target, side="left") - 1
    valid = valid_prev & (start_idx >= 0) & (end_idx >= start_idx)
    ret = np.full(len(out), np.nan)
    ret[valid] = levels[end_idx[valid]] / levels[start_idx[valid]] - 1.0
    if valid.any() and np.any(dates[end_idx[valid]] >= target[valid]):
        raise RuntimeError("HKMA target-date leakage")
    out["hkma_usdcny_closure_return"] = ret
    return out, {
        "target_observation_strictly_before_china_trading_day": True,
        "start_observation_at_or_before_previous_china_day": True,
        "forward_fill_or_interpolation": False,
        "target_date_leakage": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor-runtime-root", type=Path, required=True)
    ap.add_argument("--source-manifest", type=Path, required=True)
    ap.add_argument("--ordinary-a50", type=Path, required=True)
    ap.add_argument("--holiday-a50", type=Path, required=True)
    ap.add_argument("--hkma", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    required_assertions = [
        "same_contract_all_events",
        "no_future_volume_or_oi_selection",
        "no_mid_window_roll",
        "no_forward_fill_or_interpolation",
        "blackbox_not_used_for_fit_or_rule_selection",
    ]
    if not all(source_manifest.get("assertions", {}).get(k) is True for k in required_assertions):
        raise RuntimeError("V6A external-source assertions are not all satisfied")

    days = load_runtime_days(args.factor_runtime_root)
    frame, a50_integrity = attach_a50(days, args.ordinary_a50, args.holiday_a50)
    frame, hkma_integrity = attach_hkma(frame, args.hkma)
    if frame["trading_day"].max() > DEV_END:
        raise RuntimeError("post-2020 development row present")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    output_meta = {}
    keep = [
        "trading_day",
        "holiday_reopen",
        "a50_channel_mode",
        "a50_channel_return",
        "a50_target_end_time",
        "hkma_usdcny_closure_return",
    ]
    for year in YEARS:
        y = frame.loc[frame["trading_day"].dt.year.eq(year), keep].copy()
        y["trading_day"] = y["trading_day"].dt.strftime("%Y-%m-%d")
        path = args.out_dir / f"driver_external_{year}.csv"
        y.to_csv(path, index=False, float_format="%.17g")
        output_meta[str(year)] = {
            "path": str(path),
            "sha256": sha256(path),
            "rows": int(len(y)),
            "min_day": None if y.empty else str(y["trading_day"].min()),
            "max_day": None if y.empty else str(y["trading_day"].max()),
            "bytes": path.stat().st_size,
        }

    manifest = {
        "schema_id": "overnight_driver_runtime_text_2015_2020@1.0",
        "session_date": "2026-09-12",
        "purpose": "connector_readable_causal_A50_HKMA_driver_carrier_for_open_development_only",
        "published_window": "2015-01-05..2020-12-31",
        "withheld_years": [2021, 2022, 2023, 2024, 2025],
        "instrument": "000852.SH",
        "source_files": {
            "external_manifest": {"path": str(args.source_manifest), "sha256": sha256(args.source_manifest)},
            "ordinary_a50": {"path": str(args.ordinary_a50), "sha256": sha256(args.ordinary_a50)},
            "holiday_a50": {"path": str(args.holiday_a50), "sha256": sha256(args.holiday_a50)},
            "hkma": {"path": str(args.hkma), "sha256": sha256(args.hkma)},
        },
        "columns": keep,
        "outputs": output_meta,
        "transform": {
            "scientific_change": False,
            "feature_selection_from_outcomes": False,
            "row_filter_to_open_development_only": True,
            "same_contract_A50_semantics": True,
            "forward_fill_or_interpolation": False,
            "2021_2025_row_level_text_generated": False,
        },
        "a50_integrity": a50_integrity,
        "hkma_integrity": hkma_integrity,
        "blackbox_opened": False,
        "production_authority": False,
    }
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = """# Driver runtime text carrier (2015-2020)\n\nConnector-readable development-only carrier for the causal SGX A50 and HKMA\nUSD/CNY driver coordinates used by Overnight/Open research. It publishes only\n2015-2020 rows. 2021-2025 remain reusable BLACKBOX-governed and are not\nmaterialized here.\n\nThis carrier is not new scientific evidence, not a fresh OOS sample, and not a\nproduction dataset. Physical/textual accessibility does not grant evidence\nauthority. Each research identity still requires its own preregistration and\nevidence boundary.\n"""
    (args.out_dir / "README.md").write_text(readme, encoding="utf-8")

    receipt = {
        "schema_id": "overnight_driver_runtime_text_carrier_receipt@1.0",
        "session_date": "2026-09-12",
        "published_window": "2015-01-05..2020-12-31",
        "source_manifest_assertions_pass": True,
        "a50_clock_integrity": "PASS",
        "hkma_causal_timing_integrity": "PASS",
        "target_rows_after_2020_loaded": False,
        "2021_2025_text_shards_generated": False,
        "2021_2025_blackbox_opened": False,
        "output_manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "scientific_change": False,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DRIVER_RUNTIME_TEXT_CARRIER_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
