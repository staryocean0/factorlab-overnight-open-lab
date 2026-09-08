#!/usr/bin/env python3
"""Frozen R1 parent-integrity v2 representation-selection runner.

Selection uses only CSI1000 through 2022-12-31. It reuses the promoted broad R1
causal event geometry and exact broad severity definition. The 2023-2025
mechanism holdout and all 2026 rows remain unopened.
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

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_selection_protocol_v1.json"
SCALE_CONTRACT = ROOT / "docs/governance/reversal_mean_reversion_stage1_scale_contract_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R1_parent_integrity_v2_selection_receipt_v1.json"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json"

EXPECTED_SOURCE_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2019-12-31"
STAB_START = "2020-01-01"
STAB_END = "2022-12-31"
CANDIDATE_ORDER = ("R1_PARENT_COMPOSITE_1D", "R1_PARENT_ORIGINAL_3D")
PAIRINGS = (
    ("PAIR_A", "S1", "S2"),
    ("PAIR_B", "S2", "S3"),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def validate_contracts() -> None:
    p = load_json(PROTOCOL)
    s = load_json(SCALE_CONTRACT)
    if p["research_identity"] != "rmr_cross_scale_pullback_parent_integrity_v2":
        raise RuntimeError("R1 specialist identity drifted")
    if p["stage"] != "results_blind_specialist_representation_selection_before_2023_2025_holdout_open":
        raise RuntimeError("R1 specialist selection stage drifted")
    if p["source"]["sha256"] != EXPECTED_SOURCE_SHA:
        raise RuntimeError("R1 specialist source identity drifted")
    if p["source"]["holdout_2023_2025_open_for_selection"] is not False:
        raise RuntimeError("R1 specialist holdout unexpectedly open")
    if tuple(c["candidate_id"] for c in p["candidate_ladder"]) != CANDIDATE_ORDER:
        raise RuntimeError("R1 candidate ladder drifted")
    if p["event_and_outcome"]["severity"] != "abs(lower_wave_move)/DEV_median_rvol20_exact_broad_R1_definition":
        raise RuntimeError("R1 broad-compatible severity drifted")
    if s["first_passage_horizon"]["maximum_observed_1m_bars"] != 1200:
        raise RuntimeError("R1 common horizon drifted")


def read_source(path: Path) -> tuple[pd.DataFrame, dict]:
    actual = sha256(path)
    if actual != EXPECTED_SOURCE_SHA:
        raise RuntimeError(f"R1 source SHA mismatch: {actual}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("trading_day", "<=", STAB_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame = frame.loc[frame["symbol"].eq(SYMBOL)].copy()
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty:
        raise RuntimeError("R1 source empty")
    if str(frame["trading_day"].max()) > STAB_END:
        raise RuntimeError("R1 selection crossed 2022 boundary")
    if (frame["trading_day"] >= "2023-01-01").any():
        raise RuntimeError("R1 selection read 2023-2025 holdout")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("R1 invalid close values")
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    return frame, {
        "sha256": actual,
        "rows_loaded": int(len(frame)),
        "min_day": str(frame["trading_day"].min()),
        "max_day": str(frame["trading_day"].max()),
        "rows_2023_or_later": 0,
        "holdout_2023_2025_opened": False,
        "all_2026_rows_opened": False,
    }


def frozen_scales(frame: pd.DataFrame) -> tuple[float, dict[str, float]]:
    temp = frame.copy()
    temp["clock"] = temp["timestamp"].astype(str).str[11:16]
    daily = temp.loc[temp["clock"].eq("15:00"), ["trading_day", "close"]].drop_duplicates(
        "trading_day", keep="last"
    ).sort_values("trading_day")
    daily["ret"] = daily["close"].pct_change(fill_method=None)
    daily["rv20"] = daily["ret"].rolling(20, min_periods=20).std().shift(1)
    vol_ref = float(daily.loc[daily["trading_day"] <= DEV_END, "rv20"].dropna().median())
    if not np.isfinite(vol_ref) or vol_ref <= 0:
        raise RuntimeError("R1 invalid DEV median rvol20")
    return vol_ref, {"S1": 0.25 * vol_ref, "S2": 0.50 * vol_ref, "S3": 1.00 * vol_ref}


def resolved_binary(events: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return events.copy()
    out = events.loc[events["outcome"].isin(["recovery", "failure"])].copy()
    out["y"] = out["outcome"].eq("recovery").astype(int)
    cols = ["day", "severity", "abs_drift", "overlap", "parent_eff", "y"]
    return out[cols].replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def fit_probability(frame: pd.DataFrame, features: list[str]) -> Pipeline:
    if len(frame) < 30 or frame["y"].nunique() < 2:
        raise RuntimeError("R1 insufficient fit sample")
    model = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000)),
    ])
    model.fit(frame[features].to_numpy(float), frame["y"].to_numpy(int))
    return model


def model_snapshot(model: Pipeline, features: list[str]) -> dict:
    sc: StandardScaler = model.named_steps["sc"]
    lr: LogisticRegression = model.named_steps["lr"]
    return {
        "features": list(features),
        "scaler": {
            "mean": [float(x) for x in sc.mean_],
            "scale": [float(x) for x in sc.scale_],
            "var": [float(x) for x in sc.var_],
        },
        "logistic": {
            "coef": [float(x) for x in lr.coef_[0]],
            "intercept": float(lr.intercept_[0]),
            "classes": [int(x) for x in lr.classes_],
        },
    }


def score(model: Pipeline, frame: pd.DataFrame, features: list[str]) -> dict:
    if frame.empty:
        return {"status": "evidence_insufficient", "n": 0}
    y = frame["y"].to_numpy(int)
    p = model.predict_proba(frame[features].to_numpy(float))[:, 1]
    return {
        "status": "scored",
        "n": int(len(frame)),
        "event_rate": float(np.mean(y)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "mean_probability": float(np.mean(p)),
    }


def fit_parent_scaler(train: pd.DataFrame) -> StandardScaler:
    sc = StandardScaler()
    sc.fit(train[["abs_drift", "overlap", "parent_eff"]].to_numpy(float))
    return sc


def add_composite(frame: pd.DataFrame, sc: StandardScaler) -> pd.DataFrame:
    out = frame.copy()
    z = sc.transform(out[["abs_drift", "overlap", "parent_eff"]].to_numpy(float))
    out["parent_integrity"] = (z[:, 0] - z[:, 1] + z[:, 2]) / 3.0
    return out


def parent_scaler_snapshot(sc: StandardScaler) -> dict:
    return {
        "features": ["abs_drift", "overlap", "parent_eff"],
        "orientation": [1, -1, 1],
        "mean": [float(x) for x in sc.mean_],
        "scale": [float(x) for x in sc.scale_],
        "var": [float(x) for x in sc.var_],
    }


def evaluate_candidate(pair_data: dict[str, pd.DataFrame], candidate_id: str) -> dict:
    result = {"candidate_id": candidate_id, "pairings": {}, "eligible": True}
    for pair_id, data in pair_data.items():
        train = data.loc[data["day"] <= DEV_END].copy()
        stability = data.loc[(data["day"] >= STAB_START) & (data["day"] <= STAB_END)].copy()
        baseline_features = ["severity"]
        baseline = fit_probability(train, baseline_features)

        parent_scaler = None
        if candidate_id == "R1_PARENT_COMPOSITE_1D":
            parent_scaler = fit_parent_scaler(train)
            train_c = add_composite(train, parent_scaler)
            stability_c = add_composite(stability, parent_scaler)
            candidate_features = ["severity", "parent_integrity"]
        elif candidate_id == "R1_PARENT_ORIGINAL_3D":
            train_c = train
            stability_c = stability
            candidate_features = ["severity", "abs_drift", "overlap", "parent_eff"]
        else:
            raise RuntimeError(f"unknown R1 candidate {candidate_id}")

        candidate = fit_probability(train_c, candidate_features)
        pooled_base = score(baseline, stability, baseline_features)
        pooled_cand = score(candidate, stability_c, candidate_features)
        annual = {}
        annual_improvements = 0
        annual_min_ok = True
        for year in (2020, 2021, 2022):
            mask = stability["day"].str.startswith(str(year))
            ybase = score(baseline, stability.loc[mask], baseline_features)
            ycand = score(candidate, stability_c.loc[mask], candidate_features)
            delta = None
            if ybase.get("status") == "scored" and ycand.get("status") == "scored":
                delta = float(ybase["brier"] - ycand["brier"])
                if delta > 0:
                    annual_improvements += 1
            if int(ybase.get("n", 0)) < 50:
                annual_min_ok = False
            annual[str(year)] = {"baseline": ybase, "candidate": ycand, "baseline_minus_candidate_brier": delta}

        gates = {
            "pooled_stability_resolved_ge_200": int(len(stability)) >= 200,
            "each_year_resolved_ge_50": annual_min_ok,
            "pooled_brier_better": pooled_cand["brier"] < pooled_base["brier"],
            "pooled_logloss_better": pooled_cand["log_loss"] < pooled_base["log_loss"],
            "annual_brier_improvement_ge_2_of_3": annual_improvements >= 2,
        }
        eligible = all(gates.values())
        result["eligible"] = bool(result["eligible"] and eligible)
        result["pairings"][pair_id] = {
            "inventory": {"n_dev": int(len(train)), "n_stability": int(len(stability))},
            "baseline": pooled_base,
            "candidate": pooled_cand,
            "baseline_minus_candidate_brier": float(pooled_base["brier"] - pooled_cand["brier"]),
            "baseline_minus_candidate_logloss": float(pooled_base["log_loss"] - pooled_cand["log_loss"]),
            "annual": annual,
            "gates": gates,
            "eligible": eligible,
            "parent_feature_scaler": parent_scaler_snapshot(parent_scaler) if parent_scaler is not None else None,
            "selection_fit_candidate_model": model_snapshot(candidate, candidate_features),
        }
    return result


def refit_selected(pair_data: dict[str, pd.DataFrame], selected: str, thresholds: dict[str, float], vol_ref: float) -> dict:
    freeze = {
        "schema_id": "factorlab_reversal_mean_reversion_R1_parent_integrity_v2_parameter_freeze@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "selected_candidate_id": selected,
        "source_sha256": EXPECTED_SOURCE_SHA,
        "consumed_refit_window": {"start": "2015-01-05", "end": STAB_END},
        "severity_denominator": "DEV_median_rvol20",
        "DEV_median_rvol20": float(vol_ref),
        "directional_change_thresholds": {k: float(v) for k, v in thresholds.items()},
        "holdout_window": {"start": "2023-01-01", "end": "2025-12-31", "opened_during_refit": False},
        "pairings": {},
        "holdout_gate": {
            "minimum_pooled_resolved_each_pairing": 200,
            "minimum_each_2023_2024_2025_resolved_each_pairing": 50,
            "candidate_pooled_Brier_strictly_lower_than_frozen_severity_baseline": True,
            "candidate_pooled_logloss_strictly_lower_than_frozen_severity_baseline": True,
            "annual_Brier_improvement_positive_min_years_each_pairing": 2,
            "both_pairings_required": True,
            "scientifically_fresh": False,
        },
        "production_authority": False,
    }
    sign_precondition = True
    for pair_id, data in pair_data.items():
        baseline = fit_probability(data, ["severity"])
        parent_scaler = None
        if selected == "R1_PARENT_COMPOSITE_1D":
            parent_scaler = fit_parent_scaler(data)
            fit_data = add_composite(data, parent_scaler)
            features = ["severity", "parent_integrity"]
        else:
            fit_data = data
            features = ["severity", "abs_drift", "overlap", "parent_eff"]
        candidate = fit_probability(fit_data, features)
        snap = model_snapshot(candidate, features)
        if selected == "R1_PARENT_COMPOSITE_1D":
            integrity_coef = snap["logistic"]["coef"][1]
            sign_precondition = bool(sign_precondition and integrity_coef > 0)
        freeze["pairings"][pair_id] = {
            "n_consumed_resolved": int(len(data)),
            "parent_feature_scaler": parent_scaler_snapshot(parent_scaler) if parent_scaler is not None else None,
            "severity_baseline_model": model_snapshot(baseline, ["severity"]),
            "selected_candidate_model": snap,
        }
    freeze["mechanistic_sign_precondition_passed"] = sign_precondition
    freeze["parameter_bundle_sha256"] = json_digest(freeze)
    return freeze


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    ap.add_argument("--parameter-freeze", type=Path, default=DEFAULT_FREEZE)
    args = ap.parse_args()

    validate_contracts()
    frame, source_audit = read_source(args.parquet.resolve())
    vol_ref, thresholds = frozen_scales(frame)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    waves = {name: common.detect_waves(prices, threshold) for name, threshold in thresholds.items()}

    pair_data: dict[str, pd.DataFrame] = {}
    pair_inventory = {}
    for pair_id, lower, parent in PAIRINGS:
        events = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        binary = resolved_binary(events)
        pair_data[pair_id] = binary
        pair_inventory[pair_id] = {
            "lower": lower,
            "parent": parent,
            "resolved_through_2022": int(len(binary)),
            "DEV": int((binary["day"] <= DEV_END).sum()),
            "STABILITY": int(((binary["day"] >= STAB_START) & (binary["day"] <= STAB_END)).sum()),
        }

    attempts = []
    selected = None
    for candidate_id in CANDIDATE_ORDER:
        attempt = evaluate_candidate(pair_data, candidate_id)
        attempts.append(attempt)
        if attempt["eligible"]:
            selected = candidate_id
            break

    parameter_freeze = None
    if selected is not None:
        parameter_freeze = refit_selected(pair_data, selected, thresholds, vol_ref)
        dump_json(args.parameter_freeze.resolve(), parameter_freeze)

    receipt = {
        "schema_id": "factorlab_reversal_mean_reversion_R1_parent_integrity_v2_selection_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "stage": "R1_specialist_representation_selection_complete_pending_cloud_adjudication",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source": source_audit,
        "DEV_median_rvol20": float(vol_ref),
        "directional_change_thresholds": {k: float(v) for k, v in thresholds.items()},
        "severity_definition": "abs(lower_wave_move)/DEV_median_rvol20",
        "pair_inventory": pair_inventory,
        "candidate_order": list(CANDIDATE_ORDER),
        "attempts": attempts,
        "selected_candidate_id": selected,
        "selection_rule": "first_eligible_in_complexity_ladder",
        "parameter_freeze_written": parameter_freeze is not None,
        "parameter_bundle_sha256": parameter_freeze.get("parameter_bundle_sha256") if parameter_freeze else None,
        "mechanistic_sign_precondition_passed": parameter_freeze.get("mechanistic_sign_precondition_passed") if parameter_freeze else None,
        "holdout_2023_2025_opened": False,
        "all_2026_rows_opened": False,
        "candidate_addition_or_reordering_performed": False,
        "scale_or_threshold_search_performed": False,
        "model_or_hyperparameter_search_performed": False,
        "calibration_performed": False,
        "binary_threshold_selection_performed": False,
        "trading_return_used": False,
        "scientifically_fresh": False,
        "production_authority": False,
    }
    dump_json(args.receipt.resolve(), receipt)
    print("R1_PARENT_INTEGRITY_V2_SELECTION", json.dumps({
        "selected_candidate_id": selected,
        "attempted": [a["candidate_id"] for a in attempts],
        "holdout_2023_2025_opened": False,
        "mechanistic_sign_precondition_passed": receipt["mechanistic_sign_precondition_passed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
