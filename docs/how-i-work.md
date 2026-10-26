# How I decide a number is real

Most of what I build is a judgment about demand, and most arguments about demand turn out to be arguments about evidence. How I weigh that evidence is the part of my work that does not change from project to project.

## Four stages, four different questions

| Stage | Question | What it looks like |
|---|---|---|
| **Unit** | Does the change do what I intended? | Cases I can check by hand, offline, before it touches data |
| **Backtest** | Is it actually more accurate? | Predict a period the model cannot see, score against what shipped. Mandatory whenever a threshold or a cap is being set — a threshold chosen without one is a preference wearing a number |
| **Regression** | Did it break anything else? | Same data, before and after. The only differences allowed are the ones I intended, and I check that the count matches |
| **Shadow** | Should it ship? | Run it beside the live system on real weeks, with nothing downstream connected, and compare |

Each stage is a command in the [clean-room system](https://github.com/yss2333/jay-supply-chain-ai/tree/main/system): `python -m forecast_review backtest | regression | shadow`, plus the unit tests.

## Always against a baseline

A forecast is judged against what you would have got for free.

- **Naive**: next week equals last week. If a method cannot beat that, it has not earned its complexity.
- **The incumbent**: whatever we run today.
- **Forecast value added**: the gain over the naive forecast, in points. Negative value added is a finding, not a failure to hide. It is how you learn that a human touch, or a model, is making things worse.

## The metric comes from the question

- Asking about the **shape** of a season? That is correlation. But correlation cannot see level: a forecast uniformly 20% too low still scores a perfect 1.00.
- Asking about **quantity**? That is WMAPE. But WMAPE cannot see direction: it prices a stockout and an overstock identically, and the business does not.
- Asking about **service**? Then it is fill rate and the shortfall against confirmed orders, read next to inventory, because you can always buy a better fill rate by holding more stock.
- Asking about **money**? Then someone in finance has to recognise the number, which usually means it is smaller and slower than the model says.

## The decision log

Three real changes, and what the test said. One of them did not ship.

| Change proposed | How I tested it | What the test said | Shipped | What it protected |
|---|---|---|---|---|
| A recovery guard for items chronically shipped short | Compared three candidate thresholds against historical fills; took the first where false positives reached zero | In a small backtest at one account, it stopped most cuts on items that were already under-forecast | Yes | Items stores could not keep on the shelf stopped being cut further |
| That guard, before release | Regression against the live system on identical data | It changed exactly the rows it tagged, and nothing else | Yes | The change did what it claimed, and only that |
| Image-derived curves in place of erratic seasonal curves on existing items | Adversarial review before release, against the guardrails it would interact with | It would have silently suppressed holiday peaks. Package color describes packaging, not demand | No (color stays only as a new item's starting curve) | Peak-season forecasts were not quietly cut on eighteen items |

## The checks I run on my own numbers

- "Looks fine" is not evidence.
- Set the bar before you see the number. A threshold chosen afterwards is a preference.
- A pleasant surprise is more dangerous than an unpleasant one. Single-digit error on monthly item-level demand is almost always leakage.
- Correlation cannot see level. WMAPE cannot see direction. Pick the metric from the question.
- Never score an unfinished month.
- If a number does not reproduce on a different day, it is not a number yet.
- Fix the data before you judge the item. [One line of integrity checking](work/data-integrity-review.md) once changed 79 items' decisions.

## One item, start to finish

```
ACCOUNT   national drugstore chain · 78 items in scope
FLAG      shipments −59% vs 4-week average
CHECK     sell-through, last 4 weeks ......  flat
CHECK     store-level in-stock ...........  71%  ← below floor
CHECK     open orders ....................  2 pending
REFUTE    "demand fell" — not supported. Flat sell-through with
          low in-stock indicates a supply gap, not a demand drop.
VERDICT   HOLD · forecast unchanged · buffer applied
```

Most of what the system produces is, by design, a non-event like this one.
