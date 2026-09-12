#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_b2_stock_selection_offshore_risk_abstention_adapter_v1"
YEARS = tuple(range(2015, 2021))
CLOCKS = ("14:30", "14:45")
PROTOCOL = ROOT / "docs/governance/downstream_b2_stock_selection_offshore_risk_adapter_v1_protocol.json"
STATE = ROOT / "docs/governance/downstream_b2_stock_selection_offshore_risk_adapter_v1_state.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
DRIVER_ROOT = ROOT / "data/driver_runtime_text_2015_2020"
RECEIPT = ROOT / "docs/research/cloud_downstream_b2_stock_selection_offshore_risk_adapter_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def trailing_rms_prev(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def verify_contracts() -> tuple[dict, dict]:
    p, s, ledger = read_json(PROTOCOL), read_json(STATE), read_json(LEDGER)
    if p.get("research_identity") != IDENTITY or s.get("research_identity") != IDENTITY or s.get("outcome_opened") is not False:
        raise RuntimeError("E2v3 result-free identity/state drift")
    if p.get("development_window") != "2015-01-05..2020-12-31" or p.get("annual_report_slices") != list(YEARS):
        raise RuntimeError("E2v3 development boundary drift")
    if tuple(p.get("consumer_variants", [])) != CLOCKS:
        raise RuntimeError("E2v3 consumer clock drift")
    if p.get("adapter", {}).get("candidate_attempt_count") != 1 or p.get("adapter", {}).get("semantic_boundary") != 0.0:
        raise RuntimeError("E2v3 candidate drift")
    q9 = next((q for q in ledger.get("queries", []) if int(q.get("ordinal", -1)) == 9), None)
    if not q9 or q9.get("research_identity") != "overnight_china_offshore_open_gap_v1" or q9.get("decision") != "PASS" or q9.get("query_id") != "608e037b0d24724b097b":
        raise RuntimeError("validated B2 authority missing")
    return p, ledger


def github_meta(repo: str, path: str, ref: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "factorlab-overnight-open-lab"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def load_consumer(p: dict) -> tuple[pd.DataFrame, dict]:
    c = p["consumer"]
    meta = github_meta(c["repository"], c["selection_decision_carrier"], c["source_commit"])
    if meta.get("sha") != c["selection_decision_carrier_blob_sha"]:
        raise RuntimeError("consumer carrier blob drift")
    req = urllib.request.Request(meta["download_url"], headers={"User-Agent": "factorlab-overnight-open-lab"})
    rows, sentinel = [], False
    with urllib.request.urlopen(req, timeout=30) as resp:
        reader = csv.DictReader(io.TextIOWrapper(resp, encoding="utf-8", newline=""))
        need = {"decision_id", "decision_date", "year", "decision_clock", "selected_mean_h20_return", "oracle_mean_h20_return", "selection_gap_mean_h20_return"}
        if reader.fieldnames is None or need.difference(reader.fieldnames):
            raise RuntimeError("consumer schema drift")
        for row in reader:
            y = int(row["year"])
            if y < 2015:
                continue
            if y > 2020:
                sentinel = True
                break
            rows.append(row)
    if not sentinel:
        raise RuntimeError("consumer post-2020 stop sentinel absent")
    f = pd.DataFrame(rows)
    f["decision_date"] = pd.to_datetime(f["decision_date"], errors="raise").dt.normalize()
    f["year"] = pd.to_numeric(f["year"], errors="raise").astype(int)
    if f.empty or not f["year"].between(2015, 2020).all() or f["decision_id"].duplicated().any():
        raise RuntimeError("consumer development inventory drift")
    for col in ["selected_mean_h20_return", "oracle_mean_h20_return", "selection_gap_mean_h20_return"]:
        f[col] = pd.to_numeric(f[col], errors="coerce")
    return f, {"repository": c["repository"], "source_commit": c["source_commit"], "path": c["selection_decision_carrier"], "blob_sha": meta["sha"], "post2020_scientific_rows_parsed": False}


def load_b2() -> tuple[pd.DataFrame, dict]:
    manifest = read_json(DRIVER_ROOT / "manifest.json")
    if manifest.get("published_window") != "2015-01-05..2020-12-31" or manifest.get("withheld_years") != [2021, 2022, 2023, 2024, 2025]:
        raise RuntimeError("driver carrier boundary drift")
    expected = manifest.get("outputs", {})
    pieces, hashes = [], {}
    for y in YEARS:
        path = DRIVER_ROOT / f"driver_external_{y}.csv"
        if sha256(path) != expected[str(y)]["sha256"]:
            raise RuntimeError(f"driver shard digest drift {y}")
        f = pd.read_csv(path)
        if {"trading_day", "a50_channel_return"}.difference(f.columns):
            raise RuntimeError(f"driver shard {y} missing B2 input")
        f["trading_day"] = pd.to_datetime(f["trading_day"], errors="raise").dt.normalize()
        if not f["trading_day"].dt.year.eq(y).all() or f["trading_day"].duplicated().any():
            raise RuntimeError(f"driver shard inventory drift {y}")
        pieces.append(f[["trading_day", "a50_channel_return"]].copy())
        hashes[str(y)] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    x = pd.concat(pieces, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    x["a50_channel_return"] = pd.to_numeric(x["a50_channel_return"], errors="coerce")
    x["a50_rms60_prev"] = trailing_rms_prev(x["a50_channel_return"])
    x["china_offshore_z"] = x["a50_channel_return"] / x["a50_rms60_prev"]
    return x[["trading_day", "china_offshore_z"]], {"driver_manifest_sha256": sha256(DRIVER_ROOT / "manifest.json"), "driver_shards": hashes}


def diagnose(part: pd.DataFrame, min_complete: int, min_active: int) -> dict:
    cols = ["china_offshore_z", "selected_mean_h20_return", "selection_gap_mean_h20_return"]
    x = part[["decision_id", "decision_date", *cols]].copy()
    numeric = x[cols].apply(pd.to_numeric, errors="coerce")
    x = x.loc[np.isfinite(numeric.to_numpy(float)).all(axis=1)].copy()
    n = int(len(x)); active = x["china_offshore_z"].ge(0); an = int(active.sum())
    cr = float(x["selected_mean_h20_return"].mean()) if n else None
    ar = float(x.loc[active, "selected_mean_h20_return"].mean()) if an else None
    cg = float(x["selection_gap_mean_h20_return"].mean()) if n else None
    ag = float(x.loc[active, "selection_gap_mean_h20_return"].mean()) if an else None
    return {
        "complete_decision_count": n, "active_decision_count": an, "active_coverage": float(an/n) if n else None,
        "comparator_mean_selected_h20_return": cr, "candidate_mean_selected_h20_return": ar,
        "delta_selected_h20_return": None if ar is None or cr is None else float(ar-cr),
        "comparator_mean_selection_gap": cg, "candidate_mean_selection_gap": ag,
        "delta_selection_gap": None if ag is None or cg is None else float(ag-cg),
        "sufficiency_complete_pass": n >= min_complete, "sufficiency_active_pass": an >= min_active,
        "sufficiency_pass": n >= min_complete and an >= min_active,
    }


def main() -> None:
    if RECEIPT.exists(): raise RuntimeError("refusing to overwrite E2v3 receipt")
    p, ledger = verify_contracts()
    consumer, ci = load_consumer(p); b2, bi = load_b2()
    frame = consumer.merge(b2.rename(columns={"trading_day":"decision_date"}), on="decision_date", how="left", validate="many_to_one")
    min_c = int(p["sufficiency_gates"]["minimum_complete_decisions_each_clock_year"]); min_a = int(p["sufficiency_gates"]["minimum_active_decisions_each_clock_year"])
    tol = float(p["selection_quality_safeguard"]["maximum_allowed_annual_worsening"]); ptol = float(p["selection_quality_safeguard"]["maximum_allowed_pooled_worsening"])
    min_pos = int(p["progression_gates_each_clock"]["minimum_positive_annual_selected_return_delta_count"]); min_gap = int(p["progression_gates_each_clock"]["minimum_annual_selection_gap_delta_not_worse_than_minus_0_002_count"])
    diagnostics, passes = {}, {}
    for clock in CLOCKS:
        c = frame.loc[frame["decision_clock"].eq(clock)].copy()
        by = {str(y): diagnose(c.loc[c["year"].eq(y)], min_c, min_a) for y in YEARS}; pooled = diagnose(c, min_c*6, min_a*6)
        ur = [by[str(y)]["delta_selected_h20_return"] for y in YEARS]; gd = [by[str(y)]["delta_selection_gap"] for y in YEARS]
        suff = all(by[str(y)]["sufficiency_pass"] for y in YEARS); pos = sum(v is not None and v>0 for v in ur); med = float(np.median([float(v) for v in ur if v is not None])); gok = sum(v is not None and v>=-tol for v in gd)
        gates = {
            "all_annual_sufficiency_pass": suff,
            "pooled_selected_return_delta_positive": pooled["delta_selected_h20_return"] is not None and pooled["delta_selected_h20_return"]>0,
            "positive_annual_selected_return_delta_count": pos,
            "minimum_positive_annual_selected_return_delta_count_pass": pos>=min_pos,
            "median_annual_selected_return_delta": med,
            "median_annual_selected_return_delta_nonnegative": med>=0,
            "pooled_selection_gap_delta_not_worse_than_tolerance": pooled["delta_selection_gap"] is not None and pooled["delta_selection_gap"]>=-ptol,
            "annual_selection_gap_delta_not_worse_than_tolerance_count": gok,
            "minimum_annual_selection_gap_count_pass": gok>=min_gap,
        }
        passed = all([gates["all_annual_sufficiency_pass"],gates["pooled_selected_return_delta_positive"],gates["minimum_positive_annual_selected_return_delta_count_pass"],gates["median_annual_selected_return_delta_nonnegative"],gates["pooled_selection_gap_delta_not_worse_than_tolerance"],gates["minimum_annual_selection_gap_count_pass"]])
        diagnostics[clock] = {"pooled":pooled,"by_year":by,"gates":gates,"progression_pass":passed}; passes[clock]=passed
    all_suff = all(diagnostics[c]["gates"]["all_annual_sufficiency_pass"] for c in CLOCKS); joint=all(passes.values())
    decision = "E2V3_DEV_INSUFFICIENT" if not all_suff else ("E2V3_DEV_PROGRESS_RETROSPECTIVE_SELECTION_QUALITY_ADAPTER_CANDIDATE" if joint else "E2V3_DEV_NO_PROGRESS")
    payload = {
        "schema_id":"overnight_downstream_b2_stock_selection_offshore_risk_adapter_dev_diagnostic@1.0","session_date":"2026-09-12","research_identity":IDENTITY,"product_family":"OFP-E2_stock_selection_adapter","phase":"retrospective_selection_quality_diagnostic","development_window":"2015-01-05..2020-12-31",
        "protocol":{"path":str(PROTOCOL.relative_to(ROOT)),"sha256":sha256(PROTOCOL)},"state_at_execution":{"path":str(STATE.relative_to(ROOT)),"sha256":sha256(STATE)},"consumer":p["consumer"],"adapter_rule":"active iff china_offshore_z >= 0","diagnostics":diagnostics,"joint_clock_progression_pass":joint,"decision":decision,"maximum_authority_if_progressed":"retrospective_E2_selection_quality_adapter_candidate_only","source_integrity":{"consumer":ci,"B2":bi},"validated_B2_query_id":"608e037b0d24724b097b","ledger_query_count_at_execution":int(ledger.get("query_count",-1)),
        "candidate_attempt_count":1,"ranking_mutation":False,"topn_mutation":False,"threshold_search":False,"magnitude_bucket_search":False,"ordinary_holiday_split_search":False,"clock_selection":False,"upstream_add_drop_search":False,"account_PnL_backtest_opened":False,"2021_2025_scientific_rows_opened":False,"blackbox_query_created":False,"production_authority":False
    }
    RECEIPT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("E2V3_B2_STOCK_SELECTION_OFFSHORE_RISK_ADAPTER_DEV_COMPLETE"); print(decision)

if __name__ == "__main__": main()
