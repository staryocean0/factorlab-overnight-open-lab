#!/usr/bin/env python3
"""Metadata-only controller for V21 source verification -> DEV admission.

This script intentionally stops BEFORE any V21_DEV OHLC/outcome/model access.
It reads only symbol/trading_day/timestamp from market data.  Its two outputs are
compact receipts for cloud review:

1) verify the frozen 2019-2024 audit package identity and named-clock gate;
2) inventory the frozen 2015-2018 DEV source under the same gate.

A successful local run is necessary but not sufficient to open DEV outcomes.
Cloud must review both receipts and explicitly update repository state first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import v21_session_complete_239_gate as gate

PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_source_to_dev_metadata_controller_v1.json"
DEFAULT_AUDIT = ROOT / "data/v21_future_audit_csi_index_1m_session_complete_2019_2024/csi300_csi500_1m.parquet"
DEFAULT_SOURCE_RECEIPT = ROOT / "docs/research/local_gap_fill_v21_future_audit_source_admission_receipt_v1.json"
DEFAULT_DEV_RECEIPT = ROOT / "docs/research/local_gap_fill_v21_dev_metadata_admission_receipt_v1.json"
SYMBOLS = ("000300.SH", "000905.SH")
DEV_START = "2015-01-01"
DEV_END = "2018-12-31"
EXPECTED_AUDIT_SHA = "3088ff2119ccffce3ff2fb8468a497775bcf64bc78df01008c85390ccd27777c"
EXPECTED_PARENT_SHA = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
EXPECTED_AUDIT_ROWS = 695_929
EXPECTED_MISSING_REQUIRED_ROWS = 39
EXPECTED_COVERAGE = {
    "000300.SH": {"observed_trading_days": 1456, "session_complete_days": 1449, "incomplete_days": 7},
    "000905.SH": {"observed_trading_days": 1456, "session_complete_days": 1448, "incomplete_days": 8},
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def command_string() -> str:
    return " ".join(sys.argv)


def read_metadata(path: Path, *, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Read only the three explicitly authorized metadata columns."""
    frame = pd.read_parquet(path, columns=["symbol", "trading_day", "timestamp"])
    if frame.empty:
        raise RuntimeError(f"metadata source is empty: {path}")
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    if start is not None:
        frame = frame.loc[frame["trading_day"] >= start].copy()
    if end is not None:
        frame = frame.loc[frame["trading_day"] <= end].copy()
    if frame.empty:
        raise RuntimeError(f"metadata source has no rows in requested window: {path}")
    unexpected = sorted(set(frame["symbol"]) - set(SYMBOLS))
    if unexpected:
        raise RuntimeError(f"unexpected symbols in V21 metadata source: {unexpected}")
    return frame.sort_values(["symbol", "trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def audit_frame(frame: pd.DataFrame) -> dict:
    by_symbol: dict[str, dict] = {}
    total_missing = 0
    total_optional = 0
    for symbol in SYMBOLS:
        part = frame.loc[frame["symbol"].eq(symbol)].copy()
        if part.empty:
            raise RuntimeError(f"missing required symbol {symbol}")
        complete = 0
        incomplete = 0
        reasons: Counter[str] = Counter()
        incomplete_days: list[dict] = []
        optional_days = 0
        for trading_day, day in part.groupby("trading_day", sort=True):
            result = gate.evaluate_session_complete_239(day["timestamp"].tolist())
            reasons[result.reason] += 1
            if result.optional_1459_present:
                optional_days += 1
            if result.accepted:
                complete += 1
            else:
                incomplete += 1
                total_missing += len(result.missing_required_clocks)
                incomplete_days.append({
                    "trading_day": str(trading_day),
                    "reason": result.reason,
                    "observed_rows": result.observed_rows,
                    "missing_required_clocks": list(result.missing_required_clocks),
                    "duplicate_clocks": list(result.duplicate_clocks),
                    "unexpected_clocks": list(result.unexpected_clocks),
                    "optional_1459_present": result.optional_1459_present,
                })
        total_optional += optional_days
        by_symbol[symbol] = {
            "observed_trading_days": int(part["trading_day"].nunique()),
            "min_day": str(part["trading_day"].min()),
            "max_day": str(part["trading_day"].max()),
            "session_complete_days": int(complete),
            "incomplete_days": int(incomplete),
            "optional_1459_present_days": int(optional_days),
            "reason_counts": dict(sorted(reasons.items())),
            "incomplete_day_details": incomplete_days,
        }
    return {
        "rows": int(len(frame)),
        "by_symbol": by_symbol,
        "total_missing_required_clock_rows": int(total_missing),
        "total_optional_1459_present_days": int(total_optional),
        "gate": {
            "gate_id": "session_complete_239_required_v1",
            "legacy_clock_count": len(gate.legacy_expected_240_clocks()),
            "required_clock_count": len(gate.required_session_complete_239_clocks()),
            "systematic_optional_clock": gate.SYSTEMATIC_OPTIONAL_CLOCK,
            "generic_len_239_rule": False,
            "imputation_allowed": False,
        },
    }


def verify_audit_package(audit_path: Path, parent_source_sha256: str) -> dict:
    if not audit_path.exists() or not audit_path.is_file():
        raise RuntimeError(f"audit package not found: {audit_path}")
    actual_sha = gate.sha256(audit_path)
    if actual_sha != EXPECTED_AUDIT_SHA:
        raise RuntimeError(f"audit package SHA mismatch: {actual_sha} != {EXPECTED_AUDIT_SHA}")
    if parent_source_sha256 != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"parent HE-00 v8 identity mismatch: {parent_source_sha256} != {EXPECTED_PARENT_SHA}")
    frame = read_metadata(audit_path)
    audit = audit_frame(frame)
    if audit["rows"] != EXPECTED_AUDIT_ROWS:
        raise RuntimeError(f"audit package row-count mismatch: {audit['rows']} != {EXPECTED_AUDIT_ROWS}")
    for symbol, expected in EXPECTED_COVERAGE.items():
        got = audit["by_symbol"][symbol]
        for key, value in expected.items():
            if got[key] != value:
                raise RuntimeError(f"audit coverage mismatch {symbol} {key}: {got[key]} != {value}")
    if audit["total_missing_required_clock_rows"] != EXPECTED_MISSING_REQUIRED_ROWS:
        raise RuntimeError(
            "audit missing-required-clock total mismatch: "
            f"{audit['total_missing_required_clock_rows']} != {EXPECTED_MISSING_REQUIRED_ROWS}"
        )
    return {
        "schema_id": "overnight_open_gap_fill_v21_future_audit_source_admission_receipt@1.0",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "stage": "local_source_verification_complete_pending_cloud_review",
        "code_commit": git_head(),
        "command": command_string(),
        "controller_sha256": sha256(Path(__file__)),
        "gate_module_sha256": sha256(ROOT / "scripts/v21_session_complete_239_gate.py"),
        "audit_package_path": str(audit_path),
        "audit_package_sha256": actual_sha,
        "parent_he00_v8_sha256": parent_source_sha256,
        "metadata_audit": audit,
        "acceptance": {
            "audit_package_sha_matches": True,
            "audit_package_row_count_matches": True,
            "parent_source_identity_matches": True,
            "reported_per_symbol_coverage_matches": True,
            "reported_missing_required_rows_total_matches": True,
            "no_middle_clock_imputation": True,
            "passed": True,
        },
        "columns_read": ["symbol", "trading_day", "timestamp"],
        "OHLC_read": False,
        "outcome_read": False,
        "imputation_performed": False,
        "V21_DEV_outcomes_opened": False,
        "successor_model_fit_performed": False,
        "successor_model_selection_performed": False,
        "production_authority": False,
    }


def audit_dev_metadata(dev_source: Path, parent_source_sha256: str) -> dict:
    if not dev_source.exists():
        raise RuntimeError(f"DEV metadata source not found: {dev_source}")
    if parent_source_sha256 != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"DEV parent source identity mismatch: {parent_source_sha256} != {EXPECTED_PARENT_SHA}")
    frame = read_metadata(dev_source, start=DEV_START, end=DEV_END)
    audit = audit_frame(frame)
    for symbol in SYMBOLS:
        info = audit["by_symbol"][symbol]
        if info["min_day"] < DEV_START or info["max_day"] > DEV_END:
            raise RuntimeError(f"DEV metadata boundary drift for {symbol}")
        if info["observed_trading_days"] <= 0 or info["session_complete_days"] <= 0:
            raise RuntimeError(f"DEV metadata has no usable complete day for {symbol}")
    return {
        "schema_id": "overnight_open_gap_fill_v21_dev_metadata_admission_receipt@1.0",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "stage": "local_DEV_metadata_inventory_complete_pending_cloud_review",
        "code_commit": git_head(),
        "command": command_string(),
        "controller_sha256": sha256(Path(__file__)),
        "gate_module_sha256": sha256(ROOT / "scripts/v21_session_complete_239_gate.py"),
        "dev_source_path": str(dev_source),
        "parent_he00_v8_sha256": parent_source_sha256,
        "frozen_window": {"start": DEV_START, "end": DEV_END},
        "metadata_audit": audit,
        "acceptance": {
            "same_named_239_gate": True,
            "both_symbols_present": True,
            "frozen_window_only": True,
            "all_rejections_reported_fail_closed": True,
            "no_imputation": True,
            "metadata_inventory_complete": True,
            "passed": True,
        },
        "columns_read": ["symbol", "trading_day", "timestamp"],
        "OHLC_read": False,
        "outcome_read": False,
        "imputation_performed": False,
        "V21_DEV_outcomes_opened": False,
        "successor_model_fit_performed": False,
        "successor_model_selection_performed": False,
        "production_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-parquet", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--dev-source", type=Path, required=True)
    parser.add_argument("--parent-source-sha256", required=True)
    parser.add_argument("--source-receipt-out", type=Path, default=DEFAULT_SOURCE_RECEIPT)
    parser.add_argument("--dev-receipt-out", type=Path, default=DEFAULT_DEV_RECEIPT)
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["hard_stop_after_outputs"] is not True:
        raise RuntimeError("metadata controller protocol unexpectedly authorizes continuation")
    if protocol["V21_DEV_outcomes_open_authorized"] is not False:
        raise RuntimeError("metadata controller protocol unexpectedly opens DEV")
    if args.parent_source_sha256 != protocol["audit_package"]["expected_parent_he00_v8_sha256"]:
        raise RuntimeError("parent source identity does not match frozen controller protocol")

    source_receipt = verify_audit_package(args.audit_parquet.resolve(), args.parent_source_sha256)
    dump_json(args.source_receipt_out.resolve(), source_receipt)

    # Only after source verification passed do we scan the frozen DEV metadata.
    dev_receipt = audit_dev_metadata(args.dev_source.resolve(), args.parent_source_sha256)
    dump_json(args.dev_receipt_out.resolve(), dev_receipt)

    print("V21_SOURCE_TO_DEV_METADATA_RESULT", json.dumps({
        "source_verification_passed": True,
        "dev_metadata_inventory_passed": True,
        "source_receipt": str(args.source_receipt_out),
        "dev_receipt": str(args.dev_receipt_out),
        "V21_DEV_outcomes_opened": False,
        "hard_stop_before_DEV_outcomes": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
