from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("a50_extract", ROOT / "scripts/refresh_external_sgx_a50_holiday_endpoints.py")
a50 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(a50)


def test_old_fixed_width_cn_price_is_scaled_once() -> None:
    assert a50.normalize_price("0001049000") == 10490.0
    assert a50.normalize_price("13550") == 13550.0
    assert a50.normalize_price("13412.5") == 13412.5


def test_choose_nearest_nonpast_traded_contract() -> None:
    summary = {
        "contracts": {
            "2020-01": {"delivery_year": 2020, "delivery_month": 1, "last_le_150000": None},
            "2020-02": {"delivery_year": 2020, "delivery_month": 2, "last_le_150000": {"time": "145959", "price": 13000.0}},
            "2020-03": {"delivery_year": 2020, "delivery_month": 3, "last_le_150000": {"time": "145958", "price": 13100.0}},
        }
    }
    chosen = a50.choose_contract(summary, pd.Timestamp("2020-01-23"))
    assert chosen is not None
    assert chosen[0] == "2020-02"


def test_choose_contract_never_uses_expired_calendar_month() -> None:
    summary = {
        "contracts": {
            "2019-12": {"delivery_year": 2019, "delivery_month": 12, "last_le_150000": {"time": "145959", "price": 12000.0}},
            "2020-01": {"delivery_year": 2020, "delivery_month": 1, "last_le_150000": {"time": "145959", "price": 12100.0}},
        }
    }
    chosen = a50.choose_contract(summary, pd.Timestamp("2020-01-02"))
    assert chosen is not None
    assert chosen[0] == "2020-01"
