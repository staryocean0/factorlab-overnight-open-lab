#!/usr/bin/env python3
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
IDENTITY = "overnight_c1_b4_timing_confidence_adapter_validation_v1"
BB_START = pd.Timestamp("2021-01-01")
BB_END = pd.Timestamp("2025-12-31")
SYMBOL = "000852.SH"
TARGET_CLOCKS = {"09:35": "close_0935", "09:50": "close_0950"}
PARITY_TOL = 1e-12


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_b4_module():
    path = ROOT / "scripts/run_driver_coherence_open_gap_blackbox.py"
    spec = importlib.util.spec_from_file_location("frozen_b4_blackbox", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen B4 reconstruction module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sign_series(x: pd.Series) -> pd.Series:
    v = pd.to_numeric(x, errors="coerce").to_numpy(dtype=float)
    return pd.Series(np.sign(v), index=x.index, dtype=float)


def extract_exact_clocks(minute_bars: Path) -> pd.DataFrame:
    bars = pd.read_parquet(
        minute_bars,
        columns=["symbol", "trading_day", "timestamp", "close"],
        filters=[
            ("symbol", "==", SYMBOL),
            ("trading_day", ">=", "2019-01-01"),
            ("trading_day", "<=", "2025-12-31"),
        ],
    ).copy()
    bars = bars.loc[bars["symbol"].astype(str).eq(SYMBOL)].copy()
    if bars.empty:
        raise RuntimeError("minute bars contain no CSI1000 rows")
    bars["trading_day"] = pd.to_datetime(bars["trading_day"], errors="raise").dt.normalize()
    ts = bars["timestamp"].astype(str)
    bars["clock"] = ts.str.slice(11, 16)
    exact = bars.loc[bars["clock"].isin(TARGET_CLOCKS), ["trading_day", "clock", "close"]].copy()
    if exact.duplicated(["trading_day", "clock"]).any():
        raise RuntimeError("duplicate exact target clock rows")
    exact["close"] = pd.to_numeric(exact["close"], errors="coerce")
    wide = exact.pivot(index="trading_day", columns="clock", values="close").reset_index()
    out = pd.DataFrame({"trading_day": wide["trading_day"]})
    for clock, col in TARGET_CLOCKS.items():
        out[col] = pd.to_numeric(wide[clock], errors="coerce") if clock in wide.columns else np.nan
    return out.sort_values("trading_day", kind="mergesort").reset_index(drop=True)


def verify_clock_parity(clocks: pd.DataFrame) -> None:
    current = clocks.set_index("trading_day")
    for year in (2019, 2020):
        path = ROOT / f"data/runtime_text_2015_2025/opening_clocks_{year}.csv"
        dev = pd.read_csv(path)
        dev["trading_day"] = pd.to_datetime(dev["trading_day"], errors="raise").dt.normalize()
        dev = dev.set_index("trading_day")
        common = dev.index.intersection(current.index)
        if len(common) < 200:
            raise RuntimeError("insufficient target-clock overlap for parity")
        for col in TARGET_CLOCKS.values():
            a = pd.to_numeric(current.loc[common, col], errors="coerce")
            b = pd.to_numeric(dev.loc[common, col], errors="coerce")
            if not np.array_equal(a.isna().to_numpy(), b.isna().to_numpy()):
                raise RuntimeError("target-clock parity NaN-mask drift")
            mask = a.notna() & b.notna()
            if int(mask.sum()) < 200:
                raise RuntimeError("insufficient comparable target-clock parity rows")
            if float((a[mask] - b[mask]).abs().max()) > PARITY_TOL:
                raise RuntimeError("target-clock reconstruction drift")


def build_frame(panel_path: Path, hkma: Path, holiday_a50: Path, ordinary_a50: Path, minute_bars: Path, external_manifest: dict, b4) -> tuple[pd.DataFrame, bool]:
    panel = pd.read_parquet(panel_path).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    needed = {
        "trading_day", "gap", "r1", "r20", "rvol20", "holiday_reopen",
        "us_nasdaq", "us_vix_chg",
    }
    if not needed.issubset(panel.columns):
        raise RuntimeError("reconstructed panel missing frozen E1 inputs")
    panel = panel.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    panel["previous_china_day"] = panel["trading_day"].shift(1)

    df = b4.add_hkma(panel, hkma)
    df, ordinary_coverage, a50_clocks_ok = b4.attach_a50(df, holiday_a50, ordinary_a50)
    df = b4.build_coordinates(df)

    clocks = extract_exact_clocks(minute_bars)
    verify_clock_parity(clocks)
    df = df.merge(clocks, on="trading_day", how="left", validate="one_to_one")

    rvol = pd.to_numeric(df["rvol20"], errors="coerce")
    gap = pd.to_numeric(df["gap"], errors="coerce")
    r20 = pd.to_numeric(df["r20"], errors="coerce")
    df["observed_gap_rvol"] = gap / rvol
    df["trend20_rvol"] = r20 / (np.sqrt(20.0) * rvol)
    df["trend_gap_interaction"] = df["observed_gap_rvol"] * df["trend20_rvol"]
    df["c1_action"] = sign_series(-df["trend_gap_interaction"])
    df["gap_sign"] = sign_series(df["observed_gap_rvol"])
    df["driver_alignment"] = pd.to_numeric(df["driver_coherence"], errors="coerce") * df["gap_sign"]
    df["comparator_action"] = df["c1_action"]
    df["candidate_action"] = np.where(df["driver_alignment"] >= 0, df["c1_action"], 0.0)
    df["target"] = pd.to_numeric(df["close_0950"], errors="coerce") / pd.to_numeric(df["close_0935"], errors="coerce") - 1.0
    df["year"] = df["trading_day"].dt.year.astype(int)

    required_assertions = [
        "same_contract_all_events", "no_future_volume_or_oi_selection",
        "no_mid_window_roll", "no_forward_fill_or_interpolation",
        "blackbox_not_used_for_fit_or_rule_selection",
    ]
    source_ok = all(external_manifest.get("assertions", {}).get(k) is True for k in required_assertions)
    source_ok = bool(source_ok and a50_clocks_ok and ordinary_coverage >= 0.90)
    return df, source_ok


def complete_rows(frame: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "rvol20", "observed_gap_rvol", "trend20_rvol", "trend_gap_interaction",
        "driver_coherence", "driver_alignment", "comparator_action", "candidate_action", "target",
    ]
    numeric = frame[cols].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(numeric.to_numpy(dtype=float)).all(axis=1) & numeric["rvol20"].gt(0)
    return frame.loc[mask, ["trading_day", "year", *cols]].copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)


def mean_delta(frame: pd.DataFrame) -> float:
    comp = frame["comparator_action"].to_numpy(float) * frame["target"].to_numpy(float)
    cand = frame["candidate_action"].to_numpy(float) * frame["target"].to_numpy(float)
    return float(np.mean(cand - comp))


def bootstrap_support(frame: pd.DataFrame, block: int, reps: int, seed: int) -> float:
    n = len(frame)
    if n < block:
        return float("nan")
    delta = (
        frame["candidate_action"].to_numpy(float) * frame["target"].to_numpy(float)
        - frame["comparator_action"].to_numpy(float) * frame["target"].to_numpy(float)
    )
    rng = np.random.default_rng(seed)
    max_start = n - block
    blocks_needed = int(math.ceil(n / block))
    positive = 0
    for _ in range(reps):
        starts = rng.integers(0, max_start + 1, size=blocks_needed)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        positive += int(float(np.mean(delta[idx])) > 0)
    return float(positive / reps)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--minute-bars", type=Path, required=True)
    ap.add_argument("--hkma", type=Path, required=True)
    ap.add_argument("--holiday-a50", type=Path, required=True)
    ap.add_argument("--ordinary-a50", type=Path, required=True)
    ap.add_argument("--high-open-source-manifest", type=Path, required=True)
    ap.add_argument("--external-source-manifest", type=Path, required=True)
    ap.add_argument("--reconstruction-contract", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--receipt-out", type=Path, required=True)
    args = ap.parse_args()

    if args.receipt_out.exists():
        raise RuntimeError("refusing to overwrite existing compact receipt")
    protocol = load_json(args.protocol)
    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("wrong E1 validation identity")
    defs = protocol.get("definitions", {})
    if defs.get("candidate_action") != "c1_action if driver_alignment >= 0 else 0" or defs.get("comparator_action") != "c1_action":
        raise RuntimeError("E1 validation action contract drift")
    if protocol.get("candidate_family", {}).get("attempt_count") != 1 or protocol.get("candidate_family", {}).get("free_parameters") != 0:
        raise RuntimeError("E1 validation candidate family drift")

    high_manifest = load_json(args.high_open_source_manifest)
    external_manifest = load_json(args.external_source_manifest)
    b4 = load_b4_module()
    frame_all, source_ok = build_frame(
        args.panel, args.hkma, args.holiday_a50, args.ordinary_a50,
        args.minute_bars, external_manifest, b4,
    )
    bb = frame_all.loc[frame_all["trading_day"].between(BB_START, BB_END)].copy()
    bb = complete_rows(bb)

    suff = protocol["sufficiency_gates"]
    pooled_n = len(bb)
    annual_n = {year: int((bb["year"] == year).sum()) for year in range(2021, 2026)}
    annual_active = {
        year: int(bb.loc[bb["year"] == year, "candidate_action"].ne(0).sum())
        for year in range(2021, 2026)
    }
    sufficient = bool(
        source_ok
        and pooled_n >= int(suff["minimum_pooled_complete_cases"])
        and all(v >= int(suff["minimum_complete_cases_each_calendar_year"]) for v in annual_n.values())
        and all(v >= int(suff["minimum_candidate_active_days_each_calendar_year"]) for v in annual_active.values())
    )

    if not sufficient:
        decision = "INSUFFICIENT"
    else:
        pooled_delta = mean_delta(bb)
        annual_delta = [mean_delta(bb.loc[bb["year"] == year].copy()) for year in range(2021, 2026)]
        positive_years = sum(v > 0 for v in annual_delta)
        median_annual = float(np.median(annual_delta))
        boot = protocol["moving_block_bootstrap"]
        support = bootstrap_support(
            bb,
            int(boot["block_length_trading_days"]),
            int(boot["resamples"]),
            int(boot["seed"]),
        )
        sci = protocol["scientific_gates"]
        passed = bool(
            pooled_delta > 0
            and positive_years >= int(sci["minimum_positive_calendar_year_delta_count"])
            and median_annual >= 0
            and support >= 0.90
        )
        decision = "PASS" if passed else "FAIL"

    protocol_sha = sha256(args.protocol)
    high_sha = sha256(args.high_open_source_manifest)
    external_sha = sha256(args.external_source_manifest)
    reconstruction_sha = sha256(args.reconstruction_contract)
    query_id = hashlib.sha256(
        f"{IDENTITY}|{protocol_sha}|{high_sha}|{external_sha}|{reconstruction_sha}".encode()
    ).hexdigest()[:20]

    receipt = {
        "schema_id": "overnight_downstream_timing_adapter_reusable_blackbox_receipt@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "parent_development_identity": "overnight_c1_b4_timing_confidence_adapter_v1",
        "product_family": "OFP-E1_timing_adapter",
        "decision": decision,
        "query_id": query_id,
        "protocol_sha256": protocol_sha,
        "high_open_source_manifest_sha256": high_sha,
        "external_source_manifest_sha256": external_sha,
        "reconstruction_contract_sha256": reconstruction_sha,
        "validation_window": "2021-01-01..2025-12-31",
        "reconstructed_panel_2015_2020_parity": "PASS",
        "target_clock_2019_2020_parity": "PASS",
        "upstream_C1_query_id": "5a27b953276382e473c0",
        "upstream_B4_query_id": "33ccb040dd0d1822f3b6",
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "calendar_year_results_persisted": False,
        "counts_persisted": False,
        "bootstrap_results_persisted": False,
        "failure_attribution_persisted": False,
        "strategy_PnL_persisted": False,
        "account_results_persisted": False,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "same_period_reuse_is_independent_oos": False,
        "authority_if_PASS": "validated_E1_factor_utility_adapter_contract_only",
        "account_or_strategy_authority_if_PASS": False,
        "production_authority": False,
    }
    args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
