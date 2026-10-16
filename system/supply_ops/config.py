"""Parameters for the operations tools.

Round, illustrative values chosen for the synthetic data. None of them is a production
setting; the structure is the point.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryConfig:
    normal_months: int = 3                          # stock the next 3 months of demand will use: normal
    surplus_months: int = 6                         # stock months 4-6 will use: surplus
    horizon_months: int = 12                        # stock beyond 12 months of demand: over-excess
    aging_years: int = 3                            # stock no receipt in this window can account for: aged
    fold_past_due: tuple[str, ...] = ("confirmed",)  # demand kinds still owed when their date has passed


@dataclass(frozen=True)
class RouteConfig:
    slow_lane_days: int = 30     # business days of coverage at or above this: the cheapest, slowest lane
    fast_lane_days: int = 15     # between this and slow_lane_days: a faster lane; below it: air
    ocean_days: int = 30         # international plants: ocean at or above this, otherwise air
    horizon_days: int = 180      # how far ahead projected stock is rolled forward


@dataclass(frozen=True)
class SupplierTiers:
    rush_days: int = 15          # coverage under this: rush the next batch
    urgent_days: int = 30        # under this: next batch, as soon as possible
    excess_days: int = 60        # at or above this: slow production down


INVENTORY = InventoryConfig()
ROUTES = RouteConfig()
TIERS = SupplierTiers()
