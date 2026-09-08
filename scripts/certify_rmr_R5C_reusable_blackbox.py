#!/usr/bin/env python3
"""Low-bandwidth reusable BLACKBOX certifier for dedicated R5-C."""
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
import run_rmr_stage1_common_probe as common
import run_rmr_R5C_reusable_validation as r5c

PROTOCOL = ROOT / "docs/governance/reversal_mean_reversion_R5C_reusable_validation_protocol_v1.json"
DEFAULT_HIST = ROOT / "data/high_open_dev_2015_2025/1m_official.parquet"
DEFAULT_BLACKBOX = ROOT / "archive/data/gap_fill_repeat_2026/csi1000_1m_20260105_to_20260821.parquet"
DEFAULT_FREEZE = ROOT / "docs/governance/local_rmr_R5C_reusable_parameter_freeze_v1.json"
DEFAULT_RECEIPT = ROOT / "docs/research/local_rmr_R5C_reusable_blackbox_receipt_v1.json"
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


def json_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_freeze(path: Path) -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    freeze = load_json(path)
    if freeze["research_identity"] != "rmr_event_density_state_reversal_v2":
        raise RuntimeError("R5-C BLACKBOX identity drifted")
    if freeze["blackbox_used_in_fit"] is not False:
        raise RuntimeError("R5-C final fit used BLACKBOX")
    if freeze["density_bars"] != 240 or freeze["normalization_history"] != 100:
        raise RuntimeError("R5-C property freeze drifted")
    if freeze["baseline_features"] != r5c.BASE_FEATURES or freeze["candidate_features"] != r5c.CAND_FEATURES:
        raise RuntimeError("R5-C feature freeze drifted")
    expected = freeze["parameter_bundle_sha256"]
    check = dict(freeze)
    check.pop("parameter_bundle_sha256")
    if json_digest(check) != expected:
        raise RuntimeError("R5-C final parameter bundle digest mismatch")
    return protocol, freeze


def read_frame(path: Path, expected_sha: str, start: str, end: str) -> pd.DataFrame:
    if sha256(path) != expected_sha:
        raise RuntimeError("R5-C BLACKBOX source identity mismatch")
    frame = pd.read_parquet(
        path,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[("symbol", "==", SYMBOL), ("trading_day", ">=", start), ("trading_day", "<=", end)],
    )
    frame["symbol"] = frame["symbol"].astype(str)
    frame["trading_day"] = frame["trading_day"].astype(str)
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame.empty:
        raise RuntimeError("R5-C source empty")
    vals = frame["close"].to_numpy(float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        raise RuntimeError("R5-C source invalid closes")
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def combine(hist: pd.DataFrame, blackbox: pd.DataFrame) -> pd.DataFrame:
    if str(hist["trading_day"].min()) != "2015-01-05" or str(hist["trading_day"].max()) != "2025-12-31":
        raise RuntimeError("R5-C historical context drifted")
    if str(blackbox["trading_day"].min()) != BLACKBOX_START or str(blackbox["trading_day"].max()) != BLACKBOX_END:
        raise RuntimeError("R5-C BLACKBOX window incomplete")
    out = pd.concat([hist, blackbox], ignore_index=True).sort_values(["trading_day", "timestamp"], kind="mergesort")
    if out.duplicated(["symbol", "trading_day", "timestamp"]).any():
        raise RuntimeError("R5-C combined source duplicate minute")
    return out.reset_index(drop=True)


def frozen_predict(snapshot: dict, x: np.ndarray) -> np.ndarray:
    mean = np.asarray(snapshot["scaler"]["mean"], dtype=float)
    scale = np.asarray(snapshot["scaler"]["scale"], dtype=float)
    z = (np.asarray(x, dtype=float) - mean) / scale
    coef = np.asarray(snapshot["logistic"]["coef"], dtype=float)
    intercept = float(snapshot["logistic"]["intercept"])
    logits = z @ coef + intercept
    out = np.empty_like(logits, dtype=float)
    pos = logits >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-logits[pos]))
    ex = np.exp(logits[~pos])
    out[~pos] = ex / (1.0 + ex)
    return out


def scale_gate(events: pd.DataFrame, frozen: dict, minimum: int) -> tuple[bool, bool]:
    if len(events) < minimum:
        return False, False
    y = events["y"].to_numpy(int)
    p_base = frozen_predict(frozen["baseline_model"], events[r5c.BASE_FEATURES].to_numpy(float))
    p_cand = frozen_predict(frozen["candidate_model"], events[r5c.CAND_FEATURES].to_numpy(float))
    brier_base = float(brier_score_loss(y, p_base))
    brier_cand = float(brier_score_loss(y, p_cand))
    ll_base = float(log_loss(y, p_base, labels=[0, 1]))
    ll_cand = float(log_loss(y, p_cand, labels=[0, 1]))
    return True, bool(brier_cand < brier_base and ll_cand < ll_base)


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
    last_idx = len(frame) - 1

    results = {}
    for scale in r5c.SCALES:
        threshold = float(freeze["thresholds"][scale])
        waves = common.detect_waves(prices, threshold)
        obs = r5c.wave_observations(waves, threshold, days)
        events = r5c.role_events(obs, prices, threshold, BLACKBOX_START, BLACKBOX_END, last_idx)
        minimum = int(protocol["BLACKBOX"]["minimum_resolved"][scale])
        results[scale] = scale_gate(events, freeze["pairings"][scale], minimum)
    decision = decide(results)

    candidate_fp = freeze["parameter_bundle_sha256"]
    protocol_fp = sha256(PROTOCOL)
    query_id = hashlib.sha256(f"R5C|{candidate_fp}|{protocol_fp}|{BLACKBOX_SHA}".encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "factorlab_reusable_blackbox_certification_receipt@1.0",
        "research_identity": "rmr_event_density_state_reversal_v2",
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
