"""The rule engine: RAISE, LOWER, HOLD or OK for one item.

The two ways a forecast can be wrong do not cost the same, so they do not share a rule.

  Cutting risks an empty shelf. Cuts are capped, and when store-level in-stock is
  below the floor, cutting is switched off and the item gets a buffer instead.
  New items are protected from cuts for their first weeks.

  Raising risks trapped cash. A raise needs a second, independent signal on top of
  the demand gap. Shipments going up is not one: it returns HOLD.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .config import DEFAULT, ReviewConfig
from .signals import Signals


@dataclass(frozen=True)
class Decision:
    retailer: str
    sku: str
    action: str                 # RAISE / LOWER / HOLD / OK
    change: float = 0.0         # proportional change to the forecast level
    buffer: float = 0.0         # extra cover on top, as a proportion
    reasons: tuple[str, ...] = ()
    flagged: bool = False


def _pct(x: float) -> str:
    return f"{round(x * 100):+d}%"


def is_flagged(s: Signals, cfg: ReviewConfig = DEFAULT) -> bool:
    return (
        abs(s.gap) > cfg.ok_band
        or abs(s.shipment_trend) >= cfg.shipment_flag
        or s.sell_through_trend <= -cfg.momentum_cut
    )


def decide(s: Signals, cfg: ReviewConfig = DEFAULT) -> Decision:
    def out(action: str, *reasons: str, change: float = 0.0, buffer: float = 0.0) -> Decision:
        return Decision(s.retailer, s.sku, action, change, buffer, tuple(reasons), flagged=True)

    if not is_flagged(s, cfg):
        return Decision(s.retailer, s.sku, "OK", reasons=("demand estimate within the band of the plan",))

    low_stock = s.in_stock < cfg.in_stock_floor
    is_new = s.weeks_of_history < cfg.new_item_weeks
    buffer = cfg.low_stock_buffer if low_stock else 0.0

    # Evidence the plan is too high: the level gap, or a sharp fall in sell-through.
    if s.gap < -cfg.ok_band or s.sell_through_trend <= -cfg.momentum_cut:
        if low_stock:
            return out("HOLD", "cutting is disabled below the in-stock floor; buffer instead", buffer=buffer)
        if is_new:
            return out("HOLD", f"new item ({s.weeks_of_history} weeks): protected from cuts")
        drop = min(s.gap, s.sell_through_trend)
        change = max(drop, -cfg.cut_cap)
        why = (f"demand estimate {_pct(s.gap)} vs plan" if s.gap <= s.sell_through_trend
               else f"sell-through {_pct(s.sell_through_trend)} vs the prior window")
        capped = f"; capped at {_pct(-cfg.cut_cap)}" if change > drop else ""
        return out("LOWER", why + capped, change=change)

    # Evidence the plan is too low: needs something independent of the gap itself.
    if s.gap > cfg.ok_band:
        support = []
        if s.sell_through_trend >= cfg.trend_threshold:
            support.append(f"sell-through {_pct(s.sell_through_trend)}")
        if s.open_orders_trend >= cfg.trend_threshold:
            support.append(f"open orders {_pct(s.open_orders_trend)}")
        if low_stock:
            support.append(f"in-stock {s.in_stock:.0%}")
        if len(support) >= cfg.raise_signals_required:
            change = min(s.gap, cfg.raise_cap)
            capped = f"; capped at {_pct(cfg.raise_cap)}" if change < s.gap else ""
            return out("RAISE", f"demand estimate {_pct(s.gap)} vs plan, confirmed by "
                       + " and ".join(support) + capped, change=change, buffer=buffer)
        return out("HOLD", f"demand estimate {_pct(s.gap)} vs plan, but nothing independent confirms it")

    # The plan looks right, but shipments swung.
    if s.shipment_trend <= -cfg.shipment_flag:
        if low_stock:
            return out("HOLD", f"shipments {_pct(s.shipment_trend)} while sell-through held and in-stock "
                       "is below the floor: a supply gap", buffer=buffer)
        return out("HOLD", f"shipments {_pct(s.shipment_trend)} but sell-through did not fall")
    return out("HOLD", f"shipments {_pct(s.shipment_trend)} with no second signal: one order is not a trend")


def reconcile(proposal: Decision, verdict_outcome: str, verdict_reason: str) -> Decision:
    """A refuted change does not ship: the forecast is held."""
    if verdict_outcome == "REFUTED" and proposal.action in ("RAISE", "LOWER"):
        return replace(proposal, action="HOLD", change=0.0,
                       reasons=proposal.reasons + (f"refuted: {verdict_reason}",))
    return proposal
