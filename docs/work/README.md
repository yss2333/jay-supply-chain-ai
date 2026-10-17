# Work

Everything I have built and run as a demand planner at a CPG beauty manufacturer: 20+ retail accounts across the US, Canada and Europe, about 1,400 nail SKUs, five plants.

Each page leads with the outcome, says what I did as opposed to what the team did, and states the definition and window behind every number. Where a number is modeled or estimated rather than measured, it says so. **★ = start with these four.**

Accounts are named where the work being described is my own planning, and left as a type where the number belongs to the customer. Raw order and sales data, customer contract terms, system credentials and internal identifiers stay out.

## Forecasting, and the system that runs it

| | What it is | Result |
|---|---|---|
| ★ | [The forecasting system](forecasting-system.md) | Weighted forecast error 35–45% → 18–25% in backtests; review 5h → 2h per account; three regions on a weekly cadence; planning-related backorders down 36% since it went live |
| ★ | [What the weekly job became](exception-based-planning.md) | Every item still reviewed — by rules; a planner takes what the rules could not settle. Monthly cadence → weekly |
| ★ | [Handing the system to teams that are not mine](handover-to-other-teams.md) | Four product divisions: 15+ people in their purchasing and supply chain teams, weekly, configured by them, not run by me |
| | [Forecasting new products before they sell](new-product-introduction.md) | The cross-retailer forecast that supported a pitch securing a second national retailer; NPI forecasting for 178 new items across 380+ launches; launch-window rules that stop early cuts |
| | [Rebuilding the review rules](fc-review-overhaul.md) | A certainty gate on cuts, a floor at the selling rate and tiered ceilings; six accounts re-validated |
| | [Fix the data before you judge the item](data-integrity-review.md) | Three data defects; demand estimates went from 0.21 to 0.91 of actual; 79 items' decisions changed |
| | [Measuring forecast accuracy at all](forecast-accuracy-measurement.md) | The monthly exception report that scores every item's shipments against its forecast |
| | [From R to Python to a forecast engine](forecast-automation-engine.md) | The seasonality index and automation that replaced a paid platform's statistics |

## Customers, orders and service level

| | What it is | Result |
|---|---|---|
| | [How much of a customer's plan to trust](supply-plan-vs-orders.md) | 20 weekly plan snapshots; the four-month plan beat the one-month plan, 8.7% vs 10.5% |
| | [Service level for a grocery wholesaler](wholesale-service-level.md) | Fill rate held near 96% for five straight quarters; the customer's own report agrees at 96.5%, with charge-backs at 0.03% of order value |
| ★ | [Allocation when supply is short](allocation.md) | On-time in-full 84% → 98% on a retailer's own scorecard, across 20+ accounts — by diagnosing each shortfall and completing orders in priority order instead of splitting stock thin |
| | [Forecast, orders and back-orders in one tracker](fc-order-backorder-tracker.md) | Retailer forecast against our forecast, orders and back-orders, per item |
| | [Back-orders at two retailers, caused by a third](shared-stock-pool.md) | A shared regional stock pool and an account with no forecast of its own |
| | [Order trend and in-stock dashboard](order-trend-dashboard.md) | 600K+ order lines from all 130 customers beside weekly store in-stock and point-of-sale in one self-serve model, refreshed daily; it anchors order-exception reviews with retailers. A forecast-variance report and per-retailer trend reports sit beside it |

## Inventory and working capital

| | What it is | Result |
|---|---|---|
| | [Excess and aging inventory, five plants](inventory-health-reporting.md) | A 3-year aging standard that did not exist before: 489 SKU-locations of aged excess stock surfaced for management review; excess and obsolete (E&O) reporting for six teams in four departments, by our estimate from about 6 hours to 30 minutes |
| | [Stock availability checks, automated](stock-check-automation.md) | 5+ requests a week from 15+ accounts, answered from shippable stock net of open orders and deliveries; a scheduled ERP extract that used to be a manual morning routine |

## Procurement and logistics

| | What it is | Result |
|---|---|---|
| | [Freight routing from days of coverage](shipping-route-automation.md) | The routing our supplier ships to, decided by stockout date against each lane's lead time; air lands on 0.6% of the lines it clears for a cheap lane, 29% of those it flags at risk |
| | [Dashboards for vendors, retailers and the warehouse](dashboards.md) | Supplier coverage matched to the ERP exactly; 400 items down to the 319 that needed an answer |

## Data platform and reporting

| | What it is | Result |
|---|---|---|
| | [From SAP to Snowflake](data-platform.md) | Four years of orders across five markets in one model, about 1.6M lines: assembled by hand monthly before, refreshed weekly now |

## Earlier work

[Boeing case competition, stock price forecasting and labor market research, 2022–2023](../archive/2023/README.md) — the statistics degree, and the parts of it I still use.

## Runnable

[A clean-room version of the system](https://github.com/yss2333/Jay-supply-chain-ai-portfolio/tree/main/system) on synthetic data: the rule engine, the review agents, six Jupyter notebooks and 31 tests. The rules described on these pages are its unit tests.
