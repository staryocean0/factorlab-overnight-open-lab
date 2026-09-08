#!/usr/bin/env python3
"""Unified R1/R2 parent-normal-state router on reusable DEV / VALIDATION.

Reads only through 2025-12-31. Reuses the original causal R1/R2 event engines,
fits cell-local geometry baselines on DEV, and tests one pooled signed
state-consistency increment. BLACKBOX is never read here.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_unified_parent_state_router_v1_protocol.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_unified_parent_state_router_v1_validation_receipt.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_unified_parent_state_router_v1_parameter_freeze.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
PARENT_FEATURES = ["abs_drift", "overlap", "parent_eff"]
POOL_BASE_FEATURES = ["base_logit", "lane_R2", "pair_B"]
POOL_CAND_FEATURES = POOL_BASE_FEATURES + ["state_consistency"]
CELL_ORDER = ("R1_A", "R1_B", "R2_A", "R2_B")


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
    if p["research_identity"] != "rmr_unified_parent_normal_state_router_v1":
        raise RuntimeError("router identity drifted")
    if p["parent_state"]["trend_axis"] != "(z(abs_drift)-z(overlap)+z(parent_eff))/3":
        raise RuntimeError("router axis drifted")
    if p["pooled_models"]["candidate_features"] != POOL_CAND_FEATURES:
        raise RuntimeError("router candidate features drifted")
    if p["BLACKBOX"]["query_number_if_reached"] != 4:
        raise RuntimeError("router query number drifted")
    return p


def read_source(path: Path) -> pd.DataFrame:
    actual = sha256(path)
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"historical source SHA mismatch: {actual}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame = frame.loc[frame["symbol"].eq(SYMBOL)].copy()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("router historical source boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("router DEV/VALIDATION runner read BLACKBOX rows")
    values = frame["close"].to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        raise RuntimeError("router invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def build_events(frame: pd.DataFrame, protocol: dict) -> dict[str, pd.DataFrame]:
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = {k: float(protocol["frozen_scales"][k]) for k in ("S1", "S2", "S3")}
    # Scale identity is inherited from the already-certified R1/R2 mechanisms.
    # Do not re-estimate it under the later reusable DEV window.
    vol_ref = float(protocol["frozen_scales"]["DEV_median_rvol20"])
    if not np.isfinite(vol_ref) or vol_ref <= 0.0:
        raise RuntimeError("router frozen DEV volatility reference invalid")
    waves = {name: common.detect_waves(prices, thresholds[name]) for name in ("S1", "S2", "S3")}
    out: dict[str, pd.DataFrame] = {}
    for cell_id in CELL_ORDER:
        cfg = protocol["cells"][cell_id]
        lower, parent = cfg["lower"], cfg["parent"]
        if cfg["lane"] == "R1":
            e = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        else:
            e = common.r2_events(prices, days, waves[parent], thresholds[lower], thresholds[parent])
        if e.empty:
            out[cell_id] = e.copy()
            continue
        e = e.copy()
        e["cell"] = cell_id
        e["lane"] = cfg["lane"]
        e["lane_R2"] = 1.0 if cfg["lane"] == "R2" else 0.0
        e["pair_B"] = 1.0 if cell_id.endswith("_B") else 0.0
        out[cell_id] = e
    return out


def resolved_frame(events: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    positive, negative = cfg["positive"], cfg["negative"]
    out = events.loc[events["outcome"].isin([positive, negative])].copy()
    out["y"] = out["outcome"].eq(positive).astype(int)
    needed = PARENT_FEATURES + cfg["local_baseline_features"]
    return out.replace([np.inf, -np.inf], np.nan).dropna(subset=needed).reset_index(drop=True)


def fit_parent_scaler(all_events: dict[str, pd.DataFrame], end_day: str) -> StandardScaler:
    parts = []
    for frame in all_events.values():
        if frame.empty:
            continue
        part = frame.loc[frame["day"] <= end_day, PARENT_FEATURES].replace([np.inf, -np.inf], np.nan).dropna()
        if not part.empty:
            parts.append(part)
    if not parts:
        raise RuntimeError("router parent scaler has no eligible events")
    x = pd.concat(parts, ignore_index=True)[PARENT_FEATURES].to_numpy(float)
    return StandardScaler().fit(x)


def add_state_consistency(frame: pd.DataFrame, scaler: StandardScaler, lane: str) -> pd.DataFrame:
    out = frame.copy()
    z = scaler.transform(out[PARENT_FEATURES].to_numpy(float))
    axis = (z[:, 0] - z[:, 1] + z[:, 2]) / 3.0
    out["state_consistency"] = axis if lane == "R1" else -axis
    return out


def fit_logit(frame: pd.DataFrame, features: list[str]) -> Pipeline:
    if len(frame) < 20 or frame["y"].nunique() < 2:
        raise RuntimeError("router model has insufficient DEV classes")
    model = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000)),
    ])
    model.fit(frame[features].to_numpy(float), frame["y"].to_numpy(int))
    return model


def score(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> dict:
    if frame.empty:
        return {"status": "empty", "n": 0, "brier": None, "log_loss": None, "event_rate": None}
    p = model.predict_proba(frame[features].to_numpy(float))[:, 1]
    y = frame["y"].to_numpy(int)
    return {
        "status": "scored",
        "n": int(len(frame)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "event_rate": float(np.mean(y)),
    }


def add_local_baseline_probability(frame: pd.DataFrame, model: Pipeline, features: list[str]) -> pd.DataFrame:
    out = frame.copy()
    p = model.predict_proba(out[features].to_numpy(float))[:, 1]
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    out["base_logit"] = np.log(p / (1.0 - p))
    return out


def build_pooled(
    all_events: dict[str, pd.DataFrame],
    protocol: dict,
    parent_scaler: StandardScaler,
    cell_models: dict[str, Pipeline],
) -> pd.DataFrame:
    parts = []
    for cell_id in CELL_ORDER:
        cfg = protocol["cells"][cell_id]
        data = resolved_frame(all_events[cell_id], cfg)
        if data.empty:
            continue
        data = add_state_consistency(data, parent_scaler, cfg["lane"])
        data = add_local_baseline_probability(data, cell_models[cell_id], cfg["local_baseline_features"])
        parts.append(data[["day", "cell", "lane", "lane_R2", "pair_B", "y", "base_logit", "state_consistency"]])
    if not parts:
        raise RuntimeError("router pooled frame empty")
    return pd.concat(parts, ignore_index=True).sort_values(["day", "cell"], kind="mergesort").reset_index(drop=True)


def model_snapshot(model: Pipeline, features: list[str]) -> dict:
    sc = model.named_steps["sc"]
    lr = model.named_steps["lr"]
    return {
        "features": list(features),
        "scaler": {"mean": [float(x) for x in sc.mean_], "scale": [float(x) for x in sc.scale_]},
        "logistic": {"coef": [float(x) for x in lr.coef_[0]], "intercept": float(lr.intercept_[0])},
    }


def parent_scaler_snapshot(scaler: StandardScaler) -> dict:
    return {
        "features": PARENT_FEATURES,
        "mean": [float(x) for x in scaler.mean_],
        "scale": [float(x) for x in scaler.scale_],
    }


def evaluate_validation(all_events: dict[str, pd.DataFrame], protocol: dict) -> tuple[dict, dict]:
    parent_scaler = fit_parent_scaler(all_events, DEV_END)
    cell_models: dict[str, Pipeline] = {}
    cell_inventory = {}
    for cell_id in CELL_ORDER:
        cfg = protocol["cells"][cell_id]
        data = resolved_frame(all_events[cell_id], cfg)
        dev = data.loc[data["day"] <= DEV_END].copy()
        val = data.loc[data["day"].between(VAL_START, VAL_END)].copy()
        cell_models[cell_id] = fit_logit(dev, cfg["local_baseline_features"])
        cell_inventory[cell_id] = {"DEV_resolved": int(len(dev)), "VALIDATION_resolved": int(len(val))}

    pooled = build_pooled(all_events, protocol, parent_scaler, cell_models)
    dev_pool = pooled.loc[pooled["day"] <= DEV_END].copy()
    val_pool = pooled.loc[pooled["day"].between(VAL_START, VAL_END)].copy()
    base_model = fit_logit(dev_pool, POOL_BASE_FEATURES)
    cand_model = fit_logit(dev_pool, POOL_CAND_FEATURES)

    pooled_base = score(base_model, val_pool, POOL_BASE_FEATURES)
    pooled_cand = score(cand_model, val_pool, POOL_CAND_FEATURES)

    lane_results = {}
    for lane in ("R1", "R2"):
        subset = val_pool.loc[val_pool["lane"].eq(lane)]
        b = score(base_model, subset, POOL_BASE_FEATURES)
        c = score(cand_model, subset, POOL_CAND_FEATURES)
        lane_results[lane] = {
            "baseline": b,
            "candidate": c,
            "brier_improvement": b["brier"] - c["brier"],
            "logloss_improvement": b["log_loss"] - c["log_loss"],
        }

    cell_results = {}
    for cell_id in CELL_ORDER:
        subset = val_pool.loc[val_pool["cell"].eq(cell_id)]
        b = score(base_model, subset, POOL_BASE_FEATURES)
        c = score(cand_model, subset, POOL_CAND_FEATURES)
        cell_results[cell_id] = {
            "baseline": b,
            "candidate": c,
            "brier_improvement": b["brier"] - c["brier"],
        }

    annual = {}
    positive_years = 0
    for year in range(2021, 2026):
        subset = val_pool.loc[val_pool["day"].str.startswith(str(year))]
        b = score(base_model, subset, POOL_BASE_FEATURES)
        c = score(cand_model, subset, POOL_CAND_FEATURES)
        delta = b["brier"] - c["brier"]
        if delta > 0:
            positive_years += 1
        annual[str(year)] = {"baseline": b, "candidate": c, "brier_improvement": delta}

    coef_idx = POOL_CAND_FEATURES.index("state_consistency")
    state_coef = float(cand_model.named_steps["lr"].coef_[0][coef_idx])
    min_counts = protocol["VALIDATION"]["minimum_resolved"]
    gates = {
        "minimum_resolved_all_cells": all(cell_inventory[c]["VALIDATION_resolved"] >= int(min_counts[c]) for c in CELL_ORDER),
        "pooled_brier_better": pooled_cand["brier"] < pooled_base["brier"],
        "pooled_logloss_better": pooled_cand["log_loss"] < pooled_base["log_loss"],
        "R1_lane_brier_and_logloss_better": lane_results["R1"]["brier_improvement"] > 0 and lane_results["R1"]["logloss_improvement"] > 0,
        "R2_lane_brier_and_logloss_better": lane_results["R2"]["brier_improvement"] > 0 and lane_results["R2"]["logloss_improvement"] > 0,
        "all_four_cells_brier_better": all(cell_results[c]["brier_improvement"] > 0 for c in CELL_ORDER),
        "annual_pooled_brier_positive_ge_4_of_5": positive_years >= 4,
        "DEV_state_consistency_coefficient_positive": state_coef > 0,
    }
    result = {
        "inventory": cell_inventory,
        "pooled": {
            "baseline": pooled_base,
            "candidate": pooled_cand,
            "brier_improvement": pooled_base["brier"] - pooled_cand["brier"],
            "logloss_improvement": pooled_base["log_loss"] - pooled_cand["log_loss"],
        },
        "lanes": lane_results,
        "cells": cell_results,
        "annual": annual,
        "DEV_state_consistency_coefficient": state_coef,
        "gates": gates,
        "passed": bool(all(gates.values())),
    }
    fit_meta = {
        "DEV_parent_scaler": parent_scaler_snapshot(parent_scaler),
        "DEV_cell_baselines": {
            c: model_snapshot(cell_models[c], protocol["cells"][c]["local_baseline_features"])
            for c in CELL_ORDER
        },
        "DEV_pooled_baseline": model_snapshot(base_model, POOL_BASE_FEATURES),
        "DEV_pooled_candidate": model_snapshot(cand_model, POOL_CAND_FEATURES),
    }
    return result, fit_meta


def final_refit(all_events: dict[str, pd.DataFrame], protocol: dict) -> dict:
    parent_scaler = fit_parent_scaler(all_events, VAL_END)
    cell_models: dict[str, Pipeline] = {}
    final_counts = {}
    for cell_id in CELL_ORDER:
        cfg = protocol["cells"][cell_id]
        data = resolved_frame(all_events[cell_id], cfg)
        pool = data.loc[data["day"] <= VAL_END].copy()
        cell_models[cell_id] = fit_logit(pool, cfg["local_baseline_features"])
        final_counts[cell_id] = int(len(pool))

    pooled = build_pooled(all_events, protocol, parent_scaler, cell_models)
    pool = pooled.loc[pooled["day"] <= VAL_END].copy()
    base_model = fit_logit(pool, POOL_BASE_FEATURES)
    cand_model = fit_logit(pool, POOL_CAND_FEATURES)

    payload = {
        "schema_id": "factorlab_rmr_unified_parent_state_router_v1_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_unified_parent_normal_state_router_v1",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": "2015-01-05", "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "DEV_median_rvol20": float(protocol["frozen_scales"]["DEV_median_rvol20"]),
        "thresholds": {k: float(protocol["frozen_scales"][k]) for k in ("S1", "S2", "S3")},
        "parent_scaler": parent_scaler_snapshot(parent_scaler),
        "cell_baselines": {
            c: model_snapshot(cell_models[c], protocol["cells"][c]["local_baseline_features"])
            for c in CELL_ORDER
        },
        "pooled_baseline": model_snapshot(base_model, POOL_BASE_FEATURES),
        "pooled_candidate": model_snapshot(cand_model, POOL_CAND_FEATURES),
        "final_refit_resolved_counts": final_counts,
        "blackbox_minimum_resolved": protocol["BLACKBOX"]["minimum_resolved"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    payload["parameter_bundle_sha256"] = json_digest(payload)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    args = ap.parse_args()

    protocol = validate_protocol()
    frame = read_source(args.source.resolve())
    all_events = build_events(frame, protocol)
    validation, fit_meta = evaluate_validation(all_events, protocol)
    passed = bool(validation["passed"])
    receipt = {
        "schema_id": "factorlab_rmr_unified_parent_state_router_v1_validation_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_unified_parent_normal_state_router_v1",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "DEV_window": {"start": "2015-01-05", "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_opened": False,
        "validation": validation,
        "DEV_fit_metadata": fit_meta,
        "validation_passed": passed,
        "final_refit_performed": passed,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not passed:
        print("UNIFIED_ROUTER_VALIDATION_FAIL")
        return 2
    freeze = final_refit(all_events, protocol)
    dump_json(args.freeze.resolve(), freeze)
    print("UNIFIED_ROUTER_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
