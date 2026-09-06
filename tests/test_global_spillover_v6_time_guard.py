from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "research_global_spillover_v6_daily_a50",
    SCRIPTS / "research_global_spillover_v6_daily_a50.py",
)
v6 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(v6)


def test_time_guard_accepts_float_values_created_by_left_merge() -> None:
    s = pd.Series([91459.0, 90000.0])
    out = v6._time_values_as_hhmmss_int(s)
    assert out.tolist() == [91459, 90000]
    assert not out.ge(91500).any()


def test_time_guard_rejects_actual_091500_or_later() -> None:
    s = pd.Series([91459.0, 91500.0])
    out = v6._time_values_as_hhmmss_int(s)
    assert out.ge(91500).any()


def test_time_guard_rejects_fractional_or_missing_time() -> None:
    with pytest.raises(AssertionError):
        v6._time_values_as_hhmmss_int(pd.Series([91459.5]))
    with pytest.raises(AssertionError):
        v6._time_values_as_hhmmss_int(pd.Series([float("nan")]))
