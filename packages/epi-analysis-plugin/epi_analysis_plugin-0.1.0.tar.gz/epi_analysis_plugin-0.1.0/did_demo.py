"""
Short demo of DID (Difference-in-Differences) plugin functions.

Builds a small synthetic unbalanced panel, runs ATT(g,t), and shows aggregations.
"""

from __future__ import annotations

import random
from typing import Any, Dict

import polars as pl

from matching_plugin import aggregate_effects, compute_att_gt, get_panel_info


def _make_synthetic_panel(
    n_ids: int = 200, years: range = range(2004, 2010)
) -> pl.DataFrame:
    rng = random.Random(123)
    rows = []
    # Assign half of units to eventually treated with different cohorts; others never treated (0)
    cohort_choices = [0, 2006, 2007, 2008]
    sectors = ["health", "manufacturing", "services", "education"]
    for uid in range(1, n_ids + 1):
        first_treat = rng.choice(cohort_choices)
        # Unit-level covariates
        x1 = rng.gauss(0.0, 1.0)  # time-invariant ability
        sector = rng.choice(sectors)  # categorical covariate (time-invariant)
        # Generate observations for a subset of years (unbalanced)
        start = rng.choice([years.start, years.start + 1])
        end = rng.choice([years.stop - 1, years.stop - 2])
        for t in range(start, end):
            # Outcome baseline + time trend + treatment effect if post-treatment
            trend = 0.1 * (t - years.start)
            x2 = rng.gauss(0.0, 1.0)  # time-varying shock
            treat_effect = 0.7 if (first_treat != 0 and t >= first_treat) else 0.0
            noise = rng.gauss(0.0, 0.2)
            # Covariate effects
            y = 3.0 + 0.5 * x1 + 0.3 * x2 + trend + treat_effect + noise
            rows.append(
                {
                    "id": uid,
                    "year": t,
                    "first.treat": first_treat,
                    "lemp": float(y),
                    "x1": float(x1),
                    "x2": float(x2),
                    "sector": sector,
                }
            )
    return pl.DataFrame(rows)


def _config() -> Dict[str, Any]:
    return {
        "outcome_var": "lemp",
        "treatment_var": "first.treat",
        "time_var": "year",
        "id_var": "id",
        "group_var": "first.treat",
        "control_vars": ["x1", "x2", "sector"],
        "cluster_var": None,
        "weights_var": None,
        "bootstrap_iterations": 200,
        "confidence_level": 0.95,
        "base_period": "Varying",
        "control_group": "NotYetTreated",
        "method": "Dr",
        "inference": "Did",
        "loss": "Logistic",
        "panel_type": "UnbalancedPanel",
        "allow_unbalanced_panel": True,
        "rng_seed": 123,
    }


def run() -> None:
    print("\n" + "=" * 80)
    print("DID Demo: ATT(g,t) and Aggregations")
    print("=" * 80)
    df = _make_synthetic_panel()
    cfg = _config()

    # Panel diagnostics
    info = get_panel_info(df, cfg)
    print("Panel info (core):")
    print(info)

    # Enhanced panel diagnostics (computed locally for convenience)
    print("\nPanel info (enhanced):")
    id_var = cfg["id_var"]
    time_var = cfg["time_var"]
    group_var = cfg["group_var"]

    n_units = df[id_var].n_unique()
    n_rows = df.height
    years = df[time_var].unique().sort()
    n_years = years.len()
    year_min = int(years.min())
    year_max = int(years.max())

    groups_s = df[group_var].unique().sort()
    n_groups = groups_s.len()
    treated_group_list = [g for g in groups_s.to_list() if g is not None and g > 0]
    has_never_treated = (df[group_var] == 0).any()
    n_never_treated = (
        df.group_by(id_var)
        .agg(pl.col(group_var).first().alias("g"))
        .filter(pl.col("g") == 0)
        .height
    )
    n_treated = n_units - n_never_treated

    panel_counts = (
        df.group_by(id_var)
        .agg(pl.len().alias("n_periods"))
        .select(
            [
                pl.col("n_periods").mean().alias("avg_periods_per_unit"),
                pl.col("n_periods").median().alias("median_periods_per_unit"),
                pl.col("n_periods").min().alias("min_periods_per_unit"),
                pl.col("n_periods").max().alias("max_periods_per_unit"),
            ]
        )
    )

    # Event-time coverage for treated observations
    event_stats = (
        df.filter(pl.col(group_var) > 0)
        .with_columns((pl.col(time_var) - pl.col(group_var)).alias("event_time"))
        .select(
            [
                pl.col("event_time").min().alias("min_event_time"),
                pl.col("event_time").max().alias("max_event_time"),
            ]
        )
    )

    base_enhanced = pl.DataFrame(
        {
            "n_units": [n_units],
            "n_rows": [n_rows],
            "n_years": [n_years],
            "years_range": [f"{year_min}-{year_max}"],
            "n_groups": [n_groups],
            "treated_groups": [treated_group_list],
            "has_never_treated": [bool(has_never_treated)],
            "n_treated_units": [n_treated],
            "n_never_treated_units": [n_never_treated],
        }
    )
    enhanced = pl.concat(
        [base_enhanced, panel_counts, event_stats], how="horizontal"
    ).rename(
        {
            "n_units": "units",
            "n_rows": "rows",
            "n_years": "years",
            "n_groups": "groups",
            "treated_groups": "treated_groups",
            "has_never_treated": "never_treated",
            "n_treated_units": "treated_units",
            "n_never_treated_units": "never_units",
            "avg_periods_per_unit": "avg_per_unit",
            "median_periods_per_unit": "med_per_unit",
            "min_periods_per_unit": "min_per_unit",
            "max_periods_per_unit": "max_per_unit",
            "min_event_time": "min_et",
            "max_event_time": "max_et",
        }
    )
    print(enhanced)

    # ATT(g,t)
    att = compute_att_gt(df, cfg)
    print("\nATT(g,t) (head):")
    print(att.head(6))

    # Aggregations
    simple = aggregate_effects(df, cfg, kind="simple")
    print("\nSimple aggregation:")
    print(simple)

    group = aggregate_effects(df, cfg, kind="group")
    print("\nGroup aggregation (head):")
    print(group.filter(not pl.col("is_overall")).head(6))
    print("\nGroup aggregation (overall):")
    print(group.filter(pl.col("is_overall")))

    dynamic = aggregate_effects(df, cfg, kind="dynamic")
    print("\nDynamic (event-time) aggregation (head):")
    print(dynamic.filter(not pl.col("is_overall")).head(6))

    dynamic_u = aggregate_effects(df, cfg, kind="dynamic", uniform_bands=True)
    print("\nDynamic (event-time) aggregation with uniform bands (head):")
    print(dynamic_u.filter(not pl.col("is_overall")).head(6))

    calendar = aggregate_effects(df, cfg, kind="calendar")
    print("\nCalendar-time aggregation (head):")
    print(calendar.filter(not pl.col("is_overall")).head(6))

    print("\n✓ DID demo completed")


if __name__ == "__main__":
    run()
