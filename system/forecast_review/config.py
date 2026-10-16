"""Parameters for the review.

Every number here is a round, illustrative value chosen for the synthetic dataset.
None of them is a production setting. The structure is the point: which rules
exist, what they are allowed to do, and in what order they are checked.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewConfig:
    # When is a forecast "fine"?
    ok_band: float = 0.15            # |demand estimate / plan - 1| inside this band -> OK
    shipment_flag: float = 0.30      # a shipment swing this large gets a review even if the plan looks fine
    momentum_cut: float = 0.30       # sell-through down this much in one window proposes a cut on its own

    # The two ways to be wrong do not cost the same, so they get different rules.
    cut_cap: float = 0.20            # largest cut in one review
    raise_cap: float = 0.30          # largest raise in one review
    in_stock_floor: float = 0.85     # below this store-level in-stock, cutting is disabled
    low_stock_buffer: float = 0.08   # buffer added instead of a cut when in-stock is below the floor
    raise_signals_required: int = 1  # independent signals needed beyond the demand gap itself

    # Reading the signals
    window_weeks: int = 4            # recent window vs the window before it
    trend_threshold: float = 0.10    # a run-rate change this large counts as "up" or "down"
    spike_ratio: float = 3.0         # a week above this multiple of the window median is a spike
    new_item_weeks: int = 13         # items with less history are protected from cuts

    # Seasonality: how many months of evidence the segment curve is worth
    shrinkage_tau: float = 8.0
    season_clip: tuple[float, float] = (0.5, 1.8)


@dataclass(frozen=True)
class AdoptionRule:
    """Fixed before any backtest result is looked at."""

    min_gain_points: float = 2.0     # WMAPE must improve by at least this many points
    min_items: int = 8               # and the retailer must have enough items to judge


DEFAULT = ReviewConfig()
ADOPTION = AdoptionRule()
