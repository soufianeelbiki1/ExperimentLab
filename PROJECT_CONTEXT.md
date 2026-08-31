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
- Decision thresholds and acceptable guardrail harm must be specified before interpreting results.

## Current state

- Balanced synthetic experiment generator with pre-period activity, conversion, revenue, sessions, and support-contact guardrail outcomes.
- DuckDB experiment warehouse with experiment, assignment, and outcome grains plus a variant-level mart.
- Sample-ratio-mismatch test for assignment integrity.
- Two-proportion effect estimator with absolute/relative lift, z-test p-value, and 95% confidence interval.
- CUPED adjustment primitive with regression tests for mean preservation and variance reduction.
- Deterministic percentile bootstrap for skewed treatment-minus-control mean metrics such as revenue per assigned user.
- Explicit `ship`, `hold`, and `do_not_ship` decision engine: SRM blocks interpretation, configured guardrail harm can veto shipping, and the complete primary interval must clear the pre-specified minimum useful effect to ship.
- Markdown decision output explicitly labels evidence as a synthetic scenario.
- Decision-policy documentation describes rule ordering, guardrail semantics, and current statistical limitations.
- CI on Python 3.11/3.12 with lint, formatting, and tests.

## Next highest-value slice

Add funnel event tables and retention/cohort models, bootstrap-derived guardrail uncertainty rather than point-estimate-only guardrails, power/MDE utilities, and a reproducible end-to-end experiment analysis function that builds the decision inputs from warehouse data. Then add sequential-look and multiple-testing demonstrations that show how naive repeated testing can inflate false-positive risk.
