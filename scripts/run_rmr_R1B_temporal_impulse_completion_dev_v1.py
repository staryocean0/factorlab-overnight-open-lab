#!/usr/bin/env python3
"""DEV-only test of the preregistered R1_B temporal impulse completion identity.

Reads 2015-2020 only. No VALIDATION, BLACKBOX, probability filtering, refit,
parameter search, horizon selection, or portfolio optimization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_stage1_common_probe as common

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R1B_temporal_impulse_completion_dev_protocol_v1.json"
DEFAULT_SOURCE = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_OUTPUT = ROOT / "docs/research/local_rmr_R1B_temporal_impulse_completion_DEV_v1.json"
EXPECTED_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
SYMBOL = "000852.SH"
DEV_START = "2015-01-05"
DEV_END = "2020-12-31"
S2 = 0.006891654009228464
S3 = 0.013783308018456928
VOL_REF = 0.013783308018456928
HORIZON = 1200
COST = 0.0010
YEARS = list(range(2015, 2021))


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


def validate_protocol() -> dict:
    p = load_json(PROTOCOL)
    if p["research_identity"] != "rmr_R1B_temporal_impulse_completion_v1":
        raise RuntimeError("temporal identity drifted")
    if p["candidate_id"] != "R1B_S2_PARENT_IMPULSE_CONFIRM_EXIT":
        raise RuntimeError("temporal candidate drifted")
    src = p["source_identity"]
    if src["historical_source_sha256"] != EXPECTED_SHA or src["max_read_day"] != DEV_END:
        raise RuntimeError("DEV source contract drifted")
    dep = p["certified_R1_dependency"]
    if dep["pairing"] != "PAIR_B" or dep["lower_scale"] != "S2" or dep["parent_scale"] != "S3":
        raise RuntimeError("R1_B scale identity drifted")
    if float(dep["S2_threshold"]) != S2 or float(dep["S3_threshold"]) != S3:
        raise RuntimeError("frozen thresholds drifted")
    ex = p["execution"]
    if int(ex["structural_resolution_horizon_bars"]) != HORIZON or float(ex["round_trip_cost_bps"]) != 10.0:
        raise RuntimeError("execution constants drifted")
    if ex["probability_threshold"] is not None:
        raise RuntimeError("probability filtering is forbidden")
    return p


def read_source(path: Path) -> pd.DataFrame:
    actual = sha256(path)
    if actual != EXPECTED_SHA:
        raise RuntimeError(f"historical source SHA mismatch: {actual}")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", "<=", DEV_END)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.loc[frame["symbol"].eq(SYMBOL)].copy()
    if frame.empty:
        raise RuntimeError("empty DEV source")
    if str(frame["trading_day"].min()) != DEV_START or str(frame["trading_day"].max()) != DEV_END:
        raise RuntimeError("DEV source boundary drifted")
    if (frame["trading_day"] > DEV_END).any():
        raise RuntimeError("DEV runner crossed role boundary")
    values = frame["close"].to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise RuntimeError("invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def r1b_events_with_context(prices: np.ndarray, days: np.ndarray, s2_waves, s3_waves) -> pd.DataFrame:
    parent_confirms = [w.confirm_idx for w in s3_waves]
    rows = []
    next_allowed = -1
    for lower_pos, lower in enumerate(s2_waves):
        if lower.confirm_idx <= next_allowed:
            continue
        k = bisect_right(parent_confirms, lower.confirm_idx)
        if k < 2:
            continue
        w1, w2 = s3_waves[k - 2], s3_waves[k - 1]
        pf = common.parent_features(w1, w2, prices)
        if not pf or not np.isfinite(list(pf.values())).all():
            continue
        parent_sign = 1 if pf["signed_drift"] > 0 else -1 if pf["signed_drift"] < 0 else 0
        if parent_sign == 0 or lower.direction == parent_sign:
            continue
        recovery = float(lower.start_price)
        failure = float(common.structural_boundary(w1, w2, parent_sign))
        current = float(prices[lower.confirm_idx])
        if parent_sign > 0 and not (failure < current < recovery):
            continue
        if parent_sign < 0 and not (recovery < current < failure):
            continue
        outcome, resolved = common.first_passage(prices, lower.confirm_idx, recovery, failure, parent_sign, HORIZON)
        if outcome == "tie":
            continue
        rows.append(
            {
                "day": str(days[lower.confirm_idx]),
                "confirm_idx": int(lower.confirm_idx),
                "lower_wave_pos": int(lower_pos),
                "severity": float(abs(lower.move) / VOL_REF),
                "parent_sign": int(parent_sign),
                "recovery": recovery,
                "failure": failure,
                "baseline_outcome": outcome,
                "baseline_resolve_idx": int(resolved),
                **pf,
            }
        )
        next_allowed = resolved
    return pd.DataFrame(rows)


def assert_population_matches_certified(prices, days, s2_waves, s3_waves, events: pd.DataFrame) -> None:
    certified = common.r1_events(prices, days, s2_waves, s3_waves, VOL_REF).reset_index(drop=True)
    if len(certified) != len(events):
        raise RuntimeError(f"R1_B event count drifted: {len(events)} != {len(certified)}")
    if len(events) == 0:
        return
    if certified["day"].astype(str).tolist() != events["day"].astype(str).tolist():
        raise RuntimeError("R1_B event day sequence drifted")
    if certified["outcome"].astype(str).tolist() != events["baseline_outcome"].astype(str).tolist():
        raise RuntimeError("R1_B event outcome sequence drifted")
    if certified["resolve_idx"].astype(int).tolist() != events["baseline_resolve_idx"].astype(int).tolist():
        raise RuntimeError("R1_B resolution sequence drifted")


def entry_valid(entry: float, recovery: float, failure: float, direction: int) -> bool:
    return (failure < entry < recovery) if direction > 0 else (recovery < entry < failure)


def crossed_failure(price: float, failure: float, direction: int) -> bool:
    return price <= failure if direction > 0 else price >= failure


def first_parent_aligned_s2_confirmation(s2_waves, lower_wave_pos: int, confirm_idx: int, direction: int):
    for wave in s2_waves[lower_wave_pos + 1 :]:
        if wave.confirm_idx <= confirm_idx:
            continue
        if wave.direction == direction:
            return wave
    return None


def candidate_exit(prices: np.ndarray, event: dict, s2_waves) -> tuple[str, int]:
    confirm_idx = int(event["confirm_idx"])
    direction = int(event["parent_sign"])
    failure = float(event["failure"])
    end = min(len(prices) - 1, confirm_idx + HORIZON)
    impulse = first_parent_aligned_s2_confirmation(
        s2_waves, int(event["lower_wave_pos"]), confirm_idx, direction
    )
    impulse_confirm = int(impulse.confirm_idx) if impulse is not None else None
    scan_end = min(end, impulse_confirm) if impulse_confirm is not None else end
    for idx in range(confirm_idx + 1, scan_end + 1):
        if crossed_failure(float(prices[idx]), failure, direction):
            return "parent_failure", idx
    if impulse_confirm is not None and impulse_confirm <= end:
        return "parent_aligned_S2_impulse_confirmed", impulse_confirm
    return "censored", end


def add_execution_rows(events: pd.DataFrame, prices: np.ndarray, s2_waves) -> pd.DataFrame:
    rows = []
    for record in events.to_dict("records"):
        confirm_idx = int(record["confirm_idx"])
        entry_idx = confirm_idx + 1
        row = dict(record)
        row["entry_invalid"] = True
        if entry_idx >= len(prices):
            rows.append(row)
            continue
        entry = float(prices[entry_idx])
        direction = int(record["parent_sign"])
        recovery = float(record["recovery"])
        failure = float(record["failure"])
        if not entry_valid(entry, recovery, failure, direction):
            rows.append(row)
            continue
        row["entry_invalid"] = False
        row["entry_idx"] = entry_idx
        row["entry_price"] = entry

        c_class, c_idx = candidate_exit(prices, record, s2_waves)
        c_price = float(prices[c_idx])
        c_gross = float(direction * (c_price / entry - 1.0))
        row.update(
            {
                "candidate_exit_class": c_class,
                "candidate_exit_idx": int(c_idx),
                "candidate_exit_price": c_price,
                "candidate_gross": c_gross,
                "candidate_net": c_gross - COST,
                "candidate_win": bool(c_gross - COST > 0),
                "candidate_holding_bars": int(max(0, c_idx - entry_idx)),
            }
        )

        b_idx = int(record["baseline_resolve_idx"])
        b_price = float(prices[b_idx])
        b_gross = float(direction * (b_price / entry - 1.0))
        row.update(
            {
                "baseline_exit_class": str(record["baseline_outcome"]),
                "baseline_exit_idx": b_idx,
                "baseline_exit_price": b_price,
                "baseline_gross": b_gross,
                "baseline_net": b_gross - COST,
                "baseline_win": bool(b_gross - COST > 0),
                "baseline_holding_bars": int(max(0, b_idx - entry_idx)),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def safe_mean(series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if len(values) else None


def safe_median(series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.median()) if len(values) else None


def safe_p90(series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.quantile(0.90)) if len(values) else None


def summarize(frame: pd.DataFrame) -> dict:
    trade = frame.loc[~frame["entry_invalid"]].copy()
    result = {
        "events": int(len(frame)),
        "tradeable": int(len(trade)),
        "entry_invalid": int(frame["entry_invalid"].sum()),
        "tradeable_fraction": float(len(trade) / len(frame)) if len(frame) else None,
    }
    if trade.empty:
        result["DEV_gate"] = {"passed": False, "reason": "no_tradeable_events"}
        return result

    exit_counts = trade["candidate_exit_class"].value_counts(dropna=False).to_dict()
    exit_rates = {str(k): float(v / len(trade)) for k, v in exit_counts.items()}
    result.update(
        {
            "candidate_mean_gross": safe_mean(trade["candidate_gross"]),
            "candidate_mean_net": safe_mean(trade["candidate_net"]),
            "candidate_median_net": safe_median(trade["candidate_net"]),
            "candidate_win_rate": safe_mean(trade["candidate_win"].astype(float)),
            "candidate_exit_class_counts": {str(k): int(v) for k, v in exit_counts.items()},
            "candidate_exit_class_rates": exit_rates,
            "candidate_mean_holding_bars": safe_mean(trade["candidate_holding_bars"]),
            "candidate_median_holding_bars": safe_median(trade["candidate_holding_bars"]),
            "candidate_p90_holding_bars": safe_p90(trade["candidate_holding_bars"]),
            "baseline_mean_gross": safe_mean(trade["baseline_gross"]),
            "baseline_mean_net": safe_mean(trade["baseline_net"]),
            "baseline_median_net": safe_median(trade["baseline_net"]),
            "baseline_win_rate": safe_mean(trade["baseline_win"].astype(float)),
            "candidate_minus_baseline_mean_net": safe_mean(trade["candidate_net"] - trade["baseline_net"]),
        }
    )

    annual = {}
    positive_candidate_years = 0
    for year in YEARS:
        sub = trade.loc[trade["day"].str.startswith(str(year))]
        c = safe_mean(sub["candidate_net"])
        b = safe_mean(sub["baseline_net"])
        delta = float(c - b) if c is not None and b is not None else None
        if c is not None and c > 0:
            positive_candidate_years += 1
        annual[str(year)] = {
            "tradeable": int(len(sub)),
            "candidate_mean_net": c,
            "baseline_mean_net": b,
            "candidate_minus_baseline_mean_net": delta,
        }
    result["annual"] = annual
    result["positive_candidate_mean_net_years"] = int(positive_candidate_years)

    gates = {
        "pooled_candidate_mean_net_gt_zero": bool(result["candidate_mean_net"] is not None and result["candidate_mean_net"] > 0),
        "pooled_candidate_mean_net_gt_pooled_baseline_mean_net": bool(
            result["candidate_mean_net"] is not None
            and result["baseline_mean_net"] is not None
            and result["candidate_mean_net"] > result["baseline_mean_net"]
        ),
        "pooled_candidate_median_net_gt_zero": bool(result["candidate_median_net"] is not None and result["candidate_median_net"] > 0),
        "positive_candidate_mean_net_years_ge_4_of_6": positive_candidate_years >= 4,
    }
    gates["passed"] = bool(all(gates.values()))
    result["DEV_gate"] = gates
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    protocol = validate_protocol()
    frame = read_source(args.source.resolve())
    prices = frame["close"].to_numpy(float)
    days = frame["trading_day"].to_numpy(str)
    s2_waves = common.detect_waves(prices, S2)
    s3_waves = common.detect_waves(prices, S3)
    events = r1b_events_with_context(prices, days, s2_waves, s3_waves)
    assert_population_matches_certified(prices, days, s2_waves, s3_waves, events)
    executed = add_execution_rows(events, prices, s2_waves)
    summary = summarize(executed)

    report = {
        "schema_id": "factorlab_rmr_R1B_temporal_impulse_completion_DEV_receipt@1.0",
        "session_date": "2026-09-08",
        "research_identity": "rmr_R1B_temporal_impulse_completion_v1",
        "candidate_id": "R1B_S2_PARENT_IMPULSE_CONFIRM_EXIT",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "historical_source_sha256": EXPECTED_SHA,
        "max_read_day": DEV_END,
        "role": "DEV_ONLY",
        "certified_R1_event_population_match": True,
        "S2_threshold": S2,
        "S3_threshold": S3,
        "round_trip_cost_bps": 10.0,
        "structural_resolution_horizon_bars": HORIZON,
        "probability_filter_used": False,
        "parameter_or_horizon_search_performed": False,
        "VALIDATION_opened": False,
        "BLACKBOX_opened": False,
        "BLACKBOX_query_created": False,
        "production_authority": False,
        "summary": summary,
    }
    dump_json(args.output.resolve(), report)
    if summary.get("DEV_gate", {}).get("passed"):
        print("R1B_TEMPORAL_IMPULSE_DEV_READY_FOR_VALIDATION_FREEZE")
        return 0
    print("R1B_TEMPORAL_IMPULSE_DEV_CLOSE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
