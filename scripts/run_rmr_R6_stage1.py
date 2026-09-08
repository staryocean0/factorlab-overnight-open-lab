#!/usr/bin/env python3
"""Frozen R6 multi-scale amplitude-state Stage-1 screen.

Uses exactly two preregistered amplitude-curve scores at frozen S1/S2 causal
directional-change event scales. Reads CSI1000 only through 2022-12-31.
2023-2025 reserve and all 2026 rows remain unopened.

This is a mechanism screen: no PnL, band search, threshold search, combined
spectral model, FFT/wavelet family search or third-mechanism auto-promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
import run_rmr_R5_stage1 as r5

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R6_stage1_protocol_v1.json"
PREANALYSIS = ROOT / "docs/research/rmr_R6_multiscale_amplitude_state_preanalysis_20260908.md"
DATA_ROLES = ROOT / "docs/governance/reversal_mean_reversion_stage1_common_data_roles_v1.json"
SCALE_CONTRACT = ROOT / "docs/governance/reversal_mean_reversion_stage1_scale_contract_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/research/local_rmr_R6_stage1_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_rmr_R6_stage1_data_usage_v1.json"

EXPECTED_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2019-12-31"
STAB_START = "2020-01-01"
STAB_END = "2022-12-31"
LOOKBACK = 240
HORIZONS = (4, 16, 64)
MIN_VALID_RETURNS = 20
REFERENCE_WINDOW = 100
EXTREME_Z = 2.0
HORIZON_BARS = 1200
SCALES = ("S1", "S2")
SCORE_IDS = ("R6_A_short_mid", "R6_B_mid_parent")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def validate_contracts() -> tuple[dict, dict, dict]:
    protocol = load_json(PROTOCOL)
    roles = load_json(DATA_ROLES)
    scales = load_json(SCALE_CONTRACT)
    if protocol["research_identity"] != "R6_multiscale_amplitude_state_stage1_v1":
        raise RuntimeError("R6 identity drifted")
    if protocol["stage"] != "results_blind_R6_stage1_protocol_freeze_before_empirical_outcome_open":
        raise RuntimeError("R6 protocol stage drifted")
    if protocol["market_outcomes_opened_for_protocol_design"] is not False:
        raise RuntimeError("R6 protocol was not results blind")
    if protocol["amplitude_measurement"]["fixed_horizons_bars"] != list(HORIZONS):
        raise RuntimeError("R6 amplitude horizons drifted")
    if int(protocol["amplitude_measurement"]["lookback_observed_1m_bars"]) != LOOKBACK:
        raise RuntimeError("R6 amplitude lookback drifted")
    if int(protocol["normalization"]["reference_window"]) != REFERENCE_WINDOW:
        raise RuntimeError("R6 normalization window drifted")
    if tuple(protocol["event_scales"]["reported_scales"]) != SCALES:
        raise RuntimeError("R6 event scale set drifted")
    if roles["source"]["sha256"] != EXPECTED_SHA:
        raise RuntimeError("R6 source identity drifted")
    if roles["broad_program_roles"]["STAGE1_RESERVE"]["open_now"] is not False:
        raise RuntimeError("R6 reserve unexpectedly open")
    if scales["source"] != roles["source"]["path"]:
        raise RuntimeError("R6 scale/source contract mismatch")
    return protocol, roles, scales


def read_source(path: Path) -> tuple[pd.DataFrame, dict]:
    actual_sha = sha256(path)
    if actual_sha != EXPECTED_SHA:
        raise RuntimeError(f"R6 source SHA mismatch: {actual_sha}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("trading_day", "<=", STAB_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.loc[frame["symbol"].eq(SYMBOL)].copy()
    if frame.empty:
        raise RuntimeError("R6 source empty")
    if str(frame["trading_day"].max()) > STAB_END:
        raise RuntimeError("R6 read crossed 2022 stability boundary")
    prices = frame["close"].to_numpy(dtype=float)
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise RuntimeError("R6 invalid close values")
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    frame["_idx"] = np.arange(len(frame), dtype=int)
    return frame, {
        "source_sha256": actual_sha,
        "rows_loaded": int(len(frame)),
        "min_day": str(frame["trading_day"].min()),
        "max_day": str(frame["trading_day"].max()),
        "rows_2023_or_later": 0,
        "reserve_2023_2025_opened": False,
    }


def frozen_thresholds(frame: pd.DataFrame) -> tuple[float, dict[str, float]]:
    temp = frame.copy()
    temp["clock"] = temp["timestamp"].astype(str).str[11:16]
    daily = temp.loc[temp["clock"].eq("15:00"), ["trading_day", "close"]].drop_duplicates(
        "trading_day", keep="last"
    ).sort_values("trading_day")
    daily["ret"] = daily["close"].pct_change(fill_method=None)
    daily["rv20"] = daily["ret"].rolling(20, min_periods=20).std().shift(1)
    vol_ref = float(daily.loc[daily["trading_day"] <= DEV_END, "rv20"].dropna().median())
    if not np.isfinite(vol_ref) or vol_ref <= 0:
        raise RuntimeError("R6 invalid DEV median rvol20")
    return vol_ref, {"S1": 0.25 * vol_ref, "S2": 0.50 * vol_ref}


def valid_k_bar_returns(
    log_prices: np.ndarray,
    days: np.ndarray,
    end_idx: int,
    k: int,
    lookback: int = LOOKBACK,
) -> np.ndarray:
    """Trailing causal within-session k-observation log returns."""
    if k <= 0 or end_idx <= k:
        return np.asarray([], dtype=float)
    first_end = max(k, end_idx - lookback + 1)
    vals: list[float] = []
    for j in range(first_end, end_idx + 1):
        start = j - k
        if start < 0:
            continue
        if str(days[j]) != str(days[start]):
            continue
        value = float(log_prices[j] - log_prices[start])
        if np.isfinite(value):
            vals.append(value)
    return np.asarray(vals, dtype=float)


def robust_amplitude(
    log_prices: np.ndarray,
    days: np.ndarray,
    end_idx: int,
    k: int,
) -> float:
    values = valid_k_bar_returns(log_prices, days, end_idx, k)
    if len(values) < MIN_VALID_RETURNS:
        return float("nan")
    amp = float(np.median(np.abs(values)) / math.sqrt(k))
    return amp if np.isfinite(amp) and amp > 0 else float("nan")


def amplitude_scores(
    log_prices: np.ndarray,
    days: np.ndarray,
    end_idx: int,
) -> dict[str, float]:
    amps = {k: robust_amplitude(log_prices, days, end_idx, k) for k in HORIZONS}
    if not all(np.isfinite(v) and v > 0 for v in amps.values()):
        return {score: float("nan") for score in SCORE_IDS}
    return {
        "R6_A_short_mid": float(np.log(amps[4] / amps[16])),
        "R6_B_mid_parent": float(np.log(amps[16] / amps[64])),
    }


def build_score_table(
    frame: pd.DataFrame,
    prices: np.ndarray,
    waves: list[common.Wave],
    threshold: float,
) -> pd.DataFrame:
    log_prices = np.log(prices)
    days = frame["trading_day"].to_numpy(dtype=str)
    rows: list[dict] = []
    for wave in waves:
        idx = int(wave.confirm_idx)
        if idx >= len(frame):
            continue
        day = str(days[idx])
        if day > STAB_END:
            continue
        scores = amplitude_scores(log_prices, days, idx)
        severity = abs(float(wave.move)) / float(threshold)
        for score_id, value in scores.items():
            rows.append({
                "property_id": score_id,
                "day": day,
                "confirm_idx": idx,
                "wave_direction": int(wave.direction),
                "severity": float(severity),
                "property_value": float(value) if np.isfinite(value) else np.nan,
            })
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    parts: list[pd.DataFrame] = []
    for score_id, part in table.groupby("property_id", sort=False):
        part = part.sort_values("confirm_idx", kind="mergesort").reset_index(drop=True)
        part["z"] = r5.rolling_median_mad_z(part["property_value"].tolist(), REFERENCE_WINDOW)
        part["next_z"] = part["z"].shift(-1)
        parts.append(part)
    return pd.concat(parts, ignore_index=True).sort_values(
        ["property_id", "confirm_idx"], kind="mergesort"
    ).reset_index(drop=True)


def fit_model(train: pd.DataFrame, features: list[str]) -> Pipeline | None:
    clean = train.dropna(subset=features + ["y"]).copy()
    if len(clean) < 30 or clean["y"].nunique() < 2:
        return None
    model = Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(
            C=1.0,
            penalty="l2",
            solver="lbfgs",
            fit_intercept=True,
            class_weight=None,
            max_iter=1000,
        )),
    ])
    model.fit(clean[features].to_numpy(dtype=float), clean["y"].to_numpy(dtype=int))
    return model


def score_model(model: Pipeline | None, data: pd.DataFrame, features: list[str]) -> dict:
    clean = data.dropna(subset=features + ["y"]).copy()
    if model is None or clean.empty:
        return {"status": "evidence_insufficient", "n": int(len(clean))}
    y = clean["y"].to_numpy(dtype=int)
    p = model.predict_proba(clean[features].to_numpy(dtype=float))[:, 1]
    return {
        "status": "scored",
        "n": int(len(clean)),
        "event_rate": float(np.mean(y)),
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "mean_probability": float(np.mean(p)),
    }


def summarize_score(events: pd.DataFrame, raw: pd.DataFrame, score_id: str) -> dict:
    event_part = events.loc[events["property_id"].eq(score_id)].copy()
    raw_part = raw.loc[raw["property_id"].eq(score_id)].copy()
    resolved = event_part.loc[event_part["outcome"].isin(["reversion", "extension"])].copy()
    if not resolved.empty:
        resolved["y"] = resolved["outcome"].eq("reversion").astype(int)
    dev = resolved.loc[resolved["day"] <= DEV_END].copy()
    stability = resolved.loc[
        (resolved["day"] >= STAB_START) & (resolved["day"] <= STAB_END)
    ].copy()
    baseline_features = ["severity"]
    augmented_features = ["severity", "z"]
    base_model = fit_model(dev, baseline_features)
    aug_model = fit_model(dev, augmented_features)
    pooled = {
        "baseline": score_model(base_model, stability, baseline_features),
        "augmented": score_model(aug_model, stability, augmented_features),
    }
    if pooled["baseline"].get("status") == "scored" and pooled["augmented"].get("status") == "scored":
        pooled["augmented_minus_baseline_brier"] = float(
            pooled["augmented"]["brier"] - pooled["baseline"]["brier"]
        )
        pooled["augmented_minus_baseline_log_loss"] = float(
            pooled["augmented"]["log_loss"] - pooled["baseline"]["log_loss"]
        )
    annual: dict[str, dict] = {}
    annual_counts: dict[str, int] = {}
    annual_improved = 0
    for year in (2020, 2021, 2022):
        yp = stability.loc[stability["day"].str.startswith(str(year))].copy()
        b = score_model(base_model, yp, baseline_features)
        a = score_model(aug_model, yp, augmented_features)
        annual[str(year)] = {"baseline": b, "augmented": a}
        annual_counts[str(year)] = int(len(yp))
        if b.get("status") == "scored" and a.get("status") == "scored" and a["brier"] < b["brier"]:
            annual_improved += 1
    local_gate = {
        "minimum_resolved_stability_events": int(len(stability)) >= 200,
        "minimum_50_each_stability_year": all(v >= 50 for v in annual_counts.values()),
        "pooled_brier_strictly_lower": bool(
            pooled["baseline"].get("status") == "scored"
            and pooled["augmented"].get("status") == "scored"
            and pooled["augmented"]["brier"] < pooled["baseline"]["brier"]
        ),
        "pooled_logloss_strictly_lower": bool(
            pooled["baseline"].get("status") == "scored"
            and pooled["augmented"].get("status") == "scored"
            and pooled["augmented"]["log_loss"] < pooled["baseline"]["log_loss"]
        ),
        "annual_brier_improvement_at_least_2_of_3": annual_improved >= 2,
    }
    prop_reversion = r5.property_reversion_stats(
        raw_part.loc[
            (raw_part["day"] >= STAB_START)
            & (raw_part["day"] <= STAB_END)
        ]
    )
    return {
        "inventory": {
            "raw_observations": int(len(raw_part)),
            "normalized_observations": int(raw_part["z"].notna().sum()),
            "price_outcome_events": int(len(event_part)),
            "resolved": int(len(resolved)),
            "censored": int((event_part["outcome"] == "censored").sum()),
            "dev_resolved": int(len(dev)),
            "stability_resolved": int(len(stability)),
            "stability_by_year": annual_counts,
        },
        "price_path_model_comparison": {"pooled_stability": pooled, "annual": annual},
        "descriptive_score_reversion": prop_reversion,
        "scale_local_gate": local_gate,
        "scale_local_gate_passed": bool(all(local_gate.values())),
    }


def aggregate_candidate_gate(results: dict) -> dict:
    candidates: dict[str, dict] = {}
    for score_id in SCORE_IDS:
        cells = {scale: results[scale]["scores"][score_id] for scale in SCALES}
        qualifies = bool(all(cell["scale_local_gate_passed"] for cell in cells.values()))
        improvements = []
        ll_improvements = []
        for scale, cell in cells.items():
            pooled = cell["price_path_model_comparison"]["pooled_stability"]
            if pooled["baseline"].get("status") == "scored" and pooled["augmented"].get("status") == "scored":
                improvements.append(float(pooled["baseline"]["brier"] - pooled["augmented"]["brier"]))
                ll_improvements.append(float(pooled["baseline"]["log_loss"] - pooled["augmented"]["log_loss"]))
        candidates[score_id] = {
            "qualifies_for_program_review": qualifies,
            "mean_pooled_brier_improvement_across_scales": None if len(improvements) != len(SCALES) else float(np.mean(improvements)),
            "mean_pooled_logloss_improvement_across_scales": None if len(ll_improvements) != len(SCALES) else float(np.mean(ll_improvements)),
        }
    qualified = [k for k, v in candidates.items() if v["qualifies_for_program_review"]]
    ranked = sorted(
        qualified,
        key=lambda k: (
            -(candidates[k]["mean_pooled_brier_improvement_across_scales"] or -1e99),
            -(candidates[k]["mean_pooled_logloss_improvement_across_scales"] or -1e99),
            k,
        ),
    )
    return {
        "by_score": candidates,
        "qualified_score_ids": qualified,
        "ranked_for_review": ranked,
        "positive_result_label": "candidate_for_program_review_only",
        "third_mechanism_auto_promotion": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--usage-output", type=Path, default=USAGE)
    args = parser.parse_args()

    validate_contracts()
    frame, source_audit = read_source(args.parquet.resolve())
    vol_ref, thresholds = frozen_thresholds(frame)
    prices = frame["close"].to_numpy(dtype=float)

    results: dict[str, dict] = {}
    for scale in SCALES:
        waves = common.detect_waves(prices, thresholds[scale])
        raw = build_score_table(frame, prices, waves, thresholds[scale])
        events = r5.add_price_outcomes(raw, prices, thresholds[scale])
        results[scale] = {
            "threshold": float(thresholds[scale]),
            "completed_wave_count": int(len(waves)),
            "scores": {score_id: summarize_score(events, raw, score_id) for score_id in SCORE_IDS},
        }

    candidate_gate = aggregate_candidate_gate(results)
    receipt = {
        "schema_id": "factorlab_reversal_mean_reversion_R6_stage1_receipt@1.0",
        "session_date": "2026-09-08",
        "program_identity": "broad_reversal_mean_reversion_discovery_program_v1",
        "research_identity": "R6_multiscale_amplitude_state_stage1_v1",
        "stage": "R6_stage1_screen_complete_pending_program_review",
        "code_commit": git_head(),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "preanalysis": str(PREANALYSIS.relative_to(ROOT)),
        "runner_sha256": sha256(Path(__file__)),
        "source": source_audit,
        "vol_ref_dev_median_rvol20": float(vol_ref),
        "directional_change_thresholds": {k: float(v) for k, v in thresholds.items()},
        "amplitude_lookback_observed_bars": LOOKBACK,
        "amplitude_horizons": list(HORIZONS),
        "minimum_valid_returns_each_horizon": MIN_VALID_RETURNS,
        "normalization_reference_window": REFERENCE_WINDOW,
        "score_ids_exact": list(SCORE_IDS),
        "scales_exact": list(SCALES),
        "results": results,
        "candidate_for_program_review_gate": candidate_gate,
        "reserve_2023_2025_opened": False,
        "2026_rows_loaded": False,
        "amplitude_horizon_search_performed": False,
        "amplitude_lookback_search_performed": False,
        "z_threshold_search_performed": False,
        "combined_score_model_used": False,
        "FFT_or_wavelet_family_search_performed": False,
        "scale_search_performed": False,
        "hyperparameter_search_performed": False,
        "probability_calibration_performed": False,
        "binary_threshold_selection_performed": False,
        "trading_return_used": False,
        "deep_model_used": False,
        "third_mechanism_auto_promoted": False,
        "raw_event_rows_written_to_repo": False,
        "scientifically_fresh": False,
        "production_authority": False,
    }
    dump_json(args.output.resolve(), receipt)

    usage = {
        "schema_id": "factorlab_reversal_mean_reversion_R6_stage1_data_usage@1.0",
        "session_date": "2026-09-08",
        "research_identity": "R6_multiscale_amplitude_state_stage1_v1",
        "opened": {
            "CSI1000_2015-01-05_to_2019-12-31": "development_material",
            "CSI1000_2020-01-01_to_2022-12-31": "chronological_stability_not_fresh"
        },
        "sealed_or_unopened": {
            "CSI1000_2023-01-01_to_2025-12-31_internal_reserve": True,
            "all_2026_rows": True
        },
        "aggregate_outputs_only": True,
        "raw_rows_written_to_repo": False,
        "trading_return_used": False,
        "scientifically_fresh": False,
        "production_authority": False
    }
    dump_json(args.usage_output.resolve(), usage)

    print("RMR_R6_STAGE1_RESULT", json.dumps({
        "qualified_score_ids": candidate_gate["qualified_score_ids"],
        "ranked_for_review": candidate_gate["ranked_for_review"],
        "reserve_2023_2025_opened": False,
        "2026_rows_loaded": False,
        "third_mechanism_auto_promoted": False
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
