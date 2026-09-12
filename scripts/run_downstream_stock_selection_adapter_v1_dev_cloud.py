#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import urllib.request

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import diagnose_driver_agreement_disagreement_dev as b4  # noqa: E402

IDENTITY = "overnight_b4_stock_selection_abstention_adapter_v1"
YEARS = tuple(range(2015, 2021))
CLOCKS = ("14:30", "14:45")
PROTOCOL = ROOT / "docs/governance/downstream_stock_selection_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_stock_selection_adapter_v1_state.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
DRIVER_ROOT = ROOT / "data/driver_runtime_text_2015_2020"
DRIVER_RECEIPT = ROOT / "docs/research/driver_runtime_text_carrier_parity_receipt_v1.json"
RECEIPT = ROOT / "docs/research/cloud_downstream_stock_selection_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_contracts() -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    state = load_json(STATE)
    ledger = load_json(LEDGER)
    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("E2 identity drift")
    if state.get("research_identity") != IDENTITY or state.get("outcome_opened") is not False:
        raise RuntimeError("E2 state not result-free/pending")
    if protocol.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("E2 development window drift")
    if tuple(protocol.get("consumer_variants", [])) != CLOCKS:
        raise RuntimeError("E2 consumer clock drift")
    if protocol.get("adapter", {}).get("semantic_boundary") != 0.0:
        raise RuntimeError("E2 boundary drift")
    if protocol.get("adapter", {}).get("candidate_attempt_count") != 1:
        raise RuntimeError("E2 multiplicity drift")
    if protocol.get("account_PnL_backtest_authorized") is not False:
        raise RuntimeError("E2 account PnL improperly authorized")
    if protocol.get("strategy_execution_authorized") is not False:
        raise RuntimeError("E2 strategy execution improperly authorized")
    if ledger.get("query_count") != 6:
        raise RuntimeError("unexpected BLACKBOX ledger count before E2 DEV")
    q3 = next((q for q in ledger.get("queries", []) if int(q.get("ordinal", -1)) == 3), None)
    if not q3 or q3.get("research_identity") != "overnight_driver_coherence_open_gap_v1" or q3.get("decision") != "PASS":
        raise RuntimeError("validated B4 authority missing")
    if q3.get("query_id") != protocol["upstream"]["validated_query_id"]:
        raise RuntimeError("B4 query id drift")
    return protocol, ledger


def _github_contents_metadata(repo: str, path: str, ref: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "factorlab-overnight-open-lab"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def load_consumer_dev(protocol: dict) -> tuple[pd.DataFrame, dict]:
    c = protocol["consumer"]
    meta = _github_contents_metadata(c["repository"], c["selection_decision_carrier"], c["source_commit"])
    if meta.get("sha") != c["selection_decision_carrier_blob_sha"]:
        raise RuntimeError("consumer decision carrier blob SHA drift")
    raw_url = meta.get("download_url")
    if not raw_url:
        raise RuntimeError("consumer decision carrier download URL missing")
    req = urllib.request.Request(raw_url, headers={"User-Agent": "factorlab-overnight-open-lab"})
    kept: list[dict[str, str]] = []
    first_post2020_seen = False
    with urllib.request.urlopen(req, timeout=30) as resp:
        wrapper = io.TextIOWrapper(resp, encoding="utf-8", newline="")
        reader = csv.DictReader(wrapper)
        required = {
            "decision_id", "decision_date", "year", "decision_clock", "replay_segment_id",
            "selected_mean_h20_return", "oracle_mean_h20_return", "selection_gap_mean_h20_return",
        }
        if reader.fieldnames is None or required.difference(reader.fieldnames):
            raise RuntimeError("consumer decision carrier schema drift")
        for row in reader:
            year = int(row["year"])
            if year < 2015:
                continue
            if year > 2020:
                first_post2020_seen = True
                break
            kept.append({k: row[k] for k in reader.fieldnames})
    if not first_post2020_seen:
        raise RuntimeError("consumer carrier ordering/boundary cannot be verified")
    frame = pd.DataFrame(kept)
    if frame.empty:
        raise RuntimeError("no E2 development consumer rows")
    frame["decision_date"] = pd.to_datetime(frame["decision_date"], errors="raise").dt.normalize()
    frame["year"] = pd.to_numeric(frame["year"], errors="raise").astype(int)
    if not frame["year"].between(2015, 2020).all():
        raise RuntimeError("post-2020 consumer row admitted")
    if set(frame["decision_clock"].unique()) != set(CLOCKS):
        raise RuntimeError("consumer clock inventory drift")
    if frame["decision_id"].duplicated().any():
        raise RuntimeError("duplicate consumer decision id")
    for col in ["selected_mean_h20_return", "oracle_mean_h20_return", "selection_gap_mean_h20_return"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    integrity = {
        "repository": c["repository"],
        "source_commit": c["source_commit"],
        "path": c["selection_decision_carrier"],
        "blob_sha": meta["sha"],
        "development_rows_materialized_only": True,
        "first_post2020_row_used_only_as_stream_stop_sentinel": True,
        "post2020_values_parsed_for_science": False,
    }
    return frame, integrity


def build_b4_dev() -> tuple[pd.DataFrame, dict]:
    raw, hashes = b4.load_frames(FACTOR_ROOT, DRIVER_ROOT)
    dev = b4.build_coordinates(raw)
    out = dev[["trading_day", "driver_coherence"]].copy()
    out["trading_day"] = pd.to_datetime(out["trading_day"], errors="raise").dt.normalize()
    out = out.loc[out["trading_day"].between(pd.Timestamp("2015-01-05"), pd.Timestamp("2020-12-31"))].copy()
    if out["trading_day"].duplicated().any():
        raise RuntimeError("duplicate B4 development day")
    return out, {
        "factor_driver_hashes": hashes,
        "factor_manifest_sha256": sha256(FACTOR_ROOT / "manifest.json"),
        "driver_manifest_sha256": sha256(DRIVER_ROOT / "manifest.json"),
        "driver_carrier_receipt_sha256": sha256(DRIVER_RECEIPT),
        "B4_reconstruction_script_sha256": sha256(ROOT / "scripts/diagnose_driver_agreement_disagreement_dev.py"),
    }


def diag(part: pd.DataFrame, min_complete: int, min_active: int) -> dict:
    cols = ["driver_coherence", "selected_mean_h20_return", "selection_gap_mean_h20_return"]
    x = part[["decision_id", "decision_date", *cols]].copy()
    numeric = x[cols].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(numeric.to_numpy(float)).all(axis=1)
    x = x.loc[mask].copy()
    n = int(len(x))
    active = pd.to_numeric(x["driver_coherence"], errors="coerce").ge(0)
    active_n = int(active.sum())
    comp_ret = float(x["selected_mean_h20_return"].mean()) if n else None
    cand_ret = float(x.loc[active, "selected_mean_h20_return"].mean()) if active_n else None
    comp_gap = float(x["selection_gap_mean_h20_return"].mean()) if n else None
    cand_gap = float(x.loc[active, "selection_gap_mean_h20_return"].mean()) if active_n else None
    return {
        "complete_decision_count": n,
        "active_decision_count": active_n,
        "active_coverage": float(active_n / n) if n else None,
        "comparator_mean_selected_h20_return": comp_ret,
        "candidate_mean_selected_h20_return": cand_ret,
        "delta_selected_h20_return": None if cand_ret is None or comp_ret is None else float(cand_ret - comp_ret),
        "comparator_mean_selection_gap": comp_gap,
        "candidate_mean_selection_gap": cand_gap,
        "delta_selection_gap": None if cand_gap is None or comp_gap is None else float(cand_gap - comp_gap),
        "sufficiency_complete_pass": bool(n >= min_complete),
        "sufficiency_active_pass": bool(active_n >= min_active),
        "sufficiency_pass": bool(n >= min_complete and active_n >= min_active),
    }


def main() -> None:
    if RECEIPT.exists():
        raise RuntimeError(f"refusing to overwrite existing receipt: {RECEIPT}")
    protocol, ledger = verify_contracts()
    consumer, consumer_integrity = load_consumer_dev(protocol)
    b4dev, b4_integrity = build_b4_dev()
    frame = consumer.merge(
        b4dev.rename(columns={"trading_day": "decision_date"}),
        on="decision_date", how="left", validate="many_to_one",
    )
    if frame["decision_date"].min() < pd.Timestamp("2015-01-05") or frame["decision_date"].max() > pd.Timestamp("2020-12-31"):
        raise RuntimeError("E2 merged boundary drift")

    min_complete = int(protocol["sufficiency_gates"]["minimum_complete_decisions_each_clock_year"])
    min_active = int(protocol["sufficiency_gates"]["minimum_active_decisions_each_clock_year"])
    gap_tol = float(protocol["selection_quality_safeguard"]["maximum_allowed_annual_worsening"])
    pooled_gap_tol = float(protocol["selection_quality_safeguard"]["maximum_allowed_pooled_worsening"])
    min_pos = int(protocol["progression_gates_each_clock"]["minimum_positive_annual_selected_return_delta_count"])
    min_gap_ok = int(protocol["progression_gates_each_clock"]["minimum_annual_selection_gap_delta_not_worse_than_minus_0_002_count"])

    diagnostics: dict[str, dict] = {}
    clock_pass: dict[str, bool] = {}
    for clock in CLOCKS:
        c = frame.loc[frame["decision_clock"].eq(clock)].copy()
        by_year = {str(y): diag(c.loc[c["year"].eq(y)], min_complete, min_active) for y in YEARS}
        pooled = diag(c, min_complete * len(YEARS), min_active * len(YEARS))
        annual_ret = [by_year[str(y)]["delta_selected_h20_return"] for y in YEARS]
        annual_gap = [by_year[str(y)]["delta_selection_gap"] for y in YEARS]
        suff = all(by_year[str(y)]["sufficiency_pass"] for y in YEARS)
        positive_count = sum(v is not None and float(v) > 0 for v in annual_ret)
        median_ret = float(np.median([float(v) for v in annual_ret if v is not None]))
        gap_ok_count = sum(v is not None and float(v) >= -gap_tol for v in annual_gap)
        gates = {
            "all_annual_sufficiency_pass": bool(suff),
            "pooled_selected_return_delta_positive": bool(pooled["delta_selected_h20_return"] is not None and pooled["delta_selected_h20_return"] > 0),
            "positive_annual_selected_return_delta_count": int(positive_count),
            "minimum_positive_annual_selected_return_delta_count_pass": bool(positive_count >= min_pos),
            "median_annual_selected_return_delta": median_ret,
            "median_annual_selected_return_delta_nonnegative": bool(median_ret >= 0),
            "pooled_selection_gap_delta_not_worse_than_tolerance": bool(pooled["delta_selection_gap"] is not None and pooled["delta_selection_gap"] >= -pooled_gap_tol),
            "annual_selection_gap_delta_not_worse_than_tolerance_count": int(gap_ok_count),
            "minimum_annual_selection_gap_count_pass": bool(gap_ok_count >= min_gap_ok),
        }
        passed = all([
            gates["all_annual_sufficiency_pass"],
            gates["pooled_selected_return_delta_positive"],
            gates["minimum_positive_annual_selected_return_delta_count_pass"],
            gates["median_annual_selected_return_delta_nonnegative"],
            gates["pooled_selection_gap_delta_not_worse_than_tolerance"],
            gates["minimum_annual_selection_gap_count_pass"],
        ])
        diagnostics[clock] = {"pooled": pooled, "by_year": by_year, "gates": gates, "progression_pass": bool(passed)}
        clock_pass[clock] = bool(passed)

    all_sufficient = all(diagnostics[c]["gates"]["all_annual_sufficiency_pass"] for c in CLOCKS)
    joint_pass = all(clock_pass.values())
    if not all_sufficient:
        decision = "E2_DEV_INSUFFICIENT"
    elif joint_pass:
        decision = "E2_DEV_PROGRESS_RETROSPECTIVE_SELECTION_QUALITY_ADAPTER_CANDIDATE"
    else:
        decision = "E2_DEV_NO_PROGRESS"

    payload = {
        "schema_id": "overnight_downstream_stock_selection_adapter_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-E2_stock_selection_adapter",
        "phase": "retrospective_selection_quality_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)},
        "consumer": protocol["consumer"],
        "adapter_rule": "active iff driver_coherence >= 0",
        "diagnostics": diagnostics,
        "joint_clock_progression_pass": bool(joint_pass),
        "decision": decision,
        "maximum_authority_if_progressed": "retrospective_E2_selection_quality_adapter_candidate_only",
        "source_integrity": {"consumer": consumer_integrity, "B4": b4_integrity},
        "validated_B4_query_id": ledger["queries"][2]["query_id"],
        "candidate_attempt_count": 1,
        "ranking_mutation": False,
        "topn_mutation": False,
        "threshold_search": False,
        "magnitude_bucket_search": False,
        "clock_selection": False,
        "upstream_add_drop_search": False,
        "account_PnL_backtest_opened": False,
        "strategy_execution_opened": False,
        "2021_2025_scientific_rows_opened": False,
        "blackbox_query_created": False,
        "production_authority": False,
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E2_STOCK_SELECTION_ADAPTER_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)


if __name__ == "__main__":
    main()
