#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
OUT_PATH = ROOT / "artifacts/research/us_feature_clock_mismatches.json"


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


def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    raw = pd.read_parquet(US_PATH).copy()
    cols = [str(c) for c in raw.columns]
    d = _find_col(cols, ("date", "trading_day"), ("date", "day"))
    n = _find_col(cols, ("NASDAQCOM", "nasdaq"), ("nasdaq",))
    v = _find_col(cols, ("VIXCLS", "vix"), ("vix",))
    us = pd.DataFrame({
        "date": pd.to_datetime(raw[d], errors="coerce").dt.normalize(),
        "nasdaq": pd.to_numeric(raw[n], errors="coerce"),
        "vix": pd.to_numeric(raw[v], errors="coerce"),
    }).dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return panel, us


def _series_table(us: pd.DataFrame, col: str) -> pd.DataFrame:
    s = us.loc[us[col].notna(), ["date", col]].copy().reset_index(drop=True)
    s["pct"] = s[col].pct_change(fill_method=None)
    s["log"] = np.log(s[col] / s[col].shift(1))
    s["prev_date"] = s["date"].shift(1)
    for k in [1, 2, 3]:
        s[f"pct_lag{k}"] = s["pct"].shift(k)
        s[f"pct_lead{k}"] = s["pct"].shift(-k)
    return s


def _align(panel: pd.DataFrame, s: pd.DataFrame) -> pd.DataFrame:
    dates = s["date"].to_numpy(dtype="datetime64[ns]")
    target = panel["trading_day"].to_numpy(dtype="datetime64[ns]")
    idx = np.searchsorted(dates, target, side="left") - 1
    valid = idx >= 0
    out = panel[["trading_day"]].copy()
    for c in ["date", "prev_date", "pct", "log", "pct_lag1", "pct_lag2", "pct_lag3", "pct_lead1", "pct_lead2", "pct_lead3"]:
        out[c] = pd.NaT if c in {"date", "prev_date"} else np.nan
        out.loc[valid, c] = s.iloc[idx[valid]][c].to_numpy()
    return out


def _corr(panel_feature: pd.Series, candidate: pd.Series) -> dict:
    y = pd.to_numeric(panel_feature, errors="coerce")
    x = pd.to_numeric(candidate, errors="coerce")
    m = y.notna() & x.notna()
    yy, xx = y.loc[m].to_numpy(float), x.loc[m].to_numpy(float)
    return {
        "n": int(m.sum()),
        "corr": float(np.corrcoef(yy, xx)[0, 1]),
        "mae": float(np.mean(np.abs(yy - xx))),
        "max_abs": float(np.max(np.abs(yy - xx))),
        "near_exact_1e_10_share": float(np.mean(np.abs(yy - xx) <= 1e-10)),
        "near_exact_1e_6_share": float(np.mean(np.abs(yy - xx) <= 1e-6)),
        "near_exact_1e_4_share": float(np.mean(np.abs(yy - xx) <= 1e-4)),
    }


def _top_rows(panel: pd.DataFrame, aligned: pd.DataFrame, feature: str, level_col: str, us: pd.DataFrame, n: int = 25) -> list[dict]:
    tmp = pd.DataFrame({
        "trading_day": panel["trading_day"],
        "panel": pd.to_numeric(panel[feature], errors="coerce"),
        "source_date": aligned["date"],
        "prev_source_date": aligned["prev_date"],
        "recon_pct": pd.to_numeric(aligned["pct"], errors="coerce"),
        "recon_log": pd.to_numeric(aligned["log"], errors="coerce"),
    })
    tmp["abs_diff_pct"] = (tmp["panel"] - tmp["recon_pct"]).abs()
    tmp = tmp.sort_values("abs_diff_pct", ascending=False).head(n)
    us_map = us.set_index("date")
    rows: list[dict] = []
    for _, r in tmp.iterrows():
        sd = pd.Timestamp(r["source_date"]) if pd.notna(r["source_date"]) else pd.NaT
        ps = pd.Timestamp(r["prev_source_date"]) if pd.notna(r["prev_source_date"]) else pd.NaT
        item = {
            "trading_day": str(pd.Timestamp(r["trading_day"]).date()),
            "panel_feature": None if pd.isna(r["panel"]) else float(r["panel"]),
            "source_date": None if pd.isna(sd) else str(sd.date()),
            "prev_source_date": None if pd.isna(ps) else str(ps.date()),
            "reconstructed_pct": None if pd.isna(r["recon_pct"]) else float(r["recon_pct"]),
            "reconstructed_log": None if pd.isna(r["recon_log"]) else float(r["recon_log"]),
            "abs_diff_pct": None if pd.isna(r["abs_diff_pct"]) else float(r["abs_diff_pct"]),
        }
        for label, dt in [("source", sd), ("prev", ps)]:
            if pd.notna(dt) and dt in us_map.index:
                val = us_map.loc[dt, level_col]
                item[f"{label}_level"] = None if pd.isna(val) else float(val)
        rows.append(item)
    return rows


def main() -> None:
    panel, us = _load()
    nas_s = _series_table(us, "nasdaq")
    vix_s = _series_table(us, "vix")
    nas = _align(panel, nas_s)
    vix = _align(panel, vix_s)
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31") or us["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 row detected")

    transforms = ["pct", "log", "pct_lag1", "pct_lag2", "pct_lag3", "pct_lead1", "pct_lead2", "pct_lead3"]
    report = {
        "schema_id": "overnight_open_us_feature_clock_mismatch_diagnostic@1.0",
        "nasdaq_transform_relations": {c: _corr(panel["us_nasdaq"], nas[c]) for c in transforms},
        "vix_transform_relations": {c: _corr(panel["us_vix_chg"], vix[c]) for c in transforms},
        "top_nasdaq_mismatches": _top_rows(panel, nas, "us_nasdaq", "nasdaq", us),
        "top_vix_mismatches": _top_rows(panel, vix, "us_vix_chg", "vix", us),
        "authority": {"measurement_diagnostic_only": True, "production": False, "fresh_oos": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
