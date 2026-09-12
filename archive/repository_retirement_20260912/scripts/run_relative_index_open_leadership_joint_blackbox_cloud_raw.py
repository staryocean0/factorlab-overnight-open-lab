#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/relative_index_blackbox_raw_text_2020_2025"
RAW_MANIFEST = RAW_ROOT / "manifest.json"
UPLOAD_RECEIPT = ROOT / "docs/research/relative_index_blackbox_raw_text_upload_receipt_v1.json"
DEV_2020 = ROOT / "data/relative_index_runtime_text_2015_2020/relative_index_open_carrier_2020.csv"
PROTOCOL = ROOT / "docs/governance/relative_index_open_leadership_joint_blackbox_protocol_v1.json"
RECEIPT = ROOT / "docs/research/local_relative_index_open_leadership_joint_blackbox_receipt_v1.json"

IDENTITY = "overnight_relative_size_open_leadership_joint_15m_30m_60m_v1"
SYMBOLS = {"CSI1000": "000852.SH", "CSI300": "000300.SH"}
BASELINE = ["common_open_component", "relative_r1", "relative_log_rvol"]
TARGETS = ["relative_ret_0935_0950", "relative_ret_0935_1005", "relative_ret_0935_1035"]
RAW_COLUMNS = [
    "trading_day", "index_name", "symbol", "open_0931", "close_0935",
    "close_0950", "close_1005", "close_1035", "close_1500",
]
EXPECTED_CLOCKS = ["09:31", "09:35", "09:50", "10:05", "10:35", "15:00"]
VALID_START = pd.Timestamp("2021-01-01")
VALID_END = pd.Timestamp("2025-12-31")
PARITY_TOL = 1e-12


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
    elif np.any(~np.isfinite(sd)) or np.any(sd <= 0):
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
    xdf = xdf.loc[np.isfinite(xdf.to_numpy(dtype=float)).all(axis=1)]
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


def verify_contract() -> tuple[dict, dict]:
    protocol = load_json(PROTOCOL)
    manifest = load_json(RAW_MANIFEST)
    upload = load_json(UPLOAD_RECEIPT)

    if protocol.get("research_identity") != IDENTITY:
        raise RuntimeError("identity drift")
    if protocol.get("candidate_indices") != SYMBOLS:
        raise RuntimeError("candidate-index drift")
    if protocol.get("candidate_increment") != ["size_open_leadership"]:
        raise RuntimeError("candidate drift")
    if protocol.get("baseline_controls") != BASELINE or protocol.get("targets") != TARGETS:
        raise RuntimeError("frozen model contract drift")

    expected_version = protocol["source_dataset"]["dataset_version"]
    expected_source_sha = protocol["source_dataset"]["sha256"]
    if manifest.get("research_identity") != IDENTITY:
        raise RuntimeError("raw carrier identity drift")
    if manifest.get("source_dataset_version") != expected_version or manifest.get("source_dataset_sha256") != expected_source_sha:
        raise RuntimeError("raw carrier source identity drift")
    if manifest.get("symbols") != SYMBOLS:
        raise RuntimeError("raw carrier symbols drift")
    if manifest.get("exact_clocks") != EXPECTED_CLOCKS or manifest.get("columns") != RAW_COLUMNS:
        raise RuntimeError("raw carrier clock/column drift")
    if manifest.get("read_window") != {"start": "2020-11-01", "end": "2025-12-31"}:
        raise RuntimeError("raw carrier read-window drift")
    if manifest.get("CSI500_loaded") is not False or manifest.get("2026_rows_loaded") is not False:
        raise RuntimeError("forbidden data exposure in raw carrier")
    transform = manifest.get("transform", {})
    required_false = ["feature_engineering", "target_engineering", "forward_fill", "backward_fill", "nearest_clock_substitution", "resampling", "scientific_analysis"]
    if transform.get("exact_clock_filter_only") is not True or any(transform.get(k) is not False for k in required_false):
        raise RuntimeError("raw carrier transform contract drift")

    if upload.get("BLACKBOX_controller_run") is not False or upload.get("BLACKBOX_decision_generated") is not False or upload.get("D1_regression_run") is not False:
        raise RuntimeError("local upload crossed scientific boundary")
    if upload.get("query_4_created") is not False or upload.get("2026_rows_loaded") is not False or upload.get("CSI500_loaded") is not False:
        raise RuntimeError("local upload governance boundary drift")
    if sha256(RAW_MANIFEST) != upload["output_manifest"]["sha256"]:
        raise RuntimeError("raw manifest sha mismatch versus upload receipt")
    return protocol, manifest


def load_raw(manifest: dict) -> pd.DataFrame:
    expected_files = [
        "relative_index_raw_clocks_2020_warmup.csv",
        "relative_index_raw_clocks_2021.csv",
        "relative_index_raw_clocks_2022.csv",
        "relative_index_raw_clocks_2023.csv",
        "relative_index_raw_clocks_2024.csv",
        "relative_index_raw_clocks_2025.csv",
    ]
    observed = sorted(p.name for p in RAW_ROOT.glob("relative_index_raw_clocks_*.csv"))
    if observed != sorted(expected_files):
        raise RuntimeError(f"raw carrier inventory drift: {observed}")
    pieces = []
    for name in expected_files:
        path = RAW_ROOT / name
        spec = manifest["outputs"][name]
        if sha256(path) != spec["sha256"]:
            raise RuntimeError(f"raw carrier sha mismatch: {name}")
        df = pd.read_csv(path)
        if list(df.columns) != RAW_COLUMNS or int(len(df)) != int(spec["rows"]):
            raise RuntimeError(f"raw carrier schema/row drift: {name}")
        if set(df["index_name"].dropna().unique()) != set(SYMBOLS):
            raise RuntimeError(f"raw carrier index inventory drift: {name}")
        if set(df["symbol"].dropna().unique()) != set(SYMBOLS.values()):
            raise RuntimeError(f"raw carrier symbol inventory drift: {name}")
        days = pd.to_datetime(df["trading_day"], errors="raise")
        if str(days.min().date()) != spec["min_day"] or str(days.max().date()) != spec["max_day"]:
            raise RuntimeError(f"raw carrier date drift: {name}")
        pieces.append(df)
    raw = pd.concat(pieces, ignore_index=True)
    raw["trading_day"] = pd.to_datetime(raw["trading_day"], errors="raise")
    if raw.duplicated(["trading_day", "index_name"]).any():
        raise RuntimeError("duplicate raw day/index row")
    if raw["trading_day"].max() > VALID_END or raw["trading_day"].min() < pd.Timestamp("2020-11-01"):
        raise RuntimeError("raw carrier crossed frozen read boundary")
    if int(len(raw)) != int(manifest["total_rows"]):
        raise RuntimeError("raw carrier total-row drift")
    return raw.sort_values(["trading_day", "index_name"], kind="mergesort").reset_index(drop=True)


def verify_2020_parity(raw: pd.DataFrame) -> None:
    dev = pd.read_csv(DEV_2020)
    dev["trading_day"] = pd.to_datetime(dev["trading_day"], errors="raise")
    dev = dev.loc[(dev["index_name"].isin(SYMBOLS)) & (dev["trading_day"] >= pd.Timestamp("2020-11-01"))].copy()
    r = raw.loc[raw["trading_day"] <= pd.Timestamp("2020-12-31")].copy()
    keys = ["trading_day", "index_name", "symbol"]
    if set(map(tuple, dev[keys].astype(str).to_numpy())) != set(map(tuple, r[keys].astype(str).to_numpy())):
        raise RuntimeError("2020 raw/dev key inventory mismatch")
    merged = r.merge(dev, on=keys, how="inner", suffixes=("_raw", "_dev"), validate="one_to_one")
    for col in ["open_0931", "close_0935", "close_0950", "close_1005", "close_1035", "close_1500"]:
        a = pd.to_numeric(merged[f"{col}_raw"], errors="coerce")
        b = pd.to_numeric(merged[f"{col}_dev"], errors="coerce")
        if int((a.isna() ^ b.isna()).sum()) != 0:
            raise RuntimeError(f"2020 parity NaN-mask mismatch: {col}")
        both = a.notna() & b.notna()
        if both.any() and float((a[both] - b[both]).abs().max()) > PARITY_TOL:
            raise RuntimeError(f"2020 parity value mismatch: {col}")


def daily_symbol(raw: pd.DataFrame, name: str) -> pd.DataFrame:
    out = raw.loc[raw["index_name"] == name, RAW_COLUMNS].copy().sort_values("trading_day", kind="mergesort")
    out = out.set_index("trading_day")
    close = pd.to_numeric(out["close_1500"], errors="coerce")
    daily_ret = close.pct_change(fill_method=None)
    out["prev_close_1500"] = close.shift(1)
    out["r1"] = daily_ret.shift(1)
    out["rvol20"] = daily_ret.shift(1).rolling(20, min_periods=20).std()
    out["gap"] = pd.to_numeric(out["open_0931"], errors="coerce") / out["prev_close_1500"] - 1.0
    out["gap_rvol"] = out["gap"] / out["rvol20"]
    keep = ["open_0931", "close_0935", "close_0950", "close_1005", "close_1035", "close_1500", "r1", "rvol20", "gap", "gap_rvol"]
    return out[keep].add_suffix(f"_{name}").reset_index()


def build_frame(raw: pd.DataFrame) -> pd.DataFrame:
    a = daily_symbol(raw, "CSI1000")
    b = daily_symbol(raw, "CSI300")
    frame = a.merge(b, on="trading_day", how="inner", validate="one_to_one").sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    frame = frame.loc[(frame["trading_day"] >= VALID_START) & (frame["trading_day"] <= VALID_END)].copy()
    frame["size_open_leadership"] = frame["gap_rvol_CSI1000"] - frame["gap_rvol_CSI300"]
    frame["common_open_component"] = 0.5 * (frame["gap_rvol_CSI1000"] + frame["gap_rvol_CSI300"])
    frame["relative_r1"] = frame["r1_CSI1000"] - frame["r1_CSI300"]
    good = (frame["rvol20_CSI1000"] > 0) & (frame["rvol20_CSI300"] > 0)
    frame["relative_log_rvol"] = np.where(good, np.log(frame["rvol20_CSI1000"]) - np.log(frame["rvol20_CSI300"]), np.nan)
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
    protocol, manifest = verify_contract()
    raw = load_raw(manifest)
    verify_2020_parity(raw)
    frame = build_frame(raw)

    suff = protocol["sufficiency_gates"]
    sci = protocol["scientific_gates_each_horizon"]
    boot = protocol["moving_block_bootstrap"]
    insufficient = False
    all_pass = True
    for target in TARGETS:
        pooled = metrics(frame, target)
        annual = {y: metrics(frame.loc[frame["year"] == y], target) for y in range(2021, 2026)}
        target_insufficient = bool(
            pooled.get("n", 0) < int(suff["minimum_pooled_complete_cases_each_horizon"])
            or any(annual[y].get("n", 0) < int(suff["minimum_complete_cases_each_calendar_year_each_horizon"]) for y in annual)
        )
        insufficient = insufficient or target_insufficient
        if target_insufficient:
            continue
        annual_coefs = [annual[y]["std_coef"] for y in annual]
        support = bootstrap_support(frame, target, int(boot["block_length_trading_days"]), int(boot["resamples"]), int(boot["seed"]))
        target_pass = bool(
            pooled["partial_corr"] > 0
            and pooled["std_coef"] > 0
            and pooled["delta_r2"] > 0
            and sum(v > 0 for v in annual_coefs) >= int(sci["minimum_positive_calendar_year_coefficients"])
            and float(np.median(annual_coefs)) > 0
            and support >= float(str(sci["moving_block_bootstrap_positive_coefficient_support"]).replace(">=", ""))
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
        "raw_carrier_manifest_sha256": sha256(RAW_MANIFEST),
        "raw_upload_receipt_sha256": sha256(UPLOAD_RECEIPT),
        "raw_clock_2020_overlap_parity": "PASS",
        "execution_channel": "cloud_github_actions_from_minimal_raw_text_carrier",
        "validation_window": "2021-01-01..2025-12-31",
        "joint_horizons": ["15m", "30m", "60m"],
        "public_detail_release": False,
        "internal_metrics_persisted": False,
        "calendar_year_results_persisted": False,
        "bootstrap_results_persisted": False,
        "failure_attribution_persisted": False,
        "blackbox_reusable_after_query": True,
        "blackbox_consumed": False,
        "same_period_reuse_is_independent_oos": False,
        "production_authority": False,
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(decision)


if __name__ == "__main__":
    main()
