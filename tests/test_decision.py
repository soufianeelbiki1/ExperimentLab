from __future__ import annotations

import numpy as np
import pytest

from experimentlab import (
    ExperimentDecisionInput,
    bootstrap_mean_difference,
    decide_experiment,
    generate_experiment,
)


def test_bootstrap_revenue_difference_is_deterministic() -> None:
    experiment = generate_experiment(seed=17, users=1000, treatment_absolute_uplift=0.03)
    control = experiment.revenue[experiment.variants == "control"]
    treatment = experiment.revenue[experiment.variants == "treatment"]

    first = bootstrap_mean_difference(control, treatment, seed=23, resamples=800)
    second = bootstrap_mean_difference(control, treatment, seed=23, resamples=800)

    assert first == second
    assert first.resamples == 800
    assert first.confidence_level == 0.95
    assert first.ci_low <= first.difference <= first.ci_high


def test_bootstrap_rejects_non_finite_inputs() -> None:
    with pytest.raises(ValueError, match="finite"):
        bootstrap_mean_difference(
            np.array([1.0, np.nan]),
            np.array([1.0, 2.0]),
            resamples=100,
        )


def test_srm_failure_forces_hold_even_with_strong_primary_effect() -> None:
    result = decide_experiment(
        ExperimentDecisionInput(
            srm_mismatch=True,
            primary_effect=0.04,
            primary_ci_low=0.02,
            primary_ci_high=0.06,
            minimum_useful_effect=0.01,
            guardrail_effect=0.0,
            maximum_guardrail_harm=0.005,
        )
    )

    assert result.decision == "hold"
    assert any("Sample Ratio Mismatch" in reason for reason in result.reasons)


def test_guardrail_breach_vetoes_shipping() -> None:
    result = decide_experiment(
        ExperimentDecisionInput(
            srm_mismatch=False,
            primary_effect=0.04,
            primary_ci_low=0.02,
            primary_ci_high=0.06,
            minimum_useful_effect=0.01,
            guardrail_effect=0.008,
            maximum_guardrail_harm=0.005,
        )
    )

    assert result.decision == "do_not_ship"
    assert any("guardrail" in reason.lower() for reason in result.reasons)


def test_full_interval_above_business_threshold_ships() -> None:
    result = decide_experiment(
        ExperimentDecisionInput(
            srm_mismatch=False,
            primary_effect=0.025,
            primary_ci_low=0.015,
            primary_ci_high=0.035,
            minimum_useful_effect=0.01,
            guardrail_effect=0.001,
            maximum_guardrail_harm=0.005,
        )
    )

    assert result.decision == "ship"
    assert result.data_scope == "synthetic"
    assert "Evidence scope" in result.to_markdown()
    assert "synthetic" in result.to_markdown().lower()


def test_interval_below_useful_effect_does_not_ship() -> None:
    result = decide_experiment(
        ExperimentDecisionInput(
            srm_mismatch=False,
            primary_effect=0.004,
            primary_ci_low=-0.002,
            primary_ci_high=0.009,
            minimum_useful_effect=0.01,
            guardrail_effect=0.0,
            maximum_guardrail_harm=0.005,
        )
    )

    assert result.decision == "do_not_ship"


def test_ambiguous_interval_holds_for_more_evidence() -> None:
    result = decide_experiment(
        ExperimentDecisionInput(
            srm_mismatch=False,
            primary_effect=0.012,
            primary_ci_low=0.004,
            primary_ci_high=0.020,
            minimum_useful_effect=0.01,
            guardrail_effect=0.0,
            maximum_guardrail_harm=0.005,
        )
    )

    assert result.decision == "hold"
