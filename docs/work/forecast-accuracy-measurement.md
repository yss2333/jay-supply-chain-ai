# Measuring how wrong the forecast was

I built the exception report that scores every item's shipments against its forecast each month. The headline accuracy figures on this site come from a separate, line-level backtest, described below.

## The problem

Forecasts were written each month and then never looked at again. When an item went on back-order or piled up, the argument was about whose call it had been, not how far off the plan was. There was no agreed number to improve against.

## Constraints

The ERP holds a monthly forecast per item, customer and plant, and shipments and open orders separately. Neither keeps a history of its own accuracy: the forecast row is overwritten as the month moves.

Shipping is lumpy. Many items ship on a two-month order cycle, so one month tells you almost nothing — a large month follows an empty one and both look wrong. The current month is always incomplete, by an amount that depends on the day you run it.

## What I built

A Python pipeline pulls forecast, shipments and open orders from the data warehouse for the domestic and Canada plants, keeps active, normally planned nail items with a forecast, and computes one measure.

- **A trailing three-month ratio** — shipped plus open orders over forecast, summed across the three months before the current one. The rolling sum absorbs the order cycle: an empty month is paid for by the next.
- **A flag band of 75 to 105 percent.** Inside it nobody looks; outside it the item goes on an exception list. It is asymmetric on purpose — 25 points below plan, 5 above — because shipping above plan is rarer and says more.
- **Two lists.** The three-month list is the accuracy measure. A second flags the current month early, and before the 20th it flags only items above plan, since a month in progress always looks short.
- Both are dated workbooks in the shared folders planners already use. The same data feeds a Power BI report.

## How the number is defined

WMAPE: the sum of absolute error divided by the sum of actual, weighted by volume. A high-volume item missing by a tenth matters more than a slow seller missing by double, and the weighting says so.

The denominator is actual, the standard form, so ordering too much is not rewarded. Items selling fewer than five units a month are scored separately, so a near-zero month cannot blow up the ratio.

WMAPE is absolute, so it cannot show direction. The signed ratio and the band carry that: WMAPE for the size of the miss, the ratio for whether we run over or under.

An unfinished month is never scored: the window starts one month back, so the current month appears only on the early-warning list.

## What it made possible

Planners now work the exception list, and drift above plan surfaces mid-month.

The headline figures are measured separately. On our eight major domestic accounts, weighted error went from 35–45% under the previous process to 18–25% in 2026 Q1, checked on a six-month rolling backtest. It is scored line by line (customer, month and item), with continuing items scored three months ahead (October's shipments against the forecast made in July), inside our three-to-four-month production lead time, and newly launched items one month ahead. Each range is the spread across retailers, not uncertainty in the measurement.

## Limitations

- It measures shipment against forecast, not demand. Shipping short for lack of stock scores as a miss.
- Open orders count on the shipped side, so part of the number is commitment, not goods out the door.
- An item that shipped nothing for three months produces no ratio at all and falls off the list.
- Monthly buckets hide timing within the month, and the measure flags without attributing cause.

## Run it

A clean-room version on synthetic data: [notebook 02](https://github.com/yss2333/jay-supply-chain-ai/blob/main/system/notebooks/02_validation.ipynb) — the validation stages, and what an unfinished month does to a score.
