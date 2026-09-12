#!/usr/bin/env python3
"""Frozen Development diagnostic for A1 expected-open validated-driver adapter."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = "overnight_expected_open_validated_driver_coordinates_v1"
TRAIN_START = pd.Timestamp("2015-01-05")
TRAIN_END = pd.Timestamp("2018-12-31")
DEV_START = pd.Timestamp("2019-01-01")
DEV_END = pd.Timestamp("2020-12-31")
PROTOCOL = ROOT / "docs/governance/expected_open_validated_driver_coordinates_v1_protocol.json"
STATE = ROOT / "docs/governance/expected_open_validated_driver_coordinates_v1_state.json"
AUTHORITY = ROOT / "docs/governance/current_authority_v1.json"
LEDGER = ROOT / "docs/governance/overnight_reusable_blackbox_query_ledger_v1.json"
PANEL = ROOT / "data/development/csi1000_open_pit_panel.parquet"
NASDAQ = ROOT / "data/high_open_dev_2015_2025/fred_nasdaq.csv"
VIX = ROOT / "data/high_open_dev_2015_2025/fred_vix.csv"
HKMA = ROOT / "data/v6a_external_sources_2015_2025/hkma_usdcny_cross.parquet"
HOLIDAY_A50 = ROOT / "data/v6a_external_sources_2015_2025/sgx_a50_holiday_endpoints.parquet"
ORDINARY_A50 = ROOT / "data/v6a_external_sources_2015_2025/sgx_a50_ordinary_preauction_endpoints.parquet"
EXTERNAL_MANIFEST = ROOT / "data/v6a_external_sources_2015_2025/manifest.json"
OUTPUT = ROOT / "docs/research/cloud_expected_open_validated_driver_coordinates_v1_dev_diagnostic.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_v6a_module():
    path = ROOT / "scripts/run_v6a_reusable_blackbox_local.py"
    spec = importlib.util.spec_from_file_location("v6a_frozen_model_authority", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen V6A implementation")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trailing_rms_prev(series: pd.Series) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    return np.sqrt(x.pow(2).shift(1).rolling(window=60, min_periods=20).mean())


def corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.nanstd(a) == 0 or np.nanstd(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    sse = float(np.sum((y - p) ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "sse": sse,
        "r2": float("nan") if sst <= 0 else 1.0 - sse / sst,
        "ic": corr(y, p),
        "sign_accuracy": float(np.mean((p >= 0) == (y >= 0))),
    }


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray]:
    pipe = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
    pipe.fit(train[features].to_numpy(float), train["gap"].to_numpy(float))
    return test["gap"].to_numpy(float), pipe.predict(test[features].to_numpy(float))


def verify_contracts(v6a) -> dict:
    protocol = read_json(PROTOCOL)
    state = read_json(STATE)
    authority = read_json(AUTHORITY)
    ledger = read_json(LEDGER)
    external = read_json(EXTERNAL_MANIFEST)

    if protocol.get("research_identity") != IDENTITY or state.get("research_identity") != IDENTITY:
        raise RuntimeError("A1 identity drift")
    if state.get("outcome_opened") is not False:
        raise RuntimeError("A1 outcome already opened")
    if (authority.get("active_research") or {}).get("identity") != IDENTITY:
        raise RuntimeError("A1 is not current active research")
    if ledger.get("query_count") != 11:
        raise RuntimeError("unexpected BLACKBOX ledger count before A1 Development")
    if protocol.get("estimator") != "StandardScaler + Ridge(alpha=1.0)" or protocol.get("target") != "gap":
        raise RuntimeError("A1 estimator/target drift")
    if protocol.get("training_window") != "2015-01-05..2018-12-31" or protocol.get("development_evaluation_window") != "2019-01-01..2020-12-31":
        raise RuntimeError("A1 evidence window drift")
    expected_baseline = list(v6a.V6_FEATURES)
    if protocol.get("baseline_features") != expected_baseline:
        raise RuntimeError("A1 V6A baseline feature drift")
    if protocol.get("candidate_additions") != ["global_risk_z", "china_offshore_z"]:
        raise RuntimeError("A1 candidate additions drift")
    if protocol.get("common_sample_rule") != "fit_and_evaluate_baseline_and_candidate_on_candidate_complete_common_sample":
        raise RuntimeError("A1 common-sample rule drift")
    upstream = protocol.get("validated_upstream_products", {})
    queries = {int(q["ordinal"]): q for q in ledger.get("queries", [])}
    if queries.get(8, {}).get("query_id") != upstream.get("B1", {}).get("query_id") or queries.get(8, {}).get("decision") != "PASS":
        raise RuntimeError("validated B1 authority missing")
    if queries.get(9, {}).get("query_id") != upstream.get("B2", {}).get("query_id") or queries.get(9, {}).get("decision") != "PASS":
        raise RuntimeError("validated B2 authority missing")
    required_assertions = [
        "same_contract_all_events", "no_future_volume_or_oi_selection", "no_mid_window_roll",
        "no_forward_fill_or_interpolation", "blackbox_not_used_for_fit_or_rule_selection",
    ]
    if not all(external.get("assertions", {}).get(k) is True for k in required_assertions):
        raise RuntimeError("external-source governance assertions fail")
    return protocol


def assemble_development(v6a) -> tuple[pd.DataFrame, dict]:
    panel = pd.read_parquet(PANEL).copy()
    panel["trading_day"] = pd.to_datetime(panel["trading_day"], errors="raise").dt.normalize()
    panel = panel.loc[panel["trading_day"].between(TRAIN_START, DEV_END)].copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if panel.empty or panel["trading_day"].min() != TRAIN_START or panel["trading_day"].max() != DEV_END:
        raise RuntimeError("A1 development panel boundary drift")
    if panel["trading_day"].duplicated().any():
        raise RuntimeError("duplicate A1 trading day")

    # Restrict U.S. source observations to the open Development boundary before assembly.
    nasdaq = v6a.read_fred(NASDAQ, "NASDAQCOM")
    vix = v6a.read_fred(VIX, "VIXCLS")
    nasdaq = nasdaq.loc[nasdaq["date"].le(DEV_END)].copy()
    vix = vix.loc[vix["date"].le(DEV_END)].copy()
    df = v6a.add_us_complete_clock(panel, nasdaq, vix)

    # The panel itself is bounded to 2020. The external pack is immutable; merging by panel trading_day
    # cannot materialize any post-2020 research row.
    df = v6a.add_hkma(df, HKMA)
    df, ordinary_coverage_unused, clocks_ok = v6a.attach_a50(df, HOLIDAY_A50, ORDINARY_A50)
    if not clocks_ok:
        raise RuntimeError("A1 A50 causal clock integrity failed")

    holiday = pd.to_numeric(df["holiday_reopen"], errors="coerce").fillna(0).ne(0)
    df["a50_channel_return"] = np.where(
        holiday,
        pd.to_numeric(df["a50_holiday_closure_return"], errors="coerce"),
        pd.to_numeric(df["a50_ordinary_preauction_closure_return"], errors="coerce"),
    )

    for raw in ["us_nasdaq", "us_vix_chg", "a50_channel_return"]:
        df[raw] = pd.to_numeric(df[raw], errors="coerce")
        df[f"{raw}_rms60_prev"] = trailing_rms_prev(df[raw])
    df["nasdaq_risk_z"] = df["us_nasdaq"] / df["us_nasdaq_rms60_prev"]
    df["vix_risk_z"] = -df["us_vix_chg"] / df["us_vix_chg_rms60_prev"]
    df["global_risk_z"] = 0.5 * (df["nasdaq_risk_z"] + df["vix_risk_z"])
    df["china_offshore_z"] = df["a50_channel_return"] / df["a50_channel_return_rms60_prev"]

    integrity = {
        "panel": {"path": str(PANEL.relative_to(ROOT)), "sha256": sha256(PANEL)},
        "external_manifest": {"path": str(EXTERNAL_MANIFEST.relative_to(ROOT)), "sha256": sha256(EXTERNAL_MANIFEST)},
        "V6A_implementation": {"path": "scripts/run_v6a_reusable_blackbox_local.py", "sha256": sha256(ROOT / "scripts/run_v6a_reusable_blackbox_local.py")},
        "post_2020_research_rows_materialized": False,
    }
    return df, integrity


def main() -> int:
    if OUTPUT.exists():
        raise RuntimeError(f"refusing to overwrite A1 Development receipt: {OUTPUT}")
    v6a = load_v6a_module()
    protocol = verify_contracts(v6a)
    df, integrity = assemble_development(v6a)

    baseline = list(protocol["baseline_features"])
    candidate_features = [*baseline, *protocol["candidate_additions"]]
    complete_cols = [*candidate_features, "gap"]
    numeric = df[complete_cols].apply(pd.to_numeric, errors="coerce")
    common = numeric.notna().all(axis=1) & np.isfinite(numeric.to_numpy(float)).all(axis=1) & df["a50_common_available"].fillna(False).astype(bool)
    common_df = df.loc[common].copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)

    train = common_df.loc[common_df["trading_day"].between(TRAIN_START, TRAIN_END)].copy()
    dev = common_df.loc[common_df["trading_day"].between(DEV_START, DEV_END)].copy()
    suff = protocol["sufficiency_gates"]
    year_counts = {str(y): int(dev["trading_day"].dt.year.eq(y).sum()) for y in (2019, 2020)}
    sufficient = (
        len(train) >= int(suff["training_common_complete_cases_min"])
        and all(year_counts[str(y)] >= int(suff["each_evaluation_year_common_complete_cases_min"]) for y in (2019, 2020))
    )

    diagnostics: dict[str, object] = {
        "training_common_complete_cases": int(len(train)),
        "evaluation_common_complete_cases": int(len(dev)),
        "evaluation_year_common_complete_cases": year_counts,
    }
    if not sufficient:
        decision = "A1_VALIDATED_DRIVER_ADAPTER_DEV_INSUFFICIENT"
        gates = {"sufficiency_pass": False}
    else:
        y0, p0 = fit_predict(train, dev, baseline)
        y1, p1 = fit_predict(train, dev, candidate_features)
        if not np.array_equal(y0, y1):
            raise RuntimeError("A1 baseline/candidate common-sample target mismatch")
        pooled0, pooled1 = metrics(y0, p0), metrics(y1, p1)
        annual: dict[str, dict[str, dict[str, float]]] = {}
        annual_sse_wins = 0
        annual_ic_not_below = 0
        annual_sign_ok = 0
        for year in (2019, 2020):
            mask = dev["trading_day"].dt.year.eq(year).to_numpy()
            m0, m1 = metrics(y0[mask], p0[mask]), metrics(y1[mask], p1[mask])
            annual[str(year)] = {"comparator": m0, "candidate": m1}
            annual_sse_wins += int(m1["sse"] < m0["sse"])
            annual_ic_not_below += int(np.isfinite(m1["ic"]) and np.isfinite(m0["ic"]) and m1["ic"] >= m0["ic"])
            annual_sign_ok += int(m1["sign_accuracy"] >= m0["sign_accuracy"] - float(protocol["progression_gates"]["each_evaluation_year_candidate_sign_accuracy_not_below_comparator_minus"]))
        diagnostics.update({"pooled": {"comparator": pooled0, "candidate": pooled1}, "by_year": annual})
        pg = protocol["progression_gates"]
        gates = {
            "sufficiency_pass": True,
            "pooled_candidate_sse_below_comparator": bool(pooled1["sse"] < pooled0["sse"]),
            "pooled_candidate_r2_above_comparator": bool(pooled1["r2"] > pooled0["r2"]),
            "pooled_candidate_ic_not_below_comparator": bool(np.isfinite(pooled1["ic"]) and np.isfinite(pooled0["ic"]) and pooled1["ic"] >= pooled0["ic"]),
            "pooled_candidate_sign_accuracy_not_below_comparator_minus_tolerance": bool(pooled1["sign_accuracy"] >= pooled0["sign_accuracy"] - float(pg["pooled_candidate_sign_accuracy_not_below_comparator_minus"])),
            "evaluation_years_candidate_sse_below_comparator_count": int(annual_sse_wins),
            "evaluation_years_candidate_sse_below_comparator_min_pass": bool(annual_sse_wins >= int(pg["evaluation_years_candidate_sse_below_comparator_min"])),
            "evaluation_years_candidate_ic_not_below_comparator_count": int(annual_ic_not_below),
            "evaluation_years_candidate_ic_not_below_comparator_min_pass": bool(annual_ic_not_below >= int(pg["evaluation_years_candidate_ic_not_below_comparator_min"])),
            "evaluation_years_candidate_sign_accuracy_within_tolerance_count": int(annual_sign_ok),
            "each_evaluation_year_candidate_sign_accuracy_within_tolerance_pass": bool(annual_sign_ok == 2),
        }
        progression = all(gates[k] for k in [
            "pooled_candidate_sse_below_comparator", "pooled_candidate_r2_above_comparator",
            "pooled_candidate_ic_not_below_comparator", "pooled_candidate_sign_accuracy_not_below_comparator_minus_tolerance",
            "evaluation_years_candidate_sse_below_comparator_min_pass", "evaluation_years_candidate_ic_not_below_comparator_min_pass",
            "each_evaluation_year_candidate_sign_accuracy_within_tolerance_pass",
        ])
        decision = "A1_VALIDATED_DRIVER_ADAPTER_DEV_PROGRESS" if progression else "A1_VALIDATED_DRIVER_ADAPTER_DEV_NO_PROGRESS"

    payload = {
        "schema_id": "overnight_expected_open_validated_driver_coordinates_dev_diagnostic@1.0",
        "session_date": "2026-09-12",
        "research_identity": IDENTITY,
        "product_family": "OFP-A1_expected_open_state",
        "training_window": "2015-01-05..2018-12-31",
        "development_evaluation_window": "2019-01-01..2020-12-31",
        "comparator": "V6A_model_refit_on_candidate_common_sample",
        "candidate": "V6A_plus_validated_B1_B2_coordinates",
        "target": "gap",
        "diagnostics": diagnostics,
        "progression_gate_components": gates,
        "decision": decision,
        "source_integrity": integrity,
        "protocol": {"path": str(PROTOCOL.relative_to(ROOT)), "sha256": sha256(PROTOCOL)},
        "candidate_attempt_count": 1,
        "ridge_alpha_search": False,
        "upstream_add_drop_search": False,
        "interaction_search": False,
        "threshold_search": False,
        "bucket_search": False,
        "clock_search": False,
        "target_search": False,
        "strategy_PnL_optimization": False,
        "2021_2025_research_rows_opened": False,
        "reusable_blackbox_query_created": False,
        "production_authority": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("A1_VALIDATED_DRIVER_ADAPTER_DEV_DIAGNOSTIC_COMPLETE")
    print(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
