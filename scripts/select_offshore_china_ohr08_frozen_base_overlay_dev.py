#!/usr/bin/env python3
"""OHR-08 final low-DOF offshore-China development test.

The incumbent 13-feature Median model is fit and frozen independently in each
expanding OOF fold. Exactly one no-intercept median-regression coefficient is
then fit on the residual using the preregistered offshore gated feature g.
No 2026 row may be loaded.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import diagnose_high_open_false_negatives_dev as highdiag
import diagnose_offshore_china_price_discovery_dev as ohr06
import select_high_open_recall_phase2_dev as phase2

PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr08_frozen_base_overlay_v1.json"
INCUMBENT = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
OHR06_RECEIPT = ROOT / "docs/research/cloud_session_20260906_local_offshore_china_ohr06_diagnostic_receipt_v1.json"
OHR07_RECEIPT = ROOT / "docs/research/cloud_session_20260906_cloud_offshore_china_ohr07_dev_receipt_v1.json"
SOURCE = ROOT / "data/offshore_etf_dev_2015_2025/offshore_etf_daily.parquet"
OUT = ROOT / "docs/research/cloud_session_20260906_cloud_offshore_china_ohr08_dev_receipt_v1.json"
USAGE = ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr08_data_usage.json"

EXPECTED_SOURCE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
INCUMBENT_SPEC_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
YEARS = list(range(2016, 2026))
G = "broad_china_specific_tail_weak"
EPS = 1e-12


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


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def add_g(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    broad = pd.to_numeric(out["broad_china_specific_vs_spy"], errors="coerce")
    prev_last = pd.to_numeric(out["prev_last_hour"], errors="coerce")
    valid = out["offshore_common_valid"].astype(bool)
    g = broad * (prev_last < 0.0).astype(float)
    out[G] = np.where(valid, g, np.nan)
    return out


def common_mask(frame: pd.DataFrame, base_features: list[str]) -> pd.Series:
    cols = base_features + [G]
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    valid = frame["offshore_common_valid"].astype(bool)
    return x.notna().all(axis=1) & y.notna() & valid


def run_expanding_overlay(frame: pd.DataFrame, base_features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    inc_parts: list[pd.DataFrame] = []
    cand_parts: list[pd.DataFrame] = []
    betas: dict[str, dict] = {}
    frame_year = pd.to_datetime(frame["trading_day"]).dt.year

    for valid_year in YEARS:
        train = frame.loc[frame_year < valid_year].copy()
        valid = frame.loc[frame_year == valid_year].copy()
        train_mask = common_mask(train, base_features)
        valid_mask = common_mask(valid, base_features)
        if int(train_mask.sum()) == 0 or int(valid_mask.sum()) == 0:
            raise RuntimeError(f"empty OHR-08 common fold for {valid_year}")

        x_train = train.loc[train_mask, base_features].apply(pd.to_numeric, errors="coerce")
        y_train = pd.to_numeric(train.loc[train_mask, "gap"], errors="coerce").to_numpy(dtype=float)
        x_valid = valid.loc[valid_mask, base_features].apply(pd.to_numeric, errors="coerce")
        g_train = pd.to_numeric(train.loc[train_mask, G], errors="coerce").to_numpy(dtype=float)
        g_valid = pd.to_numeric(valid.loc[valid_mask, G], errors="coerce").to_numpy(dtype=float)

        base = phase2.median_pipe()
        base.fit(x_train, y_train)
        base_train_score = np.asarray(base.predict(x_train), dtype=float)
        base_valid_score = np.asarray(base.predict(x_valid), dtype=float)

        residual = y_train - base_train_score
        if int(np.sum(np.abs(g_train) > EPS)) == 0:
            raise RuntimeError(f"OHR-08 training fold {valid_year} has no nonzero g observations")
        overlay = QuantileRegressor(quantile=0.5, alpha=0.0, fit_intercept=False, solver="highs")
        overlay.fit(g_train.reshape(-1, 1), residual)
        beta = float(np.asarray(overlay.coef_, dtype=float)[0])
        if abs(float(overlay.intercept_)) > EPS:
            raise RuntimeError("OHR-08 overlay unexpectedly fit an intercept")

        correction = beta * g_valid
        candidate_score = np.where(np.abs(g_valid) <= EPS, base_valid_score, base_valid_score + correction)

        part_cols = ["trading_day", "gap", "prev_last_hour"]
        inc = valid.loc[valid_mask, part_cols].copy()
        inc["score"] = base_valid_score
        inc["pred_up"] = inc["score"] >= 0.0
        inc["oof_year"] = int(valid_year)
        inc[G] = g_valid

        cand = valid.loc[valid_mask, part_cols].copy()
        cand["score"] = candidate_score
        cand["pred_up"] = cand["score"] >= 0.0
        cand["oof_year"] = int(valid_year)
        cand[G] = g_valid

        non_tail = pd.to_numeric(inc["prev_last_hour"], errors="coerce").to_numpy(dtype=float) >= 0.0
        if not np.array_equal(inc.loc[non_tail, "score"].to_numpy(), cand.loc[non_tail, "score"].to_numpy()):
            raise RuntimeError(f"OHR-08 changed a non-tail score in {valid_year}")
        if not np.array_equal(inc.loc[non_tail, "pred_up"].to_numpy(), cand.loc[non_tail, "pred_up"].to_numpy()):
            raise RuntimeError(f"OHR-08 changed a non-tail prediction in {valid_year}")

        inc_parts.append(inc)
        cand_parts.append(cand)
        betas[str(valid_year)] = {
            "beta": beta,
            "n_train_common": int(train_mask.sum()),
            "n_train_nonzero_g": int(np.sum(np.abs(g_train) > EPS)),
            "n_valid_common": int(valid_mask.sum()),
            "n_valid_nonzero_g": int(np.sum(np.abs(g_valid) > EPS)),
        }

    incumbent_oof = pd.concat(inc_parts, ignore_index=True)
    candidate_oof = pd.concat(cand_parts, ignore_index=True)
    if (pd.to_datetime(incumbent_oof["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered OHR-08 OOF")
    if incumbent_oof["trading_day"].tolist() != candidate_oof["trading_day"].tolist():
        raise RuntimeError("OHR-08 incumbent/candidate inventory mismatch")
    return incumbent_oof, candidate_oof, betas


def annual_metrics(pred: pd.DataFrame) -> dict:
    return {str(y): phase2.score_metrics(pred.loc[pred["oof_year"] == y]) for y in YEARS}


def flip_morphology(inc: pd.DataFrame, cand: pd.DataFrame) -> dict:
    actual = pd.to_numeric(inc["gap"], errors="coerce").to_numpy(dtype=float) >= 0.0
    i = inc["pred_up"].to_numpy(dtype=bool)
    c = cand["pred_up"].to_numpy(dtype=bool)
    added = (~i) & c
    removed = i & (~c)
    return {
        "incumbent_down_to_candidate_up": int(added.sum()),
        "rescued_high": int(np.sum(added & actual)),
        "new_false_high": int(np.sum(added & (~actual))),
        "added_up_precision": None if int(added.sum()) == 0 else float(np.sum(added & actual) / added.sum()),
        "incumbent_up_to_candidate_down": int(removed.sum()),
        "lost_high": int(np.sum(removed & actual)),
        "repaired_false_high": int(np.sum(removed & (~actual))),
    }


def subset_metrics(pred: pd.DataFrame, weak: bool) -> dict:
    mask = pd.to_numeric(pred["prev_last_hour"], errors="coerce") < 0.0
    return phase2.score_metrics(pred.loc[mask if weak else ~mask])


def spec(protocol: dict, base_features: list[str]) -> dict:
    return {
        "name": protocol["single_candidate"]["name"],
        "stage_1": {
            "pipeline": protocol["fixed_incumbent"]["pipeline"],
            "direction_features": base_features,
            "fit_target": "gap"
        },
        "stage_2": {
            "feature": G,
            "target": "gap - frozen_incumbent_training_score",
            "model": protocol["single_candidate"]["stage_2_model"]
        },
        "score": "frozen_incumbent_score + beta * broad_china_specific_tail_weak",
        "decision": "score >= 0",
        "offshore_source_sha256": EXPECTED_SOURCE_SHA,
        "development_selection_window": "2016-2025_expanding_natural_year_OOF_common_offshore_inventory",
        "repeat_blackbox": "2026-01-05_to_2026-08-21_after_exact_successor_freeze_only",
        "true_fresh_reserved": "post_2026-08-21"
    }


def main() -> int:
    protocol = load_json(PROTOCOL)
    incumbent = load_json(INCUMBENT)
    ohr06_receipt = load_json(OHR06_RECEIPT)
    ohr07_receipt = load_json(OHR07_RECEIPT)

    if incumbent["selected_spec_sha256"] != INCUMBENT_SPEC_SHA:
        raise RuntimeError("OHR-08 incumbent SHA mismatch")
    if protocol["multiplicity"] != 1:
        raise RuntimeError("OHR-08 multiplicity drifted")
    if protocol["accepted_source"]["sha256"] != EXPECTED_SOURCE_SHA or sha256(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("OHR-08 source identity drifted")
    if ohr06_receipt["china_specific_passers"] != ["broad_china_specific_vs_spy"]:
        raise RuntimeError("OHR-06 mechanism identity drifted")
    if ohr07_receipt["decision"] != "retain_incumbent_close_offshore_route_do_not_open_repeat_blackbox":
        raise RuntimeError("OHR-07 was not the expected rejected joint-refit candidate")
    if ohr07_receipt["2026_rows_loaded"] or ohr07_receipt["2026_blackbox_opened"]:
        raise RuntimeError("OHR-07 evidence boundary invalid")

    base_features = list(incumbent["selected_spec"]["direction_features"])
    source = ohr06.load_frozen_source(SOURCE)
    frame, reconstruction = highdiag.build_development_frame()
    frame, clock_audit = ohr06.attach_offshore_states(frame, source)
    frame = add_g(frame)
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered OHR-08 development frame")

    incumbent_oof, candidate_oof, betas = run_expanding_overlay(frame, base_features)
    if len(incumbent_oof) != int(ohr06_receipt["n_common_offshore_oof"]):
        raise RuntimeError("OHR-08 common OOF inventory differs from OHR-06")

    non_tail = pd.to_numeric(incumbent_oof["prev_last_hour"], errors="coerce") >= 0.0
    non_tail_score_max_abs = float(np.max(np.abs(
        pd.to_numeric(candidate_oof.loc[non_tail, "score"], errors="coerce").to_numpy(dtype=float)
        - pd.to_numeric(incumbent_oof.loc[non_tail, "score"], errors="coerce").to_numpy(dtype=float)
    ))) if int(non_tail.sum()) else 0.0
    non_tail_predictions_identical = bool(np.array_equal(
        candidate_oof.loc[non_tail, "pred_up"].to_numpy(dtype=bool),
        incumbent_oof.loc[non_tail, "pred_up"].to_numpy(dtype=bool),
    ))

    inc_metrics = phase2.score_metrics(incumbent_oof)
    cand_metrics = phase2.score_metrics(candidate_oof)
    inc_annual = annual_metrics(incumbent_oof)
    cand_annual = annual_metrics(candidate_oof)
    deltas = {str(y): float(cand_annual[str(y)]["recall_up"] - inc_annual[str(y)]["recall_up"]) for y in YEARS}
    positive_years = int(sum(v > EPS for v in deltas.values()))
    median_delta = float(np.median(list(deltas.values())))

    gates = {
        "recall_up_strictly_higher": cand_metrics["recall_up"] > inc_metrics["recall_up"] + EPS,
        "direction_hit_not_lower": cand_metrics["direction_hit"] >= inc_metrics["direction_hit"] - EPS,
        "balanced_accuracy_not_lower": cand_metrics["balanced_accuracy"] >= inc_metrics["balanced_accuracy"] - EPS,
        "recall_down_above_half": cand_metrics["recall_down"] > 0.5,
        "positive_annual_recall_up_delta_at_least_6": positive_years >= 6,
        "median_annual_recall_up_delta_nonnegative": median_delta >= -EPS,
        "material_gt10bp_recall_not_lower": cand_metrics["material_high_open_gt10bp_recall"] >= inc_metrics["material_high_open_gt10bp_recall"] - EPS,
        "material_gt30bp_recall_not_lower": cand_metrics["material_high_open_gt30bp_recall"] >= inc_metrics["material_high_open_gt30bp_recall"] - EPS,
        "non_tail_predictions_identical_to_incumbent": non_tail_predictions_identical and non_tail_score_max_abs <= EPS,
    }
    eligible = bool(all(gates.values()))
    candidate_spec = spec(protocol, base_features)
    candidate_spec_sha = canonical_digest(candidate_spec)

    attempt = {
        "name": protocol["single_candidate"]["name"],
        "metrics": cand_metrics,
        "annual_metrics": cand_annual,
        "annual_recall_up_delta": deltas,
        "positive_annual_recall_up_delta_count": positive_years,
        "median_annual_recall_up_delta": median_delta,
        "fold_betas": betas,
        "non_tail_score_max_abs_difference": non_tail_score_max_abs,
        "non_tail_predictions_identical": non_tail_predictions_identical,
        "paired_disagreement_counts": phase2.paired_counts(incumbent_oof, candidate_oof),
        "flip_morphology": flip_morphology(incumbent_oof, candidate_oof),
        "tail_weak_metrics": {
            "incumbent": subset_metrics(incumbent_oof, True),
            "candidate": subset_metrics(candidate_oof, True),
        },
        "non_tail_weak_metrics": {
            "incumbent": subset_metrics(incumbent_oof, False),
            "candidate": subset_metrics(candidate_oof, False),
        },
        "eligibility_gates": gates,
        "eligible": eligible,
        "candidate_spec": candidate_spec,
        "candidate_spec_sha256": candidate_spec_sha,
    }

    receipt = {
        "schema_id": "overnight_open_offshore_china_ohr08_dev_receipt@1.0",
        "session_date": "2026-09-06",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": sha256(PROTOCOL),
        "incumbent_spec_sha256": INCUMBENT_SPEC_SHA,
        "source_sha256": EXPECTED_SOURCE_SHA,
        "development_window": {"start": highdiag.DEV_START, "end": highdiag.DEV_END},
        "oof_years": YEARS,
        "n_oof_common": int(len(incumbent_oof)),
        "incumbent_common_metrics": inc_metrics,
        "incumbent_common_annual_metrics": inc_annual,
        "attempts": [attempt],
        "eligible_candidate_count": int(eligible),
        "selected": None if not eligible else {
            "name": attempt["name"],
            "candidate_spec": candidate_spec,
            "candidate_spec_sha256": candidate_spec_sha,
            "metrics": cand_metrics,
            "fold_betas": betas,
            "positive_annual_recall_up_delta_count": positive_years,
            "median_annual_recall_up_delta": median_delta,
            "paired_disagreement_counts": attempt["paired_disagreement_counts"],
            "flip_morphology": attempt["flip_morphology"],
        },
        "decision": "freeze_exact_two_stage_successor_before_repeat_blackbox" if eligible else "close_offshore_china_route_retain_incumbent_do_not_open_2026",
        "clock_audit": clock_audit,
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "offshore_etf_daily": sha256(SOURCE),
            "annotated_panel": sha256(highdiag.ANNOTATED_PANEL),
            "datahub_1m_export": sha256(highdiag.DATAHUB_1M),
            "fred_nasdaq": sha256(highdiag.FRED_NDQ),
            "fred_vix": sha256(highdiag.FRED_VIX),
            "incumbent": sha256(INCUMBENT),
            "ohr06_receipt": sha256(OHR06_RECEIPT),
            "ohr07_receipt": sha256(OHR07_RECEIPT),
            "protocol": sha256(PROTOCOL),
            "runner": sha256(Path(__file__)),
        },
        "candidate_selection_performed": True,
        "parameter_search_performed": False,
        "beta_grid_search_performed": False,
        "threshold_search_performed": False,
        "quantile_search_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "2026_blackbox_opened": False,
        "ohr_03_opened": False,
        "raw_rows_newly_written_by_runner": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)

    usage = {
        "schema_id": "overnight_open_offshore_china_ohr08_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31_final_one_parameter_frozen_base_overlay_test",
        "offshore_source_sha256": EXPECTED_SOURCE_SHA,
        "candidate_selection_performed": True,
        "beta_grid_search_performed": False,
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_rows_newly_written_by_runner": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)

    print("OFFSHORE_CHINA_OHR08_SELECTION_RESULT", json.dumps({
        "n_oof_common": receipt["n_oof_common"],
        "eligible_candidate_count": receipt["eligible_candidate_count"],
        "selected": receipt["selected"],
        "decision": receipt["decision"],
        "non_tail_score_max_abs_difference": non_tail_score_max_abs,
        "2026_blackbox_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
