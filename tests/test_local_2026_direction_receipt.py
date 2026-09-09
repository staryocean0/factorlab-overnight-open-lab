from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SPEC_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"


def test_direction_candidate_sha_still_matches() -> None:
    selected = json.loads((ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json").read_text())
    digest = hashlib.sha256(
        json.dumps(selected["selected_spec"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert digest == SPEC_SHA
    assert selected["selected_spec_sha256"] == SPEC_SHA


def test_local_2026_receipt_flags() -> None:
    receipt = json.loads(
        (ROOT / "docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json").read_text()
    )
    assert receipt["candidate_spec_sha256"] == SPEC_SHA
    assert receipt["decision"] == "direction_candidate_2026_robustly_confirmed"
    assert receipt["raw_hit_confirmation"] is True
    assert receipt["robust_confirmation"] is True
    assert receipt["fresh_oos"] is True
    assert receipt["production_authority"] is False
    assert receipt["parameter_search_after_open"] is False
    assert receipt["trading_return_used_in_gate"] is False
    assert receipt["raw_2026_rows_written_to_bounded_repo"] is False
    assert receipt["n_validation_rows"] == 154
    assert receipt["n_validation_complete"] == 154
    assert receipt["n_validation_dropped_missing"] == 0
    assert receipt["validation_window"] == {"start": "2026-01-05", "end": "2026-08-21"}
    assert receipt["candidate"]["direction_hit"] > receipt["baseline"]["direction_hit"]
    assert receipt["candidate_minus_baseline_correct_count"] > 0
    assert receipt["candidate"]["balanced_accuracy"] >= receipt["baseline"]["balanced_accuracy"]
    assert receipt["candidate"]["recall_up"] > 0.5
    assert receipt["candidate"]["recall_down"] > 0.5
