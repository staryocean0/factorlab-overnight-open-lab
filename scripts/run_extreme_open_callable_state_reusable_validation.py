#!/usr/bin/env python3
"""Compact reusable BLACKBOX validation for the exact frozen P4 six-state interface.

Internally evaluates governed 2021-2025 rows but persists/prints only one overall
PASS / FAIL / INSUFFICIENT decision plus non-outcome provenance. No state-level
metrics, counts, years, failure attribution or rescue clues are written.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_extreme_open_callable_state_reusable_validation_v1"
BB_START = pd.Timestamp("2021-01-01")
BB_END = pd.Timestamp("2025-12-31")
YEARS = tuple(range(2021, 2026))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def classify_event(value) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "MISSING"
    if not math.isfinite(v):
        return "MISSING"
    if v >= 0.003:
        return "EXTREME_UP"
    if v <= -0.003:
        return "EXTREME_DOWN"
    return "NONE"


def counts(frame: pd.DataFrame, target: str) -> tuple[int, int]:
    return int(len(frame)), int(frame["event_class"].eq(target).sum())


def probability(x: int, n: int) -> float | None:
    return None if n <= 0 else x / n


def state_rows(frame: pd.DataFrame, p4, state_id: str) -> dict[str, pd.DataFrame]:
    spec = p4.P3[state_id]
    left_id, right_id = spec["requires"]
    _, left_coord, left_bucket = p4.P1[left_id]
    _, right_coord, right_bucket = p4.P1[right_id]
    eligible = frame.loc[
        frame[left_coord].notna() & frame[right_coord].notna() & frame["event_class"].ne("MISSING")
    ].copy()
    left = eligible[left_coord].map(lambda v: p4.bucket_for(left_coord, v) == left_bucket)
    right = eligible[right_coord].map(lambda v: p4.bucket_for(right_coord, v) == right_bucket)
    inter = left & right
    return {
        "PARENT": eligible,
        "INTERSECTION": eligible.loc[inter],
        "LEFT_FULL": eligible.loc[left],
        "RIGHT_FULL": eligible.loc[right],
        "LEFT_EXCLUSIVE": eligible.loc[left & ~right],
        "RIGHT_EXCLUSIVE": eligible.loc[right & ~left],
        "REST": eligible.loc[~inter],
    }


def compare(stats, a_n: int, a_x: int, b_n: int, b_x: int) -> dict:
    pa, pb = probability(a_x, a_n), probability(b_x, b_n)
    ci = stats.newcombe_hybrid_score_diff(a_x, a_n, b_x, b_n)
    return {
        "difference": None if pa is None or pb is None else pa - pb,
        "ci_lower": ci[0],
        "p": stats.fisher_two_sided(a_x, a_n, b_x, b_n),
    }


def build_internal_state_result(frame: pd.DataFrame, p4, stats, state_id: str, protocol: dict) -> dict:
    target = p4.P3[state_id]["target"]
    c = state_rows(frame, p4, state_id)
    pn, px = counts(c["PARENT"], target)
    inn, inx = counts(c["INTERSECTION"], target)
    ln, lx = counts(c["LEFT_FULL"], target)
    rn, rx = counts(c["RIGHT_FULL"], target)
    len_, lex = counts(c["LEFT_EXCLUSIVE"], target)
    ren, rex = counts(c["RIGHT_EXCLUSIVE"], target)
    restn, restx = counts(c["REST"], target)

    pint, pparent = probability(inx, inn), probability(px, pn)
    pleft, pright = probability(lx, ln), probability(rx, rn)
    parent_lift = None if pint is None or pparent is None else 100.0 * (pint - pparent)
    parent_rr = None if pint is None or pparent is None or pparent <= 0 else pint / pparent
    stronger = None if pleft is None or pright is None else max(pleft, pright)
    inc_lift = None if pint is None or stronger is None else 100.0 * (pint - stronger)
    inc_rr = None if pint is None or stronger is None or stronger <= 0 else pint / stronger

    primary = compare(stats, inn, inx, restn, restx)
    left_inc = compare(stats, inn, inx, len_, lex)
    right_inc = compare(stats, inn, inx, ren, rex)

    suff = protocol["sample_sufficiency_gates_per_state"]
    sufficient = (
        inn >= int(suff["intersection_pooled_minimum_n"])
        and len_ >= int(suff["left_exclusive_pooled_minimum_n"])
        and ren >= int(suff["right_exclusive_pooled_minimum_n"])
    )
    annual_primary_positive = True
    annual_left_positive = True
    annual_right_positive = True
    for year in YEARS:
        cy = state_rows(frame.loc[frame["year"].eq(year)], p4, state_id)
        iyn, iyx = counts(cy["INTERSECTION"], target)
        lyn, lyx = counts(cy["LEFT_EXCLUSIVE"], target)
        ryn, ryx = counts(cy["RIGHT_EXCLUSIVE"], target)
        restyn, restyx = counts(cy["REST"], target)
        sufficient = sufficient and (
            iyn >= int(suff["intersection_minimum_n_each_calendar_year"])
            and lyn >= int(suff["left_exclusive_minimum_n_each_calendar_year"])
            and ryn >= int(suff["right_exclusive_minimum_n_each_calendar_year"])
        )
        pdiff = compare(stats, iyn, iyx, restyn, restyx)["difference"]
        ldiff = compare(stats, iyn, iyx, lyn, lyx)["difference"]
        rdiff = compare(stats, iyn, iyx, ryn, ryx)["difference"]
        annual_primary_positive = annual_primary_positive and pdiff is not None and pdiff > 0
        annual_left_positive = annual_left_positive and ldiff is not None and ldiff > 0
        annual_right_positive = annual_right_positive and rdiff is not None and rdiff > 0

    g = protocol["scientific_gates_per_state"]
    pre_bh = {
        "target_probability_gt_parent": pint is not None and pparent is not None and pint > pparent,
        "parent_materiality": (parent_lift is not None and parent_lift >= float(g["minimum_parent_probability_lift_pp"])) or (parent_rr is not None and parent_rr >= float(g["minimum_parent_risk_ratio"])),
        "primary_newcombe": primary["ci_lower"] is not None and primary["ci_lower"] > 0,
        "higher_than_both_full_constituents": pint is not None and pleft is not None and pright is not None and pint > pleft and pint > pright,
        "incremental_materiality": (inc_lift is not None and inc_lift >= float(g["minimum_incremental_probability_lift_pp_over_stronger_constituent"])) or (inc_rr is not None and inc_rr >= float(g["minimum_incremental_risk_ratio_over_stronger_constituent"])),
        "left_increment_newcombe": left_inc["ci_lower"] is not None and left_inc["ci_lower"] > 0,
        "right_increment_newcombe": right_inc["ci_lower"] is not None and right_inc["ci_lower"] > 0,
        "annual_primary_positive": annual_primary_positive,
        "annual_left_positive": annual_left_positive,
        "annual_right_positive": annual_right_positive,
    }
    return {
        "state_id": state_id,
        "target": target,
        "sufficient": bool(sufficient),
        "pre_bh": pre_bh,
        "primary_p": primary["p"],
        "left_p": left_inc["p"],
        "right_p": right_inc["p"],
    }


def evaluate_package(frame: pd.DataFrame, p4, stats, protocol: dict) -> str:
    results = [build_internal_state_result(frame, p4, stats, sid, protocol) for sid in protocol["exact_state_set"]]
    qmax = float(protocol["scientific_gates_per_state"]["primary_two_sided_Fisher_BH_q_max"])
    for target in ("EXTREME_UP", "EXTREME_DOWN"):
        fam = [r for r in results if r["target"] == target]
        primary_q = stats.bh_adjust([r["primary_p"] for r in fam])
        inc_p, refs = [], []
        for r in fam:
            inc_p.extend([r["left_p"], r["right_p"]])
            refs.extend([(r, "left"), (r, "right")])
        inc_q = stats.bh_adjust(inc_p)
        for r, q in zip(fam, primary_q):
            r["primary_bh"] = q is not None and q <= qmax
        for (r, side), q in zip(refs, inc_q):
            r[f"{side}_bh"] = q is not None and q <= qmax

    any_fail = False
    any_insufficient = False
    for r in results:
        if not r["sufficient"]:
            any_insufficient = True
            continue
        scientific_pass = all(r["pre_bh"].values()) and r.get("primary_bh", False) and r.get("left_bh", False) and r.get("right_bh", False)
        if not scientific_pass:
            any_fail = True
    if any_fail:
        return "FAIL"
    if any_insufficient:
        return "INSUFFICIENT"
    return "PASS"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--hkma", type=Path, required=True)
    ap.add_argument("--holiday-a50", type=Path, required=True)
    ap.add_argument("--ordinary-a50", type=Path, required=True)
    ap.add_argument("--high-open-source-manifest", type=Path, required=True)
    ap.add_argument("--external-source-manifest", type=Path, required=True)
    ap.add_argument("--reconstruction-contract", type=Path, required=True)
    ap.add_argument("--p4-protocol", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("wrong P5 identity")
    if protocol.get("public_output_enum") != ["PASS", "FAIL", "INSUFFICIENT"]:
        raise RuntimeError("P5 public output contract drift")
    if protocol.get("state_count") != 6 or len(protocol.get("exact_state_set", [])) != 6:
        raise RuntimeError("P5 exact state-set drift")
    if protocol.get("blackbox_window") != "2021-01-01..2025-12-31":
        raise RuntimeError("P5 BLACKBOX window drift")

    p4 = load_module("p4_callable_state", ROOT / "scripts/extreme_open_callable_state.py")
    stats = load_module("p5_frozen_stats", ROOT / "scripts/extreme_open_univariate_stats.py")
    b4 = load_module("p5_b4_source", ROOT / "scripts/run_driver_coherence_open_gap_blackbox.py")

    p4_protocol = json.loads(args.p4_protocol.read_text(encoding="utf-8"))
    if p4_protocol.get("research_identity") != "overnight_extreme_open_callable_state_packaging_v1":
        raise RuntimeError("wrong P4 parent protocol")
    if tuple(protocol["exact_state_set"]) != tuple(p4.P3_ORDER):
        raise RuntimeError("P5 state order differs from frozen P4 implementation")

    ext_manifest = json.loads(args.external_source_manifest.read_text(encoding="utf-8"))
    required_assertions = ["same_contract_all_events", "no_future_volume_or_oi_selection", "no_mid_window_roll", "no_forward_fill_or_interpolation", "blackbox_not_used_for_fit_or_rule_selection"]
    if not all(ext_manifest.get("assertions", {}).get(k) is True for k in required_assertions):
        raise RuntimeError("external source assertions fail")

    panel = pd.read_parquet(args.panel).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    panel = panel.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    needed = {"trading_day", "gap", "rvol20", "us_nasdaq", "us_vix_chg", "holiday_reopen"}
    if needed.difference(panel.columns):
        raise RuntimeError("P5 reconstructed base panel missing frozen inputs")
    panel["previous_china_day"] = panel["trading_day"].shift(1)
    df = b4.add_hkma(panel, args.hkma)
    df, _ordinary_coverage, clock_ok = b4.attach_a50(df, args.holiday_a50, args.ordinary_a50)
    if not clock_ok:
        raise RuntimeError("A50 causal clock integrity failed")
    df = b4.build_coordinates(df)
    df["B1_global_risk"] = df["global_risk_z"]
    df["B2_china_offshore"] = df["china_offshore_z"]
    df["B4_driver_coherence"] = df["driver_coherence"]
    df["causal_prior_volatility_parent"] = df["log_rvol20"]
    df["event_class"] = [classify_event(v) for v in pd.to_numeric(df["gap"], errors="coerce")]
    bb = df.loc[df["trading_day"].between(BB_START, BB_END)].copy()
    bb["year"] = bb["trading_day"].dt.year.astype(int)

    decision = evaluate_package(bb, p4, stats, protocol)
    protocol_sha = sha256(args.protocol)
    p4_protocol_sha = sha256(args.p4_protocol)
    p4_impl_sha = sha256(ROOT / "scripts/extreme_open_callable_state.py")
    high_sha = sha256(args.high_open_source_manifest)
    ext_sha = sha256(args.external_source_manifest)
    recon_sha = sha256(args.reconstruction_contract)
    query_id = hashlib.sha256("|".join([IDENTITY, protocol_sha, p4_protocol_sha, p4_impl_sha, high_sha, ext_sha, recon_sha]).encode("utf-8")).hexdigest()[:20]
    receipt = {
        "schema_id": "overnight_extreme_open_callable_state_reusable_validation_receipt@1.0",
        "query_id": query_id,
        "research_identity": IDENTITY,
        "parent_packaging_identity": "overnight_extreme_open_callable_state_packaging_v1",
        "comparator": "exact_P4_six_state_DEV_contract_replayed_on_reusable_2021_2025_window",
        "decision": decision,
        "public_detail_release": False,
        "state_level_decisions_persisted": False,
        "internal_metrics_persisted": False,
        "counts_persisted": False,
        "yearly_results_persisted": False,
        "failure_attribution_persisted": False,
        "probability_breakdowns_persisted": False,
        "protocol_sha256": protocol_sha,
        "p4_protocol_sha256": p4_protocol_sha,
        "p4_reference_implementation_sha256": p4_impl_sha,
        "high_open_source_manifest_sha256": high_sha,
        "external_source_manifest_sha256": ext_sha,
        "reconstruction_contract_sha256": recon_sha,
        "exact_state_count": 6,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed_as_one_time_data": False,
        "reuse_is_independent_oos": False,
        "production_authority": False
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
