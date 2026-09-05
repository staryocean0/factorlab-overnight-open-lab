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
SPEC = importlib.util.spec_from_file_location(
    "night_audit_base", ROOT / "scripts/audit_domestic_night_source_crosscheck.py"
)
base = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(base)

# Pure transport/runtime correction. Research samples, endpoints, clocks, tolerances,
# product set and fallback ordering remain frozen in the already-committed contracts.
HTTP_TIMEOUT_SECONDS = 20
HTTP_ATTEMPTS_PER_ENDPOINT = 2
MAX_SAMPLE_WORKERS = 9


def bounded_fetch(
    session: requests.Session,
    url: str,
    *,
    method: str = "GET",
    data: dict[str, str] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    last: Exception | None = None
    for attempt in range(HTTP_ATTEMPTS_PER_ENDPOINT):
        try:
            if method == "POST":
                r = session.post(url, data=data, timeout=HTTP_TIMEOUT_SECONDS, allow_redirects=True)
            else:
                r = session.get(url, timeout=HTTP_TIMEOUT_SECONDS, allow_redirects=True)
            if r.status_code != 200:
                raise RuntimeError(("http", r.status_code, url, r.text[:160]))
            raw = r.content
            return raw, {
                "requested_url": url,
                "final_url": r.url,
                "status": r.status_code,
                "content_type": r.headers.get("content-type"),
                "bytes": len(raw),
                "sha256": base.sha256_bytes(raw),
                "transport_attempt": attempt + 1,
                "timeout_seconds": HTTP_TIMEOUT_SECONDS,
            }
        except Exception as exc:
            last = exc
            if attempt + 1 < HTTP_ATTEMPTS_PER_ENDPOINT:
                time.sleep(0.75 * (attempt + 1))
    assert last is not None
    raise last


# All official-source functions in the base module resolve this global at call time.
base.fetch = bounded_fetch


def evaluate_one(
    product: str,
    pcfg: dict[str, Any],
    anchor_s: str,
    scfg: dict[str, Any],
    endpoint_contract: dict[str, Any],
) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": base.UA, "Accept": "*/*"})

    path = scfg["path"]
    raw, raw_meta = bounded_fetch(session, base.RAW_BASE.format(path=path))
    df, pmeta = base.parse_transport(raw, scfg["git_blob_sha"])
    transport_meta = {"raw_response": raw_meta, **pmeta}

    attempts: list[dict[str, Any]] = []
    for day in base.candidate_dates(base.pd.Timestamp(anchor_s)):
        agg = base.aggregate_trading_day(df, day, product)
        if agg is None:
            attempts.append({"date": str(day.date()), "transport": "unavailable"})
            continue
        official = (
            base.fetch_shfe(session, day, scfg["contract"], endpoint_contract)
            if product.startswith("SHFE_")
            else base.fetch_dce(session, day, scfg["contract"], endpoint_contract)
        )
        if not official.get("ok"):
            attempts.append(
                {"date": str(day.date()), "transport": "available", "official": official}
            )
            continue
        tick = float(endpoint_contract["minimum_price_ticks"][product]["tick"])
        cmp = base.compare_values(agg["all_bars_ohlc"], official["values"], tick)
        return {
            "anchor_date": anchor_s,
            "chosen_date": str(day.date()),
            "used_fallback_date": str(day.date()) != anchor_s,
            "contract": scfg["contract"],
            "path": path,
            "frozen_git_blob_sha": scfg["git_blob_sha"],
            "transport_file_validation": transport_meta,
            "transport_trading_day": agg,
            "official": official,
            "comparison": cmp,
            "sample_pass": bool(cmp["primary_ohlc_pass"]),
            "failed_attempts_before_chosen": attempts,
        }

    return {
        "anchor_date": anchor_s,
        "contract": scfg["contract"],
        "path": path,
        "frozen_git_blob_sha": scfg["git_blob_sha"],
        "transport_file_validation": transport_meta,
        "attempts": attempts,
        "sample_pass": False,
        "unavailable": True,
        "reason": "no_date_with_both_transport_aggregate_and_machine_readable_exact_official_contract_row_within_frozen_window",
    }


def main() -> None:
    freeze = json.loads(base.SAMPLE_FREEZE.read_text())
    endpoint_contract = json.loads(base.ENDPOINT_CONTRACT.read_text())
    clock_freeze = json.loads(base.CLOCK_FREEZE.read_text())
    if freeze["status"] != "result_free_before_fetching_crosscheck_price_values":
        raise AssertionError("sample freeze status invalid")
    if endpoint_contract["status"] != "result_free_before_official_daily_price_fetch":
        raise AssertionError("endpoint/tolerance contract status invalid")
    if clock_freeze["status"] != "frozen_before_crosscheck_price_values":
        raise AssertionError("clock evidence not frozen")

    tasks: list[tuple[str, dict[str, Any], str, dict[str, Any]]] = []
    for product, pcfg in freeze["sample_design"]["products"].items():
        for anchor_s, scfg in pcfg["contracts_by_date"].items():
            tasks.append((product, pcfg, anchor_s, scfg))
    if len(tasks) != 9:
        raise AssertionError(("frozen sample count changed", len(tasks)))

    by_product: dict[str, list[dict[str, Any]]] = {
        p: [] for p in freeze["sample_design"]["products"]
    }
    with ThreadPoolExecutor(max_workers=MAX_SAMPLE_WORKERS) as ex:
        futures = {
            ex.submit(evaluate_one, product, pcfg, anchor_s, scfg, endpoint_contract):
            (product, anchor_s)
            for product, pcfg, anchor_s, scfg in tasks
        }
        for fut in as_completed(futures):
            product, anchor_s = futures[fut]
            try:
                sample = fut.result()
            except Exception as exc:
                # Preserve infrastructure failure as an unavailable frozen sample;
                # never silently replace its product/contract/date family.
                sample_cfg = freeze["sample_design"]["products"][product]["contracts_by_date"][anchor_s]
                sample = {
                    "anchor_date": anchor_s,
                    "contract": sample_cfg["contract"],
                    "path": sample_cfg["path"],
                    "frozen_git_blob_sha": sample_cfg["git_blob_sha"],
                    "sample_pass": False,
                    "unavailable": True,
                    "reason": "sample_worker_infrastructure_error",
                    "error": repr(exc),
                }
            by_product[product].append(sample)

    results: dict[str, Any] = {}
    for product, pcfg in freeze["sample_design"]["products"].items():
        samples = sorted(by_product[product], key=lambda x: x["anchor_date"])
        pass_count = sum(bool(x.get("sample_pass")) for x in samples)
        results[product] = {
            "economic_role": pcfg["economic_role"],
            "samples": samples,
            "sample_pass_count": int(pass_count),
            "sample_total": len(samples),
            "product_pass": bool(pass_count >= 2),
        }

    all_products_pass = all(x["product_pass"] for x in results.values())
    unavailable = sum(
        bool(s.get("unavailable")) for p in results.values() for s in p["samples"]
    )
    failed_price = sum(
        (not bool(s.get("sample_pass"))) and (not bool(s.get("unavailable")))
        for p in results.values() for s in p["samples"]
    )
    if all_products_pass:
        status = "transport_source_admitted_for_predefined_products_waiting_separate_predictive_preregistration"
    elif unavailable and failed_price == 0:
        status = "infrastructure_gap_official_daily_price_retrieval_or_parse_prevents_admission"
    else:
        status = "transport_source_not_admitted_under_frozen_crosscheck_gates"

    report = {
        "schema_id": "overnight_open_domestic_night_source_crosscheck_results@1.1",
        "sample_freeze": str(base.SAMPLE_FREEZE.relative_to(ROOT)),
        "endpoint_contract": str(base.ENDPOINT_CONTRACT.relative_to(ROOT)),
        "clock_evidence": str(base.CLOCK_FREEZE.relative_to(ROOT)),
        "execution_transport": {
            "parallel_frozen_sample_workers": MAX_SAMPLE_WORKERS,
            "http_timeout_seconds": HTTP_TIMEOUT_SECONDS,
            "http_attempts_per_endpoint": HTTP_ATTEMPTS_PER_ENDPOINT,
            "research_definitions_changed": False,
        },
        "data_boundary": {
            "CSI1000_target_rows_read": 0,
            "post_2020_transport_rows_read": 0,
        },
        "products": results,
        "summary": {
            "product_pass_count": sum(bool(x["product_pass"]) for x in results.values()),
            "product_total": len(results),
            "unavailable_sample_count": int(unavailable),
            "failed_price_sample_count": int(failed_price),
            "source_admission_pass": bool(all_products_pass),
            "scientific_status": status,
        },
        "authority": {
            "predictive_model_execution": False,
            "fresh_oos": False,
            "baseline_replacement": False,
            "production": False,
            "registry_mutation": False,
            "merge_main": False,
        },
    }
    base.OUT.parent.mkdir(parents=True, exist_ok=True)
    base.OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
