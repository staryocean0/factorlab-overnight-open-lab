#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily"
START = pd.Timestamp("2014-01-01")
END = pd.Timestamp("2020-12-31")
RAW_OUT = ROOT / "data/external/hkma_er_eeri_daily_2014_2020.json"
PARQUET_OUT = ROOT / "data/development/hkma_usdcny_cross.parquet"
MANIFEST_OUT = ROOT / "docs/governance/external_hkma_usdcny_2014_2020_manifest.json"
PACKAGE_MANIFEST = ROOT / "data/manifest.json"
PAGE_SIZE = 1000


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_page(offset: int) -> tuple[list[dict], dict]:
    params = {
        "choose": "end_of_day",
        "from": str(START.date()),
        "to": str(END.date()),
        "fields": "end_of_day,usd,cny",
        "pagesize": str(PAGE_SIZE),
        "offset": str(offset),
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "factorlab-overnight-open-lab/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    header = payload.get("header", {})
    if not bool(header.get("success")):
        raise AssertionError(("HKMA API failure", header))
    result = payload.get("result", {})
    records = result.get("records")
    if not isinstance(records, list):
        raise AssertionError(("HKMA records missing", type(records).__name__))
    return records, {"url": url, "header": header, "datasize": result.get("datasize")}


def _update_package_manifest(frame: pd.DataFrame) -> None:
    package = json.loads(PACKAGE_MANIFEST.read_text())
    rel = str(PARQUET_OUT.relative_to(ROOT))
    product = {
        "path": rel,
        "rows": int(len(frame)),
        "bytes": int(PARQUET_OUT.stat().st_size),
        "sha256": _sha256(PARQUET_OUT),
        "min_day": str(frame["date"].min().date()),
        "max_day": str(frame["date"].max().date()),
    }
    products = [x for x in package["products"] if x["path"] != rel]
    products.append(product)
    package["products"] = products
    PACKAGE_MANIFEST.write_text(json.dumps(package, indent=2) + "\n")


def main() -> None:
    records: list[dict] = []
    pages: list[dict] = []
    for offset in range(0, 10000, PAGE_SIZE):
        page, meta = _fetch_page(offset)
        pages.append(meta)
        records.extend(page)
        if len(page) < PAGE_SIZE:
            break
    else:
        raise AssertionError("HKMA pagination exceeded safety bound")

    if not records:
        raise AssertionError("HKMA returned no exchange-rate records")
    raw_df = pd.DataFrame.from_records(records)
    required = {"end_of_day", "usd", "cny"}
    if not required.issubset(raw_df.columns):
        raise AssertionError(("HKMA fields missing", sorted(raw_df.columns)))

    df = raw_df[["end_of_day", "usd", "cny"]].copy()
    df["date"] = pd.to_datetime(df.pop("end_of_day"), errors="raise").dt.normalize()
    df["usd_hkd"] = pd.to_numeric(df.pop("usd"), errors="coerce")
    df["cny_hkd"] = pd.to_numeric(df.pop("cny"), errors="coerce")
    df = df.loc[(df["date"] >= START) & (df["date"] <= END)].copy()
    df = df.drop_duplicates("date", keep="last").sort_values("date").reset_index(drop=True)
    df["usdcny_hk"] = df["usd_hkd"] / df["cny_hkd"]

    observed = df.dropna(subset=["usd_hkd", "cny_hkd", "usdcny_hk"]).copy()
    if len(observed) < 1500:
        raise AssertionError(("too few HKMA joint observations", len(observed)))
    if observed["date"].min() > pd.Timestamp("2014-01-31"):
        raise AssertionError(("HKMA history starts too late", observed["date"].min()))
    if observed["date"].max() < pd.Timestamp("2020-12-20"):
        raise AssertionError(("HKMA history ends too early", observed["date"].max()))
    if bool((observed["date"] > END).any()):
        raise AssertionError("post-2020 HKMA row detected")
    if bool((observed["usd_hkd"] <= 0).any() or (observed["cny_hkd"] <= 0).any() or (observed["usdcny_hk"] <= 0).any()):
        raise AssertionError("non-positive HKMA FX level detected")

    RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    raw_payload = {
        "schema_id": "external_hkma_er_eeri_daily_raw@1.0",
        "retrieval_date": "2026-09-05",
        "provider": "Hong Kong Monetary Authority",
        "endpoint": API_URL,
        "query_window": [str(START.date()), str(END.date())],
        "pages": pages,
        "records": records,
    }
    RAW_OUT.write_text(json.dumps(raw_payload, indent=2, sort_keys=True) + "\n")

    PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)
    observed[["date", "usd_hkd", "cny_hkd", "usdcny_hk"]].to_parquet(PARQUET_OUT, index=False)
    _update_package_manifest(observed)

    manifest = {
        "schema_id": "external_hkma_usdcny_manifest@1.0",
        "frozen_retrieval_date": "2026-09-05",
        "provider": "Hong Kong Monetary Authority public API",
        "documentation": "https://apidocs.hkma.gov.hk/documentation/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily/",
        "endpoint": API_URL,
        "published_fields": {
            "usd": "HKD per unit of USD",
            "cny": "HKD per unit of CNY",
        },
        "derived_cross": "usdcny_hk = usd_hkd / cny_hkd (CNY per USD)",
        "interpretation": "Hong-Kong-market China-FX price-discovery proxy; not labeled as an exact executable interbank CNH spot series",
        "window": [str(START.date()), str(END.date())],
        "row_counts": {
            "api_records_returned": int(len(records)),
            "joint_observed": int(len(observed)),
            "missing_joint_within_returned_dates": int(len(df) - len(observed)),
        },
        "date_range": {
            "min_observed": str(observed["date"].min().date()),
            "max_observed": str(observed["date"].max().date()),
        },
        "assets": {
            str(RAW_OUT.relative_to(ROOT)): {"sha256": _sha256(RAW_OUT)},
            str(PARQUET_OUT.relative_to(ROOT)): {"sha256": _sha256(PARQUET_OUT)},
        },
        "guards": {
            "post_2020_rows": 0,
            "forward_fill": False,
            "interpolation": False,
            "target_date_observation_allowed_in_model": False,
        },
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
