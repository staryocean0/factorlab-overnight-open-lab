#!/usr/bin/env python3
"""Build the frozen 2015-2020 three-index runtime text carrier for OFP-D1.

Data engineering only. This script does not evaluate D1 outcomes, regressions,
strategy returns, thresholds, or BLACKBOX data. It materializes exact-clock
CSI1000/CSI500/CSI300 rows from the admitted Unified DataHub 1m dataset and
checks CSI1000 gap/rvol20 parity against the already-open development carrier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

ADMITTED_VERSION = "bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
ADMITTED_DATASET_SHA256 = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
WARM_START = "2014-10-17"
DEV_START = "2015-01-05"
DEV_END = "2020-12-31"
YEARS = tuple(range(2015, 2021))
SYMBOLS = {
    "CSI1000": "000852.SH",
    "CSI500": "000905.SH",
    "CSI300": "000300.SH",
}
CLOCKS = ("09:31", "09:35", "09:50", "10:05", "10:35", "15:00")
PARITY_TOL = 1e-12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resolve_source(cli_source: str | None) -> Path:
    raw = cli_source or os.environ.get("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE")
    if not raw:
        raise RuntimeError("source missing: pass --source or set OVERNIGHT_HISTORICAL_INDEX_1M_LAKE")
    path = Path(raw)
    if ADMITTED_VERSION not in str(path):
        raise RuntimeError("source path does not bind the admitted Unified DataHub dataset version")
    if not path.exists():
        raise RuntimeError(f"source path does not exist: {path}")
    return path


def load_symbol(source: Path, name: str, symbol: str) -> pd.DataFrame:
    # Use the already-authoritative DataHub filtering pattern. No fallback may
    # load post-2020 rows into memory: a filter/type failure is an infrastructure
    # failure and must be repaired without weakening the evidence boundary.
    x = pd.read_parquet(
        source,
        filters=[
            ("symbol", "==", symbol),
            ("trading_day", ">=", WARM_START),
            ("trading_day", "<=", DEV_END),
        ],
        columns=["symbol", "trading_day", "timestamp", "open", "close"],
    ).copy()
    if x.empty:
        raise RuntimeError(f"no admitted rows for {name} {symbol}")
    x["trading_day"] = pd.to_datetime(x["trading_day"], errors="raise").dt.normalize()
    if x["trading_day"].max() > pd.Timestamp(DEV_END):
        raise RuntimeError(f"post-2020 row loaded for {name}")
    if x.duplicated(["trading_day", "timestamp"]).any():
        raise RuntimeError(f"duplicate timestamp rows for {name}")
    x["clock"] = x["timestamp"].astype(str).str.slice(11, 16)
    x = x.loc[x["clock"].isin(CLOCKS)].copy()
    x["open"] = pd.to_numeric(x["open"], errors="coerce")
    x["close"] = pd.to_numeric(x["close"], errors="coerce")

    closes = x.pivot(index="trading_day", columns="clock", values="close")
    for clock in CLOCKS:
        if clock not in closes.columns:
            closes[clock] = np.nan
    opens = (
        x.loc[x["clock"].eq("09:31"), ["trading_day", "open"]]
        .drop_duplicates("trading_day", keep="last")
        .set_index("trading_day")
        .rename(columns={"open": "open_0931"})
    )
    daily = closes.join(opens, how="outer").sort_index()
    daily = daily.rename(
        columns={
            "09:35": "close_0935",
            "09:50": "close_0950",
            "10:05": "close_1005",
            "10:35": "close_1035",
            "15:00": "close_1500",
        }
    )
    keep = ["open_0931", "close_0935", "close_0950", "close_1005", "close_1035", "close_1500"]
    for col in keep:
        if col not in daily.columns:
            daily[col] = np.nan
    daily = daily[keep]
    daily["prev_close_1500"] = daily["close_1500"].shift(1)
    daily_close_return = daily["close_1500"].pct_change(fill_method=None)
    daily["r1"] = daily_close_return.shift(1)
    daily["rvol20"] = daily_close_return.shift(1).rolling(20, min_periods=20).std()
    daily["gap"] = daily["open_0931"] / daily["prev_close_1500"] - 1.0
    daily["gap_rvol"] = daily["gap"] / daily["rvol20"]
    daily["required_clocks_complete"] = daily[keep].notna().all(axis=1)
    daily = daily.reset_index().rename(columns={"index": "trading_day"})
    daily.insert(0, "index_name", name)
    daily.insert(1, "symbol", symbol)
    daily = daily.loc[daily["trading_day"].between(pd.Timestamp(DEV_START), pd.Timestamp(DEV_END))].copy()
    daily["trading_day"] = daily["trading_day"].dt.strftime("%Y-%m-%d")
    return daily


def check_csi1000_reference_parity(carrier: pd.DataFrame, factor_root: Path) -> dict:
    refs = []
    for year in YEARS:
        path = factor_root / f"factor_panel_{year}.csv"
        if not path.exists():
            raise RuntimeError(f"missing CSI1000 reference carrier: {path}")
        x = pd.read_csv(path, usecols=["trading_day", "gap", "rvol20"])
        x["trading_day"] = x["trading_day"].astype(str)
        refs.append(x)
    ref = pd.concat(refs, ignore_index=True).sort_values("trading_day").reset_index(drop=True)
    c = carrier.loc[carrier["index_name"].eq("CSI1000"), ["trading_day", "gap", "rvol20", "required_clocks_complete"]].copy()
    c = c.sort_values("trading_day").reset_index(drop=True)
    if set(c["trading_day"]) != set(ref["trading_day"]):
        raise RuntimeError("CSI1000 trading-day inventory differs from admitted factor runtime carrier")
    m = ref.merge(c, on="trading_day", how="inner", suffixes=("_ref", "_carrier"), validate="one_to_one")
    report: dict[str, object] = {"trading_day_inventory_exact": True}
    for col in ("gap", "rvol20"):
        left = pd.to_numeric(m[f"{col}_ref"], errors="coerce")
        right = pd.to_numeric(m[f"{col}_carrier"], errors="coerce")
        comparable = left.notna() & right.notna()
        diff = (left[comparable] - right[comparable]).abs()
        max_abs = 0.0 if diff.empty else float(diff.max())
        mismatch = int((diff > PARITY_TOL).sum())
        if mismatch:
            raise RuntimeError(f"CSI1000 {col} parity failed: mismatch={mismatch} max_abs={max_abs}")
        report[col] = {
            "status": "PASS",
            "tolerance": PARITY_TOL,
            "comparable_rows": int(comparable.sum()),
            "reference_finite_carrier_missing_rows": int((left.notna() & right.isna()).sum()),
            "max_abs_diff_on_comparable_rows": max_abs,
        }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=None)
    ap.add_argument("--source-admission", type=Path, default=Path("docs/governance/relative_index_open_leadership_source_admission_20260912.json"))
    ap.add_argument("--protocol", type=Path, default=Path("docs/governance/relative_index_open_leadership_v1_protocol.json"))
    ap.add_argument("--csi1000-factor-runtime-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    source = resolve_source(args.source)
    admission = json.loads(args.source_admission.read_text(encoding="utf-8"))
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if admission.get("research_identity") != "overnight_relative_size_open_leadership_v1":
        raise RuntimeError("wrong D1 source admission")
    if protocol.get("research_identity") != "overnight_relative_size_open_leadership_v1":
        raise RuntimeError("wrong D1 protocol")
    if protocol.get("development_window") != f"{DEV_START}..{DEV_END}":
        raise RuntimeError("D1 development window drifted")
    if protocol.get("candidate_increment") != ["size_open_leadership"]:
        raise RuntimeError("D1 candidate identity drifted")
    if protocol.get("candidate_indices") != ["CSI1000", "CSI300"]:
        raise RuntimeError("D1 v1 candidate index pair drifted")
    if protocol.get("inventory_only_indices") != ["CSI500"]:
        raise RuntimeError("D1 CSI500 inventory-only role drifted")

    frames = [load_symbol(source, name, symbol) for name, symbol in SYMBOLS.items()]
    carrier = pd.concat(frames, ignore_index=True)
    if pd.to_datetime(carrier["trading_day"]).max() > pd.Timestamp(DEV_END):
        raise RuntimeError("post-2020 row entered D1 carrier")
    parity = check_csi1000_reference_parity(carrier, args.csi1000_factor_runtime_root)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    output_meta: dict[str, dict] = {}
    for year in YEARS:
        y = carrier.loc[pd.to_datetime(carrier["trading_day"]).dt.year.eq(year)].copy()
        y = y.sort_values(["trading_day", "index_name"], kind="mergesort")
        path = args.out_dir / f"relative_index_open_carrier_{year}.csv"
        y.to_csv(path, index=False, float_format="%.17g")
        output_meta[str(year)] = {
            "path": str(path),
            "sha256": sha256(path),
            "rows": int(len(y)),
            "min_day": None if y.empty else str(y["trading_day"].min()),
            "max_day": None if y.empty else str(y["trading_day"].max()),
            "bytes": path.stat().st_size,
            "symbols": sorted(y["symbol"].dropna().unique().tolist()),
        }

    manifest = {
        "schema_id": "overnight_relative_index_runtime_text_2015_2020@1.0",
        "session_date": "2026-09-12",
        "purpose": "connector_readable_three_index_exact_clock_carrier_for_D1_open_development_only",
        "source_dataset_version": ADMITTED_VERSION,
        "source_dataset_admitted_sha256": ADMITTED_DATASET_SHA256,
        "source_path": str(source),
        "published_window": f"{DEV_START}..{DEV_END}",
        "warmup_start": WARM_START,
        "withheld_years": [2021, 2022, 2023, 2024, 2025],
        "indices": SYMBOLS,
        "D1_v1_candidate_indices": ["CSI1000", "CSI300"],
        "CSI500_role": "carrier_inventory_only_not_candidate",
        "exact_clocks": list(CLOCKS),
        "columns": carrier.columns.tolist(),
        "outputs": output_meta,
        "transform": {
            "scientific_change": False,
            "outcome_analysis": False,
            "exact_clock_only": True,
            "nearest_clock_substitution": False,
            "forward_fill": False,
            "backward_fill": False,
            "resampling": False,
            "2021_2025_row_level_text_generated": False,
        },
        "csi1000_reference_parity": parity,
        "production_authority": False,
    }
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme = """# Relative-index runtime text carrier (2015-2020)\n\nDeterministic connector-readable carrier for CSI1000, CSI500 and CSI300 exact\nopening clocks. It is data engineering only. D1 v1 uses CSI1000 versus CSI300;\nCSI500 is inventory-only. No 2021-2025 text rows are materialized.\n\nPhysical accessibility is not scientific authority. The D1 protocol governs all\noutcome use; this pack does not itself validate a factor or trading strategy.\n"""
    (args.out_dir / "README.md").write_text(readme, encoding="utf-8")

    receipt = {
        "schema_id": "overnight_relative_index_runtime_text_carrier_receipt@1.0",
        "session_date": "2026-09-12",
        "research_identity": "overnight_relative_size_open_leadership_v1",
        "published_window": f"{DEV_START}..{DEV_END}",
        "source_dataset_version": ADMITTED_VERSION,
        "source_dataset_admitted_sha256": ADMITTED_DATASET_SHA256,
        "source_admission": {"path": str(args.source_admission), "sha256": sha256(args.source_admission)},
        "protocol": {"path": str(args.protocol), "sha256": sha256(args.protocol)},
        "output_manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
        "csi1000_reference_parity": parity,
        "exact_clock_only": True,
        "target_rows_after_2020_loaded": False,
        "2021_2025_text_shards_generated": False,
        "2021_2025_blackbox_opened": False,
        "D1_outcome_diagnostic_performed": False,
        "candidate_family_search": False,
        "CSI500_candidate_search": False,
        "P2_rescue_performed": False,
        "scientific_change": False,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("RELATIVE_INDEX_RUNTIME_TEXT_CARRIER_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
