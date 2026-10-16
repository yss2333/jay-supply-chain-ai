"""The operating rules behind the operations write-ups, as tests."""
import unittest

import pandas as pd

from forecast_review import synthetic as fr_synthetic
from forecast_review.signals import complete_weeks
from supply_ops import coverage, inventory, leakage, plan_accuracy
from supply_ops.config import InventoryConfig

AS_OF = pd.Timestamp("2026-07-01")


def _stock(on_hand, cost=1.0):
    return pd.DataFrame({"item": ["X"], "on_hand": [on_hand], "unit_cost": [cost], "lifecycle": ["active"]})


def _demand(*lines):
    return pd.DataFrame([{"item": "X", "date": pd.Timestamp(d), "units": u, "kind": k} for d, u, k in lines])


class Excess(unittest.TestCase):
    def test_stock_with_a_confirmed_order_is_never_excess(self):
        """A confirmed order dated last month is still owed. It counts as demand."""
        demand = _demand(("2026-06-29", 1000, "confirmed"))
        fixed = inventory.excess(_stock(1000), demand, AS_OF)
        self.assertEqual(fixed.loc[0, "total_excess"], 0)
        bug = inventory.excess(_stock(1000), demand, AS_OF, fold_past_due=False)
        self.assertEqual(bug.loc[0, "total_excess"], 1000)

    def test_a_stale_requirement_is_not_demand(self):
        """Folding every past-due line would hide excess behind requirements nobody will order."""
        demand = _demand(("2026-03-15", 1000, "requisition"))
        self.assertEqual(inventory.excess(_stock(1000), demand, AS_OF).loc[0, "total_excess"], 1000)

    def test_tiers_add_up_to_stock(self):
        demand = _demand(("2026-07-15", 300, "forecast"), ("2026-10-15", 200, "forecast"),
                         ("2027-03-15", 100, "forecast"))
        row = inventory.excess(_stock(1000), demand, AS_OF).loc[0]
        self.assertAlmostEqual(sum(row[t] for t in inventory.TIERS), 1000)
        self.assertEqual((row["normal"], row["surplus"], row["excess"], row["over_excess"]), (300, 200, 100, 400))


class Aging(unittest.TestCase):
    def test_bought_again_recently_is_not_on_the_write_off_list(self):
        tiers = inventory.excess(pd.concat([_stock(500), _stock(500).assign(item="Y")], ignore_index=True),
                                 _demand(), AS_OF)
        receipts = pd.DataFrame({"item": ["X", "Y"], "units": [100, 100],
                                 "date": [pd.Timestamp("2021-01-10"), pd.Timestamp("2026-01-10")]})
        aged = inventory.aged(tiers, receipts, AS_OF, InventoryConfig()).set_index("item")
        self.assertTrue(aged.loc["X", "write_off_list"])
        self.assertFalse(aged.loc["Y", "write_off_list"])
        self.assertEqual(aged.loc["Y", "aged_units"], 400)   # still aged by quantity: an over-buy


class Coverage(unittest.TestCase):
    events = pd.DataFrame({"item": "X", "date": pd.bdate_range(AS_OF, periods=10, freq="5B"), "units": -100})

    def test_coverage_is_business_days_to_the_first_shortfall(self):
        # 250 on hand, 100 out every fifth business day: the third draw goes negative.
        self.assertEqual(coverage.coverage_days(250, self.events, AS_OF), 10)

    def test_no_shortfall_ahead_takes_the_cheapest_lane(self):
        self.assertIsNone(coverage.coverage_days(10_000, self.events, AS_OF))
        self.assertEqual(coverage.route(None), "slow lane")
        self.assertEqual(coverage.route(None, "international"), "ocean")

    def test_routes_follow_coverage(self):
        self.assertEqual([coverage.route(d) for d in (5, 20, 40)], ["air", "fast lane", "slow lane"])

    def test_no_stock_is_critical_whatever_is_coming(self):
        self.assertEqual(coverage.supplier_tier(0, None), "critical")


class PlanAccuracy(unittest.TestCase):
    def test_unplanned_orders_still_count_against_the_plan(self):
        month = pd.Period("2026-07")
        plan = pd.DataFrame({"item": ["A"], "units": [100]})
        orders = pd.DataFrame({"item": ["A", "B"], "month": [month, month], "units": [100, 50]})
        self.assertAlmostEqual(plan_accuracy.gap(plan, orders, month), 0.5)
        self.assertAlmostEqual(plan_accuracy.gap(plan, orders, month, join="inner"), 0.0)

    def test_the_plan_held_comes_from_the_right_month(self):
        snaps = pd.DataFrame({"received": pd.to_datetime(["2026-03-05", "2026-03-26", "2026-04-02"]),
                              "item": "A", "month": pd.Period("2026-07"), "units": [1, 2, 3]})
        month = pd.Period("2026-07")
        self.assertEqual(plan_accuracy.plan_held(snaps, month, 4, "first")["units"].tolist(), [1])
        self.assertEqual(plan_accuracy.plan_held(snaps, month, 4, "last")["units"].tolist(), [2])


class Leakage(unittest.TestCase):
    def test_an_honest_forecast_cannot_see_its_own_answer(self):
        weekly, _ = fr_synthetic.generate(seed=7)
        item = complete_weeks(weekly, fr_synthetic.AS_OF)
        item = item[item["sku"] == "A-01"]
        origin = fr_synthetic.AS_OF - pd.Timedelta(weeks=11)
        week = fr_synthetic.AS_OF - pd.Timedelta(weeks=5)
        self.assertAlmostEqual(leakage.moves_with_its_own_answer(item, week, origin, leak=False), 0.0)
        self.assertGreater(leakage.moves_with_its_own_answer(item, week, origin, leak=True), 0.5)


if __name__ == "__main__":
    unittest.main()
