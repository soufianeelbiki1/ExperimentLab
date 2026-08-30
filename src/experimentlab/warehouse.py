from __future__ import annotations

from pathlib import Path

import duckdb

from .synthetic import SyntheticExperiment, generate_experiment

ROOT = Path(__file__).resolve().parents[2]


def build_experiment_warehouse(
    experiment: SyntheticExperiment | None = None,
    database: str = ":memory:",
) -> duckdb.DuckDBPyConnection:
    experiment = experiment or generate_experiment()
    connection = duckdb.connect(database)
    connection.execute((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
    connection.execute(
        "insert into dim_experiment values (?, ?, ?, ?)",
        [experiment.experiment_id, "Synthetic checkout copy", "conversion", 0.5],
    )

    assignments = [
        (
            user_id,
            experiment.experiment_id,
            str(variant),
            experiment.assigned_at,
            float(pre_period_activity),
        )
        for user_id, variant, pre_period_activity in zip(
            experiment.user_ids,
            experiment.variants,
            experiment.pre_period_activity,
            strict=True,
        )
    ]
    outcomes = [
        (
            user_id,
            experiment.experiment_id,
            bool(converted),
            float(revenue),
            int(sessions),
            bool(support_contact),
        )
        for user_id, converted, revenue, sessions, support_contact in zip(
            experiment.user_ids,
            experiment.converted,
            experiment.revenue,
            experiment.sessions,
            experiment.support_contact,
            strict=True,
        )
    ]
    connection.executemany("insert into fact_assignment values (?, ?, ?, ?, ?)", assignments)
    connection.executemany("insert into fact_outcome values (?, ?, ?, ?, ?, ?)", outcomes)
    return connection
