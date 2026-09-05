from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sgx_cn_tick", ROOT / "scripts/sgx_cn_tick.py")
sgx = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sgx)


def test_legacy_schema_resolves_price_and_Y_trade_from_header() -> None:
    header = "Comm\tContract Type\tMth Code\tYear\tStrike\tTrade Date\tLog Time\tPrice Ind\tPrice\tMsg Code\tAmend Code\tVolume"
    rows = [
        "CN\tF\tG\t2015\t0000000\t20150217\t084500\t\t0001084500\tA\t\t00001",
        "CN\tF\tG\t2015\t0000000\t20150217\t091459\t\t0001079000\tY\t\t00002",
        "CN\tF\tG\t2015\t0000000\t20150217\t091500\t\t0001080000\tY\t\t00003",
        "CN\tF\tG\t2015\t0000000\t20150217\t150000\t\t0001081000\tY\t\t00004",
        "CN\tF\tG\t2015\t0000000\t20150217\t160000\t\t0001082000\tS\t\t00005",
    ]
    out = sgx.parse_cn_rows(header, rows, "20150217")
    assert out["schema_id"] == "legacy_price_indicator_amend"
    assert out["canonical_indices"]["price"] == 8
    assert out["canonical_indices"]["msg_code"] == 9
    assert out["trade_code_counts"] == {"Y": 3}
    c = out["contracts"]["2015-02"]
    assert c["last_le_091459"] == {"time": "091459", "price": 10790.0}
    assert c["last_le_150000"] == {"time": "150000", "price": 10810.0}


def test_compact_schema_resolves_T_trade() -> None:
    header = "Comm\tContract_Type\tMth_Code\tYear\tStrike\tTrade_Date\tLog_Time\tPrice\tMsg_Code\tVolume"
    rows = [
        "CN\tF\tF\t2016\t0000000\t20160104\t084500\t0001049000\tA\t00001",
        "CN\tF\tF\t2016\t0000000\t20160104\t091400\t0001051000\tT\t00002",
        "CN\tF\tF\t2016\t0000000\t20160104\t091500\t0001052000\tT\t00003",
    ]
    out = sgx.parse_cn_rows(header, rows, "20160104")
    assert out["schema_id"] == "compact"
    assert out["canonical_indices"]["price"] == 7
    assert out["canonical_indices"]["msg_code"] == 8
    assert out["trade_code_counts"] == {"T": 2}
    assert out["contracts"]["2016-01"]["last_le_091459"] == {"time": "091400", "price": 10510.0}


def test_settlement_is_not_a_trade() -> None:
    header = "Comm\tContract Type\tMth Code\tYear\tStrike\tTrade Date\tLog Time\tPrice Ind\tPrice\tMsg Code\tAmend Code\tVolume"
    rows = ["CN\tF\tG\t2015\t0000000\t20150217\t090000\t\t0001084500\tS\t\t00001"]
    out = sgx.parse_cn_rows(header, rows, "20150217")
    assert out["eligible_trade_rows"] == 0
    assert out["contracts"] == {}


def test_nonblank_legacy_amend_trade_is_conservatively_excluded() -> None:
    header = "Comm\tContract Type\tMth Code\tYear\tStrike\tTrade Date\tLog Time\tPrice Ind\tPrice\tMsg Code\tAmend Code\tVolume"
    rows = [
        "CN\tF\tG\t2015\t0000000\t20150217\t090000\t\t0001084500\tY\tD\t00001",
        "CN\tF\tG\t2015\t0000000\t20150217\t090100\t\t0001084600\tY\t\t00001",
    ]
    out = sgx.parse_cn_rows(header, rows, "20150217")
    assert out["nonblank_trade_amend_rows"] == 1
    assert out["eligible_trade_rows"] == 1
    assert out["contracts"]["2015-02"]["last_le_091459"]["time"] == "090100"


def test_legacy_blank_price_trade_is_counted_and_skipped_without_invalidating_archive() -> None:
    header = "Comm\tContract Type\tMth Code\tYear\tStrike\tTrade Date\tLog Time\tPrice Ind\tPrice\tMsg Code\tAmend Code\tVolume"
    rows = [
        "CN\tF\tG\t2015\t0000000\t20150217\t090000\t\t\tY\t\t00001",
        "CN\tF\tG\t2015\t0000000\t20150217\t091459\t\t0001079000\tY\t\t00002",
        "CN\tF\tG\t2015\t0000000\t20150217\t150000\t\t0001081000\tY\t\t00003",
    ]
    out = sgx.parse_cn_rows(header, rows, "20150217")
    assert out["blank_price_trade_rows"] == 1
    assert out["trade_code_counts"] == {"Y": 3}
    assert out["eligible_trade_rows"] == 2
    c = out["contracts"]["2015-02"]
    assert c["last_le_091459"] == {"time": "091459", "price": 10790.0}
    assert c["last_le_150000"] == {"time": "150000", "price": 10810.0}


def test_choose_contract_is_nearest_nonpast_with_prior_close_trade() -> None:
    summary = {
        "contracts": {
            "2019-12": {"delivery_year": 2019, "delivery_month": 12, "last_le_150000": {"time": "145900", "price": 12000.0}},
            "2020-01": {"delivery_year": 2020, "delivery_month": 1, "last_le_150000": None},
            "2020-02": {"delivery_year": 2020, "delivery_month": 2, "last_le_150000": {"time": "145959", "price": 13000.0}},
            "2020-03": {"delivery_year": 2020, "delivery_month": 3, "last_le_150000": {"time": "145958", "price": 13100.0}},
        }
    }
    chosen = sgx.choose_contract(summary, pd.Timestamp("2020-01-23"))
    assert chosen is not None
    assert chosen[0] == "2020-02"


def test_normalize_price_scaled_exactly_once() -> None:
    assert sgx.normalize_price("0001049000") == 10490.0
    assert sgx.normalize_price("13550") == 13550.0
    assert sgx.normalize_price("13412.5") == 13412.5
