from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_cross_index_transport_protocol_v1.json"
RUNNER = ROOT / "scripts/run_gap_fill_cross_index_transport_dev.py"


def protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_identity_and_frozen_csi1000_reference():
    p = protocol()
    assert p["research_identity"] == "gap_fill_cross_index_transport_v1"
    assert p["stage"] == "CT-DEV_external_index_development_transport"
    assert p["frozen_csi1000_v2_v1"]["architecture_sha256"] == "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
    assert p["frozen_csi1000_v2_v1"]["parameter_bundle_sha256"] == "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"
    assert p["frozen_csi1000_v2_v1"]["must_not_be_modified"] is True


def test_external_dev_and_audit_boundaries_are_fixed():
    p = protocol()["indices"]
    assert p["CSI300"]["development_window"] == {"start": "2005-04-08", "end": "2010-12-31"}
    assert p["CSI500"]["development_window"] == {"start": "2007-01-15", "end": "2010-12-31"}
    assert p["CSI300"]["oof_validation_years"] == [2007, 2008, 2009, 2010]
    assert p["CSI500"]["oof_validation_years"] == [2009, 2010]
    for name in ["CSI300", "CSI500"]:
        assert p[name]["audit_a"] == {"start": "2011-01-01", "end": "2012-12-31", "sealed_now": True}
        assert p[name]["audit_b"] == {"start": "2013-01-01", "end": "2014-10-16", "sealed_now": True}
        assert p[name]["supporting_crosscheck"]["sealed_now"] is True


def test_common_full_240_clock_rule_is_fail_closed():
    p = protocol()["target_day_validity"]
    assert p["current_day_must_have_exact_complete_240_official_clocks"] is True
    assert p["duplicate_timestamp_count_must_be_zero"] is True
    assert p["missing_minutes_may_be_forward_filled"] is False
    assert p["missing_minutes_may_be_treated_as_non_events"] is False
    assert p["common_complete_240_row_inventory_for_all_three_horizons"] is True


def test_transport_modes_are_not_a_model_zoo():
    p = protocol()["transport_modes"]
    assert p["T1_exact_parameter_transport"]["refit"] is False
    assert p["T1_exact_parameter_transport"]["apply_frozen_csi1000_parameter_bundle"] is True
    t2 = p["T2_architecture_transport"]
    assert t2["refit"] is True
    assert t2["refit_scope"] == "each_external_index_development_window_only"
    assert t2["logistic_regression"]["C"] == 1.0
    assert t2["logistic_regression"]["solver"] == "lbfgs"
    assert t2["alternative_model_or_hyperparameter_search"] is False
    assert t2["probability_calibration"] == "none"
    assert t2["binary_threshold"] is None


def test_runner_hard_boundaries_and_no_raw_prediction_outputs():
    text = RUNNER.read_text(encoding="utf-8")
    assert "OVERNIGHT_HISTORICAL_INDEX_1M_LAKE" in text
    assert "audit_a_or_later_rows_loaded\": False" in text
    assert "csi1000_post_2026_08_21_outcomes_opened\": False" in text
    assert "raw_rows_written_to_repo\": False" in text
    assert "to_csv" not in text
    assert "to_parquet" not in text
    assert "XGBoost" not in text and "RandomForest" not in text


def test_ct_dev_outputs_and_next_stage():
    p = protocol()
    assert p["CT_DEV_outputs"] == [
        "docs/research/local_gap_fill_cross_index_transport_dev_receipt_v1.json",
        "docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json",
        "docs/governance/local_gap_fill_cross_index_transport_dev_data_usage_v1.json",
    ]
    assert p["next_stage_rule"] == "cloud_review_CT_DEV_before_any_Audit_A_open"
    assert p["audit_b_remains_sealed_after_CT_DEV"] is True
    assert p["fresh_oos"] is False
    assert p["production_authority"] is False
