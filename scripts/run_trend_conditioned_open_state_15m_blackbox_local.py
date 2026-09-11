#!/usr/bin/env python3
"""Low-bandwidth reusable BLACKBOX controller for the frozen C1 15m identity.

Public scientific output is exactly PASS / FAIL / INSUFFICIENT. Detailed
2021-2025 metrics, yearly signs, counts, bootstrap statistics and event rows are
never persisted in the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

IDENTITY = "overnight_trend_conditioned_open_state_15m_v1"
SYMBOL = "000852.SH"
BLACKBOX_START = "2021-01-01"
BLACKBOX_END = "2025-12-31"
BASELINE_CONTROLS = [
    "observed_gap_rvol",
    "trend20_rvol",
    "r1",
    "prev_daytime",
    "holiday_reopen",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_manifest_product(manifest: dict, path: Path) -> None:
    wanted = path.as_posix()
    products = manifest.get("products", [])
    match = next((p for p in products if p.get("path") == wanted), None)
    if match is None:
        raise RuntimeError(f"source path not declared by manifest: {wanted}")
    expected = match.get("sha256")
    if not expected or sha256(path) != expected:
        raise RuntimeError(f"source hash mismatch: {wanted}")


def residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    design = np.column_stack([np.ones(len(x)), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    return y - design @ coef


def standardized_interaction_coefficient(frame: pd.DataFrame) -> float:
    cols = [*BASELINE_CONTROLS, "trend_gap_interaction", "target"]
    x = frame[cols].astype(float).copy()
    for col in cols:
        sd = float(x[col].std(ddof=0))
        if not np.isfinite(sd) or sd == 0:
            raise RuntimeError("degenerate BLACKBOX regression column")
        x[col] = (x[col] - float(x[col].mean())) / sd
    design = np.column_stack(
        [np.ones(len(x)), x[[*BASELINE_CONTROLS, "trend_gap_interaction"]].to_numpy(float)]
    )
    coef, *_ = np.linalg.lstsq(design, x["target"].to_numpy(float), rcond=None)
    return float(coef[-1])


def partial_corr(frame: pd.DataFrame) -> float:
    controls = frame[BASELINE_CONTROLS].to_numpy(float)
    interaction = frame["trend_gap_interaction"].to_numpy(float)
    target = frame["target"].to_numpy(float)
    i_resid = residualize(interaction, controls)
    y_resid = residualize(target, controls)
    if np.std(i_resid) == 0 or np.std(y_resid) == 0:
        raise RuntimeError("degenerate BLACKBOX partial correlation")
    value = float(np.corrcoef(i_resid, y_resid)[0, 1])
    if not np.isfinite(value):
        raise RuntimeError("non-finite BLACKBOX partial correlation")
    return value


def moving_block_negative_support(
    frame: pd.DataFrame, block_length: int, resamples: int, seed: int
) -> float:
    n = len(frame)
    if n < block_length:
        raise RuntimeError("BLACKBOX sample shorter than bootstrap block")
    rng = np.random.default_rng(seed)
    starts = np.arange(0, n - block_length + 1)
    negative = 0
    valid = 0
    for _ in range(resamples):
        idx_parts: list[np.ndarray] = []
        length = 0
        while length < n:
            start = int(rng.choice(starts))
            block = np.arange(start, start + block_length)
            idx_parts.append(block)
            length += len(block)
        idx = np.concatenate(idx_parts)[:n]
        sample = frame.iloc[idx]
        try:
            coef = standardized_interaction_coefficient(sample)
        except RuntimeError:
            continue
        valid += 1
        negative += int(coef < 0)
    if valid != resamples:
        raise RuntimeError("invalid bootstrap resample encountered")
    return negative / valid


def load_target(minute_bars: Path) -> pd.DataFrame:
    bars = pd.read_parquet(
        minute_bars,
        filters=[
            ("symbol", "==", SYMBOL),
            ("trading_day", ">=", BLACKBOX_START),
            ("trading_day", "<=", BLACKBOX_END),
        ],
        columns=["trading_day", "timestamp", "close"],
    ).copy()
    bars["trading_day"] = bars["trading_day"].astype(str)
    bars["clock"] = bars["timestamp"].astype(str).str.slice(11, 16)
    bars = bars.loc[bars["clock"].isin(["09:35", "09:50"])].copy()
    bars["close"] = pd.to_numeric(bars["close"], errors="coerce")
    wide = bars.pivot_table(index="trading_day", columns="clock", values="close", aggfunc="last")
    if "09:35" not in wide.columns or "09:50" not in wide.columns:
        raise RuntimeError("frozen 15m BLACKBOX clocks unavailable")
    out = pd.DataFrame(
        {
            "trading_day": wide.index.astype(str),
            "target": (wide["09:50"] / wide["09:35"] - 1.0).to_numpy(),
        }
    )
    return out.reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--minute-bars", type=Path, required=True)
    ap.add_argument("--raw-panel", type=Path, required=True)
    ap.add_argument("--nasdaq", type=Path, required=True)
    ap.add_argument("--vix", type=Path, required=True)
    ap.add_argument("--frozen-panel", type=Path, required=True)
    ap.add_argument("--source-manifest", type=Path, required=True)
    ap.add_argument("--base-manifest", type=Path, required=True)
    ap.add_argument("--reconstruction-contract", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("wrong C1 15m BLACKBOX protocol")
    if protocol.get("public_output_enum") != ["PASS", "FAIL", "INSUFFICIENT"]:
        raise RuntimeError("unexpected BLACKBOX public-output contract")

    source_manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    base_manifest = json.loads(args.base_manifest.read_text(encoding="utf-8"))
    for path in (args.raw_panel, args.minute_bars, args.nasdaq, args.vix):
        verify_manifest_product(source_manifest, path)
    verify_manifest_product(base_manifest, args.frozen_panel)

    panel = pd.read_parquet(args.panel).copy()
    panel["trading_day"] = panel["trading_day"].astype(str)
    panel = panel.loc[
        panel["trading_day"].between(BLACKBOX_START, BLACKBOX_END),
        ["trading_day", "gap", "r1", "r20", "prev_daytime", "rvol20", "holiday_reopen"],
    ].copy()
    panel["rvol20"] = pd.to_numeric(panel["rvol20"], errors="coerce")
    panel = panel.loc[np.isfinite(panel["rvol20"]) & panel["rvol20"].gt(0)].copy()
    panel["observed_gap_rvol"] = pd.to_numeric(panel["gap"], errors="coerce") / panel["rvol20"]
    panel["trend20_rvol"] = pd.to_numeric(panel["r20"], errors="coerce") / (
        np.sqrt(20.0) * panel["rvol20"]
    )
    panel["trend_gap_interaction"] = panel["observed_gap_rvol"] * panel["trend20_rvol"]

    target = load_target(args.minute_bars)
    frame = panel.merge(target, on="trading_day", how="inner", validate="one_to_one")
    cols = [*BASELINE_CONTROLS, "trend_gap_interaction", "target"]
    frame[cols] = frame[cols].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=cols).sort_values("trading_day").reset_index(drop=True)
    frame["year"] = pd.to_datetime(frame["trading_day"]).dt.year

    suff = protocol["internal_sufficiency_gates"]
    pooled_min = int(suff["pooled_complete_cases_min"])
    per_year_min = int(suff["each_calendar_year_complete_cases_min"])
    years = list(range(2021, 2026))
    sufficient = len(frame) >= pooled_min and all(int((frame["year"] == y).sum()) >= per_year_min for y in years)

    if not sufficient:
        decision = "INSUFFICIENT"
    else:
        pooled_coef = standardized_interaction_coefficient(frame)
        pooled_pcorr = partial_corr(frame)
        yearly_coefs = [standardized_interaction_coefficient(frame.loc[frame["year"] == y]) for y in years]
        negative_year_count = sum(c < 0 for c in yearly_coefs)
        median_year_coef = float(np.median(yearly_coefs))
        boot = protocol["internal_scientific_gates"]["moving_block_bootstrap"]
        bootstrap_support = moving_block_negative_support(
            frame,
            int(boot["block_length_trading_days"]),
            int(boot["resamples"]),
            int(boot["seed"]),
        )
        gates = [
            pooled_pcorr < 0,
            pooled_coef < 0,
            negative_year_count >= int(protocol["internal_scientific_gates"]["negative_calendar_year_coefficient_count_min"]),
            median_year_coef < 0,
            bootstrap_support >= float(boot["negative_coefficient_support_min"]),
        ]
        decision = "PASS" if all(gates) else "FAIL"

    protocol_sha = sha256(args.protocol)
    source_manifest_sha = sha256(args.source_manifest)
    reconstruction_sha = sha256(args.reconstruction_contract)
    query_payload = "|".join([IDENTITY, protocol_sha, source_manifest_sha, reconstruction_sha])
    query_id = hashlib.sha256(query_payload.encode("utf-8")).hexdigest()[:20]

    receipt = {
        "schema_id": "overnight_trend_conditioned_open_state_15m_blackbox_receipt@1.0",
        "query_id": query_id,
        "research_identity": IDENTITY,
        "comparator": "same_controls_without_trend_gap_interaction",
        "decision": decision,
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "protocol_sha256": protocol_sha,
        "source_manifest_sha256": source_manifest_sha,
        "reconstruction_contract_sha256": reconstruction_sha,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
