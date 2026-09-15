# G10 real-world research audit: censored demand

Status: audit before redesign. No build, no model run. It supersedes the reconstruction-heavy parts of
`research/gen3_designs/G10_censored_demand.md`. Tournament criticism of G10 (`research/gen3_design_tournament.md`
§3 #3, §4) is binding:
- the profile-scaling reference estimator is stopping-time biased;
- there are too many mechanisms;
- the tolerance is unproven;
- the contract wording was too technical;
- the shrink description contradicted itself.

Literature references are marked *(to verify)*. The design relies on none of them for correctness: every claim used
by the task is checked by simulation in `research/g10/pilot/`.

## 1. What real job does this simulate?

A demand-planning / applied-science review for a grocery retailer. It asks: "Did customer demand fall, or did we stop
serving it?" This comes after a working-capital programme cut store inventory and a new forecast went live.

The analyst must produce three things:
- an unconstrained demand history, which planning retrains on;
- baseline demand trends by category, which drive the next quarter's buy plan and range reviews;
- the forecast bias of the models against demand, not sales.

These are standard deliverables for a retail demand-science team. "Unconstrained demand" is the term planning
systems use for demand before availability limits it.

## 2. Who would solve this in a real company?

- **Primary:** a senior demand scientist / applied scientist on the forecasting or supply-chain analytics team.
- **Stakeholders:** category managers, supply planning, store operations and finance (working capital).
- **Tools:** SQL on the sales / availability warehouse, Python (pandas, statsmodels / scipy), notebooks, and the
  replenishment system's logs.

## 3. What decision depends on the output?

1. **Buy plan and range review for next quarter.** Planning proposes cutting category buys, and delisting slow
   SKUs, in categories whose sales fell. Cutting buys where demand has not fallen deepens stockouts: less stock, more
   censoring, lower sales, lower forecast. This is the classic censored-demand spiral.
2. **LEAN-26 continuation.** Finance wants the inventory programme rolled out to the 4 holdout stores. The lost-sales
   estimate is the cost side of that decision.
3. **Forecast model governance.** v4 went live with LEAN-26. Is it biased against demand?

## 4. Why observed sales differ from latent demand

Sales record units sold while the item was on the shelf. When on-hand reaches zero, later shoppers who wanted the
item cannot buy it:
- no transaction is recorded;
- in this setting they do not wait or come back the same day.

Sales are therefore demand truncated at available inventory, observed only during in-stock time. Retail
out-of-stock studies commonly report lost sales from stockouts as a material share of demand in grocery *(to
verify)*.

## 5. What creates censoring

- **Inventory after delivery** is set by an order-up-to rule driven by the day's forecast: `target = ceil(m × F)`,
  capped by shelf capacity.
- **Delivery slots:**
  - morning-slot stores are replenished before opening, so stockouts run to close;
  - afternoon-slot stores open on yesterday's leftovers and are replenished at 14:00, so they have morning stockout
    windows and fragmented in-stock intervals.
- **LEAN-26** cut `m` in 12 of 16 stores, raising the stockout rate.
- **v4 forecasts** are trained on sales, so they under-forecast items that were often censored. Inventory set from
  them runs out sooner. This is a feedback loop.

## 6. Is censoring independent or informative?

**Informative.** Stockout happens when realised arrivals exceed inventory:
- days with a high latent demand shock stock out earlier and more often;
- promotional and weekend days, where the forecast under-reacts, stock out more.

Consequences:
- dropping stockout days selects low-demand days;
- the average non-stockout rate understates demand on stockout days;
- per-day "sales ÷ in-stock share" is a ratio stopped at a random time (the stockout), and is biased upward;
- a Poisson exposure model ignores that exposure is shorter precisely on high-intensity days, and is biased
  downward when day-level demand is overdispersed.

Censoring is **ignorable for likelihood inference** under two conditions:
1. the stopping rule (sell-out of a known inventory) depends only on observed history;
2. inventory is predetermined given observed covariates.

The likelihood of the observed arrival path up to a stopping time is the same as with a fixed horizon. So a correctly
specified likelihood (Poisson process mixed over the day-level shock) with the realised exposure is valid, while the
moment-based shortcuts above are not.

## 7. Assumptions that make the target estimable

| # | Assumption | Supplied by evidence? |
|---|---|---|
| A1 | Within a store-SKU-day, shoppers wanting the item arrive as a Poisson process with intensity λ_d · g(t). g is the store's intraday shape (weekday / weekend), independent of the day's level. | Hourly sales on fully in-stock days, and in holdout stores, show a stable shape by day type. Traffic doc describes day-type shapes. |
| A2 | `λ_d = μ(x_d) · ε_d`: covariates x (store, SKU, weekday, promotion, week) times an i.i.d. day-level shock ε with mean 1, independent of x and of that day's inventory. | Overdispersion is visible on uncensored days; the replenishment doc shows orders use only the forecast and on-hand. |
| A3 | Stockout and restock instants are recorded exactly; every arrival during in-stock time is a sale of one unit; no phantom stock. | Availability log doc (perpetual inventory, daily count reconciliation); sales lines are single units. |
| A4 | Shoppers arriving during a stockout are lost for that day: no same-day return, no substitution into the item. | Store ops / loyalty study note ("no measurable same-day return"). |
| A5 | Trading hours define exposure; closed hours and closed days are not demand. | Store calendar. |

Under A1–A5:
- `μ(x)`, the mixing distribution of ε, and `E[D_d | observed data]` are identified.
- Aggregates of expected demand, baseline trends and forecast bias against demand are estimable.
- **Not identified:** the realised number of lost shoppers on a particular censored day. Only its conditional
  expectation is. The task grades aggregates, not per-day realised counts.

## 8. Operational artifacts a real scientist would have

- sales lines (or hourly buckets) by store × SKU;
- the availability / out-of-stock log from perpetual inventory;
- deliveries and order-up-to targets;
- daily open/close on-hand;
- forecasts by model;
- promo calendar;
- store master (delivery slot, trading hours, calendar exceptions);
- programme assignment (LEAN-26 vs holdout);
- category / SKU master;
- replenishment policy docs;
- model card;
- programme memo;
- previous category reviews and availability KPI reports;
- analyst notebooks.

All appear in the redesign. None is filler.

## 9. Candidate methods: used or plausible

| Method | Used in practice? | Valid here? |
|---|---|---|
| Sales as demand | common default | no |
| Drop / flag stockout days | common "cleaning" | no (selection on outcome) |
| Scale sales by in-stock share of day (time or traffic-weighted) | common quick fix *(to verify)* | no per day (stopping-time bias); traffic weighting needed |
| Impute lost sales at the average non-stockout rate | common | no (informative censoring) |
| Poisson GLM with log-exposure offset | textbook | no under overdispersion + informative exposure |
| Censored (Tobit-style) daily Poisson | textbook | no under overdispersion |
| Censored negative binomial / Gamma–Poisson with exposure | used in lost-sales work *(to verify)* | **yes** |
| EM over latent lost arrivals (Gamma–Poisson posterior) | used *(to verify)* | **yes** |
| Kaplan–Meier / product-limit estimators of the demand distribution | used in censored inventory literature *(to verify)* | valid for a stationary demand distribution per series; weak with covariates. Allowed if it passes. |
| Use uncensored holdout/test stores to calibrate | strong practice (availability experiments) | **validation**; transfer alone is biased by store effects |
| Forecast as imputation | common | no (circular: forecast trained on censored sales drives inventory) |

## 10. Artificial complications removed vs natural ones kept

**Removed** (they served the reconstruction puzzle or existed mainly to trip an agent):
- posted vs effective event log and cycle-count correction chains (G08 already tests event-time reconstruction);
- POS gateway outages;
- multiple timezones and DST;
- the substitution study and sibling inflation (would make the own-demand estimand fragile);
- phantom stock;
- the "close on-hand = 0" flag attractor based on a snapshot-timing trick.

**Kept** (each arises from the data-generating process and changes the inference):
- intraday traffic shape (weekday / weekend);
- delivery slots giving fragmented in-stock intervals;
- forecast-driven order-up-to inventory, i.e. informative censoring and feedback;
- promotions (intensity and promo-mix change);
- day-level overdispersion;
- a genuine seasonal decline in some categories and a competitor opening near some stores, i.e. true demand change;
- the randomized LEAN-26 holdout stores, which give nearly uncensored validation data and a negative control;
- holiday trading hours and a closure day, i.e. exposure.
