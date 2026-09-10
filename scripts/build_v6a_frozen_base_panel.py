#!/usr/bin/env python3
"""Build the frozen V6A base-feature panel with a pre-BLACKBOX parity gate.

This script reuses the already-existing reconstruction logic in
`scripts/evaluate_local_2021_2025_two_head.py`. It first reconstructs only
2015-2020 and requires exact parity with the historical frozen panel. Only after
that succeeds may it materialize a temporary 2015-2025 panel for the V6A
BLACKBOX controller.

It prints no data values, counts, dates, metrics or BLACKBOX diagnostics.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIT_START = "2015-01-05"
FIT_END = "2020-12-31"
FULL_END = "2025-12-31"
BASE_FEATURES = [
    "r1",
    "r20",
    "abs_r1",
    "prev_gap",
    "overnight_trend_5",
    "prev_daytime",
    "prev_last_hour",
    "prev_afternoon",
    "rvol20",
    "weekend",
    "holiday_reopen",
    "us_nasdaq",
    "us_vix_chg",
]


def _load_frozen_reconstruction_module():
    path = ROOT / "scripts/evaluate_local_2021_2025_two_head.py"
    spec = importlib.util.spec_from_file_location("v6a_frozen_reconstruction", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen reconstruction authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_fred(src: Path, dst: Path) -> None:
    frame = pd.read_csv(src)
    if "date" not in frame.columns:
        if "observation_date" in frame.columns:
            frame = frame.rename(columns={"observation_date": "date"})
        elif "DATE" in frame.columns:
            frame = frame.rename(columns={"DATE": "date"})
        else:
            raise RuntimeError(f"FRED date column not found in {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(dst, index=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-panel", type=Path, required=True)
    ap.add_argument("--minute-bars", type=Path, required=True)
    ap.add_argument("--nasdaq", type=Path, required=True)
    ap.add_argument("--vix", type=Path, required=True)
    ap.add_argument("--frozen-panel", type=Path, required=True)
    ap.add_argument("--panel-out", type=Path, required=True)
    ap.add_argument("--nasdaq-normalized-out", type=Path, required=True)
    ap.add_argument("--vix-normalized-out", type=Path, required=True)
    args = ap.parse_args()

    authority = _load_frozen_reconstruction_module()
    authority.ANNOTATED_PANEL = args.raw_panel
    authority.DATAHUB_1M = args.minute_bars
    authority.FRED_NDQ = args.nasdaq
    authority.FRED_VIX = args.vix

    # Gate 1: development-only exact parity. This must complete before any
    # 2021-2025 feature rows are materialized.
    frozen = pd.read_parquet(args.frozen_panel).copy()
    frozen["trading_day"] = frozen["trading_day"].astype(str)
    authority.assert_dev_reconstruction(frozen)

    # Gate 2: deterministic extension using exactly the same functions/formulas.
    raw = pd.read_parquet(
        args.raw_panel,
        filters=[("trading_day", ">=", FIT_START), ("trading_day", "<=", FULL_END)],
    ).copy()
    raw["trading_day"] = raw["trading_day"].astype(str)
    hours = authority.load_hours(args.minute_bars, FIT_START, FULL_END)
    frame = authority.add_domestic_features(raw, hours)
    us = authority.load_us(args.nasdaq, args.vix, max_date=FULL_END)
    frame = authority.attach_us(frame, us)

    required = ["trading_day", "gap", *BASE_FEATURES]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise RuntimeError(f"reconstructed panel missing frozen columns: {missing}")

    args.panel_out.parent.mkdir(parents=True, exist_ok=True)
    frame[required].to_parquet(args.panel_out, index=False)

    # The BLACKBOX controller's FRED reader accepts `date`; normalize only the
    # header/date-column name, without changing observations.
    _normalize_fred(args.nasdaq, args.nasdaq_normalized_out)
    _normalize_fred(args.vix, args.vix_normalized_out)

    print("PANEL_READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
