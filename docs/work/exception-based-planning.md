# What the weekly job became

**The accuracy gain is the easy part to state. The harder change is that the weekly review stopped being a review of everything.** Rules now decide what they can settle, a separate agent tries to disprove every flagged call against the raw data, and a planner spends the week on what the rules could not settle.

[The problem](#the-problem) · [What changed](#what-changed) · [Where it hands back](#where-it-hands-back-to-a-person) · [Does reviewing less mean missing more?](#does-reviewing-less-mean-missing-more) · [The same method, twice](#the-same-method-twice)

## The problem

A weekly forecast review used to mean opening four things (point-of-sale, shipments, the current forecast, the retailer's own file) and reconciling them by hand, item by item, account by account.

That had two problems, and the second was the expensive one.

It was slow: one account took about five hours a week, more than the team could give 20-plus accounts every week, so Canada and Europe were reviewed monthly or skipped.

And it was **not reproducible**. Two planners could look at the same item and reach different conclusions, both defensible, because the judgment had never been written down. It lived in each person's head, where it could not be questioned, compared or improved. If nobody can explain a forecast, nobody can argue with it, even when it is wrong.

## What changed

| | Before | Now |
|---|---|---|
| Getting the data | four separate pulls, reconciled by hand | one plain-language request; the system pulls and reconciles |
| Deciding | person by person, not reproducible | written rules plus AI agents, every call recorded with its reason |
| Checking | none; a second person re-read it if there was time | every call passes about thirty guardrails, and a separate agent tries to disprove each **flagged** call before a planner sees it |
| The planner's week | review everything | judge what the rules could not settle |
| Cadence | monthly | weekly, as the demand input to S&OP |

The checking layer is the part people ask about. It is not the same model run twice. A separate agent takes each flagged call and tries to disprove it against the raw weekly data: is the comparison like for like, is a single spike week driving it, do the other sources agree, is a tool limit behind it. It returns confirmed, suspect or refuted. In one case it showed that a 59% sales drop came from a single spike week, and a healthy item was not cut.

## Where it hands back to a person

The system is built to stop, and where it stops was decided in advance rather than after an incident.

- **Uncertain signals hold.** If the evidence disagrees with itself, the forecast does not move, and with low store stock the system never cuts on its own.
- **Outliers do not raise on their own.** A shipment far outside an item's own history is flagged, not acted on.
- **The current month is frozen**, so a mid-cycle number cannot whipsaw the plan.
- **Cuts have floors** — a hard limit on how far a forecast can fall in one pass, and a tighter one for new products, whose early months look like weakness and usually are not.
- **A consistency guard** rejects decisions whose direction and number disagree.
- **Every output is versioned**, so any decision can be traced back to what it saw.

The phrase the team uses is that the system proposes and the planner disposes. It is a constraint built into the design.

## Does reviewing less mean missing more?

No, because **the coverage did not shrink.**

Every item is still reviewed every cycle. What changed is who reviews it. The rules review all of them; a person looks at the share the rules could not settle.

The old way had a gap of its own. A planner spreading attention evenly across hundreds of lines was not giving each line equal attention: the lines near the end of the list got less. Now attention is concentrated where the uncertainty is. What was automated is the volume, not the judgment.

## The same method, twice

The [freight routing tool](shipping-route-automation.md) was built the same way, for a different decision: every line of a supplier's shipping plan is judged against the destination's own transit time, and a buyer sees the roughly 7% the rules cannot settle.

Both problems got the same method: write the judgment down, let the rules handle what they can settle, and put a person on what they cannot. Once the judgment is written down, people can argue with it, and that is how it improves.

## What I cannot show here

How much of the improvement came from the process change rather than the new rules and agents. Both landed in the same period, and I have no clean way to separate them. The accuracy numbers on [the forecasting system](forecasting-system.md) are measured; the claim on this page is about how the work is organised.
