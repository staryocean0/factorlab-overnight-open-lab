#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import research_global_spillover_v3_complete_clock as v3

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs/governance/baseline_receipt.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v3_leave_one_event_out.json"


def corr(y: np.ndarray, p: np.ndarray) -> float:
    if len(y) < 3 or np.std(y) == 0 or np.std(p) == 0:
        return float("nan")
    return float(np.corrcoef(y, p)[0, 1])


def metrics(rows: pd.DataFrame, pred_col: str) -> dict:
    y = rows["y"].to_numpy(dtype=float)
    p = rows[pred_col].to_numpy(dtype=float)
    return {
        "n": int(len(rows)),
        "ic": corr(y, p),
        "sign_hit": float(np.mean((p >= 0) == (y >= 0))),
        "sse": float(np.sum((y - p) ** 2)),
    }


def main() -> None:
    baseline = json.loads(BASELINE_PATH.read_text())
    panel = pd.read_parquet(PANEL_PATH).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    if panel["trading_day"].max() > pd.Timestamp("2020-12-31"):
        raise AssertionError("post-2020 China row detected")
    df = v3.add_complete_clock_features(panel, v3._load_us())
    base = list(baseline["features"])
    c0m, c0 = v3._fit_predict(df, base)
    c1m, c1 = v3._fit_predict(df, base + ["us_nasdaq_closure_extra", "us_vix_closure_extra"])
    if not c0["trading_day"].reset_index(drop=True).equals(c1["trading_day"].reset_index(drop=True)):
        raise AssertionError("prediction alignment mismatch")

    rows = c0[["trading_day", "holiday_reopen", "us_interval_count", "y", "pred"]].copy()
    rows = rows.rename(columns={"pred": "c0_pred"}).reset_index(drop=True)
    rows["c1_pred"] = c1["pred"].to_numpy(dtype=float)
    multi = rows.loc[rows["us_interval_count"] > 1].copy().reset_index(drop=True)
    if len(multi) != 12:
        raise AssertionError(("unexpected multi-interval event count", len(multi)))
    if not bool((pd.to_numeric(multi["holiday_reopen"], errors="coerce").fillna(0) != 0).all()):
        raise AssertionError("multi-interval events do not coincide with holiday reopen in this holdout")

    full_c0 = metrics(multi, "c0_pred")
    full_c1 = metrics(multi, "c1_pred")
    full_improvement = full_c0["sse"] - full_c1["sse"]

    loo = []
    for i, row in multi.iterrows():
        kept = multi.drop(index=i).reset_index(drop=True)
        m0 = metrics(kept, "c0_pred")
        m1 = metrics(kept, "c1_pred")
        loo.append({
            "removed_trading_day": str(row["trading_day"].date()),
            "removed_gap": float(row["y"]),
            "n": int(len(kept)),
            "c0_ic": m0["ic"],
            "c1_ic": m1["ic"],
            "delta_ic": float(m1["ic"] - m0["ic"]),
            "c0_sign_hit": m0["sign_hit"],
            "c1_sign_hit": m1["sign_hit"],
            "sse_improvement_c1_vs_c0": float(m0["sse"] - m1["sse"]),
        })

    delta_ics = np.array([x["delta_ic"] for x in loo], dtype=float)
    sse_imps = np.array([x["sse_improvement_c1_vs_c0"] for x in loo], dtype=float)
    event_imps = ((multi["y"] - multi["c0_pred"]) ** 2 - (multi["y"] - multi["c1_pred"]) ** 2).to_numpy(dtype=float)
    ranked = sorted(
        [
            {"trading_day": str(d.date()), "sse_improvement": float(s)}
            for d, s in zip(multi["trading_day"], event_imps, strict=True)
        ],
        key=lambda x: x["sse_improvement"],
        reverse=True,
    )
    positive_sum = float(event_imps[event_imps > 0].sum())
    top1_positive_share = float(max(event_imps.max(), 0.0) / positive_sum) if positive_sum > 0 else float("nan")
    top2_positive_share = float(sum(max(x["sse_improvement"], 0.0) for x in ranked[:2]) / positive_sum) if positive_sum > 0 else float("nan")

    report = {
        "schema_id": "overnight_open_global_spillover_v3_leave_one_event_out@1.0",
        "role": "preregistered fixed-prediction robustness diagnostic; no refit and no candidate reselection",
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_internal"},
        "full_multiple_interval_subset": {
            "n": int(len(multi)),
            "c0_ic": full_c0["ic"],
            "c1_ic": full_c1["ic"],
            "delta_ic": float(full_c1["ic"] - full_c0["ic"]),
            "c0_sign_hit": full_c0["sign_hit"],
            "c1_sign_hit": full_c1["sign_hit"],
            "sse_improvement_c1_vs_c0": float(full_improvement),
        },
        "leave_one_event_out": loo,
        "robustness_summary": {
            "loo_cases": int(len(loo)),
            "delta_ic_positive_count": int(np.sum(delta_ics > 0)),
            "delta_ic_min": float(np.nanmin(delta_ics)),
            "delta_ic_median": float(np.nanmedian(delta_ics)),
            "delta_ic_max": float(np.nanmax(delta_ics)),
            "sse_improvement_positive_count": int(np.sum(sse_imps > 0)),
            "sse_improvement_min": float(np.nanmin(sse_imps)),
            "sse_improvement_median": float(np.nanmedian(sse_imps)),
            "sse_improvement_max": float(np.nanmax(sse_imps)),
            "top1_share_of_positive_event_sse_improvement": top1_positive_share,
            "top2_share_of_positive_event_sse_improvement": top2_positive_share,
            "event_sse_improvement_ranked": ranked,
        },
        "authority": {
            "fresh_oos": False,
            "candidate_reselection": False,
            "baseline_replacement": False,
            "production": False,
        },
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
