"""Days of coverage, and the decisions that hang off it.

Coverage = business days from today until projected stock first goes negative, the next
back-order date. It drives two decisions: which freight route a new shipment takes, and how
urgently a supplier should produce. Both read the same number, so they share one function.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ROUTES, TIERS, RouteConfig, SupplierTiers


def coverage_days(on_hand: float, events: pd.DataFrame, as_of: pd.Timestamp,
                  cfg: RouteConfig = ROUTES) -> int | None:
    """Business days until projected stock first drops below zero; None if it never does
    inside the horizon. `events` holds dated units: supply positive, demand negative."""
    if on_hand <= 0:
        return 0
    horizon_end = as_of + pd.Timedelta(days=cfg.horizon_days)
    ev = events[(events["date"] >= as_of) & (events["date"] <= horizon_end)]
    daily = ev.groupby("date")["units"].sum().sort_index()
    projected = on_hand + daily.cumsum()
    short = projected[projected < 0]
    if short.empty:
        return None
    return int(np.busday_count(as_of.date(), short.index[0].date()))


def route(coverage: int | None, family: str = "domestic", cfg: RouteConfig = ROUTES) -> str:
    """The freight route coverage implies. Plenty of time takes the cheapest, slowest lane;
    tight takes a faster lane; imminent takes air; no back-order ahead takes the cheapest."""
    if family == "international":
        return "ocean" if coverage is None or coverage >= cfg.ocean_days else "air"
    if coverage is None or coverage >= cfg.slow_lane_days:
        return "slow lane"
    return "fast lane" if coverage >= cfg.fast_lane_days else "air"


def supplier_tier(on_hand: float, coverage: int | None, tiers: SupplierTiers = TIERS) -> str:
    """What a supplier should do about an item: produce now, rush, next batch, normal, or slow down."""
    if on_hand <= 0:
        return "critical"
    if coverage is None or coverage >= tiers.excess_days:
        return "excess"
    if coverage < tiers.rush_days:
        return "rush"
    return "urgent" if coverage < tiers.urgent_days else "ok"


def plan(items: pd.DataFrame, events: pd.DataFrame, as_of: pd.Timestamp, stock_column: str = "on_hand",
         cfg: RouteConfig = ROUTES) -> pd.DataFrame:
    """Coverage, route and supplier tier for every item, read from `stock_column`."""
    by_item = dict(tuple(events.groupby("item")))
    rows = []
    for it in items.itertuples(index=False):
        on_hand = getattr(it, stock_column)
        cov = coverage_days(on_hand, by_item.get(it.item, events.iloc[0:0]), as_of, cfg)
        rows.append({"item": it.item, "family": it.family, "on_hand": on_hand, "coverage_days": cov,
                     "route": route(cov, it.family, cfg), "supplier_tier": supplier_tier(on_hand, cov)})
    return pd.DataFrame(rows)
