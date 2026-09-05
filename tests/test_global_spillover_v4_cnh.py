from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v4", ROOT / "scripts/research_global_spillover_v4_cnh.py")
v4 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v4)


def test_cnh_zero_interval_is_zero_extra() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-20", "2020-01-21"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-20"]),
    })
    cnh = pd.DataFrame({"date": pd.to_datetime(["2020-01-17"]), "close": [7.0]})
    out = v4.add_cnh_closure_extra(panel, cnh)
    r = out.iloc[1]
    assert r["cnh_interval_count"] == 0
    assert r["usdcnh_closure_extra"] == 0


def test_cnh_one_interval_is_zero_extra() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-02", "2020-01-03"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-02"]),
    })
    cnh = pd.DataFrame({
        "date": pd.to_datetime(["2019-12-31", "2020-01-02"]),
        "close": [7.0, 7.07],
    })
    out = v4.add_cnh_closure_extra(panel, cnh)
    r = out.iloc[1]
    assert r["cnh_interval_count"] == 1
    assert abs(r["usdcnh_closure_extra"]) < 1e-12


def test_cnh_multi_interval_extra_excludes_final_daily_move() -> None:
    panel = pd.DataFrame({
        "trading_day": pd.to_datetime(["2020-01-23", "2020-02-03"]),
        "previous_china_day": pd.to_datetime([pd.NaT, "2020-01-23"]),
    })
    cnh = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-22", "2020-01-23", "2020-01-24", "2020-01-27", "2020-01-28", "2020-01-29", "2020-01-30", "2020-01-31"]),
        "close": [7.00, 7.01, 7.02, 7.03, 7.04, 7.05, 7.06, 7.07],
    })
    out = v4.add_cnh_closure_extra(panel, cnh)
    r = out.iloc[1]
    expected_cum = 7.07 / 7.00 - 1
    expected_daily = 7.07 / 7.06 - 1
    assert r["cnh_interval_count"] == 7
    assert abs(r["usdcnh_complete_cum"] - expected_cum) < 1e-12
    assert abs(r["usdcnh_closure_extra"] - (expected_cum - expected_daily)) < 1e-12
