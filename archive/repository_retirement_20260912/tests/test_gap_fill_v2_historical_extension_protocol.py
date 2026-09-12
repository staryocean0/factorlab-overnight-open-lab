from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_historical_extension_protocol_v1.json"
TEMPLATE = ROOT / "docs/ops/gap_fill_v2_historical_source_inventory_template_v1.json"
HANDOFF = ROOT / "docs/ops/gap_fill_v2_historical_source_inventory_handoff.md"


def load_protocol():
    return json.loads(PROTOCOL.read_text(encoding="utf-8"))


def test_new_identity_can_research_v21_without_mutating_v2v1():
    p = load_protocol()
    assert p["research_identity"] == "gap_fill_v2_historical_extension_v1"
    assert p["new_generation_policy"]["v2_1_research_allowed"] is True
    assert p["new_generation_policy"]["existing_evidence_may_never_be_relabelled_fresh"] is True
    assert p["v2_v1_is_immutable"]["selected_architecture_sha256"] == "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
    assert p["v2_v1_is_immutable"]["parameter_bundle_sha256"] == "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"


def test_he00_is_metadata_only_and_forbids_outcomes():
    p = load_protocol()
    forbidden = set(p["HE00_forbidden_operations"])
    assert "construct_or_inspect_fill_15m_fill_60m_fill_eod" in forbidden
    assert "score_any_V2_model" in forbidden
    assert "compute_feature_outcome_association" in forbidden
    assert "inspect_post_2026_08_21_outcomes" in forbidden
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert template["outcome_inspection_performed"] is False
    assert template["fill_target_construction_performed"] is False
    assert template["model_scoring_performed"] is False


def test_fixed_historical_partitions_cannot_slide():
    p = load_protocol()["fixed_same_index_calendar_partitions"]
    assert p["HE_DEV"]["start"] == "2005-01-01"
    assert p["HE_DEV"]["end"] == "2010-12-31"
    assert p["HE_AUDIT_A"]["start"] == "2011-01-01"
    assert p["HE_AUDIT_A"]["end"] == "2012-12-31"
    assert p["HE_AUDIT_B"]["start"] == "2013-01-01"
    assert p["HE_AUDIT_B"]["end"] == "2014-10-16"
    assert p["HE_LIVE_CROSSCHECK"]["start"] == "2014-10-17"
    assert p["HE_LIVE_CROSSCHECK"]["end"] == "2014-12-31"
    assert "audit_boundaries_must_not_shift" in p["missing_coverage_rule"]


def test_prepublication_csi1000_requires_nonlive_provenance_label():
    p = load_protocol()["same_index_source_contract"]
    assert p["official_publication_date"] == "2014-10-17"
    assert p["official_base_date"] == "2004-12-31"
    assert p["unknown_provenance_promotion_authority"] is False
    assert "vendor_backfilled_index" in p["provenance_classes"]
    assert "constituent_reconstructed_index" in p["provenance_classes"]


def test_cross_index_is_inventory_only_until_new_protocol():
    p = load_protocol()["cross_index_inventory"]
    assert p["symbols"] == ["CSI300_000300", "CSI500_000905"]
    assert p["stage_now"] == "metadata_only_no_outcomes"
    assert p["pool_with_CSI1000_now"] is False
    assert p["later_protocol_required"] == "gap_fill_cross_index_transport_v1"


def test_handoff_repeats_the_no_outcome_rule():
    text = HANDOFF.read_text(encoding="utf-8")
    assert "Do not authorize HE_DEV outcome opening locally" in text
    assert "compute `fill_15m`, `fill_60m` or `fill_eod`" in text
    assert "2014-10-17" in text
