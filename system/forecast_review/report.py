"""Output: one trace per flagged item, and a summary of the week."""
from __future__ import annotations

from collections import Counter

import pandas as pd

from .pipeline import ReviewRow, to_frame
from .rules import Decision


def verdict_text(d: Decision) -> str:
    if d.action in ("RAISE", "LOWER"):
        text = f"{d.action} {d.change:+.0%}"
    elif d.action == "HOLD":
        text = "HOLD · forecast unchanged"
    else:
        return "OK"
    return text + (f" · buffer {d.buffer:+.0%}" if d.buffer else "")


def trace(row: ReviewRow) -> str:
    s, f, p, v = row.signals, row.finding, row.proposal, row.verdict
    lines = [f"ITEM      {s.retailer} · {s.sku} · {s.segment}", f"FLAG      {f.flag}"]
    for label, value, note in f.checks:
        dots = "." * max(2, 34 - len(label))
        lines.append(f"CHECK     {label} {dots} {value:>6}  {note}".rstrip())
    proposed = p.action + (f" {p.change:+.0%}" if p.change else "")
    lines.append(f"RULE      proposed {proposed}: {p.reasons[0]}")
    lines.append(f'REFUTE    "{f.claim}": {v.outcome}. {v.reason}')
    lines.append(f"VERDICT   {verdict_text(row.final)}" + (" · sent to planner" if row.needs_planner else ""))
    return "\n".join(lines)


def summary(rows: list[ReviewRow]) -> str:
    final = Counter(r.final.action for r in rows)
    flagged = sum(r.proposal.flagged for r in rows)
    refuted = sum(1 for r in rows if r.verdict and r.verdict.outcome == "REFUTED")
    planner = sum(r.needs_planner for r in rows)
    parts = " · ".join(f"{a} {final.get(a, 0)}" for a in ("RAISE", "LOWER", "HOLD", "OK"))
    return (f"{len(rows)} items · {flagged} flagged · {refuted} claims refuted · "
            f"{planner} sent to planner\n{parts}")


def markdown(rows: list[ReviewRow], as_of: pd.Timestamp) -> str:
    table = to_frame([r for r in rows if r.proposal.flagged])
    lines = [
        f"# Weekly forecast review, week ending {as_of:%Y-%m-%d}",
        "",
        "Synthetic data. Every retailer, item and number here is generated.",
        "",
        "```text",
        summary(rows),
        "```",
        "",
        "## Flagged items",
        "",
        table.to_markdown(index=False) if _has_tabulate()
        else "```text\n" + table.to_string(index=False) + "\n```",
        "",
        "## Traces",
        "",
    ]
    for r in rows:
        if r.proposal.flagged:
            lines += ["```text", trace(r), "```", ""]
    return "\n".join(lines)


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False
