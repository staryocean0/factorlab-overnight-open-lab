#!/usr/bin/env python3
"""Frozen R1 specialist representation-selection runner.

Reads CSI1000 only through 2022-12-31.  It evaluates the simple composite first;
the original three-parent-feature candidate is evaluated only if the composite
fails the complete two-pairing mechanism gate.  2023-2025 is never read here.
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

PROTOCOL = ROOT / "docs/governance/rmr_R1_parent_integrity_v2_representation_protocol_v1.json"
PREANALYSIS = ROOT / "docs/research/rmr_R1_parent_integrity_v2_representation_preanalysis_20260908.md"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/research/local_rmr_R1_parent_integrity_v2_representation_receipt_v1.json"
BUNDLE = ROOT / "docs/governance/local_rmr_R1_parent_integrity_v2_selected_bundle_v1.json"
USAGE = ROOT / "docs/governance/local_rmr_R1_parent_integrity_v2_representation_data_usage_v1.json"

EXPECTED_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2019-12-31"
STAB_START = "2020-01-01"
STAB_END = "2022-12-31"
PAIRINGS = (("S1", "S2"), ("S2", "S3"))
PARENT = ("abs_drift", "overlap", "parent_eff")
CANDIDATE_ORDER = ("composite_integrity_plus_severity", "original_three_parent_plus_severity")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_head() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def validate_protocol() -> dict:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if p["research_identity"] != "rmr_cross_scale_pullback_parent_integrity_v2":
        raise RuntimeError("R1 specialist identity drifted")
    if p["stage"] != "results_blind_representation_selection_freeze_before_2023_2025_holdout":
        raise RuntimeError("R1 representation stage drifted")
    if p["source"]["holdout_2023_2025_open_authorized"] is not False:
        raise RuntimeError("R1 holdout unexpectedly authorized")
    if tuple(x["id"] for x in p["candidate_ladder"]) != CANDIDATE_ORDER:
        raise RuntimeError("R1 candidate order drifted")
    return p


def read_source(path: Path) -> tuple[pd.DataFrame, dict]:
    actual = sha256(path)
    if actual != EXPECTED_SHA:
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
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    frame["_idx"] = np.arange(len(frame), dtype=int)
    if frame.empty or str(frame["trading_day"].max()) > STAB_END:
        raise RuntimeError("R1 representation read crossed 2022 boundary")
    if not np.isfinite(frame["close"].to_numpy(float)).all() or (frame["close"].to_numpy(float) <= 0).any():
        raise RuntimeError("invalid prices")
    return frame, {
        "path": str(path),
        "sha256": actual,
        "rows_loaded": int(len(frame)),
        "min_day": str(frame["trading_day"].min()),
        "max_day": str(frame["trading_day"].max()),
        "rows_2023_or_later": 0,
        "holdout_2023_2025_opened": False,
    }


def thresholds(frame: pd.DataFrame) -> tuple[float, dict[str, float]]:
    temp = frame.copy()
    temp["clock"] = temp["timestamp"].astype(str).str[11:16]
    daily = temp.loc[temp["clock"].eq("15:00"), ["trading_day", "close"]].drop_duplicates("trading_day", keep="last").sort_values("trading_day")
    daily["ret"] = daily["close"].pct_change(fill_method=None)
    daily["rv20"] = daily["ret"].rolling(20, min_periods=20).std().shift(1)
    ref = float(daily.loc[daily["trading_day"] <= DEV_END, "rv20"].dropna().median())
    if not np.isfinite(ref) or ref <= 0:
        raise RuntimeError("invalid DEV volatility reference")
    return ref, {"S1": 0.25 * ref, "S2": 0.50 * ref, "S3": 1.00 * ref}


def binary_events(raw: pd.DataFrame) -> pd.DataFrame:
    data = raw.loc[raw["outcome"].isin(["recovery", "failure"])].copy()
    data["y"] = data["outcome"].eq("recovery").astype(int)
    cols = ["day", "severity", "abs_drift", "overlap", "parent_eff", "y"]
    return data[cols].replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def fit_parent_standardizer(train: pd.DataFrame) -> dict:
    mean = {c: float(train[c].mean()) for c in PARENT}
    raw_scale = {c: float(train[c].std(ddof=0)) for c in PARENT}
    if any(not np.isfinite(raw_scale[c]) for c in PARENT):
        raise RuntimeError("invalid parent-feature standardization")
    # Match StandardScaler's constant-feature semantics: a zero-variance column
    # carries no standardized information, so use scale=1 and z=(x-mean)=0.
    zero_variance = [c for c in PARENT if raw_scale[c] == 0.0]
    scale = {c: (1.0 if raw_scale[c] == 0.0 else raw_scale[c]) for c in PARENT}
    return {"mean": mean, "scale": scale, "zero_variance_features": zero_variance}


def add_composite(data: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = data.copy()
    zd = (out["abs_drift"] - params["mean"]["abs_drift"]) / params["scale"]["abs_drift"]
    zo = (out["overlap"] - params["mean"]["overlap"]) / params["scale"]["overlap"]
    ze = (out["parent_eff"] - params["mean"]["parent_eff"]) / params["scale"]["parent_eff"]
    out["parent_integrity"] = (zd - zo + ze) / 3.0
    return out


def fit_model(data: pd.DataFrame, features: list[str]) -> Pipeline | None:
    clean = data.dropna(subset=features + ["y"]).copy()
    if len(clean) < 30 or clean["y"].nunique() < 2:
        return None
    m = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000, class_weight=None)),
    ])
    m.fit(clean[features].to_numpy(float), clean["y"].to_numpy(int))
    return m


def score_model(model: Pipeline | None, data: pd.DataFrame, features: list[str]) -> dict:
    clean = data.dropna(subset=features + ["y"]).copy()
    if model is None or clean.empty:
        return {"status": "evidence_insufficient", "n": int(len(clean))}
    y = clean["y"].to_numpy(int)
    p = model.predict_proba(clean[features].to_numpy(float))[:, 1]
    return {
        "status": "scored",
        "n": int(len(clean)),
        "event_rate": float(np.mean(y)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "mean_probability": float(np.mean(p)),
    }


def model_params(model: Pipeline, features: list[str]) -> dict:
    sc = model.named_steps["sc"]
    lr = model.named_steps["lr"]
    return {
        "features": list(features),
        "scaler_mean": [float(x) for x in sc.mean_],
        "scaler_scale": [float(x) for x in sc.scale_],
        "logistic_coef": [float(x) for x in lr.coef_[0]],
        "logistic_intercept": float(lr.intercept_[0]),
    }


def direction_value(model: Pipeline, candidate_id: str) -> float:
    coef = model.named_steps["lr"].coef_[0]
    if candidate_id == "composite_integrity_plus_severity":
        return float(coef[1])
    return float(coef[1] - coef[2] + coef[3])


def pairing_evaluation(raw: pd.DataFrame, candidate_id: str) -> dict:
    data = binary_events(raw)
    dev = data.loc[data["day"] <= DEV_END].copy()
    stab = data.loc[(data["day"] >= STAB_START) & (data["day"] <= STAB_END)].copy()
    parent_std = None
    if candidate_id == "composite_integrity_plus_severity":
        parent_std = fit_parent_standardizer(dev)
        dev = add_composite(dev, parent_std)
        stab = add_composite(stab, parent_std)
        candidate_features = ["severity", "parent_integrity"]
    else:
        candidate_features = ["severity", "abs_drift", "overlap", "parent_eff"]
    baseline_features = ["severity"]
    baseline = fit_model(dev, baseline_features)
    candidate = fit_model(dev, candidate_features)
    pooled_b = score_model(baseline, stab, baseline_features)
    pooled_c = score_model(candidate, stab, candidate_features)
    annual: dict[str, dict] = {}
    annual_counts: dict[str, int] = {}
    annual_improvements = 0
    for year in (2020, 2021, 2022):
        yp = stab.loc[stab["day"].str.startswith(str(year))].copy()
        b = score_model(baseline, yp, baseline_features)
        c = score_model(candidate, yp, candidate_features)
        annual[str(year)] = {"baseline": b, "candidate": c}
        annual_counts[str(year)] = int(len(yp))
        if b.get("status") == "scored" and c.get("status") == "scored" and c["brier"] < b["brier"]:
            annual_improvements += 1
    direction = None if candidate is None else direction_value(candidate, candidate_id)
    gates = {
        "minimum_200_stability": int(len(stab)) >= 200,
        "minimum_50_each_year": all(v >= 50 for v in annual_counts.values()),
        "pooled_brier_strictly_lower": bool(pooled_b.get("status") == "scored" and pooled_c.get("status") == "scored" and pooled_c["brier"] < pooled_b["brier"]),
        "pooled_logloss_strictly_lower": bool(pooled_b.get("status") == "scored" and pooled_c.get("status") == "scored" and pooled_c["log_loss"] < pooled_b["log_loss"]),
        "annual_brier_improvement_at_least_2_of_3": annual_improvements >= 2,
        "positive_integrity_direction": bool(direction is not None and direction > 0.0),
    }
    return {
        "inventory": {"dev_resolved": int(len(dev)), "stability_resolved": int(len(stab)), "stability_by_year": annual_counts},
        "parent_standardization_DEV": parent_std,
        "candidate_features": candidate_features,
        "pooled_stability": {"baseline": pooled_b, "candidate": pooled_c},
        "annual": annual,
        "integrity_direction_value": direction,
        "gates": gates,
        "passed": bool(all(gates.values())),
    }


def freeze_selected(selected: str, raw_by_pairing: dict[str, pd.DataFrame], th: dict[str, float], source: dict) -> dict:
    pairings: dict[str, dict] = {}
    for key, raw in raw_by_pairing.items():
        data = binary_events(raw)
        train = data.loc[data["day"] <= STAB_END].copy()
        parent_std = None
        if selected == "composite_integrity_plus_severity":
            parent_std = fit_parent_standardizer(train)
            train = add_composite(train, parent_std)
            features = ["severity", "parent_integrity"]
        else:
            features = ["severity", "abs_drift", "overlap", "parent_eff"]
        candidate = fit_model(train, features)
        baseline = fit_model(train, ["severity"])
        if candidate is None or baseline is None:
            raise RuntimeError("selected R1 candidate could not refit on full consumed material")
        pairings[key] = {
            "n_fit": int(len(train)),
            "parent_standardization_full_2015_2022": parent_std,
            "candidate_model": model_params(candidate, features),
            "severity_baseline_model": model_params(baseline, ["severity"]),
            "integrity_direction_value": direction_value(candidate, selected),
        }
    core = {
        "schema_id": "factorlab_rmr_R1_parent_integrity_v2_selected_bundle@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "selected_candidate_id": selected,
        "source": source,
        "directional_change_thresholds": {k: float(v) for k, v in th.items()},
        "pairings": pairings,
        "fit_material": "2015-01-05_to_2022-12-31_consumed_not_fresh",
        "holdout_2023_2025_opened": False,
        "production_authority": False,
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    core["bundle_digest_sha256"] = hashlib.sha256(canonical).hexdigest()
    return core


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, default=OUT)
    ap.add_argument("--bundle-output", type=Path, default=BUNDLE)
    ap.add_argument("--usage-output", type=Path, default=USAGE)
    args = ap.parse_args()

    validate_protocol()
    frame, source = read_source(args.parquet.resolve())
    vol_ref, th = thresholds(frame)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    waves = {name: common.detect_waves(prices, threshold) for name, threshold in th.items()}
    raw_by_pairing: dict[str, pd.DataFrame] = {}
    for lower, parent in PAIRINGS:
        key = f"{lower}_inside_{parent}"
        raw_by_pairing[key] = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)

    attempts: list[dict] = []
    selected = None
    for candidate_id in CANDIDATE_ORDER:
        pairing_results = {key: pairing_evaluation(raw, candidate_id) for key, raw in raw_by_pairing.items()}
        passed = bool(all(x["passed"] for x in pairing_results.values()))
        attempts.append({"candidate_id": candidate_id, "pairings": pairing_results, "eligible": passed})
        if passed:
            selected = candidate_id
            break

    bundle = None
    if selected is not None:
        bundle = freeze_selected(selected, raw_by_pairing, th, source)
        dump(args.bundle_output.resolve(), bundle)

    receipt = {
        "schema_id": "factorlab_rmr_R1_parent_integrity_v2_representation_receipt@1.0",
        "session_date": "2026-09-08",
        "program_identity": "broad_reversal_mean_reversion_discovery_program_v1",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "stage": "representation_selection_complete_pending_cloud_review",
        "code_commit": git_head(),
        "runner_sha256": sha256(Path(__file__)),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source": source,
        "vol_ref_dev_median_rvol20": float(vol_ref),
        "directional_change_thresholds": {k: float(v) for k, v in th.items()},
        "wave_counts": {k: int(len(v)) for k, v in waves.items()},
        "candidate_order": list(CANDIDATE_ORDER),
        "candidate_attempts": attempts,
        "selected_candidate_id": selected,
        "selection_status": "selected_pending_cloud_freeze" if selected else "family_closed_no_eligible_representation",
        "selected_bundle_digest_sha256": None if bundle is None else bundle["bundle_digest_sha256"],
        "original_three_evaluated": any(x["candidate_id"] == "original_three_parent_plus_severity" for x in attempts),
        "holdout_2023_2025_opened": False,
        "2026_rows_loaded": False,
        "composite_weight_fit_performed": False,
        "parent_feature_search_performed": False,
        "wave_scale_search_performed": False,
        "hyperparameter_search_performed": False,
        "trading_return_used": False,
        "production_authority": False,
        "scientifically_fresh": False,
    }
    dump(args.output.resolve(), receipt)
    usage = {
        "schema_id": "factorlab_rmr_R1_parent_integrity_v2_representation_data_usage@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "opened": {
            "CSI1000_2015-01-05_to_2019-12-31": "development_material",
            "CSI1000_2020-01-01_to_2022-12-31": "chronological_stability_consumed_not_fresh"
        },
        "sealed_or_unopened": {
            "CSI1000_2023-01-01_to_2025-12-31_mechanism_holdout": True,
            "all_2026_rows": True
        },
        "aggregate_outputs_only": True,
        "raw_rows_written_to_repo": False,
        "trading_return_used": False,
        "production_authority": False
    }
    dump(args.usage_output.resolve(), usage)
    print("RMR_R1_REPRESENTATION_RESULT", json.dumps({
        "selected_candidate_id": selected,
        "selection_status": receipt["selection_status"],
        "attempted_candidates": [x["candidate_id"] for x in attempts],
        "holdout_2023_2025_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
