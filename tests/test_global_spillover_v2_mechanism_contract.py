from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/governance/global_spillover_v2_mechanism_preregistration.json"
SCRIPT = ROOT / "scripts/research_global_spillover_v2_mechanism.py"
PANEL = ROOT / "data/development/csi1000_open_pit_panel.parquet"


def _module():
    spec = importlib.util.spec_from_file_location("spillover_v2", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v2_preregistration_is_bounded_and_nonproduction() -> None:
    p = json.loads(PREREG.read_text())
    assert p["multiplicity_attempts"] == 8
    assert len(p["candidate_family"]) == 8
    assert p["no_grid_search"] is True
    assert p["authority"]["fresh_oos"] is False
    assert p["authority"]["baseline_replacement"] is False
    assert p["authority"]["production"] is False


def test_v2_duplicate_placebo_contains_exactly_zero_new_information() -> None:
    mod = _module()
    panel = pd.read_parquet(PANEL).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"]).dt.normalize()
    us = mod._load_us()
    df = mod._add_diagnostic_features(mod._add_cumulative_windows(panel, us))
    assert np.allclose(
        pd.to_numeric(df["us_nasdaq_duplicate"], errors="coerce"),
        pd.to_numeric(df["us_nasdaq"], errors="coerce"),
        equal_nan=True,
    )
    assert np.allclose(
        pd.to_numeric(df["us_vix_chg_duplicate"], errors="coerce"),
        pd.to_numeric(df["us_vix_chg"], errors="coerce"),
        equal_nan=True,
    )


def test_v2_cumulative_window_is_causal_and_bounded() -> None:
    mod = _module()
    panel = pd.read_parquet(PANEL).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"]).dt.normalize()
    us = mod._load_us()
    df = mod._add_cumulative_windows(panel, us)
    assert df["trading_day"].max() <= pd.Timestamp("2020-12-31")
    assert us["us_date"].max() <= pd.Timestamp("2020-12-31")
    end = df["_us_end_date"].notna()
    assert (df.loc[end, "_us_end_date"] < df.loc[end, "trading_day"]).all()
    start = df["_us_start_date"].notna() & df["previous_china_day"].notna()
    assert (df.loc[start, "_us_start_date"] < df.loc[start, "previous_china_day"]).all()
    assert (pd.to_numeric(df["us_session_intervals"], errors="coerce") >= 2).any()
