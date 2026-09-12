#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_c1_c2_timing_agreement_adapter_v1"
YEARS = tuple(range(2015, 2021))
PROTOCOL = ROOT / "docs/governance/downstream_c1_c2_timing_agreement_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_c1_c2_timing_agreement_adapter_v1_state.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
RECEIPT = ROOT / "docs/research/cloud_downstream_c1_c2_timing_agreement_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_contracts() -> tuple[dict, dict]:
    p = load_json(PROTOCOL)
    s = load_json(STATE)
    ledger = load_json(LEDGER)
    if p.get("research_identity") != IDENTITY or s.get("research_identity") != IDENTITY:
        raise RuntimeError("identity drift")
    if s.get("outcome_opened") is not False:
        raise RuntimeError("state is not result-free")
    if p.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("development window drift")
    if p.get("annual_report_slices") != list(YEARS):
        raise RuntimeError("annual slices drift")
    if p.get("candidate_family", {}).get("attempt_count") != 1 or p.get("candidate_family", {}).get("free_parameters") != 0:
        raise RuntimeError("candidate family drift")
    if p.get("definitions", {}).get("candidate_action") != "c1_action if c1_action * c2_action > 0 else 0":
        raise RuntimeError("candidate action drift")
    if p.get("target", {}).get("id") != "ret_0935_0950":
        raise RuntimeError("target drift")
    qs = {int(q["ordinal"]): q for q in ledger.get("queries", [])}
    if qs.get(2, {}).get("query_id") != "5a27b953276382e473c0" or qs.get(2, {}).get("decision") != "PASS":
        raise RuntimeError("validated C1 authority missing")
    if qs.get(7, {}).get("query_id") != "a1068de9321c04632aad" or qs.get(7, {}).get("decision") != "PASS":
        raise RuntimeError("validated C2 authority missing")
    return p, ledger


def load_frame() -> tuple[pd.DataFrame, dict]:
    pieces = []
    hashes = {}
    manifest = load_json(FACTOR_ROOT / "manifest.json")
    if manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary drift")
    for y in YEARS:
        fp = FACTOR_ROOT / f"factor_panel_{y}.csv"
        cp = FACTOR_ROOT / f"opening_clocks_{y}.csv"
        f = pd.read_csv(fp)
        c = pd.read_csv(cp)
        need_f = {"trading_day", "gap", "r20", "rvol20"}
        need_c = {"trading_day", "close_0935", "close_0950"}
        if need_f.difference(f.columns) or need_c.difference(c.columns):
            raise RuntimeError(f"missing columns in {y}")
        for x in (f, c):
            x["trading_day"] = pd.to_datetime(x["trading_day"], errors="raise").dt.normalize()
            if not x["trading_day"].dt.year.eq(y).all() or x["trading_day"].duplicated().any():
                raise RuntimeError(f"year/day inventory drift {y}")
        m = f[["trading_day", "gap", "r20", "rvol20"]].merge(
            c[["trading_day", "close_0935", "close_0950"]], on="trading_day", how="inner", validate="one_to_one"
        )
        pieces.append(m)
        hashes[str(y)] = {
            "factor_panel": {"path": str(fp.relative_to(ROOT)), "sha256": sha256(fp)},
            "opening_clocks": {"path": str(cp.relative_to(ROOT)), "sha256": sha256(cp)},
        }
    x = pd.concat(pieces, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if x["trading_day"].min() != pd.Timestamp("2015-01-05") or x["trading_day"].max() != pd.Timestamp("2020-12-31"):
        raise RuntimeError("merged development boundary drift")
    rvol = pd.to_numeric(x["rvol20"], errors="coerce")
    gap = pd.to_numeric(x["gap"], errors="coerce")
    r20 = pd.to_numeric(x["r20"], errors="coerce")
    x["observed_gap_rvol"] = gap / rvol
    x["trend20_rvol"] = r20 / (np.sqrt(20.0) * rvol)
    x["trend_gap_interaction"] = x["observed_gap_rvol"] * x["trend20_rvol"]
    x["vol_gap_interaction"] = x["observed_gap_rvol"] * np.log(rvol)
    x["c1_direction_score"] = -x["trend_gap_interaction"]
    x["c2_direction_score"] = -x["vol_gap_interaction"]
    x["c1_action"] = np.sign(x["c1_direction_score"].to_numpy(float))
    x["c2_action"] = np.sign(x["c2_direction_score"].to_numpy(float))
    x["comparator_action"] = x["c1_action"]
    x["candidate_action"] = np.where(x["c1_action"] * x["c2_action"] > 0, x["c1_action"], 0.0)
    x["ret_0935_0950"] = pd.to_numeric(x["close_0950"], errors="coerce") / pd.to_numeric(x["close_0935"], errors="coerce") - 1.0
    x["year"] = x["trading_day"].dt.year.astype(int)
    integrity = {
        "factor_manifest": {"path": str((FACTOR_ROOT / "manifest.json").relative_to(ROOT)), "sha256": sha256(FACTOR_ROOT / "manifest.json")},
        "year_shards": hashes,
    }
    return x, integrity


def diagnose(part: pd.DataFrame, minimum_n: int, minimum_active: int) -> dict:
    cols = [
        "rvol20", "observed_gap_rvol", "trend20_rvol", "trend_gap_interaction", "vol_gap_interaction",
        "c1_direction_score", "c2_direction_score", "comparator_action", "candidate_action", "ret_0935_0950",
    ]
    z = part[["trading_day", *cols]].copy()
    numeric = z[cols].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(numeric.to_numpy(float)).all(axis=1) & numeric["rvol20"].gt(0)
    z = z.loc[mask].copy()
    n = int(len(z))
    ca = z["candidate_action"].ne(0)
    ba = z["comparator_action"].ne(0)
    cand_n, base_n = int(ca.sum()), int(ba.sum())
    base_u = z["comparator_action"] * z["ret_0935_0950"]
    cand_u = z["candidate_action"] * z["ret_0935_0950"]
    out = {
        "complete_case_count": n,
        "comparator_active_day_count": base_n,
        "candidate_active_day_count": cand_n,
        "candidate_coverage": float(cand_n / n) if n else None,
        "comparator_hit_rate": float((base_u.loc[ba] > 0).mean()) if base_n else None,
        "candidate_active_hit_rate": float((cand_u.loc[ca] > 0).mean()) if cand_n else None,
        "mean_comparator_signed_utility": float(base_u.mean()) if n else None,
        "mean_candidate_signed_utility": float(cand_u.mean()) if n else None,
        "delta_mean_signed_utility": float(cand_u.mean() - base_u.mean()) if n else None,
        "sufficiency_complete_cases_pass": bool(n >= minimum_n),
        "sufficiency_candidate_active_days_pass": bool(cand_n >= minimum_active),
    }
    out["sufficiency_pass"] = bool(out["sufficiency_complete_cases_pass"] and out["sufficiency_candidate_active_days_pass"])
    return out


def main() -> None:
    if RECEIPT.exists():
        raise RuntimeError("refusing to overwrite existing receipt")
    p, ledger = verify_contracts()
    frame, integrity = load_frame()
    min_n = int(p["sufficiency_gates"]["minimum_complete_cases_each_year"])
    min_active = int(p["sufficiency_gates"]["minimum_candidate_active_days_each_year"])
    annual = {str(y): diagnose(frame.loc[frame["year"].eq(y)].copy(), min_n, min_active) for y in YEARS}
    pooled = diagnose(frame, min_n * len(YEARS), min_active * len(YEARS))
    suff = bool(all(annual[str(y)]["sufficiency_pass"] for y in YEARS))
    deltas = [float(annual[str(y)]["delta_mean_signed_utility"]) for y in YEARS]
    positive_count = int(sum(v > 0 for v in deltas))
    med = float(np.median(deltas))
    pooled_delta = float(pooled["delta_mean_signed_utility"])
    gates = {
        "all_annual_sufficiency_pass": suff,
        "pooled_delta_mean_signed_utility_positive": bool(pooled_delta > 0),
        "positive_annual_delta_count": positive_count,
        "minimum_positive_annual_delta_count_pass": bool(positive_count >= int(p["progression_gates"]["minimum_positive_annual_delta_count"])),
        "median_annual_delta": med,
        "median_annual_delta_nonnegative": bool(med >= 0),
    }
    progressed = bool(suff and gates["pooled_delta_mean_signed_utility_positive"] and gates["minimum_positive_annual_delta_count_pass"] and gates["median_annual_delta_nonnegative"])
    decision = "E1V2_DEV_PROGRESS_RETROSPECTIVE_FACTOR_UTILITY_ADAPTER_CANDIDATE" if progressed else ("E1V2_DEV_INSUFFICIENT" if not suff else "E1V2_DEV_NO_PROGRESS")
    payload = {
        "schema_id": "overnight_downstream_c1_c2_timing_agreement_adapter_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-E1_timing_adapter",
        "phase": "retrospective_factor_utility_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)},
        "validated_upstream_query_ids": {"C1": "5a27b953276382e473c0", "C2": "a1068de9321c04632aad"},
        "candidate": "C2_zero_boundary_agreement_abstention_overlay_on_C1_direction",
        "comparator": "C1_direction_without_C2_abstention",
        "target": "ret_0935_0950",
        "diagnostics": {"pooled": pooled, "by_year": annual},
        "progression_gate_components": gates,
        "decision": decision,
        "maximum_authority_if_progressed": "retrospective_factor_utility_adapter_candidate_only",
        "source_integrity": integrity,
        "ledger_query_count_at_execution": int(ledger.get("query_count", -1)),
        "candidate_attempt_count": 1,
        "threshold_search": False,
        "weight_search": False,
        "alternate_horizon_search": False,
        "upstream_add_drop_search": False,
        "strategy_PnL_optimization": False,
        "cost_model_used": False,
        "account_backtest_opened": False,
        "2021_2025_detailed_rows_opened": False,
        "reusable_blackbox_query_created": False,
        "production_authority": False
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E1V2_C1_C2_TIMING_ADAPTER_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)


if __name__ == "__main__":
    main()
