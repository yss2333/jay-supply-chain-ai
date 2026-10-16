"""Validation: four stages, and they answer four different questions.

  unit        tests/                 Does the change do what I intended?
  backtest    seasonal_backtest()    Is it more accurate on periods it could not see?
  regression  compare()              Did it change anything I did not intend?
  shadow      compare()              Beside the live review, with nothing downstream connected

The backtest never lets data from the forecast period into the forecast: history is
cut strictly before the first forecast week, and that cut is asserted, not assumed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import seasonality
from .config import ADOPTION, DEFAULT, AdoptionRule, ReviewConfig
from .pipeline import ReviewRow


# ---- metrics: pick the one that answers the question --------------------------------

def wmape(forecast, actual) -> float:
    """Weighted absolute percentage error: sum|F - A| / sum A. Blind to direction."""
    f, a = np.asarray(forecast, float), np.asarray(actual, float)
    return float(np.abs(f - a).sum() / a.sum())


def bias(forecast, actual) -> float:
    """sum(F - A) / sum A. Positive means over-forecast."""
    f, a = np.asarray(forecast, float), np.asarray(actual, float)
    return float((f - a).sum() / a.sum())


def shortfall_rate(forecast, actual) -> float:
    """Share of periods where the forecast came in under actual: the stockout side."""
    f, a = np.asarray(forecast, float), np.asarray(actual, float)
    return float((f < a).mean())


# ---- backtest ----------------------------------------------------------------------

def history_before(weekly: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """Everything strictly before the first forecast week."""
    return weekly[weekly["week"] < origin]


def forecast_pair(history: pd.DataFrame, segment_curve: np.ndarray, horizon_weeks: pd.Series,
                  cfg: ReviewConfig = DEFAULT, lookback: int = 8) -> tuple[np.ndarray, np.ndarray]:
    """Two candidate forecasts for the same horizon, from the same history:
    a flat recent average, and the same level re-shaped by the seasonal curve."""
    recent = history.sort_values("week").iloc[-lookback:]
    months = horizon_weeks.dt.month.to_numpy() - 1
    flat = np.full(len(months), recent["pos_units"].mean())
    curve = seasonality.item_curve(history, segment_curve, cfg.shrinkage_tau, cfg.season_clip, cfg.spike_ratio)
    level = (recent["pos_units"].to_numpy() / curve[recent["week"].dt.month.to_numpy() - 1]).mean()
    return flat, level * curve[months]


def seasonal_backtest(weekly: pd.DataFrame, as_of: pd.Timestamp, cfg: ReviewConfig = DEFAULT,
                      rule: AdoptionRule = ADOPTION, folds: int = 4, horizon: int = 8,
                      min_history: int = 52) -> pd.DataFrame:
    """Should each retailer's forecasts use the seasonal curve, or a flat level?

    Rolling origins: each fold forecasts `horizon` weeks it has never seen. The adoption
    rule is fixed in config before this function runs.
    """
    complete = weekly[weekly["week"] <= as_of]
    records = []
    for k in range(folds):
        start = as_of - pd.Timedelta(weeks=horizon - 1 + horizon * k)
        end = start + pd.Timedelta(weeks=horizon - 1)
        history = history_before(complete, start)
        assert history["week"].max() < start, "history must end before the forecast period"
        curves = seasonality.segment_indices(history, cfg.spike_ratio)
        for (retailer, sku), hist in history.groupby(["retailer", "sku"]):
            if len(hist) < min_history:
                continue
            item = complete[(complete["retailer"] == retailer) & (complete["sku"] == sku)]
            actual = item[(item["week"] >= start) & (item["week"] <= end)].sort_values("week")
            if len(actual) < horizon:
                continue
            flat, seasonal = forecast_pair(hist, curves[(retailer, hist["segment"].iloc[0])],
                                           actual["week"], cfg)
            naive = np.full(len(actual), hist.sort_values("week")["pos_units"].iloc[-1])  # next week = last week
            a = actual["pos_units"].to_numpy()
            records.append({"retailer": retailer, "sku": sku, "fold": k, "actual": a.sum(),
                            "err_naive": np.abs(naive - a).sum(),
                            "err_flat": np.abs(flat - a).sum(),
                            "err_seasonal": np.abs(seasonal - a).sum(),
                            "signed_seasonal": (seasonal - a).sum()})

    df = pd.DataFrame(records)
    out = df.groupby("retailer").agg(items=("sku", "nunique"), actual=("actual", "sum"),
                                     err_naive=("err_naive", "sum"), err_flat=("err_flat", "sum"),
                                     err_seasonal=("err_seasonal", "sum"),
                                     signed_seasonal=("signed_seasonal", "sum"))
    for name in ("naive", "flat", "seasonal"):
        out[f"wmape_{name}"] = out[f"err_{name}"] / out["actual"]
    out["bias_seasonal"] = out["signed_seasonal"] / out["actual"]
    out["value_added_vs_naive"] = (out["wmape_naive"] - out["wmape_seasonal"]) * 100
    out["gain_vs_flat"] = (out["wmape_flat"] - out["wmape_seasonal"]) * 100
    out["decision"] = np.where(
        (out["gain_vs_flat"] >= rule.min_gain_points) & (out["items"] >= rule.min_items), "ADOPT", "KEEP FLAT")
    return out[["items", "wmape_naive", "wmape_flat", "wmape_seasonal", "bias_seasonal",
                "value_added_vs_naive", "gain_vs_flat", "decision"]].reset_index()


# ---- regression and shadow -----------------------------------------------------------

def _decision(row: ReviewRow) -> str:
    d = row.final
    return f"{d.action} {round(d.change * 100):+d}%" if d.action in ("RAISE", "LOWER") else d.action


def compare(first: list[ReviewRow], second: list[ReviewRow],
            labels: tuple[str, str] = ("live", "candidate")) -> pd.DataFrame:
    """Items where the second run's final decision differs from the first's."""
    earlier = {(r.signals.retailer, r.signals.sku): r for r in first}
    diffs = []
    for r in second:
        key = (r.signals.retailer, r.signals.sku)
        old = earlier[key]
        if (old.final.action, round(old.final.change, 4)) != (r.final.action, round(r.final.change, 4)):
            diffs.append({
                "retailer": key[0], "sku": key[1], "scenario": r.signals.scenario,
                "weeks_of_history": r.signals.weeks_of_history,
                labels[0]: _decision(old), labels[1]: _decision(r),
            })
    return pd.DataFrame(diffs)
