from pathlib import Path
import json
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_v21_source_to_dev_metadata_controller as ctl
import v21_session_complete_239_gate as gate

PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_source_to_dev_metadata_controller_v1.json"


def _rows(symbol: str, day: str, clocks: list[str]) -> list[dict]:
    return [
        {
            "symbol": symbol,
            "trading_day": day,
            "timestamp": f"{day}T{clock}:00Z",
            "open": 999999.0,
            "high": 999999.0,
            "low": 999999.0,
            "close": 999999.0,
        }
        for clock in clocks
    ]


def test_protocol_hard_stops_before_dev_outcomes():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert p["metadata_columns_only"] == ["symbol", "trading_day", "timestamp"]
    assert p["hard_stop_after_outputs"] is True
    assert p["V21_DEV_outcomes_open_authorized"] is False
    assert p["successor_model_fit_authorized"] is False
    assert p["successor_model_selection_authorized"] is False
    assert p["Audit_A_outcomes_open_authorized"] is False
    assert p["Audit_B_outcomes_open_authorized"] is False


def test_read_metadata_does_not_load_ohlc(tmp_path):
    required = list(gate.required_session_complete_239_clocks())
    frame = pd.DataFrame(
        _rows("000300.SH", "2015-01-05", required)
        + _rows("000905.SH", "2015-01-05", required)
    )
    path = tmp_path / "sample.parquet"
    frame.to_parquet(path, index=False)
    got = ctl.read_metadata(path, start="2015-01-01", end="2015-12-31")
    assert list(got.columns) == ["symbol", "trading_day", "timestamp"]
    assert "open" not in got.columns
    assert "high" not in got.columns
    assert "low" not in got.columns
    assert "close" not in got.columns


def test_audit_frame_accepts_optional_1459_absence_and_rejects_middle_hole():
    required = list(gate.required_session_complete_239_clocks())
    bad = [clock for clock in required if clock != "13:22"]
    frame = pd.DataFrame(
        _rows("000300.SH", "2015-01-05", required)
        + _rows("000300.SH", "2015-01-06", bad)
        + _rows("000905.SH", "2015-01-05", required)
        + _rows("000905.SH", "2015-01-06", required + ["14:59"])
    )[["symbol", "trading_day", "timestamp"]]
    result = ctl.audit_frame(frame)
    assert result["by_symbol"]["000300.SH"]["session_complete_days"] == 1
    assert result["by_symbol"]["000300.SH"]["incomplete_days"] == 1
    detail = result["by_symbol"]["000300.SH"]["incomplete_day_details"][0]
    assert detail["missing_required_clocks"] == ["13:22"]
    assert result["by_symbol"]["000905.SH"]["session_complete_days"] == 2
    assert result["by_symbol"]["000905.SH"]["optional_1459_present_days"] == 1


def test_source_verification_constants_match_frozen_owner_report():
    assert ctl.EXPECTED_AUDIT_SHA == "3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c"
    assert ctl.EXPECTED_PARENT_SHA == "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
    assert ctl.EXPECTED_AUDIT_ROWS == 695_929
    assert ctl.EXPECTED_MISSING_REQUIRED_ROWS == 39
    assert ctl.EXPECTED_COVERAGE["000300.SH"] == {
        "observed_trading_days": 1456,
        "session_complete_days": 1449,
        "incomplete_days": 7,
    }
    assert ctl.EXPECTED_COVERAGE["000905.SH"] == {
        "observed_trading_days": 1456,
        "session_complete_days": 1448,
        "incomplete_days": 8,
    }


def test_controller_source_contains_no_dev_model_or_outcome_engine():
    text = (ROOT / "scripts/run_v21_source_to_dev_metadata_controller.py").read_text(encoding="utf-8")
    assert "LogisticRegression" not in text
    assert "v21_p2_overlay" not in text
    assert "v21_evaluation_kernel" not in text
    assert ".fit(" not in text
    assert 'columns=["symbol", "trading_day", "timestamp"]' in text
    assert '"V21_DEV_outcomes_opened": False' in text
    assert '"successor_model_fit_performed": False' in text
    assert '"successor_model_selection_performed": False' in text
