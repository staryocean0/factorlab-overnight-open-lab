#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/relative_index_open_leadership_joint_blackbox_protocol_v1.json"
RECEIPT = ROOT / "docs/research/local_relative_index_open_leadership_joint_blackbox_receipt_v1.json"
IDENTITY = "overnight_relative_size_open_leadership_joint_15m_30m_60m_v1"
BASELINE = ["common_open_component", "relative_r1", "relative_log_rvol"]
TARGETS = ["relative_ret_0935_0950", "relative_ret_0935_1005", "relative_ret_0935_1035"]
VALID_START = pd.Timestamp("2021-01-01")
VALID_END = pd.Timestamp("2025-12-31")
WARMUP_START = pd.Timestamp("2020-11-01")
SYMBOLS = {"CSI1000": "000852.SH", "CSI300": "000300.SH"}
CLOCKS = ["09:31", "09:35", "09:50", "10:05", "10:35", "15:00"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def zscore(a: np.ndarray) -> np.ndarray:
    sd = a.std(axis=0, ddof=0)
    if np.ndim(sd) == 0:
        if not np.isfinite(sd) or sd <= 0:
            raise RuntimeError("zero/nonfinite standard deviation")
    else:
        if np.any(~np.isfinite(sd)) or np.any(sd <= 0):
            raise RuntimeError("zero/nonfinite standard deviation")
    return (a - a.mean(axis=0)) / sd


def ols_r2_beta(y: np.ndarray, x: np.ndarray) -> tuple[float, np.ndarray]:
    X = np.column_stack([np.ones(len(y)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sse = float(resid @ resid)
    centered = y - y.mean()
    sst = float(centered @ centered)
    r2 = float(1.0 - sse / sst) if sst > 0 else float("nan")
    return r2, beta


def residualize(v: np.ndarray, x: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones(len(v)), x])
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    return v - X @ beta


def metrics(part: pd.DataFrame, target: str) -> dict[str, float]:
    cols = BASELINE + ["size_open_leadership", target]
    xdf = part[cols].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(xdf.to_numpy(dtype=float)).all(axis=1)
    xdf = xdf.loc[mask]
    if len(xdf) < 4:
        return {"n": float(len(xdf))}
    b = xdf[BASELINE].to_numpy(dtype=float)
    c = xdf["size_open_leadership"].to_numpy(dtype=float)
    y = xdf[target].to_numpy(dtype=float)
    r2_base, _ = ols_r2_beta(y, b)
    full = np.column_stack([b, c])
    r2_full, _ = ols_r2_beta(y, full)
    ry = residualize(y, b)
    rc = residualize(c, b)
    pc = float(np.corrcoef(ry, rc)[0, 1]) if np.std(ry) > 0 and np.std(rc) > 0 else float("nan")
    _, beta_z = ols_r2_beta(zscore(y), zscore(full))
    return {
        "n": float(len(xdf)),
        "partial_corr": pc,
        "std_coef": float(beta_z[-1]),
        "delta_r2": float(r2_full - r2_base),
    }


def standardized_coef(part: pd.DataFrame, target: str) -> float:
    cols = BASELINE + ["size_open_leadership", target]
    xdf = part[cols].apply(pd.to_numeric, errors="coerce")
    xdf = xdf.loc[np.isfinite(xdf.to_numpy(dtype=float)).all(axis=1)]
    if len(xdf) < 4:
        return float("nan")
    full = xdf[BASELINE + ["size_open_leadership"]].to_numpy(dtype=float)
    y = xdf[target].to_numpy(dtype=float)
    _, beta_z = ols_r2_beta(zscore(y), zscore(full))
    return float(beta_z[-1])


def bootstrap_support(part: pd.DataFrame, target: str, block: int, reps: int, seed: int) -> float:
    cols = BASELINE + ["size_open_leadership", target]
    xdf = part[["trading_day"] + cols].copy()
    numeric = xdf[cols].apply(pd.to_numeric, errors="coerce")
    xdf = xdf.loc[np.isfinite(numeric.to_numpy(dtype=float)).all(axis=1)].sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    n = len(xdf)
    if n < block:
        return float("nan")
    rng = np.random.default_rng(seed)
    positive = 0
    valid = 0
    max_start = n - block
    blocks_needed = int(math.ceil(n / block))
    for _ in range(reps):
        starts = rng.integers(0, max_start + 1, size=blocks_needed)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        coef = standardized_coef(xdf.iloc[idx], target)
        if np.isfinite(coef):
            valid += 1
            positive += int(coef > 0)
    if valid != reps:
        raise RuntimeError("bootstrap produced invalid replicate")
    return float(positive / valid)


def read_symbol(source: Path, symbol: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        source,
        filters=[
            ("symbol", "==", symbol),
            ("trading_day", ">=", WARMUP_START),
            ("trading_day", "<=", VALID_END),
        ],
        columns=["symbol", "trading_day", "timestamp", "open", "close"],
    )
    if frame.empty:
        raise RuntimeError(f"no source rows for {symbol}")
    frame["trading_day"] = pd.to_datetime(frame["trading_day"])
    if frame["trading_day"].min() < WARMUP_START or frame["trading_day"].max() > VALID_END:
        raise RuntimeError("source crossed frozen read boundary")
    if frame.duplicated(["trading_day", "timestamp"]).any():
        raise RuntimeError(f"duplicate timestamp for {symbol}")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    frame = frame.loc[frame["clock"].isin(CLOCKS)].copy()
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def daily_symbol(source: Path, name: str, symbol: str) -> pd.DataFrame:
    m = read_symbol(source, symbol)
    closes = m.pivot_table(index="trading_day", columns="clock", values="close", aggfunc="last")
    opens = m.loc[m["clock"] == "09:31", ["trading_day", "open"]].drop_duplicates("trading_day").set_index("trading_day")
    out = pd.DataFrame(index=sorted(set(m["trading_day"])))
    out.index.name = "trading_day"
    out["open_0931"] = pd.to_numeric(opens["open"], errors="coerce").reindex(out.index)
    for clock in ["09:35", "09:50", "10:05", "10:35", "15:00"]:
        out[f"close_{clock.replace(':','')}"] = pd.to_numeric(closes.get(clock), errors="coerce").reindex(out.index)
    close = out["close_1500"]
    out["prev_close_1500"] = close.shift(1)
    daily_ret = close.pct_change(fill_method=None)
    out["r1"] = daily_ret.shift(1)
    out["rvol20"] = daily_ret.shift(1).rolling(20, min_periods=20).std()
    out["gap"] = out["open_0931"] / out["prev_close_1500"] - 1.0
    out["gap_rvol"] = out["gap"] / out["rvol20"]
    return out.add_suffix(f"_{name}").reset_index()


def build_frame(source: Path) -> pd.DataFrame:
    a = daily_symbol(source, "CSI1000", SYMBOLS["CSI1000"])
    b = daily_symbol(source, "CSI300", SYMBOLS["CSI300"])
    frame = a.merge(b, on="trading_day", how="inner").sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    frame = frame.loc[(frame["trading_day"] >= VALID_START) & (frame["trading_day"] <= VALID_END)].copy()
    frame["size_open_leadership"] = frame["gap_rvol_CSI1000"] - frame["gap_rvol_CSI300"]
    frame["common_open_component"] = 0.5 * (frame["gap_rvol_CSI1000"] + frame["gap_rvol_CSI300"])
    frame["relative_r1"] = frame["r1_CSI1000"] - frame["r1_CSI300"]
    good_rvol = (frame["rvol20_CSI1000"] > 0) & (frame["rvol20_CSI300"] > 0)
    frame["relative_log_rvol"] = np.where(
        good_rvol,
        np.log(frame["rvol20_CSI1000"]) - np.log(frame["rvol20_CSI300"]),
        np.nan,
    )
    for clock in ["0950", "1005", "1035"]:
        r1000 = frame[f"close_{clock}_CSI1000"] / frame["close_0935_CSI1000"] - 1.0
        r300 = frame[f"close_{clock}_CSI300"] / frame["close_0935_CSI300"] - 1.0
        frame[f"relative_ret_0935_{clock}"] = r1000 - r300
    frame["year"] = frame["trading_day"].dt.year.astype(int)
    if not set(frame["year"].unique()).issubset({2021, 2022, 2023, 2024, 2025}):
        raise RuntimeError("validation frame crossed 2021-2025")
    return frame


def main() -> None:
    if RECEIPT.exists():
        raise RuntimeError("refusing to overwrite existing compact receipt")
    protocol = load_json(PROTOCOL)
    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("identity drift")
    if protocol.get("candidate_increment") != ["size_open_leadership"] or protocol.get("baseline_controls") != BASELINE or protocol.get("targets") != TARGETS:
        raise RuntimeError("frozen model contract drift")
    if protocol.get("candidate_indices") != SYMBOLS:
        raise RuntimeError("candidate index drift")
    source_raw = os.environ.get(protocol["source_dataset"]["required_environment_variable"])
    if not source_raw:
        raise RuntimeError("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE is required")
    source = Path(source_raw).expanduser().resolve()
    if not source.exists():
        raise RuntimeError("admitted source path does not exist")
    expected_version = protocol["source_dataset"]["dataset_version"]
    if expected_version not in str(source):
        raise RuntimeError("source path is not the admitted dataset identity")

    frame = build_frame(source)
    suff = protocol["sufficiency_gates"]
    sci = protocol["scientific_gates_each_horizon"]
    boot = protocol["moving_block_bootstrap"]
    insufficient = False
    all_pass = True
    for target in TARGETS:
        pooled = metrics(frame, target)
        annual = {y: metrics(frame.loc[frame["year"] == y], target) for y in range(2021, 2026)}
        if pooled.get("n", 0) < int(suff["minimum_pooled_complete_cases_each_horizon"]):
            insufficient = True
        if any(annual[y].get("n", 0) < int(suff["minimum_complete_cases_each_calendar_year_each_horizon"]) for y in annual):
            insufficient = True
        if insufficient:
            continue
        annual_coefs = [annual[y]["std_coef"] for y in annual]
        support = bootstrap_support(frame, target, int(boot["block_length_trading_days"]), int(boot["resamples"]), int(boot["seed"]))
        target_pass = bool(
            pooled["partial_corr"] > 0
            and pooled["std_coef"] > 0
            and pooled["delta_r2"] > 0
            and sum(v > 0 for v in annual_coefs) >= int(sci["minimum_positive_calendar_year_coefficients"])
            and float(np.median(annual_coefs)) > 0
            and support >= 0.90
        )
        all_pass = all_pass and target_pass

    decision = "INSUFFICIENT" if insufficient else ("PASS" if all_pass else "FAIL")
    protocol_sha = sha256(PROTOCOL)
    source_sha = str(protocol["source_dataset"]["sha256"])
    query_id = hashlib.sha256(f"{IDENTITY}|{protocol_sha}|{source_sha}".encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "overnight_relative_index_open_leadership_joint_blackbox_receipt@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "parent_development_identity": "overnight_relative_size_open_leadership_v1",
        "product_family": "OFP-D1_relative_index_open",
        "decision": decision,
        "query_id": query_id,
        "protocol_sha256": protocol_sha,
        "source_dataset_sha256": source_sha,
        "validation_window": "2021-01-01..2025-12-31",
        "joint_horizons": ["15m", "30m", "60m"],
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "calendar_year_results_persisted": False,
        "bootstrap_results_persisted": False,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "same_period_reuse_is_independent_oos": False,
        "production_authority": False
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)


if __name__ == "__main__":
    main()
