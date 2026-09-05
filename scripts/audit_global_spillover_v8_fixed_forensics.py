#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "docs/governance/global_spillover_v8_forensic_diagnostic_plan.json"
OUT_PATH = ROOT / "artifacts/research/global_spillover_v8_fixed_forensics.json"


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def concentration(imp: np.ndarray) -> dict:
    imp = np.asarray(imp, dtype=float)
    positive = np.sort(imp[imp > 0])[::-1]
    total_positive = float(positive.sum())
    total = float(imp.sum())
    def share(n: int) -> float:
        return float(positive[:n].sum() / total_positive) if total_positive > 0 else float("nan")
    return {
        "positive_row_count": int(np.sum(imp > 0)),
        "negative_row_count": int(np.sum(imp < 0)),
        "zero_row_count": int(np.sum(imp == 0)),
        "total_fixed_prediction_sse_improvement": total,
        "top1_share_of_positive_gain": share(1),
        "top5_share_of_positive_gain": share(5),
        "top10_share_of_positive_gain": share(10),
        "remaining_total_after_removing_top1_positive_row": float(total - positive[:1].sum()),
        "remaining_total_after_removing_top5_positive_rows": float(total - positive[:5].sum()),
        "remaining_total_after_removing_top10_positive_rows": float(total - positive[:10].sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formal-result", required=True)
    args = ap.parse_args()
    formal_path = Path(args.formal_result)
    if not formal_path.is_absolute():
        formal_path = ROOT / formal_path
    plan = json.loads(PLAN_PATH.read_text())
    formal = json.loads(formal_path.read_text())
    if plan["status"] != "result_free_before_formal_v8_model_execution":
        raise AssertionError("v8 forensic plan was not frozen result-free")
    if formal["schema_id"] != "overnight_open_global_spillover_v8_regime_results@1.0":
        raise AssertionError("unexpected formal v8 result schema")
    rows = formal.get("fixed_holdout_predictions", [])
    if not rows:
        raise AssertionError("formal v8 result lacks fixed predictions")
    fixed = pd.DataFrame(rows)
    fixed["trading_day"] = pd.to_datetime(fixed["trading_day"], errors="raise").dt.normalize()
    fixed = fixed.sort_values("trading_day").reset_index(drop=True)
    expected_n = int(formal["candidates"]["V6A_frozen_common_sample_comparator"]["n_holdout"])
    if len(fixed) != expected_n:
        raise AssertionError(("fixed row count mismatch", len(fixed), expected_n))

    interaction = fixed["a50_ordinary_x_rvol20"].to_numpy(dtype=float)
    target = fixed["y"].to_numpy(dtype=float)
    v6_pred = fixed["V6_pred"].to_numpy(dtype=float)
    residual = target - v6_pred
    a50 = fixed["a50_ordinary_preauction_closure_return"].to_numpy(dtype=float)
    rvol = fixed["rvol20"].to_numpy(dtype=float)
    imp = fixed["sse_improvement"].to_numpy(dtype=float)

    c0 = formal["candidates"]["V6A_frozen_common_sample_comparator"]
    c1 = formal["candidates"]["V8A_plus_A50_x_rvol20"]
    shifts = {}
    flips = []
    for feature, beta0 in c0["standardized_coefficients"].items():
        beta1 = c1["standardized_coefficients"][feature]
        shifts[feature] = float(beta1 - beta0)
        if beta0 != 0 and beta1 != 0 and np.sign(beta0) != np.sign(beta1):
            flips.append(feature)

    report = {
        "schema_id": "overnight_open_global_spillover_v8_fixed_forensics@1.0",
        "forensic_plan": str(PLAN_PATH.relative_to(ROOT)),
        "formal_result_source": str(formal_path),
        "formal_progression_rule_pass": bool(formal["adjudication"]["progression_rule_pass"]),
        "fixed_prediction_rows": int(len(fixed)),
        "refit_or_reselection_performed": False,
        "time_shift_placebo": {
            "same_row_corr_interaction_t_target_t": corr(interaction, target),
            "lead_one_row_corr_interaction_t_target_t_plus_1": corr(interaction[:-1], target[1:]),
            "lag_one_row_corr_interaction_t_target_t_minus_1": corr(interaction[1:], target[:-1]),
        },
        "incremental_information": {
            "corr_interaction_with_V6_fixed_residual": corr(interaction, residual),
            "corr_interaction_with_A50_main_effect": corr(interaction, a50),
            "corr_interaction_with_rvol20_main_effect": corr(interaction, rvol),
            "corr_interaction_with_target": corr(interaction, target),
        },
        "fixed_prediction_concentration": concentration(imp),
        "coefficient_redistribution": {
            "interaction_standardized_coefficient": float(c1["standardized_coefficients"]["a50_ordinary_x_rvol20"]),
            "shared_feature_coefficient_shifts": shifts,
            "shared_feature_sign_flips": flips,
            "A50_main_coefficient_before": float(c0["standardized_coefficients"]["a50_ordinary_preauction_closure_return"]),
            "A50_main_coefficient_after": float(c1["standardized_coefficients"]["a50_ordinary_preauction_closure_return"]),
            "rvol20_main_coefficient_before": float(c0["standardized_coefficients"]["rvol20"]),
            "rvol20_main_coefficient_after": float(c1["standardized_coefficients"]["rvol20"]),
        },
        "formal_mechanism_subsets": {
            "ordinary": formal["subsets"]["ordinary"],
            "holiday": formal["subsets"]["holiday"],
        },
        "interpretation": {
            "primary_verdict_unchanged": True,
            "diagnostics_can_promote_failed_v8": False,
            "scientific_read": "A high same-row correlation can coexist with a failed increment when the raw interaction is mostly a rescaled version of the already-retained A50 main effect and has little or adverse relation to the residual left by V6."
        },
        "authority": {
            "candidate_selection": False,
            "fresh_oos": False,
            "baseline_replacement": False,
            "production": False,
            "registry_mutation": False,
            "merge_main": False
        }
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
