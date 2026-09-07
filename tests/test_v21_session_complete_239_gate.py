from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/v21_session_complete_239_gate.py"
CONTRACT = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_future_audit_source_admission_v1.json"
STATE = ROOT / "docs/governance/gap_fill_v21_state_v1.json"

spec = spec_from_file_location("v21_session_complete_239_gate", GATE_PATH)
assert spec and spec.loader
mod = module_from_spec(spec)
spec.loader.exec_module(mod)


def test_required_clock_set_is_old_240_minus_only_1459():
    old = set(mod.legacy_expected_240_clocks())
    required = set(mod.required_session_complete_239_clocks())
    assert len(old) == 240
    assert len(required) == 239
    assert old - required == {"14:59"}
    assert "09:31" in required
    assert "11:30" in required
    assert "13:01" in required
    assert "15:00" in required


def test_gate_accepts_required_239_and_optional_1459():
    required = list(mod.required_session_complete_239_clocks())
    r239 = mod.evaluate_session_complete_239(required)
    r240 = mod.evaluate_session_complete_239(required + ["14:59"])
    assert r239.accepted is True
    assert r239.optional_1459_present is False
    assert r240.accepted is True
    assert r240.optional_1459_present is True


def test_gate_is_not_generic_len_239_and_fails_mid_session_missing():
    required = list(mod.required_session_complete_239_clocks())
    # Same row count as the required contract, but replace a required middle
    # clock with the optional 14:59.  This must fail closed.
    altered = [c for c in required if c != "13:22"] + ["14:59"]
    assert len(altered) == 239
    result = mod.evaluate_session_complete_239(altered)
    assert result.accepted is False
    assert result.reason == "missing_required_session_clock"
    assert result.missing_required_clocks == ("13:22",)


def test_gate_fails_duplicate_and_unexpected_clocks():
    required = list(mod.required_session_complete_239_clocks())
    duplicate = mod.evaluate_session_complete_239(required + ["09:31"])
    unexpected = mod.evaluate_session_complete_239(required + ["09:30"])
    assert duplicate.accepted is False
    assert duplicate.reason == "duplicate_session_clock"
    assert unexpected.accepted is False
    assert unexpected.reason == "unexpected_target_session_clock"


def test_cloud_admission_contract_matches_reported_package_identity():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["reported_package"]["relative_path"] == (
        "data/v21_future_audit_csi_index_1m_session_complete_2019_2024/"
        "csi300_csi500_1m.parquet"
    )
    assert c["reported_package"]["rows"] == 695_929
    assert c["reported_package"]["sha256"] == "3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c"
    assert c["reported_package"]["parent_he00_v8_sha256"] == "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
    assert c["reported_package"]["calendar_days_per_symbol"] == 1456
    assert c["reported_package"]["expected_rows_if_all_days_pass_239"] == 695_968
    assert c["reported_package"]["reported_missing_required_rows_total"] == 39
    assert c["reported_package"]["symbols"]["000300.SH"] == {
        "session_complete_days": 1449,
        "incomplete_days": 7,
    }
    assert c["reported_package"]["symbols"]["000905.SH"] == {
        "session_complete_days": 1448,
        "incomplete_days": 8,
    }


def test_contract_preserves_rd1_and_keeps_dev_sealed():
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert c["gate"]["required_clock_count"] == 239
    assert c["gate"]["systematic_optional_clock"] == "14:59"
    assert c["gate"]["generic_len_239_rule"] is False
    assert c["gate"]["imputation_allowed"] is False
    assert c["historical_rd1_runner_must_change"] is False
    assert c["V21_DEV_outcomes_open_authorized"] is False
    assert c["successor_model_fit_authorized"] is False
    assert c["successor_model_selection_authorized"] is False

    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["sealed"]["V21_DEV_outcomes"] is True
    assert state["successor_model_fit_authorized"] is False
    assert state["successor_model_selection_authorized"] is False
