#!/usr/bin/env python3
"""Dedicated R2 range-integrity validation on reusable DEV / VALIDATION.

Reads only through 2025-12-31. Reuses the original causal R2 event engine and
compares breakout geometry against geometry + one parent range-integrity score.
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

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R2_range_integrity_v2_protocol.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R2_range_integrity_v2_validation_receipt.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R2_range_integrity_v2_parameter_freeze.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
THRESHOLDS = {
    "S1": 0.003445827004614232,
    "S2": 0.006891654009228464,
    "S3": 0.013783308018456928,
}
PAIRINGS = (("PAIR_A", "S1", "S2"), ("PAIR_B", "S2", "S3"))
BASELINE_FEATURES = ["outside_ratio", "break_speed", "local_vol_ratio"]
PARENT_FEATURES = ["abs_drift", "overlap", "parent_eff"]
CANDIDATE_FEATURES = BASELINE_FEATURES + ["range_integrity"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    if p["research_identity"] != "rmr_range_boundary_parent_integrity_v2":
        raise RuntimeError("R2 identity drifted")
    if p["baseline"]["features"] != BASELINE_FEATURES:
        raise RuntimeError("R2 baseline drifted")
    if p["candidate"]["formula"] != "(-z(abs_drift)+z(overlap)-z(parent_eff))/3":
        raise RuntimeError("R2 range-integrity formula drifted")
    if p["frozen_scales"]["scale_search_allowed"] is not False:
        raise RuntimeError("R2 scale search unexpectedly allowed")
    return p


def read_source(path: Path) -> pd.DataFrame:
    actual = sha256(path)
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"R2 source SHA mismatch: {actual}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", VAL_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) != VAL_END:
        raise RuntimeError("R2 detailed source boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("R2 DEV/VALIDATION runner read BLACKBOX")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("R2 invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def prepare(events: pd.DataFrame) -> pd.DataFrame:
    cols = ["day", *BASELINE_FEATURES, *PARENT_FEATURES, "outcome"]
    out = events.loc[events["outcome"].isin(["reentry", "continuation"]), cols].copy()
    out["y"] = out["outcome"].eq("reentry").astype(int)
    return out.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def fit_parent_scaler(frame: pd.DataFrame) -> StandardScaler:
    sc = StandardScaler()
    sc.fit(frame[PARENT_FEATURES].to_numpy(float))
    return sc


def add_range_integrity(frame: pd.DataFrame, scaler: StandardScaler) -> pd.DataFrame:
    out = frame.copy()
    z = scaler.transform(out[PARENT_FEATURES].to_numpy(float))
    out["range_integrity"] = (-z[:, 0] + z[:, 1] - z[:, 2]) / 3.0
    return out


def fit_logit(frame: pd.DataFrame, features: list[str]) -> Pipeline:
    if len(frame) < 30 or frame["y"].nunique() < 2:
        raise RuntimeError("R2 insufficient fit sample")
    model = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000)),
    ])
    model.fit(frame[features].to_numpy(float), frame["y"].to_numpy(int))
    return model


def scaler_snapshot(sc: StandardScaler) -> dict:
    return {
        "features": list(PARENT_FEATURES),
        "orientation": [-1, 1, -1],
        "mean": [float(x) for x in sc.mean_],
        "scale": [float(x) for x in sc.scale_],
        "var": [float(x) for x in sc.var_],
    }


def model_snapshot(model: Pipeline, features: list[str]) -> dict:
    sc = model.named_steps["sc"]
    lr = model.named_steps["lr"]
    return {
        "features": list(features),
        "scaler": {
            "mean": [float(x) for x in sc.mean_],
            "scale": [float(x) for x in sc.scale_],
            "var": [float(x) for x in sc.var_],
        },
        "logistic": {
            "C": 1.0,
            "classes": [int(x) for x in lr.classes_],
            "coef": [float(x) for x in lr.coef_[0]],
            "intercept": float(lr.intercept_[0]),
        },
    }


def metrics(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> dict:
    if frame.empty:
        return {"n": 0, "brier": None, "logloss": None, "event_rate": None}
    y = frame["y"].to_numpy(int)
    p = model.predict_proba(frame[features].to_numpy(float))[:, 1]
    return {
        "n": int(len(frame)),
        "brier": float(brier_score_loss(y, p)),
        "logloss": float(log_loss(y, p, labels=[0, 1])),
        "event_rate": float(np.mean(y)),
    }


def validation_pair(data: pd.DataFrame, pair_id: str, protocol: dict) -> tuple[dict, dict]:
    dev = data.loc[data["day"] <= DEV_END].copy()
    val = data.loc[data["day"].between(VAL_START, VAL_END)].copy()
    parent_sc = fit_parent_scaler(dev)
    dev_c = add_range_integrity(dev, parent_sc)
    val_c = add_range_integrity(val, parent_sc)
    baseline = fit_logit(dev, BASELINE_FEATURES)
    candidate = fit_logit(dev_c, CANDIDATE_FEATURES)

    pooled_base = metrics(baseline, val, BASELINE_FEATURES)
    pooled_cand = metrics(candidate, val_c, CANDIDATE_FEATURES)
    annual = {}
    positive_years = 0
    each_year_ok = True
    min_year = int(protocol["VALIDATION"]["gate_each_pairing"]["minimum_each_year_resolved"][pair_id])
    for year in range(2021, 2026):
        mask = val["day"].str.startswith(str(year))
        b = metrics(baseline, val.loc[mask], BASELINE_FEATURES)
        c = metrics(candidate, val_c.loc[mask], CANDIDATE_FEATURES)
        delta = None if b["n"] == 0 else float(b["brier"] - c["brier"])
        if delta is not None and delta > 0:
            positive_years += 1
        if b["n"] < min_year:
            each_year_ok = False
        annual[str(year)] = {"baseline": b, "candidate": c, "baseline_minus_candidate_brier": delta}

    coef = float(candidate.named_steps["lr"].coef_[0][-1])
    min_pooled = int(protocol["VALIDATION"]["gate_each_pairing"]["minimum_pooled_resolved"][pair_id])
    gates = {
        "minimum_pooled_resolved": len(val) >= min_pooled,
        "minimum_each_year_resolved": each_year_ok,
        "pooled_brier_better": pooled_cand["brier"] < pooled_base["brier"],
        "pooled_logloss_better": pooled_cand["logloss"] < pooled_base["logloss"],
        "annual_brier_improvement_ge_4_of_5": positive_years >= 4,
        "DEV_range_integrity_coefficient_positive": coef > 0.0,
    }
    result = {
        "inventory": {"DEV_resolved": int(len(dev)), "VALIDATION_resolved": int(len(val))},
        "baseline": pooled_base,
        "candidate": pooled_cand,
        "baseline_minus_candidate_brier": float(pooled_base["brier"] - pooled_cand["brier"]),
        "baseline_minus_candidate_logloss": float(pooled_base["logloss"] - pooled_cand["logloss"]),
        "DEV_range_integrity_coef": coef,
        "annual": annual,
        "gates": gates,
        "passed": bool(all(gates.values())),
    }
    fit_snapshot = {
        "parent_feature_scaler": scaler_snapshot(parent_sc),
        "baseline_model": model_snapshot(baseline, BASELINE_FEATURES),
        "candidate_model": model_snapshot(candidate, CANDIDATE_FEATURES),
    }
    return result, fit_snapshot


def final_refit(pair_data: dict[str, pd.DataFrame], protocol: dict) -> dict:
    payload = {
        "schema_id": "factorlab_rmr_R2_range_integrity_v2_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_range_boundary_parent_integrity_v2",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": "2015-01-05", "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "thresholds": THRESHOLDS,
        "baseline_features": BASELINE_FEATURES,
        "candidate_features": CANDIDATE_FEATURES,
        "pairings": {},
        "blackbox_minimum_resolved": protocol["BLACKBOX"]["gate_each_pairing"]["minimum_resolved"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    for pair_id, data in pair_data.items():
        parent_sc = fit_parent_scaler(data)
        data_c = add_range_integrity(data, parent_sc)
        baseline = fit_logit(data, BASELINE_FEATURES)
        candidate = fit_logit(data_c, CANDIDATE_FEATURES)
        payload["pairings"][pair_id] = {
            "n_final_fit": int(len(data)),
            "parent_feature_scaler": scaler_snapshot(parent_sc),
            "baseline_model": model_snapshot(baseline, BASELINE_FEATURES),
            "candidate_model": model_snapshot(candidate, CANDIDATE_FEATURES),
            "final_range_integrity_coef": float(candidate.named_steps["lr"].coef_[0][-1]),
        }
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

    pair_data: dict[str, pd.DataFrame] = {}
    validation = {}
    dev_fit_snapshots = {}
    for pair_id, lower, parent in PAIRINGS:
        events = common.r2_events(prices, days, waves[parent], THRESHOLDS[lower], THRESHOLDS[parent])
        data = prepare(events)
        pair_data[pair_id] = data
        validation[pair_id], dev_fit_snapshots[pair_id] = validation_pair(data, pair_id, protocol)

    passed = bool(all(v["passed"] for v in validation.values()))
    receipt = {
        "schema_id": "factorlab_rmr_R2_range_integrity_v2_validation_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_range_boundary_parent_integrity_v2",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "DEV_window": {"start": "2015-01-05", "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_opened": False,
        "validation": validation,
        "DEV_fit_snapshots": dev_fit_snapshots,
        "validation_passed": passed,
        "final_refit_performed": passed,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not passed:
        print("R2_RANGE_INTEGRITY_VALIDATION_FAIL")
        return 2
    freeze = final_refit(pair_data, protocol)
    if not all(float(v["final_range_integrity_coef"]) > 0.0 for v in freeze["pairings"].values()):
        raise RuntimeError("R2 final refit range-integrity sign drifted")
    dump_json(args.freeze.resolve(), freeze)
    print("R2_RANGE_INTEGRITY_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
