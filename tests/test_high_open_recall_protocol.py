from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_high_open_recall_evidence_boundary() -> None:
    protocol = json.loads(
        (ROOT / "docs/governance/cloud_session_20260906_high_open_recall_research_protocol_v1.json").read_text()
    )
    boundary = protocol["evidence_boundary"]
    assert boundary["2026-01-05_to_2026-08-21"] == "sealed_repeat_blackbox_validation_only"
    assert protocol["2026_blackbox_semantics"]["may_participate_in_diagnostics"] is False
    assert protocol["2026_blackbox_semantics"]["may_participate_in_feature_engineering"] is False
    assert protocol["2026_blackbox_semantics"]["may_participate_in_candidate_family_design"] is False
    assert protocol["2026_blackbox_semantics"]["may_participate_in_candidate_ranking"] is False
    assert protocol["2026_blackbox_semantics"]["fresh_oos_authority"] is False
    assert protocol["true_fresh_promotion"]["window"] == "post_2026-08-21"
    assert protocol["production_authority"] is False


def test_high_open_diagnostic_runner_is_development_only() -> None:
    text = (ROOT / "scripts/diagnose_high_open_false_negatives_dev.py").read_text()
    assert 'DEV_END = "2025-12-31"' in text
    assert 'OOF_YEARS = list(range(2016, 2026))' in text
    assert '"candidate_selection_performed": False' in text
    assert '"parameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_blackbox_opened": False' in text


def test_high_open_phase2_family_is_bounded_piecewise_weakness_only() -> None:
    family = json.loads(
        (ROOT / "docs/governance/cloud_session_20260906_high_open_recall_phase2_family_v1.json").read_text()
    )
    assert family["multiplicity"] == 4
    assert family["fixed_estimator"]["quantile"] == 0.5
    assert family["fixed_estimator"]["alpha"] == 0.0
    assert family["fixed_estimator"]["threshold"] == 0.0
    assert family["evidence_boundary"]["sealed_repeat_blackbox"] == "2026-01-05_to_2026-08-21"
    assert family["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    allowed = {
        "prev_daytime_weakness",
        "prev_afternoon_weakness",
        "prev_last_hour_weakness",
    }
    assert set(family["derived_feature_definitions"]) == allowed
    assert len(family["candidates"]) == 4
    for candidate in family["candidates"]:
        assert set(candidate["extra_features"]).issubset(allowed)
    forbidden = set(family["forbidden"])
    assert "threshold search" in forbidden
    assert "quantile search" in forbidden
    assert "positive-US interaction features" in forbidden
    assert family["production_authority"] is False


def test_high_open_phase2_selector_does_not_open_2026() -> None:
    text = (ROOT / "scripts/select_high_open_recall_phase2_dev.py").read_text()
    assert 'DEV_END = "2025-12-31"' in text
    assert 'OOF_YEARS = list(range(2016, 2026))' in text
    assert '"candidate_selection_performed": True' in text
    assert '"parameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"quantile_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_blackbox_opened": False' in text
