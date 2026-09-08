#!/usr/bin/env python3
"""Diagnostic bridge from certified R1/R2 mechanisms to realized index economics.

DEV/VALIDATION only. No strategy selection, no refit, no BLACKBOX access.
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
            "cell": cell, "lane": "R1", "day": str(days[lower.confirm_idx]),
            "confirm_idx": int(lower.confirm_idx), "resolve_idx": int(resolved),
            "mechanism_outcome": outcome, "restoration": 1 if outcome == "recovery" else 0 if outcome == "failure" else np.nan,
            "severity": float(abs(lower.move) / vol_ref), **pf,
            "direction": int(parent_sign), "target": target, "failure": failure,
        }
        temp = pd.DataFrame([row])
        temp = add_integrity(temp, freeze_pair["parent_feature_scaler"], "parent_integrity")
        row["certified_probability"] = float(frozen_predict(freeze_pair["selected_candidate_model"], temp)[0])
        entry_idx = lower.confirm_idx + 1
        row["entry_invalid"] = True
        if entry_idx < len(prices):
            entry = float(prices[entry_idx])
            valid = (failure < entry < target) if parent_sign > 0 else (target < entry < failure)
            row["entry_invalid"] = not valid
            if valid:
                target_g = float(parent_sign * (target / entry - 1.0))
                failure_g = float(parent_sign * (failure / entry - 1.0))
                exit_price = float(prices[resolved])
                gross = float(parent_sign * (exit_price / entry - 1.0))
                row.update({
                    "entry_idx": int(entry_idx), "entry_price": entry,
                    "target_gross": target_g, "failure_gross": failure_g,
                    "reward_loss_abs_ratio": abs(target_g) / abs(failure_g) if failure_g != 0 else np.nan,
                    "break_even_restoration_probability_10bp": break_even_probability(target_g, failure_g),
                    "realized_gross": gross, "realized_net": gross - COST,
                    "win": bool(gross - COST > 0), "holding_bars": int(max(0, resolved - entry_idx)),
                    "censored": outcome == "censored",
                })
                theoretical = target_g if outcome == "recovery" else failure_g if outcome == "failure" else np.nan
                row["boundary_overshoot"] = gross - theoretical if np.isfinite(theoretical) else np.nan
                row.update(markouts(prices, entry_idx, entry, parent_sign))
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
                if z <= edge: outcome, resolved = "reentry", j; break
                if z >= continuation: outcome, resolved = "continuation", j; break
            else:
                if z >= edge: outcome, resolved = "reentry", j; break
                if z <= continuation: outcome, resolved = "continuation", j; break
        speed, vol_ratio = common.local_vol_features(prices, i)
        row = {
            "cell": cell, "lane": "R2", "day": str(days[i]), "confirm_idx": int(i), "resolve_idx": int(resolved),
            "mechanism_outcome": outcome, "restoration": 1 if outcome == "reentry" else 0 if outcome == "continuation" else np.nan,
            "outside_ratio": float(abs(x - edge) / edge / (width / edge)),
            "break_speed": float(speed / lower_threshold) if lower_threshold > 0 else np.nan,
            "local_vol_ratio": float(vol_ratio), **pf,
            "direction": int(-side), "target": float(edge), "failure": float(continuation),
        }
        temp = pd.DataFrame([row]).replace([np.inf, -np.inf], np.nan)
        needed = freeze_pair["candidate_model"]["features"][:-1]
        if temp[needed + ["abs_drift", "overlap", "parent_eff"]].isna().any(axis=None):
            continue
        temp = add_integrity(temp, freeze_pair["parent_feature_scaler"], "range_integrity")
        row["certified_probability"] = float(frozen_predict(freeze_pair["candidate_model"], temp)[0])
        entry_idx = i + 1
        row["entry_invalid"] = True
        if entry_idx < len(prices):
            entry = float(prices[entry_idx])
            valid = (edge < entry < continuation) if side > 0 else (continuation < entry < edge)
            row["entry_invalid"] = not valid
            if valid:
                direction = -side
                target_g = float(direction * (edge / entry - 1.0))
                failure_g = float(direction * (continuation / entry - 1.0))
                exit_price = float(prices[resolved])
                gross = float(direction * (exit_price / entry - 1.0))
                row.update({
                    "entry_idx": int(entry_idx), "entry_price": entry,
                    "target_gross": target_g, "failure_gross": failure_g,
                    "reward_loss_abs_ratio": abs(target_g) / abs(failure_g) if failure_g != 0 else np.nan,
                    "break_even_restoration_probability_10bp": break_even_probability(target_g, failure_g),
                    "realized_gross": gross, "realized_net": gross - COST,
                    "win": bool(gross - COST > 0), "holding_bars": int(max(0, resolved - entry_idx)),
                    "censored": outcome == "censored",
                })
                theoretical = target_g if outcome == "reentry" else failure_g if outcome == "continuation" else np.nan
                row["boundary_overshoot"] = gross - theoretical if np.isfinite(theoretical) else np.nan
                row.update(markouts(prices, entry_idx, entry, direction))
        rows.append(row)
        next_allowed = resolved
    return pd.DataFrame(rows)


def safe_mean(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.mean()) if len(s) else None


def safe_median(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return float(s.median()) if len(s) else None


def summarize(frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {"events": 0}
    trade = frame.loc[~frame["entry_invalid"] & frame["realized_net"].notna()].copy()
    out = {
        "events": int(len(frame)),
        "tradeable": int(len(trade)),
        "entry_invalid": int(frame["entry_invalid"].sum()),
        "mechanism_restoration_rate_resolved": safe_mean(frame["restoration"]),
    }
    if trade.empty:
        return out
    out.update({
        "mean_target_gross": safe_mean(trade["target_gross"]),
        "mean_failure_gross": safe_mean(trade["failure_gross"]),
        "median_reward_loss_abs_ratio": safe_median(trade["reward_loss_abs_ratio"]),
        "mean_break_even_probability_10bp": safe_mean(trade["break_even_restoration_probability_10bp"]),
        "mean_certified_probability": safe_mean(trade["certified_probability"]),
        "mean_realized_gross": safe_mean(trade["realized_gross"]),
        "mean_realized_net": safe_mean(trade["realized_net"]),
        "median_realized_net": safe_median(trade["realized_net"]),
        "win_rate": safe_mean(trade["win"].astype(float)),
        "censor_rate": safe_mean(trade["censored"].astype(float)),
        "median_holding_bars": safe_median(trade["holding_bars"]),
        "mean_boundary_overshoot": safe_mean(trade["boundary_overshoot"]),
    })
    for h in MARKOUTS:
        col = f"markout_{h}"
        out[f"mean_{col}"] = safe_mean(trade[col])
        values = pd.to_numeric(trade[col], errors="coerce").dropna()
        out[f"positive_share_{col}"] = float((values > 0).mean()) if len(values) else None
    valid = trade[["certified_probability", "realized_net"]].dropna()
    out["probability_net_return_correlation"] = float(valid.corr().iloc[0, 1]) if len(valid) > 2 else None
    bin_rows = []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        mask = trade["certified_probability"].ge(lo) & trade["certified_probability"].lt(hi)
        sub = trade.loc[mask]
        bin_rows.append({
            "lo": lo, "hi": min(hi, 1.0), "n": int(len(sub)),
            "mean_net_return": safe_mean(sub["realized_net"]),
            "mean_break_even_probability_10bp": safe_mean(sub["break_even_restoration_probability_10bp"]),
        })
    out["fixed_probability_bins"] = bin_rows
    return out


def role_summary(frame: pd.DataFrame) -> dict:
    dev = frame.loc[frame["day"] <= DEV_END].copy()
    val = frame.loc[frame["day"].between(VAL_START, VAL_END)].copy()
    annual = {}
    for year in range(2021, 2026):
        annual[str(year)] = summarize(val.loc[val["day"].str.startswith(str(year))])
    return {"DEV": summarize(dev), "VALIDATION": summarize(val), "VALIDATION_annual": annual}


def classify_failure_modes(report: dict) -> list[str]:
    labels = set()
    for cell in report["cells"].values():
        v = cell["VALIDATION"]
        if not v.get("tradeable"):
            continue
        bp = v.get("mean_break_even_probability_10bp")
        cp = v.get("mean_certified_probability")
        if bp is not None and cp is not None and bp > cp:
            labels.add("geometry_unfavorable")
        if (v.get("mean_boundary_overshoot") or 0) < -0.0005:
            labels.add("boundary_overshoot_tail")
        if (v.get("median_holding_bars") or 0) > 60 or (v.get("censor_rate") or 0) > 0.10:
            labels.add("slow_resolution_cost_exposure")
        if (v.get("mean_markout_1") or 0) < 0 or (v.get("mean_markout_5") or 0) < 0:
            labels.add("short_horizon_wrong_way_markout")
        corr = v.get("probability_net_return_correlation")
        if corr is not None and corr <= 0:
            labels.add("probability_not_monetonic_with_realized_return")
    return sorted(labels)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    frame = read_source(args.source.resolve())
    r1f, r2f = load_json(R1_FREEZE), load_json(R2_FREEZE)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = {k: float(v) for k, v in r1f["directional_change_thresholds"].items()}
    if thresholds != {k: float(v) for k, v in r2f["thresholds"].items()}:
        raise RuntimeError("R1/R2 frozen scales disagree")
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
        "max_read_day": VAL_END,
        "BLACKBOX_opened": False,
        "selection_or_strategy_optimization_performed": False,
        "round_trip_cost_bps_for_diagnostic": 10.0,
        "fixed_markout_horizons": MARKOUTS,
        "cells": {k: role_summary(v) for k, v in events.items()},
        "production_authority": False,
    }
    report["descriptive_failure_mode_labels"] = classify_failure_modes(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("MECHANISM_TO_EXECUTION_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
