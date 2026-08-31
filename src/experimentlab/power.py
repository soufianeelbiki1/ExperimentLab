from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt
from statistics import NormalDist


@dataclass(frozen=True)
class ProportionPowerPlan:
    baseline_rate: float
    target_rate: float
    absolute_mde: float
    relative_mde: float | None
    alpha: float
    power: float
    sample_size_per_arm: int


def required_sample_size_per_arm(
    baseline_rate: float,
    absolute_mde: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
) -> ProportionPowerPlan:
    """Approximate equal-allocation sample size for a two-sided proportion test."""

    if not 0 < baseline_rate < 1:
        raise ValueError("baseline_rate must be between 0 and 1")
    if absolute_mde == 0:
        raise ValueError("absolute_mde must be non-zero")
    target_rate = baseline_rate + absolute_mde
    if not 0 < target_rate < 1:
        raise ValueError("baseline_rate + absolute_mde must remain between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")

    normal = NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha / 2)
    z_power = normal.inv_cdf(power)
    pooled = (baseline_rate + target_rate) / 2
    numerator = (
        z_alpha * sqrt(2 * pooled * (1 - pooled))
        + z_power * sqrt(baseline_rate * (1 - baseline_rate) + target_rate * (1 - target_rate))
    ) ** 2
    sample_size = ceil(numerator / (absolute_mde**2))
    relative_mde = absolute_mde / baseline_rate if baseline_rate else None
    return ProportionPowerPlan(
        baseline_rate=baseline_rate,
        target_rate=target_rate,
        absolute_mde=absolute_mde,
        relative_mde=relative_mde,
        alpha=alpha,
        power=power,
        sample_size_per_arm=sample_size,
    )


def minimum_detectable_effect(
    baseline_rate: float,
    sample_size_per_arm: int,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
    direction: str = "increase",
) -> ProportionPowerPlan:
    """Find the smallest absolute effect supported by the declared sample size.

    Uses binary search over the same normal-approximation planning equation as
    ``required_sample_size_per_arm``. This is planning guidance, not a promise
    of realized power under violated assumptions or sequential peeking.
    """

    if sample_size_per_arm <= 1:
        raise ValueError("sample_size_per_arm must be greater than 1")
    if direction not in {"increase", "decrease"}:
        raise ValueError("direction must be 'increase' or 'decrease'")

    max_effect = (1 - baseline_rate - 1e-9) if direction == "increase" else baseline_rate - 1e-9
    if max_effect <= 0:
        raise ValueError("baseline_rate leaves no room in the requested direction")

    sign = 1.0 if direction == "increase" else -1.0
    low = 1e-9
    high = max_effect
    for _ in range(80):
        midpoint = (low + high) / 2
        plan = required_sample_size_per_arm(
            baseline_rate,
            sign * midpoint,
            alpha=alpha,
            power=power,
        )
        if plan.sample_size_per_arm <= sample_size_per_arm:
            high = midpoint
        else:
            low = midpoint

    return required_sample_size_per_arm(
        baseline_rate,
        sign * high,
        alpha=alpha,
        power=power,
    )
