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
            r = session.post(url, data=data, timeout=45, allow_redirects=True) if method == "POST" else session.get(url, timeout=45, allow_redirects=True)
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
    numeric = ["open", "high", "low", "close", "volume", "open_interest"] + (["money"] if "money" in df.columns else [])
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="raise")
    if not np.isfinite(df[["open", "high", "low", "close"]].to_numpy(dtype=float)).all():
        raise AssertionError("nonfinite OHLC")
    bad_ohlc = (df["low"] > df["open"]) | (df["low"] > df["close"]) | (df["high"] < df["open"]) | (df["high"] < df["close"]) | (df["low"] > df["high"])
    if bad_ohlc.any():
        raise AssertionError("OHLC inequality failure")
    if (df["volume"] < 0).any() or (df["open_interest"] < 0).any():
        raise AssertionError("negative volume/open_interest")

    dup = df[df["datetime"].duplicated(keep=False)].copy()
    exact_groups = 0
    conflicting_groups = 0
    if not dup.empty:
        compare_cols = [c for c in df.columns if c != "datetime"]
        for _, g in dup.groupby("datetime"):
            if len(g[compare_cols].drop_duplicates()) == 1:
                exact_groups += 1
            else:
                conflicting_groups += 1
        if conflicting_groups:
            raise AssertionError(("conflicting duplicate contract-datetime rows", conflicting_groups))
        df = df.drop_duplicates()
    df = df.sort_values("datetime").reset_index(drop=True)
    return df, {
        "git_blob_sha": actual_blob,
        "raw_sha256": sha256_bytes(raw),
        "rows": int(len(df)),
        "min_datetime": str(df["datetime"].min()),
        "max_datetime": str(df["datetime"].max()),
        "exact_duplicate_groups_collapsed": int(exact_groups),
        "conflicting_duplicate_groups": int(conflicting_groups),
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
        return ("233000", False) if day < pd.Timestamp("2019-04-01") else ("230000", False)
    raise KeyError(product)


def aggregate_trading_day(df: pd.DataFrame, day: pd.Timestamp, product: str) -> dict[str, Any] | None:
    day = day.normalize()
    end_hhmmss, crosses_midnight = clock_for(product, day)
    dates = df["datetime"].dt.normalize()
    times = df["datetime"].dt.strftime("%H%M%S")
    earlier = df.loc[(dates < day) & (dates >= day - pd.Timedelta(days=4)) & (times >= "210000")]
    night_date = earlier["datetime"].dt.normalize().max() if not earlier.empty else None

    pieces: list[pd.DataFrame] = []
    if night_date is not None:
        nd = dates == night_date
        if crosses_midnight:
            pieces.append(df.loc[nd & (times >= "210000")].copy())
        else:
            pieces.append(df.loc[nd & (times >= "210000") & (times <= end_hhmmss)].copy())
    if crosses_midnight:
        pieces.append(df.loc[(dates == day) & (times <= end_hhmmss)].copy())
    daybars = df.loc[(dates == day) & (times >= "090000") & (times <= "150000")].copy()
    pieces.append(daybars)
    nonempty = [p for p in pieces if not p.empty]
    if not nonempty or daybars.empty:
        return None
    selected = pd.concat(nonempty, ignore_index=True).sort_values("datetime").reset_index(drop=True)

    invalid = []
    for ts in selected["datetime"]:
        ts = pd.Timestamp(ts)
        t, d = ts.strftime("%H%M%S"), ts.normalize()
        valid = (d == day and "090000" <= t <= "150000")
        valid = valid or (night_date is not None and d == night_date and t >= "210000" and (crosses_midnight or t <= end_hhmmss))
        valid = valid or (crosses_midnight and d == day and t <= end_hhmmss)
        if not valid:
            invalid.append(str(ts))
    if invalid:
        raise AssertionError(("selected bars outside frozen clock", product, str(day.date()), invalid[:10]))

    def ohlc(f: pd.DataFrame) -> dict[str, float] | None:
        if f.empty:
            return None
        f = f.sort_values("datetime")
        return {"open": float(f.iloc[0]["open"]), "high": float(f["high"].max()), "low": float(f["low"].min()), "close": float(f.iloc[-1]["close"])}

    all_ohlc = ohlc(selected)
    assert all_ohlc is not None
    pos = selected.loc[selected["volume"] > 0].copy()
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
            product = re.sub(r"[^a-z]", "", str(v).lower()).removesuffix("f") or None
        if k in {"deliverymonth", "deliverymonthid", "contractmonth"}:
            digits = re.sub(r"\D", "", str(v))
            if len(digits) >= 4:
                month = digits[-4:]
    return (product + month).upper() if product and month else None


def fetch_shfe(session: requests.Session, day: pd.Timestamp, contract: str, cfg: dict[str, Any]) -> dict[str, Any]:
    ymd = day.strftime("%Y%m%d")
    ecfg = cfg["official_daily_price_endpoints"]["SHFE"]
    errors = []
    for template in [ecfg["primary"], ecfg["protocol_compatibility_fallback"]]:
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
                "open": ["openprice", "open"], "high": ["highestprice", "highprice", "high"],
                "low": ["lowestprice", "lowprice", "low"], "close": ["closeprice", "close"],
                "settlement": ["settlementprice", "settlement"], "volume": ["volume"],
                "open_interest": ["openinterest", "openinterestqty"],
            }
            values = {name: next((_number(norm[k]) for k in keys if k in norm), None) for name, keys in aliases.items()}
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
    return " ".join(str(x) for x in c if str(x) != "nan") if isinstance(c, tuple) else str(c)


def _extract_dce_table(text: str, contract: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    diag: dict[str, Any] = {"table_count": 0, "tables_with_contract_token": 0}
    try:
        tables = pd.read_html(io.StringIO(text))
    except Exception as exc:
        diag["read_html_error"] = repr(exc)
        return None, diag
    diag["table_count"] = len(tables)
    for ti, table in enumerate(tables):
        table = table.copy()
        table.columns = [_flatten_col(c) for c in table.columns]
        mask = table.apply(lambda col: col.astype(str).str.strip().str.lower().eq(contract.lower())).any(axis=1)
        if not mask.any():
            continue
        diag["tables_with_contract_token"] += 1
        for _, row in table.loc[mask].iterrows():
            record = {str(k): row[k] for k in table.columns}
            norm = {_norm_key(k): v for k, v in record.items()}
            def cn(label: str) -> float | None:
                for k, v in norm.items():
                    if label in k:
                        x = _number(v)
                        if x is not None:
                            return x
                return None
            values = {
                "open": cn("开盘价") if cn("开盘价") is not None else cn("开盘"),
                "high": cn("最高价") if cn("最高价") is not None else cn("最高"),
                "low": cn("最低价") if cn("最低价") is not None else cn("最低"),
                "close": cn("收盘价") if cn("收盘价") is not None else cn("收盘"),
                "settlement": cn("结算价") if cn("结算价") is not None else cn("结算"),
                "volume": cn("成交量") if cn("成交量") is not None else cn("成交"),
                "open_interest": cn("持仓量") if cn("持仓量") is not None else cn("持仓"),
            }
            if all(values[k] is not None for k in ["open", "high", "low", "close"]):
                return {"table_index": ti, "values": values, "raw_matched_row": record}, diag
    return None, diag


def fetch_dce(session: requests.Session, day: pd.Timestamp, contract: str, cfg: dict[str, Any]) -> dict[str, Any]:
    ecfg = cfg["official_daily_price_endpoints"]["DCE"]
    fields = {"dayQuotes.variety": "all", "dayQuotes.trade_type": "0", "year": str(day.year), "month": str(day.month - 1), "day": f"{day.day:02d}"}
    errors = []
    try:
        session.get("https://www.dce.com.cn/", timeout=20)
    except Exception:
        pass
    for label in ["daily_html", "daily_export"]:
        try:
            raw, meta = fetch(session, ecfg[label], method="POST", data=fields)
            text = _decode_response(raw)
            matched, diag = _extract_dce_table(text, contract)
            if matched is None:
                errors.append({"endpoint": label, "response": meta, "parse": diag, "body_prefix": text[:300]})
                continue
            return {"ok": True, "source": "DCE", "endpoint": label, "response": meta, "contract": contract, **matched, "errors_before_success": errors}
        except Exception as exc:
            errors.append({"endpoint": label, "url": ecfg[label], "error": repr(exc)})
    return {"ok": False, "source": "DCE", "contract": contract, "errors": errors}


def compare_values(transport: dict[str, float], official: dict[str, float | None], tick: float) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    ok_all = True
    for k in ["open", "high", "low", "close"]:
        ov, tv = official.get(k), float(transport[k])
        if ov is None:
            fields[k] = {"transport": tv, "official": None, "difference": None, "tolerance": tick, "pass": False, "reason": "missing_authoritative_field"}
            ok_all = False
        else:
            diff = abs(tv - float(ov))
            ok = diff <= tick + 1e-12
            fields[k] = {"transport": tv, "official": float(ov), "difference": float(diff), "tolerance": float(tick), "pass": bool(ok)}
            ok_all = ok_all and ok
    return {"fields": fields, "primary_ohlc_pass": bool(ok_all)}


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
    # Build the forbidden target filename dynamically so the guard does not contain
    # the exact forbidden path token and trigger itself.
    forbidden_target_name = "csi" + "1000_open_pit_panel.parquet"
    if forbidden_target_name in Path(__file__).read_text():
        raise AssertionError("source audit script must not reference the forbidden target panel")

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "*/*"})
    transport_cache: dict[str, tuple[pd.DataFrame, dict[str, Any]]] = {}
    results: dict[str, Any] = {}
    ticks = endpoint_contract["minimum_price_ticks"]

    for product, pcfg in freeze["sample_design"]["products"].items():
        samples = []
        for anchor_s, scfg in pcfg["contracts_by_date"].items():
            path = scfg["path"]
            if path not in transport_cache:
                raw, raw_meta = fetch(session, RAW_BASE.format(path=path))
                parsed, pmeta = parse_transport(raw, scfg["git_blob_sha"])
                transport_cache[path] = (parsed, {"raw_response": raw_meta, **pmeta})
            df, tmeta = transport_cache[path]
            attempts = []
            chosen = None
            for day in candidate_dates(pd.Timestamp(anchor_s)):
                agg = aggregate_trading_day(df, day, product)
                if agg is None:
                    attempts.append({"date": str(day.date()), "transport": "unavailable"})
                    continue
                official = fetch_shfe(session, day, scfg["contract"], endpoint_contract) if product.startswith("SHFE_") else fetch_dce(session, day, scfg["contract"], endpoint_contract)
                if not official.get("ok"):
                    attempts.append({"date": str(day.date()), "transport": "available", "official": official})
                    continue
                cmp = compare_values(agg["all_bars_ohlc"], official["values"], float(ticks[product]["tick"]))
                chosen = {
                    "anchor_date": anchor_s,
                    "chosen_date": str(day.date()),
                    "used_fallback_date": str(day.date()) != anchor_s,
                    "contract": scfg["contract"],
                    "path": path,
                    "frozen_git_blob_sha": scfg["git_blob_sha"],
                    "transport_file_validation": tmeta,
                    "transport_trading_day": agg,
                    "official": official,
                    "comparison": cmp,
                    "sample_pass": bool(cmp["primary_ohlc_pass"]),
                    "failed_attempts_before_chosen": attempts,
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
            samples.append(chosen)
        pass_count = sum(bool(x.get("sample_pass")) for x in samples)
        results[product] = {"economic_role": pcfg["economic_role"], "samples": samples, "sample_pass_count": int(pass_count), "sample_total": len(samples), "product_pass": bool(pass_count >= 2)}

    all_products_pass = all(x["product_pass"] for x in results.values())
    unavailable = sum(bool(s.get("unavailable")) for p in results.values() for s in p["samples"])
    failed_price = sum((not bool(s.get("sample_pass"))) and (not bool(s.get("unavailable"))) for p in results.values() for s in p["samples"])
    if all_products_pass:
        status = "transport_source_admitted_for_predefined_products_waiting_separate_predictive_preregistration"
    elif unavailable and failed_price == 0:
        status = "infrastructure_gap_official_daily_price_retrieval_or_parse_prevents_admission"
    else:
        status = "transport_source_not_admitted_under_frozen_crosscheck_gates"
    report = {
        "schema_id": "overnight_open_domestic_night_source_crosscheck_results@1.0",
        "sample_freeze": str(SAMPLE_FREEZE.relative_to(ROOT)),
        "endpoint_contract": str(ENDPOINT_CONTRACT.relative_to(ROOT)),
        "clock_evidence": str(CLOCK_FREEZE.relative_to(ROOT)),
        "data_boundary": {"CSI1000_target_rows_read": 0, "post_2020_transport_rows_read": 0},
        "products": results,
        "summary": {
            "product_pass_count": sum(bool(x["product_pass"]) for x in results.values()),
            "product_total": len(results),
            "unavailable_sample_count": int(unavailable),
            "failed_price_sample_count": int(failed_price),
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
