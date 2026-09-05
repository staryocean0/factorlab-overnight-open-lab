#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "artifacts/research/global_spillover_v5_a50_results.json"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v5_a50_leave_one_event_out.json"


def corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.nanstd(a) == 0 or np.nanstd(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def metrics(rows: list[dict], candidate_field: str) -> dict:
    y = np.asarray([float(r["y"]) for r in rows], dtype=float)
    p0 = np.asarray([float(r["V4_pred"]) for r in rows], dtype=float)
    px = np.asarray([float(r[candidate_field]) for r in rows], dtype=float)
    return {
        "n": int(len(rows)),
        "v4_ic": corr(y, p0),
        "candidate_ic": corr(y, px),
        "delta_ic": float(corr(y, px) - corr(y, p0)) if len(rows) >= 3 else float("nan"),
        "v4_sign_hit": float(np.mean((p0 >= 0) == (y >= 0))) if len(rows) else float("nan"),
        "candidate_sign_hit": float(np.mean((px >= 0) == (y >= 0))) if len(rows) else float("nan"),
        "sse_improvement_candidate_vs_v4": float(np.sum((y - p0) ** 2) - np.sum((y - px) ** 2)),
    }


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    selected = result["adjudication"].get("selected_progression_candidate")
    base_report = {
        "schema_id": "overnight_open_global_spillover_v5_a50_leave_one_event_out@1.0",
        "role": "fixed-prediction robustness diagnostic; no refit and no candidate reselection",
        "source_results": str(RESULT_PATH.relative_to(ROOT)),
        "selected_progression_candidate": selected,
        "data_boundary": {"post_2020_rows_read": 0, "holdout": "2019-2020_consumed_internal"},
        "authority": {"fresh_oos": False, "candidate_reselection": False, "baseline_replacement": False, "production": False},
    }
    if selected is None:
        base_report.update({"status": "not_applicable_no_v5_progression_candidate", "leave_one_event_out": [], "robustness_summary": None})
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(base_report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(base_report, indent=2, sort_keys=True))
        return

    candidate_field = "V5B_pred" if selected == "V5B_plus_A50_closure_and_preopen" else "V5A_pred"
    rows = list(result.get("event_predictions", []))
    if len(rows) < 10:
        raise AssertionError(("too few holiday event predictions for preregistered LOO", len(rows)))
    full = metrics(rows, candidate_field)
    loo = []
    for i, removed in enumerate(rows):
        keep = rows[:i] + rows[i + 1 :]
        m = metrics(keep, candidate_field)
        m["removed_trading_day"] = removed["trading_day"]
        m["removed_gap"] = float(removed["y"])
        loo.append(m)

    delta = [float(x["delta_ic"]) for x in loo]
    sse = [float(x["sse_improvement_candidate_vs_v4"]) for x in loo]
    # Event-level contribution to full-sample SSE improvement, for concentration diagnostics.
    contributions = []
    for r in rows:
        y = float(r["y"]); p0 = float(r["V4_pred"]); px = float(r[candidate_field])
        contributions.append({"trading_day": r["trading_day"], "sse_improvement": (y - p0) ** 2 - (y - px) ** 2})
    positive_total = sum(max(0.0, x["sse_improvement"]) for x in contributions)
    ranked = sorted(contributions, key=lambda x: x["sse_improvement"], reverse=True)
    top1_share = max(0.0, ranked[0]["sse_improvement"]) / positive_total if positive_total > 0 else float("nan")
    top2_share = sum(max(0.0, x["sse_improvement"]) for x in ranked[:2]) / positive_total if positive_total > 0 else float("nan")

    base_report.update({
        "status": "completed",
        "full_holiday_subset": full,
        "leave_one_event_out": loo,
        "robustness_summary": {
            "loo_cases": len(loo),
            "delta_ic_positive_count": int(sum(x > 0 for x in delta)),
            "delta_ic_min": float(min(delta)),
            "delta_ic_median": float(np.median(delta)),
            "delta_ic_max": float(max(delta)),
            "sse_improvement_positive_count": int(sum(x > 0 for x in sse)),
            "sse_improvement_min": float(min(sse)),
            "sse_improvement_median": float(np.median(sse)),
            "sse_improvement_max": float(max(sse)),
            "event_sse_improvement_ranked": ranked,
            "top1_share_of_positive_event_sse_improvement": float(top1_share),
            "top2_share_of_positive_event_sse_improvement": float(top2_share),
        },
    })
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(base_report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(base_report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
