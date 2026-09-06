from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_protocol_v1.json"
SELECTED = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase2_selected_v1.json"
RUNNER = ROOT / "scripts/fit_gap_fill_v2_selected_dev.py"


def test_final_fit_binds_exact_selected_geometry_architecture() -> None:
    p = json.loads(PROTOCOL.read_text())
    s = json.loads(SELECTED.read_text())
    assert p["selected_architecture"]["selected_architecture_sha256"] == "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
    assert p["selected_architecture"]["git_blob_sha"] == "17599d3f77861febf373b2ea05cd16131ceac5e8"
    assert s["selected_architecture_sha256"] == "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
    for sign in ["high", "low"]:
        assert s["selected_heads"][sign]["selected_feature_set"] == "geometry_only"
        assert s["selected_heads"][sign]["features"] == ["abs_gap", "abs_gap_over_rvol20"]
        assert p["features"][sign] == ["abs_gap", "abs_gap_over_rvol20"]


def test_final_fit_is_identity_freeze_not_selection() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["no_model_selection"] is True
    assert p["development_window"] == "2015-01-05_to_2025-12-31"
    assert p["training_inventory"]["material_gap_threshold"] == "none_for_training"
    assert p["fixed_estimator"]["LogisticRegression"]["C"] == 1.0
    assert p["fixed_estimator"]["LogisticRegression"]["penalty"] == "l2"
    assert p["fixed_estimator"]["LogisticRegression"]["solver"] == "lbfgs"
    assert p["fixed_estimator"]["LogisticRegression"]["class_weight"] is None
    assert p["fixed_estimator"]["probability_calibration"] == "none"
    assert p["fixed_estimator"]["binary_threshold"] is None


def test_final_fit_runtime_dependencies_are_minimal() -> None:
    text = RUNNER.read_text()
    assert 'FEATURES = ["abs_gap", "abs_gap_over_rvol20"]' in text
    assert 'close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()' in text
    assert "diagnose_high_open" not in text
    assert "FRED" not in text
    assert "OFFSHORE" not in text
    assert "v1_direction" not in text.lower()
    assert "post_09:31" not in text.lower()


def test_final_fit_runner_is_fail_closed_on_2026_and_search() -> None:
    text = RUNNER.read_text()
    assert '"model_selection_performed": False' in text
    assert '"hyperparameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"probability_calibration_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_repeat_validation_opened": False' in text
    assert 'EXPECTED_PANEL_SHA = "f2587a528a517052016b646b58c734569b64a87766ff096575f353587e46aed1"' in text
    assert 'EXPECTED_MINUTES_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"' in text


def test_final_fit_environment_is_pinned() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["execution_environment"] == {
        "python": "3.11",
        "numpy": "2.4.6",
        "pandas": "3.0.5",
        "scipy": "1.17.1",
        "scikit_learn": "1.9.0",
        "pyarrow": "25.0.1",
    }


def test_final_fit_evidence_boundary_remains_closed() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["evidence_boundary"]["2026-01-05_to_2026-08-21"] == "must_remain_unopened_repeat_only_reserved"
    assert p["evidence_boundary"]["post_2026-08-21"] == "must_remain_unread_true_fresh"
    assert p["production_authority"] is False
