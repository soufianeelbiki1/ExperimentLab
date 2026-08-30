create table dim_experiment (
    experiment_id varchar primary key,
    experiment_name varchar not null,
    primary_metric varchar not null,
    expected_treatment_share double not null check (expected_treatment_share > 0 and expected_treatment_share < 1)
);

create table fact_assignment (
    user_id varchar not null,
    experiment_id varchar not null references dim_experiment(experiment_id),
    variant varchar not null check (variant in ('control', 'treatment')),
    assigned_at timestamp not null,
    pre_period_activity double not null check (pre_period_activity >= 0),
    primary key (user_id, experiment_id)
);

create table fact_outcome (
    user_id varchar not null,
    experiment_id varchar not null,
    converted boolean not null,
    revenue double not null check (revenue >= 0),
    sessions integer not null check (sessions > 0),
    support_contact boolean not null,
    primary key (user_id, experiment_id),
    foreign key (user_id, experiment_id) references fact_assignment(user_id, experiment_id),
    check (converted or revenue = 0)
);

create or replace view mart_experiment_variant as
select
    a.experiment_id,
    a.variant,
    count(*) as assigned_users,
    sum(cast(o.converted as integer)) as conversions,
    avg(cast(o.converted as double)) as conversion_rate,
    sum(o.revenue) as revenue,
    avg(o.revenue) as revenue_per_assigned_user,
    avg(o.sessions) as sessions_per_user,
    avg(cast(o.support_contact as double)) as support_contact_rate,
    avg(a.pre_period_activity) as pre_period_activity_mean
from fact_assignment a
join fact_outcome o using (user_id, experiment_id)
group by 1, 2;
