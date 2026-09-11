#!/usr/bin/env python3
"""Build a connector-readable runtime text carrier from frozen parquet.

This is a deterministic data-engineering transform only:

* row filter by year
* column filter of already-materialized frozen development features
* exact-clock pivot of already-stored one-minute closes
* CSV serialization

It does not recompute features, forward/back fill, resample, nearest-match
clocks, or inspect 2021-2025 BLACKBOX outcomes. Physical text accessibility
does not grant evidence authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ID = "overnight_runtime_text_carrier@1.0"
INSTRUMENT = "000852.SH"
DEFAULT_START_YEAR = 2015
DEFAULT_END_YEAR = 2025
BLACKBOX_START_YEAR = 2021
PARITY_START = "2015-01-05"
PARITY_END = "2020-12-31"
CLOCK_DEV_START = "2019-01-01"
CLOCK_DEV_END = "2020-12-31"
TIMESTAMP_PREFIX_RE = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:"
FLOAT_FORMAT = "%.17g"
CSV_ABS_FLOOR = 2e-15
CSV_ULP_MULT = 2.0

CLOCKS = ["09:35", "09:50", "10:05", "10:35"]
CLOCK_COLUMNS = {
    "09:35": "close_0935",
    "09:50": "close_0950",
    "10:05": "close_1005",
    "10:35": "close_1035",
}
FACTOR_PANEL_COLUMNS = [
    "trading_day",
    "gap",
    "r1",
    "r20",
    "rvol20",
    "prev_daytime",
    "prev_last_hour",
    "prev_afternoon",
    "holiday_reopen",
    "weekend",
    "prev_gap",
    "overnight_trend_5",
    "abs_r1",
    "us_nasdaq",
    "us_vix_chg",
]
TRANSFORM_FLAGS = {
    "scientific_change": False,
    "row_filter_only": True,
    "column_filter_only": True,
    "exact_clock_filter_only": True,
    "forward_fill": False,
    "backward_fill": False,
    "resampling": False,
    "feature_engineering": False,
    "nearest_clock_match": False,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def normalize_trading_day(series: pd.Series) -> pd.Series:
    days = pd.to_datetime(series, errors="raise").dt.strftime("%Y-%m-%d")
    if days.isna().any():
        raise RuntimeError("trading_day normalization produced nulls")
    return days


def assert_one_row_per_day(frame: pd.DataFrame, label: str) -> None:
    days = frame["trading_day"].astype(str)
    if days.duplicated().any():
        raise RuntimeError(f"{label} is not one row per trading_day")
    if days.nunique() != len(frame):
        raise RuntimeError(f"{label} trading_day inventory is not unique")


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format=FLOAT_FORMAT)


def file_stats(path: Path, frame: pd.DataFrame, source_sha256: str) -> dict:
    days = frame["trading_day"].astype(str)
    return {
        "path": repo_path(path),
        "sha256": sha256_file(path),
        "row_count": int(len(frame)),
        "min_day": str(days.min()),
        "max_day": str(days.max()),
        "bytes": int(path.stat().st_size),
        "source_parquet_sha256": source_sha256,
    }


def load_frozen_factor_panel(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    missing = [col for col in FACTOR_PANEL_COLUMNS if col not in frame.columns]
    if missing:
        raise RuntimeError(f"frozen panel missing required carrier columns: {missing}")
    out = frame.loc[:, FACTOR_PANEL_COLUMNS].copy()
    out["trading_day"] = normalize_trading_day(out["trading_day"])
    out = out.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    assert_one_row_per_day(out, "frozen factor panel")
    return out


def load_annotated_days(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path, columns=["symbol", "trading_day"])
    frame = frame.loc[frame["symbol"].astype(str) == INSTRUMENT, ["trading_day"]].copy()
    frame["trading_day"] = normalize_trading_day(frame["trading_day"])
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    assert_one_row_per_day(frame, "annotated_panel")
    return frame


def extract_exact_clocks(path: Path, days: pd.Series) -> pd.DataFrame:
    bars = pd.read_parquet(path, columns=["symbol", "trading_day", "timestamp", "close"])
    bars = bars.loc[bars["symbol"].astype(str) == INSTRUMENT].copy()
    if bars.empty:
        raise RuntimeError(f"minute bars contain no rows for {INSTRUMENT}")
    bars["trading_day"] = normalize_trading_day(bars["trading_day"])
    timestamps = bars["timestamp"].astype(str)
    if not timestamps.str.match(TIMESTAMP_PREFIX_RE).all():
        raise RuntimeError("unexpected minute timestamp format; refusing implicit clock inference")
    bars["clock"] = timestamps.str.slice(11, 16)
    exact = bars.loc[bars["clock"].isin(CLOCKS), ["trading_day", "clock", "close"]].copy()
    if exact.duplicated(["trading_day", "clock"]).any():
        raise RuntimeError("duplicate exact-clock rows; refusing aggregation")
    exact["close"] = pd.to_numeric(exact["close"], errors="raise")
    wide = exact.pivot(index="trading_day", columns="clock", values="close")
    spine = pd.DataFrame({"trading_day": days.astype(str).drop_duplicates().sort_values().to_numpy()})
    out = spine.merge(wide, on="trading_day", how="left", validate="one_to_one")
    for clock, column in CLOCK_COLUMNS.items():
        if clock not in out.columns:
            out[clock] = np.nan
        out[column] = pd.to_numeric(out[clock], errors="coerce")
    out = out.loc[:, ["trading_day", *CLOCK_COLUMNS.values()]].sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    assert_one_row_per_day(out, "opening clock carrier")
    return out


def year_slice(frame: pd.DataFrame, year: int) -> pd.DataFrame:
    days = pd.to_datetime(frame["trading_day"], errors="raise")
    out = frame.loc[days.dt.year == year].copy()
    return out.sort_values("trading_day", kind="mergesort").reset_index(drop=True)


def compare_numeric_series(left: pd.Series, right: pd.Series, label: str) -> dict:
    left_num = pd.to_numeric(left, errors="coerce")
    right_num = pd.to_numeric(right, errors="coerce")
    if len(left_num) != len(right_num):
        raise RuntimeError(f"{label} length mismatch")
    if not bool((left_num.isna().to_numpy() == right_num.isna().to_numpy()).all()):
        raise RuntimeError(f"{label} NaN mask mismatch")
    both = ~left_num.isna()
    if not bool(both.any()):
        return {"column": label, "nan_mask": "exact", "max_abs_diff": 0.0, "nonzero_diff_count": 0}
    left_v = left_num[both].to_numpy(dtype=np.float64)
    right_v = right_num[both].to_numpy(dtype=np.float64)
    diff = np.abs(left_v - right_v)
    max_abs = float(diff.max()) if len(diff) else 0.0
    ulp = np.abs(np.nextafter(left_v, np.inf) - left_v)
    allowed = np.maximum(CSV_ABS_FLOOR, ulp * CSV_ULP_MULT)
    if bool(np.any(diff > allowed)):
        raise RuntimeError(f"{label} exceeds CSV round-trip machine precision: {max_abs}")
    return {
        "column": label,
        "nan_mask": "exact",
        "max_abs_diff": max_abs,
        "nonzero_diff_count": int((diff > 0).sum()),
    }


def verify_factor_parity(frozen: pd.DataFrame, out_dir: Path, years: list[int]) -> dict:
    shards = []
    expected_parts = []
    for year in years:
        path = out_dir / f"factor_panel_{year}.csv"
        shard = pd.read_csv(path)
        shard["trading_day"] = normalize_trading_day(shard["trading_day"])
        if list(shard.columns) != list(FACTOR_PANEL_COLUMNS):
            raise RuntimeError(f"{path.name} column order/schema mismatch")
        shards.append(shard)
        expected_parts.append(year_slice(frozen, year))
    got = pd.concat(shards, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    exp = pd.concat(expected_parts, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    exp = exp.loc[exp["trading_day"].between(PARITY_START, PARITY_END)].reset_index(drop=True)
    got = got.loc[got["trading_day"].between(PARITY_START, PARITY_END)].reset_index(drop=True)
    if list(got["trading_day"]) != list(exp["trading_day"]):
        raise RuntimeError("2015-2020 factor-panel trading_day inventory mismatch")
    column_parity = [compare_numeric_series(exp[column], got[column], column) for column in FACTOR_PANEL_COLUMNS[1:]]
    return {
        "window": f"{PARITY_START}..{PARITY_END}",
        "status": "PASS",
        "row_count": int(len(got)),
        "min_day": str(got["trading_day"].min()),
        "max_day": str(got["trading_day"].max()),
        "columns": column_parity,
    }


def load_published_clocks(out_dir: Path, years: list[int]) -> pd.DataFrame:
    shards = []
    for year in years:
        path = out_dir / f"opening_clocks_{year}.csv"
        shard = pd.read_csv(path)
        shard["trading_day"] = normalize_trading_day(shard["trading_day"])
        expected = ["trading_day", *CLOCK_COLUMNS.values()]
        if list(shard.columns) != expected:
            raise RuntimeError(f"{path.name} column order/schema mismatch")
        shards.append(shard)
    return pd.concat(shards, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)


def verify_clock_parity(minute_bars: Path, clocks: pd.DataFrame, reference_csv: Path) -> dict:
    source = extract_exact_clocks(
        minute_bars,
        clocks.loc[clocks["trading_day"].between(CLOCK_DEV_START, CLOCK_DEV_END), "trading_day"],
    )
    source = source.loc[source["trading_day"].between(CLOCK_DEV_START, CLOCK_DEV_END)].reset_index(drop=True)
    published = clocks.loc[clocks["trading_day"].between(CLOCK_DEV_START, CLOCK_DEV_END)].reset_index(drop=True)
    if list(published["trading_day"]) != list(source["trading_day"]):
        raise RuntimeError("2019-2020 clock carrier inventory mismatch versus source parquet")
    ref = pd.read_csv(reference_csv)
    required = {"trading_day", "clock", "close"}
    missing = required.difference(ref.columns)
    if missing:
        raise RuntimeError(f"clock reference missing columns: {sorted(missing)}")
    ref["trading_day"] = normalize_trading_day(ref["trading_day"])
    ref["clock"] = ref["clock"].astype(str)
    ref = ref.loc[ref["clock"].isin(CLOCKS)].copy()
    if ref.duplicated(["trading_day", "clock"]).any():
        raise RuntimeError("clock reference contains duplicate exact clocks")
    ref_wide = ref.pivot(index="trading_day", columns="clock", values="close").reset_index()
    ref_wide["trading_day"] = normalize_trading_day(ref_wide["trading_day"])
    for clock, column in CLOCK_COLUMNS.items():
        if clock not in ref_wide.columns:
            raise RuntimeError(f"clock reference missing {clock}")
        ref_wide[column] = pd.to_numeric(ref_wide[clock], errors="coerce")
    ref_wide = ref_wide.loc[:, ["trading_day", *CLOCK_COLUMNS.values()]].sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if list(published["trading_day"]) != list(ref_wide["trading_day"]):
        raise RuntimeError("2019-2020 clock carrier trading_day inventory mismatch versus development CSV")
    column_parity = []
    for column in CLOCK_COLUMNS.values():
        column_parity.append(compare_numeric_series(source[column], published[column], f"source:{column}"))
        column_parity.append(compare_numeric_series(ref_wide[column], published[column], f"devpack:{column}"))
    return {
        "window": f"{CLOCK_DEV_START}..{CLOCK_DEV_END}",
        "status": "PASS",
        "row_count": int(len(published)),
        "clocks": list(CLOCKS),
        "reference_csv": repo_path(reference_csv),
        "columns": column_parity,
    }


def published_years(start_year: int, end_year: int, emit_blackbox: bool) -> list[int]:
    years = list(range(start_year, end_year + 1))
    if emit_blackbox:
        return years
    return [year for year in years if year < BLACKBOX_START_YEAR]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the connector-readable 2015-2020 runtime text carrier.")
    parser.add_argument("--annotated-panel", type=Path, default=ROOT / "data/high_open_dev_2015_2025/annotated_panel.parquet")
    parser.add_argument("--minute-bars", type=Path, default=ROOT / "data/high_open_dev_2015_2025/1m_official.parquet")
    parser.add_argument("--frozen-panel", type=Path, default=ROOT / "data/development/csi1000_open_pit_panel.parquet")
    parser.add_argument("--clock-reference-csv", type=Path, default=ROOT / "data/development/trend_open_state_dev_pack_2019_2020/minute_clocks_2019_2020.csv")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/runtime_text_2015_2025")
    parser.add_argument("--receipt", type=Path, default=ROOT / "docs/research/runtime_text_carrier_parity_receipt_v1.json")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int, default=DEFAULT_END_YEAR)
    parser.add_argument(
        "--emit-blackbox-window-text",
        action="store_true",
        help="Refuse-by-default switch. 2021-2025 row-level text is withheld unless explicitly forced.",
    )
    args = parser.parse_args()

    if args.start_year > args.end_year:
        raise RuntimeError("start-year must be <= end-year")
    if args.start_year < DEFAULT_START_YEAR or args.end_year > DEFAULT_END_YEAR:
        raise RuntimeError(f"supported year window is {DEFAULT_START_YEAR}..{DEFAULT_END_YEAR}")
    if args.emit_blackbox_window_text:
        raise RuntimeError(
            "refusing to emit 2021-2025 row-level text shards: "
            "overnight_reusable_blackbox_policy and current_authority forbid a public BLACKBOX CSV pack, "
            "and 2021-2025 factor rows would require reconstruction/feature engineering"
        )

    years = published_years(args.start_year, args.end_year, False)
    withheld_years = [year for year in range(args.start_year, args.end_year + 1) if year not in years]
    if not years:
        raise RuntimeError("no publishable years remain after BLACKBOX withhold")

    annotated_days = load_annotated_days(args.annotated_panel)
    frozen = load_frozen_factor_panel(args.frozen_panel)
    frozen = frozen.loc[frozen["trading_day"].between(PARITY_START, PARITY_END)].reset_index(drop=True)
    annotated_dev = annotated_days.loc[annotated_days["trading_day"].between(PARITY_START, PARITY_END)].reset_index(drop=True)
    if list(frozen["trading_day"]) != list(annotated_dev["trading_day"]):
        raise RuntimeError("annotated_panel 2015-2020 trading_day inventory differs from frozen development panel")

    requested_factor = frozen.loc[pd.to_datetime(frozen["trading_day"]).dt.year.isin(years)].copy()
    if requested_factor.empty:
        raise RuntimeError("frozen development panel has no rows in the publishable year window")
    clocks = extract_exact_clocks(args.minute_bars, requested_factor["trading_day"])

    args.out_dir.mkdir(parents=True, exist_ok=True)
    factor_outputs = {}
    clock_outputs = {}
    annotated_sha = sha256_file(args.annotated_panel)
    minute_sha = sha256_file(args.minute_bars)
    frozen_sha = sha256_file(args.frozen_panel)

    for year in years:
        factor_year = year_slice(requested_factor, year)
        clock_year = year_slice(clocks, year)
        if factor_year.empty or clock_year.empty:
            raise RuntimeError(f"missing publishable rows for {year}")
        if list(factor_year["trading_day"]) != list(clock_year["trading_day"]):
            raise RuntimeError(f"{year} factor/clock trading_day inventory mismatch")
        factor_path = args.out_dir / f"factor_panel_{year}.csv"
        clock_path = args.out_dir / f"opening_clocks_{year}.csv"
        write_csv(factor_year, factor_path)
        write_csv(clock_year, clock_path)
        factor_outputs[str(year)] = file_stats(factor_path, factor_year, frozen_sha)
        clock_outputs[str(year)] = file_stats(clock_path, clock_year, minute_sha)

    factor_parity = verify_factor_parity(frozen, args.out_dir, years)
    published_clocks = load_published_clocks(args.out_dir, years)
    clock_parity = verify_clock_parity(args.minute_bars, published_clocks, args.clock_reference_csv)

    manifest = {
        "schema_id": SCHEMA_ID,
        "instrument": INSTRUMENT,
        "purpose": "cloud_readable_minimal_runtime_carrier",
        "source_files": {
            "annotated_panel": {
                "path": repo_path(args.annotated_panel),
                "sha256": annotated_sha,
            },
            "minute_bars": {
                "path": repo_path(args.minute_bars),
                "sha256": minute_sha,
            },
            "frozen_development_panel": {
                "path": repo_path(args.frozen_panel),
                "sha256": frozen_sha,
                "role": "already_materialized_2015_2020_feature_authority_no_recompute",
            },
        },
        "transform": TRANSFORM_FLAGS,
        "factor_panel_columns": list(FACTOR_PANEL_COLUMNS),
        "clock_columns": list(CLOCK_COLUMNS.values()),
        "clocks": list(CLOCKS),
        "years": years,
        "supported_year_window": [DEFAULT_START_YEAR, DEFAULT_END_YEAR],
        "published_year_window": [min(years), max(years)],
        "withheld_years": withheld_years,
        "withhold_reason": (
            "2021-2025 row-level text would convert reusable BLACKBOX detailed rows into a public CSV pack "
            "and 2021-2025 factor values are not already materialized without reconstruction"
        ),
        "outputs": {
            "factor_panel": factor_outputs,
            "opening_clocks": clock_outputs,
        },
        "evidence_role": "connector_readable_runtime_carrier_not_new_scientific_authority",
        "production_authority": False,
    }
    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    receipt = {
        "schema_id": "overnight_runtime_text_carrier_parity_receipt@1.0",
        "purpose": "data_engineering_parity_only",
        "scientific_change": False,
        "transform": TRANSFORM_FLAGS,
        "instrument": INSTRUMENT,
        "source_hashes": {
            "annotated_panel": annotated_sha,
            "minute_bars": minute_sha,
            "frozen_development_panel": frozen_sha,
        },
        "output_hashes": {
            "manifest": sha256_file(manifest_path),
            "factor_panel": {year: spec["sha256"] for year, spec in factor_outputs.items()},
            "opening_clocks": {year: spec["sha256"] for year, spec in clock_outputs.items()},
        },
        "row_inventories": {
            "factor_panel": {
                year: {"row_count": spec["row_count"], "min_day": spec["min_day"], "max_day": spec["max_day"]}
                for year, spec in factor_outputs.items()
            },
            "opening_clocks": {
                year: {"row_count": spec["row_count"], "min_day": spec["min_day"], "max_day": spec["max_day"]}
                for year, spec in clock_outputs.items()
            },
        },
        "clock_inventories": {
            "clocks": list(CLOCKS),
            "columns": list(CLOCK_COLUMNS.values()),
            "exact_clock_only": True,
        },
        "factor_panel_parity_2015_2020": factor_parity,
        "clock_parity_2019_2020": clock_parity,
        "blackbox_window_text_shards": {
            "generated": False,
            "committed": False,
            "reason": "overnight_reusable_blackbox_policy_v1 and current_authority forbid public 2021-2025 detailed text rows",
        },
        "production_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("RUNTIME_TEXT_CARRIER_READY")
    print("PUBLISHED_YEARS", ",".join(str(year) for year in years))
    print("FACTOR_PANEL_PARITY_2015_2020", factor_parity["status"])
    print("CLOCK_PARITY_2019_2020", clock_parity["status"])
    print("BLACKBOX_TEXT_WITHHELD", "true" if withheld_years else "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
