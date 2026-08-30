# ExperimentLab operating brief

ExperimentLab is the product analytics and experimentation flagship. Its purpose is to show trustworthy causal/experimental reasoning, not just statistical API usage.

## Guardrails

- Synthetic observations must stay explicitly synthetic and reproducible.
- Validate experiment assignment integrity before interpreting treatment effects.
- Report absolute lift, relative lift, uncertainty, and business impact separately.
- Do not equate statistical significance with a shipping decision.
- Guardrail metrics and potential harm must be considered alongside the primary metric.
- Sequential peeking, multiple testing, power/MDE, and heterogeneity require explicit caveats.
- CUPED/covariate adjustment must use pre-treatment covariates only.

## Current slice

- Balanced synthetic experiment generator with pre-period activity, conversion, revenue, sessions, and support-contact guardrail outcomes.
- DuckDB experiment warehouse with experiment, assignment, and outcome grains plus a variant-level mart.
- Sample-ratio-mismatch test for assignment integrity.
- Two-proportion effect estimator with absolute/relative lift, z-test p-value, and 95% confidence interval.
- CUPED adjustment primitive with regression tests for mean preservation and variance reduction.
- CI on Python 3.11/3.12 with lint, formatting, and tests.

## Next highest-value slice

Add funnel event tables, retention/cohort models, bootstrap confidence intervals for revenue, explicit guardrail decision rules, power/MDE utilities, and a reproducible experiment decision report that can return `ship`, `hold`, or `do_not_ship` with documented reasons. Then add sequential-look and multiple-testing demonstrations that show how naive analysis can produce false positives.
