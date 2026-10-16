# Architecture

A clean-room rebuild of an agentic forecast review. This document explains how it is put together, and how the production system it is modelled on got to this shape.

---

## 1. Three layers

```
┌─ Judgment layer ── sub-agents, defined as prompts ─────────────┐
│  retailer-scout      investigates one retailer, in parallel    │
│  forecast-refuter    tries to disprove every finding           │
│  item-investigator   settles one item whose signals disagree   │
│  .claude/agents/*.md                                           │
└──────────────────────────────┬─────────────────────────────────┘
                               │ calls
┌─ Execution layer ── deterministic tools ───────────────────────┐
│  MCP server: list_retailers · review_retailer · item_signals   │
│  weekly_series · refute · weekly_review · seasonal_backtest    │
│  explain_rules · excess_inventory · aged_stock · coverage_plan │
│  plan_horizon_accuracy · leakage_check           mcp_server.py │
│  Python package: signals · seasonality · rules · agents        │
│  pipeline · validation                         forecast_review/│
│  inventory · plan_accuracy · coverage · leakage     supply_ops/│
└──────────────────────────────┬─────────────────────────────────┘
                               │ reads
┌─ Data layer ───────────────────────────────────────────────────┐
│  Synthetic weekly sell-through, store in-stock, shipments,     │
│  open orders and a six-month plan         forecast_review/     │
│                                           synthetic.py         │
└────────────────────────────────────────────────────────────────┘
```

An interactive version of this map, with guided views: [`docs/diagrams/system-map.html`](../docs/diagrams/system-map.html) (one HTML file; open it in a browser).

**Why the split.** Tools are deterministic and unit-tested. Judgment is written as prompts and can change without touching code. Adding an agent never touches the data or the rules. The same split holds in production, where the data layer is real point-of-sale, shipment and inventory data and the tool layer is much larger.

---

## 2. One item, step by step

| Step | Module | What happens |
|---|---|---|
| Read | `signals.py` | Complete weeks only. The last four weeks are compared with the four before, on deseasonalized sales, both plainly and with spike weeks removed |
| Season | `seasonality.py` | A store-normalized seasonal index, shrunk toward the segment's curve by n / (n + τ). Built from history that ends before the weeks being judged, with spike weeks clipped |
| Decide | `rules.py` | RAISE, LOWER, HOLD or OK. Cuts are capped, blocked below the in-stock floor and blocked for new items. A raise needs an independent second signal |
| Frame | `agents.py` → `Investigator` | States what the flag implies as a claim: "demand fell", "demand rose", "the plan is too high", "the plan is too low" |
| Argue | `agents.py` → `Refuter` | Tries to disprove the claim through fixed lenses: spike baseline, supply rather than demand, one source, thin history |
| Settle | `rules.reconcile` | A refuted change does not ship. A suspect one goes to a planner |

The order of checks in `rules.decide`, drawn: [`docs/diagrams/review-decision.html`](../docs/diagrams/review-decision.html).

The deterministic refuter follows `forecast_review/prompts/refuter.md` line for line. `LLMRefuter` sends the same prompt and evidence to a model and falls back to the deterministic version if the model is unavailable.

---

## 3. How the production system got here

**Phase 1: one pipeline.** Shipment plans, actual shipments, retailer point-of-sale, store in-stock and syndicated rankings were merged into one table, and a review function produced an action per item. The governing idea was already there: shipments falling below plan do not mean demand fell, so sell-through is the demand signal and an item stores cannot keep on the shelf is never cut.

**Phase 2: the rules accumulated.** Every exception found in operation became a written rule: caps by region, a buffer for low in-stock, a protection window for new items, a guard against one-off bulk shipments, a blend that shifts with how far into the month the data runs. The rules were kept in plain-language documents rather than buried in code, so people and agents read the same source. That is also why other product divisions could adopt the system in days.

**Phase 3: a judgment layer.** Scouts investigate retailers in parallel, a separate agent refutes their findings, and an investigator settles the hard cases. Only prompt files were added; no data pipeline changed. The reason for the split is the lesson of Phase 2: a single agent asked to find problems finds them, including the ones that are not real.

This repository rebuilds Phase 3 at small scale, on synthetic data.

---

## 4. Validation

| Stage | Question | Where |
|---|---|---|
| Unit | Does each rule do what it says? | `tests/`: 31 tests |
| Backtest | Is it more accurate on weeks it could not see? | `validation.seasonal_backtest`, rolling origins, scored against a naive forecast |
| Regression | Did a change touch anything it was not meant to? | `validation.compare`, same data, old rules against new |
| Shadow | What would change if it shipped? | `validation.compare`, candidate beside live, nothing downstream |

Two honesty checks run as tests: an unfinished week is never read, and changing data after a forecast origin does not move the forecast.

---

## 5. What this version leaves out

- Real data, and everything that comes with it: retailer file formats, store-count changes, syndicated rankings.
- Inventory position, lead times and order cadence. Signals here are one four-week window at weekly grain.
- The vision model that gives new items a starting seasonal curve from their packaging.
- Production parameters. Every number in `config.py` is an illustrative round value.
