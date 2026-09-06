from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_v2_protocol_freezes_targets_and_evidence_boundary() -> None:
    p = json.loads((ROOT / 'docs/governance/cloud_session_20260906_gap_fill_prediction_v2_protocol_v1.json').read_text())
    assert p['research_identity'] == 'gap_fill_prediction_v2'
    assert p['prediction_timestamp'] == '09:31_China_time_after_open_gap_is_observed'
    assert p['frozen_horizons']['fill_15m'] == 'first_15_one_minute_bars_from_09:31'
    assert p['frozen_horizons']['fill_60m'] == 'first_60_one_minute_bars_from_09:31'
    assert p['frozen_horizons']['fill_eod'] == 'through_current_15:00_close'
    assert p['nested_event_invariant'] == 'fill_15m <= fill_60m <= fill_eod'
    assert p['material_gap_cohorts'] == ['abs_gap_gt_10bp', 'abs_gap_gt_30bp']
    assert p['target_ledger_phase']['model_fitting_allowed'] is False
    assert p['target_ledger_phase']['feature_selection_allowed'] is False
    assert p['evidence_boundary']['repeat_only_reserved'] == '2026-01-05_to_2026-08-21'
    assert p['evidence_boundary']['repeat_only_may_not_participate_in_design'] is True
    assert p['evidence_boundary']['true_fresh_reserved'] == 'post_2026-08-21'
    assert p['production_authority'] is False


def test_v2_target_builder_is_development_only_and_no_modeling() -> None:
    text = (ROOT / 'scripts/build_gap_fill_v2_target_ledger.py').read_text()
    assert 'END = "2025-12-31"' in text
    assert 'MATERIAL = {"gt10bp": 0.001, "gt30bp": 0.003}' in text
    assert '"model_fitting_performed": False' in text
    assert '"feature_selection_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"raw_target_rows_written_to_repo": False' in text
    assert 'RandomForest' not in text
    assert 'XGB' not in text
    assert '.fit(' not in text


def test_v2_expected_clock_endpoints_are_fixed() -> None:
    text = (ROOT / 'scripts/build_gap_fill_v2_target_ledger.py').read_text()
    assert '"2000-01-01 09:31", "2000-01-01 11:30"' in text
    assert '"2000-01-01 13:01", "2000-01-01 15:00"' in text
    assert '"15m": morning[:15]' in text
    assert '"60m": morning[:60]' in text
