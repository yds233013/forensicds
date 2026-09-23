# Candidate incidents P01–P10

Field key: A id · B title · C domain · D role · E incident · F consequence · G evidence · H hypotheses ·
I hidden scientific issue · J object to derive · K applicable methods · L tempting sophisticated wrong
route · M why it looks coherent · N coherence checks it passes · O falsification that exposes it ·
P independent validation · Q expected chain · R why harder than current tasks · S verifier strategy ·
T multiple-valid-method handling · U cheap-solve risk · V ambiguity risk · W realism · X scaling family ·
Y novelty · Z admission result.

---

## P01 — The promotion that paid for itself on paper
**C** grocery retail, trade promotion · **D** category analyst, promo governance · **E** a 4-week
multibuy on a coffee line shows +38 % unit uplift and the category team want it in the annual calendar;
Finance sees category margin flat. **F** £14 m annual promo budget reallocation; the governance rule
funds a mechanic only if incremental category margin ≥ £0.9 m. **G** EPOS baskets, promo registry with
mechanic and funding, planogram, competitor price file, DC shipments, category P&L, a prior promo
evaluation deck, buyer's note claiming "the multibuy recruits new shoppers". **H** (1) genuine
incremental demand; (2) cannibalisation from other coffee lines; (3) pantry loading — forward-buying
that depresses the following 4 weeks; (4) basket-level substitution away from higher-margin adjacents;
(5) a competitor's concurrent price cut. **I** incrementality must be measured on the **category and
basket margin object**, not the promoted SKU's units, and over a window long enough to contain the
post-promo dip. **J** incremental category contribution margin per promo pound, over promo plus recovery
window, net of cannibalisation and forward-buy. **K** matched-store DiD with a category-level outcome ·
synthetic control on category margin · basket-level switching decomposition · both accepted if they
agree within tolerance. **L** a careful matched-store DiD on the *promoted SKU's* units with store and
week effects, correct standard errors, and a clean pre-trend on that outcome. **M** every number ties;
the SKU-level effect is real and large; the pre-trend is flat because the *SKU* had no trend. **N** ties
to EPOS totals; matched stores balanced; SKU pre-trend flat; effect stable across regions. **O** run the
same estimator on **category** margin in the same stores, and extend the window past the promo: the
uplift shrinks and a negative dip appears. A second route: the buyer's "new shopper" claim is falsified
by loyalty-ID first-purchase counts. **P** DC shipments to promo stores vs the modelled incremental
units — an independent system that cannot be moved by EPOS definitional choices. **Q** reproduce +38 % →
notice category margin flat → hypothesise cannibalisation/forward-buy → extend the window → measure
switching in baskets → re-estimate at category level → reconcile to shipments → decide. **R** three
dependent commitments (outcome object, window, unit of aggregation) where the wrong first choice makes
the rest look clean. **S** grade incremental category margin, the cannibalisation and forward-buy
components, the recovery-window length implied, and the funding decision; hidden extracts vary competitor
activity and pantry-loading strength. **T** accept DiD, synthetic control and a switching decomposition
if they reproduce the components within tolerance. **U** low: the SKU-level answer is the trap, not the
answer. **V** medium — must state the governance rule's window explicitly, else the recovery window is
underdetermined. **W** standard trade-promotion practice; cannibalisation and forward-buying are the
first two things a commercial analyst is taught to check. **X** family: economic-object incrementality ·
variants in pharmacy, telco handset promos, gaming IAP. **Y** not G05: no staggered adoption, no
identification-by-conditioning; the failure is the outcome object and the economics. **Z** ADMITTED.

---

## P02 — The elasticity that came from the price changes we chose
**C** grocery pricing · **D** pricing scientist · **E** a log-log demand model estimated on two years of
price moves says own-price elasticity is −1.9, so a 4 % price cut on 200 lines "pays back"; the trading
director has seen this fail twice. **F** a £30 m revenue decision on 200 lines. **G** price registry with
reason codes (competitor match, promo, cost pass-through, range review), EPOS, competitor price feed,
cost file, a 40-store randomised price test run 14 months ago and then forgotten, pricing policy doc.
**H** (1) the estimate is right; (2) prices moved in response to demand (endogeneity); (3) competitor
matching makes price and competitor price collinear; (4) promo periods contaminate the base-price
series; (5) elasticity differs by mission/format so the pooled number does not apply to the proposed
lines. **I** observational price variation was **policy-induced**; the only exogenous variation in the
estimate sits in the forgotten randomised test. **J** own-price elasticity identified from exogenous
variation, for the specific line group and format the decision applies to. **K** the randomised test as
the primary estimate · an IV/cost-shock design as a second route · a comparison of both against the
pooled observational estimate to *quantify* the bias. **L** a sophisticated panel model: store and week
fixed effects, promo flags, competitor price control, clustered SEs, log-log, with sensible diagnostics.
**M** it fits well, the coefficient is stable across specifications, and the sign is right. **N** R²,
stable coefficients across FE specifications, balanced residuals, a placebo on a *non-price* covariate.
**O** estimate elasticity on the randomised-test stores only: it is materially smaller. Equivalently,
split the observational variation by **reason code** — competitor-match moves and cost pass-through
moves imply different elasticities, which they cannot if the parameter is structural. **P** the test's
own pre-registered readout, and a held-out post-test period. **Q** reproduce −1.9 → ask where price
variation came from → read reason codes → discover the randomised test → estimate on it → compare and
explain the gap → apply to the correct line group → decide. **R** the wrong route is a *good*
econometric answer to the wrong identification question; three commitments (variation source, line
group, base-price construction). **S** grade the exogenous elasticity, the observational-vs-exogenous
gap, the segment-specific estimates, and the price decision. **T** accept the randomised estimate or a
defensible IV if it lands within tolerance and its exclusion restriction is respected. **U** medium — the
test must not be signposted in the instruction; it must be discoverable from the registry. **V** low.
**W** endogenous pricing is the canonical applied-econometrics warning; retailers routinely hold small
randomised price tests. **X** family: policy-induced variation · variants in insurance rate-making, ad
bidding, freight rates. **Y** not Task02: nothing temporal; the failure is identification from the wrong
variation. **Z** ADMITTED.

---

## P03 — The shelf got better the week we changed the scanner
**C** retail operations · **D** availability analytics lead · **E** on-shelf availability jumps from
94.1 % to 97.3 % in week 32, exactly when a new handheld gap-scan app shipped; the supplier penalty
regime pays out on availability. **F** £2.2 m in supplier service-level penalties and a decision to
stop a remediation programme. **H** (1) the remediation worked; (2) the new app changed what counts as a
gap (definition); (3) scan frequency and coverage changed (sampling); (4) staff behaviour changed
(gaming); (5) a seasonal mix shift. **G** gap-scan events (old and new app, with a 3-week overlap where
both ran), EPOS, inventory snapshots, planogram, the app release note, penalty contract schedule,
store-manager comms, remediation programme brief. **I** the metric's **instrument** changed; historical
and current availability are not the same measurement. **J** availability on a *single* consistent
definition and sampling frame, over the whole period, and the penalty exposure implied. **K** re-derive
both definitions on the overlap period and bridge · reconstruct availability from inventory+EPOS as an
instrument-free proxy · model the sampling frame explicitly. **L** a careful interrupted-time-series on
the published availability series with a level-shift term at the app release, reporting a significant
improvement net of seasonality. **M** the ITS is well specified, seasonality is controlled, the break is
exactly at the intervention, and the effect is large. **N** series reconciles to the published KPI; break
date matches the release note; seasonal terms significant. **O** the **dual-instrumented overlap**: on
the same store-days the two apps disagree systematically; the "improvement" is a measurement bridge, not
behaviour. A second route: availability reconstructed from inventory and sales shows no break. **P** the
remediation programme's own store-level rollout schedule — if the improvement were real it would follow
the rollout, not the app release. **Q** reproduce the jump → enumerate instrument vs behaviour →
find the overlap → quantify the bridge → restate the series → recompute penalty exposure → decide.
**R** the sophisticated wrong route is a textbook-correct ITS; the error is that the *outcome variable
changed definition mid-series*, which no amount of time-series care fixes. **S** grade the bridged
series, the instrument effect, the behaviour effect and the penalty figure; hidden extracts vary overlap
length and the direction of the instrument bias. **T** accept any bridge that recovers the instrument
effect within tolerance. **U** low. **V** medium — the contract must state which definition governs
penalties. **W** instrumentation-change artefacts are among the most common causes of "metric moved"
tickets in retail and observability practice. **X** family: non-stationary measurement · variants in
telemetry, clinical devices, energy metering. **Y** entirely new to the suite. **Z** ADMITTED.

---

## P04 — Two forecasts, both reconciled, one buy plan
**C** supply-chain planning · **D** demand planner · **E** the SKU-level forecast sums to 4 % above the
category forecast the commercial team signed; the planning system reconciles top-down and the buy is
committed on the reconciled numbers, which are now 7 % below last year on a growing category. **F** a
£40 m seasonal buy; over-buy risks markdown, under-buy risks lost sales. **G** forecast service with
**vintaged** outputs at three hierarchy levels, actuals with revisions, promo calendar, a reconciliation
config, planner overrides log, last season's post-mortem, the commercial sign-off pack. **H** (1) SKU
models are wrong; (2) the category model is wrong; (3) top-down reconciliation is destroying SKU signal;
(4) planner overrides are double-counted; (5) the comparison to last year uses a restated actual. **I**
reconciliation is a **statistical choice**, not bookkeeping: top-down, bottom-up and MinT imply different
variances and different buys, and the correct one depends on where the signal is. **J** a coherent
forecast whose reconciliation is justified by measured level-wise accuracy, evaluated on the vintage that
would have been available at buy time. **K** bottom-up · top-down · optimal (MinT/least-squares)
reconciliation · any accepted if justified by a level-wise backtest on held-out vintages. **L** a clean
MinT implementation with the covariance estimated on the *revised* actuals and the *current* vintage,
reported as "statistically optimal reconciliation". **M** it is genuinely optimal under its assumptions,
the hierarchy sums exactly, and accuracy improves on the data used. **N** hierarchy coherence holds;
in-sample accuracy improves; overrides reconciled. **O** a **held-out vintage backtest**: rebuild the
forecast as of last season's buy date using only then-available actuals, and score all three
reconciliations against the outcome. The current-vintage advantage disappears. **P** the planner-override
log as an independent record of where humans already knew the SKU signal was better. **Q** reproduce the
gap → ask what reconciliation does → discover vintages → rebuild as-of → score levels → choose
reconciliation → set the buy → decide. **R** two dependent commitments (vintage and reconciliation) plus
an economics step (buy from a forecast under asymmetric cost). **S** grade level-wise accuracy on the
held-out vintage, the chosen reconciliation's weights, the resulting buy, and the markdown/lost-sales
exposure. **T** accept any of the three reconciliations if the justification metric is computed correctly
and the buy follows from it. **U** low. **V** medium — must state the buy-date and the cost asymmetry.
**W** hierarchical reconciliation and vintage-correct backtesting are standard, and getting them wrong is
a documented cause of seasonal over-buy. **X** family: hierarchical reconciliation · variants in energy
load, workforce demand, revenue planning. **Y** not G08 (which is a vintage-of-actuals problem for model
comparison); here the object is the reconciliation choice and the buy. **Z** ADMITTED.

---

## P05 — The supplier we were about to delist
**C** procurement / supplier quality · **D** supplier quality analyst · **E** supplier B's defect rate
has doubled to 1.8 % while supplier A sits at 0.6 %; the delist threshold is 1.5 %. **F** delisting a
supplier worth £18 m of annual volume and a 6-week transition risk. **G** inbound inspection records
with a sampling design that changed in April (from a fixed 1-in-20 to a risk-weighted plan), goods-receipt
volumes, a random audit stratum retained for exactly this purpose, defect taxonomy, supplier quality
agreement, the April change memo in an ops folder, complaint and return records. **H** (1) supplier B
genuinely degraded; (2) risk-weighted sampling over-samples B's suspect lots; (3) a defect-taxonomy change
reclassified cosmetic defects as functional; (4) a plant/line change at B affects one SKU only;
(5) inspector effects. **I** the inspection data are a **multi-stage non-random sample** whose selection
probabilities are known but not applied; the naive rate estimates the wrong quantity. **J** the
design-weighted defect rate per supplier per period, on a consistent defect definition, with the
contractual population. **K** inverse-probability-weighted estimation from the sampling frame · the random
audit stratum as a design-unbiased estimate · a stratified comparison; accepted if they agree. **L** a
careful logistic model of defect probability with supplier, month, SKU and plant effects, reporting an
adjusted odds ratio for supplier B — "controlling for mix". **M** the model is well specified, the
adjusted effect is still significant, and mix is "controlled". **N** predicted rates match observed by
cell; mix adjustment is present; model diagnostics fine. **O** the **random audit stratum**: in it,
B's rate is barely above A's. Conditioning on inspection cannot fix selection *into* inspection.
**P** customer returns and complaints per unit shipped — an independent system unaffected by the
inspection plan. **Q** reproduce the rates → ask how lots were selected → find the April change → apply
weights (or use the audit stratum) → check the taxonomy change → re-estimate → decide. **R** the wrong
route is a genuinely good mix-adjustment; the error is conditioning on a post-selection variable.
**S** grade weighted rates per supplier, the taxonomy-adjusted series, the audit-stratum estimate and
the delist decision. **T** accept IPW, the audit stratum, or a correctly specified selection model.
**U** low. **V** medium — must fix the contractual definition of a defect. **W** sampling-plan changes
routinely distort supplier scorecards; audit strata exist precisely to arbitrate. **X** family:
multi-stage selection with known design · variants in tax audit, claims review, food safety. **Y** not
G24: no logging policy, no OPE; the selection is an inspection plan and the object is a rate. **Z** ADMITTED.

---

## P06 — The cohort that stopped shrinking when we merged the cards
**C** retail CRM / loyalty · **D** customer analytics lead · **E** 12-month cohort retention improved
4.8 points for cohorts after March, which is when a household-identity merge shipped; the CRM team want
to claim the improvement for their onboarding programme. **F** a £6 m CRM budget reallocation and a
target set on retention. **G** loyalty transactions, card registry with a merge register (survivor and
merged IDs, with effective dates), household inference service output, onboarding-programme enrolment
log, a data-migration ADR, the CRM pack, definitions doc for "active customer". **H** (1) the programme
worked; (2) identity merges mechanically retain cohorts (two cards becoming one cannot both churn);
(3) the merge changed cohort *membership* retroactively; (4) a promotional recruitment wave changed cohort
composition; (5) the active-customer definition changed. **I** the unit of analysis is an **identity whose
definition changed mid-series**, and the merge is *not* random with respect to activity — active
households are more likely to be merged. **J** retention on a consistent identity spine, with cohorts
defined by the identity in force at acquisition, and merge-induced survivorship removed. **K** rebuild the
spine as-of each cohort date · restrict to a known-merge-free subset · a merge-aware survival model;
accepted if they agree. **L** a survival model with cohort and tenure effects and a March indicator,
concluding the hazard fell after March net of composition. **M** the model is coherent, the hazard
change is significant, and composition is "controlled". **N** cohort sizes tie to the registry; hazards
smooth; the indicator is significant. **O** a **known-answer subset**: households the merge register shows
were never merged show no improvement. Second route: reconstruct pre-March cohorts under the *post-March*
identity rule — the historical improvement disappears. **P** an independent system: payment-instrument
tokens, which identify households without the loyalty merge logic. **Q** reproduce the lift → ask what an
identity is → read the merge register → rebuild the spine → compare merged vs never-merged → restate →
decide. **R** entity resolution interacting with survival is two commitments (identity definition and
retroactivity) plus a selection argument. **S** grade retention on the consistent spine, the merge-induced
component, and the budget decision. **T** accept spine reconstruction or the never-merged subset if both
recover the component. **U** low. **V** medium — the "active customer" definition must be pinned.
**W** identity merges silently improving retention is a well-known CRM artefact. **X** family: identity/
entity resolution × time-to-event · variants in telco, banking, healthcare MPI. **Y** not Task02: no
point-in-time feature leakage; the mutable object is the *unit*, not the features. **Z** ADMITTED.

---

## P07 — Margin per order, once the kitchen is already paid for
**C** rapid-delivery unit economics · **D** commercial finance analyst with a DS remit · **E** the
40-site rapid-delivery arm reports −£0.42 contribution per order on fully-allocated costs; the exec
proposal is to close the 12 worst sites. **F** closing 12 sites, £9 m of annualised cost and a strategic
retreat. **G** order-level revenue and picking/dispatch times, site rosters with shift patterns, a
capacity model, site P&Ls with an allocation basis document, a site that added a third shift mid-year, two
sites that closed, delivery-partner contract with tiered rates, the exec proposal deck. **H** (1) the
sites are genuinely loss-making; (2) fixed-cost allocation makes marginal orders look unprofitable;
(3) the tiered courier contract makes cost non-linear in volume; (4) closure would displace, not remove,
demand (cannibalisation into stores); (5) mix (basket size) differs by site. **I** the decision needs the
**incremental** cost and revenue of the marginal order and of a site's closure, not an allocated average;
and the courier tier makes the cost curve kinked. **J** contribution margin under the relevant
counterfactual: marginal order at current volume, and site closure net of demand displacement.
**K** a cost-function estimate exploiting the shift addition and the two closures as natural experiments ·
a bottom-up engineering cost build with the tier schedule · both accepted if they agree. **L** a careful
site-level regression of cost on volume with site fixed effects, yielding a marginal cost per order that
is then compared with revenue — reported as "the true incremental economics". **M** it *is* a marginal
estimate and it is internally consistent; the fixed effects absorb the allocation. **N** ties to the P&L;
marginal cost stable; fit good. **O** the **kink**: estimate the cost curve separately either side of the
courier tier boundary — the pooled slope is a weighted average of two regimes and misprices exactly the
sites near the boundary. Second route: the closed sites' catchments show demand recapture in stores, which
the closure case ignores. **P** the third-shift site as a known-answer experiment: predicted vs actual
incremental cost. **Q** reproduce −£0.42 → separate allocated from incremental → find the tier → estimate
the kinked cost curve → measure displacement at the closed sites → re-rank sites → decide. **R** an
economic object plus a non-linearity plus a counterfactual — three commitments, and the sophisticated
route gets the first right and the other two wrong. **S** grade incremental margin per order at each
site, the tier-boundary effect, the displacement rate, and the closure list. **T** accept the natural-
experiment or engineering-build route. **U** low. **V** medium — the allocation basis document must be
explicit so the agent can tell allocated from incremental. **W** fully-allocated cost driving bad
closure decisions is a classic managerial-accounting failure; tiered logistics contracts are ubiquitous.
**X** family: economic object / non-linear economics · variants in cloud unit costs, freight, manufacturing.
**Y** nothing in the suite touches cost functions or non-linear economics. **Z** ADMITTED.

---

## P08 — The dispatch change that worked in every window
**C** delivery marketplace · **D** experimentation scientist · **E** a switchback test of a new dispatch
policy shows +2.1 % completion rate and the team want a full launch; ops report couriers "chasing" the new
batching behaviour across window boundaries. **F** a platform-wide dispatch change affecting 40 k couriers.
**G** switchback assignment log (30-minute windows, city-level), order and assignment events, courier
session logs, a 3-day pilot with 2-hour windows, the experiment registry, dispatch service code, the
design doc specifying windows, an ops note about courier repositioning. **H** (1) the effect is real;
(2) carryover across windows biases the estimate (couriers reposition and the state persists); (3) the
effect is heterogeneous by supply tightness and the test over-samples slack periods; (4) window boundaries
correlate with demand peaks; (5) a concurrent promo contaminates. **I** switchback validity depends on
**carryover relative to window length**; the state that carries over is courier position, and the
estimator must either use a washout or model the carryover. **J** the policy effect under a design whose
identifying assumption (no carryover beyond the washout) is *tested*, at the decision's time-of-day mix.
**K** switchback difference-in-means with a washout · a carryover-adjusted estimator · the 2-hour-window
pilot as a validity check; accepted if consistent. **L** a careful mixed model on 30-minute windows with
city and time-of-day effects and cluster-robust SEs — a textbook switchback analysis. **M** randomisation
is real, balance is perfect, SEs are conservative, and the effect replicates across cities. **N** balance
on pre-period covariates; effect stable across cities and days; SRM clean. **O** estimate the effect as a
function of **minutes since the last switch**: it ramps, which is carryover, and the first-minutes estimate
is contaminated by the previous policy. Second route: compare with the 2-hour-window pilot — a longer
window implies a larger effect if carryover is present. **P** courier position/state telemetry: an
independent system showing repositioning that persists past the window boundary. **Q** reproduce +2.1 % →
enumerate design threats → test carryover by time-since-switch → compare window lengths → re-estimate with
a washout → reweight to the launch time mix → decide. **R** the wrong route is the *recommended* analysis
for the design; the flaw is a design assumption that the data can test and nobody did. **S** grade the
washout-based effect, the carryover profile, the window-length comparison, and the launch decision.
**T** accept washout or carryover-adjusted estimators. **U** low. **V** medium — the design doc must
state the window length but not the carryover risk. **W** carryover is the central threat in switchback
designs and is discussed in marketplace experimentation practice. **Y** not G05 (staggered adoption, no
randomisation) and not G35 (saturation/interference across units at a point in time); here the threat is
temporal carryover within a randomised design. **X** family: design-validity assumption testing ·
variants in ride-hailing pricing, ad auctions, warehouse slotting. **Z** ADMITTED.

---

## P09 — What the earnings guarantee will cost once couriers know about it
**C** gig economy / workforce incentives · **D** incentives analyst · **E** a pilot guaranteeing £14/hour
in three cities cost £0.31 per delivered order; scaling nationally is budgeted at £4.2 m on that basis.
**F** a £4.2 m commitment that the finance committee will hold the team to. **G** courier session and
earnings logs, the pilot design (city-level, 6 weeks), a supply-forecast model, courier communications
log (when the guarantee was announced, per city), acceptance-rate logs, a second pilot wave with a
different announcement lag, contract terms, the budget paper. **H** (1) the pilot cost generalises;
(2) couriers changed behaviour once they understood the guarantee, so cost rises with awareness
(performativity); (3) the pilot cities have atypical supply; (4) the guarantee interacts with surge, so
cost depends on the demand mix; (5) self-selection of who works guaranteed hours. **I** the treatment
**changes the data-generating process it is evaluated on**: the cost depends on a behavioural response
that grows with awareness, so a 6-week pilot underestimates the steady state. **J** steady-state cost per
order under full awareness and the national supply/demand mix — an extrapolation whose *dynamics* must be
estimated, not an average. **K** dose-response on awareness (announcement timing gives variation) ·
a structural labour-supply response model · the second wave as an out-of-sample test; accepted if
consistent. **L** a careful matched-city synthetic control on cost per order with pre-period fit and
placebo cities, reporting £0.31 with a tight interval. **M** the synthetic control fits beautifully,
placebos are null, and the estimate is precise — it is a good answer to "what did the pilot cost".
**N** pre-period fit; placebo distribution; cost ties to payroll. **O** plot cost per order **against weeks
since announcement**: it is still rising at week 6. Second route: the second wave, with a longer
announcement lag, shows a different trajectory at the same tenure — inconsistent with a static effect.
**P** payroll and acceptance-rate data as an independent check on the behavioural channel.
**Q** reproduce £0.31 → ask whether the pilot is at steady state → find announcement timing → estimate the
trajectory → validate on the second wave → transport to the national mix → budget → decide. **R** three
commitments: estimand (pilot average vs steady state), dynamics, and transport. **S** grade the
steady-state cost, the trajectory parameters, the transported national figure, and the budget decision.
**T** accept dose-response or a structural model with the same implied steady state. **U** low.
**V** medium — "steady state" must be defined by the contract horizon. **W** performative response to
incentive schemes is standard in gig-economy analytics. **X** family: policy feedback / performativity ·
variants in pricing, credit limits, fraud thresholds. **Y** nothing in the suite has a behavioural
response to the intervention. **Z** ADMITTED.

---

## P10 — The media model and the geo test disagree
**C** marketing measurement · **D** marketing scientist · **E** the MMM says paid social ROAS is 3.1 and
the CFO wants to shift £12 m into it; a geo holdout run last quarter implies 1.4. **F** a £12 m budget
shift. **G** MMM code and inputs (spend, impressions, price, distribution, seasonality), the geo-test
design and results, ad platform reported conversions, a CRM conversion log with timestamps, an attribution
config with a 7-day window, a channel-overlap report, the MMM vendor's documentation, finance revenue.
**H** (1) MMM is right and the geo test is underpowered; (2) the geo test is right and MMM suffers
collinearity/omitted-variable bias; (3) the two measure different estimands (short-run geo lift vs MMM's
long-run with adstock); (4) platform-reported conversions double-count across channels, inflating MMM's
response variable; (5) the geo test's control markets were contaminated by national media. **I** the two
numbers are **different objects**: geo-lift measures incremental short-run sales in test markets; the MMM
coefficient measures a modelled long-run response, on a *different conversion source*. Reconciliation
requires making them comparable, not choosing a winner. **J** an incrementality estimate on a stated
horizon and conversion source, with the MMM recalibrated to the experimental result. **K** geo-lift as the
anchor with MMM calibrated to it (priors/constraints) · a Bayesian MMM with the experiment as a prior ·
both accepted if the implied ROAS agrees. **L** a rigorous MMM rebuild: better adstock, saturation curves,
cross-validation, VIF checks — concluding 3.1 is robust and the geo test was noisy. **M** the model is
better than the vendor's, cross-validates well, and the geo interval is wide enough to contain 3.1.
**N** CV error improves; VIF acceptable; holdout fit good; ties to finance revenue. **O** a **placebo
geo test in a pre-period** (markets that were never treated) shows the geo estimator is unbiased, so its
narrower interpretation stands; and re-running the MMM on **CRM conversions** rather than platform
conversions collapses the coefficient — identifying double counting as the mechanism. **P** finance
revenue by market as an independent outcome that neither the platform nor the MMM controls.
**Q** reproduce both → articulate the two estimands → check the conversion source → run the pre-period
placebo → recalibrate MMM to the experiment → state the horizon → decide. **R** two legitimate methods
that disagree, and the resolution is neither "pick one" nor "average"; three commitments (conversion
source, horizon, calibration). **S** grade the calibrated ROAS on the stated horizon, the double-counting
magnitude, the placebo result, and the budget decision. **T** both routes accepted; the graded object is
the reconciled incrementality, not the method. **U** low. **V** high — mitigated by the finance policy
stating the horizon and the conversion source of record. **W** MMM-vs-experiment reconciliation is the
central live debate in marketing measurement. **X** family: reconciling model and experiment · variants in
pricing, churn interventions, promo. **Y** nothing in the suite requires reconciling two legitimate
methods. **Z** ADMITTED (with the ambiguity mitigation mandatory).
