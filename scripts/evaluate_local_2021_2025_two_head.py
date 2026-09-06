#!/usr/bin/env python3
"""One-shot local 2021-2025 confirmation of the frozen two-head candidate.

Fit both frozen heads on 2015-2020 before any 2021+ target is scored.
Do not retune features, alphas, thresholds, calendar exceptions, or heads.
Trading return is not a gate. Production authority remains false.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from select_clock_candidates_dev import add_us_interval_features

def resolve_source(env_name: str, local_default: Path, pack_relative: str) -> Path:
    """Prefer env, then the original local files, then the 2015-2025 cloud pack.

    The pack stops on 2025-12-31 and does not contain the sealed 2026 blackbox.
    """
    override = os.environ.get(env_name)
    if override:
        return Path(override)
    if local_default.exists():
        return local_default
    pack_path = ROOT / pack_relative
    if pack_path.exists():
        return pack_path
    return local_default


FACTORLAB_ROOT = Path("/home/starryocean/桌面/量化/baylum terminal 0.4.1/factor_lab")
ANNOTATED_PANEL = resolve_source(
    "OVERNIGHT_ANNOTATED_PANEL",
    FACTORLAB_ROOT / "artifacts/market_state/timing_layer2_overnight_gap_ledger_v1_2/annotated_panel.parquet",
    "data/high_open_dev_2015_2025/annotated_panel.parquet",
)
DATAHUB_1M = resolve_source(
    "OVERNIGHT_DATAHUB_1M",
    Path(
        "/home/starryocean/桌面/量化/unified_datahub/.runtime/live/exports/"
        "factorlab_unified_index_kline_v3_20260824/1m_official.parquet"
    ),
    "data/high_open_dev_2015_2025/1m_official.parquet",
)
FRED_NDQ = resolve_source(
    "OVERNIGHT_FRED_NASDAQ",
    FACTORLAB_ROOT / "tmp/csi1000_overnight_gap_model_v2/fred_nasdaq.csv",
    "data/high_open_dev_2015_2025/fred_nasdaq.csv",
)
FRED_VIX = resolve_source(
    "OVERNIGHT_FRED_VIX",
    FACTORLAB_ROOT / "tmp/csi1000_overnight_gap_model_v2/fred_vix.csv",
    "data/high_open_dev_2015_2025/fred_vix.csv",
)

FIT_START = "2015-01-05"
FIT_END = "2020-12-31"
VAL_START = "2021-01-01"
VAL_END = "2025-12-31"
SYMBOL = "000852.SH"
CLOCKS = ("09:31", "11:30", "13:01", "14:00", "15:00")
CANDIDATE_SHA = "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"
TAIL_ABS_GAP = 0.003
YEAR_BEAT_MIN = 3
FIT_FREEZE_PATH = ROOT / "docs/research/cloud_session_20260906_local_2021_2025_fit_freeze_v1.json"
RECEIPT_PATH = ROOT / "docs/research/cloud_session_20260906_local_2021_2025_two_head_receipt_v1.json"
DATA_USAGE_PATH = ROOT / "docs/governance/local_session_20260906_2021_2025_data_usage.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def candidate_digest(selected_spec: dict) -> str:
    payload = {key: value for key, value in selected_spec.items() if key != "sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_us(path_ndq: Path, path_vix: Path, max_date: str | None = None) -> pd.DataFrame:
    ndq = pd.read_csv(path_ndq)
    vix = pd.read_csv(path_vix)
    ndq["date"] = pd.to_datetime(ndq["observation_date"])
    vix["date"] = pd.to_datetime(vix["observation_date"])
    ndq["nasdaq"] = pd.to_numeric(ndq["NASDAQCOM"], errors="coerce")
    vix["vix"] = pd.to_numeric(vix["VIXCLS"], errors="coerce")
    us = ndq.merge(vix[["date", "vix"]], on="date", how="outer").sort_values("date")
    if max_date is not None:
        us = us.loc[us["date"] <= pd.Timestamp(max_date)].copy()
    us["us_nasdaq"] = us["nasdaq"].pct_change(fill_method=None)
    us["us_vix_chg"] = us["vix"].pct_change(fill_method=None)
    return us.dropna(subset=["us_nasdaq"]).reset_index(drop=True)


def attach_us(frame: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
    usd = us.set_index("date")
    nasdaq: list[float] = []
    vix: list[float] = []
    for day in pd.to_datetime(frame["trading_day"]):
        hist = usd.loc[usd.index < day]
        if hist.empty:
            nasdaq.append(np.nan)
            vix.append(np.nan)
            continue
        nasdaq.append(float(hist["us_nasdaq"].iloc[-1]))
        last = hist["us_vix_chg"].iloc[-1]
        vix.append(float(last) if np.isfinite(last) else np.nan)
    out = frame.copy()
    out["us_nasdaq"] = nasdaq
    out["us_vix_chg"] = vix
    return out


def load_hours(path_1m: Path, start: str, end: str) -> pd.DataFrame:
    minutes = pd.read_parquet(
        path_1m,
        filters=[
            ("symbol", "==", SYMBOL),
            ("trading_day", ">=", start),
            ("trading_day", "<=", end),
        ],
        columns=["trading_day", "timestamp", "open", "close"],
    )
    minutes["clock"] = minutes["timestamp"].astype(str).str.slice(11, 16)
    minutes = minutes.loc[minutes["clock"].isin(CLOCKS)].copy()
    minutes["close"] = pd.to_numeric(minutes["close"], errors="coerce")
    minutes["open"] = pd.to_numeric(minutes["open"], errors="coerce")
    minutes["trading_day"] = minutes["trading_day"].astype(str)
    wide = minutes.pivot_table(index="trading_day", columns="clock", values="close", aggfunc="last")
    opens = minutes.loc[minutes["clock"] == "09:31", ["trading_day", "open"]].drop_duplicates("trading_day")
    wide = wide.join(opens.set_index("trading_day"))
    hours = pd.DataFrame({"trading_day": wide.index.astype(str)})
    hours["daytime"] = (wide["15:00"] / wide["open"] - 1.0).to_numpy()
    hours["afternoon"] = (wide["15:00"] / wide["13:01"] - 1.0).to_numpy()
    hours["last_hour"] = (wide["15:00"] / wide["14:00"] - 1.0).to_numpy()
    hours["missing_clocks"] = wide[list(CLOCKS)].isna().any(axis=1).to_numpy()
    return hours


def add_domestic_features(raw: pd.DataFrame, hours: pd.DataFrame) -> pd.DataFrame:
    frame = raw.merge(hours, on="trading_day", how="left").sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    close = pd.to_numeric(frame["close_1500"], errors="coerce")
    gap = pd.to_numeric(frame["overnight_gap"], errors="coerce")
    frame["gap"] = gap
    frame["r1"] = close.shift(1) / close.shift(2) - 1.0
    frame["r20"] = close.shift(1) / close.shift(21) - 1.0
    frame["abs_r1"] = frame["r1"].abs()
    frame["prev_daytime"] = pd.to_numeric(frame["daytime"], errors="coerce").shift(1)
    frame["prev_afternoon"] = pd.to_numeric(frame["afternoon"], errors="coerce").shift(1)
    frame["prev_last_hour"] = pd.to_numeric(frame["last_hour"], errors="coerce").shift(1)
    frame["prev_gap"] = gap.shift(1)
    frame["overnight_trend_5"] = gap.shift(1).rolling(5, min_periods=5).mean()
    frame["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    cal = pd.to_numeric(frame["calendar_gap_days"], errors="coerce")
    frame["holiday_reopen"] = (cal >= 4).astype(float)
    frame["weekend"] = (cal == 3).astype(float)
    return frame


def assert_dev_reconstruction(frozen: pd.DataFrame) -> dict:
    raw = pd.read_parquet(
        ANNOTATED_PANEL,
        filters=[("trading_day", ">=", FIT_START), ("trading_day", "<=", FIT_END)],
    )
    raw["trading_day"] = raw["trading_day"].astype(str)
    hours = load_hours(DATAHUB_1M, FIT_START, FIT_END)
    frame = add_domestic_features(raw, hours)
    us = load_us(FRED_NDQ, FRED_VIX, max_date=FIT_END)
    frame = attach_us(frame, us)
    frozen_idx = frozen.set_index("trading_day")
    recon_idx = frame.set_index("trading_day")
    if set(frozen_idx.index) != set(recon_idx.index):
        raise RuntimeError("2015-2020 trading_day mismatch versus frozen package panel")
    cols = [
        "open_0931",
        "close_1500",
        "day_high",
        "day_low",
        "prev_close",
        "gap",
        "close_from_open",
        "calendar_gap_days",
        "r1",
        "r20",
        "abs_r1",
        "prev_gap",
        "overnight_trend_5",
        "prev_daytime",
        "prev_last_hour",
        "prev_afternoon",
        "rvol20",
        "weekend",
        "holiday_reopen",
        "us_nasdaq",
        "us_vix_chg",
    ]
    report: dict[str, float] = {}
    for col in cols:
        left_col = "overnight_gap" if col == "gap" and "overnight_gap" in recon_idx.columns and col not in recon_idx.columns else col
        if col == "gap":
            left = pd.to_numeric(recon_idx["gap"], errors="coerce")
        else:
            left = pd.to_numeric(recon_idx[left_col], errors="coerce")
        right = pd.to_numeric(frozen_idx[col], errors="coerce")
        diff = (left - right).to_numpy(dtype=float)
        na_mismatch = int((left.isna() ^ right.isna()).sum())
        max_abs = float(np.nanmax(np.abs(diff))) if len(diff) else 0.0
        if na_mismatch != 0 or not np.isfinite(max_abs) or max_abs > 0.0:
            raise RuntimeError(f"2015-2020 reconstruction drifted on {col}: max_abs={max_abs} na_mismatch={na_mismatch}")
        report[col] = max_abs
    frozen_us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    frozen_us["date"] = pd.to_datetime(frozen_us["date"])
    merged = us.merge(frozen_us, on="date", suffixes=("_local", "_pkg"))
    for col in ["nasdaq", "vix", "us_nasdaq", "us_vix_chg"]:
        max_abs = float(np.nanmax(np.abs(pd.to_numeric(merged[f"{col}_local"], errors="coerce") - pd.to_numeric(merged[f"{col}_pkg"], errors="coerce"))))
        if max_abs > 0.0:
            raise RuntimeError(f"2015-2020 US reconstruction drifted on {col}: max_abs={max_abs}")
        report[f"us_{col}"] = max_abs
    if len(us) != len(frozen_us) or set(us["date"]) != set(frozen_us["date"]):
        raise RuntimeError("2015-2020 US date inventory mismatch")
    return report


def complete_mask(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    return x.notna().all(axis=1) & y.notna()


def fit_head(train: pd.DataFrame, cols: list[str], alpha: float) -> tuple[Pipeline, pd.Series]:
    mask = complete_mask(train, cols)
    x = train.loc[mask, cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(train.loc[mask, "gap"], errors="coerce")
    pipe = Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    pipe.fit(x, y)
    return pipe, mask


def predict_head(pipe: Pipeline, frame: pd.DataFrame, cols: list[str], mask: pd.Series) -> pd.Series:
    x = frame.loc[mask, cols].apply(pd.to_numeric, errors="coerce")
    return pd.Series(pipe.predict(x), index=x.index)


def corr_or_none(left: np.ndarray, right: np.ndarray) -> float | None:
    if len(left) < 3 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return None
    value = float(np.corrcoef(left, right)[0, 1])
    return value if np.isfinite(value) else None


def mag_metrics(y: np.ndarray, mag: np.ndarray) -> dict:
    actual = np.abs(y)
    err = actual - mag
    return {
        "n": int(len(actual)),
        "corr_abs_gap": corr_or_none(actual, mag),
        "mae_abs_gap": float(np.mean(np.abs(err))),
        "rmse_abs_gap": float(np.sqrt(np.mean(err**2))),
    }


def signed_metrics(y: np.ndarray, pred: np.ndarray, direction_up: np.ndarray) -> dict:
    err = y - pred
    return {
        "signed_gap_ic": corr_or_none(y, pred),
        "signed_gap_mae": float(np.mean(np.abs(err))),
        "signed_gap_rmse": float(np.sqrt(np.mean(err**2))),
        "direction_hit": float(np.mean(direction_up == (y >= 0.0))),
    }


def tail_metrics(y: np.ndarray, mag: np.ndarray, direction_up: np.ndarray) -> dict:
    tail = np.abs(y) > TAIL_ABS_GAP
    if int(tail.sum()) == 0:
        return {
            "n": 0,
            "tail_abs_gap_gt_30bp_direction_hit": None,
            "tail_abs_gap_gt_30bp_magnitude_mae": None,
            "tail_abs_gap_gt_30bp_magnitude_rmse": None,
        }
    yt = y[tail]
    mt = mag[tail]
    dt = direction_up[tail]
    err = np.abs(yt) - mt
    return {
        "n": int(tail.sum()),
        "tail_abs_gap_gt_30bp_direction_hit": float(np.mean(dt == (yt >= 0.0))),
        "tail_abs_gap_gt_30bp_magnitude_mae": float(np.mean(np.abs(err))),
        "tail_abs_gap_gt_30bp_magnitude_rmse": float(np.sqrt(np.mean(err**2))),
    }


def pack_model(pipe: Pipeline, cols: list[str], alpha: float, n_train: int) -> dict:
    scaler: StandardScaler = pipe.named_steps["sc"]
    ridge: Ridge = pipe.named_steps["ridge"]
    return {
        "pipeline": f"StandardScaler + Ridge(alpha={alpha})",
        "alpha": float(alpha),
        "features": cols,
        "n_train": int(n_train),
        "scaler_mean": [float(x) for x in scaler.mean_],
        "scaler_scale": [float(x) for x in scaler.scale_],
        "coef": [float(x) for x in ridge.coef_],
        "intercept": float(ridge.intercept_),
    }


def gt(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and left > right


def lt(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and left < right


def main() -> int:
    selected = load_json(ROOT / "docs/governance/cloud_session_20260906_two_head_selected_v1.json")
    protocol = load_json(ROOT / "docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json")
    spec = selected["selected_spec"]
    digest = candidate_digest(spec)
    if digest != CANDIDATE_SHA or spec.get("sha256") != CANDIDATE_SHA or protocol["candidate_sha256"] != CANDIDATE_SHA:
        raise RuntimeError(f"frozen candidate SHA mismatch: {digest}")
    direction_cols = list(spec["direction_head"]["features"])
    magnitude_cols = list(spec["magnitude_head"]["features"])
    if float(spec["direction_head"]["alpha"]) != 1.0 or float(spec["magnitude_head"]["alpha"]) != 100.0:
        raise RuntimeError("frozen head alphas drifted")
    if spec["magnitude_head"]["variant"] != "abs_frozen_clock_signed_prediction":
        raise RuntimeError("magnitude head variant drifted")

    frozen = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    frozen_us = pd.read_parquet(ROOT / "data/development/us_nasdaq_vix.parquet")
    if str(pd.to_datetime(frozen["trading_day"]).max().date()) > FIT_END:
        raise RuntimeError("frozen package panel leaked post-2020 rows")
    reconstruction = assert_dev_reconstruction(frozen)

    fit_frame = add_us_interval_features(frozen, frozen_us)
    fit_days = pd.to_datetime(fit_frame["trading_day"])
    fit_frame = fit_frame.loc[(fit_days >= FIT_START) & (fit_days <= FIT_END)].copy()
    direction_pipe, direction_mask = fit_head(fit_frame, direction_cols, 1.0)
    magnitude_pipe, magnitude_mask = fit_head(fit_frame, magnitude_cols, 100.0)
    fit_freeze = {
        "schema_id": "overnight_open_two_head_local_fit_freeze@1.0",
        "candidate_sha256": digest,
        "fit_window": {"start": FIT_START, "end": FIT_END},
        "validation_window_not_opened": {"start": VAL_START, "end": VAL_END},
        "n_fit_rows": int(len(fit_frame)),
        "n_fit_direction": int(direction_mask.sum()),
        "n_fit_magnitude": int(magnitude_mask.sum()),
        "direction_head": pack_model(direction_pipe, direction_cols, 1.0, int(direction_mask.sum())),
        "magnitude_head": pack_model(magnitude_pipe, magnitude_cols, 100.0, int(magnitude_mask.sum())),
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "package_panel": sha256(ROOT / "data/development/csi1000_open_pit_panel.parquet"),
            "package_us": sha256(ROOT / "data/development/us_nasdaq_vix.parquet"),
            "package_1m": sha256(ROOT / "data/development/1m_official.parquet"),
            "candidate_spec": sha256(ROOT / "docs/governance/cloud_session_20260906_two_head_selected_v1.json"),
            "protocol": sha256(ROOT / "docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json"),
        },
        "fresh_oos": False,
        "production_authority": False,
        "note": "models fitted on 2015-2020 only; 2021-2025 targets were not scored at freeze time",
    }
    dump_json(FIT_FREEZE_PATH, fit_freeze)

    raw = pd.read_parquet(
        ANNOTATED_PANEL,
        filters=[("trading_day", ">=", FIT_START), ("trading_day", "<=", VAL_END)],
    )
    raw["trading_day"] = raw["trading_day"].astype(str)
    hours = load_hours(DATAHUB_1M, FIT_START, VAL_END)
    local_us = load_us(FRED_NDQ, FRED_VIX, max_date=VAL_END)
    built = add_domestic_features(raw, hours)
    built = attach_us(built, local_us)
    built = add_us_interval_features(built, local_us.rename(columns={"date": "date"}))
    days = pd.to_datetime(built["trading_day"])
    val = built.loc[(days >= VAL_START) & (days <= VAL_END)].copy()
    if val.empty:
        raise RuntimeError("2021-2025 validation window is empty")
    if str(pd.to_datetime(val["trading_day"]).min().date()) < VAL_START:
        raise RuntimeError("validation slice leaked pre-2021 rows")
    if str(pd.to_datetime(val["trading_day"]).max().date()) > VAL_END:
        raise RuntimeError("validation slice leaked post-2025 rows")

    union_cols = list(dict.fromkeys(direction_cols + magnitude_cols))
    usable = complete_mask(val, union_cols)
    y = pd.to_numeric(val.loc[usable, "gap"], errors="coerce").to_numpy(dtype=float)
    base_pred = predict_head(direction_pipe, val, direction_cols, usable).to_numpy(dtype=float)
    clock_pred = predict_head(magnitude_pipe, val, magnitude_cols, usable).to_numpy(dtype=float)
    direction_up = base_pred >= 0.0
    baseline_mag = np.abs(base_pred)
    candidate_mag = np.abs(clock_pred)
    candidate_signed_pred = np.where(direction_up, 1.0, -1.0) * candidate_mag
    years = pd.to_datetime(val.loc[usable, "trading_day"]).dt.year.to_numpy()

    baseline_primary = mag_metrics(y, baseline_mag)
    candidate_primary = mag_metrics(y, candidate_mag)
    baseline_signed = signed_metrics(y, base_pred, direction_up)
    candidate_signed = signed_metrics(y, candidate_signed_pred, direction_up)
    baseline_primary["direction_hit"] = baseline_signed["direction_hit"]
    candidate_primary["direction_hit"] = candidate_signed["direction_hit"]
    baseline_tail = tail_metrics(y, baseline_mag, direction_up)
    candidate_tail = tail_metrics(y, candidate_mag, direction_up)

    per_year: dict[str, dict] = {}
    year_beats = 0
    corr_positive_every_year = True
    for year in [2021, 2022, 2023, 2024, 2025]:
        mask = years == year
        y_year = y[mask]
        b_year = baseline_mag[mask]
        c_year = candidate_mag[mask]
        d_year = direction_up[mask]
        base = mag_metrics(y_year, b_year)
        cand = mag_metrics(y_year, c_year)
        base_signed = signed_metrics(y_year, base_pred[mask], d_year)
        cand_signed = signed_metrics(y_year, candidate_signed_pred[mask], d_year)
        base["direction_hit"] = base_signed["direction_hit"]
        cand["direction_hit"] = cand_signed["direction_hit"]
        beat_mae = lt(cand["mae_abs_gap"], base["mae_abs_gap"])
        beat_rmse = lt(cand["rmse_abs_gap"], base["rmse_abs_gap"])
        if cand["corr_abs_gap"] is None or cand["corr_abs_gap"] <= 0.0:
            corr_positive_every_year = False
        if beat_mae and beat_rmse:
            year_beats += 1
        per_year[str(year)] = {
            "baseline": base,
            "candidate": cand,
            "beat_mae": beat_mae,
            "beat_rmse": beat_rmse,
            "beat_both": bool(beat_mae and beat_rmse),
        }

    direction_equal = bool(np.array_equal(direction_up, base_pred >= 0.0)) and candidate_primary["direction_hit"] == baseline_primary["direction_hit"]
    gates = {
        "direction_hit_equals_baseline": direction_equal,
        "pooled_corr_abs_gap_higher": gt(candidate_primary["corr_abs_gap"], baseline_primary["corr_abs_gap"]),
        "pooled_mae_abs_gap_lower": lt(candidate_primary["mae_abs_gap"], baseline_primary["mae_abs_gap"]),
        "pooled_rmse_abs_gap_lower": lt(candidate_primary["rmse_abs_gap"], baseline_primary["rmse_abs_gap"]),
        "corr_abs_gap_positive_every_full_year": corr_positive_every_year,
        "beat_both_mae_rmse_in_at_least_3_of_5_years": year_beats >= YEAR_BEAT_MIN,
        "year_both_beats": year_beats,
    }
    passed = all(
        [
            gates["direction_hit_equals_baseline"],
            gates["pooled_corr_abs_gap_higher"],
            gates["pooled_mae_abs_gap_lower"],
            gates["pooled_rmse_abs_gap_lower"],
            gates["corr_abs_gap_positive_every_full_year"],
            gates["beat_both_mae_rmse_in_at_least_3_of_5_years"],
        ]
    )
    decision = (
        "research_candidate_local_2021_2025_confirmed"
        if passed
        else "two_head_candidate_not_confirmed_retain_frozen_baseline"
    )

    receipt = {
        "schema_id": "overnight_open_two_head_local_fresh_receipt@1.0",
        "session_date": "2026-09-06",
        "candidate": "docs/governance/cloud_session_20260906_two_head_selected_v1.json",
        "protocol": "docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json",
        "fit_freeze": str(FIT_FREEZE_PATH.relative_to(ROOT)),
        "candidate_sha256": digest,
        "fit_window": {"start": FIT_START, "end": FIT_END},
        "validation_window": {"start": VAL_START, "end": VAL_END},
        "instrument": SYMBOL,
        "n_fit_rows": int(len(fit_frame)),
        "n_fit_direction": int(direction_mask.sum()),
        "n_fit_magnitude": int(magnitude_mask.sum()),
        "n_validation_rows": int(len(val)),
        "n_validation_complete": int(usable.sum()),
        "n_validation_dropped_missing": int((~usable).sum()),
        "missing_clock_rows": int(pd.Series(val.get("missing_clocks", False)).fillna(False).astype(bool).sum()) if "missing_clocks" in val.columns else None,
        "validation_min_day": str(pd.to_datetime(val["trading_day"]).min().date()),
        "validation_max_day": str(pd.to_datetime(val["trading_day"]).max().date()),
        "primary_metrics": {
            "baseline": baseline_primary,
            "candidate": candidate_primary,
        },
        "secondary_metrics": {
            "baseline": {**baseline_signed, **baseline_tail},
            "candidate": {**candidate_signed, **candidate_tail},
        },
        "per_year_primary_metrics": per_year,
        "pass_gate": gates,
        "passed": passed,
        "decision": decision,
        "fresh_oos": True,
        "production_authority": False,
        "trading_return_used_in_gate": False,
        "parameter_search_after_open": False,
        "source_hashes": {
            "package_panel": sha256(ROOT / "data/development/csi1000_open_pit_panel.parquet"),
            "package_us": sha256(ROOT / "data/development/us_nasdaq_vix.parquet"),
            "package_1m": sha256(ROOT / "data/development/1m_official.parquet"),
            "annotated_panel": sha256(ANNOTATED_PANEL),
            "datahub_1m_export": sha256(DATAHUB_1M),
            "fred_nasdaq": sha256(FRED_NDQ),
            "fred_vix": sha256(FRED_VIX),
            "candidate_spec": sha256(ROOT / "docs/governance/cloud_session_20260906_two_head_selected_v1.json"),
            "protocol": sha256(ROOT / "docs/governance/cloud_session_20260906_local_2021_2025_protocol_v1.json"),
            "runner": sha256(Path(__file__)),
        },
        "local_source_paths": {
            "annotated_panel": str(ANNOTATED_PANEL),
            "datahub_1m_export": str(DATAHUB_1M),
            "fred_nasdaq": str(FRED_NDQ),
            "fred_vix": str(FRED_VIX),
        },
        "repository_visibility_at_receipt": "private",
        "raw_2021_2025_rows_written_to_bounded_repo": False,
    }
    dump_json(RECEIPT_PATH, receipt)
    dump_json(
        DATA_USAGE_PATH,
        {
            "schema_id": "overnight_open_local_2021_2025_data_usage@1.0",
            "session_date": "2026-09-06",
            "2015-01-05_to_2020-12-31": "fit_only_repeat_of_consumed_development_material",
            "2019-01-01_to_2020-12-31": "consumed_holdout_not_reused_to_select_or_retune",
            "2021-01-01_to_2025-12-31": "fresh_challenge_opened_once_after_fit_freeze",
            "post_2025-12-31": "unread",
            "fresh_oos": True,
            "production_authority": False,
            "raw_validation_rows_persisted_in_bounded_repo": False,
        },
    )
    print("LOCAL_2021_2025_TWO_HEAD_RECEIPT", json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
