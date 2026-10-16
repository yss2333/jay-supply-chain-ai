"""How far ahead a customer's supply plan can be trusted.

Each target month is scored against the plan held some months before it. The actual is one
fixed number per month, so every row measures a plan and nothing else. Plan and actual are
outer-joined: items ordered without ever being planned still count against the plan.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def plan_held(snapshots: pd.DataFrame, month: pd.Period, months_ahead: int, anchor: str = "first") -> pd.DataFrame:
    """The plan for `month` as it stood `months_ahead` months earlier: the first (or last)
    snapshot received in that earlier month."""
    source = month - months_ahead
    in_source = snapshots[snapshots["received"].dt.to_period("M") == source]
    if in_source.empty:
        return in_source.iloc[0:0]
    pick = in_source["received"].min() if anchor == "first" else in_source["received"].max()
    return in_source[(in_source["received"] == pick) & (in_source["month"] == month)]


def gap(plan: pd.DataFrame, orders: pd.DataFrame, month: pd.Period, join: str = "outer") -> float:
    """(actual orders - plan) / plan for one month, over all items. `join="inner"` keeps only
    items present in both, which silently drops everything the plan never mentioned."""
    actual = orders[orders["month"] == month].groupby("item")["units"].sum()
    planned = plan.groupby("item")["units"].sum()
    both = pd.concat([planned.rename("plan"), actual.rename("actual")], axis=1, join=join).fillna(0)
    return float(both["actual"].sum() / both["plan"].sum() - 1)


def horizon_table(snapshots: pd.DataFrame, orders: pd.DataFrame, months: list[pd.Period],
                  horizons=range(1, 6), anchor: str = "first") -> pd.DataFrame:
    """One row per horizon: the gap for each target month and the average absolute miss."""
    rows = []
    for h in horizons:
        row = {"months_ahead": h}
        for m in months:
            held = plan_held(snapshots, m, h, anchor)
            row[str(m)] = gap(held, orders, m) if not held.empty else np.nan
        misses = [abs(v) for k, v in row.items() if k != "months_ahead" and not np.isnan(v)]
        row["average_miss"] = float(np.mean(misses)) if misses else np.nan
        row["months_scored"] = len(misses)
        rows.append(row)
    return pd.DataFrame(rows)
