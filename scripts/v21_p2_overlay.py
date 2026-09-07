#!/usr/bin/env python3
"""Pure math helpers for the frozen V21 P2 candidate family.

This module intentionally performs no file I/O and cannot open V21_DEV or audit
outcomes.  It only codifies the preregistered residual-hazard overlay and the
complexity-first candidate ladder so the math can be tested before data access.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import minimize_scalar

PROB_EPS = 1e-6
BETA_BOUNDS = (-6.0, 6.0)
CANDIDATE_LADDER = (
    "P2_XI_SHARED_1B",
    "P2_CSI500_SHARED_1B",
    "P2_CSI500_STAGE_2B",
)


@dataclass(frozen=True)
class TrainingStandardizer:
    mean: float
    scale: float

    def transform(self, values: Sequence[float] | np.ndarray) -> np.ndarray:
        x = np.asarray(values, dtype=float)
        if not np.isfinite(x).all():
            raise ValueError("non-finite P2 value")
        if not np.isfinite(self.scale) or self.scale <= 0.0:
            raise ValueError("invalid frozen P2 scale")
        return (x - self.mean) / self.scale


@dataclass(frozen=True)
class OffsetCell:
    """One training risk-set cell for a shared beta objective."""

    base_hazard: np.ndarray
    z_p2: np.ndarray
    target: np.ndarray

    def __post_init__(self) -> None:
        h = np.asarray(self.base_hazard, dtype=float)
        z = np.asarray(self.z_p2, dtype=float)
        y = np.asarray(self.target, dtype=float)
        if h.ndim != 1 or z.ndim != 1 or y.ndim != 1:
            raise ValueError("offset cell arrays must be one-dimensional")
        if not (len(h) == len(z) == len(y)) or len(h) == 0:
            raise ValueError("offset cell arrays must be non-empty and aligned")
        if not np.isfinite(h).all() or not np.isfinite(z).all() or not np.isfinite(y).all():
            raise ValueError("offset cell contains non-finite values")
        if ((y != 0.0) & (y != 1.0)).any():
            raise ValueError("target must be binary")


def fit_standardizer(values: Sequence[float] | np.ndarray) -> TrainingStandardizer:
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("P2 training values must be finite one-dimensional data")
    mean = float(np.mean(x))
    scale = float(np.std(x, ddof=0))
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("P2 training values have zero/invalid population scale")
    return TrainingStandardizer(mean=mean, scale=scale)


def _logit(prob: Sequence[float] | np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(prob, dtype=float), PROB_EPS, 1.0 - PROB_EPS)
    if not np.isfinite(p).all():
        raise ValueError("non-finite probability")
    return np.log(p / (1.0 - p))


def _expit(value: Sequence[float] | np.ndarray) -> np.ndarray:
    x = np.asarray(value, dtype=float)
    out = np.empty_like(x, dtype=float)
    pos = x >= 0.0
    out[pos] = 1.0 / (1.0 + np.exp(-x[pos]))
    neg = ~pos
    ex = np.exp(x[neg])
    out[neg] = ex / (1.0 + ex)
    return out


def apply_beta(
    base_hazard: Sequence[float] | np.ndarray,
    z_p2: Sequence[float] | np.ndarray,
    beta: float,
) -> np.ndarray:
    h = np.asarray(base_hazard, dtype=float)
    z = np.asarray(z_p2, dtype=float)
    if h.shape != z.shape:
        raise ValueError("base hazard and P2 arrays must align")
    if not np.isfinite(float(beta)):
        raise ValueError("beta must be finite")
    return _expit(_logit(h) + float(beta) * z)


def cumulative_probs(
    h15: Sequence[float] | np.ndarray,
    h60: Sequence[float] | np.ndarray,
    h_eod: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = np.asarray(h15, dtype=float)
    b = np.asarray(h60, dtype=float)
    c = np.asarray(h_eod, dtype=float)
    if not (a.shape == b.shape == c.shape):
        raise ValueError("hazard arrays must align")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or not np.isfinite(c).all():
        raise ValueError("non-finite hazard")
    if ((a < 0.0) | (a > 1.0) | (b < 0.0) | (b > 1.0) | (c < 0.0) | (c > 1.0)).any():
        raise ValueError("hazards must lie in [0,1]")
    p15 = a
    p60 = 1.0 - (1.0 - a) * (1.0 - b)
    peod = 1.0 - (1.0 - a) * (1.0 - b) * (1.0 - c)
    return p15, p60, peod


def monotonicity_violations(
    p15: Sequence[float] | np.ndarray,
    p60: Sequence[float] | np.ndarray,
    peod: Sequence[float] | np.ndarray,
    eps: float = 1e-12,
) -> int:
    a = np.asarray(p15, dtype=float)
    b = np.asarray(p60, dtype=float)
    c = np.asarray(peod, dtype=float)
    if not (a.shape == b.shape == c.shape):
        raise ValueError("probability arrays must align")
    bad = (~np.isfinite(a)) | (~np.isfinite(b)) | (~np.isfinite(c))
    bad |= (a < -eps) | (b < a - eps) | (c < b - eps) | (c > 1.0 + eps)
    return int(np.sum(bad))


def binary_log_loss(target: Sequence[float] | np.ndarray, prob: Sequence[float] | np.ndarray) -> float:
    y = np.asarray(target, dtype=float)
    p = np.clip(np.asarray(prob, dtype=float), PROB_EPS, 1.0 - PROB_EPS)
    if y.shape != p.shape or y.ndim != 1 or len(y) == 0:
        raise ValueError("target/probability arrays must be aligned non-empty vectors")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("non-finite target/probability")
    if ((y != 0.0) & (y != 1.0)).any():
        raise ValueError("target must be binary")
    return float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p)))


def shared_beta_objective(beta: float, cells: Iterable[OffsetCell]) -> float:
    """Equal-weight mean of cell-level log losses, not row-count weighting."""
    losses: list[float] = []
    for cell in cells:
        p = apply_beta(cell.base_hazard, cell.z_p2, beta)
        losses.append(binary_log_loss(cell.target, p))
    if not losses:
        raise ValueError("shared beta objective requires at least one cell")
    return float(np.mean(losses))


def fit_shared_beta(cells: Sequence[OffsetCell], bounds: tuple[float, float] = BETA_BOUNDS) -> dict:
    if not cells:
        raise ValueError("no cells supplied")
    lo, hi = map(float, bounds)
    if not np.isfinite([lo, hi]).all() or lo >= hi:
        raise ValueError("invalid beta bounds")
    result = minimize_scalar(
        lambda b: shared_beta_objective(float(b), cells),
        bounds=(lo, hi),
        method="bounded",
        options={"xatol": 1e-10},
    )
    return {
        "beta": float(result.x),
        "objective": float(result.fun),
        "success": bool(result.success),
        "n_cells": int(len(cells)),
        "bounds": [lo, hi],
    }


def first_eligible_candidate(eligibility: Mapping[str, bool]) -> str | None:
    """Complexity-first selection: later candidates can never leapfrog."""
    unknown = set(eligibility) - set(CANDIDATE_LADDER)
    if unknown:
        raise ValueError(f"unknown candidate ids: {sorted(unknown)}")
    for candidate in CANDIDATE_LADDER:
        if eligibility.get(candidate, False):
            return candidate
    return None


def positive_sign_gate(beta_history: Sequence[float]) -> bool:
    """Frozen DEV OOF sign gate: >=2/3 positive and positive median."""
    b = np.asarray(beta_history, dtype=float)
    if b.ndim != 1 or len(b) != 3 or not np.isfinite(b).all():
        raise ValueError("beta history must contain exactly three finite expanding-fold fits")
    return bool(int(np.sum(b > 0.0)) >= 2 and float(np.median(b)) > 0.0)


def annual_improvement_gate(improvements: Sequence[float]) -> bool:
    """Frozen DEV OOF annual gate: >=2/3 improvements and positive median."""
    x = np.asarray(improvements, dtype=float)
    if x.ndim != 1 or len(x) != 3 or not np.isfinite(x).all():
        raise ValueError("annual improvement history must contain exactly three finite years")
    return bool(int(np.sum(x > 0.0)) >= 2 and float(np.median(x)) > 0.0)
