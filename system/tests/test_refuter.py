"""The refuter's lenses. Each test is a claim the refuter must be able to knock down, or not."""
import unittest

from forecast_review.agents import Investigator, Refuter
from forecast_review.rules import decide, reconcile

from .helpers import signals, with_gap


def run(s):
    proposal = decide(s)
    finding = Investigator().investigate(s)
    verdict = Refuter().refute(finding, s, proposal)
    return finding, verdict, reconcile(proposal, verdict.outcome, verdict.reason)


class Refuter_(unittest.TestCase):
    def test_a_spike_in_the_baseline_is_not_a_fall(self):
        s = signals(sell_through_trend=-0.46, sell_through_trend_robust=-0.03, pos_spike_in_window=True)
        finding, verdict, final = run(s)
        self.assertEqual(finding.claim, "demand fell")
        self.assertEqual(verdict.outcome, "REFUTED")
        self.assertEqual(final.action, "HOLD")  # the proposed cut did not ship

    def test_low_in_stock_with_flat_sell_through_is_supply_not_demand(self):
        s = signals(shipment_trend=-0.55, in_stock=0.70)
        _, verdict, _ = run(s)
        self.assertEqual(verdict.outcome, "REFUTED")
        self.assertIn("supply gap", verdict.reason)

    def test_one_bulk_order_is_not_rising_demand(self):
        s = signals(shipment_trend=+1.0, shipment_spike_in_window=True)
        _, verdict, _ = run(s)
        self.assertEqual(verdict.outcome, "REFUTED")

    def test_a_real_decline_survives(self):
        s = with_gap(-0.35, sell_through_trend=-0.20, sell_through_trend_robust=-0.20)
        _, verdict, final = run(s)
        self.assertEqual(verdict.outcome, "CONFIRMED")
        self.assertEqual(final.action, "LOWER")

    def test_confirmed_growth_survives(self):
        s = with_gap(+0.30, sell_through_trend=+0.15, sell_through_trend_robust=+0.15, open_orders_trend=+0.40)
        _, verdict, final = run(s)
        self.assertEqual((verdict.outcome, final.action), ("CONFIRMED", "RAISE"))


if __name__ == "__main__":
    unittest.main()
