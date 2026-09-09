from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_b_protocol_v1.json"
RUNNER = ROOT / "scripts/evaluate_gap_fill_cross_index_audit_b.py"


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_identity_role_and_audit_a_authorization():
    p = protocol()
    assert p["research_identity"] == "gap_fill_cross_index_transport_v1"
    assert p["stage"] == "CT_AUDIT_B_preregistered_unopened"
    assert p["scientific_role"] == "final_backward_historical_external_confirmation"
    assert p["audit_a_opened"] is True
    assert p["audit_b_opened"] is False
    assert p["audit_a_decision"] == "CT_AUDIT_A_cloud_review_passed_all_four_heads_Audit_B_eligible"
    assert "only_to_authorize_Audit_B_open" in p["audit_a_result_use_rule"]


def test_frozen_parameter_identities_are_unchanged_since_dev():
    p = protocol()["frozen_external_parameter_artifact"]
    assert p["sha256"] == "0cc74f79d9e9f26d1b9d8d554c96db0207a63d68787cceff1152dd71d26ae992"
    assert p["CSI300_parameter_bundle_sha256"] == "87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb"
    assert p["CSI500_parameter_bundle_sha256"] == "6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957"
    assert p["training_cutoff"] == "2010-12-31"
    assert p["must_not_be_refit_on_Audit_A_or_Audit_B"] is True


def test_audit_b_calendar_is_fixed_and_crosscheck_is_separate():
    p = protocol()
    for name in ["CSI300", "CSI500"]:
        w = p["audit_b_window"][name]
        assert w["start"] == "2013-01-01"
        assert w["end"] == "2014-10-16"
    assert p["supporting_crosscheck_opened"] is False
    assert p["audit_b_decision_rule"]["supporting_crosscheck_cannot_replace_or_rescue_Audit_B"] is True


def test_target_and_feature_contract_match_previous_generation():
    p = protocol()
    assert p["features"]["names"] == ["abs_gap", "abs_gap_over_rvol20"]
    assert p["target_day_validity"]["current_day_must_have_exact_complete_240_official_clocks"] is True
    assert p["target_day_validity"]["missing_minutes_may_be_forward_filled"] is False
    assert p["target_day_validity"]["missing_minutes_may_be_treated_as_non_events"] is False
    assert p["target_contract"]["fill_15m"] == "09:31_through_09:45_inclusive"
    assert p["target_contract"]["fill_60m"] == "09:31_through_10:30_inclusive"
    assert p["target_contract"]["nested_invariant"] == "fill_15m<=fill_60m<=fill_eod"


def test_sample_sufficiency_and_six_gates_are_frozen():
    p = protocol()
    s = p["sample_sufficiency_per_index_sign"]
    assert s["minimum_all_nonzero_gap_rows"] == 25
    assert s["minimum_abs_gap_gt_10bp_rows"] == 20
    assert s["minimum_abs_gap_gt_30bp_rows"] == 12
    gates = p["primary_T2_gate_per_index_sign"]
    assert len(gates) == 6
    assert all(gates.values())
    assert p["audit_b_decision_rule"]["CT_AUDIT_B_final_backward_external_robustly_confirmed"] == "all_four_index_sign_heads_are_sample_sufficient_and_pass_all_six_primary_T2_gates"
    assert p["audit_b_decision_rule"]["no_posthoc_partial_rescue"] is True


def test_runner_is_forward_only_no_fit_and_hard_denies_crosscheck():
    text = RUNNER.read_text(encoding="utf-8")
    assert ".fit(" not in text
    assert 'HISTORY_START = "2012-10-01"' in text
    assert 'AUDIT_START = "2013-01-01"' in text
    assert 'AUDIT_END = "2014-10-16"' in text
    assert 'SUPPORTING_CROSSCHECK_START = "2014-10-17"' in text
    assert 'frame["trading_day"] >= SUPPORTING_CROSSCHECK_START' in text
    assert '"supporting_crosscheck_opened": False' in text
    assert '"csi1000_post_2026_08_21_outcomes_opened": False' in text


def test_runner_uses_fixed_dev_benchmark_and_no_audit_a_retraining():
    text = RUNNER.read_text(encoding="utf-8")
    assert "dev_benchmark" in text
    assert 'stages["15m"]' not in text  # benchmark helper binds through bundle heads/sign stages
    assert 's = bundle["heads"][sign]["stages"]' in text
    assert 'EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256' in text
    assert 'canonical_digest(item["parameter_bundle"])' in text


def test_runner_has_fail_closed_insufficient_evidence_and_final_decision_labels():
    text = RUNNER.read_text(encoding="utf-8")
    assert 'decision = "CT_AUDIT_B_evidence_insufficient"' in text
    assert 'decision = "CT_AUDIT_B_final_backward_external_robustly_confirmed"' in text
    assert 'decision = "CT_AUDIT_B_final_backward_external_not_confirmed"' in text
    assert '"audit_b_passed": False' in text


def test_required_outputs_are_only_aggregate_audit_b_files():
    p = protocol()
    assert p["required_outputs"] == [
        "docs/research/local_gap_fill_cross_index_transport_audit_b_receipt_v1.json",
        "docs/governance/local_gap_fill_cross_index_transport_audit_b_data_usage_v1.json",
    ]
    text = RUNNER.read_text(encoding="utf-8")
    assert "local_gap_fill_cross_index_transport_audit_b_receipt_v1.json" in text
    assert "local_gap_fill_cross_index_transport_audit_b_data_usage_v1.json" in text
