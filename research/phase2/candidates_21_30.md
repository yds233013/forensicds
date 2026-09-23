# Candidate incidents P21–P30

---

## P21 — The assay is 96 % sensitive on the samples we sent for confirmation
**C** diagnostics laboratory · **D** clinical data scientist · **E** a new rapid assay is reported at 96 %
sensitivity and the lab wants to drop the confirmatory step for negatives to save £1.4 m; the medical
director is uneasy. **F** removing a confirmatory test for ~180 k specimens a year.
**G** LIS orders and results, confirmatory results (ordered for all positives, plus a **systematic 1-in-40
audit of negatives**, plus clinician-requested confirmations), requesting-clinician notes, the method
validation report on an enriched panel, QC and calibration logs, the SOP defining when confirmation is
ordered, prevalence by requesting source. **H** (1) sensitivity really is 96 %; (2) **verification bias** —
sensitivity computed on confirmed specimens is inflated because confirmation is ordered when the clinician
suspects disease; (3) the validation panel is enriched and non-representative; (4) sensitivity varies by
specimen type and viral load / analyte concentration; (5) clinician-requested confirmations break the
audit design's weights. **I** the accuracy estimate must be computed over the **design-weighted** specimen
population, separating the systematic audit (known probability) from clinician-requested confirmations
(unknown, outcome-dependent), and sensitivity is conditional on analyte level.
**J** design-weighted sensitivity and specificity on the routine population, plus the number of missed
cases per year under each policy. **K** design-weighted estimation with the audit stratum · a
Begg–Greenes-style correction for verification bias · stratification by analyte concentration; accepted if
consistent. **L** a careful analysis restricted to specimens with a confirmatory result, with bootstrap
intervals and a subgroup breakdown by specimen type — reported as "sensitivity on all verified specimens,
n = 9,412". **M** the sample is large, the subgroups are consistent, the intervals are tight, and it
reconciles with the validation report. **N** ties to the LIS; subgroup consistency; matches the vendor's
panel figure. **O** separate the confirmed specimens by **why** they were confirmed: within the systematic
audit stratum, weighted sensitivity is materially lower, and the gap grows at low analyte concentration —
exactly where the missed cases are. Second route: predicted vs observed positives in a source with
independent registry follow-up. **P** an external registry or downstream clinical-outcome linkage for a
subset — an independent system. **Q** reproduce 96 % → ask who got confirmed and why → split audit vs
requested → weight → stratify by concentration → compute annual missed cases → decide.
**R** the sophisticated route is the standard "use all verified data" analysis; three commitments
(verification mechanism, weighting, conditioning variable). **S** grade weighted sensitivity/specificity,
the concentration-stratified profile, missed cases per year, and the policy decision. **T** accept
design-weighting or a Begg–Greenes correction. **U** low. **V** medium — the SOP must specify the audit
design without stating its statistical consequence. **W** verification bias is a named, well-documented
hazard in diagnostic accuracy studies (STARD reporting standards address it). **X** family: outcome-
dependent verification · variants in fraud review, QA inspection, content moderation. **Y** distinct from
G44 in the discovery set: there the contract *stated* the target population and rate and the task was a
transport identity; here the target population must be *reconstructed* from two different verification
mechanisms, one with unknown weights, and the estimand is conditional on a continuous covariate.
**Z** ADMITTED.

---

## P22 — Yield fell the week we recalibrated the CMM
**C** discrete manufacturing · **D** quality engineer / process data scientist · **E** first-pass yield on
a machined component dropped from 97.2 % to 92.8 % in week 19; scrap cost is up £180 k/month and the
supplier of the raw bar is being blamed. **F** a supplier change worth £2.4 m and a possible line
shutdown. **G** dimensional measurement records from two coordinate-measuring machines (one recalibrated in
week 19, with the calibration certificate and the as-found/as-left deviations), **retained reference parts**
measured before and after, process parameter logs, raw-material certificates by heat/lot, operator and
shift records, the SPC control-chart config with its limits, a gauge R&R study from 2024, the scrap
disposition log. **H** (1) material quality degraded; (2) the **measurement system** changed — the
recalibration shifted bias, so parts that used to pass now fail; (3) a tool-wear trend crossed the
tolerance; (4) the SPC limits were recomputed on a different period; (5) a new operator on nights.
**I** the pass/fail outcome is produced by an **instrument whose bias changed**, and the specification is
unchanged — so "yield" is not comparable across week 19, and a correct analysis needs the measurement bias
separated from the process shift. **J** process capability and true nonconforming rate on a single
measurement reference, with the measurement-bias component quantified and the material effect estimated
after removing it. **K** the retained reference parts as a bias bridge · a nested variance decomposition
(part/instrument/operator) to allocate variation · a heat-lot analysis after bias correction; accepted if
consistent. **L** a rigorous SPC and capability study: control charts by shift and material lot, Cp/Cpk
before and after, and an ANOVA showing a significant lot effect — concluding the new heat lots are out of
specification. **M** the analysis is textbook, the lot effect is significant, and the timing coincides with
a lot changeover (it does — lots change weekly). **N** charts are in control apart from the shift; Cpk
recomputes consistently; lot means differ significantly. **O** the **retained reference parts**: measured
on the recalibrated machine they read systematically ~8 µm larger, which alone moves the pass rate by most
of the observed drop. A second route: the *second*, un-recalibrated CMM shows no yield change on parts it
measured over the same weeks. **P** functional test results (leak/fit test) which do not depend on the CMM
— an independent outcome. **Q** reproduce the drop → enumerate material vs measurement → find the
calibration certificate and reference parts → quantify bias → correct → re-test the lot effect → decide
(recalibrate the specification limits, not the supplier) → repair. **R** the wrong route is a correct SPC
investigation whose outcome variable is instrument-dependent; three commitments (measurement reference,
variance allocation, material effect after correction). **S** grade the bias estimate, the corrected
nonconforming rate, the residual lot effect, and the supplier decision. **T** accept the reference-part
bridge or the second-CMM comparison. **U** low. **V** low — the certificate makes the change factual.
**W** gauge bias and gauge R&R are core quality-engineering practice; "recalibration changed the yield" is a
classic plant story. **X** family: measurement-system change with a physical bridge · variants in clinical
labs, energy metering, environmental monitoring. **Y** distinct from P03 (software instrument, overlap
period) by having a *physical* bridge and a specification that does not move. **Z** ADMITTED.

---

## P23 — The better alloy that was only better in the lots we trialled
**C** manufacturing / materials · **D** process data scientist · **E** a trial of an alternative alloy
shows 22 % fewer fatigue failures (p = 0.003, n = 1,840 parts) and procurement wants to switch; the
metallurgist points out the trial ran on four heats. **F** a £5 m annual material switch and a
qualification programme. **G** trial records (part-level results, with heat/lot, line, shift, die and
operator), incoming material certificates with chemistry per heat, fatigue test rig logs, a **randomised
sub-trial** where both alloys were run within the same shift and die, the qualification protocol, historical
failure data by heat, a note that the trial alloy arrived in four heats from one mill.
**H** (1) the alloy is better; (2) the comparison is **confounded at the heat level** — four heats is an
effective n of 4, not 1,840, and heats differ in chemistry and processing; (3) die and line assignment
correlate with alloy; (4) the test rig drifted between trial phases; (5) a selection effect in which parts
were submitted for testing. **I** the **error structure**: observations are nested in heats, and the
treatment is assigned at heat level, so unit-level inference is invalid; the correct object is a
heat-level effect with a heat-level variance component. **J** the alloy effect with the correct level of
clustering and its associated uncertainty, plus what sample of heats would be needed to support the
decision. **K** a mixed model with heat random effects · cluster-robust inference at heat level · the
within-shift randomised sub-trial as the design-clean estimate; accepted if consistent.
**L** a sophisticated part-level survival analysis of cycles-to-failure with Weibull fitting, covariate
adjustment for die and line, and a highly significant alloy coefficient. **M** the survival model is
appropriate for fatigue data, covariates are controlled, and the effect is large and precise; the
practitioner has done real statistics. **N** Weibull fit diagnostics; covariate balance; result stable to
covariate choice; ties to the rig logs. **O** re-fit with **heat as a random effect**: the standard error
roughly triples and the effect is no longer distinguishable from zero. Second route: within the
**randomised sub-trial** (same shift, same die, alternating alloy), the difference is near zero — and the
historical data show between-heat variance of the same magnitude as the claimed effect. **P** field
warranty returns for parts already shipped from both alloys — an independent outcome with different
selection. **Q** reproduce p = 0.003 → ask at what level treatment varies → discover four heats →
re-fit with clustering → find the within-shift sub-trial → estimate the heat variance component →
compute the required number of heats → decide (extend qualification, do not switch yet).
**R** the wrong route is *more* sophisticated than the right one and fails on the unit of inference;
three commitments (level of assignment, variance components, decision under uncertainty). **S** grade the
heat-level effect and its interval, the variance components, the required-heats calculation and the
switch decision. **T** accept mixed model, cluster-robust or sub-trial routes. **U** low. **V** low.
**W** pseudo-replication with cluster-assigned treatments is among the most common real inferential
errors in industrial trials. **X** family: unit-of-inference / variance components · variants in
agriculture, education, clinical cluster trials, ad geo tests. **Y** entirely new: nothing in the suite
tests the level of inference or uncertainty-driven decisions. **Z** ADMITTED.

---

## P24 — Consumption is falling, or we stopped reading the meters
**C** utilities / energy retail · **D** demand analyst · **E** residential consumption per customer appears
down 6.3 % year-on-year, which drives a hedging and a tariff decision; field ops mention a meter-reader
shortage. **F** a £20 m energy-procurement hedge and a tariff filing.
**G** billing reads with a read-type flag (actual, customer-provided, **estimated**), meter exchange
register (traditional → smart), the estimation algorithm documentation, smart-meter interval data for the
converted subset, weather data, tariff and customer registry, a field-ops staffing note, the hedging model.
**H** (1) consumption genuinely fell (efficiency, prices, weather); (2) the share of **estimated** reads rose
and the estimator is biased low; (3) the smart-meter conversion changed *who* is measured accurately
(selection); (4) weather normalisation is wrong; (5) a tariff migration changed the customer mix.
**I** the measurement process is **missing-not-at-random**: reads are estimated when access fails, access
failure correlates with occupancy and consumption, and the estimation algorithm regresses to a stale
historical mean. **J** weather-normalised consumption per customer on a consistent measurement basis, with
the estimation-induced bias quantified and the hedge volume implied.
**K** the smart-meter subset as a known-answer panel (actual interval data for the same customers who also
receive estimated bills) · a selection model for read type · reconciliation to network-level offtake;
accepted if consistent. **L** a careful weather-normalised regression (HDD/CDD, customer fixed effects,
tariff controls) on billed consumption, concluding a genuine 4.8 % efficiency-driven decline after
normalisation. **M** the normalisation is standard and well fitted, the fixed effects absorb mix, and the
residual decline is smooth and plausible. **N** HDD/CDD fit; customer FE absorb mix; ties to billed volume.
**O** the **smart-meter subset**: for customers with both an estimated bill and actual interval data, the
estimate is systematically low, and the bias is larger for high-consumption households. Second route:
**network-level offtake** (an independent system) shows no comparable decline — billed volume and delivered
volume have diverged. **P** distribution-network offtake and settlement data. **Q** reproduce −6.3 % →
check read types → find the estimated share rose → use the smart-meter panel to measure the bias →
reconcile to offtake → restate → re-run the hedge → decide. **R** the sophisticated route does the right
thing to the wrong variable; three commitments (measurement basis, selection mechanism, reconciliation
target). **S** grade the bias-corrected consumption series, the estimation bias by decile, the offtake
reconciliation and the hedge volume. **T** accept the panel-bridge or a selection-model route.
**U** low. **V** low. **W** estimated-read bias and its effect on demand series is a documented utility
problem; unbilled/unaccounted-for energy reconciliation is standard practice. **X** family: MNAR
measurement with an independent physical aggregate · variants in water, telemetry, survey statistics.
**Y** new: the suite has no measurement-process-missingness task. **Z** ADMITTED.

---

## P25 — We sized the substation on the average of the peaks
**C** energy / capacity planning · **D** network planning analyst · **E** a load study says the feeder needs
no reinforcement for five years; the planning standard is written on the **coincident** peak, and the study
used the average of individual customer peaks. Heat-pump adoption is accelerating.
**F** a £6 m reinforcement deferral with an outage-risk consequence.
**G** smart-meter interval data for a sample of customers, the customer registry with heat-pump and EV
flags, the feeder's SCADA measured peak (an independent aggregate), the planning standard (defining the
design condition: 1-in-20 winter peak at the feeder), an adoption forecast, a diversity-factor table from
2019, weather data, the load study workbook. **H** (1) no reinforcement needed; (2) the study used the
wrong aggregation — non-coincident peaks overstate diversity; (3) the diversity factor is stale because
heat pumps are more coincident than legacy load; (4) the sample under-represents adopters;
(5) the design weather condition was mis-specified. **I** the object is a **property of the aggregate
distribution, not of an average of individual quantities**: peak of the sum ≠ sum of peaks, and the
diversity between customers changes with technology. **J** the feeder-level coincident peak under the
design condition, with a diversity factor estimated from current interval data, projected under adoption,
with uncertainty. **K** direct summation of interval data to a feeder profile then extreme-value / design-
condition estimation · a diversity-factor model by technology · reconciliation to SCADA; accepted if
consistent. **L** a rigorous per-customer peak-demand model with weather sensitivity and a stale
diversity factor applied at the end — reported with confidence intervals and a scenario table.
**M** the per-customer model is excellent and validated at customer level; the final step is one
multiplication by a documented factor. **N** per-customer predictions validate; weather response sensible;
scenario table coherent. **O** reconcile the modelled feeder peak against **SCADA measured peak** for last
winter: the model under-predicts, and the error grows with heat-pump penetration — the diversity factor is
wrong for the new load. Second route: estimate coincidence directly from the interval data for adopters vs
non-adopters. **P** SCADA feeder measurements — an independent physical aggregate the study never used.
**Q** reproduce the study → ask what the standard's design condition is → recognise peak-of-sum →
aggregate intervals → estimate coincidence by technology → validate against SCADA → project → decide.
**R** the wrong route is high-quality bottom-up modelling ruined by one aggregation step; three commitments
(aggregation object, diversity estimation, design condition). **S** grade the coincident peak, the
technology-specific diversity factors, the SCADA reconciliation and the reinforcement decision.
**T** accept direct aggregation or a coincidence model that reproduces the SCADA-validated peak.
**U** medium — SCADA must be present but not signposted as the answer key. **V** low — the standard defines
the design condition. **W** diversity/coincidence factors and their invalidation by electrification are a
live network-planning issue. **X** family: aggregation object (extremes vs averages) · variants in telecom
capacity, cloud autoscaling, staffing peaks. **Y** new: the suite has no extremes/aggregation-object task.
**Z** ADMITTED.

---

## P26 — The loss ratio that improves every time we look at it early
**C** insurance · **D** reserving analyst with a DS remit · **E** the latest accident year shows a 58 %
paid loss ratio against a 71 % plan, and the pricing team want to cut rates by 5 %; the chief actuary
objects. **F** a 5 % rate cut across a £180 m book and a reserve release.
**G** claims transactions with report and payment dates (a development triangle), exposure/earned premium
by month, a mid-year **claims-handling change** (a new triage team accelerating small claims), a
reinsurance treaty with an attachment point, large-loss register, case reserves with an adjuster-strength
note, a prior-year actual-vs-expected report, the pricing model.
**H** (1) genuine improvement; (2) the year is **immature** — paid-to-date understates ultimate
(development/truncation); (3) the claims-handling change altered the payment pattern, so historical
development factors no longer apply; (4) a mix shift toward shorter-tail covers; (5) a large loss not yet
reported. **I** the object is an **ultimate** quantity estimated from truncated data, and the estimator's
key input (development pattern) was invalidated by an operational change — so applying historical factors
is doubly wrong. **J** ultimate loss ratio for the accident year with a development pattern appropriate to
the post-change process, with uncertainty, plus the rate implication.
**K** chain-ladder with adjusted factors · Bornhuetter–Ferguson with an exposure prior · a
payment-pattern model estimated on post-change months; accepted if the ultimates agree within tolerance.
**L** a careful chain-ladder with tail factor selection, outlier handling for the large loss, and a
Mack-style standard error — concluding the ultimate loss ratio is 63 % and the rate cut is supportable.
**M** it is the standard method, diagnostics (residual plots, factor stability) look fine, and it does
account for immaturity. **N** triangle ties to the ledger; factor selection documented; Mack SEs reported.
**O** test factor stability **around the handling change**: development factors for post-change months are
materially different, and the historical tail no longer applies. A held-out backtest — apply the same
method to a *prior* year at the same maturity and compare with its known ultimate — reveals systematic
under-reserving of the current approach. Second route: Bornhuetter–Ferguson with the exposure prior gives a
materially higher ultimate, and the divergence is diagnostic.
**P** reinsurer's independent estimate of ceded losses for the same year, or the case-reserve strength
trend. **Q** reproduce 58 % → recognise immaturity → build the triangle → discover the handling change →
test factor stability → backtest the method on a matured year → choose an estimator → quantify uncertainty
→ decide. **R** truncation plus an operational break in the estimator's key input; three commitments
(ultimate vs paid, pattern validity, uncertainty-aware rate decision). **S** grade the ultimate loss
ratio, the post-change development pattern, the backtest error and the rate decision. **T** accept
chain-ladder with justified factors, BF, or a pattern model. **U** low. **V** medium — the rate rule must
state what loss ratio it is written on. **W** claims-handling changes invalidating development factors is a
standard reserving caution. **Y** distinct from G34: competing risks vs truncation/development; and the
decision is a price, with uncertainty mattering. **X** family: truncation + estimator-input invalidation ·
variants in warranty reserves, clinical trial interim analysis, cohort LTV. **Z** ADMITTED.

---

## P27 — A roster that is optimal and illegal
**C** workforce operations / logistics · **D** operations research analyst · **E** an optimiser says the
depot can cover next quarter's volume with 12 fewer drivers, saving £1.1 m; the transport manager says the
roster cannot be worked. **F** a headcount decision for 180 drivers and a service-level commitment.
**G** the optimiser code and its constraint set, driver contracts (two agreements with different rest
rules), the licence and certification register (ADR, tacho cards, vehicle categories), the working-time
rules engine used by payroll, historical rosters with compliance exceptions, absence and holiday patterns,
volume forecasts with vintage, depot vehicle availability and maintenance schedule, a union agreement,
a rules-engine audit log showing rejected rosters.
**H** (1) the saving is real; (2) the optimiser's **feasible set omits constraints** (rest between shifts
by agreement type, certification coverage per route, vehicle-type matching, maximum consecutive nights);
(3) demand variability means a plan feasible in expectation fails on peak days; (4) absence is modelled at
the average rather than as a distribution; (5) the objective is drivers, not cost — overtime substitutes.
**I** the optimisation is **mathematically correct over the wrong feasible set**, and the decision also
requires a **stochastic** feasibility notion: a roster must be workable on a bad day, not on an average one.
**J** the minimum sustainable headcount such that a compliant roster exists with a stated service level
under demand and absence variability — plus the cost-optimal mix of headcount and overtime.
**K** re-solve with the full constraint set (validated against the rules engine) · a simulation of the
proposed roster against historical demand/absence draws · a cost model including overtime and agency;
accepted if the headcount and cost agree. **L** a strong OR job: tighten the LP/MIP formulation, add
valid inequalities, prove optimality with a small gap, and report a robust-looking solution with a
sensitivity table on volume. **M** it is provably optimal for its model, the gap is < 0.5 %, and the
sensitivity table shows the saving survives ±10 % volume. **N** solver optimality certificate; constraint
satisfaction *as modelled*; sensitivity table; ties to payroll rates. **O** **replay the roster through the
payroll rules engine**: it is rejected on rest and consecutive-night rules for a named subset of weeks —
the engine is an independent implementation of the constraints. Second route: simulate against historical
absence and peak days — service level falls below commitment on 18 % of weeks. **P** the rules-engine audit
log of historically rejected rosters, showing which constraints bind in practice.
**Q** reproduce the saving → enumerate the true constraint set from contracts and the register → replay
through the rules engine → re-solve → simulate absence and peak → price overtime → decide.
**R** an optimisation object plus a stochastic feasibility object plus an economic mix decision — three
consequential commitments, and the sophisticated route improves the *solver*, not the *model*.
**S** grade the corrected feasible headcount, the binding constraints, the simulated service level and the
headcount/overtime decision. **T** accept any solver or formulation that reproduces the feasible headcount
and cost. **U** low. **V** medium — the contracts must be authoritative and complete.
**W** "feasible in the model, infeasible on the ground" is the defining failure of workforce optimisation.
**X** family: wrong feasible set + stochastic feasibility · variants in nurse rostering, crew pairing,
field service, manufacturing scheduling. **Y** distinct from G41 (which is object-stated, execution-hard):
here the constraint set itself must be reconstructed from contracts and an independent rules engine.
**Z** ADMITTED.

---

## P28 — Safety stock for a world where demand is independent
**C** supply chain / inventory · **D** inventory scientist · **E** a re-parameterisation of safety stock
promises a £9 m working-capital release at the same 98 % service level; the DC manager reports more
backorders since it went live in two regions. **F** a £9 m working-capital decision and a service-level
commitment to key accounts. **G** demand history by SKU-DC-week, supplier lead-time records (with a
documented carrier change), open-order and receipt data, the current safety-stock formula in code (normal
demand, deterministic lead time), a service-level definition doc (fill rate vs cycle service level),
promotional calendar, two regions where the new parameters went live, historical backorder records, a
supplier performance report. **H** (1) the release is safe; (2) demand is **autocorrelated and
cross-correlated** across SKUs (promotions, weather), so pooled variance understates risk;
(3) **lead-time variability** is ignored and the carrier change increased it; (4) the service-level metric
in the formula (cycle service level) is not the one committed (fill rate); (5) forecast error, not demand
variance, is the right input. **I** three distinct modelling commitments — the **variance object** (forecast
error vs demand variance, with correlation), the **lead-time distribution**, and the **service-level
definition** — and the live regions constitute a natural experiment that can test the whole package.
**J** safety stock achieving the committed fill rate under the empirical joint distribution of forecast
error and lead time, and the working-capital figure that follows.
**K** an analytic formula with lead-time variance and correlation corrections · a simulation/bootstrap of
the inventory process · the live regions as validation; accepted if the implied stock and service agree.
**L** a careful statistical upgrade: fit demand distributions per SKU, test normality, use empirical
quantiles instead of z-scores, and report a rigorous quantile-based safety stock — still with
deterministic lead time and cycle service level. **M** the distributional work is genuinely better than
the incumbent, the quantiles are empirical, and the metric improves on the data used. **N** fitted
distributions pass goodness-of-fit; ties to current stock; service-level formula applied consistently.
**O** **the two live regions**: realised fill rate is below target at the new parameters, and the shortfall
concentrates in weeks following a long lead time — the omitted variance component. Second route: a
bootstrap of the inventory process with resampled *joint* demand-and-lead-time draws reproduces the
observed backorders; the analytic formula does not. **P** realised fill rate from the order-line ledger,
an independent outcome. **Q** reproduce the promise → enumerate the three inputs → measure lead-time
variability and the carrier break → recognise fill-rate vs CSL → simulate → validate against the live
regions → re-parameterise → decide. **R** three dependent modelling commitments and a decision under
uncertainty; the sophisticated route fixes the least important one. **S** grade the required safety stock
by SKU class, the lead-time variance contribution, the fill-rate/CSL gap, the simulated service level and
the working-capital decision. **T** accept analytic-with-corrections or simulation. **U** low.
**V** medium — the committed service metric must be in the customer agreement. **W** ignoring lead-time
variability and confusing service-level definitions are the two classic inventory errors.
**X** family: optimisation under mis-specified uncertainty · variants in cash buffers, staffing, capacity.
**Y** distinct from G10 (latent demand under censoring) and G41 (deterministic feasibility): here the
object is a distributional input to a decision rule. **Z** ADMITTED.

---

## P29 — A churn model that is excellent on the customers who have not churned yet
**C** B2B SaaS · **D** ML engineer / data scientist · **E** a churn model reports AUC 0.88 and lift that
would justify a £4 m retention programme; the previous model scored 0.74 and nothing else changed except a
"label-window fix" in the pipeline. **F** a £4 m programme and a decision to replace the incumbent model.
**G** contract and subscription ledger with renewal dates and notice periods, a **label definition doc**
with a dated change (from "no renewal by expiry" to "no renewal within 90 days of expiry"), the training
pipeline with a snapshot date, support and usage data, a model registry with both models' training
windows, a cohort maturity table, a prior backtest, the programme business case.
**H** (1) the new model is genuinely better; (2) the **label window** change makes recent accounts'
labels immature, so the evaluation set is enriched with resolved (easy) cases; (3) the notice-period
structure means churn is *known* before it is labelled, so a feature encodes it (leakage);
(4) the training window now includes a period with a pricing change; (5) the comparison is on different
populations. **I** **label maturity and label definition interact**: with a 90-day window, accounts whose
outcome is not yet determined are dropped, and the drop is outcome-dependent (accounts that churn late look
like non-churners then vanish). Evaluation must be on a **matured cohort** under a **fixed** definition, and
the notice field must be checked for leakage. **J** discrimination and lift on a matured, definition-fixed
cohort, with the leakage component isolated, and the programme's expected value.
**K** matured-cohort evaluation · a time-sliced backtest with as-of features · a leakage audit by feature
ablation; accepted if consistent. **L** a careful temporal validation: train on months 1–18, test on
19–24, report AUC by month, and confirm stability — with the label definition held at the *new* standard
throughout. **M** temporal validation is exactly right in spirit, the AUC is stable across test months,
and the same definition is used on both sides. **N** no train/test overlap; stable monthly AUC; ties to
the registry. **O** compute, per test month, **the share of accounts whose label is determined**: it falls
to 40 % in the last months, and the retained accounts are disproportionately resolved churners. Restricting
to accounts with a full 90-day post-expiry window collapses the AUC. Second route: ablate the
notice-period-derived feature; most of the gain disappears. **P** realised renewal outcomes from the
billing ledger for a fully matured cohort — an independent, complete record.
**Q** reproduce 0.88 → ask what the label change did → compute maturity by month → restrict to matured →
ablate suspicious features → re-evaluate → value the programme → decide. **R** two interacting data-
generating features (definition change, maturity) plus a leakage channel; three commitments.
**S** grade matured-cohort AUC/lift, the maturity profile, the leakage contribution and the programme
decision. **T** accept matured-cohort or a censoring-aware survival evaluation. **U** medium — must not
name the maturity issue in the instruction. **V** low. **W** delayed/immature labels inflating offline
metrics is a documented, frequent production ML error. **Y** distinct from Task02: there the *features*
were timed wrongly; here the *labels* are immature and their definition changed, and the correct fix is an
evaluation-population change, not a feature rebuild. **X** family: delayed labels and maturity · variants
in credit, fraud, medical outcomes, ads conversion. **Z** ADMITTED.

---

## P30 — The retargeting channel that converts people who had already decided
**C** advertising / performance marketing · **D** measurement scientist · **E** the retargeting vendor
reports a 6.8× ROAS from last-touch attribution; a finance-led review wants either to double spend or cut
it. **F** a £9 m annual spend decision and the vendor contract.
**G** ad-server delivery logs including **ghost-ad / PSA holdout** records (eligible users who were assigned
to a control and had the auction won but the ad withheld), site and app conversion events with timestamps,
the attribution config (7-day click, 1-day view), CRM orders, audience-definition rules (cart abandoners in
the last 3 days), a prior geo-experiment on a different channel, the vendor's methodology doc, the media
plan. **H** (1) retargeting is highly incremental; (2) the audience is selected on **intent** — cart
abandoners would convert anyway — so last-touch credits organic conversions; (3) the attribution window
captures conversions that were already in flight; (4) view-through conversions are mostly spurious;
(5) cross-device identity merging double counts. **I** the audience definition makes exposure
**endogenous to the outcome**, and the workspace contains a genuine randomised control (the ghost-ad
holdout) that most practitioners never use because the vendor's own report does not. **J** incremental
conversions and incremental profit per pound, estimated from the randomised holdout, on a stated
conversion window, with the last-touch overstatement quantified. **K** ghost-ad holdout contrast ·
a geo/market-level test if available · an intent-matched observational estimate as a *bias
demonstration* only; accepted if the holdout-based estimate is reproduced. **L** a sophisticated
observational causal analysis: propensity matching on intent signals (cart value, visit recency,
category), doubly-robust estimation, sensitivity analysis to unobserved confounding with an E-value —
reporting 2.9× ROAS as "the incremental figure after removing selection". **M** it is a serious causal
analysis, the matching balances all observed intent signals, and the E-value suggests robustness to
plausible unobserved confounding. **N** covariate balance; overlap; E-value reported; ties to CRM revenue.
**O** the **ghost-ad holdout**: incremental ROAS is ~1.1×, far below the matched estimate, because the
decisive confounder (purchase intent at the moment of impression) is not in any logged covariate.
A placebo: apply the same matched estimator to the holdout arm's *withheld* impressions, which should show
zero effect and does not. **P** CRM revenue by randomised arm — the independent outcome.
**Q** reproduce 6.8× → identify audience selection → attempt observational adjustment → discover the
holdout → estimate the randomised effect → explain the gap → restate the window → decide.
**R** the sophisticated route is a modern causal-ML analysis with a sensitivity check, defeated by a
confounder that no log contains; three commitments (identification source, window, profit object).
**S** grade the randomised incremental ROAS, the last-touch overstatement, the placebo result and the
spend decision. **T** accept holdout or any design-based route; the observational route may be reported
as a bias estimate but not as the answer. **U** medium — the holdout must be discoverable from the
delivery logs, not named. **V** low. **W** ghost ads / PSA holdouts and the "retargeting converts the
already-converting" problem are documented in ad-measurement practice. **X** family: endogenous exposure
with an in-log randomised control · variants in email, push, sales outreach, coupons.
**Y** distinct from P10 (there, two legitimate methods disagree about a modelled channel; here a
randomised control exists in the logs and the trap is a sophisticated observational substitute).
**Z** ADMITTED.
