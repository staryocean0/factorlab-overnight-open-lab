#!/usr/bin/env python3
"""Evaluate the frozen R1 parent-integrity v2 model on 2023-2025 holdout.

No fitting is performed. Frozen 2015-2022 baseline/candidate models are replayed
on the pre-authorized 2023-2025 within-program mechanism holdout. 2026 remains
sealed. This is not scientifically fresh and not a trading backtest.
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
from sklearn.metrics import brier_score_loss, log_loss

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_holdout_protocol_v1.json"
FREEZE = ROOT / "docs/governance/cloud_session_20260908_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_OUTPUT = ROOT / "docs/research/local_rmr_R1_parent_integrity_v2_holdout_receipt_v1.json"
EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
HOLDOUT_START = "2023-01-01"
HOLDOUT_END = "2025-12-31"
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


def validate_freeze() -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    freeze = load_json(FREEZE)
    if protocol["selected_candidate_id"] != "R1_PARENT_COMPOSITE_1D":
        raise RuntimeError("R1 holdout candidate drifted")
    if freeze["selected_candidate_id"] != protocol["selected_candidate_id"]:
        raise RuntimeError("R1 parameter/candidate mismatch")
    expected = freeze["parameter_bundle_sha256"]
    check = dict(freeze)
    check.pop("parameter_bundle_sha256")
    if json_digest(check) != expected:
        raise RuntimeError("R1 frozen parameter bundle digest mismatch")
    if expected != protocol["parameter_bundle_sha256"]:
        raise RuntimeError("R1 protocol parameter digest mismatch")
    if freeze["mechanistic_sign_precondition_passed"] is not True:
        raise RuntimeError("R1 mechanistic sign precondition failed before holdout")
    if protocol["source"]["all_2026_rows_open"] is not False:
        raise RuntimeError("R1 2026 seal drifted")
    return protocol, freeze


def read_source(path: Path) -> tuple[pd.DataFrame, dict]:
    actual = sha256(path)
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"R1 holdout source SHA mismatch: {actual}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("trading_day", "<=", HOLDOUT_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame = frame.loc[frame["symbol"].eq("000852.SH")].copy()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty or str(frame["trading_day"].max()) > HOLDOUT_END:
        raise RuntimeError("R1 holdout source boundary violated")
    if (frame["trading_day"] >= "2026-01-01").any():
        raise RuntimeError("R1 holdout read 2026")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("R1 holdout invalid close values")
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    return frame, {
        "sha256": actual,
        "rows_loaded_through_2025": int(len(frame)),
        "min_day": str(frame["trading_day"].min()),
        "max_day": str(frame["trading_day"].max()),
        "2026_rows_loaded": False,
    }


def resolved_binary(events: pd.DataFrame) -> pd.DataFrame:
    out = events.loc[events["outcome"].isin(["recovery", "failure"])].copy()
    out["y"] = out["outcome"].eq("recovery").astype(int)
    cols = ["day", "severity", "abs_drift", "overlap", "parent_eff", "y"]
    return out[cols].replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def standardize(x: np.ndarray, scaler: dict) -> np.ndarray:
    mean = np.asarray(scaler["mean"], dtype=float)
    scale = np.asarray(scaler["scale"], dtype=float)
    return (np.asarray(x, dtype=float) - mean) / scale


def frozen_predict(snapshot: dict, x: np.ndarray) -> np.ndarray:
    z = standardize(x, snapshot["scaler"])
    coef = np.asarray(snapshot["logistic"]["coef"], dtype=float)
    intercept = float(snapshot["logistic"]["intercept"])
    logits = z @ coef + intercept
    out = np.empty_like(logits, dtype=float)
    pos = logits >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-logits[pos]))
    expx = np.exp(logits[~pos])
    out[~pos] = expx / (1.0 + expx)
    return out


def add_frozen_integrity(frame: pd.DataFrame, parent_scaler: dict) -> pd.DataFrame:
    out = frame.copy()
    raw = out[["abs_drift", "overlap", "parent_eff"]].to_numpy(float)
    z = standardize(raw, parent_scaler)
    out["parent_integrity"] = (z[:, 0] - z[:, 1] + z[:, 2]) / 3.0
    return out


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "n": int(len(y)),
        "event_rate": float(np.mean(y)) if len(y) else None,
        "brier": float(brier_score_loss(y, p)) if len(y) else None,
        "log_loss": float(log_loss(y, p, labels=[0, 1])) if len(y) else None,
        "mean_probability": float(np.mean(p)) if len(y) else None,
    }


def evaluate_pair(data: pd.DataFrame, frozen_pair: dict) -> dict:
    hold = data.loc[(data["day"] >= HOLDOUT_START) & (data["day"] <= HOLDOUT_END)].copy()
    hold = add_frozen_integrity(hold, frozen_pair["parent_feature_scaler"])
    y = hold["y"].to_numpy(int)
    p_base = frozen_predict(frozen_pair["severity_baseline_model"], hold[["severity"]].to_numpy(float))
    p_cand = frozen_predict(frozen_pair["selected_candidate_model"], hold[["severity", "parent_integrity"]].to_numpy(float))
    pooled_base = metrics(y, p_base)
    pooled_cand = metrics(y, p_cand)
    annual = {}
    positive_years = 0
    min_year_ok = True
    for year in (2023, 2024, 2025):
        mask = hold["day"].str.startswith(str(year)).to_numpy()
        y_y = y[mask]
        b = metrics(y_y, p_base[mask])
        c = metrics(y_y, p_cand[mask])
        delta = None if not len(y_y) else float(b["brier"] - c["brier"])
        if delta is not None and delta > 0:
            positive_years += 1
        if len(y_y) < 50:
            min_year_ok = False
        annual[str(year)] = {"baseline": b, "candidate": c, "baseline_minus_candidate_brier": delta}
    gates = {
        "pooled_resolved_ge_200": len(hold) >= 200,
        "each_year_resolved_ge_50": min_year_ok,
        "pooled_brier_better": pooled_cand["brier"] < pooled_base["brier"],
        "pooled_logloss_better": pooled_cand["log_loss"] < pooled_base["log_loss"],
        "annual_brier_improvement_ge_2_of_3": positive_years >= 2,
    }
    return {
        "inventory": {"holdout_resolved": int(len(hold)), "by_year": {str(yv): int(hold["day"].str.startswith(str(yv)).sum()) for yv in (2023, 2024, 2025)}},
        "baseline": pooled_base,
        "candidate": pooled_cand,
        "baseline_minus_candidate_brier": float(pooled_base["brier"] - pooled_cand["brier"]),
        "baseline_minus_candidate_logloss": float(pooled_base["log_loss"] - pooled_cand["log_loss"]),
        "annual": annual,
        "gates": gates,
        "passed": all(gates.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    protocol, freeze = validate_freeze()
    frame, source_audit = read_source(args.parquet.resolve())
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = freeze["directional_change_thresholds"]
    vol_ref = float(freeze["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, float(thresholds[name])) for name in ("S1", "S2", "S3")}

    pair_results = {}
    for pair_id, lower, parent in PAIRINGS:
        events = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        data = resolved_binary(events)
        pair_results[pair_id] = evaluate_pair(data, freeze["pairings"][pair_id])

    overall = bool(freeze["mechanistic_sign_precondition_passed"] and all(v["passed"] for v in pair_results.values()))
    decision = "R1_parent_integrity_v2_holdout_confirmed_not_fresh" if overall else "R1_parent_integrity_v2_holdout_failed"
    receipt = {
        "schema_id": "factorlab_reversal_mean_reversion_R1_parent_integrity_v2_holdout_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "stage": "R1_2023_2025_mechanism_holdout_complete_pending_cloud_adjudication",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "parameter_freeze": str(FREEZE.relative_to(ROOT)),
        "parameter_bundle_sha256": freeze["parameter_bundle_sha256"],
        "selected_candidate_id": freeze["selected_candidate_id"],
        "source": source_audit,
        "holdout_window": {"start": HOLDOUT_START, "end": HOLDOUT_END},
        "pairings": pair_results,
        "mechanistic_sign_precondition_passed": freeze["mechanistic_sign_precondition_passed"],
        "decision": decision,
        "all_pairings_passed": overall,
        "refit_performed": False,
        "parameter_mutation_performed": False,
        "candidate_change_performed": False,
        "scale_or_threshold_search_performed": False,
        "calibration_performed": False,
        "binary_threshold_selection_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "scientifically_fresh": False,
        "production_authority": False,
    }
    dump_json(args.output.resolve(), receipt)
    print("R1_PARENT_INTEGRITY_V2_HOLDOUT", json.dumps({
        "decision": decision,
        "PAIR_A_passed": pair_results["PAIR_A"]["passed"],
        "PAIR_B_passed": pair_results["PAIR_B"]["passed"],
        "2026_rows_loaded": False,
        "refit_performed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
