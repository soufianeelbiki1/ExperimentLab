# Experiment decision policy

All current examples use reproducible synthetic experiments.

## Decision order

1. **Assignment integrity** — Sample Ratio Mismatch is evaluated before treatment effects. A failed SRM gate returns `hold` because a broken randomization process can invalidate the comparison.
2. **Guardrail harm** — an undesirable guardrail increase above the pre-specified tolerance returns `do_not_ship`, even when the primary metric improves.
3. **Minimum useful effect** — shipping requires the *entire* primary-metric confidence interval to be at or above a pre-specified business threshold. Statistical significance versus zero is not enough.
4. **Negative/insufficient business evidence** — if the interval is entirely below the minimum useful effect, return `do_not_ship`.
5. **Ambiguity** — if the interval crosses the business threshold, return `hold` for more evidence.

## Revenue uncertainty

Revenue per assigned user is typically zero-inflated and right-skewed. ExperimentLab therefore includes a percentile bootstrap for treatment-minus-control mean revenue rather than treating a normal approximation as automatically appropriate. Groups are resampled independently and group sizes are held fixed.

The bootstrap is deterministic for a fixed random seed so CI regressions can be tested. The current percentile interval is a portfolio reference implementation, not a claim that percentile bootstrap is optimal for every metric or sample size.

## Guardrail semantics

The decision engine treats a positive guardrail effect as harm. For the synthetic support-contact metric, for example, `treatment - control > 0` means treatment generated more support contacts. The maximum acceptable harm must be chosen before interpreting the experiment; changing it after seeing results would undermine the decision rule.

## Limitations

The current policy does not yet model sequential peeking, multiple comparisons, cluster randomization, interference, missing-not-at-random outcomes, or heterogeneous treatment effects. Those are explicit later slices rather than hidden assumptions.
