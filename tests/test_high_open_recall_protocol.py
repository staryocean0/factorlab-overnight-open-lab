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
