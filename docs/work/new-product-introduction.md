# Forecasting new products before they sell

**I developed the cross-retailer sales-velocity forecast that supported a pitch securing a second national retailer for a nail set ranked No. 4 in sales at its launch retailer**, scaling that forecast to the new retailer's distribution. Across launches, I forecast 178 new items in 380+ retailer launches, and wrote the launch-window rules that stop the review system cutting a launch too early.

[The problem](#the-problem) · [How a launch is forecast](#how-a-launch-is-forecast) · [The forecast behind a new retailer](#the-forecast-behind-a-new-retailer) · [Launch-window rules](#launch-window-rules) · [Limitations](#limitations)

## The problem

A new item has no sales history, so its forecast has to come from somewhere other than itself. And the first shipment is only half the risk. Once the initial inventory sells through, replenishment has to already be on its way, or the item sits empty through the launch window, the period the retailer is watching. Plan too much and the surplus becomes [excess and aging inventory](inventory-health-reporting.md) within a year.

## Constraints

- **No history for the item at that retailer, often none anywhere.** Nothing to extrapolate from.
- **Store counts are not fixed or known per item.** A new item has none of its own, and the retailer's counts move week to week.
- **Sell-through lags the fill.** The first shipments are pipeline, not demand. Read them as demand and you over-build; read the quiet weeks after as failure and you cut a healthy launch.

## How a launch is forecast

For each of the 178 new items and 380+ retailer launches, a launch forecast is store count × comparable items' weekly sell-through per store × weeks, shaped by a starting seasonal curve.

- **The retailer's planogram changes** say which items are added, kept or deleted, and when. They are an input the retailer sends us, along with other information retailers share; they are not something we plan together.
- **Store counts**: how many of the retailer's stores will carry the item.
- **Comparable items** are chosen by a planner, not by the system. Where the same item already sells at another retailer, its weekly sell-through per store is the strongest comparison available.
- **A starting seasonal curve.** A vision model reads each new item's color from product images, and a fixed color-to-month table sets its starting curve until real sales replace it.

## The forecast behind a new retailer

A nail set ranked No. 4 in sales at the retailer that launched it. To pitch it to a second national retailer, I took its sales per store per week at the launch retailer and scaled that velocity to the new retailer's store count. That forecast went into the sales team's pitch, and the second retailer took the set.

I then designed a regression model with shrinkage that scores each product attribute and each retailer's fit, so the same reasoning can reach items with no sales history anywhere. It is a design so far: a clean attribute table is the work it still needs.

## Launch-window rules

These live in [the forecasting system](forecasting-system.md), and they respond to the shape of an item's shipments, so they apply to anything that looks like a launch, not only to items tagged as new.

**A launch protection window.** For six to eight weeks after the initial pipeline ships, an item is marked as recently launched, with the weeks since its first shipment. The first version marked but did not override: the system could still recommend a cut, with "3 weeks since launch" in front of the planner. The later version is harder. If the first shipment falls inside the last two months, the cut is blocked while the item settles.

**A fill-rate gate.** Compare the last two months pooled: total shipped divided by total forecast, not the average of two monthly ratios. Averaging lets one lumpy month produce a figure neither month showed. Above the upper threshold it counts as evidence to raise; between them a cut is blocked; below the lower one the item is genuinely declining and the cut proceeds. Thresholds are per plant: 1.20 and 0.50 for domestic, UK and Canada; 1.15 and 0.40 for the EU, deliberately more conservative.

Backtested on 500 new-item cases over a 24-month lookback, false cuts fell from 43.7% to 6.5%, about seven times fewer. By plant: 5.2% of 348 domestic cases, 0% of 33 UK cases, 12.5% of 119 EU cases. Recall on genuine declines 63.8%, overall accuracy 72.6%.

**A pre-fill pattern is not a spike.** One shipment more than twice the forecast and over a thousand units with nothing after it is a distribution centre filling up, waiting for sell-through. It is flagged, and the cut blocked.

## Limitations

- The pitch was the sales team's, and the retailer's decision had other inputs. My part was the forecast behind it.
- The forecast is only as good as the comparable items a planner picks. The system does not choose them.
- The color-to-season link is weak on existing items, which is why color only sets a new item's starting curve and is replaced by real sales as they arrive.
- The EU false-cut rate of 12.5% is monitored, not solved, and 33 UK cases is too small a sample to conclude from.
- The fill-rate backtest compared shipments against forecast only. Sell-through and store in-stock were not in it, so live behaviour can differ.
- The gate cannot separate an every-other-month ordering pattern from a real supply shortfall; both look like shipments below forecast.
