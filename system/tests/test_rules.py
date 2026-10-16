"""The operating rules, as tests. If one of these fails, the rule stopped being true."""
import unittest

from forecast_review.config import DEFAULT
from forecast_review.rules import decide

from .helpers import signals, with_gap


class CuttingRules(unittest.TestCase):
    def test_an_item_stores_cannot_keep_on_the_shelf_is_never_cut(self):
        d = decide(with_gap(-0.40, in_stock=0.70))
        self.assertNotEqual(d.action, "LOWER")
        self.assertEqual(d.buffer, DEFAULT.low_stock_buffer)

    def test_a_cut_is_capped(self):
        d = decide(with_gap(-0.60))
        self.assertEqual(d.action, "LOWER")
        self.assertAlmostEqual(d.change, -DEFAULT.cut_cap)

    def test_new_items_are_protected_from_cuts(self):
        d = decide(with_gap(-0.40, weeks_of_history=DEFAULT.new_item_weeks - 1))
        self.assertEqual(d.action, "HOLD")

    def test_shipments_falling_alone_do_not_cut(self):
        d = decide(signals(shipment_trend=-0.55))
        self.assertEqual(d.action, "HOLD")

    def test_supply_gap_gets_a_buffer_not_a_cut(self):
        d = decide(signals(shipment_trend=-0.55, in_stock=0.72))
        self.assertEqual((d.action, d.buffer), ("HOLD", DEFAULT.low_stock_buffer))


class RaisingRules(unittest.TestCase):
    def test_a_raise_needs_a_second_independent_signal(self):
        d = decide(with_gap(+0.40, shipment_trend=+0.50))
        self.assertEqual(d.action, "HOLD")

    def test_a_raise_with_rising_sell_through_goes_through(self):
        d = decide(with_gap(+0.40, sell_through_trend=+0.20))
        self.assertEqual(d.action, "RAISE")

    def test_a_raise_is_capped(self):
        d = decide(with_gap(+0.80, sell_through_trend=+0.30))
        self.assertAlmostEqual(d.change, DEFAULT.raise_cap)


class Band(unittest.TestCase):
    def test_inside_the_band_nothing_moves(self):
        d = decide(with_gap(+0.05))
        self.assertEqual((d.action, d.change), ("OK", 0.0))


if __name__ == "__main__":
    unittest.main()
