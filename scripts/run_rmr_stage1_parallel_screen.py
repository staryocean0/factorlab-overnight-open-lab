#!/usr/bin/env python3
"""Run the frozen broad reversal / mean-reversion Stage-1 parallel screen.

This is a mechanism screen, not a strategy backtest. It uses only the declared
CSI1000 2015-2025 development material, two predeclared causal
directional-change scale pairings, and the frozen R1/R2/R3 definitions.

The runner writes aggregate receipts only. It never reads 2026 rows, never
optimizes trading return, and never selects a trading threshold.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_ROLE = ROOT / "docs/governance/reversal_mean_reversion_stage1_common_data_role_v1.json"
PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_stage1_execution_protocol_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/research/local_rmr_stage1_parallel_screen_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_rmr_stage1_parallel_screen_data_usage_v1.json"

EXPECTED_SOURCE_SHA256 = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
START = "2015-01-05"
END = "2025-12-31"
EXPECTED_CLOCKS = tuple(
    pd.date_range("2000-01-01 09:31", "2000-01-01 11:30", freq="min").strftime("%H:%M").tolist()
    + pd.date_range("2000-01-01 13:01", "2000-01-01 15:00", freq="min").strftime("%H:%M").tolist()
)
BLOCKS = {
    "DEV_A": ("2015-01-05", "2018-12-31"),
    "DEV_B": ("2019-01-01", "2022-12-31"),
    "DEV_C": ("2023-01-01", "2025-12-31"),
}
MAX_SESSION_HORIZON = 5
R2_TRIGGER_FRAC = 0.10
R3_MIN_RESID = 0.50
EPS = 1e-12


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def block_for_day(day: str) -> str | None:
    for name, (start, end) in BLOCKS.items():
        if start <= day <= end:
            return name
    return None


def safe_log_loss(y: np.ndarray, p: np.ndarray) -> float:
    pp = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    yy = np.asarray(y, dtype=float)
    return float(-np.mean(yy * np.log(pp) + (1 - yy) * np.log(1 - pp)))


def brier(y: np.ndarray, p: np.ndarray) -> float:
    yy = np.asarray(y, dtype=float)
    pp = np.asarray(p, dtype=float)
    return float(np.mean((pp - yy) ** 2))


def auc(y: np.ndarray, p: np.ndarray) -> float | None:
    yy = np.asarray(y, dtype=int)
    if len(yy) == 0 or np.unique(yy).size < 2:
        return None
    return float(roc_auc_score(yy, np.asarray(p, dtype=float)))


def fit_logistic(train: pd.DataFrame, valid: pd.DataFrame, features: list[str]) -> dict:
    tr = train.dropna(subset=features + ["outcome"]).copy()
    va = valid.dropna(subset=features + ["outcome"]).copy()
    if len(tr) < 30 or len(va) == 0 or tr["outcome"].nunique() < 2:
        return {"status": "evidence_insufficient", "train_n": int(len(tr)), "validation_n": int(len(va))}
    pipe = Pipeline([
        ("sc", StandardScaler()),
        ("model", LogisticRegression(
            C=1.0, penalty="l2", solver="lbfgs", fit_intercept=True,
            class_weight=None, max_iter=1000,
        )),
    ])
    xtr = tr[features].to_numpy(dtype=float)
    ytr = tr["outcome"].to_numpy(dtype=int)
    xva = va[features].to_numpy(dtype=float)
    yva = va["outcome"].to_numpy(dtype=int)
    pipe.fit(xtr, ytr)
    prob = pipe.predict_proba(xva)[:, 1]
    model = pipe.named_steps["model"]
    sc = pipe.named_steps["sc"]
    return {
        "status": "scored",
        "train_n": int(len(tr)),
        "validation_n": int(len(va)),
        "validation_event_rate": float(np.mean(yva)),
        "brier": brier(yva, prob),
        "log_loss": safe_log_loss(yva, prob),
        "roc_auc": auc(yva, prob),
        "coef_standardized": [float(v) for v in model.coef_[0]],
        "intercept": float(model.intercept_[0]),
        "scaler_mean": [float(v) for v in sc.mean_],
        "scaler_scale": [float(v) for v in sc.scale_],
    }


@dataclass(frozen=True)
class Wave:
    start_idx: int
    end_idx: int
    confirm_idx: int
    start_confirm_idx: int | None
    start_logp: float
    end_logp: float
    direction: int
    threshold_sigma: float
    segment_id: int

    @property
    def move(self) -> float:
        return float(self.end_logp - self.start_logp)

    @property
    def abs_move(self) -> float:
        return abs(self.move)


@dataclass(frozen=True)
class ParentState:
    signed_drift_ratio: float
    absolute_drift_ratio: float
    overlap_ratio: float
    parent_path_efficiency: float
    parent_range_width: float
    envelope_low: float
    envelope_high: float
    structural_low: float
    structural_high: float
    short_to_parent_volatility_ratio: float
    segment_id: int


def read_source(path: Path) -> pd.DataFrame:
    actual = sha256(path)
    if actual != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"common source SHA mismatch: {actual} != {EXPECTED_SOURCE_SHA256}")
    frame = pd.read_parquet(
        path,
        filters=[("symbol", "==", SYMBOL), ("trading_day", ">=", START), ("trading_day", "<=", END)],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError("common Stage1 source is empty")
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    if set(frame["symbol"]) != {SYMBOL}:
        raise RuntimeError("unexpected symbol in common Stage1 source")
    if frame["trading_day"].min() < START or frame["trading_day"].max() > END:
        raise RuntimeError("source crossed frozen Stage1 development window")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    for c in ["open", "high", "low", "close"]:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def inventory_and_path(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    expected = set(EXPECTED_CLOCKS)
    valid_days: list[str] = []
    incomplete: list[dict] = []
    duplicate_days = 0
    for day, part in frame.groupby("trading_day", sort=True):
        clocks = part["clock"].tolist()
        unique = set(clocks)
        duplicates = len(clocks) != len(unique)
        missing = sorted(expected - unique)
        unexpected = sorted(unique - expected)
        numeric_bad = bool(part[["open", "high", "low", "close"]].isna().any().any())
        if len(part) == 240 and not duplicates and not missing and not unexpected and not numeric_bad:
            valid_days.append(str(day))
        else:
            duplicate_days += int(duplicates)
            incomplete.append({
                "trading_day": str(day), "rows": int(len(part)),
                "missing_count": int(len(missing)), "unexpected_count": int(len(unexpected)),
                "duplicate": bool(duplicates), "non_numeric_ohlc": numeric_bad,
            })
    good = frame.loc[frame["trading_day"].isin(valid_days)].copy()
    if good.empty:
        raise RuntimeError("no exact complete 240-clock Stage1 days")
    good = good.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)

    all_days = sorted(frame["trading_day"].unique())
    day_pos = {d: i for i, d in enumerate(all_days)}
    segment = 0
    last_pos = None
    day_segment: dict[str, int] = {}
    for day in valid_days:
        pos = day_pos[day]
        if last_pos is not None and pos != last_pos + 1:
            segment += 1
        day_segment[day] = segment
        last_pos = pos
    good["segment_id"] = good["trading_day"].map(day_segment).astype(int)
    good["log_close"] = np.log(good["close"].to_numpy(dtype=float))
    good["log_high"] = np.log(good["high"].to_numpy(dtype=float))
    good["log_low"] = np.log(good["low"].to_numpy(dtype=float))

    daily_close = (
        good.loc[good["clock"].eq("15:00"), ["trading_day", "close"]]
        .drop_duplicates("trading_day", keep="last").sort_values("trading_day").reset_index(drop=True)
    )
    daily_close["log_close"] = np.log(daily_close["close"].to_numpy(dtype=float))
    daily_close["daily_ret"] = daily_close["log_close"].diff()
    daily_close["sigma20_for_day"] = daily_close["daily_ret"].rolling(20, min_periods=20).std(ddof=0).shift(1)
    sigma_map = dict(zip(daily_close["trading_day"], daily_close["sigma20_for_day"]))
    good["sigma20"] = good["trading_day"].map(sigma_map)

    ord_map = {d: i for i, d in enumerate(valid_days)}
    good["session_ord"] = good["trading_day"].map(ord_map).astype(int)

    good["one_minute_log_return"] = good.groupby("segment_id", sort=False)["log_close"].diff()
    short_std = (
        good.groupby("segment_id", sort=False)["one_minute_log_return"]
        .rolling(60, min_periods=30).std(ddof=0).reset_index(level=0, drop=True)
    )
    good["short_vol_annualized"] = np.sqrt(240.0) * short_std
    good["short_to_parent_volatility_ratio"] = good["short_vol_annualized"] / good["sigma20"]
    good["abs_1m_move"] = good["one_minute_log_return"].abs().fillna(0.0)
    good["cum_abs_move_segment"] = good.groupby("segment_id", sort=False)["abs_1m_move"].cumsum()

    audit = {
        "source_rows": int(len(frame)), "observed_days": int(frame["trading_day"].nunique()),
        "exact_complete_240_days": int(len(valid_days)), "incomplete_days": int(len(incomplete)),
        "duplicate_days": int(duplicate_days), "segment_count": int(good["segment_id"].nunique()),
        "first_complete_day": str(good["trading_day"].min()), "last_complete_day": str(good["trading_day"].max()),
        "sigma20_available_days": int(daily_close["sigma20_for_day"].notna().sum()),
        "incomplete_day_examples": incomplete[:20],
    }
    return good, audit


def generate_waves(path: pd.DataFrame, threshold_sigma: float) -> list[Wave]:
    logp = path["log_close"].to_numpy(dtype=float)
    sigma = path["sigma20"].to_numpy(dtype=float)
    segment = path["segment_id"].to_numpy(dtype=int)
    waves: list[Wave] = []
    mode: int | None = None
    anchor_idx: int | None = None
    anchor_confirm_idx: int | None = None
    extreme_idx: int | None = None
    current_segment: int | None = None

    for i in range(len(path)):
        if current_segment != int(segment[i]) or not np.isfinite(sigma[i]) or sigma[i] <= 0:
            current_segment = int(segment[i]); mode = None; anchor_idx = i; anchor_confirm_idx = None; extreme_idx = i
            continue
        theta = float(threshold_sigma * sigma[i])
        if theta <= 0 or not np.isfinite(theta):
            continue
        if anchor_idx is None or extreme_idx is None:
            anchor_idx = extreme_idx = i
            continue
        if mode is None:
            up = logp[i] - logp[anchor_idx]
            dn = logp[anchor_idx] - logp[i]
            if up >= theta:
                mode = 1; extreme_idx = i
            elif dn >= theta:
                mode = -1; extreme_idx = i
            else:
                if abs(logp[i] - logp[anchor_idx]) > abs(logp[extreme_idx] - logp[anchor_idx]):
                    extreme_idx = i
            continue
        if mode > 0:
            if logp[i] >= logp[extreme_idx]:
                extreme_idx = i; continue
            if logp[extreme_idx] - logp[i] >= theta:
                if anchor_confirm_idx is not None:
                    waves.append(Wave(anchor_idx, extreme_idx, i, anchor_confirm_idx, float(logp[anchor_idx]), float(logp[extreme_idx]), 1, float(threshold_sigma), int(segment[i])))
                anchor_idx = extreme_idx; anchor_confirm_idx = i; mode = -1; extreme_idx = i
        else:
            if logp[i] <= logp[extreme_idx]:
                extreme_idx = i; continue
            if logp[i] - logp[extreme_idx] >= theta:
                if anchor_confirm_idx is not None:
                    waves.append(Wave(anchor_idx, extreme_idx, i, anchor_confirm_idx, float(logp[anchor_idx]), float(logp[extreme_idx]), -1, float(threshold_sigma), int(segment[i])))
                anchor_idx = extreme_idx; anchor_confirm_idx = i; mode = 1; extreme_idx = i
    return waves


def parent_state(path: pd.DataFrame, waves: list[Wave], confirm_indices: list[int], info_idx: int) -> ParentState | None:
    pos = bisect.bisect_right(confirm_indices, int(info_idx))
    if pos < 2:
        return None
    w1, w2 = waves[pos - 2], waves[pos - 1]
    if w1.segment_id != w2.segment_id or w2.segment_id != int(path.iloc[info_idx]["segment_id"]):
        return None
    denom = w1.abs_move + w2.abs_move
    if denom <= EPS:
        return None
    signed = float((w2.end_logp - w1.start_logp) / denom)
    int1 = (min(w1.start_logp, w1.end_logp), max(w1.start_logp, w1.end_logp))
    int2 = (min(w2.start_logp, w2.end_logp), max(w2.start_logp, w2.end_logp))
    width1, width2 = int1[1] - int1[0], int2[1] - int2[0]
    if min(width1, width2) <= EPS:
        return None
    overlap = max(0.0, min(int1[1], int2[1]) - max(int1[0], int2[0]))
    start_idx, end_idx = w1.start_idx, w2.end_idx
    if end_idx <= start_idx:
        return None
    cum = path["cum_abs_move_segment"].to_numpy(dtype=float)
    path_abs = float(cum[end_idx] - cum[start_idx])
    if path_abs <= EPS:
        return None
    low, high = float(min(int1[0], int2[0])), float(max(int1[1], int2[1]))
    short_ratio = float(path.iloc[info_idx]["short_to_parent_volatility_ratio"])
    if not np.isfinite(short_ratio) or high - low <= EPS:
        return None
    return ParentState(
        signed_drift_ratio=signed, absolute_drift_ratio=abs(signed),
        overlap_ratio=float(overlap / min(width1, width2)),
        parent_path_efficiency=float(abs(w2.end_logp - w1.start_logp) / path_abs),
        parent_range_width=float(high - low), envelope_low=low, envelope_high=high,
        structural_low=low, structural_high=high,
        short_to_parent_volatility_ratio=short_ratio, segment_id=w2.segment_id,
    )


def first_passage(path: pd.DataFrame, event_idx: int, upper_boundary: float, lower_boundary: float, upper_label: str, lower_label: str) -> dict:
    if upper_boundary <= lower_boundary:
        return {"status": "invalid_boundary", "outcome": None, "end_idx": int(event_idx)}
    event_row = path.iloc[event_idx]
    event_seg, event_ord = int(event_row["segment_id"]), int(event_row["session_ord"])
    highs, lows = path["log_high"].to_numpy(dtype=float), path["log_low"].to_numpy(dtype=float)
    seg, ords = path["segment_id"].to_numpy(dtype=int), path["session_ord"].to_numpy(dtype=int)
    for j in range(event_idx + 1, len(path)):
        if int(seg[j]) != event_seg:
            return {"status": "censored_source_break", "outcome": None, "end_idx": int(j - 1)}
        if int(ords[j]) - event_ord >= MAX_SESSION_HORIZON:
            return {"status": "censored_horizon", "outcome": None, "end_idx": int(j - 1)}
        hit_up, hit_dn = bool(highs[j] >= upper_boundary), bool(lows[j] <= lower_boundary)
        if hit_up and hit_dn:
            return {"status": "censored_same_bar_tie", "outcome": None, "end_idx": int(j)}
        if hit_up:
            return {"status": "resolved", "outcome": upper_label, "end_idx": int(j)}
        if hit_dn:
            return {"status": "resolved", "outcome": lower_label, "end_idx": int(j)}
    return {"status": "censored_end_of_data", "outcome": None, "end_idx": int(len(path) - 1)}


def score_models(events: pd.DataFrame, objects: dict[str, list[str]]) -> dict:
    resolved = events.loc[events["outcome"].notna()].copy()
    out = {"inventory": {"events_total": int(len(events)), "resolved": int(len(resolved)), "censored": int(events["outcome"].isna().sum())}, "by_block": {}, "objects": {}}
    for block in BLOCKS:
        part = events.loc[events["block"].eq(block)]
        rr = part.loc[part["outcome"].notna()]
        out["by_block"][block] = {
            "events": int(len(part)), "resolved": int(len(rr)),
            "recovery_share": None if rr.empty else float(rr["outcome"].mean()),
            "median_time_minutes": None if rr.empty else float(rr["time_to_event_minutes"].median()),
        }
    folds = [(["DEV_A"], "DEV_B"), (["DEV_A", "DEV_B"], "DEV_C")]
    for obj_id, features in objects.items():
        obj = {"features": features, "folds": []}
        for train_blocks, valid_block in folds:
            tr = resolved.loc[resolved["block"].isin(train_blocks)].copy()
            va = resolved.loc[resolved["block"].eq(valid_block)].copy()
            obj["folds"].append({"train_blocks": train_blocks, "validation_block": valid_block, **fit_logistic(tr, va, features)})
        out["objects"][obj_id] = obj
    return out


def build_r1(path: pd.DataFrame, lower_waves: list[Wave], parent_waves: list[Wave]) -> tuple[pd.DataFrame, dict]:
    pconf = [w.confirm_idx for w in parent_waves]
    rows, next_allowed, overlap_skipped = [], -1, 0
    for lw in lower_waves:
        if lw.confirm_idx < next_allowed:
            overlap_skipped += 1; continue
        info_idx = lw.start_confirm_idx
        if info_idx is None:
            continue
        ps = parent_state(path, parent_waves, pconf, info_idx)
        if ps is None or abs(ps.signed_drift_ratio) <= EPS:
            continue
        parent_sign = 1 if ps.signed_drift_ratio > 0 else -1
        if lw.direction == parent_sign:
            continue
        sigma = float(path.iloc[info_idx]["sigma20"])
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        event_price, recovery = float(path.iloc[lw.confirm_idx]["log_close"]), float(lw.start_logp)
        failure = ps.structural_low if parent_sign > 0 else ps.structural_high
        if parent_sign > 0:
            if event_price >= recovery or event_price <= failure:
                continue
            fp = first_passage(path, lw.confirm_idx, recovery, failure, "recovery", "failure")
        else:
            if event_price <= recovery or event_price >= failure:
                continue
            fp = first_passage(path, lw.confirm_idx, failure, recovery, "failure", "recovery")
        end_idx = int(fp["end_idx"]); next_allowed = end_idx + 1
        outcome = None if fp["status"] != "resolved" else (1 if fp["outcome"] == "recovery" else 0)
        move_slice = path["abs_1m_move"].iloc[max(lw.start_idx, 1):lw.end_idx + 1]
        efficiency = None if float(move_slice.sum()) <= EPS else float(lw.abs_move / move_slice.sum())
        rows.append({
            "event_idx": int(lw.confirm_idx), "trading_day": str(path.iloc[lw.confirm_idx]["trading_day"]),
            "block": block_for_day(str(path.iloc[lw.confirm_idx]["trading_day"])), "outcome": outcome,
            "censor_reason": None if outcome is not None else fp["status"], "time_to_event_minutes": int(max(0, end_idx - lw.confirm_idx)),
            "counter_move_abs_log_return_over_sigma": float(lw.abs_move / sigma),
            "counter_move_duration_trading_minutes": int(max(1, lw.end_idx - lw.start_idx)), "counter_move_path_efficiency": efficiency,
            "absolute_drift_ratio": ps.absolute_drift_ratio, "overlap_ratio": ps.overlap_ratio,
            "parent_path_efficiency": ps.parent_path_efficiency, "short_to_parent_volatility_ratio": ps.short_to_parent_volatility_ratio,
        })
    return pd.DataFrame(rows), {"overlap_skipped_lower_waves": int(overlap_skipped)}


def build_r2(path: pd.DataFrame, parent_waves: list[Wave]) -> tuple[pd.DataFrame, dict]:
    pconf = [w.confirm_idx for w in parent_waves]
    rows, next_allowed, active_minutes_skipped = [], -1, 0
    for i in range(len(path)):
        if i < next_allowed:
            active_minutes_skipped += 1; continue
        ps = parent_state(path, parent_waves, pconf, i)
        if ps is None:
            continue
        price = float(path.iloc[i]["log_close"])
        if price > ps.envelope_high:
            side, edge, outside = 1, ps.envelope_high, price - ps.envelope_high
        elif price < ps.envelope_low:
            side, edge, outside = -1, ps.envelope_low, ps.envelope_low - price
        else:
            continue
        if outside < R2_TRIGGER_FRAC * ps.parent_range_width:
            continue
        if side > 0:
            fp = first_passage(path, i, price + outside, edge, "continuation", "reentry")
        else:
            fp = first_passage(path, i, edge, price - outside, "reentry", "continuation")
        end_idx = int(fp["end_idx"]); next_allowed = end_idx + 1
        outcome = None if fp["status"] != "resolved" else (1 if fp["outcome"] == "reentry" else 0)
        rows.append({
            "event_idx": int(i), "trading_day": str(path.iloc[i]["trading_day"]), "block": block_for_day(str(path.iloc[i]["trading_day"])),
            "outcome": outcome, "censor_reason": None if outcome is not None else fp["status"],
            "time_to_event_minutes": int(max(0, end_idx - i)), "outside_distance_over_parent_range_width": float(outside / ps.parent_range_width),
            "absolute_drift_ratio": ps.absolute_drift_ratio, "overlap_ratio": ps.overlap_ratio,
            "parent_path_efficiency": ps.parent_path_efficiency, "short_to_parent_volatility_ratio": ps.short_to_parent_volatility_ratio,
        })
    return pd.DataFrame(rows), {"active_path_minutes_skipped": int(active_minutes_skipped)}


def r3_sample_table(path: pd.DataFrame, lower_waves: list[Wave], parent_waves: list[Wave]) -> pd.DataFrame:
    pconf = [w.confirm_idx for w in parent_waves]
    rows = []
    for lw in lower_waves:
        info_idx = lw.start_confirm_idx
        if info_idx is None:
            continue
        ps = parent_state(path, parent_waves, pconf, info_idx)
        if ps is None:
            continue
        sigma = float(path.iloc[info_idx]["sigma20"])
        if not np.isfinite(sigma) or sigma <= 0:
            continue
        day = str(path.iloc[lw.confirm_idx]["trading_day"])
        rows.append({
            "event_idx": int(lw.confirm_idx), "trading_day": day, "block": block_for_day(day),
            "current_move": float(lw.move / sigma), "event_sigma": sigma,
            "signed_drift_ratio": ps.signed_drift_ratio, "parent_path_efficiency": ps.parent_path_efficiency,
            "short_to_parent_volatility_ratio": ps.short_to_parent_volatility_ratio,
        })
    return pd.DataFrame(rows)


def residual_first_passage(path: pd.DataFrame, event_idx: int, residual: float, sigma: float) -> dict:
    if not np.isfinite(residual) or not np.isfinite(sigma) or sigma <= 0:
        return {"status": "invalid_residual", "outcome": None, "end_idx": event_idx}
    distance = 0.5 * abs(float(residual)) * float(sigma)
    if distance <= EPS:
        return {"status": "invalid_residual", "outcome": None, "end_idx": event_idx}
    cur = float(path.iloc[event_idx]["log_close"])
    if residual > 0:
        return first_passage(path, event_idx, cur + distance, cur - distance, "extension", "reversion")
    return first_passage(path, event_idx, cur + distance, cur - distance, "reversion", "extension")


def build_r3(path: pd.DataFrame, samples: pd.DataFrame) -> dict:
    state_features = ["signed_drift_ratio", "parent_path_efficiency", "short_to_parent_volatility_ratio"]
    folds = [(["DEV_A"], "DEV_B"), (["DEV_A", "DEV_B"], "DEV_C")]
    out = {"folds": [], "paired_events_total": 0, "overlap_skipped": 0}
    for train_blocks, valid_block in folds:
        tr = samples.loc[samples["block"].isin(train_blocks)].dropna(subset=state_features + ["current_move"]).copy()
        va = samples.loc[samples["block"].eq(valid_block)].dropna(subset=state_features + ["current_move"]).copy()
        if len(tr) < 50 or len(va) == 0:
            out["folds"].append({"train_blocks": train_blocks, "validation_block": valid_block, "status": "evidence_insufficient", "train_n": int(len(tr)), "validation_n": int(len(va))}); continue
        conditional = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=1.0, fit_intercept=True))])
        conditional.fit(tr[state_features].to_numpy(dtype=float), tr["current_move"].to_numpy(dtype=float))
        cond_expected = conditional.predict(va[state_features].to_numpy(dtype=float))
        uncond_expected = float(tr["current_move"].mean())
        va = va.copy()
        va["conditional_residual"] = va["current_move"].to_numpy(dtype=float) - cond_expected
        va["unconditional_deviation"] = va["current_move"].to_numpy(dtype=float) - uncond_expected
        paired = va.loc[(va["conditional_residual"].abs() >= R3_MIN_RESID) & (va["unconditional_deviation"].abs() >= R3_MIN_RESID)].sort_values("event_idx")
        cond_outcomes, uncond_outcomes, cond_times, uncond_times = [], [], [], []
        next_allowed, used, skipped = -1, 0, 0
        for _, row in paired.iterrows():
            idx = int(row["event_idx"])
            if idx < next_allowed:
                skipped += 1; continue
            cfp = residual_first_passage(path, idx, float(row["conditional_residual"]), float(row["event_sigma"]))
            ufp = residual_first_passage(path, idx, float(row["unconditional_deviation"]), float(row["event_sigma"]))
            next_allowed = max(int(cfp["end_idx"]), int(ufp["end_idx"])) + 1; used += 1
            co = 1 if cfp["status"] == "resolved" and cfp["outcome"] == "reversion" else 0 if cfp["status"] == "resolved" else None
            uo = 1 if ufp["status"] == "resolved" and ufp["outcome"] == "reversion" else 0 if ufp["status"] == "resolved" else None
            cond_outcomes.append(co); uncond_outcomes.append(uo)
            cond_times.append(None if co is None else int(cfp["end_idx"]) - idx); uncond_times.append(None if uo is None else int(ufp["end_idx"]) - idx)
        out["paired_events_total"] += used; out["overlap_skipped"] += skipped
        cvals, uvals = [v for v in cond_outcomes if v is not None], [v for v in uncond_outcomes if v is not None]
        ctimes, utimes = [v for v in cond_times if v is not None], [v for v in uncond_times if v is not None]
        out["folds"].append({
            "train_blocks": train_blocks, "validation_block": valid_block, "status": "scored",
            "train_n": int(len(tr)), "validation_n": int(len(va)), "paired_threshold_eligible": int(len(paired)), "paired_nonoverlap_used": int(used),
            "conditional_residual": {"resolved": int(len(cvals)), "reversion_share": None if not cvals else float(np.mean(cvals)), "median_time_minutes": None if not ctimes else float(np.median(ctimes))},
            "unconditional_deviation": {"resolved": int(len(uvals)), "reversion_share": None if not uvals else float(np.mean(uvals)), "median_time_minutes": None if not utimes else float(np.median(utimes))},
            "conditional_minus_unconditional_reversion_share": None if not cvals or not uvals else float(np.mean(cvals) - np.mean(uvals)),
            "ridge_coef_standardized": [float(v) for v in conditional.named_steps["ridge"].coef_],
            "ridge_intercept": float(conditional.named_steps["ridge"].intercept_), "unconditional_expected_move": uncond_expected,
        })
    return out


def lane_summary(events: pd.DataFrame, model_result: dict, meta: dict) -> dict:
    if events.empty:
        return {"status": "evidence_insufficient", "event_count": 0, **meta}
    resolved = events.loc[events["outcome"].notna()]
    return {
        "status": "screen_complete", "event_count": int(len(events)), "resolved_count": int(len(resolved)),
        "censored_count": int(events["outcome"].isna().sum()), "pooled_recovery_share": None if resolved.empty else float(resolved["outcome"].mean()),
        "model_comparisons": model_result, **meta,
    }


def run_pair(path: pd.DataFrame, pair: dict) -> dict:
    lower = generate_waves(path, float(pair["lower_wave_reversal_threshold_sigma"]))
    parent = generate_waves(path, float(pair["parent_wave_reversal_threshold_sigma"]))
    r1_events, r1_meta = build_r1(path, lower, parent)
    r2_events, r2_meta = build_r2(path, parent)
    r3_samples = r3_sample_table(path, lower, parent)
    r1_objects = {
        "severity_only": ["counter_move_abs_log_return_over_sigma"],
        "parent_state_only": ["absolute_drift_ratio", "overlap_ratio", "parent_path_efficiency", "short_to_parent_volatility_ratio"],
        "parent_state_plus_severity": ["counter_move_abs_log_return_over_sigma", "absolute_drift_ratio", "overlap_ratio", "parent_path_efficiency", "short_to_parent_volatility_ratio"],
    }
    r2_objects = {
        "excursion_size_only": ["outside_distance_over_parent_range_width"],
        "parent_range_state_only": ["absolute_drift_ratio", "overlap_ratio", "parent_path_efficiency"],
        "parent_range_plus_state_change": ["outside_distance_over_parent_range_width", "absolute_drift_ratio", "overlap_ratio", "parent_path_efficiency", "short_to_parent_volatility_ratio"],
    }
    r1_models = score_models(r1_events, r1_objects) if not r1_events.empty else {}
    r2_models = score_models(r2_events, r2_objects) if not r2_events.empty else {}
    r3_result = build_r3(path, r3_samples) if not r3_samples.empty else {"status": "evidence_insufficient"}
    return {
        "pairing": pair,
        "wave_inventory": {"lower_completed_waves": int(len(lower)), "parent_completed_waves": int(len(parent))},
        "R1": lane_summary(r1_events, r1_models, r1_meta),
        "R2": lane_summary(r2_events, r2_models, r2_meta),
        "R3": {
            "status": "screen_complete" if not r3_samples.empty else "evidence_insufficient",
            "completed_lower_wave_samples": int(len(r3_samples)),
            "by_block_samples": {b: int(r3_samples["block"].eq(b).sum()) for b in BLOCKS} if not r3_samples.empty else {},
            "residual_comparison": r3_result,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--usage-output", type=Path, default=USAGE)
    args = parser.parse_args()
    data_role, protocol = load_json(DATA_ROLE), load_json(PROTOCOL)
    if protocol["stage"] != "stage1_parallel_empirical_screening_semantics_frozen_before_outcome_read" or protocol["market_outcomes_opened_for_protocol_design"] is not False:
        raise RuntimeError("Stage1 execution protocol drifted or was not results blind")
    if data_role["common_dataset"]["sha256"] != EXPECTED_SOURCE_SHA256 or data_role["evidence_roles"]["2015-01-05_to_2025-12-31"]["role"] != "development_material_only":
        raise RuntimeError("common Stage1 data role drifted")
    if protocol["R2"]["excursion_trigger_fraction_of_range_width"] != R2_TRIGGER_FRAC or protocol["R3"]["minimum_abs_residual_sigma"] != R3_MIN_RESID:
        raise RuntimeError("frozen Stage1 event threshold drifted")
    source = args.source.expanduser().resolve()
    frame = read_source(source)
    path, source_audit = inventory_and_path(frame)
    pair_results = [run_pair(path, pair) for pair in data_role["first_pass_scale_pairings"]]
    receipt = {
        "schema_id": "factorlab_reversal_mean_reversion_stage1_parallel_screen_receipt@1.0",
        "session_date": "2026-09-08", "program_identity": "broad_reversal_mean_reversion_discovery_program_v1",
        "stage": "local_stage1_parallel_screen_complete_pending_cloud_comparison", "code_commit": git_head(),
        "source_path": str(source), "source_sha256": sha256(source), "source_audit": source_audit,
        "data_role": str(DATA_ROLE.relative_to(ROOT)), "execution_protocol": str(PROTOCOL.relative_to(ROOT)),
        "pair_results": pair_results, "lane_budget_equal_first_pass": True,
        "parameter_grid_search_performed": False, "scale_search_performed": False, "horizon_search_performed": False,
        "trading_return_used": False, "2026_rows_loaded": False, "raw_event_rows_written_to_repo": False,
        "deep_model_used": False, "production_authority": False,
    }
    dump_json(args.output.resolve(), receipt)
    usage = {
        "schema_id": "factorlab_reversal_mean_reversion_stage1_parallel_screen_data_usage@1.0",
        "session_date": "2026-09-08", "program_identity": "broad_reversal_mean_reversion_discovery_program_v1",
        "opened": {"CSI1000_2015-01-05_to_2025-12-31": "development_material_only"},
        "sealed_or_forbidden": {"CSI1000_2026-01-05_to_2026-08-21": True, "CSI1000_2026-08-24_to_2026-12-31": True, "broad_program_future_audit_from_2027-01-01": True},
        "raw_rows_written_to_repo": False, "aggregate_outputs_only": True, "trading_return_used": False, "production_authority": False,
    }
    dump_json(args.usage_output.resolve(), usage)
    print("RMR_STAGE1_PARALLEL_SCREEN_RESULT", json.dumps({
        "pairings": [x["pairing"]["id"] for x in pair_results],
        "R1_events": {x["pairing"]["id"]: x["R1"].get("event_count", 0) for x in pair_results},
        "R2_events": {x["pairing"]["id"]: x["R2"].get("event_count", 0) for x in pair_results},
        "R3_samples": {x["pairing"]["id"]: x["R3"].get("completed_lower_wave_samples", 0) for x in pair_results},
        "2026_rows_loaded": False, "trading_return_used": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
