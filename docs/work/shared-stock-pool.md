# Back-orders at two retailers, caused by a third

Two retailers in one region kept getting back-ordered on items their own forecasts covered. The cause was a third account drawing on the same stock with no forecast behind it.

## The problem

All three accounts in that region are supplied from one shared stock pool. The third account had been ordering items that had no forecast: **27 of the 45 items it bought had a forecast of zero.** Its orders were real, but supply planning could not see them. So its draw showed up as shortfalls on the other two accounts' items, where it looked like a supply failure.

## Two traps in the data

- **The account's "sell-through" field was a copy of its shipments.** Month by month the values matched exactly. It carried no demand signal, so I used the account's actual orders as the demand signal instead.
- **A coverage value of 999.9 was a code, not a number.** It meant "no future demand planned", which in practice meant infinite coverage. Filtering on 999 would have found nothing.

## What I did

I built a forecast for the account from its own order history:

- **Account-level seasonality** from about two and a half years of orders. I checked it two independent ways (year-normalized ratios, and a centered 12-month moving average) so that a purchasing rhythm could not pass for a season. The two methods agreed.
- **Level** from a blend of the last 6 and 12 months.
- **New items' first month excluded.** This account buys a small test quantity first and then scales up, roughly 2 to 2.7 times. That is the opposite of a normal launch spike, so the usual outlier logic would have gotten it backwards.
- **Never below orders already confirmed.**

In a three-fold backtest, adding seasonality cut the account's monthly weighted error from 53.4% to 26.9%. Damping an unstable autumn peak brought it to 24.7%.

## Choosing by the right metric

The goal was fewer back-orders, so the deciding metric was **shortfall**, not WMAPE: how often, and by how much, the forecast came in under actual orders.

| Version | Shortfall rate | Account WMAPE |
|---|---|---|
| Full seasonal curve | 40.4% | 19.7% |
| Seasonal dips floored | 37.5% | 31.6% |
| Completely flat | 35.7% | 52.6% |

The flat version looked safest on shortfall *rate*. But its total shortfall in *units* went up, and overstock rose by about a third. Item-level orders here are lumpy and barely follow the account's seasonal curve, and the shortfall comes from those spikes, which flattening does not fix. I chose the floored version: it keeps the autumn peak and stops the winter dips from starving items.

## Result

- Raised as the lead finding of the review, with the account's first real forecast attached.
- Not yet measured: back-orders at the two affected retailers in the quarter after the forecast went in, against the quarter before.
