import pytest

from experimentlab.power import minimum_detectable_effect, required_sample_size_per_arm


def test_smaller_mde_requires_more_sample() -> None:
    small_effect = required_sample_size_per_arm(0.10, 0.01)
    larger_effect = required_sample_size_per_arm(0.10, 0.02)

    assert small_effect.sample_size_per_arm > larger_effect.sample_size_per_arm


def test_higher_power_requires_more_sample() -> None:
    standard = required_sample_size_per_arm(0.10, 0.02, power=0.80)
    strict = required_sample_size_per_arm(0.10, 0.02, power=0.90)

    assert strict.sample_size_per_arm > standard.sample_size_per_arm


def test_mde_round_trip_is_consistent_with_sample_budget() -> None:
    planned = required_sample_size_per_arm(0.12, 0.015, power=0.80)
    recovered = minimum_detectable_effect(
        0.12,
        planned.sample_size_per_arm,
        power=0.80,
    )

    assert recovered.sample_size_per_arm <= planned.sample_size_per_arm
    assert recovered.absolute_mde == pytest.approx(0.015, rel=0.02)


def test_decrease_direction_returns_negative_effect() -> None:
    plan = minimum_detectable_effect(0.20, 10_000, direction="decrease")

    assert plan.absolute_mde < 0
    assert plan.target_rate < plan.baseline_rate


def test_invalid_planning_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        required_sample_size_per_arm(0.0, 0.01)
    with pytest.raises(ValueError):
        required_sample_size_per_arm(0.10, 0.0)
    with pytest.raises(ValueError):
        minimum_detectable_effect(0.10, 1)
