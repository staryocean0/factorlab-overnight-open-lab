#!/usr/bin/env python3
"""Detailed 2019-2020 strategy-science evaluation for the frozen V6A short-side rule.

This runner MUST NOT read 2021-2025 CSI1000 strategy outcomes. It fits the frozen
V5A/V6A predictors on 2015-2018, evaluates only 2019-2020, enters an index-level
synthetic short at the 09:35 one-minute close when predicted signed gap > 0, and
exits at the 15:00 one-minute close. Costs are 1bp on entry and 1bp on exit.

The cash index is used only as a research PnL proxy; this is not a claim of
tradability or production readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TRAIN_END = pd.Timestamp("2018-12-31")
DEV_START = pd.Timestamp("2019-01-01")
DEV_END = pd.Timestamp("2020-12-31")
SYMBOL = "000852.SH"
ENTRY_CLOCK = "09:35"
EXIT_CLOCK = "15:00"
ROUND_TRIP_COST = 0.0002


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_v6a_module():
    path = ROOT / "scripts/run_v6a_reusable_blackbox_local.py"
    spec = importlib.util.spec_from_file_location("v6a_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen V6A module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_execution_prices(path: Path) -> pd.DataFrame:
    cols = ["symbol", "trading_day", "timestamp", "close"]
    try:
        x = pd.read_parquet(
            path,
            filters=[
                ("symbol", "==", SYMBOL),
                ("trading_day", ">=", "2019-01-01"),
                ("trading_day", "<=", "2020-12-31"),
            ],
            columns=cols,
        )
    except Exception:
        x = pd.read_parquet(path, columns=cols)
        x = x.loc[x["symbol"].astype(str).eq(SYMBOL)].copy()
    x["trading_day"] = pd.to_datetime(x["trading_day"], errors="raise").dt.normalize()
    x = x.loc[x["trading_day"].between(DEV_START, DEV_END)].copy()
    x["clock"] = x["timestamp"].astype(str).str.slice(11, 16)
    x = x.loc[x["clock"].isin([ENTRY_CLOCK, EXIT_CLOCK])].copy()
    x["close"] = pd.to_numeric(x["close"], errors="coerce")
    wide = x.pivot_table(index="trading_day", columns="clock", values="close", aggfunc="last")
    wide = wide.rename(columns={ENTRY_CLOCK: "entry_price", EXIT_CLOCK: "exit_price"}).reset_index()
    return wide[["trading_day", "entry_price", "exit_price"]]


def fit_predictions(df: pd.DataFrame, features: list[str], train_mask: pd.Series, test_mask: pd.Series) -> pd.Series:
    xtr = df.loc[train_mask, features].apply(pd.to_numeric, errors="coerce")
    ytr = pd.to_numeric(df.loc[train_mask, "gap"], errors="coerce")
    train_complete = xtr.notna().all(axis=1) & ytr.notna()
    if int(train_complete.sum()) == 0:
        raise RuntimeError("no complete frozen training rows")
    pipe = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
    pipe.fit(xtr.loc[train_complete], ytr.loc[train_complete])
    xte = df.loc[test_mask, features].apply(pd.to_numeric, errors="coerce")
    if not xte.notna().all(axis=1).all():
        raise RuntimeError("strategy-science test matrix contains incomplete frozen features")
    return pd.Series(pipe.predict(xte), index=xte.index)


def stats(values: pd.Series) -> dict:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(float)
    if len(arr) == 0:
        return {"n": 0, "mean_net_return": None, "median_net_return": None, "win_rate": None, "sum_net_return": None}
    return {
        "n": int(len(arr)),
        "mean_net_return": float(np.mean(arr)),
        "median_net_return": float(np.median(arr)),
        "win_rate": float(np.mean(arr > 0.0)),
        "sum_net_return": float(np.sum(arr)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-panel", type=Path, default=ROOT / "data/development/csi1000_open_pit_panel.parquet")
    ap.add_argument("--minute-bars", type=Path, default=ROOT / "data/high_open_dev_2015_2025/1m_official.parquet")
    ap.add_argument("--nasdaq", type=Path, default=ROOT / "data/high_open_dev_2015_2025/fred_nasdaq.csv")
    ap.add_argument("--vix", type=Path, default=ROOT / "data/high_open_dev_2015_2025/fred_vix.csv")
    ap.add_argument("--hkma", type=Path, default=ROOT / "data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet")
    ap.add_argument("--holiday-a50", type=Path, default=ROOT / "data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet")
    ap.add_argument("--ordinary-a50", type=Path, default=ROOT / "data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet")
    ap.add_argument("--protocol", type=Path, default=ROOT / "docs/governance/v6a_short0935_strategy_science_protocol_v1.json")
    ap.add_argument("--decision-contract", type=Path, default=ROOT / "docs/governance/v6a_short0935_financial_decision_use_contract_v1.json")
    ap.add_argument("--receipt-out", type=Path, default=ROOT / "docs/research/local_v6a_short0935_strategy_science_dev_receipt_v1.json")
    args = ap.parse_args()

    mod = load_v6a_module()
    panel = pd.read_parquet(args.base_panel).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > DEV_END:
        raise RuntimeError("base panel unexpectedly contains post-2020 rows")

    df = mod.add_us_complete_clock(panel, mod.read_fred(args.nasdaq, "NASDAQCOM"), mod.read_fred(args.vix, "VIXCLS"))
    df = mod.add_hkma(df, args.hkma)
    df, _, clocks_ok = mod.attach_a50(df, args.holiday_a50, args.ordinary_a50)
    if not clocks_ok:
        raise RuntimeError("frozen A50 clock guard failed")

    prices = read_execution_prices(args.minute_bars)
    df = df.merge(prices, on="trading_day", how="left", validate="one_to_one")

    train_mask = df["a50_common_available"] & df["trading_day"].le(TRAIN_END)
    dev_mask_base = df["a50_common_available"] & df["trading_day"].between(DEV_START, DEV_END)

    joint_features = list(mod.V6_FEATURES)
    complete_dev = (
        dev_mask_base
        & df[joint_features].apply(pd.to_numeric, errors="coerce").notna().all(axis=1)
        & pd.to_numeric(df["gap"], errors="coerce").notna()
        & pd.to_numeric(df["entry_price"], errors="coerce").notna()
        & pd.to_numeric(df["exit_price"], errors="coerce").notna()
    )
    if int(complete_dev.sum()) == 0:
        raise RuntimeError("no complete 2019-2020 strategy-science rows")

    p5 = fit_predictions(df, list(mod.V5_FEATURES), train_mask, complete_dev)
    p6 = fit_predictions(df, list(mod.V6_FEATURES), train_mask, complete_dev)
    idx = p6.index
    eval_df = df.loc[idx, ["trading_day", "entry_price", "exit_price"]].copy()
    eval_df["p5"] = p5
    eval_df["p6"] = p6
    eval_df["short_net_return"] = (
        (pd.to_numeric(eval_df["entry_price"], errors="coerce") - pd.to_numeric(eval_df["exit_price"], errors="coerce"))
        / pd.to_numeric(eval_df["entry_price"], errors="coerce")
        - ROUND_TRIP_COST
    )
    eval_df["v5_trade"] = eval_df["p5"] > 0.0
    eval_df["v6_trade"] = eval_df["p6"] > 0.0

    v6_stats = stats(eval_df.loc[eval_df["v6_trade"], "short_net_return"])
    v5_stats = stats(eval_df.loc[eval_df["v5_trade"], "short_net_return"])
    always_stats = stats(eval_df["short_net_return"])

    by_year = {}
    yearly_positive = True
    yearly_counts_ok = True
    for year in (2019, 2020):
        sub = eval_df.loc[(eval_df["trading_day"].dt.year == year) & eval_df["v6_trade"], "short_net_return"]
        s = stats(sub)
        by_year[str(year)] = s
        yearly_counts_ok &= s["n"] >= 40
        yearly_positive &= s["mean_net_return"] is not None and s["mean_net_return"] > 0.0

    sample_ok = v6_stats["n"] >= 100 and yearly_counts_ok
    gates = {
        "candidate_trade_sample_sufficiency_pass": bool(sample_ok),
        "candidate_pooled_mean_net_return_gt_0": bool(v6_stats["mean_net_return"] is not None and v6_stats["mean_net_return"] > 0.0),
        "candidate_pooled_median_net_return_gt_0": bool(v6_stats["median_net_return"] is not None and v6_stats["median_net_return"] > 0.0),
        "candidate_pooled_mean_net_return_gt_V5A_mapped_strategy_mean_net_return": bool(
            v6_stats["mean_net_return"] is not None
            and v5_stats["mean_net_return"] is not None
            and v6_stats["mean_net_return"] > v5_stats["mean_net_return"]
        ),
        "candidate_positive_mean_net_return_in_both_2019_and_2020": bool(yearly_positive),
    }
    if not sample_ok:
        decision = "DEV_INSUFFICIENT"
    else:
        decision = "DEV_PASS" if all(gates.values()) else "DEV_CLOSE"

    receipt = {
        "schema_id": "overnight_v6a_short0935_strategy_science_dev_receipt@1.0",
        "session_date": "2026-09-10",
        "research_identity": "overnight_v6a_short0935_to_close_v1",
        "decision": decision,
        "window": "2019-01-01..2020-12-31",
        "blackbox_2021_2025_opened_for_this_strategy_identity": False,
        "candidate_V6A": v6_stats,
        "parent_V5A_mapped_strategy": v5_stats,
        "always_short_context": always_stats,
        "candidate_by_year": by_year,
        "gates": gates,
        "execution": {
            "side": "short_only",
            "entry": "09:35 one-minute close",
            "exit": "15:00 one-minute close",
            "entry_cost": 0.0001,
            "exit_cost": 0.0001,
            "round_trip_cost": ROUND_TRIP_COST,
            "index_level_research_proxy_only": True,
        },
        "protocol_sha256": sha256(args.protocol),
        "decision_contract_sha256": sha256(args.decision_contract),
        "base_panel_sha256": sha256(args.base_panel),
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
