"""The agent layer: an investigator that frames a claim, and a refuter that argues against it.

A single agent asked to find problems will confirm whatever it finds. So finding and
checking are separate roles, and the refuter's instruction is to refute, not to check.

The default refuter is deterministic and encodes the lenses in prompts/refuter.md.
LLMRefuter asks a model the same question with the same instructions; it is optional
and falls back to the deterministic refuter if the model or the API key is unavailable.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import DEFAULT, ReviewConfig
from .rules import Decision
from .signals import Signals

PROMPTS = Path(__file__).parent / "prompts"
OUTCOMES = ("CONFIRMED", "SUSPECT", "REFUTED")


@dataclass(frozen=True)
class Finding:
    claim: str                                  # what the flag suggests, stated as a claim to test
    flag: str                                   # the signal that raised the flag
    checks: tuple[tuple[str, str, str], ...]    # (what was checked, value, note)


@dataclass(frozen=True)
class Verdict:
    outcome: str    # CONFIRMED / SUSPECT / REFUTED
    reason: str


def _pct(x: float) -> str:
    return f"{round(x * 100):+d}%"


class Investigator:
    """Turns a flag into a claim and gathers the evidence around it."""

    def investigate(self, s: Signals, cfg: ReviewConfig = DEFAULT) -> Finding:
        w = cfg.window_weeks
        if s.sell_through_trend <= -cfg.momentum_cut:
            flag, claim = f"sell-through {_pct(s.sell_through_trend)} vs the prior {w} weeks", "demand fell"
        elif s.shipment_trend <= -cfg.shipment_flag and abs(s.gap) <= cfg.ok_band:
            flag, claim = f"shipments {_pct(s.shipment_trend)} vs the prior {w} weeks", "demand fell"
        elif s.shipment_trend >= cfg.shipment_flag and abs(s.gap) <= cfg.ok_band:
            flag, claim = f"shipments {_pct(s.shipment_trend)} vs the prior {w} weeks", "demand rose"
        elif s.gap < 0:
            flag, claim = f"demand estimate {_pct(s.gap)} vs plan", "the plan is too high"
        else:
            flag, claim = f"demand estimate {_pct(s.gap)} vs plan", "the plan is too low"

        def trend_word(x: float) -> str:
            return "up" if x >= cfg.trend_threshold else "down" if x <= -cfg.trend_threshold else "flat"

        checks = (
            (f"sell-through, last {w} weeks", _pct(s.sell_through_trend), trend_word(s.sell_through_trend)),
            ("  same, spike weeks removed", _pct(s.sell_through_trend_robust),
             "one week dominates the window" if s.pos_spike_in_window else ""),
            ("store-level in-stock", f"{s.in_stock:.0%}",
             "<- below floor" if s.in_stock < cfg.in_stock_floor else ""),
            (f"shipments, last {w} weeks", _pct(s.shipment_trend),
             "one week dominates the window" if s.shipment_spike_in_window else ""),
            ("open orders", _pct(s.open_orders_trend), trend_word(s.open_orders_trend)),
            ("history", f"{s.weeks_of_history} weeks",
             "new item" if s.weeks_of_history < cfg.new_item_weeks else ""),
        )
        return Finding(claim=claim, flag=flag, checks=checks)


class Refuter:
    """Tries to disprove the claim, using the lenses in prompts/refuter.md, in order."""

    def refute(self, finding: Finding, s: Signals, proposal: Decision,
               cfg: ReviewConfig = DEFAULT) -> Verdict:
        low_stock = s.in_stock < cfg.in_stock_floor
        flat_on_run_rate = abs(s.sell_through_trend_robust) < cfg.trend_threshold

        if finding.claim in ("demand fell", "the plan is too high"):
            # 1. Spike baseline: take the spike weeks out; if the fall goes with them, it was never a fall.
            if s.pos_spike_in_window and s.sell_through_trend_robust > -cfg.trend_threshold:
                return Verdict("REFUTED", "one spike week sits in the comparison window; on run-rate, "
                               f"sell-through is {_pct(s.sell_through_trend_robust)}")
            # 2. Supply, not demand
            if low_stock and flat_on_run_rate:
                return Verdict("REFUTED", f"flat sell-through with in-stock at {s.in_stock:.0%} indicates "
                               "a supply gap, not a demand drop")
            # 4. Thin history
            if s.weeks_of_history < cfg.new_item_weeks:
                return Verdict("SUSPECT", f"{s.weeks_of_history} weeks of history is too little to call it")
            if s.sell_through_trend_robust <= -cfg.trend_threshold:
                return Verdict("CONFIRMED", f"sell-through is down on run-rate too "
                               f"({_pct(s.sell_through_trend_robust)}) with in-stock at {s.in_stock:.0%}: "
                               "the fall is in demand")
            if s.gap_robust < -cfg.ok_band:
                return Verdict("CONFIRMED", f"sell-through is steady, but at a level {_pct(s.gap_robust)} "
                               f"below plan with in-stock at {s.in_stock:.0%}: the plan was set too high")
            return Verdict("SUSPECT", "the plan looks high, but sell-through is not clearly falling")

        # Claims that demand is higher than planned
        # 1. Spike baseline, on the shipment side
        if s.shipment_spike_in_window and flat_on_run_rate:
            return Verdict("REFUTED", "one bulk shipment makes the rise; sell-through is flat")
        # 3. One source
        support = []
        if s.sell_through_trend_robust >= cfg.trend_threshold:
            support.append(f"sell-through {_pct(s.sell_through_trend_robust)}")
        if s.open_orders_trend >= cfg.trend_threshold:
            support.append(f"open orders {_pct(s.open_orders_trend)}")
        if not support:
            return Verdict("REFUTED", "only one source says demand rose")
        if s.weeks_of_history < cfg.new_item_weeks:
            return Verdict("SUSPECT", f"{s.weeks_of_history} weeks of history is too little to call it")
        return Verdict("CONFIRMED", " and ".join(support) + " agree")


class LLMRefuter(Refuter):
    """The same role, asked of a model. Needs the `anthropic` package and ANTHROPIC_API_KEY."""

    def __init__(self, model: str = "claude-sonnet-5"):
        self.model = model

    def refute(self, finding: Finding, s: Signals, proposal: Decision,
               cfg: ReviewConfig = DEFAULT) -> Verdict:
        try:
            import anthropic

            evidence = {
                "claim": finding.claim,
                "flag": finding.flag,
                "proposed_action": proposal.action,
                "checks": [{"check": c, "value": v, "note": n} for c, v, n in finding.checks],
                "signals": {k: v for k, v in asdict(s).items() if k not in ("retailer", "sku", "scenario")},
                "config": asdict(cfg),
            }
            message = anthropic.Anthropic().messages.create(
                model=self.model,
                max_tokens=300,
                system=(PROMPTS / "refuter.md").read_text(encoding="utf-8"),
                messages=[{"role": "user", "content": json.dumps(evidence, default=str)}],
            )
            text = "".join(b.text for b in message.content if getattr(b, "type", "") == "text").strip()
            outcome, _, reason = text.partition(":")
            if outcome.strip().upper() in OUTCOMES:
                return Verdict(outcome.strip().upper(), reason.strip())
        except Exception:  # no key, no package, no network: use the deterministic refuter
            pass
        return super().refute(finding, s, proposal, cfg)
