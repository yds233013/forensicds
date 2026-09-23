# Candidates P33–P36 — added from the production-failure research (each has a documented instance)

## P33 — The savings the meter never saw
**C** energy efficiency / utility programme evaluation · **D** programme evaluation analyst · **E** the
residential weatherisation programme reports 24 % energy savings from a deemed engineering model and a
pre/post billing analysis; the regulator will credit the savings as an avoided-capacity resource.
**F** programme funding, avoided-capacity credit in the resource plan, and rate-case cost recovery.
**G** billing histories for participants and non-participants, enrolment dates and channel, the engineering
model's inputs and outputs per home, weather data, an **oversubscribed cohort with a waiting list assigned
by application order** (a quasi-random encouragement design), audit/inspection records, the programme's
M&V protocol, the resource-plan credit rule. **H** (1) savings are real at 24 %; (2) the engineering model
overstates because behaviour differs from assumptions (rebound, partial use); (3) **selection** — households
enrol after an anomalously high-bill year, so pre/post captures regression to the mean; (4) weather
normalisation is mis-specified; (5) installation quality varies. **I** two independent biases point the same
way: **regression to the mean from enrolment timing**, and a deemed model treated as a measurement.
**J** realised savings against a valid counterfactual, decomposed into engineering-model error and selection,
with the resource-plan credit implied. **K** the waiting-list/encouragement design as the primary estimate ·
a matched comparison with a pre-registered fixed baseline period · a weather-normalised model with an
explicit RTM control; accepted if consistent. **L** a careful weather-normalised pre/post analysis
(HDD/CDD, home fixed effects, a non-participant control for the *weather* term only) reporting 19 % savings
"after normalisation". **M** the normalisation is textbook, the fit is excellent, and it is *lower* than the
deemed figure, which reads as conservatism. **N** HDD/CDD fit; ties to billed volume; non-participant weather
term sensible. **O** compare participants' **pre-enrolment year against their own prior years**: it is
anomalously high, so part of the "saving" is reversion. Then the **waiting-list cohort** gives a
counterfactual that removes it, and the realised saving is a fraction of the deemed one. **P** the
waiting-list cohort's realised consumption. **Q** reproduce 24 % → find the enrolment trigger → test for RTM
→ find the waiting list → estimate → decompose deemed vs realised → restate the capacity credit → decide.
**R** three commitments (counterfactual, RTM, credit object). **S** grade realised savings, the RTM
component, the deemed-model error and the capacity credit. **T** encouragement-design or matched routes.
**U** low. **V** low. **W** **documented**: Fowlie, Greenstone & Wolfram (QJE 133(3):1597), RCT over ~30,000
Michigan households — model-projected savings ≈ **2.5×** realised, upfront costs ≈ 2× realised savings.
**X** family: deemed-vs-realised, and RTM from self-selected enrolment. **Y** new mechanism (RTM from
enrolment timing) and new domain. **Z** ADMITTED.

## P34 — Savings on the slide, not in the ledger
**C** procurement / FP&A · **D** procurement analytics lead · **E** the category team reports £31 m of
annualised savings; total addressable spend is flat. **F** the efficiency programme's credibility, next
year's budget, and incentive comp. **G** the savings register with per-initiative baselines and methods,
purchase-order and invoice history, contract price schedules, volume and mix data, the general ledger by
cost centre, a category-manager scorecard definition, a finance memo on how savings must be evidenced.
**H** (1) savings are real and offset by volume growth; (2) baselines are counterfactual (list price, prior
quote) and were never paid; (3) one-off timing gains annualised; (4) double counting across initiatives and
years; (5) price effect swamped by mix. **I** the reported quantity is a **counterfactual against a baseline
that must itself be validated**, and the decomposition of spend change into price, volume and mix is the
only way to reconcile it to the ledger. **J** realised recurring price effect, tied to the ledger,
decomposed from volume and mix, net of double counting. **K** a Laspeyres/Paasche-style price-volume-mix
decomposition on like-for-like SKU-supplier pairs · initiative-level ledger tracing · duplicate detection;
accepted if they reconcile. **L** a rigorous like-for-like unit-price comparison per SKU-supplier showing a
genuine weighted average price reduction of 4.1 %, presented as validated savings. **M** it is a real price
reduction, computed correctly on matched pairs, and it ties to the contract schedules. **N** matched pairs
reconcile; weighted average price down; contracts agree. **O** apply the price effect to **realised
volumes** and reconcile to the ledger: most of the register's value is on initiatives whose baseline was a
quote, or on volumes that did not materialise; and a duplicate scan shows two initiatives claiming the same
supplier-category. **P** the general ledger. **Q** reproduce £31 m → decompose price/volume/mix → validate
baselines → trace to the ledger → strip one-offs and duplicates → restate → decide. **R** three commitments
(baseline validity, decomposition, recurrence). **S** grade the recurring price effect, the PVM
decomposition, the double-counted amount and the restated figure. **T** any decomposition that reconciles.
**U** low. **V** medium — the finance memo must define what counts as a saving. **W** **documented**: NAO —
of DfT's reported **£892 m**, 43 % fairly represented realised cash savings and **35 % possibly overstated**;
Home Office 17 % with significant concerns. **X** family: counterfactual baselines and ledger
reconciliation. **Y** new: the only candidate whose object is a counterfactual *baseline* rather than an
effect or a rate. **Z** ADMITTED.

## P35 — The drives that never failed because they left first
**C** infrastructure reliability · **D** reliability analyst · **E** a vendor's drive model shows an annualised
failure rate of 0.31 % against a fleet average of 1.4 %, and the procurement team want to standardise on it.
**F** a £12 m procurement commitment and the spares/replacement schedule. **G** current-state telemetry
(SMART, in-service drives), the asset register including **decommissioned** units with exit reason codes,
procurement and deployment dates, RMA records, a firmware-update log, pod/enclosure metadata, a
minimum-exposure rule in the reliability SOP. **H** (1) the model is genuinely better; (2) **survivorship** —
weak units were pulled early and left the queryable population; (3) exposure is too small for the estimate
(drive-days, not drive counts); (4) the model is deployed in cooler/lighter-duty enclosures (confounding);
(5) a firmware fix mid-life changes the hazard. **I** the population an analyst can query is the population
that survived, and **exit is correlated with the outcome**; the denominator must be exposure, not units.
**J** the cause-specific failure hazard per drive-day over the full cohort including exits, with exit as a
competing event, and the procurement implication. **K** full-cohort reconstruction from the asset register ·
survival analysis with exit as a competing risk · exposure-weighted AFR with a minimum-exposure rule;
accepted if consistent. **L** a careful exposure-weighted AFR using drive-days from the telemetry warehouse,
with Poisson confidence intervals and enclosure stratification. **M** it corrects the obvious error (counts
vs drive-days), the intervals are honest, and the stratification handles the confounder. **N** drive-days
tie to telemetry; intervals computed; enclosure strata balanced. **O** join the **asset register's
decommissioned units**: a material share exited with failure-adjacent reason codes that never reached the
telemetry warehouse, and the model's advantage collapses. Second route: the **minimum-exposure rule** in the
SOP disqualifies the model's estimate entirely at its current drive-days. **P** RMA records from the vendor —
an independent system. **Q** reproduce 0.31 % → ask what the queryable population is → find exits →
reconstruct the cohort → model exit as a competing risk → apply the exposure rule → decide. **R** three
commitments (population, denominator, competing exit). **S** grade the full-cohort hazard, the
survivorship component, the exposure sufficiency verdict and the procurement decision. **T** any full-cohort
route. **U** low. **V** low. **W** **documented**: Backblaze Drive Stats publishes a **50,000 drive-day**
minimum for statistical relevance and documents zero-failure small-cohort models; Wald's WWII armour
analysis is the canonical statement. **Y** distinct from G34: the mechanism is *which units are in the
warehouse at all*, not competing events among observed units. **X** family: survivorship in current-state
systems. **Z** ADMITTED.

## P36 — Our customers are erratic (they are not)
**C** manufacturing / upstream supply planning · **D** supply-planning data scientist · **E** order variance
from the distributor channel has a coefficient of variation of 0.62, justifying a £7 m capacity buffer and a
safety-stock increase; the consumer-offtake series is smooth. **F** a £7 m capacity investment and echelon
safety-stock policy. **G** customer order history, POS/consumer-offtake data shared by two large customers,
the promotional calendar, order-minimum and case-pack rules, an allocation/rationing log from a shortage
period, lead-time records, the S&OP deck proposing the buffer. **H** (1) end demand is volatile;
(2) **bullwhip** — variance is manufactured by ordering policy (batching, order minimums, forecast updating,
promotion, rationing) not by consumption; (3) a customer's inventory-policy change (one-off restock);
(4) lead-time variability misread as demand variability; (5) mix shift across SKUs. **I** the series the
planner models as demand is an **order stream generated by a policy**, and the variance can be attributed to
its sources; the right buffer depends on which echelon the variance originates in. **J** the variance
decomposition by source (consumption, batching/minimums, promotion, rationing) and the buffer implied at the
correct echelon. **K** variance-ratio analysis level by level against POS · alignment of order spikes with
promotion and allocation events · a simulation of the ordering policy to reproduce the observed CV; accepted
if consistent. **L** a careful ARIMA/state-space model of the order series with promotional regressors,
producing a well-calibrated predictive interval and a statistically defensible safety-stock level.
**M** the model fits, the intervals are calibrated *on the order series*, and the promotional regressors are
significant. **N** in-sample and out-of-sample fit; interval coverage on orders; ties to shipments.
**O** compare the **variance ratio against POS** level by level: consumption CV is a fraction of order CV,
and the order spikes align with **order minimums and the rationing log**, not with consumption. A simulation
of the customer's reorder policy driven by the *smooth* POS series reproduces the observed CV — which
falsifies "end demand is volatile". **P** the customers' POS data — an independent system upstream of the
ordering policy. **Q** reproduce CV 0.62 → obtain POS → compute variance ratios → align spikes with policy
events → simulate the policy → attribute variance → size the buffer at the right echelon → decide.
**R** three commitments (what the series is, variance attribution, echelon). **S** grade the variance
decomposition, the consumption-level CV, the simulated policy CV and the buffer decision. **T** variance-
ratio or simulation routes. **U** low. **V** medium — the buffer policy must state which echelon it protects.
**W** **documented**: Lee, Padmanabhan & Whang (*Sloan Management Review* 38(3) 1997; *Management Science*
43(4):546) — P&G Pampers, steady consumer offtake with variance amplifying to the largest swings in P&G's
own orders. **Y** new: the failure is that the modelled series is an artefact of a policy, which nothing in
the suite covers. **X** family: policy-generated data mistaken for exogenous demand. **Z** ADMITTED.
