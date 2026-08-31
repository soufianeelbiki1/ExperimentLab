from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np

from experimentlab.bootstrap import bootstrap_mean_difference
from experimentlab.decision import ExperimentDecisionInput, decide_experiment
from experimentlab.power import minimum_detectable_effect
from experimentlab.statistics import sample_ratio_mismatch, two_proportion_test
from experimentlab.warehouse import build_experiment_warehouse

MINIMUM_USEFUL_CONVERSION_EFFECT = 0.005
MAXIMUM_SUPPORT_CONTACT_HARM = 0.01

STYLES = """
:root {
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  color: #172033;
  background: #f5f6f8;
}
* { box-sizing: border-box; }
body { margin: 0; }
main { max-width: 1080px; margin: auto; padding: 40px 24px 64px; }
h1 { font-size: clamp(2rem, 6vw, 4rem); margin: 5px 0 8px; }
h2 { font-size: 1.1rem; margin: 0 0 15px; }
.sub { max-width: 760px; line-height: 1.6; color: #647083; }
.note { font-size: .82rem; color: #707a89; }
.cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 24px 0;
}
.card, .panel {
  background: white;
  border: 1px solid #dfe4ea;
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(20, 30, 50, .05);
}
.card { padding: 18px; }
.card span { color: #707a89; font-size: .8rem; text-transform: uppercase; }
.card strong { display: block; margin-top: 8px; font-size: 1.6rem; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.panel { padding: 20px; }
.full { margin-top: 18px; }
.decision { border-left: 5px solid #475569; }
.decision-ship { border-left-color: #16a34a; }
.decision-hold { border-left-color: #d97706; }
.decision-do_not_ship { border-left-color: #dc2626; }
.decision strong { font-size: 1.65rem; text-transform: uppercase; }
table { width: 100%; border-collapse: collapse; font-size: .9rem; }
th, td { padding: 10px 8px; text-align: left; border-bottom: 1px solid #edf0f3; }
th { color: #707a89; font-weight: 600; }
ul { padding-left: 20px; line-height: 1.6; }
@media (max-width: 800px) {
  .cards { grid-template-columns: 1fr 1fr; }
  .grid { grid-template-columns: 1fr; }
}
@media (max-width: 500px) { .cards { grid-template-columns: 1fr; } }
"""


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_report_html(connection: duckdb.DuckDBPyConnection) -> str:
    variant_rows = connection.execute(
        """
        select
            a.variant,
            count(*)::bigint as assigned,
            count(*) filter (where o.converted)::bigint as conversions,
            avg(o.revenue) as revenue_per_user,
            avg(case when o.support_contact then 1.0 else 0.0 end) as support_rate
        from fact_assignment a
        join fact_outcome o using (user_id, experiment_id)
        group by a.variant
        order by a.variant
        """
    ).fetchall()
    if len(variant_rows) != 2:
        raise ValueError("decision report requires exactly control and treatment variants")

    by_variant = {str(row[0]): row for row in variant_rows}
    if "control" not in by_variant or "treatment" not in by_variant:
        raise ValueError("decision report requires control and treatment variants")

    control = by_variant["control"]
    treatment = by_variant["treatment"]
    control_n = int(control[1])
    treatment_n = int(treatment[1])
    control_conversions = int(control[2])
    treatment_conversions = int(treatment[2])

    srm = sample_ratio_mismatch(control_n, treatment_n)
    conversion = two_proportion_test(
        control_conversions,
        control_n,
        treatment_conversions,
        treatment_n,
    )
    support_effect = float(treatment[4]) - float(control[4])
    decision = decide_experiment(
        ExperimentDecisionInput(
            srm_mismatch=srm.mismatch,
            primary_effect=conversion.absolute_lift,
            primary_ci_low=conversion.ci_low,
            primary_ci_high=conversion.ci_high,
            minimum_useful_effect=MINIMUM_USEFUL_CONVERSION_EFFECT,
            guardrail_effect=support_effect,
            maximum_guardrail_harm=MAXIMUM_SUPPORT_CONTACT_HARM,
        )
    )

    control_revenue = np.asarray(
        [
            row[0]
            for row in connection.execute(
                """
                select o.revenue
                from fact_assignment a
                join fact_outcome o using (user_id, experiment_id)
                where a.variant = 'control'
                order by a.user_id
                """
            ).fetchall()
        ],
        dtype=float,
    )
    treatment_revenue = np.asarray(
        [
            row[0]
            for row in connection.execute(
                """
                select o.revenue
                from fact_assignment a
                join fact_outcome o using (user_id, experiment_id)
                where a.variant = 'treatment'
                order by a.user_id
                """
            ).fetchall()
        ],
        dtype=float,
    )
    revenue = bootstrap_mean_difference(
        control_revenue,
        treatment_revenue,
        resamples=1000,
    )
    mde = minimum_detectable_effect(
        conversion.control_rate,
        min(control_n, treatment_n),
    )

    reasons = "".join(f"<li>{reason}</li>" for reason in decision.reasons)
    variants_html = "".join(
        "<tr>"
        f"<td>{variant}</td>"
        f"<td>{int(assigned):,}</td>"
        f"<td>{int(conversions):,}</td>"
        f"<td>{_pct(int(conversions) / int(assigned))}</td>"
        f"<td>{float(revenue_per_user):.2f}</td>"
        f"<td>{_pct(float(support_rate))}</td>"
        "</tr>"
        for (
            variant,
            assigned,
            conversions,
            revenue_per_user,
            support_rate,
        ) in variant_rows
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ExperimentLab — Experiment Decision</title>
<style>{STYLES}</style>
</head>
<body>
<main>
<header>
  <div class="note">SYNTHETIC EXPERIMENT · FIXED-HORIZON ANALYSIS</div>
  <h1>Checkout experiment</h1>
  <p class="sub">
    Assignment integrity, conversion uncertainty, revenue bootstrap, support-contact guardrail
    and power planning combined into one decision report.
  </p>
</header>
<section class="cards">
  <div class="card">
    <span>Control conversion</span><strong>{_pct(conversion.control_rate)}</strong>
  </div>
  <div class="card">
    <span>Treatment conversion</span><strong>{_pct(conversion.treatment_rate)}</strong>
  </div>
  <div class="card">
    <span>Absolute lift</span><strong>{_pct(conversion.absolute_lift)}</strong>
  </div>
  <div class="card"><span>SRM p-value</span><strong>{srm.p_value:.3f}</strong></div>
</section>
<section class="grid">
  <article class="panel decision decision-{decision.decision}">
    <h2>Decision</h2>
    <strong>{decision.decision.replace('_', ' ')}</strong>
    <ul>{reasons}</ul>
  </article>
  <article class="panel">
    <h2>Conversion uncertainty</h2>
    <p>95% interval: <strong>{_pct(conversion.ci_low)} to {_pct(conversion.ci_high)}</strong></p>
    <p>Two-sided p-value: <strong>{conversion.p_value:.4f}</strong></p>
    <p>Minimum useful effect: <strong>{_pct(MINIMUM_USEFUL_CONVERSION_EFFECT)}</strong></p>
    <p class="note">The decision uses the interval and guardrail policy, not p-value alone.</p>
  </article>
</section>
<section class="grid full">
  <article class="panel">
    <h2>Revenue per assigned user</h2>
    <p>Control: <strong>{revenue.control_mean:.2f}</strong></p>
    <p>Treatment: <strong>{revenue.treatment_mean:.2f}</strong></p>
    <p>Difference: <strong>{revenue.difference:.2f}</strong></p>
    <p>Bootstrap 95% interval: <strong>{revenue.ci_low:.2f} to {revenue.ci_high:.2f}</strong></p>
  </article>
  <article class="panel">
    <h2>Guardrail and power</h2>
    <p>Support-contact change: <strong>{_pct(support_effect)}</strong></p>
    <p>Maximum configured harm: <strong>{_pct(MAXIMUM_SUPPORT_CONTACT_HARM)}</strong></p>
    <p>Current approximate conversion MDE: <strong>{_pct(abs(mde.absolute_mde))}</strong></p>
    <p class="note">
      Power uses a normal approximation, equal allocation and fixed-horizon assumptions.
    </p>
  </article>
</section>
<section class="panel full">
  <h2>Variant metrics</h2>
  <table>
    <thead><tr><th>Variant</th><th>Assigned</th><th>Conversions</th><th>Conversion</th>
    <th>Revenue/user</th><th>Support rate</th></tr></thead>
    <tbody>{variants_html}</tbody>
  </table>
  <p class="note">
    All observations in this report are deterministically generated by ExperimentLab and are
    not production experiment results or evidence of real business uplift.
  </p>
</section>
</main>
</body>
</html>"""


def write_report(
    path: str | Path,
    connection: duckdb.DuckDBPyConnection | None = None,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    owns_connection = connection is None
    conn = connection or build_experiment_warehouse()
    try:
        output.write_text(build_report_html(conn), encoding="utf-8")
    finally:
        if owns_connection:
            conn.close()
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the ExperimentLab decision report")
    parser.add_argument("--output", default="build/experiment-decision.html")
    args = parser.parse_args()
    print(write_report(args.output))


if __name__ == "__main__":
    main()
