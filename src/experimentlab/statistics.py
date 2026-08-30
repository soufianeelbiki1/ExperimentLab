from __future__ import annotations

from dataclasses import dataclass
from math import erfc, sqrt

import numpy as np


@dataclass(frozen=True)
class SrmResult:
    chi_square: float
    p_value: float
    observed_treatment_share: float
    expected_treatment_share: float
    mismatch: bool


@dataclass(frozen=True)
class ProportionTestResult:
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float | None
    z_score: float
    p_value: float
    ci_low: float
    ci_high: float


def sample_ratio_mismatch(
    control_n: int,
    treatment_n: int,
    expected_treatment_share: float = 0.5,
    alpha: float = 0.01,
) -> SrmResult:
    if control_n < 0 or treatment_n < 0 or control_n + treatment_n == 0:
        raise ValueError("assignment counts must be non-negative with a positive total")
    if not 0 < expected_treatment_share < 1:
        raise ValueError("expected_treatment_share must be between 0 and 1")

    total = control_n + treatment_n
    expected_treatment = total * expected_treatment_share
    expected_control = total - expected_treatment
    chi_square = (
        (treatment_n - expected_treatment) ** 2 / expected_treatment
        + (control_n - expected_control) ** 2 / expected_control
    )
    p_value = erfc(sqrt(chi_square / 2.0))
    observed_share = treatment_n / total
    return SrmResult(
        chi_square=chi_square,
        p_value=p_value,
        observed_treatment_share=observed_share,
        expected_treatment_share=expected_treatment_share,
        mismatch=p_value < alpha,
    )


def two_proportion_test(
    control_successes: int,
    control_n: int,
    treatment_successes: int,
    treatment_n: int,
) -> ProportionTestResult:
    if control_n <= 0 or treatment_n <= 0:
        raise ValueError("group sizes must be positive")
    if not 0 <= control_successes <= control_n or not 0 <= treatment_successes <= treatment_n:
        raise ValueError("success counts must be within group sizes")

    control_rate = control_successes / control_n
    treatment_rate = treatment_successes / treatment_n
    absolute_lift = treatment_rate - control_rate
    relative_lift = absolute_lift / control_rate if control_rate > 0 else None

    pooled = (control_successes + treatment_successes) / (control_n + treatment_n)
    pooled_se = sqrt(pooled * (1 - pooled) * (1 / control_n + 1 / treatment_n))
    z_score = absolute_lift / pooled_se if pooled_se > 0 else 0.0
    p_value = erfc(abs(z_score) / sqrt(2.0))

    unpooled_se = sqrt(
        control_rate * (1 - control_rate) / control_n
        + treatment_rate * (1 - treatment_rate) / treatment_n
    )
    z_975 = 1.959963984540054
    return ProportionTestResult(
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        absolute_lift=absolute_lift,
        relative_lift=relative_lift,
        z_score=z_score,
        p_value=p_value,
        ci_low=absolute_lift - z_975 * unpooled_se,
        ci_high=absolute_lift + z_975 * unpooled_se,
    )


def cuped_adjust(outcome: np.ndarray, covariate: np.ndarray) -> tuple[np.ndarray, float]:
    outcome = np.asarray(outcome, dtype=float)
    covariate = np.asarray(covariate, dtype=float)
    if outcome.ndim != 1 or covariate.ndim != 1 or outcome.size != covariate.size:
        raise ValueError("outcome and covariate must be one-dimensional arrays of equal length")
    if outcome.size < 2:
        raise ValueError("at least two observations are required")

    covariate_variance = float(np.var(covariate, ddof=1))
    if covariate_variance == 0:
        return outcome.copy(), 0.0

    covariance = float(np.cov(outcome, covariate, ddof=1)[0, 1])
    theta = covariance / covariate_variance
    adjusted = outcome - theta * (covariate - covariate.mean())
    return adjusted, theta
