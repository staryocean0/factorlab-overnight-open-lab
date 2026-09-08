#!/usr/bin/env python3
"""Metadata-only admission for the future R1 2026Q4 source.

This runner is intentionally incapable of reading OHLC or constructing R1
outcomes.  It may run only after the complete 2026 calendar year extension
exists (not before 2027-01-01 Asia/Shanghai), and it verifies an authoritative
trading calendar plus exact named 240-clock A-share sessions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

SYMBOL = "000852.SH"
CONTEXT_START = "2026-01-05"
CONTEXT_END = "2026-12-31"
CHALLENGE_START = "2026-10-01"
CHALLENGE_END = "2026-12-31"
EARLIEST_ADMISSION_DATE = date(2027, 1, 1)
METADATA_COLUMNS = ["symbol", "trading_day", "timestamp"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def expected_clocks() -> tuple[str, ...]:
    morning = pd.date_range("2000-01-01 09:31", "2000-01-01 11:30", freq="1min")
    afternoon = pd.date_range("2000-01-01 13:01", "2000-01-01 15:00", freq="1min")
    clocks = tuple(x.strftime("%H:%M") for x in [*morning, *afternoon])
    if len(clocks) != 240 or len(set(clocks)) != 240:
        raise RuntimeError("internal 240-clock construction failed")
    return clocks


def validate_execution_date(as_of: date) -> None:
    if as_of < EARLIEST_ADMISSION_DATE:
        raise RuntimeError(
            f"complete-2026 source admission is sealed until {EARLIEST_ADMISSION_DATE.isoformat()} Asia/Shanghai"
        )


def read_calendar(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path, usecols=["trading_day"])
        values = frame["trading_day"].astype(str).tolist()
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(path, columns=["trading_day"])
        values = frame["trading_day"].astype(str).tolist()
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("trading_days"), list):
            values = [str(x) for x in payload["trading_days"]]
        elif isinstance(payload, list):
            if all(isinstance(x, str) for x in payload):
                values = [str(x) for x in payload]
            elif all(isinstance(x, dict) and "trading_day" in x for x in payload):
                values = [str(x["trading_day"]) for x in payload]
            else:
                raise RuntimeError("unsupported JSON calendar format")
        else:
            raise RuntimeError("unsupported JSON calendar format")
    else:
        raise RuntimeError("calendar must be .csv, .parquet/.pq, or .json")

    selected = sorted({d for d in values if CONTEXT_START <= d <= CONTEXT_END})
    if not selected:
        raise RuntimeError("calendar contains no 2026 context-extension trading days")
    if selected[0] != CONTEXT_START:
        raise RuntimeError(f"calendar first required trading day drifted: {selected[0]}")
    if not any(CHALLENGE_START <= d <= CHALLENGE_END for d in selected):
        raise RuntimeError("calendar contains no Q4 challenge trading days")
    return selected


def read_source_metadata(path: Path) -> pd.DataFrame:
    # Only metadata columns are requested.  OHLC columns are never named here.
    frame = pd.read_parquet(
        path,
        columns=METADATA_COLUMNS,
        filters=[("symbol", "==", SYMBOL), ("trading_day", ">=", CONTEXT_START)],
    )
    if frame.empty:
        raise RuntimeError("future source contains no authorized-symbol 2026 metadata")
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["timestamp"] = frame["timestamp"].astype(str)
    if set(frame["symbol"].unique()) != {SYMBOL}:
        raise RuntimeError("symbol filter/identity drifted")
    if str(frame["trading_day"].max()) > CONTEXT_END:
        raise RuntimeError("source includes post-2026-12-31 authorized-symbol rows")
    if str(frame["trading_day"].min()) != CONTEXT_START:
        raise RuntimeError(f"source first context day drifted: {frame['trading_day'].min()}")
    frame["timestamp_day"] = frame["timestamp"].str.slice(0, 10)
    frame["clock"] = frame["timestamp"].str.slice(11, 16)
    if not frame["timestamp_day"].eq(frame["trading_day"]).all():
        raise RuntimeError("timestamp calendar date does not equal trading_day")
    return frame[["symbol", "trading_day", "timestamp", "clock"]].copy()


def audit(frame: pd.DataFrame, expected_days: list[str]) -> dict:
    clocks = expected_clocks()
    expected_clock_set = set(clocks)
    observed_days = sorted(frame["trading_day"].unique().tolist())
    expected_day_set = set(expected_days)
    observed_day_set = set(observed_days)
    missing_days = sorted(expected_day_set - observed_day_set)
    unexpected_days = sorted(observed_day_set - expected_day_set)

    duplicate_mask = frame.duplicated(["trading_day", "clock"], keep=False)
    duplicate_rows = int(duplicate_mask.sum())
    complete_days: list[str] = []
    incomplete: dict[str, dict] = {}
    for day in observed_days:
        day_frame = frame.loc[frame["trading_day"].eq(day)]
        day_clocks = day_frame["clock"].tolist()
        day_set = set(day_clocks)
        missing = sorted(expected_clock_set - day_set)
        unexpected = sorted(day_set - expected_clock_set)
        duplicate_clock_count = int(day_frame.duplicated(["clock"], keep=False).sum())
        exact = (
            len(day_frame) == 240
            and len(day_set) == 240
            and not missing
            and not unexpected
            and duplicate_clock_count == 0
        )
        if exact:
            complete_days.append(day)
        else:
            incomplete[day] = {
                "rows": int(len(day_frame)),
                "unique_clocks": int(len(day_set)),
                "missing_clocks": missing,
                "unexpected_clocks": unexpected,
                "duplicate_clock_rows": duplicate_clock_count,
            }

    passed = (
        not missing_days
        and not unexpected_days
        and not incomplete
        and duplicate_rows == 0
        and observed_days == expected_days
    )
    return {
        "passed": bool(passed),
        "observed_trading_days": len(observed_days),
        "expected_trading_days": len(expected_days),
        "complete_trading_days": len(complete_days),
        "incomplete_trading_days": len(incomplete),
        "missing_expected_days": missing_days,
        "unexpected_days": unexpected_days,
        "duplicate_metadata_rows": duplicate_rows,
        "incomplete_day_details": incomplete,
        "total_metadata_rows": int(len(frame)),
        "expected_named_clocks_per_day": 240,
        "named_clock_gate_passed": bool(not incomplete and duplicate_rows == 0),
        "Q4_calendar_days": int(sum(CHALLENGE_START <= d <= CHALLENGE_END for d in expected_days)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    china_now = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    validate_execution_date(china_now)

    source_digest = sha256(args.source)
    calendar_digest = sha256(args.calendar)
    expected_days = read_calendar(args.calendar)
    frame = read_source_metadata(args.source)
    result = audit(frame, expected_days)

    receipt = {
        "schema_id": "factorlab_rmr_R1_true_fresh_2026Q4_source_admission_receipt@1.0",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "stage": "metadata_only_source_admission",
        "admission_date_China": china_now.isoformat(),
        "source_identity": str(args.source),
        "source_sha256": source_digest,
        "calendar_identity": str(args.calendar),
        "calendar_sha256": calendar_digest,
        "context_window": {"start": CONTEXT_START, "end": CONTEXT_END},
        "challenge_window": {"start": CHALLENGE_START, "end": CHALLENGE_END},
        "OHLC_read": False,
        "outcome_read": False,
        "R1_events_constructed": False,
        "challenge_outcomes_opened": False,
        "V21_239_clock_exception_used": False,
        **result,
        "Q4_outcome_execution_authorized": False,
        "cloud_review_required": True,
        "production_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise RuntimeError("future source admission failed closed; inspect compact receipt")
    print("R1_TRUE_FRESH_Q4_SOURCE_ADMISSION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
