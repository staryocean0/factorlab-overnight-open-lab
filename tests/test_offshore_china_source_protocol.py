from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_offshore_china_protocol_keeps_2026_sealed() -> None:
    protocol = json.loads(
        (ROOT / "docs/governance/cloud_session_20260906_offshore_china_price_discovery_protocol_v1.json").read_text()
    )
    assert protocol["evidence_boundary"]["development"] == "2015-01-05_to_2025-12-31"
    assert protocol["evidence_boundary"]["sealed_repeat_blackbox"] == "2026-01-05_to_2026-08-21"
    assert protocol["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    assert protocol["hard_causality"]["same_morning_china_information"] == "forbidden"
    assert protocol["source_provenance_rule"]["provider_must_be_frozen_before_target_diagnostics"] is True
    assert protocol["production_authority"] is False


def test_offshore_source_universe_is_fixed_and_small() -> None:
    protocol = json.loads(
        (ROOT / "docs/governance/cloud_session_20260906_offshore_china_price_discovery_protocol_v1.json").read_text()
    )
    assert set(protocol["source_universe"]) == {"ASHS", "ASHR", "FXI", "MCHI", "SPY"}
    assert set(protocol["preregistered_source_representations"]) == {
        "ashs_session",
        "ashr_session",
        "ashs_minus_ashr",
        "a_share_consensus",
        "a_share_specific_vs_spy",
        "broad_china_specific_vs_spy",
        "china_etf_positive_breadth",
    }


def test_offshore_source_probe_is_source_only() -> None:
    text = (ROOT / "scripts/probe_offshore_china_source_quality.py").read_text()
    assert 'END = "2025-12-31"' in text
    assert 'SYMBOLS = ["ASHS", "ASHR", "FXI", "MCHI", "SPY"]' in text
    assert '"predictive_target_loaded": False' in text
    assert '"candidate_selection_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_blackbox_opened": False' in text
    assert "ANNOTATED_PANEL" not in text
    assert "overnight_gap" not in text
    assert "csi1000_open_pit_panel" not in text
