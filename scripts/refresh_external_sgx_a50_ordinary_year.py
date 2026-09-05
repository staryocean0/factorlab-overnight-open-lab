#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

import sgx_cn_tick as sgx

ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
NAV_COMMIT = "303df3f2c6a71b84cab3c5354c9bf936fb6ef082"
NAV_URL = f"https://raw.githubusercontent.com/blurridge/sgx-derivative-downloader/{NAV_COMMIT}/db/indexes.json"
SGX_URL = "https://links.sgx.com/1.0.0/derivatives-historical/{key}/WEBPXTICK_DT.zip"
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024


def fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "factorlab-overnight-open-lab/phase6"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode("utf-8"))


def download_and_parse(date: str, key: int, tmpdir: Path) -> tuple[str, dict, dict]:
    url = SGX_URL.format(key=key)
    last_exc: Exception | None = None
    for attempt in range(4):
        path = tmpdir / f"{date}-{key}.zip"
        h = hashlib.sha256()
        size = 0
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 factorlab-phase6"})
            with urllib.request.urlopen(req, timeout=90) as r, path.open("wb") as out:
                if int(r.status) != 200:
                    raise RuntimeError((date, key, r.status))
                headers = {k.lower(): v for k, v in r.headers.items()}
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_ARCHIVE_BYTES:
                        raise RuntimeError(("archive too large", date, size))
                    h.update(chunk)
                    out.write(chunk)
            summary = sgx.parse_cn_summary_from_zip(path, date)
            meta = {
                "key": int(key),
                "url": url,
                "bytes": int(size),
                "sha256": h.hexdigest(),
                "member": summary["member"],
                "schema_id": summary["schema_id"],
                "delimiter": summary["delimiter"],
                "header_fields": summary["header_fields"],
                "cn_rows": int(summary["cn_rows"]),
                "cn_futures_rows": int(summary["cn_futures_rows"]),
                "eligible_trade_rows": int(summary["eligible_trade_rows"]),
                "nonblank_trade_amend_rows": int(summary["nonblank_trade_amend_rows"]),
                "message_counts": summary["message_counts"],
                "trade_code_counts": summary["trade_code_counts"],
                "unknown_message_counts": summary["unknown_message_counts"],
                "headers": headers,
            }
            path.unlink(missing_ok=True)
            return date, meta, summary
        except Exception as exc:
            last_exc = exc
            path.unlink(missing_ok=True)
            time.sleep(1.5 * (attempt + 1))
    assert last_exc is not None
    raise last_exc


def build_events(year: int) -> pd.DataFrame:
    panel = pd.read_parquet(PANEL_PATH).copy().sort_values("trading_day").reset_index(drop=True)
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    panel["previous_china_day"] = panel["trading_day"].shift(1)
    ordinary = pd.to_numeric(panel["holiday_reopen"], errors="coerce").fillna(0).eq(0)
    events = panel.loc[
        ordinary & panel["trading_day"].dt.year.eq(year) & panel["previous_china_day"].notna(),
        ["trading_day", "previous_china_day"],
    ].copy()
    if events.empty:
        raise AssertionError(("no ordinary events", year))
    return events


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True, choices=range(2015, 2021))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--output-dir", default="artifacts/staging/a50_ordinary")
    args = ap.parse_args()
    year = int(args.year)
    events = build_events(year)

    nav = fetch_json(NAV_URL)
    if not isinstance(nav, dict):
        raise AssertionError("SGX navigation index is not a dict")
    required_dates = sorted({d.strftime("%Y%m%d") for d in pd.concat([events["trading_day"], events["previous_china_day"]])})
    used_index = {d: int(nav[d]) if d in nav else None for d in required_dates}
    fetchable = {d: k for d, k in used_index.items() if k is not None}

    archive_meta: dict[str, dict] = {}
    summaries: dict[str, dict] = {}
    failures: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix=f"sgx-a50-{year}-") as td:
        tmpdir = Path(td)
        with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
            futs = {ex.submit(download_and_parse, d, int(k), tmpdir): d for d, k in fetchable.items()}
            for fut in as_completed(futs):
                d = futs[fut]
                try:
                    date, meta, summary = fut.result()
                    archive_meta[date] = meta
                    summaries[date] = summary
                except Exception as exc:
                    failures[d] = repr(exc)

    rows: list[dict] = []
    unavailable: list[dict] = []
    for _, ev in events.iterrows():
        target = pd.Timestamp(ev["trading_day"])
        prev = pd.Timestamp(ev["previous_china_day"])
        td = target.strftime("%Y%m%d")
        pd_ = prev.strftime("%Y%m%d")
        base = {"trading_day": str(target.date()), "previous_china_day": str(prev.date())}
        if used_index.get(pd_) is None:
            unavailable.append({**base, "reason": "previous_china_day_navigation_key_unavailable"})
            continue
        if used_index.get(td) is None:
            unavailable.append({**base, "reason": "target_china_day_navigation_key_unavailable"})
            continue
        if pd_ not in summaries:
            unavailable.append({**base, "reason": "previous_china_day_SGX_archive_or_parse_unavailable", "detail": failures.get(pd_)})
            continue
        if td not in summaries:
            unavailable.append({**base, "reason": "target_china_day_SGX_archive_or_parse_unavailable", "detail": failures.get(td)})
            continue
        chosen = sgx.choose_contract(summaries[pd_], prev)
        if chosen is None:
            unavailable.append({**base, "reason": "no_eligible_CN_contract_trade_by_previous_150000"})
            continue
        cid, start_contract = chosen
        target_contract = summaries[td]["contracts"].get(cid)
        if target_contract is None or target_contract.get("last_le_091459") is None:
            unavailable.append({**base, "contract": cid, "reason": "same_contract_has_no_target_trade_by_091459"})
            continue
        start = start_contract["last_le_150000"]
        end = target_contract["last_le_091459"]
        assert start is not None and end is not None
        if not start["time"] <= "150000" or not end["time"] < "091500":
            raise AssertionError(("endpoint clock violation", target, start, end))
        rows.append({
            "trading_day": str(target.date()),
            "previous_china_day": str(prev.date()),
            "contract": cid,
            "delivery_year": int(start_contract["delivery_year"]),
            "delivery_month": int(start_contract["delivery_month"]),
            "start_time": start["time"],
            "start_price": float(start["price"]),
            "target_end_time": end["time"],
            "target_end_price": float(end["price"]),
            "a50_ordinary_preauction_closure_return": float(end["price"] / start["price"] - 1.0),
            "previous_archive_key": int(archive_meta[pd_]["key"]),
            "previous_archive_sha256": archive_meta[pd_]["sha256"],
            "target_archive_key": int(archive_meta[td]["key"]),
            "target_archive_sha256": archive_meta[td]["sha256"],
        })

    outdir = ROOT / args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    endpoint_path = outdir / f"a50_ordinary_endpoints_{year}.csv"
    manifest_path = outdir / f"a50_ordinary_manifest_{year}.json"
    navigation_path = outdir / f"a50_ordinary_navigation_{year}.json"
    pd.DataFrame(rows).to_csv(endpoint_path, index=False, float_format="%.12g", lineterminator="\n")
    navigation_path.write_text(json.dumps({
        "schema_id": "sgx_a50_ordinary_navigation_year@1.0",
        "year": year,
        "source_repository": "blurridge/sgx-derivative-downloader",
        "pinned_commit": NAV_COMMIT,
        "source_path": "db/indexes.json",
        "used_date_to_key": used_index,
    }, indent=2, sort_keys=True) + "\n")
    schema_counts: dict[str, int] = {}
    for m in archive_meta.values():
        schema_counts[m["schema_id"]] = schema_counts.get(m["schema_id"], 0) + 1
    manifest = {
        "schema_id": "external_sgx_a50_ordinary_year_manifest@1.0",
        "year": year,
        "provider": "Singapore Exchange official historical derivatives endpoint",
        "commodity_code": "CN",
        "target_cutoff": "09:14:59 Singapore/Beijing time",
        "event_definition": "holiday_reopen == 0 in bounded CSI1000 panel",
        "events_total": int(len(events)),
        "events_usable": int(len(rows)),
        "coverage": float(len(rows) / len(events)),
        "required_archive_dates": int(len(required_dates)),
        "archives_parsed": int(len(archive_meta)),
        "archive_failures": failures,
        "schema_counts": schema_counts,
        "unavailable_events": unavailable,
        "used_archives": archive_meta,
        "guards": {
            "future_volume_contract_selection": False,
            "mid_window_roll": False,
            "post_2020_rows": 0,
            "target_ticks_at_or_after_091500": 0,
            "raw_full_market_archives_committed": False,
            "field_resolution_by_header": True,
            "legacy_Y_trade_code_supported": True,
            "settlement_S_used_as_trade": False,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: manifest[k] for k in ["year", "events_total", "events_usable", "coverage", "required_archive_dates", "archives_parsed", "schema_counts"]}, indent=2))


if __name__ == "__main__":
    main()
