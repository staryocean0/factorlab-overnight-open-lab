#!/usr/bin/env python3
"""Single-candidate R2 economic translation on reusable DEV / VALIDATION.

Reads only through 2025-12-31. The R2 probability mechanism is fit on resolved
DEV events. Trading enters at the next observed minute and uses the original
range edge / continuation boundary with fixed 10bp round-trip cost.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common
import run_rmr_R2_range_integrity_v2 as mech

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R2_economic_translation_v1_protocol.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R2_economic_translation_v1_validation_receipt.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R2_economic_translation_v1_parameter_freeze.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
HORIZON = 1200
ROUND_TRIP_COST = 0.0010
THRESHOLDS = dict(mech.THRESHOLDS)
PAIRINGS = tuple(mech.PAIRINGS)


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
    if p["research_identity"] != "rmr_R2_range_reentry_economic_translation_v1":
        raise RuntimeError("R2 economic identity drifted")
    s = p["strategy_candidate"]
    if s["id"] != "R2_STRUCTURAL_EXPECTANCY_POSITIVE_NEXT_BAR_10BP":
        raise RuntimeError("R2 economic candidate drifted")
    if s["filter_1"] != "p_range_integrity_augmented_strictly_greater_than_p_geometry_baseline":
        raise RuntimeError("R2 probability-edge filter drifted")
    if s["filter_2"] != "candidate_structural_expected_net_return_strictly_greater_than_zero":
        raise RuntimeError("R2 expectancy filter drifted")
    if p["cost_model"]["primary_round_trip_bps"] != 10.0:
        raise RuntimeError("R2 economic cost drifted")
    return p


def read_source(path: Path) -> pd.DataFrame:
    if sha256(path) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("R2 economic historical source SHA mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("R2 economic detailed source boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("R2 economic DEV/VALIDATION runner read BLACKBOX")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("R2 economic invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def trade_events(
    prices: np.ndarray,
    days: np.ndarray,
    parent_waves: list[common.Wave],
    lower_threshold: float,
    parent_threshold: float,
) -> pd.DataFrame:
    rows: list[dict] = []
    next_allowed = -1
    wave_cursor = 0
    last2: list[common.Wave] = []
    for i, x in enumerate(prices):
        while wave_cursor < len(parent_waves) and parent_waves[wave_cursor].confirm_idx <= i:
            last2.append(parent_waves[wave_cursor])
            last2 = last2[-2:]
            wave_cursor += 1
        if i <= next_allowed or len(last2) < 2:
            continue
        pf = common.parent_features(last2[0], last2[1], prices)
        if not pf or not np.isfinite(list(pf.values())).all():
            continue
        points = [last2[0].start_price, last2[0].end_price, last2[1].start_price, last2[1].end_price]
        low, high = min(points), max(points)
        width = high - low
        if width <= 0.0:
            continue
        if x >= high * (1.0 + lower_threshold):
            side, edge = 1, float(high)
        elif x <= low * (1.0 - lower_threshold):
            side, edge = -1, float(low)
        else:
            continue
        continuation = edge * (1.0 + parent_threshold) if side > 0 else edge * (1.0 - parent_threshold)
        if (side > 0 and x >= continuation) or (side < 0 and x <= continuation):
            continue

        end = min(len(prices) - 1, i + HORIZON)
        original_resolve = end
        for j in range(i, end + 1):
            z = float(prices[j])
            if side > 0:
                if z <= edge or z >= continuation:
                    original_resolve = j
                    break
            else:
                if z >= edge or z <= continuation:
                    original_resolve = j
                    break
        next_allowed = original_resolve

        speed, vol_ratio = common.local_vol_features(prices, i)
        outside_ratio = abs(float(x) - edge) / edge / (width / edge)
        if not np.isfinite([outside_ratio, speed, vol_ratio]).all():
            continue

        entry_idx = i + 1
        if entry_idx > end or entry_idx >= len(prices):
            continue
        entry = float(prices[entry_idx])
        if side > 0 and not (edge < entry < continuation):
            continue
        if side < 0 and not (continuation < entry < edge):
            continue

        trade_direction = -side
        outcome = "censored"
        exit_idx = end
        for j in range(entry_idx + 1, end + 1):
            z = float(prices[j])
            if side > 0:
                if z <= edge:
                    outcome, exit_idx = "reentry", j
                    break
                if z >= continuation:
                    outcome, exit_idx = "continuation", j
                    break
            else:
                if z >= edge:
                    outcome, exit_idx = "reentry", j
                    break
                if z <= continuation:
                    outcome, exit_idx = "continuation", j
                    break

        exit_price = float(prices[exit_idx])
        gross = trade_direction * (exit_price / entry - 1.0)
        net = gross - ROUND_TRIP_COST
        reward_gross = trade_direction * (edge / entry - 1.0)
        loss_gross = trade_direction * (continuation / entry - 1.0)
        if not (reward_gross > 0.0 and loss_gross < 0.0):
            raise RuntimeError("R2 economic structural reward/loss orientation drifted")
        rows.append({
            "day": str(days[i]),
            "event_idx": int(i),
            "entry_idx": int(entry_idx),
            "exit_idx": int(exit_idx),
            "holding_bars": int(exit_idx - entry_idx),
            "side": int(side),
            "trade_direction": int(trade_direction),
            "edge": float(edge),
            "continuation": float(continuation),
            "entry_price": float(entry),
            "outside_ratio": float(outside_ratio),
            "break_speed": float(speed / lower_threshold),
            "local_vol_ratio": float(vol_ratio),
            "abs_drift": float(pf["abs_drift"]),
            "overlap": float(pf["overlap"]),
            "parent_eff": float(pf["parent_eff"]),
            "outcome": outcome,
            "reward_gross": float(reward_gross),
            "loss_gross": float(loss_gross),
            "gross_return": float(gross),
            "net_return": float(net),
        })
    return pd.DataFrame(rows)


def fit_probability_bundle(mechanism_data: pd.DataFrame, end_day: str) -> dict:
    fit = mechanism_data.loc[mechanism_data["day"] <= end_day].copy()
    parent_sc = mech.fit_parent_scaler(fit)
    fit_c = mech.add_range_integrity(fit, parent_sc)
    baseline = mech.fit_logit(fit, mech.BASELINE_FEATURES)
    candidate = mech.fit_logit(fit_c, mech.CANDIDATE_FEATURES)
    return {
        "parent_scaler_object": parent_sc,
        "baseline_object": baseline,
        "candidate_object": candidate,
        "snapshot": {
            "n_resolved_fit": int(len(fit)),
            "parent_feature_scaler": mech.scaler_snapshot(parent_sc),
            "baseline_model": mech.model_snapshot(baseline, mech.BASELINE_FEATURES),
            "candidate_model": mech.model_snapshot(candidate, mech.CANDIDATE_FEATURES),
        },
    }


def add_filters(trades: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    out = mech.add_range_integrity(trades, bundle["parent_scaler_object"])
    p_base = bundle["baseline_object"].predict_proba(out[mech.BASELINE_FEATURES].to_numpy(float))[:, 1]
    p_cand = bundle["candidate_object"].predict_proba(out[mech.CANDIDATE_FEATURES].to_numpy(float))[:, 1]
    out["p_baseline"] = p_base
    out["p_candidate"] = p_cand
    out["model_edge"] = p_cand - p_base
    out["structural_expected_net_return"] = (
        p_cand * out["reward_gross"].to_numpy(float)
        + (1.0 - p_cand) * out["loss_gross"].to_numpy(float)
        - ROUND_TRIP_COST
    )
    out["selected_trade"] = (out["model_edge"] > 0.0) & (out["structural_expected_net_return"] > 0.0)
    return out


def stats(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"n": 0, "mean_net_return": None, "median_net_return": None, "win_rate": None, "mean_holding_bars": None}
    return {
        "n": int(len(frame)),
        "mean_net_return": float(frame["net_return"].mean()),
        "median_net_return": float(frame["net_return"].median()),
        "win_rate": float((frame["net_return"] > 0.0).mean()),
        "mean_holding_bars": float(frame["holding_bars"].mean()),
    }


def validation_pair(trades: pd.DataFrame, dev_bundle: dict, pair_id: str, protocol: dict) -> dict:
    scored = add_filters(trades, dev_bundle)
    val = scored.loc[scored["day"].between(VAL_START, VAL_END)].copy()
    all_stats = stats(val)
    selected = val.loc[val["selected_trade"]].copy()
    selected_stats = stats(selected)
    annual = {}
    positive_years = 0
    each_year_ok = True
    min_year = int(protocol["VALIDATION"]["gate_each_pairing"]["minimum_each_year_selected_trades"][pair_id])
    for year in range(2021, 2026):
        yf = selected.loc[selected["day"].str.startswith(str(year))]
        ys = stats(yf)
        if ys["mean_net_return"] is not None and ys["mean_net_return"] > 0.0:
            positive_years += 1
        if ys["n"] < min_year:
            each_year_ok = False
        annual[str(year)] = ys
    min_pooled = int(protocol["VALIDATION"]["gate_each_pairing"]["minimum_selected_trades"][pair_id])
    gates = {
        "minimum_selected_trades": selected_stats["n"] >= min_pooled,
        "minimum_each_year_selected_trades": each_year_ok,
        "selected_mean_net_return_gt_0": selected_stats["mean_net_return"] is not None and selected_stats["mean_net_return"] > 0.0,
        "selected_mean_net_return_gt_all_tradeable_event_baseline": (
            selected_stats["mean_net_return"] is not None
            and all_stats["mean_net_return"] is not None
            and selected_stats["mean_net_return"] > all_stats["mean_net_return"]
        ),
        "annual_positive_mean_net_return_ge_4_of_5": positive_years >= 4,
    }
    return {
        "all_tradeable_event_baseline": all_stats,
        "candidate": selected_stats,
        "annual_candidate": annual,
        "gates": gates,
        "passed": bool(all(gates.values())),
    }


def final_freeze(mechanism_data: dict[str, pd.DataFrame], protocol: dict) -> dict:
    payload = {
        "schema_id": "factorlab_rmr_R2_economic_translation_v1_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R2_range_reentry_economic_translation_v1",
        "parent_mechanism_identity": "rmr_range_boundary_parent_integrity_v2",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": "2015-01-05", "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "thresholds": THRESHOLDS,
        "round_trip_cost_bps": 10.0,
        "entry": "next_observed_1m_close_after_R2_event_confirmation",
        "filter_1": "p_range_integrity_augmented_strictly_greater_than_p_geometry_baseline",
        "filter_2": "candidate_structural_expected_net_return_strictly_greater_than_zero",
        "pairings": {},
        "blackbox_minimum_selected_trades": protocol["BLACKBOX"]["gate_each_pairing"]["minimum_selected_trades"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    for pair_id, data in mechanism_data.items():
        bundle = fit_probability_bundle(data, VAL_END)
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
    waves = {name: common.detect_waves(prices, THRESHOLDS[name]) for name in ("S1", "S2", "S3")}

    mechanism_data: dict[str, pd.DataFrame] = {}
    trade_data: dict[str, pd.DataFrame] = {}
    validation = {}
    DEV_probability_snapshots = {}
    for pair_id, lower, parent in PAIRINGS:
        original_events = common.r2_events(prices, days, waves[parent], THRESHOLDS[lower], THRESHOLDS[parent])
        mechanism_data[pair_id] = mech.prepare(original_events)
        trades = trade_events(prices, days, waves[parent], THRESHOLDS[lower], THRESHOLDS[parent])
        trade_data[pair_id] = trades
        dev_bundle = fit_probability_bundle(mechanism_data[pair_id], DEV_END)
        DEV_probability_snapshots[pair_id] = dev_bundle["snapshot"]
        validation[pair_id] = validation_pair(trades, dev_bundle, pair_id, protocol)

    passed = bool(all(v["passed"] for v in validation.values()))
    receipt = {
        "schema_id": "factorlab_rmr_R2_economic_translation_v1_validation_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R2_range_reentry_economic_translation_v1",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "DEV_window": {"start": "2015-01-05", "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_opened": False,
        "round_trip_cost_bps": 10.0,
        "validation": validation,
        "DEV_probability_snapshots": DEV_probability_snapshots,
        "validation_passed": passed,
        "final_refit_performed": passed,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not passed:
        print("R2_ECONOMIC_TRANSLATION_VALIDATION_FAIL")
        return 2
    freeze = final_freeze(mechanism_data, protocol)
    dump_json(args.freeze.resolve(), freeze)
    print("R2_ECONOMIC_TRANSLATION_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
