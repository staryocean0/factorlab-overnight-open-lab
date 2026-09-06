#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_OUT = ROOT / "data/external/sgx_a50_ordinary_preauction_endpoints_2015_2020.csv"
PARQUET_OUT = ROOT / "data/development/sgx_a50_ordinary_preauction_endpoints.parquet"
NAV_OUT = ROOT / "data/external/sgx_historical_date_index_used_ordinary_2015_2020.json"
MANIFEST_OUT = ROOT / "docs/governance/external_sgx_a50_ordinary_preauction_2015_2020_manifest.json"
PACKAGE_MANIFEST = ROOT / "data/manifest.json"
YEARS = [2015, 2016, 2017, 2018, 2019, 2020]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def merge_unique_dict(dst: dict, src: dict, label: str) -> None:
    for k, v in src.items():
        if k in dst and dst[k] != v:
            raise AssertionError(("conflicting repeated key", label, k))
        dst[k] = v


def _stable_archive_record(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "headers"}


def merge_archive_records(dst: dict, src: dict, source_year: int) -> None:
    for date, record in src.items():
        stable = _stable_archive_record(record)
        observation = {
            "source_year": int(source_year),
            "headers": record.get("headers", {}),
        }
        if date not in dst:
            dst[date] = {
                **stable,
                "retrieval_observations": [observation],
            }
            continue
        existing_stable = {
            k: v for k, v in dst[date].items() if k != "retrieval_observations"
        }
        if existing_stable != stable:
            raise AssertionError(("conflicting repeated archive stable identity", date))
        dst[date]["retrieval_observations"].append(observation)


def discover_year_files(indir: Path, prefix: str, suffix: str, years: list[int] | None = None) -> list[Path]:
    expected = YEARS if years is None else years
    found: dict[int, list[Path]] = {year: [] for year in expected}
    for path in indir.rglob(f"{prefix}*{suffix}"):
        name = path.name
        if not name.startswith(prefix) or not name.endswith(suffix):
            continue
        middle = name[len(prefix): len(name) - len(suffix)]
        if not middle.isdigit():
            continue
        year = int(middle)
        if year in found:
            found[year].append(path)
    problems = {
        str(year): [str(p.relative_to(indir)) for p in paths]
        for year, paths in found.items()
        if len(paths) != 1
    }
    if problems:
        raise AssertionError(("yearly artifact discovery must resolve exactly one file per year", prefix, suffix, problems))
    return [found[year][0] for year in expected]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="artifacts/staging/a50_ordinary_combined")
    args = ap.parse_args()
    indir = ROOT / args.input_dir
    endpoint_files = discover_year_files(indir, "a50_ordinary_endpoints_", ".csv")
    manifest_files = discover_year_files(indir, "a50_ordinary_manifest_", ".json")
    nav_files = discover_year_files(indir, "a50_ordinary_navigation_", ".json")

    frames = []
    yearly: dict[str, dict] = {}
    used_archives: dict[str, dict] = {}
    used_index: dict[str, int | None] = {}
    unavailable: list[dict] = []
    schema_counts: dict[str, int] = {}
    total_events = 0
    total_usable = 0
    total_blank_price_trade_rows = 0
    for ep, mp, np in zip(endpoint_files, manifest_files, nav_files, strict=True):
        year = int(ep.stem.rsplit("_", 1)[1])
        frame = pd.read_csv(ep)
        if not frame.empty:
            frame["trading_day"] = pd.to_datetime(frame["trading_day"], errors="raise").dt.normalize()
            frame["previous_china_day"] = pd.to_datetime(frame["previous_china_day"], errors="raise").dt.normalize()
            if not frame["trading_day"].dt.year.eq(year).all():
                raise AssertionError(("yearly endpoint target-year mismatch", year))
            frames.append(frame)
        man = json.loads(mp.read_text())
        nav = json.loads(np.read_text())
        if int(man["year"]) != year or int(nav["year"]) != year:
            raise AssertionError(("year metadata mismatch", year))
        yearly[str(year)] = {
            "events_total": int(man["events_total"]),
            "events_usable": int(man["events_usable"]),
            "coverage": float(man["coverage"]),
            "required_archive_dates": int(man["required_archive_dates"]),
            "archives_parsed": int(man["archives_parsed"]),
            "archive_failure_count": len(man["archive_failures"]),
            "blank_price_trade_rows_skipped": int(man.get("blank_price_trade_rows_skipped", 0)),
        }
        total_events += int(man["events_total"])
        total_usable += int(man["events_usable"])
        total_blank_price_trade_rows += int(man.get("blank_price_trade_rows_skipped", 0))
        unavailable.extend(man["unavailable_events"])
        merge_archive_records(used_archives, man["used_archives"], year)
        merge_unique_dict(used_index, nav["used_date_to_key"], "navigation")
        for k, v in man["schema_counts"].items():
            schema_counts[k] = schema_counts.get(k, 0) + int(v)

    if not frames:
        raise AssertionError("no ordinary A50 endpoints across 2015-2020")
    out = pd.concat(frames, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
    if out["trading_day"].duplicated().any():
        raise AssertionError("duplicate ordinary A50 target days")
    if out["trading_day"].min() < pd.Timestamp("2015-01-01") or out["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("ordinary A50 date boundary violated")
    if out["target_end_time"].astype(str).str.zfill(6).ge("091500").any():
        raise AssertionError("ordinary A50 target endpoint at or after 09:15")
    if out["start_time"].astype(str).str.zfill(6).gt("150000").any():
        raise AssertionError("ordinary A50 start endpoint after 15:00")
    if (out["a50_ordinary_preauction_closure_return"].abs() > 0.30).any():
        raise AssertionError("ordinary A50 return outside conservative 30% single-closure sanity bound")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    csv = out.copy()
    csv["trading_day"] = csv["trading_day"].dt.strftime("%Y-%m-%d")
    csv["previous_china_day"] = csv["previous_china_day"].dt.strftime("%Y-%m-%d")
    csv.to_csv(CSV_OUT, index=False, float_format="%.12g", lineterminator="\n")
    PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(PARQUET_OUT, index=False)
    NAV_OUT.write_text(json.dumps({
        "schema_id": "sgx_a50_ordinary_navigation_2015_2020@1.0",
        "role": "date-to-key navigation only; no market prices",
        "source_repository": "blurridge/sgx-derivative-downloader",
        "pinned_commit": "303df3f2c6a71b84cab3c5354c9bf936fb6ef082",
        "used_date_to_key": dict(sorted(used_index.items())),
    }, indent=2, sort_keys=True) + "\n")

    repeated_archive_retrieval_dates = [
        date for date, record in used_archives.items()
        if len(record.get("retrieval_observations", [])) > 1
    ]
    manifest = {
        "schema_id": "external_sgx_a50_ordinary_preauction_2015_2020_manifest@1.2",
        "frozen_retrieval_date": "2026-09-05",
        "provider": "Singapore Exchange official historical derivatives endpoint",
        "commodity_code": "CN",
        "target_cutoff": "09:14:59 Singapore/Beijing time",
        "event_definition": "holiday_reopen == 0 in bounded CSI1000 panel",
        "contract_selection": "nearest non-past CN contract month with an actual trade at or before previous China 15:00; same contract required at target",
        "schema_correction": "docs/governance/global_spillover_v6_sgx_legacy_schema_correction.json",
        "coverage": {
            "events_total": int(total_events),
            "events_usable": int(total_usable),
            "overall": float(total_usable / total_events),
            "by_target_year": yearly,
        },
        "schema_archive_counts": schema_counts,
        "blank_price_trade_rows_skipped": int(total_blank_price_trade_rows),
        "repeated_archive_retrieval_dates": sorted(repeated_archive_retrieval_dates),
        "repeated_archive_merge_rule": "stable archive identity fields must match exactly; dynamic HTTP retrieval headers are retained as separate retrieval observations",
        "unavailable_events": unavailable,
        "assets": {
            str(CSV_OUT.relative_to(ROOT)): {"sha256": sha256_file(CSV_OUT)},
            str(PARQUET_OUT.relative_to(ROOT)): {"sha256": sha256_file(PARQUET_OUT)},
            str(NAV_OUT.relative_to(ROOT)): {"sha256": sha256_file(NAV_OUT)},
        },
        "guards": {
            "future_volume_contract_selection": False,
            "mid_window_roll": False,
            "post_2020_rows": 0,
            "target_ticks_at_or_after_091500": 0,
            "raw_full_market_archives_committed": False,
            "field_resolution_by_header": True,
            "legacy_Y_trade_code_supported": True,
            "legacy_blank_price_trade_rows_skipped_not_fatal": True,
            "settlement_S_used_as_trade": False,
        },
        "used_archives": dict(sorted(used_archives.items())),
    }
    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    package = json.loads(PACKAGE_MANIFEST.read_text())
    rel = str(PARQUET_OUT.relative_to(ROOT))
    product = {
        "path": rel,
        "rows": int(len(out)),
        "bytes": int(PARQUET_OUT.stat().st_size),
        "sha256": sha256_file(PARQUET_OUT),
        "min_day": str(out["trading_day"].min().date()),
        "max_day": str(out["trading_day"].max().date()),
    }
    package["products"] = [x for x in package["products"] if x["path"] != rel] + [product]
    PACKAGE_MANIFEST.write_text(json.dumps(package, indent=2) + "\n")
    print(json.dumps({
        "events_total": total_events,
        "events_usable": total_usable,
        "coverage": total_usable / total_events,
        "rows": len(out),
        "schema_archive_counts": schema_counts,
        "blank_price_trade_rows_skipped": total_blank_price_trade_rows,
        "repeated_archive_retrieval_dates": sorted(repeated_archive_retrieval_dates),
        "by_target_year": yearly,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
