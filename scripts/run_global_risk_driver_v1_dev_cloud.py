#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_global_risk_driver_v1"
YEARS = tuple(range(2015, 2021))
TARGET = "opening_gap_rvol"
CANDIDATE = "global_risk_z"
BASELINE = [
    "r1", "r20", "abs_r1", "prev_gap", "overnight_trend_5",
    "prev_daytime", "prev_last_hour", "prev_afternoon", "log_rvol20",
    "weekend", "holiday_reopen",
]
PROTOCOL = ROOT / "docs/governance/global_risk_driver_v1_protocol.json"
STATE = ROOT / "docs/governance/global_risk_driver_v1_state.json"
AUTHORITY = ROOT / "docs/governance/current_authority_v1.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
FACTOR_ROOT = ROOT / "data/runtime_text_2015_2025"
OUTPUT = ROOT / "docs/research/cloud_global_risk_driver_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    d = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(d, y, rcond=None)
    return y - d @ coef


def r2(y: np.ndarray, p: np.ndarray) -> float:
    sst = float(np.sum((y - np.mean(y)) ** 2))
    if sst <= 0:
        return float("nan")
    return 1.0 - float(np.sum((y - p) ** 2)) / sst


def trailing_rms_prev(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def linear_diag(frame: pd.DataFrame, min_n: int) -> dict:
    cols = [*BASELINE, CANDIDATE, TARGET]
    x = frame[cols].apply(pd.to_numeric, errors="coerce").dropna()
    if len(x) < min_n:
        return {"n": int(len(x)), "status": "insufficient"}
    y = x[TARGET].to_numpy(float)
    xb = x[BASELINE].to_numpy(float)
    c = x[CANDIDATE].to_numpy(float)
    db = np.column_stack([np.ones(len(xb)), xb])
    dc = np.column_stack([np.ones(len(xb)), xb, c])
    bb, *_ = np.linalg.lstsq(db, y, rcond=None)
    bc, *_ = np.linalg.lstsq(dc, y, rcond=None)
    rb, rc = r2(y, db @ bb), r2(y, dc @ bc)
    cr = residualize(c, xb)
    yr = residualize(y, xb)
    pcorr = None if np.std(cr) == 0 or np.std(yr) == 0 else float(np.corrcoef(cr, yr)[0, 1])
    z = x[[*BASELINE, CANDIDATE, TARGET]].copy()
    for col in z.columns:
        sd = float(z[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            return {"n": int(len(x)), "status": "degenerate"}
        z[col] = (z[col] - float(z[col].mean())) / sd
    zd = np.column_stack([np.ones(len(z)), z[[*BASELINE, CANDIDATE]].to_numpy(float)])
    zcoef, *_ = np.linalg.lstsq(zd, z[TARGET].to_numpy(float), rcond=None)
    return {
        "n": int(len(x)),
        "status": "ok",
        "partial_corr": pcorr,
        "baseline_r2": rb,
        "candidate_r2": rc,
        "delta_r2": rc - rb,
        "standardized_global_risk_z_coefficient": float(zcoef[-1]),
    }


def load_frame() -> tuple[pd.DataFrame, dict]:
    manifest = read_json(FACTOR_ROOT / "manifest.json")
    if manifest.get("published_year_window") != [2015, 2020]:
        raise RuntimeError("factor runtime publication boundary drift")
    pieces, hashes = [], {}
    required = {
        "trading_day", "gap", "r1", "r20", "abs_r1", "prev_gap",
        "overnight_trend_5", "prev_daytime", "prev_last_hour", "prev_afternoon",
        "rvol20", "weekend", "holiday_reopen", "us_nasdaq", "us_vix_chg",
    }
    expected_outputs = manifest.get("outputs", {}).get("factor_panel", {})
    for year in YEARS:
        path = FACTOR_ROOT / f"factor_panel_{year}.csv"
        if sha256(path) != expected_outputs[str(year)]["sha256"]:
            raise RuntimeError(f"factor shard digest drift {year}")
        f = pd.read_csv(path)
        if required.difference(f.columns):
            raise RuntimeError(f"factor shard {year} missing columns")
        f["trading_day"] = pd.to_datetime(f["trading_day"], errors="raise").dt.normalize()
        if not f["trading_day"].dt.year.eq(year).all():
            raise RuntimeError(f"factor shard year drift {year}")
        f["year"] = year
        pieces.append(f)
        hashes[str(year)] = {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
    x = pd.concat(pieces, ignore_index=True).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if x["trading_day"].duplicated().any():
        raise RuntimeError("duplicate B1 trading day")
    if x["trading_day"].min() != pd.Timestamp("2015-01-05") or x["trading_day"].max() != pd.Timestamp("2020-12-31"):
        raise RuntimeError("B1 development boundary drift")
    return x, {"factor_shards": hashes, "manifest_sha256": sha256(FACTOR_ROOT / "manifest.json")}


def build_coordinates(x: pd.DataFrame) -> pd.DataFrame:
    y = x.copy()
    y["rvol20"] = pd.to_numeric(y["rvol20"], errors="coerce")
    y = y.loc[np.isfinite(y["rvol20"]) & y["rvol20"].gt(0)].copy()
    for raw in ["us_nasdaq", "us_vix_chg"]:
        y[raw] = pd.to_numeric(y[raw], errors="coerce")
        y[f"{raw}_rms60_prev"] = trailing_rms_prev(y[raw])
    y["nasdaq_risk_z"] = y["us_nasdaq"] / y["us_nasdaq_rms60_prev"]
    y["vix_risk_z"] = -y["us_vix_chg"] / y["us_vix_chg_rms60_prev"]
    y[CANDIDATE] = 0.5 * (y["nasdaq_risk_z"] + y["vix_risk_z"])
    y["log_rvol20"] = np.log(y["rvol20"])
    y[TARGET] = pd.to_numeric(y["gap"], errors="coerce") / y["rvol20"]
    return y


def main() -> int:
    if OUTPUT.exists():
        raise RuntimeError(f"refusing to overwrite existing B1 receipt: {OUTPUT}")
    protocol = read_json(PROTOCOL)
    state = read_json(STATE)
    authority = read_json(AUTHORITY)
    ledger = read_json(LEDGER)
    if protocol.get("research_identity") != IDENTITY or state.get("research_identity") != IDENTITY:
        raise RuntimeError("B1 identity drift")
    if state.get("outcome_opened") is not False:
        raise RuntimeError("B1 outcome already opened")
    if (authority.get("active_research") or {}).get("identity") != IDENTITY:
        raise RuntimeError("B1 is not current active research")
    if protocol.get("candidate_increment") != [CANDIDATE] or protocol.get("baseline_controls") != BASELINE or protocol.get("target") != TARGET:
        raise RuntimeError("B1 frozen design drift")
    if protocol.get("expected_direction") != "positive":
        raise RuntimeError("B1 expected direction drift")
    if ledger.get("query_count") != 7:
        raise RuntimeError("unexpected BLACKBOX ledger count before B1 DEV")

    raw, source = load_frame()
    dev = build_coordinates(raw)
    suff = protocol["sufficiency_gates"]
    annual_min = int(suff["each_calendar_year_complete_cases_min"])
    pooled_min = int(suff["pooled_complete_cases_min"])
    diagnostics = {"pooled": linear_diag(dev, pooled_min), "by_year": {}}
    for year in YEARS:
        diagnostics["by_year"][str(year)] = linear_diag(dev.loc[dev["year"].eq(year)], annual_min)

    pooled = diagnostics["pooled"]
    annual = diagnostics["by_year"]
    sufficient = pooled.get("status") == "ok" and all(annual[str(y)].get("status") == "ok" for y in YEARS)
    if sufficient:
        annual_coef = [float(annual[str(y)]["standardized_global_risk_z_coefficient"]) for y in YEARS]
        annual_dr2 = [float(annual[str(y)]["delta_r2"]) for y in YEARS]
        gates = {
            "all_sufficiency_pass": True,
            "pooled_partial_corr_positive": bool(float(pooled["partial_corr"]) > 0),
            "pooled_standardized_coefficient_positive": bool(float(pooled["standardized_global_risk_z_coefficient"]) > 0),
            "positive_annual_coefficient_count": int(sum(v > 0 for v in annual_coef)),
            "minimum_positive_annual_coefficient_count_pass": bool(sum(v > 0 for v in annual_coef) >= int(protocol["progression_gates"]["positive_calendar_year_coefficient_count_min"])),
            "median_annual_coefficient": float(np.median(annual_coef)),
            "median_annual_coefficient_positive": bool(float(np.median(annual_coef)) > 0),
            "pooled_delta_r2_positive": bool(float(pooled["delta_r2"]) > 0),
            "positive_annual_delta_r2_count": int(sum(v > 0 for v in annual_dr2)),
            "minimum_positive_annual_delta_r2_count_pass": bool(sum(v > 0 for v in annual_dr2) >= int(protocol["progression_gates"]["positive_calendar_year_delta_r2_count_min"])),
        }
        progression = all(gates[k] for k in [
            "pooled_partial_corr_positive", "pooled_standardized_coefficient_positive",
            "minimum_positive_annual_coefficient_count_pass", "median_annual_coefficient_positive",
            "pooled_delta_r2_positive", "minimum_positive_annual_delta_r2_count_pass",
        ])
    else:
        gates = {"all_sufficiency_pass": False}
        progression = False
    decision = "B1_DEV_INSUFFICIENT" if not sufficient else ("B1_DEV_PROGRESS_GLOBAL_RISK_CONTINUOUS_COORDINATE" if progression else "B1_DEV_NO_PROGRESS")

    receipt = {
        "schema_id": "overnight_global_risk_driver_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-B1_global_risk_driver",
        "phase": "mechanism_diagnostic",
        "development_window": "2015-01-05..2020-12-31",
        "candidate": CANDIDATE,
        "target": TARGET,
        "baseline_controls": BASELINE,
        "normalization": protocol["normalization"],
        "diagnostics": diagnostics,
        "progression_gate_components": gates,
        "decision": decision,
        "source_integrity": source,
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "state_at_execution": {"path": str(STATE.relative_to(ROOT)), "sha256": sha256(STATE)},
        "candidate_attempt_count": 1,
        "weight_search": False,
        "normalization_search": False,
        "threshold_search": False,
        "bucket_search": False,
        "channel_add_drop_search": False,
        "alternate_target_search": False,
        "strategy_PnL_optimization": False,
        "2021_2025_rows_opened": False,
        "reusable_blackbox_query_created": False,
        "production_authority": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("B1_GLOBAL_RISK_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
