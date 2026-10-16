"""MCP tool server: the execution layer, on synthetic data.

Claude Code starts it from .mcp.json. The sub-agents in .claude/agents/ reach the data
only through these tools. The tools are deterministic; the judgment lives in the prompts.

    python mcp_server.py        # stdio transport; normally started by Claude Code
"""
from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache

import pandas as pd
from mcp.server.fastmcp import FastMCP

from forecast_review import pipeline, report, synthetic, validation
from forecast_review.agents import Investigator
from forecast_review.config import ADOPTION, DEFAULT
from forecast_review.signals import complete_weeks
from forecast_review.synthetic import AS_OF

mcp = FastMCP("forecast-review")


@lru_cache(maxsize=1)
def _data():
    return synthetic.generate(seed=7)


@lru_cache(maxsize=1)
def _rows() -> tuple[pipeline.ReviewRow, ...]:
    weekly, plan = _data()
    return tuple(pipeline.review(weekly, plan, AS_OF))


def _row(retailer: str, sku: str) -> pipeline.ReviewRow:
    for r in _rows():
        if r.signals.retailer == retailer.upper() and r.signals.sku == sku.upper():
            return r
    raise ValueError(f"No item {sku} at {retailer}. Call list_retailers first.")


def _pct(x: float) -> str:
    return f"{round(x * 100):+d}%"


@mcp.tool()
def list_retailers() -> str:
    """Retailers in the synthetic dataset, with store counts, item counts and the review date."""
    weekly, _ = _data()
    table = (complete_weeks(weekly, AS_OF)
             .groupby("retailer").agg(stores=("stores", "first"), items=("sku", "nunique")))
    return f"Review date: week ending {AS_OF:%Y-%m-%d}. All data is synthetic.\n\n{table.to_string()}"


@mcp.tool()
def review_retailer(retailer: str) -> str:
    """Run the rule engine for one retailer. Returns every flagged item with the rule's proposal
    and the key signals. It does not refute anything: that is the refuter's job."""
    rows = [r for r in _rows() if r.signals.retailer == retailer.upper()]
    if not rows:
        raise ValueError(f"Unknown retailer {retailer}. Call list_retailers first.")
    flagged = [r for r in rows if r.proposal.flagged]
    lines = [f"{retailer.upper()}: {len(rows)} items, {len(flagged)} flagged by the rules.", ""]
    for r in flagged:
        s, p = r.signals, r.proposal
        finding = Investigator().investigate(s)
        change = f" {_pct(p.change)}" if p.change else ""
        lines += [
            f"{s.sku} ({s.segment}) · flag: {finding.flag}",
            f"  proposed {p.action}{change}: {p.reasons[0]}",
            f"  sell-through {_pct(s.sell_through_trend)} (spike-free {_pct(s.sell_through_trend_robust)}) · "
            f"in-stock {s.in_stock:.0%} · shipments {_pct(s.shipment_trend)} · open orders "
            f"{_pct(s.open_orders_trend)} · demand vs plan {_pct(s.gap)} · {s.weeks_of_history} weeks",
            "",
        ]
    return "\n".join(lines)


@mcp.tool()
def item_signals(retailer: str, sku: str) -> str:
    """Every signal the rules and the refuter read for one item, and the investigator's checks."""
    r = _row(retailer, sku)
    finding = Investigator().investigate(r.signals)
    signals = "\n".join(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}"
                        for k, v in asdict(r.signals).items() if k != "scenario")
    checks = "\n".join(f"  {c}: {v} {n}".rstrip() for c, v, n in finding.checks)
    return (f"{r.signals.retailer} · {r.signals.sku}\nclaim the flag implies: {finding.claim}\n"
            f"flag: {finding.flag}\n\nchecks:\n{checks}\n\nsignals:\n{signals}\n"
            f"  gap: {r.signals.gap:.3f}\n  gap_robust: {r.signals.gap_robust:.3f}")


@mcp.tool()
def weekly_series(retailer: str, sku: str, weeks: int = 12) -> str:
    """The last `weeks` complete weeks for one item: sell-through, store in-stock, shipments and
    open orders. Use it to spot-check a claim against the raw series."""
    weekly, _ = _data()
    item = complete_weeks(weekly, AS_OF)
    item = item[(item["retailer"] == retailer.upper()) & (item["sku"] == sku.upper())]
    if item.empty:
        raise ValueError(f"No item {sku} at {retailer}.")
    tail = item.sort_values("week").tail(max(1, min(weeks, 104)))
    out = pd.DataFrame({
        "week": tail["week"].dt.strftime("%Y-%m-%d"),
        "sell_through": tail["pos_units"].round(0).astype(int),
        "in_stock": (tail["in_stock"] * 100).round(0).astype(int).astype(str) + "%",
        "shipments": tail["shipments"].round(0).astype(int),
        "open_orders": tail["open_orders"].round(0).astype(int),
    })
    return out.to_string(index=False)


@mcp.tool()
def refute(retailer: str, sku: str) -> str:
    """The deterministic refuter's verdict for one flagged item, to compare with your own."""
    r = _row(retailer, sku)
    if not r.verdict:
        return f"{r.signals.sku} was not flagged: {r.final.reasons[0]}"
    return (f'claim "{r.finding.claim}": {r.verdict.outcome}. {r.verdict.reason}\n'
            f"final: {report.verdict_text(r.final)}" + (" · sent to planner" if r.needs_planner else ""))


@mcp.tool()
def weekly_review() -> str:
    """The whole deterministic pipeline for every retailer: a summary, then a trace for every flagged item."""
    rows = list(_rows())
    return report.summary(rows) + "\n\n" + "\n\n".join(report.trace(r) for r in rows if r.proposal.flagged)


@mcp.tool()
def seasonal_backtest() -> str:
    """The pre-registered seasonality backtest by retailer: naive, flat and seasonal WMAPE,
    bias, value added over naive, and the adoption decision."""
    weekly, _ = _data()
    table = validation.seasonal_backtest(weekly, AS_OF)
    return (f"Adoption rule, fixed before any result: at least {ADOPTION.min_gain_points:.1f} WMAPE points "
            f"better than flat, on at least {ADOPTION.min_items} items.\n\n" + table.round(3).to_string(index=False))


@mcp.tool()
def explain_rules() -> str:
    """The operating rules and the parameters in force. All parameters are illustrative."""
    c = DEFAULT
    return "\n".join([
        f"OK band: demand estimate within {c.ok_band:.0%} of plan -> OK.",
        f"Cuts: capped at {c.cut_cap:.0%}; disabled below {c.in_stock_floor:.0%} store in-stock "
        f"(buffer {c.low_stock_buffer:.0%} instead); disabled for items under {c.new_item_weeks} weeks old.",
        f"Raises: capped at {c.raise_cap:.0%}; need sell-through or open orders up at least "
        f"{c.trend_threshold:.0%}, or low in-stock. Shipments alone return HOLD.",
        f"Flags: a shipment swing of {c.shipment_flag:.0%}, or sell-through down {c.momentum_cut:.0%}, "
        "gets a review even when the plan looks right.",
        f"Signals: complete weeks only; {c.window_weeks}-week windows; trends on deseasonalized sales; "
        f"a week above {c.spike_ratio:.0f}x the median is a spike.",
        "A refuted change does not ship: the forecast is held.",
    ])


# ---------- the decisions around the forecast (supply_ops) ----------

@lru_cache(maxsize=1)
def _inventory():
    from supply_ops import synthetic as ops
    return ops.inventory()


@mcp.tool()
def excess_inventory(fold_past_due: bool = True) -> str:
    """Stock value by tier (normal, surplus, excess, over-excess) from stock against forward demand.
    Set fold_past_due=False to see the date-filter bug: confirmed orders dated last month dropped."""
    from supply_ops import inventory
    from supply_ops.synthetic import AS_OF as OPS_AS_OF
    stock, demand, _ = _inventory()
    s = inventory.summary(inventory.excess(stock, demand, OPS_AS_OF, fold_past_due=fold_past_due))
    lines = [f"Report date {OPS_AS_OF:%Y-%m-%d}; confirmed orders past due are "
             f"{'counted as demand' if fold_past_due else 'DROPPED (the bug)'}. Synthetic data."]
    lines += [f"  {k:<13} ${s[k]:,.0f}" for k in ("normal", "surplus", "excess", "over_excess", "total_excess", "stock")]
    lines.append(f"  excess share of stock {s['excess_share']:.1%} (report dollars first; the share moves when healthy stock ships)")
    return "\n".join(lines)


@mcp.tool()
def aged_stock(limit: int = 10) -> str:
    """Excess older than the aging window, largest first, with whether it belongs on the write-off
    list (no receipt inside the window) or is an over-buy (received again recently)."""
    from supply_ops import inventory
    from supply_ops.synthetic import AS_OF as OPS_AS_OF
    stock, demand, receipts = _inventory()
    aged = inventory.aged(inventory.excess(stock, demand, OPS_AS_OF), receipts, OPS_AS_OF)
    head = aged.head(max(1, limit))[["item", "aged_units", "aged_value", "last_receipt", "write_off_list"]]
    return (f"{len(aged)} aged items; {int(aged['write_off_list'].sum())} on the write-off list "
            f"(${aged.loc[aged['write_off_list'], 'aged_value'].sum():,.0f}).\n\n" + head.round(0).to_string(index=False))


@mcp.tool()
def coverage_plan(family: str = "all", live_stock: bool = True) -> str:
    """Days of coverage, freight route and supplier tier per item. family: all, domestic or
    international. live_stock=False reads the overnight snapshot instead of live stock."""
    from supply_ops import coverage
    from supply_ops import synthetic as ops
    items, events = ops.supply_events()
    if family != "all":
        items = items[items["family"] == family]
    out = coverage.plan(items, events, ops.AS_OF, stock_column="on_hand" if live_stock else "snapshot_on_hand")
    counts = out["route"].value_counts().to_dict()
    return f"Routes: {counts}. Coverage in business days; blank = no back-order ahead.\n\n" + out.to_string(index=False)


@mcp.tool()
def plan_horizon_accuracy(anchor: str = "first") -> str:
    """How accurate a customer's supply plan was, by how many months ahead it was written.
    anchor: first or last plan received in the earlier month."""
    from supply_ops import plan_accuracy
    from supply_ops import synthetic as ops
    snapshots, orders = ops.plan_snapshots()
    months = [pd.Period("2026-05"), pd.Period("2026-06"), pd.Period("2026-07")]
    table = plan_accuracy.horizon_table(snapshots, orders, months, anchor=anchor)
    return (f"Gap = (orders - plan) / plan, outer join, {anchor} plan in the month. Synthetic data.\n\n"
            + table.round(3).to_string(index=False))


@mcp.tool()
def leakage_check() -> str:
    """The same forecast model with and without a leaking feature: WMAPE, value added over naive,
    and the share of forecasts within 5% of actual (a leak fingerprint)."""
    from supply_ops import leakage
    weekly, _ = _data()
    card = pd.DataFrame({"honest": leakage.scorecard(leakage.backtest(weekly, AS_OF, leak=False)),
                         "leaky": leakage.scorecard(leakage.backtest(weekly, AS_OF, leak=True))}).T
    return ("A pleasant surprise is a reason to test further, not to ship.\n\n" + card.round(3).to_string())


if __name__ == "__main__":
    mcp.run()
