#!/usr/bin/env python3
"""Reusable low-bandwidth BLACKBOX certifier for R1 economic translation v2."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common
import run_rmr_R1_economic_translation_v2 as econ2
import evaluate_rmr_R1_parent_integrity_v2_holdout as frozen_eval

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1_economic_translation_v2_protocol.json"
DEFAULT_HIST = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_BLACKBOX = ROOT / "archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R1_economic_translation_v2_parameter_freeze.json"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R1_economic_translation_v2_blackbox_receipt.json"
HIST_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
BLACKBOX_SHA = "307e48021ef4576c2b364a1309a8b0474d6ab783afee16be41edb975abaa6dcd"
BLACKBOX_START = "2026-01-05"
BLACKBOX_END = "2026-08-21"
SYMBOL = "000852.SH"
PAIRINGS = (("PAIR_A", "S1", "S2"), ("PAIR_B", "S2", "S3"))
ROUND_TRIP_COST = 0.0010


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_freeze(path: Path) -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    freeze = load_json(path)
    if freeze["research_identity"] != "rmr_R1_parent_integrity_economic_translation_v2":
        raise RuntimeError("economic v2 blackbox identity drifted")
    if freeze["strategy_candidate_id"] != "R1_STRUCTURAL_EXPECTANCY_POSITIVE_NEXT_BAR_10BP":
        raise RuntimeError("economic v2 candidate drifted")
    if freeze["blackbox_used_in_fit"] is not False:
        raise RuntimeError("economic v2 fit used blackbox")
    if float(freeze["round_trip_cost_bps"]) != 10.0:
        raise RuntimeError("economic v2 cost drifted")
    if float(freeze["expectancy_threshold"]) != 0.0:
        raise RuntimeError("economic v2 expectancy threshold drifted")
    expected = freeze["parameter_bundle_sha256"]
    check = dict(freeze)
    check.pop("parameter_bundle_sha256")
    if json_digest(check) != expected:
        raise RuntimeError("economic v2 final bundle digest mismatch")
    return protocol, freeze


def read_frame(path: Path, expected_sha: str, start: str, end: str) -> pd.DataFrame:
    if sha256(path) != expected_sha:
        raise RuntimeError("economic v2 source identity mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", ">=", start), ("trading_day", "<=", end)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty:
        raise RuntimeError("economic v2 source empty")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("economic v2 source invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def combine(hist: pd.DataFrame, blackbox: pd.DataFrame) -> pd.DataFrame:
    if str(hist["trading_day"].max()) != "2025-12-31":
        raise RuntimeError("economic v2 historical context end drifted")
    if str(blackbox["trading_day"].min()) != BLACKBOX_START or str(blackbox["trading_day"].max()) != BLACKBOX_END:
        raise RuntimeError("economic v2 blackbox window incomplete")
    out = pd.concat([hist, blackbox], ignore_index=True).sort_values(["trading_day", "timestamp"], kind="mergesort")
    if out.duplicated(["symbol", "trading_day", "timestamp"]).any():
        raise RuntimeError("economic v2 combined source duplicate minute")
    return out.reset_index(drop=True)


def add_frozen_filters(events: pd.DataFrame, frozen_pair: dict) -> pd.DataFrame:
    out = frozen_eval.add_frozen_integrity(events, frozen_pair["parent_feature_scaler"])
    p_base = frozen_eval.frozen_predict(
        frozen_pair["severity_baseline_model"], out[["severity"]].to_numpy(float)
    )
    p_cand = frozen_eval.frozen_predict(
        frozen_pair["selected_candidate_model"], out[["severity", "parent_integrity"]].to_numpy(float)
    )
    structural_expected = (
        p_cand * out["recovery_gross"].to_numpy(float)
        + (1.0 - p_cand) * out["failure_gross"].to_numpy(float)
        - ROUND_TRIP_COST
    )
    out["selected_trade"] = (p_cand > p_base) & (structural_expected > 0.0)
    return out


def pairing_gate(events: pd.DataFrame, frozen_pair: dict, minimum: int) -> tuple[bool, bool]:
    bb = events.loc[events["day"].between(BLACKBOX_START, BLACKBOX_END)].copy()
    scored = add_frozen_filters(bb, frozen_pair)
    selected = scored.loc[scored["selected_trade"]]
    if len(selected) < minimum:
        return False, False
    mean_candidate = float(selected["net_return"].mean())
    mean_all = float(scored["net_return"].mean())
    return True, bool(mean_candidate > 0.0 and mean_candidate > mean_all)


def decide(results: dict[str, tuple[bool, bool]]) -> str:
    if not all(sample_ok for sample_ok, _ in results.values()):
        return "INSUFFICIENT"
    if all(metric_ok for _, metric_ok in results.values()):
        return "PASS"
    return "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical", type=Path, default=DEFAULT_HIST)
    ap.add_argument("--blackbox", type=Path, default=DEFAULT_BLACKBOX)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = ap.parse_args()

    protocol, freeze = validate_freeze(args.freeze.resolve())
    hist = read_frame(args.historical.resolve(), HIST_SHA, "2015-01-05", "2025-12-31")
    bb = read_frame(args.blackbox.resolve(), BLACKBOX_SHA, BLACKBOX_START, BLACKBOX_END)
    frame = combine(hist, bb)
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    thresholds = {k: float(v) for k, v in freeze["directional_change_thresholds"].items()}
    vol_ref = float(freeze["DEV_median_rvol20"])
    waves = {name: common.detect_waves(prices, thresholds[name]) for name in ("S1", "S2", "S3")}

    results = {}
    for pair_id, lower, parent in PAIRINGS:
        events = econ2.trade_events(prices, days, waves[lower], waves[parent], vol_ref)
        minimum = int(protocol["BLACKBOX"]["gate_each_pairing"]["minimum_filtered_trades"][pair_id])
        results[pair_id] = pairing_gate(events, freeze["pairings"][pair_id], minimum)
    decision = decide(results)

    candidate_fp = freeze["parameter_bundle_sha256"]
    protocol_fp = sha256(PROTOCOL)
    query_id = hashlib.sha256(f"R1ECONV2|{candidate_fp}|{protocol_fp}|{BLACKBOX_SHA}".encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "factorlab_reusable_blackbox_certification_receipt@1.0",
        "research_identity": "rmr_R1_parent_integrity_economic_translation_v2",
        "query_id": query_id,
        "candidate_fingerprint": candidate_fp,
        "protocol_fingerprint": protocol_fp,
        "blackbox_source_fingerprint": BLACKBOX_SHA,
        "blackbox_window": {"start": BLACKBOX_START, "end": BLACKBOX_END},
        "decision": decision,
        "details_released": False,
        "exact_metrics_released": False,
        "counts_released": False,
        "subperiods_released": False,
        "event_rows_released": False,
        "blackbox_remains_closed": True,
        "repeated_query_is_independent_OOS": False,
        "production_authority": False,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0 if decision == "PASS" else 2 if decision == "FAIL" else 3


if __name__ == "__main__":
    raise SystemExit(main())
