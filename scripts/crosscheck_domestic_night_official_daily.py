#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research/domestic_night_official_daily_crosscheck.json"
PREREG = ROOT / "docs/governance/domestic_night_official_daily_crosscheck_preregistration.json"
SOURCE_REPO = "Freddy-Hexas/china-futures-5min-2015-2025"
SOURCE_COMMIT = "1a402721d639432875504a343e2b9ffe9508cd36"
RAW_BASE = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}"
TREE_URL = f"https://api.github.com/repos/{SOURCE_REPO}/git/trees/{SOURCE_COMMIT}?recursive=1"
SHFE_URLS = [
    "https://www.shfe.com.cn/data/tradedata/future/dailydata/kx{ymd}.dat",
    "http://tsite.shfe.com.cn/data/dailydata/kx/kx{ymd}.dat",
]
DCE_URLS = [
    "https://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes",
    "http://www.dce.com.cn/dcereport/publicweb/dailystat/dayQuotes",
]
PRODUCTS = {
    "CU": {"exchange": "SHFE", "months": [1, 5, 9]},
    "RB": {"exchange": "SHFE", "months": [1, 5, 10]},
    "I": {"exchange": "DCE", "months": [1, 5, 9]},
}
YEARS = list(range(2015, 2021))
ANCHORS = [(3, 15), (4, 15)]
UA = "Mozilla/5.0 factorlab-domestic-night-official-crosscheck"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_json_get(url: str) -> tuple[bytes, Any, int]:
    last: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(url, headers={"User-Agent": UA, "Referer": "https://www.shfe.com.cn/"}, timeout=30)
            if r.status_code == 404:
                raise FileNotFoundError(url)
            r.raise_for_status()
            raw = r.content
            return raw, r.json(), r.status_code
        except Exception as exc:
            last = exc
            time.sleep(0.7 * (attempt + 1))
    assert last is not None
    raise last


def fetch_json_post(url: str, payload: dict) -> tuple[bytes, Any, int]:
    last: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.post(
                url,
                json=payload,
                headers={
                    "User-Agent": UA,
                    "Accept": "application/json, text/plain, */*",
                    "Content-Type": "application/json",
                    "Referer": "https://www.dce.com.cn/",
                },
                timeout=30,
            )
            r.raise_for_status()
            raw = r.content
            return raw, r.json(), r.status_code
        except Exception as exc:
            last = exc
            time.sleep(0.7 * (attempt + 1))
    assert last is not None
    raise last


def norm_symbol(value: Any) -> str:
    return re.sub(r"\s+", "", str(value)).upper()


def num(value: Any) -> float:
    if value is None:
        return float("nan")
    s = str(value).replace(",", "").strip()
    if s in {"", "-", "--", "None", "nan"}:
        return float("nan")
    return float(s)


@dataclass
class OfficialResponse:
    exchange: str
    ymd: str
    source_url: str
    source_method: str
    source_sha256: str
    source_bytes: int
    rows: list[dict]


def parse_shfe_rows(payload: Any, ymd: str) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    raw_rows = payload.get("o_curinstrument") or []
    rows: list[dict] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        delivery = str(row.get("DELIVERYMONTH", "")).strip()
        if delivery in {"", "小计", "合计"}:
            continue
        product = str(row.get("PRODUCTGROUPID", row.get("PRODUCTID", ""))).strip().upper()
        product = product.split("_")[0]
        if not product:
            continue
        symbol = norm_symbol(product + delivery)
        rows.append({
            "symbol": symbol,
            "date": ymd,
            "open": num(row.get("OPENPRICE")),
            "high": num(row.get("HIGHESTPRICE")),
            "low": num(row.get("LOWESTPRICE")),
            "close": num(row.get("CLOSEPRICE")),
            "volume": num(row.get("VOLUME")),
            "open_interest": num(row.get("OPENINTEREST")),
        })
    return rows


def fetch_shfe(ymd: str) -> OfficialResponse | None:
    errors = []
    for pattern in SHFE_URLS:
        url = pattern.format(ymd=ymd)
        try:
            raw, payload, _ = fetch_json_get(url)
            rows = parse_shfe_rows(payload, ymd)
            if rows:
                return OfficialResponse("SHFE", ymd, url, "GET", sha256_bytes(raw), len(raw), rows)
            errors.append(f"empty:{url}")
        except Exception as exc:
            errors.append(f"{url}:{type(exc).__name__}:{exc}")
    return None


def parse_dce_rows(payload: Any, ymd: str) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    raw_rows = payload.get("data") or []
    rows: list[dict] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        symbol = norm_symbol(row.get("contractId", ""))
        if not symbol or "小计" in str(row.get("variety", "")) or "总计" in str(row.get("variety", "")):
            continue
        rows.append({
            "symbol": symbol,
            "date": ymd,
            "open": num(row.get("open")),
            "high": num(row.get("high")),
            "low": num(row.get("low")),
            "close": num(row.get("close")),
            "volume": num(row.get("volumn")),
            "open_interest": num(row.get("openInterest")),
        })
    return rows


def fetch_dce(ymd: str) -> OfficialResponse | None:
    payload = {
        "contractId": "",
        "lang": "zh",
        "optionSeries": "",
        "statisticsType": "0",
        "tradeDate": ymd,
        "tradeType": "1",
        "varietyId": "all",
    }
    for url in DCE_URLS:
        try:
            raw, data, _ = fetch_json_post(url, payload)
            rows = parse_dce_rows(data, ymd)
            if rows:
                return OfficialResponse("DCE", ymd, url, "POST JSON", sha256_bytes(raw), len(raw), rows)
        except Exception:
            continue
    return None


def fetch_official(exchange: str, d: date, cache: dict[tuple[str, str], OfficialResponse | None]) -> OfficialResponse | None:
    ymd = d.strftime("%Y%m%d")
    key = (exchange, ymd)
    if key not in cache:
        cache[key] = fetch_shfe(ymd) if exchange == "SHFE" else fetch_dce(ymd)
    return cache[key]


def row_for_symbol(response: OfficialResponse | None, symbol: str) -> dict | None:
    if response is None:
        return None
    sym = norm_symbol(symbol)
    matches = [r for r in response.rows if norm_symbol(r["symbol"]) == sym]
    if len(matches) > 1:
        raise AssertionError(("duplicate official symbol", response.exchange, response.ymd, sym))
    return matches[0] if matches else None


def resolve_anchor(exchange: str, symbol: str, anchor: date, cache: dict) -> tuple[date, OfficialResponse, dict] | None:
    for offset in range(5):
        d = anchor + timedelta(days=offset)
        response = fetch_official(exchange, d, cache)
        row = row_for_symbol(response, symbol)
        if row is not None and all(np.isfinite([row[k] for k in ["open", "high", "low", "close", "volume", "open_interest"]])):
            return d, response, row
    return None


def previous_official_day(exchange: str, d: date, cache: dict) -> tuple[date, OfficialResponse] | None:
    for offset in range(1, 11):
        p = d - timedelta(days=offset)
        response = fetch_official(exchange, p, cache)
        if response is not None and len(response.rows) > 0:
            return p, response
    return None


def load_vendor_file(exchange: str, symbol: str, year: int, tree_map: dict[str, str]) -> tuple[pd.DataFrame, dict]:
    contract = f"{symbol}{year % 100:02d}05"
    path = f"5min/{exchange}/{symbol}/{contract}.csv"
    if path not in tree_map:
        raise AssertionError(("missing pinned vendor crosscheck file", path))
    url = f"{RAW_BASE}/{path}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    raw = r.content
    df = pd.read_csv(io.StringIO(raw.decode("utf-8-sig")))
    if list(df.columns) != ["datetime", "open", "high", "low", "close", "volume", "money", "open_interest"]:
        raise AssertionError(("vendor schema drift", path, list(df.columns)))
    df["datetime"] = pd.to_datetime(df["datetime"], errors="raise")
    for col in ["open", "high", "low", "close", "volume", "open_interest"]:
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df, {
        "path": path,
        "contract": contract,
        "git_blob_sha": tree_map[path],
        "download_sha256": sha256_bytes(raw),
        "bytes": len(raw),
    }


def aggregate_vendor_day(df: pd.DataFrame, prev_day: date, day: date) -> dict | None:
    start = pd.Timestamp(prev_day) + pd.Timedelta(hours=15)
    end = pd.Timestamp(day) + pd.Timedelta(hours=15)
    m = (df["datetime"] > start) & (df["datetime"] <= end) & (df["volume"] > 0)
    x = df.loc[m].sort_values("datetime")
    if x.empty:
        return None
    return {
        "bar_count": int(len(x)),
        "first_datetime": str(x.iloc[0]["datetime"]),
        "last_datetime": str(x.iloc[-1]["datetime"]),
        "open": float(x.iloc[0]["open"]),
        "high": float(x["high"].max()),
        "low": float(x["low"].min()),
        "close": float(x.iloc[-1]["close"]),
        "volume": float(x["volume"].sum()),
        "open_interest": float(x.iloc[-1]["open_interest"]),
    }


def close_enough(a: float, b: float, tol: float = 1e-8) -> bool:
    return bool(np.isfinite(a) and np.isfinite(b) and abs(a - b) <= tol)


def main() -> None:
    prereg = json.loads(PREREG.read_text())
    if prereg["status"] != "result_free_before_official_exchange_crosscheck_no_CSI1000_target":
        raise AssertionError("official crosscheck preregistration status drift")

    tree_response = requests.get(TREE_URL, headers={"User-Agent": UA}, timeout=60)
    tree_response.raise_for_status()
    tree_json = tree_response.json()
    tree_map = {item["path"]: item["sha"] for item in tree_json["tree"] if item.get("type") == "blob"}

    cache: dict[tuple[str, str], OfficialResponse | None] = {}
    vendor_meta: dict[str, dict] = {}
    checks: list[dict] = []

    for product, cfg in PRODUCTS.items():
        exchange = cfg["exchange"]
        for year in YEARS:
            vendor_df, meta = load_vendor_file(exchange, product, year, tree_map)
            vendor_meta[meta["path"]] = meta
            contract = meta["contract"]
            for month, dom in ANCHORS:
                anchor = date(year, month, dom)
                resolved = resolve_anchor(exchange, contract, anchor, cache)
                if resolved is None:
                    checks.append({
                        "exchange": exchange,
                        "product": product,
                        "year": year,
                        "contract": contract,
                        "anchor": anchor.isoformat(),
                        "available": False,
                        "reason": "official_contract_not_resolved_within_anchor_plus_4_days",
                    })
                    continue
                d, official_response, official = resolved
                prev = previous_official_day(exchange, d, cache)
                if prev is None:
                    checks.append({
                        "exchange": exchange,
                        "product": product,
                        "year": year,
                        "contract": contract,
                        "anchor": anchor.isoformat(),
                        "resolved_date": d.isoformat(),
                        "available": False,
                        "reason": "previous_official_trading_day_not_found_within_10_days",
                    })
                    continue
                p, prev_response = prev
                vendor = aggregate_vendor_day(vendor_df, p, d)
                if vendor is None:
                    checks.append({
                        "exchange": exchange,
                        "product": product,
                        "year": year,
                        "contract": contract,
                        "anchor": anchor.isoformat(),
                        "resolved_date": d.isoformat(),
                        "previous_official_date": p.isoformat(),
                        "available": False,
                        "reason": "no_positive_volume_vendor_bars_in_official_trading_day_interval",
                    })
                    continue

                price_matches = {k: close_enough(vendor[k], float(official[k])) for k in ["open", "high", "low", "close"]}
                volume_match = close_enough(vendor["volume"], float(official["volume"]), 1e-8)
                oi_match = close_enough(vendor["open_interest"], float(official["open_interest"]), 1e-8)
                checks.append({
                    "exchange": exchange,
                    "product": product,
                    "year": year,
                    "contract": contract,
                    "anchor": anchor.isoformat(),
                    "resolved_date": d.isoformat(),
                    "previous_official_date": p.isoformat(),
                    "available": True,
                    "official_source": {
                        "url": official_response.source_url,
                        "method": official_response.source_method,
                        "sha256": official_response.source_sha256,
                        "bytes": official_response.source_bytes,
                    },
                    "previous_official_source": {
                        "url": prev_response.source_url,
                        "method": prev_response.source_method,
                        "sha256": prev_response.source_sha256,
                        "bytes": prev_response.source_bytes,
                    },
                    "official": official,
                    "vendor_positive_volume_aggregate": vendor,
                    "matches": {
                        **price_matches,
                        "all_ohlc": bool(all(price_matches.values())),
                        "volume": bool(volume_match),
                        "open_interest": bool(oi_match),
                    },
                    "differences": {k: float(vendor[k] - float(official[k])) for k in ["open", "high", "low", "close", "volume", "open_interest"]},
                })

    if len(checks) != 36:
        raise AssertionError(("fixed official crosscheck count drift", len(checks)))

    available = [x for x in checks if x.get("available")]
    def rate(items: list[dict], key: str) -> float:
        return float(np.mean([bool(x["matches"][key]) for x in items])) if items else float("nan")

    by_product: dict[str, dict] = {}
    for product in PRODUCTS:
        items = [x for x in available if x["product"] == product]
        available_n = len(items)
        ohlc_rate = rate(items, "all_ohlc")
        vol_rate = rate(items, "volume")
        oi_rate = rate(items, "open_interest")
        by_product[product] = {
            "available_checks": available_n,
            "all_ohlc_match_rate": ohlc_rate,
            "volume_match_rate": vol_rate,
            "open_interest_match_rate": oi_rate,
            "product_floor_pass": bool(available_n >= 8 and np.isfinite(ohlc_rate) and ohlc_rate >= 0.90),
        }

    overall = {
        "fixed_checks": 36,
        "available_checks": len(available),
        "official_access_pass": len(available) >= 30,
        "all_ohlc_match_rate": rate(available, "all_ohlc"),
        "volume_match_rate": rate(available, "volume"),
        "open_interest_match_rate": rate(available, "open_interest"),
    }
    overall["price_match_pass"] = bool(np.isfinite(overall["all_ohlc_match_rate"]) and overall["all_ohlc_match_rate"] >= 0.95)
    overall["volume_match_pass"] = bool(np.isfinite(overall["volume_match_rate"]) and overall["volume_match_rate"] >= 0.95)
    overall["open_interest_match_pass"] = bool(np.isfinite(overall["open_interest_match_rate"]) and overall["open_interest_match_rate"] >= 0.95)
    overall["all_products_floor_pass"] = bool(all(x["product_floor_pass"] for x in by_product.values()))
    overall["all_crosscheck_gates_pass"] = bool(
        overall["official_access_pass"]
        and overall["price_match_pass"]
        and overall["volume_match_pass"]
        and overall["open_interest_match_pass"]
        and overall["all_products_floor_pass"]
    )

    report = {
        "schema_id": "overnight_open_domestic_night_official_daily_crosscheck_results@1.0",
        "role": "official source cross-validation only; no CSI1000 target labels or model metrics read",
        "preregistration": str(PREREG.relative_to(ROOT)),
        "source_under_test": {
            "repository": SOURCE_REPO,
            "pinned_commit": SOURCE_COMMIT,
            "vendor_files": vendor_meta,
        },
        "official_response_cache": {
            f"{exchange}:{ymd}": None if response is None else {
                "url": response.source_url,
                "method": response.source_method,
                "sha256": response.source_sha256,
                "bytes": response.source_bytes,
                "row_count": len(response.rows),
            }
            for (exchange, ymd), response in sorted(cache.items())
        },
        "overall": overall,
        "by_product": by_product,
        "checks": checks,
        "decision": {
            "products_eligible_for_later_preregistration": [p for p, x in by_product.items() if x["product_floor_pass"]] if overall["official_access_pass"] else [],
            "transport_source_all_gate_pass": overall["all_crosscheck_gates_pass"],
            "target_model_execution": False,
        },
        "data_boundary": {
            "CSI1000_target_rows_read": 0,
            "post_2020_market_rows_used_for_crosscheck": 0,
        },
        "authority": {
            "target_model_execution": False,
            "fresh_oos": False,
            "baseline_replacement": False,
            "production": False,
            "registry_mutation": False,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"overall": overall, "by_product": by_product, "unavailable_checks": [x for x in checks if not x.get("available")]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
