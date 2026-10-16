"""Seasonality and validation: the checks that keep a backtest honest."""
import unittest

import numpy as np
import pandas as pd

from forecast_review import seasonality, synthetic
from forecast_review.config import DEFAULT
from forecast_review.signals import complete_weeks
from forecast_review.validation import forecast_pair, history_before, shortfall_rate, wmape


class Shrinkage(unittest.TestCase):
    item = np.array([2.0] + [10 / 11] * 11)   # an item with one extreme month
    segment = np.ones(12)

    def test_short_history_borrows_from_the_segment(self):
        short = seasonality.shrink(self.item, 2, self.segment, tau=8.0)
        long = seasonality.shrink(self.item, 24, self.segment, tau=8.0)
        self.assertLess(short[0], long[0])       # less of the item's own peak survives
        self.assertGreater(short[0], 1.0)

    def test_the_curve_has_mean_one(self):
        self.assertAlmostEqual(seasonality.shrink(self.item, 12, self.segment, 8.0).mean(), 1.0)


class Honesty(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weekly, _ = synthetic.generate(seed=3)

    def test_an_unfinished_week_is_never_read(self):
        self.assertGreater(self.weekly["week"].max(), synthetic.AS_OF)
        self.assertLessEqual(complete_weeks(self.weekly, synthetic.AS_OF)["week"].max(), synthetic.AS_OF)

    def test_the_forecast_cannot_see_the_period_it_forecasts(self):
        """Change everything after the origin; the forecast must not move."""
        origin = synthetic.AS_OF - pd.Timedelta(weeks=7)
        tampered = self.weekly.copy()
        tampered.loc[tampered["week"] >= origin, "pos_units"] *= 10

        def forecast(weekly):
            history = history_before(weekly, origin)
            curves = seasonality.segment_indices(history, DEFAULT.spike_ratio)
            item = history[history["sku"] == "A-01"]
            horizon = pd.Series(pd.date_range(origin, periods=8, freq="W-FRI"))
            return forecast_pair(item, curves[("RETAILER_A", item["segment"].iloc[0])], horizon)

        for a, b in zip(forecast(self.weekly), forecast(tampered)):
            np.testing.assert_allclose(a, b)


class Metrics(unittest.TestCase):
    def test_wmape_is_blind_to_direction(self):
        actual = [100, 100]
        self.assertAlmostEqual(wmape([80, 80], actual), wmape([120, 120], actual))

    def test_shortfall_rate_is_not(self):
        actual = [100, 100]
        self.assertEqual(shortfall_rate([80, 80], actual), 1.0)
        self.assertEqual(shortfall_rate([120, 120], actual), 0.0)


if __name__ == "__main__":
    unittest.main()
