from __future__ import annotations

import numpy as np

from experimentlab.statistics import cuped_adjust, sample_ratio_mismatch, two_proportion_test
from experimentlab.synthetic import generate_experiment
from experimentlab.warehouse import build_experiment_warehouse


def test_generator_is_balanced_and_reproducible() -> None:
    first = generate_experiment(seed=9, users=1000)
    second = generate_experiment(seed=9, users=1000)

    assert first.user_ids == second.user_ids
    assert np.array_equal(first.variants, second.variants)
    assert np.array_equal(first.converted, second.converted)
    assert int(np.sum(first.variants == "control")) == 500
    assert int(np.sum(first.variants == "treatment")) == 500


def test_srm_gate_accepts_balanced_assignment_and_rejects_skew() -> None:
    balanced = sample_ratio_mismatch(5000, 5000)
    skewed = sample_ratio_mismatch(6000, 4000)

    assert balanced.mismatch is False
    assert balanced.p_value == 1.0
    assert skewed.mismatch is True
    assert skewed.p_value < 0.01


def test_two_proportion_test_reports_effect_size_and_interval() -> None:
    result = two_proportion_test(
        control_successes=100,
        control_n=1000,
        treatment_successes=130,
        treatment_n=1000,
    )

    assert result.control_rate == 0.10
    assert result.treatment_rate == 0.13
    assert abs(result.absolute_lift - 0.03) < 1e-12
    assert result.relative_lift is not None
    assert abs(result.relative_lift - 0.30) < 1e-12
    assert result.p_value < 0.05
    assert result.ci_low > 0


def test_cuped_preserves_mean_and_reduces_variance_when_covariate_is_predictive() -> None:
    covariate = np.arange(1, 101, dtype=float)
    outcome = 3.0 * covariate + np.tile(np.array([-1.0, 1.0]), 50)

    adjusted, theta = cuped_adjust(outcome, covariate)

    assert theta > 0
    assert abs(float(adjusted.mean()) - float(outcome.mean())) < 1e-10
    assert float(np.var(adjusted, ddof=1)) < float(np.var(outcome, ddof=1))


def test_experiment_mart_reconciles_assignment_and_outcome_grains() -> None:
    connection = build_experiment_warehouse(generate_experiment(seed=12, users=1200))

    assignment_count = connection.execute("select count(*) from fact_assignment").fetchone()[0]
    outcome_count = connection.execute("select count(*) from fact_outcome").fetchone()[0]
    mart_count = connection.execute("select sum(assigned_users) from mart_experiment_variant").fetchone()[0]
    invalid_rates = connection.execute(
        "select count(*) from mart_experiment_variant where conversion_rate < 0 or conversion_rate > 1"
    ).fetchone()[0]

    assert assignment_count == 1200
    assert outcome_count == 1200
    assert mart_count == 1200
    assert invalid_rates == 0
