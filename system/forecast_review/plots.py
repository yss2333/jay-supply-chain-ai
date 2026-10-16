"""Charts for the notebooks and the README.

One visual system for every figure: a light surface, recessive hairline grid, 2px lines,
end-dots with a surface ring, text in ink tokens (never in the series color), and a
categorical palette checked for colour-vision separation. Series colours are assigned
in a fixed order and never cycled.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator, PercentFormatter

from .config import ADOPTION, DEFAULT
from .pipeline import ReviewRow
from .report import verdict_text
from .signals import complete_weeks

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, WASH = "#e1e0d9", "#c3c2b7", "#efeee9"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a")  # fixed order: blue, orange, aqua

def _sans() -> str:
    """The first installed UI sans, so no machine prints font warnings."""
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Segoe UI", "Helvetica Neue", "Helvetica", "Arial", "Liberation Sans"):
        if name in installed:
            return name
    return "DejaVu Sans"


STYLE = {
    "font.family": _sans(),
    "font.size": 9.5,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": BASELINE,
    "axes.linewidth": 1.0,
    "axes.labelcolor": INK_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "grid.color": GRID,
    "grid.linewidth": 1.0,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "lines.linewidth": 2.0,
    "lines.solid_capstyle": "round",
    "lines.solid_joinstyle": "round",
    "legend.frameon": False,
    "savefig.facecolor": SURFACE,
    "savefig.dpi": 160,
}

SCENARIOS = [
    ("RETAILER_A", "A-03", "Supply gap"),
    ("RETAILER_A", "A-07", "Real decline"),
    ("RETAILER_B", "B-02", "Confirmed growth"),
    ("RETAILER_B", "B-09", "One bulk order"),
    ("RETAILER_C", "C-05", "Promotion in the baseline"),
    ("RETAILER_D", "D-01", "New item"),
]

_thousands = FuncFormatter(lambda v, _: f"{v:,.0f}")


def _header(fig, title: str, subtitle: str) -> None:
    fig.text(0.012, 0.975, title, ha="left", va="top", fontsize=14, weight="semibold", color=INK)
    fig.text(0.012, 0.925, subtitle, ha="left", va="top", fontsize=10, color=INK_2)


def _save(fig, path: str | Path | None) -> None:
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", pad_inches=0.25)


def planted_scenarios(weekly: pd.DataFrame, rows: list[ReviewRow], as_of: pd.Timestamp,
                      weeks: int = 16, path: str | Path | None = None):
    """Small multiples: sell-through and shipments for each planted scenario, with the two
    comparison windows shaded and the review's final decision underneath the title."""
    by_key = {(r.signals.retailer, r.signals.sku): r for r in rows}
    w = DEFAULT.window_weeks
    history = complete_weeks(weekly, as_of)

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2))
        for ax, (retailer, sku, label) in zip(axes.flat, SCENARIOS):
            item = history[(history["retailer"] == retailer) & (history["sku"] == sku)]
            item = item.sort_values("week").tail(weeks)
            x = item["week"]
            recent_start = x.iloc[-w] - pd.Timedelta(days=3.5)
            prior_start = x.iloc[-2 * w] - pd.Timedelta(days=3.5) if len(x) >= 2 * w else x.iloc[0]
            end = x.iloc[-1] + pd.Timedelta(days=3.5)
            ax.axvspan(prior_start, recent_start, color=WASH, lw=0, zorder=0)
            ax.axvspan(recent_start, end, color="#e6e5df", lw=0, zorder=0)

            for column, color in (("pos_units", SERIES[0]), ("shipments", SERIES[1])):
                ax.plot(x, item[column], color=color, zorder=2)
                ax.plot(x.iloc[-1], item[column].iloc[-1], "o", ms=8, color=color,
                        mec=SURFACE, mew=2, zorder=3)

            row = by_key[(retailer, sku)]
            ax.text(0, 1.17, f"{sku}  ·  {label}", transform=ax.transAxes, fontsize=11,
                    weight="semibold", color=INK, va="bottom")
            ax.text(0, 1.04, f"in-stock {row.signals.in_stock:.0%}  ·  {verdict_text(row.final)}",
                    transform=ax.transAxes, fontsize=9, color=INK_2, va="bottom")

            top = max(item["pos_units"].max(), item["shipments"].max())
            ax.set_ylim(0, top * 1.12)
            ax.set_xlim(x.iloc[0] - pd.Timedelta(days=3.5), end)
            ax.yaxis.set_major_formatter(_thousands)
            ax.yaxis.set_major_locator(plt.MaxNLocator(4))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
            ax.grid(axis="y")

        first = axes.flat[0]
        first.text(1 - 1.5 * w / weeks, 0.97, "prior\n4 wks", transform=first.transAxes, ha="center",
                   va="top", fontsize=8, color=MUTED)
        first.text(1 - 0.5 * w / weeks, 0.97, "last\n4 wks", transform=first.transAxes, ha="center",
                   va="top", fontsize=8, color=MUTED)

        _header(fig, "Six planted scenarios, and what the review decided",
                f"Last {weeks} complete weeks, units per week. Shaded: the two windows the rules compare. "
                "Synthetic data.")
        keys = [Line2D([0], [0], color=SERIES[0], lw=2), Line2D([0], [0], color=SERIES[1], lw=2)]
        fig.legend(keys, ["Sell-through", "Shipments"], loc="upper right", bbox_to_anchor=(0.995, 0.985),
                   ncol=2, fontsize=9.5, handlelength=1.6, labelcolor=INK_2)
        fig.subplots_adjust(left=0.05, right=0.99, top=0.80, bottom=0.06, hspace=0.62, wspace=0.18)
        _save(fig, path)
    return fig


def backtest_dots(table: pd.DataFrame, path: str | Path | None = None):
    """Dot plot: WMAPE of the naive, flat and seasonal forecasts for each retailer, with the
    adoption decision read off the pre-registered rule."""
    table = table.sort_values("retailer", ascending=False).reset_index(drop=True)
    series = (("wmape_naive", "Naive: next week = last week"),
              ("wmape_flat", "Flat: recent average"),
              ("wmape_seasonal", "Seasonal: level x seasonal curve"))

    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(10.5, 4.4))
        ys = range(len(table))
        for y, (_, row) in zip(ys, table.iterrows()):
            values = [row[c] for c, _ in series]
            ax.plot([min(values), max(values)], [y, y], color=BASELINE, lw=2, zorder=1)
        for (column, label), color in zip(series, SERIES):
            ax.scatter(table[column], list(ys), s=80, color=color, edgecolor=SURFACE, linewidth=2,
                       zorder=3, label=label)

        right = table[[c for c, _ in series]].to_numpy().max() * 1.06
        for y, (_, row) in zip(ys, table.iterrows()):
            ax.text(right, y, f"{row['decision']}   {row['gain_vs_flat']:+.1f} pts vs flat",
                    va="center", ha="left", fontsize=9.5,
                    color=INK if row["decision"] == "ADOPT" else INK_2,
                    weight="semibold" if row["decision"] == "ADOPT" else "normal")

        ax.set_yticks(list(ys), labels=table["retailer"].str.replace("_", " ").str.title())
        ax.tick_params(axis="y", colors=INK_2, labelsize=10)
        ax.xaxis.set_major_locator(MultipleLocator(0.05))
        ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.set_xlim(0, right)
        ax.grid(axis="x")
        ax.spines["left"].set_visible(False)
        ax.set_xlabel("WMAPE, 8 weeks ahead (lower is better)", color=INK_2, labelpad=8)

        _header(fig, "Should each retailer's forecast follow the seasonal curve?",
                f"Four rolling origins. Adopt only if seasonal beats flat by at least "
                f"{ADOPTION.min_gain_points:.1f} points on {ADOPTION.min_items}+ items, a rule fixed before any "
                "result. Synthetic data.")
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, fontsize=9.5,
                  handletextpad=0.3, columnspacing=1.6, labelcolor=INK_2)
        fig.subplots_adjust(left=0.13, right=0.80, top=0.76, bottom=0.16)
        _save(fig, path)
    return fig
