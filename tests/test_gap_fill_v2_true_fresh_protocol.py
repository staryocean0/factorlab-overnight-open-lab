from pathlib import Path
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_true_fresh_protocol_v1.json"
RUNNER = ROOT / "scripts/evaluate_gap_fill_v2_true_fresh_2026q4.py"
BASE = ROOT / "scripts/evaluate_local_gap_fill_v2_2026_repeat.py"


def test_true_fresh_window_is_complete_future_block() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["scientific_role"] == "true_fresh_oos"
    assert p["validation_window"] == {
        "start": "2026-08-24",
        "end": "2026-12-31",
        "complete_calendar_block_required": True,
        "partial_window_open_forbidden": True,
        "not_before_china_date": "2027-01-01",
        "post_2026_12_31": "outside_this_first_fresh_challenge",
    }
    assert p["fresh_window_opened"] is False
    assert p["fresh_oos"] is True
    assert p["production_authority"] is False


def test_true_fresh_binds_exact_frozen_v2_identity() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["frozen_model"]["selected_architecture_sha256"] == "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
    assert p["frozen_model"]["parameter_bundle_sha256"] == "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"
    assert p["frozen_model"]["parameter_artifact_git_blob_sha"] == "eef7a9af6d42ee2faf53dbd16dce0b15ebfd10ed"
    assert p["frozen_model"]["features"] == ["abs_gap", "abs_gap_over_rvol20"]
    assert p["frozen_scoring_implementation"]["base_evaluator_git_blob_sha"] == "d61e00efa6e605864c8153a1e7e577257f813939"


def test_true_fresh_gates_match_repeat_gate_shape() -> None:
    p = json.loads(PROTOCOL.read_text())
    gates = p["fresh_confirmation_gate_per_sign"]
    assert set(gates) == {
        "pooled_all_integrated_brier_strictly_lower_than_frozen_empirical_benchmark",
        "pooled_all_integrated_log_loss_strictly_lower_than_frozen_empirical_benchmark",
        "pooled_gt10_integrated_brier_strictly_lower_than_frozen_empirical_benchmark",
        "pooled_gt30_integrated_brier_not_higher_than_frozen_empirical_benchmark",
        "gt10_at_least_2_of_3_horizon_brier_scores_strictly_lower_than_benchmark",
        "monotonicity_violations_zero",
    }
    assert all(v is True for v in gates.values())


def test_true_fresh_sample_sufficiency_is_preregistered() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["sample_sufficiency_per_sign"] == {
        "minimum_all_nonzero_gap_rows": 25,
        "minimum_abs_gap_gt_10bp_rows": 20,
        "minimum_abs_gap_gt_30bp_rows": 12,
        "rule": "counts_use_only_observed_09:31_gap_state; if_insufficient_label_fresh_evidence_insufficient_and_do_not_extend_window_or_relax_thresholds",
    }


def test_true_fresh_runner_is_eval_only_and_has_premature_open_guard() -> None:
    text = RUNNER.read_text()
    assert 'FRESH_START = "2026-08-24"' in text
    assert 'FRESH_END = "2026-12-31"' in text
    assert 'NOT_BEFORE_CHINA_DATE = "2027-01-01"' in text
    assert 'require_source("OVERNIGHT_FRESH_ANNOTATED_PANEL")' in text
    assert 'require_source("OVERNIGHT_FRESH_DATAHUB_1M")' in text
    assert '"model_refit_performed": False' in text
    assert '"scaler_refit_performed": False' in text
    assert '"feature_selection_performed": False' in text
    assert '"hyperparameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"probability_calibration_layer_fit_or_applied": False' in text
    assert '"partial_window_scored": False' in text
    assert '"post_2026_12_31_rows_loaded": False' in text
    assert ".fit(" not in text


def test_true_fresh_reuses_frozen_scoring_functions() -> None:
    text = RUNNER.read_text()
    assert "import evaluate_local_gap_fill_v2_2026_repeat as base" in text
    assert "base.evaluate_sign" in text
    assert "base.build_targets" in text
    assert "base.load_local_minutes" in text
    assert BASE.exists()


def test_sample_sufficiency_transform_does_not_change_scientific_gates() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_gap_fill_v2_true_fresh_2026q4 as mod

    p = json.loads(PROTOCOL.read_text())
    gates = {k: True for k in p["fresh_confirmation_gate_per_sign"]}
    fake = {
        "n": 30,
        "n_gt10bp": 24,
        "n_gt30bp": 15,
        "repeat_confirmation_gates": gates,
        "repeat_confirmed": True,
    }
    out = mod.transform_result_to_fresh(fake, p)
    assert out["sample_sufficient"] is True
    assert out["fresh_confirmed"] is True
    assert out["fresh_confirmation_gates"] == gates

    fake2 = dict(fake)
    fake2["n_gt30bp"] = 11
    out2 = mod.transform_result_to_fresh(fake2, p)
    assert out2["sample_sufficient"] is False
    assert out2["fresh_confirmed"] is False


def test_frozen_base_cumulative_probability_formula_still_monotone() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import evaluate_local_gap_fill_v2_2026_repeat as base

    fake_stage = {
        "scaler": {"mean": [0.0, 0.0], "scale": [1.0, 1.0]},
        "logistic": {"coef": [0.0, 0.0], "intercept": 0.0},
    }
    head = {"stages": {"15m": fake_stage, "60m": fake_stage, "eod": fake_stage}}
    x = np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=float)
    p15, p60, peod = base.cumulative_probs(head, x)
    assert np.allclose(p15, 0.5)
    assert np.allclose(p60, 0.75)
    assert np.allclose(peod, 0.875)
