"""One weekly review: signals -> rules -> investigator -> refuter -> final decision."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import seasonality
from .agents import Finding, Investigator, Refuter, Verdict
from .config import DEFAULT, ReviewConfig
from .rules import Decision, decide, reconcile
from .signals import Signals, build, complete_weeks, season_basis


@dataclass(frozen=True)
class ReviewRow:
    signals: Signals
    proposal: Decision
    finding: Finding | None
    verdict: Verdict | None
    final: Decision

    @property
    def needs_planner(self) -> bool:
        return self.verdict is not None and self.verdict.outcome == "SUSPECT"


def review(weekly: pd.DataFrame, plan: pd.DataFrame, as_of: pd.Timestamp,
           cfg: ReviewConfig = DEFAULT, refuter: Refuter | None = None,
           use_refuter: bool = True) -> list[ReviewRow]:
    refuter = refuter or Refuter()
    investigator = Investigator()
    history = complete_weeks(weekly, as_of)
    curves = seasonality.segment_indices(season_basis(history, as_of, cfg), cfg.spike_ratio)
    next_month = as_of.to_period("M") + 1
    plan_next = plan[plan["month"] == next_month].set_index(["retailer", "sku"])["forecast_units"]

    rows: list[ReviewRow] = []
    for (retailer, sku), frame in history.groupby(["retailer", "sku"], sort=False):
        segment = frame["segment"].iloc[0]
        s = build(frame, float(plan_next[(retailer, sku)]), next_month,
                  curves[(retailer, segment)], as_of, cfg)
        proposal = decide(s, cfg)
        finding = verdict = None
        final = proposal
        if proposal.flagged and use_refuter:
            finding = investigator.investigate(s, cfg)
            verdict = refuter.refute(finding, s, proposal, cfg)
            final = reconcile(proposal, verdict.outcome, verdict.reason)
        rows.append(ReviewRow(s, proposal, finding, verdict, final))
    return rows


def to_frame(rows: list[ReviewRow]) -> pd.DataFrame:
    return pd.DataFrame([{
        "retailer": r.signals.retailer,
        "sku": r.signals.sku,
        "scenario": r.signals.scenario,
        "proposed": r.proposal.action,
        "verdict": r.verdict.outcome if r.verdict else "",
        "final": r.final.action,
        "change": round(r.final.change, 3),
        "buffer": round(r.final.buffer, 3),
        "to_planner": r.needs_planner,
        "reason": r.final.reasons[-1] if r.final.reasons else "",
    } for r in rows])


def revised_plan(rows: list[ReviewRow], plan: pd.DataFrame) -> pd.DataFrame:
    """Apply each final decision to every future month of the plan."""
    factor = {(r.signals.retailer, r.signals.sku): (1 + r.final.change) * (1 + r.final.buffer) for r in rows}
    out = plan.copy()
    out["revised_units"] = [
        units * factor.get((ret, sku), 1.0)
        for ret, sku, units in zip(out["retailer"], out["sku"], out["forecast_units"])
    ]
    return out
