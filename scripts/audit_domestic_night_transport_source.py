#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/research/domestic_night_transport_source_audit.json"
SOURCE_REPO = "Freddy-Hexas/china-futures-5min-2015-2025"
SOURCE_COMMIT = "1a402721d639432875504a343e2b9ffe9508cd36"
TREE_URL = f"https://api.github.com/repos/{SOURCE_REPO}/git/trees/{SOURCE_COMMIT}?recursive=1"
RAW_BASE = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}"

PRODUCTS = {
    "CU": {"exchange": "SHFE", "months": [1, 5, 9]},
    "RB": {"exchange": "SHFE", "months": [1, 5, 10]},
    "I": {"exchange": "DCE", "months": [1, 5, 9]},
}
YEARS = range(2015, 2021)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "factorlab-domestic-night-source-audit"})
    with urllib.request.urlopen(req, timeout=90) as r:
        if int(r.status) != 200:
            raise RuntimeError(("http", url, r.status))
        return r.read()


def fetch_json(url: str) -> object:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def contract_code(symbol: str, year: int, month: int) -> str:
    return f"{symbol}{year % 100:02d}{month:02d}"


def expected_paths() -> list[dict]:
    rows = []
    for symbol, cfg in PRODUCTS.items():
        for year in YEARS:
            for month in cfg["months"]:
                code = contract_code(symbol, year, month)
                rows.append({
                    "exchange": cfg["exchange"],
                    "symbol": symbol,
                    "year": year,
                    "month": month,
                    "contract": code,
                    "path": f"5min/{cfg['exchange']}/{symbol}/{code}.csv",
                })
    return rows


def hhmm_int(ts: pd.Series) -> pd.Series:
    return ts.dt.hour * 100 + ts.dt.minute


def broad_session_allowed(exchange: str, symbol: str, ts: pd.Series) -> pd.Series:
    # This first-pass transport audit intentionally uses a broad historical union window.
    # Later source sealing must apply the exact dated session regimes from governance.
    hm = hhmm_int(ts)
    day = ((hm >= 900) & (hm <= 1015)) | ((hm >= 1030) & (hm <= 1130)) | ((hm >= 1330) & (hm <= 1500))
    if exchange == "SHFE" and symbol in {"CU", "RB"}:
        night = (hm >= 2100) | (hm <= 230)
    elif exchange == "DCE" and symbol == "I":
        night = (hm >= 2100) | (hm <= 230)
    else:
        raise AssertionError((exchange, symbol))
    return day | night


def parse_one(meta: dict, blob_sha: str, raw: bytes) -> dict:
    text = raw.decode("utf-8-sig", errors="strict")
    df = pd.read_csv(io.StringIO(text))
    required = ["datetime", "open", "high", "low", "close", "volume", "money", "open_interest"]
    if list(df.columns) != required:
        raise AssertionError((meta["path"], "schema", list(df.columns)))
    dt = pd.to_datetime(df["datetime"], errors="raise")
    if not dt.is_monotonic_increasing:
        raise AssertionError((meta["path"], "datetime not monotonic"))
    duplicate_count = int(dt.duplicated().sum())
    numeric = {}
    for col in required[1:]:
        numeric[col] = pd.to_numeric(df[col], errors="raise")
        if not np.isfinite(numeric[col].to_numpy(dtype=float)).all():
            raise AssertionError((meta["path"], "nonfinite", col))
    o, h, l, c = numeric["open"], numeric["high"], numeric["low"], numeric["close"]
    ohlc_bad = int(((l > o) | (l > c) | (h < o) | (h < c) | (l > h)).sum())
    neg_volume = int((numeric["volume"] < 0).sum())
    neg_oi = int((numeric["open_interest"] < 0).sum())
    post_2020 = int((dt > pd.Timestamp("2020-12-31 23:59:59")).sum())

    vol = numeric["volume"]
    zero_vol = vol.eq(0)
    pos_vol = vol.gt(0)
    flat = o.eq(h) & h.eq(l) & l.eq(c)
    zero_flat = zero_vol & flat
    prev_close = c.shift(1)
    zero_flat_carry = zero_flat & c.eq(prev_close)
    zero_money = pd.to_numeric(numeric["money"], errors="raise").eq(0)
    zero_full_fill_signature = zero_flat_carry & zero_money

    broad_allowed = broad_session_allowed(meta["exchange"], meta["symbol"], dt)
    positive_outside_broad = int((pos_vol & ~broad_allowed).sum())
    zero_outside_broad = int((zero_vol & ~broad_allowed).sum())

    diffs = dt.diff().dropna().dt.total_seconds().div(60)
    five_minute_diff_share = float(diffs.eq(5).mean()) if len(diffs) else float("nan")

    pos_dt = dt.loc[pos_vol]
    positive_date_min = str(pos_dt.min()) if len(pos_dt) else None
    positive_date_max = str(pos_dt.max()) if len(pos_dt) else None

    sample_fill_rows = []
    for idx in df.index[zero_full_fill_signature][:5]:
        sample_fill_rows.append({
            "datetime": str(dt.loc[idx]),
            "close": float(c.loc[idx]),
            "volume": float(vol.loc[idx]),
            "money": float(numeric["money"].loc[idx]),
            "open_interest": float(numeric["open_interest"].loc[idx]),
        })

    return {
        **meta,
        "git_blob_sha": blob_sha,
        "download_sha256": sha256_bytes(raw),
        "bytes": len(raw),
        "rows": int(len(df)),
        "datetime_min": str(dt.min()) if len(dt) else None,
        "datetime_max": str(dt.max()) if len(dt) else None,
        "positive_volume_datetime_min": positive_date_min,
        "positive_volume_datetime_max": positive_date_max,
        "duplicate_datetime_rows": duplicate_count,
        "ohlc_logic_violations": ohlc_bad,
        "negative_volume_rows": neg_volume,
        "negative_open_interest_rows": neg_oi,
        "post_2020_rows": post_2020,
        "positive_volume_rows": int(pos_vol.sum()),
        "zero_volume_rows": int(zero_vol.sum()),
        "zero_volume_share": float(zero_vol.mean()) if len(df) else float("nan"),
        "zero_volume_flat_rows": int(zero_flat.sum()),
        "zero_volume_flat_carry_rows": int(zero_flat_carry.sum()),
        "zero_volume_flat_carry_zero_money_rows": int(zero_full_fill_signature.sum()),
        "zero_volume_flat_carry_zero_money_share_of_zero_volume": float(zero_full_fill_signature.sum() / zero_vol.sum()) if zero_vol.sum() else float("nan"),
        "positive_volume_outside_broad_historical_session_union": positive_outside,
        "zero_volume_outside_broad_historical_session_union": zero_outside_broad,
        "adjacent_rows_exactly_5_minutes_share": five_minute_diff_share,
        "sample_fill_signature_rows": sample_fill_rows,
    }


def main() -> None:
    tree = fetch_json(TREE_URL)
    if not isinstance(tree, dict) or "tree" not in tree:
        raise AssertionError("source Git tree unavailable")
    blob_map = {item["path"]: item["sha"] for item in tree["tree"] if item.get("type") == "blob"}
    specs = expected_paths()
    missing = [x["path"] for x in specs if x["path"] not in blob_map]
    if missing:
        raise AssertionError(("frozen sample paths missing from pinned source tree", missing))

    results: list[dict] = []
    errors: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {
            ex.submit(fetch_bytes, f"{RAW_BASE}/{spec['path']}"): spec
            for spec in specs
        }
        for fut in as_completed(futures):
            spec = futures[fut]
            try:
                raw = fut.result()
                results.append(parse_one(spec, blob_map[spec["path"]], raw))
            except Exception as exc:
                errors.append({**spec, "error": repr(exc)})

    results.sort(key=lambda x: (x["exchange"], x["symbol"], x["year"], x["month"]))
    if errors:
        raise AssertionError(("transport source audit file failures", errors))
    if len(results) != 54:
        raise AssertionError(("unexpected audited contract count", len(results)))

    total_rows = sum(x["rows"] for x in results)
    total_zero = sum(x["zero_volume_rows"] for x in results)
    total_fill = sum(x["zero_volume_flat_carry_zero_money_rows"] for x in results)
    total_pos = sum(x["positive_volume_rows"] for x in results)
    total_pos_outside = sum(x["positive_volume_outside_broad_historical_session_union"] for x in results)
    summary_by_product = {}
    for symbol in PRODUCTS:
        subset = [x for x in results if x["symbol"] == symbol]
        z = sum(x["zero_volume_rows"] for x in subset)
        summary_by_product[symbol] = {
            "contracts": len(subset),
            "rows": sum(x["rows"] for x in subset),
            "positive_volume_rows": sum(x["positive_volume_rows"] for x in subset),
            "zero_volume_rows": z,
            "zero_volume_share": z / sum(x["rows"] for x in subset),
            "fill_signature_rows": sum(x["zero_volume_flat_carry_zero_money_rows"] for x in subset),
            "positive_volume_outside_broad_session_rows": sum(x["positive_volume_outside_broad_historical_session_union"] for x in subset),
        }

    report = {
        "schema_id": "overnight_open_domestic_night_transport_source_audit@1.0",
        "role": "source validation only; no CSI1000 target labels or model metrics read",
        "source": {
            "repository": SOURCE_REPO,
            "pinned_commit": SOURCE_COMMIT,
            "license": "CC0-1.0",
            "audited_contract_files": len(results),
        },
        "scope": {
            "products": PRODUCTS,
            "years": list(YEARS),
            "post_2020_target_rows_read": 0,
        },
        "aggregate": {
            "rows": int(total_rows),
            "positive_volume_rows": int(total_pos),
            "zero_volume_rows": int(total_zero),
            "zero_volume_share": float(total_zero / total_rows),
            "fill_signature_rows": int(total_fill),
            "fill_signature_share_of_zero_volume": float(total_fill / total_zero) if total_zero else float("nan"),
            "positive_volume_outside_broad_historical_session_union": int(total_pos_outside),
            "contracts_with_ohlc_violation": int(sum(x["ohlc_logic_violations"] > 0 for x in results)),
            "contracts_with_duplicate_datetime": int(sum(x["duplicate_datetime_rows"] > 0 for x in results)),
            "contracts_with_post_2020_rows": int(sum(x["post_2020_rows"] > 0 for x in results)),
        },
        "by_product": summary_by_product,
        "contracts": results,
        "interpretation_rules": {
            "nonzero_OHLC_with_zero_volume_is_not_treated_as_an_observed_trade": True,
            "candidate_price_endpoints_must_use_positive_volume_bars_if_this_transport_source_advances": True,
            "official_daily_price_crosscheck_still_required_before_model_admission": True,
            "this_audit_cannot_select_a_forecasting_product_or_feature": True,
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
    print(json.dumps({
        "source": report["source"],
        "aggregate": report["aggregate"],
        "by_product": report["by_product"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
