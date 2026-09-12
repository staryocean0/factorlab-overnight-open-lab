#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/governance/previous_session_last_hour_conditioned_open_state_joint_30m_60m_blackbox_protocol_v1.json"
RECEIPT = ROOT / "docs/research/local_previous_session_last_hour_conditioned_open_state_joint_blackbox_receipt_v1.json"

D1_RAW_ROOT = ROOT / "data/relative_index_blackbox_raw_text_2020_2025"
D1_RAW_MANIFEST = D1_RAW_ROOT / "manifest.json"
D1_RAW_UPLOAD = ROOT / "docs/research/relative_index_blackbox_raw_text_upload_receipt_v1.json"
SUP_ROOT = ROOT / "data/c3_blackbox_raw_1400_2020_2025"
SUP_FILE = SUP_ROOT / "csi1000_close_1400_2020_2025.csv"
SUP_MANIFEST = SUP_ROOT / "manifest.json"
SUP_UPLOAD = ROOT / "docs/research/c3_blackbox_raw_1400_upload_receipt_v1.json"
DEV_FACTOR_2020 = ROOT / "data/runtime_text_2015_2025/factor_panel_2020.csv"

IDENTITY = "overnight_previous_session_last_hour_conditioned_open_state_joint_30m_60m_v1"
SYMBOL = "000852.SH"
BASELINE = [
    "observed_gap_rvol",
    "last_hour_rvol",
    "prev_daytime",
    "trend20_rvol",
    "trend_gap_interaction",
    "log_rvol20",
    "r1",
    "holiday_reopen",
]
TARGETS = ["ret_0935_1005", "ret_0935_1035"]
D1_REQUIRED = ["trading_day", "index_name", "symbol", "open_0931", "close_0935", "close_1005", "close_1035", "close_1500"]
SUP_COLUMNS = ["trading_day", "index_name", "symbol", "close_1400"]
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
    cols = BASELINE + ["last_hour_gap_interaction", target]
    xdf = part[cols].apply(pd.to_numeric, errors="coerce")
    xdf = xdf.loc[np.isfinite(xdf.to_numpy(dtype=float)).all(axis=1)]
    if len(xdf) < 4:
        return {"n": float(len(xdf))}
    b = xdf[BASELINE].to_numpy(dtype=float)
    c = xdf["last_hour_gap_interaction"].to_numpy(dtype=float)
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
    cols = BASELINE + ["last_hour_gap_interaction", target]
    xdf = part[cols].apply(pd.to_numeric, errors="coerce")
    xdf = xdf.loc[np.isfinite(xdf.to_numpy(dtype=float)).all(axis=1)]
    if len(xdf) < 4:
        return float("nan")
    full = xdf[BASELINE + ["last_hour_gap_interaction"]].to_numpy(dtype=float)
    y = xdf[target].to_numpy(dtype=float)
    _, beta_z = ols_r2_beta(zscore(y), zscore(full))
    return float(beta_z[-1])


def bootstrap_support(part: pd.DataFrame, target: str, block: int, reps: int, seed: int) -> float:
    cols = BASELINE + ["last_hour_gap_interaction", target]
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


def verify_protocol() -> dict:
    p = load_json(PROTOCOL)
    if p.get("research_identity") != IDENTITY:
        raise RuntimeError("identity drift")
    if p.get("candidate_increment") != ["last_hour_gap_interaction"]:
        raise RuntimeError("candidate drift")
    if p.get("baseline_controls") != BASELINE:
        raise RuntimeError("baseline drift")
    if [x["id"] for x in p.get("targets", [])] != TARGETS:
        raise RuntimeError("target drift")
    if p.get("frozen_direction") != "positive":
        raise RuntimeError("direction drift")
    return p


def load_d1_raw(protocol: dict) -> pd.DataFrame:
    manifest = load_json(D1_RAW_MANIFEST)
    upload = load_json(D1_RAW_UPLOAD)
    if manifest.get("source_dataset_sha256") != protocol["source_dataset"]["sha256"]:
        raise RuntimeError("D1 raw physical source mismatch")
    if upload.get("BLACKBOX_controller_run") is not False or upload.get("D1_regression_run") is not False:
        raise RuntimeError("D1 raw upload boundary drift")
    if sha256(D1_RAW_MANIFEST) != upload["output_manifest"]["sha256"]:
        raise RuntimeError("D1 raw manifest sha mismatch")
    files = [
        "relative_index_raw_clocks_2020_warmup.csv",
        "relative_index_raw_clocks_2021.csv",
        "relative_index_raw_clocks_2022.csv",
        "relative_index_raw_clocks_2023.csv",
        "relative_index_raw_clocks_2024.csv",
        "relative_index_raw_clocks_2025.csv",
    ]
    pieces = []
    for name in files:
        path = D1_RAW_ROOT / name
        spec = manifest["outputs"][name]
        if sha256(path) != spec["sha256"]:
            raise RuntimeError(f"D1 raw sha mismatch: {name}")
        df = pd.read_csv(path)
        if int(len(df)) != int(spec["rows"]):
            raise RuntimeError(f"D1 raw row mismatch: {name}")
        df = df.loc[(df["index_name"] == "CSI1000") & (df["symbol"] == SYMBOL), D1_REQUIRED].copy()
        pieces.append(df)
    out = pd.concat(pieces, ignore_index=True)
    out["trading_day"] = pd.to_datetime(out["trading_day"], errors="raise")
    if out.duplicated(["trading_day"]).any():
        raise RuntimeError("duplicate CSI1000 day in reused raw carrier")
    return out.sort_values("trading_day", kind="mergesort").reset_index(drop=True)


def load_supplement(protocol: dict) -> pd.DataFrame:
    manifest = load_json(SUP_MANIFEST)
    upload = load_json(SUP_UPLOAD)
    if manifest.get("research_identity") != IDENTITY:
        raise RuntimeError("supplement identity drift")
    if manifest.get("source_dataset_sha256") != protocol["source_dataset"]["sha256"]:
        raise RuntimeError("supplement source drift")
    if manifest.get("read_window") != {"start": "2020-11-01", "end": "2025-12-31"}:
        raise RuntimeError("supplement read-window drift")
    if manifest.get("symbol") != SYMBOL or manifest.get("exact_clock") != "14:00" or manifest.get("columns") != SUP_COLUMNS:
        raise RuntimeError("supplement schema drift")
    transform = manifest.get("transform", {})
    if transform.get("exact_clock_filter_only") is not True:
        raise RuntimeError("supplement not exact-clock-only")
    for k in ["feature_engineering", "target_engineering", "scientific_analysis", "forward_fill", "backward_fill", "nearest_clock_substitution", "resampling"]:
        if transform.get(k) is not False:
            raise RuntimeError(f"supplement transform drift: {k}")
    if upload.get("BLACKBOX_controller_run") is not False or upload.get("scientific_diagnostic_performed") is not False:
        raise RuntimeError("supplement upload crossed scientific boundary")
    if sha256(SUP_MANIFEST) != upload["output_manifest"]["sha256"]:
        raise RuntimeError("supplement manifest sha mismatch")
    spec = manifest["output"]
    if sha256(SUP_FILE) != spec["sha256"]:
        raise RuntimeError("supplement file sha mismatch")
    df = pd.read_csv(SUP_FILE)
    if list(df.columns) != SUP_COLUMNS or int(len(df)) != int(spec["rows"]):
        raise RuntimeError("supplement schema/row drift")
    if set(df["index_name"].dropna().unique()) != {"CSI1000"} or set(df["symbol"].dropna().unique()) != {SYMBOL}:
        raise RuntimeError("supplement index/symbol drift")
    df["trading_day"] = pd.to_datetime(df["trading_day"], errors="raise")
    if df.duplicated(["trading_day"]).any():
        raise RuntimeError("duplicate supplement day")
    if str(df["trading_day"].min().date()) != spec["min_day"] or str(df["trading_day"].max().date()) != spec["max_day"]:
        raise RuntimeError("supplement date drift")
    return df


def build_all_daily(raw: pd.DataFrame, sup: pd.DataFrame) -> pd.DataFrame:
    frame = raw.merge(sup[["trading_day", "close_1400"]], on="trading_day", how="inner", validate="one_to_one")
    frame = frame.sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    close = pd.to_numeric(frame["close_1500"], errors="coerce")
    open0931 = pd.to_numeric(frame["open_0931"], errors="coerce")
    close1400 = pd.to_numeric(frame["close_1400"], errors="coerce")
    daily_ret = close.pct_change(fill_method=None)
    frame["gap"] = open0931 / close.shift(1) - 1.0
    frame["r1"] = close.shift(1) / close.shift(2) - 1.0
    frame["r20"] = close.shift(1) / close.shift(21) - 1.0
    frame["rvol20"] = daily_ret.shift(1).rolling(20, min_periods=20).std()
    daytime = close / open0931 - 1.0
    last_hour = close / close1400 - 1.0
    frame["prev_daytime"] = daytime.shift(1)
    frame["prev_last_hour"] = last_hour.shift(1)
    cal_gap = frame["trading_day"].diff().dt.days
    frame["holiday_reopen"] = (cal_gap >= 4).astype(float)
    frame["observed_gap_rvol"] = frame["gap"] / frame["rvol20"]
    frame["last_hour_rvol"] = frame["prev_last_hour"] / frame["rvol20"]
    frame["trend20_rvol"] = frame["r20"] / (np.sqrt(20.0) * frame["rvol20"])
    frame["trend_gap_interaction"] = frame["observed_gap_rvol"] * frame["trend20_rvol"]
    frame["log_rvol20"] = np.where(frame["rvol20"] > 0, np.log(frame["rvol20"]), np.nan)
    frame["last_hour_gap_interaction"] = frame["last_hour_rvol"] * frame["observed_gap_rvol"]
    frame["ret_0935_1005"] = pd.to_numeric(frame["close_1005"], errors="coerce") / pd.to_numeric(frame["close_0935"], errors="coerce") - 1.0
    frame["ret_0935_1035"] = pd.to_numeric(frame["close_1035"], errors="coerce") / pd.to_numeric(frame["close_0935"], errors="coerce") - 1.0
    frame["year"] = frame["trading_day"].dt.year.astype(int)
    return frame


def verify_2020_factor_parity(frame: pd.DataFrame) -> None:
    dev = pd.read_csv(DEV_FACTOR_2020)
    dev["trading_day"] = pd.to_datetime(dev["trading_day"], errors="raise")
    dev = dev.loc[dev["trading_day"] >= pd.Timestamp("2020-11-01")].set_index("trading_day")
    cur = frame.loc[frame["trading_day"] <= pd.Timestamp("2020-12-31")].set_index("trading_day")
    common = dev.index.intersection(cur.index)
    if len(common) < 20:
        raise RuntimeError("insufficient 2020 overlap for technical parity")
    for col in ["gap", "r1", "r20", "rvol20", "prev_daytime", "prev_last_hour", "holiday_reopen"]:
        a = pd.to_numeric(cur.loc[common, col], errors="coerce")
        b = pd.to_numeric(dev.loc[common, col], errors="coerce")
        mask = a.notna() & b.notna()
        minimum = 15 if col in {"r20", "rvol20"} else 20
        if int(mask.sum()) < minimum:
            raise RuntimeError(f"insufficient comparable 2020 parity rows: {col}")
        if float((a[mask] - b[mask]).abs().max()) > PARITY_TOL:
            raise RuntimeError(f"2020 factor reconstruction drift: {col}")


def main() -> None:
    if RECEIPT.exists():
        raise RuntimeError("refusing to overwrite existing compact receipt")
    protocol = verify_protocol()
    raw = load_d1_raw(protocol)
    sup = load_supplement(protocol)
    frame_all = build_all_daily(raw, sup)
    verify_2020_factor_parity(frame_all)
    frame = frame_all.loc[(frame_all["trading_day"] >= VALID_START) & (frame_all["trading_day"] <= VALID_END)].copy()
    if not set(frame["year"].unique()).issubset({2021, 2022, 2023, 2024, 2025}):
        raise RuntimeError("C3 validation frame crossed 2021-2025")

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
            and support >= 0.90
        )
        all_pass = all_pass and target_pass

    decision = "INSUFFICIENT" if insufficient else ("PASS" if all_pass else "FAIL")
    protocol_sha = sha256(PROTOCOL)
    source_sha = str(protocol["source_dataset"]["sha256"])
    query_id = hashlib.sha256(f"{IDENTITY}|{protocol_sha}|{source_sha}".encode()).hexdigest()[:20]
    receipt = {
        "schema_id": "overnight_previous_session_last_hour_conditioned_open_state_joint_blackbox_receipt@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "parent_development_identity": "overnight_previous_session_last_hour_conditioned_open_state_v1",
        "product_family": "OFP-C3_previous_china_session_shape_x_OFP-A2_observed_open_geometry",
        "decision": decision,
        "query_id": query_id,
        "protocol_sha256": protocol_sha,
        "source_dataset_sha256": source_sha,
        "reused_D1_raw_manifest_sha256": sha256(D1_RAW_MANIFEST),
        "supplemental_1400_manifest_sha256": sha256(SUP_MANIFEST),
        "factor_reconstruction_2020_overlap_parity": "PASS",
        "execution_channel": "cloud_from_reused_raw_clocks_plus_minimal_1400_supplement",
        "validation_window": "2021-01-01..2025-12-31",
        "joint_horizons": ["30m", "60m"],
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
