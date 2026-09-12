#!/usr/bin/env python3
"""V21-RD1 consumed-evidence regime diagnostic.

Uses only already-consumed CSI300/CSI500 2011-01-01..2014-10-16 outcomes to
explain the localized CSI500-high material-gap Audit-B failure. It does not
select or fit a successor model. Future 2015+ external-index blocks are scanned
with symbol/trading_day/timestamp columns only for physical coverage metadata;
no future OHLC, gap target, fill target, or model score is opened.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_gap_fill_v2_target_ledger as targetmod
import evaluate_local_gap_fill_v2_2026_repeat as evalbase

PROTOCOL = ROOT / "docs/governance/cloud_session_20260907_gap_fill_v21_regime_diagnostic_protocol_v1.json"
EXTERNAL_PARAMETERS = ROOT / "docs/governance/local_gap_fill_cross_index_transport_dev_parameter_freeze_v1.json"
OUT = ROOT / "docs/research/local_gap_fill_v21_regime_diagnostic_receipt_v1.json"
USAGE = ROOT / "docs/governance/local_gap_fill_v21_regime_diagnostic_data_usage_v1.json"

ADMITTED_DATASET_VERSION = "bars_cn_index_1m_raw_canonical_market_index_baidu_3s_20000714_20260821_factorlab_unified_missing_day_repaired_v8_20260824"
ADMITTED_DATASET_SHA256 = "25f4f9f8b67c799ffb1a7b7fdee94b0b21dbbfed1efc54d063264ccb046411f0"
EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256 = "0cc74f79d9e9f26d1b9d8d554c96db0207a63d68787cceff1152dd71d26ae992"
EXPECTED_BUNDLES = {
    "CSI300": "87b4bf1c4153bd786189b48e631175e0eaf83a34fc9ca7b96bff8d794c5158eb",
    "CSI500": "6cf2966d1ae4c48df2d52ef024c197907d76169ac2672ac0c6dd96e0ddd9a957",
}
SYMBOLS = {"CSI300": "000300.SH", "CSI500": "000905.SH"}
OTHER = {"CSI300": "CSI500", "CSI500": "CSI300"}
HISTORY_START = "2010-09-01"
CONSUMED_START = "2011-01-01"
AUDIT_A_END = "2012-12-31"
AUDIT_B_START = "2013-01-01"
CONSUMED_END = "2014-10-16"
FUTURE_START = "2015-01-01"
FUTURE_END = "2026-08-21"
FUTURE_PARTITIONS = {
    "V21_DEV": ("2015-01-01", "2018-12-31"),
    "V21_AUDIT_A": ("2019-01-01", "2021-12-31"),
    "V21_AUDIT_B": ("2022-01-01", "2024-12-31"),
    "V21_EXTERNAL_RESERVE": ("2025-01-01", "2026-08-21"),
}
FEATURES = ["abs_gap", "abs_gap_over_rvol20"]
PROB_COL = {"fill_15m": "base_p15", "fill_60m": "base_p60"}
BETA_BOUNDS = (-6.0, 6.0)
MIN_CELL_ROWS = 20
EPS = 1e-9


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_digest(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def require_source() -> Path:
    raw = os.environ.get("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE")
    if not raw:
        raise RuntimeError("OVERNIGHT_HISTORICAL_INDEX_1M_LAKE is required")
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"historical source does not exist: {path}")
    if ADMITTED_DATASET_VERSION not in str(path):
        raise RuntimeError("source path is not the HE-00 admitted dataset identity")
    return path


def read_consumed_minutes(source: Path, symbol: str) -> pd.DataFrame:
    frame = pd.read_parquet(
        source,
        filters=[
            ("symbol", "==", symbol),
            ("trading_day", ">=", HISTORY_START),
            ("trading_day", "<=", CONSUMED_END),
        ],
        columns=["symbol", "trading_day", "timestamp", "open", "high", "low", "close"],
    )
    if frame.empty:
        raise RuntimeError(f"no consumed diagnostic rows for {symbol}")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].max() > CONSUMED_END or (frame["trading_day"] >= "2014-10-17").any():
        raise RuntimeError(f"{symbol} supporting-crosscheck row entered RD1")
    if frame.duplicated(["trading_day", "timestamp"]).any():
        raise RuntimeError(f"{symbol} duplicate timestamp")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    return frame.sort_values(["trading_day", "timestamp"], kind="mergesort").reset_index(drop=True)


def build_index_frames(minutes: pd.DataFrame, name: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    clocks = targetmod.expected_clocks()
    expected_set = set(clocks["eod"])
    groups = {day: g.copy() for day, g in minutes.groupby("trading_day", sort=True)}
    days = sorted(groups)
    daily_rows = []
    exact_240 = {}
    for day in days:
        g = groups[day]
        present = g["clock"].tolist()
        exact = len(g) == 240 and len(set(present)) == 240 and set(present) == expected_set
        exact_240[day] = bool(exact)
        gg = g.set_index("clock")
        open_0931 = np.nan if "09:31" not in gg.index else pd.to_numeric(pd.Series([gg.loc["09:31", "open"]]), errors="coerce").iloc[0]
        close_1500 = np.nan if "15:00" not in gg.index else pd.to_numeric(pd.Series([gg.loc["15:00", "close"]]), errors="coerce").iloc[0]
        daily_rows.append({"trading_day": day, "open_0931": open_0931, "close_1500": close_1500, "exact_240": bool(exact)})

    daily = pd.DataFrame(daily_rows).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    close = pd.to_numeric(daily["close_1500"], errors="coerce")
    open0931 = pd.to_numeric(daily["open_0931"], errors="coerce")
    daily["prev_close"] = close.shift(1)
    daily["rvol20"] = close.pct_change(fill_method=None).shift(1).rolling(20, min_periods=20).std()
    daily["gap"] = open0931 / daily["prev_close"] - 1.0
    daily["trend20"] = close.shift(1) / close.shift(21) - 1.0
    daily["momentum5"] = close.shift(1) / close.shift(6) - 1.0
    daily["prior_daytime"] = close.shift(1) / open0931.shift(1) - 1.0

    target_rows = []
    invalid: dict[str, int] = {}
    for _, row in daily.loc[(daily["trading_day"] >= CONSUMED_START) & (daily["trading_day"] <= CONSUMED_END)].iterrows():
        day = str(row["trading_day"])
        if not bool(row["exact_240"]):
            invalid["not_exact_complete_240_clocks"] = invalid.get("not_exact_complete_240_clocks", 0) + 1
            continue
        numeric = [row["open_0931"], row["prev_close"], row["gap"], row["rvol20"]]
        if not all(np.isfinite(float(v)) for v in numeric) or float(row["rvol20"]) <= 0:
            invalid["incomplete_gap_or_rvol20"] = invalid.get("incomplete_gap_or_rvol20", 0) + 1
            continue
        day_row = pd.Series({
            "trading_day": day,
            "open_0931": float(row["open_0931"]),
            "prev_close": float(row["prev_close"]),
            "overnight_gap": float(row["gap"]),
        })
        result = targetmod.compute_day(day_row, groups[day], clocks)
        if result is None or not bool(result.get("target_valid", False)):
            reason = "target_invalid" if result is None else str(result.get("invalid_reason"))
            invalid[reason] = invalid.get(reason, 0) + 1
            continue
        result.update({
            "rvol20": float(row["rvol20"]),
            "abs_gap_over_rvol20": float(abs(row["gap"]) / row["rvol20"]),
            "trend20": float(row["trend20"]) if np.isfinite(row["trend20"]) else np.nan,
            "momentum5": float(row["momentum5"]) if np.isfinite(row["momentum5"]) else np.nan,
            "prior_daytime": float(row["prior_daytime"]) if np.isfinite(row["prior_daytime"]) else np.nan,
        })
        target_rows.append(result)

    targets = pd.DataFrame(target_rows).sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    if targets.empty:
        raise RuntimeError(f"{name} no consumed target-valid rows")
    if targets["trading_day"].max() > CONSUMED_END:
        raise RuntimeError(f"{name} target boundary crossed")
    if int((targets["fill_15m"].astype(bool) & ~targets["fill_60m"].astype(bool)).sum()) or int((targets["fill_60m"].astype(bool) & ~targets["fill_eod"].astype(bool)).sum()):
        raise RuntimeError(f"{name} target nesting violation")
    audit = {
        "symbol": SYMBOLS[name],
        "history_start": HISTORY_START,
        "consumed_target_window": {"start": CONSUMED_START, "end": CONSUMED_END},
        "trading_days_loaded_including_history": int(len(days)),
        "target_valid_rows": int(len(targets)),
        "audit_a_rows": int(((targets["trading_day"] >= CONSUMED_START) & (targets["trading_day"] <= AUDIT_A_END)).sum()),
        "audit_b_rows": int(((targets["trading_day"] >= AUDIT_B_START) & (targets["trading_day"] <= CONSUMED_END)).sum()),
        "invalid_reason_counts": invalid,
        "supporting_crosscheck_or_later_rows_loaded": False,
    }
    return daily, targets, audit


def attach_other_and_probes(name: str, target: pd.DataFrame, daily_self: pd.DataFrame, daily_other: pd.DataFrame) -> pd.DataFrame:
    self_cols = daily_self[["trading_day", "gap", "rvol20", "trend20", "momentum5", "prior_daytime"]].copy()
    self_cols = self_cols.rename(columns={c: f"self_{c}" for c in ["gap", "rvol20", "trend20", "momentum5", "prior_daytime"]})
    other_cols = daily_other[["trading_day", "gap", "rvol20", "momentum5"]].copy()
    other_cols = other_cols.rename(columns={"gap": "other_gap", "rvol20": "other_rvol20", "momentum5": "other_momentum5"})
    out = target.merge(self_cols, on="trading_day", how="left", validate="one_to_one").merge(other_cols, on="trading_day", how="left", validate="one_to_one")
    sign = np.where(out["gap_sign"].eq("high"), 1.0, -1.0)
    out["P1_common_gap_support"] = sign * pd.to_numeric(out["other_gap"], errors="coerce") / pd.to_numeric(out["other_rvol20"], errors="coerce")
    out["P2_relative_gap_excess"] = sign * (pd.to_numeric(out["gap"], errors="coerce") - pd.to_numeric(out["other_gap"], errors="coerce")) / pd.to_numeric(out["rvol20"], errors="coerce")
    out["P3_trend20_alignment"] = sign * pd.to_numeric(out["self_trend20"], errors="coerce")
    out["P4_prior_daytime_alignment"] = sign * pd.to_numeric(out["self_prior_daytime"], errors="coerce")
    out["P5_relative_momentum5_alignment"] = sign * (pd.to_numeric(out["self_momentum5"], errors="coerce") - pd.to_numeric(out["other_momentum5"], errors="coerce"))
    out["index"] = name
    return out


def attach_base_probs(frame: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    out = frame.copy()
    out["base_p15"] = np.nan
    out["base_p60"] = np.nan
    for sign in ["high", "low"]:
        mask = out["gap_sign"].eq(sign)
        if not mask.any():
            continue
        x = out.loc[mask, FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(x).all():
            raise RuntimeError(f"nonfinite base geometry for {sign}")
        p15, p60, _ = evalbase.cumulative_probs(bundle["heads"][sign], x)
        out.loc[mask, "base_p15"] = p15
        out.loc[mask, "base_p60"] = p60
    return out


def nll(y: np.ndarray, p: np.ndarray) -> float:
    pp = np.clip(np.asarray(p, dtype=float), EPS, 1.0 - EPS)
    yy = np.asarray(y, dtype=float)
    return float(-np.mean(yy * np.log(pp) + (1.0 - yy) * np.log(1.0 - pp)))


def fit_offset(part: pd.DataFrame, probe: str, horizon: str) -> dict:
    cols = [probe, horizon, PROB_COL[horizon]]
    cell = part[cols].apply(pd.to_numeric, errors="coerce").dropna()
    cell = cell.loc[np.isfinite(cell.to_numpy(dtype=float)).all(axis=1)].copy()
    n = int(len(cell))
    if n < MIN_CELL_ROWS:
        return {"n": n, "status": "insufficient", "beta": None, "base_log_loss": None, "adjusted_log_loss": None, "log_loss_improvement": None, "optimizer_success": False}
    x = cell[probe].to_numpy(dtype=float)
    mu = float(np.mean(x))
    sd = float(np.std(x, ddof=0))
    if not np.isfinite(sd) or sd <= 0:
        return {"n": n, "status": "degenerate_probe", "beta": None, "base_log_loss": None, "adjusted_log_loss": None, "log_loss_improvement": None, "optimizer_success": False, "probe_mean": mu, "probe_std": sd}
    z = (x - mu) / sd
    y = cell[horizon].to_numpy(dtype=float)
    base_p = np.clip(cell[PROB_COL[horizon]].to_numpy(dtype=float), EPS, 1.0 - EPS)
    offset = np.log(base_p / (1.0 - base_p))
    base_ll = nll(y, base_p)

    def objective(beta: float) -> float:
        return nll(y, expit(offset + float(beta) * z))

    res = minimize_scalar(objective, bounds=BETA_BOUNDS, method="bounded", options={"xatol": 1e-10})
    beta = float(res.x)
    adj = float(res.fun)
    return {
        "n": n,
        "status": "ok" if bool(res.success) else "optimizer_failed",
        "beta": beta,
        "beta_at_bound": bool(abs(beta - BETA_BOUNDS[0]) < 1e-5 or abs(beta - BETA_BOUNDS[1]) < 1e-5),
        "base_log_loss": base_ll,
        "adjusted_log_loss": adj,
        "log_loss_improvement": float(base_ll - adj),
        "probe_mean": mu,
        "probe_std": sd,
        "optimizer_success": bool(res.success),
    }


def expected_sign_ok(beta: float | None, expected: str) -> bool:
    if beta is None or not np.isfinite(beta):
        return False
    return bool(beta < 0.0) if expected == "negative" else bool(beta > 0.0)


def evaluate_probe(probe_spec: dict, primary: pd.DataFrame, contrast: pd.DataFrame) -> dict:
    probe = probe_spec["id"]
    expected = probe_spec["expected_beta_sign"]
    periods = {
        "pooled": primary,
        "Audit_A": primary.loc[(primary["trading_day"] >= CONSUMED_START) & (primary["trading_day"] <= AUDIT_A_END)].copy(),
        "Audit_B": primary.loc[(primary["trading_day"] >= AUDIT_B_START) & (primary["trading_day"] <= CONSUMED_END)].copy(),
    }
    results: dict[str, dict] = {}
    for period, part in periods.items():
        results[period] = {h: fit_offset(part, probe, h) for h in ["fill_15m", "fill_60m"]}
    contrast_res = {h: fit_offset(contrast, probe, h) for h in ["fill_15m", "fill_60m"]}

    pooled_signs = [expected_sign_ok(results["pooled"][h]["beta"], expected) for h in ["fill_15m", "fill_60m"]]
    pooled_improve = [bool((results["pooled"][h]["log_loss_improvement"] or 0.0) > 0.0) for h in ["fill_15m", "fill_60m"]]
    audit_b_signs = [expected_sign_ok(results["Audit_B"][h]["beta"], expected) for h in ["fill_15m", "fill_60m"]]
    audit_b_improve = [bool((results["Audit_B"][h]["log_loss_improvement"] or 0.0) > 0.0) for h in ["fill_15m", "fill_60m"]]
    audit_a_signs = [expected_sign_ok(results["Audit_A"][h]["beta"], expected) for h in ["fill_15m", "fill_60m"]]
    contrast_signs = [expected_sign_ok(contrast_res[h]["beta"], expected) for h in ["fill_15m", "fill_60m"]]
    required_cells_ok = all(results[p][h]["status"] == "ok" for p in results for h in ["fill_15m", "fill_60m"]) and all(contrast_res[h]["status"] == "ok" for h in ["fill_15m", "fill_60m"])
    gates = {
        "required_cells_optimizer_and_n_ok": bool(required_cells_ok),
        "pooled_primary_expected_sign_both_horizons": bool(all(pooled_signs)),
        "pooled_primary_logloss_improves_both_horizons": bool(all(pooled_improve)),
        "audit_b_primary_expected_sign_both_horizons": bool(all(audit_b_signs)),
        "audit_b_primary_logloss_improves_at_least_one_of_two": bool(sum(audit_b_improve) >= 1),
        "audit_a_primary_expected_sign_at_least_one_of_two": bool(sum(audit_a_signs) >= 1),
        "csi300_high_contrast_not_contradicted_both_horizons": bool(sum(contrast_signs) >= 1),
    }
    supported = bool(all(gates.values()))
    return {
        "probe_id": probe,
        "expected_beta_sign": expected,
        "primary": results,
        "CSI300_high_gt10bp_contrast_pooled": contrast_res,
        "gates": gates,
        "gate_pass_count": int(sum(gates.values())),
        "mechanism_supported_for_family_design": supported,
    }


def inventory_future(source: Path, symbol: str) -> dict:
    frame = pd.read_parquet(
        source,
        filters=[("symbol", "==", symbol), ("trading_day", ">=", FUTURE_START), ("trading_day", "<=", FUTURE_END)],
        columns=["symbol", "trading_day", "timestamp"],
    )
    if frame.empty:
        raise RuntimeError(f"no future metadata rows for {symbol}")
    frame["trading_day"] = frame["trading_day"].astype(str)
    if frame["trading_day"].min() < FUTURE_START or frame["trading_day"].max() > FUTURE_END:
        raise RuntimeError(f"future metadata boundary crossed for {symbol}")
    frame["clock"] = frame["timestamp"].astype(str).str.slice(11, 16)
    expected_set = set(targetmod.expected_clocks()["eod"])
    daily = []
    for day, g in frame.groupby("trading_day", sort=True):
        clocks = g["clock"].tolist()
        exact = len(g) == 240 and len(set(clocks)) == 240 and set(clocks) == expected_set
        daily.append({"trading_day": str(day), "exact_240": bool(exact)})
    dd = pd.DataFrame(daily)
    partitions = {}
    for name, (start, end) in FUTURE_PARTITIONS.items():
        part = dd.loc[(dd["trading_day"] >= start) & (dd["trading_day"] <= end)].copy()
        partitions[name] = {
            "window": {"start": start, "end": end},
            "observed_trading_day_count": int(len(part)),
            "exact_240_day_count": int(part["exact_240"].sum()) if len(part) else 0,
            "min_day": None if part.empty else str(part["trading_day"].min()),
            "max_day": None if part.empty else str(part["trading_day"].max()),
        }
    return {
        "columns_read": ["symbol", "trading_day", "timestamp"],
        "OHLC_read": False,
        "gap_or_fill_constructed": False,
        "model_scored": False,
        "partitions": partitions,
    }


def main() -> int:
    protocol = load_json(PROTOCOL)
    external = load_json(EXTERNAL_PARAMETERS)
    if protocol["research_identity"] != "gap_fill_v2_1_regime_conditioned_successor" or protocol["stage"] != "V21_RD1_consumed_evidence_mechanism_diagnostic_before_successor_family":
        raise RuntimeError("V2.1 RD1 protocol identity drifted")
    if sha256(EXTERNAL_PARAMETERS) != EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256:
        raise RuntimeError("external parameter artifact SHA256 drifted")
    if external["source_dataset_sha256_from_HE00"] != ADMITTED_DATASET_SHA256 or external["source_dataset_version"] != ADMITTED_DATASET_VERSION:
        raise RuntimeError("source identity drifted")
    for name, expected in EXPECTED_BUNDLES.items():
        item = external["external_index_bundles"][name]
        if item["parameter_bundle_sha256"] != expected or canonical_digest(item["parameter_bundle"]) != expected:
            raise RuntimeError(f"{name} frozen bundle drifted")

    source = require_source()
    daily: dict[str, pd.DataFrame] = {}
    targets: dict[str, pd.DataFrame] = {}
    source_audits = {}
    for name, symbol in SYMBOLS.items():
        minutes = read_consumed_minutes(source, symbol)
        d, t, audit = build_index_frames(minutes, name)
        daily[name], targets[name], source_audits[name] = d, t, audit

    scored: dict[str, pd.DataFrame] = {}
    for name in SYMBOLS:
        frame = attach_other_and_probes(name, targets[name], daily[name], daily[OTHER[name]])
        frame = attach_base_probs(frame, external["external_index_bundles"][name]["parameter_bundle"])
        scored[name] = frame

    primary = scored["CSI500"].loc[(scored["CSI500"]["gap_sign"] == "high") & (scored["CSI500"]["abs_gap"] > 0.001)].copy()
    contrast = scored["CSI300"].loc[(scored["CSI300"]["gap_sign"] == "high") & (scored["CSI300"]["abs_gap"] > 0.001)].copy()
    if primary.empty or contrast.empty:
        raise RuntimeError("RD1 primary/contrast cell empty")

    probe_results = []
    for spec in protocol["probes"]:
        probe_results.append(evaluate_probe(spec, primary, contrast))
    admitted = [r["probe_id"] for r in probe_results if r["mechanism_supported_for_family_design"]]

    future_inventory = {name: inventory_future(source, symbol) for name, symbol in SYMBOLS.items()}

    receipt = {
        "schema_id": "overnight_open_gap_fill_v21_regime_diagnostic_receipt@1.0",
        "session_date": "2026-09-07",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "stage": "V21_RD1_completed_local_pending_cloud_review",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "source_dataset_version": ADMITTED_DATASET_VERSION,
        "source_dataset_sha256_from_HE00": ADMITTED_DATASET_SHA256,
        "external_parameter_artifact_sha256": EXPECTED_EXTERNAL_PARAMETER_FILE_SHA256,
        "source_audits": source_audits,
        "primary_cell_counts": {
            "pooled": int(len(primary)),
            "Audit_A": int(((primary["trading_day"] >= CONSUMED_START) & (primary["trading_day"] <= AUDIT_A_END)).sum()),
            "Audit_B": int(((primary["trading_day"] >= AUDIT_B_START) & (primary["trading_day"] <= CONSUMED_END)).sum()),
        },
        "contrast_cell_count": int(len(contrast)),
        "probe_results": probe_results,
        "mechanism_supported_probe_ids": admitted,
        "supported_probe_count": int(len(admitted)),
        "future_external_metadata_inventory": future_inventory,
        "successor_model_fit_performed": False,
        "successor_model_selection_performed": False,
        "feature_family_frozen_after_RD1": False,
        "2014Q4_supporting_crosscheck_opened": False,
        "V21_DEV_outcomes_opened": False,
        "V21_AUDIT_A_outcomes_opened": False,
        "V21_AUDIT_B_outcomes_opened": False,
        "V21_EXTERNAL_RESERVE_outcomes_opened": False,
        "CSI1000_post_2026_08_21_outcomes_opened": False,
        "trading_return_used": False,
        "production_authority": False,
    }
    usage = {
        "schema_id": "overnight_open_gap_fill_v21_regime_diagnostic_data_usage@1.0",
        "session_date": "2026-09-07",
        "research_identity": "gap_fill_v2_1_regime_conditioned_successor",
        "outcome_bearing_consumed_data_opened": {
            "CSI300_Audit_A_2011_2012": True,
            "CSI300_Audit_B_2013_to_2014_10_16": True,
            "CSI500_Audit_A_2011_2012": True,
            "CSI500_Audit_B_2013_to_2014_10_16": True,
        },
        "future_external_metadata_only_scanned": True,
        "future_external_OHLC_read": False,
        "future_external_gap_fill_or_model_scores_opened": False,
        "supporting_crosscheck_2014Q4_opened": False,
        "CSI1000_post_2026_08_21_outcomes_opened": False,
        "raw_rows_written_to_repo": False,
        "aggregate_outputs_only": True,
        "production_authority": False,
    }
    dump_json(OUT, receipt)
    dump_json(USAGE, usage)
    print("GAP_FILL_V21_RD1_RESULT", json.dumps({"supported_probe_count": len(admitted), "supported_probe_ids": admitted, "V21_DEV_outcomes_opened": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
