#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_OUT = ROOT / "data/external/yahoo_usdcnh_2014_2020.json"
PARQUET_OUT = ROOT / "data/development/usdcnh_yahoo.parquet"
MANIFEST_OUT = ROOT / "docs/governance/external_cnh_yahoo_2014_2020_manifest.json"
PACKAGE_MANIFEST = ROOT / "data/manifest.json"
START = pd.Timestamp("2014-01-01", tz="UTC")
END = pd.Timestamp("2020-12-31", tz="UTC")
SYMBOL = "CNH=X"
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch() -> tuple[bytes, str]:
    # period2 is exclusive; request through 2021-01-02 and hard-filter afterward.
    p1 = int(START.timestamp())
    p2 = int(pd.Timestamp("2021-01-02", tz="UTC").timestamp())
    query = urllib.parse.urlencode({
        "period1": p1,
        "period2": p2,
        "interval": "1d",
        "includePrePost": "false",
        "events": "history",
    })
    url = f"{BASE}{urllib.parse.quote(SYMBOL, safe='')}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 factorlab-research"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
        if response.status != 200:
            raise RuntimeError((response.status, url))
    return data, url


def main() -> None:
    raw_bytes, url = fetch()
    payload = json.loads(raw_bytes)
    chart = payload.get("chart", {})
    if chart.get("error") is not None:
        raise AssertionError(chart["error"])
    results = chart.get("result") or []
    if len(results) != 1:
        raise AssertionError(("unexpected Yahoo result count", len(results)))
    r = results[0]
    ts = r.get("timestamp") or []
    quote = ((r.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    if len(ts) != len(closes) or not ts:
        raise AssertionError(("invalid timestamp/close arrays", len(ts), len(closes)))

    frame = pd.DataFrame({
        "timestamp_utc": pd.to_datetime(ts, unit="s", utc=True),
        "close": pd.to_numeric(pd.Series(closes), errors="coerce"),
    })
    frame["date"] = frame["timestamp_utc"].dt.normalize().dt.tz_localize(None)
    frame = frame.loc[(frame["date"] >= START.tz_localize(None)) & (frame["date"] <= END.tz_localize(None))].copy()
    frame = frame.dropna(subset=["close"]).drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    if frame.empty or frame["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("invalid filtered CNH boundary")
    if frame["date"].min() > pd.Timestamp("2014-01-10"):
        raise AssertionError(("CNH history begins unexpectedly late", frame["date"].min()))
    if frame["date"].max() < pd.Timestamp("2020-12-30"):
        raise AssertionError(("CNH history ends unexpectedly early", frame["date"].max()))

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW_OUT.write_bytes(raw_bytes)
    PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)
    frame[["date", "timestamp_utc", "close"]].to_parquet(PARQUET_OUT, index=False)

    meta = r.get("meta") or {}
    manifest = {
        "schema_id": "external_cnh_yahoo_manifest@1.0",
        "frozen_retrieval_date": "2026-09-05",
        "provider": "Yahoo Finance public chart endpoint",
        "symbol": SYMBOL,
        "instrument": "USD/CNH offshore RMB exchange rate",
        "source_url": url,
        "window": ["2014-01-01", "2020-12-31"],
        "observed_rows": int(len(frame)),
        "min_date": str(frame["date"].min().date()),
        "max_date": str(frame["date"].max().date()),
        "yahoo_meta": {
            "currency": meta.get("currency"),
            "exchangeName": meta.get("exchangeName"),
            "exchangeTimezoneName": meta.get("exchangeTimezoneName"),
            "gmtoffset": meta.get("gmtoffset"),
            "instrumentType": meta.get("instrumentType"),
        },
        "causal_semantics": "Research uses only rows whose normalized Yahoo bar timestamp date is strictly earlier than the China target trading date. No target-date close, interpolation, or forward fill is allowed.",
        "assets": {
            str(RAW_OUT.relative_to(ROOT)): {"sha256": sha256(RAW_OUT)},
            str(PARQUET_OUT.relative_to(ROOT)): {"sha256": sha256(PARQUET_OUT)}
        },
        "guards": {"post_2020_rows": 0, "forward_fill": False, "interpolation": False}
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    package = json.loads(PACKAGE_MANIFEST.read_text())
    path = "data/development/usdcnh_yahoo.parquet"
    matches = [p for p in package["products"] if p["path"] == path]
    product = {
        "path": path,
        "rows": int(len(frame)),
        "bytes": int(PARQUET_OUT.stat().st_size),
        "sha256": sha256(PARQUET_OUT),
        "min_day": str(frame["date"].min().date()),
        "max_day": str(frame["date"].max().date()),
    }
    if len(matches) == 0:
        package["products"].append(product)
    elif len(matches) == 1:
        matches[0].update(product)
    else:
        raise AssertionError("duplicate CNH product entries")
    PACKAGE_MANIFEST.write_text(json.dumps(package, indent=2) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
