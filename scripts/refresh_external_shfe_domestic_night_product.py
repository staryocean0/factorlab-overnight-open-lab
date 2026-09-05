#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shfe_domestic_night_extract as core  # noqa: E402

PANEL = ROOT / "data/development/csi1000_open_pit_panel.parquet"
PREREG = ROOT / "docs/governance/global_spillover_v7_domestic_night_preregistration.json"
SCOPE_CORRECTION = ROOT / "docs/governance/global_spillover_v7_domestic_night_holiday_scope_correction.json"


def indexed_night_stats(df: pd.DataFrame, previous_days: set[pd.Timestamp], product: str) -> dict[pd.Timestamp, dict[str, Any]]:
    out: dict[pd.Timestamp, dict[str, Any]] = {}
    if df.empty:
        return out
    positive = df.loc[df["volume"] > 0].copy()
    if positive.empty:
        return out
    for _, row in positive.iterrows():
        ts = pd.Timestamp(row["datetime"])
        d = ts.normalize()
        t = ts.strftime("%H%M%S")
        prev: pd.Timestamp | None = None
        if t >= "210000":
            prev = d
            if product == "RB" and prev > core.RB_QUARANTINE_END and t > "230000":
                prev = None
        elif t <= "010000":
            candidate = d - pd.Timedelta(days=1)
            if product == "CU":
                prev = candidate
            elif product == "RB" and candidate < core.RB_QUARANTINE_START:
                prev = candidate
        if prev is None or prev not in previous_days:
            continue
        if product == "RB" and core.RB_QUARANTINE_START <= prev <= core.RB_QUARANTINE_END:
            continue
        cur = out.get(prev)
        if cur is None or ts > pd.Timestamp(cur["night_end_datetime"]):
            out[prev] = {
                "positive_volume_bar_count": 1 if cur is None else int(cur["positive_volume_bar_count"]) + 1,
                "night_end_datetime": str(ts),
                "night_end_close": float(row["close"]),
            }
        else:
            cur["positive_volume_bar_count"] = int(cur["positive_volume_bar_count"]) + 1
    return out


def process_source(source: core.SourceFile, previous_days: set[pd.Timestamp]) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update({"User-Agent": "factorlab-overnight-domestic-night-v7/1.0"})
    raw, retrieval = core.fetch_raw(session, source)
    df, parsed = core.parse_bounded_contract(raw, source.blob_sha)
    day = core.daytime_stats(df)
    night = indexed_night_stats(df, previous_days, source.product)
    return {
        "source": source,
        "retrieval": retrieval,
        "parsed": parsed,
        "day": day,
        "night": night,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", required=True, choices=["CU", "RB"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--output-dir", default="artifacts/staging/domestic_night")
    args = ap.parse_args()
    product = args.product.upper()

    prereg = json.loads(PREREG.read_text())
    scope = json.loads(SCOPE_CORRECTION.read_text())
    if prereg["status"] != "result_free_before_bulk_CU_RB_extraction_and_any_v7_target_model_execution":
        raise AssertionError("v7 preregistration not result-free")
    if scope["status"] != "result_free_before_bulk_CU_RB_extraction_and_any_v7_target_model_execution":
        raise AssertionError("v7 holiday correction not result-free")

    # Read only session metadata needed to define P->T and ordinary scope. No gap.
    panel = pd.read_parquet(PANEL, columns=["trading_day", "holiday_reopen"]).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China metadata row")
    panel = panel.sort_values("trading_day").reset_index(drop=True)
    panel["previous_china_day"] = panel["trading_day"].shift(1)
    ordinary = pd.to_numeric(panel["holiday_reopen"], errors="raise") == 0
    events = panel.loc[
        ordinary
        & panel["previous_china_day"].notna()
        & panel["trading_day"].between(pd.Timestamp("2015-01-01"), pd.Timestamp("2020-12-31")),
        ["trading_day", "previous_china_day"],
    ].copy()
    previous_days = set(pd.to_datetime(events["previous_china_day"]).dt.normalize())

    tree_session = requests.Session()
    tree_session.headers.update({"User-Agent": "factorlab-overnight-domestic-night-v7/1.0", "Accept": "application/vnd.github+json"})
    tree = core.fetch_json(tree_session, core.TREE_URL)
    if tree.get("sha") not in {None, core.PINNED_TREE}:
        raise AssertionError(("unexpected pinned tree response", tree.get("sha"), core.PINNED_TREE))
    sources = core.enumerate_source_files(tree, product)

    day_by_contract: dict[str, dict[pd.Timestamp, dict[str, Any]]] = {}
    night_by_contract: dict[str, dict[pd.Timestamp, dict[str, Any]]] = {}
    source_meta: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {ex.submit(process_source, s, previous_days): s for s in sources}
        for fut in as_completed(futures):
            s = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:
                failures.append({"contract": s.contract, "path": s.path, "git_blob_sha": s.blob_sha, "error": repr(exc)})
                continue
            day_by_contract[s.contract] = result["day"]
            night_by_contract[s.contract] = result["night"]
            source_meta[s.contract] = {
                "path": s.path,
                "delivery_year": s.delivery_year,
                "delivery_month": s.delivery_month,
                "tree_git_blob_sha": s.blob_sha,
                "tree_size": s.size,
                "retrieval": result["retrieval"],
                "bounded_parse": result["parsed"],
            }

    if failures:
        raise AssertionError(("one or more pinned contract files failed", product, failures[:10], len(failures)))
    if len(source_meta) != len(sources):
        raise AssertionError(("source inventory incomplete", len(source_meta), len(sources)))
    if any(int(m["bounded_parse"].get("post_2020_market_fields_parsed", -1)) != 0 for m in source_meta.values()):
        raise AssertionError("post-2020 market field parse detected")

    source_lookup = {s.contract: s for s in sources}
    rows: list[dict[str, Any]] = []
    unavailable: list[dict[str, Any]] = []
    for _, ev in events.iterrows():
        target = pd.Timestamp(ev["trading_day"]).normalize()
        prev = pd.Timestamp(ev["previous_china_day"]).normalize()
        candidates: list[dict[str, Any]] = []
        for contract, days in day_by_contract.items():
            stat = days.get(prev)
            if stat is None:
                continue
            source = source_lookup[contract]
            candidates.append({
                "contract": contract,
                "delivery_year": source.delivery_year,
                "delivery_month": source.delivery_month,
                **stat,
            })
        chosen = core.choose_contract(candidates, prev)
        if chosen is None:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "reason": "no_eligible_contract_with_previous_day_bar"})
            continue
        contract = str(chosen["contract"])
        if chosen["start_1455_close"] is None:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "contract": contract, "reason": "selected_contract_missing_exact_1455_start"})
            continue
        if product == "RB" and core.RB_QUARANTINE_START <= prev <= core.RB_QUARANTINE_END:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "contract": contract, "reason": "RB_transition_quarantine"})
            continue
        night = night_by_contract.get(contract, {}).get(prev)
        if night is None or int(night.get("positive_volume_bar_count", 0)) <= 0 or night.get("night_end_close") is None:
            unavailable.append({"trading_day": str(target.date()), "previous_china_day": str(prev.date()), "contract": contract, "reason": "selected_contract_has_no_positive_volume_night_activity"})
            continue
        start_price = float(chosen["start_1455_close"])
        end_price = float(night["night_end_close"])
        if start_price <= 0 or end_price <= 0:
            raise AssertionError(("nonpositive endpoint price", target, contract, start_price, end_price))
        source = source_lookup[contract]
        ret = end_price / start_price - 1.0
        if abs(ret) > 0.30:
            raise AssertionError(("night return outside 30% sanity bound", target, contract, ret))
        rows.append({
            "trading_day": target,
            "previous_china_day": prev,
            "product": product,
            "contract": contract,
            "delivery_year": int(source.delivery_year),
            "delivery_month": int(source.delivery_month),
            "previous_day_volume_0900_1455": float(chosen["day_volume_0900_1455"]),
            "previous_1455_close": start_price,
            "previous_1455_volume": float(chosen["start_1455_volume"]),
            "night_positive_volume_bar_count": int(night["positive_volume_bar_count"]),
            "night_end_datetime": pd.Timestamp(night["night_end_datetime"]),
            "night_end_close": end_price,
            f"{product.lower()}_night_return": float(ret),
            "source_path": source.path,
            "source_git_blob_sha": source.blob_sha,
        })

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise AssertionError(("no usable night endpoints", product))
    frame = frame.sort_values("trading_day").reset_index(drop=True)
    if frame["trading_day"].duplicated().any():
        raise AssertionError("duplicate target day")
    if frame["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 endpoint")

    outdir = ROOT / args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"shfe_{product.lower()}_night_endpoints_2015_2020.csv"
    manifest_path = outdir / f"shfe_{product.lower()}_night_manifest_2015_2020.json"
    csv_frame = frame.copy()
    csv_frame["trading_day"] = csv_frame["trading_day"].dt.strftime("%Y-%m-%d")
    csv_frame["previous_china_day"] = csv_frame["previous_china_day"].dt.strftime("%Y-%m-%d")
    csv_frame["night_end_datetime"] = pd.to_datetime(csv_frame["night_end_datetime"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    csv_frame.to_csv(csv_path, index=False, float_format="%.12g", lineterminator="\n")

    by_year = {}
    usable_days = set(frame["trading_day"])
    for year in range(2015, 2021):
        ev = events.loc[events["trading_day"].dt.year == year]
        n = int(len(ev)); u = int(ev["trading_day"].isin(usable_days).sum())
        by_year[str(year)] = {"events_total": n, "events_usable": u, "coverage": float(u / n) if n else None}
    manifest = {
        "schema_id": f"external_shfe_{product.lower()}_night_endpoints_2015_2020_manifest@1.0",
        "product": product,
        "source_repository": "Freddy-Hexas/china-futures-5min-2015-2025",
        "pinned_commit": core.PINNED_COMMIT,
        "pinned_tree": core.PINNED_TREE,
        "scope": "ordinary China target sessions only; holiday_reopen rows excluded before source extraction",
        "contract_selection": "previous-China-day 09:00-14:55 volume rank; ties nearest delivery then lexical; selection occurs before 15:00",
        "start": "selected contract exact 14:55 bar close",
        "end": "last positive-volume bar in frozen product night window beginning previous China trading date",
        "events_total": int(len(events)),
        "events_usable": int(len(frame)),
        "coverage": float(len(frame) / len(events)),
        "coverage_by_target_year": by_year,
        "unavailable_events": unavailable,
        "source_files_enumerated": int(len(sources)),
        "source_files": dict(sorted(source_meta.items())),
        "guards": {
            "CSI1000_gap_column_read": false,
            "post_2020_market_fields_parsed": 0,
            "future_full_day_volume_selection": false,
            "future_open_interest_selection": false,
            "contract_switch_after_missing_start_or_night": false,
            "zero_or_forward_fill_no_night": false,
            "raw_source_files_committed": false,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "product": product,
        "events_total": len(events),
        "events_usable": len(frame),
        "coverage": len(frame) / len(events),
        "source_files": len(sources),
        "unavailable": len(unavailable),
        "by_year": by_year,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
