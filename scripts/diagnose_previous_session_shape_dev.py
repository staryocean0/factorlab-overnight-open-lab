#!/usr/bin/env python3
"""Frozen 2015-2020 development diagnostic for OFP-C3.

Identity: overnight_previous_session_last_hour_conditioned_open_state_v1
Candidate: (prev_last_hour / rvol20) * (gap / rvol20)
Baseline includes the validated C1 trend-gap interaction. This is a mechanism
research diagnostic only; it is not a trading backtest and never reads 2021+.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS = tuple(range(2015, 2021))
HORIZONS = {
    "ret_0935_0950": "close_0950",
    "ret_0935_1005": "close_1005",
    "ret_0935_1035": "close_1035",
}
BASELINE_CONTROLS = [
    "observed_gap_rvol",
    "last_hour_rvol",
    "prev_daytime",
    "trend20_rvol",
    "trend_gap_interaction",
    "log_rvol20",
    "r1",
    "holiday_reopen",
]
CANDIDATE = "last_hour_gap_interaction"


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


def linear_diag(frame: pd.DataFrame, target: str) -> dict:
    cols = [*BASELINE_CONTROLS, CANDIDATE, target]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 10:
        return {"n": int(len(x)), "status": "insufficient"}

    y = x[target].to_numpy(float)
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

    z = x[[*BASELINE_CONTROLS, CANDIDATE, target]].copy()
    for col in z.columns:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            return {"n": int(len(x)), "status": "degenerate"}
        z[col] = (z[col] - float(z[col].mean())) / sd
    zx = z[[*BASELINE_CONTROLS, CANDIDATE]].to_numpy(float)
    zy = z[target].to_numpy(float)
    zdesign = np.column_stack([np.ones(len(zx)), zx])
    zcoef, *_ = np.linalg.lstsq(zdesign, zy, rcond=None)

    return {
        "n": int(len(x)),
        "status": "ok",
        "partial_corr": partial_corr,
        "baseline_r2": rb,
        "candidate_r2": rc,
        "delta_r2": rc - rb,
        "standardized_interaction_coefficient": float(zcoef[-1]),
    }


def load_year(root: Path, year: int) -> tuple[pd.DataFrame, dict]:
    panel_path = root / f"factor_panel_{year}.csv"
    clocks_path = root / f"opening_clocks_{year}.csv"
    if not panel_path.exists() or not clocks_path.exists():
        raise RuntimeError(f"missing runtime shard for {year}")

    panel = pd.read_csv(panel_path)
    clocks = pd.read_csv(clocks_path)
    required_panel = {
        "trading_day", "gap", "r1", "r20", "rvol20", "prev_daytime",
        "prev_last_hour", "holiday_reopen",
    }
    required_clocks = {"trading_day", "close_0935", "close_0950", "close_1005", "close_1035"}
    if required_panel.difference(panel.columns):
        raise RuntimeError(f"panel {year} missing columns: {sorted(required_panel.difference(panel.columns))}")
    if required_clocks.difference(clocks.columns):
        raise RuntimeError(f"clocks {year} missing columns: {sorted(required_clocks.difference(clocks.columns))}")

    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    clocks["trading_day"] = pd.to_datetime(clocks["trading_day"], errors="raise").dt.normalize()
    if not panel["trading_day"].dt.year.eq(year).all() or not clocks["trading_day"].dt.year.eq(year).all():
        raise RuntimeError(f"year boundary violation in {year}")

    dev = panel.merge(clocks, on="trading_day", how="inner", validate="one_to_one")
    dev["rvol20"] = pd.to_numeric(dev["rvol20"], errors="coerce")
    dev = dev.loc[np.isfinite(dev["rvol20"]) & dev["rvol20"].gt(0)].copy()
    dev["observed_gap_rvol"] = pd.to_numeric(dev["gap"], errors="coerce") / dev["rvol20"]
    dev["last_hour_rvol"] = pd.to_numeric(dev["prev_last_hour"], errors="coerce") / dev["rvol20"]
    dev["trend20_rvol"] = pd.to_numeric(dev["r20"], errors="coerce") / (np.sqrt(20.0) * dev["rvol20"])
    dev["trend_gap_interaction"] = dev["observed_gap_rvol"] * dev["trend20_rvol"]
    dev["log_rvol20"] = np.log(dev["rvol20"])
    dev[CANDIDATE] = dev["last_hour_rvol"] * dev["observed_gap_rvol"]
    for target, end_col in HORIZONS.items():
        dev[target] = pd.to_numeric(dev[end_col], errors="coerce") / pd.to_numeric(dev["close_0935"], errors="coerce") - 1.0
    dev["year"] = year

    hashes = {
        "factor_panel": {"path": str(panel_path), "sha256": sha256(panel_path)},
        "opening_clocks": {"path": str(clocks_path), "sha256": sha256(clocks_path)},
    }
    return dev, hashes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime-root", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != "overnight_previous_session_last_hour_conditioned_open_state_v1":
        raise RuntimeError("wrong C3 protocol")
    if protocol.get("development_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("unexpected C3 development window")
    if protocol.get("candidate_increment") != [CANDIDATE]:
        raise RuntimeError("candidate increment differs from frozen C3 protocol")
    if protocol.get("baseline_controls") != BASELINE_CONTROLS:
        raise RuntimeError("baseline controls differ from frozen C3 protocol")

    manifest_path = args.runtime_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("runtime carrier publication boundary changed")
    if manifest.get("withheld_years") != [2021, 2022, 2023, 2024, 2025]:
        raise RuntimeError("runtime carrier withheld-year boundary changed")

    frames: list[pd.DataFrame] = []
    source_hashes: dict[str, dict] = {}
    for year in YEARS:
        frame, hashes = load_year(args.runtime_root, year)
        frames.append(frame)
        source_hashes[str(year)] = hashes
    dev = pd.concat(frames, ignore_index=True)
    if int(dev["year"].max()) > 2020:
        raise RuntimeError("post-2020 row loaded")

    diagnostics = {
        "pooled": {},
        "by_year": {str(year): {} for year in YEARS},
    }
    for horizon in HORIZONS:
        diagnostics["pooled"][horizon] = linear_diag(dev, horizon)
        for year in YEARS:
            diagnostics["by_year"][str(year)][horizon] = linear_diag(dev.loc[dev["year"] == year], horizon)

    receipt = {
        "schema_id": "overnight_previous_session_shape_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": "overnight_previous_session_last_hour_conditioned_open_state_v1",
        "phase": "mechanism_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "product_family": "OFP-C3_previous_china_session_shape_x_OFP-A2_observed_open_geometry",
        "factor": CANDIDATE,
        "baseline_controls": BASELINE_CONTROLS,
        "horizons": list(HORIZONS),
        "diagnostics": diagnostics,
        "source_hashes": source_hashes,
        "runtime_manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "protocol": {"path": str(args.protocol), "sha256": sha256(args.protocol)},
        "target_rows_after_2020_loaded": False,
        "reusable_blackbox_2021_2025_opened": False,
        "candidate_family_search": False,
        "prev_afternoon_search": False,
        "alternate_session_window_search": False,
        "threshold_search": False,
        "bucket_search": False,
        "horizon_search": False,
        "trading_return_optimization": False,
        "cost_model_used": False,
        "auto_promotion": False,
        "main_agent_review_required": True,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PREVIOUS_SESSION_SHAPE_C3_DEV_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
