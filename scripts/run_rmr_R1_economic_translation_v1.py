#!/usr/bin/env python3
"""R1 economic translation v1 on reusable DEV / VALIDATION.

Reads only 2015-2025. Probability models are fit on DEV 2015-2020 and used
unchanged on detailed VALIDATION 2021-2025. If validation passes, one final
DEV+VALIDATION refit is frozen for a later low-bandwidth blackbox query.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common
import run_rmr_R1_parent_integrity_v2_selection as model_utils

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_economic_translation_v1_protocol.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R1_economic_translation_v1_validation_receipt.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R1_economic_translation_v1_parameter_freeze.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
HORIZON = 1200
ROUND_TRIP_COST = 0.0010
PAIRINGS = (("PAIR_A", "S1", "S2"), ("PAIR_B", "S2", "S3"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None


def validate_protocol() -> dict:
    p = load_json(PROTOCOL)
    if p["research_identity"] != "rmr_R1_parent_integrity_economic_translation_v1":
        raise RuntimeError("economic identity drifted")
    s = p["strategy_candidate"]
    if s["id"] != "R1_EDGE_POSITIVE_NEXT_BAR_10BP":
        raise RuntimeError("strategy candidate drifted")
    if s["filter"] != "p_parent_integrity_augmented_strictly_greater_than_p_severity_only":
        raise RuntimeError("economic filter drifted")
    if p["cost_model"]["primary_round_trip_bps"] != 10.0:
        raise RuntimeError("cost model drifted")
    if p["model"]["VALIDATION_model_fit"] != "DEV_only_2015_2020":
        raise RuntimeError("validation fit rule drifted")
    return p


def read_source(path: Path) -> pd.DataFrame:
    if sha256(path) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("historical source SHA mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("historical source validation boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("economic DEV/VALIDATION runner read blackbox")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def trade_events(
    prices: np.ndarray,
    days: np.ndarray,
    lower_waves: list[common.Wave],
    parent_waves: list[common.Wave],
    vol_ref: float,
) -> pd.DataFrame:
    parent_confirms = [w.confirm_idx for w in parent_waves]
    rows: list[dict] = []
    next_allowed = -1
    for lower in lower_waves:
        if lower.confirm_idx <= next_allowed:
            continue
        k = bisect_right(parent_confirms, lower.confirm_idx)
        if k < 2:
            continue
        w1, w2 = parent_waves[k - 2], parent_waves[k - 1]
        pf = common.parent_features(w1, w2, prices)
        if not pf or not np.isfinite(list(pf.values())).all():
            continue
        parent_sign = 1 if pf["signed_drift"] > 0 else -1 if pf["signed_drift"] < 0 else 0
        if parent_sign == 0 or lower.direction == parent_sign:
            continue
        recovery = float(lower.start_price)
        failure = float(common.structural_boundary(w1, w2, parent_sign))
        confirm_price = float(prices[lower.confirm_idx])
        if parent_sign > 0 and not (failure < confirm_price < recovery):
            continue
        if parent_sign < 0 and not (recovery < confirm_price < failure):
            continue

        entry_idx = lower.confirm_idx + 1
        if entry_idx >= len(prices):
            continue
        entry_price = float(prices[entry_idx])
        if parent_sign > 0 and not (failure < entry_price < recovery):
            continue
        if parent_sign < 0 and not (recovery < entry_price < failure):
            continue

        end = min(len(prices) - 1, lower.confirm_idx + HORIZON)
        outcome = "censored"
        exit_idx = end
        for j in range(entry_idx + 1, end + 1):
            x = float(prices[j])
            if parent_sign > 0:
                if x >= recovery:
                    outcome, exit_idx = "recovery", j
                    break
                if x <= failure:
                    outcome, exit_idx = "failure", j
                    break
            else:
                if x <= recovery:
                    outcome, exit_idx = "recovery", j
                    break
                if x >= failure:
                    outcome, exit_idx = "failure", j
                    break
        exit_price = float(prices[exit_idx])
        gross = parent_sign * (exit_price / entry_price - 1.0)
        net = gross - ROUND_TRIP_COST
        rows.append({
            "day": str(days[lower.confirm_idx]),
            "confirm_idx": int(lower.confirm_idx),
            "entry_idx": int(entry_idx),
            "exit_idx": int(exit_idx),
            "holding_bars": int(exit_idx - entry_idx),
            "parent_sign": int(parent_sign),
            "severity": float(abs(lower.move) / vol_ref),
            "abs_drift": float(pf["abs_drift"]),
            "overlap": float(pf["overlap"]),
            "parent_eff": float(pf["parent_eff"]),
            "outcome": outcome,
            "gross_return": float(gross),
            "net_return": float(net),
        })
        next_allowed = exit_idx
    return pd.DataFrame(rows)


def fit_probability_bundle(events: pd.DataFrame, end_day: str) -> dict:
    resolved = events.loc[events["outcome"].isin(["recovery", "failure"]) & (events["day"] <= end_day)].copy()
    resolved["y"] = resolved["outcome"].eq("recovery").astype(int)
    parent_sc = model_utils.fit_parent_scaler(resolved)
    resolved_c = model_utils.add_composite(resolved, parent_sc)
    baseline = model_utils.fit_probability(resolved, ["severity"])
    candidate = model_utils.fit_probability(resolved_c, ["severity", "parent_integrity"])
    return {
        "parent_scaler_object": parent_sc,
        "baseline_object": baseline,
        "candidate_object": candidate,
        "snapshot": {
            "n_resolved_fit": int(len(resolved)),
            "parent_feature_scaler": model_utils.parent_scaler_snapshot(parent_sc),
            "severity_baseline_model": model_utils.model_snapshot(baseline, ["severity"]),
            "selected_candidate_model": model_utils.model_snapshot(candidate, ["severity", "parent_integrity"]),
        },
    }


def add_edge(events: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    out = model_utils.add_composite(events, bundle["parent_scaler_object"])
    p_base = bundle["baseline_object"].predict_proba(out[["severity"]].to_numpy(float))[:, 1]
    p_cand = bundle["candidate_object"].predict_proba(out[["severity", "parent_integrity"]].to_numpy(float))[:, 1]
    out["model_edge"] = p_cand - p_base
    out["selected_trade"] = out["model_edge"] > 0.0
    return out


def stats(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"n": 0, "mean_net_return": None, "median_net_return": None, "win_rate": None, "mean_holding_bars": None}
    return {
        "n": int(len(frame)),
        "mean_net_return": float(frame["net_return"].mean()),
        "median_net_return": float(frame["net_return"].median()),
        "win_rate": float((frame["net_return"] > 0).mean()),
        "mean_holding_bars": float(frame["holding_bars"].mean()),
    }


def validation_pair(events: pd.DataFrame, dev_bundle: dict, pair_id: str, protocol: dict) -> dict:
    scored = add_edge(events, dev_bundle)
    val = scored.loc[scored["day"].between(VAL_START, VAL_END)].copy()
    all_stats = stats(val)
    selected = val.loc[val["selected_trade"]].copy()
    sel_stats = stats(selected)
    annual = {}
    positive_years = 0
    for year in range(2021, 2026):
        yf = selected.loc[selected["day"].str.startswith(str(year))]
        ys = stats(yf)
        if ys["mean_net_return"] is not None and ys["mean_net_return"] > 0:
            positive_years += 1
        annual[str(year)] = ys
    min_n = int(protocol["VALIDATION"]["gate_each_pairing"]["minimum_filtered_trades"][pair_id])
    gates = {
        "minimum_filtered_trades": int(sel_stats["n"]) >= min_n,
        "candidate_mean_net_return_gt_0": sel_stats["mean_net_return"] is not None and sel_stats["mean_net_return"] > 0,
        "candidate_mean_net_return_gt_all_event_baseline": (
            sel_stats["mean_net_return"] is not None
            and all_stats["mean_net_return"] is not None
            and sel_stats["mean_net_return"] > all_stats["mean_net_return"]
        ),
        "annual_positive_mean_net_return_ge_4_of_5": positive_years >= 4,
    }
    return {
        "all_event_baseline": all_stats,
        "candidate": sel_stats,
        "annual_candidate": annual,
        "gates": gates,
        "passed": bool(all(gates.values())),
    }


def final_freeze(pair_events: dict[str, pd.DataFrame], protocol: dict) -> dict:
    payload = {
        "schema_id": "factorlab_rmr_R1_economic_translation_v1_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R1_parent_integrity_economic_translation_v1",
        "parent_mechanism_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "strategy_candidate_id": "R1_EDGE_POSITIVE_NEXT_BAR_10BP",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": "2015-01-05", "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "DEV_median_rvol20": float(protocol["model"]["DEV_median_rvol20"]),
        "directional_change_thresholds": protocol["model"]["directional_change_thresholds"],
        "round_trip_cost_bps": 10.0,
        "filter": "p_parent_integrity_augmented_strictly_greater_than_p_severity_only",
        "entry": "next_observed_1m_close_after_R1_event_confirmation",
        "pairings": {},
        "blackbox_gate": protocol["BLACKBOX"]["gate_each_pairing"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    for pair_id, events in pair_events.items():
        bundle = fit_probability_bundle(events, VAL_END)
        payload["pairings"][pair_id] = bundle["snapshot"]
    check = dict(payload)
    payload["parameter_bundle_sha256"] = json_digest(check)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    args = ap.parse_args()

    protocol = validate_protocol()
    frame = read_source(args.source.resolve())
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = {k: float(v) for k, v in protocol["model"]["directional_change_thresholds"].items()}
    vol_ref = float(protocol["model"]["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, thresholds[name]) for name in ("S1", "S2", "S3")}

    pair_events: dict[str, pd.DataFrame] = {}
    validation = {}
    dev_model_snapshots = {}
    for pair_id, lower, parent in PAIRINGS:
        events = trade_events(prices, days, waves[lower], waves[parent], vol_ref)
        pair_events[pair_id] = events
        dev_bundle = fit_probability_bundle(events, DEV_END)
        dev_model_snapshots[pair_id] = dev_bundle["snapshot"]
        validation[pair_id] = validation_pair(events, dev_bundle, pair_id, protocol)

    passed = bool(all(v["passed"] for v in validation.values()))
    receipt = {
        "schema_id": "factorlab_rmr_R1_economic_translation_v1_validation_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R1_parent_integrity_economic_translation_v1",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "DEV_window": {"start": "2015-01-05", "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_opened": False,
        "round_trip_cost_bps": 10.0,
        "validation": validation,
        "DEV_model_snapshots": dev_model_snapshots,
        "validation_passed": passed,
        "final_refit_performed": passed,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not passed:
        print("R1_ECONOMIC_TRANSLATION_VALIDATION_FAIL")
        return 2
    freeze = final_freeze(pair_events, protocol)
    dump_json(args.freeze.resolve(), freeze)
    print("R1_ECONOMIC_TRANSLATION_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
