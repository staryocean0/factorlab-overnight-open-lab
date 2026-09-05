from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import research_global_spillover_v8_regime as v8  # noqa: E402


def test_interaction_is_exact_raw_product_and_zero_on_holiday() -> None:
    df = pd.DataFrame({
        "a50_ordinary_preauction_closure_return": [0.01, -0.02, 0.0],
        "rvol20": [0.30, 0.50, 0.70],
        "holiday_reopen": [0, 0, 1],
    })
    got = v8.add_interaction(df)
    assert got[v8.INTERACTION].tolist() == [0.003, -0.01, 0.0]


def test_interaction_does_not_recenter_or_bucket_state() -> None:
    df = pd.DataFrame({
        "a50_ordinary_preauction_closure_return": [0.02, 0.02],
        "rvol20": [1.0, 2.0],
        "holiday_reopen": [0, 0],
    })
    got = v8.add_interaction(df)
    assert got[v8.INTERACTION].tolist() == [0.02, 0.04]


def test_v8_does_not_mutate_main_effect_columns() -> None:
    df = pd.DataFrame({
        "a50_ordinary_preauction_closure_return": [0.01],
        "rvol20": [0.5],
        "holiday_reopen": [0],
    })
    got = v8.add_interaction(df)
    assert got.loc[0, "a50_ordinary_preauction_closure_return"] == 0.01
    assert got.loc[0, "rvol20"] == 0.5
