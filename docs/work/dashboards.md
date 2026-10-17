# Dashboards for vendors, retailers and the warehouse

Five tools built for people outside demand planning: suppliers, a third-party warehouse, sales and procurement. Each one ties out to the ERP before anyone sees it.

## Production coverage for suppliers

Four suppliers decide what to produce next, and none of them can see our data warehouse. So they get a self-contained HTML report instead. It shows each item's coverage in weeks, computed from live stock and the ERP's supply-and-demand schedule, and sorts every item into one of five actions: critical (no stock), rush (under 4 weeks), urgent (4–8 weeks), OK (8–16 weeks) or excess (over 16 weeks). An internal Streamlit version runs on the same data.

- **Matches the ERP screen exactly.** The first version read stock from the overnight schedule snapshot, and on one item it was **13,994 units** short: a receipt posted that morning. Once stock came from the live stock table, the report matched the ERP to the unit.
- **Only items with a current or future forecast,** the same gate the forecasting system uses. The list went from **400 items to 319**, dropping **81** that suppliers were being asked about for nothing.
- First run: **28 critical, 157 rush, 76 urgent, 46 OK, 12 excess**. That is the order suppliers work through the list.

## Retailer forecast against orders, UK

Two UK retailers send their own forecasts. A tracker lines each one up against our forecast, the orders that arrived, what shipped and what is on back-order, item by item. It ties out to the ERP to the unit, and it caught a parsing defect that had been undercounting one retailer's forecast by 44%. It has its own page: [forecast, orders and back-orders in one tracker](fc-order-backorder-tracker.md).

## Procurement dashboard

Receipts, open purchase orders, inbound shipments and planned orders in one view. It can be read by goods-receipt date or by PO issue date, and followed down to a single item. It lives on the team drive.

- **Ties to the ERP within 0.07%** on quantity; value matches.
- **Caught a window bug.** The forward view was hard-coded to end in January, so every month's run showed less of the future. By August, planned orders had fallen from **1,267 rows to 159**, even though the ERP held planned orders through the end of the following year. The window now rolls 18 months ahead.

## UK warehouse velocity

The UK third-party warehouse asked which items to move to ground level. Of **164** nail items on site:

- **71** are active and should stay accessible. **93** should be cleared from the pick face: either discontinued, or with no forecast left.
- Ranked by sales since May 2025, the top **20%** of items (32) carried **71.6%** of sales. The next 30% carried 21.1%, and the bottom half 7.3%. The fast movers went to ground level.
- Ranking by item count rather than cumulative sales was deliberate. A cumulative cut named only two items as fast, which is no use for deciding pallet positions.

## Short-ships behind a drop in store stock

Store in-stock fell at a national mass retailer, and the first read was that the retailer was ordering less. Orders by date received, compared over equal-length windows, said otherwise. On the low-stock items, orders held or rose, and **we short-shipped 9–22%** of what was ordered on them. The fix was on our side: supply, not the account.

- The rule it left behind: **compare windows of equal length.** An earlier cut compared 3 weeks against a 9-week average that included a spike, and produced a −90% that meant nothing.

## Run it

A clean-room version on synthetic data: [notebook 05](https://github.com/yss2333/Jay-supply-chain-ai-portfolio/blob/main/system/notebooks/05_coverage_and_routing.ipynb) — the coverage number behind the supplier report, and its five tiers.
