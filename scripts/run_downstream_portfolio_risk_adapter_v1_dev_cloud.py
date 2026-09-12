#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_c1_intraday_portfolio_risk_abstention_v1"
YEARS = tuple(range(2015, 2021))
CLOCKS = ("14:30", "14:45")
DEV_START = pd.Timestamp("2015-01-05")
DEV_END = pd.Timestamp("2020-12-31")
CONSUMER_COMMIT = "af2e478aaff5c8ef7f753424b57fd2d19019f248"
HOLDINGS_SHA = "1a0d6e52849fef50a94e6a204a498ea8379af6f837a866216fdb86539723ac01"
DAILY_SHA = "8f6be84836d7839642e3cf722639887be339fa3f660c274b16d7c0a2b56ae1a5"
SNAPSHOT_CANONICAL = "sha256:b652b4c3ddeeef9c4999a5ea7d61af6082a2fe7fa1910d32f3c73fa33b2729ca"
PROTOCOL = ROOT / "docs/governance/downstream_portfolio_risk_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_portfolio_risk_adapter_v1_state.json"
AUTHORITY = ROOT / "docs/governance/current_authority_v1.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
PRICE_ROOT = ROOT / "data/e3_portfolio_intraday_qfq_2015_2020"
UPLOAD_RECEIPT = ROOT / "docs/research/e3_portfolio_intraday_qfq_upload_receipt_v1.json"
OUTPUT = ROOT / "docs/research/cloud_downstream_portfolio_risk_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_contracts(holdings_path: Path, daily_path: Path, snapshot_manifest_path: Path) -> tuple[dict, dict]:
    protocol = read_json(PROTOCOL)
    state = read_json(STATE)
    authority = read_json(AUTHORITY)
    ledger = read_json(LEDGER)
    carrier = read_json(PRICE_ROOT / "manifest.json")
    upload = read_json(UPLOAD_RECEIPT)
    factor_manifest = read_json(FACTOR_ROOT / "manifest.json")
    snapshot_manifest = read_json(snapshot_manifest_path)

    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("E3 protocol identity drift")
    if state.get("research_identity") != IDENTITY or state.get("outcome_opened") is not False:
        raise RuntimeError("E3 state is not result-free/pending")
    active = authority.get("active_research") or {}
    if active.get("identity") != IDENTITY:
        raise RuntimeError("E3 is not current active research")
    if protocol.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("E3 development window drift")
    if protocol.get("annual_report_slices") != list(YEARS):
        raise RuntimeError("E3 annual slices drift")
    if tuple(protocol.get("consumer_variants", [])) != CLOCKS:
        raise RuntimeError("E3 consumer clock drift")
    adapter = protocol.get("adapter", {})
    if adapter.get("candidate_exposure_rule") != "0 if c1_action < 0 else 1":
        raise RuntimeError("E3 candidate rule drift")
    if float(adapter.get("semantic_boundary")) != 0.0 or int(adapter.get("free_parameters")) != 0:
        raise RuntimeError("E3 gained free parameters")
    if protocol.get("account_execution_authorized") is not False or protocol.get("strategy_mutation_authorized") is not False:
        raise RuntimeError("E3 improperly grants account/strategy authority")
    if protocol.get("future_2021_2025_validation_authorized_now") is not False:
        raise RuntimeError("E3 improperly opens 2021-2025")
    if ledger.get("query_count") != 6:
        raise RuntimeError("unexpected BLACKBOX ledger count before E3 DEV")
    q2 = next((q for q in ledger.get("queries", []) if int(q.get("ordinal", -1)) == 2), None)
    if not q2 or q2.get("research_identity") != "overnight_trend_conditioned_open_state_15m_v1" or q2.get("decision") != "PASS":
        raise RuntimeError("validated C1 authority missing")

    consumer = protocol.get("consumer", {})
    if consumer.get("source_commit") != CONSUMER_COMMIT:
        raise RuntimeError("consumer commit drift")
    if consumer.get("holdings_scientific_sha256") != HOLDINGS_SHA or consumer.get("portfolio_daily_scientific_sha256") != DAILY_SHA:
        raise RuntimeError("consumer scientific digest drift")
    if sha256(holdings_path) != HOLDINGS_SHA or sha256(daily_path) != DAILY_SHA:
        raise RuntimeError("downloaded consumer parquet digest mismatch")
    if snapshot_manifest.get("canonical_digest") != SNAPSHOT_CANONICAL:
        raise RuntimeError("consumer snapshot canonical digest mismatch")
    if snapshot_manifest.get("identity", {}).get("strategy_id") != consumer.get("strategy_id"):
        raise RuntimeError("consumer snapshot strategy mismatch")

    if carrier.get("research_identity") != IDENTITY or carrier.get("consumer_commit") != CONSUMER_COMMIT:
        raise RuntimeError("E3 price carrier identity drift")
    if carrier.get("post_2020_rows_loaded") is not False:
        raise RuntimeError("E3 price carrier opened post-2020 rows")
    transform = carrier.get("transform", {})
    forbidden_true = ["feature_engineering", "target_engineering", "scientific_analysis", "nearest_clock_substitution", "forward_fill", "backward_fill", "resampling"]
    if any(transform.get(name) is not False for name in forbidden_true):
        raise RuntimeError("E3 price carrier transform drift")
    if carrier.get("read_window") != {"start": "2015-01-05", "end": "2020-12-31"}:
        raise RuntimeError("E3 price carrier window drift")
    if upload.get("scientific_diagnostic_performed") is not False or upload.get("portfolio_return_calculated") is not False or upload.get("C1_calculated") is not False:
        raise RuntimeError("local E3 upload performed unauthorized science")
    if upload.get("BLACKBOX_run") is not False or upload.get("post_2020_rows_loaded") is not False:
        raise RuntimeError("local E3 upload opened forbidden evidence")

    if factor_manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary drift")

    files = carrier.get("files", [])
    if len(files) != 6:
        raise RuntimeError("E3 carrier file inventory drift")
    for item in files:
        path = ROOT / item["path"]
        if not path.exists():
            raise RuntimeError(f"missing E3 carrier shard: {path}")
        if sha256(path) != item["sha256"]:
            raise RuntimeError(f"E3 carrier shard digest mismatch: {path}")
        frame = pd.read_csv(path, dtype={"asset_id": str})
        if len(frame) != int(item["rows"]):
            raise RuntimeError(f"E3 carrier row count mismatch: {path}")
        frame["trading_day"] = pd.to_datetime(frame["trading_day"], errors="raise").dt.normalize()
        if frame["trading_day"].min().strftime("%Y-%m-%d") != item["min_day"] or frame["trading_day"].max().strftime("%Y-%m-%d") != item["max_day"]:
            raise RuntimeError(f"E3 carrier date bound mismatch: {path}")
        if (frame["trading_day"] > DEV_END).any() or (frame["trading_day"] < DEV_START).any():
            raise RuntimeError("E3 carrier row outside development window")

    integrity = {
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)},
        "current_authority": {"path": str(AUTHORITY.relative_to(ROOT)), "sha256": sha256(AUTHORITY)},
        "blackbox_ledger_query_count": int(ledger["query_count"]),
        "consumer": {
            "repository": consumer["repository"],
            "commit": CONSUMER_COMMIT,
            "holdings_sha256": HOLDINGS_SHA,
            "portfolio_daily_sha256": DAILY_SHA,
            "snapshot_manifest_canonical_digest": SNAPSHOT_CANONICAL,
        },
        "price_carrier": {
            "manifest_path": str((PRICE_ROOT / "manifest.json").relative_to(ROOT)),
            "manifest_sha256": sha256(PRICE_ROOT / "manifest.json"),
            "upload_receipt_path": str(UPLOAD_RECEIPT.relative_to(ROOT)),
            "upload_receipt_sha256": sha256(UPLOAD_RECEIPT),
            "inventory_rows": int(carrier["inventory_rows"]),
        },
        "factor_runtime_manifest": {
            "path": str((FACTOR_ROOT / "manifest.json").relative_to(ROOT)),
            "sha256": sha256(FACTOR_ROOT / "manifest.json"),
        },
        "validated_C1_query_id": q2["query_id"],
    }
    return protocol, integrity


def load_price_carrier() -> pd.DataFrame:
    pieces = []
    for year in YEARS:
        path = PRICE_ROOT / f"portfolio_intraday_qfq_{year}.csv"
        frame = pd.read_csv(path, dtype={"asset_id": str})
        required = {"trading_day", "prev_trading_day", "asset_id", "prev_close_1500_qfq", "close_0935_qfq", "close_0950_qfq"}
        if required.difference(frame.columns):
            raise RuntimeError(f"E3 carrier {year} missing columns")
        frame["asset_id"] = frame["asset_id"].astype(str).str.zfill(6)
        frame["trading_day"] = pd.to_datetime(frame["trading_day"], errors="raise").dt.normalize()
        frame["prev_trading_day"] = pd.to_datetime(frame["prev_trading_day"], errors="raise").dt.normalize()
        if not frame["trading_day"].dt.year.eq(year).all():
            raise RuntimeError(f"E3 carrier year drift {year}")
        if frame.duplicated(["trading_day", "prev_trading_day", "asset_id"]).any():
            raise RuntimeError(f"duplicate E3 carrier key {year}")
        pieces.append(frame)
    out = pd.concat(pieces, ignore_index=True)
    return out.sort_values(["trading_day", "asset_id"], kind="mergesort").reset_index(drop=True)


def load_c1() -> pd.DataFrame:
    pieces = []
    for year in YEARS:
        path = FACTOR_ROOT / f"factor_panel_{year}.csv"
        frame = pd.read_csv(path)
        required = {"trading_day", "gap", "r20", "rvol20"}
        if required.difference(frame.columns):
            raise RuntimeError(f"factor shard {year} missing C1 columns")
        frame["trading_day"] = pd.to_datetime(frame["trading_day"], errors="raise").dt.normalize()
        pieces.append(frame[["trading_day", "gap", "r20", "rvol20"]].copy())
    out = pd.concat(pieces, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if out["trading_day"].duplicated().any():
        raise RuntimeError("duplicate C1 trading day")
    rvol = pd.to_numeric(out["rvol20"], errors="coerce")
    gap = pd.to_numeric(out["gap"], errors="coerce")
    r20 = pd.to_numeric(out["r20"], errors="coerce")
    observed_gap_rvol = gap / rvol
    trend20_rvol = r20 / (np.sqrt(20.0) * rvol)
    interaction = observed_gap_rvol * trend20_rvol
    score = -interaction
    action = np.sign(score.to_numpy(float))
    action[~np.isfinite(score.to_numpy(float))] = np.nan
    out["c1_action"] = action
    out["rvol20_positive"] = rvol.gt(0)
    return out[["trading_day", "c1_action", "rvol20_positive"]]


def reconstruct_account_days(holdings: pd.DataFrame, daily: pd.DataFrame, prices: pd.DataFrame, c1: pd.DataFrame) -> pd.DataFrame:
    for frame in (holdings, daily):
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    holdings["asset_id"] = holdings["asset_id"].astype(str).str.zfill(6)

    identity_cols = ["account_id", "variant_id", "policy_id", "cost_scenario_id"]
    required_hold = {"date", *identity_cols, "asset_id", "market_value"}
    required_daily = {"date", *identity_cols, "nav", "cash", "cash_weight"}
    if required_hold.difference(holdings.columns):
        raise RuntimeError(f"consumer holdings missing columns: {sorted(required_hold.difference(holdings.columns))}")
    if required_daily.difference(daily.columns):
        raise RuntimeError(f"consumer daily missing columns: {sorted(required_daily.difference(daily.columns))}")

    # Development window uses the frozen 2011_2020 replay segment accounts only.
    holdings = holdings.loc[holdings["variant_id"].astype(str).isin(CLOCKS)].copy()
    daily = daily.loc[daily["variant_id"].astype(str).isin(CLOCKS)].copy()
    if "replay_segment_id" in holdings.columns:
        holdings = holdings.loc[holdings["replay_segment_id"].astype(str).eq("2011_2020")].copy()
    else:
        holdings = holdings.loc[holdings["account_id"].astype(str).str.endswith(":2011_2020")].copy()
    if "replay_segment_id" in daily.columns:
        daily = daily.loc[daily["replay_segment_id"].astype(str).eq("2011_2020")].copy()
    else:
        daily = daily.loc[daily["account_id"].astype(str).str.endswith(":2011_2020")].copy()

    # Build a unique current-day -> previous-day spine from the carrier.
    spine = prices[["trading_day", "prev_trading_day"]].drop_duplicates().sort_values("trading_day", kind="mergesort")
    if spine["trading_day"].duplicated().any():
        raise RuntimeError("E3 carrier has non-unique previous-day mapping")
    spine = spine.loc[spine["trading_day"].between(DEV_START, DEV_END)].copy()
    spine = spine.merge(c1, on="trading_day", how="left", validate="one_to_one")

    rows: list[dict[str, object]] = []
    price_key = prices.set_index(["trading_day", "prev_trading_day", "asset_id"], verify_integrity=True)
    daily_key = daily.set_index([*identity_cols, "date"], verify_integrity=True)

    account_identities = daily[identity_cols].drop_duplicates().sort_values(["variant_id", "account_id"], kind="mergesort")
    # Exactly one development replay account per frozen clock is expected.
    counts = account_identities.groupby("variant_id", sort=True).size().to_dict()
    if any(int(counts.get(clock, 0)) != 1 for clock in CLOCKS):
        raise RuntimeError(f"unexpected E3 development account inventory: {counts}")

    holdings_groups = {
        tuple([*key[:-1], pd.Timestamp(key[-1])]): group.copy()
        for key, group in holdings.groupby([*identity_cols, "date"], sort=False)
    }

    for ident in account_identities.itertuples(index=False):
        identity = [str(ident.account_id), str(ident.variant_id), str(ident.policy_id), str(ident.cost_scenario_id)]
        for srow in spine.itertuples(index=False):
            day = pd.Timestamp(srow.trading_day)
            prev = pd.Timestamp(srow.prev_trading_day)
            dkey = tuple([*identity, prev])
            if dkey not in daily_key.index:
                rows.append({
                    "trading_day": day,
                    "year": int(day.year),
                    "account_id": identity[0],
                    "variant_id": identity[1],
                    "complete": False,
                    "incomplete_reason": "previous_daily_missing",
                    "c1_action": getattr(srow, "c1_action"),
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue
            prev_daily = daily_key.loc[dkey]
            hkey = tuple([*identity, prev])
            held = holdings_groups.get(hkey)
            if held is None or held.empty:
                rows.append({
                    "trading_day": day,
                    "year": int(day.year),
                    "account_id": identity[0],
                    "variant_id": identity[1],
                    "complete": False,
                    "incomplete_reason": "previous_holdings_missing",
                    "c1_action": getattr(srow, "c1_action"),
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue

            nav = float(pd.to_numeric(pd.Series([prev_daily["nav"]]), errors="coerce").iloc[0])
            cash = float(pd.to_numeric(pd.Series([prev_daily["cash"]]), errors="coerce").iloc[0])
            action = float(getattr(srow, "c1_action")) if pd.notna(getattr(srow, "c1_action")) else np.nan
            rvol_ok = bool(getattr(srow, "rvol20_positive")) if pd.notna(getattr(srow, "rvol20_positive")) else False
            if not np.isfinite(nav) or nav <= 0 or not np.isfinite(cash) or not np.isfinite(action) or not rvol_ok:
                rows.append({
                    "trading_day": day,
                    "year": int(day.year),
                    "account_id": identity[0],
                    "variant_id": identity[1],
                    "complete": False,
                    "incomplete_reason": "daily_or_C1_invalid",
                    "c1_action": action,
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue

            market_value = pd.to_numeric(held["market_value"], errors="coerce").to_numpy(float)
            assets = held["asset_id"].astype(str).str.zfill(6).to_numpy()
            if not np.isfinite(market_value).all():
                rows.append({
                    "trading_day": day, "year": int(day.year), "account_id": identity[0], "variant_id": identity[1],
                    "complete": False, "incomplete_reason": "holding_market_value_invalid", "c1_action": action,
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue

            keys = [(day, prev, str(asset)) for asset in assets]
            try:
                px = price_key.loc[keys, ["prev_close_1500_qfq", "close_0935_qfq", "close_0950_qfq"]].copy()
            except KeyError:
                rows.append({
                    "trading_day": day, "year": int(day.year), "account_id": identity[0], "variant_id": identity[1],
                    "complete": False, "incomplete_reason": "price_inventory_key_missing", "c1_action": action,
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue
            arr = px.apply(pd.to_numeric, errors="coerce").to_numpy(float)
            if not np.isfinite(arr).all() or (arr <= 0).any():
                rows.append({
                    "trading_day": day, "year": int(day.year), "account_id": identity[0], "variant_id": identity[1],
                    "complete": False, "incomplete_reason": "exact_price_missing_or_invalid", "c1_action": action,
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue

            w = market_value / nav
            cash_w = cash / nav
            g = arr[:, 1] / arr[:, 0]
            intraday = arr[:, 2] / arr[:, 1] - 1.0
            denom = cash_w + float(np.sum(w * g))
            if not np.isfinite(denom) or denom <= 0:
                rows.append({
                    "trading_day": day, "year": int(day.year), "account_id": identity[0], "variant_id": identity[1],
                    "complete": False, "incomplete_reason": "revalued_denominator_invalid", "c1_action": action,
                    "portfolio_ret_0935_0950": np.nan,
                })
                continue
            ret = float(np.sum(w * g * intraday) / denom)
            rows.append({
                "trading_day": day,
                "year": int(day.year),
                "account_id": identity[0],
                "variant_id": identity[1],
                "complete": bool(np.isfinite(ret)),
                "incomplete_reason": None if np.isfinite(ret) else "portfolio_return_nonfinite",
                "c1_action": action,
                "portfolio_ret_0935_0950": ret,
            })

    return pd.DataFrame(rows).sort_values(["variant_id", "trading_day"], kind="mergesort").reset_index(drop=True)


def diagnose(frame: pd.DataFrame, min_complete: int, min_exposed: int, min_derisked: int) -> dict:
    x = frame.loc[frame["complete"]].copy()
    n = int(len(x))
    exposed = x["c1_action"].ge(0)
    derisked = x["c1_action"].lt(0)
    exposed_n = int(exposed.sum())
    derisked_n = int(derisked.sum())
    comp = pd.to_numeric(x["portfolio_ret_0935_0950"], errors="coerce")
    cand = comp.where(exposed, 0.0)
    if n:
        comp_mean = float(comp.mean())
        cand_mean = float(cand.mean())
        comp_p05 = float(np.quantile(comp.to_numpy(float), 0.05))
        cand_p05 = float(np.quantile(cand.to_numpy(float), 0.05))
    else:
        comp_mean = cand_mean = comp_p05 = cand_p05 = None
    out = {
        "complete_account_day_count": n,
        "candidate_exposed_day_count": exposed_n,
        "candidate_derisked_day_count": derisked_n,
        "candidate_exposure_coverage": float(exposed_n / n) if n else None,
        "mean_comparator_utility": comp_mean,
        "mean_candidate_utility": cand_mean,
        "delta_mean_utility": None if n == 0 else float(cand_mean - comp_mean),
        "comparator_p05": comp_p05,
        "candidate_p05": cand_p05,
        "p05_delta": None if n == 0 else float(cand_p05 - comp_p05),
        "sufficiency_complete_pass": bool(n >= min_complete),
        "sufficiency_exposed_pass": bool(exposed_n >= min_exposed),
        "sufficiency_derisked_pass": bool(derisked_n >= min_derisked),
    }
    out["sufficiency_pass"] = bool(out["sufficiency_complete_pass"] and out["sufficiency_exposed_pass"] and out["sufficiency_derisked_pass"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--consumer-holdings", type=Path, required=True)
    ap.add_argument("--consumer-daily", type=Path, required=True)
    ap.add_argument("--consumer-snapshot-manifest", type=Path, required=True)
    args = ap.parse_args()

    if OUTPUT.exists():
        raise RuntimeError(f"refusing to overwrite existing E3 DEV receipt: {OUTPUT}")

    protocol, integrity = verify_contracts(args.consumer_holdings, args.consumer_daily, args.consumer_snapshot_manifest)
    holdings = pd.read_parquet(args.consumer_holdings)
    daily = pd.read_parquet(args.consumer_daily)
    prices = load_price_carrier()
    c1 = load_c1()
    account_days = reconstruct_account_days(holdings, daily, prices, c1)

    suff = protocol["sufficiency_gates"]
    min_complete = int(suff["minimum_complete_account_days_each_clock_year"])
    min_exposed = int(suff["minimum_exposed_days_each_clock_year"])
    min_derisked = int(suff["minimum_derisked_days_each_clock_year"])

    diagnostics: dict[str, dict] = {}
    clock_gates: dict[str, dict] = {}
    all_clock_pass = True
    for clock in CLOCKS:
        local = account_days.loc[account_days["variant_id"].eq(clock)].copy()
        annual = {str(y): diagnose(local.loc[local["year"].eq(y)], min_complete, min_exposed, min_derisked) for y in YEARS}
        pooled = diagnose(local, min_complete * len(YEARS), min_exposed * len(YEARS), min_derisked * len(YEARS))
        annual_delta = [float(annual[str(y)]["delta_mean_utility"]) for y in YEARS if annual[str(y)]["delta_mean_utility"] is not None]
        annual_p05_delta = [float(annual[str(y)]["p05_delta"]) for y in YEARS if annual[str(y)]["p05_delta"] is not None]
        positive_count = int(sum(v > 0 for v in annual_delta))
        p05_not_worse_count = int(sum(v >= 0 for v in annual_p05_delta))
        all_suff = bool(all(annual[str(y)]["sufficiency_pass"] for y in YEARS))
        gates = {
            "all_annual_sufficiency_pass": all_suff,
            "pooled_mean_utility_delta_positive": bool(pooled["delta_mean_utility"] is not None and float(pooled["delta_mean_utility"]) > 0),
            "positive_annual_mean_utility_delta_count": positive_count,
            "minimum_positive_annual_mean_utility_delta_count_pass": bool(positive_count >= int(protocol["progression_gates_each_clock"]["minimum_positive_annual_mean_utility_delta_count"])),
            "median_annual_mean_utility_delta": float(np.median(annual_delta)) if annual_delta else None,
            "median_annual_mean_utility_delta_nonnegative": bool(annual_delta and float(np.median(annual_delta)) >= 0),
            "pooled_candidate_p05_not_below_comparator": bool(pooled["p05_delta"] is not None and float(pooled["p05_delta"]) >= 0),
            "annual_candidate_p05_not_below_comparator_count": p05_not_worse_count,
            "minimum_annual_candidate_p05_not_below_comparator_count_pass": bool(p05_not_worse_count >= int(protocol["progression_gates_each_clock"]["minimum_annual_candidate_p05_not_below_comparator_count"])),
        }
        clock_pass = bool(all(gates[k] for k in [
            "all_annual_sufficiency_pass",
            "pooled_mean_utility_delta_positive",
            "minimum_positive_annual_mean_utility_delta_count_pass",
            "median_annual_mean_utility_delta_nonnegative",
            "pooled_candidate_p05_not_below_comparator",
            "minimum_annual_candidate_p05_not_below_comparator_count_pass",
        ]))
        gates["clock_progression_pass"] = clock_pass
        all_clock_pass &= clock_pass
        diagnostics[clock] = {"pooled": pooled, "by_year": annual}
        clock_gates[clock] = gates

    any_insufficient = any(not clock_gates[clock]["all_annual_sufficiency_pass"] for clock in CLOCKS)
    decision = (
        "E3_DEV_INSUFFICIENT" if any_insufficient else
        "E3_DEV_PROGRESS_RETROSPECTIVE_INTRADAY_PORTFOLIO_RISK_UTILITY_CANDIDATE" if all_clock_pass else
        "E3_DEV_NO_PROGRESS"
    )

    incomplete = account_days.loc[~account_days["complete"]]
    incomplete_counts = {str(k): int(v) for k, v in incomplete["incomplete_reason"].value_counts(dropna=False).to_dict().items()}
    payload = {
        "schema_id": "overnight_downstream_portfolio_risk_adapter_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-E3_portfolio_risk_adapter",
        "phase": "retrospective_intraday_portfolio_utility_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "candidate": "exposure_zero_if_C1_action_negative_else_one",
        "comparator": "always_exposed_one",
        "target": "frozen_consumer_portfolio_QFQ_signal_return_09:35_to_09:50",
        "diagnostics": diagnostics,
        "progression_gate_components": clock_gates,
        "joint_clock_progression_pass": bool(all_clock_pass),
        "decision": decision,
        "maximum_authority_if_pass": "retrospective_E3_intraday_portfolio_risk_utility_candidate_only",
        "source_integrity": integrity,
        "reconstruction_diagnostics": {
            "account_day_rows": int(len(account_days)),
            "complete_account_day_rows": int(account_days["complete"].sum()),
            "incomplete_account_day_rows": int((~account_days["complete"]).sum()),
            "incomplete_reason_counts": incomplete_counts,
        },
        "candidate_attempt_count": 1,
        "threshold_search": False,
        "magnitude_bucket_search": False,
        "alternate_horizon_search": False,
        "consumer_clock_selection": False,
        "additional_upstream_search": False,
        "account_execution_opened": False,
        "transaction_cost_model_used": False,
        "strategy_mutation_opened": False,
        "2021_2025_rows_opened": False,
        "reusable_blackbox_query_created": False,
        "production_authority": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("E3_PORTFOLIO_RISK_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
