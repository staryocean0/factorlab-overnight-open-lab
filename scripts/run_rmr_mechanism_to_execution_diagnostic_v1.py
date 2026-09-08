#!/usr/bin/env python3
"""Diagnostic bridge from certified R1/R2 mechanisms to realized index economics.

DEV/VALIDATION only. No strategy selection, no refit, no BLACKBOX access.
The certified event engines and frozen parameter bundles are reused unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common

DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_OUTPUT = ROOT / "docs/research/local_rmr_mechanism_to_execution_diagnostic_v1.json"
R1_FREEZE = ROOT / "docs/governance/rmr_R1_reusable_blackbox_parameter_freeze_v1.json"
R2_FREEZE = ROOT / "docs/governance/rmr_R2_range_integrity_v2_parameter_freeze.json"
EXPECTED_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
EXPECTED_R1_BUNDLE_SHA = "41072c78a6e657aec01d7da95d9c00bff23ff01829ada6afe256d7c254107fcb"
EXPECTED_R2_BUNDLE_SHA = "08d28cc1f145247cc755cea70b26cfb75a53941db8df0f0a0f640c268ae5f0d1"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
HORIZON = 1200
COST = 0.0010
MARKOUTS = [1, 5, 15, 30, 60, 120, 240]
BINS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0000001]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_source(path: Path) -> pd.DataFrame:
    if sha256(path) != EXPECTED_SHA:
        raise RuntimeError("diagnostic historical source SHA mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("diagnostic source boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("diagnostic attempted to read BLACKBOX rows")
    values = frame["close"].to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        raise RuntimeError("invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def validate_freezes(r1f: dict, r2f: dict) -> dict[str, float]:
    if r1f.get("parameter_bundle_sha256") != EXPECTED_R1_BUNDLE_SHA:
        raise RuntimeError("R1 certified bundle identity drifted")
    if r2f.get("parameter_bundle_sha256") != EXPECTED_R2_BUNDLE_SHA:
        raise RuntimeError("R2 certified bundle identity drifted")
    if r1f.get("historical_source_sha256") != EXPECTED_SHA or r2f.get("historical_source_sha256") != EXPECTED_SHA:
        raise RuntimeError("certified bundle historical source drifted")
    thresholds = {k: float(v) for k, v in r1f["directional_change_thresholds"].items()}
    if thresholds != {k: float(v) for k, v in r2f["thresholds"].items()}:
        raise RuntimeError("R1/R2 frozen scales disagree")
    expected = {
        "S1": 0.003445827004614232,
        "S2": 0.006891654009228464,
        "S3": 0.013783308018456928,
    }
    if thresholds != expected or float(r1f["DEV_median_rvol20"]) != expected["S3"]:
        raise RuntimeError("certified scale identity drifted")
    return thresholds


def frozen_predict(snapshot: dict, frame: pd.DataFrame) -> np.ndarray:
    features = snapshot["features"]
    x = frame[features].to_numpy(float)
    mean = np.asarray(snapshot["scaler"]["mean"], float)
    scale = np.asarray(snapshot["scaler"]["scale"], float)
    coef = np.asarray(snapshot["logistic"]["coef"], float)
    intercept = float(snapshot["logistic"]["intercept"])
    z = (x - mean) / scale
    logits = np.clip(z @ coef + intercept, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-logits))


def add_integrity(frame: pd.DataFrame, scaler: dict, name: str) -> pd.DataFrame:
    out = frame.copy()
    feats = scaler["features"]
    x = out[feats].to_numpy(float)
    mean = np.asarray(scaler["mean"], float)
    scale = np.asarray(scaler["scale"], float)
    orientation = np.asarray(scaler["orientation"], float)
    z = (x - mean) / scale
    out[name] = np.mean(z * orientation, axis=1)
    return out


def markouts(prices: np.ndarray, entry_idx: int, entry_price: float, direction: int) -> dict:
    result = {}
    for h in MARKOUTS:
        idx = entry_idx + h
        result[f"markout_{h}"] = float(direction * (prices[idx] / entry_price - 1.0)) if idx < len(prices) else np.nan
    return result


def break_even_probability(target_gross: float, failure_gross: float) -> float:
    denom = target_gross - failure_gross
    if not np.isfinite(denom) or denom <= 0:
        return np.nan
    return float((COST - failure_gross) / denom)


def add_execution_fields(
    row: dict,
    prices: np.ndarray,
    confirm_idx: int,
    resolved: int,
    direction: int,
    target: float,
    failure: float,
    outcome: str,
    restoration_label: str,
    failure_label: str,
) -> None:
    entry_idx = confirm_idx + 1
    row["entry_invalid"] = True
    if entry_idx >= len(prices):
        return
    entry = float(prices[entry_idx])
    current = float(prices[confirm_idx])
    if direction > 0:
        valid = failure < entry < target
    else:
        valid = target < entry < failure
    row["entry_invalid"] = not valid
    if not valid:
        return

    target_g = float(direction * (target / entry - 1.0))
    failure_g = float(direction * (failure / entry - 1.0))
    target_at_confirm = float(direction * (target / current - 1.0))
    failure_at_confirm = float(direction * (failure / current - 1.0))
    entry_move = float(direction * (entry / current - 1.0))
    reward_consumed = float(target_at_confirm - target_g)
    reward_consumed_fraction = (
        float(reward_consumed / target_at_confirm) if np.isfinite(target_at_confirm) and target_at_confirm > 0.0 else np.nan
    )
    p = float(row["certified_probability"])
    binary_expected_net = float(p * target_g + (1.0 - p) * failure_g - COST)

    exit_price = float(prices[resolved])
    gross = float(direction * (exit_price / entry - 1.0))
    theoretical = target_g if outcome == restoration_label else failure_g if outcome == failure_label else np.nan
    boundary_overshoot = gross - theoretical if np.isfinite(theoretical) else np.nan
    target_overshoot = boundary_overshoot if outcome == restoration_label else np.nan
    failure_overshoot = boundary_overshoot if outcome == failure_label else np.nan

    row.update(
        {
            "entry_idx": int(entry_idx),
            "entry_price": entry,
            "confirmation_price": current,
            "entry_move_from_confirmation": entry_move,
            "target_gross_at_confirmation": target_at_confirm,
            "failure_gross_at_confirmation": failure_at_confirm,
            "target_reward_consumed_by_entry": reward_consumed,
            "target_reward_consumed_fraction": reward_consumed_fraction,
            "target_gross": target_g,
            "failure_gross": failure_g,
            "reward_loss_abs_ratio": abs(target_g) / abs(failure_g) if failure_g != 0 else np.nan,
            "break_even_restoration_probability_10bp": break_even_probability(target_g, failure_g),
            "binary_structural_expected_net_10bp": binary_expected_net,
            "realized_gross": gross,
            "realized_net": gross - COST,
            "win": bool(gross - COST > 0),
            "holding_bars": int(max(0, resolved - entry_idx)),
            "censored": outcome == "censored",
            "boundary_overshoot": boundary_overshoot,
            "target_overshoot": target_overshoot,
            "failure_overshoot": failure_overshoot,
        }
    )
    row.update(markouts(prices, entry_idx, entry, direction))


def r1_diagnostic_events(prices, days, lower_waves, parent_waves, vol_ref, cell, freeze_pair):
    parent_confirms = [w.confirm_idx for w in parent_waves]
    rows = []
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
        target = float(lower.start_price)
        failure = float(common.structural_boundary(w1, w2, parent_sign))
        current = float(prices[lower.confirm_idx])
        if parent_sign > 0 and not (failure < current < target):
            continue
        if parent_sign < 0 and not (target < current < failure):
            continue
        outcome, resolved = common.first_passage(prices, lower.confirm_idx, target, failure, parent_sign, HORIZON)
        if outcome == "tie":
            continue
        row = {
            "cell": cell,
            "lane": "R1",
            "day": str(days[lower.confirm_idx]),
            "confirm_idx": int(lower.confirm_idx),
            "resolve_idx": int(resolved),
            "mechanism_outcome": outcome,
            "restoration": 1 if outcome == "recovery" else 0 if outcome == "failure" else np.nan,
            "severity": float(abs(lower.move) / vol_ref),
            **pf,
            "direction": int(parent_sign),
            "target": target,
            "failure": failure,
        }
        temp = add_integrity(pd.DataFrame([row]), freeze_pair["parent_feature_scaler"], "parent_integrity")
        row["certified_probability"] = float(frozen_predict(freeze_pair["selected_candidate_model"], temp)[0])
        add_execution_fields(
            row,
            prices,
            lower.confirm_idx,
            resolved,
            parent_sign,
            target,
            failure,
            outcome,
            "recovery",
            "failure",
        )
        rows.append(row)
        next_allowed = resolved
    return pd.DataFrame(rows)


def r2_diagnostic_events(prices, days, parent_waves, lower_threshold, parent_threshold, cell, freeze_pair):
    rows = []
    next_allowed = -1
    wave_cursor = 0
    last2 = []
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
        if width <= 0:
            continue
        if x >= high * (1.0 + lower_threshold):
            side, edge = 1, high
        elif x <= low * (1.0 - lower_threshold):
            side, edge = -1, low
        else:
            continue
        continuation = edge * (1.0 + parent_threshold) if side > 0 else edge * (1.0 - parent_threshold)
        if (side > 0 and x >= continuation) or (side < 0 and x <= continuation):
            continue
        end = min(len(prices) - 1, i + HORIZON)
        outcome, resolved = "censored", end
        for j in range(i, end + 1):
            z = float(prices[j])
            if side > 0:
                if z <= edge:
                    outcome, resolved = "reentry", j
                    break
                if z >= continuation:
                    outcome, resolved = "continuation", j
                    break
            else:
                if z >= edge:
                    outcome, resolved = "reentry", j
                    break
                if z <= continuation:
                    outcome, resolved = "continuation", j
                    break
        speed, vol_ratio = common.local_vol_features(prices, i)
        row = {
            "cell": cell,
            "lane": "R2",
            "day": str(days[i]),
            "confirm_idx": int(i),
            "resolve_idx": int(resolved),
            "mechanism_outcome": outcome,
            "restoration": 1 if outcome == "reentry" else 0 if outcome == "continuation" else np.nan,
            "outside_ratio": float(abs(x - edge) / edge / (width / edge)),
            "break_speed": float(speed / lower_threshold) if lower_threshold > 0 else np.nan,
            "local_vol_ratio": float(vol_ratio),
            **pf,
            "direction": int(-side),
            "target": float(edge),
            "failure": float(continuation),
        }
        temp = pd.DataFrame([row]).replace([np.inf, -np.inf], np.nan)
        needed = freeze_pair["candidate_model"]["features"][:-1]
        if temp[needed + ["abs_drift", "overlap", "parent_eff"]].isna().any(axis=None):
            continue
        temp = add_integrity(temp, freeze_pair["parent_feature_scaler"], "range_integrity")
        row["certified_probability"] = float(frozen_predict(freeze_pair["candidate_model"], temp)[0])
        add_execution_fields(
            row,
            prices,
            i,
            resolved,
            -side,
            float(edge),
            float(continuation),
            outcome,
            "reentry",
            "continuation",
        )
        rows.append(row)
        next_allowed = resolved
    return pd.DataFrame(rows)


def safe_mean(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.mean()) if len(s) else None


def safe_median(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.median()) if len(s) else None


def safe_quantile(s, q: float):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.quantile(q)) if len(s) else None


def summarize(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"events": 0, "tradeable": 0, "next_minute_tradeable_fraction": None}
    trade = frame.loc[~frame["entry_invalid"] & frame["realized_net"].notna()].copy()
    out = {
        "events": int(len(frame)),
        "tradeable": int(len(trade)),
        "next_minute_tradeable_fraction": float(len(trade) / len(frame)),
        "entry_invalid": int(frame["entry_invalid"].sum()),
        "mechanism_restoration_rate_resolved": safe_mean(frame["restoration"]),
        "mean_certified_probability_all_confirmed": safe_mean(frame["certified_probability"]),
    }
    if trade.empty:
        return out
    out.update(
        {
            "mean_target_gross": safe_mean(trade["target_gross"]),
            "mean_failure_gross": safe_mean(trade["failure_gross"]),
            "median_reward_loss_abs_ratio": safe_median(trade["reward_loss_abs_ratio"]),
            "mean_break_even_probability_10bp": safe_mean(trade["break_even_restoration_probability_10bp"]),
            "mean_certified_probability": safe_mean(trade["certified_probability"]),
            "mean_binary_structural_expected_net_10bp": safe_mean(trade["binary_structural_expected_net_10bp"]),
            "mean_realized_gross": safe_mean(trade["realized_gross"]),
            "mean_realized_net": safe_mean(trade["realized_net"]),
            "median_realized_net": safe_median(trade["realized_net"]),
            "win_rate": safe_mean(trade["win"].astype(float)),
            "censor_rate": safe_mean(trade["censored"].astype(float)),
            "mean_holding_bars": safe_mean(trade["holding_bars"]),
            "median_holding_bars": safe_median(trade["holding_bars"]),
            "p90_holding_bars": safe_quantile(trade["holding_bars"], 0.90),
            "mean_entry_move_from_confirmation": safe_mean(trade["entry_move_from_confirmation"]),
            "mean_target_reward_consumed_by_entry": safe_mean(trade["target_reward_consumed_by_entry"]),
            "median_target_reward_consumed_fraction": safe_median(trade["target_reward_consumed_fraction"]),
            "mean_boundary_overshoot": safe_mean(trade["boundary_overshoot"]),
            "mean_target_overshoot": safe_mean(trade["target_overshoot"]),
            "mean_failure_overshoot": safe_mean(trade["failure_overshoot"]),
        }
    )
    for h in MARKOUTS:
        col = f"markout_{h}"
        out[f"mean_{col}"] = safe_mean(trade[col])
        values = pd.to_numeric(trade[col], errors="coerce").dropna()
        out[f"positive_share_{col}"] = float((values > 0).mean()) if len(values) else None

    valid = trade[["certified_probability", "realized_net"]].dropna()
    out["probability_net_return_correlation"] = float(valid.corr().iloc[0, 1]) if len(valid) > 2 else None
    bin_rows = []
    nonempty_bin_means = []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        mask = trade["certified_probability"].ge(lo) & trade["certified_probability"].lt(hi)
        sub = trade.loc[mask]
        mean_net = safe_mean(sub["realized_net"])
        bin_rows.append(
            {
                "lo": lo,
                "hi": min(hi, 1.0),
                "n": int(len(sub)),
                "mean_certified_probability": safe_mean(sub["certified_probability"]),
                "mean_realized_net": mean_net,
                "mean_binary_structural_expected_net_10bp": safe_mean(sub["binary_structural_expected_net_10bp"]),
                "mean_break_even_probability_10bp": safe_mean(sub["break_even_restoration_probability_10bp"]),
            }
        )
        if mean_net is not None:
            nonempty_bin_means.append(mean_net)
    out["fixed_probability_bins"] = bin_rows
    out["probability_bin_mean_net_monotonic_non_decreasing"] = (
        all(b >= a for a, b in zip(nonempty_bin_means, nonempty_bin_means[1:])) if len(nonempty_bin_means) >= 2 else None
    )
    return out


def role_summary(frame: pd.DataFrame) -> dict:
    dev = frame.loc[frame["day"] <= DEV_END].copy()
    val = frame.loc[frame["day"].between(VAL_START, VAL_END)].copy()
    annual = {}
    for year in range(2021, 2026):
        annual[str(year)] = summarize(val.loc[val["day"].str.startswith(str(year))])
    return {"DEV": summarize(dev), "VALIDATION": summarize(val), "VALIDATION_annual": annual}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    frame = read_source(args.source.resolve())
    r1f, r2f = load_json(R1_FREEZE), load_json(R2_FREEZE)
    thresholds = validate_freezes(r1f, r2f)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    vol_ref = float(r1f["DEV_median_rvol20"])
    waves = {k: common.detect_waves(prices, thresholds[k]) for k in ("S1", "S2", "S3")}

    events = {
        "R1_A": r1_diagnostic_events(prices, days, waves["S1"], waves["S2"], vol_ref, "R1_A", r1f["pairings"]["PAIR_A"]),
        "R1_B": r1_diagnostic_events(prices, days, waves["S2"], waves["S3"], vol_ref, "R1_B", r1f["pairings"]["PAIR_B"]),
        "R2_A": r2_diagnostic_events(prices, days, waves["S2"], thresholds["S1"], thresholds["S2"], "R2_A", r2f["pairings"]["PAIR_A"]),
        "R2_B": r2_diagnostic_events(prices, days, waves["S3"], thresholds["S2"], thresholds["S3"], "R2_B", r2f["pairings"]["PAIR_B"]),
    }
    report = {
        "schema_id": "factorlab_rmr_mechanism_to_execution_diagnostic_v1@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_mechanism_to_execution_diagnostic_v1",
        "historical_source_sha256": EXPECTED_SHA,
        "certified_R1_parameter_bundle_sha256": EXPECTED_R1_BUNDLE_SHA,
        "certified_R2_parameter_bundle_sha256": EXPECTED_R2_BUNDLE_SHA,
        "frozen_scale_identity": thresholds,
        "max_read_day": VAL_END,
        "BLACKBOX_opened": False,
        "BLACKBOX_query_created": False,
        "selection_or_strategy_optimization_performed": False,
        "refit_performed": False,
        "round_trip_cost_bps_for_diagnostic": 10.0,
        "structural_resolution_horizon_bars": HORIZON,
        "fixed_markout_horizons": MARKOUTS,
        "fixed_probability_bins": [[0.0, 0.2], [0.2, 0.4], [0.4, 0.6], [0.6, 0.8], [0.8, 1.0]],
        "cells": {k: role_summary(v) for k, v in events.items()},
        "production_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("MECHANISM_TO_EXECUTION_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
