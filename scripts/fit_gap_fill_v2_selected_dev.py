#!/usr/bin/env python3
"""Deterministically refit the already-selected Gap-Fill V2 geometry hazards.

This is an identity-freeze step, not model selection. It fits exactly six fixed
LogisticRegression stages (high/low x 15m/60m/EOD) on the full permitted
2015-2025 development inventory and writes only aggregate parameters/counts.

The selected V2 predictor depends only on the observed gap and prior 20-session
close-to-close volatility. Accordingly this runner intentionally does not load
V1 direction outputs, FRED data, offshore ETFs, or any post-09:31 China feature.
No 2026 row may be loaded and no raw predictions are persisted.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow
import scipy
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_gap_fill_v2_target_ledger as targetmod

PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_protocol_v1.json"
SELECTED = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase2_selected_v1.json"
PANEL = ROOT / "data/high_open_dev_2015_2025/annotated_panel.parquet"
MINUTES = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
USAGE = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_data_usage_v1.json"

START = "2015-01-05"
END = "2025-12-31"
FEATURES = ["abs_gap", "abs_gap_over_rvol20"]
EXPECTED_ARCH_SHA = "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
EXPECTED_SELECTED_BLOB = "17599d3f77861febf373b2ea05cd16131ceac5e8"
EXPECTED_PANEL_SHA = "f2587a528a517052016b646b58c734569b64a87766ff096575f353587e46aed1"
EXPECTED_MINUTES_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
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


def build_targets_full() -> pd.DataFrame:
    panel = pd.read_parquet(
        PANEL,
        filters=[("trading_day", ">=", START), ("trading_day", "<=", END)],
        columns=["trading_day", "open_0931", "prev_close", "overnight_gap"],
    )
    panel["trading_day"] = panel["trading_day"].astype(str)
    if panel.empty:
        raise RuntimeError("final-fit panel is empty")
    if panel["trading_day"].min() < START or panel["trading_day"].max() > END:
        raise RuntimeError("final-fit panel boundary drifted")
    if (pd.to_datetime(panel["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered final-fit panel")

    minutes = pd.read_parquet(
        MINUTES,
        filters=[
            ("symbol", "==", targetmod.SYMBOL),
            ("trading_day", ">=", START),
            ("trading_day", "<=", END),
        ],
        columns=["trading_day", "timestamp", "open", "high", "low", "close"],
    )
    minutes["trading_day"] = minutes["trading_day"].astype(str)
    if (pd.to_datetime(minutes["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered final-fit minute source")

    groups = {day: g.copy() for day, g in minutes.groupby("trading_day", sort=False)}
    clocks = targetmod.expected_clocks()
    rows: list[dict] = []
    for _, row in panel.sort_values("trading_day", kind="mergesort").iterrows():
        day = str(row["trading_day"])
        if day not in groups:
            continue
        result = targetmod.compute_day(row, groups[day], clocks)
        if result is not None and bool(result.get("target_valid", False)):
            rows.append(result)
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError("no target-valid rows for final fit")
    if out["trading_day"].min() < START or out["trading_day"].max() > END:
        raise RuntimeError("final-fit target boundary drifted")
    if (pd.to_datetime(out["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 target entered final fit")
    nested_15_60 = int((out["fill_15m"].astype(bool) & (~out["fill_60m"].astype(bool))).sum())
    nested_60_eod = int((out["fill_60m"].astype(bool) & (~out["fill_eod"].astype(bool))).sum())
    if nested_15_60 or nested_60_eod:
        raise RuntimeError("target nesting invariant violated in final fit")
    return out.sort_values("trading_day", kind="mergesort").reset_index(drop=True)


def build_geometry_frame() -> tuple[pd.DataFrame, dict]:
    panel = pd.read_parquet(
        PANEL,
        filters=[("trading_day", ">=", START), ("trading_day", "<=", END)],
        columns=["trading_day", "close_1500", "overnight_gap"],
    )
    panel["trading_day"] = panel["trading_day"].astype(str)
    panel = panel.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if panel.empty or (pd.to_datetime(panel["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("invalid final-fit geometry source")

    close = pd.to_numeric(panel["close_1500"], errors="coerce")
    gap = pd.to_numeric(panel["overnight_gap"], errors="coerce")
    panel["gap"] = gap
    panel["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()

    targets = build_targets_full()
    merged = panel.merge(
        targets[["trading_day", "gap", "gap_sign", "fill_15m", "fill_60m", "fill_eod"]],
        on="trading_day",
        how="inner",
        suffixes=("", "_target"),
        validate="one_to_one",
    )
    if merged.empty:
        raise RuntimeError("geometry/target final-fit merge is empty")
    panel_gap = pd.to_numeric(merged["gap"], errors="coerce")
    target_gap = pd.to_numeric(merged["gap_target"], errors="coerce")
    gap_diff = np.abs(panel_gap.to_numpy(dtype=float) - target_gap.to_numpy(dtype=float))
    if not np.isfinite(gap_diff).all():
        raise RuntimeError("non-finite gap in final-fit merge")
    max_gap_diff = float(np.max(gap_diff))
    if max_gap_diff > 1e-12:
        raise RuntimeError(f"final-fit geometry/target gap mismatch {max_gap_diff}")
    merged = merged.drop(columns=["gap_target"])

    rvol = pd.to_numeric(merged["rvol20"], errors="coerce")
    merged["abs_gap"] = panel_gap.abs()
    merged["abs_gap_over_rvol20"] = np.where(rvol > 0.0, panel_gap.abs() / rvol, np.nan)
    feature_values = merged[FEATURES].apply(pd.to_numeric, errors="coerce")
    valid = feature_values.notna().all(axis=1)
    valid &= np.isfinite(feature_values.to_numpy(dtype=float)).all(axis=1)
    valid &= merged[["gap_sign", "fill_15m", "fill_60m", "fill_eod"]].notna().all(axis=1)
    final = merged.loc[valid].copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if final.empty:
        raise RuntimeError("no geometry-complete final-fit rows")
    if (pd.to_datetime(final["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered final-fit training inventory")
    if not set(final["gap_sign"].unique()).issubset({"high", "low"}):
        raise RuntimeError("unexpected gap sign in final-fit inventory")

    audit = {
        "n_panel_rows": int(len(panel)),
        "n_target_valid": int(len(targets)),
        "n_feature_target_merged": int(len(merged)),
        "n_geometry_complete": int(len(final)),
        "geometry_missing_or_invalid_count": int(len(merged) - len(final)),
        "min_day": str(final["trading_day"].min()),
        "max_day": str(final["trading_day"].max()),
        "gap_match_max_abs": max_gap_diff,
        "rvol20_formula": "close_1500.pct_change(fill_method=None).shift(1).rolling(20,min_periods=20).std()",
    }
    return final, audit


def make_pipeline() -> Pipeline:
    return Pipeline([
        ("sc", StandardScaler(with_mean=True, with_std=True)),
        ("model", LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            class_weight=None,
            max_iter=1000,
            fit_intercept=True,
        )),
    ])


def stage_risk(frame: pd.DataFrame, stage: str) -> tuple[pd.Series, pd.Series]:
    if stage == "15m":
        risk = pd.Series(True, index=frame.index)
        target = frame["fill_15m"].astype(int)
    elif stage == "60m":
        risk = ~frame["fill_15m"].astype(bool)
        target = frame["fill_60m"].astype(int)
    elif stage == "eod":
        risk = ~frame["fill_60m"].astype(bool)
        target = frame["fill_eod"].astype(int)
    else:
        raise ValueError(stage)
    return risk, target


def fit_one(frame: pd.DataFrame, stage: str) -> dict:
    risk, target = stage_risk(frame, stage)
    part = frame.loc[risk].copy()
    y = target.loc[risk].to_numpy(dtype=int)
    if len(part) == 0 or np.unique(y).size != 2:
        raise RuntimeError(f"final-fit {stage} risk set lacks both classes")
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce")
    pipe = make_pipeline()
    pipe.fit(x, y)
    scaler = pipe.named_steps["sc"]
    model = pipe.named_steps["model"]
    return {
        "stage": stage,
        "training_min_day": str(part["trading_day"].min()),
        "training_max_day": str(part["trading_day"].max()),
        "n_train_risk": int(len(part)),
        "event_count": int(np.sum(y)),
        "event_rate": float(np.mean(y)),
        "feature_names": FEATURES,
        "scaler": {
            "mean": [float(v) for v in np.asarray(scaler.mean_, dtype=float)],
            "scale": [float(v) for v in np.asarray(scaler.scale_, dtype=float)],
            "var": [float(v) for v in np.asarray(scaler.var_, dtype=float)],
            "n_features_in": int(scaler.n_features_in_),
            "n_samples_seen": int(np.asarray(scaler.n_samples_seen_).item()),
        },
        "logistic": {
            "coef": [float(v) for v in np.asarray(model.coef_[0], dtype=float)],
            "intercept": float(np.asarray(model.intercept_, dtype=float)[0]),
            "classes": [int(v) for v in np.asarray(model.classes_, dtype=int)],
            "n_iter": [int(v) for v in np.asarray(model.n_iter_, dtype=int)],
            "n_features_in": int(model.n_features_in_),
        },
    }


def main() -> int:
    protocol = load_json(PROTOCOL)
    selected = load_json(SELECTED)
    if protocol["research_identity"] != "gap_fill_prediction_v2":
        raise RuntimeError("final-fit protocol identity drifted")
    if protocol["no_model_selection"] is not True:
        raise RuntimeError("final-fit protocol unexpectedly allows selection")
    if selected["selected_architecture_sha256"] != EXPECTED_ARCH_SHA:
        raise RuntimeError("selected V2 architecture SHA drifted")
    if protocol["selected_architecture"]["git_blob_sha"] != EXPECTED_SELECTED_BLOB:
        raise RuntimeError("selected V2 file identity drifted in protocol")
    for sign in ["high", "low"]:
        head = selected["selected_heads"][sign]
        if head["selected_feature_set"] != "geometry_only" or head["features"] != FEATURES:
            raise RuntimeError(f"selected {sign} head drifted")
    if sha256(PANEL) != EXPECTED_PANEL_SHA or sha256(MINUTES) != EXPECTED_MINUTES_SHA:
        raise RuntimeError("final-fit source identity drifted")

    frame, inventory = build_geometry_frame()
    heads: dict[str, dict] = {}
    for sign in ["high", "low"]:
        sf = frame.loc[frame["gap_sign"] == sign].copy()
        if sf.empty:
            raise RuntimeError(f"empty final-fit sign inventory {sign}")
        stages = {stage: fit_one(sf, stage) for stage in ["15m", "60m", "eod"]}
        heads[sign] = {
            "n_sign_rows": int(len(sf)),
            "min_day": str(sf["trading_day"].min()),
            "max_day": str(sf["trading_day"].max()),
            "features": FEATURES,
            "stages": stages,
        }

    versions = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "pyarrow": pyarrow.__version__,
    }
    expected_versions = protocol["execution_environment"]
    if not versions["python"].startswith(expected_versions["python"] + "."):
        raise RuntimeError(f"python version drifted: {versions['python']}")
    for key in ["numpy", "pandas", "scipy", "scikit_learn", "pyarrow"]:
        if versions[key] != expected_versions[key]:
            raise RuntimeError(f"library version drifted for {key}: {versions[key]} != {expected_versions[key]}")

    source_hashes = {
        "protocol": sha256(PROTOCOL),
        "selected_architecture_file": sha256(SELECTED),
        "annotated_panel": sha256(PANEL),
        "one_minute_official": sha256(MINUTES),
        "runner": sha256(Path(__file__)),
    }
    parameter_bundle = {
        "schema_id": "overnight_open_gap_fill_v2_parameter_bundle@1.0",
        "selected_architecture_sha256": EXPECTED_ARCH_SHA,
        "development_window": {"start": START, "end": END},
        "features": FEATURES,
        "hazard_probability_contract": protocol["cumulative_probability_contract"],
        "estimator": protocol["fixed_estimator"],
        "inventory": inventory,
        "heads": heads,
        "library_versions": versions,
        "source_hashes": source_hashes,
    }
    bundle_sha = canonical_digest(parameter_bundle)

    receipt = {
        "schema_id": "overnight_open_gap_fill_v2_final_fit_freeze@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_prediction_v2",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "selected_architecture": str(SELECTED.relative_to(ROOT)),
        "selected_architecture_sha256": EXPECTED_ARCH_SHA,
        "parameter_bundle": parameter_bundle,
        "parameter_bundle_sha256": bundle_sha,
        "final_fit_status": "completed_parameter_identity_frozen",
        "model_selection_performed": False,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "2026_repeat_validation_opened": False,
        "raw_prediction_rows_written_to_repo": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    usage = {
        "schema_id": "overnight_open_gap_fill_v2_final_fit_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31_final_parameter_refit_only",
        "selected_architecture_sha256": EXPECTED_ARCH_SHA,
        "parameter_bundle_sha256": bundle_sha,
        "model_selection_performed": False,
        "2026-01-05_to_2026-08-21": "not_loaded_unopened_repeat_only_reserved",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_predictions_persisted": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)
    print("GAP_FILL_V2_FINAL_FIT_FREEZE_RESULT", json.dumps({
        "parameter_bundle_sha256": bundle_sha,
        "inventory": inventory,
        "head_counts": {
            sign: {
                "n_sign_rows": heads[sign]["n_sign_rows"],
                "stage_risk_counts": {stage: heads[sign]["stages"][stage]["n_train_risk"] for stage in ["15m", "60m", "eod"]},
                "stage_event_counts": {stage: heads[sign]["stages"][stage]["event_count"] for stage in ["15m", "60m", "eod"]},
            }
            for sign in ["high", "low"]
        },
        "library_versions": versions,
        "2026_rows_loaded": False,
        "2026_repeat_validation_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
