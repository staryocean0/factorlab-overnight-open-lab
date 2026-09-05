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
PREREG_PATH = ROOT / "docs/governance/global_spillover_v2_mechanism_preregistration.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v2_mechanism_results.json"


def _corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.nanstd(a) == 0 or np.nanstd(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def _find_col(columns: list[str], exact: tuple[str, ...], contains: tuple[str, ...]) -> str:
    lower = {str(c).lower(): str(c) for c in columns}
    for name in exact:
        if name.lower() in lower:
            return lower[name.lower()]
    for c in columns:
        lc = str(c).lower()
        if any(token.lower() in lc for token in contains):
            return str(c)
    raise KeyError(f"cannot find required column among {columns}; exact={exact}, contains={contains}")


def _load_us() -> pd.DataFrame:
    us = pd.read_parquet(US_PATH).copy()
    cols = [str(c) for c in us.columns]
    date_col = _find_col(cols, ("date", "trading_day"), ("date", "day"))
    nasdaq_col = _find_col(cols, ("NASDAQCOM", "nasdaq"), ("nasdaq",))
    vix_col = _find_col(cols, ("VIXCLS", "vix"), ("vix",))
    out = pd.DataFrame(
        {
            "us_date": pd.to_datetime(us[date_col], errors="coerce").dt.normalize(),
            "nasdaq_level": pd.to_numeric(us[nasdaq_col], errors="coerce"),
            "vix_level": pd.to_numeric(us[vix_col], errors="coerce"),
        }
    ).dropna(subset=["us_date", "nasdaq_level", "vix_level"])
    return out.sort_values("us_date").drop_duplicates("us_date", keep="last").reset_index(drop=True)


def _add_cumulative_windows(panel: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy().sort_values("trading_day").reset_index(drop=True)
    df["previous_china_day"] = df["trading_day"].shift(1)

    us_dates = us["us_date"].to_numpy(dtype="datetime64[ns]")
    nasdaq = us["nasdaq_level"].to_numpy(dtype=float)
    vix = us["vix_level"].to_numpy(dtype=float)
    target_dates = df["trading_day"].to_numpy(dtype="datetime64[ns]")
    prev_dates = df["previous_china_day"].to_numpy(dtype="datetime64[ns]")

    end_idx = np.searchsorted(us_dates, target_dates, side="left") - 1
    start_idx = np.full(len(df), -1, dtype=int)
    valid_prev = ~pd.isna(df["previous_china_day"]).to_numpy()
    start_idx[valid_prev] = np.searchsorted(us_dates, prev_dates[valid_prev], side="left") - 1
    valid = valid_prev & (start_idx >= 0) & (end_idx >= 0) & (end_idx >= start_idx)

    cum_nas = np.full(len(df), np.nan, dtype=float)
    cum_vix = np.full(len(df), np.nan, dtype=float)
    intervals = np.full(len(df), np.nan, dtype=float)
    cum_nas[valid] = nasdaq[end_idx[valid]] / nasdaq[start_idx[valid]] - 1.0
    cum_vix[valid] = vix[end_idx[valid]] / vix[start_idx[valid]] - 1.0
    intervals[valid] = end_idx[valid] - start_idx[valid]

    df["us_nasdaq_unabsorbed_cum"] = cum_nas
    df["us_vix_unabsorbed_cum"] = cum_vix
    df["us_session_intervals"] = intervals
    df["_us_start_date"] = pd.NaT
    df["_us_end_date"] = pd.NaT
    df.loc[valid, "_us_start_date"] = pd.to_datetime(us_dates[start_idx[valid]])
    df.loc[valid, "_us_end_date"] = pd.to_datetime(us_dates[end_idx[valid]])

    v = df["_us_end_date"].notna()
    if not bool((df.loc[v, "_us_end_date"] < df.loc[v, "trading_day"]).all()):
        raise AssertionError("US end date is not strictly before target China day")
    v = df["_us_start_date"].notna() & df["previous_china_day"].notna()
    if not bool((df.loc[v, "_us_start_date"] < df.loc[v, "previous_china_day"]).all()):
        raise AssertionError("US start date is not strictly before previous China day")
    return df


def _add_diagnostic_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    nas = pd.to_numeric(out["us_nasdaq"], errors="coerce")
    vix = pd.to_numeric(out["us_vix_chg"], errors="coerce")
    holiday = pd.to_numeric(out["holiday_reopen"], errors="coerce").fillna(0.0).eq(1.0)
    multi = pd.to_numeric(out["us_session_intervals"], errors="coerce").ge(2.0)

    out["us_nasdaq_duplicate"] = nas
    out["us_vix_chg_duplicate"] = vix
    out["us_nasdaq_unabsorbed_extra"] = pd.to_numeric(out["us_nasdaq_unabsorbed_cum"], errors="coerce") - nas
    out["us_vix_unabsorbed_extra"] = pd.to_numeric(out["us_vix_unabsorbed_cum"], errors="coerce") - vix
    out["extra_nasdaq_holiday"] = out["us_nasdaq_unabsorbed_extra"].where(holiday, 0.0)
    out["extra_vix_holiday"] = out["us_vix_unabsorbed_extra"].where(holiday, 0.0)
    nonholiday_multi = (~holiday) & multi
    out["extra_nasdaq_nonholiday_multi"] = out["us_nasdaq_unabsorbed_extra"].where(nonholiday_multi, 0.0)
    out["extra_vix_nonholiday_multi"] = out["us_vix_unabsorbed_extra"].where(nonholiday_multi, 0.0)

    if not np.allclose(out["us_nasdaq_duplicate"], nas, equal_nan=True):
        raise AssertionError("NASDAQ duplicate placebo is not exact")
    if not np.allclose(out["us_vix_chg_duplicate"], vix, equal_nan=True):
        raise AssertionError("VIX duplicate placebo is not exact")
    return out


def _evaluate(df: pd.DataFrame, features: list[str]) -> tuple[dict, pd.Series]:
    train = df.loc[df["trading_day"] <= pd.Timestamp("2018-12-31")]
    hold = df.loc[df["trading_day"] >= pd.Timestamp("2019-01-01")]
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
    pred_s = pd.Series(pred, index=hold.loc[m_te].index, dtype=float)

    by_year: dict[str, dict[str, float]] = {}
    tmp = hold.loc[m_te, ["trading_day"]].copy()
    tmp["y"] = y
    tmp["pred"] = pred
    for year, g in tmp.groupby(tmp["trading_day"].dt.year):
        yy = g["y"].to_numpy(dtype=float)
        pp = g["pred"].to_numpy(dtype=float)
        by_year[str(int(year))] = {
            "n": int(len(g)),
            "ic": _corr(yy, pp),
            "sign_hit": float(np.mean((pp >= 0) == (yy >= 0))),
        }

    model: Ridge = pipe.named_steps["m"]
    coeff = {f: float(c) for f, c in zip(features, model.coef_, strict=True)}
    return (
        {
            "n_train": int(m_tr.sum()),
            "n_holdout": int(m_te.sum()),
            "holdout_ic": _corr(y, pred),
            "holdout_sign_hit": float(np.mean((pred >= 0) == (y >= 0))),
            "holdout_r2": float(r2_score(y, pred)),
            "year_diagnostics": by_year,
            "standardized_coefficients": coeff,
        },
        pred_s,
    )


def _subset_summary(df: pd.DataFrame, idx: pd.Index, contribution: pd.Series, pred: pd.Series) -> dict:
    rows = df.loc[idx].copy()
    rows["contribution"] = contribution.loc[idx]
    rows["pred"] = pred.loc[idx]
    rows["y"] = pd.to_numeric(rows["gap"], errors="coerce")

    holiday = pd.to_numeric(rows["holiday_reopen"], errors="coerce").fillna(0).eq(1)
    intervals = pd.to_numeric(rows["us_session_intervals"], errors="coerce")
    ordinary = rows["y"].abs().le(0.003)
    masks = {
        "holiday_reopen": holiday,
        "nonholiday": ~holiday,
        "single_US_session": intervals.eq(1),
        "multi_US_session": intervals.ge(2),
        "ordinary_gap_le_30bp": ordinary,
        "tail_gap_gt_30bp": ~ordinary,
        "year_2019": rows["trading_day"].dt.year.eq(2019),
        "year_2020": rows["trading_day"].dt.year.eq(2020),
    }
    out: dict[str, dict[str, float]] = {}
    for name, mask in masks.items():
        g = rows.loc[mask]
        yy = g["y"].to_numpy(dtype=float)
        pp = g["pred"].to_numpy(dtype=float)
        out[name] = {
            "n": int(len(g)),
            "sse_improvement_vs_C0": float(g["contribution"].sum()),
            "mean_sse_improvement_vs_C0": float(g["contribution"].mean()) if len(g) else float("nan"),
            "candidate_ic": _corr(yy, pp),
            "candidate_sign_hit": float(np.mean((pp >= 0) == (yy >= 0))) if len(g) else float("nan"),
        }
    return out


def _influence(contribution: pd.Series) -> dict:
    positive = contribution.loc[contribution > 0].sort_values(ascending=False)
    denom = float(positive.sum())
    def share(k: int) -> float:
        if denom <= 0:
            return float("nan")
        return float(positive.iloc[:k].sum() / denom)
    return {
        "net_sse_improvement": float(contribution.sum()),
        "positive_sse_improvement": denom,
        "negative_sse_deterioration": float(contribution.loc[contribution < 0].sum()),
        "top_1_positive_share": share(1),
        "top_5_positive_share": share(5),
        "top_10_positive_share": share(10),
    }


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text())
    prereg = json.loads(PREREG_PATH.read_text())
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    us = _load_us()
    if us["us_date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 US row detected")

    df = _add_diagnostic_features(_add_cumulative_windows(panel, us))
    base = list(baseline["features"])
    candidate_features = {
        "C0_frozen_baseline": base,
        "C1_v1_cumulative_replay": base + ["us_nasdaq_unabsorbed_cum", "us_vix_unabsorbed_cum"],
        "C2_exact_duplicate_placebo": base + ["us_nasdaq_duplicate", "us_vix_chg_duplicate"],
        "C3_incremental_information_only": base + ["us_nasdaq_unabsorbed_extra", "us_vix_unabsorbed_extra"],
        "C4_incremental_nasdaq_only": base + ["us_nasdaq_unabsorbed_extra"],
        "C5_incremental_vix_only": base + ["us_vix_unabsorbed_extra"],
        "C6_incremental_holiday_only": base + ["extra_nasdaq_holiday", "extra_vix_holiday"],
        "C7_incremental_nonholiday_multisession_only": base + ["extra_nasdaq_nonholiday_multi", "extra_vix_nonholiday_multi"],
    }
    prereg_ids = [x["id"] for x in prereg["candidate_family"]]
    if list(candidate_features) != prereg_ids or len(candidate_features) != int(prereg["multiplicity_attempts"]):
        raise AssertionError("candidate family differs from frozen v2 preregistration")

    metrics: dict[str, dict] = {}
    predictions: dict[str, pd.Series] = {}
    for cid, features in candidate_features.items():
        metrics[cid], predictions[cid] = _evaluate(df, features)

    receipt_ic = float(baseline["metrics"]["ridge_ic"])
    receipt_sign = float(baseline["metrics"]["ridge_sign_hit"])
    c0 = metrics["C0_frozen_baseline"]
    if abs(c0["holdout_ic"] - receipt_ic) > 1e-6 or abs(c0["holdout_sign_hit"] - receipt_sign) > 1e-12:
        raise AssertionError("frozen baseline replay mismatch")

    v1_expected = 0.49135678663435955
    if abs(metrics["C1_v1_cumulative_replay"]["holdout_ic"] - v1_expected) > 1e-6:
        raise AssertionError("v1 C1 replay mismatch")

    for cid, r in metrics.items():
        r["delta_ic_vs_C0"] = float(r["holdout_ic"] - c0["holdout_ic"])
        r["delta_sign_hit_vs_C0"] = float(r["holdout_sign_hit"] - c0["holdout_sign_hit"])

    y_hold = pd.to_numeric(df.loc[df["trading_day"] >= pd.Timestamp("2019-01-01"), "gap"], errors="coerce")
    base_pred = predictions["C0_frozen_baseline"]
    decompositions: dict[str, dict] = {}
    for cid, pred in predictions.items():
        if cid == "C0_frozen_baseline":
            continue
        idx = base_pred.index.intersection(pred.index).intersection(y_hold.dropna().index)
        y = y_hold.loc[idx]
        contribution = (y - base_pred.loc[idx]) ** 2 - (y - pred.loc[idx]) ** 2
        decompositions[cid] = {
            "subsets": _subset_summary(df, idx, contribution, pred),
            "influence": _influence(contribution),
        }

    hold = df.loc[df["trading_day"] >= pd.Timestamp("2019-01-01")].copy()
    intervals = pd.to_numeric(hold["us_session_intervals"], errors="coerce")
    holiday = pd.to_numeric(hold["holiday_reopen"], errors="coerce").fillna(0).eq(1)
    interval_counts = {str(int(k)): int(v) for k, v in intervals.dropna().value_counts().sort_index().items()}
    extra_nas = pd.to_numeric(hold["us_nasdaq_unabsorbed_extra"], errors="coerce")
    extra_vix = pd.to_numeric(hold["us_vix_unabsorbed_extra"], errors="coerce")
    single = intervals.eq(1) & extra_nas.notna() & extra_vix.notna()

    tol = 1e-12
    c2_gain = metrics["C2_exact_duplicate_placebo"]["delta_ic_vs_C0"]
    c3_gain = metrics["C3_incremental_information_only"]["delta_ic_vs_C0"]
    mechanism_supported = bool(c3_gain > tol)
    placebo_present = bool(c2_gain > tol)
    if mechanism_supported:
        scientific_status = "genuine_cumulative_information_supported_on_consumed_internal_holdout"
    else:
        scientific_status = "v1_cumulative_interpretation_not_supported_after_incremental_information_control"

    report = {
        "schema_id": "overnight_open_global_spillover_mechanism_results@2.0",
        "preregistration": str(PREREG_PATH.relative_to(ROOT)),
        "parent_receipt": "docs/governance/global_spillover_v1_receipt.json",
        "data_max_china_day": str(df["trading_day"].max().date()),
        "data_max_us_day": str(us["us_date"].max().date()),
        "multiplicity_attempts": len(candidate_features),
        "hard_checks": {
            "post_2020_rows_read": 0,
            "baseline_replay_pass": True,
            "v1_C1_replay_pass": True,
            "duplicate_placebo_exact": True,
            "us_end_strictly_before_target": True,
            "us_start_strictly_before_previous_china_day": True,
        },
        "window_diagnostics": {
            "holdout_interval_counts": interval_counts,
            "holdout_holiday_reopen_n": int(holiday.sum()),
            "holdout_nonholiday_multi_US_session_n": int(((~holiday) & intervals.ge(2)).sum()),
            "holdout_extra_nasdaq_nonzero_n": int((extra_nas.abs() > 1e-12).sum()),
            "holdout_extra_vix_nonzero_n": int((extra_vix.abs() > 1e-12).sum()),
            "single_session_extra_nasdaq_max_abs": float(extra_nas.loc[single].abs().max()),
            "single_session_extra_vix_max_abs": float(extra_vix.loc[single].abs().max()),
        },
        "candidates": metrics,
        "decomposition_vs_C0": decompositions,
        "adjudication": {
            "duplicate_regularization_artifact_present": placebo_present,
            "genuine_incremental_information_mechanism_supported": mechanism_supported,
            "C2_placebo_delta_ic": float(c2_gain),
            "C3_incremental_delta_ic": float(c3_gain),
            "scientific_status": scientific_status,
            "baseline_replacement": False,
        },
        "authority": {
            "fresh_oos": False,
            "baseline_replacement": False,
            "production": False,
            "registry_mutation": False,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
