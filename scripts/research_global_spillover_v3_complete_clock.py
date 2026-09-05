#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/governance/baseline_receipt.json"
PREREG_PATH = ROOT / "docs/governance/global_spillover_v3_complete_us_data_preregistration.json"
MANIFEST_PATH = ROOT / "docs/governance/external_us_fred_2014_2020_manifest.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v3_complete_clock_results.json"


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.nanstd(a) == 0 or np.nanstd(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _load_us() -> pd.DataFrame:
    us = pd.read_parquet(US_PATH).copy()
    us["date"] = pd.to_datetime(us["date"], errors="raise").dt.normalize()
    us["NASDAQCOM"] = pd.to_numeric(us["NASDAQCOM"], errors="coerce")
    us["VIXCLS"] = pd.to_numeric(us["VIXCLS"], errors="coerce")
    if us["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 US row detected")
    return us.sort_values("date").reset_index(drop=True)


def add_complete_clock_features(panel: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy().sort_values("trading_day").reset_index(drop=True)
    df["previous_china_day"] = df["trading_day"].shift(1)
    joint = us.dropna(subset=["NASDAQCOM", "VIXCLS"]).copy().sort_values("date").reset_index(drop=True)
    us_dates = joint["date"].to_numpy(dtype="datetime64[ns]")
    nas = joint["NASDAQCOM"].to_numpy(dtype=float)
    vix = joint["VIXCLS"].to_numpy(dtype=float)
    target = df["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev = df["previous_china_day"].to_numpy(dtype="datetime64[ns]")
    end_idx = np.searchsorted(us_dates, target, side="left") - 1
    start_idx = np.full(len(df), -1, dtype=int)
    valid_prev = df["previous_china_day"].notna().to_numpy()
    start_idx[valid_prev] = np.searchsorted(us_dates, prev[valid_prev], side="left") - 1

    clock_valid = valid_prev & (start_idx >= 0) & (end_idx >= start_idx)
    positive = clock_valid & (end_idx > start_idx) & (end_idx >= 1)
    zero = clock_valid & (end_idx == start_idx)

    interval_count = np.full(len(df), np.nan, dtype=float)
    nas_cum = np.full(len(df), np.nan, dtype=float)
    vix_cum = np.full(len(df), np.nan, dtype=float)
    nas_daily = np.full(len(df), np.nan, dtype=float)
    vix_daily = np.full(len(df), np.nan, dtype=float)
    nas_extra = np.full(len(df), np.nan, dtype=float)
    vix_extra = np.full(len(df), np.nan, dtype=float)

    interval_count[clock_valid] = end_idx[clock_valid] - start_idx[clock_valid]
    # If no new U.S. observed close arrived between two China sessions, there is
    # exactly zero new foreign information by this closure-accrual definition.
    nas_cum[zero] = 0.0
    vix_cum[zero] = 0.0
    nas_extra[zero] = 0.0
    vix_extra[zero] = 0.0

    nas_cum[positive] = nas[end_idx[positive]] / nas[start_idx[positive]] - 1.0
    vix_cum[positive] = vix[end_idx[positive]] / vix[start_idx[positive]] - 1.0
    nas_daily[positive] = nas[end_idx[positive]] / nas[end_idx[positive] - 1] - 1.0
    vix_daily[positive] = vix[end_idx[positive]] / vix[end_idx[positive] - 1] - 1.0
    nas_extra[positive] = nas_cum[positive] - nas_daily[positive]
    vix_extra[positive] = vix_cum[positive] - vix_daily[positive]

    at_most_one = clock_valid & (interval_count <= 1)
    if np.any(np.abs(nas_extra[at_most_one]) > 1e-12) or np.any(np.abs(vix_extra[at_most_one]) > 1e-12):
        raise AssertionError("closure_extra identity failed for <=1-US-interval rows")

    df["us_interval_count"] = interval_count
    df["us_nasdaq_complete_daily"] = nas_daily
    df["us_vix_complete_daily"] = vix_daily
    df["us_nasdaq_complete_cum"] = nas_cum
    df["us_vix_complete_cum"] = vix_cum
    df["us_nasdaq_closure_extra"] = nas_extra
    df["us_vix_closure_extra"] = vix_extra
    df["us_nasdaq_dup"] = pd.to_numeric(df["us_nasdaq"], errors="coerce")
    df["us_vix_dup"] = pd.to_numeric(df["us_vix_chg"], errors="coerce")
    return df


def _fit_predict(df: pd.DataFrame, features: list[str]) -> tuple[dict, pd.DataFrame]:
    train = df.loc[df["trading_day"] <= pd.Timestamp("2018-12-31")].copy()
    hold = df.loc[(df["trading_day"] >= pd.Timestamp("2019-01-01")) & (df["trading_day"] <= pd.Timestamp("2020-12-31"))].copy()
    x_tr = train[features].apply(pd.to_numeric, errors="coerce")
    y_tr = pd.to_numeric(train["gap"], errors="coerce")
    x_te = hold[features].apply(pd.to_numeric, errors="coerce")
    y_te = pd.to_numeric(hold["gap"], errors="coerce")
    m_tr = x_tr.notna().all(axis=1) & y_tr.notna()
    m_te = x_te.notna().all(axis=1) & y_te.notna()
    pipe = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
    pipe.fit(x_tr.loc[m_tr], y_tr.loc[m_tr])
    pred = pipe.predict(x_te.loc[m_te])
    y = y_te.loc[m_te].to_numpy(dtype=float)
    rows = hold.loc[m_te, ["trading_day", "holiday_reopen", "us_interval_count"]].copy()
    rows["y"] = y
    rows["pred"] = pred
    rows["sse"] = (rows["y"] - rows["pred"]) ** 2
    model: Ridge = pipe.named_steps["m"]
    metrics = {
        "n_train": int(m_tr.sum()),
        "n_holdout": int(m_te.sum()),
        "holdout_ic": _corr(y, pred),
        "holdout_sign_hit": float(np.mean((pred >= 0) == (y >= 0))),
        "holdout_r2": float(r2_score(y, pred)),
        "holdout_sse": float(np.sum((y - pred) ** 2)),
        "standardized_coefficients": {f: float(c) for f, c in zip(features, model.coef_, strict=True)},
        "year_diagnostics": {}
    }
    for year, g in rows.groupby(rows["trading_day"].dt.year):
        metrics["year_diagnostics"][str(int(year))] = {
            "n": int(len(g)),
            "ic": _corr(g["y"].to_numpy(), g["pred"].to_numpy()),
            "sign_hit": float(np.mean((g["pred"] >= 0) == (g["y"] >= 0))),
            "sse": float(g["sse"].sum())
        }
    return metrics, rows


def _subset_compare(c0: pd.DataFrame, cx: pd.DataFrame, mask: pd.Series) -> dict:
    a = c0.loc[mask].copy()
    b = cx.loc[mask].copy()
    if not a["trading_day"].reset_index(drop=True).equals(b["trading_day"].reset_index(drop=True)):
        raise AssertionError("prediction rows misaligned")
    y = a["y"].to_numpy(dtype=float)
    p0 = a["pred"].to_numpy(dtype=float)
    px = b["pred"].to_numpy(dtype=float)
    return {
        "n": int(len(a)),
        "c0_ic": _corr(y, p0),
        "candidate_ic": _corr(y, px),
        "c0_sign_hit": float(np.mean((p0 >= 0) == (y >= 0))) if len(a) else float("nan"),
        "candidate_sign_hit": float(np.mean((px >= 0) == (y >= 0))) if len(a) else float("nan"),
        "c0_sse": float(np.sum((y - p0) ** 2)),
        "candidate_sse": float(np.sum((y - px) ** 2)),
        "candidate_minus_c0_sse_improvement": float(np.sum((y - p0) ** 2) - np.sum((y - px) ** 2))
    }


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text())
    prereg = json.loads(PREREG_PATH.read_text())
    manifest = json.loads(MANIFEST_PATH.read_text())
    if manifest["guards"]["post_2020_rows"] != 0 or manifest["guards"]["forward_fill"]:
        raise AssertionError("external data manifest violates preregistered boundary")
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    df = add_complete_clock_features(panel, _load_us())

    n = pd.to_numeric(df["us_nasdaq"], errors="coerce")
    v = pd.to_numeric(df["us_vix_chg"], errors="coerce")
    nd = pd.to_numeric(df["us_nasdaq_complete_daily"], errors="coerce")
    vd = pd.to_numeric(df["us_vix_complete_daily"], errors="coerce")
    mn = n.notna() & nd.notna()
    mv = v.notna() & vd.notna()
    nas_exact = float(np.mean(np.isclose(n[mn], nd[mn], atol=1e-10, rtol=0)))
    vix_exact = float(np.mean(np.isclose(v[mv], vd[mv], atol=1e-10, rtol=0)))

    base = list(baseline["features"])
    feature_sets = {
        "C0_frozen_baseline": base,
        "P0_exact_duplicate_us_placebo": base + ["us_nasdaq_dup", "us_vix_dup"],
        "C1_complete_clock_closure_extra": base + ["us_nasdaq_closure_extra", "us_vix_closure_extra"]
    }
    if list(feature_sets) != [x["id"] for x in prereg["attempts"]]:
        raise AssertionError("v3 attempt family differs from preregistration")

    metrics: dict[str, dict] = {}
    preds: dict[str, pd.DataFrame] = {}
    for cid, features in feature_sets.items():
        metrics[cid], preds[cid] = _fit_predict(df, features)

    receipt_ic = float(baseline["metrics"]["ridge_ic"])
    receipt_sign = float(baseline["metrics"]["ridge_sign_hit"])
    c0 = metrics["C0_frozen_baseline"]
    if abs(c0["holdout_ic"] - receipt_ic) > 1e-6 or abs(c0["holdout_sign_hit"] - receipt_sign) > 1e-12:
        raise AssertionError("frozen baseline replay mismatch")

    c0p = preds["C0_frozen_baseline"].reset_index(drop=True)
    p0p = preds["P0_exact_duplicate_us_placebo"].reset_index(drop=True)
    c1p = preds["C1_complete_clock_closure_extra"].reset_index(drop=True)
    if not c0p["trading_day"].equals(c1p["trading_day"]) or not c0p["trading_day"].equals(p0p["trading_day"]):
        raise AssertionError("holdout prediction alignment mismatch")

    zero = c0p["us_interval_count"] == 0
    one = c0p["us_interval_count"] == 1
    multi = c0p["us_interval_count"] > 1
    holiday = pd.to_numeric(c0p["holiday_reopen"], errors="coerce").fillna(0) != 0
    subset = {
        "C1": {
            "zero_us_interval": _subset_compare(c0p, c1p, zero),
            "one_us_interval": _subset_compare(c0p, c1p, one),
            "multiple_us_intervals": _subset_compare(c0p, c1p, multi),
            "holiday_reopen": _subset_compare(c0p, c1p, holiday)
        },
        "P0": {
            "zero_us_interval": _subset_compare(c0p, p0p, zero),
            "one_us_interval": _subset_compare(c0p, p0p, one),
            "multiple_us_intervals": _subset_compare(c0p, p0p, multi),
            "holiday_reopen": _subset_compare(c0p, p0p, holiday)
        }
    }

    events = c0p.loc[multi, ["trading_day", "y", "pred"]].copy().rename(columns={"pred": "c0_pred"})
    events["c1_pred"] = c1p.loc[multi, "pred"].to_numpy()
    events["p0_pred"] = p0p.loc[multi, "pred"].to_numpy()
    events["c1_sse_improvement"] = (events["y"] - events["c0_pred"]) ** 2 - (events["y"] - events["c1_pred"]) ** 2
    events["p0_sse_improvement"] = (events["y"] - events["c0_pred"]) ** 2 - (events["y"] - events["p0_pred"]) ** 2
    event_rows = [{
        "trading_day": str(r["trading_day"].date()),
        "gap": float(r["y"]),
        "c1_sse_improvement": float(r["c1_sse_improvement"]),
        "p0_sse_improvement": float(r["p0_sse_improvement"])
    } for _, r in events.sort_values("trading_day").iterrows()]

    c1m = metrics["C1_complete_clock_closure_extra"]
    for r in metrics.values():
        r["delta_ic_vs_c0"] = float(r["holdout_ic"] - c0["holdout_ic"])
        r["delta_sse_vs_c0_improvement"] = float(c0["holdout_sse"] - r["holdout_sse"])

    progression = (
        c1m["holdout_ic"] > c0["holdout_ic"]
        and subset["C1"]["multiple_us_intervals"]["candidate_minus_c0_sse_improvement"] > 0
        and subset["C1"]["one_us_interval"]["candidate_minus_c0_sse_improvement"] <= max(1e-12, abs(subset["C1"]["multiple_us_intervals"]["candidate_minus_c0_sse_improvement"]) * 0.10)
        and subset["C1"]["multiple_us_intervals"]["candidate_minus_c0_sse_improvement"] > subset["P0"]["multiple_us_intervals"]["candidate_minus_c0_sse_improvement"]
    )

    report = {
        "schema_id": "overnight_open_global_spillover_v3_complete_clock_results@1.1",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "external_manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_internal"},
        "clock_reconstruction": {
            "nasdaq_panel_daily_exact_share": nas_exact,
            "vix_panel_daily_exact_share": vix_exact,
            "zero_interval_n": int(zero.sum()),
            "one_interval_n": int(one.sum()),
            "multiple_interval_n": int(multi.sum()),
            "holiday_reopen_n": int(holiday.sum())
        },
        "candidates": metrics,
        "mechanism_subsets": subset,
        "multiple_interval_event_diagnostics": event_rows,
        "adjudication": {
            "C1_progression_rule_pass": bool(progression),
            "placebo_selectable": False,
            "baseline_replacement": False,
            "fresh_oos": False,
            "scientific_status": "progress_to_unseen_controller_confirmation" if progression else "do_not_progress_from_consumed_holdout"
        },
        "authority": {"production": False, "registry_mutation": False, "holiday_runtime_routing": False}
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
