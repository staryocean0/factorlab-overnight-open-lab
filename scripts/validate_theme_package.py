#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
END = "2020-12-31"
DIRECTION_SPEC_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
MAGNITUDE_CANDIDATE_SHA = "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"

def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as h:
        for b in iter(lambda: h.read(1024 * 1024), b""):
            d.update(b)
    return d.hexdigest()

def load_json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def main() -> int:
    man = load_json("data/manifest.json")
    assert man["post_2020_rows_included"] is False
    assert man["production_authority"] is False
    for item in man["products"]:
        path = ROOT / item["path"]
        assert path.is_file()
        assert sha256(path) == item["sha256"]
        frame = pd.read_parquet(path)
        col = "trading_day" if "trading_day" in frame.columns else "date"
        days = pd.to_datetime(frame[col]).dt.strftime("%Y-%m-%d")
        assert str(days.max()) <= END
    panel = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    assert panel["gap"].notna().mean() > 0.9

    selected = load_json("docs/governance/cloud_session_20260906_direction_head_selected_v1.json")
    selected_digest = hashlib.sha256(
        json.dumps(
            selected["selected_spec"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    assert selected_digest == DIRECTION_SPEC_SHA
    assert selected["selected_spec_sha256"] == DIRECTION_SPEC_SHA
    assert selected["production_authority"] is False

    direction_receipt = load_json("docs/research/cloud_session_20260906_local_2026_direction_receipt_v1.json")
    assert direction_receipt["candidate_spec_sha256"] == DIRECTION_SPEC_SHA
    assert direction_receipt["validation_window"] == {"start": "2026-01-05", "end": "2026-08-21"}
    assert direction_receipt["n_validation_rows"] == direction_receipt["n_validation_complete"] == 154
    assert direction_receipt["n_validation_dropped_missing"] == 0
    assert direction_receipt["decision"] == "direction_candidate_2026_robustly_confirmed"
    assert direction_receipt["fresh_oos"] is True
    assert direction_receipt["parameter_search_after_open"] is False
    assert direction_receipt["trading_return_used_in_gate"] is False
    assert direction_receipt["raw_2026_rows_written_to_bounded_repo"] is False
    assert direction_receipt["production_authority"] is False

    magnitude_receipt = load_json("docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json")
    assert magnitude_receipt["candidate_sha256"] == MAGNITUDE_CANDIDATE_SHA
    assert magnitude_receipt["passed"] is True
    assert magnitude_receipt["fresh_oos"] is True
    assert magnitude_receipt["parameter_search_after_open"] is False
    assert magnitude_receipt["trading_return_used_in_gate"] is False
    assert magnitude_receipt["raw_2021_2025_rows_written_to_bounded_repo"] is False
    assert magnitude_receipt["production_authority"] is False

    acceptance = load_json("docs/governance/cloud_session_20260906_research_architecture_acceptance_v1.json")
    assert acceptance["direction_head"]["selected_spec_sha256"] == DIRECTION_SPEC_SHA
    assert acceptance["magnitude_head"]["candidate_sha256"] == MAGNITUDE_CANDIDATE_SHA
    assert acceptance["accepted_research_architecture"]["status"] == "component_confirmed_incumbent_research_architecture"
    assert acceptance["accepted_research_architecture"]["joint_fresh_full_model_challenge_completed"] is False
    assert acceptance["accepted_research_architecture"]["trading_profit_claim_allowed"] is False
    assert acceptance["model_search_status"] == "closed_for_current_identity_on_all_consumed_windows"
    assert acceptance["production_authority"] is False

    production = load_json("docs/governance/cloud_session_20260906_production_readiness_review_v1.json")
    assert production["review_decision"] == "blocked_before_strategy_account_audit_missing_financial_decision_use_contract"
    assert production["strategy_science_acceptance_status"] == "not_opened"
    assert production["post_training_account_audit_status"] == "not_opened"
    assert production["production_authority"] is False

    usage = load_json("docs/governance/local_session_20260906_2026_direction_data_usage.json")
    assert usage["raw_validation_rows_persisted_in_bounded_repo"] is False
    assert usage["post_2026-08-21"] == "unread_for_this_candidate_identity"
    assert usage["production_authority"] is False

    print("ok", len(man["products"]), "research_architecture_accepted", "production_authority=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
