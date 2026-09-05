#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
OUT_PATH = ROOT / "artifacts/research/us_feature_clock_alignment_diagnostic.json"


def _find_col(columns: list[str], exact: tuple[str, ...], contains: tuple[str, ...]) -> str:
    lower = {str(c).lower(): str(c) for c in columns}
    for name in exact:
        if name.lower() in lower:
            return lower[name.lower()]
    for c in columns:
        lc = str(c).lower()
        if any(token.lower() in lc for token in contains):
            return str(c)
    raise KeyError((columns, exact, contains))


def _load_raw_us() -> pd.DataFrame:
    raw = pd.read_parquet(US_PATH).copy()
    cols = [str(c) for c in raw.columns]
    d = _find_col(cols, ("date", "trading_day"), ("date", "day"))
    n = _find_col(cols, ("NASDAQCOM", "nasdaq"), ("nasdaq",))
    v = _find_col(cols, ("VIXCLS", "vix"), ("vix",))
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[d], errors="coerce").dt.normalize(),
            "nasdaq": pd.to_numeric(raw[n], errors="coerce"),
            "vix": pd.to_numeric(raw[v], errors="coerce"),
        }
    ).dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    return out.reset_index(drop=True)


def _series_candidates(us: pd.DataFrame, level_col: str, target_days: pd.Series) -> pd.DataFrame:
    s = us.loc[us[level_col].notna(), ["date", level_col]].copy().reset_index(drop=True)
    level = s[level_col].to_numpy(dtype=float)
    dates = s["date"].to_numpy(dtype="datetime64[ns]")
    pct = np.full(len(s), np.nan)
    logret = np.full(len(s), np.nan)
    diff = np.full(len(s), np.nan)
    pct[1:] = level[1:] / level[:-1] - 1.0
    logret[1:] = np.log(level[1:] / level[:-1])
    diff[1:] = level[1:] - level[:-1]

    target = target_days.to_numpy(dtype="datetime64[ns]")
    end_idx = np.searchsorted(dates, target, side="left") - 1
    valid = end_idx >= 1
    out = pd.DataFrame(index=target_days.index)
    out["source_date"] = pd.NaT
    out["pct"] = np.nan
    out["log"] = np.nan
    out["diff"] = np.nan
    out["level"] = np.nan
    out.loc[valid, "source_date"] = pd.to_datetime(dates[end_idx[valid]])
    out.loc[valid, "pct"] = pct[end_idx[valid]]
    out.loc[valid, "log"] = logret[end_idx[valid]]
    out.loc[valid, "diff"] = diff[end_idx[valid]]
    out.loc[valid, "level"] = level[end_idx[valid]]
    return out


def _fit_relation(panel_feature: pd.Series, candidate: pd.Series) -> dict:
    y = pd.to_numeric(panel_feature, errors="coerce")
    x = pd.to_numeric(candidate, errors="coerce")
    m = y.notna() & x.notna()
    yy = y.loc[m].to_numpy(dtype=float)
    xx = x.loc[m].to_numpy(dtype=float)
    if len(xx) < 3 or np.std(xx) == 0:
        return {"n": int(len(xx)), "corr": float("nan")}
    X = np.column_stack([np.ones(len(xx)), xx])
    coef, *_ = np.linalg.lstsq(X, yy, rcond=None)
    fitted = X @ coef
    resid = yy - fitted
    return {
        "n": int(len(xx)),
        "corr": float(np.corrcoef(xx, yy)[0, 1]),
        "intercept": float(coef[0]),
        "slope": float(coef[1]),
        "residual_rmse": float(np.sqrt(np.mean(resid**2))),
        "direct_mae": float(np.mean(np.abs(yy - xx))),
        "direct_max_abs": float(np.max(np.abs(yy - xx))),
    }


def main() -> None:
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    us = _load_raw_us()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31") or us["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 row detected")

    nas = _series_candidates(us, "nasdaq", panel["trading_day"])
    vix = _series_candidates(us, "vix", panel["trading_day"])
    result = {
        "schema_id": "overnight_open_us_feature_clock_alignment_diagnostic@1.0",
        "data_max_china_day": str(panel["trading_day"].max().date()),
        "data_max_us_day": str(us["date"].max().date()),
        "raw_us_rows": int(len(us)),
        "raw_missing": {
            "nasdaq": int(us["nasdaq"].isna().sum()),
            "vix": int(us["vix"].isna().sum()),
            "either": int((us["nasdaq"].isna() | us["vix"].isna()).sum()),
            "nasdaq_only_available": int((us["nasdaq"].notna() & us["vix"].isna()).sum()),
            "vix_only_available": int((us["vix"].notna() & us["nasdaq"].isna()).sum()),
        },
        "panel_us_nasdaq_relation": {
            name: _fit_relation(panel["us_nasdaq"], nas[name]) for name in ["pct", "log", "diff", "level"]
        },
        "panel_us_vix_chg_relation": {
            name: _fit_relation(panel["us_vix_chg"], vix[name]) for name in ["pct", "log", "diff", "level"]
        },
        "source_date_checks": {
            "nasdaq_strictly_before_china": bool((nas.loc[nas["source_date"].notna(), "source_date"] < panel.loc[nas["source_date"].notna(), "trading_day"]).all()),
            "vix_strictly_before_china": bool((vix.loc[vix["source_date"].notna(), "source_date"] < panel.loc[vix["source_date"].notna(), "trading_day"]).all()),
        },
        "authority": {
            "measurement_diagnostic_only": True,
            "fresh_oos": False,
            "production": False,
            "registry_mutation": False,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
