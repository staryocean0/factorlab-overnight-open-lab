#!/usr/bin/env python3
"""Development-only Phase-2 selection for the high-open recall successor.

The candidate family is frozen in
`docs/governance/cloud_session_20260906_high_open_recall_phase2_family_v1.json`.
This runner uses only 2015-2025 development material and expanding natural-year
OOF predictions for 2016-2025. It must not load or inspect any 2026 row.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_local_2021_2025_two_head as local

local.ANNOTATED_PANEL = Path(os.environ.get("OVERNIGHT_ANNOTATED_PANEL", str(local.ANNOTATED_PANEL)))
local.DATAHUB_1M = Path(os.environ.get("OVERNIGHT_DATAHUB_1M", str(local.DATAHUB_1M)))
local.FRED_NDQ = Path(os.environ.get("OVERNIGHT_FRED_NASDAQ", str(local.FRED_NDQ)))
local.FRED_VIX = Path(os.environ.get("OVERNIGHT_FRED_VIX", str(local.FRED_VIX)))

ANNOTATED_PANEL = local.ANNOTATED_PANEL
DATAHUB_1M = local.DATAHUB_1M
FRED_NDQ = local.FRED_NDQ
FRED_VIX = local.FRED_VIX

DEV_START = "2015-01-05"
DEV_END = "2025-12-31"
OOF_YEARS = list(range(2016, 2026))
INCUMBENT_PATH = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
FAMILY_PATH = ROOT / "docs/governance/cloud_session_20260906_high_open_recall_phase2_family_v1.json"
RECEIPT_PATH = ROOT / "docs/research/cloud_session_20260906_local_high_open_recall_phase2_dev_receipt_v1.json"
DATA_USAGE_PATH = ROOT / "docs/governance/local_session_20260906_high_open_recall_phase2_data_usage.json"
INCUMBENT_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
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


def median_pipe() -> Pipeline:
    return Pipeline(
        [
            ("sc", StandardScaler()),
            ("model", QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")),
        ]
    )


def complete_mask(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    return x.notna().all(axis=1) & y.notna()


def add_weakness_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["prev_daytime_weakness"] = np.maximum(-pd.to_numeric(out["prev_daytime"], errors="coerce"), 0.0)
    out["prev_afternoon_weakness"] = np.maximum(-pd.to_numeric(out["prev_afternoon"], errors="coerce"), 0.0)
    out["prev_last_hour_weakness"] = np.maximum(-pd.to_numeric(out["prev_last_hour"], errors="coerce"), 0.0)
    return out


def build_development_frame() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_parquet(
        ANNOTATED_PANEL,
        filters=[("trading_day", ">=", DEV_START), ("trading_day", "<=", DEV_END)],
    )
    raw["trading_day"] = raw["trading_day"].astype(str)
    if raw.empty:
        raise RuntimeError("development annotated panel is empty")
    if str(pd.to_datetime(raw["trading_day"]).max().date()) > DEV_END:
        raise RuntimeError("development loader crossed into 2026")

    hours = local.load_hours(DATAHUB_1M, DEV_START, DEV_END)
    us = local.load_us(FRED_NDQ, FRED_VIX, max_date=DEV_END)
    frame = local.add_domestic_features(raw, hours)
    frame = local.attach_us(frame, us)
    frame = add_weakness_features(frame)

    day = pd.to_datetime(frame["trading_day"])
    frame = frame.loc[(day >= DEV_START) & (day <= DEV_END)].copy()
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered Phase-2 development frame")

    frozen = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    reconstruction = local.assert_dev_reconstruction(frozen)
    return frame, reconstruction


def rank_auc(actual_up: np.ndarray, score: np.ndarray) -> float | None:
    y = np.asarray(actual_up, dtype=bool)
    if np.unique(y.astype(int)).size != 2:
        return None
    ranks = pd.Series(score).rank(method="average").to_numpy(dtype=float)
    n_pos = int(y.sum())
    n_neg = int((~y).sum())
    rank_sum_pos = float(ranks[y].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def score_metrics(pred: pd.DataFrame) -> dict:
    y = pd.to_numeric(pred["gap"], errors="coerce").to_numpy(dtype=float)
    actual_up = y >= 0.0
    pred_up = pred["pred_up"].to_numpy(dtype=bool)
    score = pd.to_numeric(pred["score"], errors="coerce").to_numpy(dtype=float)
    correct = actual_up == pred_up
    tp = int(np.sum(actual_up & pred_up))
    fn = int(np.sum(actual_up & (~pred_up)))
    tn = int(np.sum((~actual_up) & (~pred_up)))
    fp = int(np.sum((~actual_up) & pred_up))
    recall_up = tp / (tp + fn)
    recall_down = tn / (tn + fp)

    material10 = y > 0.001
    material30 = y > 0.003
    return {
        "n": int(len(pred)),
        "direction_hit": float(np.mean(correct)),
        "correct_count": int(correct.sum()),
        "balanced_accuracy": float(0.5 * (recall_up + recall_down)),
        "recall_up": float(recall_up),
        "recall_down": float(recall_down),
        "actual_up_share": float(np.mean(actual_up)),
        "pred_up_share": float(np.mean(pred_up)),
        "roc_auc": rank_auc(actual_up, score),
        "material_high_open_gt10bp_recall": float(np.mean(pred_up[material10])) if int(material10.sum()) else None,
        "material_high_open_gt30bp_recall": float(np.mean(pred_up[material30])) if int(material30.sum()) else None,
        "tp": tp,
        "fn": fn,
        "tn": tn,
        "fp": fp,
    }


def expanding_oof(frame: pd.DataFrame, cols: list[str], common_cols: list[str]) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    years = pd.to_datetime(frame["trading_day"]).dt.year
    for valid_year in OOF_YEARS:
        train = frame.loc[years < valid_year].copy()
        valid = frame.loc[years == valid_year].copy()
        common_train = complete_mask(train, common_cols)
        common_valid = complete_mask(valid, common_cols)
        candidate_train = complete_mask(train, cols)
        candidate_valid = complete_mask(valid, cols)
        if not candidate_train.equals(common_train) or not candidate_valid.equals(common_valid):
            raise RuntimeError(f"candidate changed complete-row mask in {valid_year}")
        if int(common_train.sum()) == 0 or int(common_valid.sum()) == 0:
            raise RuntimeError(f"empty complete fold for {valid_year}")

        pipe = median_pipe()
        x_train = train.loc[common_train, cols].apply(pd.to_numeric, errors="coerce")
        y_train = pd.to_numeric(train.loc[common_train, "gap"], errors="coerce")
        pipe.fit(x_train, y_train)

        part = valid.loc[common_valid, ["trading_day", "gap"]].copy()
        x_valid = valid.loc[common_valid, cols].apply(pd.to_numeric, errors="coerce")
        part["score"] = np.asarray(pipe.predict(x_valid), dtype=float)
        part["pred_up"] = part["score"] >= 0.0
        part["oof_year"] = int(valid_year)
        pieces.append(part)

    out = pd.concat(pieces, ignore_index=True)
    if out.empty or int(pd.to_datetime(out["trading_day"]).dt.year.max()) != 2025:
        raise RuntimeError("Phase-2 OOF did not end in 2025")
    if (pd.to_datetime(out["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered Phase-2 OOF")
    return out


def annual_metrics(pred: pd.DataFrame) -> dict:
    return {
        str(year): score_metrics(pred.loc[pred["oof_year"] == year])
        for year in OOF_YEARS
    }


def paired_counts(incumbent: pd.DataFrame, candidate: pd.DataFrame) -> dict:
    if incumbent["trading_day"].tolist() != candidate["trading_day"].tolist():
        raise RuntimeError("candidate OOF day inventory differs from incumbent")
    y = pd.to_numeric(incumbent["gap"], errors="coerce").to_numpy(dtype=float) >= 0.0
    inc_correct = incumbent["pred_up"].to_numpy(dtype=bool) == y
    cand_correct = candidate["pred_up"].to_numpy(dtype=bool) == y
    return {
        "candidate_correct_incumbent_wrong": int(np.sum(cand_correct & (~inc_correct))),
        "incumbent_correct_candidate_wrong": int(np.sum(inc_correct & (~cand_correct))),
        "total_disagreements": int(np.sum(cand_correct != inc_correct)),
    }


def candidate_spec(name: str, features: list[str], family: dict) -> dict:
    return {
        "name": name,
        "pipeline": family["fixed_estimator"]["pipeline"],
        "fit_target": "gap",
        "decision": "prediction >= 0",
        "direction_features": features,
        "derived_feature_definitions": family["derived_feature_definitions"],
        "development_selection_window": "2016-2025_expanding_natural_year_OOF",
        "eligible_repeat_blackbox": "2026-01-05_to_2026-08-21_after_freeze_only",
        "true_fresh_reserved": "post_2026-08-21",
    }


def main() -> int:
    family = load_json(FAMILY_PATH)
    incumbent = load_json(INCUMBENT_PATH)
    if incumbent["selected_spec_sha256"] != INCUMBENT_SHA:
        raise RuntimeError("incumbent direction SHA mismatch")
    if family["multiplicity"] != 4 or len(family["candidates"]) != 4:
        raise RuntimeError("unexpected Phase-2 multiplicity")
    if family["fixed_estimator"]["quantile"] != 0.5 or family["fixed_estimator"]["threshold"] != 0.0:
        raise RuntimeError("Phase-2 estimator or threshold drifted")
    if family["evidence_boundary"]["sealed_repeat_blackbox"] != "2026-01-05_to_2026-08-21":
        raise RuntimeError("2026 repeat-blackbox boundary drifted")

    base_features = list(family["base_features"])
    if base_features != list(incumbent["selected_spec"]["direction_features"]):
        raise RuntimeError("Phase-2 base features differ from incumbent")

    frame, reconstruction = build_development_frame()
    incumbent_oof = expanding_oof(frame, base_features, base_features)
    incumbent_metrics = score_metrics(incumbent_oof)
    incumbent_annual = annual_metrics(incumbent_oof)

    attempts: list[dict] = []
    allowed_extra = set(family["derived_feature_definitions"])
    for registered in family["candidates"]:
        extra = list(registered["extra_features"])
        if not set(extra).issubset(allowed_extra):
            raise RuntimeError(f"unregistered feature in {registered['name']}")
        cols = base_features + extra
        pred = expanding_oof(frame, cols, base_features)
        metrics = score_metrics(pred)
        annual = annual_metrics(pred)
        deltas = {
            year: float(annual[year]["recall_up"] - incumbent_annual[year]["recall_up"])
            for year in sorted(annual)
        }
        positive_years = int(sum(v > EPS for v in deltas.values()))
        median_delta = float(np.median(list(deltas.values())))

        gates = {
            "recall_up_strictly_higher": metrics["recall_up"] > incumbent_metrics["recall_up"] + EPS,
            "direction_hit_not_lower": metrics["direction_hit"] >= incumbent_metrics["direction_hit"] - EPS,
            "balanced_accuracy_not_lower": metrics["balanced_accuracy"] >= incumbent_metrics["balanced_accuracy"] - EPS,
            "recall_down_above_half": metrics["recall_down"] > 0.5,
            "positive_annual_recall_up_delta_at_least_6": positive_years >= 6,
            "median_annual_recall_up_delta_nonnegative": median_delta >= -EPS,
            "material_gt10bp_recall_not_lower": metrics["material_high_open_gt10bp_recall"] >= incumbent_metrics["material_high_open_gt10bp_recall"] - EPS,
            "material_gt30bp_recall_not_lower": metrics["material_high_open_gt30bp_recall"] >= incumbent_metrics["material_high_open_gt30bp_recall"] - EPS,
        }
        eligible = bool(all(gates.values()))
        spec = candidate_spec(registered["name"], cols, family)
        attempts.append(
            {
                "name": registered["name"],
                "extra_features": extra,
                "extra_feature_count": int(registered["extra_feature_count"]),
                "metrics": metrics,
                "annual_metrics": annual,
                "annual_recall_up_delta": deltas,
                "positive_annual_recall_up_delta_count": positive_years,
                "median_annual_recall_up_delta": median_delta,
                "paired_disagreement_counts": paired_counts(incumbent_oof, pred),
                "eligibility_gates": gates,
                "eligible": eligible,
                "candidate_spec": spec,
                "candidate_spec_sha256": canonical_digest(spec),
            }
        )

    eligible = [a for a in attempts if a["eligible"]]
    selected = None
    if eligible:
        selected = sorted(
            eligible,
            key=lambda a: (
                -a["metrics"]["recall_up"],
                -a["metrics"]["balanced_accuracy"],
                -a["metrics"]["direction_hit"],
                a["extra_feature_count"],
                a["name"],
            ),
        )[0]

    receipt = {
        "schema_id": "overnight_open_high_open_recall_phase2_dev_receipt@1.0",
        "session_date": "2026-09-06",
        "family": str(FAMILY_PATH.relative_to(ROOT)),
        "family_sha256": sha256(FAMILY_PATH),
        "incumbent": str(INCUMBENT_PATH.relative_to(ROOT)),
        "incumbent_spec_sha256": INCUMBENT_SHA,
        "development_window": {"start": DEV_START, "end": DEV_END},
        "oof_years": OOF_YEARS,
        "n_oof": int(len(incumbent_oof)),
        "incumbent_metrics": incumbent_metrics,
        "incumbent_annual_metrics": incumbent_annual,
        "attempts": attempts,
        "eligible_candidate_count": int(len(eligible)),
        "selected": None if selected is None else {
            "name": selected["name"],
            "candidate_spec": selected["candidate_spec"],
            "candidate_spec_sha256": selected["candidate_spec_sha256"],
            "metrics": selected["metrics"],
            "positive_annual_recall_up_delta_count": selected["positive_annual_recall_up_delta_count"],
            "median_annual_recall_up_delta": selected["median_annual_recall_up_delta"],
            "paired_disagreement_counts": selected["paired_disagreement_counts"],
        },
        "decision": "freeze_selected_successor_before_repeat_blackbox" if selected is not None else "retain_incumbent_do_not_open_repeat_blackbox",
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "annotated_panel": sha256(ANNOTATED_PANEL),
            "datahub_1m_export": sha256(DATAHUB_1M),
            "fred_nasdaq": sha256(FRED_NDQ),
            "fred_vix": sha256(FRED_VIX),
            "incumbent": sha256(INCUMBENT_PATH),
            "family": sha256(FAMILY_PATH),
            "runner": sha256(Path(__file__)),
        },
        "candidate_selection_performed": True,
        "parameter_search_performed": False,
        "threshold_search_performed": False,
        "quantile_search_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "2026_blackbox_opened": False,
        "raw_development_rows_written_to_repo": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(RECEIPT_PATH, receipt)

    usage = {
        "schema_id": "overnight_open_local_high_open_recall_phase2_data_usage@1.0",
        "session_date": "2026-09-06",
        "2015-01-05_to_2025-12-31": "development_selection_for_frozen_high_open_phase2_family",
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_rows_persisted_in_bounded_repo": False,
        "production_authority": False,
    }
    dump_json(DATA_USAGE_PATH, usage)

    summary = {
        "incumbent": incumbent_metrics,
        "eligible_candidate_count": len(eligible),
        "selected": receipt["selected"],
        "decision": receipt["decision"],
        "2026_blackbox_opened": False,
    }
    print("HIGH_OPEN_RECALL_PHASE2_SELECTION_RESULT", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
