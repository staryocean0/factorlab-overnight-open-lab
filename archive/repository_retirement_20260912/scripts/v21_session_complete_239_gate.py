#!/usr/bin/env python3
"""V21 future-source session-completeness gate.

This module supersedes the historical ``exact_240`` source-admission assumption
for future V21 CSI300/CSI500 minute data only.  It does NOT rewrite the frozen
RD1 runner or any already-consumed evidence.

The admitted source contract is deliberately narrow:

* old target clock set = 09:31..11:30 + 13:01..15:00 (240 labels);
* 14:59 is structurally optional for the admitted session-complete source;
* every other one of the 239 labels is required;
* 14:59 may be present, but it is never synthesized;
* any other missing clock, duplicate clock, or unexpected row in the target
  session fails closed.

In particular, this is NOT a generic ``len(day) >= 239`` rule.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

SYSTEMATIC_OPTIONAL_CLOCK = "14:59"
EXPECTED_PACKAGE_RELATIVE_PATH = (
    "data/v21_future_audit_csi_index_1m_session_complete_2019_2024/"
    "csi300_csi500_1m.parquet"
)
EXPECTED_PACKAGE_SHA256 = "3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c"
PARENT_HE00_V8_SHA256 = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
SYMBOLS = ("000300.SH", "000905.SH")


def _minute_labels(start: str, end: str) -> list[str]:
    cur = datetime.strptime(start, "%H:%M")
    stop = datetime.strptime(end, "%H:%M")
    out: list[str] = []
    while cur <= stop:
        out.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=1)
    return out


def legacy_expected_240_clocks() -> tuple[str, ...]:
    return tuple(_minute_labels("09:31", "11:30") + _minute_labels("13:01", "15:00"))


def required_session_complete_239_clocks() -> tuple[str, ...]:
    return tuple(c for c in legacy_expected_240_clocks() if c != SYSTEMATIC_OPTIONAL_CLOCK)


def _clock(value: object) -> str:
    s = str(value)
    # Accept a bare HH:MM[/HH:MM:SS] or the repository's ISO-like timestamps.
    if len(s) >= 16 and s[4:5] == "-" and s[7:8] == "-":
        return s[11:16]
    if len(s) >= 5 and s[2:3] == ":":
        return s[:5]
    raise ValueError(f"cannot extract HH:MM from timestamp: {s!r}")


@dataclass(frozen=True)
class SessionGateResult:
    accepted: bool
    observed_rows: int
    unique_clocks: int
    required_clock_count: int
    optional_1459_present: bool
    missing_required_clocks: tuple[str, ...]
    duplicate_clocks: tuple[str, ...]
    unexpected_clocks: tuple[str, ...]
    reason: str


def evaluate_session_complete_239(timestamps: Iterable[object]) -> SessionGateResult:
    """Evaluate one trading day's timestamp labels under the frozen 239 gate."""
    clocks = [_clock(x) for x in timestamps]
    counts = Counter(clocks)
    present = set(clocks)
    required = set(required_session_complete_239_clocks())
    allowed = set(legacy_expected_240_clocks())

    missing = tuple(sorted(required - present))
    duplicate = tuple(sorted(c for c, n in counts.items() if n != 1))
    unexpected = tuple(sorted(present - allowed))
    optional = SYSTEMATIC_OPTIONAL_CLOCK in present

    accepted = not missing and not duplicate and not unexpected
    if missing:
        reason = "missing_required_session_clock"
    elif duplicate:
        reason = "duplicate_session_clock"
    elif unexpected:
        reason = "unexpected_target_session_clock"
    else:
        reason = "session_complete_239_required"

    return SessionGateResult(
        accepted=accepted,
        observed_rows=len(clocks),
        unique_clocks=len(present),
        required_clock_count=len(required),
        optional_1459_present=optional,
        missing_required_clocks=missing,
        duplicate_clocks=duplicate,
        unexpected_clocks=unexpected,
        reason=reason,
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def audit_parquet_metadata_only(path: Path, *, expected_sha256: str | None = None) -> dict:
    """Audit symbol/day/timestamp coverage only; never read OHLC or outcomes."""
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - CLI dependency only
        raise RuntimeError("pandas/pyarrow are required for parquet auditing") from exc

    actual_sha = sha256(path)
    if expected_sha256 and actual_sha != expected_sha256:
        raise RuntimeError(f"source SHA mismatch: {actual_sha} != {expected_sha256}")

    frame = pd.read_parquet(path, columns=["symbol", "trading_day", "timestamp"])
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    if set(frame["symbol"]) - set(SYMBOLS):
        raise RuntimeError("unexpected symbol in V21 audit source")

    by_symbol: dict[str, dict] = {}
    for symbol in SYMBOLS:
        part = frame.loc[frame["symbol"].eq(symbol)].copy()
        complete = 0
        incomplete = 0
        missing_required_rows = 0
        reasons: Counter[str] = Counter()
        for _, day in part.groupby("trading_day", sort=True):
            result = evaluate_session_complete_239(day["timestamp"].tolist())
            reasons[result.reason] += 1
            if result.accepted:
                complete += 1
            else:
                incomplete += 1
                missing_required_rows += len(result.missing_required_clocks)
        by_symbol[symbol] = {
            "observed_trading_days": int(part["trading_day"].nunique()),
            "session_complete_days": complete,
            "incomplete_days": incomplete,
            "missing_required_clock_rows": missing_required_rows,
            "reason_counts": dict(sorted(reasons.items())),
        }

    return {
        "schema_id": "v21_session_complete_239_metadata_audit@1.0",
        "source_path": str(path),
        "source_sha256": actual_sha,
        "parent_he00_v8_sha256": PARENT_HE00_V8_SHA256,
        "rows": int(len(frame)),
        "gate": {
            "legacy_expected_clock_count": len(legacy_expected_240_clocks()),
            "required_clock_count": len(required_session_complete_239_clocks()),
            "systematic_optional_clock": SYSTEMATIC_OPTIONAL_CLOCK,
            "generic_len_239_rule": False,
            "imputation_allowed": False,
        },
        "by_symbol": by_symbol,
        "OHLC_read": False,
        "outcome_read": False,
    }


def _self_test() -> None:
    required = list(required_session_complete_239_clocks())
    assert len(legacy_expected_240_clocks()) == 240
    assert len(required) == 239
    assert SYSTEMATIC_OPTIONAL_CLOCK not in required
    assert evaluate_session_complete_239(required).accepted
    assert evaluate_session_complete_239(required + [SYSTEMATIC_OPTIONAL_CLOCK]).accepted
    assert not evaluate_session_complete_239([c for c in required if c != "13:22"]).accepted
    assert not evaluate_session_complete_239([c for c in required if c != "10:39"] + [SYSTEMATIC_OPTIONAL_CLOCK]).accepted
    assert not evaluate_session_complete_239(required + [required[0]]).accepted
    assert not evaluate_session_complete_239(required + ["09:30"]).accepted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parquet", type=Path)
    parser.add_argument("--expected-sha256", default=EXPECTED_PACKAGE_SHA256)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("V21_SESSION_COMPLETE_239_SELF_TEST passed")
        if not args.parquet:
            return 0
    if not args.parquet:
        parser.error("--parquet is required unless only --self-test is used")

    payload = audit_parquet_metadata_only(args.parquet, expected_sha256=args.expected_sha256)
    raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
