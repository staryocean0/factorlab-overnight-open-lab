#!/usr/bin/env python3
"""Gap-fill prediction V2 Phase-1 development-only factor diagnostic.

This runner does NOT fit a gap-fill candidate model. It reconstructs the frozen
V1 direction/magnitude specs in expanding-year OOF form to create preregistered
surprise/support probes, reconstructs the already-frozen gap-fill targets, and
reports mechanism diagnostics separately by high/low gap and horizon.

No 2026 row may be loaded.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_gap_fill_v2_target_ledger as targetmod
import diagnose_high_open_false_negatives_dev as highdiag
import diagnose_offshore_china_price_discovery_dev as ohr06

PROTOCOL = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase1_factor_diagnostic_protocol_v1.json"
PARENT = ROOT / "docs/governance/cloud_session_20260906_gap_fill_prediction_v2_protocol_v1.json"
TARGET_LEDGER = ROOT / "docs/research/cloud_session_20260906_gap_fill_v2_target_ledger_v1.json"
DIRECTION_SPEC = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
TWO_HEAD_SPEC = ROOT / "docs/governance/cloud_session_20260906_two_head_selected_v1.json"
OFFSHORE = ROOT / "data/offshore_etf_dev_2015_2025/offshore_etf_daily.parquet"
PANEL = ROOT / "data/high_open_dev_2015_2025/annotated_panel.parquet"
MINUTES = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
OUT = ROOT / "docs/research/cloud_session_20260906_gap_fill_v2_phase1_factor_diagnostic_receipt_v1.json"
USAGE = ROOT / "docs/governance/cloud_session_20260906_gap_fill_v2_phase1_factor_data_usage_v1.json"

START = "2015-01-05"
END = "2025-12-31"
YEARS = list(range(2016, 2026))
MATERIAL = {"gt10bp": 0.001, "gt30bp": 0.003}
EXPECTED_DIRECTION_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"
EXPECTED_TWO_HEAD_SHA = "76ff94f401eb3a9a9edc1cc462a3d818b49bfc732b93ee0bfc1a7070f92ccb8f"
EXPECTED_OFFSHORE_SHA = "045cf728977ff72a9fabd236aaf06b7a9df3310ad1f6f487bd594d487cc05ffd"
EPS = 1e-12


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


def complete_mask(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    return x.notna().all(axis=1) & y.notna()


def ridge_pipe(alpha: float) -> Pipeline:
    return Pipeline([("sc", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def build_v1_oof(frame: pd.DataFrame, direction_features: list[str], magnitude_features: list[str]) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    year = pd.to_datetime(frame["trading_day"]).dt.year
    for valid_year in YEARS:
        tr = frame.loc[year < valid_year].copy()
        va = frame.loc[year == valid_year].copy()

        md_tr = complete_mask(tr, direction_features)
        md_va = complete_mask(va, direction_features)
        mm_tr = complete_mask(tr, magnitude_features)
        mm_va = complete_mask(va, magnitude_features)
        if int(md_tr.sum()) == 0 or int(md_va.sum()) == 0 or int(mm_tr.sum()) == 0 or int(mm_va.sum()) == 0:
            raise RuntimeError(f"empty V1 OOF fold for {valid_year}")

        direction = highdiag.median_pipe()
        direction.fit(
            tr.loc[md_tr, direction_features].apply(pd.to_numeric, errors="coerce"),
            pd.to_numeric(tr.loc[md_tr, "gap"], errors="coerce"),
        )
        mag = ridge_pipe(100.0)
        mag.fit(
            tr.loc[mm_tr, magnitude_features].apply(pd.to_numeric, errors="coerce"),
            pd.to_numeric(tr.loc[mm_tr, "gap"], errors="coerce"),
        )

        part = va[["trading_day", "gap", "rvol20", "prev_daytime", "prev_last_hour", "prev_gap",
                   "us_nasdaq_interval", "us_vix_interval", "broad_china_specific_vs_spy"]].copy()
        part["oof_year"] = int(valid_year)
        part["v1_direction_score_oof"] = np.nan
        part["v1_magnitude_oof"] = np.nan

        dscore = direction.predict(va.loc[md_va, direction_features].apply(pd.to_numeric, errors="coerce"))
        mscore = mag.predict(va.loc[mm_va, magnitude_features].apply(pd.to_numeric, errors="coerce"))
        part.loc[md_va, "v1_direction_score_oof"] = np.asarray(dscore, dtype=float)
        part.loc[mm_va, "v1_magnitude_oof"] = np.abs(np.asarray(mscore, dtype=float))
        pieces.append(part)

    out = pd.concat(pieces, ignore_index=True)
    if out.empty or int(pd.to_datetime(out["trading_day"]).dt.year.min()) != 2016 or int(pd.to_datetime(out["trading_day"]).dt.year.max()) != 2025:
        raise RuntimeError("V1 OOF window drifted")
    if (pd.to_datetime(out["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered V1 OOF references")
    return out


def build_targets() -> pd.DataFrame:
    panel = pd.read_parquet(
        PANEL,
        filters=[("trading_day", ">=", START), ("trading_day", "<=", END)],
        columns=["trading_day", "open_0931", "prev_close", "overnight_gap"],
    )
    panel["trading_day"] = panel["trading_day"].astype(str)
    minutes = pd.read_parquet(
        MINUTES,
        filters=[("symbol", "==", targetmod.SYMBOL), ("trading_day", ">=", START), ("trading_day", "<=", END)],
        columns=["trading_day", "timestamp", "open", "high", "low", "close"],
    )
    minutes["trading_day"] = minutes["trading_day"].astype(str)
    if (pd.to_datetime(panel["trading_day"]).dt.year >= 2026).any() or (pd.to_datetime(minutes["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered V2 Phase-1 target reconstruction")
    groups = {d: g.copy() for d, g in minutes.groupby("trading_day", sort=False)}
    clocks = targetmod.expected_clocks()
    rows: list[dict] = []
    for _, row in panel.sort_values("trading_day").iterrows():
        day = row["trading_day"]
        if day not in groups:
            continue
        r = targetmod.compute_day(row, groups[day], clocks)
        if r is not None and bool(r.get("target_valid", False)):
            rows.append(r)
    out = pd.DataFrame(rows)
    out = out.loc[pd.to_datetime(out["trading_day"]).dt.year.isin(YEARS)].copy()
    if out.empty or (pd.to_datetime(out["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("invalid Phase-1 target inventory")
    return out


def add_probes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    gap = pd.to_numeric(out["gap"], errors="coerce")
    sign = np.where(gap > 0.0, 1.0, -1.0)
    abs_gap = gap.abs()
    rvol = pd.to_numeric(out["rvol20"], errors="coerce")
    out["abs_gap"] = abs_gap
    out["abs_gap_over_rvol20"] = np.where(rvol > 0.0, abs_gap / rvol, np.nan)
    out["v1_magnitude_surprise"] = abs_gap - pd.to_numeric(out["v1_magnitude_oof"], errors="coerce")
    out["v1_direction_support"] = sign * pd.to_numeric(out["v1_direction_score_oof"], errors="coerce")
    out["broad_china_specific_support"] = sign * pd.to_numeric(out["broad_china_specific_vs_spy"], errors="coerce")
    out["nasdaq_interval_support"] = sign * pd.to_numeric(out["us_nasdaq_interval"], errors="coerce")
    out["vix_interval_support"] = -sign * pd.to_numeric(out["us_vix_interval"], errors="coerce")
    out["prior_daytime_alignment"] = sign * pd.to_numeric(out["prev_daytime"], errors="coerce")
    out["prior_last_hour_alignment"] = sign * pd.to_numeric(out["prev_last_hour"], errors="coerce")
    out["prior_gap_alignment"] = sign * pd.to_numeric(out["prev_gap"], errors="coerce")
    return out


def expected_sign(effect: str) -> int:
    if effect == "higher":
        return 1
    if effect == "lower":
        return -1
    raise ValueError(effect)


def analyze(part: pd.DataFrame, probe: str, fill_col: str, effect: str) -> dict:
    x = pd.to_numeric(part[probe], errors="coerce")
    y = part[fill_col].astype(bool)
    valid = x.notna() & y.notna()
    x = x.loc[valid]
    y = y.loc[valid]
    if len(x) < 20 or int(y.sum()) == 0 or int((~y).sum()) == 0:
        return {"n": int(len(x)), "insufficient": True}
    filled = x.loc[y]
    unfilled = x.loc[~y]
    diff = float(filled.mean() - unfilled.mean())
    std = float(x.std(ddof=0))
    standardized = None if std <= 0 else float(diff / std)

    ranked = x.rank(method="first")
    q = pd.qcut(ranked, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    qdf = pd.DataFrame({"x": x, "y": y, "q": q.astype(str)})
    quartiles = {}
    for label in ["Q1", "Q2", "Q3", "Q4"]:
        qp = qdf.loc[qdf["q"] == label]
        quartiles[label] = {"n": int(len(qp)), "probe_mean": float(qp["x"].mean()), "fill_rate": float(qp["y"].mean())}

    annual = {}
    annual_diffs: list[float] = []
    expected = expected_sign(effect)
    matching_years = 0
    for yr in YEARS:
        yp = part.loc[part["oof_year"] == yr].copy()
        xx = pd.to_numeric(yp[probe], errors="coerce")
        yy = yp[fill_col].astype(bool)
        mv = xx.notna() & yy.notna()
        xx = xx.loc[mv]
        yy = yy.loc[mv]
        if len(xx) == 0 or int(yy.sum()) == 0 or int((~yy).sum()) == 0:
            d = None
        else:
            d = float(xx.loc[yy].mean() - xx.loc[~yy].mean())
            annual_diffs.append(d)
            if expected * d > EPS:
                matching_years += 1
        annual[str(yr)] = {"n": int(len(xx)), "filled": int(yy.sum()) if len(xx) else 0, "difference": d}

    median_annual = None if not annual_diffs else float(np.median(annual_diffs))
    return {
        "n": int(len(x)),
        "filled_n": int(y.sum()),
        "unfilled_n": int((~y).sum()),
        "filled_mean": float(filled.mean()),
        "unfilled_mean": float(unfilled.mean()),
        "filled_minus_unfilled_mean": diff,
        "standardized_mean_difference": standardized,
        "quartiles": quartiles,
        "annual": annual,
        "matching_direction_year_count": int(matching_years),
        "median_annual_difference": median_annual,
        "pooled_matches_expected": bool(expected * diff > EPS),
        "median_annual_matches_expected": bool(median_annual is not None and expected * median_annual > EPS),
        "quartile_matches_expected": bool(
            quartiles["Q4"]["fill_rate"] > quartiles["Q1"]["fill_rate"] + EPS
            if effect == "higher" else
            quartiles["Q4"]["fill_rate"] < quartiles["Q1"]["fill_rate"] - EPS
        ),
        "insufficient": False,
    }


def main() -> int:
    protocol = load_json(PROTOCOL)
    parent = load_json(PARENT)
    target_receipt = load_json(TARGET_LEDGER)
    direction_spec = load_json(DIRECTION_SPEC)
    two_head = load_json(TWO_HEAD_SPEC)

    if protocol["research_identity"] != "gap_fill_prediction_v2":
        raise RuntimeError("Phase-1 protocol identity drifted")
    if direction_spec["selected_spec_sha256"] != EXPECTED_DIRECTION_SHA:
        raise RuntimeError("direction V1 identity drifted")
    if two_head["selected_spec"]["sha256"] != EXPECTED_TWO_HEAD_SHA:
        raise RuntimeError("magnitude V1 identity drifted")
    if sha256(OFFSHORE) != EXPECTED_OFFSHORE_SHA:
        raise RuntimeError("offshore source identity drifted")
    if target_receipt["2026_rows_loaded"] is not False or target_receipt["model_fitting_performed"] is not False:
        raise RuntimeError("target-ledger evidence boundary invalid")
    if parent["prediction_timestamp"] != "09:31_China_time_after_open_gap_is_observed":
        raise RuntimeError("V2 prediction timestamp drifted")

    frame, reconstruction = highdiag.build_development_frame()
    source = ohr06.load_frozen_source(OFFSHORE)
    frame, clock_audit = ohr06.attach_offshore_states(frame, source)
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered Phase-1 feature frame")

    direction_features = list(direction_spec["selected_spec"]["direction_features"])
    magnitude_features = list(two_head["selected_spec"]["magnitude_head"]["features"])
    v1 = build_v1_oof(frame, direction_features, magnitude_features)
    targets = build_targets()
    merged = v1.merge(
        targets[["trading_day", "gap_sign", "abs_gap", "fill_15m", "fill_60m", "fill_eod"]],
        on="trading_day",
        how="inner",
        suffixes=("", "_target"),
        validate="one_to_one",
    )
    if merged.empty:
        raise RuntimeError("Phase-1 V1/target merge is empty")
    if (pd.to_datetime(merged["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered Phase-1 merged inventory")
    merged = add_probes(merged)

    probe_defs = {p["name"]: p for p in protocol["probes"]}
    probe_names = [p["name"] for p in protocol["probes"]]
    common_cols = probe_names + ["fill_15m", "fill_60m", "fill_eod", "gap_sign", "oof_year"]
    common = merged[common_cols].notna().all(axis=1)
    common_frame = merged.loc[common].copy()
    if common_frame.empty:
        raise RuntimeError("Phase-1 common complete-row inventory is empty")

    results: dict[str, dict] = {"high": {}, "low": {}}
    passers: list[dict] = []
    for sign in ["high", "low"]:
        sign_part = common_frame.loc[common_frame["gap_sign"] == sign].copy()
        for horizon in ["fill_15m", "fill_60m", "fill_eod"]:
            results[sign][horizon] = {}
            for probe in probe_names:
                effect = probe_defs[probe]["higher_expected_fill_effect"]
                gt10 = sign_part.loc[pd.to_numeric(sign_part["abs_gap"], errors="coerce") > MATERIAL["gt10bp"]].copy()
                gt30 = sign_part.loc[pd.to_numeric(sign_part["abs_gap"], errors="coerce") > MATERIAL["gt30bp"]].copy()
                a10 = analyze(gt10, probe, horizon, effect)
                a30 = analyze(gt30, probe, horizon, effect)
                expected = expected_sign(effect)
                gt30_same = bool(not a30.get("insufficient", True) and expected * float(a30["filled_minus_unfilled_mean"]) > EPS)
                gate = {
                    "pooled_gt10_matches_expected": bool(not a10.get("insufficient", True) and a10.get("pooled_matches_expected", False)),
                    "matching_direction_year_count_at_least_6": bool(not a10.get("insufficient", True) and int(a10.get("matching_direction_year_count", 0)) >= 6),
                    "median_annual_gt10_matches_expected": bool(not a10.get("insufficient", True) and a10.get("median_annual_matches_expected", False)),
                    "quartile_gt10_matches_expected": bool(not a10.get("insufficient", True) and a10.get("quartile_matches_expected", False)),
                    "gt30_pooled_same_direction": gt30_same,
                }
                passes = bool(all(gate.values()))
                results[sign][horizon][probe] = {
                    "block": probe_defs[probe]["block"],
                    "expected_higher_fill_effect": effect,
                    "gt10bp": a10,
                    "gt30bp": a30,
                    "mechanism_gate": gate,
                    "passes_mechanism_gate": passes,
                }
                if passes:
                    passers.append({"sign": sign, "horizon": horizon, "probe": probe, "block": probe_defs[probe]["block"]})

    blocks = sorted(set(p["block"] for p in protocol["probes"]))
    block_summary = {}
    for block in blocks:
        bp = [x for x in passers if x["block"] == block]
        block_summary[block] = {
            "passer_count": int(len(bp)),
            "passers": bp,
            "authorized_for_later_family_discussion": bool(bp),
        }

    receipt = {
        "schema_id": "overnight_open_gap_fill_v2_phase1_factor_diagnostic_receipt@1.0",
        "session_date": "2026-09-06",
        "research_identity": "gap_fill_prediction_v2",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "development_window": {"start": START, "end": END},
        "diagnostic_oof_years": YEARS,
        "n_v1_oof_rows": int(len(v1)),
        "n_valid_target_rows_2016_2025": int(len(targets)),
        "n_merged_rows": int(len(merged)),
        "n_common_complete_rows": int(len(common_frame)),
        "common_inventory_by_sign": {s: int((common_frame["gap_sign"] == s).sum()) for s in ["high", "low"]},
        "probe_count": int(len(probe_names)),
        "probes": probe_names,
        "results": results,
        "mechanism_passers": passers,
        "mechanism_passer_count": int(len(passers)),
        "factor_block_summary": block_summary,
        "later_bounded_family_discussion_authorized": bool(passers),
        "reconstruction_2015_2020_max_abs": reconstruction,
        "offshore_clock_audit": clock_audit,
        "source_hashes": {
            "protocol": sha256(PROTOCOL),
            "parent_protocol": sha256(PARENT),
            "target_ledger": sha256(TARGET_LEDGER),
            "direction_spec": sha256(DIRECTION_SPEC),
            "two_head_spec": sha256(TWO_HEAD_SPEC),
            "annotated_panel": sha256(PANEL),
            "one_minute_official": sha256(MINUTES),
            "offshore_etf": sha256(OFFSHORE),
            "runner": sha256(Path(__file__)),
        },
        "v1_reference_fitting_performed": True,
        "v1_reference_fits_used_gap_fill_outcomes": False,
        "gap_fill_model_fitting_performed": False,
        "candidate_selection_performed": False,
        "feature_selection_performed": False,
        "threshold_search_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    usage = {
        "schema_id": "overnight_open_gap_fill_v2_phase1_factor_data_usage@1.0",
        "session_date": "2026-09-06",
        "development": "2015-01-05_to_2025-12-31_with_2016_to_2025_expanding_year_V1_reference_OOF",
        "target_use": "diagnostic_only_no_gap_fill_candidate_fit",
        "2026-01-05_to_2026-08-21": "not_loaded_repeat_only_reserved",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_rows_newly_persisted": False,
        "production_authority": False,
    }
    dump_json(USAGE, usage)
    print("GAP_FILL_V2_PHASE1_FACTOR_DIAGNOSTIC_RESULT", json.dumps({
        "n_common_complete_rows": receipt["n_common_complete_rows"],
        "common_inventory_by_sign": receipt["common_inventory_by_sign"],
        "mechanism_passer_count": receipt["mechanism_passer_count"],
        "mechanism_passers": receipt["mechanism_passers"],
        "later_bounded_family_discussion_authorized": receipt["later_bounded_family_discussion_authorized"],
        "2026_rows_loaded": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
