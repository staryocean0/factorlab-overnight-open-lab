#!/usr/bin/env python3
"""CT-AUDIT-A: sealed 2011-2012 cross-index validation for Gap-Fill geometry hazards.

This evaluator opens only the preregistered CSI300/CSI500 Audit-A windows.
It never refits T1/T2 models or scalers. T2 uses the index-specific parameter
bundles frozen after CT-DEV; T1 uses the frozen CSI1000 V2-v1 bundle only as a
descriptive exact-parameter transport. Audit B, the 2014 crosscheck, and
CSI1000 post-2026-08-21 outcomes are never loaded.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_gap_fill_v2_target_ledger as targetmod
import evaluate_local_gap_fill_v2_2026_repeat as evalbase

PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_a_protocol_v1.json"
EXTERNAL_PARAMETERS = ROOT / "docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json"
CSI1000_PARAMETERS = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
OUT = ROOT / "docs/research/local_gap_fill_cross_index_transport_audit_a_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_gap_fill_cross_index_transport_audit_a_data_usage_v1.json"

FEATURES = ["abs_gap", "abs_gap_over_rvol20"]
MATERIAL = {"all": 0.0, "gt10bp": 0.001, "gt30bp": 0.003}
HISTORY_START = "2010-10-01"
AUDIT_START = "2011-01-01"
AUDIT_END = "2012-12-31"
ADMITTED_DATASET_VERSION = "bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
ADMITTED_DATASET_SHA256 = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256 = "0cc74f79d9e9f26d1b9d8d554c96db0207a63d68787cceff1152dd71d26ae992"
EXPECTED_CSI300_BUNDLE_SHA256 = "87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb"
EXPECTED_CSI500_BUNDLE_SHA256 = "6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957"
EXPECTED_CSI1000_ARCH_SHA256 = "07810dafbab629f196d04ea1204d90ee68177ce764bb765be560bc1b84261c00"
EXPECTED_CSI1000_BUNDLE_SHA256 = "07abe29e31ce09b69bd6250b1ce3ebc5af7688b69ed39909feb80e9db882aaa0"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def require_source() -> Path:
    raw = os.environ.get("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE")
    if not raw:
        raise RuntimeError("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE is required")
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"historical 1m source does not exist: {path}")
    if ADMITTED_DATASET_VERSION not in str(path):
        raise RuntimeError("historical source path is not the HE-00 admitted dataset identity")
    return path


def parameter_bundle_digest(bundle: dict) -> str:
    return canonical_digest(bundle)


def read_symbol(source: Path, symbol: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        source,
        filters=[
            ("symbol", "==", symbol),
            ("trading_day", ">=", HISTORY_START),
            ("trading_day", "<=", AUDIT_END),
        ],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError(f"no Audit-A/history rows for {symbol}")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].min() < HISTORY_START or frame["trading_day"].max() > AUDIT_END:
        raise RuntimeError(f"{symbol} source crossed Audit-A boundary")
    if (frame["trading_day"] >= "2013-01-01").any():
        raise RuntimeError(f"{symbol} Audit-B row entered Audit A")
    if frame.duplicated(["trading_day", "timestamp"]).any():
        raise RuntimeError(f"{symbol} duplicate timestamp in Audit-A source")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def build_audit_frame(source: Path, name: str, symbol: str) -> tuple[pd.DataFrame, dict]:
    minutes = read_symbol(source, symbol)
    clocks = targetmod.expected_clocks()
    expected = clocks["eod"]
    expected_set = set(expected)
    groups = {day: g.copy() for day, g in minutes.groupby("trading_day", sort=True)}
    days = sorted(groups)

    daily_rows: list[dict] = []
    exact_240: dict[str, bool] = {}
    for day in days:
        g = groups[day]
        present = g["clock"].tolist()
        exact = len(g) == 240 and len(set(present)) == 240 and set(present) == expected_set
        exact_240[day] = bool(exact)
        gg = g.set_index("clock")
        close_1500 = np.nan
        open_0931 = np.nan
        if "15:00" in gg.index:
            close_1500 = pd.to_numeric(pd.Series([gg.loc["15:00", "close"]]), errors="coerce").iloc[0]
        if "09:31" in gg.index:
            open_0931 = pd.to_numeric(pd.Series([gg.loc["09:31", "open"]]), errors="coerce").iloc[0]
        daily_rows.append({
            "trading_day": day,
            "close_1500": close_1500,
            "open_0931": open_0931,
            "exact_240": bool(exact),
        })

    daily = pd.DataFrame(daily_rows).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    daily["prev_close"] = pd.to_numeric(daily["close_1500"], errors="coerce").shift(1)
    close = pd.to_numeric(daily["close_1500"], errors="coerce")
    daily["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    daily["gap"] = pd.to_numeric(daily["open_0931"], errors="coerce") / pd.to_numeric(daily["prev_close"], errors="coerce") - 1.0
    daily["abs_gap"] = daily["gap"].abs()
    daily["abs_gap_over_rvol20"] = daily["abs_gap"] / pd.to_numeric(daily["rvol20"], errors="coerce")

    audit_daily = daily.loc[(daily["trading_day"] >= AUDIT_START) & (daily["trading_day"] <= AUDIT_END)].copy()
    if audit_daily.empty:
        raise RuntimeError(f"{name} Audit-A daily inventory empty")

    target_rows: list[dict] = []
    invalid_reasons: dict[str, int] = {}
    for _, row in audit_daily.iterrows():
        day = str(row["trading_day"])
        if not bool(row["exact_240"]):
            invalid_reasons["not_exact_complete_240_clocks"] = invalid_reasons.get("not_exact_complete_240_clocks", 0) + 1
            continue
        numeric = [row["open_0931"], row["prev_close"], row["gap"], row["rvol20"], row["abs_gap_over_rvol20"]]
        if not all(np.isfinite(float(v)) for v in numeric) or float(row["rvol20"]) <= 0.0:
            invalid_reasons["incomplete_gap_or_rvol20"] = invalid_reasons.get("incomplete_gap_or_rvol20", 0) + 1
            continue
        day_row = pd.Series({
            "trading_day": day,
            "open_0931": float(row["open_0931"]),
            "prev_close": float(row["prev_close"]),
            "overnight_gap": float(row["gap"]),
        })
        result = targetmod.compute_day(day_row, groups[day], clocks)
        if result is None or not bool(result.get("target_valid", False)):
            reason = "target_invalid" if result is None else str(result.get("invalid_reason"))
            invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1
            continue
        result["rvol20"] = float(row["rvol20"])
        result["abs_gap_over_rvol20"] = float(row["abs_gap_over_rvol20"])
        target_rows.append(result)

    frame = pd.DataFrame(target_rows)
    if frame.empty:
        raise RuntimeError(f"{name} has no Audit-A target-valid complete rows")
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if frame["trading_day"].min() < AUDIT_START or frame["trading_day"].max() > AUDIT_END:
        raise RuntimeError(f"{name} target inventory crossed Audit-A boundary")
    if int((frame["fill_15m"].astype(bool) & ~frame["fill_60m"].astype(bool)).sum()) != 0:
        raise RuntimeError(f"{name} 15m/60m nesting violation")
    if int((frame["fill_60m"].astype(bool) & ~frame["fill_eod"].astype(bool)).sum()) != 0:
        raise RuntimeError(f"{name} 60m/EOD nesting violation")
    if not set(frame["gap_sign"].unique()).issubset({"high", "low"}):
        raise RuntimeError(f"{name} unexpected gap sign")

    audit_days = sorted(audit_daily["trading_day"].astype(str).unique().tolist())
    source_audit = {
        "symbol": symbol,
        "feature_history_start": HISTORY_START,
        "audit_window": {"start": AUDIT_START, "end": AUDIT_END},
        "minute_rows_loaded_including_feature_history": int(len(minutes)),
        "trading_days_loaded_including_feature_history": int(len(days)),
        "pre_audit_feature_history_days": int(sum(day < AUDIT_START for day in days)),
        "audit_trading_days_loaded": int(len(audit_days)),
        "audit_exact_240_days": int(sum(exact_240.get(day, False) for day in audit_days)),
        "target_valid_geometry_complete_rows": int(len(frame)),
        "invalid_reason_counts": invalid_reasons,
        "target_min_day": str(frame["trading_day"].min()),
        "target_max_day": str(frame["trading_day"].max()),
        "audit_b_or_later_rows_loaded": False,
    }
    return frame, source_audit


def cumulative_from_bundle(bundle: dict, sign: str, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return evalbase.cumulative_probs(bundle["heads"][sign], x)


def benchmark_from_dev_bundle(bundle: dict, sign: str, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    stages = bundle["heads"][sign]["stages"]
    h15 = float(stages["15m"]["event_rate"])
    h60 = float(stages["60m"]["event_rate"])
    heod = float(stages["eod"]["event_rate"])
    return (
        np.full(n, h15, dtype=float),
        np.full(n, 1.0 - (1.0 - h15) * (1.0 - h60), dtype=float),
        np.full(n, 1.0 - (1.0 - h15) * (1.0 - h60) * (1.0 - heod), dtype=float),
    )


def evaluate_sign(frame: pd.DataFrame, sign: str, model_bundle: dict, benchmark_bundle: dict) -> dict:
    part = frame.loc[frame["gap_sign"] == sign].copy().reset_index(drop=True)
    if part.empty:
        raise RuntimeError(f"empty Audit-A sign inventory: {sign}")
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise RuntimeError(f"nonfinite Audit-A features: {sign}")
    model_probs_all = cumulative_from_bundle(model_bundle, sign, x)
    bench_probs_all = benchmark_from_dev_bundle(benchmark_bundle, sign, len(part))

    monotonicity_violations = int(np.sum((model_probs_all[0] > model_probs_all[1]) | (model_probs_all[1] > model_probs_all[2])))
    result: dict = {
        "counts": {
            "all": int(len(part)),
            "gt10bp": int((part["abs_gap"] > 0.001).sum()),
            "gt30bp": int((part["abs_gap"] > 0.003).sum()),
        },
        "model": {},
        "benchmark": {},
        "monotonicity_violations": monotonicity_violations,
    }

    for cohort, threshold in MATERIAL.items():
        mask = np.ones(len(part), dtype=bool) if threshold == 0.0 else part["abs_gap"].to_numpy(dtype=float) > threshold
        cohort_part = part.loc[mask].copy().reset_index(drop=True)
        model_probs = tuple(p[mask] for p in model_probs_all)
        bench_probs = tuple(p[mask] for p in bench_probs_all)
        result["model"][cohort] = evalbase.evaluate_cohort(cohort_part, model_probs, include_deciles=True)
        result["benchmark"][cohort] = evalbase.evaluate_cohort(cohort_part, bench_probs, include_deciles=False)

    suff = result["counts"]
    sample_sufficient = bool(suff["all"] >= 25 and suff["gt10bp"] >= 20 and suff["gt30bp"] >= 12)
    result["sample_sufficient"] = sample_sufficient

    if sample_sufficient:
        model = result["model"]
        bench = result["benchmark"]
        gt10_horizon_wins = 0
        for horizon in ["fill_15m", "fill_60m", "fill_eod"]:
            if model["gt10bp"]["horizons"][horizon]["brier_score"] < bench["gt10bp"]["horizons"][horizon]["brier_score"]:
                gt10_horizon_wins += 1
        gates = {
            "all_integrated_brier_better": bool(model["all"]["integrated_brier"] < bench["all"]["integrated_brier"]),
            "all_integrated_log_loss_better": bool(model["all"]["integrated_log_loss"] < bench["all"]["integrated_log_loss"]),
            "gt10_integrated_brier_better": bool(model["gt10bp"]["integrated_brier"] < bench["gt10bp"]["integrated_brier"]),
            "gt30_integrated_brier_not_worse": bool(model["gt30bp"]["integrated_brier"] <= bench["gt30bp"]["integrated_brier"]),
            "gt10_at_least_2_of_3_horizon_brier_better": bool(gt10_horizon_wins >= 2),
            "monotonicity_violations_zero": bool(monotonicity_violations == 0),
        }
        result["gates"] = gates
        result["gate_pass_count"] = int(sum(bool(v) for v in gates.values()))
        result["audit_a_passed"] = bool(all(gates.values()))
    else:
        result["gates"] = None
        result["gate_pass_count"] = None
        result["audit_a_passed"] = False

    annual = {}
    for year in [2011, 2012]:
        year_mask = part["year"].to_numpy(dtype=int) == year
        year_part = part.loc[year_mask].copy().reset_index(drop=True)
        if year_part.empty:
            continue
        annual[str(year)] = {
            "model": evalbase.evaluate_cohort(year_part, tuple(p[year_mask] for p in model_probs_all), include_deciles=False),
            "benchmark": evalbase.evaluate_cohort(year_part, tuple(p[year_mask] for p in bench_probs_all), include_deciles=False),
        }
    result["annual_all_gap"] = annual
    return result


def evaluate_t1(frame: pd.DataFrame, sign: str, csi1000_bundle: dict) -> dict:
    part = frame.loc[frame["gap_sign"] == sign].copy().reset_index(drop=True)
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    probs_all = cumulative_from_bundle(csi1000_bundle, sign, x)
    result: dict = {"counts": {}, "metrics": {}, "monotonicity_violations": int(np.sum((probs_all[0] > probs_all[1]) | (probs_all[1] > probs_all[2])))}
    for cohort, threshold in MATERIAL.items():
        mask = np.ones(len(part), dtype=bool) if threshold == 0.0 else part["abs_gap"].to_numpy(dtype=float) > threshold
        cohort_part = part.loc[mask].copy().reset_index(drop=True)
        result["counts"][cohort] = int(mask.sum())
        result["metrics"][cohort] = evalbase.evaluate_cohort(cohort_part, tuple(p[mask] for p in probs_all), include_deciles=True)
    return result


def main() -> int:
    protocol = load_json(PROTOCOL)
    external = load_json(EXTERNAL_PARAMETERS)
    csi1000 = load_json(CSI1000_PARAMETERS)

    if protocol["stage"] != "CT_AUDIT_A_preregistered_unopened":
        raise RuntimeError("Audit-A protocol stage drifted")
    if protocol["audit_a_opened"] is not False or protocol["audit_b_opened"] is not False:
        raise RuntimeError("Audit-A protocol evidence state drifted")
    if sha256(EXTERNAL_PARAMETERS) != EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256:
        raise RuntimeError("external parameter artifact SHA256 drifted")
    if external["source_dataset_sha256_from_HE00"] != ADMITTED_DATASET_SHA256:
        raise RuntimeError("external parameter artifact source identity drifted")
    if external["source_dataset_version"] != ADMITTED_DATASET_VERSION:
        raise RuntimeError("external parameter artifact dataset version drifted")
    if external["external_index_bundles"]["CSI300"]["parameter_bundle_sha256"] != EXPECTED_CSI300_BUNDLE_SHA256:
        raise RuntimeError("CSI300 frozen bundle SHA drifted")
    if external["external_index_bundles"]["CSI500"]["parameter_bundle_sha256"] != EXPECTED_CSI500_BUNDLE_SHA256:
        raise RuntimeError("CSI500 frozen bundle SHA drifted")
    if parameter_bundle_digest(external["external_index_bundles"]["CSI300"]["parameter_bundle"]) != EXPECTED_CSI300_BUNDLE_SHA256:
        raise RuntimeError("CSI300 parameter payload digest drifted")
    if parameter_bundle_digest(external["external_index_bundles"]["CSI500"]["parameter_bundle"]) != EXPECTED_CSI500_BUNDLE_SHA256:
        raise RuntimeError("CSI500 parameter payload digest drifted")
    if csi1000["selected_architecture_sha256"] != EXPECTED_CSI1000_ARCH_SHA256:
        raise RuntimeError("CSI1000 architecture SHA drifted")
    if parameter_bundle_digest(csi1000["parameter_bundle"]) != EXPECTED_CSI1000_BUNDLE_SHA256:
        raise RuntimeError("CSI1000 bundle digest drifted")

    source = require_source()
    specs = {
        "CSI300": "000300.SH",
        "CSI500": "000905.SH",
    }

    results = {}
    source_audits = {}
    all_head_passes = []
    all_head_sufficient = []

    for name, symbol in specs.items():
        frame, source_audit = build_audit_frame(source, name, symbol)
        source_audits[name] = source_audit
        ext_bundle = external["external_index_bundles"][name]["parameter_bundle"]
        t2 = {}
        t1 = {}
        for sign in ["high", "low"]:
            t2[sign] = evaluate_sign(frame, sign, ext_bundle, ext_bundle)
            t1[sign] = evaluate_t1(frame, sign, csi1000["parameter_bundle"])
            all_head_passes.append(bool(t2[sign]["audit_a_passed"]))
            all_head_sufficient.append(bool(t2[sign]["sample_sufficient"]))
        results[name] = {
            "symbol": symbol,
            "counts": {
                "all": int(len(frame)),
                "high": int((frame["gap_sign"] == "high").sum()),
                "low": int((frame["gap_sign"] == "low").sum()),
                "gt10bp": int((frame["abs_gap"] > 0.001).sum()),
                "gt30bp": int((frame["abs_gap"] > 0.003).sum()),
            },
            "T1_exact_CSI1000_parameter_transport_descriptive": t1,
            "T2_frozen_external_parameter_audit": t2,
        }

    all_four_sufficient = bool(len(all_head_sufficient) == 4 and all(all_head_sufficient))
    all_four_pass = bool(len(all_head_passes) == 4 and all(all_head_passes))
    audit_b_eligibility = bool(all_four_sufficient and all_four_pass)
    if audit_b_eligibility:
        decision = "CT_AUDIT_A_all_four_heads_pass_cloud_review_required_before_Audit_B"
    elif not all_four_sufficient:
        decision = "CT_AUDIT_A_evidence_insufficient_or_head_failure_do_not_open_Audit_B"
    else:
        decision = "CT_AUDIT_A_not_all_four_heads_pass_do_not_open_Audit_B"

    receipt = {
        "schema_id": "overnight_open_gap_fill_cross_index_audit_a_receipt@1.0",
        "session_date": "2026-09-07",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "stage": "CT_AUDIT_A_completed_local_pending_cloud_review",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source_dataset_version": ADMITTED_DATASET_VERSION,
        "source_dataset_sha256_from_HE00": ADMITTED_DATASET_SHA256,
        "external_parameter_artifact_sha256": EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256,
        "CSI300_parameter_bundle_sha256": EXPECTED_CSI300_BUNDLE_SHA256,
        "CSI500_parameter_bundle_sha256": EXPECTED_CSI500_BUNDLE_SHA256,
        "CSI1000_architecture_sha256": EXPECTED_CSI1000_ARCH_SHA256,
        "CSI1000_parameter_bundle_sha256": EXPECTED_CSI1000_BUNDLE_SHA256,
        "source_audits": source_audits,
        "indices": results,
        "all_four_T2_heads_sample_sufficient": all_four_sufficient,
        "all_four_T2_heads_pass_all_six_gates": all_four_pass,
        "audit_b_eligibility_under_frozen_rule": audit_b_eligibility,
        "decision": decision,
        "T1_refit_performed": False,
        "T2_refit_performed": False,
        "scaler_refit_performed": False,
        "feature_search_performed": False,
        "model_class_search_performed": False,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_performed": False,
        "audit_b_opened": False,
        "supporting_crosscheck_opened": False,
        "csi1000_post_2026_08_21_outcomes_opened": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    usage = {
        "schema_id": "overnight_open_gap_fill_cross_index_audit_a_data_usage@1.0",
        "session_date": "2026-09-07",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "opened": {
            "CSI300_Audit_A_2011-01-01_to_2012-12-31": True,
            "CSI500_Audit_A_2011-01-01_to_2012-12-31": True,
        },
        "feature_history_only": {"2010-10-01_to_2010-12-31": True},
        "sealed": {
            "Audit_B_2013-01-01_to_2014-10-16": True,
            "supporting_crosscheck_2014-10-17_to_2014-12-31": True,
            "CSI1000_2026Q4_true_fresh": True,
        },
        "aggregate_outputs_only": True,
        "raw_rows_written_to_repo": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    dump_json(USAGE, usage)
    print("GAP_FILL_CROSS_INDEX_AUDIT_A_RESULT", json.dumps({
        "decision": decision,
        "audit_b_eligibility_under_frozen_rule": audit_b_eligibility,
        "all_four_sample_sufficient": all_four_sufficient,
        "all_four_pass": all_four_pass,
        "audit_b_opened": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
