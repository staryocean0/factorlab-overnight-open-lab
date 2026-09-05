from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("night_audit", ROOT / "scripts/audit_domestic_night_source_crosscheck.py")
night = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(night)


def frame(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    # datetime, price, volume; use flat OHLC so endpoint semantics are transparent.
    return pd.DataFrame([
        {
            "datetime": pd.Timestamp(ts),
            "open": px,
            "high": px,
            "low": px,
            "close": px,
            "volume": vol,
            "open_interest": 1.0,
        }
        for ts, px, vol in rows
    ]).sort_values("datetime").reset_index(drop=True)


def test_dce_friday_night_belongs_to_monday_trading_day() -> None:
    df = frame([
        ("2020-06-12 21:00:00", 100.0, 1.0),
        ("2020-06-12 23:00:00", 102.0, 1.0),
        ("2020-06-15 09:00:00", 103.0, 1.0),
        ("2020-06-15 15:00:00", 104.0, 1.0),
    ])
    out = night.aggregate_trading_day(df, pd.Timestamp("2020-06-15"), "DCE_I")
    assert out is not None
    assert out["night_source_calendar_date"] == "2020-06-12"
    assert out["all_bars_ohlc"] == {"open": 100.0, "high": 104.0, "low": 100.0, "close": 104.0}


def test_cu_includes_target_calendar_early_morning_until_0100() -> None:
    df = frame([
        ("2018-06-14 21:00:00", 100.0, 1.0),
        ("2018-06-14 23:55:00", 99.0, 1.0),
        ("2018-06-15 00:30:00", 98.0, 1.0),
        ("2018-06-15 01:00:00", 101.0, 1.0),
        ("2018-06-15 01:05:00", 500.0, 1.0),
        ("2018-06-15 09:00:00", 102.0, 1.0),
        ("2018-06-15 15:00:00", 103.0, 1.0),
    ])
    out = night.aggregate_trading_day(df, pd.Timestamp("2018-06-15"), "SHFE_CU")
    assert out is not None
    assert out["all_bars_ohlc"] == {"open": 100.0, "high": 103.0, "low": 98.0, "close": 103.0}
    assert out["selected_bar_count"] == 6


def test_rb_does_not_include_after_2300_or_target_early_morning() -> None:
    df = frame([
        ("2018-06-14 21:00:00", 100.0, 1.0),
        ("2018-06-14 23:00:00", 101.0, 1.0),
        ("2018-06-14 23:05:00", 50.0, 1.0),
        ("2018-06-15 00:30:00", 40.0, 1.0),
        ("2018-06-15 09:00:00", 102.0, 1.0),
        ("2018-06-15 15:00:00", 103.0, 1.0),
    ])
    out = night.aggregate_trading_day(df, pd.Timestamp("2018-06-15"), "SHFE_RB")
    assert out is not None
    assert out["all_bars_ohlc"] == {"open": 100.0, "high": 103.0, "low": 100.0, "close": 103.0}
    assert out["selected_bar_count"] == 4


def test_frozen_sample_fallback_has_anchor_plus_five_previous_weekdays() -> None:
    days = night.candidate_dates(pd.Timestamp("2020-06-15"))
    assert [str(d.date()) for d in days] == [
        "2020-06-15", "2020-06-12", "2020-06-11", "2020-06-10", "2020-06-09", "2020-06-08"
    ]
