from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v4", ROOT / "scripts/research_global_spillover_v4_cnh.py")
v4 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v4)


def test_hkma_adjacent_china_day_has_zero_new_end_of_day_interval() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-02", "2020-01-03"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-02"]),
    })
    fx = pd.DataFrame({
        "date": pd.to_datetime(["2019-12-31", "2020-01-02"]),
        "usdcny_hk": [7.00, 7.07],
    })
    out = v4.add_hkma_closure_return(panel, fx)
    r = out.iloc[1]
    assert r["hkma_interval_count"] == 0
    assert abs(r["hkma_usdcny_closure_return"]) < 1e-12
    assert r["hkma_start_date"] == pd.Timestamp("2020-01-02")
    assert r["hkma_end_date"] == pd.Timestamp("2020-01-02")


def test_hkma_long_china_closure_accumulates_only_after_previous_china_day_end() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-23", "2020-02-03"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-23"]),
    })
    fx = pd.DataFrame({
        "date": pd.to_datetime([
            "2020-01-22", "2020-01-23", "2020-01-24", "2020-01-27",
            "2020-01-28", "2020-01-29", "2020-01-30", "2020-01-31",
        ]),
        "usdcny_hk": [7.00, 7.01, 7.02, 7.03, 7.04, 7.05, 7.06, 7.07],
    })
    out = v4.add_hkma_closure_return(panel, fx)
    r = out.iloc[1]
    assert r["hkma_start_date"] == pd.Timestamp("2020-01-23")
    assert r["hkma_end_date"] == pd.Timestamp("2020-01-31")
    assert r["hkma_interval_count"] == 6
    assert abs(r["hkma_usdcny_closure_return"] - (7.07 / 7.01 - 1.0)) < 1e-12


def test_hkma_target_date_observation_is_never_used() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-23", "2020-02-03"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-23"]),
    })
    fx = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-23", "2020-01-31", "2020-02-03"]),
        "usdcny_hk": [7.01, 7.07, 7.50],
    })
    out = v4.add_hkma_closure_return(panel, fx)
    r = out.iloc[1]
    assert r["hkma_end_date"] == pd.Timestamp("2020-01-31")
    assert abs(r["hkma_usdcny_closure_return"] - (7.07 / 7.01 - 1.0)) < 1e-12


def test_hkma_start_falls_back_to_latest_observation_not_after_previous_china_day() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-22", "2020-01-24"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-22"]),
    })
    fx = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-21", "2020-01-23"]),
        "usdcny_hk": [7.00, 7.05],
    })
    out = v4.add_hkma_closure_return(panel, fx)
    r = out.iloc[1]
    assert r["hkma_start_date"] == pd.Timestamp("2020-01-21")
    assert r["hkma_end_date"] == pd.Timestamp("2020-01-23")
    assert r["hkma_interval_count"] == 1
    assert abs(r["hkma_usdcny_closure_return"] - (7.05 / 7.00 - 1.0)) < 1e-12
