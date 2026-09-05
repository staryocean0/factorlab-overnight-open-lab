#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_FREEZE = ROOT / "docs/governance/domestic_night_source_crosscheck_sample_freeze.json"
ENDPOINT_CONTRACT = ROOT / "docs/governance/domestic_night_source_official_endpoint_contract.json"
CLOCK_FREEZE = ROOT / "docs/governance/domestic_night_source_clock_evidence_freeze.json"
OUT = ROOT / "artifacts/research/domestic_night_source_crosscheck_results.json"
PINNED = "1a402721d639432875504a343e2b9ffe9508cd36"
RAW_BASE = f"https://raw.githubusercontent.com/Freddy-Hexas/china-futures-5min-2015-2025/{PINNED}/{{path}}"
REQUIRED_COLS = ["datetime", "open", "high", "low", "close", "volume", "open_interest"]
UA = "factorlab-overnight-open-source-audit/1.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    hdr = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(hdr + data).hexdigest()


def fetch(session: requests.Session, url: str, *, method: str = "GET", data: dict[str, str] | None = None) -> tuple[bytes, dict[str, Any]]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            if method == "POST":
                r = session.post(url, data=data, timeout=45, allow_redirects=True)
            else:
                r = session.get(url, timeout=45, allow_redirects=True)
            if r.status_code != 200:
                raise RuntimeError(("http", r.status_code, url, r.text[:160]))
            raw = r.content
            return raw, {
                "requested_url": url,
                "final_url": r.url,
                "status": r.status_code,
                "content_type": r.headers.get("content-type"),
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
            }
        except Exception as exc:
            last = exc
            time.sleep(1.0 + attempt)
    assert last is not None
    raise last


def parse_transport(raw: bytes, expected_blob: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    actual_blob = git_blob_sha(raw)
    if actual_blob != expected_blob:
        raise AssertionError(("third-party Git blob identity mismatch", actual_blob, expected_blob))
    df = pd.read_csv(io.BytesIO(raw))
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise AssertionError(("missing transport columns", missing, list(df.columns)))
    df["datetime"] = pd.to_datetime(df["datetime"], errors="raise")
    if df["datetime"].max() > pd.Timestamp("2020-12-31 23:59:59"):
        raise AssertionError("post-2020 transport row detected")
    numeric = ["open", "high", "low", "close", "volume", "open_interest"]
    if "money" in df.columns:
        numeric.append("money")
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="raise")
    prices = df[["open", "high", "low", "close"]]
    if not np.isfinite(prices.to_numpy(dtype=float)).all():
        raise AssertionError("nonfinite OHLC")
    if ((df["low"] > df["open"]) | (df["low"] > df["close"]) | (df["high"] < df["open"]) | (df["high"] < df["close"]) | (df["low"] > df["high"])).any():
        raise AssertionError("OHLC inequality failure")
    if (df["volume"] < 0).any() or (df["open_interest"] < 0).any():
        raise AssertionError("negative volume/open_interest")

    duplicate_rows = df[df["datetime"].duplicated(keep=False)].copy()
    exact_duplicate_groups = 0
    conflicting_duplicate_groups = 0
    if not duplicate_rows.empty:
        compare_cols = [c for c in df.columns if c != "datetime"]
        for _, g in duplicate_rows.groupby("datetime"):
            if len(g[compare_cols].drop_duplicates()) == 1:
                exact_duplicate_groups += 1
            else:
                conflicting_duplicate_groups += 1
        if conflicting_duplicate_groups:
            raise AssertionError(("conflicting duplicate contract-datetime rows", conflicting_duplicate_groups))
        df = df.drop_duplicates().sort_values("datetime").reset_index(drop=True)
    else:
        df = df.sort_values("datetime").reset_index(drop=True)

    return df, {
        "git_blob_sha": actual_blob,
        "raw_sha256": sha256_bytes(raw),
        "rows": int(len(df)),
        "min_datetime": str(df["datetime"].min()),
        "max_datetime": str(df["datetime"].max()),
        "exact_duplicate_groups_collapsed": int(exact_duplicate_groups),
        "conflicting_duplicate_groups": int(conflicting_duplicate_groups),
        "zero_volume_rows": int((df["volume"] == 0).sum()),
    }


def candidate_dates(anchor: pd.Timestamp) -> list[pd.Timestamp]:
    out = [anchor.normalize()]
    x = anchor.normalize()
    while len(out) < 6:
        x -= pd.Timedelta(days=1)
        if x.weekday() < 5:
            out.append(x)
    return out


def clock_for(product: str, day: pd.Timestamp) -> tuple[str, bool]:
    if product == "SHFE_CU":
        return "010000", True
    if product == "SHFE_RB":
        return "230000", False
    if product == "DCE_I":
        if day < pd.Timestamp("2019-04-01"):
            return "233000", False
        return "230000", False
    raise KeyError(product)


def aggregate_trading_day(df: pd.DataFrame, day: pd.Timestamp, product: str) -> dict[str, Any] | None:
    day = day.normalize()
    end_hhmmss, crosses_midnight = clock_for(product, day)
    date = df["datetime"].dt.normalize()
    hhmmss = df["datetime"].dt.strftime("%H%M%S")

    earlier = df.loc[(date < day) & (date >= day - pd.Timedelta(days=4)) & (hhmmss >= "210000")].copy()
    night_date: pd.Timestamp | None = None
    if not earlier.empty:
        # The exchange trading day uses the most recent prior workday continuous session;
        # for Monday this naturally selects Friday when Friday-night bars exist.
        night_date = earlier["datetime"].dt.normalize().max()

    pieces: list[pd.DataFrame] = []
    if night_date is not None:
        nd = df["datetime"].dt.normalize() == night_date
        nt = df["datetime"].dt.strftime("%H%M%S")
        if crosses_midnight:
            pieces.append(df.loc[nd & (nt >= "210000")].copy())
        else:
            pieces.append(df.loc[nd & (nt >= "210000") & (nt <= end_hhmmss)].copy())
    if crosses_midnight:
        td = df["datetime"].dt.normalize() == day
        tt = df["datetime"].dt.strftime("%H%M%S")
        pieces.append(df.loc[td & (tt <= end_hhmmss)].copy())

    td = df["datetime"].dt.normalize() == day
    tt = df["datetime"].dt.strftime("%H%M%S")
    daybars = df.loc[td & (tt >= "090000") & (tt <= "150000")].copy()
    pieces.append(daybars)
    selected = pd.concat([p for p in pieces if not p.empty], ignore_index=True) if any(not p.empty for p in pieces) else pd.DataFrame()
    if selected.empty or daybars.empty:
        return None
    selected = selected.sort_values("datetime").reset_index(drop=True)

    # Hard clock validation on rows actually entering the aggregate.
    invalid_clock = []
    for _, r in selected.iterrows():
        ts = pd.Timestamp(r["datetime"])
        t = ts.strftime("%H%M%S")
        d = ts.normalize()
        valid = False
        if d == day and "090000" <= t <= "150000":
            valid = True
        elif night_date is not None and d == night_date and t >= "210000":
            valid = crosses_midnight or t <= end_hhmmss
        elif crosses_midnight and d == day and t <= end_hhmmss:
            valid = True
        if not valid:
            invalid_clock.append(str(ts))
    if invalid_clock:
        raise AssertionError(("selected bars outside frozen clock", product, str(day.date()), invalid_clock[:10]))

    def ohlc(frame: pd.DataFrame) -> dict[str, float] | None:
        if frame.empty:
            return None
        f = frame.sort_values("datetime")
        return {
            "open": float(f.iloc[0]["open"]),
            "high": float(f["high"].max()),
            "low": float(f["low"].min()),
            "close": float(f.iloc[-1]["close"]),
        }

    pos = selected.loc[selected["volume"] > 0].copy()
    all_ohlc = ohlc(selected)
    assert all_ohlc is not None
    return {
        "trading_day": str(day.date()),
        "night_source_calendar_date": str(night_date.date()) if night_date is not None else None,
        "frozen_night_end": end_hhmmss,
        "crosses_midnight": crosses_midnight,
        "selected_bar_count": int(len(selected)),
        "selected_zero_volume_count": int((selected["volume"] == 0).sum()),
        "first_selected_datetime": str(selected["datetime"].min()),
        "last_selected_datetime": str(selected["datetime"].max()),
        "all_bars_ohlc": all_ohlc,
        "positive_volume_diagnostic_ohlc": ohlc(pos),
        "positive_volume_bar_count": int(len(pos)),
    }


def _norm_key(x: Any) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", str(x).lower())


def _number(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s in {"", "-", "--", "nan", "None", "null"}:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    return x if np.isfinite(x) else None


def _shfe_contract(row: dict[str, Any]) -> str | None:
    norm = {_norm_key(k): v for k, v in row.items()}
    for k in ["instrumentid", "instrument", "contractid"]:
        if k in norm:
            s = re.sub(r"[^a-z0-9]", "", str(norm[k]).lower())
            if re.fullmatch(r"[a-z]+\d{4}", s):
                return s.upper()
    product = None
    month = None
    for k, v in norm.items():
        if k in {"productid", "product", "productgroupid"}:
            letters = re.sub(r"[^a-z]", "", str(v).lower()).replace("f", "")
            if letters:
                product = letters
        if k in {"deliverymonth", "deliverymonthid", "contractmonth"}:
            digits = re.sub(r"\D", "", str(v))
            if len(digits) >= 4:
                month = digits[-4:]
    if product and month:
        return (product + month).upper()
    return None


def fetch_shfe(session: requests.Session, day: pd.Timestamp, contract: str, contract_cfg: dict[str, Any]) -> dict[str, Any]:
    ymd = day.strftime("%Y%m%d")
    urls = [contract_cfg["official_daily_price_endpoints"]["SHFE"]["primary"], contract_cfg["official_daily_price_endpoints"]["SHFE"]["protocol_compatibility_fallback"]]
    errors = []
    for template in urls:
        url = template.replace("{YYYYMMDD}", ymd)
        try:
            raw, meta = fetch(session, url)
            payload = json.loads(raw.decode("utf-8-sig"))
            rows = payload.get("o_curinstrument", []) if isinstance(payload, dict) else []
            matches = [r for r in rows if isinstance(r, dict) and _shfe_contract(r) == contract.upper()]
            if len(matches) != 1:
                errors.append({"url": url, "error": f"exact contract rows={len(matches)}"})
                continue
            row = matches[0]
            norm = {_norm_key(k): v for k, v in row.items()}
            aliases = {
                "open": ["openprice", "open"],
                "high": ["highestprice", "highprice", "high"],
                "low": ["lowestprice", "lowprice", "low"],
                "close": ["closeprice", "close"],
                "settlement": ["settlementprice", "settlement"],
                "volume": ["volume"],
                "open_interest": ["openinterest", "openinterestqty"],
            }
            values: dict[str, float | None] = {}
            for name, keys in aliases.items():
                values[name] = next((_number(norm[k]) for k in keys if k in norm), None)
            return {"ok": True, "source": "SHFE", "response": meta, "contract": contract, "values": values, "raw_matched_row": row, "errors_before_success": errors}
        except Exception as exc:
            errors.append({"url": url, "error": repr(exc)})
    return {"ok": False, "source": "SHFE", "contract": contract, "errors": errors}


def _decode_response(raw: bytes) -> str:
    for enc in ["utf-8", "gb18030", "gbk"]:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def _flatten_col(c: Any) -> str:
    if isinstance(c, tuple):
        return " ".join(str(x) for x in c if str(x) != "nan")
    return str(c)


def _extract_dce_table(text: str, contract: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    diagnostics: dict[str, Any] = {"table_count": 0, "tables_with_contract_token": 0}
    try:
        tables = pd.read_html(io.StringIO(text))
    except Exception as exc:
        diagnostics["read_html_error"] = repr(exc)
        return None, diagnostics
    diagnostics["table_count"] = len(tables)
    target = contract.lower()
    for ti, table in enumerate(tables):
        table = table.copy()
        table.columns = [_flatten_col(c) for c in table.columns]
        mask = table.apply(lambda col: col.astype(str).str.strip().str.lower().eq(target)).any(axis=1)
        if not mask.any():
            continue
        diagnostics["tables_with_contract_token"] += 1
        for _, row in table.loc[mask].iterrows():
            record = {str(k): row[k] for k in table.columns}
            norm = {_norm_key(k): v for k, v in record.items()}
            def by_cn(substr: str) -> float | None:
                for k, v in norm.items():
                    if substr in k:
                        x = _number(v)
                        if x is not None:
                            return x
                return None
            values = {
                "open": by_cn("开盘价") or by_cn("开盘"),
                "high": by_cn("最高价") or by_cn("最高"),
                "low": by_cn("最低价") or by_cn("最低"),
                "close": by_cn("收盘价") or by_cn("收盘"),
                "settlement": by_cn("结算价") or by_cn("结算"),
                "volume": by_cn("成交量") or by_cn("成交"),
                "open_interest": by_cn("持仓量") or by_cn("持仓"),
            }
            if all(values[k] is not None for k in ["open", "high", "low", "close"]):
                return {"table_index": ti, "values": values, "raw_matched_row": record}, diagnostics
    return None, diagnostics


def fetch_dce(session: requests.Session, day: pd.Timestamp, contract: str, contract_cfg: dict[str, Any]) -> dict[str, Any]:
    cfg = contract_cfg["official_daily_price_endpoints"]["DCE"]
    fields = {
        "dayQuotes.variety": "all",
        "dayQuotes.trade_type": "0",
        "year": str(day.year),
        "month": str(day.month - 1),
        "day": f"{day.day:02d}",
    }
    errors = []
    # Establish official-domain cookies once; failure here is not fatal if direct POST still works.
    try:
        session.get("https://www.dce.com.cn/", timeout=20)
    except Exception:
        pass
    for label in ["daily_html", "daily_export"]:
        url = cfg[label]
        try:
            raw, meta = fetch(session, url, method="POST", data=fields)
            text = _decode_response(raw)
            matched, diag = _extract_dce_table(text, contract)
            if matched is None:
                errors.append({"endpoint": label, "response": meta, "parse": diag, "body_prefix": text[:300]})
                continue
            return {"ok": True, "source": "DCE", "endpoint": label, "response": meta, "contract": contract, **matched, "errors_before_success": errors}
        except Exception as exc:
            errors.append({"endpoint": label, "url": url, "error": repr(exc)})
    return {"ok": False, "source": "DCE", "contract": contract, "errors": errors}


def compare_values(transport: dict[str, float], official: dict[str, float | None], tick: float) -> dict[str, Any]:
    fields = {}
    all_pass = True
    for k in ["open", "high", "low", "close"]:
        ov = official.get(k)
        tv = transport[k]
        if ov is None:
            fields[k] = {"transport": tv, "official": None, "difference": None, "tolerance": tick, "pass": False, "reason": "missing_authoritative_field"}
            all_pass = False
            continue
        diff = abs(float(tv) - float(ov))
        ok = diff <= tick + 1e-12
        fields[k] = {"transport": float(tv), "official": float(ov), "difference": float(diff), "tolerance": float(tick), "pass": bool(ok)}
        all_pass = all_pass and ok
    return {"fields": fields, "primary_ohlc_pass": bool(all_pass)}


def main() -> None:
    freeze = json.loads(SAMPLE_FREEZE.read_text())
    endpoint_contract = json.loads(ENDPOINT_CONTRACT.read_text())
    clock_freeze = json.loads(CLOCK_FREEZE.read_text())
    if freeze["status"] != "result_free_before_fetching_crosscheck_price_values":
        raise AssertionError("sample freeze status invalid")
    if endpoint_contract["status"] != "result_free_before_official_daily_price_fetch":
        raise AssertionError("endpoint/tolerance contract status invalid")
    if clock_freeze["status"] != "frozen_before_crosscheck_price_values":
        raise AssertionError("clock evidence not frozen")
    if (ROOT / "data/development/csi1000_open_pit_panel.parquet").name in Path(__file__).read_text():
        raise AssertionError("source audit script must not reference CSI1000 panel")

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "*/*"})
    product_results: dict[str, Any] = {}
    transport_cache: dict[str, tuple[pd.DataFrame, dict[str, Any]]] = {}

    product_cfgs = freeze["sample_design"]["products"]
    ticks = endpoint_contract["minimum_price_ticks"]
    for product, pcfg in product_cfgs.items():
        samples = []
        for anchor_s, scfg in pcfg["contracts_by_date"].items():
            path = scfg["path"]
            if path not in transport_cache:
                raw_url = RAW_BASE.format(path=path)
                raw, raw_meta = fetch(session, raw_url)
                parsed, parse_meta = parse_transport(raw, scfg["git_blob_sha"])
                transport_cache[path] = (parsed, {"raw_response": raw_meta, **parse_meta})
            df, tmeta = transport_cache[path]
            attempts = []
            chosen = None
            for d in candidate_dates(pd.Timestamp(anchor_s)):
                agg = aggregate_trading_day(df, d, product)
                if agg is None:
                    attempts.append({"date": str(d.date()), "transport": "unavailable"})
                    continue
                official = fetch_shfe(session, d, scfg["contract"], endpoint_contract) if product.startswith("SHFE_") else fetch_dce(session, d, scfg["contract"], endpoint_contract)
                if not official.get("ok"):
                    attempts.append({"date": str(d.date()), "transport": "available", "official": official})
                    continue
                tick = float(ticks[product]["tick"])
                cmp = compare_values(agg["all_bars_ohlc"], official["values"], tick)
                chosen = {
                    "anchor_date": anchor_s,
                    "chosen_date": str(d.date()),
                    "used_fallback_date": str(d.date()) != anchor_s,
                    "contract": scfg["contract"],
                    "path": path,
                    "frozen_git_blob_sha": scfg["git_blob_sha"],
                    "transport_file_validation": tmeta,
                    "transport_trading_day": agg,
                    "official": official,
                    "comparison": cmp,
                    "sample_pass": bool(cmp["primary_ohlc_pass"]),
                }
                break
            if chosen is None:
                chosen = {
                    "anchor_date": anchor_s,
                    "contract": scfg["contract"],
                    "path": path,
                    "frozen_git_blob_sha": scfg["git_blob_sha"],
                    "transport_file_validation": tmeta,
                    "attempts": attempts,
                    "sample_pass": False,
                    "unavailable": True,
                    "reason": "no_date_with_both_transport_aggregate_and_machine_readable_exact_official_contract_row_within_frozen_window",
                }
            else:
                chosen["failed_attempts_before_chosen"] = attempts
            samples.append(chosen)
        pass_count = sum(bool(x.get("sample_pass")) for x in samples)
        product_results[product] = {
            "economic_role": pcfg["economic_role"],
            "samples": samples,
            "sample_pass_count": int(pass_count),
            "sample_total": len(samples),
            "product_pass": bool(pass_count >= 2),
        }

    all_products_pass = all(x["product_pass"] for x in product_results.values())
    unavailable_samples = sum(bool(s.get("unavailable")) for p in product_results.values() for s in p["samples"])
    failed_price_samples = sum((not bool(s.get("sample_pass"))) and (not bool(s.get("unavailable"))) for p in product_results.values() for s in p["samples"])
    if all_products_pass:
        status = "transport_source_admitted_for_predefined_products_waiting_separate_predictive_preregistration"
    elif unavailable_samples and failed_price_samples == 0:
        status = "infrastructure_gap_official_daily_price_retrieval_or_parse_prevents_admission"
    else:
        status = "transport_source_not_admitted_under_frozen_crosscheck_gates"

    report = {
        "schema_id": "overnight_open_domestic_night_source_crosscheck_results@1.0",
        "sample_freeze": str(SAMPLE_FREEZE.relative_to(ROOT)),
        "endpoint_contract": str(ENDPOINT_CONTRACT.relative_to(ROOT)),
        "clock_evidence": str(CLOCK_FREEZE.relative_to(ROOT)),
        "data_boundary": {"CSI1000_target_rows_read": 0, "post_2020_transport_rows_read": 0},
        "products": product_results,
        "summary": {
            "product_pass_count": sum(bool(x["product_pass"]) for x in product_results.values()),
            "product_total": len(product_results),
            "unavailable_sample_count": int(unavailable_samples),
            "failed_price_sample_count": int(failed_price_samples),
            "source_admission_pass": bool(all_products_pass),
            "scientific_status": status,
        },
        "authority": {"predictive_model_execution": False, "fresh_oos": False, "baseline_replacement": False, "production": False, "registry_mutation": False, "merge_main": False},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
