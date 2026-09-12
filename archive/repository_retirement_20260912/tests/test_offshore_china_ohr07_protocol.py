from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_ohr07_family_is_single_candidate_and_source_frozen() -> None:
    p = json.loads((ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr07_family_v1.json").read_text())
    assert p["multiplicity"] == 1
    assert len(p["candidates"]) == 1
    assert p["candidates"][0]["name"] == "broad_china_specific_tail_weak_piecewise"
    assert p["candidates"][0]["extra_features"] == ["broad_china_specific_tail_weak"]
    assert p["accepted_source"]["source_sha256"] == "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
    assert p["fixed_estimator"]["quantile"] == 0.5
    assert p["fixed_estimator"]["alpha"] == 0.0
    assert p["fixed_estimator"]["threshold"] == 0.0


def test_ohr07_blackbox_and_fresh_boundaries() -> None:
    p = json.loads((ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr07_family_v1.json").read_text())
    assert p["evidence_boundary"]["sealed_repeat_blackbox"] == "2026-01-05_to_2026-08-21"
    assert p["evidence_boundary"]["repeat_blackbox_fresh_authority"] is False
    assert p["evidence_boundary"]["true_fresh_reserved"] == "post_2026-08-21"
    assert p["production_authority"] is False


def test_ohr07_selector_is_fail_closed() -> None:
    text = (ROOT / "scripts/select_offshore_china_ohr07_dev.py").read_text()
    assert 'EXPECTED_SOURCE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"' in text
    assert 'EXTRA = "broad_china_specific_tail_weak"' in text
    assert '"candidate_selection_performed": True' in text
    assert '"parameter_search_performed": False' in text
    assert '"threshold_search_performed": False' in text
    assert '"quantile_search_performed": False' in text
    assert '"2026_rows_loaded": False' in text
    assert '"2026_blackbox_opened": False' in text
    assert '"ohr_03_opened": False' in text
    assert "ashs_session" not in text
    assert "ashr_session" not in text
    assert "china_etf_positive_breadth" not in text
