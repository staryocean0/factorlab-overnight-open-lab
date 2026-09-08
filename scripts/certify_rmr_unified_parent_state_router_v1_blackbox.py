#!/usr/bin/env python3
"""Low-bandwidth reusable BLACKBOX certifier for unified parent-state router v1."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_rmr_unified_parent_state_router_v1 as router

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_unified_parent_state_router_v1_protocol.json"
DEFAULT_HIST = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_BLACKBOX = ROOT / "archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_unified_parent_state_router_v1_parameter_freeze.json"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_unified_parent_state_router_v1_blackbox_receipt.json"
HIST_SHA = "11f4a5e78381371680fbcf6e01891216f645a8de869646ced6a623970727bcce"
BLACKBOX_SHA = "307e48021ef4576c2b364a1309a8b0474d6ab783afee16be41edb975abaa6dcd"
BLACKBOX_START = "2026-01-05"
BLACKBOX_END = "2026-08-21"
SYMBOL = "000852.SH"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def validate_freeze(path: Path) -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    freeze = load_json(path)
    if freeze["research_identity"] != "rmr_unified_parent_normal_state_router_v1":
        raise RuntimeError("router BLACKBOX identity drifted")
    if freeze["blackbox_used_in_fit"] is not False:
        raise RuntimeError("router frozen bundle used BLACKBOX")
    if freeze["public_blackbox_output_only"] != ["PASS", "FAIL", "INSUFFICIENT"]:
        raise RuntimeError("router BLACKBOX output contract drifted")
    expected = freeze["parameter_bundle_sha256"]
    check = dict(freeze)
    check.pop("parameter_bundle_sha256")
    if json_digest(check) != expected:
        raise RuntimeError("router parameter bundle digest mismatch")
    if protocol["BLACKBOX"]["query_number_if_reached"] != 4:
        raise RuntimeError("router query number drifted")
    return protocol, freeze


def read_frame(path: Path, expected_sha: str, start: str, end: str) -> pd.DataFrame:
    if sha256(path) != expected_sha:
        raise RuntimeError("router source identity mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", ">=", start), ("trading_day", "<=", end)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty:
        raise RuntimeError("router source empty")
    values = frame["close"].to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        raise RuntimeError("router invalid close values")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def combine(hist: pd.DataFrame, blackbox: pd.DataFrame) -> pd.DataFrame:
    if str(hist["trading_day"].min()) != "2015-01-05" or str(hist["trading_day"].max()) != "2025-12-31":
        raise RuntimeError("router historical context boundary drifted")
    if str(blackbox["trading_day"].min()) != BLACKBOX_START or str(blackbox["trading_day"].max()) != BLACKBOX_END:
        raise RuntimeError("router BLACKBOX window incomplete")
    out = pd.concat([hist, blackbox], ignore_index=True).sort_values(["trading_day", "timestamp"], kind="mergesort")
    if out.duplicated(["symbol", "trading_day", "timestamp"]).any():
        raise RuntimeError("router combined source duplicate minute")
    return out.reset_index(drop=True)


def frozen_predict(snapshot: dict, frame: pd.DataFrame) -> np.ndarray:
    features = snapshot["features"]
    x = frame[features].to_numpy(float)
    mean = np.asarray(snapshot["scaler"]["mean"], dtype=float)
    scale = np.asarray(snapshot["scaler"]["scale"], dtype=float)
    coef = np.asarray(snapshot["logistic"]["coef"], dtype=float)
    intercept = float(snapshot["logistic"]["intercept"])
    z = (x - mean) / scale
    logits = z @ coef + intercept
    logits = np.clip(logits, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-logits))


def add_frozen_state(frame: pd.DataFrame, parent_scaler: dict, lane: str) -> pd.DataFrame:
    out = frame.copy()
    x = out[router.PARENT_FEATURES].to_numpy(float)
    mean = np.asarray(parent_scaler["mean"], dtype=float)
    scale = np.asarray(parent_scaler["scale"], dtype=float)
    z = (x - mean) / scale
    axis = (z[:, 0] - z[:, 1] + z[:, 2]) / 3.0
    out["state_consistency"] = axis if lane == "R1" else -axis
    return out


def build_blackbox_pool(all_events: dict[str, pd.DataFrame], protocol: dict, freeze: dict) -> pd.DataFrame:
    parts = []
    for cell_id in router.CELL_ORDER:
        cfg = protocol["cells"][cell_id]
        data = router.resolved_frame(all_events[cell_id], cfg)
        if data.empty:
            continue
        data = add_frozen_state(data, freeze["parent_scaler"], cfg["lane"])
        p = frozen_predict(freeze["cell_baselines"][cell_id], data)
        p = np.clip(p, 1e-6, 1.0 - 1e-6)
        data["base_logit"] = np.log(p / (1.0 - p))
        keep = data.loc[data["day"].between(BLACKBOX_START, BLACKBOX_END), [
            "day", "cell", "lane", "lane_R2", "pair_B", "y", "base_logit", "state_consistency"
        ]].copy()
        parts.append(keep)
    if not parts:
        return pd.DataFrame(columns=["day", "cell", "lane", "lane_R2", "pair_B", "y", "base_logit", "state_consistency"])
    return pd.concat(parts, ignore_index=True).reset_index(drop=True)


def metrics(snapshot: dict, frame: pd.DataFrame) -> tuple[float, float]:
    p = frozen_predict(snapshot, frame)
    y = frame["y"].to_numpy(int)
    return float(brier_score_loss(y, p)), float(log_loss(y, p, labels=[0, 1]))


def internal_gate(pool: pd.DataFrame, protocol: dict, freeze: dict) -> tuple[bool, bool]:
    minimum = {k: int(v) for k, v in protocol["BLACKBOX"]["minimum_resolved"].items()}
    sample_ok = all(int((pool["cell"] == cell).sum()) >= minimum[cell] for cell in router.CELL_ORDER)
    if not sample_ok:
        return False, False

    base_brier, base_logloss = metrics(freeze["pooled_baseline"], pool)
    cand_brier, cand_logloss = metrics(freeze["pooled_candidate"], pool)
    metric_ok = cand_brier < base_brier and cand_logloss < base_logloss

    for lane in ("R1", "R2"):
        subset = pool.loc[pool["lane"].eq(lane)].copy()
        b_brier, b_log = metrics(freeze["pooled_baseline"], subset)
        c_brier, c_log = metrics(freeze["pooled_candidate"], subset)
        metric_ok = metric_ok and c_brier < b_brier and c_log < b_log

    for cell in router.CELL_ORDER:
        subset = pool.loc[pool["cell"].eq(cell)].copy()
        b_brier, _ = metrics(freeze["pooled_baseline"], subset)
        c_brier, _ = metrics(freeze["pooled_candidate"], subset)
        metric_ok = metric_ok and c_brier < b_brier

    return True, bool(metric_ok)


def decide(sample_ok: bool, metric_ok: bool) -> str:
    if not sample_ok:
        return "INSUFFICIENT"
    return "PASS" if metric_ok else "FAIL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--historical", type=Path, default=DEFAULT_HIST)
    ap.add_argument("--blackbox", type=Path, default=DEFAULT_BLACKBOX)
    ap.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    ap.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = ap.parse_args()

    protocol, freeze = validate_freeze(args.freeze.resolve())
    hist = read_frame(args.historical.resolve(), HIST_SHA, "2015-01-05", "2025-12-31")
    blackbox = read_frame(args.blackbox.resolve(), BLACKBOX_SHA, BLACKBOX_START, BLACKBOX_END)
    frame = combine(hist, blackbox)
    all_events = router.build_events(frame, protocol)
    pool = build_blackbox_pool(all_events, protocol, freeze)
    sample_ok, metric_ok = internal_gate(pool, protocol, freeze)
    decision = decide(sample_ok, metric_ok)

    candidate_fp = freeze["parameter_bundle_sha256"]
    protocol_fp = sha256(PROTOCOL)
    query_id = hashlib.sha256(f"ROUTER|{candidate_fp}|{protocol_fp}|{BLACKBOX_SHA}".encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "factorlab_reusable_blackbox_certification_receipt@1.0",
        "research_identity": "rmr_unified_parent_normal_state_router_v1",
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
