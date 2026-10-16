"""A forecast that looks too good, and three checks that catch it.

The same simple model is fitted twice on the weekly synthetic data. The honest version sees
only the past. The leaky version also gets a smoothed level centred on the week being
forecast, the kind of feature that appears when coarser figures are interpolated to weeks:
it quietly contains the answer, and the week after it. It scores beautifully in a backtest
and could not exist in production.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from forecast_review.signals import complete_weeks
from forecast_review.validation import wmape


def features(item: pd.DataFrame, leak: bool) -> pd.DataFrame:
    """Per-week features for one item. Every honest feature uses weeks strictly before the target."""
    s = item.set_index("week")["pos_units"].astype(float)
    f = pd.DataFrame({
        "target": s,
        "last_week": s.shift(1),
        "mean_4": s.shift(1).rolling(4).mean(),
        "mean_13": s.shift(1).rolling(13).mean(),
        "last_year": s.shift(52),
    })
    if leak:
        f["smoothed_level"] = s.rolling(3, center=True).mean()   # weeks t-1, t and t+1: the answer is inside
    return f.dropna()


def fit_predict(frame: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """Least squares on weeks before `origin`, predictions for weeks from `origin` on."""
    x_cols = [c for c in frame.columns if c != "target"]
    train, test = frame[frame.index < origin], frame[frame.index >= origin]
    x = np.column_stack([np.ones(len(train)), train[x_cols].to_numpy()])
    coef, *_ = np.linalg.lstsq(x, train["target"].to_numpy(), rcond=None)
    pred = np.column_stack([np.ones(len(test)), test[x_cols].to_numpy()]) @ coef
    return pd.DataFrame({"actual": test["target"], "forecast": pred, "naive": test["last_week"]})


def backtest(weekly: pd.DataFrame, as_of: pd.Timestamp, leak: bool, test_weeks: int = 12) -> pd.DataFrame:
    """Every item, the last `test_weeks` complete weeks held out."""
    data = complete_weeks(weekly, as_of)
    origin = as_of - pd.Timedelta(weeks=test_weeks - 1)
    out = []
    for (retailer, sku), item in data.groupby(["retailer", "sku"]):
        frame = features(item, leak)
        if (frame.index < origin).sum() < 30 or (frame.index >= origin).sum() == 0:
            continue
        res = fit_predict(frame, origin)
        res["retailer"], res["sku"] = retailer, sku
        out.append(res)
    return pd.concat(out)


def moves_with_its_own_answer(item: pd.DataFrame, week: pd.Timestamp, origin: pd.Timestamp, leak: bool) -> float:
    """Multiply the actual for `week` by ten and refit. Returns the relative change in the
    forecast for that same week. An honest forecast cannot see its own answer: zero."""
    base = fit_predict(features(item, leak), origin).loc[week, "forecast"]
    tampered = item.copy()
    tampered.loc[tampered["week"] == week, "pos_units"] *= 10
    moved = fit_predict(features(tampered, leak), origin).loc[week, "forecast"]
    return float(moved / base - 1)


def within_5pct(result: pd.DataFrame) -> float:
    """Share of forecasts within 5% of actual. A leak fingerprint: an honest weekly item
    forecast rarely does this more than a small fraction of the time."""
    return float((np.abs(result["forecast"] / result["actual"] - 1) <= 0.05).mean())


def scorecard(result: pd.DataFrame) -> pd.Series:
    fc, naive = wmape(result["forecast"], result["actual"]), wmape(result["naive"], result["actual"])
    return pd.Series({"wmape": fc, "wmape_naive": naive, "value_added_points": (naive - fc) * 100,
                      "within_5pct": within_5pct(result)})
