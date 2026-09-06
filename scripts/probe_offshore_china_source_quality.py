#!/usr/bin/env python3
"""Source-only admission probe for offshore-China US-listed ETF daily OHLC.

This script MUST NOT read China target/panel data. It freezes one local source
identity and reports calendar/price quality for ASHS, ASHR, FXI, MCHI and SPY
through 2025-12-31. Predictive diagnostics are a later task after cloud review.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ENV = "OVERNIGHT_OFFSHORE_ETF_DAILY"
PROVIDER_ENV = "OVERNIGHT_OFFSHORE_ETF_PROVIDER"
PROVIDER_ID_ENV = "OVERNIGHT_OFFSHORE_ETF_PROVIDER_ID"
START = "2015-01-01"
END = "2025-12-31"
SYMBOLS = ["ASHS", "ASHR", "FXI", "MCHI", "SPY"]
OUT = ROOT / "docs/research/cloud_session_20260906_local_offshore_china_source_freeze_v1.json"
USAGE = ROOT / "docs/governance/local_session_20260906_offshore_china_source_data_usage.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_source(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
    elif suffix in {".csv", ".txt"}:
        frame = pd.read_csv(path)
    else:
        raise RuntimeError(f"unsupported source format: {suffix}; use parquet or csv")

    required = {"date", "symbol", "open", "close", "volume"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"offshore source missing columns: {missing}")

    out = frame[["date", "symbol", "open", "close", "volume"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    for col in ["open", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if out["date"].isna().any():
        raise RuntimeError("offshore source contains unparseable date")
    if out.duplicated(["symbol", "date"]).any():
        dup = out.loc[out.duplicated(["symbol", "date"], keep=False), ["symbol", "date"]].head(10)
        raise RuntimeError(f"duplicate symbol/date rows in source: {dup.to_dict('records')}")
    return out.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def yearly_quality(frame: pd.DataFrame, spy_dates: set[pd.Timestamp], symbol: str) -> dict:
    result: dict[str, dict] = {}
    sf = frame.loc[frame["symbol"] == symbol].set_index("date")
    for year in range(2015, 2026):
        year_spy = sorted(d for d in spy_dates if d.year == year)
        present = [d for d in year_spy if d in sf.index]
        missing = len(year_spy) - len(present)
        if present:
            rows = sf.loc[present]
            invalid_price = int(((rows["open"] <= 0) | (rows["close"] <= 0) | rows[["open", "close"]].isna().any(axis=1)).sum())
            invalid_volume = int(((rows["volume"] < 0) | rows["volume"].isna()).sum())
            zero_volume = int((rows["volume"] == 0).sum())
            ret = rows["close"] / rows["open"] - 1.0
            zero_return = int((ret.abs() <= 1e-15).sum())
            extreme20 = int((ret.abs() > 0.20).sum())
        else:
            invalid_price = invalid_volume = zero_volume = zero_return = extreme20 = 0
        result[str(year)] = {
            "spy_sessions": int(len(year_spy)),
            "present": int(len(present)),
            "missing_vs_spy": int(missing),
            "coverage_vs_spy": None if not year_spy else float(len(present) / len(year_spy)),
            "invalid_price_rows": invalid_price,
            "invalid_volume_rows": invalid_volume,
            "zero_volume_rows": zero_volume,
            "zero_return_rows": zero_return,
            "abs_session_return_gt_20pct_rows": extreme20,
        }
    return result


def main() -> int:
    source_value = os.environ.get(SOURCE_ENV)
    if not source_value:
        raise RuntimeError(
            f"{SOURCE_ENV} is required and must point to a local 2015-2025-only parquet/csv with date,symbol,open,close,volume"
        )
    provider = os.environ.get(PROVIDER_ENV, "").strip()
    provider_id = os.environ.get(PROVIDER_ID_ENV, "").strip()
    if not provider:
        raise RuntimeError(f"{PROVIDER_ENV} is required; freeze the provider identity before any predictive diagnostics")

    path = Path(source_value).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"offshore source file not found: {path}")

    frame = load_source(path)
    if frame.empty:
        raise RuntimeError("offshore source is empty")
    if frame["date"].max() > pd.Timestamp(END):
        raise RuntimeError("source file contains post-2025 rows; create a development-only export before source admission")
    if frame["date"].min() > pd.Timestamp(START):
        raise RuntimeError("source begins after 2015-01-01")

    extras = sorted(set(frame["symbol"]) - set(SYMBOLS))
    missing_symbols = sorted(set(SYMBOLS) - set(frame["symbol"]))
    if missing_symbols:
        raise RuntimeError(f"required symbols missing from source: {missing_symbols}")

    dev = frame.loc[(frame["date"] >= START) & (frame["date"] <= END) & frame["symbol"].isin(SYMBOLS)].copy()
    spy = dev.loc[dev["symbol"] == "SPY"].copy()
    invalid_spy = spy.loc[(spy["open"] <= 0) | (spy["close"] <= 0) | spy[["open", "close", "volume"]].isna().any(axis=1)]
    if not invalid_spy.empty:
        raise RuntimeError("SPY calendar anchor contains invalid OHLCV rows")
    spy_dates = set(spy["date"].tolist())
    if not spy_dates:
        raise RuntimeError("SPY session calendar is empty")

    quality: dict[str, dict] = {}
    for symbol in SYMBOLS:
        sf = dev.loc[dev["symbol"] == symbol].copy()
        rows_on_spy = sf.loc[sf["date"].isin(spy_dates)].copy()
        missing_dates = sorted(spy_dates - set(rows_on_spy["date"].tolist()))
        invalid_price = int(((rows_on_spy["open"] <= 0) | (rows_on_spy["close"] <= 0) | rows_on_spy[["open", "close"]].isna().any(axis=1)).sum())
        invalid_volume = int(((rows_on_spy["volume"] < 0) | rows_on_spy["volume"].isna()).sum())
        ret = rows_on_spy["close"] / rows_on_spy["open"] - 1.0
        quality[symbol] = {
            "first_date": None if sf.empty else str(sf["date"].min().date()),
            "last_date": None if sf.empty else str(sf["date"].max().date()),
            "rows_in_development_file": int(len(sf)),
            "spy_sessions": int(len(spy_dates)),
            "present_on_spy_sessions": int(len(rows_on_spy)),
            "missing_vs_spy": int(len(missing_dates)),
            "coverage_vs_spy": float(len(rows_on_spy) / len(spy_dates)),
            "first_missing_dates": [str(d.date()) for d in missing_dates[:20]],
            "invalid_price_rows": invalid_price,
            "invalid_volume_rows": invalid_volume,
            "zero_volume_rows": int((rows_on_spy["volume"] == 0).sum()),
            "zero_return_rows": int((ret.abs() <= 1e-15).sum()),
            "abs_session_return_gt_20pct_rows": int((ret.abs() > 0.20).sum()),
            "session_return_min": None if ret.empty else float(ret.min()),
            "session_return_max": None if ret.empty else float(ret.max()),
            "yearly": yearly_quality(dev, spy_dates, symbol),
        }

    receipt = {
        "schema_id": "overnight_open_local_offshore_china_source_freeze@1.0",
        "session_date": "2026-09-06",
        "provider": provider,
        "provider_id": provider_id or None,
        "local_source_path": str(path),
        "source_sha256": sha256(path),
        "source_format": path.suffix.lower(),
        "development_window": {"start": START, "end": END},
        "required_symbols": SYMBOLS,
        "extra_symbols_ignored": extras,
        "fields": ["date", "symbol", "open", "close", "volume"],
        "spy_session_count": int(len(spy_dates)),
        "quality": quality,
        "predictive_target_loaded": False,
        "candidate_selection_performed": False,
        "2026_rows_loaded": False,
        "2026_blackbox_opened": False,
        "raw_external_rows_written_to_bounded_repo": False,
        "production_authority": False,
        "note": "Source/provider identity and source-only quality are frozen before any China-target predictive diagnostic."
    }
    dump_json(OUT, receipt)

    usage = {
        "schema_id": "overnight_open_local_offshore_china_source_data_usage@1.0",
        "session_date": "2026-09-06",
        "external_source_window": "2015-01-01_to_2025-12-31_source_quality_only",
        "china_target_loaded": False,
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_rows_persisted_in_bounded_repo": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)

    summary = {
        "provider": provider,
        "source_sha256": receipt["source_sha256"],
        "spy_session_count": receipt["spy_session_count"],
        "quality": {s: {k: quality[s][k] for k in ["coverage_vs_spy", "missing_vs_spy", "invalid_price_rows", "invalid_volume_rows", "zero_volume_rows", "zero_return_rows"]} for s in SYMBOLS},
        "predictive_target_loaded": False,
        "2026_blackbox_opened": False,
    }
    print("OFFSHORE_CHINA_SOURCE_QUALITY_RESULT", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
