from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase1_factor_diagnostic_protocol_v1.json"
RUNNER = ROOT / "scripts/diagnose_gap_fill_v2_phase1_factors.py"


def test_phase1_probe_family_is_exactly_frozen() -> None:
    p = json.loads(PROTOCOL.read_text())
    names = [x["name"] for x in p["probes"]]
    assert names == [
        "abs_gap",
        "abs_gap_over_rvol20",
        "v1_magnitude_surprise",
        "v1_direction_support",
        "broad_china_specific_support",
        "nasdaq_interval_support",
        "vix_interval_support",
        "prior_daytime_alignment",
        "prior_last_hour_alignment",
        "prior_gap_alignment",
    ]
    assert p["target_horizons"] == ["fill_15m", "fill_60m", "fill_eod"]
    assert p["mandatory_strata"]["gap_sign"] == ["high", "low"]
    assert p["mandatory_strata"]["material_cohorts"] == ["abs_gap_gt_10bp", "abs_gap_gt_30bp"]


def test_phase1_v1_identities_and_evidence_boundary_are_frozen() -> None:
    p = json.loads(PROTOCOL.read_text())
    assert p["frozen_v1_reference"]["direction"]["spec_sha256"] == "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
    assert p["frozen_v1_reference"]["magnitude"]["selected_architecture_sha256"] == "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"
    assert p["evidence_boundary"]["repeat_only_reserved"] == "2026-01-05_to_2026-08-21"
    assert p["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    assert p["candidate_selection_performed"] is False
    assert p["gap_fill_model_fitting_performed"] is False


def test_phase1_runner_is_diagnostic_only_and_fail_closed() -> None:
    text = RUNNER.read_text()
    assert 'EXPECTED_DIRECTION_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"' in text
    assert 'EXPECTED_TWO_HEAD_SHA = "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"' in text
    assert 'EXPECTED_OFFSHORE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"' in text
    assert '"gap_fill_model_fitting_performed": False' in text
    assert '"candidate_selection_performed": False' in text
    assert '"feature_selection_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert 'YEARS = list(range(2016, 2026))' in text
    assert "LogisticRegression" not in text
    assert "RandomForest" not in text
    assert "XGB" not in text
