#!/usr/bin/env python3
"""Select the bounded Gap-Fill Prediction V2 Phase-2 hazard family.

High-gap and low-gap heads are selected independently. Within each sign, an
expanding empirical stage-hazard benchmark is compared with a geometry-only
logistic hazard model and a single Phase-1-admitted full logistic hazard model.

The stacked V1 direction-support feature is generated in prior-year-only OOF
form for 2016-2025. Hazard OOF selection therefore begins in 2017, with 2016
serving only as the first clean hazard-training year. No 2026 row may be loaded.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import diagnose_gap_fill_v2_phase1_factors as p1
import diagnose_high_open_false_negatives_dev as highdiag

FAMILY = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase2_hazard_family_v1.json"
PARENT = ROOT / "docs/governance/cloud_session_20260906_gap_fill_prediction_v2_protocol_v1.json"
PHASE1 = ROOT / "docs/research/gap_fill_v2_phase1_factor_adjudication_20260906.md"
DIRECTION_SPEC = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
OUT = ROOT / "docs/research/cloud_session_20260906_gap_fill_v2_phase2_hazard_selection_receipt_v1.json"
USAGE = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase2_hazard_data_usage_v1.json"

EXPECTED_DIRECTION_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
REFERENCE_YEARS = list(range(2016, 2026))
VALID_YEARS = list(range(2017, 2026))
MATERIAL = {"gt10bp": 0.001, "gt30bp": 0.003}
HORIZONS = [("fill_15m", "p15"), ("fill_60m", "p60"), ("fill_eod", "pEOD")]
EPS = 1e-12
PROB_EPS = 1e-6


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


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def complete_mask(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    return x.notna().all(axis=1) & y.notna()


def build_direction_oof(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    years = pd.to_datetime(frame["trading_day"]).dt.year
    for valid_year in REFERENCE_YEARS:
        train = frame.loc[years < valid_year].copy()
        valid = frame.loc[years == valid_year].copy()
        mt = complete_mask(train, features)
        mv = complete_mask(valid, features)
        if int(mt.sum()) == 0 or int(mv.sum()) == 0:
            raise RuntimeError(f"empty V1 direction reference fold for {valid_year}")
        model = highdiag.median_pipe()
        model.fit(
            train.loc[mt, features].apply(pd.to_numeric, errors="coerce"),
            pd.to_numeric(train.loc[mt, "gap"], errors="coerce"),
        )
        part = valid[[
            "trading_day", "gap", "rvol20", "prev_daytime", "prev_last_hour",
            "us_nasdaq_interval", "us_vix_interval"
        ]].copy()
        part["oof_year"] = int(valid_year)
        part["v1_direction_score_oof"] = np.nan
        score = model.predict(valid.loc[mv, features].apply(pd.to_numeric, errors="coerce"))
        part.loc[mv, "v1_direction_score_oof"] = np.asarray(score, dtype=float)
        pieces.append(part)
    out = pd.concat(pieces, ignore_index=True)
    if out.empty:
        raise RuntimeError("empty V1 direction OOF reference")
    years_out = pd.to_datetime(out["trading_day"]).dt.year
    if int(years_out.min()) != 2016 or int(years_out.max()) != 2025 or (years_out >= 2026).any():
        raise RuntimeError("V1 direction OOF reference boundary drifted")
    return out


def build_model_frame(direction_features: list[str]) -> tuple[pd.DataFrame, dict]:
    frame, reconstruction = highdiag.build_development_frame()
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered Phase-2 feature frame")
    v1 = build_direction_oof(frame, direction_features)
    targets = p1.build_targets()
    merged = v1.merge(
        targets[["trading_day", "gap", "gap_sign", "abs_gap", "fill_15m", "fill_60m", "fill_eod"]],
        on="trading_day",
        how="inner",
        suffixes=("", "_target"),
        validate="one_to_one",
    )
    if merged.empty:
        raise RuntimeError("Phase-2 V1/target merge empty")
    diff = np.max(np.abs(
        pd.to_numeric(merged["gap"], errors="coerce").to_numpy(dtype=float)
        - pd.to_numeric(merged["gap_target"], errors="coerce").to_numpy(dtype=float)
    ))
    if not np.isfinite(diff) or diff > 1e-12:
        raise RuntimeError(f"V1/target gap mismatch: {diff}")
    merged = merged.drop(columns=["gap_target"])
    gap = pd.to_numeric(merged["gap"], errors="coerce")
    sign = np.where(gap > 0.0, 1.0, -1.0)
    rvol = pd.to_numeric(merged["rvol20"], errors="coerce")
    merged["abs_gap"] = gap.abs()
    merged["abs_gap_over_rvol20"] = np.where(rvol > 0.0, gap.abs() / rvol, np.nan)
    merged["v1_direction_support"] = sign * pd.to_numeric(merged["v1_direction_score_oof"], errors="coerce")
    merged["nasdaq_interval_support"] = sign * pd.to_numeric(merged["us_nasdaq_interval"], errors="coerce")
    merged["vix_interval_support"] = -sign * pd.to_numeric(merged["us_vix_interval"], errors="coerce")
    merged["prior_daytime_alignment"] = sign * pd.to_numeric(merged["prev_daytime"], errors="coerce")
    merged["prior_last_hour_alignment"] = sign * pd.to_numeric(merged["prev_last_hour"], errors="coerce")
    if (pd.to_datetime(merged["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered Phase-2 merged frame")
    return merged, reconstruction


def logistic_pipe(family: dict) -> Pipeline:
    est = family["fixed_estimator"]
    if est["C"] != 1.0 or est["penalty"] != "l2" or est["solver"] != "lbfgs" or est["class_weight"] is not None:
        raise RuntimeError("Phase-2 estimator drifted")
    return Pipeline([
        ("sc", StandardScaler()),
        ("model", LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            class_weight=None,
            max_iter=1000,
        )),
    ])


def fit_stage_model(train: pd.DataFrame, features: list[str], stage: str, family: dict):
    if stage == "15m":
        risk = np.ones(len(train), dtype=bool)
        target = train["fill_15m"].astype(int).to_numpy()
    elif stage == "60m":
        risk = (~train["fill_15m"].astype(bool)).to_numpy()
        target = train["fill_60m"].astype(int).to_numpy()
    elif stage == "eod":
        risk = (~train["fill_60m"].astype(bool)).to_numpy()
        target = train["fill_eod"].astype(int).to_numpy()
    else:
        raise ValueError(stage)
    y = target[risk]
    if len(y) == 0 or np.unique(y).size != 2:
        raise RuntimeError(f"stage {stage} training risk set lacks both classes")
    x = train.loc[risk, features].apply(pd.to_numeric, errors="coerce")
    model = logistic_pipe(family)
    model.fit(x, y)
    return model, int(len(y)), int(y.sum())


def empirical_stage_rate(train: pd.DataFrame, stage: str) -> tuple[float, int, int]:
    if stage == "15m":
        risk = np.ones(len(train), dtype=bool)
        target = train["fill_15m"].astype(int).to_numpy()
    elif stage == "60m":
        risk = (~train["fill_15m"].astype(bool)).to_numpy()
        target = train["fill_60m"].astype(int).to_numpy()
    elif stage == "eod":
        risk = (~train["fill_60m"].astype(bool)).to_numpy()
        target = train["fill_eod"].astype(int).to_numpy()
    else:
        raise ValueError(stage)
    y = target[risk]
    if len(y) == 0:
        raise RuntimeError(f"empty empirical risk set {stage}")
    rate = float(np.clip(np.mean(y), PROB_EPS, 1.0 - PROB_EPS))
    return rate, int(len(y)), int(y.sum())


def cumulative_probs(h15: np.ndarray, h60: np.ndarray, heod: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p15 = np.asarray(h15, dtype=float)
    p60 = 1.0 - (1.0 - p15) * (1.0 - np.asarray(h60, dtype=float))
    peod = 1.0 - (1.0 - p15) * (1.0 - np.asarray(h60, dtype=float)) * (1.0 - np.asarray(heod, dtype=float))
    return p15, p60, peod


def assert_monotone(pred: pd.DataFrame) -> int:
    p15 = pd.to_numeric(pred["p15"], errors="coerce").to_numpy(dtype=float)
    p60 = pd.to_numeric(pred["p60"], errors="coerce").to_numpy(dtype=float)
    peod = pd.to_numeric(pred["pEOD"], errors="coerce").to_numpy(dtype=float)
    bad = (~np.isfinite(p15)) | (~np.isfinite(p60)) | (~np.isfinite(peod))
    bad |= (p15 < -EPS) | (p60 < p15 - EPS) | (peod < p60 - EPS) | (peod > 1.0 + EPS)
    return int(np.sum(bad))


def expanding_predictions(sign_frame: pd.DataFrame, features: list[str] | None, family: dict, name: str) -> tuple[pd.DataFrame, dict]:
    parts: list[pd.DataFrame] = []
    fold_audit: dict[str, dict] = {}
    for valid_year in VALID_YEARS:
        train = sign_frame.loc[sign_frame["oof_year"] < valid_year].copy()
        valid = sign_frame.loc[sign_frame["oof_year"] == valid_year].copy()
        if train.empty or valid.empty:
            raise RuntimeError(f"empty hazard fold {valid_year} for {name}")

        stage_meta: dict[str, dict] = {}
        if features is None:
            h15_rate, n15, e15 = empirical_stage_rate(train, "15m")
            h60_rate, n60, e60 = empirical_stage_rate(train, "60m")
            heod_rate, neod, eeod = empirical_stage_rate(train, "eod")
            h15 = np.full(len(valid), h15_rate, dtype=float)
            h60 = np.full(len(valid), h60_rate, dtype=float)
            heod = np.full(len(valid), heod_rate, dtype=float)
            stage_meta = {
                "15m": {"n_train_risk": n15, "events": e15, "empirical_rate": h15_rate},
                "60m": {"n_train_risk": n60, "events": e60, "empirical_rate": h60_rate},
                "eod": {"n_train_risk": neod, "events": eeod, "empirical_rate": heod_rate},
            }
        else:
            m15, n15, e15 = fit_stage_model(train, features, "15m", family)
            m60, n60, e60 = fit_stage_model(train, features, "60m", family)
            meod, neod, eeod = fit_stage_model(train, features, "eod", family)
            xv = valid[features].apply(pd.to_numeric, errors="coerce")
            h15 = m15.predict_proba(xv)[:, 1]
            h60 = m60.predict_proba(xv)[:, 1]
            heod = meod.predict_proba(xv)[:, 1]
            stage_meta = {
                "15m": {"n_train_risk": n15, "events": e15},
                "60m": {"n_train_risk": n60, "events": e60},
                "eod": {"n_train_risk": neod, "events": eeod},
            }

        p15, p60, peod = cumulative_probs(h15, h60, heod)
        part = valid[["trading_day", "oof_year", "gap_sign", "abs_gap", "fill_15m", "fill_60m", "fill_eod"]].copy()
        part["h15"] = h15
        part["h60"] = h60
        part["hEOD"] = heod
        part["p15"] = p15
        part["p60"] = p60
        part["pEOD"] = peod
        violations = assert_monotone(part)
        if violations:
            raise RuntimeError(f"probability monotonicity violated in {name} {valid_year}")
        parts.append(part)
        fold_audit[str(valid_year)] = {
            "n_train": int(len(train)),
            "n_valid": int(len(valid)),
            "stage_training": stage_meta,
            "monotonicity_violations": violations,
        }
    out = pd.concat(parts, ignore_index=True)
    if out.empty or int(out["oof_year"].min()) != 2017 or int(out["oof_year"].max()) != 2025:
        raise RuntimeError(f"hazard OOF boundary drifted for {name}")
    if assert_monotone(out):
        raise RuntimeError(f"pooled monotonicity violation for {name}")
    return out, fold_audit


def calibration_intercept_slope(y: np.ndarray, p: np.ndarray) -> tuple[float | None, float | None]:
    y = np.asarray(y, dtype=float)
    p = np.clip(np.asarray(p, dtype=float), PROB_EPS, 1.0 - PROB_EPS)
    if np.unique(y.astype(int)).size != 2:
        return None, None
    logit = np.log(p / (1.0 - p))

    def objective(theta: np.ndarray) -> float:
        q = expit(theta[0] + theta[1] * logit)
        q = np.clip(q, PROB_EPS, 1.0 - PROB_EPS)
        return float(-np.mean(y * np.log(q) + (1.0 - y) * np.log(1.0 - q)))

    res = minimize(objective, np.asarray([0.0, 1.0]), method="BFGS")
    if not res.success or not np.isfinite(res.x).all():
        return None, None
    return float(res.x[0]), float(res.x[1])


def probability_deciles(y: np.ndarray, p: np.ndarray) -> list[dict]:
    frame = pd.DataFrame({"y": np.asarray(y, dtype=float), "p": np.asarray(p, dtype=float)})
    if len(frame) < 20:
        return []
    ranked = frame["p"].rank(method="first")
    q = pd.qcut(ranked, 10, labels=False) + 1
    frame["decile"] = q.astype(int)
    result = []
    for d in range(1, 11):
        part = frame.loc[frame["decile"] == d]
        result.append({
            "decile": d,
            "n": int(len(part)),
            "mean_predicted": float(part["p"].mean()),
            "observed_fill_rate": float(part["y"].mean()),
        })
    return result


def binary_metrics(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), PROB_EPS, 1.0 - PROB_EPS)
    brier = float(np.mean((p - y) ** 2))
    ll = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    if np.unique(y).size == 2:
        auc = float(roc_auc_score(y, p))
        pr = float(average_precision_score(y, p))
    else:
        auc = None
        pr = None
    ci, cs = calibration_intercept_slope(y, p)
    return {
        "n": int(len(y)),
        "event_rate": float(np.mean(y)),
        "brier_score": brier,
        "log_loss": ll,
        "roc_auc": auc,
        "pr_auc": pr,
        "calibration_intercept": ci,
        "calibration_slope": cs,
        "probability_deciles": probability_deciles(y, p),
    }


def evaluate(pred: pd.DataFrame, mask: pd.Series | np.ndarray | None = None) -> dict:
    part = pred if mask is None else pred.loc[np.asarray(mask, dtype=bool)]
    if part.empty:
        raise RuntimeError("empty evaluation cohort")
    horizons = {}
    briers = []
    losses = []
    for target, prob in HORIZONS:
        m = binary_metrics(part[target].astype(int).to_numpy(), pd.to_numeric(part[prob], errors="coerce").to_numpy(dtype=float))
        horizons[target] = m
        briers.append(float(m["brier_score"]))
        losses.append(float(m["log_loss"]))
    return {
        "n": int(len(part)),
        "integrated_brier": float(np.mean(briers)),
        "integrated_log_loss": float(np.mean(losses)),
        "horizons": horizons,
    }


def annual_evaluations(pred: pd.DataFrame, threshold: float) -> dict:
    out = {}
    for year in VALID_YEARS:
        mask = (pred["oof_year"] == year) & (pd.to_numeric(pred["abs_gap"], errors="coerce") > threshold)
        out[str(year)] = evaluate(pred, mask)
    return out


def compare_integrated(reference: dict, candidate: dict) -> dict:
    return {
        "brier_improvement": float(reference["integrated_brier"] - candidate["integrated_brier"]),
        "log_loss_improvement": float(reference["integrated_log_loss"] - candidate["integrated_log_loss"]),
    }


def evaluate_all(pred: pd.DataFrame) -> dict:
    all_eval = evaluate(pred)
    gt10 = evaluate(pred, pd.to_numeric(pred["abs_gap"], errors="coerce") > MATERIAL["gt10bp"])
    gt30 = evaluate(pred, pd.to_numeric(pred["abs_gap"], errors="coerce") > MATERIAL["gt30bp"])
    annual_gt10 = annual_evaluations(pred, MATERIAL["gt10bp"])
    return {"all": all_eval, "gt10bp": gt10, "gt30bp": gt30, "annual_gt10bp": annual_gt10}


def annual_improvements(reference: dict, candidate: dict) -> tuple[dict, int, float]:
    deltas = {
        str(year): float(reference[str(year)]["integrated_brier"] - candidate[str(year)]["integrated_brier"])
        for year in VALID_YEARS
    }
    positive = int(sum(v > EPS for v in deltas.values()))
    median = float(np.median(list(deltas.values())))
    return deltas, positive, median


def geometry_gate(benchmark_eval: dict, geometry_eval: dict, monotonicity_violations: int) -> dict:
    annual_delta, positive, median = annual_improvements(benchmark_eval["annual_gt10bp"], geometry_eval["annual_gt10bp"])
    gate = {
        "pooled_all_integrated_brier_strictly_lower": geometry_eval["all"]["integrated_brier"] < benchmark_eval["all"]["integrated_brier"] - EPS,
        "pooled_all_integrated_log_loss_strictly_lower": geometry_eval["all"]["integrated_log_loss"] < benchmark_eval["all"]["integrated_log_loss"] - EPS,
        "pooled_gt10_integrated_brier_strictly_lower": geometry_eval["gt10bp"]["integrated_brier"] < benchmark_eval["gt10bp"]["integrated_brier"] - EPS,
        "pooled_gt30_integrated_brier_not_higher": geometry_eval["gt30bp"]["integrated_brier"] <= benchmark_eval["gt30bp"]["integrated_brier"] + EPS,
        "gt10_positive_annual_integrated_brier_improvement_at_least_5_of_9": positive >= 5,
        "gt10_median_annual_integrated_brier_improvement_positive": median > EPS,
        "monotonicity_violations_zero": monotonicity_violations == 0,
    }
    return {
        "eligible": bool(all(gate.values())),
        "gates": gate,
        "annual_gt10_integrated_brier_improvement": annual_delta,
        "positive_annual_improvement_count": positive,
        "median_annual_improvement": median,
    }


def full_gate(geometry_eval: dict, full_eval: dict, monotonicity_violations: int) -> dict:
    annual_delta, positive, median = annual_improvements(geometry_eval["annual_gt10bp"], full_eval["annual_gt10bp"])
    horizon_improve = {
        h: float(geometry_eval["gt10bp"]["horizons"][h]["brier_score"] - full_eval["gt10bp"]["horizons"][h]["brier_score"])
        for h, _ in HORIZONS
    }
    horizon_positive = int(sum(v > EPS for v in horizon_improve.values()))
    gate = {
        "pooled_all_integrated_brier_strictly_lower": full_eval["all"]["integrated_brier"] < geometry_eval["all"]["integrated_brier"] - EPS,
        "pooled_all_integrated_log_loss_strictly_lower": full_eval["all"]["integrated_log_loss"] < geometry_eval["all"]["integrated_log_loss"] - EPS,
        "pooled_gt10_integrated_brier_strictly_lower": full_eval["gt10bp"]["integrated_brier"] < geometry_eval["gt10bp"]["integrated_brier"] - EPS,
        "pooled_gt30_integrated_brier_not_higher": full_eval["gt30bp"]["integrated_brier"] <= geometry_eval["gt30bp"]["integrated_brier"] + EPS,
        "gt10_at_least_2_of_3_horizon_brier_scores_strictly_lower": horizon_positive >= 2,
        "gt10_positive_annual_integrated_brier_improvement_at_least_6_of_9": positive >= 6,
        "gt10_median_annual_integrated_brier_improvement_positive": median > EPS,
        "monotonicity_violations_zero": monotonicity_violations == 0,
    }
    return {
        "eligible": bool(all(gate.values())),
        "gates": gate,
        "annual_gt10_integrated_brier_improvement": annual_delta,
        "positive_annual_improvement_count": positive,
        "median_annual_improvement": median,
        "gt10_horizon_brier_improvement": horizon_improve,
        "gt10_horizon_improvement_count": horizon_positive,
    }


def selected_spec(sign: str, selection: str, features: list[str], family: dict) -> dict:
    return {
        "sign": sign,
        "selected_feature_set": selection,
        "features": features,
        "hazard_structure": family["hazard_definition"],
        "estimator": family["fixed_estimator"],
        "v1_direction_spec_sha256": EXPECTED_DIRECTION_SHA,
        "development_reference": "2016_to_2025_prior-year-only_V1_direction_OOF",
        "hazard_selection_oof": "2017_to_2025_expanding_natural_year",
        "decision_output": "cumulative_fill_probabilities_p15_p60_pEOD_no_fixed_binary_threshold",
    }


def main() -> int:
    family = load_json(FAMILY)
    parent = load_json(PARENT)
    direction_spec = load_json(DIRECTION_SPEC)
    if family["research_identity"] != "gap_fill_prediction_v2" or parent["research_identity"] != "gap_fill_prediction_v2":
        raise RuntimeError("V2 identity drifted")
    if direction_spec["selected_spec_sha256"] != EXPECTED_DIRECTION_SHA:
        raise RuntimeError("V1 direction identity drifted")
    if family["candidate_family"]["multiplicity"] != 4:
        raise RuntimeError("unexpected Phase-2 candidate multiplicity")
    if family["time_structure"]["hazard_oof_validation_years"] != VALID_YEARS:
        raise RuntimeError("Phase-2 OOF years drifted")

    high_expected = [
        "abs_gap", "abs_gap_over_rvol20", "v1_direction_support",
        "nasdaq_interval_support", "vix_interval_support",
        "prior_daytime_alignment", "prior_last_hour_alignment",
    ]
    low_expected = [
        "abs_gap", "abs_gap_over_rvol20", "v1_direction_support",
        "nasdaq_interval_support", "vix_interval_support",
    ]
    if family["candidate_family"]["high"]["phase1_full"] != high_expected:
        raise RuntimeError("high full feature family drifted")
    if family["candidate_family"]["low"]["phase1_full"] != low_expected:
        raise RuntimeError("low full feature family drifted")

    direction_features = list(direction_spec["selected_spec"]["direction_features"])
    model_frame, reconstruction = build_model_frame(direction_features)

    sign_results = {}
    selected = {}
    selected_count = 0
    for sign in ["high", "low"]:
        geometry_features = list(family["candidate_family"][sign]["geometry_only"])
        full_features = list(family["candidate_family"][sign]["phase1_full"])
        needed = full_features + ["fill_15m", "fill_60m", "fill_eod", "gap_sign", "oof_year", "trading_day", "abs_gap"]
        complete = model_frame[needed].notna().all(axis=1)
        sf = model_frame.loc[complete & (model_frame["gap_sign"] == sign)].copy()
        sf = sf.loc[sf["oof_year"].isin(REFERENCE_YEARS)].sort_values("trading_day", kind="mergesort").reset_index(drop=True)
        if sf.empty or int(sf["oof_year"].min()) != 2016 or int(sf["oof_year"].max()) != 2025:
            raise RuntimeError(f"invalid common inventory for {sign}")

        benchmark_pred, benchmark_folds = expanding_predictions(sf, None, family, f"{sign}_benchmark")
        geometry_pred, geometry_folds = expanding_predictions(sf, geometry_features, family, f"{sign}_geometry")
        full_pred, full_folds = expanding_predictions(sf, full_features, family, f"{sign}_full")
        days = benchmark_pred["trading_day"].tolist()
        if days != geometry_pred["trading_day"].tolist() or days != full_pred["trading_day"].tolist():
            raise RuntimeError(f"comparator day inventory differs for {sign}")

        benchmark_eval = evaluate_all(benchmark_pred)
        geometry_eval = evaluate_all(geometry_pred)
        full_eval = evaluate_all(full_pred)
        geometry_admission = geometry_gate(benchmark_eval, geometry_eval, assert_monotone(geometry_pred))
        full_admission = full_gate(geometry_eval, full_eval, assert_monotone(full_pred))

        if not geometry_admission["eligible"]:
            choice = None
            choice_features: list[str] = []
        elif full_admission["eligible"]:
            choice = "phase1_full"
            choice_features = full_features
        else:
            choice = "geometry_only"
            choice_features = geometry_features

        spec = None if choice is None else selected_spec(sign, choice, choice_features, family)
        if spec is not None:
            selected_count += 1
            selected[sign] = {
                "selected_feature_set": choice,
                "spec": spec,
                "spec_sha256": canonical_digest(spec),
            }
        else:
            selected[sign] = None

        sign_results[sign] = {
            "n_common_reference_rows_2016_2025": int(len(sf)),
            "n_oof_rows_2017_2025": int(len(benchmark_pred)),
            "common_oof_days_identical": True,
            "geometry_features": geometry_features,
            "full_features": full_features,
            "benchmark": {"evaluation": benchmark_eval, "fold_audit": benchmark_folds},
            "geometry": {
                "evaluation": geometry_eval,
                "fold_audit": geometry_folds,
                "admission_vs_benchmark": geometry_admission,
                "pooled_all_improvement_vs_benchmark": compare_integrated(benchmark_eval["all"], geometry_eval["all"]),
                "pooled_gt10_improvement_vs_benchmark": compare_integrated(benchmark_eval["gt10bp"], geometry_eval["gt10bp"]),
                "pooled_gt30_improvement_vs_benchmark": compare_integrated(benchmark_eval["gt30bp"], geometry_eval["gt30bp"]),
            },
            "full": {
                "evaluation": full_eval,
                "fold_audit": full_folds,
                "admission_vs_geometry": full_admission,
                "pooled_all_improvement_vs_geometry": compare_integrated(geometry_eval["all"], full_eval["all"]),
                "pooled_gt10_improvement_vs_geometry": compare_integrated(geometry_eval["gt10bp"], full_eval["gt10bp"]),
                "pooled_gt30_improvement_vs_geometry": compare_integrated(geometry_eval["gt30bp"], full_eval["gt30bp"]),
            },
            "selected_feature_set": choice,
            "selected_spec": spec,
            "selected_spec_sha256": None if spec is None else canonical_digest(spec),
        }

    if selected_count == 2:
        decision = "freeze_complete_v2_phase2_hazard_architecture_before_any_repeat_validation"
    elif selected_count == 1:
        decision = "partial_v2_phase2_head_admitted_do_not_open_repeat_validation"
    else:
        decision = "no_v2_phase2_head_admitted_do_not_open_repeat_validation"

    architecture = {
        "research_identity": "gap_fill_prediction_v2",
        "architecture": "separate_high_low_three_stage_discrete_time_fill_hazards",
        "selected_heads": selected,
        "selection_oof": "2017_to_2025_expanding_natural_year",
        "probability_outputs": ["p15", "p60", "pEOD"],
        "binary_threshold": None,
        "repeat_only_reserved": "2026-01-05_to_2026-08-21",
        "true_fresh_reserved": "post_2026-08-21",
    }
    architecture_sha = canonical_digest(architecture)

    receipt = {
        "schema_id": "overnight_open_gap_fill_v2_phase2_hazard_selection_receipt@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_prediction_v2",
        "family": str(FAMILY.relative_to(ROOT)),
        "family_sha256": sha256(FAMILY),
        "phase1_adjudication": str(PHASE1.relative_to(ROOT)),
        "hazard_oof_years": VALID_YEARS,
        "sign_results": sign_results,
        "selected_heads": selected,
        "selected_head_count": selected_count,
        "selected_architecture": architecture,
        "selected_architecture_sha256": architecture_sha,
        "decision": decision,
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "family": sha256(FAMILY),
            "parent_protocol": sha256(PARENT),
            "phase1_adjudication": sha256(PHASE1),
            "direction_spec": sha256(DIRECTION_SPEC),
            "annotated_panel": sha256(highdiag.ANNOTATED_PANEL),
            "one_minute_official": sha256(highdiag.DATAHUB_1M),
            "fred_nasdaq": sha256(highdiag.FRED_NDQ),
            "fred_vix": sha256(highdiag.FRED_VIX),
            "runner": sha256(Path(__file__)),
        },
        "v1_reference_fitting_performed": True,
        "v1_reference_fits_used_gap_fill_outcomes": False,
        "gap_fill_model_fitting_performed": True,
        "candidate_selection_performed": True,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "model_class_search_performed": False,
        "probability_calibration_used_for_selection": False,
        "descriptive_calibration_fit_performed": True,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "2026_repeat_validation_opened": False,
        "fresh_oos": False,
        "production_authority": False,
        "raw_prediction_rows_written_to_repo": False,
    }
    dump_json(OUT, receipt)
    usage = {
        "schema_id": "overnight_open_gap_fill_v2_phase2_hazard_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31",
        "v1_reference_scores": "2016_to_2025_prior-year-only_expanding_OOF",
        "hazard_selection_oof": "2017_to_2025_expanding_natural_year",
        "2021_to_2025_role": "consumed_development_not_fresh",
        "2026-01-05_to_2026-08-21": "not_loaded_repeat_only_reserved",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_prediction_rows_persisted": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)
    print("GAP_FILL_V2_PHASE2_HAZARD_SELECTION_RESULT", json.dumps({
        "selected_head_count": selected_count,
        "selected_heads": {k: None if v is None else v["selected_feature_set"] for k, v in selected.items()},
        "selected_architecture_sha256": architecture_sha,
        "decision": decision,
        "2026_rows_loaded": False,
        "2026_repeat_validation_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
