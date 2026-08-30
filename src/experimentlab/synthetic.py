from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass(frozen=True)
class SyntheticExperiment:
    experiment_id: str
    user_ids: list[str]
    variants: np.ndarray
    assigned_at: datetime
    pre_period_activity: np.ndarray
    converted: np.ndarray
    revenue: np.ndarray
    sessions: np.ndarray
    support_contact: np.ndarray


def generate_experiment(
    seed: int = 20260831,
    users: int = 4000,
    treatment_absolute_uplift: float = 0.02,
) -> SyntheticExperiment:
    """Generate an exactly balanced, reproducible synthetic product experiment."""

    if users < 100 or users % 2 != 0:
        raise ValueError("users must be an even integer of at least 100")
    if not -0.2 <= treatment_absolute_uplift <= 0.2:
        raise ValueError("treatment_absolute_uplift is outside the supported synthetic range")

    rng = np.random.default_rng(seed)
    variants = np.array(["control"] * (users // 2) + ["treatment"] * (users // 2))
    rng.shuffle(variants)

    pre_period_activity = rng.gamma(shape=2.2, scale=2.0, size=users)
    baseline_probability = np.clip(0.05 + 0.018 * pre_period_activity, 0.02, 0.35)
    treatment_effect = np.where(variants == "treatment", treatment_absolute_uplift, 0.0)
    conversion_probability = np.clip(baseline_probability + treatment_effect, 0.0, 0.95)
    converted = rng.binomial(1, conversion_probability, size=users)

    order_value = rng.lognormal(mean=3.7, sigma=0.45, size=users)
    revenue = converted * order_value
    sessions = 1 + rng.poisson(lam=2.0 + 0.25 * pre_period_activity, size=users)
    support_probability = np.where(variants == "treatment", 0.031, 0.030)
    support_contact = rng.binomial(1, support_probability, size=users)

    return SyntheticExperiment(
        experiment_id="checkout-copy-v1-synthetic",
        user_ids=[f"usr-{index + 1:06d}" for index in range(users)],
        variants=variants,
        assigned_at=datetime(2026, 8, 1, 9, 0, 0),
        pre_period_activity=pre_period_activity,
        converted=converted,
        revenue=revenue,
        sessions=sessions,
        support_contact=support_contact,
    )
