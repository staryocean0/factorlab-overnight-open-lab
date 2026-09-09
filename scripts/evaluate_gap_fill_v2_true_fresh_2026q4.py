#!/usr/bin/env python3
"""One-shot first true-fresh validation for frozen Gap-Fill Prediction V2 v1.

This wrapper reuses the already-frozen 2026 repeat evaluator's target, forward-
probability and metric functions. It reconstructs only the same two runtime
features for the preregistered fresh calendar block and adds the preregistered
sample-sufficiency adjudication.

No partial-window execution is authorized. No model/scaler/calibration fit or
parameter/feature/threshold search is performed.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_local_gap_fill_v2_2026_repeat as base

PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_true_fresh_protocol_v1.json"
PARAMETERS = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
OUT = ROOT / "docs/research/gap_fill_v2_true_fresh_2026q4_receipt_v1.json"
USAGE = ROOT / "docs/governance/gap_fill_v2_true_fresh_2026q4_data_usage_v1.json"

FRESH_START = "2026-08-24"
FRESH_END = "2026-12-31"
HISTORY_START = "2026-07-01"
NOT_BEFORE_CHINA_DATE = "2027-01-01"
EXPECTED_ARCH_SHA = "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
EXPECTED_PARAMETER_BUNDLE_SHA = "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"
EXPECTED_PARAMETER_BLOB = "eef7a9af6d42ee2faf53dbd16dce0b15ebfd10ed"
EXPECTED_BASE_EVALUATOR_BLOB = "d61e00efa6e605864c8153a1e7e577257f813939"


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


def china_date_now() -> str:
    return str((datetime.now(timezone.utc) + timedelta(hours=8)).date())


def require_source(env_name: str) -> Path:
    raw = os.environ.get(env_name)
    if not raw:
        raise RuntimeError(f"required environment variable is not set: {env_name}")
    path = Path(raw).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise RuntimeError(f"source does not exist: {env_name}={path}")
    return path


def assert_source_boundary(panel_path: Path, minute_path: Path) -> dict:
    panel_days = pd.read_parquet(panel_path, columns=["trading_day"])["trading_day"].astype(str)
    minute_days = pd.read_parquet(minute_path, columns=["trading_day"])["trading_day"].astype(str)
    if panel_days.empty or minute_days.empty:
        raise RuntimeError("fresh source is empty")
    if panel_days.max() != FRESH_END:
        raise RuntimeError(f"fresh panel is not complete through frozen endpoint: {panel_days.max()}")
    if minute_days.min() != FRESH_START or minute_days.max() != FRESH_END:
        raise RuntimeError(
            f"fresh minute source must be exactly inside target window: {minute_days.min()}..{minute_days.max()}"
        )
    if (panel_days > FRESH_END).any() or (minute_days > FRESH_END).any():
        raise RuntimeError("post-2026-12-31 row entered first fresh challenge source")
    if panel_days.min() > "2026-07-31":
        raise RuntimeError("insufficient pre-fresh panel history for rvol20")

    panel_fresh_days = set(panel_days.loc[(panel_days >= FRESH_START) & (panel_days <= FRESH_END)])
    minute_fresh_days = set(minute_days)
    if panel_fresh_days != minute_fresh_days:
        raise RuntimeError("fresh panel/minute trading-day inventories differ")
    counts = minute_days.value_counts()
    bad_counts = counts.loc[counts != 240]
    if len(bad_counts):
        raise RuntimeError(f"fresh minute source has non-240-bar days: {bad_counts.to_dict()}")

    return {
        "panel_min_day": str(panel_days.min()),
        "panel_max_day": str(panel_days.max()),
        "fresh_panel_day_count": int(len(panel_fresh_days)),
        "minute_min_day": str(minute_days.min()),
        "minute_max_day": str(minute_days.max()),
        "minute_trading_day_count": int(len(minute_fresh_days)),
        "minute_row_count": int(len(minute_days)),
        "all_minute_days_have_240_bars": True,
    }


def load_fresh_panel(path: Path) -> pd.DataFrame:
    cols = ["trading_day", "open_0931", "prev_close", "close_1500", "overnight_gap"]
    frame = pd.read_parquet(
        path,
        filters=[("trading_day", ">=", HISTORY_START), ("trading_day", "<=", FRESH_END)],
        columns=cols,
    )
    if frame.empty:
        raise RuntimeError("fresh annotated panel returned no rows")
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame = frame.sort_values("trading_day", kind="mergesort").drop_duplicates("trading_day", keep="last").reset_index(drop=True)
    if frame["trading_day"].max() != FRESH_END:
        raise RuntimeError("fresh panel filtered inventory does not end at frozen endpoint")
    if frame["trading_day"].min() > "2026-07-31":
        raise RuntimeError("fresh panel lacks enough prior close history")

    close = pd.to_numeric(frame["close_1500"], errors="coerce")
    frame["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    gap_calc = pd.to_numeric(frame["open_0931"], errors="coerce") / pd.to_numeric(frame["prev_close"], errors="coerce") - 1.0
    stored = pd.to_numeric(frame["overnight_gap"], errors="coerce")
    valid_gap = gap_calc.notna() & stored.notna()
    gap_match_max_abs = float((gap_calc.loc[valid_gap] - stored.loc[valid_gap]).abs().max()) if valid_gap.any() else None
    if gap_match_max_abs is None or gap_match_max_abs > 1e-12:
        raise RuntimeError(f"fresh panel gap identity mismatch: {gap_match_max_abs}")
    frame["gap"] = gap_calc
    frame["abs_gap"] = gap_calc.abs()
    frame["abs_gap_over_rvol20"] = frame["abs_gap"] / pd.to_numeric(frame["rvol20"], errors="coerce")
    frame.attrs["gap_match_max_abs"] = gap_match_max_abs
    return frame


def transform_result_to_fresh(result: dict, protocol: dict) -> dict:
    out = dict(result)
    gates = dict(out.pop("repeat_confirmation_gates"))
    out.pop("repeat_confirmed", None)
    expected_gate_names = set(protocol["fresh_confirmation_gate_per_sign"])
    if set(gates) != expected_gate_names:
        raise RuntimeError("base evaluator gate names drifted from frozen fresh protocol")
    thresholds = protocol["sample_sufficiency_per_sign"]
    suff = {
        "all_nonzero_gap_rows": int(out["n"]) >= int(thresholds["minimum_all_nonzero_gap_rows"]),
        "abs_gap_gt_10bp_rows": int(out["n_gt10bp"]) >= int(thresholds["minimum_abs_gap_gt_10bp_rows"]),
        "abs_gap_gt_30bp_rows": int(out["n_gt30bp"]) >= int(thresholds["minimum_abs_gap_gt_30bp_rows"]),
    }
    sample_sufficient = bool(all(suff.values()))
    out["fresh_confirmation_gates"] = gates
    out["sample_sufficiency_gates"] = suff
    out["sample_sufficient"] = sample_sufficient
    out["fresh_confirmed"] = bool(sample_sufficient and all(gates.values()))
    return out


def main() -> int:
    protocol = load_json(PROTOCOL)
    frozen = load_json(PARAMETERS)
    bundle = frozen["parameter_bundle"]

    if china_date_now() < NOT_BEFORE_CHINA_DATE:
        raise RuntimeError(f"premature true-fresh open forbidden before China date {NOT_BEFORE_CHINA_DATE}")
    if protocol["scientific_role"] != "true_fresh_oos" or protocol["fresh_window_opened"] is not False:
        raise RuntimeError("true-fresh protocol role/open-state drifted")
    expected_window = {
        "start": FRESH_START,
        "end": FRESH_END,
        "complete_calendar_block_required": True,
        "partial_window_open_forbidden": True,
        "not_before_china_date": NOT_BEFORE_CHINA_DATE,
        "post_2026_12_31": "outside_this_first_fresh_challenge",
    }
    if protocol["validation_window"] != expected_window:
        raise RuntimeError("true-fresh validation window drifted")
    if frozen["selected_architecture_sha256"] != EXPECTED_ARCH_SHA:
        raise RuntimeError("selected architecture identity drifted")
    if protocol["frozen_model"]["selected_architecture_sha256"] != EXPECTED_ARCH_SHA:
        raise RuntimeError("fresh protocol architecture binding drifted")
    digest = base.parameter_bundle_digest(bundle)
    if digest != EXPECTED_PARAMETER_BUNDLE_SHA:
        raise RuntimeError(f"sealed parameter bundle identity drifted: {digest}")
    if frozen["parameter_bundle_sha256"] != EXPECTED_PARAMETER_BUNDLE_SHA:
        raise RuntimeError("parameter artifact bundle SHA drifted")
    if protocol["frozen_model"]["parameter_bundle_sha256"] != EXPECTED_PARAMETER_BUNDLE_SHA:
        raise RuntimeError("fresh protocol bundle binding drifted")
    if protocol["frozen_model"]["parameter_artifact_git_blob_sha"] != EXPECTED_PARAMETER_BLOB:
        raise RuntimeError("parameter artifact Git blob binding drifted")
    if protocol["frozen_scoring_implementation"]["base_evaluator_git_blob_sha"] != EXPECTED_BASE_EVALUATOR_BLOB:
        raise RuntimeError("base scoring implementation binding drifted")
    if bundle["features"] != ["abs_gap", "abs_gap_over_rvol20"]:
        raise RuntimeError("sealed runtime features drifted")

    panel_path = require_source("OVERNIGHT_FRESH_ANNOTATED_PANEL")
    minute_path = require_source("OVERNIGHT_FRESH_DATAHUB_1M")
    source_boundary = assert_source_boundary(panel_path, minute_path)

    # Target construction and scoring reuse the exact frozen repeat implementation.
    base.VAL_START = FRESH_START
    base.VAL_END = FRESH_END
    base.HISTORY_START = HISTORY_START
    panel = load_fresh_panel(panel_path)
    minutes = base.load_local_minutes(minute_path)
    targets, target_audit = base.build_targets(panel, minutes)

    features = panel.loc[
        (panel["trading_day"] >= FRESH_START) & (panel["trading_day"] <= FRESH_END),
        ["trading_day", "gap", "abs_gap", "rvol20", "abs_gap_over_rvol20"],
    ].copy()
    merged = targets.merge(features, on="trading_day", how="left", validate="one_to_one", suffixes=("_target", ""))
    if merged.empty:
        raise RuntimeError("fresh target/feature merge is empty")
    merged["gap_sign"] = np.where(pd.to_numeric(merged["gap"], errors="coerce") > 0.0, "high", "low")
    complete = merged[["abs_gap", "rvol20", "abs_gap_over_rvol20"]].apply(pd.to_numeric, errors="coerce").notna().all(axis=1)
    complete &= pd.to_numeric(merged["rvol20"], errors="coerce") > 0.0
    if int((~complete).sum()) != 0:
        raise RuntimeError(f"fresh validation contains {int((~complete).sum())} incomplete geometry rows")
    merged = merged.loc[complete].copy().reset_index(drop=True)
    if merged["trading_day"].min() != FRESH_START or merged["trading_day"].max() != FRESH_END:
        raise RuntimeError(
            f"fresh target inventory does not span frozen endpoints: {merged['trading_day'].min()}..{merged['trading_day'].max()}"
        )

    raw_results = {sign: base.evaluate_sign(merged, bundle, protocol, sign) for sign in ["high", "low"]}
    results = {sign: transform_result_to_fresh(raw_results[sign], protocol) for sign in ["high", "low"]}
    confirmed = [s for s in ["high", "low"] if results[s]["fresh_confirmed"]]
    sufficient = [s for s in ["high", "low"] if results[s]["sample_sufficient"]]

    if len(confirmed) == 2:
        decision = "gap_fill_v2_true_fresh_robustly_confirmed"
    elif len(confirmed) == 1:
        decision = "gap_fill_v2_true_fresh_partially_confirmed"
    elif len(sufficient) == 0:
        decision = "gap_fill_v2_true_fresh_evidence_insufficient"
    else:
        decision = "gap_fill_v2_true_fresh_not_confirmed"

    session_date = china_date_now()
    receipt = {
        "schema_id": "overnight_open_gap_fill_v2_true_fresh_2026q4_receipt@1.0",
        "session_date": session_date,
        "research_identity": "gap_fill_prediction_v2",
        "scientific_role": "true_fresh_oos",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "parameter_artifact": str(PARAMETERS.relative_to(ROOT)),
        "selected_architecture_sha256": EXPECTED_ARCH_SHA,
        "parameter_bundle_sha256": EXPECTED_PARAMETER_BUNDLE_SHA,
        "validation_window": {"start": FRESH_START, "end": FRESH_END},
        "source_boundary": source_boundary,
        "target_audit": target_audit,
        "n_fresh_rows": int(len(merged)),
        "n_fresh_high": int((merged["gap_sign"] == "high").sum()),
        "n_fresh_low": int((merged["gap_sign"] == "low").sum()),
        "results": results,
        "sample_sufficient_heads": sufficient,
        "fresh_confirmed_heads": confirmed,
        "decision": decision,
        "source_hashes": {
            "annotated_panel": sha256(panel_path),
            "datahub_1m": sha256(minute_path),
            "protocol": sha256(PROTOCOL),
            "parameter_artifact": sha256(PARAMETERS),
            "fresh_wrapper": sha256(Path(__file__)),
            "base_scoring_evaluator": sha256(ROOT / "scripts/evaluate_local_gap_fill_v2_2026_repeat.py"),
        },
        "model_refit_performed": False,
        "scaler_refit_performed": False,
        "feature_selection_performed": False,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_layer_fit_or_applied": False,
        "descriptive_calibration_regression_performed": True,
        "trading_return_used": False,
        "partial_window_scored": False,
        "fresh_window_opened": True,
        "post_2026_12_31_rows_loaded": False,
        "raw_fresh_rows_written_to_repo": False,
        "fresh_oos": True,
        "production_authority": False,
    }
    dump_json(OUT, receipt)

    usage = {
        "schema_id": "overnight_open_gap_fill_v2_true_fresh_2026q4_data_usage@1.0",
        "session_date": session_date,
        "research_identity": "gap_fill_prediction_v2",
        "window": "2026-08-24_to_2026-12-31",
        "role": "true_fresh_oos",
        "fresh_window_opened": True,
        "partial_window_scored": False,
        "model_refit_performed": False,
        "parameter_search_performed": False,
        "post_2026_12_31_rows_loaded": False,
        "aggregate_receipt_only": True,
        "production_authority": False,
    }
    dump_json(USAGE, usage)

    print("GAP_FILL_V2_TRUE_FRESH_RESULT", json.dumps({
        "n_fresh_rows": receipt["n_fresh_rows"],
        "n_fresh_high": receipt["n_fresh_high"],
        "n_fresh_low": receipt["n_fresh_low"],
        "sample_sufficient_heads": receipt["sample_sufficient_heads"],
        "fresh_confirmed_heads": receipt["fresh_confirmed_heads"],
        "decision": receipt["decision"],
        "fresh_oos": True,
        "post_2026_12_31_rows_loaded": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
