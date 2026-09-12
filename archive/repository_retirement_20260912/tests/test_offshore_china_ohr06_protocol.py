from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_ohr06_protocol_freezes_source_and_blackbox() -> None:
    p = json.loads((ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr06_diagnostic_protocol_v1.json").read_text())
    assert p["accepted_source"]["source_sha256"] == "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
    assert p["accepted_source"]["symbols"] == ["ASHS", "ASHR", "FXI", "MCHI", "SPY"]
    assert p["evidence_boundary"]["sealed_repeat_blackbox"] == "2026-01-05_to_2026-08-21"
    assert p["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    assert len(p["fixed_source_representations"]) == 7
    assert p["candidate_selection_performed"] is False
    assert p["production_authority"] is False


def test_ohr06_requires_china_specific_support_before_family() -> None:
    p = json.loads((ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr06_diagnostic_protocol_v1.json").read_text())
    rule = p["china_specific_admission_rule"]
    assert rule["candidate_family_may_be_opened_only_if_at_least_one_china_specific_representation_passes_all_mechanism_gates"] is True
    assert set(rule["china_specific_representations"]) == {
        "ashs_minus_ashr",
        "a_share_specific_vs_spy",
        "broad_china_specific_vs_spy",
    }


def test_ohr06_runner_is_development_diagnostic_only() -> None:
    text = (ROOT / "scripts/diagnose_offshore_china_price_discovery_dev.py").read_text()
    assert 'ACCEPTED_SOURCE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"' in text
    assert '"candidate_selection_performed": False' in text
    assert '"parameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"quantile_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_blackbox_opened": False' in text
    assert '"ohr_03_opened": False' in text
    assert 'last_hour_minus' not in text
