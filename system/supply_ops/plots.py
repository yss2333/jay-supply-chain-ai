"""Charts for the operations notebooks, in the same visual system as forecast_review.plots."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator, PercentFormatter

from forecast_review.plots import BASELINE, GRID, INK, INK_2, MUTED, SERIES, STYLE, SURFACE, WASH, _header, _save

from .config import ROUTES
from .inventory import TIERS

# Ordinal tiers read as one hue, light to dark (the lightest step still clears 2:1 on the surface).
TIER_COLORS = ("#86b6ef", "#5598e7", "#256abf", "#104281")
TIER_LABELS = ("Normal", "Surplus", "Excess", "Over-excess")
_money = FuncFormatter(lambda v, _: f"${v / 1e6:.1f}M")


def excess_tiers(before: pd.Series, after: pd.Series, path: str | Path | None = None):
    """Two stacked bars: stock value by tier, with the date-filter bug and with it fixed."""
    rows = (("Past-due orders dropped", before), ("Confirmed orders counted", after))
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(10.5, 3.6))
        for y, (_, s) in enumerate(reversed(rows)):
            left = 0.0
            for tier, color in zip(TIERS, TIER_COLORS):
                width = s[tier]
                ax.barh(y, width, left=left, height=0.52, color=color, edgecolor=SURFACE, linewidth=2)
                if width > 0.06 * s["stock"]:
                    ax.text(left + width / 2, y, f"${width / 1e3:,.0f}K", ha="center", va="center",
                            fontsize=9, color="white" if tier in ("excess", "over_excess") else INK)
                left += width
            ax.text(left * 1.01, y, f"excess {s['excess_share']:.0%} of stock", va="center", fontsize=9.5, color=INK_2)
        ax.set_yticks([0, 1], labels=[r[0] for r in reversed(rows)])
        ax.tick_params(axis="y", colors=INK_2, labelsize=10)
        ax.xaxis.set_major_formatter(_money)
        ax.set_xlim(0, before["stock"] * 1.22)
        ax.grid(axis="x")
        ax.spines["left"].set_visible(False)
        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in TIER_COLORS]
        ax.legend(handles, TIER_LABELS, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=4, fontsize=9.5,
                  labelcolor=INK_2, handlelength=1.2)
        _header(fig, "The same stock, the same day, two answers",
                "Stock value by tier. The only difference is whether confirmed orders dated last month still count. Synthetic data.")
        fig.subplots_adjust(left=0.2, right=0.97, top=0.66, bottom=0.14)
        _save(fig, path)
    return fig


def horizon_curve(first: pd.DataFrame, last: pd.DataFrame, path: str | Path | None = None):
    """Average miss by how many months ahead the plan was written, for two anchors."""
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(9.5, 4.6))
        for table, label, color in ((first, "First plan received in the month", SERIES[0]),
                                    (last, "Last plan received in the month", SERIES[1])):
            ax.plot(table["months_ahead"], table["average_miss"], color=color, zorder=2)
            ax.plot(table["months_ahead"], table["average_miss"], "o", ms=8, color=color, mec=SURFACE, mew=2, zorder=3)
            end = table.iloc[-1]
            ax.text(end["months_ahead"] + 0.08, end["average_miss"], label, va="center", fontsize=9.5, color=INK_2)
        best = first.loc[first["average_miss"].idxmin()]
        ax.annotate("first plan: most accurate", (best["months_ahead"], best["average_miss"]), xytext=(0, -22),
                    textcoords="offset points", ha="center", fontsize=9, color=INK_2)
        ax.set_xticks(first["months_ahead"], labels=[f"{m} mo" for m in first["months_ahead"]])
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.yaxis.set_major_locator(MultipleLocator(0.05))
        ax.set_ylim(0, max(first["average_miss"].max(), last["average_miss"].max()) * 1.15)
        ax.set_xlim(0.7, 7.4)
        ax.grid(axis="y")
        ax.set_xlabel("How far ahead the plan was written", color=INK_2, labelpad=8)
        _header(fig, "The freshest plan is the least accurate",
                "Average absolute miss, orders vs plan, three target months. Synthetic data.")
        fig.subplots_adjust(left=0.08, right=0.98, top=0.8, bottom=0.14)
        _save(fig, path)
    return fig


def coverage_routes(plan: pd.DataFrame, path: str | Path | None = None, cfg=ROUTES):
    """One dot per item at its coverage, one row per route, with the thresholds drawn in."""
    order = ["air", "fast lane", "slow lane", "ocean"]
    cap = 100
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(10.5, 4.2))
        rng = np.random.default_rng(0)
        for y, r in enumerate(order):
            sub = plan[plan["route"] == r]
            x = sub["coverage_days"].fillna(cap).clip(upper=cap).to_numpy(dtype=float)
            ax.scatter(x, y + rng.uniform(-0.18, 0.18, len(x)), s=46, color=SERIES[0], edgecolor=SURFACE,
                       linewidth=1.5, zorder=3)
            ax.text(cap + 3, y, f"{len(sub)} items", va="center", fontsize=9.5, color=INK_2)
        for d, label in ((cfg.fast_lane_days, "air below"), (cfg.slow_lane_days, "slow lane / ocean at or above")):
            ax.axvline(d, color=BASELINE, lw=1.5, ls=(0, (4, 3)), zorder=1)
            ax.text(d + 1, len(order) - 0.45, f"{d} days · {label}", fontsize=8.5, color=MUTED)
        ax.set_yticks(range(len(order)), labels=[o.capitalize() for o in order])
        ax.tick_params(axis="y", colors=INK_2, labelsize=10)
        ax.set_xlim(-2, cap + 16)
        ax.set_xticks([0, 15, 30, 45, 60, 75, 100], labels=["0", "15", "30", "45", "60", "75", "none\nahead"])
        ax.grid(axis="x")
        ax.spines["left"].set_visible(False)
        ax.set_xlabel("Business days until the next back-order", color=INK_2, labelpad=8)
        _header(fig, "Coverage decides the route",
                "Each dot is an item's next shipment. Domestic plants choose among three lanes, international between ocean and air. Synthetic data.")
        fig.subplots_adjust(left=0.1, right=0.97, top=0.78, bottom=0.2)
        _save(fig, path)
    return fig


def leak_fingerprint(honest: pd.DataFrame, leaky: pd.DataFrame, path: str | Path | None = None):
    """Forecast / actual - 1 for both models, with the within-5% band shaded."""
    bins = np.linspace(-0.4, 0.4, 41)
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
        for ax, (res, title, color) in zip(axes, ((honest, "Honest: sees only the past", SERIES[0]),
                                                   (leaky, "Leaky: a feature holds the answer", SERIES[1]))):
            err = (res["forecast"] / res["actual"] - 1).clip(-0.399, 0.399)
            ax.axvspan(-0.05, 0.05, color=WASH, lw=0, zorder=0)
            ax.hist(err, bins=bins, color=color, edgecolor=SURFACE, linewidth=1, zorder=2)
            share = float((np.abs(res["forecast"] / res["actual"] - 1) <= 0.05).mean())
            ax.text(0, 1.04, f"{title}  ·  {share:.0%} within 5%", transform=ax.transAxes, fontsize=10.5,
                    weight="semibold", color=INK)
            ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
            ax.grid(axis="y")
            ax.set_xlabel("forecast vs actual", color=INK_2)
        _header(fig, "A leak has a fingerprint",
                "Share of weekly forecasts within 5% of actual (shaded band), 12 held-out weeks, every item. Synthetic data.")
        fig.subplots_adjust(left=0.06, right=0.98, top=0.74, bottom=0.18, wspace=0.08)
        _save(fig, path)
    return fig
