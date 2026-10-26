# Forecast, orders and back-orders in one tracker

One page per account lines up the retailer's own forecast, our forecast, the orders that arrived, what shipped and what is still on back-order, item by item and month by month. It exists so stock gets secured and allocated before a gap turns into a shortage.

## The problem

Three numbers lived in three places: the retailer's forecast in a file they email, [our forecast](forecasting-system.md) in the planning system, and orders and back-orders in the order ledger. Nobody read all three per item at once, so "buy or move stock for this item" got decided after the shortage. When an account blamed us for its back-orders, we had nothing to answer with.

## Constraints

- Every account sends a different file: daily columns in a binary workbook from a UK health-and-beauty retailer, a weekly grid split across three header rows from a UK drug chain, date-headed monthly columns from a [grocery wholesaler](wholesale-service-level.md).
- Their forecasts are short and rolling: two snapshots two weeks apart covered different months.
- Their item codes are not ours, and one wholesaler's ledger mixes two of our code prefixes.
- The UK accounts have no store-level sales feed.
- Their weeks straddle month ends, and nobody outside planning can query our warehouse.

## What I built

- **A self-contained HTML report per account** &mdash; the same hand-off idea as the [supplier coverage reports](dashboards.md), with data embedded, charts from a public library and no database connection. The UK file carries both accounts as tabs rather than a sum.
- **Five series per item per month:** retailer forecast, our forecast, orders, shipped and back-order, plus store sales and in-stock where a feed exists, hidden where it does not.
- **A week-to-month rule, written down:** a week goes whole to the month holding most of its days. I tried and dropped three alternatives; planners did not want a week split.
- **An item universe that is the union** of the three sources, because an item in only one of them is the interesting one.
- **Four checks before anyone sees it:** raw total equals the sum of months, mapping is 100%, the page's numbers equal the parsed table, orders equal the ERP.
- **A snapshot version for the wholesaler:** forecast by date received against the orders that followed, one tab per snapshot.

## What it caught / what it changed

- **It ties out.** Orders matched the ERP to the unit for both UK accounts, our forecast matched the planning total, and 100% of item codes mapped.
- **A parsing defect undercounted a retailer's forecast by 44%.** The reader handled only text dates, so date-valued headers were skipped: it read 44% less than the file held.
- **Our plan runs above theirs:** 8–34% higher over the months both cover, with year-to-date orders at 42% of our full-year plan. The difference is either over-planning or replenishment buffer, and we have never separated the two.
- **Scope inflated a gap.** Joining on both their product number and ours matched about 98% of the wholesaler's order lines; narrowing to nail items moved the forecast-over-order buffer from +65% to +90%.

## Limitations

- Retailer forecasts run three to four months out; past that the only line is ours.
- No per-item lead-time overlay, which would settle whether a forecast increase arrived inside our lead time.
- The snapshot-over-time view sits in the wholesaler report, not the tracker, which shows the latest file only.
- The UK accounts have no sales signal to check the retailer forecast against.
- It is a report, not an alert, and a refresh means re-running it on the new file.
