#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

IDENTITY = "overnight_b1_forward_cycle_portfolio_risk_abstention_validation_v1"
PARENT = "overnight_b1_forward_cycle_portfolio_risk_abstention_v1"
B1_IDENTITY = "overnight_global_risk_open_gap_v1"
B1_QUERY_ID = "6b0b6899f94fd8353a34"
VALIDATION_START = pd.Timestamp("2021-01-01")
VALIDATION_END = pd.Timestamp("2025-12-31")
YEARS = tuple(range(2021, 2026))
CLOCKS = ("14:30", "14:45")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def query_id(payload: dict) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:20]


def trailing_rms_prev(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def verify_contracts(protocol_path: Path, state_path: Path, ledger_path: Path) -> tuple[dict, dict]:
    protocol = read_json(protocol_path)
    state = read_json(state_path)
    ledger = read_json(ledger_path)
    if protocol.get("research_identity") != IDENTITY or protocol.get("parent_development_identity") != PARENT:
        raise RuntimeError("E3v2 validation identity drift")
    if state.get("research_identity") != IDENTITY or state.get("blackbox_query_opened") is not False or state.get("ledger_entry_created") is not False:
        raise RuntimeError("E3v2 validation state is not unopened")
    if protocol.get("validation_window") != "2021-01-01..2025-12-31" or protocol.get("calendar_years") != list(YEARS):
        raise RuntimeError("E3v2 validation window drift")
    if protocol.get("adapter", {}).get("candidate_exposure_rule") != "1 if global_risk_z >= 0 else 0":
        raise RuntimeError("E3v2 validation adapter drift")
    target = protocol.get("target", {})
    if target.get("future_window_length_trading_days") != 5 or target.get("decision_day_return_included") is not False or target.get("2026_rows_may_complete_2025_target") is not False:
        raise RuntimeError("E3v2 validation target drift")
    boot = protocol.get("moving_block_bootstrap", {})
    if boot.get("block_length_decisions") != 4 or boot.get("repetitions") != 1000 or boot.get("seed") != 20260912:
        raise RuntimeError("E3v2 bootstrap drift")
    if ledger.get("query_count") != 11:
        raise RuntimeError("unexpected reusable BLACKBOX ledger count before E3v2 validation")
    q8 = next((q for q in ledger.get("queries", []) if int(q.get("ordinal", -1)) == 8), None)
    if not q8 or q8.get("research_identity") != B1_IDENTITY or q8.get("query_id") != B1_QUERY_ID or q8.get("decision") != "PASS":
        raise RuntimeError("validated B1 authority missing")
    return protocol, ledger


def build_b1(panel_path: Path) -> pd.DataFrame:
    panel = pd.read_parquet(panel_path).copy()
    required = {"trading_day", "us_nasdaq", "us_vix_chg"}
    if required.difference(panel.columns):
        raise RuntimeError("reconstructed panel missing B1 inputs")
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    panel = panel.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if panel["trading_day"].duplicated().any():
        raise RuntimeError("duplicate reconstructed panel day")
    for raw in ("us_nasdaq", "us_vix_chg"):
        panel[raw] = pd.to_numeric(panel[raw], errors="coerce")
        panel[f"{raw}_rms60_prev"] = trailing_rms_prev(panel[raw])
    panel["nasdaq_risk_z"] = panel["us_nasdaq"] / panel["us_nasdaq_rms60_prev"]
    panel["vix_risk_z"] = -panel["us_vix_chg"] / panel["us_vix_chg_rms60_prev"]
    panel["global_risk_z"] = 0.5 * (panel["nasdaq_risk_z"] + panel["vix_risk_z"])
    return panel[["trading_day", "global_risk_z"]].copy()


def load_cycles(consumer_root: Path, protocol: dict) -> pd.DataFrame:
    c = protocol["consumer"]
    daily_path = consumer_root / c["daily_carrier"]
    if sha256(daily_path) != c["daily_carrier_sha256"]:
        raise RuntimeError("consumer daily carrier SHA256 drift")
    columns = ["date", "account_id", "variant_id", "policy_id", "daily_return", "is_rebalance", "replay_segment_id"]
    daily = pd.read_parquet(
        daily_path,
        columns=columns,
        filters=[
            ("replay_segment_id", "==", c["replay_segment"]),
            ("date", ">=", VALIDATION_START),
            ("date", "<=", VALIDATION_END),
        ],
    )
    daily["date"] = pd.to_datetime(daily["date"], errors="raise").dt.normalize()
    if daily.empty or daily["date"].min() < VALIDATION_START or daily["date"].max() > VALIDATION_END:
        raise RuntimeError("consumer validation boundary drift")
    if set(daily["variant_id"].astype(str).unique()) != set(CLOCKS):
        raise RuntimeError("consumer validation variant inventory drift")
    if set(daily["policy_id"].astype(str).unique()) != {c["account_policy"]}:
        raise RuntimeError("consumer validation policy drift")
    if set(daily["replay_segment_id"].astype(str).unique()) != {c["replay_segment"]}:
        raise RuntimeError("consumer validation replay segment drift")
    if daily.duplicated(["account_id", "date"]).any():
        raise RuntimeError("duplicate consumer validation account-day")
    daily["daily_return"] = pd.to_numeric(daily["daily_return"], errors="coerce")

    rows: list[dict[str, object]] = []
    for account_id, g in daily.groupby("account_id", sort=True):
        g = g.sort_values("date", kind="mergesort").reset_index(drop=True)
        variant = str(g["variant_id"].iloc[0])
        for i, row in g.iterrows():
            if not bool(row["is_rebalance"]):
                continue
            day = pd.Timestamp(row["date"])
            if day < VALIDATION_START or day > VALIDATION_END:
                continue
            future = g.iloc[i + 1 : i + 6]
            if len(future) != 5 or pd.Timestamp(future["date"].max()) > VALIDATION_END:
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
        raise RuntimeError("invalid consumer validation cycle inventory")
    return cycles


def moving_block_support(diff: np.ndarray, block: int, reps: int, seed: int) -> float:
    n = len(diff)
    if n < block or not np.isfinite(diff).all():
        return float("nan")
    rng = np.random.default_rng(seed)
    starts_max = n - block
    needed = int(np.ceil(n / block))
    positive = 0
    for _ in range(reps):
        starts = rng.integers(0, starts_max + 1, size=needed)
        sample = np.concatenate([diff[s : s + block] for s in starts])[:n]
        positive += int(float(np.mean(sample)) > 0.0)
    return positive / reps


def hidden_clock_result(frame: pd.DataFrame, clock: str, protocol: dict) -> tuple[bool, bool]:
    c = frame.loc[frame["variant_id"].eq(clock)].sort_values("decision_date", kind="mergesort").copy()
    min_n = int(protocol["sufficiency_gates_each_clock_year"]["minimum_complete_decisions"])
    min_active = int(protocol["sufficiency_gates_each_clock_year"]["minimum_active_decisions"])
    annual_u: list[float] = []
    annual_d: list[float] = []
    sufficient = True
    for year in YEARS:
        y = c.loc[c["year"].eq(year)].copy()
        numeric = y[["global_risk_z", "forward_5_account_return"]].apply(pd.to_numeric, errors="coerce")
        y = y.loc[np.isfinite(numeric.to_numpy(float)).all(axis=1)].copy()
        active = pd.to_numeric(y["global_risk_z"], errors="coerce").ge(0)
        if len(y) < min_n or int(active.sum()) < min_active:
            sufficient = False
            continue
        comp = pd.to_numeric(y["forward_5_account_return"], errors="coerce").to_numpy(float)
        cand = np.where(active.to_numpy(bool), comp, 0.0)
        annual_u.append(float(np.mean(cand) - np.mean(comp)))
        annual_d.append(float(np.mean(np.minimum(cand, 0.0)) - np.mean(np.minimum(comp, 0.0))))
    numeric = c[["global_risk_z", "forward_5_account_return"]].apply(pd.to_numeric, errors="coerce")
    c = c.loc[np.isfinite(numeric.to_numpy(float)).all(axis=1)].copy()
    active = pd.to_numeric(c["global_risk_z"], errors="coerce").ge(0).to_numpy(bool)
    comp = pd.to_numeric(c["forward_5_account_return"], errors="coerce").to_numpy(float)
    cand = np.where(active, comp, 0.0)
    pooled_delta = float(np.mean(cand) - np.mean(comp)) if len(c) else float("nan")
    downside_delta = float(np.mean(np.minimum(cand, 0.0)) - np.mean(np.minimum(comp, 0.0))) if len(c) else float("nan")
    diff = cand - comp
    boot = protocol["moving_block_bootstrap"]
    support = moving_block_support(diff, int(boot["block_length_decisions"]), int(boot["repetitions"]), int(boot["seed"]))
    if not sufficient or len(annual_u) != 5 or len(annual_d) != 5:
        return False, False
    gates = protocol["pass_gates_each_clock"]
    passed = all([
        pooled_delta > 0,
        sum(v > 0 for v in annual_u) >= int(gates["minimum_positive_calendar_year_mean_utility_delta_count"]),
        float(np.median(annual_u)) >= 0,
        downside_delta >= 0,
        sum(v >= 0 for v in annual_d) >= int(gates["minimum_nonnegative_calendar_year_downside_mean_delta_count"]),
        np.isfinite(support) and support >= 0.90,
    ])
    return True, bool(passed)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--consumer-root", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--state", type=Path, required=True)
    ap.add_argument("--ledger", type=Path, required=True)
    ap.add_argument("--high-open-source-manifest", type=Path, required=True)
    ap.add_argument("--reconstruction-contract", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    if args.receipt_out.exists():
        raise RuntimeError("refusing to overwrite E3v2 validation receipt")
    protocol, _ = verify_contracts(args.protocol, args.state, args.ledger)
    b1 = build_b1(args.panel)
    cycles = load_cycles(args.consumer_root, protocol)
    frame = cycles.merge(b1.rename(columns={"trading_day": "decision_date"}), on="decision_date", how="left", validate="many_to_one")

    suff_and_pass = [hidden_clock_result(frame, clock, protocol) for clock in CLOCKS]
    sufficient = all(s for s, _ in suff_and_pass)
    passed = sufficient and all(p for _, p in suff_and_pass)
    decision = "PASS" if passed else ("INSUFFICIENT" if not sufficient else "FAIL")

    protocol_sha = sha256(args.protocol)
    high_open_sha = sha256(args.high_open_source_manifest)
    reconstruction_sha = sha256(args.reconstruction_contract)
    c = protocol["consumer"]
    q_payload = {
        "identity": IDENTITY,
        "protocol_sha256": protocol_sha,
        "high_open_source_manifest_sha256": high_open_sha,
        "reconstruction_contract_sha256": reconstruction_sha,
        "consumer_commit": c["source_commit"],
        "consumer_daily_sha256": c["daily_carrier_sha256"],
        "validation_window": protocol["validation_window"],
    }
    qid = query_id(q_payload)
    receipt = {
        "schema_id": "overnight_downstream_b1_forward_cycle_portfolio_risk_adapter_reusable_blackbox_receipt@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "parent_development_identity": PARENT,
        "product_family": "OFP-E3_portfolio_risk_adapter",
        "decision": decision,
        "query_id": qid,
        "validation_window": protocol["validation_window"],
        "protocol_sha256": protocol_sha,
        "high_open_source_manifest_sha256": high_open_sha,
        "reconstruction_contract_sha256": reconstruction_sha,
        "consumer_repository": c["repository"],
        "consumer_commit": c["source_commit"],
        "consumer_daily_sha256": c["daily_carrier_sha256"],
        "upstream_B1_query_id": B1_QUERY_ID,
        "reconstructed_panel_2015_2020_parity": "PASS",
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "counts_persisted": False,
        "calendar_year_results_persisted": False,
        "bootstrap_results_persisted": False,
        "failure_attribution_persisted": False,
        "account_results_persisted": False,
        "account_execution_authority_if_PASS": False,
        "authority_if_PASS": protocol["authority_if_PASS"],
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "same_period_reuse_is_independent_oos": False,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
