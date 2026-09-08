#!/usr/bin/env python3
"""Frozen R5 statistical-state-extremes Stage-1 shallow screen.

Runs exactly three preregistered statistical-state properties at the frozen
S1/S2 directional-change scales on CSI1000 development/stability data through
2022-12-31. 2023-2025 reserve and all 2026 rows remain unopened.

This is mechanism screening only: no PnL, threshold search, scale search,
interaction search, calibration, or deep/frequency-model rescue.
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

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R5_stage1_protocol_v1.json"
DATA_ROLES = ROOT / "docs/governance/reversal_mean_reversion_stage1_common_data_roles_v1.json"
SCALE_CONTRACT = ROOT / "docs/governance/reversal_mean_reversion_stage1_scale_contract_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/research/local_rmr_R5_stage1_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_rmr_R5_stage1_data_usage_v1.json"

EXPECTED_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_END = "2019-12-31"
STAB_START = "2020-01-01"
STAB_END = "2022-12-31"
HORIZON_BARS = 1200
REFERENCE_WINDOW = 100
EXTREME_Z = 2.0
EVENT_DENSITY_BARS = 240

PROPERTY_IDS = (
    "R5_A_path_efficiency",
    "R5_B_volatility_state_displacement",
    "R5_C_event_density",
)
SCALES = ("S1", "S2")


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
    if protocol["research_identity"] != "R5_statistical_state_extremes_stage1_v1":
        raise RuntimeError("R5 research identity drifted")
    if protocol["stage"] != "results_blind_R5_stage1_execution_freeze_before_empirical_outcome_open":
        raise RuntimeError("R5 stage drifted")
    if protocol["market_outcomes_opened_for_protocol_design"] is not False:
        raise RuntimeError("R5 protocol was not results blind")
    if tuple(protocol["wave_scales"]["reported_scales"]) != SCALES:
        raise RuntimeError("R5 reported scale set drifted")
    if protocol["normalization"]["reference_window"] != REFERENCE_WINDOW:
        raise RuntimeError("R5 normalization window drifted")
    if float(protocol["normalization"]["descriptive_extreme_threshold_abs_z"]) != EXTREME_Z:
        raise RuntimeError("R5 descriptive extreme threshold drifted")
    if protocol["price_path_outcome"]["maximum_observed_1m_bars"] != HORIZON_BARS:
        raise RuntimeError("R5 outcome horizon drifted")
    if roles["source"]["sha256"] != EXPECTED_SHA:
        raise RuntimeError("common source identity drifted")
    if roles["broad_program_roles"]["STAGE1_RESERVE"]["open_now"] is not False:
        raise RuntimeError("2023-2025 reserve was unexpectedly opened")
    if scales["source"] != roles["source"]["path"]:
        raise RuntimeError("R5 scale/source contract mismatch")
    return protocol, roles, scales


def read_source(path: Path) -> tuple[pd.DataFrame, dict]:
    actual_sha = sha256(path)
    if actual_sha != EXPECTED_SHA:
        raise RuntimeError(f"source SHA mismatch: {actual_sha}")
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
        raise RuntimeError("R5 source is empty")
    if str(frame["trading_day"].max()) > STAB_END:
        raise RuntimeError("R5 read crossed 2022 stability boundary")
    if not np.isfinite(frame["close"].to_numpy(dtype=float)).all() or (frame["close"] <= 0).any():
        raise RuntimeError("R5 source contains invalid close values")
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    frame["_idx"] = np.arange(len(frame), dtype=int)
    audit = {
        "source_sha256": actual_sha,
        "rows_loaded": int(len(frame)),
        "min_day": str(frame["trading_day"].min()),
        "max_day": str(frame["trading_day"].max()),
        "reserve_2023_2025_opened": False,
        "rows_2023_or_later": 0,
    }
    return frame, audit


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
        raise RuntimeError("invalid frozen DEV median rvol20")
    thresholds = {"S1": 0.25 * vol_ref, "S2": 0.50 * vol_ref}
    return vol_ref, thresholds


def wave_path_efficiency(prices: np.ndarray, wave: common.Wave) -> float:
    part = np.asarray(prices[wave.start_idx : wave.end_idx + 1], dtype=float)
    if len(part) < 2:
        return float("nan")
    denom = float(np.sum(np.abs(np.diff(part))))
    if not np.isfinite(denom) or denom <= 0:
        return float("nan")
    return float(abs(part[-1] - part[0]) / denom)


def volatility_ratio(log_prices: np.ndarray, confirm_idx: int) -> float:
    if confirm_idx < 31:
        return float("nan")
    start = max(0, confirm_idx - EVENT_DENSITY_BARS)
    rets = np.diff(log_prices[start : confirm_idx + 1])
    if len(rets) < 120:
        return float("nan")
    short = rets[-30:]
    parent = rets[-240:] if len(rets) >= 240 else rets
    short_std = float(np.std(short, ddof=0))
    parent_std = float(np.std(parent, ddof=0))
    if not np.isfinite(short_std) or not np.isfinite(parent_std) or parent_std <= 0:
        return float("nan")
    return float(short_std / parent_std)


def event_density(confirm_indices: list[int], position: int) -> tuple[float, int | None]:
    idx = int(confirm_indices[position])
    lo = idx - (EVENT_DENSITY_BARS - 1)
    start_pos = int(np.searchsorted(np.asarray(confirm_indices, dtype=int), lo, side="left"))
    count = position - start_pos + 1
    duration = None if position == 0 else int(idx - int(confirm_indices[position - 1]))
    return float(count / EVENT_DENSITY_BARS), duration


def rolling_median_mad_z(values: list[float], window: int = REFERENCE_WINDOW) -> list[float | None]:
    out: list[float | None] = []
    history: list[float] = []
    for value in values:
        if len(history) < window or not np.isfinite(value):
            out.append(None)
        else:
            ref = np.asarray(history[-window:], dtype=float)
            med = float(np.median(ref))
            mad = float(np.median(np.abs(ref - med)))
            if not np.isfinite(mad) or mad <= 0:
                out.append(None)
            else:
                out.append(float((value - med) / mad))
        if np.isfinite(value):
            history.append(float(value))
    return out


def first_passage_close(
    prices: np.ndarray,
    start_idx: int,
    direction: int,
    threshold: float,
    horizon: int = HORIZON_BARS,
) -> tuple[str, int]:
    event_price = float(prices[start_idx])
    if direction > 0:
        extension = event_price * (1.0 + threshold)
        reversion = event_price * (1.0 - threshold)
    else:
        extension = event_price * (1.0 - threshold)
        reversion = event_price * (1.0 + threshold)
    end = min(len(prices) - 1, start_idx + horizon)
    for j in range(start_idx + 1, end + 1):
        x = float(prices[j])
        if direction > 0:
            if x >= extension:
                return "extension", j
            if x <= reversion:
                return "reversion", j
        else:
            if x <= extension:
                return "extension", j
            if x >= reversion:
                return "reversion", j
    return "censored", end


def build_property_table(
    frame: pd.DataFrame,
    prices: np.ndarray,
    waves: list[common.Wave],
    threshold: float,
) -> pd.DataFrame:
    log_prices = np.log(prices)
    confirms = [int(w.confirm_idx) for w in waves]
    rows: list[dict] = []
    for pos, wave in enumerate(waves):
        if wave.confirm_idx >= len(frame):
            continue
        day = str(frame.iloc[wave.confirm_idx]["trading_day"])
        if day > STAB_END:
            continue
        density, duration = event_density(confirms, pos)
        values = {
            "R5_A_path_efficiency": wave_path_efficiency(prices, wave),
            "R5_B_volatility_state_displacement": volatility_ratio(log_prices, wave.confirm_idx),
            "R5_C_event_density": density,
        }
        severity = abs(float(wave.move)) / float(threshold)
        for prop, value in values.items():
            rows.append(
                {
                    "property_id": prop,
                    "day": day,
                    "confirm_idx": int(wave.confirm_idx),
                    "wave_direction": int(wave.direction),
                    "severity": float(severity),
                    "property_value": float(value) if np.isfinite(value) else np.nan,
                    "duration_since_previous_confirmation_bars": duration,
                }
            )
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    out_parts: list[pd.DataFrame] = []
    for prop, part in table.groupby("property_id", sort=False):
        part = part.sort_values("confirm_idx", kind="mergesort").reset_index(drop=True)
        part["z"] = rolling_median_mad_z(part["property_value"].tolist())
        part["next_z"] = part["z"].shift(-1)
        out_parts.append(part)
    return pd.concat(out_parts, ignore_index=True).sort_values(
        ["property_id", "confirm_idx"], kind="mergesort"
    ).reset_index(drop=True)


def add_price_outcomes(table: pd.DataFrame, prices: np.ndarray, threshold: float) -> pd.DataFrame:
    if table.empty:
        return table
    parts: list[pd.DataFrame] = []
    for prop, part in table.groupby("property_id", sort=False):
        part = part.loc[part["z"].notna()].sort_values("confirm_idx", kind="mergesort").copy()
        next_allowed = -1
        records: list[dict] = []
        for _, row in part.iterrows():
            idx = int(row["confirm_idx"])
            if idx <= next_allowed:
                continue
            outcome, end_idx = first_passage_close(
                prices, idx, int(row["wave_direction"]), threshold
            )
            rec = row.to_dict()
            rec["outcome"] = outcome
            rec["resolve_idx"] = int(end_idx)
            rec["time_to_event_bars"] = int(end_idx - idx)
            records.append(rec)
            next_allowed = int(end_idx)
        parts.append(pd.DataFrame(records))
    nonempty = [p for p in parts if not p.empty]
    if not nonempty:
        return pd.DataFrame()
    return pd.concat(nonempty, ignore_index=True)


def fit_model(train: pd.DataFrame, features: list[str]) -> Pipeline | None:
    clean = train.dropna(subset=features + ["y"]).copy()
    if len(clean) < 30 or clean["y"].nunique() < 2:
        return None
    pipe = Pipeline(
        [
            ("sc", StandardScaler()),
            (
                "lr",
                LogisticRegression(
                    C=1.0,
                    penalty="l2",
                    solver="lbfgs",
                    fit_intercept=True,
                    class_weight=None,
                    max_iter=1000,
                ),
            ),
        ]
    )
    pipe.fit(clean[features].to_numpy(dtype=float), clean["y"].to_numpy(dtype=int))
    return pipe


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


def property_reversion_stats(part: pd.DataFrame) -> dict:
    clean = part.loc[
        part["z"].notna()
        & part["next_z"].notna()
        & (part["z"].abs() >= EXTREME_Z)
    ].copy()
    if clean.empty:
        return {"n": 0}
    z = clean["z"].to_numpy(dtype=float)
    nz = clean["next_z"].to_numpy(dtype=float)
    corr = None
    if len(clean) >= 3 and np.std(z) > 0 and np.std(nz) > 0:
        corr = float(np.corrcoef(z, nz)[0, 1])
    return {
        "n": int(len(clean)),
        "share_abs_next_z_lower_than_abs_current_z": float(np.mean(np.abs(nz) < np.abs(z))),
        "median_abs_next_z_minus_abs_current_z": float(np.median(np.abs(nz) - np.abs(z))),
        "corr_current_z_next_z": corr,
    }


def summarize_property(events: pd.DataFrame, raw_table: pd.DataFrame, prop: str) -> dict:
    event_part = events.loc[events["property_id"].eq(prop)].copy()
    raw_part = raw_table.loc[raw_table["property_id"].eq(prop)].copy()
    resolved = event_part.loc[event_part["outcome"].isin(["reversion", "extension"])].copy()
    if not resolved.empty:
        resolved["y"] = resolved["outcome"].eq("reversion").astype(int)
    dev = resolved.loc[resolved["day"] <= DEV_END].copy()
    stability = resolved.loc[
        (resolved["day"] >= STAB_START) & (resolved["day"] <= STAB_END)
    ].copy()

    baseline_features = ["severity"]
    augmented_features = ["severity", "z"]
    baseline_model = fit_model(dev, baseline_features)
    augmented_model = fit_model(dev, augmented_features)

    annual = {}
    for year in (2020, 2021, 2022):
        yp = stability.loc[stability["day"].str.startswith(str(year))].copy()
        annual[str(year)] = {
            "baseline": score_model(baseline_model, yp, baseline_features),
            "augmented": score_model(augmented_model, yp, augmented_features),
        }

    pooled = {
        "baseline": score_model(baseline_model, stability, baseline_features),
        "augmented": score_model(augmented_model, stability, augmented_features),
    }
    if (
        pooled["baseline"].get("status") == "scored"
        and pooled["augmented"].get("status") == "scored"
    ):
        pooled["augmented_minus_baseline_brier"] = float(
            pooled["augmented"]["brier"] - pooled["baseline"]["brier"]
        )
        pooled["augmented_minus_baseline_log_loss"] = float(
            pooled["augmented"]["log_loss"] - pooled["baseline"]["log_loss"]
        )

    return {
        "inventory": {
            "normalized_observations": int(raw_part["z"].notna().sum()),
            "price_outcome_events": int(len(event_part)),
            "resolved": int(len(resolved)),
            "censored": int((event_part["outcome"] == "censored").sum()),
            "dev_resolved": int(len(dev)),
            "stability_resolved": int(len(stability)),
        },
        "price_path_model_comparison": {"pooled_stability": pooled, "annual": annual},
        "property_reversion": {
            "DEV": property_reversion_stats(raw_part.loc[raw_part["day"] <= DEV_END]),
            "STABILITY": property_reversion_stats(
                raw_part.loc[
                    (raw_part["day"] >= STAB_START)
                    & (raw_part["day"] <= STAB_END)
                ]
            ),
            "annual": {
                str(year): property_reversion_stats(
                    raw_part.loc[raw_part["day"].str.startswith(str(year))]
                )
                for year in (2020, 2021, 2022)
            },
        },
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
    scale_results = {}
    for scale in SCALES:
        waves = common.detect_waves(prices, thresholds[scale])
        raw_table = build_property_table(frame, prices, waves, thresholds[scale])
        events = add_price_outcomes(raw_table, prices, thresholds[scale])
        scale_results[scale] = {
            "threshold": float(thresholds[scale]),
            "completed_wave_count": int(len(waves)),
            "properties": {
                prop: summarize_property(events, raw_table, prop) for prop in PROPERTY_IDS
            },
        }

    receipt = {
        "schema_id": "factorlab_reversal_mean_reversion_R5_stage1_receipt@1.0",
        "session_date": "2026-09-08",
        "program_identity": "broad_reversal_mean_reversion_discovery_program_v1",
        "research_identity": "R5_statistical_state_extremes_stage1_v1",
        "stage": "local_R5_stage1_screen_complete_pending_cloud_adjudication",
        "code_commit": git_head(),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "common_data_roles": str(DATA_ROLES.relative_to(ROOT)),
        "scale_contract": str(SCALE_CONTRACT.relative_to(ROOT)),
        "runner_sha256": sha256(Path(__file__)),
        "source": source_audit,
        "vol_ref_dev_median_rvol20": float(vol_ref),
        "directional_change_thresholds": {k: float(v) for k, v in thresholds.items()},
        "results": scale_results,
        "properties_exact": list(PROPERTY_IDS),
        "scales_exact": list(SCALES),
        "reference_window": REFERENCE_WINDOW,
        "descriptive_extreme_abs_z": EXTREME_Z,
        "reserve_2023_2025_opened": False,
        "2026_rows_loaded": False,
        "scale_search_performed": False,
        "z_threshold_search_performed": False,
        "volatility_window_search_performed": False,
        "event_density_window_search_performed": False,
        "interaction_or_ensemble_search_performed": False,
        "probability_calibration_performed": False,
        "binary_threshold_selection_performed": False,
        "deep_or_frequency_model_used": False,
        "trading_return_used": False,
        "raw_event_rows_written_to_repo": False,
        "scientifically_fresh": False,
        "production_authority": False,
    }
    dump_json(args.output.resolve(), receipt)

    usage = {
        "schema_id": "factorlab_reversal_mean_reversion_R5_stage1_data_usage@1.0",
        "session_date": "2026-09-08",
        "research_identity": "R5_statistical_state_extremes_stage1_v1",
        "opened": {
            "CSI1000_2015-01-05_to_2019-12-31": "development_material",
            "CSI1000_2020-01-01_to_2022-12-31": "chronological_stability_not_fresh",
        },
        "sealed_or_unopened": {
            "CSI1000_2023-01-01_to_2025-12-31_internal_reserve": True,
            "all_2026_rows": True,
        },
        "raw_rows_written_to_repo": False,
        "aggregate_outputs_only": True,
        "trading_return_used": False,
        "scientifically_fresh": False,
        "production_authority": False,
    }
    dump_json(args.usage_output.resolve(), usage)

    print(
        "RMR_R5_STAGE1_RESULT",
        json.dumps(
            {
                "scales": list(SCALES),
                "properties": list(PROPERTY_IDS),
                "reserve_2023_2025_opened": False,
                "2026_rows_loaded": False,
                "trading_return_used": False,
            },
            sort_keys=True,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
