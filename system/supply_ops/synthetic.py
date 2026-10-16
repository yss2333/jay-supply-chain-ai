"""Synthetic operations data with planted scenarios.

Nothing here comes from a real company, customer or product. Three generators, one per
tool, each hiding the situation its notebook is about among ordinary noise.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

AS_OF = pd.Timestamp("2026-07-01")   # the first day of a month: the moment month-end rules bite


def inventory(seed: int = 11) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (stock, demand, receipts).

    stock:    one row per item: on-hand units, unit cost, lifecycle.
    demand:   forward demand lines: item, date, units, kind (confirmed / forecast / requisition).
    receipts: goods receipts over the last five years: item, date, units.

    Planted: a seasonal line whose confirmed orders slipped into last month (phantom excess),
    past-due requisitions that are not real demand, dead items last received years ago, and
    over-bought items that were received again recently.
    """
    rng = np.random.default_rng(seed)
    months = pd.date_range(AS_OF, periods=18, freq="MS")
    stock_rows, demand_rows, receipt_rows = [], [], []

    for i in range(1, 161):
        item = f"N-{i:03d}"
        cost = round(float(rng.lognormal(np.log(2.2), 0.45)), 2)
        if i <= 8:
            life = "seasonal"         # large confirmed orders, dated last month, not yet shipped
        elif i <= 22:
            life = "dead"             # no forecast; last received more than three years ago
        elif i <= 30:
            life = "rebought"         # no forecast, but received again last year
        else:
            life = str(rng.choice(["active", "active", "active", "fading"]))

        rate = float(rng.lognormal(np.log(2500), 0.7))            # units per month
        decay = 0.93 if life == "fading" else 1.0
        forecast = rate * decay ** np.arange(len(months)) * rng.lognormal(0, 0.12, len(months))
        if life in ("dead", "rebought"):
            forecast[:] = 0.0
        if life == "seasonal":
            forecast *= 0.04          # the season is already sold in; what is left is a trickle

        cover = {"active": rng.uniform(2, 7), "fading": rng.uniform(6, 16), "seasonal": 1.0,
                 "dead": 0.0, "rebought": 0.0}[life]
        on_hand = rate * cover
        if life == "seasonal":
            on_hand = rate * rng.uniform(5.5, 7.0)                  # built up ahead of the season
        if life in ("dead", "rebought"):
            on_hand = float(rng.lognormal(np.log(9000), 0.6))
        stock_rows.append({"item": item, "on_hand": round(on_hand), "unit_cost": cost, "lifecycle": life})

        for m, units in zip(months, forecast):
            if units > 0:
                demand_rows.append({"item": item, "date": m + pd.Timedelta(days=14),
                                    "units": round(units), "kind": "forecast"})
        if life == "seasonal":
            # The whole season sold in on confirmed orders, dated late last month, not yet shipped.
            for d in (AS_OF - pd.Timedelta(days=3), AS_OF - pd.Timedelta(days=2)):
                demand_rows.append({"item": item, "date": d, "units": round(on_hand * 0.42), "kind": "confirmed"})
        if life == "active" and rng.random() < 0.25:
            # An old planned requirement nobody cleaned up: it is not an order, and it is past due.
            demand_rows.append({"item": item, "date": AS_OF - pd.Timedelta(days=int(rng.integers(20, 200))),
                                "units": round(rate * rng.uniform(0.5, 1.5)), "kind": "requisition"})

        # Receipts: dead items stopped years ago; the rest were received on a rolling basis.
        if life == "dead":
            last = AS_OF - pd.DateOffset(years=int(rng.integers(3, 5)), months=int(rng.integers(1, 11)))
            dates = pd.date_range(end=last, periods=4, freq="90D")
        elif life == "rebought":
            dates = pd.DatetimeIndex([AS_OF - pd.DateOffset(years=4), AS_OF - pd.DateOffset(months=10)])
        else:
            dates = pd.date_range(end=AS_OF - pd.Timedelta(days=int(rng.integers(5, 60))), periods=20, freq="60D")
        per = (on_hand / 2 if life == "rebought" else max(on_hand, rate) / 3)
        for d in dates:
            receipt_rows.append({"item": item, "date": d, "units": round(per * rng.uniform(0.8, 1.2))})

    return pd.DataFrame(stock_rows), pd.DataFrame(demand_rows), pd.DataFrame(receipt_rows)


def plan_snapshots(seed: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (snapshots, orders).

    snapshots: a customer's weekly supply plan: received date, item, target month, planned units.
    orders:    the orders that actually landed: item, month, units.

    Planted: plans written about three to four months out are roughly right. Closer in, the
    customer cuts the plan in the final weeks, and cuts too far; further out, plans run
    optimistic. A few items are ordered without ever appearing in a plan.
    """
    rng = np.random.default_rng(seed)
    targets = pd.period_range("2026-05", "2026-07", freq="M")
    received = pd.date_range("2025-12-04", "2026-06-25", freq="W-THU")
    items = [f"P-{i:03d}" for i in range(1, 121)]
    true = {(it, m): float(rng.lognormal(np.log(4000), 0.8)) * rng.lognormal(0, 0.05)
            for it in items for m in targets}
    level_shift = {m: rng.normal(0, 0.02) for m in targets}      # the month runs a little hot or cold
    never = [f"P-{i:03d}" for i in range(121, 126)]               # ordered, never planned

    snap_rows = []
    for rec in received:
        for m in targets:
            days = (m.start_time - rec).days
            if days < 1 or days > 185:
                continue
            cut = -0.18 * float(np.clip(1 - days / 85, 0, 1))           # the late cut, and it overshoots
            optimism = 0.12 * float(np.clip((days - 112) / 40, 0, 1))    # early plans run high
            common = rng.normal(0, 0.02)                                  # this week's plan, all items
            for it in items:
                units = true[(it, m)] * (1 + cut + optimism + common) * rng.lognormal(0, 0.06)
                snap_rows.append({"received": rec, "item": it, "month": m, "units": round(units)})

    order_rows = []
    for m in targets:
        for it in items:
            order_rows.append({"item": it, "month": m,
                               "units": round(true[(it, m)] * (1 + level_shift[m]) * rng.lognormal(0, 0.10))})
        for it in never:
            order_rows.append({"item": it, "month": m, "units": round(rng.lognormal(np.log(3000), 0.3))})
    return pd.DataFrame(snap_rows), pd.DataFrame(order_rows)


def supply_events(seed: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (items, events) for the coverage tools.

    items:  item, plant family (domestic / international), live on-hand, and an on-hand figure
            read from an overnight snapshot that missed this morning's receipt.
    events: dated supply (+) and demand (-) in units over the next six months.
    """
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(AS_OF, periods=126)
    item_rows, event_rows = [], []
    for i in range(1, 61):
        item = f"S-{i:03d}"
        family = "domestic" if i <= 40 else "international"
        daily = float(rng.lognormal(np.log(300), 0.6))
        weeks_on_hand = rng.choice([0.4, 1, 2, 3, 4, 6, 8, 14], p=[.06, .12, .16, .18, .16, .14, .1, .08])
        on_hand = daily * 5 * weeks_on_hand
        morning = round(daily * 5 * rng.uniform(1, 3)) if rng.random() < 0.2 else 0
        item_rows.append({"item": item, "family": family, "on_hand": round(on_hand + morning),
                          "snapshot_on_hand": round(on_hand), "received_this_morning": morning})
        for d in days[::5]:                                                  # weekly demand
            event_rows.append({"item": item, "date": d, "units": -round(daily * 5 * rng.lognormal(0, 0.2))})
        for k in range(int(rng.integers(0, 3))):                             # purchase orders arriving
            arrive = days[int(rng.integers(10, 110))]
            event_rows.append({"item": item, "date": arrive, "units": round(daily * 5 * rng.uniform(4, 10))})
    return pd.DataFrame(item_rows), pd.DataFrame(event_rows)
