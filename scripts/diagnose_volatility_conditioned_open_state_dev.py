#!/usr/bin/env python3
"""Development-only diagnostic for `overnight_volatility_conditioned_open_state_v1`.

Uses only the bounded 2019-2020 CSV development text pack. Tests whether the
continuous interaction between pre-open volatility level and observed opening
gap adds short-horizon information beyond main effects and the validated C1
trend-conditioned interaction. This is not a trading backtest.
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
CLOCKS = ["09:35", "09:50", "10:05", "10:35"]
HORIZONS = {
    "ret_0935_0950": "09:50",
    "ret_0935_1005": "10:05",
    "ret_0935_1035": "10:35",
}
BASELINE_CONTROLS = [
    "observed_gap_rvol",
    "log_rvol20",
    "trend20_rvol",
    "trend_gap_interaction",
    "r1",
    "prev_daytime",
    "holiday_reopen",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_pack(dev_pack_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict, Path, Path, Path]:
    manifest_path = dev_pack_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_id") != "trend_open_state_dev_pack@1.0":
        raise RuntimeError("unexpected development text-pack schema")
    if manifest.get("development_window") != "2019-01-01..2020-12-31":
        raise RuntimeError("unexpected development text-pack window")
    files = manifest.get("files") or {}
    panel_path = dev_pack_dir / str(files.get("base_panel_csv", "base_panel_2019_2020.csv"))
    clocks_path = dev_pack_dir / str(files.get("minute_clocks_csv", "minute_clocks_2019_2020.csv"))
    panel = pd.read_csv(panel_path)
    clocks = pd.read_csv(clocks_path)
    return panel, clocks, manifest, manifest_path, panel_path, clocks_path


def short_horizon_returns(clocks: pd.DataFrame) -> pd.DataFrame:
    required = {"trading_day", "clock", "close"}
    missing = required.difference(clocks.columns)
    if missing:
        raise RuntimeError(f"minute text pack missing columns: {sorted(missing)}")
    bars = clocks.copy()
    bars["trading_day"] = bars["trading_day"].astype(str)
    bars["clock"] = bars["clock"].astype(str)
    bars = bars.loc[bars["clock"].isin(CLOCKS)].copy()
    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    wide = bars.pivot_table(index="trading_day", columns="clock", values="close", aggfunc="last")
    for clock in CLOCKS:
        if clock not in wide.columns:
            raise RuntimeError(f"missing frozen clock: {clock}")
    out = pd.DataFrame({"trading_day": wide.index.astype(str)})
    for name, end_clock in HORIZONS.items():
        out[name] = (wide[end_clock] / wide["09:35"] - 1.0).to_numpy()
    return out.reset_index(drop=True)


def build_frame(panel: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    required = {"trading_day", "gap", "r20", "rvol20", "r1", "prev_daytime", "holiday_reopen"}
    missing = required.difference(panel.columns)
    if missing:
        raise RuntimeError(f"base text pack missing columns: {sorted(missing)}")
    dev = panel.copy()
    dev["trading_day"] = pd.to_datetime(dev["trading_day"], errors="raise").dt.normalize()
    if dev["trading_day"].min() < DEV_START or dev["trading_day"].max() > DEV_END:
        raise RuntimeError("development text pack crosses authorized 2019-2020 boundary")
    dev["rvol20"] = pd.to_numeric(dev["rvol20"], errors="coerce")
    dev = dev.loc[np.isfinite(dev["rvol20"]) & dev["rvol20"].gt(0)].copy()
    dev["observed_gap_rvol"] = pd.to_numeric(dev["gap"], errors="coerce") / dev["rvol20"]
    dev["trend20_rvol"] = pd.to_numeric(dev["r20"], errors="coerce") / (np.sqrt(20.0) * dev["rvol20"])
    dev["trend_gap_interaction"] = dev["observed_gap_rvol"] * dev["trend20_rvol"]
    dev["log_rvol20"] = np.log(dev["rvol20"])
    dev["vol_gap_interaction"] = dev["observed_gap_rvol"] * dev["log_rvol20"]
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
    cols = [*BASELINE_CONTROLS, "vol_gap_interaction", target]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 10:
        return {"n": int(len(x)), "status": "insufficient"}

    y = x[target].to_numpy(float)
    xb = x[BASELINE_CONTROLS].to_numpy(float)
    interaction = x["vol_gap_interaction"].to_numpy(float)
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

    z = x[[*BASELINE_CONTROLS, "vol_gap_interaction", target]].copy()
    for col in z.columns:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            return {"n": int(len(x)), "status": "degenerate"}
        z[col] = (z[col] - float(z[col].mean())) / sd
    zx = z[[*BASELINE_CONTROLS, "vol_gap_interaction"]].to_numpy(float)
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
    ap.add_argument("--dev-pack-dir", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != "overnight_volatility_conditioned_open_state_v1":
        raise RuntimeError("wrong C2 protocol")

    panel, clocks, manifest, manifest_path, panel_path, clocks_path = load_pack(args.dev_pack_dir)
    future = short_horizon_returns(clocks)
    dev = build_frame(panel, future)

    result = {"pooled": {}, "by_year": {"2019": {}, "2020": {}}}
    for horizon in HORIZONS:
        result["pooled"][horizon] = linear_diag(dev, horizon)
        for year in (2019, 2020):
            result["by_year"][str(year)][horizon] = linear_diag(dev.loc[dev["year"] == year], horizon)

    receipt = {
        "schema_id": "overnight_volatility_conditioned_open_state_dev_diagnostic@1.0",
        "session_date": "2026-09-11",
        "research_identity": "overnight_volatility_conditioned_open_state_v1",
        "phase": "mechanism_diagnostic",
        "development_window": "2019-01-01..2020-12-31",
        "product_family": "OFP-C2_prior_volatility_context_x_OFP-A2_observed_open_geometry",
        "factor": "vol_gap_interaction",
        "baseline_controls": BASELINE_CONTROLS,
        "horizons": list(HORIZONS),
        "diagnostics": result,
        "source_hashes": {
            "base_panel_csv": sha256(panel_path),
            "minute_clocks_csv": sha256(clocks_path),
            "dev_pack_manifest": sha256(manifest_path),
            "protocol": sha256(args.protocol),
        },
        "source_parquet_hashes": manifest.get("source_parquet_hashes"),
        "target_rows_after_2020_loaded": False,
        "reusable_blackbox_2021_2025_opened": False,
        "candidate_family_search": False,
        "volatility_bucket_search": False,
        "threshold_search": False,
        "alternate_volatility_lookback_search": False,
        "horizon_search": False,
        "trend_bucket_search": False,
        "trading_return_optimization": False,
        "opening_surprise_rescue_performed": False,
        "auto_promotion": False,
        "main_agent_review_required": True,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("VOLATILITY_CONDITIONED_OPEN_STATE_DEV_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
