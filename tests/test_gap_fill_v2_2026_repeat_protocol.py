from pathlib import Path
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_2026_repeat_protocol_v1.json"
PARAMETERS = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
RUNNER = ROOT / "scripts/evaluate_local_gap_fill_v2_2026_repeat.py"


def test_repeat_protocol_binds_exact_v2_parameter_identity() -> None:
    p = json.loads(PROTOCOL.read_text())
    f = json.loads(PARAMETERS.read_text())
    assert p["scientific_role"] == "repeat_only_not_fresh"
    assert p["frozen_model"]["selected_architecture_sha256"] == "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
    assert p["frozen_model"]["parameter_bundle_sha256"] == "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"
    assert p["frozen_model"]["parameter_artifact_git_blob_sha"] == "eef7a9af6d42ee2faf53dbd16dce0b15ebfd10ed"
    assert f["selected_architecture_sha256"] == p["frozen_model"]["selected_architecture_sha256"]
    assert f["parameter_bundle_sha256"] == p["frozen_model"]["parameter_bundle_sha256"]


def test_repeat_window_and_fresh_boundary_are_frozen() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["validation_window"] == {
        "start": "2026-01-05",
        "end": "2026-08-21",
        "endpoint_is_frozen": True,
        "post_2026_08_21": "must_not_be_loaded",
    }
    assert p["fresh_oos"] is False
    assert p["production_authority"] is False
    assert p["raw_2026_rows_must_not_be_committed"] is True


def test_repeat_runtime_features_and_frozen_benchmark_are_exact() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["frozen_model"]["features"] == ["abs_gap", "abs_gap_over_rvol20"]
    b = p["fixed_development_empirical_benchmark"]
    assert b["high"] == {
        "h15": 0.4395501405810684,
        "h60": 0.22742474916387959,
        "hEOD": 0.2532467532467532,
    }
    assert b["low"] == {
        "h15": 0.49715729627289956,
        "h60": 0.3165829145728643,
        "hEOD": 0.32169117647058826,
    }


def test_repeat_gates_are_frozen_before_open() -> None:
    p = json.loads(PROTOCOL.read_text())
    gates = p["repeat_confirmation_gate_per_sign"]
    assert set(gates) == {
        "pooled_all_integrated_brier_strictly_lower_than_frozen_empirical_benchmark",
        "pooled_all_integrated_log_loss_strictly_lower_than_frozen_empirical_benchmark",
        "pooled_gt10_integrated_brier_strictly_lower_than_frozen_empirical_benchmark",
        "pooled_gt30_integrated_brier_not_higher_than_frozen_empirical_benchmark",
        "gt10_at_least_2_of_3_horizon_brier_scores_strictly_lower_than_benchmark",
        "monotonicity_violations_zero",
    }
    assert all(v is True for v in gates.values())


def test_repeat_runner_is_evaluation_only_and_fail_closed() -> None:
    text = RUNNER.read_text()
    assert 'EXPECTED_PARAMETER_BUNDLE_SHA = "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"' in text
    assert 'VAL_END = "2026-08-21"' in text
    assert 'require_local_path("OVERNIGHT_ANNOTATED_PANEL")' in text
    assert 'require_local_path("OVERNIGHT_DATAHUB_1M")' in text
    assert '"model_refit_performed": False' in text
    assert '"scaler_refit_performed": False' in text
    assert '"hyperparameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"probability_calibration_layer_fit_or_applied": False' in text
    assert '"post_2026_08_21_rows_loaded": False' in text
    assert "LogisticRegression" not in text
    assert ".fit(" not in text


def test_sealed_forward_probability_formula_is_monotone() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_local_gap_fill_v2_2026_repeat as mod

    fake_stage = {
        "scaler": {"mean": [0.0, 0.0], "scale": [1.0, 1.0]},
        "logistic": {"coef": [0.0, 0.0], "intercept": 0.0},
    }
    head = {"stages": {"15m": fake_stage, "60m": fake_stage, "eod": fake_stage}}
    x = np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=float)
    p15, p60, peod = mod.cumulative_probs(head, x)
    assert np.allclose(p15, 0.5)
    assert np.allclose(p60, 0.75)
    assert np.allclose(peod, 0.875)
    assert np.all(p15 <= p60)
    assert np.all(p60 <= peod)
