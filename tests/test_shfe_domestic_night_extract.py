from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shfe_domestic_night_extract as mod  # noqa: E402


def make_frame(rows: list[tuple[str, float, float]]) -> pd.DataFrame:
    return pd.DataFrame({
        "datetime": pd.to_datetime([r[0] for r in rows]),
        "open": [r[1] for r in rows],
        "high": [r[1] for r in rows],
        "low": [r[1] for r in rows],
        "close": [r[1] for r in rows],
        "volume": [r[2] for r in rows],
        "open_interest": 1.0,
    })


def test_contract_delivery_and_all_future_files_remain_enumerable() -> None:
    assert mod.contract_delivery("CU2012", "CU") == (2020, 12)
    tree = {"tree": [
        {"type": "blob", "path": "5min/SHFE/CU/CU1501.csv", "sha": "a", "size": 1},
        {"type": "blob", "path": "5min/SHFE/CU/CU2201.csv", "sha": "b", "size": 1},
        {"type": "blob", "path": "5min/SHFE/CU/CU1401.csv", "sha": "c", "size": 1},
    ]}
    got = mod.enumerate_source_files(tree, "CU")
    assert [x.contract for x in got] == ["CU1501", "CU2201"]


def test_choose_contract_uses_previous_day_volume_then_nearest_then_lexical() -> None:
    day = pd.Timestamp("2020-06-15")
    candidates = [
        {"contract": "CU2007", "delivery_year": 2020, "delivery_month": 7, "observed_bar_count": 10, "day_volume_0900_1455": 100},
        {"contract": "CU2008", "delivery_year": 2020, "delivery_month": 8, "observed_bar_count": 10, "day_volume_0900_1455": 200},
        {"contract": "CU2006", "delivery_year": 2020, "delivery_month": 6, "observed_bar_count": 10, "day_volume_0900_1455": 200},
        {"contract": "CU2005", "delivery_year": 2020, "delivery_month": 5, "observed_bar_count": 10, "day_volume_0900_1455": 999},
    ]
    assert mod.choose_contract(candidates, day)["contract"] == "CU2006"


def test_daytime_stats_requires_exact_1455_but_does_not_fake_it() -> None:
    df = make_frame([
        ("2020-06-15 09:00:00", 100, 1),
        ("2020-06-15 14:50:00", 101, 2),
    ])
    got = mod.daytime_stats(df)[pd.Timestamp("2020-06-15")]
    assert got["observed_bar_count"] == 2
    assert got["day_volume_0900_1455"] == 3.0
    assert got["start_1455_close"] is None


def test_cu_night_crosses_midnight_and_uses_last_positive_volume_bar() -> None:
    df = make_frame([
        ("2020-06-15 21:00:00", 100, 1),
        ("2020-06-15 23:55:00", 101, 2),
        ("2020-06-16 00:55:00", 102, 3),
        ("2020-06-16 01:00:00", 999, 0),
        ("2020-06-16 01:05:00", 777, 5),
    ])
    got = mod.night_stats(df, [pd.Timestamp("2020-06-15")], "CU")[pd.Timestamp("2020-06-15")]
    assert got["positive_volume_bar_count"] == 3
    assert got["night_end_datetime"] == "2020-06-16 00:55:00"
    assert got["night_end_close"] == 102.0


def test_rb_pre_transition_crosses_midnight_post_transition_stops_2300() -> None:
    pre = make_frame([
        ("2016-04-20 21:00:00", 100, 1),
        ("2016-04-21 00:55:00", 101, 2),
        ("2016-04-21 01:05:00", 999, 3),
    ])
    got_pre = mod.night_stats(pre, [pd.Timestamp("2016-04-20")], "RB")[pd.Timestamp("2016-04-20")]
    assert got_pre["night_end_close"] == 101.0

    post = make_frame([
        ("2016-05-10 21:00:00", 200, 1),
        ("2016-05-10 23:00:00", 201, 2),
        ("2016-05-10 23:05:00", 999, 3),
        ("2016-05-11 00:30:00", 888, 4),
    ])
    got_post = mod.night_stats(post, [pd.Timestamp("2016-05-10")], "RB")[pd.Timestamp("2016-05-10")]
    assert got_post["night_end_close"] == 201.0


def test_rb_transition_quarantine_is_unavailable() -> None:
    df = make_frame([("2016-04-28 21:00:00", 100, 10)])
    got = mod.night_stats(df, [pd.Timestamp("2016-04-28")], "RB")[pd.Timestamp("2016-04-28")]
    assert got["quarantined"] is True
    assert got["night_end_close"] is None


def test_zero_volume_night_is_not_activity() -> None:
    df = make_frame([
        ("2020-06-15 21:00:00", 100, 0),
        ("2020-06-15 23:00:00", 101, 0),
    ])
    got = mod.night_stats(df, [pd.Timestamp("2020-06-15")], "RB")[pd.Timestamp("2020-06-15")]
    assert got["positive_volume_bar_count"] == 0
    assert got["night_end_close"] is None


def test_post_2020_poison_market_fields_are_not_parsed() -> None:
    body = (
        "datetime,open,high,low,close,volume,money,open_interest\n"
        "2020-12-31 14:55:00,100,100,100,100,1,100,2\n"
        "2021-01-04 09:00:00,POISON,POISON,POISON,POISON,POISON,POISON,POISON\n"
    ).encode()
    blob = mod.git_blob_sha(body)
    df, meta = mod.parse_bounded_contract(body, blob)
    assert len(df) == 1
    assert meta["post_2020_boundary_timestamp"] == "2021-01-04 09:00:00"
    assert meta["post_2020_market_fields_parsed"] == 0
