#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/governance/opening_auction_csi1000_pit_membership_audit_preregistration.json"
OUT_CSV = ROOT / "data/external/csi1000_pit_membership_2015_2020.csv"
OUT_MANIFEST = ROOT / "docs/governance/opening_auction_csi1000_pit_membership_manifest.json"
API_ROOT = "https://www.dolthub.com/api/v1alpha1/chenditc/investment_data/master"
INDEX_CODE = "000852.SH"
START = date(2015, 1, 1)
END = date(2020, 12, 31)
CODE_RE = re.compile(r"^(\d{6})\.(SH|SZ|BJ)$")


def _api_query(sql: str, timeout: int = 45) -> dict[str, Any]:
    r = requests.get(API_ROOT, params={"q": sql}, timeout=timeout)
    r.raise_for_status()
    obj = r.json()
    if not isinstance(obj, dict):
        raise AssertionError("DoltHub response is not a JSON object")
    if "error" in obj and obj["error"]:
        raise RuntimeError(f"DoltHub SQL error: {obj['error']}")
    if "rows" not in obj or not isinstance(obj["rows"], list):
        raise AssertionError(f"DoltHub response missing rows: {sorted(obj)}")
    return obj


def _d(v: Any) -> date:
    s = str(v)[:10]
    return datetime.strptime(s, "%Y-%m-%d").date()


def _f(v: Any) -> float:
    if v is None or v == "":
        raise AssertionError("missing numeric value")
    return float(v)


def _i(v: Any) -> int:
    return int(v)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary_rows() -> list[dict[str, Any]]:
    sql = f"""
SELECT trade_date,
       COUNT(*) AS n,
       ROUND(SUM(weight), 10) AS weight_sum,
       MD5(GROUP_CONCAT(stock_code ORDER BY stock_code SEPARATOR ',')) AS membership_signature
FROM ts_index_weight
WHERE index_code = '{INDEX_CODE}'
  AND trade_date >= '{START.isoformat()}'
  AND trade_date <= '{END.isoformat()}'
GROUP BY trade_date
ORDER BY trade_date
""".strip()
    rows = _api_query(sql)["rows"]
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append({
            "trade_date": _d(r["trade_date"]),
            "n": _i(r["n"]),
            "weight_sum": _f(r["weight_sum"]),
            "membership_signature": str(r["membership_signature"]),
        })
    if not out:
        raise AssertionError("no bounded CSI1000 index_weight snapshots returned")
    return out


def _members(snapshot_date: date) -> list[dict[str, Any]]:
    sql = f"""
SELECT stock_code, weight
FROM ts_index_weight
WHERE index_code = '{INDEX_CODE}'
  AND trade_date = '{snapshot_date.isoformat()}'
ORDER BY stock_code
LIMIT 2000
""".strip()
    rows = _api_query(sql)["rows"]
    out = []
    seen: set[str] = set()
    for r in rows:
        code = str(r["stock_code"]).upper()
        if CODE_RE.fullmatch(code) is None:
            raise AssertionError(("malformed stock_code", snapshot_date.isoformat(), code))
        if code in seen:
            raise AssertionError(("duplicate stock within snapshot", snapshot_date.isoformat(), code))
        seen.add(code)
        out.append({"stock_code": code, "weight": _f(r["weight"])})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-write", action="store_true")
    args = ap.parse_args()

    prereg = json.loads(PREREG.read_text())
    if prereg["status"] != "result_free_before_public_DoltHub_membership_query":
        raise AssertionError("PIT membership audit preregistration status drift")
    if prereg.get("source_query_executed_before_latest_correction") is not False:
        raise AssertionError("result-free source-query guard drift")

    summary = _summary_rows()
    dates = [r["trade_date"] for r in summary]
    if dates != sorted(set(dates)):
        raise AssertionError("snapshot dates are not unique and sorted")
    if min(dates) < START or max(dates) > END:
        raise AssertionError("bounded source query leaked outside 2015-2020")

    count_bad = [r for r in summary if not (950 <= r["n"] <= 1050)]
    weight_bad = [r for r in summary if not (99.0 <= r["weight_sum"] <= 101.0)]
    earliest_ok = min(dates) <= date(2015, 5, 31)

    change_dates: list[date] = []
    last_sig: str | None = None
    for r in summary:
        if r["membership_signature"] != last_sig:
            change_dates.append(r["trade_date"])
            last_sig = r["membership_signature"]

    snapshots: dict[date, list[dict[str, Any]]] = {}
    for d0 in change_dates:
        m = _members(d0)
        expected = next(r["n"] for r in summary if r["trade_date"] == d0)
        if len(m) != expected:
            raise AssertionError(("snapshot row count mismatch", d0.isoformat(), len(m), expected))
        snapshots[d0] = m

    official_date = date(2020, 12, 14)
    official_row_exists = official_date in dates
    official_members = set(x["stock_code"] for x in _members(official_date)) if official_row_exists else set()
    required = set(prereg["official_crosschecks_frozen_before_query"][0]["required_new_member_examples"])
    official_missing = sorted(required - official_members)
    official_event_pass = bool(official_row_exists and not official_missing)

    # Materialize only membership intervals. Weights are recorded at the change snapshot
    # as audit metadata and are NOT authorized as daily historical weights.
    interval_rows: list[dict[str, Any]] = []
    for idx, d0 in enumerate(change_dates):
        end = END if idx == len(change_dates) - 1 else change_dates[idx + 1] - timedelta(days=1)
        for m in snapshots[d0]:
            interval_rows.append({
                "stock_code": m["stock_code"],
                "membership_start": d0.isoformat(),
                "membership_end": end.isoformat(),
                "source_weight_at_change_snapshot": f"{m['weight']:.10g}",
            })

    hard_pass = bool(earliest_ok and not count_bad and not weight_bad and official_event_pass)
    first_snapshot = min(dates)
    known_early_gap = first_snapshot > START
    max_gap = max((b - a).days for a, b in zip(dates, dates[1:])) if len(dates) > 1 else None
    exact_daily_like = bool(max_gap is not None and max_gap <= 7)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if not args.skip_write:
        with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["stock_code", "membership_start", "membership_end", "source_weight_at_change_snapshot"])
            w.writeheader()
            w.writerows(interval_rows)

    manifest = {
        "schema_id": "overnight_open_csi1000_pit_membership_manifest@1.0",
        "source": {
            "transport": "public DoltHub chenditc/investment_data",
            "api_root": API_ROOT,
            "table": "ts_index_weight",
            "index_code": INDEX_CODE,
            "upstream_claim": "Tushare index_weight via chenditc/investment_data",
        },
        "bounded_window": {"start": START.isoformat(), "end": END.isoformat(), "post_2020_rows": 0},
        "summary": {
            "snapshot_dates": len(summary),
            "first_snapshot": first_snapshot.isoformat(),
            "last_snapshot": max(dates).isoformat(),
            "membership_signature_changes": len(change_dates),
            "membership_interval_rows": len(interval_rows),
            "max_calendar_gap_between_source_snapshots_days": max_gap,
            "source_is_daily_like_under_7_day_gap_test": exact_daily_like,
            "known_uncovered_early_window": [START.isoformat(), (first_snapshot - timedelta(days=1)).isoformat()] if known_early_gap else None,
        },
        "health_gates": {
            "earliest_snapshot_no_later_than_2015_05_31": earliest_ok,
            "constituent_count_range_pass": not count_bad,
            "weight_sum_99_101_pass": not weight_bad,
            "count_bad_examples": [
                {"trade_date": r["trade_date"].isoformat(), "n": r["n"]} for r in count_bad[:10]
            ],
            "weight_bad_examples": [
                {"trade_date": r["trade_date"].isoformat(), "weight_sum": r["weight_sum"]} for r in weight_bad[:10]
            ],
        },
        "official_crosscheck": {
            "effective_date": official_date.isoformat(),
            "source_snapshot_exists_exactly_on_effective_date": official_row_exists,
            "required_19_STAR_members": sorted(required),
            "missing_required_members": official_missing,
            "pass": official_event_pass,
        },
        "adjudication": {
            "all_frozen_hard_gates_pass": hard_pass,
            "membership_transport_status": "retain_from_first_valid_snapshot_only" if hard_pass else "reject_or_block_exact_PIT_transport",
            "January_April_2015_backfill_allowed": False,
            "daily_weight_use_authorized": False,
            "predictive_model_authorized": False,
        },
        "authority": {"target_rows_read": 0, "post_2020_rows_read": 0, "production": False, "merge_main": False},
    }
    if not args.skip_write:
        manifest["assets"] = {
            str(OUT_CSV.relative_to(ROOT)): {"bytes": OUT_CSV.stat().st_size, "sha256": _sha(OUT_CSV)}
        }
        OUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    if not hard_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
