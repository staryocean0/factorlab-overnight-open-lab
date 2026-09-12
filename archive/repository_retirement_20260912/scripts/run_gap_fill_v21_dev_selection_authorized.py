#!/usr/bin/env python3
"""Authorized entry point for the V21 DEV selection runner.

The HE-00 v8 parent lake may contain indices beyond CSI300/CSI500. This thin
entry point narrows metadata preflight to the two explicitly authorized symbols
and the frozen 2015-2018 window before delegating to the frozen V21 DEV engine.
It does not change any model, target, candidate, metric, or selection semantics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_gap_fill_v21_dev_selection as engine


def read_authorized_metadata(source: Path) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for symbol in engine.SYMBOLS.values():
        part = pd.read_parquet(
            source,
            filters=[
                ("symbol", "==", symbol),
                ("trading_day", ">=", engine.DEV_START),
                ("trading_day", "<=", engine.DEV_END),
            ],
            columns=["symbol", "trading_day", "timestamp"],
        )
        if part.empty:
            raise RuntimeError(f"V21 DEV source metadata missing authorized symbol {symbol}")
        parts.append(part)
    frame = pd.concat(parts, ignore_index=True)
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    if set(frame["symbol"]) != set(engine.SYMBOLS.values()):
        raise RuntimeError("authorized metadata filter returned an unexpected symbol inventory")
    if frame["trading_day"].min() < engine.DEV_START or frame["trading_day"].max() > engine.DEV_END:
        raise RuntimeError("authorized metadata filter crossed frozen V21 DEV window")
    return frame.sort_values(["symbol", "trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def main() -> int:
    engine.read_metadata = read_authorized_metadata
    return engine.main()


if __name__ == "__main__":
    raise SystemExit(main())
