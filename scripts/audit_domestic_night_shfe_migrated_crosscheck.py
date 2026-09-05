#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE_SPEC = importlib.util.spec_from_file_location(
    "night_base", ROOT / "scripts/audit_domestic_night_source_crosscheck.py"
)
base = importlib.util.module_from_spec(BASE_SPEC)
assert BASE_SPEC.loader is not None
BASE_SPEC.loader.exec_module(base)

SAMPLE_FREEZE = ROOT / "docs/governance/domestic_night_source_crosscheck_sample_freeze.json"
ENDPOINT_CONTRACT = ROOT / "docs/governance/domestic_night_source_official_endpoint_contract.json"
MIGRATION = ROOT / "docs/governance/domestic_night_official_endpoint_migration_correction.json"
OUT = ROOT / "artifacts/research/domestic_night_shfe_migrated_crosscheck_results.json"
SHFE_URL = "https://www.shfe.com.cn/data/tradedata/future/dailydata/kx{ymd}.dat"
HTTP_TIMEOUT = 20
HTTP_ATTEMPTS = 2


def get_bytes(session: requests.Session, url: str) -> tuple[bytes, dict[str, Any]]:
    last: Exception | None = None
    for attempt in range(HTTP_ATTEMPTS):
        try:
            r = session.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                raise RuntimeError(("http", r.status_code, url, r.text[:120]))
            raw = r.content
            return raw, {
                "url": url,
                "final_url": r.url,
                "status": r.status_code,
                "content_type": r.headers.get("content-type"),
                "bytes": len(raw),
                "sha256": base.sha256_bytes(raw),
                "attempt": attempt + 1,
            }
        except Exception as exc:
            last = exc
            if attempt + 1 < HTTP_ATTEMPTS:
                time.sleep(0.8)
    assert last is not None
    raise last


def fetch_official_shfe(session: requests.Session, day: base.pd.Timestamp, contract: str) -> dict[str, Any]:
    ymd = day.strftime("%Y%m%d")
    url = SHFE_URL.format(ymd=ymd)
    try:
        raw, response_meta = get_bytes(session, url)
    except Exception as exc:
        return {"ok": False, "failure_class": "official_http_infrastructure", "url": url, "error": repr(exc)}
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        return {"ok": False, "failure_class": "official_payload_not_json", "response": response_meta, "error": repr(exc)}
    rows = payload.get("o_curinstrument", []) if isinstance(payload, dict) else []
    matches = [r for r in rows if isinstance(r, dict) and base._shfe_contract(r) == contract.upper()]
    if len(matches) != 1:
        return {
            "ok": False,
            "failure_class": "official_exact_contract_row_absent",
            "response": response_meta,
            "row_count": len(rows),
            "exact_contract_row_count": len(matches),
        }
    row = matches[0]
    norm = {base._norm_key(k): v for k, v in row.items()}
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
        values[name] = next((base._number(norm[k]) for k in keys if k in norm), None)
    return {
        "ok": True,
        "response": response_meta,
        "contract": contract,
        "values": values,
        "matched_row_identity": {
            "product_id": row.get("PRODUCTID"),
            "product_group_id": row.get("PRODUCTGROUPID"),
            "delivery_month": row.get("DELIVERYMONTH"),
            "instrument_id": row.get("INSTRUMENTID") or row.get("INSTRUMENTID_CH"),
        },
    }


def evaluate_sample(product: str, anchor_s: str, cfg: dict[str, Any], tick: float) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 factorlab-shfe-crosscheck", "Accept": "*/*"})
    raw_url = base.RAW_BASE.format(path=cfg["path"])
    try:
        transport_raw, transport_http = get_bytes(session, raw_url)
        df, transport_parse = base.parse_transport(transport_raw, cfg["git_blob_sha"])
    except Exception as exc:
        return {
            "anchor_date": anchor_s,
            "contract": cfg["contract"],
            "path": cfg["path"],
            "sample_pass": False,
            "unavailable": True,
            "failure_class": "transport_infrastructure_or_schema",
            "error": repr(exc),
        }

    attempts: list[dict[str, Any]] = []
    for day in base.candidate_dates(base.pd.Timestamp(anchor_s)):
        agg = base.aggregate_trading_day(df, day, product)
        if agg is None:
            attempts.append({"date": str(day.date()), "transport": "unavailable"})
            continue
        official = fetch_official_shfe(session, day, cfg["contract"])
        if not official.get("ok"):
            attempts.append({"date": str(day.date()), "transport": "available", "official": official})
            if official.get("failure_class") != "official_exact_contract_row_absent":
                return {
                    "anchor_date": anchor_s,
                    "contract": cfg["contract"],
                    "path": cfg["path"],
                    "transport_file_validation": {"http": transport_http, **transport_parse},
                    "attempts": attempts,
                    "sample_pass": False,
                    "unavailable": True,
                    "failure_class": official.get("failure_class"),
                    "reason": "official infrastructure/payload failure; frozen date fallback is not consumed by host/protocol failures",
                }
            continue
        cmp = base.compare_values(agg["all_bars_ohlc"], official["values"], tick)
        return {
            "anchor_date": anchor_s,
            "chosen_date": str(day.date()),
            "used_fallback_date": str(day.date()) != anchor_s,
            "contract": cfg["contract"],
            "path": cfg["path"],
            "frozen_git_blob_sha": cfg["git_blob_sha"],
            "transport_file_validation": {"http": transport_http, **transport_parse},
            "transport_trading_day": agg,
            "official": official,
            "comparison": cmp,
            "sample_pass": bool(cmp["primary_ohlc_pass"]),
            "failed_attempts_before_chosen": attempts,
        }
    return {
        "anchor_date": anchor_s,
        "contract": cfg["contract"],
        "path": cfg["path"],
        "frozen_git_blob_sha": cfg["git_blob_sha"],
        "transport_file_validation": {"http": transport_http, **transport_parse},
        "attempts": attempts,
        "sample_pass": False,
        "unavailable": True,
        "failure_class": "no_exact_contract_row_within_frozen_date_fallback_window",
    }


def main() -> None:
    sample_freeze = json.loads(SAMPLE_FREEZE.read_text())
    endpoint = json.loads(ENDPOINT_CONTRACT.read_text())
    migration = json.loads(MIGRATION.read_text())
    if migration["status"] != "result_free_before_fetching_any_official_OHLC_from_migrated_endpoints":
        raise AssertionError("endpoint migration was not frozen result-free")
    if migration["first_audit"]["official_OHLC_values_retrieved"] != 0:
        raise AssertionError("migration correction is not value-free")

    tasks = []
    for product in ["SHFE_CU", "SHFE_RB"]:
        pcfg = sample_freeze["sample_design"]["products"][product]
        tick = float(endpoint["minimum_price_ticks"][product]["tick"])
        for anchor_s, cfg in pcfg["contracts_by_date"].items():
            tasks.append((product, anchor_s, cfg, tick))
    if len(tasks) != 6:
        raise AssertionError(("frozen SHFE sample count changed", len(tasks)))

    by_product: dict[str, list[dict[str, Any]]] = {"SHFE_CU": [], "SHFE_RB": []}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(evaluate_sample, *t): (t[0], t[1]) for t in tasks}
        for fut in as_completed(futures):
            product, anchor = futures[fut]
            try:
                row = fut.result()
            except Exception as exc:
                row = {"anchor_date": anchor, "sample_pass": False, "unavailable": True, "failure_class": "worker_error", "error": repr(exc)}
            by_product[product].append(row)

    products: dict[str, Any] = {}
    for product in ["SHFE_CU", "SHFE_RB"]:
        rows = sorted(by_product[product], key=lambda x: x["anchor_date"])
        n_pass = sum(bool(x.get("sample_pass")) for x in rows)
        products[product] = {
            "samples": rows,
            "sample_pass_count": int(n_pass),
            "sample_total": len(rows),
            "product_pass": bool(n_pass >= 2),
        }

    both_pass = all(v["product_pass"] for v in products.values())
    any_true_price_failure = any(
        (not s.get("sample_pass", False)) and (not s.get("unavailable", False))
        for p in products.values() for s in p["samples"]
    )
    if both_pass:
        status = "SHFE_CU_RB_transport_subset_admitted_waiting_separate_predictive_preregistration"
    elif any_true_price_failure:
        status = "SHFE_transport_subset_not_admitted_due_frozen_price_crosscheck_failure"
    else:
        status = "SHFE_migrated_endpoint_or_payload_infrastructure_gap_prevents_subset_admission"

    report = {
        "schema_id": "overnight_open_domestic_night_shfe_migrated_crosscheck_results@1.0",
        "data_boundary": {"CSI1000_target_rows_read": 0, "post_2020_transport_rows_read": 0},
        "sample_freeze": str(SAMPLE_FREEZE.relative_to(ROOT)),
        "endpoint_migration_correction": str(MIGRATION.relative_to(ROOT)),
        "official_provider": "Shanghai Futures Exchange",
        "official_url_template": SHFE_URL,
        "products": products,
        "DCE_I": {
            "status": "official_auth_access_blocked_not_price_rejected",
            "included_in_this_run": False,
            "may_enter_future_predictive_candidate": False
        },
        "summary": {
            "SHFE_product_pass_count": sum(bool(v["product_pass"]) for v in products.values()),
            "SHFE_product_total": 2,
            "SHFE_subset_admission_pass": bool(both_pass),
            "scientific_status": status
        },
        "authority": {"predictive_model_execution": False, "fresh_oos": False, "baseline_replacement": False, "production": False, "registry_mutation": False, "merge_main": False}
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
