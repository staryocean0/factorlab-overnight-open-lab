#!/usr/bin/env python3
"""Compact reusable BLACKBOX controller for frozen OFP-B4 driver coherence.

Internally reads the governed 2021-2025 rows but persists and prints only one of
PASS / FAIL / INSUFFICIENT plus non-outcome provenance. Hidden metrics, counts,
yearly results, dates, examples and failure attribution are never written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

TRAIN_START = pd.Timestamp("2015-01-05")
TRAIN_END = pd.Timestamp("2020-12-31")
BB_START = pd.Timestamp("2021-01-01")
BB_END = pd.Timestamp("2025-12-31")
TARGET = "opening_gap_rvol"
CANDIDATE = "driver_coherence"
BASELINE_CONTROLS = [
    "r1", "r20", "abs_r1", "prev_gap", "overnight_trend_5",
    "prev_daytime", "prev_last_hour", "prev_afternoon", "log_rvol20",
    "weekend", "holiday_reopen", "global_risk_z", "china_offshore_z",
    "fx_cny_z",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.nanstd(a) == 0 or np.nanstd(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    d = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(d, y, rcond=None)
    return y - d @ coef


def partial_corr(y: np.ndarray, candidate: np.ndarray, baseline: np.ndarray) -> float:
    yr = residualize(y, baseline)
    cr = residualize(candidate, baseline)
    return corr(yr, cr)


def trailing_rms_prev(values: pd.Series) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def add_hkma(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path).copy()
    x["date"] = pd.to_datetime(x["date"], errors="raise").dt.normalize()
    x["usdcny_hk"] = pd.to_numeric(x["usdcny_hk"], errors="coerce")
    x = x.dropna(subset=["date", "usdcny_hk"]).drop_duplicates("date", keep="last").sort_values("date")
    out = df.copy()
    dates = x["date"].to_numpy(dtype="datetime64[ns]")
    levels = x["usdcny_hk"].to_numpy(float)
    target = out["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev = out["previous_china_day"].to_numpy(dtype="datetime64[ns]")
    start_idx = np.full(len(out), -1, dtype=int)
    valid_prev = out["previous_china_day"].notna().to_numpy()
    start_idx[valid_prev] = np.searchsorted(dates, prev[valid_prev], side="right") - 1
    end_idx = np.searchsorted(dates, target, side="left") - 1
    valid = valid_prev & (start_idx >= 0) & (end_idx >= start_idx)
    ret = np.full(len(out), np.nan)
    ret[valid] = levels[end_idx[valid]] / levels[start_idx[valid]] - 1.0
    if valid.any() and np.any(dates[end_idx[valid]] >= target[valid]):
        raise RuntimeError("HKMA target-date leakage")
    out["hkma_usdcny_closure_return"] = ret
    return out


def attach_a50(df: pd.DataFrame, holiday_path: Path, ordinary_path: Path) -> tuple[pd.DataFrame, float, bool]:
    h = pd.read_parquet(holiday_path).copy()
    o = pd.read_parquet(ordinary_path).copy()
    for x in (h, o):
        x["trading_day"] = pd.to_datetime(x["trading_day"], errors="raise").dt.normalize()
    hcols = ["trading_day", "a50_holiday_closure_return", "target_end_time"]
    ocols = ["trading_day", "a50_ordinary_preauction_closure_return", "target_end_time"]
    out = df.merge(h[hcols].rename(columns={"target_end_time": "holiday_end_time"}), on="trading_day", how="left", validate="one_to_one")
    out = out.merge(o[ocols].rename(columns={"target_end_time": "ordinary_end_time"}), on="trading_day", how="left", validate="one_to_one")
    holiday = pd.to_numeric(out["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    havail = holiday & out["a50_holiday_closure_return"].notna()
    oavail = (~holiday) & out["a50_ordinary_preauction_closure_return"].notna()
    clock_ok = True
    if havail.any():
        clock_ok &= bool((pd.to_numeric(out.loc[havail, "holiday_end_time"], errors="raise").round().astype("int64") < 92500).all())
    if oavail.any():
        clock_ok &= bool((pd.to_numeric(out.loc[oavail, "ordinary_end_time"], errors="raise").round().astype("int64") < 91500).all())
    out["a50_channel_return"] = np.where(
        holiday,
        pd.to_numeric(out["a50_holiday_closure_return"], errors="coerce"),
        pd.to_numeric(out["a50_ordinary_preauction_closure_return"], errors="coerce"),
    )
    bb = out["trading_day"].between(BB_START, BB_END)
    ordinary_bb = bb & ~holiday
    ordinary_coverage = float((oavail & bb).sum() / ordinary_bb.sum()) if ordinary_bb.any() else 0.0
    return out, ordinary_coverage, clock_ok


def build_coordinates(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.sort_values("trading_day").reset_index(drop=True).copy()
    x["rvol20"] = pd.to_numeric(x["rvol20"], errors="coerce")
    for raw in ["us_nasdaq", "us_vix_chg", "a50_channel_return", "hkma_usdcny_closure_return"]:
        x[raw] = pd.to_numeric(x[raw], errors="coerce")
        x[f"{raw}_rms60_prev"] = trailing_rms_prev(x[raw])
    x["nasdaq_risk_z"] = x["us_nasdaq"] / x["us_nasdaq_rms60_prev"]
    x["vix_risk_z"] = -x["us_vix_chg"] / x["us_vix_chg_rms60_prev"]
    x["global_risk_z"] = 0.5 * (x["nasdaq_risk_z"] + x["vix_risk_z"])
    x["china_offshore_z"] = x["a50_channel_return"] / x["a50_channel_return_rms60_prev"]
    x["fx_cny_z"] = -x["hkma_usdcny_closure_return"] / x["hkma_usdcny_closure_return_rms60_prev"]
    denom = x["global_risk_z"].abs() + x["china_offshore_z"].abs() + x["fx_cny_z"].abs()
    x[CANDIDATE] = np.where(
        np.isfinite(denom) & denom.gt(0),
        (x["global_risk_z"] + x["china_offshore_z"] + x["fx_cny_z"]) / denom,
        np.nan,
    )
    x["log_rvol20"] = np.where(x["rvol20"].gt(0), np.log(x["rvol20"]), np.nan)
    x[TARGET] = pd.to_numeric(x["gap"], errors="coerce") / x["rvol20"]
    return x


def fit_ols(train: pd.DataFrame, features: list[str]) -> np.ndarray:
    x = train[features].to_numpy(float)
    y = train[TARGET].to_numpy(float)
    d = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(d, y, rcond=None)
    return coef


def predict(frame: pd.DataFrame, features: list[str], coef: np.ndarray) -> np.ndarray:
    x = frame[features].to_numpy(float)
    d = np.column_stack([np.ones(len(x)), x])
    return d @ coef


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    sse = float(np.sum((y - p) ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "sse": sse,
        "r2": float("nan") if sst <= 0 else 1.0 - sse / sst,
        "ic": corr(y, p),
        "sign": float(np.mean((p >= 0) == (y >= 0))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--hkma", type=Path, required=True)
    ap.add_argument("--holiday-a50", type=Path, required=True)
    ap.add_argument("--ordinary-a50", type=Path, required=True)
    ap.add_argument("--source-manifest", type=Path, required=True)
    ap.add_argument("--reconstruction-contract", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != "overnight_driver_coherence_open_gap_v1":
        raise RuntimeError("wrong B4 BLACKBOX protocol identity")
    if protocol.get("candidate_increment") != [CANDIDATE] or protocol.get("baseline_controls") != BASELINE_CONTROLS:
        raise RuntimeError("B4 BLACKBOX formula/baseline differs from frozen protocol")
    if protocol.get("target") != TARGET:
        raise RuntimeError("B4 BLACKBOX target differs from frozen protocol")

    manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    required_assertions = [
        "same_contract_all_events", "no_future_volume_or_oi_selection",
        "no_mid_window_roll", "no_forward_fill_or_interpolation",
        "blackbox_not_used_for_fit_or_rule_selection",
    ]
    source_ok = all(manifest.get("assertions", {}).get(k) is True for k in required_assertions)

    panel = pd.read_parquet(args.panel).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    needed = {
        "trading_day", "gap", "r1", "r20", "abs_r1", "prev_gap",
        "overnight_trend_5", "prev_daytime", "prev_last_hour",
        "prev_afternoon", "rvol20", "weekend", "holiday_reopen",
        "us_nasdaq", "us_vix_chg",
    }
    if not needed.issubset(panel.columns):
        raise RuntimeError("reconstructed panel missing frozen B4 inputs")
    panel = panel.sort_values("trading_day").reset_index(drop=True)
    panel["previous_china_day"] = panel["trading_day"].shift(1)
    df = add_hkma(panel, args.hkma)
    df, ordinary_coverage, clocks_ok = attach_a50(df, args.holiday_a50, args.ordinary_a50)
    df = build_coordinates(df)

    all_required = [*BASELINE_CONTROLS, CANDIDATE, TARGET]
    complete = df[all_required].apply(pd.to_numeric, errors="coerce").notna().all(axis=1)
    train_mask = df["trading_day"].between(TRAIN_START, TRAIN_END) & complete
    bb_window = df["trading_day"].between(BB_START, BB_END)
    bb_mask = bb_window & complete
    train = df.loc[train_mask].copy()
    bb = df.loc[bb_mask].copy()

    bb_total = int(bb_window.sum())
    complete_coverage = float(len(bb) / bb_total) if bb_total else 0.0
    suff = protocol["sufficiency_gates"]
    sufficient = (
        source_ok
        and clocks_ok
        and ordinary_coverage >= float(suff["ordinary_A50_coverage_minimum"])
        and len(train) >= int(suff["development_complete_cases_minimum"])
        and len(bb) >= int(suff["blackbox_complete_cases_minimum"])
        and complete_coverage >= float(suff["blackbox_complete_case_coverage_minimum"])
    )

    if not sufficient:
        decision = "INSUFFICIENT"
    else:
        baseline_coef = fit_ols(train, BASELINE_CONTROLS)
        candidate_features = [*BASELINE_CONTROLS, CANDIDATE]
        candidate_coef = fit_ols(train, candidate_features)
        y = bb[TARGET].to_numpy(float)
        p0 = predict(bb, BASELINE_CONTROLS, baseline_coef)
        p1 = predict(bb, candidate_features, candidate_coef)
        m0, m1 = metrics(y, p0), metrics(y, p1)

        pooled_pcorr = partial_corr(
            y,
            bb[CANDIDATE].to_numpy(float),
            bb[BASELINE_CONTROLS].to_numpy(float),
        )
        annual_sse = 0
        annual_ic = 0
        annual_negative_pcorr = 0
        years = bb["trading_day"].dt.year.to_numpy()
        for year in range(2021, 2026):
            mask = years == year
            if not mask.any():
                continue
            ym = y[mask]
            a0, a1 = metrics(ym, p0[mask]), metrics(ym, p1[mask])
            annual_sse += int(a1["sse"] < a0["sse"])
            annual_ic += int(np.isfinite(a1["ic"]) and np.isfinite(a0["ic"]) and a1["ic"] >= a0["ic"])
            pc = partial_corr(
                ym,
                bb.loc[mask, CANDIDATE].to_numpy(float),
                bb.loc[mask, BASELINE_CONTROLS].to_numpy(float),
            )
            annual_negative_pcorr += int(np.isfinite(pc) and pc < 0)

        gates = protocol["pass_gates"]
        passed = [
            m1["sse"] < m0["sse"],
            m1["r2"] > m0["r2"],
            np.isfinite(m1["ic"]) and np.isfinite(m0["ic"]) and m1["ic"] >= m0["ic"],
            m1["sign"] >= m0["sign"] - float(gates["candidate_blackbox_sign_accuracy_not_below_baseline_minus"]),
            annual_sse >= int(gates["minimum_natural_years_candidate_sse_below_baseline"]),
            annual_ic >= int(gates["minimum_natural_years_candidate_ic_not_below_baseline"]),
            np.isfinite(pooled_pcorr) and pooled_pcorr < 0,
            annual_negative_pcorr >= int(gates["minimum_natural_years_partial_correlation_matching_DEV_negative_sign"]),
        ]
        decision = "PASS" if all(passed) else "FAIL"

    protocol_sha = sha256(args.protocol)
    source_manifest_sha = sha256(args.source_manifest)
    reconstruction_contract_sha = sha256(args.reconstruction_contract)
    query_payload = {
        "candidate": "overnight_driver_coherence_open_gap_v1",
        "comparator": "same_OLS_baseline_without_driver_coherence",
        "blackbox_window": "2021-01-01..2025-12-31",
        "protocol_sha256": protocol_sha,
        "source_manifest_sha256": source_manifest_sha,
        "reconstruction_contract_sha256": reconstruction_contract_sha,
    }
    query_id = hashlib.sha256(json.dumps(query_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "overnight_driver_coherence_open_gap_blackbox_receipt@1.0",
        "session_date": "2026-09-12",
        "research_identity": "overnight_driver_coherence_open_gap_v1",
        "candidate": "driver_coherence",
        "comparator": "same_OLS_baseline_without_driver_coherence",
        "blackbox_window": "2021-01-01..2025-12-31",
        "decision": decision,
        "query_id": query_id,
        "protocol_sha256": protocol_sha,
        "source_manifest_sha256": source_manifest_sha,
        "reconstruction_contract_sha256": reconstruction_contract_sha,
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "yearly_results_persisted": False,
        "counts_persisted": False,
        "failure_attribution_persisted": False,
        "reuse_is_independent_oos": False,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
