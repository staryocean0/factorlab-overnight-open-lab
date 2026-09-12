#!/usr/bin/env python3
"""Compact reusable BLACKBOX controller for frozen OFP-B1 global risk.

Internally reads governed 2021-2025 rows but persists and prints only the compact
PASS / FAIL / INSUFFICIENT decision and non-outcome provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

IDENTITY = "overnight_global_risk_open_gap_v1"
BB_START = pd.Timestamp("2021-01-01")
BB_END = pd.Timestamp("2025-12-31")
TARGET = "opening_gap_rvol"
CANDIDATE = "global_risk_z"
BASELINE = [
    "r1", "r20", "abs_r1", "prev_gap", "overnight_trend_5",
    "prev_daytime", "prev_last_hour", "prev_afternoon", "log_rvol20",
    "weekend", "holiday_reopen",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def trailing_rms_prev(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    d = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(d, y, rcond=None)
    return y - d @ coef


def partial_corr(frame: pd.DataFrame) -> float:
    xb = frame[BASELINE].to_numpy(float)
    cr = residualize(frame[CANDIDATE].to_numpy(float), xb)
    yr = residualize(frame[TARGET].to_numpy(float), xb)
    if np.std(cr) == 0 or np.std(yr) == 0:
        raise RuntimeError("degenerate B1 partial correlation")
    value = float(np.corrcoef(cr, yr)[0, 1])
    if not np.isfinite(value):
        raise RuntimeError("non-finite B1 partial correlation")
    return value


def standardized_candidate_coefficient(frame: pd.DataFrame) -> float:
    cols = [*BASELINE, CANDIDATE, TARGET]
    z = frame[cols].astype(float).copy()
    for col in cols:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            raise RuntimeError("degenerate B1 regression column")
        z[col] = (z[col] - float(z[col].mean())) / sd
    d = np.column_stack([np.ones(len(z)), z[[*BASELINE, CANDIDATE]].to_numpy(float)])
    coef, *_ = np.linalg.lstsq(d, z[TARGET].to_numpy(float), rcond=None)
    return float(coef[-1])


def moving_block_positive_support(frame: pd.DataFrame, block_length: int, resamples: int, seed: int) -> float:
    n = len(frame)
    if n < block_length:
        raise RuntimeError("B1 BLACKBOX sample shorter than bootstrap block")
    rng = np.random.default_rng(seed)
    starts = np.arange(0, n - block_length + 1)
    positive = 0
    valid = 0
    for _ in range(resamples):
        parts: list[np.ndarray] = []
        length = 0
        while length < n:
            start = int(rng.choice(starts))
            block = np.arange(start, start + block_length)
            parts.append(block)
            length += len(block)
        idx = np.concatenate(parts)[:n]
        try:
            coef = standardized_candidate_coefficient(frame.iloc[idx])
        except RuntimeError:
            continue
        valid += 1
        positive += int(coef > 0)
    if valid != resamples:
        raise RuntimeError("invalid B1 bootstrap resample")
    return positive / valid


def build_coordinates(panel: pd.DataFrame) -> pd.DataFrame:
    x = panel.sort_values("trading_day", kind="mergesort").reset_index(drop=True).copy()
    x["rvol20"] = pd.to_numeric(x["rvol20"], errors="coerce")
    for raw in ["us_nasdaq", "us_vix_chg"]:
        x[raw] = pd.to_numeric(x[raw], errors="coerce")
        x[f"{raw}_rms60_prev"] = trailing_rms_prev(x[raw])
    x["nasdaq_risk_z"] = x["us_nasdaq"] / x["us_nasdaq_rms60_prev"]
    x["vix_risk_z"] = -x["us_vix_chg"] / x["us_vix_chg_rms60_prev"]
    x[CANDIDATE] = 0.5 * (x["nasdaq_risk_z"] + x["vix_risk_z"])
    x["log_rvol20"] = np.where(x["rvol20"].gt(0), np.log(x["rvol20"]), np.nan)
    x[TARGET] = pd.to_numeric(x["gap"], errors="coerce") / x["rvol20"]
    return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--source-manifest", type=Path, required=True)
    ap.add_argument("--reconstruction-contract", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("wrong B1 BLACKBOX identity")
    if protocol.get("candidate") != CANDIDATE or protocol.get("target") != TARGET:
        raise RuntimeError("B1 BLACKBOX candidate/target drift")
    if protocol.get("baseline_controls") != BASELINE:
        raise RuntimeError("B1 BLACKBOX baseline drift")
    norm = protocol.get("normalization", {})
    if norm != {"method": "lagged_trailing_RMS", "window": 60, "min_periods": 20, "shift": 1, "current_observation_excluded": True}:
        raise RuntimeError("B1 BLACKBOX normalization drift")
    if protocol.get("public_output_enum") != ["PASS", "FAIL", "INSUFFICIENT"]:
        raise RuntimeError("B1 public output contract drift")

    panel = pd.read_parquet(args.panel).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    needed = {"trading_day", "gap", "r1", "r20", "abs_r1", "prev_gap", "overnight_trend_5", "prev_daytime", "prev_last_hour", "prev_afternoon", "rvol20", "weekend", "holiday_reopen", "us_nasdaq", "us_vix_chg"}
    if needed.difference(panel.columns):
        raise RuntimeError("B1 reconstructed panel missing frozen inputs")
    x = build_coordinates(panel)
    cols = [*BASELINE, CANDIDATE, TARGET]
    x[cols] = x[cols].apply(pd.to_numeric, errors="coerce")
    complete = x[cols].notna().all(axis=1) & np.isfinite(x[cols].to_numpy(float)).all(axis=1) & x["rvol20"].gt(0)
    bb = x.loc[x["trading_day"].between(BB_START, BB_END) & complete].copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    bb["year"] = bb["trading_day"].dt.year.astype(int)

    suff = protocol["internal_sufficiency_gates"]
    years = list(range(2021, 2026))
    sufficient = len(bb) >= int(suff["pooled_complete_cases_min"]) and all(int(bb["year"].eq(y).sum()) >= int(suff["each_calendar_year_complete_cases_min"]) for y in years)
    if not sufficient:
        decision = "INSUFFICIENT"
    else:
        pooled_pcorr = partial_corr(bb)
        pooled_coef = standardized_candidate_coefficient(bb)
        annual_coefs = [standardized_candidate_coefficient(bb.loc[bb["year"].eq(y)]) for y in years]
        pos_count = int(sum(v > 0 for v in annual_coefs))
        median_coef = float(np.median(annual_coefs))
        boot = protocol["internal_scientific_gates"]["moving_block_bootstrap"]
        support = moving_block_positive_support(bb, int(boot["block_length_trading_days"]), int(boot["resamples"]), int(boot["seed"]))
        gates = [
            pooled_pcorr > 0,
            pooled_coef > 0,
            pos_count >= int(protocol["internal_scientific_gates"]["positive_calendar_year_coefficient_count_min"]),
            median_coef > 0,
            support >= float(boot["positive_coefficient_support_min"]),
        ]
        decision = "PASS" if all(gates) else "FAIL"

    protocol_sha = sha256(args.protocol)
    source_sha = sha256(args.source_manifest)
    recon_sha = sha256(args.reconstruction_contract)
    query_payload = "|".join([IDENTITY, protocol_sha, source_sha, recon_sha])
    query_id = hashlib.sha256(query_payload.encode("utf-8")).hexdigest()[:20]
    receipt = {
        "schema_id": "overnight_global_risk_open_gap_blackbox_receipt@1.0",
        "query_id": query_id,
        "research_identity": IDENTITY,
        "parent_development_identity": "overnight_global_risk_driver_v1",
        "comparator": "same_domestic_baseline_without_global_risk_z",
        "decision": decision,
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "yearly_results_persisted": False,
        "counts_persisted": False,
        "bootstrap_results_persisted": False,
        "failure_attribution_persisted": False,
        "protocol_sha256": protocol_sha,
        "source_manifest_sha256": source_sha,
        "reconstruction_contract_sha256": recon_sha,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "reuse_is_independent_oos": False,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
