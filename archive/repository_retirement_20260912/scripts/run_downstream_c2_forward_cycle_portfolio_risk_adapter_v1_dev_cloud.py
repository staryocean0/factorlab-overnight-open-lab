#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_c2_forward_cycle_portfolio_risk_abstention_v1"
YEARS = tuple(range(2015, 2021))
CLOCKS = ("14:30", "14:45")
PROTOCOL = ROOT / "docs/governance/downstream_c2_forward_cycle_portfolio_risk_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_c2_forward_cycle_portfolio_risk_adapter_v1_state.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
RECEIPT = ROOT / "docs/research/cloud_downstream_c2_forward_cycle_portfolio_risk_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_contracts() -> tuple[dict, dict]:
    p, s, ledger = read_json(PROTOCOL), read_json(STATE), read_json(LEDGER)
    if p.get("research_identity") != IDENTITY or s.get("research_identity") != IDENTITY or s.get("outcome_opened") is not False:
        raise RuntimeError("E3v3 result-free identity/state drift")
    if p.get("development_window") != "2015-01-05..2020-12-31" or p.get("annual_report_slices") != list(YEARS):
        raise RuntimeError("E3v3 development boundary drift")
    if tuple(p.get("consumer_variants", [])) != CLOCKS:
        raise RuntimeError("E3v3 consumer variants drift")
    if p.get("adapter", {}).get("candidate_exposure_rule") != "1 if c2_risk_on_score >= 0 else 0":
        raise RuntimeError("E3v3 adapter drift")
    if p.get("adapter", {}).get("candidate_attempt_count") != 1 or p.get("adapter", {}).get("semantic_boundary") != 0.0:
        raise RuntimeError("E3v3 candidate family drift")
    t = p.get("target", {})
    if t.get("future_window_length_trading_days") != 5 or t.get("decision_day_return_included") is not False:
        raise RuntimeError("E3v3 target drift")
    q7 = next((q for q in ledger.get("queries", []) if int(q.get("ordinal", -1)) == 7), None)
    if not q7 or q7.get("research_identity") != "overnight_volatility_conditioned_open_state_60m_v1" or q7.get("query_id") != "a1068de9321c04632aad" or q7.get("decision") != "PASS":
        raise RuntimeError("validated C2 authority missing")
    return p, ledger


def load_c2_dev() -> tuple[pd.DataFrame, dict]:
    manifest = read_json(FACTOR_ROOT / "manifest.json")
    if manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary drift")
    expected = manifest.get("outputs", {}).get("factor_panel", {})
    pieces, hashes = [], {}
    for y in YEARS:
        path = FACTOR_ROOT / f"factor_panel_{y}.csv"
        if sha256(path) != expected[str(y)]["sha256"]:
            raise RuntimeError(f"factor shard digest drift {y}")
        f = pd.read_csv(path)
        if {"trading_day", "gap", "rvol20"}.difference(f.columns):
            raise RuntimeError(f"factor shard {y} missing C2 inputs")
        f["trading_day"] = pd.to_datetime(f["trading_day"], errors="raise").dt.normalize()
        if not f["trading_day"].dt.year.eq(y).all() or f["trading_day"].duplicated().any():
            raise RuntimeError(f"factor shard inventory drift {y}")
        rvol = pd.to_numeric(f["rvol20"], errors="coerce")
        gap = pd.to_numeric(f["gap"], errors="coerce")
        observed_gap_rvol = gap / rvol
        vol_gap_interaction = observed_gap_rvol * np.log(rvol)
        pieces.append(pd.DataFrame({
            "decision_date": f["trading_day"],
            "rvol20": rvol,
            "c2_risk_on_score": -vol_gap_interaction,
        }))
        hashes[str(y)] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    x = pd.concat(pieces, ignore_index=True).sort_values("decision_date", kind="mergesort").reset_index(drop=True)
    if x["decision_date"].duplicated().any():
        raise RuntimeError("duplicate C2 development day")
    return x, {
        "factor_manifest": {"path": str((FACTOR_ROOT / "manifest.json").relative_to(ROOT)), "sha256": sha256(FACTOR_ROOT / "manifest.json")},
        "factor_shards": hashes,
    }


def load_cycles(consumer_root: Path, p: dict) -> tuple[pd.DataFrame, dict]:
    c = p["consumer"]
    daily_path = consumer_root / c["daily_carrier"]
    if not daily_path.exists() or sha256(daily_path) != c["daily_carrier_sha256"]:
        raise RuntimeError("consumer portfolio_daily missing or SHA256 drift")
    columns = ["date", "account_id", "variant_id", "policy_id", "daily_return", "is_rebalance", "replay_segment_id"]
    daily = pd.read_parquet(daily_path, columns=columns, filters=[("replay_segment_id", "==", c["replay_segment"])])
    daily["date"] = pd.to_datetime(daily["date"], errors="raise").dt.normalize()
    daily = daily.loc[daily["date"].between(pd.Timestamp("2015-01-05"), pd.Timestamp("2020-12-31"))].copy()
    if daily.empty or set(daily["variant_id"].astype(str).unique()) != set(CLOCKS):
        raise RuntimeError("consumer development variant inventory drift")
    if set(daily["policy_id"].astype(str).unique()) != {c["account_policy"]}:
        raise RuntimeError("consumer policy drift")
    if daily.duplicated(["account_id", "date"]).any():
        raise RuntimeError("duplicate consumer account-day")
    daily["daily_return"] = pd.to_numeric(daily["daily_return"], errors="coerce")
    rows = []
    for account_id, g in daily.groupby("account_id", sort=True):
        g = g.sort_values("date", kind="mergesort").reset_index(drop=True)
        variant = str(g["variant_id"].iloc[0])
        for i, row in g.iterrows():
            if not bool(row["is_rebalance"]):
                continue
            day = pd.Timestamp(row["date"])
            future = g.iloc[i + 1:i + 6]
            if len(future) != 5 or pd.Timestamp(future["date"].max()) > pd.Timestamp("2020-12-31"):
                continue
            vals = pd.to_numeric(future["daily_return"], errors="coerce").to_numpy(float)
            if not np.isfinite(vals).all() or np.any(vals <= -1.0):
                continue
            rows.append({
                "account_id": str(account_id),
                "variant_id": variant,
                "decision_date": day,
                "year": int(day.year),
                "forward_5_account_return": float(np.prod(1.0 + vals) - 1.0),
            })
    cycles = pd.DataFrame(rows)
    if cycles.empty or cycles.duplicated(["account_id", "decision_date"]).any():
        raise RuntimeError("invalid E3v3 cycle inventory")
    return cycles, {
        "consumer_repository": c["repository"],
        "source_commit": c["source_commit"],
        "daily_carrier": c["daily_carrier"],
        "daily_carrier_sha256": sha256(daily_path),
        "materialized_replay_segment": c["replay_segment"],
        "materialized_date_window": "2015-01-05..2020-12-31",
        "post2020_scientific_rows_materialized": False,
    }


def diagnose(part: pd.DataFrame, min_complete: int, min_active: int) -> dict:
    x = part[["decision_date", "rvol20", "c2_risk_on_score", "forward_5_account_return"]].copy()
    numeric = x[["rvol20", "c2_risk_on_score", "forward_5_account_return"]].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(numeric.to_numpy(float)).all(axis=1) & numeric["rvol20"].gt(0)
    x = x.loc[mask].copy()
    n = int(len(x)); active = x["c2_risk_on_score"].ge(0); an = int(active.sum())
    comp = pd.to_numeric(x["forward_5_account_return"], errors="coerce")
    cand = comp.where(active, 0.0)
    comp_down = np.minimum(comp.to_numpy(float), 0.0); cand_down = np.minimum(cand.to_numpy(float), 0.0)
    return {
        "complete_decision_count": n,
        "active_decision_count": an,
        "active_coverage": float(an / n) if n else None,
        "comparator_mean_utility": float(comp.mean()) if n else None,
        "candidate_mean_utility": float(cand.mean()) if n else None,
        "delta_mean_utility": float(cand.mean() - comp.mean()) if n else None,
        "comparator_downside_mean": float(np.mean(comp_down)) if n else None,
        "candidate_downside_mean": float(np.mean(cand_down)) if n else None,
        "delta_downside_mean": float(np.mean(cand_down) - np.mean(comp_down)) if n else None,
        "comparator_positive_cycle_rate": float((comp > 0).mean()) if n else None,
        "candidate_positive_cycle_rate": float((cand > 0).mean()) if n else None,
        "sufficiency_complete_pass": n >= min_complete,
        "sufficiency_active_pass": an >= min_active,
        "sufficiency_pass": n >= min_complete and an >= min_active,
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--consumer-root", type=Path, required=True); args = ap.parse_args()
    if RECEIPT.exists(): raise RuntimeError("refusing to overwrite existing E3v3 receipt")
    p, ledger = verify_contracts(); c2, c2i = load_c2_dev(); cycles, ci = load_cycles(args.consumer_root, p)
    frame = cycles.merge(c2, on="decision_date", how="left", validate="many_to_one")
    min_c = int(p["sufficiency_gates"]["minimum_complete_decisions_each_clock_year"]); min_a = int(p["sufficiency_gates"]["minimum_active_decisions_each_clock_year"])
    min_pos = int(p["progression_gates_each_clock"]["minimum_positive_annual_mean_utility_delta_count"]); min_down = int(p["progression_gates_each_clock"]["minimum_nonnegative_annual_downside_mean_delta_count"])
    diagnostics, passes = {}, {}
    for clock in CLOCKS:
        z = frame.loc[frame["variant_id"].eq(clock)].copy()
        by = {str(y): diagnose(z.loc[z["year"].eq(y)], min_c, min_a) for y in YEARS}; pooled = diagnose(z, min_c*6, min_a*6)
        au = [by[str(y)]["delta_mean_utility"] for y in YEARS]; ad = [by[str(y)]["delta_downside_mean"] for y in YEARS]
        suff = all(by[str(y)]["sufficiency_pass"] for y in YEARS); pos = sum(v is not None and v > 0 for v in au); med = float(np.median([float(v) for v in au if v is not None])); down = sum(v is not None and v >= 0 for v in ad)
        gates = {
            "all_annual_sufficiency_pass": suff,
            "pooled_mean_utility_delta_positive": pooled["delta_mean_utility"] is not None and pooled["delta_mean_utility"] > 0,
            "positive_annual_mean_utility_delta_count": pos,
            "minimum_positive_annual_mean_utility_delta_count_pass": pos >= min_pos,
            "median_annual_mean_utility_delta": med,
            "median_annual_mean_utility_delta_nonnegative": med >= 0,
            "pooled_downside_mean_delta_nonnegative": pooled["delta_downside_mean"] is not None and pooled["delta_downside_mean"] >= 0,
            "nonnegative_annual_downside_mean_delta_count": down,
            "minimum_nonnegative_annual_downside_mean_delta_count_pass": down >= min_down,
        }
        passed = all([gates["all_annual_sufficiency_pass"], gates["pooled_mean_utility_delta_positive"], gates["minimum_positive_annual_mean_utility_delta_count_pass"], gates["median_annual_mean_utility_delta_nonnegative"], gates["pooled_downside_mean_delta_nonnegative"], gates["minimum_nonnegative_annual_downside_mean_delta_count_pass"]])
        diagnostics[clock] = {"pooled": pooled, "by_year": by, "gates": gates, "progression_pass": passed}; passes[clock] = passed
    all_suff = all(diagnostics[c]["gates"]["all_annual_sufficiency_pass"] for c in CLOCKS); joint = all(passes.values())
    decision = "E3V3_DEV_INSUFFICIENT" if not all_suff else ("E3V3_DEV_PROGRESS_RETROSPECTIVE_PORTFOLIO_RISK_ADAPTER_CANDIDATE" if joint else "E3V3_DEV_NO_PROGRESS")
    payload = {
        "schema_id": "overnight_downstream_c2_forward_cycle_portfolio_risk_adapter_dev_diagnostic@1.0",
        "session_date": "2026-09-12", "research_identity": IDENTITY, "product_family": "OFP-E3_portfolio_risk_adapter", "phase": "retrospective_account_overlay_utility_risk_diagnostic", "development_window": "2015-01-05..2020-12-31",
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)}, "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)}, "consumer": p["consumer"],
        "adapter_rule": "candidate_exposure = 1 iff c2_risk_on_score >= 0 else 0", "target": p["target"], "diagnostics": diagnostics, "joint_clock_progression_pass": joint, "decision": decision,
        "maximum_authority_if_progressed": "retrospective_E3_portfolio_risk_adapter_candidate_only", "source_integrity": {"consumer": ci, "C2": c2i}, "validated_C2_query_id": "a1068de9321c04632aad", "ledger_query_count_at_execution": int(ledger.get("query_count", -1)),
        "candidate_attempt_count": 1, "threshold_search": False, "magnitude_bucket_search": False, "clock_selection": False, "target_length_search": False, "consumer_mutation": False, "account_execution_backtest_opened": False, "cost_or_fill_model_used": False, "2021_2025_scientific_rows_opened": False, "blackbox_query_created": False, "production_authority": False
    }
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E3V3_C2_FORWARD_CYCLE_PORTFOLIO_RISK_ADAPTER_DEV_COMPLETE"); print(decision)

if __name__ == "__main__": main()
