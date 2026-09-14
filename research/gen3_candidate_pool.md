# Generation 3: raw candidate pool (30 incidents)

Date: 2026-09-14. Status: research only. Nothing here is built, and no model has been run.

## Why generation 3 exists

Five of six built tasks were passed by Gemini 3 Flash (03, 05 and 06 went 3/3; 01 went 2/3; 04 went 1/3). Only Task 02
went 0/3. In the tasks that were passed, the natural implementation after recognising the failure class was also the
correct one.

Generation 3 therefore looks for incidents with three properties:

- **Principled wrong paths.** The most obvious repair is wrong for a principled data-science reason.
- **Reconstructed semantics.** The correct rule has to be pieced together from several sources and from the data.
- **Grain-level validation.** Validating at the level of rows or reconstructed state is required.

**Grading note.** Several candidates propose grading against generator ground truth with a tolerance, instead of one
reference estimator. The deterministic world knows the true effect, true demand or true relevance, so any statistically
valid method passes and naive methods fail. Those candidates are flagged below.

## Field legend

| Field | Meaning |
|---|---|
| **Sym** | visible symptom |
| **Truth** | hidden causal structure |
| **Wrong path** | why a strong model goes wrong |
| **Hyp** | plausible hypotheses (★ = supported by some real evidence) |
| **DS** | required data-science reasoning |
| **Grains** | key grains and states |
| **Repair** | likely repair breadth |
| **Horizon** | what makes it long-horizon |
| **Natural wrong impl** | the likely first implementation, which is wrong |
| **Verifier** | feasibility of deterministic grading |
| **vs 02** | expected hardness relative to Task 02 |
| **Overlap** | overlap with Tasks 01–06 |

---

### G01: Collections model "degradation" under label maturity, policy change and an acquired book
- **DS domain:** ML evaluation, censoring. **Setting:** consumer lender collections. A propensity-to-pay model scores delinquent accounts. Evaluation is a monthly Python job over a warehouse, with dashboards.
- **Sym:** 30-day "cure" AUC and calibration fell sharply over two quarters; Risk wants to retire the model.
- **Truth:**
  - Cure labels mature over 90 days, and early payers mature first. The eval uses "complete cases available at run date", so recent cohorts over-represent fast curers.
  - A March policy change started calling high-score accounts on day 3 instead of day 10, which raises cure among treated high scores.
  - An acquired portfolio's payment feed lands with a 45-day lag, so its accounts look uncured.
  - The model itself is stable within comparable, fully matured, untreated-comparable cohorts.
- **Wrong path:** "fix the window" to a fixed 30-day cure on all accounts. That still mixes immature acquired-book accounts and policy-treated cohorts. An agent could also just filter out the acquired book.
- **Hyp:** real drift★ (feature PSI moved); label delay★; policy effect★; data bug in the acquired book.
- **DS:** vintage and maturity analysis; informative missingness; separating treatment effects from model quality; per-source label latency.
- **Grains:** account × delinquency episode × vintage month; call-attempt timeline; payment posting vs value date; source portfolio.
- **Repair:** label builder (posting vs value date, per-source latency), cohort maturity rule, evaluation stratification and report.
- **Horizon:** reproduce; per-vintage curves; per-source lag discovery; policy timeline; rebuild labels; re-evaluate history.
- **Natural wrong impl:** a global maturity filter (`as_of - 30d`) on *posting* date.
- **Verifier:** high. Deterministic rebuilt label table and vintage metrics, plus hidden books with other lags.
- **vs 02:** comparable to harder. **Overlap:** Task 03 (policy selection), Task 02 (availability dates). Moderate.

### G02: Better AUC, worse loss ratio (sampling weights and prior shift)
- **DS domain:** calibration. **Setting:** a small-commercial insurer's claim-probability model feeds pricing. Training uses negative downsampling.
- **Sym:** v7 has higher AUC than v6 on the validation report, but live loss ratio worsened after v7 pricing went live. Actuarial says premiums are too low for two segments.
- **Truth:**
  - Training and validation extracts downsample non-claims at a rate that changed between data refreshes (10% → 25%). The rate is logged per extract batch.
  - Calibration was fit on the downsampled validation set with a single correction factor, the old 10%.
  - Exposure (policy-days) differs by segment, and the pricing target is claims per exposure-year. The eval counts policies.
  - AUC is unaffected by these errors; expected claims are mis-scaled per batch and segment.
- **Wrong path:** re-run Platt or isotonic calibration on the validation extract. That leaves it miscalibrated relative to the population, and an agent may trust "calibration curve looks diagonal".
- **Hyp:** v7 genuinely worse★ (segment AUC dips); pricing-engine bug★ (a rounding change in release notes); mix shift★; sampling-weight error.
- **DS:** prior-shift correction with batch-varying weights; exposure-weighted calibration; calibration vs discrimination.
- **Grains:** policy × exposure period; extract batch; segment; model version.
- **Repair:** weighting in validation, calibration refit on weighted data, exposure-based expected-loss report, pricing input export.
- **Horizon:** reconcile validation vs live, discover batch sampling metadata, compute exposure, recalibrate, re-evaluate by segment.
- **Natural wrong impl:** recalibrate on the (downsampled) validation set, or apply one global prior correction.
- **Verifier:** high. Weighted calibration table and expected loss ratio vs generator truth; hidden batches with other rates.
- **vs 02:** comparable. **Overlap:** low.

### G03: Leaky evaluation through linked entities and re-opened claims
- **DS domain:** ML evaluation. **Setting:** auto-insurance fraud triage. The model predicts SIU referral outcome per claim.
- **Sym:** a new model has holdout PR-AUC 0.61 vs 0.34, but investigators see no improvement in the live queue.
- **Truth:**
  - Random claim-level splits leak across *households*. Linked parties share addresses, phones and vehicles, and fraud rings recur.
  - Re-opened claims are duplicated as new claim ids carrying the original outcome.
  - Label "confirmed fraud" is back-filled up to 9 months later, and the snapshot used includes future confirmations.
- **Wrong path:** `GroupKFold` by `claim_id` or policy id. That leaks through households and rings; the rings only emerge from entity linking.
- **Hyp:** live queue ops issue★ (investigator capacity changed); model overfit; label definition change★; leakage.
- **DS:** grouped temporal validation; entity linking for split construction; label-as-of reconstruction.
- **Grains:** claim, claim lineage (re-open chain), party, household or ring cluster, label as-of date.
- **Repair:** entity-link table, re-open lineage dedupe, time-and-group split, as-of labels, re-evaluation.
- **Horizon:** find leakage signals, build linkage graph, build lineage, rebuild split, evaluate.
- **Natural wrong impl:** group by claim or policy; time split without lineage and household grouping.
- **Verifier:** medium-high. Split-assignment invariants (no group or time leakage) plus metrics vs reference within tolerance.
- **vs 02:** comparable. **Overlap:** Task 01 (identity), Task 02 (as-of labels). Moderate.

### G04: Switchback pricing test with carryover
- **DS domain:** experimentation. **Setting:** grocery-delivery marketplace. A dynamic delivery fee is tested by region × 2-hour switchback.
- **Sym:** the order-level analysis shows +4.1% revenue, significant. Ops says courier backlogs worsened in control windows.
- **Truth:**
  - Treatment windows pull demand forward and leave courier backlog that spills into the following window, which is usually control.
  - Orders are attributed by *delivery* time in the analysis table but should use *placement* time.
  - Independence at order level is false; the design unit is region × window.
  - The design doc specifies burn-in windows only as a business fact ("courier state carries over ~1 window").
- **Wrong path:** cluster SE by region-day, or analyse at window level but keep delivery-time attribution and no carryover handling.
- **Hyp:** true revenue lift★; ops noise; logging bug in fee exposure★; carryover.
- **DS:** switchback design, interference and carryover, unit of analysis, attribution timestamp.
- **Grains:** order, region × window (assignment), courier-state timeline.
- **Repair:** order-to-window attribution, window-level metrics with carryover exclusion, estimator and report.
- **Horizon:** moderate.
- **Natural wrong impl:** window-level analysis on delivery-time attribution.
- **Verifier:** medium. Effect vs simulated truth with tolerance, and window table.
- **vs 02:** slightly easier. **Overlap:** Task 05 (unit mismatch). Moderate-high.

### G05: Staggered store rollout, two-way fixed effects flips the sign
- **DS domain:** causal inference. **Setting:** retail chain. A self-checkout redesign was rolled out to stores in 5 waves; a basket-size KPI is analysed in a notebook plus SQL.
- **Sym:** the analyst's panel regression says −2.3% basket size, and the COO wants rollback. Store managers report bigger baskets.
- **Truth:**
  - Effects grow over time since adoption and differ by wave.
  - TWFE uses already-treated stores as controls, which flips the sign.
  - Wave 3 coincided with a regional competitor closure (real confounder for its region only).
  - The panel has store remodel closures (partial weeks) that must be dropped per the KPI definition.
- **Wrong path:** add wave fixed effects or event-time dummies in TWFE, which is still contaminated. An agent might also drop wave 3 entirely.
- **Hyp:** redesign hurts★ (TWFE); seasonality★; competitor closure★; KPI bug with partial weeks.
- **DS:** heterogeneous and dynamic treatment effects, clean comparisons (not-yet-treated), local confounder handling, KPI panel hygiene.
- **Grains:** store × week; adoption cohort; region; partial-week flags.
- **Repair:** panel construction, estimator, aggregation, report.
- **Horizon:** reproduce, event-study plots, discover sign flip, rebuild panel, estimate, sensitivity.
- **Natural wrong impl:** TWFE with event-time leads and lags.
- **Verifier:** high using ground truth. Overall ATT and cohort ATTs within tolerance of simulated truth, plus a direction decision.
- **vs 02:** comparable, and statistical rather than grain-based. **Overlap:** low.

### G06: Holdout contamination by account merges
- **DS domain:** experimentation and identity. **Setting:** a B2C app runs long-term marketing holdouts per user. Accounts can merge (family plans, device linking).
- **Sym:** the email-program holdout shows the program has no effect. Marketing insists it works.
- **Truth:** merges move holdout users into treated accounts, and analysis uses the current merged account's assignment.
- **Wrong path:** analyse by the original user id but outcome at the merged account.
- **Hyp:** program ineffective★; holdout leaked★; outcome definition.
- **DS:** ITT at the pre-merge assignment unit, contamination handling.
- **Grains:** user, account, merge events, assignment.
- **Repair:** assignment-snapshot table and outcome attribution.
- **Horizon:** moderate.
- **Natural wrong impl:** use the current account id.
- **Verifier:** high. **vs 02:** easier. **Overlap:** Task 05 (identity, exposure) high.

### G07: Hierarchical forecast after a SKU re-hierarchy
- **DS domain:** hierarchical forecasting. **Setting:** a CPG supply planner forecasts national → category → store-SKU.
- **Sym:** national MAPE improved after v4; store replenishment errors and stockouts rose.
- **Truth:**
  - Disaggregation proportions were computed over a window spanning a category re-map (SKUs moved) and a promo period.
  - Bottom-level forecasts are incoherent with the top.
  - New SKUs have no history.
- **Wrong path:** re-run top-down with longer history, or a proportion refresh ignoring effective-dated mapping.
- **Hyp:** v4 worse at low levels★; promo calendar error★; re-map.
- **DS:** hierarchy with effective dating, reconciliation, promotion adjustment.
- **Grains:** SKU × store × week; hierarchy version.
- **Repair:** mapping, proportions, reconciliation.
- **Horizon:** moderate-long.
- **Natural wrong impl:** proportions over the last 52 weeks under the current hierarchy.
- **Verifier:** medium. The reconciliation method is underspecified.
- **vs 02:** comparable. **Overlap:** low.

### G08: Forecast backtest on revised actuals (real-time vintages)
- **DS domain:** forecasting evaluation. **Setting:** a utility forecasts daily regional electricity load and billing volume. Meter reads are estimated first and revised later, and some regions re-read 30–60 days late.
- **Sym:** the new gradient-boosted model beats production by 18% in the backtest. After launch, live accuracy is no better and sometimes worse.
- **Truth:**
  - The backtest trains and features on *revised* history (final vintages) at every origin.
  - It scores against final actuals, while production forecasts were made on preliminary vintages.
  - Lag features are therefore cleaner than anything available live.
  - One region switched from estimated to smart-meter reads mid-year, changing revision magnitude.
  - The KPI definition for forecast accuracy uses *first settled* actuals (billing settlement), not final.
- **Wrong path:** fix the lag features to use the as-of date. That still uses revised values within the history, because the vintage table must be used, and it still scores against final instead of first-settled actuals.
- **Hyp:** live model degraded★; weather-feed issue★ (vendor switch); overfitting; vintage leakage.
- **DS:** real-time data vintages, as-of feature reconstruction, correct evaluation target, regime change in revision process.
- **Grains:** region × date × vintage; forecast origin; settlement run.
- **Repair:** vintage-aware feature builder, backtest harness, scoring target, report.
- **Horizon:** reproduce live vs backtest gap, discover vintage table, per-region revision analysis, rebuild features and backtest.
- **Natural wrong impl:** as-of on date columns (no vintages), score vs final.
- **Verifier:** high. Backtest predictions from a fixed model spec, deterministic features and metrics; hidden fixtures with other revision patterns.
- **vs 02:** comparable to harder (Task 02-like availability plus a scoring-target subtlety). **Overlap:** Task 02 (availability). Moderate.

### G09: Anomaly storm after daylight saving
- **DS domain:** anomaly detection. **Setting:** a payments ops monitor produces hourly volume anomaly alerts per merchant × region.
- **Sym:** hundreds of alerts every DST switch, and a real outage alert was missed in the noise.
- **Truth:** seasonality baselines are built in UTC hours while behaviour follows local time; regions switch DST on different dates; the baseline window includes the outage.
- **Wrong path:** convert everything to one timezone, or suppress alerts on DST days.
- **Hyp:** real volume shifts★; detector threshold regression★; DST.
- **DS:** local-time seasonality, robust baselines, contamination.
- **Grains:** merchant × local hour; region DST calendar.
- **Repair:** baseline builder and scoring.
- **Horizon:** moderate.
- **Natural wrong impl:** a UTC offset shift.
- **Verifier:** medium-high. **vs 02:** easier. **Overlap:** Task 06 (time semantics) low-moderate.

### G10: Censored demand: stockouts masquerade as low demand
- **DS domain:** forecasting and missing data. **Setting:** a grocery chain's store-SKU daily forecasts drive replenishment.
- **Sym:** a new model reduces MAPE on sales, but fill rate fell and store managers report empty shelves on promoted items.
- **Truth:**
  - Sales during stockouts are censored; on-hand is 0 at some hour, and partial-day stockouts are recorded in an inventory events log.
  - The new model trains on sales and scores MAPE on sales, which rewards predicting stockout-suppressed values.
  - Substitution inflates sibling SKU sales during stockouts.
  - A POS outage day recorded zero sales with no stockout.
- **Wrong path:**
  - Drop all zero-sales days, which removes real zero demand for slow movers.
  - Impute stockout days with trailing averages, which ignores promo lift.
  - Treat the POS outage as a stockout.
- **Hyp:** new model biased★; replenishment parameter change★ (safety stock config release); stockouts; POS outage.
- **DS:** censoring in demand, informative missingness, substitution, evaluation target (unconstrained demand), outage vs stockout.
- **Grains:** store × SKU × day; intraday inventory events; promo calendar; substitute groups.
- **Repair:** censoring flags from inventory events, training target and weights, evaluation on uncensored periods, substitution adjustment in eval, report.
- **Horizon:** long.
- **Natural wrong impl:** treat sales = 0 and on-hand = 0 at close as stockout, exclude those days.
- **Verifier:** high using ground truth. Demand is known in the generator. Grade the censoring flags table exactly, and grade the re-evaluation metrics and model choice vs truth.
- **vs 02:** harder. **Overlap:** low.

### G11: Training-serving skew across several features
- **DS domain:** production ML and feature store. **Setting:** a food-delivery ETA/ranking model. The offline training table is built from a warehouse; serving reads an online feature store and logs served feature vectors for 1% of requests.
- **Sym:** offline NDCG and MAE improved in the retrain, but online ETA error rose 9% after deploy.
- **Truth:** several features differ for different reasons.
  - (a) `restaurant_prep_p50` refreshes online every 6 h; offline computes it at request time.
  - (b) Courier-id mapping version differs; offline uses the latest identity map, serving the map at request time.
  - (c) Offline history includes corrected order timestamps (ops corrections back-filled); serving saw originals.
  - (d) Online missing defaults are −1, offline is NaN, and the tree model splits differently.
  - (e) One feature is genuinely fine and looks suspicious because of distribution shift.
- **Wrong path:** drop the most skewed feature and retrain, or retrain only on the 1% logged vectors (too small, and other skews remain for the unlogged 99%).
- **Hyp:** model overfit★; traffic mix shift★; feature skew; logging bug.
- **DS:** feature-by-feature parity analysis against serving logs, as-of snapshots with refresh cadence, identity map versioning, default semantics.
- **Grains:** request × feature × serving snapshot; restaurant × 6 h refresh; courier id × map version; order × correction version.
- **Repair:** training-table builder per feature family, default handling, parity report.
- **Horizon:** long. Several independent mechanisms have to be discovered one by one.
- **Natural wrong impl:** point-in-time join on event time for all features, which fixes (c) partially and leaves (a), (b) and (d).
- **Verifier:** high. Rebuilt training rows must match served vectors on the logged sample and a hidden logged sample, plus hidden extracts with other cadences.
- **vs 02:** harder (multi-mechanism). **Overlap:** Task 02 (point-in-time) moderate.

### G12: Retrieval quality drop from an embedding version mismatch
- **DS domain:** production ML. **Setting:** semantic search. The item index is built with embedding v2; a canary routes 30% of queries to v3.
- **Sym:** online recall@10 fell for some traffic; offline eval shows no change.
- **Truth:** canary queries embed with v3 against the v2 index; offline eval uses v2 for both; new items were missing from a stale ANN shard.
- **Wrong path:** rebuild the index with v3 for all, which breaks non-canary traffic.
- **Hyp:** model worse★; index staleness★; version mismatch.
- **DS:** versioned embedding compatibility, segmented evaluation.
- **Grains:** query × model version × index shard.
- **Repair:** routing and eval.
- **Horizon:** moderate.
- **Natural wrong impl:** full reindex.
- **Verifier:** medium (synthetic vectors). **vs 02:** easier. **Overlap:** low.

### G13: Model monitoring blind spot: refit bins and delayed labels
- **DS domain:** model monitoring. **Setting:** credit-line model monitoring job (PSI plus performance).
- **Sym:** the drift dashboard is green all quarter while approvals quietly shifted.
- **Truth:** PSI bins are re-fit on current data each month (PSI ≈ 0 by construction); performance uses immature labels.
- **Wrong path:** raise the PSI threshold, or switch to KS on current bins.
- **Hyp:** no drift★; threshold too loose; binning.
- **DS:** reference-frozen binning, label maturity.
- **Grains:** score bins × month.
- **Repair:** monitoring job.
- **Horizon:** short-moderate.
- **Natural wrong impl:** threshold change.
- **Verifier:** high. **vs 02:** easier. **Overlap:** Task 03 (monitoring) low-moderate.

### G14: Marketplace refunds, promo funding and seller economics
- **DS domain:** financial analytics and allocation. **Setting:** a multi-seller marketplace. Orders contain items from several sellers, with platform-funded and seller-funded promotions, a capped platform fee, and partial refunds.
- **Sym:** seller take-rate report shows 3 large sellers with negative net payout margin; seller success is escalating. The platform P&L ties to the ledger exactly.
- **Truth:**
  - Order-level refunds and order-level coupons are allocated to items by item price.
  - Contract and ledger facts require allocating by *post-discount* item value.
  - Platform-funded coupons must not reduce seller revenue.
  - Fee refunds follow the fee cap (capped fees are not refunded pro rata).
  - Refunds reference the *original* order line; re-shipments create new lines.
- **Wrong path:** re-allocate refunds by quantity or by item price after excluding shipping. Totals still tie in every variant.
- **Hyp:** real margin problem★ (those sellers run many promos); fee config error★ (release note); allocation.
- **DS:** allocation semantics with caps and funding source, line lineage, reconciling to seller payout statements.
- **Grains:** order, order line, refund line, promotion, seller × month.
- **Repair:** allocation module, fee-refund logic, report.
- **Horizon:** moderate-long.
- **Natural wrong impl:** pro-rata by item price after discount but including platform-funded coupons.
- **Verifier:** high. Exact seller × month statements; hidden extracts with other promo mixes.
- **vs 02:** comparable. **Overlap:** Task 01 (reconciliation) moderate; Task 07 design (allocation) moderate.

### G15: Cohort LTV with FX, late refunds and reactivation
- **DS domain:** financial analytics. **Setting:** global subscription app LTV curves by acquisition cohort.
- **Sym:** LTV for recent EU cohorts dropped 12%.
- **Truth:** conversion at month-end FX instead of transaction date; refunds booked in later months against the refund month; reactivated users counted as new cohorts.
- **Wrong path:** re-convert at the average monthly rate.
- **Hyp:** EU monetisation drop★; FX★; cohort definition.
- **DS:** cohort construction, currency conversion, refund attribution.
- **Grains:** user × transaction × currency; cohort month.
- **Repair:** revenue fact and cohort.
- **Horizon:** moderate.
- **Natural wrong impl:** monthly average FX.
- **Verifier:** high. **vs 02:** easier. **Overlap:** Task 04 (reactivation, cohorts) high.

### G16: Payment processing cost allocation with retro network adjustments
- **DS domain:** economic allocation. **Setting:** a PSP allocates interchange and scheme fees to merchants on blended pricing.
- **Sym:** merchant margin report negative for travel merchants.
- **Truth:** scheme fees billed monthly in arrears with retroactive adjustments; the allocation uses billing month and transaction counts instead of transaction month and fee drivers.
- **Wrong path:** allocate by volume in transaction month and ignore adjustment references.
- **Hyp:** travel merchants unprofitable★; pricing config★; allocation timing.
- **DS:** fee driver allocation, retro adjustments.
- **Grains:** transaction, fee invoice line, merchant × month.
- **Repair:** allocation.
- **Horizon:** moderate.
- **Natural wrong impl:** volume share.
- **Verifier:** high. **vs 02:** comparable-easier. **Overlap:** Task 06 (retro adjustments) and Task 14 (allocation) moderate.

### G17: B2B customer entity resolution through acquisitions and resellers
- **DS domain:** entity resolution and data quality. **Setting:** a SaaS company's customer-360 across CRM accounts, billing accounts, product workspaces and support orgs; feeds revenue concentration and churn.
- **Sym:** the board-pack top-20 customer concentration jumped from 31% to 44%; churn of "enterprise customers" looks zero.
- **Truth:**
  - The new resolver merges by email domain, so reseller and agency domains glue unrelated customers together.
  - Acquisitions are effective-dated: a subsidiary joins the parent after the deal close, not for its whole history.
  - Some workspaces are shared trials across companies.
  - Tax id exists for 70% of billing accounts, and billing account ownership transfers.
- **Wrong path:** merge by normalised company name plus domain; or un-merge resellers by a hard-coded list; or apply acquisitions retroactively.
- **Hyp:** real concentration from a big deal★ (a real large expansion exists); resolver bug★; acquisition events.
- **DS:** ER with conflicting keys, effective-dated hierarchy, precision/recall trade-offs checked against known links, downstream metric impact.
- **Grains:** CRM account, billing account, workspace, legal entity, parent hierarchy × effective date, customer × month.
- **Repair:** matching rules (blocking and keys), hierarchy with dates, concentration and churn metrics.
- **Horizon:** long.
- **Natural wrong impl:** domain-based merge minus a "free email" blocklist.
- **Verifier:** high. Exact cluster assignments per month from the generator plus downstream metrics; hidden extracts with other reseller patterns.
- **vs 02:** comparable. **Overlap:** Task 01 (identity) moderate.

### G18: Claims double counting through voids and replacements
- **DS domain:** data quality. **Setting:** healthcare payer analytics over claim frequency codes (original, replacement, void).
- **Sym:** PMPM cost spiked.
- **Truth:** replacements and voids counted as additional claims; provider NPI changes.
- **Wrong path:** dedupe on claim number.
- **Hyp:** utilisation increase★; pricing★; claim lineage.
- **DS:** claim lineage.
- **Grains:** claim version, member × month.
- **Repair:** lineage builder.
- **Horizon:** moderate.
- **Natural wrong impl:** latest by date.
- **Verifier:** high. **vs 02:** easier. **Overlap:** Task 06 (revisions and voids) high.

### G19: Trade-area analysis through changing geographic boundaries
- **DS domain:** geospatial analysis. **Setting:** retail real-estate analytics attributes sales and households to trade areas via ZIP → tract mappings.
- **Sym:** store penetration fell in 40 suburban stores.
- **Truth:** ZIP boundary splits and a geocoder upgrade; the mapping is not effective-dated; population denominators come from a different vintage.
- **Wrong path:** latest mapping for all history.
- **Hyp:** real decline★; geocoder★; boundary vintage.
- **DS:** spatial joins with vintages, denominator consistency.
- **Grains:** address point, ZIP vintage, tract, trade area.
- **Repair:** mapping and penetration.
- **Horizon:** moderate.
- **Natural wrong impl:** latest crosswalk.
- **Verifier:** medium (geometry libraries). **vs 02:** easier. **Overlap:** low.

### G20: Fleet telematics trip segmentation with firmware and clock drift
- **DS domain:** time-series segmentation and streaming. **Setting:** a logistics fleet computes trips, idle time and fuel efficiency from GPS/CAN pings; KPIs drive driver bonuses.
- **Sym:** fuel efficiency "improved" 14% for 300 trucks after firmware 5.2, and idle time halved. Finance suspects bonus overpayment.
- **Truth:**
  - Firmware 5.2 samples every 30 s when moving and every 5 min when idle (was a uniform 10 s).
  - The trip splitter uses a fixed 3-minute gap threshold, which splits idle periods into separate "trips" whose idle time is dropped.
  - Device clocks drift and are corrected at periodic sync events; the pipeline orders by receive time.
  - Odometer (CAN) is authoritative for distance; GPS path length is noisy at low sampling.
- **Wrong path:** lower or raise the gap threshold globally; order by device timestamp without drift correction; recompute distance from GPS.
- **Hyp:** real behaviour change★ (a fuel program launched); firmware★; data loss.
- **DS:** irregular sampling, state segmentation, clock correction, authoritative signal choice.
- **Grains:** ping, device × firmware version, sync event, trip, driver × week.
- **Repair:** ordering and clock correction, segmentation rule by sampling regime, distance source, KPI.
- **Horizon:** long.
- **Natural wrong impl:** threshold = 2 × max(sample interval) with receive-time ordering.
- **Verifier:** high. The generator knows true trips; grade trip table with a boundary tolerance plus KPIs.
- **vs 02:** comparable. **Overlap:** Task 06 (event vs receipt time) low-moderate.

### G21: Churn-save offer "works": censoring, targeting and reactivation
- **DS domain:** survival and causal inference. **Setting:** telecom or SaaS retention team with save offers at cancel intent; a 10% random holdout exists.
- **Sym:** a dashboard shows offer takers churn 60% less than non-takers; the team wants to expand the budget 3×.
- **Truth:**
  - Offers are targeted by a risk model, and takers self-select.
  - Recent customers are right-censored.
  - Contract lengths differ (annual customers cannot churn until renewal).
  - Some churners reactivate within 30 days, which the KPI definition says is not churn.
  - The observation window changed in the dashboard SQL.
  - The randomized holdout shows a small true effect concentrated in monthly plans.
- **Wrong path:**
  - Compare takers vs non-takers.
  - Use the holdout but with naive churn rates without censoring handling or contract-renewal risk sets.
  - Count reactivations as churn.
- **Hyp:** offer highly effective★; no effect★ (a naive holdout rate); effective only for monthly plans.
- **DS:** ITT vs per-protocol, survival with censoring, risk sets by contract renewal dates, churn definition.
- **Grains:** subscription × contract term; cancel-intent event; assignment; churn / reactivation spells.
- **Repair:** survival cohort builder, churn definition, estimator by arm and plan, report.
- **Horizon:** long.
- **Natural wrong impl:** holdout vs treated churn rate at 90 days on all customers.
- **Verifier:** high using ground truth. Survival difference at horizon by plan within tolerance, plus an exact churn-spell table.
- **vs 02:** harder (statistical). **Overlap:** Task 03/05 (holdout, ITT) moderate.

### G22: Survey satisfaction trend with nonresponse shift
- **DS domain:** missing data. **Setting:** B2B CSAT program; survey channel moved from email to in-app.
- **Sym:** CSAT jumped 9 points.
- **Truth:** in-app responders are active users; response is missing not at random.
- **Wrong path:** complete-case mean by month.
- **Hyp:** real improvement★; channel effect★; mix.
- **DS:** weighting with known population margins.
- **Grains:** account × survey wave.
- **Repair:** weighting.
- **Horizon:** moderate.
- **Natural wrong impl:** complete case.
- **Verifier:** medium. Weighting spec is underspecified. **vs 02:** easier. **Overlap:** low.

### G23: Readmission model labels built on encounters instead of episodes
- **DS domain:** ML evaluation, grain and competing risk. **Setting:** hospital network. A 30-day readmission risk model is evaluated quarterly from EHR encounter extracts spanning 6 hospitals.
- **Sym:** readmission rate and model AUC jumped after hospital #6 joined the network; clinical leaders doubt it.
- **Truth:**
  - Inter-hospital transfers create consecutive encounters that belong to one care episode; the label builder counts transfers as readmissions.
  - Hospital #6 transfers far more.
  - Planned readmissions (chemo cycles) are excluded by the clinical definition.
  - Deaths within 30 days are a competing outcome, not "no readmission".
  - Discharge timestamps from hospital #6 are local time without offset.
- **Wrong path:**
  - Merge encounters within 24 h at the same hospital only.
  - Drop hospital #6.
  - Exclude deaths entirely (changes the population rule).
- **Hyp:** population sicker★; model overfit to hospital #6★; label error; data feed timezone.
- **DS:** episode construction (grain), label definition with exclusions, competing risk handling, source timestamp semantics.
- **Grains:** encounter, episode, patient, index admission, 30-day window.
- **Repair:** episode builder, label builder, eval cohort, report.
- **Horizon:** long.
- **Natural wrong impl:** gap-based merge (< 24 h) ignoring transfer disposition codes and cross-facility timestamps.
- **Verifier:** high. Exact episode and label tables plus metrics.
- **vs 02:** comparable. **Overlap:** low.

### G24: Recommender feedback loop: offline win from exposure-biased logs
- **DS domain:** recommender systems and off-policy evaluation. **Setting:** a streaming service home-page recommender. Logs contain impressions with slot position and a propensity field from the production policy; 5% of sessions use a randomized exploration policy.
- **Sym:** the new model wins offline replay by +11% CTR@5; an online A/B shows −2%. The team blames the A/B infra.
- **Truth:**
  - Offline replay counts clicks only on items the old policy showed; the new model's top items were rarely shown, so they are unlabeled and treated as non-clicks or dropped.
  - Clicks depend strongly on position.
  - Logged propensities are for the *slate*, not the item-in-slot, and were clipped at 0.01 in a release.
  - Exploration sessions exist but page reloads duplicate impressions.
- **Wrong path:**
  - IPS with logged propensities as item propensities.
  - Clip and self-normalise naively.
  - Evaluate only on exploration traffic without position adjustment.
- **Hyp:** A/B infra bug★ (SRM warning exists); novelty effect★; offline evaluation bias.
- **DS:** off-policy evaluation, position bias, propensity semantics, impression dedupe, variance.
- **Grains:** session, slate, impression × position, reload group, policy.
- **Repair:** impression dedupe, exploration-based evaluation dataset, position-aware estimator, decision report.
- **Horizon:** long.
- **Natural wrong impl:** IPS on all traffic with logged propensities.
- **Verifier:** high using simulation truth. True CTR of each policy is known; grade estimates within tolerance plus the ship decision; hidden logs with other position curves and exploration rates.
- **vs 02:** harder (statistical). **Overlap:** Task 03 (selective labels) moderate.

### G25: Search ranking "regression" from judgment-pool bias
- **DS domain:** ranking evaluation. **Setting:** e-commerce search. Relevance judgments come from human raters on pooled results of previous rankers; offline NDCG gates releases.
- **Sym:** ranker B has lower NDCG@10 than production and is blocked, but the online A/B showed more purchases.
- **Truth:**
  - Unjudged documents count as irrelevant; B surfaces many new unjudged items.
  - Query normalisation changes merged query variants, so judgments are joined by the raw query string and lost.
  - Graded relevance scale changed from 3 to 5 points in one judging round.
- **Wrong path:** judge-then-drop unjudged (condensed lists) but keep the broken query join and mixed scales; or map the 5-point scale linearly.
- **Hyp:** B worse★ (NDCG); A/B novelty★; judgment bias.
- **DS:** IR evaluation with incomplete judgments, scale harmonisation, query canonicalisation.
- **Grains:** query (raw vs canonical), document, judgment round, ranked list.
- **Repair:** query join, scale mapping (documented by rater guidelines), evaluation method, gate report.
- **Horizon:** moderate-long.
- **Natural wrong impl:** condensed-list NDCG only.
- **Verifier:** high using truth relevance. Grade the ranking decision and per-query metrics vs an oracle within tolerance.
- **vs 02:** comparable. **Overlap:** low.

### G26: Negative control, twin incident: one real bug, one real mix shift
- **DS domain:** product analytics, negative control. **Setting:** a self-serve SaaS growth analytics repository with two escalations in the same week.
- **Sym:**
  - (1) Trial→paid conversion dropped from 14% to 10.6% after an attribution refactor.
  - (2) The activation metric dropped 6% the same week.
- **Truth:**
  - (1) is a real composition change: an app-store feature brought low-intent mobile trials, with within-segment rates stable. The refactor was correct (parity logs).
  - (2) is a real pipeline bug: a timezone change in the events loader drops the last hours of each day for APAC accounts.
- **Wrong path:**
  - "Fix" conversion by excluding mobile or re-weighting inside the metric.
  - Revert the refactor.
  - Blame the timezone change for both.
- **Hyp:** refactor broke conversion★; mix shift★; timezone bug★ (real for activation).
- **DS:** decomposition, parity proof, distinguishing real change from defect, targeted repair.
- **Grains:** trial × channel × week; event × local day.
- **Repair:** the activation loader only. Conversion code must be byte-identical in behaviour.
- **Horizon:** long.
- **Natural wrong impl:** fix both metrics.
- **Verifier:** high. Behavioural: activation fixed on hidden extracts; conversion outputs identical to reference on hidden extracts, including one with a genuine within-segment decline.
- **vs 02:** comparable (epistemic). **Overlap:** Task 09 design (replaced).

### G27: Negative control: fraud AUC drop is real drift, not skew
- **DS domain:** production ML, negative control. **Setting:** a card-fraud model with serving logs and a feature store; a feature-pipeline deploy happened the day the AUC dropped.
- **Sym:** AUC fell from 0.91 to 0.84 overnight; the team is sure the deploy caused skew and wants a rollback.
- **Truth:** serving/offline parity is exact (verifiable from logged vectors); a new fraud pattern (card-testing bursts on a merchant category) changed label composition.
- **Wrong path:** roll back the pipeline, or drop features.
- **Hyp:** deploy skew★; drift★; label feed issue.
- **DS:** parity verification, segment performance analysis.
- **Grains:** request × feature; merchant category × week.
- **Repair:** none to the pipeline, plus a parity and drift report (behavioural checks).
- **Horizon:** moderate.
- **Natural wrong impl:** rollback.
- **Verifier:** medium. The report grading needs care (see design). **vs 02:** easier. **Overlap:** low.

### G28: Multi-touch attribution double counting across devices
- **DS domain:** attribution. **Setting:** DTC marketing attribution with cross-device identity stitching.
- **Sym:** paid social ROAS doubled.
- **Truth:** identity stitching after conversion reassigns touches; view-through window is applied in UTC vs campaign timezone.
- **Wrong path:** a last-click fallback.
- **Hyp:** real performance★; stitching★; window.
- **DS:** identity-time, attribution windows.
- **Grains:** touch, device, person graph version, conversion.
- **Repair:** stitching snapshot, attribution.
- **Horizon:** moderate.
- **Natural wrong impl:** use the current graph.
- **Verifier:** high, but the attribution rule must be stated (leakage). **vs 02:** comparable-easier. **Overlap:** Task 01/05 (identity) moderate.

### G29: Inventory allocation optimizer uses the wrong decision quantity
- **DS domain:** decision analytics. **Setting:** a fashion retailer allocates stock to stores via a newsvendor rule.
- **Sym:** markdowns rose and stockouts rose simultaneously.
- **Truth:** the optimizer uses the forecast mean instead of the critical-ratio quantile; the critical ratio uses price instead of margin and salvage; lead time is in weeks in one source and days in another; returns are counted as demand.
- **Wrong path:** raise safety stock.
- **Hyp:** forecast worse★; supplier delays★; decision rule.
- **DS:** newsvendor, quantiles, cost parameters.
- **Grains:** store × SKU × week.
- **Repair:** decision module.
- **Horizon:** moderate.
- **Natural wrong impl:** use the P90 quantile everywhere.
- **Verifier:** high (expected cost vs truth). **vs 02:** comparable-easier. **Overlap:** low.

### G30: Delayed-label fraud model: chargebacks, representment and reject inference
- **DS domain:** fraud/risk and delayed labels. **Setting:** an e-commerce fraud model with declines, chargebacks (60–120 days) and representment outcomes (won or lost disputes).
- **Sym:** the challenger beats the champion in the backtest; after the switch, fraud losses rose.
- **Truth:**
  - The backtest only contains approved transactions (declined have no labels), and the champion declined the challenger's false negatives.
  - Chargebacks mature late, and recent months look clean.
  - Representment wins turn chargebacks into non-fraud later.
  - A 2% random approve-through sample exists (for reject inference).
- **Wrong path:** evaluate on approved transactions with a 120-day maturity. That still has selective labels and ignores representment outcomes.
- **Hyp:** challenger worse★; fraud attack wave★; label maturity★; selective labels.
- **DS:** selective labels with an exploration sample, maturity, label revision (representment), cost-based evaluation.
- **Grains:** transaction, dispute lifecycle, decision policy, random-approve sample.
- **Repair:** label builder (maturity plus representment), evaluation population (approve-through sample, weights), cost metric, decision.
- **Horizon:** long.
- **Natural wrong impl:** matured approved-only evaluation.
- **Verifier:** high using truth. **vs 02:** harder. **Overlap:** Task 03 (selective labels) moderate-high.

---

## Mandatory type coverage

| Type | Candidates (count) |
|---|---|
| ML evaluation (≥3) | G01, G02, G03, G23, G30 (5) |
| Experimentation / causal (≥3) | G04, G05, G06, G21, G24 (5) |
| Forecasting / time series (≥3) | G07, G08, G09, G10, G20 (5) |
| Production ML / feature store (≥3) | G11, G12, G13, G27 (4) |
| Financial / economic (≥3) | G14, G15, G16, G29 (4) |
| Data quality / entity resolution (≥3) | G17, G18, G19, G20 (4) |
| Missing data / survival (≥2) | G10, G21, G22, G01 (4) |
| Recommender / ranking (≥2) | G24, G25 (2) |
| No-bug negative controls (≥2) | G26, G27 (2) |
| Other | G28 attribution; G29 optimisation; G19 geospatial |

Scoring, ranking and top-15 selection: `research/gen3_scoring.md`.
