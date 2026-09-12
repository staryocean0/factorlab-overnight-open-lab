#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, QuantileRegressor, Ridge
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FAMILY_PATH = ROOT / "docs/governance/cloud_session_20260906_direction_head_family_v1.json"
PANEL_PATH = ROOT / "data/development/csi1000_open_pit_panel.parquet"
TEST_YEARS = [2016, 2017, 2018, 2019, 2020]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def regression_pipe(kind: str) -> Pipeline:
    if kind == "ridge_mean_sign":
        model = Ridge(alpha=1.0)
    elif kind == "median_quantile_sign":
        model = QuantileRegressor(quantile=0.5, alpha=0.0, solver="highs")
    else:
        raise ValueError(kind)
    return Pipeline([("sc", StandardScaler()), ("model", model)])


def logistic_pipe() -> Pipeline:
    return Pipeline(
        [
            ("sc", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=1.0,
                    penalty="l2",
                    solver="lbfgs",
                    max_iter=10000,
                    random_state=0,
                ),
            ),
        ]
    )


def metrics(y: np.ndarray, pred_up: np.ndarray, score: np.ndarray) -> dict:
    actual_up = y >= 0.0
    correct = pred_up == actual_up
    auc = None
    if np.unique(actual_up.astype(int)).size == 2:
        auc = float(roc_auc_score(actual_up.astype(int), score))
    return {
        "n": int(len(y)),
        "direction_hit": float(np.mean(correct)),
        "balanced_accuracy": float(balanced_accuracy_score(actual_up, pred_up)),
        "roc_auc": auc,
        "correct_count": int(correct.sum()),
        "actual_up_share": float(np.mean(actual_up)),
        "pred_up_share": float(np.mean(pred_up)),
    }


def fit_score(kind: str, x_train: pd.DataFrame, y_train: np.ndarray, x_test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    if kind in {"ridge_mean_sign", "median_quantile_sign"}:
        pipe = regression_pipe(kind)
        pipe.fit(x_train, y_train)
        score = np.asarray(pipe.predict(x_test), dtype=float)
        return score >= 0.0, score
    if kind == "logistic_sign":
        pipe = logistic_pipe()
        y_sign = y_train >= 0.0
        pipe.fit(x_train, y_sign)
        score = np.asarray(pipe.predict_proba(x_test)[:, 1], dtype=float)
        return score >= 0.5, score
    raise ValueError(kind)


def main() -> int:
    family = load_json(FAMILY_PATH)
    cols = list(family["direction_features"])
    panel = pd.read_parquet(PANEL_PATH).copy()
    day = pd.to_datetime(panel["trading_day"])
    if day.max() > pd.Timestamp("2020-12-31"):
        raise RuntimeError("bounded panel contains post-2020 rows")

    x_all = panel[cols].apply(pd.to_numeric, errors="coerce")
    y_all = pd.to_numeric(panel["gap"], errors="coerce")
    complete = x_all.notna().all(axis=1) & y_all.notna()
    kinds = ["ridge_mean_sign", "median_quantile_sign", "logistic_sign"]
    folds: list[dict] = []
    pooled: dict[str, list] = {
        k: [[], [], []] for k in kinds
    }  # y, pred_up, score

    for year in TEST_YEARS:
        train_mask = complete & (day.dt.year < year) & (day.dt.year >= 2015)
        test_mask = complete & (day.dt.year == year)
        if int(train_mask.sum()) == 0 or int(test_mask.sum()) == 0:
            raise RuntimeError(f"empty fold {year}")
        x_tr = x_all.loc[train_mask]
        y_tr = y_all.loc[train_mask].to_numpy(dtype=float)
        x_te = x_all.loc[test_mask]
        y_te = y_all.loc[test_mask].to_numpy(dtype=float)
        fold = {
            "year": year,
            "n_train": int(train_mask.sum()),
            "n_test": int(test_mask.sum()),
            "models": {},
        }
        for kind in kinds:
            pred_up, score = fit_score(kind, x_tr, y_tr, x_te)
            fold["models"][kind] = metrics(y_te, pred_up, score)
            pooled[kind][0].append(y_te)
            pooled[kind][1].append(pred_up)
            pooled[kind][2].append(score)
        folds.append(fold)

    pooled_metrics: dict[str, dict] = {}
    for kind in kinds:
        y = np.concatenate(pooled[kind][0])
        pred_up = np.concatenate(pooled[kind][1])
        score = np.concatenate(pooled[kind][2])
        pooled_metrics[kind] = metrics(y, pred_up, score)

    baseline_by_year = [f["models"]["ridge_mean_sign"]["direction_hit"] for f in folds]
    baseline_year_equal = float(np.mean(baseline_by_year))
    attempts = []
    for kind in ["median_quantile_sign", "logistic_sign"]:
        hits = [f["models"][kind]["direction_hit"] for f in folds]
        deltas = [h - b for h, b in zip(hits, baseline_by_year)]
        correct_delta = int(
            sum(f["models"][kind]["correct_count"] - f["models"]["ridge_mean_sign"]["correct_count"] for f in folds)
        )
        positive_years = int(sum(d > 0.0 for d in deltas))
        mean_hit = float(np.mean(hits))
        median_delta = float(np.median(deltas))
        admitted = bool(
            mean_hit > baseline_year_equal
            and correct_delta > 0
            and positive_years >= 3
            and median_delta >= 0.0
        )
        attempts.append(
            {
                "name": kind,
                "admitted": admitted,
                "year_equal_mean_direction_hit": mean_hit,
                "baseline_year_equal_mean_direction_hit": baseline_year_equal,
                "annual_hit_deltas": deltas,
                "positive_annual_hit_delta_count": positive_years,
                "median_annual_hit_delta": median_delta,
                "total_correct_count_increment": correct_delta,
                "pooled": pooled_metrics[kind],
            }
        )

    admitted = [a for a in attempts if a["admitted"]]
    selected = None
    status = "no_incremental_direction_successor_retain_ridge"
    if admitted:
        admitted_sorted = sorted(
            admitted,
            key=lambda a: (
                a["year_equal_mean_direction_hit"],
                a["total_correct_count_increment"],
                a["pooled"]["direction_hit"],
            ),
            reverse=True,
        )
        top = admitted_sorted[0]
        if len(admitted_sorted) == 1 or (
            top["year_equal_mean_direction_hit"],
            top["total_correct_count_increment"],
            top["pooled"]["direction_hit"],
        ) != (
            admitted_sorted[1]["year_equal_mean_direction_hit"],
            admitted_sorted[1]["total_correct_count_increment"],
            admitted_sorted[1]["pooled"]["direction_hit"],
        ):
            selected = top["name"]
            status = "retrospective_direction_candidate_waiting_new_unseen_local_challenge"
        else:
            status = "no_unique_direction_successor_tied_admitted_candidates"

    result = {
        "schema_id": "overnight_open_direction_head_dev_selection@1.0",
        "family_sha256": sha256(FAMILY_PATH),
        "panel_sha256": sha256(PANEL_PATH),
        "evidence_role": "consumed_2015_2020_development_only",
        "holdout_2021_2025_used": False,
        "fresh_oos": False,
        "production_authority": False,
        "folds": folds,
        "baseline": {
            "year_equal_mean_direction_hit": baseline_year_equal,
            "pooled": pooled_metrics["ridge_mean_sign"],
        },
        "attempts": attempts,
        "selected": selected,
        "scientific_status": status,
    }
    print("DIRECTION_HEAD_DEV_SELECTION_RESULT", json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
