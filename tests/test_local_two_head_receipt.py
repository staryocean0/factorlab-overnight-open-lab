from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_sha_still_matches() -> None:
    selected = json.loads((ROOT / "docs/governance/cloud_session_20260906_two_head_selected_v1.json").read_text())
    payload = {key: value for key, value in selected["selected_spec"].items() if key != "sha256"}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"
    assert selected["selected_spec"]["sha256"] == digest


def test_local_receipt_flags() -> None:
    receipt = json.loads(
        (ROOT / "docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json").read_text()
    )
    assert receipt["candidate_sha256"] == "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"
    assert receipt["passed"] is True
    assert receipt["fresh_oos"] is True
    assert receipt["production_authority"] is False
    assert receipt["trading_return_used_in_gate"] is False
    assert receipt["parameter_search_after_open"] is False
    assert receipt["raw_2021_2025_rows_written_to_bounded_repo"] is False
    assert receipt["primary_metrics"]["candidate"]["direction_hit"] == receipt["primary_metrics"]["baseline"]["direction_hit"]
