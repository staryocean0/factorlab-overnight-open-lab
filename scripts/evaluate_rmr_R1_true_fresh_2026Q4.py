#!/usr/bin/env python3
"""One-time frozen evaluator for the R1 parent-integrity 2026Q4 challenge.

This module contains no fitting path. It requires a separate concrete source
admission authorization, reconstructs causal state from the frozen 2015-2025
history plus the admitted 2026 extension, and scores only Q4-confirmed events.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common
import evaluate_rmr_R1_parent_integrity_v2_holdout as frozen_eval

FREEZE = ROOT / "docs/governance/cloud_session_20260908_rmr_R1_parent_integrity_v2_parameter_freeze_v1.json"
PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_parent_integrity_v2_true_fresh_2026Q4_evaluation_protocol_v1.json"
DEFAULT_HISTORICAL = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
HISTORICAL_SHA256 = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
FUTURE_START = "2026-01-05"
FUTURE_END = "2026-12-31"
Q4_START = "2026-10-01"
Q4_END = "2026-12-31"
EARLIEST_EXECUTION_DATE = date(2027, 1, 1)
PAIRINGS = (("PAIR_A", "S1", "S2", 40), ("PAIR_B", "S2", "S3", 15))
EXPECTED_AUTH_SCHEMA = "factorlab_rmr_R1_parent_integrity_v2_true_fresh_execution_authorization@1.0"
EXPECTED_SOURCE_REVIEW_DECISION = "R1_true_fresh_2026Q4_source_admission_cloud_passed"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_execution_date(as_of: date) -> None:
    if as_of < EARLIEST_EXECUTION_DATE:
        raise RuntimeError(
            f"R1 true-fresh Q4 evaluator is sealed until {EARLIEST_EXECUTION_DATE.isoformat()} Asia/Shanghai"
        )


def validate_parameter_freeze() -> dict:
    freeze = load_json(FREEZE)
    expected = freeze["parameter_bundle_sha256"]
    check = dict(freeze)
    check.pop("parameter_bundle_sha256")
    if frozen_eval.json_digest(check) != expected:
        raise RuntimeError("R1 frozen parameter bundle digest mismatch")
    if expected != "e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c":
        raise RuntimeError("R1 parameter bundle identity drifted")
    if freeze["selected_candidate_id"] != "R1_PARENT_COMPOSITE_1D":
        raise RuntimeError("R1 selected candidate drifted")
    if freeze["mechanistic_sign_precondition_passed"] is not True:
        raise RuntimeError("R1 mechanistic sign precondition is not frozen PASS")
    return freeze


def validate_authorization(auth_path: Path, future_source: Path) -> tuple[dict, str]:
    auth = load_json(auth_path)
    if auth.get("schema_id") != EXPECTED_AUTH_SCHEMA:
        raise RuntimeError("not a concrete R1 Q4 execution authorization")
    if auth.get("research_identity") != "rmr_cross_scale_pullback_parent_integrity_v2":
        raise RuntimeError("authorization research identity drifted")
    if auth.get("parameter_bundle_sha256") != "e618a5a06a803f4464267e69e39f98fa316fd572f40efcb3f9e40fc25df2779c":
        raise RuntimeError("authorization parameter bundle drifted")
    if auth.get("selected_candidate_id") != "R1_PARENT_COMPOSITE_1D":
        raise RuntimeError("authorization candidate drifted")
    if auth.get("context_window") != {"start": FUTURE_START, "end": FUTURE_END}:
        raise RuntimeError("authorization context window drifted")
    if auth.get("challenge_window") != {"start": Q4_START, "end": Q4_END}:
        raise RuntimeError("authorization challenge window drifted")
    if auth.get("source_admission_cloud_review_decision") != EXPECTED_SOURCE_REVIEW_DECISION:
        raise RuntimeError("source admission has not received the frozen cloud PASS decision")
    for key in ("source_admission_receipt_sha256", "exact_trading_calendar_sha256"):
        value = str(auth.get(key) or "")
        if len(value) != 64:
            raise RuntimeError(f"authorization missing {key}")
    if auth.get("evaluator_blob_sha") != git_blob_sha(Path(__file__)):
        raise RuntimeError("authorization evaluator blob identity drifted")

    flags = auth.get("authorization_flags", {})
    if flags.get("Q4_R1_outcome_open_authorized") is not True:
        raise RuntimeError("Q4 outcome open is not authorized")
    for key in (
        "R1_refit_authorized",
        "candidate_change_authorized",
        "scale_or_threshold_change_authorized",
        "calibration_authorized",
        "PnL_use_authorized",
        "production_authority",
    ):
        if flags.get(key) is not False:
            raise RuntimeError(f"authorization flag must remain false: {key}")

    actual_future_sha = sha256(future_source)
    if auth.get("exact_2026_extension_source_sha256") != actual_future_sha:
        raise RuntimeError("authorized future source SHA does not match file")
    return auth, actual_future_sha


def read_price_source(path: Path, *, historical: bool) -> pd.DataFrame:
    actual = sha256(path)
    if historical and actual != HISTORICAL_SHA256:
        raise RuntimeError("historical source SHA drifted")
    filters = [("symbol", "==", SYMBOL)]
    if historical:
        filters.append(("trading_day", "<=", "2025-12-31"))
    else:
        filters.extend([("trading_day", ">=", FUTURE_START), ("trading_day", "<=", FUTURE_END)])
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=filters,
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["timestamp"] = frame["timestamp"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.loc[frame["symbol"].eq(SYMBOL)].copy()
    if frame.empty:
        raise RuntimeError("empty authorized price source")
    if not np.isfinite(frame["close"].to_numpy(float)).all() or (frame["close"] <= 0).any():
        raise RuntimeError("invalid close values in authorized source")
    if historical:
        if str(frame["trading_day"].max()) != "2025-12-31":
            raise RuntimeError("historical source end boundary drifted")
    else:
        if str(frame["trading_day"].min()) != FUTURE_START or str(frame["trading_day"].max()) != FUTURE_END:
            raise RuntimeError("future context extension boundaries drifted")
    if not frame["timestamp"].str.slice(0, 10).eq(frame["trading_day"]).all():
        raise RuntimeError("timestamp date does not equal trading_day")
    return frame[["symbol", "trading_day", "timestamp", "close"]].copy()


def combine_sources(historical: pd.DataFrame, future: pd.DataFrame) -> pd.DataFrame:
    frame = pd.concat([historical, future], ignore_index=True)
    frame = frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)
    if frame.duplicated(["symbol", "trading_day", "timestamp"]).any():
        raise RuntimeError("duplicate minute identity across historical/future sources")
    if str(frame["trading_day"].max()) != FUTURE_END:
        raise RuntimeError("combined causal history does not end at 2026-12-31")
    return frame


def q4_pair_result(events: pd.DataFrame, frozen_pair: dict, minimum_resolved: int) -> dict:
    q4_events = events.loc[(events["day"] >= Q4_START) & (events["day"] <= Q4_END)].copy()
    resolved = frozen_eval.resolved_binary(events)
    q4 = resolved.loc[(resolved["day"] >= Q4_START) & (resolved["day"] <= Q4_END)].copy()
    q4 = frozen_eval.add_frozen_integrity(q4, frozen_pair["parent_feature_scaler"])

    outcome_counts = {k: int((q4_events["outcome"] == k).sum()) for k in ("recovery", "failure", "censored")}
    if q4.empty:
        return {
            "inventory": {"all_q4_events": int(len(q4_events)), "resolved": 0, "outcomes": outcome_counts},
            "baseline": None,
            "candidate": None,
            "baseline_minus_candidate_brier": None,
            "baseline_minus_candidate_logloss": None,
            "monthly": {},
            "gates": {"sample_minimum": False, "brier_better": False, "logloss_better": False},
            "passed": False,
        }

    y = q4["y"].to_numpy(int)
    p_base = frozen_eval.frozen_predict(frozen_pair["severity_baseline_model"], q4[["severity"]].to_numpy(float))
    p_cand = frozen_eval.frozen_predict(
        frozen_pair["selected_candidate_model"], q4[["severity", "parent_integrity"]].to_numpy(float)
    )
    base = frozen_eval.metrics(y, p_base)
    cand = frozen_eval.metrics(y, p_cand)
    monthly = {}
    for month in ("2026-10", "2026-11", "2026-12"):
        mask = q4["day"].str.startswith(month).to_numpy()
        monthly[month] = {
            "baseline": frozen_eval.metrics(y[mask], p_base[mask]),
            "candidate": frozen_eval.metrics(y[mask], p_cand[mask]),
            "resolved": int(mask.sum()),
            "descriptive_only": True,
        }
    gates = {
        "sample_minimum": len(q4) >= minimum_resolved,
        "brier_better": cand["brier"] < base["brier"],
        "logloss_better": cand["log_loss"] < base["log_loss"],
    }
    return {
        "inventory": {"all_q4_events": int(len(q4_events)), "resolved": int(len(q4)), "outcomes": outcome_counts},
        "baseline": base,
        "candidate": cand,
        "baseline_minus_candidate_brier": float(base["brier"] - cand["brier"]),
        "baseline_minus_candidate_logloss": float(base["log_loss"] - cand["log_loss"]),
        "monthly": monthly,
        "gates": gates,
        "passed": all(gates.values()),
    }


def decide(pair_results: dict) -> str:
    if not all(v["gates"]["sample_minimum"] for v in pair_results.values()):
        return "R1_parent_integrity_v2_true_fresh_2026Q4_evidence_insufficient"
    if all(v["passed"] for v in pair_results.values()):
        return "R1_parent_integrity_v2_true_fresh_2026Q4_confirmed"
    return "R1_parent_integrity_v2_true_fresh_2026Q4_failed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical-source", type=Path, default=DEFAULT_HISTORICAL)
    ap.add_argument("--future-source", type=Path, required=True)
    ap.add_argument("--authorization", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    china_date = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    validate_execution_date(china_date)
    freeze = validate_parameter_freeze()
    auth, future_sha = validate_authorization(args.authorization, args.future_source)

    historical = read_price_source(args.historical_source.resolve(), historical=True)
    future = read_price_source(args.future_source.resolve(), historical=False)
    frame = combine_sources(historical, future)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = freeze["directional_change_thresholds"]
    vol_ref = float(freeze["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, float(thresholds[name])) for name in ("S1", "S2", "S3")}

    pair_results = {}
    for pair_id, lower, parent, minimum in PAIRINGS:
        events = common.r1_events(prices, days, waves[lower], waves[parent], vol_ref)
        pair_results[pair_id] = q4_pair_result(events, freeze["pairings"][pair_id], minimum)

    decision = decide(pair_results)
    receipt = {
        "schema_id": "factorlab_rmr_R1_parent_integrity_v2_true_fresh_2026Q4_receipt@1.0",
        "research_identity": "rmr_cross_scale_pullback_parent_integrity_v2",
        "stage": "one_time_true_fresh_Q4_evaluation_complete_pending_cloud_adjudication",
        "execution_date_China": china_date.isoformat(),
        "evaluation_protocol": str(PROTOCOL.relative_to(ROOT)),
        "parameter_bundle_sha256": freeze["parameter_bundle_sha256"],
        "selected_candidate_id": freeze["selected_candidate_id"],
        "authorization_identity": str(args.authorization),
        "authorization_sha256": sha256(args.authorization),
        "source_admission_receipt_sha256": auth["source_admission_receipt_sha256"],
        "historical_source_sha256": HISTORICAL_SHA256,
        "future_extension_source_sha256": future_sha,
        "trading_calendar_sha256": auth["exact_trading_calendar_sha256"],
        "evaluator_blob_sha": git_blob_sha(Path(__file__)),
        "context_window": {"start": FUTURE_START, "end": FUTURE_END},
        "challenge_window": {"start": Q4_START, "end": Q4_END},
        "pairings": pair_results,
        "decision": decision,
        "refit_performed": False,
        "parameter_mutation_performed": False,
        "candidate_change_performed": False,
        "scale_or_threshold_search_performed": False,
        "calibration_performed": False,
        "binary_threshold_selection_performed": False,
        "trading_return_used": False,
        "post_2026_12_31_prices_read": False,
        "row_level_predictions_emitted": False,
        "production_authority": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("R1_TRUE_FRESH_2026Q4_RESULT", json.dumps({"decision": decision}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
