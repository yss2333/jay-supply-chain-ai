# From SAP to Snowflake

Most of the order and shipment numbers on this site are read from one place: the order master data I built in Python on Snowflake.

It started as plumbing for something else. The planning platform we used needed order history to model against, and that history lived in per-plant, per-year extracts that I was pasting together by hand every month. Building it properly turned a monthly chore into a weekly refresh. Once the data existed, things could be built on top of it that were not worth attempting before, including [the order trend dashboard](order-trend-dashboard.md) that other teams now use.

## The problem

The data a demand planner needs arrives in pieces: shipment plans and actual shipments from the ERP, orders and back-orders from the sales ledger, point-of-sale and store in-stock from each retailer, syndicated rankings from a market data provider, inventory and open supply from the material planning system.

Each lives somewhere else, in a different shape, on a different schedule. The practical effect is that nobody asks the second question. You pull a report to answer one thing, and the follow-up, such as whether this account differs from the others or this month from last year, costs another afternoon, so it does not get asked.

## Constraints

- The ERP is the system of record and is not going to change to suit reporting.
- Retailer files change shape without warning: a column moves, a panel is renamed, a weekly file arrives monthly.
- Identifiers do not match across systems. The same product has one code in the ERP, another at the retailer, and sometimes a third after the retailer re-codes it mid-season.
- Regions differ. Plants across the US, Canada and Europe each have their own conventions, currencies and calendars.

## What I built

- **Order master data on Snowflake, in Python.** Order lines from every plant and year joined into one history, with the material master, purchase prices and store counts attached.
- **Retailer feeds normalised on the way in**: identifier mapping, weekly-to-monthly conversion where a retailer plans in weeks and we plan in months, and channel rules for how each account reports in-stock.
- **Defensive parsers.** Files that change shape are detected and either handled or refused loudly. A silent empty table is the failure that costs a week ([what that looks like](data-integrity-review.md)).
- **One builder, reused.** The excess and aging reports share a single inventory builder, so their totals tie out by construction.

## What it made possible

- The [forecasting system](forecasting-system.md) reads one merged view per item and account instead of three files.
- [Excess and aging reporting](inventory-health-reporting.md) across five plants runs on a schedule instead of being rebuilt by hand.
- Questions that used to be projects (a customer's plan against the orders that landed, a region's back-orders by cause) became [a report](supply-plan-vs-orders.md) someone can re-run in minutes.
- The same models feed [the dashboards](order-trend-dashboard.md) other teams use, so planning and reporting stop arguing about whose number is right.

## What it comes to

- **Four years of order history across five markets in North America and Europe**, conformed into one model: about **1.6 million order lines**, each carrying ordered, confirmed, delivered and short quantities with their values.
- **Refreshed weekly, where it used to be assembled by hand once a month.** The live order model behind the reporting is an order file of about 900,000 lines that still rebuilds on that cadence.
- **Unmatched records are output, not dropped.** Items that fail to match the material master land in an exception file, so a missing master shows up as a list to fix rather than as a quietly smaller number.

## Limitations

This is a reporting platform, not a warehouse redesign. It reads what the ERP produces and does not fix upstream master data. Where a retailer re-codes an item mid-season, the mapping catches it after the fact rather than preventing it. And a scheduled extract is a copy: anything that needs the live position, like a stock check inside the order cycle, reads the source system directly.
