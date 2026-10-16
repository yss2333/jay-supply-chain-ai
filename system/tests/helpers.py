"""Hand-built signals, so each rule can be checked on a case small enough to reason about."""
from __future__ import annotations

from forecast_review.signals import Signals

STEADY = dict(
    retailer="TEST", sku="T-01", segment="everyday", scenario="",
    weeks_of_history=104, in_stock=0.95,
    sell_through_trend=0.0, sell_through_trend_robust=0.0,
    shipment_trend=0.0, open_orders_trend=0.0,
    pos_spike_in_window=False, shipment_spike_in_window=False,
    est_level=100.0, est_level_robust=100.0, plan_level=100.0,
)


def signals(**overrides) -> Signals:
    """A steady, well-stocked item, with only the fields under test changed."""
    return Signals(**{**STEADY, **overrides})


def with_gap(gap: float, **overrides) -> Signals:
    """An item whose demand estimate sits `gap` away from its plan."""
    return signals(est_level=100.0 * (1 + gap), est_level_robust=100.0 * (1 + gap), **overrides)
