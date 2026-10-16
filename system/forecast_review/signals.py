"""Per-item signals for one review date.

Two rules are built in here rather than left to the caller:
  * only complete weeks are read; a week still in progress would fake a drop;
  * trends are read on deseasonalized sales, so a seasonal swing cannot pass for a trend.

Each trend is computed twice: a plain version, the way a simple rule would read it,
and a robust version with spike weeks removed, which the refuter uses to argue back.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import seasonality
from .config import DEFAULT, ReviewConfig
from .seasonality import weeks_in_month


@dataclass(frozen=True)
class Signals:
    retailer: str
    sku: str
    segment: str
    scenario: str
    weeks_of_history: int
    in_stock: float                  # latest complete week, not an average
    sell_through_trend: float        # recent window vs the one before, plain means
    sell_through_trend_robust: float # same, spike weeks removed
    shipment_trend: float
    open_orders_trend: float
    pos_spike_in_window: bool        # one week dominates sell-through in the comparison windows
    shipment_spike_in_window: bool   # one week dominates shipments in the comparison windows
    est_level: float                 # deseasonalized weekly demand from the recent window
    est_level_robust: float
    plan_level: float                # deseasonalized weekly level implied by next month's plan

    @property
    def gap(self) -> float:
        """Demand estimate vs plan: negative means the plan is above demand."""
        return self.est_level / self.plan_level - 1.0 if self.plan_level > 0 else 0.0

    @property
    def gap_robust(self) -> float:
        return self.est_level_robust / self.plan_level - 1.0 if self.plan_level > 0 else 0.0


def complete_weeks(frame: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    """Drop any week that ends after the review date."""
    return frame[frame["week"] <= as_of]


def season_basis(frame: pd.DataFrame, as_of: pd.Timestamp, cfg: ReviewConfig = DEFAULT) -> pd.DataFrame:
    """History for the seasonal curve: everything before the two comparison windows,
    so the weeks being judged cannot shape the season they are judged against."""
    cutoff = as_of - pd.Timedelta(weeks=2 * cfg.window_weeks)
    return frame[frame["week"] <= cutoff]


def _trend(recent: np.ndarray, prior: np.ndarray) -> float:
    base = float(np.mean(prior)) if len(prior) else 0.0
    return float(np.mean(recent)) / base - 1.0 if base > 0 else 0.0


def _without_spikes(values: np.ndarray, reference: np.ndarray, ratio: float) -> np.ndarray:
    """Values with any week above `ratio` x the median of `reference` removed."""
    median = float(np.median(reference)) if len(reference) else 0.0
    if median <= 0:
        return values
    kept = values[values <= ratio * median]
    return kept if len(kept) else values


def _has_spike(values: np.ndarray, ratio: float) -> bool:
    median = float(np.median(values)) if len(values) else 0.0
    return bool(median > 0 and (values > ratio * median).any())


def build(frame: pd.DataFrame, plan_units: float, next_month: pd.Period,
          segment_index: np.ndarray, as_of: pd.Timestamp,
          cfg: ReviewConfig = DEFAULT) -> Signals:
    history = complete_weeks(frame, as_of).sort_values("week")
    w = cfg.window_weeks
    recent, prior = history.iloc[-w:], history.iloc[-2 * w:-w]

    curve = seasonality.item_curve(season_basis(history, as_of, cfg), segment_index,
                                   cfg.shrinkage_tau, cfg.season_clip, cfg.spike_ratio)

    def deseasonalized(part: pd.DataFrame, column: str) -> np.ndarray:
        return part[column].to_numpy() / curve[part["week"].dt.month.to_numpy() - 1]

    pos_r, pos_p = deseasonalized(recent, "pos_units"), deseasonalized(prior, "pos_units")
    ship_r, ship_p = deseasonalized(recent, "shipments"), deseasonalized(prior, "shipments")
    oo_r, oo_p = deseasonalized(recent, "open_orders"), deseasonalized(prior, "open_orders")
    both_pos, both_ship = np.r_[pos_r, pos_p], np.r_[ship_r, ship_p]

    pos_r_robust = _without_spikes(pos_r, both_pos, cfg.spike_ratio)
    pos_p_robust = _without_spikes(pos_p, both_pos, cfg.spike_ratio)
    plan_level = plan_units / (weeks_in_month(next_month) * curve[next_month.month - 1])

    return Signals(
        retailer=str(history["retailer"].iloc[0]),
        sku=str(history["sku"].iloc[0]),
        segment=str(history["segment"].iloc[0]),
        scenario=str(history["scenario"].iloc[0]),
        weeks_of_history=len(history),
        in_stock=float(history["in_stock"].iloc[-1]),
        sell_through_trend=_trend(pos_r, pos_p),
        sell_through_trend_robust=_trend(pos_r_robust, pos_p_robust),
        shipment_trend=_trend(ship_r, ship_p),
        open_orders_trend=_trend(oo_r, oo_p),
        pos_spike_in_window=_has_spike(both_pos, cfg.spike_ratio),
        shipment_spike_in_window=_has_spike(both_ship, cfg.spike_ratio),
        est_level=float(np.mean(pos_r)),
        est_level_robust=float(np.mean(pos_r_robust)),
        plan_level=float(plan_level),
    )
