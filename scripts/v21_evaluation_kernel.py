#!/usr/bin/env python3
"""Pure evaluation kernel for the frozen V21 P2 research program.

This module has no file I/O, no market-data adapter and no model fitting.  It
turns already-produced target/probability arrays into the preregistered DEV or
future-audit gate results.  Keeping this logic pure allows it to be tested and
frozen before any V21 future outcome is opened.
"""
from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

GT10 = 0.001
GT30 = 0.003
PROB_EPS = 1e-6
STRICT_EPS = 1e-12
DEV_YEARS = (2016, 2017, 2018)
AUDIT_A_YEARS = (2019, 2020, 2021)
AUDIT_B_YEARS = (2022, 2023, 2024)


def _binary(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    out = np.asarray(values, dtype=float)
    if out.ndim != 1 or len(out) == 0 or not np.isfinite(out).all():
        raise ValueError(f"{name} must be a non-empty finite vector")
    if ((out != 0.0) & (out != 1.0)).any():
        raise ValueError(f"{name} must be binary")
    return out


def _prob(values: Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    out = np.asarray(values, dtype=float)
    if out.ndim != 1 or len(out) == 0 or not np.isfinite(out).all():
        raise ValueError(f"{name} must be a non-empty finite vector")
    if ((out < 0.0) | (out > 1.0)).any():
        raise ValueError(f"{name} must lie in [0,1]")
    return out


def _mask(mask: Sequence[bool] | np.ndarray | None, n: int) -> np.ndarray:
    if mask is None:
        return np.ones(n, dtype=bool)
    out = np.asarray(mask, dtype=bool)
    if out.ndim != 1 or len(out) != n:
        raise ValueError("mask must align with arrays")
    if not out.any():
        raise ValueError("metric mask is empty")
    return out


def _aligned(*arrays: np.ndarray) -> int:
    if not arrays:
        raise ValueError("no arrays")
    n = len(arrays[0])
    if any(a.ndim != 1 or len(a) != n for a in arrays):
        raise ValueError("arrays must be aligned one-dimensional vectors")
    return n


def brier_score(
    target: Sequence[float] | np.ndarray,
    probability: Sequence[float] | np.ndarray,
    mask: Sequence[bool] | np.ndarray | None = None,
) -> float:
    y = _binary(target, "target")
    p = _prob(probability, "probability")
    n = _aligned(y, p)
    m = _mask(mask, n)
    return float(np.mean((p[m] - y[m]) ** 2))


def log_loss(
    target: Sequence[float] | np.ndarray,
    probability: Sequence[float] | np.ndarray,
    mask: Sequence[bool] | np.ndarray | None = None,
) -> float:
    y = _binary(target, "target")
    p = _prob(probability, "probability")
    n = _aligned(y, p)
    m = _mask(mask, n)
    pp = np.clip(p[m], PROB_EPS, 1.0 - PROB_EPS)
    yy = y[m]
    return float(-np.mean(yy * np.log(pp) + (1.0 - yy) * np.log(1.0 - pp)))


def two_horizon_mean_brier(
    y15: Sequence[float] | np.ndarray,
    y60: Sequence[float] | np.ndarray,
    p15: Sequence[float] | np.ndarray,
    p60: Sequence[float] | np.ndarray,
    mask: Sequence[bool] | np.ndarray | None = None,
) -> float:
    return float((brier_score(y15, p15, mask) + brier_score(y60, p60, mask)) / 2.0)


def two_horizon_mean_log_loss(
    y15: Sequence[float] | np.ndarray,
    y60: Sequence[float] | np.ndarray,
    p15: Sequence[float] | np.ndarray,
    p60: Sequence[float] | np.ndarray,
    mask: Sequence[bool] | np.ndarray | None = None,
) -> float:
    return float((log_loss(y15, p15, mask) + log_loss(y60, p60, mask)) / 2.0)


def _strictly_lower(left: float, right: float) -> bool:
    return bool(float(left) < float(right) - STRICT_EPS)


def _not_higher(left: float, right: float) -> bool:
    return bool(float(left) <= float(right) + STRICT_EPS)


def three_year_positive_gate(values: Sequence[float]) -> bool:
    x = np.asarray(values, dtype=float)
    if x.shape != (3,) or not np.isfinite(x).all():
        return False
    return bool(int(np.sum(x > 0.0)) >= 2 and float(np.median(x)) > 0.0)


def beta_direction_gate(beta_history: Sequence[float]) -> bool:
    """Exactly the frozen DEV rule: >=2/3 positive and positive median."""
    return three_year_positive_gate(beta_history)


def _validate_block(
    y15: Sequence[float] | np.ndarray,
    y60: Sequence[float] | np.ndarray,
    abs_gap: Sequence[float] | np.ndarray,
    years: Sequence[int] | np.ndarray,
    candidate15: Sequence[float] | np.ndarray,
    candidate60: Sequence[float] | np.ndarray,
    control15: Sequence[float] | np.ndarray,
    control60: Sequence[float] | np.ndarray,
    benchmark15: Sequence[float] | np.ndarray,
    benchmark60: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, ...]:
    yy15 = _binary(y15, "y15")
    yy60 = _binary(y60, "y60")
    gap = np.asarray(abs_gap, dtype=float)
    yr = np.asarray(years, dtype=int)
    c15 = _prob(candidate15, "candidate15")
    c60 = _prob(candidate60, "candidate60")
    k15 = _prob(control15, "control15")
    k60 = _prob(control60, "control60")
    b15 = _prob(benchmark15, "benchmark15")
    b60 = _prob(benchmark60, "benchmark60")
    _aligned(yy15, yy60, gap, yr, c15, c60, k15, k60, b15, b60)
    if not np.isfinite(gap).all() or (gap <= 0.0).any():
        raise ValueError("abs_gap must contain finite positive nonzero-gap values")
    return yy15, yy60, gap, yr, c15, c60, k15, k60, b15, b60


def _metric_snapshot(
    y15: np.ndarray,
    y60: np.ndarray,
    p15: np.ndarray,
    p60: np.ndarray,
    mask: np.ndarray,
) -> dict:
    return {
        "brier_15m": brier_score(y15, p15, mask),
        "brier_60m": brier_score(y60, p60, mask),
        "mean_brier_15m_60m": two_horizon_mean_brier(y15, y60, p15, p60, mask),
        "mean_log_loss_15m_60m": two_horizon_mean_log_loss(y15, y60, p15, p60, mask),
    }


def evaluate_dev_primary(
    *,
    y15: Sequence[float] | np.ndarray,
    y60: Sequence[float] | np.ndarray,
    abs_gap: Sequence[float] | np.ndarray,
    years: Sequence[int] | np.ndarray,
    candidate15: Sequence[float] | np.ndarray,
    candidate60: Sequence[float] | np.ndarray,
    control15: Sequence[float] | np.ndarray,
    control60: Sequence[float] | np.ndarray,
    benchmark15: Sequence[float] | np.ndarray,
    benchmark60: Sequence[float] | np.ndarray,
    beta_histories: Mapping[str, Sequence[float]],
    monotonicity_violations: int,
) -> dict:
    """Evaluate the frozen V21_DEV CSI500-high candidate eligibility gates."""
    y15a, y60a, gap, yr, c15, c60, k15, k60, b15, b60 = _validate_block(
        y15, y60, abs_gap, years, candidate15, candidate60,
        control15, control60, benchmark15, benchmark60,
    )
    primary = gap > GT10
    counts = {str(year): int(np.sum(primary & (yr == year))) for year in DEV_YEARS}
    pooled = int(np.sum(primary))
    sample_sufficient = bool(
        pooled >= 60 and all(counts[str(year)] >= 20 for year in DEV_YEARS)
    )
    sample = {
        "pooled_gt10": pooled,
        "by_validation_year_gt10": counts,
        "minimum_pooled_gt10": 60,
        "minimum_per_validation_year_gt10": 20,
        "sufficient": sample_sufficient,
    }
    if not sample_sufficient:
        return {
            "status": "evidence_insufficient",
            "eligible": False,
            "sample": sample,
            "gates": {},
            "annual_primary_control_minus_candidate_mean_brier": [],
        }
    if not beta_histories:
        raise ValueError("at least one beta component history is required")

    candidate_primary = _metric_snapshot(y15a, y60a, c15, c60, primary)
    control_primary = _metric_snapshot(y15a, y60a, k15, k60, primary)
    benchmark_primary = _metric_snapshot(y15a, y60a, b15, b60, primary)
    candidate_all = _metric_snapshot(y15a, y60a, c15, c60, np.ones(len(gap), dtype=bool))
    control_all = _metric_snapshot(y15a, y60a, k15, k60, np.ones(len(gap), dtype=bool))

    annual_improvement: list[float] = []
    for year in DEV_YEARS:
        mask = primary & (yr == year)
        annual_improvement.append(float(
            two_horizon_mean_brier(y15a, y60a, k15, k60, mask)
            - two_horizon_mean_brier(y15a, y60a, c15, c60, mask)
        ))

    beta_gates = {str(name): beta_direction_gate(history) for name, history in beta_histories.items()}
    gates = {
        "primary_gt10_15m_brier_strictly_better_than_geometry_control": _strictly_lower(
            candidate_primary["brier_15m"], control_primary["brier_15m"]
        ),
        "primary_gt10_60m_brier_strictly_better_than_geometry_control": _strictly_lower(
            candidate_primary["brier_60m"], control_primary["brier_60m"]
        ),
        "primary_gt10_two_horizon_mean_logloss_strictly_better_than_geometry_control": _strictly_lower(
            candidate_primary["mean_log_loss_15m_60m"], control_primary["mean_log_loss_15m_60m"]
        ),
        "primary_all_gap_two_horizon_mean_brier_not_higher_than_geometry_control": _not_higher(
            candidate_all["mean_brier_15m_60m"], control_all["mean_brier_15m_60m"]
        ),
        "primary_gt10_two_horizon_mean_brier_strictly_better_than_expanding_empirical_benchmark": _strictly_lower(
            candidate_primary["mean_brier_15m_60m"], benchmark_primary["mean_brier_15m_60m"]
        ),
        "annual_primary_two_horizon_mean_brier_improvement_positive_in_at_least_2_of_3_and_median_positive": three_year_positive_gate(
            annual_improvement
        ),
        "each_beta_component_direction_stable": bool(all(beta_gates.values())),
        "probability_monotonicity_violations_zero": int(monotonicity_violations) == 0,
    }
    eligible = bool(all(gates.values()))
    return {
        "status": "eligible" if eligible else "not_eligible",
        "eligible": eligible,
        "sample": sample,
        "gates": gates,
        "beta_component_direction_gates": beta_gates,
        "annual_primary_control_minus_candidate_mean_brier": annual_improvement,
        "metrics": {
            "candidate_primary_gt10": candidate_primary,
            "geometry_control_primary_gt10": control_primary,
            "empirical_benchmark_primary_gt10": benchmark_primary,
            "candidate_all_gap": candidate_all,
            "geometry_control_all_gap": control_all,
        },
    }


def evaluate_cross_index_shared_nonharm(
    *,
    y15: Sequence[float] | np.ndarray,
    y60: Sequence[float] | np.ndarray,
    abs_gap: Sequence[float] | np.ndarray,
    candidate15: Sequence[float] | np.ndarray,
    candidate60: Sequence[float] | np.ndarray,
    control15: Sequence[float] | np.ndarray,
    control60: Sequence[float] | np.ndarray,
) -> dict:
    """Extra DEV gate for P2_XI_SHARED_1B on CSI300-high."""
    yy15 = _binary(y15, "y15")
    yy60 = _binary(y60, "y60")
    gap = np.asarray(abs_gap, dtype=float)
    c15 = _prob(candidate15, "candidate15")
    c60 = _prob(candidate60, "candidate60")
    k15 = _prob(control15, "control15")
    k60 = _prob(control60, "control60")
    _aligned(yy15, yy60, gap, c15, c60, k15, k60)
    if not np.isfinite(gap).all() or (gap <= 0.0).any():
        raise ValueError("abs_gap must contain finite positive nonzero-gap values")
    gt10 = gap > GT10
    if not gt10.any():
        return {"status": "evidence_insufficient", "passed": False, "gates": {}}
    all_mask = np.ones(len(gap), dtype=bool)
    gates = {
        "CSI300_high_all_gap_two_horizon_mean_brier_not_higher_than_geometry_control": _not_higher(
            two_horizon_mean_brier(yy15, yy60, c15, c60, all_mask),
            two_horizon_mean_brier(yy15, yy60, k15, k60, all_mask),
        ),
        "CSI300_high_gt10_two_horizon_mean_brier_not_higher_than_geometry_control": _not_higher(
            two_horizon_mean_brier(yy15, yy60, c15, c60, gt10),
            two_horizon_mean_brier(yy15, yy60, k15, k60, gt10),
        ),
    }
    passed = bool(all(gates.values()))
    return {"status": "pass" if passed else "fail", "passed": passed, "gates": gates}


def evaluate_future_audit_primary(
    *,
    expected_years: Sequence[int],
    y15: Sequence[float] | np.ndarray,
    y60: Sequence[float] | np.ndarray,
    abs_gap: Sequence[float] | np.ndarray,
    years: Sequence[int] | np.ndarray,
    candidate15: Sequence[float] | np.ndarray,
    candidate60: Sequence[float] | np.ndarray,
    control15: Sequence[float] | np.ndarray,
    control60: Sequence[float] | np.ndarray,
    benchmark15: Sequence[float] | np.ndarray,
    benchmark60: Sequence[float] | np.ndarray,
    monotonicity_violations: int,
) -> dict:
    """Evaluate the same frozen primary gates for V21 Audit A or Audit B."""
    exp_years = tuple(int(v) for v in expected_years)
    if len(exp_years) != 3 or len(set(exp_years)) != 3:
        raise ValueError("future audit must contain exactly three distinct full years")
    y15a, y60a, gap, yr, c15, c60, k15, k60, b15, b60 = _validate_block(
        y15, y60, abs_gap, years, candidate15, candidate60,
        control15, control60, benchmark15, benchmark60,
    )
    if not set(np.unique(yr)).issubset(set(exp_years)):
        raise ValueError("row outside frozen audit calendar entered evaluation")
    gt10 = gap > GT10
    gt30 = gap > GT30
    by_year = {str(year): int(np.sum(gt10 & (yr == year))) for year in exp_years}
    primary_sample_sufficient = bool(
        len(gap) >= 25
        and int(np.sum(gt10)) >= 20
        and all(by_year[str(year)] > 0 for year in exp_years)
    )
    sample = {
        "all_nonzero_gap": int(len(gap)),
        "abs_gap_gt_10bp": int(np.sum(gt10)),
        "abs_gap_gt_30bp": int(np.sum(gt30)),
        "gt30_descriptive_reporting_sufficient": int(np.sum(gt30)) >= 12,
        "by_full_year_gt10": by_year,
        "primary_sufficient": primary_sample_sufficient,
    }
    if not primary_sample_sufficient:
        return {
            "status": "evidence_insufficient",
            "passed": False,
            "sample": sample,
            "gates": {},
            "annual_primary_control_minus_candidate_mean_brier": [],
        }

    candidate_primary = _metric_snapshot(y15a, y60a, c15, c60, gt10)
    control_primary = _metric_snapshot(y15a, y60a, k15, k60, gt10)
    benchmark_primary = _metric_snapshot(y15a, y60a, b15, b60, gt10)
    all_mask = np.ones(len(gap), dtype=bool)
    candidate_all = _metric_snapshot(y15a, y60a, c15, c60, all_mask)
    control_all = _metric_snapshot(y15a, y60a, k15, k60, all_mask)

    annual_improvement: list[float] = []
    for year in exp_years:
        mask = gt10 & (yr == year)
        annual_improvement.append(float(
            two_horizon_mean_brier(y15a, y60a, k15, k60, mask)
            - two_horizon_mean_brier(y15a, y60a, c15, c60, mask)
        ))

    gates = {
        "CSI500_high_gt10_15m_brier_strictly_lower_than_frozen_geometry_control": _strictly_lower(
            candidate_primary["brier_15m"], control_primary["brier_15m"]
        ),
        "CSI500_high_gt10_60m_brier_strictly_lower_than_frozen_geometry_control": _strictly_lower(
            candidate_primary["brier_60m"], control_primary["brier_60m"]
        ),
        "CSI500_high_gt10_two_horizon_mean_logloss_strictly_lower_than_frozen_geometry_control": _strictly_lower(
            candidate_primary["mean_log_loss_15m_60m"], control_primary["mean_log_loss_15m_60m"]
        ),
        "CSI500_high_all_gap_two_horizon_mean_brier_not_higher_than_frozen_geometry_control": _not_higher(
            candidate_all["mean_brier_15m_60m"], control_all["mean_brier_15m_60m"]
        ),
        "CSI500_high_gt10_two_horizon_mean_brier_strictly_lower_than_frozen_DEV_empirical_benchmark": _strictly_lower(
            candidate_primary["mean_brier_15m_60m"], benchmark_primary["mean_brier_15m_60m"]
        ),
        "calendar_primary_two_horizon_mean_brier_improvement_positive_in_at_least_2_of_3_full_years_and_median_positive": three_year_positive_gate(
            annual_improvement
        ),
        "probability_monotonicity_violations_zero": int(monotonicity_violations) == 0,
    }
    passed = bool(all(gates.values()))
    return {
        "status": "pass" if passed else "not_confirmed",
        "passed": passed,
        "sample": sample,
        "gates": gates,
        "annual_primary_control_minus_candidate_mean_brier": annual_improvement,
        "metrics": {
            "candidate_primary_gt10": candidate_primary,
            "geometry_control_primary_gt10": control_primary,
            "frozen_DEV_empirical_benchmark_primary_gt10": benchmark_primary,
            "candidate_all_gap": candidate_all,
            "geometry_control_all_gap": control_all,
        },
    }
