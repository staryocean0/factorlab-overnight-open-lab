#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CARRIER = ROOT / "data/relative_index_runtime_text_2015_2020"
MANIFEST = CARRIER / "manifest.json"
PROTOCOL = ROOT / "docs/governance/relative_index_open_leadership_v1_protocol.json"
RECEIPT = ROOT / "docs/research/cloud_relative_index_open_leadership_dev_diagnostic_v1.json"
YEARS = list(range(2015, 2021))
BASELINE = ["common_open_component", "relative_r1", "relative_log_rvol"]
TARGETS = ["relative_ret_0935_0950", "relative_ret_0935_1005", "relative_ret_0935_1035"]
EXPECTED_IDENTITY = "overnight_relative_size_open_leadership_v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ols_r2(y: np.ndarray, x: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    X = np.column_stack([np.ones(len(y)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    resid = y - fit
    sse = float(resid @ resid)
    centered = y - y.mean()
    sst = float(centered @ centered)
    r2 = float(1.0 - sse / sst) if sst > 0 else float("nan")
    return r2, beta, resid


def residualize(v: np.ndarray, x: np.ndarray) -> np.ndarray:
    X = np.column_stack([np.ones(len(v)), x])
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    return v - X @ beta


def zscore(a: np.ndarray) -> np.ndarray:
    sd = a.std(axis=0, ddof=0)
    if np.ndim(sd) == 0:
        if not np.isfinite(sd) or sd <= 0:
            raise RuntimeError("zero/nonfinite standard deviation")
    else:
        if np.any(~np.isfinite(sd)) or np.any(sd <= 0):
            raise RuntimeError("zero/nonfinite standard deviation")
    return (a - a.mean(axis=0)) / sd


def evaluate(frame: pd.DataFrame, target: str) -> dict:
    cols = BASELINE + ["size_open_leadership", target]
    part = frame[cols].apply(pd.to_numeric, errors="coerce")
    mask = np.isfinite(part.to_numpy(dtype=float)).all(axis=1)
    part = part.loc[mask]
    n = int(len(part))
    if n < 4:
        raise RuntimeError(f"insufficient rows for {target}: {n}")
    b = part[BASELINE].to_numpy(dtype=float)
    c = part["size_open_leadership"].to_numpy(dtype=float)
    y = part[target].to_numpy(dtype=float)

    baseline_r2, _, _ = ols_r2(y, b)
    full_x = np.column_stack([b, c])
    candidate_r2, _, _ = ols_r2(y, full_x)
    ry = residualize(y, b)
    rc = residualize(c, b)
    if np.std(ry, ddof=0) <= 0 or np.std(rc, ddof=0) <= 0:
        partial_corr = float("nan")
    else:
        partial_corr = float(np.corrcoef(ry, rc)[0, 1])

    yz = zscore(y)
    xz = zscore(full_x)
    _, beta_z, _ = ols_r2(yz, xz)
    std_coef = float(beta_z[-1])
    return {
        "complete_case_count": n,
        "baseline_r2": float(baseline_r2),
        "candidate_r2": float(candidate_r2),
        "delta_r2": float(candidate_r2 - baseline_r2),
        "partial_correlation_after_baseline_residualization": partial_corr,
        "standardized_candidate_coefficient": std_coef,
    }


def build_frame() -> tuple[pd.DataFrame, dict]:
    protocol = load_json(PROTOCOL)
    manifest = load_json(MANIFEST)
    if protocol.get("research_identity") != EXPECTED_IDENTITY:
        raise RuntimeError("unexpected D1 identity")
    if protocol.get("candidate_increment") != ["size_open_leadership"]:
        raise RuntimeError("candidate drift")
    if protocol.get("baseline_controls") != BASELINE:
        raise RuntimeError("baseline drift")
    if protocol.get("targets") != TARGETS:
        raise RuntimeError("target drift")
    if manifest.get("published_window") != "2015-01-05..2020-12-31":
        raise RuntimeError("carrier boundary drift")
    if manifest.get("transform", {}).get("2021_2025_row_level_text_generated") is not False:
        raise RuntimeError("post-2020 text exposure detected")
    if manifest.get("D1_v1_candidate_indices") != ["CSI1000", "CSI300"]:
        raise RuntimeError("candidate index drift")

    files = sorted(CARRIER.glob("relative_index_open_carrier_*.csv"))
    expected_names = [f"relative_index_open_carrier_{y}.csv" for y in YEARS]
    if [p.name for p in files] != expected_names:
        raise RuntimeError(f"unexpected carrier file inventory: {[p.name for p in files]}")

    pieces = []
    integrity = {}
    for year in YEARS:
        path = CARRIER / f"relative_index_open_carrier_{year}.csv"
        spec = manifest["outputs"][str(year)]
        observed_sha = sha256(path)
        if observed_sha != spec["sha256"]:
            raise RuntimeError(f"sha mismatch {path.name}")
        df = pd.read_csv(path)
        if int(len(df)) != int(spec["rows"]):
            raise RuntimeError(f"row count mismatch {path.name}")
        if not set(df["index_name"].dropna().unique()).issubset({"CSI1000", "CSI300", "CSI500"}):
            raise RuntimeError(f"unexpected index in {path.name}")
        days = pd.to_datetime(df["trading_day"], errors="raise")
        if int(days.dt.year.min()) != year or int(days.dt.year.max()) != year:
            raise RuntimeError(f"year boundary mismatch {path.name}")
        integrity[str(year)] = {"sha256": observed_sha, "rows": int(len(df))}
        pieces.append(df)

    raw = pd.concat(pieces, ignore_index=True)
    raw["trading_day"] = raw["trading_day"].astype(str)
    raw = raw.loc[raw["index_name"].isin(["CSI1000", "CSI300"])].copy()
    if raw.duplicated(["trading_day", "index_name"]).any():
        raise RuntimeError("duplicate day/index rows")

    value_cols = ["gap_rvol", "r1", "rvol20", "close_0935", "close_0950", "close_1005", "close_1035"]
    wide = raw.pivot(index="trading_day", columns="index_name", values=value_cols)
    out = pd.DataFrame(index=wide.index)
    for idx in ["CSI1000", "CSI300"]:
        for col in value_cols:
            out[f"{col}_{idx}"] = pd.to_numeric(wide[(col, idx)], errors="coerce")

    out["size_open_leadership"] = out["gap_rvol_CSI1000"] - out["gap_rvol_CSI300"]
    out["common_open_component"] = 0.5 * (out["gap_rvol_CSI1000"] + out["gap_rvol_CSI300"])
    out["relative_r1"] = out["r1_CSI1000"] - out["r1_CSI300"]
    valid_rvol = (out["rvol20_CSI1000"] > 0) & (out["rvol20_CSI300"] > 0)
    out["relative_log_rvol"] = np.where(
        valid_rvol,
        np.log(out["rvol20_CSI1000"]) - np.log(out["rvol20_CSI300"]),
        np.nan,
    )
    for clock in ["0950", "1005", "1035"]:
        r1000 = out[f"close_{clock}_CSI1000"] / out["close_0935_CSI1000"] - 1.0
        r300 = out[f"close_{clock}_CSI300"] / out["close_0935_CSI300"] - 1.0
        out[f"relative_ret_0935_{clock}"] = r1000 - r300
    out = out.reset_index()
    out["year"] = pd.to_datetime(out["trading_day"]).dt.year.astype(int)
    if int(out["year"].min()) != 2015 or int(out["year"].max()) != 2020:
        raise RuntimeError("D1 frame crossed development boundary")
    return out, integrity


def gate_summary(pooled: dict, annual: dict[str, dict], protocol: dict) -> dict:
    pc = float(pooled["partial_correlation_after_baseline_residualization"])
    coef = float(pooled["standardized_candidate_coefficient"])
    pooled_sign = int(np.sign(coef))
    same_pooled_sign = bool(np.sign(pc) == pooled_sign and pooled_sign != 0)
    annual_coefs = [float(annual[str(y)]["standardized_candidate_coefficient"]) for y in YEARS]
    annual_same = int(sum(int(np.sign(v) == pooled_sign and np.sign(v) != 0) for v in annual_coefs))
    annual_median = float(np.median(annual_coefs))
    annual_delta_positive = int(sum(float(annual[str(y)]["delta_r2"]) > 0 for y in YEARS))
    min_n = int(min(int(annual[str(y)]["complete_case_count"]) for y in YEARS))
    gates = {
        "pooled_partial_corr_and_standardized_coefficient_same_sign": same_pooled_sign,
        "annual_coefficient_same_sign_count": annual_same,
        "annual_coefficient_same_sign_count_pass": annual_same >= int(protocol["progression_gate"]["minimum_annual_coefficient_same_sign_count"]),
        "annual_median_coefficient": annual_median,
        "annual_median_coefficient_same_sign_as_pooled": bool(np.sign(annual_median) == pooled_sign and pooled_sign != 0),
        "pooled_delta_r2_positive": bool(float(pooled["delta_r2"]) > 0),
        "annual_positive_delta_r2_count": annual_delta_positive,
        "annual_positive_delta_r2_count_pass": annual_delta_positive >= int(protocol["progression_gate"]["minimum_annual_positive_delta_r2_count"]),
        "minimum_complete_case_count_each_year_observed": min_n,
        "minimum_complete_case_count_each_year_pass": min_n >= int(protocol["progression_gate"]["minimum_complete_case_count_each_year"]),
    }
    gates["all_preregistered_progression_gates_pass"] = bool(
        gates["pooled_partial_corr_and_standardized_coefficient_same_sign"]
        and gates["annual_coefficient_same_sign_count_pass"]
        and gates["annual_median_coefficient_same_sign_as_pooled"]
        and gates["pooled_delta_r2_positive"]
        and gates["annual_positive_delta_r2_count_pass"]
        and gates["minimum_complete_case_count_each_year_pass"]
    )
    return gates


def main() -> None:
    if RECEIPT.exists():
        raise RuntimeError(f"refusing to overwrite existing receipt: {RECEIPT}")
    protocol = load_json(PROTOCOL)
    frame, integrity = build_frame()
    results = {}
    for target in TARGETS:
        annual = {str(y): evaluate(frame.loc[frame["year"] == y].copy(), target) for y in YEARS}
        pooled = evaluate(frame.copy(), target)
        results[target] = {
            "pooled": pooled,
            "annual": annual,
            "progression_gate_components": gate_summary(pooled, annual, protocol),
        }

    payload = {
        "schema_id": "overnight_relative_index_open_leadership_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": EXPECTED_IDENTITY,
        "product_family": "OFP-D1_relative_index_open",
        "development_window": "2015-01-05..2020-12-31",
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "carrier_manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha256(MANIFEST)},
        "carrier_file_integrity": integrity,
        "candidate": "gap_rvol_CSI1000 - gap_rvol_CSI300",
        "baseline_controls": BASELINE,
        "targets": TARGETS,
        "results": results,
        "multiple_passing_horizons_rule": "retain_jointly_no_posthoc_unique_winner",
        "CSI500_candidate_search": False,
        "pairwise_index_search": False,
        "threshold_search": False,
        "alternate_horizon_search": False,
        "strategy_return_optimization": False,
        "2021_2025_blackbox_opened": False,
        "post_2020_detailed_rows_loaded": False,
        "auto_promotion": False,
        "production_authority": False,
    }
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("D1_RELATIVE_INDEX_DEV_DIAGNOSTIC_COMPLETE")


if __name__ == "__main__":
    main()
