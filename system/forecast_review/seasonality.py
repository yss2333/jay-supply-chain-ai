"""Seasonality: a statistical index from store-normalized sales, shrunk toward the segment.

An item with four months of history borrows most of its seasonal shape from its
segment. An item with two years of history mostly keeps its own.

Two things are kept out of the curve on purpose:
  * spike weeks are clipped first, so a one-week promotion cannot become a season;
  * the weeks being judged are excluded (the caller passes history that ends before
    them), so a recent trend cannot be absorbed into the season and hidden.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def weeks_in_month(period: pd.Period) -> float:
    return period.days_in_month / 7.0


def door_normalized(frame: pd.DataFrame, spike_ratio: float | None = None) -> pd.Series:
    """Units sold per store per week, indexed by week. Optionally clips spike weeks
    to `spike_ratio` x the item's median week."""
    frame = frame.sort_values("week")
    series = pd.Series(
        frame["pos_units"].to_numpy() / frame["stores"].to_numpy(),
        index=pd.DatetimeIndex(frame["week"]),
    )
    if spike_ratio and len(series):
        series = series.clip(upper=spike_ratio * series.median())
    return series


def monthly_index(series: pd.Series) -> np.ndarray:
    """Average of each calendar month across years, divided by the average of the
    months that have data. Months with no data come back as NaN."""
    index = np.full(12, np.nan)
    if series.empty:
        return index
    by_month = series.groupby(series.index.month).mean()
    index[by_month.index.to_numpy() - 1] = by_month.to_numpy() / by_month.mean()
    return index


def months_of_history(series: pd.Series) -> int:
    return int(series.index.to_period("M").nunique())


def shrink(item_index: np.ndarray, n_months: int, segment_index: np.ndarray, tau: float) -> np.ndarray:
    """Blend an item's curve with its segment's, weighting the item by n / (n + tau).

    Months the item has never seen take the segment value. The result has mean 1.
    """
    segment = np.where(np.isnan(segment_index), 1.0, segment_index)
    weight = n_months / (n_months + tau)
    blended = segment.copy()
    seen = ~np.isnan(item_index)
    blended[seen] = weight * item_index[seen] + (1.0 - weight) * segment[seen]
    return blended / blended.mean()


def segment_indices(weekly: pd.DataFrame, spike_ratio: float | None = None) -> dict[tuple[str, str], np.ndarray]:
    """One pooled curve per (retailer, segment).

    Each item is scaled to its own mean first, so a large item cannot set the shape
    for everyone else.
    """
    curves: dict[tuple[str, str], np.ndarray] = {}
    for key, group in weekly.groupby(["retailer", "segment"]):
        scaled = []
        for _, item in group.groupby("sku"):
            series = door_normalized(item, spike_ratio)
            if series.mean() > 0:
                scaled.append(series / series.mean())
        pooled = pd.concat(scaled, axis=1).mean(axis=1) if scaled else pd.Series(dtype=float)
        curves[key] = monthly_index(pooled)
    return curves


def item_curve(frame: pd.DataFrame, segment_index: np.ndarray, tau: float,
               clip: tuple[float, float], spike_ratio: float | None = None) -> np.ndarray:
    """The seasonal multipliers used for one item: shrunk toward its segment, then clipped."""
    series = door_normalized(frame, spike_ratio)
    curve = shrink(monthly_index(series), months_of_history(series), segment_index, tau)
    return np.clip(curve, *clip)
