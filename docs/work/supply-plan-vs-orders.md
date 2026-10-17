# How much of a customer's plan to trust

A mass retailer sends a weekly supply plan covering the next year. Our lead time is three to four months. So the real question is how far ahead we can commit production against that plan, and which part of it keeps moving.

## What I did

- **Assembled 20 consecutive weekly plan snapshots** and matched each one against the orders that actually landed, aligned four months ahead, the long end of that lead time: a January plan is scored against May orders.
- **Read the files defensively, without editing them.** Across the 20 files there were five kinds of format drift: sheet-name case, column counts, which weekday the weekly buckets start on, and summary sheets whose layout changed. The reader absorbs all five, so the customer's files stay untouched.
- **Chose the join key after the first one broke.** Our own vendor codes carry variant suffixes, so matching on them failed silently. Matching on the customer's item number matched 99.1% of order lines.
- **Used an outer join.** An inner join silently drops items that were never in the plan but were still ordered. For one month it flipped the sign of the plan-versus-actual gap.
- **Anchored each month on its first plan.** Anchoring on the last plan of the month catches the customer's steepest late cut and makes the gap between horizons look far larger. On the first plan it was 1.2 times. I report the first-plan number and wrote the anchoring rule down.
- **Left out partial months and out-of-cycle orders**, so every comparison covers the same period.

## A finding that was not a data error

Items that looked like "ordered, but never in the plan" were mostly the customer re-coding existing products under new item numbers partway through the season. Matched at the product level, they had been planned, just late or under a different number. Every item was classified as one of three: **new item**, **quantity added late**, or **never in any plan**. That turned "the plan missed it" into "the plan re-coded it". The second is a much better conversation to have with a customer.

## Result

**The freshest plan was not the most accurate.** Each month was scored on the first plan received in it:

| Plan written | May | June | July | Average miss |
|---|---|---|---|---|
| 4 months ahead, the long end of our lead time | +5.2% | −6.4% | +14.5% | **8.7%** |
| 1 month ahead | +1.0% | −10.5% | +19.9% | 10.5% |

Gap = (actual orders − plan) ÷ plan. The customer cuts its plan hard in the last weeks before a month, and cuts too far. July's plan fell 17% between early May and early June. Actual orders landed within 0.5% of the early-May plan.

- **Scored on the last plan of each month instead, the result points the same way:** the nearest plan is still the least accurate. I lead with the first-plan comparison because it is the conservative one.
- **What it shows, and no more:** the assumption that the nearest plan is the most accurate did not hold. The plan reads best as a direction for total volume. I have not claimed a change in how production is committed.
- **Caveat:** only three months had complete actuals when this was written, so it is a direction, not a settled rule.

## Run it

A clean-room version on synthetic data: [notebook 04](https://github.com/yss2333/Jay-supply-chain-ai-portfolio/blob/main/system/notebooks/04_supply_plan_horizon.ipynb) — every horizon scored, both anchors, and what an inner join would have hidden.
