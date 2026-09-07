#!/usr/bin/env python3
"""CT-AUDIT-B: final backward-historical confirmation of frozen gap-fill hazards.

Opens only CSI300/CSI500 2013-01-01..2014-10-16. No model/scaler is refit.
The 2014-10-17..2014-12-31 supporting crosscheck and CSI1000 post-2026-08-21
outcomes are never loaded. Only aggregate receipts are written.
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

PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_cross_index_audit_b_protocol_v1.json"
EXTERNAL_PARAMETERS = ROOT / "docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json"
CSI1000_PARAMETERS = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_final_fit_freeze_v1.json"
OUT = ROOT / "docs/research/local_gap_fill_cross_index_transport_audit_b_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_gap_fill_cross_index_transport_audit_b_data_usage_v1.json"

FEATURES = ["abs_gap", "abs_gap_over_rvol20"]
MATERIAL = {"all": 0.0, "gt10bp": 0.001, "gt30bp": 0.003}
HORIZONS = ["fill_15m", "fill_60m", "fill_eod"]
HISTORY_START = "2012-10-01"
AUDIT_START = "2013-01-01"
AUDIT_END = "2014-10-16"
SUPPORTING_CROSSCHECK_START = "2014-10-17"
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
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
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
        raise RuntimeError(f"historical source does not exist: {path}")
    if ADMITTED_DATASET_VERSION not in str(path):
        raise RuntimeError("source path is not the HE-00 admitted dataset identity")
    return path


def read_symbol(source: Path, symbol: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        source,
        filters=[("symbol", "==", symbol), ("trading_day", ">=", HISTORY_START), ("trading_day", "<=", AUDIT_END)],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError(f"no Audit-B rows for {symbol}")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].min() < HISTORY_START or frame["trading_day"].max() > AUDIT_END:
        raise RuntimeError(f"{symbol} source crossed Audit-B boundary")
    if (frame["trading_day"] >= SUPPORTING_CROSSCHECK_START).any():
        raise RuntimeError(f"{symbol} supporting-crosscheck row entered Audit B")
    if frame.duplicated(["trading_day", "timestamp"]).any():
        raise RuntimeError(f"{symbol} duplicate timestamp")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def build_audit_frame(source: Path, name: str, symbol: str) -> tuple[pd.DataFrame, dict]:
    minutes = read_symbol(source, symbol)
    clocks = targetmod.expected_clocks()
    expected_set = set(clocks["eod"])
    groups = {d: g.copy() for d, g in minutes.groupby("trading_day", sort=True)}
    days = sorted(groups)
    daily_rows = []
    exact_240 = {}
    for day in days:
        g = groups[day]
        present = g["clock"].tolist()
        exact = len(g) == 240 and len(set(present)) == 240 and set(present) == expected_set
        exact_240[day] = exact
        gg = g.set_index("clock")
        daily_rows.append({
            "trading_day": day,
            "close_1500": np.nan if "15:00" not in gg.index else pd.to_numeric(pd.Series([gg.loc["15:00", "close"]]), errors="coerce").iloc[0],
            "open_0931": np.nan if "09:31" not in gg.index else pd.to_numeric(pd.Series([gg.loc["09:31", "open"]]), errors="coerce").iloc[0],
            "exact_240": bool(exact),
        })
    daily = pd.DataFrame(daily_rows).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    close = pd.to_numeric(daily["close_1500"], errors="coerce")
    daily["prev_close"] = close.shift(1)
    daily["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    daily["gap"] = pd.to_numeric(daily["open_0931"], errors="coerce") / daily["prev_close"] - 1.0
    daily["abs_gap"] = daily["gap"].abs()
    daily["abs_gap_over_rvol20"] = daily["abs_gap"] / daily["rvol20"]
    audit_daily = daily.loc[(daily["trading_day"] >= AUDIT_START) & (daily["trading_day"] <= AUDIT_END)].copy()
    if audit_daily.empty:
        raise RuntimeError(f"{name} Audit-B daily inventory empty")

    rows = []
    invalid: dict[str, int] = {}
    for _, row in audit_daily.iterrows():
        day = str(row["trading_day"])
        if not bool(row["exact_240"]):
            invalid["not_exact_complete_240_clocks"] = invalid.get("not_exact_complete_240_clocks", 0) + 1
            continue
        numeric = [row["open_0931"], row["prev_close"], row["gap"], row["rvol20"], row["abs_gap_over_rvol20"]]
        if not all(np.isfinite(float(v)) for v in numeric) or float(row["rvol20"]) <= 0:
            invalid["incomplete_gap_or_rvol20"] = invalid.get("incomplete_gap_or_rvol20", 0) + 1
            continue
        day_row = pd.Series({"trading_day": day, "open_0931": float(row["open_0931"]), "prev_close": float(row["prev_close"]), "overnight_gap": float(row["gap"])})
        result = targetmod.compute_day(day_row, groups[day], clocks)
        if result is None or not bool(result.get("target_valid", False)):
            reason = "target_invalid" if result is None else str(result.get("invalid_reason"))
            invalid[reason] = invalid.get(reason, 0) + 1
            continue
        result["rvol20"] = float(row["rvol20"])
        result["abs_gap_over_rvol20"] = float(row["abs_gap_over_rvol20"])
        rows.append(result)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"{name} Audit-B target inventory empty")
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if frame["trading_day"].min() < AUDIT_START or frame["trading_day"].max() > AUDIT_END:
        raise RuntimeError(f"{name} invalid Audit-B target inventory")
    if int((frame["fill_15m"].astype(bool) & ~frame["fill_60m"].astype(bool)).sum()) or int((frame["fill_60m"].astype(bool) & ~frame["fill_eod"].astype(bool)).sum()):
        raise RuntimeError(f"{name} target nesting violation")
    audit_days = audit_daily["trading_day"].astype(str).tolist()
    return frame, {
        "symbol": symbol,
        "feature_history_start": HISTORY_START,
        "audit_window": {"start": AUDIT_START, "end": AUDIT_END},
        "minute_rows_loaded_including_feature_history": int(len(minutes)),
        "trading_days_loaded_including_feature_history": int(len(days)),
        "pre_audit_feature_history_days": int(sum(d < AUDIT_START for d in days)),
        "audit_trading_days_loaded": int(len(audit_days)),
        "audit_exact_240_days": int(sum(bool(exact_240[d]) for d in audit_days)),
        "target_valid_geometry_complete_rows": int(len(frame)),
        "invalid_reason_counts": invalid,
        "target_min_day": str(frame["trading_day"].min()),
        "target_max_day": str(frame["trading_day"].max()),
        "supporting_crosscheck_or_later_rows_loaded": False,
    }


def cumulative(bundle: dict, sign: str, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return evalbase.cumulative_probs(bundle["heads"][sign], x)


def dev_benchmark(bundle: dict, sign: str, n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    s = bundle["heads"][sign]["stages"]
    h15, h60, heod = float(s["15m"]["event_rate"]), float(s["60m"]["event_rate"]), float(s["eod"]["event_rate"])
    return np.full(n, h15), np.full(n, 1-(1-h15)*(1-h60)), np.full(n, 1-(1-h15)*(1-h60)*(1-heod))


def empty_metrics() -> dict:
    return {
        "n": 0,
        "horizons": {h: {"n": 0, "brier_score": None, "log_loss": None, "roc_auc": None, "pr_auc": None, "calibration_intercept": None, "calibration_slope": None, "probability_deciles": []} for h in HORIZONS},
        "integrated_brier": None,
        "integrated_log_loss": None,
    }


def safe_eval(part: pd.DataFrame, probs: tuple[np.ndarray, np.ndarray, np.ndarray], deciles: bool) -> dict:
    if len(part) == 0:
        return empty_metrics()
    return evalbase.evaluate_cohort(part, probs, include_deciles=deciles)


def evaluate_t2(frame: pd.DataFrame, sign: str, bundle: dict) -> dict:
    part = frame.loc[frame["gap_sign"] == sign].copy().reset_index(drop=True)
    if part.empty:
        return {"counts": {"all": 0, "gt10bp": 0, "gt30bp": 0}, "model": {}, "benchmark": {}, "sample_sufficient": False, "gates": None, "gate_pass_count": None, "audit_b_passed": False, "monotonicity_violations": 0, "calendar_all_gap": {}}
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise RuntimeError(f"nonfinite features for {sign}")
    mp = cumulative(bundle, sign, x)
    bp = dev_benchmark(bundle, sign, len(part))
    mono = int(np.sum((mp[0] > mp[1]) | (mp[1] > mp[2])))
    out = {"counts": {}, "model": {}, "benchmark": {}, "monotonicity_violations": mono}
    for cohort, threshold in MATERIAL.items():
        mask = np.ones(len(part), dtype=bool) if threshold == 0 else part["abs_gap"].to_numpy(float) > threshold
        cp = part.loc[mask].copy().reset_index(drop=True)
        out["counts"][cohort] = int(mask.sum())
        out["model"][cohort] = safe_eval(cp, tuple(p[mask] for p in mp), True)
        out["benchmark"][cohort] = safe_eval(cp, tuple(p[mask] for p in bp), False)
    c = out["counts"]
    sufficient = bool(c["all"] >= 25 and c["gt10bp"] >= 20 and c["gt30bp"] >= 12)
    out["sample_sufficient"] = sufficient
    if sufficient:
        m, b = out["model"], out["benchmark"]
        wins = sum(m["gt10bp"]["horizons"][h]["brier_score"] < b["gt10bp"]["horizons"][h]["brier_score"] for h in HORIZONS)
        gates = {
            "all_integrated_brier_better": m["all"]["integrated_brier"] < b["all"]["integrated_brier"],
            "all_integrated_log_loss_better": m["all"]["integrated_log_loss"] < b["all"]["integrated_log_loss"],
            "gt10_integrated_brier_better": m["gt10bp"]["integrated_brier"] < b["gt10bp"]["integrated_brier"],
            "gt30_integrated_brier_not_worse": m["gt30bp"]["integrated_brier"] <= b["gt30bp"]["integrated_brier"],
            "gt10_at_least_2_of_3_horizon_brier_better": wins >= 2,
            "monotonicity_violations_zero": mono == 0,
        }
        out["gates"] = {k: bool(v) for k, v in gates.items()}
        out["gate_pass_count"] = int(sum(out["gates"].values()))
        out["audit_b_passed"] = bool(all(out["gates"].values()))
    else:
        out["gates"], out["gate_pass_count"], out["audit_b_passed"] = None, None, False

    calendar = {}
    day = part["trading_day"].astype(str)
    masks = {
        "2013": day.str.startswith("2013-"),
        "2014-01-01_to_2014-10-16": (day >= "2014-01-01") & (day <= AUDIT_END),
    }
    for label, mask_series in masks.items():
        mask = mask_series.to_numpy(bool)
        yp = part.loc[mask].copy().reset_index(drop=True)
        if len(yp):
            calendar[label] = {"model": safe_eval(yp, tuple(p[mask] for p in mp), False), "benchmark": safe_eval(yp, tuple(p[mask] for p in bp), False)}
    out["calendar_all_gap"] = calendar
    return out


def evaluate_t1(frame: pd.DataFrame, sign: str, bundle: dict) -> dict:
    part = frame.loc[frame["gap_sign"] == sign].copy().reset_index(drop=True)
    if part.empty:
        return {"counts": {"all": 0, "gt10bp": 0, "gt30bp": 0}, "metrics": {}, "monotonicity_violations": 0}
    x = part[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    probs = cumulative(bundle, sign, x)
    out = {"counts": {}, "metrics": {}, "monotonicity_violations": int(np.sum((probs[0] > probs[1]) | (probs[1] > probs[2])))}
    for cohort, threshold in MATERIAL.items():
        mask = np.ones(len(part), dtype=bool) if threshold == 0 else part["abs_gap"].to_numpy(float) > threshold
        cp = part.loc[mask].copy().reset_index(drop=True)
        out["counts"][cohort] = int(mask.sum())
        out["metrics"][cohort] = safe_eval(cp, tuple(p[mask] for p in probs), True)
    return out


def main() -> int:
    protocol, external, csi1000 = load_json(PROTOCOL), load_json(EXTERNAL_PARAMETERS), load_json(CSI1000_PARAMETERS)
    if protocol["stage"] != "CT_AUDIT_B_preregistered_unopened" or not protocol["audit_a_opened"] or protocol["audit_b_opened"]:
        raise RuntimeError("Audit-B protocol state drifted")
    if protocol["audit_a_decision"] != "CT_AUDIT_A_cloud_review_passed_all_four_heads_Audit_B_eligible":
        raise RuntimeError("Audit-A authorization for Audit B missing")
    if sha256(EXTERNAL_PARAMETERS) != EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256:
        raise RuntimeError("external parameter artifact SHA256 drifted")
    if external["source_dataset_sha256_from_HE00"] != ADMITTED_DATASET_SHA256 or external["source_dataset_version"] != ADMITTED_DATASET_VERSION:
        raise RuntimeError("external parameter source identity drifted")
    for name, expected in [("CSI300", EXPECTED_CSI300_BUNDLE_SHA256), ("CSI500", EXPECTED_CSI500_BUNDLE_SHA256)]:
        item = external["external_index_bundles"][name]
        if item["parameter_bundle_sha256"] != expected or canonical_digest(item["parameter_bundle"]) != expected:
            raise RuntimeError(f"{name} bundle identity drifted")
    if csi1000["selected_architecture_sha256"] != EXPECTED_CSI1000_ARCH_SHA256 or canonical_digest(csi1000["parameter_bundle"]) != EXPECTED_CSI1000_BUNDLE_SHA256:
        raise RuntimeError("CSI1000 frozen identity drifted")

    source = require_source()
    results, audits, head_pass, head_suff = {}, {}, [], []
    for name, symbol in {"CSI300": "000300.SH", "CSI500": "000905.SH"}.items():
        frame, audit = build_audit_frame(source, name, symbol)
        audits[name] = audit
        ext_bundle = external["external_index_bundles"][name]["parameter_bundle"]
        t2, t1 = {}, {}
        for sign in ["high", "low"]:
            t2[sign] = evaluate_t2(frame, sign, ext_bundle)
            t1[sign] = evaluate_t1(frame, sign, csi1000["parameter_bundle"])
            head_pass.append(bool(t2[sign]["audit_b_passed"]))
            head_suff.append(bool(t2[sign]["sample_sufficient"]))
        results[name] = {
            "symbol": symbol,
            "counts": {"all": int(len(frame)), "high": int((frame["gap_sign"] == "high").sum()), "low": int((frame["gap_sign"] == "low").sum()), "gt10bp": int((frame["abs_gap"] > 0.001).sum()), "gt30bp": int((frame["abs_gap"] > 0.003).sum())},
            "T1_exact_CSI1000_parameter_transport_descriptive": t1,
            "T2_frozen_external_parameter_audit": t2,
        }
    all_sufficient = bool(len(head_suff) == 4 and all(head_suff))
    all_pass = bool(len(head_pass) == 4 and all(head_pass))
    if not all_sufficient:
        decision = "CT_AUDIT_B_evidence_insufficient"
    elif all_pass:
        decision = "CT_AUDIT_B_final_backward_external_robustly_confirmed"
    else:
        decision = "CT_AUDIT_B_final_backward_external_not_confirmed"

    receipt = {
        "schema_id": "overnight_open_gap_fill_cross_index_audit_b_receipt@1.0",
        "session_date": "2026-09-07",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "stage": "CT_AUDIT_B_completed_local_pending_cloud_review",
        "scientific_role": "final_backward_historical_external_confirmation",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source_dataset_version": ADMITTED_DATASET_VERSION,
        "source_dataset_sha256_from_HE00": ADMITTED_DATASET_SHA256,
        "external_parameter_artifact_sha256": EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256,
        "CSI300_parameter_bundle_sha256": EXPECTED_CSI300_BUNDLE_SHA256,
        "CSI500_parameter_bundle_sha256": EXPECTED_CSI500_BUNDLE_SHA256,
        "CSI1000_architecture_sha256": EXPECTED_CSI1000_ARCH_SHA256,
        "CSI1000_parameter_bundle_sha256": EXPECTED_CSI1000_BUNDLE_SHA256,
        "source_audits": audits,
        "indices": results,
        "all_four_T2_heads_sample_sufficient": all_sufficient,
        "all_four_T2_heads_pass_all_six_gates": all_pass,
        "decision": decision,
        "T1_refit_performed": False,
        "T2_refit_performed": False,
        "scaler_refit_performed": False,
        "feature_search_performed": False,
        "model_class_search_performed": False,
        "hyperparameter_search_performed": False,
        "threshold_search_performed": False,
        "probability_calibration_performed": False,
        "supporting_crosscheck_opened": False,
        "csi1000_post_2026_08_21_outcomes_opened": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    usage = {
        "schema_id": "overnight_open_gap_fill_cross_index_audit_b_data_usage@1.0",
        "session_date": "2026-09-07",
        "research_identity": "gap_fill_cross_index_transport_v1",
        "opened": {"CSI300_Audit_B_2013-01-01_to_2014-10-16": True, "CSI500_Audit_B_2013-01-01_to_2014-10-16": True},
        "feature_history_only": {"2012-10-01_to_2012-12-31": True},
        "sealed": {"supporting_crosscheck_2014-10-17_to_2014-12-31": True, "CSI1000_2026Q4_true_fresh": True},
        "aggregate_outputs_only": True,
        "raw_rows_written_to_repo": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    dump_json(USAGE, usage)
    print("GAP_FILL_CROSS_INDEX_AUDIT_B_RESULT", json.dumps({"decision": decision, "all_four_sample_sufficient": all_sufficient, "all_four_pass": all_pass, "supporting_crosscheck_opened": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
