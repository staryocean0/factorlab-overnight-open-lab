from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "volume_gate", ROOT / "scripts/audit_domestic_night_shfe_volume_integrity.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def frame(rows: list[tuple[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "datetime": pd.to_datetime([r[0] for r in rows]),
            "open": 1.0,
            "high": 1.0,
            "low": 1.0,
            "close": 1.0,
            "volume": [r[1] for r in rows],
            "open_interest": 1.0,
        }
    )


def test_cu_trading_day_includes_prior_night_midnight_and_day() -> None:
    df = frame(
        [
            ("2016-06-14 20:55:00", 100),
            ("2016-06-14 21:00:00", 1),
            ("2016-06-14 23:55:00", 2),
            ("2016-06-15 00:00:00", 3),
            ("2016-06-15 01:00:00", 4),
            ("2016-06-15 01:05:00", 100),
            ("2016-06-15 09:00:00", 5),
            ("2016-06-15 14:55:00", 6),
            ("2016-06-15 15:05:00", 100),
        ]
    )
    got = mod.transport_volume_summary(df, pd.Timestamp("2016-06-15"), "SHFE_CU")
    assert got is not None
    assert got["transport_volume_sum"] == 21.0


def test_rb_trading_day_stops_prior_night_at_2300() -> None:
    df = frame(
        [
            ("2018-06-14 21:00:00", 1),
            ("2018-06-14 23:00:00", 2),
            ("2018-06-14 23:05:00", 100),
            ("2018-06-15 00:00:00", 100),
            ("2018-06-15 09:00:00", 3),
            ("2018-06-15 15:00:00", 4),
        ]
    )
    got = mod.transport_volume_summary(df, pd.Timestamp("2018-06-15"), "SHFE_RB")
    assert got is not None
    assert got["transport_volume_sum"] == 10.0


def test_systematic_scale_detection_is_diagnostic_not_repair() -> None:
    same_ratio = [
        {"official_volume": 10.0, "transport_volume_sum": 20.0, "exact_volume_match": False},
        {"official_volume": 12.0, "transport_volume_sum": 24.0, "exact_volume_match": False},
    ]
    got = mod._systematic_scale_detected(same_ratio)
    assert got["repeated_exact_scale_ratio_detected"] is True
    assert got["mismatch_ratios"] == [2.0, 2.0]


def test_exact_volume_match_not_marked_as_scale_problem() -> None:
    rows = [
        {"official_volume": 10.0, "transport_volume_sum": 10.0, "exact_volume_match": True},
        {"official_volume": 12.0, "transport_volume_sum": 12.0, "exact_volume_match": True},
    ]
    got = mod._systematic_scale_detected(rows)
    assert got["mismatch_count"] == 0
    assert got["repeated_exact_scale_ratio_detected"] is False
