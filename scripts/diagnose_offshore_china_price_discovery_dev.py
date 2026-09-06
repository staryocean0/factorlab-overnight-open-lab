#!/usr/bin/env python3
"""OHR-06 development-only offshore-China price-discovery diagnostic.

This script is NOT a candidate selector. It uses the OHR-05 frozen Yahoo source
identity, reconstructs the accepted Median direction head in 2016-2025 expanding
OOF, and tests only the seven preregistered offshore state representations.
No 2026 row may be loaded.
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

import diagnose_high_open_false_negatives_dev as highdiag
import select_high_open_recall_phase2_dev as phase2

SOURCE_ENV = "OVERNIGHT_OFFSHORE_ETF_DAILY"
ACCEPTED_SOURCE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
ACCEPTED_PROVIDER = "Yahoo Finance chart v8 (query1.finance.yahoo.com)"
SYMBOLS = ["ASHS", "ASHR", "FXI", "MCHI", "SPY"]
REPS = [
    "ashs_session",
    "ashr_session",
    "ashs_minus_ashr",
    "a_share_consensus",
    "a_share_specific_vs_spy",
    "broad_china_specific_vs_spy",
    "china_etf_positive_breadth",
]
CHINA_SPECIFIC = [
    "ashs_minus_ashr",
    "a_share_specific_vs_spy",
    "broad_china_specific_vs_spy",
]
PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_offshore_china_ohr06_diagnostic_protocol_v1.json"
SOURCE_RECEIPT = ROOT / "docs/research/cloud_session_20260906_local_offshore_china_source_freeze_v1.json"
INCUMBENT = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
PHASE2_RECEIPT = ROOT / "docs/research/cloud_session_20260906_local_high_open_recall_phase2_dev_receipt_v1.json"
OUT = ROOT / "docs/research/cloud_session_20260906_local_offshore_china_ohr06_diagnostic_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_session_20260906_offshore_china_ohr06_data_usage.json"
YEARS = list(range(2016, 2026))
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


def load_frozen_source(path: Path) -> pd.DataFrame:
    if sha256(path) != ACCEPTED_SOURCE_SHA:
        raise RuntimeError("offshore source SHA does not match OHR-05 frozen Yahoo identity")
    if path.suffix.lower() in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
    elif path.suffix.lower() in {".csv", ".txt"}:
        frame = pd.read_csv(path)
    else:
        raise RuntimeError("offshore source must be parquet/csv")
    required = {"date", "symbol", "open", "close", "volume"}
    if not required.issubset(frame.columns):
        raise RuntimeError(f"offshore source missing {sorted(required - set(frame.columns))}")
    out = frame[["date", "symbol", "open", "close", "volume"]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out["symbol"] = out["symbol"].astype(str).str.upper().str.strip()
    for col in ["open", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    if out["date"].isna().any() or out.duplicated(["symbol", "date"]).any():
        raise RuntimeError("invalid date or duplicate symbol/date in offshore source")
    if set(out["symbol"]) != set(SYMBOLS):
        raise RuntimeError("OHR-06 source symbol inventory differs from OHR-05 freeze")
    if out["date"].max() > pd.Timestamp("2025-12-31"):
        raise RuntimeError("offshore source contains post-2025 rows")
    return out.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def compound(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(np.prod(1.0 + np.asarray(values, dtype=float)) - 1.0)


def attach_offshore_states(frame: pd.DataFrame, source: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = frame.copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    by_symbol = {s: source.loc[source["symbol"] == s].set_index("date") for s in SYMBOLS}
    spy_dates = sorted(by_symbol["SPY"].index.tolist())
    day_values = pd.to_datetime(out["trading_day"]).dt.normalize().tolist()
    prev_values = [pd.NaT] + day_values[:-1]

    rows: list[dict] = []
    excluded_zero_volume = 0
    excluded_missing = 0
    zero_session_rows = 0
    session_count_hist: dict[str, int] = {}

    for p, d in zip(prev_values, day_values):
        if pd.isna(p):
            rows.append({rep: np.nan for rep in REPS} | {"offshore_common_valid": False, "offshore_us_session_count": np.nan})
            continue
        sessions = [s for s in spy_dates if p <= s < d]
        session_count_hist[str(len(sessions))] = session_count_hist.get(str(len(sessions)), 0) + 1
        if not sessions:
            zero_session_rows += 1
            compounded = {s: 0.0 for s in SYMBOLS}
            valid = True
        else:
            valid = True
            per_symbol: dict[str, list[float]] = {s: [] for s in SYMBOLS}
            saw_missing = False
            saw_zero_volume = False
            for us_day in sessions:
                for symbol in SYMBOLS:
                    sf = by_symbol[symbol]
                    if us_day not in sf.index:
                        saw_missing = True
                        valid = False
                        continue
                    row = sf.loc[us_day]
                    op = float(row["open"])
                    cl = float(row["close"])
                    vol = float(row["volume"])
                    if not np.isfinite(op) or not np.isfinite(cl) or not np.isfinite(vol) or op <= 0 or cl <= 0:
                        saw_missing = True
                        valid = False
                        continue
                    if vol <= 0:
                        saw_zero_volume = True
                        valid = False
                        continue
                    per_symbol[symbol].append(cl / op - 1.0)
            if saw_missing:
                excluded_missing += 1
            if saw_zero_volume:
                excluded_zero_volume += 1
            compounded = {s: compound(per_symbol[s]) for s in SYMBOLS} if valid else {s: np.nan for s in SYMBOLS}

        if valid:
            ashs = compounded["ASHS"]
            ashr = compounded["ASHR"]
            fxi = compounded["FXI"]
            mchi = compounded["MCHI"]
            spy = compounded["SPY"]
            rep = {
                "ashs_session": ashs,
                "ashr_session": ashr,
                "ashs_minus_ashr": ashs - ashr,
                "a_share_consensus": 0.5 * (ashs + ashr),
                "a_share_specific_vs_spy": 0.5 * (ashs + ashr) - spy,
                "broad_china_specific_vs_spy": 0.5 * (fxi + mchi) - spy,
                "china_etf_positive_breadth": float(np.mean(np.asarray([ashs, ashr, fxi, mchi]) > 0.0)),
                "offshore_common_valid": True,
                "offshore_us_session_count": int(len(sessions)),
            }
        else:
            rep = {r: np.nan for r in REPS} | {"offshore_common_valid": False, "offshore_us_session_count": int(len(sessions))}
        rows.append(rep)

    states = pd.DataFrame(rows)
    for col in states.columns:
        out[col] = states[col].to_numpy()
    audit = {
        "zero_completed_us_session_rows": int(zero_session_rows),
        "excluded_for_zero_volume_required_session": int(excluded_zero_volume),
        "excluded_for_missing_or_invalid_required_session": int(excluded_missing),
        "session_count_histogram": session_count_hist,
    }
    return out, audit


def quartiles(part: pd.DataFrame, rep: str) -> dict:
    ranked = pd.to_numeric(part[rep], errors="coerce").rank(method="first")
    q = pd.qcut(ranked, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    tmp = part.assign(_q=q.astype(str))
    result: dict[str, dict] = {}
    for label in ["Q1", "Q2", "Q3", "Q4"]:
        p = tmp.loc[tmp["_q"] == label]
        result[label] = {
            "n": int(len(p)),
            "mean_representation": float(pd.to_numeric(p[rep], errors="coerce").mean()),
            "actual_up_share": float(p["actual_up"].mean()),
        }
    return result


def diagnose_rep(primary: pd.DataFrame, rep: str) -> dict:
    part = primary.loc[pd.to_numeric(primary[rep], errors="coerce").notna()].copy()
    up = part.loc[part["actual_up"]]
    down = part.loc[~part["actual_up"]]
    up_values = pd.to_numeric(up[rep], errors="coerce")
    down_values = pd.to_numeric(down[rep], errors="coerce")
    all_values = pd.to_numeric(part[rep], errors="coerce")
    mean_diff = float(up_values.mean() - down_values.mean())
    median_diff = float(up_values.median() - down_values.median())
    std = float(all_values.std(ddof=0))
    standardized = None if std <= 0 else float(mean_diff / std)

    annual: dict[str, dict] = {}
    diffs: list[float] = []
    for year in YEARS:
        yp = part.loc[part["oof_year"] == year]
        yu = yp.loc[yp["actual_up"]]
        yd = yp.loc[~yp["actual_up"]]
        if yu.empty or yd.empty:
            diff = None
        else:
            diff = float(pd.to_numeric(yu[rep], errors="coerce").mean() - pd.to_numeric(yd[rep], errors="coerce").mean())
            diffs.append(diff)
        annual[str(year)] = {"n": int(len(yp)), "n_up": int(len(yu)), "n_down": int(len(yd)), "mean_difference": diff}

    qs = quartiles(part, rep)
    positive_years = int(sum(x > EPS for x in diffs))
    median_annual = None if not diffs else float(np.median(diffs))
    gates = {
        "pooled_mean_difference_positive": mean_diff > EPS,
        "positive_annual_difference_count_at_least_6": positive_years >= 6,
        "median_annual_difference_positive": median_annual is not None and median_annual > EPS,
        "top_quartile_actual_up_share_gt_bottom_quartile": qs["Q4"]["actual_up_share"] > qs["Q1"]["actual_up_share"] + EPS,
    }
    return {
        "n": int(len(part)),
        "n_actual_up": int(part["actual_up"].sum()),
        "n_actual_down": int((~part["actual_up"]).sum()),
        "actual_up_mean": float(up_values.mean()),
        "actual_down_mean": float(down_values.mean()),
        "actual_up_minus_down_mean": mean_diff,
        "actual_up_median": float(up_values.median()),
        "actual_down_median": float(down_values.median()),
        "actual_up_minus_down_median": median_diff,
        "standardized_mean_difference": standardized,
        "quartiles": qs,
        "annual": annual,
        "positive_annual_difference_count": positive_years,
        "median_annual_mean_difference": median_annual,
        "mechanism_gates": gates,
        "passes_mechanism_gates": bool(all(gates.values())),
    }


def supporting_disagreement(incumbent_oof: pd.DataFrame, candidate_oof: pd.DataFrame, rep: str) -> dict:
    if incumbent_oof["trading_day"].tolist() != candidate_oof["trading_day"].tolist():
        raise RuntimeError("incumbent/candidate day inventory mismatch")
    merged = incumbent_oof.copy()
    merged["candidate_pred_up"] = candidate_oof["pred_up"].to_numpy(dtype=bool)
    flip = merged.loc[(~merged["pred_up"]) & merged["candidate_pred_up"] & merged["offshore_common_valid"]].copy()
    rescue = flip.loc[flip["actual_up"]]
    false_high = flip.loc[~flip["actual_up"]]
    if rescue.empty or false_high.empty:
        mean_diff = None
    else:
        mean_diff = float(pd.to_numeric(rescue[rep], errors="coerce").mean() - pd.to_numeric(false_high[rep], errors="coerce").mean())
    return {
        "n_added_up": int(len(flip)),
        "n_rescued_high": int(len(rescue)),
        "n_new_false_high": int(len(false_high)),
        "added_up_precision": None if flip.empty else float(len(rescue) / len(flip)),
        "rescue_minus_false_high_mean_difference": mean_diff,
    }


def main() -> int:
    source_value = os.environ.get(SOURCE_ENV)
    if not source_value:
        raise RuntimeError(f"{SOURCE_ENV} is required and must point to the exact OHR-05 frozen Yahoo development file")
    source_path = Path(source_value).expanduser().resolve()
    if not source_path.is_file():
        raise RuntimeError("frozen offshore source file not found")

    protocol = load_json(PROTOCOL)
    source_receipt = load_json(SOURCE_RECEIPT)
    incumbent_spec = load_json(INCUMBENT)
    phase2_receipt = load_json(PHASE2_RECEIPT)
    if source_receipt["provider"] != ACCEPTED_PROVIDER or source_receipt["source_sha256"] != ACCEPTED_SOURCE_SHA:
        raise RuntimeError("OHR-05 receipt identity does not match OHR-06 protocol")
    if protocol["accepted_source"]["source_sha256"] != ACCEPTED_SOURCE_SHA:
        raise RuntimeError("OHR-06 protocol source SHA drifted")
    if incumbent_spec["selected_spec_sha256"] != protocol["fixed_incumbent"]["spec_sha256"]:
        raise RuntimeError("incumbent identity drifted")

    source = load_frozen_source(source_path)
    frame, reconstruction = highdiag.build_development_frame()
    frame, clock_audit = attach_offshore_states(frame, source)
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered OHR-06 development frame")

    cols = list(incumbent_spec["selected_spec"]["direction_features"])
    incumbent_oof = highdiag.expanding_oof(frame, cols)
    common = incumbent_oof["offshore_common_valid"].astype(bool) & incumbent_oof[REPS].notna().all(axis=1)
    primary = incumbent_oof.loc[common & (~incumbent_oof["pred_up"]) & (pd.to_numeric(incumbent_oof["prev_last_hour"], errors="coerce") < 0.0)].copy()
    if primary.empty:
        raise RuntimeError("OHR-06 primary slice is empty")

    rep_results = {rep: diagnose_rep(primary, rep) for rep in REPS}

    last = next(a for a in phase2_receipt["attempts"] if a["name"] == "weakness_last_hour_piecewise")
    candidate_cols = list(last["candidate_spec"]["direction_features"])
    candidate_oof = phase2.expanding_oof(frame, candidate_cols, cols)
    replay = phase2.score_metrics(candidate_oof)
    for key in ["direction_hit", "balanced_accuracy", "recall_up", "recall_down", "material_high_open_gt10bp_recall", "material_high_open_gt30bp_recall"]:
        if abs(float(replay[key]) - float(last["metrics"][key])) > 1e-12:
            raise RuntimeError(f"OHR-02 last-hour replay drifted on {key}")
    supporting = {rep: supporting_disagreement(incumbent_oof, candidate_oof, rep) for rep in REPS}

    china_specific_passers = [rep for rep in CHINA_SPECIFIC if rep_results[rep]["passes_mechanism_gates"]]
    later_family_authorized = bool(china_specific_passers)
    receipt = {
        "schema_id": "overnight_open_offshore_china_ohr06_diagnostic_receipt@1.0",
        "session_date": "2026-09-06",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source_receipt": str(SOURCE_RECEIPT.relative_to(ROOT)),
        "source_sha256": ACCEPTED_SOURCE_SHA,
        "provider": ACCEPTED_PROVIDER,
        "development_window": {"start": highdiag.DEV_START, "end": highdiag.DEV_END},
        "oof_years": YEARS,
        "n_incumbent_oof": int(len(incumbent_oof)),
        "n_common_offshore_oof": int(common.sum()),
        "n_primary_slice": int(len(primary)),
        "primary_slice_actual_up_share": float(primary["actual_up"].mean()),
        "clock_audit": clock_audit,
        "representation_results": rep_results,
        "supporting_ohr04_disagreement": supporting,
        "china_specific_representations": CHINA_SPECIFIC,
        "china_specific_passers": china_specific_passers,
        "china_specific_passer_count": int(len(china_specific_passers)),
        "later_bounded_candidate_family_authorized": later_family_authorized,
        "decision": "mechanism_supported_freeze_later_bounded_family" if later_family_authorized else "no_china_specific_mechanism_support_retain_incumbent",
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "offshore_etf_daily": sha256(source_path),
            "annotated_panel": sha256(highdiag.ANNOTATED_PANEL),
            "datahub_1m_export": sha256(highdiag.DATAHUB_1M),
            "fred_nasdaq": sha256(highdiag.FRED_NDQ),
            "fred_vix": sha256(highdiag.FRED_VIX),
            "incumbent": sha256(INCUMBENT),
            "phase2_receipt": sha256(PHASE2_RECEIPT),
            "source_receipt": sha256(SOURCE_RECEIPT),
            "protocol": sha256(PROTOCOL),
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
        "raw_offshore_rows_written_to_repo": False,
        "raw_development_rows_newly_written_by_runner": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    usage = {
        "schema_id": "overnight_open_local_offshore_china_ohr06_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31_mechanism_diagnostic_only",
        "offshore_source_sha256": ACCEPTED_SOURCE_SHA,
        "candidate_selection_performed": False,
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_offshore_rows_persisted_in_repo": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)
    summary = {
        "n_incumbent_oof": receipt["n_incumbent_oof"],
        "n_common_offshore_oof": receipt["n_common_offshore_oof"],
        "n_primary_slice": receipt["n_primary_slice"],
        "china_specific_passers": china_specific_passers,
        "decision": receipt["decision"],
        "2026_blackbox_opened": False,
    }
    print("OFFSHORE_CHINA_OHR06_DIAGNOSTIC_RESULT", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
