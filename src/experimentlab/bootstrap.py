from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BootstrapDifference:
    control_mean: float
    treatment_mean: float
    difference: float
    ci_low: float
    ci_high: float
    confidence_level: float
    resamples: int


def bootstrap_mean_difference(
    control: np.ndarray,
    treatment: np.ndarray,
    *,
    seed: int = 20260831,
    resamples: int = 5000,
    confidence_level: float = 0.95,
) -> BootstrapDifference:
    """Estimate a percentile-bootstrap interval for treatment minus control mean.

    Groups are resampled independently so assignment-group sizes stay fixed. The function is
    deterministic for a fixed seed and intentionally makes no normality assumption about the
    metric, which is useful for skewed revenue-per-assigned-user outcomes.
    """

    control = np.asarray(control, dtype=float)
    treatment = np.asarray(treatment, dtype=float)
    if control.ndim != 1 or treatment.ndim != 1:
        raise ValueError("control and treatment must be one-dimensional")
    if control.size < 2 or treatment.size < 2:
        raise ValueError("each group must contain at least two observations")
    if not np.isfinite(control).all() or not np.isfinite(treatment).all():
        raise ValueError("bootstrap inputs must contain only finite values")
    if resamples < 100:
        raise ValueError("resamples must be at least 100")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")

    rng = np.random.default_rng(seed)
    differences = np.empty(resamples, dtype=float)
    for index in range(resamples):
        control_sample = rng.choice(control, size=control.size, replace=True)
        treatment_sample = rng.choice(treatment, size=treatment.size, replace=True)
        differences[index] = treatment_sample.mean() - control_sample.mean()

    alpha = 1 - confidence_level
    ci_low, ci_high = np.quantile(differences, [alpha / 2, 1 - alpha / 2])
    control_mean = float(control.mean())
    treatment_mean = float(treatment.mean())
    return BootstrapDifference(
        control_mean=control_mean,
        treatment_mean=treatment_mean,
        difference=treatment_mean - control_mean,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        confidence_level=confidence_level,
        resamples=resamples,
    )
