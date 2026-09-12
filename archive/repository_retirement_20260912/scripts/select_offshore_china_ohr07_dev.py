#!/usr/bin/env python3
"""OHR-07 development-only selection for the single offshore-China successor.

The family is frozen before execution. This script uses only 2015-2025
material, the exact OHR-05 Yahoo source bytes, and 2016-2025 expanding-year OOF.
It must never load 2026.
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

import diagnose_high_open_false_negatives_dev as highdiag
import diagnose_offshore_china_price_discovery_dev as ohr06
import select_high_open_recall_phase2_dev as phase2

FAMILY = ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr07_family_v1.json"
INCUMBENT = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
OHR06_RECEIPT = ROOT / "docs/research/cloud_session_20260906_local_offshore_china_ohr06_diagnostic_receipt_v1.json"
SOURCE = ROOT / "data/offshore_etf_dev_2015_2025/offshore_etf_daily.parquet"
OUT = ROOT / "docs/research/cloud_session_20260906_cloud_offshore_china_ohr07_dev_receipt_v1.json"
USAGE = ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr07_data_usage.json"

EXPECTED_SOURCE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
INCUMBENT_SPEC_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
YEARS = list(range(2016, 2026))
EXTRA = "broad_china_specific_tail_weak"
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


def add_candidate_feature(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    broad = pd.to_numeric(out["broad_china_specific_vs_spy"], errors="coerce")
    prev_last = pd.to_numeric(out["prev_last_hour"], errors="coerce")
    valid = out["offshore_common_valid"].astype(bool)
    value = broad * (prev_last < 0.0).astype(float)
    out[EXTRA] = np.where(valid, value, np.nan)
    return out


def common_mask(frame: pd.DataFrame, common_cols: list[str]) -> pd.Series:
    x = frame[common_cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    valid = frame["offshore_common_valid"].astype(bool)
    return x.notna().all(axis=1) & y.notna() & valid


def expanding_oof_fixed_common(frame: pd.DataFrame, cols: list[str], common_cols: list[str]) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    years = pd.to_datetime(frame["trading_day"]).dt.year
    for valid_year in YEARS:
        train = frame.loc[years < valid_year].copy()
        valid = frame.loc[years == valid_year].copy()
        train_mask = common_mask(train, common_cols)
        valid_mask = common_mask(valid, common_cols)
        if int(train_mask.sum()) == 0 or int(valid_mask.sum()) == 0:
            raise RuntimeError(f"empty fixed-common fold for {valid_year}")

        pipe = phase2.median_pipe()
        x_train = train.loc[train_mask, cols].apply(pd.to_numeric, errors="coerce")
        y_train = pd.to_numeric(train.loc[train_mask, "gap"], errors="coerce")
        if x_train.isna().any().any() or y_train.isna().any():
            raise RuntimeError(f"unexpected missing training row in {valid_year}")
        pipe.fit(x_train, y_train)

        part = valid.loc[valid_mask, ["trading_day", "gap", "prev_last_hour"]].copy()
        x_valid = valid.loc[valid_mask, cols].apply(pd.to_numeric, errors="coerce")
        part["score"] = np.asarray(pipe.predict(x_valid), dtype=float)
        part["pred_up"] = part["score"] >= 0.0
        part["oof_year"] = int(valid_year)
        pieces.append(part)

    out = pd.concat(pieces, ignore_index=True)
    if len(out) == 0 or int(pd.to_datetime(out["trading_day"]).dt.year.max()) != 2025:
        raise RuntimeError("OHR-07 OOF did not end in 2025")
    if (pd.to_datetime(out["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered OHR-07 OOF")
    return out


def annual_metrics(pred: pd.DataFrame) -> dict:
    return {str(y): phase2.score_metrics(pred.loc[pred["oof_year"] == y]) for y in YEARS}


def flip_morphology(inc: pd.DataFrame, cand: pd.DataFrame) -> dict:
    if inc["trading_day"].tolist() != cand["trading_day"].tolist():
        raise RuntimeError("OHR-07 incumbent/candidate inventory mismatch")
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
    part = pred.loc[mask if weak else ~mask]
    return phase2.score_metrics(part)


def candidate_spec(base_features: list[str], family: dict) -> dict:
    return {
        "name": "broad_china_specific_tail_weak_piecewise",
        "pipeline": family["fixed_estimator"]["pipeline"],
        "fit_target": "gap",
        "decision": "prediction >= 0",
        "direction_features": base_features + [EXTRA],
        "derived_feature_definitions": family["derived_feature_definitions"],
        "offshore_source_sha256": EXPECTED_SOURCE_SHA,
        "development_selection_window": "2016-2025_expanding_natural_year_OOF_common_offshore_inventory",
        "repeat_blackbox": "2026-01-05_to_2026-08-21_after_exact_successor_freeze_only",
        "true_fresh_reserved": "post_2026-08-21",
    }


def main() -> int:
    family = load_json(FAMILY)
    incumbent = load_json(INCUMBENT)
    diag = load_json(OHR06_RECEIPT)

    if incumbent["selected_spec_sha256"] != INCUMBENT_SPEC_SHA:
        raise RuntimeError("OHR-07 incumbent SHA mismatch")
    if family["multiplicity"] != 1 or len(family["candidates"]) != 1:
        raise RuntimeError("OHR-07 family multiplicity drifted")
    if family["candidates"][0]["extra_features"] != [EXTRA]:
        raise RuntimeError("OHR-07 candidate drifted")
    if family["fixed_estimator"]["quantile"] != 0.5 or family["fixed_estimator"]["alpha"] != 0.0 or family["fixed_estimator"]["threshold"] != 0.0:
        raise RuntimeError("OHR-07 estimator drifted")
    if family["accepted_source"]["source_sha256"] != EXPECTED_SOURCE_SHA or sha256(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("OHR-07 frozen offshore source drifted")
    if diag["china_specific_passers"] != ["broad_china_specific_vs_spy"] or not diag["later_bounded_candidate_family_authorized"]:
        raise RuntimeError("OHR-06 did not authorize this exact family")
    if diag["2026_rows_loaded"] or diag["2026_blackbox_opened"]:
        raise RuntimeError("OHR-06 evidence boundary invalid")

    base_features = list(family["base_features"])
    if base_features != list(incumbent["selected_spec"]["direction_features"]):
        raise RuntimeError("OHR-07 base features differ from incumbent")

    source = ohr06.load_frozen_source(SOURCE)
    frame, reconstruction = highdiag.build_development_frame()
    frame, clock_audit = ohr06.attach_offshore_states(frame, source)
    frame = add_candidate_feature(frame)
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered OHR-07 development frame")

    common_cols = base_features + [EXTRA]
    incumbent_oof = expanding_oof_fixed_common(frame, base_features, common_cols)
    candidate_oof = expanding_oof_fixed_common(frame, base_features + [EXTRA], common_cols)
    if len(incumbent_oof) != int(diag["n_common_offshore_oof"]):
        raise RuntimeError("OHR-07 common OOF inventory differs from OHR-06")

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
    }
    eligible = bool(all(gates.values()))
    spec = candidate_spec(base_features, family)
    spec_sha = canonical_digest(spec)

    attempt = {
        "name": family["candidates"][0]["name"],
        "extra_features": [EXTRA],
        "metrics": cand_metrics,
        "annual_metrics": cand_annual,
        "annual_recall_up_delta": deltas,
        "positive_annual_recall_up_delta_count": positive_years,
        "median_annual_recall_up_delta": median_delta,
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
        "candidate_spec": spec,
        "candidate_spec_sha256": spec_sha,
    }

    receipt = {
        "schema_id": "overnight_open_offshore_china_ohr07_dev_receipt@1.0",
        "session_date": "2026-09-06",
        "family": str(FAMILY.relative_to(ROOT)),
        "family_sha256": sha256(FAMILY),
        "ohr06_receipt": str(OHR06_RECEIPT.relative_to(ROOT)),
        "ohr06_receipt_sha256": sha256(OHR06_RECEIPT),
        "incumbent_spec_sha256": INCUMBENT_SPEC_SHA,
        "source_sha256": EXPECTED_SOURCE_SHA,
        "development_window": {"start": highdiag.DEV_START, "end": highdiag.DEV_END},
        "oof_years": YEARS,
        "n_oof_common": int(len(incumbent_oof)),
        "common_inventory_note": "incumbent and candidate are both refit/evaluated on the same offshore-valid complete-row mask; these are comparator metrics, not a replacement for the accepted incumbent receipt",
        "incumbent_common_metrics": inc_metrics,
        "incumbent_common_annual_metrics": inc_annual,
        "attempts": [attempt],
        "eligible_candidate_count": int(eligible),
        "selected": None if not eligible else {
            "name": attempt["name"],
            "candidate_spec": spec,
            "candidate_spec_sha256": spec_sha,
            "metrics": cand_metrics,
            "positive_annual_recall_up_delta_count": positive_years,
            "median_annual_recall_up_delta": median_delta,
            "paired_disagreement_counts": attempt["paired_disagreement_counts"],
            "flip_morphology": attempt["flip_morphology"],
        },
        "decision": "freeze_exact_successor_before_repeat_blackbox" if eligible else "retain_incumbent_close_offshore_route_do_not_open_repeat_blackbox",
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
            "family": sha256(FAMILY),
            "runner": sha256(Path(__file__)),
        },
        "candidate_selection_performed": True,
        "parameter_search_performed": False,
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
        "schema_id": "overnight_open_offshore_china_ohr07_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31_single_frozen_candidate_selection",
        "offshore_source_sha256": EXPECTED_SOURCE_SHA,
        "offshore_cloud_pack": str(SOURCE.relative_to(ROOT)),
        "candidate_selection_performed": True,
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_source_pack_preexisted_runner": True,
        "raw_rows_newly_written_by_runner": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)

    print("OFFSHORE_CHINA_OHR07_SELECTION_RESULT", json.dumps({
        "eligible_candidate_count": int(eligible),
        "selected": receipt["selected"],
        "decision": receipt["decision"],
        "n_oof_common": receipt["n_oof_common"],
        "2026_blackbox_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
