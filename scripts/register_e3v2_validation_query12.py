#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
RECEIPT = ROOT / "docs/research/local_downstream_b1_forward_cycle_portfolio_risk_adapter_validation_v1_blackbox_receipt.json"
EXPECTED_QID = "ce859f9c94f281b0ec49"
EXPECTED_RECEIPT_COMMIT = "f9b26dc16969df650a1bf489c58024009437dc6e"


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if ledger.get("query_count") != 11 or len(ledger.get("queries", [])) != 11:
        raise RuntimeError("ledger is not exactly at 11 before E3v2 registration")
    if any(int(q.get("ordinal", -1)) == 12 or q.get("query_id") == EXPECTED_QID for q in ledger["queries"]):
        raise RuntimeError("query 12 already registered")
    if receipt.get("research_identity") != "overnight_b1_forward_cycle_portfolio_risk_abstention_validation_v1":
        raise RuntimeError("wrong E3v2 validation receipt identity")
    if receipt.get("query_id") != EXPECTED_QID or receipt.get("decision") not in {"PASS", "FAIL", "INSUFFICIENT"}:
        raise RuntimeError("invalid E3v2 compact receipt")
    if receipt.get("public_detail_release") is not False or receipt.get("internal_metrics_persisted") is not False:
        raise RuntimeError("E3v2 receipt violates compact-release policy")
    if receipt.get("calendar_year_results_persisted") is not False or receipt.get("bootstrap_results_persisted") is not False or receipt.get("failure_attribution_persisted") is not False:
        raise RuntimeError("E3v2 receipt leaked hidden validation detail")

    entry = {
        "ordinal": 12,
        "query_id": receipt["query_id"],
        "research_identity": receipt["research_identity"],
        "comparator": "same_frozen_REAKA_account_forward_5_cycle_without_B1_zero_boundary_abstention",
        "decision": receipt["decision"],
        "receipt": "docs/research/local_downstream_b1_forward_cycle_portfolio_risk_adapter_validation_v1_blackbox_receipt.json",
        "receipt_commit": EXPECTED_RECEIPT_COMMIT,
        "protocol_sha256": receipt["protocol_sha256"],
        "high_open_source_manifest_sha256": receipt["high_open_source_manifest_sha256"],
        "reconstruction_contract_sha256": receipt["reconstruction_contract_sha256"],
        "consumer_repository": receipt["consumer_repository"],
        "consumer_commit": receipt["consumer_commit"],
        "consumer_daily_sha256": receipt["consumer_daily_sha256"],
        "upstream_B1_query_id": receipt["upstream_B1_query_id"],
        "reconstructed_panel_2015_2020_parity": receipt["reconstructed_panel_2015_2020_parity"],
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "yearly_results_persisted": False,
        "counts_persisted": False,
        "bootstrap_results_persisted": False,
        "failure_attribution_persisted": False,
        "account_results_persisted": False,
        "technical_retry_counted_as_separate_query": False,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed_as_one_time_data": False,
        "reuse_is_independent_oos": False,
        "production_authority": False,
    }
    ledger["queries"].append(entry)
    ledger["query_count"] = 12
    ledger["schema_id"] = "overnight_reusable_blackbox_query_ledger@1.9"
    LEDGER.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    print("REGISTERED_E3V2_QUERY_12")


if __name__ == "__main__":
    main()
