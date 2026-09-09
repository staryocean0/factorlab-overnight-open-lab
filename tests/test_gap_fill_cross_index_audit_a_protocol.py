from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_a_protocol_v1.json"
RUNNER = ROOT / "scripts/evaluate_gap_fill_cross_index_audit_a.py"


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_audit_a_windows_and_audit_b_sealed():
    p = protocol()
    assert p["stage"] == "CT_AUDIT_A_preregistered_unopened"
    assert p["audit_a_window"]["CSI300"] == {"symbol": "000300.SH", "start": "2011-01-01", "end": "2012-12-31"}
    assert p["audit_a_window"]["CSI500"] == {"symbol": "000905.SH", "start": "2011-01-01", "end": "2012-12-31"}
    assert p["audit_a_opened"] is False
    assert p["audit_b_opened"] is False


def test_frozen_parameter_identities_and_no_refit_contract():
    p = protocol()
    f = p["frozen_external_parameter_artifact"]
    assert f["sha256"] == "0cc74f79d9e9f26d1b9d8d554c96db0207a63d68787cceff1152dd71d26ae992"
    assert f["CSI300_parameter_bundle_sha256"] == "87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb"
    assert f["CSI500_parameter_bundle_sha256"] == "6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957"
    assert p["transport_modes"]["T2_frozen_external_index_parameter_transport"]["refit"] is False
    assert p["transport_modes"]["T2_frozen_external_index_parameter_transport"]["recalibration"] is False


def test_gate_and_sample_sufficiency_are_frozen():
    p = protocol()
    s = p["sample_sufficiency_per_index_sign"]
    assert s["minimum_all_nonzero_gap_rows"] == 25
    assert s["minimum_abs_gap_gt_10bp_rows"] == 20
    assert s["minimum_abs_gap_gt_30bp_rows"] == 12
    gates = p["primary_T2_gate_per_index_sign"]
    assert len(gates) == 6
    assert all(gates.values())
    assert p["audit_a_decision_rule"]["open_Audit_B"] == "all_four_index_sign_heads_are_sample_sufficient_and_pass_all_six_primary_T2_gates"
    assert p["audit_a_decision_rule"]["no_posthoc_partial_rescue"] is True


def test_runner_is_forward_only_and_hard_denies_audit_b():
    text = RUNNER.read_text(encoding="utf-8")
    assert ".fit(" not in text
    assert "AUDIT_END = \"2012-12-31\"" in text
    assert "frame[\"trading_day\"] >= \"2013-01-01\"" in text
    assert "audit_b_opened\": False" in text
    assert "supporting_crosscheck_opened\": False" in text
    assert "csi1000_post_2026_08_21_outcomes_opened\": False" in text


def test_runner_uses_fixed_dev_event_rate_benchmark_and_exact_240():
    text = RUNNER.read_text(encoding="utf-8")
    assert "event_rate" in text
    assert "dev_benchmark" in text
    assert "exact_240" in text
    assert "set(present) == expected_set" in text
    assert "not_exact_complete_240_clocks" in text
    assert "safe_eval" in text


def test_t1_cannot_promote_and_audit_b_needs_all_four_heads():
    p = protocol()
    assert p["transport_modes"]["T1_exact_CSI1000_parameter_transport"]["promotion_gate"] is False
    text = RUNNER.read_text(encoding="utf-8")
    assert "len(head_suff) == 4 and all(head_suff)" in text
    assert "len(head_pass) == 4 and all(head_pass)" in text
    assert "audit_b_eligibility_under_frozen_rule" in text
