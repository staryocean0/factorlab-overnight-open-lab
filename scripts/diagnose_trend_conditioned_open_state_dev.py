#!/usr/bin/env python3
"""Development-only diagnostic for `overnight_trend_conditioned_open_state_v1`.

Reads detailed target/price outcomes only for 2019-2020. It tests whether the
continuous interaction between prior trend and observed opening gap adds
short-horizon information beyond their main effects and simple causal context.
This is not a trading backtest and does not create categorical trend buckets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

DEV_START = pd.Timestamp("2019-01-01")
DEV_END = pd.Timestamp("2020-12-31")
SYMBOL = "000852.SH"
CLOCKS = ["09:35", "09:50", "10:05", "10:35"]
BASELINE_CONTROLS = [
    "observed_gap_rvol",
    "trend20_rvol",
    "r1",
    "prev_daytime",
    "holiday_reopen",
]
HORIZONS = {
    "ret_0935_0950": "09:50",
    "ret_0935_1005": "10:05",
    "ret_0935_1035": "10:35",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def short_horizon_returns_from_clocks(bars: pd.DataFrame) -> pd.DataFrame:
    bars = bars.copy()
    bars["trading_day"] = bars["trading_day"].astype(str)
    bars["clock"] = bars["clock"].astype(str)
    bars = bars.loc[bars["clock"].isin(CLOCKS)].copy()
    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    wide = bars.pivot_table(index="trading_day", columns="clock", values="close", aggfunc="last")
    if "09:35" not in wide.columns:
        raise RuntimeError("09:35 reference clock missing from development minute data")
    out = pd.DataFrame({"trading_day": wide.index.astype(str)})
    for name, end_clock in HORIZONS.items():
        if end_clock not in wide.columns:
            raise RuntimeError(f"{end_clock} target clock missing from development minute data")
        out[name] = (wide[end_clock] / wide["09:35"] - 1.0).to_numpy()
    return out.reset_index(drop=True)


def load_short_horizon_returns(path: Path) -> pd.DataFrame:
    bars = pd.read_parquet(
        path,
        filters=[
            ("symbol", "==", SYMBOL),
            ("trading_day", ">=", "2019-01-01"),
            ("trading_day", "<=", "2020-12-31"),
        ],
        columns=["trading_day", "timestamp", "close"],
    ).copy()
    bars["clock"] = bars["timestamp"].astype(str).str.slice(11, 16)
    return short_horizon_returns_from_clocks(bars)


def load_dev_pack_paths(dev_pack_dir: Path) -> tuple[Path, Path, Path]:
    manifest_path = dev_pack_dir / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"missing dev pack manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("research_identity") != "overnight_trend_conditioned_open_state_v1":
        raise RuntimeError("wrong research identity in dev pack manifest")
    files = manifest.get("files") or {}
    base_panel_csv = dev_pack_dir / str(files.get("base_panel_csv", "base_panel_2019_2020.csv"))
    minute_clocks_csv = dev_pack_dir / str(files.get("minute_clocks_csv", "minute_clocks_2019_2020.csv"))
    for path in (base_panel_csv, minute_clocks_csv):
        if not path.is_file():
            raise RuntimeError(f"missing dev pack file: {path}")
    return manifest_path, base_panel_csv, minute_clocks_csv


def load_short_horizon_returns_csv(path: Path) -> pd.DataFrame:
    bars = pd.read_csv(path)
    required = {"trading_day", "clock", "close"}
    missing = required.difference(bars.columns)
    if missing:
        raise RuntimeError(f"minute dev pack missing columns: {sorted(missing)}")
    return short_horizon_returns_from_clocks(bars)


def load_dev_panel_from_csv(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    required = {"trading_day", "gap", "r20", "rvol20", "r1", "prev_daytime", "holiday_reopen"}
    missing = required.difference(panel.columns)
    if missing:
        raise RuntimeError(f"base dev pack missing columns: {sorted(missing)}")
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > DEV_END:
        raise RuntimeError("base panel contains rows after the authorized 2020 development boundary")
    return panel.loc[panel["trading_day"].between(DEV_START, DEV_END)].copy()


def build_dev_frame(panel: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    dev = panel.copy()
    dev["observed_gap"] = pd.to_numeric(dev["gap"], errors="coerce")
    dev["rvol20"] = pd.to_numeric(dev["rvol20"], errors="coerce")
    valid_rvol = np.isfinite(dev["rvol20"]) & dev["rvol20"].gt(0)
    dev = dev.loc[valid_rvol].copy()
    dev["observed_gap_rvol"] = dev["observed_gap"] / dev["rvol20"]
    dev["trend20_rvol"] = pd.to_numeric(dev["r20"], errors="coerce") / (np.sqrt(20.0) * dev["rvol20"])
    dev["trend_gap_interaction"] = dev["observed_gap_rvol"] * dev["trend20_rvol"]
    dev["trading_day"] = dev["trading_day"].dt.strftime("%Y-%m-%d")
    dev = dev.merge(future, on="trading_day", how="inner", validate="one_to_one")
    dev["year"] = pd.to_datetime(dev["trading_day"]).dt.year
    return dev


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
    cols = [*BASELINE_CONTROLS, "trend_gap_interaction", target]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 10:
        return {"n": int(len(x)), "status": "insufficient"}

    y = x[target].to_numpy(float)
    xb = x[BASELINE_CONTROLS].to_numpy(float)
    interaction = x["trend_gap_interaction"].to_numpy(float)
    xc = np.column_stack([xb, interaction])

    db = np.column_stack([np.ones(len(xb)), xb])
    dc = np.column_stack([np.ones(len(xc)), xc])
    bb, *_ = np.linalg.lstsq(db, y, rcond=None)
    bc, *_ = np.linalg.lstsq(dc, y, rcond=None)
    rb = r2(y, db @ bb)
    rc = r2(y, dc @ bc)

    interaction_resid = residualize(interaction, xb)
    y_resid = residualize(y, xb)
    if np.std(interaction_resid) == 0 or np.std(y_resid) == 0:
        partial_corr = None
    else:
        value = float(np.corrcoef(interaction_resid, y_resid)[0, 1])
        partial_corr = value if np.isfinite(value) else None

    z = x[[*BASELINE_CONTROLS, "trend_gap_interaction", target]].copy()
    for col in z.columns:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            return {"n": int(len(x)), "status": "degenerate"}
        z[col] = (z[col] - float(z[col].mean())) / sd
    zx = z[[*BASELINE_CONTROLS, "trend_gap_interaction"]].to_numpy(float)
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-panel", type=Path)
    ap.add_argument("--minute-bars", type=Path)
    ap.add_argument("--dev-pack-dir", type=Path)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != "overnight_trend_conditioned_open_state_v1":
        raise RuntimeError("wrong trend-conditioned opening-state protocol")

    if args.dev_pack_dir is not None:
        if args.base_panel is not None or args.minute_bars is not None:
            raise RuntimeError("use either --dev-pack-dir or parquet inputs, not both")
        manifest_path, base_panel_csv, minute_clocks_csv = load_dev_pack_paths(args.dev_pack_dir)
        panel = load_dev_panel_from_csv(base_panel_csv)
        future = load_short_horizon_returns_csv(minute_clocks_csv)
        source_hashes = {
            "base_panel": sha256(base_panel_csv),
            "minute_bars": sha256(minute_clocks_csv),
            "protocol": sha256(args.protocol),
            "dev_pack_manifest": sha256(manifest_path),
        }
    else:
        if args.base_panel is None or args.minute_bars is None:
            raise RuntimeError("parquet mode requires --base-panel and --minute-bars")
        panel = pd.read_parquet(args.base_panel).copy()
        panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
        if panel["trading_day"].max() > DEV_END:
            raise RuntimeError("base panel contains rows after the authorized 2020 development boundary")
        panel = panel.loc[panel["trading_day"].between(DEV_START, DEV_END)].copy()
        future = load_short_horizon_returns(args.minute_bars)
        source_hashes = {
            "base_panel": sha256(args.base_panel),
            "minute_bars": sha256(args.minute_bars),
            "protocol": sha256(args.protocol),
        }

    dev = build_dev_frame(panel, future)

    result = {"pooled": {}, "by_year": {"2019": {}, "2020": {}}}
    for horizon in HORIZONS:
        result["pooled"][horizon] = linear_diag(dev, horizon)
        for year in (2019, 2020):
            result["by_year"][str(year)][horizon] = linear_diag(dev.loc[dev["year"] == year], horizon)

    receipt = {
        "schema_id": "overnight_trend_conditioned_open_state_dev_diagnostic@1.0",
        "session_date": "2026-09-11",
        "research_identity": "overnight_trend_conditioned_open_state_v1",
        "phase": "mechanism_diagnostic",
        "development_window": "2019-01-01..2020-12-31",
        "product_family": "OFP-C1_prior_trend_context_x_OFP-A2_observed_open_geometry",
        "factor": "trend_gap_interaction",
        "baseline_controls": BASELINE_CONTROLS,
        "horizons": list(HORIZONS),
        "diagnostics": result,
        "source_hashes": source_hashes,
        "target_rows_after_2020_loaded": False,
        "reusable_blackbox_2021_2025_opened": False,
        "candidate_family_search": False,
        "trend_bucket_search": False,
        "threshold_search": False,
        "horizon_search": False,
        "volatility_bucket_search": False,
        "trading_return_optimization": False,
        "opening_surprise_rescue_performed": False,
        "auto_promotion": False,
        "main_agent_review_required": True,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("TREND_CONDITIONED_OPEN_STATE_DEV_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
