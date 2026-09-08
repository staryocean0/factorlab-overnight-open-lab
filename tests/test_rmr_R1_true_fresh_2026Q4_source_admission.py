from datetime import date
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import admit_rmr_R1_true_fresh_2026Q4_source as mod


def complete_day(day: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": [mod.SYMBOL] * 240,
            "trading_day": [day] * 240,
            "timestamp": [f"{day} {clock}:00" for clock in mod.expected_clocks()],
            "clock": list(mod.expected_clocks()),
        }
    )


def test_named_clock_gate_is_exact_240_and_not_v21_239():
    clocks = mod.expected_clocks()
    assert len(clocks) == 240
    assert len(set(clocks)) == 240
    assert clocks[0] == "09:31"
    assert clocks[119] == "11:30"
    assert clocks[120] == "13:01"
    assert clocks[-1] == "15:00"
    assert "14:59" in clocks


def test_date_guard_prevents_premature_admission():
    with pytest.raises(RuntimeError):
        mod.validate_execution_date(date(2026, 12, 31))
    mod.validate_execution_date(date(2027, 1, 1))


def test_exact_named_clock_and_calendar_equality_pass():
    days = ["2026-01-05", "2026-10-08"]
    frame = pd.concat([complete_day(d) for d in days], ignore_index=True)
    result = mod.audit(frame, days)
    assert result["passed"] is True
    assert result["complete_trading_days"] == 2
    assert result["incomplete_trading_days"] == 0
    assert result["total_metadata_rows"] == 480


def test_missing_named_clock_fails_even_if_day_exists():
    day = "2026-10-08"
    frame = complete_day(day).iloc[:-1].copy()
    result = mod.audit(frame, [day])
    assert result["passed"] is False
    assert result["incomplete_trading_days"] == 1
    assert "15:00" in result["incomplete_day_details"][day]["missing_clocks"]


def test_unexpected_or_duplicate_clock_fails():
    day = "2026-10-08"
    frame = complete_day(day)
    frame.loc[239, "clock"] = "14:59"
    frame.loc[239, "timestamp"] = f"{day} 14:59:30"
    result = mod.audit(frame, [day])
    assert result["passed"] is False
    assert result["duplicate_metadata_rows"] > 0


def test_calendar_json_support_and_context_start_gate(tmp_path):
    path = tmp_path / "calendar.json"
    path.write_text(json.dumps({"trading_days": ["2026-01-05", "2026-10-08"]}), encoding="utf-8")
    assert mod.read_calendar(path) == ["2026-01-05", "2026-10-08"]

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"trading_days": ["2026-01-06", "2026-10-08"]}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        mod.read_calendar(bad)


def test_protocol_forbids_ohlc_outcomes_and_auto_authorization():
    protocol = json.loads(
        (ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_source_admission_protocol_v1.json").read_text()
    )
    assert protocol["source"]["required_columns_for_metadata_admission_only"] == ["symbol", "trading_day", "timestamp"]
    assert protocol["source"]["OHLC_read_during_admission"] is False
    assert protocol["source"]["outcome_read_during_admission"] is False
    assert protocol["named_session_clock_gate"]["expected_clock_count_per_complete_day"] == 240
    assert protocol["named_session_clock_gate"]["V21_239_clock_exception_applies"] is False
    assert protocol["after_admission_pass"]["Q4_outcome_execution_automatically_authorized"] is False
