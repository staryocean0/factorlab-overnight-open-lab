from pathlib import Path
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase2_hazard_family_v1.json"
RUNNER = ROOT / "scripts/select_gap_fill_v2_phase2_hazard_family.py"


def test_phase2_family_is_bounded_and_separate_by_sign() -> None:
    p = json.loads(FAMILY.read_text())
    assert p["candidate_family"]["multiplicity"] == 4
    assert p["selection_is_independent_by_sign"] is True if "selection_is_independent_by_sign" in p else p["candidate_family"]["selection_is_independent_by_sign"] is True
    assert p["candidate_family"]["high"]["geometry_only"] == ["abs_gap", "abs_gap_over_rvol20"]
    assert p["candidate_family"]["low"]["geometry_only"] == ["abs_gap", "abs_gap_over_rvol20"]
    assert p["candidate_family"]["high"]["phase1_full"] == [
        "abs_gap",
        "abs_gap_over_rvol20",
        "v1_direction_support",
        "nasdaq_interval_support",
        "vix_interval_support",
        "prior_daytime_alignment",
        "prior_last_hour_alignment",
    ]
    assert p["candidate_family"]["low"]["phase1_full"] == [
        "abs_gap",
        "abs_gap_over_rvol20",
        "v1_direction_support",
        "nasdaq_interval_support",
        "vix_interval_support",
    ]


def test_phase2_estimator_and_time_boundary_are_frozen() -> None:
    p = json.loads(FAMILY.read_text())
    e = p["fixed_estimator"]
    assert e["C"] == 1.0
    assert e["penalty"] == "l2"
    assert e["solver"] == "lbfgs"
    assert e["class_weight"] is None
    assert p["time_structure"]["hazard_oof_validation_years"] == list(range(2017, 2026))
    assert p["evidence_boundary"]["repeat_only_reserved"] == "2026-01-05_to_2026-08-21"
    assert p["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    assert p["production_authority"] is False


def test_phase2_excluded_features_do_not_enter_candidate_family() -> None:
    p = json.loads(FAMILY.read_text())
    all_features = set(p["candidate_family"]["high"]["phase1_full"] + p["candidate_family"]["low"]["phase1_full"])
    for name in [
        "v1_magnitude_surprise",
        "broad_china_specific_support",
        "prior_gap_alignment",
    ]:
        assert name not in all_features
    assert "prior_daytime_alignment" not in p["candidate_family"]["low"]["phase1_full"]
    assert "prior_last_hour_alignment" not in p["candidate_family"]["low"]["phase1_full"]


def test_phase2_runner_is_fail_closed_on_search_and_2026() -> None:
    text = RUNNER.read_text()
    assert 'EXPECTED_DIRECTION_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"' in text
    assert 'VALID_YEARS = list(range(2017, 2026))' in text
    assert '"hyperparameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"model_class_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_repeat_validation_opened": False' in text
    assert "v1_magnitude_surprise" not in text
    assert "broad_china_specific_support" not in text
    assert "prior_gap_alignment" not in text


def test_cumulative_hazard_formula_is_monotone() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import select_gap_fill_v2_phase2_hazard_family as mod

    h15 = np.asarray([0.1, 0.5, 0.9])
    h60 = np.asarray([0.2, 0.4, 0.7])
    heod = np.asarray([0.3, 0.6, 0.8])
    p15, p60, peod = mod.cumulative_probs(h15, h60, heod)
    assert np.all(p15 <= p60)
    assert np.all(p60 <= peod)
    assert np.all(peod <= 1.0)


def test_phase2_uses_empirical_benchmark_before_full_selection() -> None:
    p = json.loads(FAMILY.read_text())
    assert p["fixed_benchmark"]["name"] == "expanding_empirical_stage_hazard"
    assert p["selection_rule_per_sign"] == [
        "first_test_geometry_only_against_empirical_benchmark",
        "if_geometry_fails_select_no_phase2_head_for_that_sign",
        "if_geometry_passes_test_phase1_full_against_geometry",
        "if_full_passes_select_phase1_full_else_select_geometry_only",
    ]
