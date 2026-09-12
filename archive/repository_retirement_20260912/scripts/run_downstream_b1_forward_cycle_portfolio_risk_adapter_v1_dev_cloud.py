#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_b1_forward_cycle_portfolio_risk_abstention_v1"
YEARS = tuple(range(2015, 2021))
CLOCKS = ("14:30", "14:45")
PROTOCOL = ROOT / "docs/governance/downstream_b1_forward_cycle_portfolio_risk_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_b1_forward_cycle_portfolio_risk_adapter_v1_state.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
RECEIPT = ROOT / "docs/research/cloud_downstream_b1_forward_cycle_portfolio_risk_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def trailing_rms_prev(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def verify_contracts() -> tuple[dict, dict]:
    p = load_json(PROTOCOL)
    s = load_json(STATE)
    ledger = load_json(LEDGER)
    if p.get("research_identity") != IDENTITY or s.get("research_identity") != IDENTITY:
        raise RuntimeError("E3v2 identity drift")
    if s.get("outcome_opened") is not False:
        raise RuntimeError("E3v2 state not result-free")
    if p.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("E3v2 development window drift")
    if tuple(p.get("consumer_variants", [])) != CLOCKS:
        raise RuntimeError("E3v2 consumer variants drift")
    if p.get("adapter", {}).get("semantic_boundary") != 0.0:
        raise RuntimeError("E3v2 boundary drift")
    if p.get("adapter", {}).get("candidate_attempt_count") != 1:
        raise RuntimeError("E3v2 candidate multiplicity drift")
    if p.get("target", {}).get("future_window_length_trading_days") != 5:
        raise RuntimeError("E3v2 target length drift")
    if p.get("target", {}).get("decision_day_return_included") is not False:
        raise RuntimeError("E3v2 decision-day timing drift")
    if p.get("account_execution_backtest_authorized") is not False or p.get("cost_or_fill_model_authorized") is not False:
        raise RuntimeError("E3v2 improper execution authority")
    q8 = next((q for q in ledger.get("queries", []) if int(q.get("ordinal", -1)) == 8), None)
    if not q8 or q8.get("research_identity") != "overnight_global_risk_open_gap_v1" or q8.get("decision") != "PASS":
        raise RuntimeError("validated B1 authority missing")
    if q8.get("query_id") != p["upstream"]["validated_query_id"]:
        raise RuntimeError("B1 query id drift")
    return p, ledger


def load_b1_dev() -> tuple[pd.DataFrame, dict]:
    manifest = load_json(FACTOR_ROOT / "manifest.json")
    if manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary drift")
    expected = manifest.get("outputs", {}).get("factor_panel", {})
    pieces = []
    hashes = {}
    for y in YEARS:
        path = FACTOR_ROOT / f"factor_panel_{y}.csv"
        if sha256(path) != expected[str(y)]["sha256"]:
            raise RuntimeError(f"factor shard digest drift {y}")
        f = pd.read_csv(path)
        required = {"trading_day", "us_nasdaq", "us_vix_chg"}
        if required.difference(f.columns):
            raise RuntimeError(f"factor shard {y} missing B1 columns")
        f["trading_day"] = pd.to_datetime(f["trading_day"], errors="raise").dt.normalize()
        if not f["trading_day"].dt.year.eq(y).all() or f["trading_day"].duplicated().any():
            raise RuntimeError(f"factor shard inventory drift {y}")
        pieces.append(f[["trading_day", "us_nasdaq", "us_vix_chg"]].copy())
        hashes[str(y)] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    x = pd.concat(pieces, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if x["trading_day"].duplicated().any():
        raise RuntimeError("duplicate B1 development day")
    for raw in ["us_nasdaq", "us_vix_chg"]:
        x[raw] = pd.to_numeric(x[raw], errors="coerce")
        x[f"{raw}_rms60_prev"] = trailing_rms_prev(x[raw])
    x["nasdaq_risk_z"] = x["us_nasdaq"] / x["us_nasdaq_rms60_prev"]
    x["vix_risk_z"] = -x["us_vix_chg"] / x["us_vix_chg_rms60_prev"]
    x["global_risk_z"] = 0.5 * (x["nasdaq_risk_z"] + x["vix_risk_z"])
    return x[["trading_day", "global_risk_z"]], {
        "factor_manifest": {"path": str((FACTOR_ROOT / "manifest.json").relative_to(ROOT)), "sha256": sha256(FACTOR_ROOT / "manifest.json")},
        "factor_shards": hashes,
    }


def load_consumer_cycles(consumer_root: Path, p: dict) -> tuple[pd.DataFrame, dict]:
    c = p["consumer"]
    daily_path = consumer_root / c["daily_carrier"]
    manifest_path = consumer_root / c["snapshot_manifest"]
    if not daily_path.exists() or not manifest_path.exists():
        raise RuntimeError("consumer snapshot files missing")
    if sha256(daily_path) != c["daily_carrier_sha256"]:
        raise RuntimeError("consumer portfolio_daily SHA256 drift")
    manifest_meta = load_json(manifest_path)
    if manifest_meta.get("identity", {}).get("strategy_id") != c["strategy_id"]:
        raise RuntimeError("consumer strategy identity drift")
    manifest_digest = str(manifest_meta.get("artifact_digests", {}).get("portfolio_daily.parquet", ""))
    if manifest_digest != "sha256:" + c["daily_carrier_sha256"]:
        raise RuntimeError("consumer snapshot manifest daily digest drift")

    columns = [
        "date", "account_id", "variant_id", "policy_id", "cost_scenario_id",
        "daily_return", "is_rebalance", "replay_segment_id",
    ]
    daily = pd.read_parquet(
        daily_path,
        columns=columns,
        filters=[("replay_segment_id", "==", c["replay_segment"])],
    )
    daily["date"] = pd.to_datetime(daily["date"], errors="raise").dt.normalize()
    daily = daily.loc[daily["date"].between(pd.Timestamp("2015-01-05"), pd.Timestamp("2020-12-31"))].copy()
    if daily.empty:
        raise RuntimeError("no E3v2 development consumer rows")
    if set(daily["variant_id"].astype(str).unique()) != set(CLOCKS):
        raise RuntimeError("consumer variant inventory drift")
    if set(daily["policy_id"].astype(str).unique()) != {c["account_policy"]}:
        raise RuntimeError("consumer account policy drift")
    if set(daily["replay_segment_id"].astype(str).unique()) != {c["replay_segment"]}:
        raise RuntimeError("consumer replay segment drift")
    if daily.duplicated(["account_id", "date"]).any():
        raise RuntimeError("duplicate consumer account-day")
    daily["daily_return"] = pd.to_numeric(daily["daily_return"], errors="coerce")

    cycle_rows = []
    for account_id, g in daily.groupby("account_id", sort=True):
        g = g.sort_values("date", kind="mergesort").reset_index(drop=True)
        variant = str(g["variant_id"].iloc[0])
        for i, row in g.iterrows():
            if not bool(row["is_rebalance"]):
                continue
            decision_date = pd.Timestamp(row["date"])
            if decision_date < pd.Timestamp("2015-01-05") or decision_date > pd.Timestamp("2020-12-31"):
                continue
            future = g.iloc[i + 1 : i + 6]
            if len(future) != 5:
                continue
            if pd.Timestamp(future["date"].max()) > pd.Timestamp("2020-12-31"):
                continue
            vals = pd.to_numeric(future["daily_return"], errors="coerce").to_numpy(float)
            if not np.isfinite(vals).all() or np.any(vals <= -1.0):
                continue
            fwd = float(np.prod(1.0 + vals) - 1.0)
            cycle_rows.append({
                "account_id": str(account_id),
                "variant_id": variant,
                "decision_date": decision_date,
                "year": int(decision_date.year),
                "forward_5_account_return": fwd,
            })
    cycles = pd.DataFrame(cycle_rows)
    if cycles.empty:
        raise RuntimeError("no complete E3v2 cycles")
    if cycles.duplicated(["account_id", "decision_date"]).any():
        raise RuntimeError("duplicate E3v2 cycle")
    return cycles, {
        "consumer_repository": c["repository"],
        "source_commit": c["source_commit"],
        "daily_carrier": c["daily_carrier"],
        "daily_carrier_sha256": sha256(daily_path),
        "snapshot_manifest": c["snapshot_manifest"],
        "snapshot_manifest_strategy_id": manifest_meta.get("identity", {}).get("strategy_id"),
        "materialized_replay_segment": c["replay_segment"],
        "materialized_date_window": "2015-01-05..2020-12-31",
        "post2020_scientific_rows_materialized": False,
    }


def diagnose(part: pd.DataFrame, min_complete: int, min_active: int) -> dict:
    x = part[["decision_date", "global_risk_z", "forward_5_account_return"]].copy()
    numeric = x[["global_risk_z", "forward_5_account_return"]].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(numeric.to_numpy(float)).all(axis=1)
    x = x.loc[mask].copy()
    n = int(len(x))
    active = pd.to_numeric(x["global_risk_z"], errors="coerce").ge(0)
    active_n = int(active.sum())
    comp = pd.to_numeric(x["forward_5_account_return"], errors="coerce")
    cand = comp.where(active, 0.0)
    comp_down = np.minimum(comp.to_numpy(float), 0.0)
    cand_down = np.minimum(cand.to_numpy(float), 0.0)
    return {
        "complete_decision_count": n,
        "active_decision_count": active_n,
        "active_coverage": float(active_n / n) if n else None,
        "comparator_mean_utility": float(comp.mean()) if n else None,
        "candidate_mean_utility": float(cand.mean()) if n else None,
        "delta_mean_utility": float(cand.mean() - comp.mean()) if n else None,
        "comparator_downside_mean": float(np.mean(comp_down)) if n else None,
        "candidate_downside_mean": float(np.mean(cand_down)) if n else None,
        "delta_downside_mean": float(np.mean(cand_down) - np.mean(comp_down)) if n else None,
        "comparator_positive_cycle_rate": float((comp > 0).mean()) if n else None,
        "candidate_positive_cycle_rate": float((cand > 0).mean()) if n else None,
        "sufficiency_complete_pass": bool(n >= min_complete),
        "sufficiency_active_pass": bool(active_n >= min_active),
        "sufficiency_pass": bool(n >= min_complete and active_n >= min_active),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consumer-root", type=Path, required=True)
    args = ap.parse_args()
    if RECEIPT.exists():
        raise RuntimeError("refusing to overwrite existing E3v2 receipt")
    p, ledger = verify_contracts()
    b1, b1_integrity = load_b1_dev()
    cycles, consumer_integrity = load_consumer_cycles(args.consumer_root, p)
    frame = cycles.merge(b1.rename(columns={"trading_day": "decision_date"}), on="decision_date", how="left", validate="many_to_one")

    min_complete = int(p["sufficiency_gates"]["minimum_complete_decisions_each_clock_year"])
    min_active = int(p["sufficiency_gates"]["minimum_active_decisions_each_clock_year"])
    min_pos = int(p["progression_gates_each_clock"]["minimum_positive_annual_mean_utility_delta_count"])
    min_down = int(p["progression_gates_each_clock"]["minimum_nonnegative_annual_downside_mean_delta_count"])

    diagnostics = {}
    clock_pass = {}
    for clock in CLOCKS:
        c = frame.loc[frame["variant_id"].eq(clock)].copy()
        by_year = {str(y): diagnose(c.loc[c["year"].eq(y)], min_complete, min_active) for y in YEARS}
        pooled = diagnose(c, min_complete * len(YEARS), min_active * len(YEARS))
        annual_u = [by_year[str(y)]["delta_mean_utility"] for y in YEARS]
        annual_d = [by_year[str(y)]["delta_downside_mean"] for y in YEARS]
        sufficient = all(by_year[str(y)]["sufficiency_pass"] for y in YEARS)
        pos_count = sum(v is not None and float(v) > 0 for v in annual_u)
        median_u = float(np.median([float(v) for v in annual_u if v is not None]))
        down_count = sum(v is not None and float(v) >= 0 for v in annual_d)
        gates = {
            "all_annual_sufficiency_pass": bool(sufficient),
            "pooled_mean_utility_delta_positive": bool(pooled["delta_mean_utility"] is not None and pooled["delta_mean_utility"] > 0),
            "positive_annual_mean_utility_delta_count": int(pos_count),
            "minimum_positive_annual_mean_utility_delta_count_pass": bool(pos_count >= min_pos),
            "median_annual_mean_utility_delta": median_u,
            "median_annual_mean_utility_delta_nonnegative": bool(median_u >= 0),
            "pooled_downside_mean_delta_nonnegative": bool(pooled["delta_downside_mean"] is not None and pooled["delta_downside_mean"] >= 0),
            "nonnegative_annual_downside_mean_delta_count": int(down_count),
            "minimum_nonnegative_annual_downside_mean_delta_count_pass": bool(down_count >= min_down),
        }
        passed = all([
            gates["all_annual_sufficiency_pass"],
            gates["pooled_mean_utility_delta_positive"],
            gates["minimum_positive_annual_mean_utility_delta_count_pass"],
            gates["median_annual_mean_utility_delta_nonnegative"],
            gates["pooled_downside_mean_delta_nonnegative"],
            gates["minimum_nonnegative_annual_downside_mean_delta_count_pass"],
        ])
        diagnostics[clock] = {"pooled": pooled, "by_year": by_year, "gates": gates, "progression_pass": bool(passed)}
        clock_pass[clock] = bool(passed)

    all_sufficient = all(diagnostics[c]["gates"]["all_annual_sufficiency_pass"] for c in CLOCKS)
    joint_pass = all(clock_pass.values())
    if not all_sufficient:
        decision = "E3V2_DEV_INSUFFICIENT"
    elif joint_pass:
        decision = "E3V2_DEV_PROGRESS_RETROSPECTIVE_PORTFOLIO_RISK_ADAPTER_CANDIDATE"
    else:
        decision = "E3V2_DEV_NO_PROGRESS"

    payload = {
        "schema_id": "overnight_downstream_b1_forward_cycle_portfolio_risk_adapter_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-E3_portfolio_risk_adapter",
        "phase": "retrospective_account_overlay_utility_risk_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)},
        "consumer": p["consumer"],
        "adapter_rule": "candidate_exposure = 1 iff global_risk_z >= 0 else 0",
        "target": p["target"],
        "diagnostics": diagnostics,
        "joint_clock_progression_pass": bool(joint_pass),
        "decision": decision,
        "maximum_authority_if_progressed": "retrospective_E3_portfolio_risk_adapter_candidate_only",
        "source_integrity": {"consumer": consumer_integrity, "B1": b1_integrity},
        "validated_B1_query_id": p["upstream"]["validated_query_id"],
        "ledger_query_count_at_execution": int(ledger.get("query_count", -1)),
        "candidate_attempt_count": 1,
        "threshold_search": False,
        "magnitude_bucket_search": False,
        "clock_selection": False,
        "target_length_search": False,
        "consumer_mutation": False,
        "account_execution_backtest_opened": False,
        "cost_or_fill_model_used": False,
        "2021_2025_scientific_rows_opened": False,
        "blackbox_query_created": False,
        "production_authority": False
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E3V2_B1_FORWARD_CYCLE_PORTFOLIO_RISK_ADAPTER_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)


if __name__ == "__main__":
    main()
