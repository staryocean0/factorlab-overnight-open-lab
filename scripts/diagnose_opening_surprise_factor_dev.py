#!/usr/bin/env python3
"""Development-only diagnostic for `overnight_open_surprise_factor_v1`.

Reads detailed target/price outcomes only for 2019-2020. It fits the frozen V6A
signed-gap model on <=2018, forms opening surprise on 2019-2020, and measures
incremental short-horizon information. This is not a trading backtest.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TRAIN_END = pd.Timestamp("2018-12-31")
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


def load_v6_module():
    path = ROOT / "scripts/run_v6a_reusable_blackbox_local.py"
    spec = importlib.util.spec_from_file_location("v6a_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen V6A authority")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fit_frozen_v6(frame: pd.DataFrame, v6) -> pd.Series:
    train = frame.loc[frame["trading_day"].le(TRAIN_END)].copy()
    dev = frame.loc[frame["trading_day"].between(DEV_START, DEV_END)].copy()
    features = list(v6.V6_FEATURES)
    xtr = train[features].apply(pd.to_numeric, errors="coerce")
    ytr = pd.to_numeric(train["gap"], errors="coerce")
    xdv = dev[features].apply(pd.to_numeric, errors="coerce")
    ydv = pd.to_numeric(dev["gap"], errors="coerce")
    mtr = xtr.notna().all(axis=1) & ytr.notna()
    mdv = xdv.notna().all(axis=1) & ydv.notna()
    if not mtr.any() or not mdv.any():
        raise RuntimeError("no complete rows for frozen V6A fit/development diagnostic")
    pipe = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
    pipe.fit(xtr.loc[mtr], ytr.loc[mtr])
    pred = pd.Series(np.nan, index=dev.index, dtype=float)
    pred.loc[mdv] = pipe.predict(xdv.loc[mdv])
    return pred


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
    bars["trading_day"] = bars["trading_day"].astype(str)
    bars["clock"] = bars["timestamp"].astype(str).str.slice(11, 16)
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


def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return y - design @ coef


def partial_corr(frame: pd.DataFrame, target: str) -> float | None:
    cols = [*BASELINE_CONTROLS, "opening_surprise_rvol", target]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 10:
        return None
    controls = x[BASELINE_CONTROLS].to_numpy(float)
    s_resid = residualize(x["opening_surprise_rvol"].to_numpy(float), controls)
    y_resid = residualize(x[target].to_numpy(float), controls)
    if np.std(s_resid) == 0 or np.std(y_resid) == 0:
        return None
    value = float(np.corrcoef(s_resid, y_resid)[0, 1])
    return value if np.isfinite(value) else None


def r2(y: np.ndarray, pred: np.ndarray) -> float:
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot <= 0:
        return float("nan")
    return 1.0 - float(np.sum((y - pred) ** 2)) / ss_tot


def linear_diag(frame: pd.DataFrame, target: str) -> dict:
    cols = [*BASELINE_CONTROLS, "opening_surprise_rvol", target]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < 10:
        return {"n": int(len(x)), "status": "insufficient"}
    y = x[target].to_numpy(float)
    xb = x[BASELINE_CONTROLS].to_numpy(float)
    xc = x[[*BASELINE_CONTROLS, "opening_surprise_rvol"]].to_numpy(float)
    db = np.column_stack([np.ones(len(xb)), xb])
    dc = np.column_stack([np.ones(len(xc)), xc])
    bb, *_ = np.linalg.lstsq(db, y, rcond=None)
    bc, *_ = np.linalg.lstsq(dc, y, rcond=None)
    rb = r2(y, db @ bb)
    rc = r2(y, dc @ bc)

    # Standardized coefficient for the increment only.
    z = x[[*BASELINE_CONTROLS, "opening_surprise_rvol", target]].copy()
    for col in z.columns:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            return {"n": int(len(x)), "status": "degenerate"}
        z[col] = (z[col] - float(z[col].mean())) / sd
    zxc = z[[*BASELINE_CONTROLS, "opening_surprise_rvol"]].to_numpy(float)
    zy = z[target].to_numpy(float)
    zdesign = np.column_stack([np.ones(len(zxc)), zxc])
    zcoef, *_ = np.linalg.lstsq(zdesign, zy, rcond=None)
    surprise_coef = float(zcoef[-1])

    positive = x["opening_surprise_rvol"] > 0
    negative = x["opening_surprise_rvol"] < 0
    return {
        "n": int(len(x)),
        "status": "ok",
        "partial_corr": partial_corr(x, target),
        "baseline_r2": rb,
        "candidate_r2": rc,
        "delta_r2": rc - rb,
        "standardized_surprise_coefficient": surprise_coef,
        "positive_surprise_mean_future_return": float(x.loc[positive, target].mean()) if positive.any() else None,
        "negative_surprise_mean_future_return": float(x.loc[negative, target].mean()) if negative.any() else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-panel", type=Path, required=True)
    ap.add_argument("--minute-bars", type=Path, required=True)
    ap.add_argument("--nasdaq", type=Path, required=True)
    ap.add_argument("--vix", type=Path, required=True)
    ap.add_argument("--hkma", type=Path, required=True)
    ap.add_argument("--holiday-a50", type=Path, required=True)
    ap.add_argument("--ordinary-a50", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != "overnight_open_surprise_factor_v1":
        raise RuntimeError("wrong Opening Surprise protocol")

    v6 = load_v6_module()
    panel = pd.read_parquet(args.base_panel).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > DEV_END:
        raise RuntimeError("base panel contains rows after the authorized 2020 development boundary")

    df = v6.add_us_complete_clock(panel, v6.read_fred(args.nasdaq, "NASDAQCOM"), v6.read_fred(args.vix, "VIXCLS"))
    df = v6.add_hkma(df, args.hkma)
    df, _, clocks_ok = v6.attach_a50(df, args.holiday_a50, args.ordinary_a50)
    if not clocks_ok:
        raise RuntimeError("A50 causal clock guard failed")

    common = df["a50_common_available"].fillna(False)
    df = df.loc[common & df["trading_day"].le(DEV_END)].copy()
    pred = fit_frozen_v6(df, v6)
    dev = df.loc[df["trading_day"].between(DEV_START, DEV_END)].copy()
    dev["expected_gap"] = pred.reindex(dev.index)
    dev["observed_gap"] = pd.to_numeric(dev["gap"], errors="coerce")
    dev["rvol20"] = pd.to_numeric(dev["rvol20"], errors="coerce")
    valid_rvol = np.isfinite(dev["rvol20"]) & dev["rvol20"].gt(0)
    dev = dev.loc[valid_rvol].copy()
    dev["opening_surprise"] = dev["observed_gap"] - dev["expected_gap"]
    dev["observed_gap_rvol"] = dev["observed_gap"] / dev["rvol20"]
    dev["opening_surprise_rvol"] = dev["opening_surprise"] / dev["rvol20"]
    dev["trend20_rvol"] = pd.to_numeric(dev["r20"], errors="coerce") / (np.sqrt(20.0) * dev["rvol20"])
    dev["trading_day"] = dev["trading_day"].dt.strftime("%Y-%m-%d")

    future = load_short_horizon_returns(args.minute_bars)
    dev = dev.merge(future, on="trading_day", how="inner", validate="one_to_one")
    dev["year"] = pd.to_datetime(dev["trading_day"]).dt.year

    result = {"pooled": {}, "by_year": {"2019": {}, "2020": {}}}
    for horizon in HORIZONS:
        result["pooled"][horizon] = linear_diag(dev, horizon)
        for year in (2019, 2020):
            result["by_year"][str(year)][horizon] = linear_diag(dev.loc[dev["year"] == year], horizon)

    receipt = {
        "schema_id": "overnight_opening_surprise_factor_dev_diagnostic@1.0",
        "session_date": "2026-09-10",
        "research_identity": "overnight_open_surprise_factor_v1",
        "phase": "mechanism_diagnostic",
        "development_window": "2019-01-01..2020-12-31",
        "upstream_prediction_identity": "V6A_plus_ordinary_A50_preauction_closure",
        "factor": "opening_surprise_rvol",
        "baseline_controls": BASELINE_CONTROLS,
        "horizons": list(HORIZONS),
        "diagnostics": result,
        "source_hashes": {
            "base_panel": sha256(args.base_panel),
            "minute_bars": sha256(args.minute_bars),
            "nasdaq": sha256(args.nasdaq),
            "vix": sha256(args.vix),
            "hkma": sha256(args.hkma),
            "holiday_a50": sha256(args.holiday_a50),
            "ordinary_a50": sha256(args.ordinary_a50),
            "protocol": sha256(args.protocol),
        },
        "target_rows_after_2020_loaded": false,
        "reusable_blackbox_2021_2025_opened": false,
        "candidate_family_search": false,
        "threshold_search": false,
        "trend_bucket_search": false,
        "horizon_search": false,
        "trading_return_optimization": false,
        "auto_promotion": false,
        "main_agent_review_required": true,
        "production_authority": false,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("OPENING_SURPRISE_DEV_DIAGNOSTIC_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
