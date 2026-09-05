#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/governance/baseline_receipt.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
US_PATH = ROOT / "data/development/us_nasdaq_vix.parquet"
V1_SCRIPT = ROOT / "scripts/research_global_spillover_v1.py"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v1_clock_mismatch_attribution.json"


def _load_v1_module():
    spec = importlib.util.spec_from_file_location("spillover_v1", V1_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _find_col(columns: list[str], exact: tuple[str, ...], contains: tuple[str, ...]) -> str:
    lower = {str(c).lower(): str(c) for c in columns}
    for name in exact:
        if name.lower() in lower:
            return lower[name.lower()]
    for c in columns:
        lc = str(c).lower()
        if any(token.lower() in lc for token in contains):
            return str(c)
    raise KeyError((columns, exact, contains))


def _load_raw_us() -> pd.DataFrame:
    raw = pd.read_parquet(US_PATH).copy()
    cols = [str(c) for c in raw.columns]
    d = _find_col(cols, ("date", "trading_day"), ("date", "day"))
    n = _find_col(cols, ("NASDAQCOM", "nasdaq"), ("nasdaq",))
    v = _find_col(cols, ("VIXCLS", "vix"), ("vix",))
    return pd.DataFrame({
        "date": pd.to_datetime(raw[d], errors="coerce").dt.normalize(),
        "nasdaq": pd.to_numeric(raw[n], errors="coerce"),
        "vix": pd.to_numeric(raw[v], errors="coerce"),
    }).dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)


def _reconstructed_last_pct(us: pd.DataFrame, col: str, target_days: pd.Series) -> pd.Series:
    s = us.loc[us[col].notna(), ["date", col]].copy().reset_index(drop=True)
    s["pct"] = s[col].pct_change(fill_method=None)
    dates = s["date"].to_numpy(dtype="datetime64[ns]")
    target = target_days.to_numpy(dtype="datetime64[ns]")
    idx = np.searchsorted(dates, target, side="left") - 1
    out = np.full(len(target), np.nan)
    valid = idx >= 1
    out[valid] = s["pct"].to_numpy(dtype=float)[idx[valid]]
    return pd.Series(out, index=target_days.index, dtype=float)


def _fit_predict(df: pd.DataFrame, features: list[str]) -> pd.Series:
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
    return pd.Series(pipe.predict(x_te.loc[m_te]), index=hold.loc[m_te].index, dtype=float)


def _corr(y: pd.Series, p: pd.Series) -> float:
    if len(y) < 3 or y.std() == 0 or p.std() == 0:
        return float("nan")
    return float(np.corrcoef(y.to_numpy(float), p.to_numpy(float))[0, 1])


def _subset_stats(rows: pd.DataFrame) -> dict:
    if len(rows) == 0:
        return {"n": 0}
    return {
        "n": int(len(rows)),
        "c0_ic": _corr(rows["y"], rows["p0"]),
        "c1_ic": _corr(rows["y"], rows["p1"]),
        "c0_sign_hit": float(np.mean((rows["p0"] >= 0) == (rows["y"] >= 0))),
        "c1_sign_hit": float(np.mean((rows["p1"] >= 0) == (rows["y"] >= 0))),
        "sse_c0": float(np.sum((rows["y"] - rows["p0"]) ** 2)),
        "sse_c1": float(np.sum((rows["y"] - rows["p1"]) ** 2)),
        "sse_improvement_c1_vs_c0": float(rows["sse_improvement"].sum()),
        "mean_sse_improvement": float(rows["sse_improvement"].mean()),
    }


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text())
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    raw_us = _load_raw_us()
    if raw_us["date"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 US row detected")

    v1 = _load_v1_module()
    v1_us = v1._load_us()
    df = v1._add_unabsorbed_us(panel, v1_us)
    base = list(baseline["features"])
    c1 = base + ["us_nasdaq_unabsorbed_cum", "us_vix_unabsorbed_cum"]
    p0 = _fit_predict(df, base)
    p1 = _fit_predict(df, c1)
    idx = p0.index.intersection(p1.index)

    nas_recon = _reconstructed_last_pct(raw_us, "nasdaq", panel["trading_day"])
    vix_recon = _reconstructed_last_pct(raw_us, "vix", panel["trading_day"])
    panel_nas = pd.to_numeric(panel["us_nasdaq"], errors="coerce")
    panel_vix = pd.to_numeric(panel["us_vix_chg"], errors="coerce")
    nas_exact = panel_nas.notna() & nas_recon.notna() & ((panel_nas - nas_recon).abs() <= 1e-10)
    vix_exact = panel_vix.notna() & vix_recon.notna() & ((panel_vix - vix_recon).abs() <= 1e-10)
    both_exact = nas_exact & vix_exact

    hold = pd.DataFrame(index=idx)
    hold["trading_day"] = panel.loc[idx, "trading_day"]
    hold["y"] = pd.to_numeric(panel.loc[idx, "gap"], errors="coerce")
    hold["p0"] = p0.loc[idx]
    hold["p1"] = p1.loc[idx]
    hold["nasdaq_exact"] = nas_exact.loc[idx]
    hold["vix_exact"] = vix_exact.loc[idx]
    hold["both_exact"] = both_exact.loc[idx]
    hold["holiday_reopen"] = pd.to_numeric(panel.loc[idx, "holiday_reopen"], errors="coerce").fillna(0).eq(1)
    hold["sse_improvement"] = (hold["y"] - hold["p0"]) ** 2 - (hold["y"] - hold["p1"]) ** 2

    exact = hold.loc[hold["both_exact"]]
    mismatch = hold.loc[~hold["both_exact"]]
    positive_total = float(hold.loc[hold["sse_improvement"] > 0, "sse_improvement"].sum())
    mismatch_positive = float(mismatch.loc[mismatch["sse_improvement"] > 0, "sse_improvement"].sum())
    net_total = float(hold["sse_improvement"].sum())
    mismatch_net = float(mismatch["sse_improvement"].sum())

    top = hold.loc[~hold["both_exact"]].copy()
    top["abs_contribution"] = top["sse_improvement"].abs()
    top = top.sort_values("abs_contribution", ascending=False).head(20)
    top_rows = [
        {
            "trading_day": str(r["trading_day"].date()),
            "holiday_reopen": bool(r["holiday_reopen"]),
            "nasdaq_exact": bool(r["nasdaq_exact"]),
            "vix_exact": bool(r["vix_exact"]),
            "gap": float(r["y"]),
            "c0_pred": float(r["p0"]),
            "c1_pred": float(r["p1"]),
            "sse_improvement_c1_vs_c0": float(r["sse_improvement"]),
        }
        for _, r in top.iterrows()
    ]

    year_counts = {}
    for year, g in hold.groupby(hold["trading_day"].dt.year):
        year_counts[str(int(year))] = {
            "n": int(len(g)),
            "both_exact": int(g["both_exact"].sum()),
            "mismatch": int((~g["both_exact"]).sum()),
            "mismatch_share": float((~g["both_exact"]).mean()),
            "mismatch_sse_improvement": float(g.loc[~g["both_exact"], "sse_improvement"].sum()),
            "exact_sse_improvement": float(g.loc[g["both_exact"], "sse_improvement"].sum()),
        }

    report = {
        "schema_id": "overnight_open_global_spillover_v1_clock_mismatch_attribution@1.0",
        "audit_plan": "docs/governance/global_spillover_v1_forensic_audit_plan.json",
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020 consumed_internal"},
        "alignment": {
            "holdout_n": int(len(hold)),
            "both_exact_n": int(hold["both_exact"].sum()),
            "mismatch_n": int((~hold["both_exact"]).sum()),
            "mismatch_share": float((~hold["both_exact"]).mean()),
            "nasdaq_mismatch_n": int((~hold["nasdaq_exact"]).sum()),
            "vix_mismatch_n": int((~hold["vix_exact"]).sum()),
            "holiday_n": int(hold["holiday_reopen"].sum()),
            "holiday_and_mismatch_n": int((hold["holiday_reopen"] & ~hold["both_exact"]).sum()),
            "year_counts": year_counts,
        },
        "fixed_prediction_diagnostics": {
            "all": _subset_stats(hold),
            "both_exact": _subset_stats(exact),
            "mismatch": _subset_stats(mismatch),
            "holiday_reopen": _subset_stats(hold.loc[hold["holiday_reopen"]]),
            "nonholiday": _subset_stats(hold.loc[~hold["holiday_reopen"]]),
            "exact_nonholiday": _subset_stats(hold.loc[hold["both_exact"] & ~hold["holiday_reopen"]]),
            "mismatch_nonholiday": _subset_stats(hold.loc[~hold["both_exact"] & ~hold["holiday_reopen"]]),
        },
        "concentration": {
            "net_total_sse_improvement": net_total,
            "mismatch_net_sse_improvement": mismatch_net,
            "mismatch_net_share_of_total": float(mismatch_net / net_total) if net_total != 0 else float("nan"),
            "positive_total_sse_improvement": positive_total,
            "mismatch_positive_sse_improvement": mismatch_positive,
            "mismatch_positive_share": float(mismatch_positive / positive_total) if positive_total > 0 else float("nan"),
        },
        "top_mismatch_rows": top_rows,
        "scientific_interpretation": "forensic_only; if gain concentrates on mismatch rows, v1 unabsorbed-information mechanism is invalidated; no candidate is selected here",
        "authority": {"fresh_oos": False, "candidate_selection": False, "baseline_replacement": False, "production": False, "registry_mutation": False},
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
