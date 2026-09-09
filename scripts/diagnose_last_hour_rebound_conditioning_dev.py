#!/usr/bin/env python3
"""Diagnose why the rejected last-hour weakness hinge creates both TP and FP.

Development only: 2015-2025 raw material, expanding OOF 2016-2025.
No 2026 row may be loaded. This is not a candidate selector.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import select_high_open_recall_phase2_dev as phase2

PROTOCOL_PATH = ROOT / "docs/governance/cloud_session_20260906_high_open_rebound_conditioning_protocol_v1.json"
FAMILY_PATH = ROOT / "docs/governance/cloud_session_20260906_high_open_recall_phase2_family_v1.json"
PHASE2_RECEIPT_PATH = ROOT / "docs/research/cloud_session_20260906_local_high_open_recall_phase2_dev_receipt_v1.json"
OUTPUT_PATH = ROOT / "docs/research/cloud_session_20260906_local_last_hour_rebound_conditioning_receipt_v1.json"
DATA_USAGE_PATH = ROOT / "docs/governance/local_session_20260906_last_hour_rebound_conditioning_data_usage.json"

INCUMBENT_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
LAST_HOUR_SHA = "1a37a46c4c66026f6abe33b84a9d7704ab7c7513312ef15b25607dcfa694392d"
DEV_END = "2025-12-31"
OOF_YEARS = list(range(2016, 2026))

CONTINUOUS_PROBES = [
    "prev_daytime_weakness",
    "prev_afternoon_weakness",
    "prev_last_hour_weakness",
    "last_hour_minus_daytime_weakness",
    "last_hour_minus_afternoon_weakness",
    "prev_gap",
    "prev_gap_positive",
    "prev_gap_negative",
    "r1",
    "r20",
    "rvol20",
    "abs_r1",
]

BINARY_PROBES = [
    "tail_only_weakness",
    "tail_with_broad_day_weakness",
    "tail_with_broad_afternoon_weakness",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_conditioning_probes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    daytime = pd.to_numeric(out["prev_daytime"], errors="coerce")
    afternoon = pd.to_numeric(out["prev_afternoon"], errors="coerce")
    last_hour = pd.to_numeric(out["prev_last_hour"], errors="coerce")
    prev_gap = pd.to_numeric(out["prev_gap"], errors="coerce")

    day_weak = np.maximum(-daytime, 0.0)
    aft_weak = np.maximum(-afternoon, 0.0)
    last_weak = np.maximum(-last_hour, 0.0)

    out["prev_daytime_weakness"] = day_weak
    out["prev_afternoon_weakness"] = aft_weak
    out["prev_last_hour_weakness"] = last_weak
    out["last_hour_minus_daytime_weakness"] = last_weak - day_weak
    out["last_hour_minus_afternoon_weakness"] = last_weak - aft_weak
    out["tail_only_weakness"] = ((last_hour < 0.0) & (daytime >= 0.0)).astype(float)
    out["tail_with_broad_day_weakness"] = ((last_hour < 0.0) & (daytime < 0.0)).astype(float)
    out["tail_with_broad_afternoon_weakness"] = ((last_hour < 0.0) & (afternoon < 0.0)).astype(float)
    out["prev_gap_positive"] = np.maximum(prev_gap, 0.0)
    out["prev_gap_negative"] = np.maximum(-prev_gap, 0.0)
    return out


def assert_metric_replay(actual: dict, expected: dict, label: str) -> None:
    keys = [
        "n",
        "direction_hit",
        "balanced_accuracy",
        "recall_up",
        "recall_down",
        "material_high_open_gt10bp_recall",
        "material_high_open_gt30bp_recall",
        "correct_count",
        "tp",
        "fn",
        "tn",
        "fp",
    ]
    for key in keys:
        left = actual[key]
        right = expected[key]
        if isinstance(left, float) or isinstance(right, float):
            if abs(float(left) - float(right)) > 1e-12:
                raise RuntimeError(f"{label} replay mismatch on {key}: {left} != {right}")
        elif left != right:
            raise RuntimeError(f"{label} replay mismatch on {key}: {left} != {right}")


def safe_stats(part: pd.DataFrame, probe: str) -> tuple[float | None, float | None]:
    values = pd.to_numeric(part[probe], errors="coerce").dropna()
    if values.empty:
        return None, None
    return float(values.mean()), float(values.median())


def continuous_probe_diagnostic(oof: pd.DataFrame, probe: str) -> dict:
    valid = pd.to_numeric(oof[probe], errors="coerce").notna()
    base = oof.loc[valid].copy()
    added = base.loc[base["added_up"]].copy()
    rescue = added.loc[added["actual_up"]]
    false_high = added.loc[~added["actual_up"]]

    rescue_mean, rescue_median = safe_stats(rescue, probe)
    false_mean, false_median = safe_stats(false_high, probe)
    pooled_std = float(pd.to_numeric(added[probe], errors="coerce").std(ddof=0)) if len(added) else 0.0
    standardized = None
    if rescue_mean is not None and false_mean is not None and pooled_std > 0.0:
        standardized = float((rescue_mean - false_mean) / pooled_std)

    quartiles: dict[str, dict] = {}
    if len(base) >= 20 and pd.to_numeric(base[probe], errors="coerce").nunique(dropna=True) >= 4:
        ranks = pd.to_numeric(base[probe], errors="coerce").rank(method="first")
        base["_q"] = pd.qcut(ranks, 4, labels=["Q1", "Q2", "Q3", "Q4"]).astype(str)
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            qpart = base.loc[(base["_q"] == q) & base["added_up"]]
            n = int(len(qpart))
            rescued = int(qpart["actual_up"].sum())
            quartiles[q] = {
                "n_added_up": n,
                "rescued_high": rescued,
                "new_false_high": int(n - rescued),
                "added_up_precision": None if n == 0 else float(rescued / n),
                "probe_mean": None if n == 0 else float(pd.to_numeric(qpart[probe], errors="coerce").mean()),
            }

    annual: dict[str, dict] = {}
    positive_diff = 0
    negative_diff = 0
    for year in OOF_YEARS:
        part = added.loc[added["oof_year"] == year]
        yr = part.loc[part["actual_up"]]
        yf = part.loc[~part["actual_up"]]
        rm, _ = safe_stats(yr, probe)
        fm, _ = safe_stats(yf, probe)
        diff = None if rm is None or fm is None else float(rm - fm)
        if diff is not None:
            positive_diff += int(diff > 0.0)
            negative_diff += int(diff < 0.0)
        annual[str(year)] = {
            "rescued_high": int(len(yr)),
            "new_false_high": int(len(yf)),
            "rescue_mean": rm,
            "false_high_mean": fm,
            "rescue_minus_false_mean": diff,
        }

    return {
        "n_all_oof": int(len(base)),
        "n_added_up": int(len(added)),
        "rescued_high": int(len(rescue)),
        "new_false_high": int(len(false_high)),
        "added_up_precision": None if len(added) == 0 else float(len(rescue) / len(added)),
        "rescue_mean": rescue_mean,
        "rescue_median": rescue_median,
        "false_high_mean": false_mean,
        "false_high_median": false_median,
        "rescue_minus_false_standardized": standardized,
        "annual_diff_positive_count": positive_diff,
        "annual_diff_negative_count": negative_diff,
        "annual": annual,
        "quartiles": quartiles,
    }


def binary_probe_diagnostic(oof: pd.DataFrame, probe: str) -> dict:
    values = pd.to_numeric(oof[probe], errors="coerce")
    added = oof.loc[oof["added_up"] & values.notna()].copy()
    states: dict[str, dict] = {}
    for state in [0.0, 1.0]:
        part = added.loc[pd.to_numeric(added[probe], errors="coerce") == state]
        n = int(len(part))
        rescued = int(part["actual_up"].sum())
        states[str(int(state))] = {
            "n_added_up": n,
            "rescued_high": rescued,
            "new_false_high": int(n - rescued),
            "added_up_precision": None if n == 0 else float(rescued / n),
        }

    annual: dict[str, dict] = {}
    state1_precision_better = 0
    state0_precision_better = 0
    for year in OOF_YEARS:
        part = added.loc[added["oof_year"] == year]
        rec: dict[str, dict] = {}
        precision: dict[int, float | None] = {}
        for state in [0, 1]:
            sub = part.loc[pd.to_numeric(part[probe], errors="coerce") == float(state)]
            n = int(len(sub))
            rescued = int(sub["actual_up"].sum())
            p = None if n == 0 else float(rescued / n)
            precision[state] = p
            rec[str(state)] = {
                "n_added_up": n,
                "rescued_high": rescued,
                "new_false_high": int(n - rescued),
                "added_up_precision": p,
            }
        if precision[0] is not None and precision[1] is not None:
            state1_precision_better += int(precision[1] > precision[0])
            state0_precision_better += int(precision[0] > precision[1])
        annual[str(year)] = rec

    return {
        "states": states,
        "state1_precision_better_year_count": state1_precision_better,
        "state0_precision_better_year_count": state0_precision_better,
        "annual": annual,
    }


def main() -> int:
    protocol = load_json(PROTOCOL_PATH)
    family = load_json(FAMILY_PATH)
    phase2_receipt = load_json(PHASE2_RECEIPT_PATH)

    if protocol["fixed_models"]["incumbent"]["spec_sha256"] != INCUMBENT_SHA:
        raise RuntimeError("incumbent identity drifted")
    if protocol["fixed_models"]["diagnostic_progression_candidate"]["spec_sha256"] != LAST_HOUR_SHA:
        raise RuntimeError("last-hour diagnostic identity drifted")
    if protocol["evidence_boundary"]["sealed_repeat_blackbox"] != "2026-01-05_to_2026-08-21":
        raise RuntimeError("2026 blackbox boundary drifted")
    if phase2_receipt["decision"] != "retain_incumbent_do_not_open_repeat_blackbox":
        raise RuntimeError("unexpected Phase-2 decision")
    if phase2_receipt["2026_rows_loaded"] or phase2_receipt["2026_blackbox_opened"]:
        raise RuntimeError("Phase-2 receipt indicates 2026 access")

    last_attempt = next(a for a in phase2_receipt["attempts"] if a["name"] == "weakness_last_hour_piecewise")
    if last_attempt["candidate_spec_sha256"] != LAST_HOUR_SHA or last_attempt["eligible"]:
        raise RuntimeError("last-hour progression candidate identity/status mismatch")

    frame, reconstruction = phase2.build_development_frame()
    frame = add_conditioning_probes(frame)
    if str(pd.to_datetime(frame["trading_day"]).max().date()) > DEV_END:
        raise RuntimeError("conditioning diagnostic crossed into 2026")

    base_features = list(family["base_features"])
    candidate_features = base_features + ["prev_last_hour_weakness"]
    incumbent = phase2.expanding_oof(frame, base_features, base_features)
    candidate = phase2.expanding_oof(frame, candidate_features, base_features)

    assert_metric_replay(phase2.score_metrics(incumbent), phase2_receipt["incumbent_metrics"], "incumbent")
    assert_metric_replay(phase2.score_metrics(candidate), last_attempt["metrics"], "last-hour")

    merged = incumbent[["trading_day", "gap", "oof_year", "score", "pred_up"]].rename(
        columns={"score": "incumbent_score", "pred_up": "incumbent_up"}
    ).merge(
        candidate[["trading_day", "score", "pred_up"]].rename(
            columns={"score": "candidate_score", "pred_up": "candidate_up"}
        ),
        on="trading_day",
        how="inner",
        validate="one_to_one",
    )

    probe_cols = list(dict.fromkeys(CONTINUOUS_PROBES + BINARY_PROBES))
    probe_frame = frame[["trading_day"] + probe_cols].drop_duplicates("trading_day")
    merged = merged.merge(probe_frame, on="trading_day", how="left", validate="one_to_one")
    if len(merged) != phase2_receipt["n_oof"]:
        raise RuntimeError("OOF inventory mismatch after conditioning merge")
    if (pd.to_datetime(merged["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered conditioning OOF")

    merged["actual_up"] = pd.to_numeric(merged["gap"], errors="coerce") >= 0.0
    merged["added_up"] = (~merged["incumbent_up"].astype(bool)) & merged["candidate_up"].astype(bool)
    merged["removed_up"] = merged["incumbent_up"].astype(bool) & (~merged["candidate_up"].astype(bool))

    rescue = merged["added_up"] & merged["actual_up"]
    new_false_high = merged["added_up"] & (~merged["actual_up"])
    lost_high = merged["removed_up"] & merged["actual_up"]
    repaired_false_high = merged["removed_up"] & (~merged["actual_up"])

    disagreement = {
        "incumbent_down_candidate_up_actual_up_rescue": int(rescue.sum()),
        "incumbent_down_candidate_up_actual_down_new_false_high": int(new_false_high.sum()),
        "incumbent_up_candidate_down_actual_up_lost_high": int(lost_high.sum()),
        "incumbent_up_candidate_down_actual_down_repaired_false_high": int(repaired_false_high.sum()),
        "added_up_total": int(merged["added_up"].sum()),
        "removed_up_total": int(merged["removed_up"].sum()),
        "added_up_precision": None if int(merged["added_up"].sum()) == 0 else float(rescue.sum() / merged["added_up"].sum()),
        "total_prediction_disagreements": int((merged["incumbent_up"] != merged["candidate_up"]).sum()),
    }

    annual_disagreement: dict[str, dict] = {}
    for year in OOF_YEARS:
        part = merged.loc[merged["oof_year"] == year]
        annual_disagreement[str(year)] = {
            "rescued_high": int((part["added_up"] & part["actual_up"]).sum()),
            "new_false_high": int((part["added_up"] & (~part["actual_up"])).sum()),
            "lost_high": int((part["removed_up"] & part["actual_up"]).sum()),
            "repaired_false_high": int((part["removed_up"] & (~part["actual_up"])).sum()),
        }

    receipt = {
        "schema_id": "overnight_open_last_hour_rebound_conditioning_receipt@1.0",
        "session_date": "2026-09-06",
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "development_window": {"start": phase2.DEV_START, "end": phase2.DEV_END},
        "oof_years": OOF_YEARS,
        "n_oof": int(len(merged)),
        "incumbent_spec_sha256": INCUMBENT_SHA,
        "diagnostic_candidate_spec_sha256": LAST_HOUR_SHA,
        "phase2_receipt_sha256": sha256(PHASE2_RECEIPT_PATH),
        "disagreement_morphology": disagreement,
        "annual_disagreement_morphology": annual_disagreement,
        "continuous_probes": {p: continuous_probe_diagnostic(merged, p) for p in CONTINUOUS_PROBES},
        "binary_probes": {p: binary_probe_diagnostic(merged, p) for p in BINARY_PROBES},
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "annotated_panel": sha256(phase2.ANNOTATED_PANEL),
            "datahub_1m_export": sha256(phase2.DATAHUB_1M),
            "fred_nasdaq": sha256(phase2.FRED_NDQ),
            "fred_vix": sha256(phase2.FRED_VIX),
            "family": sha256(FAMILY_PATH),
            "phase2_receipt": sha256(PHASE2_RECEIPT_PATH),
            "protocol": sha256(PROTOCOL_PATH),
            "runner": sha256(Path(__file__)),
        },
        "candidate_selection_performed": False,
        "parameter_search_performed": False,
        "threshold_search_performed": False,
        "quantile_search_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "2026_blackbox_opened": False,
        "ohr_03_opened": False,
        "raw_development_rows_written_to_repo": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(OUTPUT_PATH, receipt)

    usage = {
        "schema_id": "overnight_open_local_last_hour_rebound_conditioning_data_usage@1.0",
        "session_date": "2026-09-06",
        "2015-01-05_to_2025-12-31": "development_diagnostic_only_for_last_hour_rebound_conditioning",
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "candidate_selection_performed": False,
        "raw_rows_persisted_in_bounded_repo": False,
        "production_authority": False,
    }
    dump_json(DATA_USAGE_PATH, usage)

    summary = {
        "n_oof": receipt["n_oof"],
        "disagreement_morphology": disagreement,
        "2026_blackbox_opened": False,
        "candidate_selection_performed": False,
    }
    print("LAST_HOUR_REBOUND_CONDITIONING_RESULT", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
