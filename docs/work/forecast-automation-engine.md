# From R to Python to a forecast engine

Over two years I moved our seasonality work off a paid platform's black box: an index in R in 2024, an automated Python version in 2025, and the seasonality layer that now runs inside the system we co-built. [The system around it is described separately](forecasting-system.md).

## The problem

Our statistical forecasts came out of a paid planning platform. I could see its output but not its arithmetic, so when a number looked wrong there was no way to reproduce it, explain it, or fix the part that was wrong.

The obvious in-house alternative had its own flaw. A seasonal curve built from shipments follows the retailer's ordering cadence, not shopper demand: an account that orders every other month produces a curve that alternates high and low, and the index reads that cadence as a season.

## 2024: a seasonality index in R

I wrote my own index in R. For each item it averaged a calendar month across years, then divided by the average of the months that actually exist in that item's history (not a fixed twelve), so a short history is not compared against months of zero. The curve averages 1.0.

Before that, sales were divided by the number of stores carrying the item. A planogram reset can double an item's distribution in a month; without normalizing, that reset becomes a seasonal peak the forecast repeats every year. Store-normalization separates "more stores" from "more demand per store." At this stage it was a step I ran myself, item by item, when a curve was needed.

## 2025: the same logic in Python, automated

I rewrote it in Python against data pulled from SAP into Snowflake instead of exported spreadsheets. It became reproducible (same inputs, same curve, steps I could show), and it could run for every account on a schedule, including Canada, which had not been getting a seasonal read of its own. It also became a step inside the forecast run rather than a document, which is what let the agent system later call it instead of rebuilding it.

## Today: the production seasonality layer

The index is built from store-normalized sell-through. Each item looks for a curve in order: its own history, then its product line, then its segment, then shipments, then flat. The segment curve is itself 60% sell-through and 40% shipments over 24 months.

The two are combined by Bayesian shrinkage. With `n` months of the item's own history and a prior weight of 12, the blended index is `(n × item + 12 × segment) / (n + 12)`. An item with four months of history borrows most of its shape from its segment. An item with four years does not.

Items with no history at all get a starting curve from their color: a vision model reads each item's color from product images, and a fixed color-to-month table sets the curve. Guards cap both ends: no seasonal cut above 1.15, a hold promoted to a raise above 1.30, a floor of 0.50 on the low-season dampener. One channel uses precomputed Prophet curves, where a backtest showed the existing curve had the season backwards.

## What I learned about which signal to trust

I tested four candidate sources on the same 309 items, each built only from data before the test window, scored by correlation with each item's actual monthly sales shape.

| Source of the seasonal curve | Mean correlation |
|---|---|
| Packaging color, where color reads as seasonal | 0.290 |
| Shipments (the incumbent method) | 0.143 |
| Point-of-sale, item level | 0.006 |
| Point-of-sale, segment level | −0.004 |

Blending diluted rather than helped: color at 70/30 scored 0.269, an even split 0.218. Color did not survive a later test on a larger sample with a different answer key: −0.036 across 248 pairs, against 0.330 across 1,714 for the shrinkage index. The two color figures are not directly comparable; the later one is the one I act on. The vision model stays limited to new items.

Read as a whole, the column shows that item-month seasonality is weakly predictable by any method I tried, 0.14 to 0.33 at best. So the decision logic deliberately does not read the seasonal index. Raise, lower and hold come from sell-through, shipments and store in-stock; seasonality adjusts the result afterwards, inside guards. A signal this weak would otherwise move decisions it has no business moving.

## Limitations

The answer keys are short (six months in one test, eight in the other) and contaminated by planogram resets, the exact event the index is meant to ignore. The color comparison covers only items whose packaging reads as seasonal. The one-channel Prophet switch rests on 34 items and one window. And the curves go stale as the item mix turns over, so they are rebuilt monthly and after every reset.

## What is not measured yet

I cannot separate the seasonality layer's share of the accuracy improvement; it shipped alongside the rule engine. The walk-forward re-test on the one switched channel needs a full year of answer key, in early 2027.
