# Stock availability checks, automated

Retail accounts email a list of items and quantities and ask what we can ship. In 2025 I fielded 5+ of these a week from 15+ accounts across the US, Canada and Europe, and automated the shippable-inventory calculation, net of open orders and deliveries, with SAP macros and Python. I released stock only once forecast demand was covered, to protect service levels at our main retailers.

In 2026 the check moved onto the agent system as an order-promising tool. The answer now comes from a scheduled ERP extract and a written rule, instead of a planner stepping through the stock screen item by item.

## The problem

Two questions hide inside one stock check: can we cover this item over the next few months, and how much can we ship against this order now. Answered by eye from one screen, they got mixed. The future balance told an account we were out while stock sat on the floor; on-hand alone hid a hole two months out.

## Constraints

- Requests arrive as email attachments in each account's own layout: a flat table, a header buried five rows down, or a monthly forecast that is not a stock check at all.
- The ERP's available quantity already deducts forecast demand, not just real orders.
- Registering an application against the mail system was not an option, so the email step runs inside the desktop client's own session.
- Deadlines differ by account. A UK health-and-beauty retailer orders every Monday, 20–30 items in a normal week and 40–55 in a rebuild week. A US drug chain orders midweek and picks the following Monday, so inbound stock has to land before then.

## What I built

- **One extract, one source.** A single query returns stock and every future supply and demand event per item and plant; the back-order tools and the [supplier coverage reports](dashboards.md) call it too, so a fix lands everywhere.
- **Three balances, all shown:** everything the ERP shows; everything but planned orders and requisitions; and confirmed only, meaning real orders and confirmed inbound. Judgment uses confirmed.
- **Two separate answers:** coverage over six months, or one named month when that is all the account asked, and [allocation](allocation.md) — full, partial or out — from physical on-hand only.
- **A back-in-stock date when coverage fails:** the first confirmed inbound after today, plus three days for a shipment already notified or seven for a purchase order not yet shipped. With neither, it says so rather than guess.
- **An email hand-off:** scan the last 72 hours, match the subject, identify the account, save the attachment, run the check, with duplicates blocked three ways.

## What it caught

- **Summing stock buckets overstated availability.** On one item our balance at the ship deadline read +5,057 against the ERP's −4,967; the 10,024-unit difference was reserved and restricted stock. The extract still sums those buckets, so the gap is flagged, not yet fixed.
- **Forecast in the denominator caused false alarms.** One item held 3,805 units with a confirmed low point of 2,332, but adding forecast demand pushed it to −744. Against a 396-unit order the honest pair was coverage no, allocation full.
- **All four test items matched a planner's own ERP reading** once forecast was deducted back out. One flipped from apparently short to fully allocatable; three stayed at zero.
- **Two silent defects,** found by tying back to the ERP screen: a date column compared as text returned zero rows for a whole check, and a planning filter stored as a number never matched the text beside it.

## Limitations

- Our copy of the data lags the ERP by about an hour. On one item we computed 1,116 units allocatable, 82% of the order, against the ERP's 288, or 21%. Reports carry a snapshot timestamp and critical items get confirmed live.
- Parsing covers flat tables; a header mid-sheet still needs a person.
- Ship deadlines are confirmed for two accounts, and each new one has to be asked about.
- The mail step needs the desktop client open, and it is Windows only.
