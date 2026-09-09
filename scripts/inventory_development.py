#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US = ROOT / "data/development/us_nasdaq_vix.parquet"
DEV_END = pd.Timestamp("2018-12-31")


def main() -> int:
    rec = json.loads((ROOT / "docs/governance/baseline_receipt.json").read_text())
    panel_schema = pq.ParquetFile(PANEL).schema.names
    us_schema = pq.ParquetFile(US).schema.names
    print("PANEL_SCHEMA", panel_schema)
    print("US_SCHEMA", us_schema)

    panel = pd.read_parquet(PANEL)
    day = pd.to_datetime(panel["trading_day"])
    assert day.max() <= pd.Timestamp("2020-12-31")
    dev = panel.loc[day <= DEV_END].copy()
    assert pd.to_datetime(dev["trading_day"]).max() <= DEV_END

    print("DEV_ROWS", len(dev))
    print("DEV_DAY_MIN", str(pd.to_datetime(dev["trading_day"]).min().date()))
    print("DEV_DAY_MAX", str(pd.to_datetime(dev["trading_day"]).max().date()))
    print("BASELINE_FEATURES", rec["features"])

    target = pd.to_numeric(dev["gap"], errors="coerce")
    print("DEV_GAP_N", int(target.notna().sum()))
    print("DEV_GAP_MEAN", float(target.mean()))
    print("DEV_DOWN_SHARE", float((target < 0).mean()))
    print("DEV_GAP_STD", float(target.std(ddof=1)))

    numeric = {}
    for c in dev.columns:
        if c in {"gap", "trading_day"}:
            continue
        s = pd.to_numeric(dev[c], errors="coerce")
        m = s.notna() & target.notna()
        if int(m.sum()) >= 100 and float(s.loc[m].std(ddof=1)) > 0:
            numeric[c] = {
                "n": int(m.sum()),
                "corr_gap": float(np.corrcoef(s.loc[m], target.loc[m])[0, 1]),
                "missing": float(1.0 - s.notna().mean()),
            }
    ranked = sorted(numeric.items(), key=lambda kv: abs(kv[1]["corr_gap"]), reverse=True)
    print("DEV_NUMERIC_CORR_TOP", ranked[:30])

    us = pd.read_parquet(US)
    us_day = pd.to_datetime(us["date"])
    assert us_day.max() <= pd.Timestamp("2020-12-31")
    us_dev = us.loc[us_day <= DEV_END].copy()
    print("US_DEV_ROWS", len(us_dev))
    print("US_DEV_HEAD", us_dev.head(3).to_dict(orient="records"))
    print("US_DEV_TAIL", us_dev.tail(3).to_dict(orient="records"))
    print("PHASE_A_HOLDOUT_TARGET_USED", False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
