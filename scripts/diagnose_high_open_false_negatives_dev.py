#!/usr/bin/env python3
"""Development-only diagnosis of incumbent high-open false negatives.

This script is intentionally NOT a candidate selector. It reconstructs the local
2015-2025 feature panel, produces expanding natural-year OOF predictions from
the frozen Median direction head, and aggregates diagnostics that can support or
reject financial mechanism hypotheses. No 2026 row may be loaded.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import QuantileRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_local_2021_2025_two_head as local
from select_clock_candidates_dev import add_us_interval_features

# Local path overrides are execution-only and do not change model semantics.
local.ANNOTATED_PANEL = Path(os.environ.get("OVERNIGHT_ANNOTATED_PANEL", str(local.ANNOTATED_PANEL)))
local.DATAHUB_1M = Path(os.environ.get("OVERNIGHT_DATAHUB_1M", str(local.DATAHUB_1M)))
local.FRED_NDQ = Path(os.environ.get("OVERNIGHT_FRED_NASDAQ", str(local.FRED_NDQ)))
local.FRED_VIX = Path(os.environ.get("OVERNIGHT_FRED_VIX", str(local.FRED_VIX)))

ANNOTATED_PANEL = local.ANNOTATED_PANEL
DATAHUB_1M = local.DATAHUB_1M
FRED_NDQ = local.FRED_NDQ
FRED_VIX = local.FRED_VIX

DEV_START = "2015-01-05"
DEV_END = "2025-12-31"
OOF_YEARS = list(range(2016, 2026))
SELECTED_PATH = ROOT / "docs/governance/cloud_session_20260906_direction_head_selected_v1.json"
PROTOCOL_PATH = ROOT / "docs/governance/cloud_session_20260906_high_open_recall_research_protocol_v1.json"
RECEIPT_PATH = ROOT / "docs/research/cloud_session_20260906_local_high_open_recall_diagnostic_receipt_v1.json"
DATA_USAGE_PATH = ROOT / "docs/governance/local_session_20260906_high_open_recall_data_usage.json"
SELECTED_SHA = "9b0255fbbf6f0c4059e8779e61cb3d5d4eabeab1ce60aed09377d782f755e465"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def spec_digest(spec: dict) -> str:
    raw = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def complete_mask(frame: pd.DataFrame, cols: list[str]) -> pd.Series:
    x = frame[cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(frame["gap"], errors="coerce")
    return x.notna().all(axis=1) & y.notna()


def median_pipe() -> Pipeline:
    return Pipeline(
        [
            ("sc", StandardScaler()),
            ("model", QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")),
        ]
    )


def rank_auc(actual_up: np.ndarray, score: np.ndarray) -> float | None:
    y = np.asarray(actual_up, dtype=bool)
    if np.unique(y.astype(int)).size != 2:
        return None
    ranks = pd.Series(score).rank(method="average").to_numpy(dtype=float)
    n_pos = int(y.sum())
    n_neg = int((~y).sum())
    rank_sum_pos = float(ranks[y].sum())
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def direction_metrics(frame: pd.DataFrame) -> dict:
    actual_up = frame["actual_up"].to_numpy(dtype=bool)
    pred_up = frame["pred_up"].to_numpy(dtype=bool)
    score = frame["score"].to_numpy(dtype=float)
    tp = int(np.sum(pred_up & actual_up))
    fn = int(np.sum((~pred_up) & actual_up))
    tn = int(np.sum((~pred_up) & (~actual_up)))
    fp = int(np.sum(pred_up & (~actual_up)))
    recall_up = tp / (tp + fn) if (tp + fn) else None
    recall_down = tn / (tn + fp) if (tn + fp) else None
    balanced = None if recall_up is None or recall_down is None else 0.5 * (recall_up + recall_down)
    return {
        "n": int(len(frame)),
        "direction_hit": float(np.mean(actual_up == pred_up)),
        "balanced_accuracy": None if balanced is None else float(balanced),
        "recall_up": None if recall_up is None else float(recall_up),
        "recall_down": None if recall_down is None else float(recall_down),
        "actual_up_share": float(np.mean(actual_up)),
        "pred_up_share": float(np.mean(pred_up)),
        "roc_auc": rank_auc(actual_up, score),
        "tp": tp,
        "fn": fn,
        "tn": tn,
        "fp": fp,
    }


def safe_mean(series: pd.Series) -> float | None:
    value = pd.to_numeric(series, errors="coerce").dropna()
    return None if value.empty else float(value.mean())


def safe_median(series: pd.Series) -> float | None:
    value = pd.to_numeric(series, errors="coerce").dropna()
    return None if value.empty else float(value.median())


def prior_up_share(prior_gap: pd.Series, window: int) -> pd.Series:
    up = pd.Series(np.nan, index=prior_gap.index, dtype=float)
    known = prior_gap.notna()
    up.loc[known] = (prior_gap.loc[known] >= 0.0).astype(float)
    return up.rolling(window, min_periods=window).mean()


def add_diagnostic_probes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values("trading_day", kind="mergesort").reset_index(drop=True)
    gap = pd.to_numeric(out["gap"], errors="coerce")
    prior = gap.shift(1)

    out["gap_up_share_20"] = prior_up_share(prior, 20)
    out["gap_up_share_60"] = prior_up_share(prior, 60)
    out["gap_mean_20"] = prior.rolling(20, min_periods=20).mean()
    out["gap_mean_60"] = prior.rolling(60, min_periods=60).mean()
    out["gap_median_20"] = prior.rolling(20, min_periods=20).median()
    out["gap_median_60"] = prior.rolling(60, min_periods=60).median()

    nasdaq = pd.to_numeric(out["us_nasdaq_interval"], errors="coerce")
    vix = pd.to_numeric(out["us_vix_interval"], errors="coerce")
    out["us_nasdaq_interval_pos"] = np.maximum(nasdaq, 0.0)
    out["us_nasdaq_interval_neg_abs"] = np.maximum(-nasdaq, 0.0)
    out["us_vix_drop"] = np.maximum(-vix, 0.0)
    out["us_vix_rise"] = np.maximum(vix, 0.0)
    out["global_risk_on_joint"] = out["us_nasdaq_interval_pos"] * out["us_vix_drop"]

    prev_daytime = pd.to_numeric(out["prev_daytime"], errors="coerce")
    prev_afternoon = pd.to_numeric(out["prev_afternoon"], errors="coerce")
    prev_last_hour = pd.to_numeric(out["prev_last_hour"], errors="coerce")
    out["prev_daytime_weakness"] = np.maximum(-prev_daytime, 0.0)
    out["prev_afternoon_weakness"] = np.maximum(-prev_afternoon, 0.0)
    out["prev_last_hour_weakness"] = np.maximum(-prev_last_hour, 0.0)
    out["catchup_daytime_x_us_up"] = out["prev_daytime_weakness"] * out["us_nasdaq_interval_pos"]
    out["catchup_afternoon_x_us_up"] = out["prev_afternoon_weakness"] * out["us_nasdaq_interval_pos"]
    out["catchup_last_hour_x_us_up"] = out["prev_last_hour_weakness"] * out["us_nasdaq_interval_pos"]
    return out


def build_development_frame() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_parquet(
        ANNOTATED_PANEL,
        filters=[("trading_day", ">=", DEV_START), ("trading_day", "<=", DEV_END)],
    )
    raw["trading_day"] = raw["trading_day"].astype(str)
    if raw.empty:
        raise RuntimeError("development annotated panel is empty")
    if str(pd.to_datetime(raw["trading_day"]).max().date()) > DEV_END:
        raise RuntimeError("development loader crossed into 2026")

    hours = local.load_hours(DATAHUB_1M, DEV_START, DEV_END)
    us = local.load_us(FRED_NDQ, FRED_VIX, max_date=DEV_END)
    frame = local.add_domestic_features(raw, hours)
    frame = local.attach_us(frame, us)
    frame = add_us_interval_features(frame, us)
    frame = add_diagnostic_probes(frame)

    day = pd.to_datetime(frame["trading_day"])
    frame = frame.loc[(day >= DEV_START) & (day <= DEV_END)].copy()
    if (pd.to_datetime(frame["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered high-open development frame")

    frozen = pd.read_parquet(ROOT / "data/development/csi1000_open_pit_panel.parquet")
    reconstruction = local.assert_dev_reconstruction(frozen)
    return frame, reconstruction


def expanding_oof(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    years = pd.to_datetime(frame["trading_day"]).dt.year
    for valid_year in OOF_YEARS:
        train = frame.loc[years < valid_year].copy()
        valid = frame.loc[years == valid_year].copy()
        m_train = complete_mask(train, cols)
        m_valid = complete_mask(valid, cols)
        if int(m_train.sum()) == 0 or int(m_valid.sum()) == 0:
            raise RuntimeError(f"empty complete fold for {valid_year}")

        pipe = median_pipe()
        x_train = train.loc[m_train, cols].apply(pd.to_numeric, errors="coerce")
        y_train = pd.to_numeric(train.loc[m_train, "gap"], errors="coerce")
        pipe.fit(x_train, y_train)

        v = valid.loc[m_valid].copy()
        x_valid = v[cols].apply(pd.to_numeric, errors="coerce")
        v["score"] = np.asarray(pipe.predict(x_valid), dtype=float)
        v["actual_up"] = pd.to_numeric(v["gap"], errors="coerce") >= 0.0
        v["pred_up"] = v["score"] >= 0.0
        v["oof_year"] = int(valid_year)
        v["n_train_complete"] = int(m_train.sum())
        pieces.append(v)

    oof = pd.concat(pieces, ignore_index=True)
    if int(pd.to_datetime(oof["trading_day"]).dt.year.max()) != 2025:
        raise RuntimeError("OOF inventory did not end in 2025")
    if (pd.to_datetime(oof["trading_day"]).dt.year >= 2026).any():
        raise RuntimeError("2026 row entered OOF diagnostics")
    return oof


def positive_gap_bins(oof: pd.DataFrame) -> dict:
    gap = pd.to_numeric(oof["gap"], errors="coerce")
    bins = {
        "exact_zero": gap == 0.0,
        "gt0_to_10bp": (gap > 0.0) & (gap <= 0.001),
        "gt10_to_30bp": (gap > 0.001) & (gap <= 0.003),
        "gt30bp": gap > 0.003,
    }
    out: dict[str, dict] = {}
    for name, mask in bins.items():
        part = oof.loc[mask]
        out[name] = {
            "n": int(len(part)),
            "recall_up": None if part.empty else float(part["pred_up"].mean()),
            "miss_count": int((~part["pred_up"]).sum()) if not part.empty else 0,
        }
    for threshold_name, threshold in [("gt10bp", 0.001), ("gt30bp", 0.003)]:
        part = oof.loc[gap > threshold]
        out[f"material_high_open_{threshold_name}"] = {
            "n": int(len(part)),
            "recall_up": None if part.empty else float(part["pred_up"].mean()),
            "miss_count": int((~part["pred_up"]).sum()) if not part.empty else 0,
        }
    return out


def false_negative_margin_bins(oof: pd.DataFrame) -> dict:
    fn = oof.loc[oof["actual_up"] & (~oof["pred_up"])].copy()
    margin = -pd.to_numeric(fn["score"], errors="coerce")
    bins = {
        "within_5bp_below_zero": (margin >= 0.0) & (margin <= 0.0005),
        "gt5_to_15bp_below_zero": (margin > 0.0005) & (margin <= 0.0015),
        "gt15bp_below_zero": margin > 0.0015,
    }
    total = int(len(fn))
    return {
        "false_negative_count": total,
        "bins": {
            name: {
                "n": int(mask.sum()),
                "share_of_false_negatives": None if total == 0 else float(mask.sum() / total),
            }
            for name, mask in bins.items()
        },
        "median_margin": None if total == 0 else float(margin.median()),
        "mean_margin": None if total == 0 else float(margin.mean()),
    }


def quartile_diagnostic(oof: pd.DataFrame, probe: str) -> dict:
    values = pd.to_numeric(oof[probe], errors="coerce")
    valid = values.notna()
    base = oof.loc[valid].copy()
    if len(base) < 20 or base[probe].nunique(dropna=True) < 4:
        return {"status": "insufficient_variation", "n": int(len(base))}

    ranked = pd.to_numeric(base[probe], errors="coerce").rank(method="first")
    q = pd.qcut(ranked, 4, labels=["Q1", "Q2", "Q3", "Q4"])
    base = base.assign(_q=q.astype(str))
    bins: dict[str, dict] = {}
    for label in ["Q1", "Q2", "Q3", "Q4"]:
        part = base.loc[base["_q"] == label]
        actual_up = part["actual_up"].astype(bool)
        up_part = part.loc[actual_up]
        bins[label] = {
            "n_all": int(len(part)),
            "probe_mean": safe_mean(part[probe]),
            "actual_up_share": None if part.empty else float(actual_up.mean()),
            "n_actual_up": int(len(up_part)),
            "recall_up": None if up_part.empty else float(up_part["pred_up"].mean()),
            "false_negative_rate_given_actual_up": None if up_part.empty else float((~up_part["pred_up"]).mean()),
        }

    fn = base.loc[base["actual_up"] & (~base["pred_up"])]
    tp = base.loc[base["actual_up"] & base["pred_up"]]
    std = float(pd.to_numeric(base[probe], errors="coerce").std(ddof=0))
    fn_mean = safe_mean(fn[probe])
    tp_mean = safe_mean(tp[probe])
    standardized = None
    if fn_mean is not None and tp_mean is not None and np.isfinite(std) and std > 0.0:
        standardized = float((fn_mean - tp_mean) / std)

    annual: dict[str, dict] = {}
    annual_diffs: list[float] = []
    for year in OOF_YEARS:
        part = base.loc[base["oof_year"] == year]
        yfn = part.loc[part["actual_up"] & (~part["pred_up"])]
        ytp = part.loc[part["actual_up"] & part["pred_up"]]
        a = safe_mean(yfn[probe])
        b = safe_mean(ytp[probe])
        diff = None if a is None or b is None else float(a - b)
        if diff is not None:
            annual_diffs.append(diff)
        annual[str(year)] = {
            "fn_mean": a,
            "tp_mean": b,
            "fn_minus_tp_mean": diff,
            "n_fn": int(len(yfn)),
            "n_tp": int(len(ytp)),
        }

    corr_gap = None
    x = pd.to_numeric(base[probe], errors="coerce").to_numpy(dtype=float)
    y = pd.to_numeric(base["gap"], errors="coerce").to_numpy(dtype=float)
    if len(x) >= 3 and np.std(x) > 0.0 and np.std(y) > 0.0:
        corr_gap = float(np.corrcoef(x, y)[0, 1])

    return {
        "status": "ok",
        "n": int(len(base)),
        "fn_probe_mean": fn_mean,
        "fn_probe_median": safe_median(fn[probe]),
        "tp_probe_mean": tp_mean,
        "tp_probe_median": safe_median(tp[probe]),
        "fn_minus_tp_standardized_mean": standardized,
        "corr_with_gap": corr_gap,
        "annual_fn_minus_tp": annual,
        "annual_diff_positive_count": int(sum(d > 0.0 for d in annual_diffs)),
        "annual_diff_negative_count": int(sum(d < 0.0 for d in annual_diffs)),
        "quartiles": bins,
    }


def main() -> int:
    protocol = load_json(PROTOCOL_PATH)
    selected = load_json(SELECTED_PATH)
    spec = selected["selected_spec"]
    digest = spec_digest(spec)
    if digest != SELECTED_SHA or selected["selected_spec_sha256"] != SELECTED_SHA:
        raise RuntimeError(f"incumbent direction SHA mismatch: {digest}")
    if spec["name"] != "median_quantile_sign":
        raise RuntimeError("unexpected incumbent direction head")
    if protocol["evidence_boundary"]["2026-01-05_to_2026-08-21"] != "sealed_repeat_blackbox_validation_only":
        raise RuntimeError("2026 blackbox boundary is not frozen as expected")

    cols = list(spec["direction_features"])
    frame, reconstruction = build_development_frame()
    oof = expanding_oof(frame, cols)

    probes = [
        "overnight_trend_5",
        "gap_up_share_20",
        "gap_up_share_60",
        "gap_mean_20",
        "gap_mean_60",
        "gap_median_20",
        "gap_median_60",
        "us_nasdaq_interval",
        "us_nasdaq_interval_pos",
        "us_nasdaq_interval_neg_abs",
        "us_vix_interval",
        "us_vix_drop",
        "us_vix_rise",
        "global_risk_on_joint",
        "us_session_count",
        "holiday_reopen",
        "prev_daytime_weakness",
        "prev_afternoon_weakness",
        "prev_last_hour_weakness",
        "catchup_daytime_x_us_up",
        "catchup_afternoon_x_us_up",
        "catchup_last_hour_x_us_up",
    ]

    annual = {
        str(year): direction_metrics(oof.loc[oof["oof_year"] == year])
        for year in OOF_YEARS
    }
    probe_results = {probe: quartile_diagnostic(oof, probe) for probe in probes}

    receipt = {
        "schema_id": "overnight_open_high_open_recall_diagnostic_receipt@1.0",
        "session_date": "2026-09-06",
        "protocol": str(PROTOCOL_PATH.relative_to(ROOT)),
        "incumbent": str(SELECTED_PATH.relative_to(ROOT)),
        "incumbent_spec_sha256": digest,
        "development_window": {"start": DEV_START, "end": DEV_END},
        "oof_years": OOF_YEARS,
        "n_oof": int(len(oof)),
        "overall_incumbent_oof": direction_metrics(oof),
        "annual_incumbent_oof": annual,
        "positive_gap_recall_bins": positive_gap_bins(oof),
        "false_negative_score_margin": false_negative_margin_bins(oof),
        "mechanism_probes": probe_results,
        "reconstruction_2015_2020_max_abs": reconstruction,
        "source_hashes": {
            "annotated_panel": sha256(ANNOTATED_PANEL),
            "datahub_1m_export": sha256(DATAHUB_1M),
            "fred_nasdaq": sha256(FRED_NDQ),
            "fred_vix": sha256(FRED_VIX),
            "incumbent": sha256(SELECTED_PATH),
            "protocol": sha256(PROTOCOL_PATH),
            "runner": sha256(Path(__file__)),
        },
        "candidate_selection_performed": False,
        "parameter_search_performed": False,
        "threshold_search_performed": False,
        "trading_return_used": False,
        "2026_rows_loaded": False,
        "2026_blackbox_opened": False,
        "raw_development_rows_written_to_repo": False,
        "fresh_oos": False,
        "production_authority": False,
    }
    dump_json(RECEIPT_PATH, receipt)

    usage = {
        "schema_id": "overnight_open_local_high_open_recall_data_usage@1.0",
        "session_date": "2026-09-06",
        "2015-01-05_to_2025-12-31": "development_material_for_high_open_recall_successor_v1",
        "2026-01-05_to_2026-08-21": "not_loaded_sealed_repeat_blackbox",
        "post_2026-08-21": "unread_true_fresh_reserved",
        "raw_rows_persisted_in_bounded_repo": False,
        "production_authority": False,
    }
    dump_json(DATA_USAGE_PATH, usage)

    summary = {
        "n_oof": receipt["n_oof"],
        "overall": receipt["overall_incumbent_oof"],
        "positive_gap_recall_bins": receipt["positive_gap_recall_bins"],
        "false_negative_score_margin": receipt["false_negative_score_margin"],
        "2026_blackbox_opened": False,
    }
    print("HIGH_OPEN_RECALL_DIAGNOSTIC_RESULT", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
