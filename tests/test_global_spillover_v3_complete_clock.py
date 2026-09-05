from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "v3", ROOT / "scripts/research_global_spillover_v3_complete_clock.py"
)
v3 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v3)


def test_zero_us_interval_has_zero_closure_extra() -> None:
    panel = pd.DataFrame(
        {
            "trading_day": pd.to_datetime(["2020-01-20", "2020-01-21"]),
            "us_nasdaq": [0.0, 0.0],
            "us_vix_chg": [0.0, 0.0],
        }
    )
    # 2020-01-20 is represented as a missing weekday (MLK Day); therefore
    # both China boundaries see 2020-01-17 as the latest observed U.S. close.
    us = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-17", "2020-01-20"]),
            "NASDAQCOM": [100.0, np.nan],
            "VIXCLS": [20.0, np.nan],
        }
    )
    out = v3.add_complete_clock_features(panel, us)
    row = out.iloc[1]
    assert row["us_interval_count"] == 0
    assert row["us_nasdaq_complete_cum"] == 0
    assert row["us_vix_complete_cum"] == 0
    assert row["us_nasdaq_closure_extra"] == 0
    assert row["us_vix_closure_extra"] == 0


def test_one_us_interval_has_zero_closure_extra() -> None:
    panel = pd.DataFrame(
        {
            "trading_day": pd.to_datetime(["2020-01-02", "2020-01-03"]),
            "us_nasdaq": [0.0, 0.02],
            "us_vix_chg": [0.0, -0.01],
        }
    )
    us = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-12-31", "2020-01-01", "2020-01-02"]),
            "NASDAQCOM": [100.0, np.nan, 102.0],
            "VIXCLS": [20.0, np.nan, 19.8],
        }
    )
    out = v3.add_complete_clock_features(panel, us)
    row = out.iloc[1]
    assert row["us_interval_count"] == 1
    assert abs(row["us_nasdaq_closure_extra"]) < 1e-12
    assert abs(row["us_vix_closure_extra"]) < 1e-12


def test_multi_interval_extra_is_prior_unabsorbed_component() -> None:
    panel = pd.DataFrame(
        {
            "trading_day": pd.to_datetime(["2020-01-23", "2020-02-03"]),
            "us_nasdaq": [0.0, 0.0],
            "us_vix_chg": [0.0, 0.0],
        }
    )
    us = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-22", "2020-01-23", "2020-01-24", "2020-01-27", "2020-01-28", "2020-01-29", "2020-01-30", "2020-01-31"]),
            "NASDAQCOM": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0],
            "VIXCLS": [20.0, 19.0, 18.5, 19.5, 20.5, 21.0, 21.5, 22.0],
        }
    )
    out = v3.add_complete_clock_features(panel, us)
    row = out.iloc[1]
    assert row["us_interval_count"] == 7
    expected_cum = 107.0 / 100.0 - 1.0
    expected_daily = 107.0 / 106.0 - 1.0
    assert abs(row["us_nasdaq_complete_cum"] - expected_cum) < 1e-12
    assert abs(row["us_nasdaq_closure_extra"] - (expected_cum - expected_daily)) < 1e-12
