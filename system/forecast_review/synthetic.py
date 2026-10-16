"""Synthetic retail data with planted scenarios.

Nothing here comes from a real retailer or product. Five retailers, twelve items
each, two years of weekly history, plus one unfinished week at the end. A handful
of items carry a planted scenario so the review has something real to find; the
rest are ordinary noise, and most of them should come back OK.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .seasonality import weeks_in_month

AS_OF = pd.Timestamp("2026-06-26")  # a Friday: the last complete week ends here
WEEKS = 104
FORECAST_MONTHS = 6

# Seasonal shapes by segment, one value per calendar month.
_SHAPES = {
    "everyday": [1.00, 0.96, 1.00, 1.02, 1.03, 1.00, 0.98, 1.00, 1.00, 1.00, 1.00, 1.02],
    "summer": [0.70, 0.75, 0.90, 1.05, 1.25, 1.40, 1.35, 1.15, 0.95, 0.85, 0.80, 0.85],
    "holiday": [0.80, 0.85, 0.85, 0.85, 0.90, 0.90, 0.90, 0.95, 1.00, 1.15, 1.45, 1.40],
}

# retailer: (store count, how strongly its sales follow the seasonal shapes)
RETAILERS = {
    "RETAILER_A": (9000, 1.0),
    "RETAILER_B": (4500, 1.0),
    "RETAILER_C": (2500, 0.6),
    "RETAILER_D": (1200, 0.2),
    "RETAILER_E": (600, 0.0),
}

# (retailer, item position) -> planted scenario
SCENARIOS = {
    ("RETAILER_A", 3): "supply_gap",        # we could not ship; stores kept selling
    ("RETAILER_A", 7): "real_decline",      # sell-through is genuinely falling
    ("RETAILER_B", 2): "confirmed_growth",  # sell-through and open orders both rising
    ("RETAILER_B", 9): "bulk_order",        # one large shipment, nothing else changed
    ("RETAILER_C", 5): "spike_baseline",    # a one-week promotion sits in the comparison window
    ("RETAILER_D", 1): "new_item",          # nine weeks of history, an optimistic launch plan
}


def season_shape(segment: str, strength: float) -> np.ndarray:
    """Monthly seasonal multipliers (mean 1.0), damped by the retailer's strength."""
    base = np.asarray(_SHAPES[segment], dtype=float)
    base = base / base.mean()
    return 1.0 + strength * (base - 1.0)


def generate(seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (weekly, plan).

    weekly: one row per retailer x item x week, including one unfinished week after AS_OF.
    plan:   the current forecast, one row per retailer x item x month for the next six months.
    """
    rng = np.random.default_rng(seed)
    weeks = pd.date_range(end=AS_OF, periods=WEEKS, freq="W-FRI")
    months = weeks.month.to_numpy() - 1
    t = np.arange(WEEKS)
    segments = list(_SHAPES)
    next_months = pd.period_range(AS_OF.to_period("M") + 1, periods=FORECAST_MONTHS, freq="M")

    weekly_rows: list[pd.DataFrame] = []
    plan_rows: list[dict] = []

    for r_i, (retailer, (stores, strength)) in enumerate(RETAILERS.items()):
        for pos in range(1, 13):
            sku = f"{retailer[-1]}-{pos:02d}"
            segment = segments[(pos + r_i) % len(segments)]
            scenario = SCENARIOS.get((retailer, pos), "")
            lifecycle = "new" if scenario == "new_item" else str(
                rng.choice(["core", "core", "core", "growing", "fading"])
            )
            growth = {"core": 0.0, "growing": 0.20, "fading": -0.20, "new": 0.0}[lifecycle]
            shape = season_shape(segment, strength)
            rate = rng.lognormal(np.log(0.12), 0.5)  # units per store per week

            demand = (
                stores * rate * shape[months]
                * (1.0 + growth) ** ((t - (WEEKS - 1)) / 52.0)
                * rng.lognormal(0.0, 0.10, WEEKS)
            )
            in_stock = np.clip(rng.normal(0.95, 0.015, WEEKS), 0.88, 0.99)
            pos_units = demand * in_stock / 0.95
            shipments = demand * rng.lognormal(0.0, 0.12, WEEKS)
            open_orders = pd.Series(shipments).rolling(2, min_periods=1).mean().to_numpy()
            open_orders = open_orders * rng.lognormal(0.0, 0.08, WEEKS)
            plan_basis = slice(WEEKS - 20, WEEKS - 8)  # the plan was set from an older snapshot
            first_week = 0

            if scenario == "supply_gap":
                k = 5
                shipments[-k:] *= 0.42
                in_stock[-k:] = np.linspace(0.90, 0.70, k)
                pos_units[-k:] = demand[-k:] * 0.97
            elif scenario == "real_decline":
                ramp = np.linspace(1.0, 0.62, 10)
                for arr in (demand, pos_units, shipments, open_orders):
                    arr[-10:] *= ramp
            elif scenario == "confirmed_growth":
                ramp = np.linspace(1.0, 1.45, 10)
                for arr in (demand, pos_units, shipments):
                    arr[-10:] *= ramp
                open_orders[-10:] *= np.linspace(1.0, 1.7, 10)
            elif scenario == "bulk_order":
                shipments[-2] *= 4.5
            elif scenario == "spike_baseline":
                pos_units[-7] *= 4.5  # a one-week promotion inside the prior comparison window
                shipments[-7] *= 3.0
            elif scenario == "new_item":
                first_week = WEEKS - 9

            # The plan: a deseasonalized level from the basis window, re-shaped by month.
            if scenario == "new_item":
                basis_idx = np.arange(first_week, WEEKS)
            else:
                basis_idx = np.arange(WEEKS)[plan_basis]
            level = (pos_units[basis_idx] / shape[months[basis_idx]]).mean()
            if scenario == "new_item":
                level *= 1.6  # an optimistic launch plan
            for m in next_months:
                plan_rows.append({
                    "retailer": retailer,
                    "sku": sku,
                    "month": m,
                    "forecast_units": level * weeks_in_month(m) * shape[m.month - 1]
                    * rng.lognormal(0.0, 0.04),
                })

            frame = pd.DataFrame({
                "retailer": retailer,
                "sku": sku,
                "segment": segment,
                "lifecycle": lifecycle,
                "scenario": scenario,
                "week": weeks,
                "stores": stores,
                "pos_units": pos_units,
                "in_stock": in_stock,
                "shipments": shipments,
                "open_orders": open_orders,
            }).iloc[first_week:]

            # One unfinished week after AS_OF: three days of data. The review must ignore it.
            partial = frame.iloc[[-1]].copy()
            partial["week"] = AS_OF + pd.Timedelta(days=7)
            for col in ("pos_units", "shipments"):
                partial[col] = partial[col] * 3 / 7
            weekly_rows.append(pd.concat([frame, partial], ignore_index=True))

    weekly = pd.concat(weekly_rows, ignore_index=True)
    plan = pd.DataFrame(plan_rows)
    return weekly, plan
