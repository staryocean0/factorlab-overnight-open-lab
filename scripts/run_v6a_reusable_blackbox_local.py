#!/usr/bin/env python3
"""Reusable low-bandwidth BLACKBOX evaluator for frozen V6A.

The controller may read 2021-2025 internally, but it persists and prints only
PASS / FAIL / INSUFFICIENT plus non-outcome provenance. Detailed metrics,
yearly/quarterly breakdowns, counts, events, attribution and failure clues are
never written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_FEATURES = [
    "r1", "r20", "abs_r1", "prev_gap", "overnight_trend_5", "prev_daytime",
    "prev_last_hour", "prev_afternoon", "rvol20", "weekend", "holiday_reopen",
    "us_nasdaq", "us_vix_chg",
]
V5_FEATURES = BASE_FEATURES + [
    "us_nasdaq_closure_extra", "us_vix_closure_extra",
    "hkma_usdcny_closure_return", "a50_holiday_closure_return",
]
V6_FEATURES = V5_FEATURES + ["a50_ordinary_preauction_closure_return"]
TRAIN_END = pd.Timestamp("2018-12-31")
BB_START = pd.Timestamp("2021-01-01")
BB_END = pd.Timestamp("2025-12-31")


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


def read_fred(path: Path, value_name: str) -> pd.DataFrame:
    x = pd.read_csv(path)
    if "DATE" in x.columns:
        date_col = "DATE"
    elif "date" in x.columns:
        date_col = "date"
    elif "observation_date" in x.columns:
        date_col = "observation_date"
    else:
        raise RuntimeError(f"cannot resolve FRED date column in {path}")
    if value_name not in x.columns:
        candidates = [c for c in x.columns if c != date_col]
        if len(candidates) != 1:
            raise RuntimeError(f"cannot resolve {value_name} in {path}")
        x = x.rename(columns={candidates[0]: value_name})
    x["date"] = pd.to_datetime(x[date_col], errors="raise").dt.normalize()
    x[value_name] = pd.to_numeric(x[value_name], errors="coerce")
    return x[["date", value_name]].drop_duplicates("date", keep="last").sort_values("date")


def add_us_complete_clock(panel: pd.DataFrame, nasdaq: pd.DataFrame, vix: pd.DataFrame) -> pd.DataFrame:
    us = nasdaq.merge(vix, on="date", how="outer").sort_values("date").reset_index(drop=True)
    joint = us.dropna(subset=["NASDAQCOM", "VIXCLS"]).copy()
    df = panel.sort_values("trading_day").reset_index(drop=True).copy()
    df["previous_china_day"] = df["trading_day"].shift(1)
    dates = joint["date"].to_numpy(dtype="datetime64[ns]")
    nas = joint["NASDAQCOM"].to_numpy(float)
    vx = joint["VIXCLS"].to_numpy(float)
    target = df["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev = df["previous_china_day"].to_numpy(dtype="datetime64[ns]")
    end_idx = np.searchsorted(dates, target, side="left") - 1
    start_idx = np.full(len(df), -1, dtype=int)
    valid_prev = df["previous_china_day"].notna().to_numpy()
    start_idx[valid_prev] = np.searchsorted(dates, prev[valid_prev], side="left") - 1
    valid = valid_prev & (start_idx >= 0) & (end_idx >= start_idx)
    positive = valid & (end_idx > start_idx) & (end_idx >= 1)
    zero = valid & (end_idx == start_idx)
    nas_extra = np.full(len(df), np.nan)
    vix_extra = np.full(len(df), np.nan)
    nas_extra[zero] = 0.0
    vix_extra[zero] = 0.0
    nas_cum = np.full(len(df), np.nan)
    vix_cum = np.full(len(df), np.nan)
    nas_daily = np.full(len(df), np.nan)
    vix_daily = np.full(len(df), np.nan)
    nas_cum[positive] = nas[end_idx[positive]] / nas[start_idx[positive]] - 1.0
    vix_cum[positive] = vx[end_idx[positive]] / vx[start_idx[positive]] - 1.0
    nas_daily[positive] = nas[end_idx[positive]] / nas[end_idx[positive] - 1] - 1.0
    vix_daily[positive] = vx[end_idx[positive]] / vx[end_idx[positive] - 1] - 1.0
    nas_extra[positive] = nas_cum[positive] - nas_daily[positive]
    vix_extra[positive] = vix_cum[positive] - vix_daily[positive]
    df["us_nasdaq_closure_extra"] = nas_extra
    df["us_vix_closure_extra"] = vix_extra
    return df


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
    if np.any(dates[end_idx[valid]] >= target[valid]):
        raise RuntimeError("HKMA target-date leakage")
    out["hkma_usdcny_closure_return"] = ret
    return out


def hhmmss(values: pd.Series) -> pd.Series:
    out = pd.to_numeric(values, errors="raise").round().astype("int64")
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
        clock_ok &= bool((hhmmss(out.loc[havail, "holiday_end_time"]) < 92500).all())
    if oavail.any():
        clock_ok &= bool((hhmmss(out.loc[oavail, "ordinary_end_time"]) < 91500).all())
    out.loc[~holiday, "a50_holiday_closure_return"] = 0.0
    out.loc[holiday, "a50_ordinary_preauction_closure_return"] = 0.0
    bb = out["trading_day"].between(BB_START, BB_END)
    ordinary_bb = bb & ~holiday
    coverage = float((oavail & bb).sum() / ordinary_bb.sum()) if ordinary_bb.any() else 0.0
    out["a50_common_available"] = havail | oavail
    return out, coverage, clock_ok


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray]:
    xtr = train[features].apply(pd.to_numeric, errors="coerce")
    ytr = pd.to_numeric(train["gap"], errors="coerce")
    xte = test[features].apply(pd.to_numeric, errors="coerce")
    yte = pd.to_numeric(test["gap"], errors="coerce")
    mtr = xtr.notna().all(axis=1) & ytr.notna()
    mte = xte.notna().all(axis=1) & yte.notna()
    if not mtr.any() or not mte.all():
        raise RuntimeError("frozen common-sample feature matrix is incomplete")
    pipe = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
    pipe.fit(xtr.loc[mtr], ytr.loc[mtr])
    return yte.to_numpy(float), pipe.predict(xte)


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    return {
        "r2": float(r2_score(y, p)),
        "sse": float(np.sum((y - p) ** 2)),
        "ic": corr(y, p),
        "sign": float(np.mean((p >= 0) == (y >= 0))),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--nasdaq", type=Path, required=True)
    ap.add_argument("--vix", type=Path, required=True)
    ap.add_argument("--hkma", type=Path, required=True)
    ap.add_argument("--holiday-a50", type=Path, required=True)
    ap.add_argument("--ordinary-a50", type=Path, required=True)
    ap.add_argument("--source-manifest", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    required_assertions = [
        "same_contract_all_events", "no_future_volume_or_oi_selection",
        "no_mid_window_roll", "no_forward_fill_or_interpolation",
        "blackbox_not_used_for_fit_or_rule_selection",
    ]
    source_ok = all(manifest.get("assertions", {}).get(k) is True for k in required_assertions)

    panel = pd.read_parquet(args.panel).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    needed = set(BASE_FEATURES + ["trading_day", "gap"])
    if not needed.issubset(panel.columns):
        raise RuntimeError(f"panel missing frozen columns: {sorted(needed - set(panel.columns))}")
    df = add_us_complete_clock(panel, read_fred(args.nasdaq, "NASDAQCOM"), read_fred(args.vix, "VIXCLS"))
    df = add_hkma(df, args.hkma)
    df, ordinary_coverage, clocks_ok = attach_a50(df, args.holiday_a50, args.ordinary_a50)

    common = df["a50_common_available"]
    train = df.loc[common & df["trading_day"].le(TRAIN_END)].copy()
    bb = df.loc[common & df["trading_day"].between(BB_START, BB_END)].copy()
    if train.empty or bb.empty:
        decision = "INSUFFICIENT"
    else:
        y5, p5 = fit_predict(train, bb, V5_FEATURES)
        y6, p6 = fit_predict(train, bb, V6_FEATURES)
        if not np.array_equal(y5, y6):
            raise RuntimeError("V5A/V6A BLACKBOX common sample misaligned")
        m5, m6 = metrics(y5, p5), metrics(y6, p6)
        holiday = pd.to_numeric(bb["holiday_reopen"], errors="coerce").fillna(0).ne(0).to_numpy()
        ordinary = ~holiday
        if not holiday.any() or not ordinary.any():
            decision = "INSUFFICIENT"
        else:
            mo5, mo6 = metrics(y5[ordinary], p5[ordinary]), metrics(y6[ordinary], p6[ordinary])
            mh5, mh6 = metrics(y5[holiday], p5[holiday]), metrics(y6[holiday], p6[holiday])
            annual_sse = 0
            annual_ic = 0
            years = bb["trading_day"].dt.year.to_numpy()
            for year in range(2021, 2026):
                mask = years == year
                if not mask.any():
                    continue
                a5, a6 = metrics(y5[mask], p5[mask]), metrics(y6[mask], p6[mask])
                annual_sse += int(a6["sse"] < a5["sse"])
                annual_ic += int(a6["ic"] >= a5["ic"])
            integrity_ok = source_ok and clocks_ok
            coverage_ok = ordinary_coverage >= 0.90
            if not integrity_ok or not coverage_ok:
                decision = "INSUFFICIENT"
            else:
                gates = [
                    m6["r2"] > m5["r2"],
                    m6["sse"] < m5["sse"],
                    m6["ic"] > m5["ic"],
                    m6["sign"] >= m5["sign"] - 0.01,
                    mo6["sse"] < mo5["sse"],
                    mo6["ic"] >= mo5["ic"],
                    mo6["sign"] >= mo5["sign"] - 0.01,
                    annual_sse >= 3,
                    annual_ic >= 3,
                    mh6["sse"] <= mh5["sse"] + 1e-12,
                ]
                decision = "PASS" if all(gates) else "FAIL"

    protocol_sha = sha256(args.protocol)
    source_manifest_sha = sha256(args.source_manifest)
    query_payload = {
        "candidate": "V6A_plus_ordinary_A50_preauction_closure",
        "comparator": "V5A_common_sample_comparator",
        "blackbox_window": "2021-01-01..2025-12-31",
        "protocol_sha256": protocol_sha,
        "source_manifest_sha256": source_manifest_sha,
    }
    query_id = hashlib.sha256(json.dumps(query_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "overnight_v6a_reusable_blackbox_receipt@1.0",
        "query_id": query_id,
        "candidate": query_payload["candidate"],
        "decision": decision,
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "protocol_sha256": protocol_sha,
        "source_manifest_sha256": source_manifest_sha,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
