#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import diagnose_driver_agreement_disagreement_dev as b4  # noqa: E402

IDENTITY = "overnight_c1_b4_timing_confidence_adapter_v1"
YEARS = tuple(range(2015, 2021))
PROTOCOL = ROOT / "docs/governance/downstream_timing_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_timing_adapter_v1_state.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
DRIVER_ROOT = ROOT / "data/driver_runtime_text_2015_2020"
DRIVER_RECEIPT = ROOT / "docs/research/driver_runtime_text_carrier_parity_receipt_v1.json"
RECEIPT = ROOT / "docs/research/cloud_downstream_timing_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sign_series(x: pd.Series) -> pd.Series:
    v = pd.to_numeric(x, errors="coerce")
    return pd.Series(np.sign(v.to_numpy(dtype=float)), index=x.index, dtype=float)


def verify_contracts() -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    state = load_json(STATE)
    ledger = load_json(LEDGER)

    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("E1 identity drift")
    if state.get("research_identity") != IDENTITY or state.get("outcome_opened") is not False:
        raise RuntimeError("E1 state is not result-free/pending")
    if protocol.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("E1 development window drift")
    if protocol.get("annual_report_slices") != list(YEARS):
        raise RuntimeError("E1 annual slice drift")
    if protocol.get("candidate_family", {}).get("attempt_count") != 1:
        raise RuntimeError("E1 candidate multiplicity drift")
    if protocol.get("candidate_family", {}).get("free_parameters") != 0:
        raise RuntimeError("E1 gained free parameters")
    defs = protocol.get("definitions", {})
    if defs.get("candidate_action") != "c1_action if driver_alignment >= 0 else 0":
        raise RuntimeError("E1 candidate action drift")
    if defs.get("comparator_action") != "c1_action":
        raise RuntimeError("E1 comparator drift")
    if protocol.get("target", {}).get("id") != "ret_0935_0950":
        raise RuntimeError("E1 target drift")
    if protocol.get("account_or_strategy_authority_if_pass") is not False:
        raise RuntimeError("E1 improperly grants strategy authority")
    if protocol.get("future_blackbox_2021_2025_authorized_now") is not False:
        raise RuntimeError("E1 improperly opens 2021-2025")

    if ledger.get("query_count") != 5:
        raise RuntimeError("unexpected reusable BLACKBOX ledger count before E1 DEV")
    queries = {int(q["ordinal"]): q for q in ledger.get("queries", [])}
    q2 = queries.get(2, {})
    q3 = queries.get(3, {})
    if q2.get("research_identity") != "overnight_trend_conditioned_open_state_15m_v1" or q2.get("decision") != "PASS":
        raise RuntimeError("validated C1 authority missing")
    if q3.get("research_identity") != "overnight_driver_coherence_open_gap_v1" or q3.get("decision") != "PASS":
        raise RuntimeError("validated B4 authority missing")
    return protocol, ledger


def load_opening_clocks() -> tuple[pd.DataFrame, dict]:
    pieces = []
    hashes = {}
    for year in YEARS:
        path = FACTOR_ROOT / f"opening_clocks_{year}.csv"
        df = pd.read_csv(path)
        required = {"trading_day", "close_0935", "close_0950"}
        if required.difference(df.columns):
            raise RuntimeError(f"opening clock shard {year} missing columns")
        df["trading_day"] = pd.to_datetime(df["trading_day"], errors="raise").dt.normalize()
        if not df["trading_day"].dt.year.eq(year).all():
            raise RuntimeError(f"opening clock year boundary drift {year}")
        if df["trading_day"].duplicated().any():
            raise RuntimeError(f"duplicate opening clock day {year}")
        pieces.append(df[["trading_day", "close_0935", "close_0950"]].copy())
        hashes[str(year)] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    out = pd.concat(pieces, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    return out, hashes


def build_frame() -> tuple[pd.DataFrame, dict]:
    factor_manifest = load_json(FACTOR_ROOT / "manifest.json")
    driver_manifest = load_json(DRIVER_ROOT / "manifest.json")
    driver_receipt = load_json(DRIVER_RECEIPT)

    if factor_manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary drift")
    if driver_manifest.get("published_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("driver runtime publication boundary drift")
    if driver_manifest.get("withheld_years") != [2021, 2022, 2023, 2024, 2025]:
        raise RuntimeError("driver withheld-year boundary drift")
    if driver_receipt.get("a50_clock_integrity") != "PASS" or driver_receipt.get("hkma_causal_timing_integrity") != "PASS":
        raise RuntimeError("driver carrier integrity is not PASS")
    if driver_receipt.get("2021_2025_text_shards_generated") is not False:
        raise RuntimeError("driver BLACKBOX text exposure detected")

    raw, source_hashes = b4.load_frames(FACTOR_ROOT, DRIVER_ROOT)
    frame = b4.build_coordinates(raw)
    clocks, clock_hashes = load_opening_clocks()
    frame = frame.merge(clocks, on="trading_day", how="inner", validate="one_to_one")
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)

    dev_start = pd.Timestamp("2015-01-05")
    dev_end = pd.Timestamp("2020-12-31")
    if frame.empty or frame["trading_day"].min() < dev_start or frame["trading_day"].max() > dev_end:
        raise RuntimeError("E1 merged rows crossed the frozen development boundary")
    if frame["trading_day"].duplicated().any():
        raise RuntimeError("duplicate E1 trading day")

    rvol = pd.to_numeric(frame["rvol20"], errors="coerce")
    gap = pd.to_numeric(frame["gap"], errors="coerce")
    r20 = pd.to_numeric(frame["r20"], errors="coerce")
    frame["observed_gap_rvol"] = gap / rvol
    frame["trend20_rvol"] = r20 / (np.sqrt(20.0) * rvol)
    frame["trend_gap_interaction"] = frame["observed_gap_rvol"] * frame["trend20_rvol"]
    frame["c1_direction_score"] = -frame["trend_gap_interaction"]
    frame["c1_action"] = sign_series(frame["c1_direction_score"])
    frame["gap_sign"] = sign_series(frame["observed_gap_rvol"])
    frame["driver_alignment"] = pd.to_numeric(frame["driver_coherence"], errors="coerce") * frame["gap_sign"]
    frame["comparator_action"] = frame["c1_action"]
    frame["candidate_action"] = np.where(frame["driver_alignment"] >= 0, frame["c1_action"], 0.0)
    frame["ret_0935_0950"] = pd.to_numeric(frame["close_0950"], errors="coerce") / pd.to_numeric(frame["close_0935"], errors="coerce") - 1.0
    frame["year"] = frame["trading_day"].dt.year.astype(int)

    integrity = {
        "factor_driver_source_hashes": source_hashes,
        "opening_clock_hashes": clock_hashes,
        "factor_manifest": {"path": str((FACTOR_ROOT / "manifest.json").relative_to(ROOT)), "sha256": sha256(FACTOR_ROOT / "manifest.json")},
        "driver_manifest": {"path": str((DRIVER_ROOT / "manifest.json").relative_to(ROOT)), "sha256": sha256(DRIVER_ROOT / "manifest.json")},
        "driver_carrier_receipt": {"path": str(DRIVER_RECEIPT.relative_to(ROOT)), "sha256": sha256(DRIVER_RECEIPT)},
        "upstream_B4_implementation": {"path": "scripts/diagnose_driver_agreement_disagreement_dev.py", "sha256": sha256(ROOT / "scripts/diagnose_driver_agreement_disagreement_dev.py")},
        "merged_min_day_after_upstream_warmup": str(frame["trading_day"].min().date()),
        "merged_max_day": str(frame["trading_day"].max().date()),
    }
    return frame, integrity


def diagnose(part: pd.DataFrame, minimum_n: int, minimum_active: int) -> dict:
    cols = [
        "rvol20", "observed_gap_rvol", "trend20_rvol", "trend_gap_interaction",
        "driver_coherence", "driver_alignment", "comparator_action", "candidate_action",
        "ret_0935_0950",
    ]
    x = part[["trading_day", *cols]].copy()
    numeric = x[cols].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(numeric.to_numpy(dtype=float)).all(axis=1) & numeric["rvol20"].gt(0)
    x = x.loc[mask].copy()
    n = int(len(x))
    comp_active = x["comparator_action"].ne(0)
    cand_active = x["candidate_action"].ne(0)
    comp_active_n = int(comp_active.sum())
    cand_active_n = int(cand_active.sum())

    comp_u = x["comparator_action"] * x["ret_0935_0950"]
    cand_u = x["candidate_action"] * x["ret_0935_0950"]

    out = {
        "complete_case_count": n,
        "comparator_active_day_count": comp_active_n,
        "candidate_active_day_count": cand_active_n,
        "candidate_coverage": float(cand_active_n / n) if n else None,
        "comparator_hit_rate": float((comp_u.loc[comp_active] > 0).mean()) if comp_active_n else None,
        "candidate_active_hit_rate": float((cand_u.loc[cand_active] > 0).mean()) if cand_active_n else None,
        "mean_comparator_signed_utility": float(comp_u.mean()) if n else None,
        "mean_candidate_signed_utility": float(cand_u.mean()) if n else None,
        "delta_mean_signed_utility": float(cand_u.mean() - comp_u.mean()) if n else None,
        "sufficiency_complete_cases_pass": bool(n >= minimum_n),
        "sufficiency_candidate_active_days_pass": bool(cand_active_n >= minimum_active),
    }
    out["sufficiency_pass"] = bool(out["sufficiency_complete_cases_pass"] and out["sufficiency_candidate_active_days_pass"])
    return out


def main() -> None:
    if RECEIPT.exists():
        raise RuntimeError(f"refusing to overwrite existing receipt: {RECEIPT}")
    protocol, ledger = verify_contracts()
    frame, integrity = build_frame()

    min_year = int(protocol["sufficiency_gates"]["minimum_complete_cases_each_year"])
    min_active = int(protocol["sufficiency_gates"]["minimum_candidate_active_days_each_year"])
    annual = {str(y): diagnose(frame.loc[frame["year"].eq(y)].copy(), min_year, min_active) for y in YEARS}
    pooled = diagnose(frame.copy(), min_year * len(YEARS), min_active * len(YEARS))

    sufficiency_pass = bool(all(annual[str(y)]["sufficiency_pass"] for y in YEARS))
    annual_deltas = [annual[str(y)]["delta_mean_signed_utility"] for y in YEARS]
    positive_count = int(sum(float(v) > 0 for v in annual_deltas))
    median_annual = float(np.median(annual_deltas))
    pooled_delta = float(pooled["delta_mean_signed_utility"])
    gates = {
        "all_annual_sufficiency_pass": sufficiency_pass,
        "pooled_delta_mean_signed_utility_positive": bool(pooled_delta > 0),
        "positive_annual_delta_count": positive_count,
        "minimum_positive_annual_delta_count_pass": bool(positive_count >= int(protocol["progression_gates"]["minimum_positive_annual_delta_count"])),
        "median_annual_delta": median_annual,
        "median_annual_delta_nonnegative": bool(median_annual >= 0),
    }
    progression_pass = bool(
        sufficiency_pass
        and gates["pooled_delta_mean_signed_utility_positive"]
        and gates["minimum_positive_annual_delta_count_pass"]
        and gates["median_annual_delta_nonnegative"]
    )
    decision = "E1_DEV_PROGRESS_RETROSPECTIVE_FACTOR_UTILITY_ADAPTER_CANDIDATE" if progression_pass else (
        "E1_DEV_INSUFFICIENT" if not sufficiency_pass else "E1_DEV_NO_PROGRESS"
    )

    payload = {
        "schema_id": "overnight_downstream_timing_adapter_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-E1_timing_adapter",
        "phase": "retrospective_factor_utility_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)},
        "candidate": "C1_direction_with_B4_zero_boundary_abstention",
        "comparator": "C1_direction_without_B4_abstention",
        "target": "ret_0935_0950",
        "diagnostics": {"pooled": pooled, "by_year": annual},
        "progression_gate_components": gates,
        "decision": decision,
        "maximum_authority_if_progressed": "retrospective_factor_utility_adapter_candidate_only",
        "source_integrity": integrity,
        "validated_upstream_query_ids": {
            "C1": ledger["queries"][1]["query_id"],
            "B4": ledger["queries"][2]["query_id"],
        },
        "candidate_attempt_count": 1,
        "technical_retry_count": 1,
        "technical_retry_reason": "initial runner incorrectly required the post-upstream-warmup merged frame to begin exactly on the raw development start; no receipt or scientific outcome was produced",
        "technical_retry_counted_as_scientific_attempt": False,
        "threshold_search": False,
        "weight_search": False,
        "alternate_horizon_search": False,
        "upstream_add_drop_search": False,
        "strategy_PnL_optimization": False,
        "cost_model_used": False,
        "cash_index_direct_tradability_claim": False,
        "account_backtest_opened": False,
        "stock_selection_backtest_opened": False,
        "2021_2025_detailed_rows_opened": False,
        "reusable_blackbox_query_created": False,
        "production_authority": False,
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E1_TIMING_ADAPTER_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)


if __name__ == "__main__":
    main()
