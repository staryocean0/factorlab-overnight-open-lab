#!/usr/bin/env python3
"""R1 economic translation v3: direct realized-net-return modeling on DEV/VALIDATION.

V3 uses the same R1 event geometry and fixed 10bp execution as v1/v2, but the
model target is realized net return (including censored horizon exits).  The
baseline uses severity + causal payoff geometry; the candidate adds only the
frozen parent-integrity concept.  This runner cannot read the 2026 BLACKBOX.
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
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_R1_economic_translation_v1 as econ1
import run_rmr_R1_economic_translation_v2 as econ2
import run_rmr_R1_parent_integrity_v2_selection as model_utils
import run_rmr_stage1_common_probe as common

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_economic_translation_v3_protocol.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R1_economic_translation_v3_validation_receipt.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R1_economic_translation_v3_parameter_freeze.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
PAIRINGS = (("PAIR_A", "S1", "S2"), ("PAIR_B", "S2", "S3"))
BASE_FEATURES = ["severity", "recovery_gross", "failure_gross"]
CAND_FEATURES = ["severity", "recovery_gross", "failure_gross", "parent_integrity"]
RIDGE_ALPHA = 1.0


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
    if p["research_identity"] != "rmr_R1_parent_integrity_economic_translation_v3":
        raise RuntimeError("economic v3 identity drifted")
    fam = p["model_family"]
    if fam["baseline_features"] != BASE_FEATURES or fam["candidate_features"] != CAND_FEATURES:
        raise RuntimeError("economic v3 feature family drifted")
    if float(fam["ridge_alpha"]) != RIDGE_ALPHA or fam["hyperparameter_search"] is not False:
        raise RuntimeError("economic v3 ridge contract drifted")
    if p["strategy_rule"]["trade_if"] != [
        "candidate_predicted_net_return_strictly_greater_than_zero",
        "candidate_predicted_net_return_strictly_greater_than_baseline_predicted_net_return",
    ]:
        raise RuntimeError("economic v3 strategy rule drifted")
    if p["VALIDATION"]["gate_change_from_v1_v2"] is not False:
        raise RuntimeError("economic v3 validation gates drifted")
    if float(p["cost_model"]["primary_round_trip_bps"]) != 10.0:
        raise RuntimeError("economic v3 cost drifted")
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
        raise RuntimeError("economic v3 validation boundary drifted")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("economic v3 DEV/VALIDATION runner read blackbox")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("economic v3 invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def fit_return_model(frame: pd.DataFrame, features: list[str]) -> Pipeline:
    if len(frame) < 30:
        raise RuntimeError("economic v3 insufficient DEV sample")
    model = Pipeline([
        ("sc", StandardScaler()),
        ("ridge", Ridge(alpha=RIDGE_ALPHA)),
    ])
    model.fit(frame[features].to_numpy(float), frame["net_return"].to_numpy(float))
    return model


def return_model_snapshot(model: Pipeline, features: list[str]) -> dict:
    sc: StandardScaler = model.named_steps["sc"]
    ridge: Ridge = model.named_steps["ridge"]
    return {
        "features": list(features),
        "scaler": {
            "mean": [float(x) for x in sc.mean_],
            "scale": [float(x) for x in sc.scale_],
            "var": [float(x) for x in sc.var_],
        },
        "ridge": {
            "alpha": float(ridge.alpha),
            "coef": [float(x) for x in np.asarray(ridge.coef_).reshape(-1)],
            "intercept": float(ridge.intercept_),
        },
    }


def fit_bundle(events: pd.DataFrame, end_day: str) -> dict:
    train = events.loc[events["day"] <= end_day].copy()
    parent_sc = model_utils.fit_parent_scaler(train)
    train_c = model_utils.add_composite(train, parent_sc)
    baseline = fit_return_model(train_c, BASE_FEATURES)
    candidate = fit_return_model(train_c, CAND_FEATURES)
    return {
        "parent_scaler_object": parent_sc,
        "baseline_object": baseline,
        "candidate_object": candidate,
        "snapshot": {
            "n_fit_events": int(len(train)),
            "parent_feature_scaler": model_utils.parent_scaler_snapshot(parent_sc),
            "baseline_return_model": return_model_snapshot(baseline, BASE_FEATURES),
            "candidate_return_model": return_model_snapshot(candidate, CAND_FEATURES),
        },
    }


def add_predictions(events: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    out = model_utils.add_composite(events, bundle["parent_scaler_object"])
    pred_base = bundle["baseline_object"].predict(out[BASE_FEATURES].to_numpy(float))
    pred_cand = bundle["candidate_object"].predict(out[CAND_FEATURES].to_numpy(float))
    out["predicted_baseline_net"] = pred_base
    out["predicted_candidate_net"] = pred_cand
    out["selected_trade"] = (pred_cand > 0.0) & (pred_cand > pred_base)
    return out


def validation_pair(events: pd.DataFrame, dev_bundle: dict, pair_id: str, protocol: dict) -> dict:
    scored = add_predictions(events, dev_bundle)
    val = scored.loc[scored["day"].between(VAL_START, VAL_END)].copy()
    all_stats = econ1.stats(val)
    selected = val.loc[val["selected_trade"]].copy()
    sel_stats = econ1.stats(selected)
    annual = {}
    positive_years = 0
    for year in range(2021, 2026):
        ys = econ1.stats(selected.loc[selected["day"].str.startswith(str(year))])
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
        "schema_id": "factorlab_rmr_R1_economic_translation_v3_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R1_parent_integrity_economic_translation_v3",
        "parent_mechanism_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "strategy_candidate_id": "R1_DIRECT_RETURN_EDGE_POSITIVE_NEXT_BAR_10BP",
        "historical_source_sha256": EXPECTED_SOURCE_SHA,
        "final_refit_window": {"start": "2015-01-05", "end": VAL_END},
        "blackbox_window": {"start": "2026-01-05", "end": "2026-08-21"},
        "blackbox_used_in_fit": False,
        "DEV_median_rvol20": float(protocol["model_constants"]["DEV_median_rvol20"]),
        "directional_change_thresholds": protocol["model_constants"]["directional_change_thresholds"],
        "round_trip_cost_bps": 10.0,
        "ridge_alpha": RIDGE_ALPHA,
        "baseline_features": BASE_FEATURES,
        "candidate_features": CAND_FEATURES,
        "trade_rule": "candidate_predicted_net_gt_0_and_gt_baseline_predicted_net",
        "pairings": {},
        "blackbox_gate": protocol["BLACKBOX"]["gate_each_pairing"],
        "public_blackbox_output_only": ["PASS", "FAIL", "INSUFFICIENT"],
        "production_authority": False,
    }
    for pair_id, events in pair_events.items():
        payload["pairings"][pair_id] = fit_bundle(events, VAL_END)["snapshot"]
    payload["parameter_bundle_sha256"] = json_digest(dict(payload))
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
    thresholds = {k: float(v) for k, v in protocol["model_constants"]["directional_change_thresholds"].items()}
    vol_ref = float(protocol["model_constants"]["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, thresholds[name]) for name in ("S1", "S2", "S3")}

    pair_events: dict[str, pd.DataFrame] = {}
    validation = {}
    dev_model_snapshots = {}
    for pair_id, lower, parent in PAIRINGS:
        events = econ2.trade_events(prices, days, waves[lower], waves[parent], vol_ref)
        pair_events[pair_id] = events
        dev_bundle = fit_bundle(events, DEV_END)
        dev_model_snapshots[pair_id] = dev_bundle["snapshot"]
        validation[pair_id] = validation_pair(events, dev_bundle, pair_id, protocol)

    passed = bool(all(v["passed"] for v in validation.values()))
    receipt = {
        "schema_id": "factorlab_rmr_R1_economic_translation_v3_validation_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R1_parent_integrity_economic_translation_v3",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "DEV_window": {"start": "2015-01-05", "end": DEV_END},
        "VALIDATION_window": {"start": VAL_START, "end": VAL_END},
        "BLACKBOX_opened": False,
        "round_trip_cost_bps": 10.0,
        "ridge_alpha": RIDGE_ALPHA,
        "validation": validation,
        "DEV_model_snapshots": dev_model_snapshots,
        "validation_passed": passed,
        "final_refit_performed": passed,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    if not passed:
        print("R1_ECONOMIC_TRANSLATION_V3_VALIDATION_FAIL")
        return 2
    dump_json(args.freeze.resolve(), final_freeze(pair_events, protocol))
    print("R1_ECONOMIC_TRANSLATION_V3_VALIDATION_PASS_FINAL_REFIT_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
