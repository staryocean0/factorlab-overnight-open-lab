#!/usr/bin/env python3
"""Frozen 2015-2020 development diagnostic for OFP-B4 driver coherence.

Tests one preregistered nonlinear driver-agreement coordinate against normalized
CSI1000 opening gap. Reads only the connector-readable 2015-2020 development
carriers and never opens the reusable 2021-2025 BLACKBOX.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = tuple(range(2015, 2021))
TARGET = "opening_gap_rvol"
CANDIDATE = "driver_coherence"
BASELINE_CONTROLS = [
    "r1",
    "r20",
    "abs_r1",
    "prev_gap",
    "overnight_trend_5",
    "prev_daytime",
    "prev_last_hour",
    "prev_afternoon",
    "log_rvol20",
    "weekend",
    "holiday_reopen",
    "global_risk_z",
    "china_offshore_z",
    "fx_cny_z",
]
ANNUAL_MIN_N = 150
POOLED_MIN_N = 900


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return y - design @ coef


def r2(y: np.ndarray, pred: np.ndarray) -> float:
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot <= 0:
        return float("nan")
    return 1.0 - float(np.sum((y - pred) ** 2)) / ss_tot


def trailing_rms_prev(values: pd.Series) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def linear_diag(frame: pd.DataFrame, min_n: int) -> dict:
    cols = [*BASELINE_CONTROLS, CANDIDATE, TARGET]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < min_n:
        return {"n": int(len(x)), "status": "insufficient"}

    y = x[TARGET].to_numpy(float)
    xb = x[BASELINE_CONTROLS].to_numpy(float)
    interaction = x[CANDIDATE].to_numpy(float)
    xc = np.column_stack([xb, interaction])

    db = np.column_stack([np.ones(len(xb)), xb])
    dc = np.column_stack([np.ones(len(xc)), xc])
    bb, *_ = np.linalg.lstsq(db, y, rcond=None)
    bc, *_ = np.linalg.lstsq(dc, y, rcond=None)
    rb = r2(y, db @ bb)
    rc = r2(y, dc @ bc)

    i_resid = residualize(interaction, xb)
    y_resid = residualize(y, xb)
    if np.std(i_resid) == 0 or np.std(y_resid) == 0:
        partial_corr = None
    else:
        value = float(np.corrcoef(i_resid, y_resid)[0, 1])
        partial_corr = value if np.isfinite(value) else None

    z = x[[*BASELINE_CONTROLS, CANDIDATE, TARGET]].copy()
    for col in z.columns:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            return {"n": int(len(x)), "status": "degenerate"}
        z[col] = (z[col] - float(z[col].mean())) / sd
    zx = z[[*BASELINE_CONTROLS, CANDIDATE]].to_numpy(float)
    zy = z[TARGET].to_numpy(float)
    zdesign = np.column_stack([np.ones(len(zx)), zx])
    zcoef, *_ = np.linalg.lstsq(zdesign, zy, rcond=None)

    return {
        "n": int(len(x)),
        "status": "ok",
        "partial_corr": partial_corr,
        "baseline_r2": rb,
        "candidate_r2": rc,
        "delta_r2": rc - rb,
        "standardized_driver_coherence_coefficient": float(zcoef[-1]),
    }


def load_frames(factor_root: Path, driver_root: Path) -> tuple[pd.DataFrame, dict]:
    frames = []
    hashes = {}
    factor_required = {
        "trading_day", "gap", "r1", "r20", "abs_r1", "prev_gap",
        "overnight_trend_5", "prev_daytime", "prev_last_hour",
        "prev_afternoon", "rvol20", "weekend", "holiday_reopen",
        "us_nasdaq", "us_vix_chg",
    }
    driver_required = {
        "trading_day", "holiday_reopen", "a50_channel_mode",
        "a50_channel_return", "a50_target_end_time",
        "hkma_usdcny_closure_return",
    }
    for year in YEARS:
        fp = factor_root / f"factor_panel_{year}.csv"
        dp = driver_root / f"driver_external_{year}.csv"
        f = pd.read_csv(fp)
        d = pd.read_csv(dp)
        if factor_required.difference(f.columns):
            raise RuntimeError(f"factor shard {year} missing columns: {sorted(factor_required.difference(f.columns))}")
        if driver_required.difference(d.columns):
            raise RuntimeError(f"driver shard {year} missing columns: {sorted(driver_required.difference(d.columns))}")
        f["trading_day"] = pd.to_datetime(f["trading_day"], errors="raise").dt.normalize()
        d["trading_day"] = pd.to_datetime(d["trading_day"], errors="raise").dt.normalize()
        if not f["trading_day"].dt.year.eq(year).all() or not d["trading_day"].dt.year.eq(year).all():
            raise RuntimeError(f"year boundary violation in {year}")
        merged = f.merge(
            d[[
                "trading_day", "a50_channel_mode", "a50_channel_return",
                "a50_target_end_time", "hkma_usdcny_closure_return",
            ]],
            on="trading_day",
            how="inner",
            validate="one_to_one",
        )
        merged["year"] = year
        frames.append(merged)
        hashes[str(year)] = {
            "factor_panel": {"path": str(fp), "sha256": sha256(fp)},
            "driver_external": {"path": str(dp), "sha256": sha256(dp)},
        }
    out = pd.concat(frames, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
    if out["trading_day"].min() != pd.Timestamp("2015-01-05") or out["trading_day"].max() != pd.Timestamp("2020-12-31"):
        raise RuntimeError("unexpected merged development boundary")
    if out["trading_day"].duplicated().any():
        raise RuntimeError("duplicate trading_day after carrier merge")
    return out, hashes


def build_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    x["rvol20"] = pd.to_numeric(x["rvol20"], errors="coerce")
    x = x.loc[np.isfinite(x["rvol20"]) & x["rvol20"].gt(0)].copy()

    for raw in ["us_nasdaq", "us_vix_chg", "a50_channel_return", "hkma_usdcny_closure_return"]:
        x[raw] = pd.to_numeric(x[raw], errors="coerce")
        x[f"{raw}_rms60_prev"] = trailing_rms_prev(x[raw])

    x["nasdaq_risk_z"] = x["us_nasdaq"] / x["us_nasdaq_rms60_prev"]
    x["vix_risk_z"] = -x["us_vix_chg"] / x["us_vix_chg_rms60_prev"]
    x["global_risk_z"] = 0.5 * (x["nasdaq_risk_z"] + x["vix_risk_z"])
    x["china_offshore_z"] = x["a50_channel_return"] / x["a50_channel_return_rms60_prev"]
    x["fx_cny_z"] = -x["hkma_usdcny_closure_return"] / x["hkma_usdcny_closure_return_rms60_prev"]

    denom = x["global_risk_z"].abs() + x["china_offshore_z"].abs() + x["fx_cny_z"].abs()
    x[CANDIDATE] = np.where(
        np.isfinite(denom) & denom.gt(0),
        (x["global_risk_z"] + x["china_offshore_z"] + x["fx_cny_z"]) / denom,
        np.nan,
    )
    x["log_rvol20"] = np.log(x["rvol20"])
    x[TARGET] = pd.to_numeric(x["gap"], errors="coerce") / x["rvol20"]
    return x


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor-runtime-root", type=Path, required=True)
    ap.add_argument("--driver-runtime-root", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--carrier-receipt", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != "overnight_driver_coherence_v1":
        raise RuntimeError("wrong B4 protocol identity")
    if protocol.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("unexpected B4 development window")
    if protocol.get("candidate_increment") != [CANDIDATE]:
        raise RuntimeError("candidate differs from frozen B4 protocol")
    if protocol.get("baseline_controls") != BASELINE_CONTROLS:
        raise RuntimeError("baseline differs from frozen B4 protocol")
    if protocol.get("target") != TARGET:
        raise RuntimeError("target differs from frozen B4 protocol")

    carrier_receipt = json.loads(args.carrier_receipt.read_text(encoding="utf-8"))
    if carrier_receipt.get("a50_clock_integrity") != "PASS":
        raise RuntimeError("A50 carrier integrity not PASS")
    if carrier_receipt.get("hkma_causal_timing_integrity") != "PASS":
        raise RuntimeError("HKMA carrier integrity not PASS")
    if carrier_receipt.get("target_rows_after_2020_loaded") is not False:
        raise RuntimeError("driver carrier crossed post-2020 boundary")
    if carrier_receipt.get("2021_2025_text_shards_generated") is not False:
        raise RuntimeError("driver carrier materialized BLACKBOX text")

    factor_manifest_path = args.factor_runtime_root / "manifest.json"
    driver_manifest_path = args.driver_runtime_root / "manifest.json"
    factor_manifest = json.loads(factor_manifest_path.read_text(encoding="utf-8"))
    driver_manifest = json.loads(driver_manifest_path.read_text(encoding="utf-8"))
    if factor_manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary changed")
    if driver_manifest.get("published_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("driver runtime publication boundary changed")
    if driver_manifest.get("withheld_years") != [2021, 2022, 2023, 2024, 2025]:
        raise RuntimeError("driver runtime withheld-year boundary changed")

    raw, source_hashes = load_frames(args.factor_runtime_root, args.driver_runtime_root)
    dev = build_coordinates(raw)
    if dev["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise RuntimeError("post-2020 row loaded")

    diagnostics = {
        "pooled": linear_diag(dev, POOLED_MIN_N),
        "by_year": {},
    }
    for year in YEARS:
        diagnostics["by_year"][str(year)] = linear_diag(dev.loc[dev["year"].eq(year)], ANNUAL_MIN_N)

    receipt = {
        "schema_id": "overnight_driver_agreement_disagreement_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": "overnight_driver_coherence_v1",
        "phase": "mechanism_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "product_family": "OFP-B4_driver_agreement_disagreement",
        "target": TARGET,
        "factor": CANDIDATE,
        "baseline_controls": BASELINE_CONTROLS,
        "normalization": {
            "method": "lagged_trailing_RMS",
            "window": 60,
            "min_periods": 20,
            "shift": 1,
        },
        "diagnostics": diagnostics,
        "source_hashes": source_hashes,
        "factor_runtime_manifest": {"path": str(factor_manifest_path), "sha256": sha256(factor_manifest_path)},
        "driver_runtime_manifest": {"path": str(driver_manifest_path), "sha256": sha256(driver_manifest_path)},
        "driver_carrier_receipt": {"path": str(args.carrier_receipt), "sha256": sha256(args.carrier_receipt)},
        "protocol": {"path": str(args.protocol), "sha256": sha256(args.protocol)},
        "target_rows_after_2020_loaded": False,
        "reusable_blackbox_2021_2025_opened": False,
        "alternate_normalization_search": False,
        "driver_weight_search": False,
        "channel_drop_add_search": False,
        "pairwise_agreement_search": False,
        "threshold_search": False,
        "bucket_search": False,
        "alternate_target_search": False,
        "post_open_horizon_search": False,
        "trading_return_optimization": False,
        "cost_model_used": False,
        "auto_promotion": False,
        "main_agent_review_required": True,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("DRIVER_AGREEMENT_DISAGREEMENT_DEV_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
