#!/usr/bin/env python3
"""Build aggregate development-only target ledger for gap-fill prediction v2.

No model fitting, feature selection, threshold search, or 2026 data is allowed.
Targets are defined from the accepted CSI1000 09:31 open / previous 15:00 close
and the subsequent official one-minute high/low path.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_prediction_v2_protocol_v1.json"
PANEL = ROOT / "data/high_open_dev_2015_2025/annotated_panel.parquet"
MINUTES = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/research/cloud_session_20260906_gap_fill_v2_target_ledger_v1.json"
USAGE = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_target_data_usage_v1.json"

SYMBOL = "000852.SH"
START = "2015-01-05"
END = "2025-12-31"
MATERIAL = {"gt10bp": 0.001, "gt30bp": 0.003}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def expected_clocks() -> dict[str, list[str]]:
    morning = pd.date_range("2000-01-01 09:31", "2000-01-01 11:30", freq="min").strftime("%H:%M").tolist()
    afternoon = pd.date_range("2000-01-01 13:01", "2000-01-01 15:00", freq="min").strftime("%H:%M").tolist()
    full = morning + afternoon
    return {
        "15m": morning[:15],
        "60m": morning[:60],
        "eod": full,
    }


def stats(part: pd.DataFrame) -> dict:
    n = int(len(part))
    if n == 0:
        return {
            "n": 0,
            "fill_15m_rate": None,
            "fill_60m_rate": None,
            "fill_eod_rate": None,
            "fill_ratio_15m_mean": None,
            "fill_ratio_60m_mean": None,
            "fill_ratio_eod_mean": None,
            "fill_ratio_eod_median": None,
            "time_to_fill_trading_minutes_median": None,
        }
    filled = part.loc[part["fill_eod"]]
    return {
        "n": n,
        "fill_15m_count": int(part["fill_15m"].sum()),
        "fill_60m_count": int(part["fill_60m"].sum()),
        "fill_eod_count": int(part["fill_eod"].sum()),
        "fill_15m_rate": float(part["fill_15m"].mean()),
        "fill_60m_rate": float(part["fill_60m"].mean()),
        "fill_eod_rate": float(part["fill_eod"].mean()),
        "fill_ratio_15m_mean": float(part["fill_ratio_15m"].mean()),
        "fill_ratio_60m_mean": float(part["fill_ratio_60m"].mean()),
        "fill_ratio_eod_mean": float(part["fill_ratio_eod"].mean()),
        "fill_ratio_eod_median": float(part["fill_ratio_eod"].median()),
        "time_to_fill_trading_minutes_median": None if filled.empty else float(filled["time_to_fill_trading_minutes"].median()),
    }


def compute_day(day_row: pd.Series, day_minutes: pd.DataFrame, clocks: dict[str, list[str]]) -> dict | None:
    open_px = float(day_row["open_0931"])
    prev_close = float(day_row["prev_close"])
    gap = float(day_row["overnight_gap"])
    if not np.isfinite(open_px) or not np.isfinite(prev_close) or not np.isfinite(gap) or open_px <= 0 or prev_close <= 0:
        return None
    if gap == 0.0:
        return {
            "trading_day": str(day_row["trading_day"]),
            "year": int(str(day_row["trading_day"])[:4]),
            "gap": gap,
            "gap_sign": "zero",
            "abs_gap": 0.0,
            "target_valid": False,
            "invalid_reason": "zero_gap",
        }

    dm = day_minutes.copy()
    dm["clock"] = dm["timestamp"].astype(str).str.slice(11, 16)
    dm = dm.sort_values("timestamp", kind="mergesort").drop_duplicates("clock", keep="last")
    present = set(dm["clock"].tolist())
    missing = {h: [c for c in req if c not in present] for h, req in clocks.items()}
    if missing["eod"]:
        return {
            "trading_day": str(day_row["trading_day"]),
            "year": int(str(day_row["trading_day"])[:4]),
            "gap": gap,
            "gap_sign": "high" if gap > 0 else "low",
            "abs_gap": abs(gap),
            "target_valid": False,
            "invalid_reason": "missing_required_minutes",
            "missing_eod_count": len(missing["eod"]),
        }

    dm = dm.set_index("clock")
    highs = pd.to_numeric(dm["high"], errors="coerce")
    lows = pd.to_numeric(dm["low"], errors="coerce")
    if highs.loc[clocks["eod"]].isna().any() or lows.loc[clocks["eod"]].isna().any():
        return {
            "trading_day": str(day_row["trading_day"]),
            "year": int(str(day_row["trading_day"])[:4]),
            "gap": gap,
            "gap_sign": "high" if gap > 0 else "low",
            "abs_gap": abs(gap),
            "target_valid": False,
            "invalid_reason": "non_numeric_high_low",
        }

    high_open = gap > 0
    denom = abs(open_px - prev_close)
    if denom <= 0:
        return None

    def horizon(req: list[str]) -> tuple[bool, float, float]:
        hh = highs.loc[req].to_numpy(dtype=float)
        ll = lows.loc[req].to_numpy(dtype=float)
        if high_open:
            favorable = open_px - float(np.min(ll))
            filled = bool(np.min(ll) <= prev_close)
        else:
            favorable = float(np.max(hh)) - open_px
            filled = bool(np.max(hh) >= prev_close)
        uncapped = float(favorable / denom)
        capped = float(np.clip(uncapped, 0.0, 1.0))
        return filled, capped, uncapped

    f15, r15, u15 = horizon(clocks["15m"])
    f60, r60, u60 = horizon(clocks["60m"])
    feod, reod, ueod = horizon(clocks["eod"])

    first_fill = None
    if feod:
        for i, c in enumerate(clocks["eod"], start=1):
            if high_open:
                hit = float(lows.loc[c]) <= prev_close
            else:
                hit = float(highs.loc[c]) >= prev_close
            if hit:
                first_fill = i
                break

    return {
        "trading_day": str(day_row["trading_day"]),
        "year": int(str(day_row["trading_day"])[:4]),
        "gap": gap,
        "gap_sign": "high" if high_open else "low",
        "abs_gap": abs(gap),
        "target_valid": True,
        "fill_15m": f15,
        "fill_60m": f60,
        "fill_eod": feod,
        "fill_ratio_15m": r15,
        "fill_ratio_60m": r60,
        "fill_ratio_eod": reod,
        "uncapped_excursion_15m": u15,
        "uncapped_excursion_60m": u60,
        "uncapped_excursion_eod": ueod,
        "time_to_fill_trading_minutes": first_fill,
    }


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["stage"] != "target_ledger_before_modeling":
        raise RuntimeError("V2 protocol stage drifted")
    if protocol["target_ledger_phase"]["model_fitting_allowed"] is not False:
        raise RuntimeError("target-ledger phase unexpectedly allows modeling")

    panel = pd.read_parquet(
        PANEL,
        filters=[("trading_day", ">=", START), ("trading_day", "<=", END)],
        columns=["trading_day", "open_0931", "prev_close", "overnight_gap"],
    )
    panel["trading_day"] = panel["trading_day"].astype(str)
    if panel.empty or panel["trading_day"].max() > END or panel["trading_day"].min() < START:
        raise RuntimeError("panel development boundary invalid")
    if (pd.to_datetime(panel["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered V2 target panel")

    minutes = pd.read_parquet(
        MINUTES,
        filters=[
            ("symbol", "==", SYMBOL),
            ("trading_day", ">=", START),
            ("trading_day", "<=", END),
        ],
        columns=["trading_day", "timestamp", "open", "high", "low", "close"],
    )
    minutes["trading_day"] = minutes["trading_day"].astype(str)
    if (pd.to_datetime(minutes["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 minute row entered V2 target ledger")

    groups = {day: g.copy() for day, g in minutes.groupby("trading_day", sort=False)}
    clocks = expected_clocks()
    rows = []
    for _, row in panel.sort_values("trading_day").iterrows():
        day = row["trading_day"]
        if day not in groups:
            rows.append({
                "trading_day": day,
                "year": int(day[:4]),
                "gap": float(row["overnight_gap"]),
                "gap_sign": "high" if float(row["overnight_gap"]) > 0 else "low" if float(row["overnight_gap"]) < 0 else "zero",
                "abs_gap": abs(float(row["overnight_gap"])),
                "target_valid": False,
                "invalid_reason": "missing_day_minutes",
            })
            continue
        result = compute_day(row, groups[day], clocks)
        if result is not None:
            rows.append(result)

    ledger = pd.DataFrame(rows)
    valid = ledger.loc[ledger["target_valid"]].copy()
    if valid.empty:
        raise RuntimeError("no valid V2 targets built")
    nested_15_60 = int((valid["fill_15m"] & (~valid["fill_60m"])).sum())
    nested_60_eod = int((valid["fill_60m"] & (~valid["fill_eod"])).sum())
    if nested_15_60 or nested_60_eod:
        raise RuntimeError("nested fill-event invariant violated")

    summary = {
        "all_valid": stats(valid),
        "by_sign": {sign: stats(valid.loc[valid["gap_sign"] == sign]) for sign in ["high", "low"]},
        "material": {},
        "by_year": {},
    }
    for name, threshold in MATERIAL.items():
        cohort = valid.loc[valid["abs_gap"] > threshold]
        summary["material"][name] = {
            "all": stats(cohort),
            "high": stats(cohort.loc[cohort["gap_sign"] == "high"]),
            "low": stats(cohort.loc[cohort["gap_sign"] == "low"]),
        }
    for year in range(2015, 2026):
        yp = valid.loc[valid["year"] == year]
        summary["by_year"][str(year)] = {
            "all": stats(yp),
            "high": stats(yp.loc[yp["gap_sign"] == "high"]),
            "low": stats(yp.loc[yp["gap_sign"] == "low"]),
            "gt10bp": stats(yp.loc[yp["abs_gap"] > MATERIAL["gt10bp"]]),
            "gt30bp": stats(yp.loc[yp["abs_gap"] > MATERIAL["gt30bp"]]),
        }

    invalid_counts = ledger.loc[~ledger["target_valid"], "invalid_reason"].value_counts(dropna=False).to_dict()
    receipt = {
        "schema_id": "overnight_open_gap_fill_v2_target_ledger@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_prediction_v2",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "development_window": {"start": START, "end": END},
        "prediction_timestamp": "09:31",
        "horizon_endpoints": {"15m": "09:45", "60m": "10:30", "eod": "15:00"},
        "expected_bar_counts": {k: len(v) for k, v in clocks.items()},
        "n_panel_days": int(len(panel)),
        "n_valid_target_days": int(len(valid)),
        "n_invalid_target_days": int((~ledger["target_valid"]).sum()),
        "invalid_reason_counts": {str(k): int(v) for k, v in invalid_counts.items()},
        "zero_gap_count": int((ledger["gap_sign"] == "zero").sum()),
        "nested_event_invariant": {
            "fill15_without_fill60": nested_15_60,
            "fill60_without_fillEOD": nested_60_eod,
            "passed": True,
        },
        "summary": summary,
        "source_hashes": {
            "protocol": sha256(PROTOCOL),
            "annotated_panel": sha256(PANEL),
            "one_minute_official": sha256(MINUTES),
            "runner": sha256(Path(__file__)),
        },
        "model_fitting_performed": False,
        "feature_selection_performed": False,
        "threshold_search_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "fresh_oos": False,
        "production_authority": False,
        "raw_target_rows_written_to_repo": False,
    }
    dump_json(OUT, receipt)
    usage = {
        "schema_id": "overnight_open_gap_fill_v2_target_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31_target_construction_only",
        "2026-01-05_to_2026-08-21": "not_loaded_repeat_only_reserved",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "model_fitting_performed": False,
        "feature_selection_performed": False,
        "raw_target_rows_persisted_in_repo": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)
    print("GAP_FILL_V2_TARGET_LEDGER_RESULT", json.dumps({
        "n_valid_target_days": receipt["n_valid_target_days"],
        "invalid_reason_counts": receipt["invalid_reason_counts"],
        "all_valid": summary["all_valid"],
        "gt10bp": summary["material"]["gt10bp"]["all"],
        "gt30bp": summary["material"]["gt30bp"]["all"],
        "2026_rows_loaded": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
