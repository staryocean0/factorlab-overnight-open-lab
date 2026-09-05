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
PREREG_PATH = ROOT / "docs/governance/global_spillover_v1_preregistration.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v1_results.json"


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
    ).dropna(subset=["us_date"])
    # FRED market series may contain missing observations; keep only rows with both values.
    out = out.dropna(subset=["nasdaq_level", "vix_level"]).sort_values("us_date")
    out = out.drop_duplicates("us_date", keep="last").reset_index(drop=True)
    return out


def _add_unabsorbed_us(panel: pd.DataFrame, us: pd.DataFrame) -> pd.DataFrame:
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
    nas_cum = np.full(len(df), np.nan, dtype=float)
    vix_cum = np.full(len(df), np.nan, dtype=float)
    nas_cum[valid] = nasdaq[end_idx[valid]] / nasdaq[start_idx[valid]] - 1.0
    vix_cum[valid] = vix[end_idx[valid]] / vix[start_idx[valid]] - 1.0

    df["us_nasdaq_unabsorbed_cum"] = nas_cum
    df["us_vix_unabsorbed_cum"] = vix_cum
    df["_us_start_date"] = pd.NaT
    df["_us_end_date"] = pd.NaT
    df.loc[valid, "_us_start_date"] = pd.to_datetime(us_dates[start_idx[valid]])
    df.loc[valid, "_us_end_date"] = pd.to_datetime(us_dates[end_idx[valid]])

    # Hard causal guards: every endpoint must precede its China information boundary.
    v = df["_us_end_date"].notna()
    if not bool((df.loc[v, "_us_end_date"] < df.loc[v, "trading_day"]).all()):
        raise AssertionError("US end date is not strictly before target China day")
    v = df["_us_start_date"].notna() & df["previous_china_day"].notna()
    if not bool((df.loc[v, "_us_start_date"] < df.loc[v, "previous_china_day"]).all()):
        raise AssertionError("US start date is not strictly before previous China day")

    return df


def _add_mechanism_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    us_ret = pd.to_numeric(out["us_nasdaq"], errors="coerce")
    vix_chg = pd.to_numeric(out["us_vix_chg"], errors="coerce")
    rvol20 = pd.to_numeric(out["rvol20"], errors="coerce")
    prev_daytime = pd.to_numeric(out["prev_daytime"], errors="coerce")

    out["us_nasdaq_pos"] = us_ret.clip(lower=0.0)
    out["us_nasdaq_neg"] = us_ret.clip(upper=0.0)
    out["us_nasdaq_neg_x_vix_up"] = out["us_nasdaq_neg"] * (vix_chg > 0).astype(float)
    out["us_nasdaq_x_rvol20"] = us_ret * rvol20
    out["us_nasdaq_x_prev_day_down"] = us_ret * (prev_daytime < 0).astype(float)
    return out


def _evaluate(df: pd.DataFrame, features: list[str]) -> dict:
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

    hold_rows = hold.loc[m_te, ["trading_day"]].copy()
    hold_rows["y"] = y
    hold_rows["pred"] = pred

    by_year: dict[str, dict[str, float]] = {}
    for year, g in hold_rows.groupby(hold_rows["trading_day"].dt.year):
        yy = g["y"].to_numpy(dtype=float)
        pp = g["pred"].to_numpy(dtype=float)
        by_year[str(int(year))] = {
            "n": int(len(g)),
            "ic": _corr(yy, pp),
            "sign_hit": float(np.mean((pp >= 0) == (yy >= 0))),
        }

    scaler: StandardScaler = pipe.named_steps["sc"]
    model: Ridge = pipe.named_steps["m"]
    # Ridge coefficients are in standardized feature coordinates because scaling precedes the model.
    coefficients = {f: float(c) for f, c in zip(features, model.coef_, strict=True)}

    return {
        "n_train": int(m_tr.sum()),
        "n_holdout": int(m_te.sum()),
        "holdout_ic": _corr(y, pred),
        "holdout_sign_hit": float(np.mean((pred >= 0) == (y >= 0))),
        "holdout_r2": float(r2_score(y, pred)),
        "year_diagnostics": by_year,
        "standardized_coefficients": coefficients,
    }


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text())
    prereg = json.loads(PREREG_PATH.read_text())
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 market row detected")

    us = _load_us()
    if us["us_date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 US row detected")

    df = _add_mechanism_features(_add_unabsorbed_us(panel, us))
    base = list(baseline["features"])
    candidate_features = {
        "C0_frozen_baseline": base,
        "C1_unabsorbed_us_closure_accrual": base + [
            "us_nasdaq_unabsorbed_cum", "us_vix_unabsorbed_cum"
        ],
        "C2_us_asymmetry": base + [
            "us_nasdaq_pos", "us_nasdaq_neg", "us_nasdaq_neg_x_vix_up"
        ],
        "C3_us_state_dependence": base + [
            "us_nasdaq_x_rvol20", "us_nasdaq_x_prev_day_down"
        ],
        "C4_bounded_combination": base + [
            "us_nasdaq_unabsorbed_cum", "us_vix_unabsorbed_cum",
            "us_nasdaq_pos", "us_nasdaq_neg", "us_nasdaq_neg_x_vix_up",
            "us_nasdaq_x_rvol20", "us_nasdaq_x_prev_day_down"
        ],
    }
    prereg_ids = [c["id"] for c in prereg["candidate_family"]]
    if list(candidate_features) != prereg_ids:
        raise AssertionError("candidate family differs from preregistration")

    results = {cid: _evaluate(df, features) for cid, features in candidate_features.items()}
    c0 = results["C0_frozen_baseline"]
    receipt_ic = float(baseline["metrics"]["ridge_ic"])
    receipt_sign = float(baseline["metrics"]["ridge_sign_hit"])
    if abs(c0["holdout_ic"] - receipt_ic) > 1e-6:
        raise AssertionError(("frozen baseline IC replay mismatch", c0["holdout_ic"], receipt_ic))
    if abs(c0["holdout_sign_hit"] - receipt_sign) > 1e-12:
        raise AssertionError(("frozen baseline sign replay mismatch", c0["holdout_sign_hit"], receipt_sign))

    hold = df.loc[df["trading_day"] >= pd.Timestamp("2019-01-01")].copy()
    y = pd.to_numeric(hold["gap"], errors="coerce")
    n = pd.to_numeric(hold["us_nasdaq"], errors="coerce")
    m = y.notna() & n.notna()
    nasdaq_single_ic = _corr(y.loc[m].to_numpy(dtype=float), n.loc[m].to_numpy(dtype=float))

    for cid, r in results.items():
        r["delta_ic_vs_frozen_ridge"] = float(r["holdout_ic"] - receipt_ic)
        r["delta_sign_hit_vs_frozen_ridge"] = float(r["holdout_sign_hit"] - receipt_sign)
        r["delta_ic_vs_us_nasdaq_single_variable"] = float(
            r["holdout_ic"] - float(baseline["metrics"]["us_nasdaq_ic"])
        )

    nonholiday = df.loc[
        (pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0) == 0)
        & df["us_nasdaq_unabsorbed_cum"].notna()
        & pd.to_numeric(df["us_nasdaq"], errors="coerce").notna()
    ]
    proxy_corr = _corr(
        pd.to_numeric(nonholiday["us_nasdaq"], errors="coerce").to_numpy(dtype=float),
        nonholiday["us_nasdaq_unabsorbed_cum"].to_numpy(dtype=float),
    )

    report = {
        "schema_id": "overnight_open_global_spillover_results@1.0",
        "preregistration": "docs/governance/global_spillover_v1_preregistration.json",
        "data_max_china_day": str(df["trading_day"].max().date()),
        "data_max_us_day": str(us["us_date"].max().date()),
        "multiplicity_attempts": len(results),
        "receipt_replay_pass": True,
        "references": {
            "frozen_ridge_ic": receipt_ic,
            "frozen_ridge_sign_hit": receipt_sign,
            "receipt_us_nasdaq_ic": float(baseline["metrics"]["us_nasdaq_ic"]),
            "recomputed_us_nasdaq_ic": nasdaq_single_ic,
            "majority_down_hit": float(baseline["metrics"]["majority_down_hit"]),
        },
        "causal_diagnostics": {
            "us_end_strictly_before_china_target": True,
            "us_start_strictly_before_previous_china_day": True,
            "nonholiday_corr_panel_us_vs_unabsorbed_cum": proxy_corr,
        },
        "candidates": results,
        "authority": {"fresh_oos": False, "production": False, "registry_mutation": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
