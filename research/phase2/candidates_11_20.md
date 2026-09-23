# Candidate incidents P11–P20

---

## P11 — Interleaving says ship, the A/B says no
**C** search / ranking · **D** relevance scientist · **E** an interleaving experiment prefers ranker R7
in 61 % of impressions; the subsequent A/B shows sessions-per-user down 0.4 %. Launch review is Friday.
**F** shipping or shelving a quarter of ranking work. **G** interleaving logs (team-draft assignment,
click positions), A/B logs, session definitions doc, click and dwell events, a position-bias estimation
job that has not been re-run since the UI changed, a UI release note (results moved down 40 px on mobile),
the ranking eval playbook, a note from the PM urging the interleaving result. **H** (1) interleaving is
right and the A/B is underpowered; (2) interleaving measures *relative* click preference, not the
session-level utility the business cares about; (3) position bias changed with the UI so historical
propensities are stale; (4) R7 wins clicks by promoting clickbait that ends sessions; (5) the A/B has a
novelty effect. **I** the two experiments estimate **different objects under different bias models**, and
the click-propensity model that interleaving relies on is invalid after the UI change. **J** the
session-level utility effect, plus a corrected relative-preference estimate with re-estimated position
bias — and an explicit statement of which object the launch rule is written on. **K** re-estimate position
bias from a randomised-swap stratum · debias interleaving · analyse the A/B at session level with the
right unit; accepted if the corrected interleaving and the A/B agree in sign. **L** a rigorous
interleaving analysis with per-user clustering, sequential-test correction and sensitivity to tie-breaking
— concluding the preference is real and highly significant. **M** it is a correct analysis of the
interleaving data; the significance is genuine; clicks really did move. **N** balance across team-draft
slots; SRM clean; result stable across query segments. **O** the **randomised-swap stratum** reveals the
position-bias curve changed; re-weighting removes most of the preference. Second route: decompose clicks
into "click then return to results" vs "click then end session" — R7's gain is concentrated in the former,
which the session metric penalises. **P** the A/B's downstream revenue and next-day-return metrics, from a
system the ranker does not touch. **Q** reproduce both → articulate the objects → check whether propensities
are current → re-estimate bias → decompose click quality → re-analyse at session level → decide.
**R** the sophisticated route is the *recommended* analysis; the invalidated input (propensity model) is
upstream of it, and three commitments follow (bias model, click-quality decomposition, decision unit).
**S** grade the debiased preference, the position-bias parameters, the session-level effect and the launch
call. **T** accept any debiasing that recovers the bias curve within tolerance. **U** medium — the swap
stratum must be discoverable, not signposted. **V** medium — the launch rule must name its metric.
**W** position-bias drift after UI change, and click-vs-session divergence, are standard ranking-eval
problems. **X** family: metric validity under a changed observation process. **Y** not G24: no off-policy
estimation; the failure is a stale bias model plus two objects. **Z** ADMITTED.

---

## P12 — Engagement is up, nothing downstream moved
**C** recommendations / product analytics · **D** growth data scientist · **E** a new "because you watched"
carousel lifts engagement (items started per session +7.2 %, p < 0.001) but 8-week retention is flat; the
launch gate is written on retention and the team propose shipping on the engagement proxy "since retention
is underpowered". **F** shipping a surface that may be neutral or negative for retention, and setting a
precedent for proxy-based gates. **G** experiment logs with 12 weeks of exposure, a surrogate-validation
study from two years ago, metric definitions, a proxy-metric charter, previous launches with both
short-term and long-term outcomes recorded, session/identity definitions, a note from the PM.
**H** (1) engagement is a valid surrogate and retention is noisy; (2) the surrogate relationship has
changed since validation; (3) the carousel shifts *which* content is consumed, breaking the surrogate's
assumption; (4) retention is diluted by a population the carousel never reaches; (5) an interference
effect through shared recommendation training data. **I** **surrogate validity is an empirical property
that can be tested on the platform's own launch history**, and it is conditional on the mechanism of the
change. **J** the effect on the gate metric, plus a defensible statement of surrogate validity for *this
class of change* — i.e. the predictive relationship estimated on comparable historical launches.
**K** surrogate-index estimation on past launches (Prentice-style criteria or a meta-analytic surrogate
index) · restricting to reached users to raise power · a sequential/Bayesian retention analysis;
accepted if the conclusion about the gate is the same. **L** a careful surrogate-index analysis: regress
long-term retention on short-term engagement across historical experiments, get a strong relationship,
and translate +7.2 % engagement into a predicted +0.9 % retention with a confidence interval.
**M** the historical relationship is real and strong, the regression is well specified, and the
translation is the textbook surrogate-index method. **N** historical fit is good; the prediction interval
is reported; the engagement effect is unambiguous. **O** **split the historical launches by mechanism**:
for changes that alter *content mix* rather than *content volume*, the surrogate relationship is flat or
negative. The current change is in the first class. Second route: restrict the current experiment to users
the carousel actually reached, which raises power enough to bound retention away from +0.9 %.
**P** a long-running holdback cohort that has never seen any of the last year's surfaces — an
independent estimate of cumulative long-run effect. **Q** reproduce both → ask whether the proxy is valid
here → validate the surrogate on comparable launches → stratify by mechanism → bound the gate metric →
decide. **R** the wrong route is a sophisticated, defensible method whose assumption (surrogate
transportability across change classes) is testable in-workspace; three commitments (surrogate validity,
population, gate object). **S** grade the surrogate coefficient by mechanism class, the reached-user
retention bound, and the gate decision. **T** accept surrogate-index or direct-power routes if the gate
conclusion matches. **U** low. **V** medium — the charter must state when a proxy may substitute.
**W** proxy metrics mispredicting long-term outcomes is among the most documented experimentation
hazards. **X** family: proxy/surrogate validity · variants in ads, education, health. **Y** new: nothing
in the suite tests whether a metric is a valid stand-in for the decision's outcome. **Z** ADMITTED.

---

## P13 — The limit increase that only looks safe on the accounts we approved
**C** consumer credit · **D** credit risk scientist · **E** a model says raising limits for "low-risk"
accounts adds £8 m revenue at +0.3 pp loss; policy requires the loss estimate to be defensible for the
whole eligible population. **F** a limit-increase programme across 400 k accounts. **G** decision logs with
policy version and score cut-off, bureau pulls with as-of stamps, a **random-approval stratum** (2 % of
declines historically approved for exactly this purpose), account performance, a champion/challenger
registry, credit policy with the eligible definition, a prior limit-increase pilot, the model's training
snapshot. **H** (1) the estimate is right; (2) outcomes exist only for accounts the policy already
approved (selective labels), so the risk model is fitted on a censored population; (3) limit increases
change behaviour (utilisation and default both respond); (4) the eligible population has drifted since
training; (5) the prior pilot's effect has been extrapolated beyond its limit range. **I** two stacked
issues: **selective labels** (who has an outcome) and **performativity** (the treatment changes the
outcome). The naive analysis conditions on approval and ignores the treatment's own effect. **J** expected
loss under the proposed policy for the eligible population, incorporating the limit's causal effect on
default, with the selection mechanism addressed. **K** the random-approval stratum as a design-unbiased
anchor · reject inference with an explicit, testable assumption · the pilot's dose-response for the causal
limit effect; accepted if consistent. **L** a well-executed reject-inference exercise: parcelling,
reweighting, a bivariate probit with a plausible exclusion restriction, and a calibrated PD that validates
on the approved book. **M** it validates beautifully **on approved accounts**, the reweighting is principled,
and the PD is calibrated where data exist. **N** calibration and discrimination on the approved book;
score distributions align; policy version accounted for. **O** the **random-approval stratum**: PD there is
materially higher than the reject-inferred estimate, and the gap is concentrated exactly in the band the
programme targets. Second route: within the pilot, default rises with the granted limit at fixed score —
the model treats limit as exogenous. **P** the challenger arm's realised losses, from a system the model
does not feed. **Q** reproduce the estimate → notice outcomes are policy-conditional → find the random
stratum → re-estimate → separate the causal limit effect using the pilot → recombine → decide.
**R** two stacked mechanisms and three commitments; the sophisticated route is exactly what a good credit
team does and is still wrong because a design-unbiased sample exists and was not used. **S** grade PD on
the eligible population, the limit dose-response, the programme loss figure and the go/no-go.
**T** accept the random stratum or a correctly assumption-checked reject-inference that reproduces it.
**U** low. **V** medium — the eligible population must be defined in policy. **W** selective labels and
random-approval strata are standard credit-risk practice. **X** family: multi-stage selection +
performativity · variants in insurance underwriting, admissions, hiring. **Y** not G24: no logging
propensity or OPE; the selection is a policy and the object is a loss rate under a counterfactual policy.
**Z** ADMITTED.

---

## P14 — We cannot see the fraud we blocked
**C** payments fraud · **D** fraud analytics lead · **E** after tightening the score threshold, measured
fraud losses fell 22 % and the reported precision of the screen rose; the team propose tightening again.
**F** a threshold change worth ~£3 m of prevented loss against an unknown volume of declined good
customers. **G** screening decisions with scores and policy versions, manual review queue outcomes, a
**random-release stratum** (0.5 % of high-score transactions released deliberately), chargeback records with
network timing rules, customer complaint/appeal log, an acquirer report, review SOP with the sampling
design, a prior threshold change. **H** (1) tightening genuinely reduced fraud; (2) blocked transactions
generate no chargebacks, so measured loss falls by construction (missing labels); (3) fraudsters
substituted to another channel (displacement); (4) chargeback maturation lags mean recent months are
incomplete; (5) good-customer decline cost is unmeasured and rising. **I** **the metric is defined on the
population the policy allows to exist**, plus a maturation lag; both make the post-change number
non-comparable. **J** fraud rate and false-positive cost on a *fixed* population definition, corrected for
chargeback maturation, and the net economics of a further tightening. **K** random-release stratum for
the counterfactual fraud rate among blocked traffic · chargeback development (triangle) for maturation ·
displacement check across channels; accepted if consistent. **L** a careful precision/recall and
cost-curve analysis on reviewed transactions with maturation-adjusted labels and bootstrap intervals,
concluding the tighter threshold dominates. **M** the maturation adjustment is right, the reviewed sample
is large, and the cost curve is smooth and convincing. **N** labels reconcile to the acquirer report;
maturation curve fits; costs tie to finance. **O** the **random-release stratum** gives the fraud rate
among transactions the policy would have blocked — it is far lower than the model implies in the marginal
band, so the marginal decline is mostly good customers. Second route: appeals/complaints per thousand
declines rise sharply at the new threshold. **P** the acquirer's own fraud-to-sales ratio, computed on
attempted rather than approved volume. **Q** reproduce the 22 % → ask what changed in the denominator →
maturation-adjust → use the random stratum for blocked traffic → price the false-positive cost →
optimise the threshold → decide. **R** three commitments (population, maturation, cost object) and a
decision that is an optimisation, not a comparison. **S** grade the counterfactual fraud rate in the
marginal band, the maturation-adjusted loss, the false-positive cost, and the threshold. **T** accept any
route that recovers the marginal-band rate. **U** low. **V** medium — the cost of a false decline must be
given by policy. **W** "we can't measure what we blocked" is the defining problem of fraud analytics;
random-release strata are real practice. **X** family: policy-induced missing labels · variants in
moderation, security alerting, insurance fraud. **Y** distinct from P13 (there: approval selection with a
causal treatment effect; here: label censoring plus maturation plus a false-positive economics object).
**Z** ADMITTED.

---

## P15 — Every issuer is fine but the total fell
**C** payments · **D** payments analytics · **E** authorisation approval rate fell 1.9 pp after a routing
change; per-issuer approval rates are flat or improved. The vendor says the routing change is innocent.
**F** reverting a routing change worth £1.1 m of annual fee savings, or accepting a real revenue loss.
**G** authorisation logs with issuer/BIN, routing decisions and versions, a routing config with a
percentage ramp, retry logic, 3-D Secure step-up flags, network response codes with a documented code
remapping, merchant category mix, an incident log entry about a partial outage, the vendor's report.
**H** (1) the routing change hurts; (2) composition shifted — traffic moved toward issuers with lower
baseline approval (Simpson); (3) retry behaviour changed so the *denominator* of "attempts" changed;
(4) a response-code remapping reclassified soft declines; (5) the outage window contaminates.
**I** a **compositional and denominator** problem: the aggregate is a mix-weighted average, and the
routing change *causes* the mix shift, so naive stratification (conditioning on issuer) also answers the
wrong question — the decision needs the total effect including composition. **J** the total effect of the
routing change on approved value per attempted transaction, decomposed into within-issuer and
between-issuer components, on a consistent attempt definition. **K** a Kitagawa–Oaxaca-style decomposition ·
the ramp as a natural experiment (dose-response on the routed share) · a retry-aware attempt definition;
accepted if consistent. **L** a careful stratified analysis: approval rate by issuer, weighted to a fixed
base period mix, with confidence intervals — concluding the routing change is neutral because every
stratum is flat. **M** it is a correct mix-adjusted comparison, and mix adjustment is exactly what one
teaches for Simpson's paradox. **N** each stratum reconciles; weights sum; totals tie to the network file.
**O** the **ramp**: approval falls monotonically with the routed share *within* issuer once retries are
counted as one attempt — because the change alters retry paths, and the fixed-mix adjustment removed the
very channel through which the effect operates. Second route: the code remapping is exposed by counting
distinct raw codes before/after on unrouted traffic. **P** settled value from the acquirer's ledger per
attempted basket — an independent outcome insensitive to attempt definitions. **Q** reproduce the drop →
stratify → notice the paradox → ask what the decision needs (total, not within) → fix the attempt
definition → use the ramp → decompose → decide. **R** the sophisticated route is the standard remedy for
the surface problem and is wrong because the mediator was adjusted away; three commitments (attempt unit,
total-vs-direct effect, code mapping). **S** grade the total effect, the decomposition, the retry-adjusted
series and the revert decision. **T** accept decomposition or dose-response routes. **U** low.
**V** medium — "approval rate" must be defined in the merchant agreement. **W** Simpson's paradox in
authorisation analytics and retry-inflated denominators are both well documented in payments practice.
**X** family: compositional effects and mediator adjustment · variants in ads auctions, ops routing.
**Y** new to the suite: the trap is *over*-adjustment, not under-adjustment. **Z** ADMITTED.

---

## P16 — The payment plan that works because we offer it to people who were going to pay
**C** collections / lending operations · **D** collections analytics · **E** accounts offered a hardship
payment plan cure at 61 % vs 38 % for non-offered; the proposal is to offer it to everyone in early
delinquency. **F** an operational change across 90 k delinquent accounts and a provisioning assumption.
**G** collections contact and treatment log, agent notes and offer eligibility rules, a **randomised pilot**
on 5 % of the queue three months ago, payment history, bureau refresh, the treatment playbook (which says
agents offer plans to accounts that "engage"), call-centre routing rules, a QA sample.
**H** (1) the plan causes cure; (2) agents offer it to accounts already likely to cure (selection on
engagement); (3) offering is correlated with contactability, which itself predicts cure; (4) the effect is
heterogeneous by balance and only positive for small balances; (5) plan acceptance is the real treatment,
not the offer. **I** treatment assignment is **endogenous to the outcome's strongest predictor** and is
partly recorded only in free-text agent notes; and offer-vs-acceptance are two different estimands
(ITT vs treatment-on-treated). **J** the ITT effect of *offering* the plan in the operational population,
and the acceptance-conditional effect, on a stated horizon. **K** the randomised pilot as the anchor ·
propensity or doubly-robust adjustment on contactability, engagement and balance · an instrumental-variable
route using agent-shift offer propensity; accepted if they agree. **L** a rigorous doubly-robust estimate
with a rich propensity model (bureau, balance, delinquency stage, contact count) and good overlap
diagnostics, reporting +14 pp with tight bounds. **M** overlap looks fine, balance is achieved on all
observed covariates, and the estimator is state-of-the-art. **N** covariate balance post-weighting;
positivity satisfied; sensitivity to trimming small. **O** the **randomised pilot**: the ITT effect is
+4 pp, not +14. The unobserved driver (what the agent heard on the call, recorded only in notes) is not in
the propensity model, and a placebo outcome — cure *before* the offer date — is already "improved" by the
weighting, which is impossible for a causal effect. **P** the pilot's own pre-registered readout and a
post-pilot period. **Q** reproduce +23 pp raw → adjust → get +14 → look for a randomised subset → find the
pilot → discover the gap → run the pre-offer placebo → conclude unobserved selection → report ITT and TOT
→ decide. **R** the wrong route is a modern causal-ML answer defeated by unobserved confounding that the
workspace can demonstrate; three commitments (estimand, population, selection). **S** grade the ITT
effect, the TOT effect, the placebo-outcome diagnostic and the rollout decision. **T** accept the pilot,
or an adjustment route that reproduces it and reports the placebo. **U** low. **V** medium — the playbook
must make eligibility discretionary but not state that it depends on engagement. **W** selection into
collections treatments by agent discretion is a standard evaluation problem. **X** family: endogenous
treatment assignment with a randomised anchor · variants in sales outreach, care management, retention offers.
**Y** not G05: no staggered adoption or trends; the threat is unobserved selection and the diagnostic is a
placebo outcome. **Z** ADMITTED.

---

## P17 — The default rate improved the month we changed what default means
**C** credit risk / regulatory reporting · **D** risk reporting analyst · **E** the 12-month default rate
fell from 4.1 % to 3.2 % and IFRS 9 stage-2 migrations dropped, releasing provision; the change coincides
with a policy amendment implementing a new definition of default (unlikeliness-to-pay criteria and a
materiality threshold). **F** a provision release of £22 m that the audit committee must sign.
**G** account ledgers, delinquency history at day-level, the credit policy with dated amendments, a
mapping note for the new definition, the staging engine config with version history, a parallel-run period
where both definitions were computed, forbearance flags, the provision model, audit committee papers.
**H** (1) credit quality improved; (2) the definition change mechanically reduces measured default;
(3) forbearance re-ageing hides delinquency; (4) portfolio mix shifted toward newer, unseasoned vintages
(seasoning); (5) a collections process change pulled cures forward. **I** the series is a **spliced
measurement** across two definitions, and the change interacts with **vintage seasoning**, so a like-for-like
comparison needs both a definitional bridge and a cohort view. **J** the default rate on a single
definition, on a seasoning-adjusted cohort basis, and the provision implication of each component.
**K** the parallel-run period to bridge definitions · vintage/cohort curves to remove seasoning ·
a decomposition into definition, mix and genuine-quality components; accepted if they agree.
**L** a careful vintage analysis: cohort default curves by origination month, correctly aligned on months
on book, showing genuinely better curves for recent cohorts. **M** the cohort analysis is the right remedy
for seasoning, the curves are cleanly separated, and the improvement persists at equal months-on-book.
**N** cohort curves monotone; ties to the ledger; provisions reconcile. **O** the **parallel-run period**:
on the same accounts, the two definitions differ by ~0.7 pp, and the cohort curves were computed on the new
definition for recent cohorts and the old one for older cohorts — the "improvement at equal seasoning" is
the splice. Second route: forbearance-flag prevalence rose, and excluding re-aged accounts removes most of
the residual. **P** cash collections per pound of balance — an economic outcome insensitive to the
definition. **Q** reproduce the improvement → enumerate definition/seasoning/forbearance → find the
parallel run → bridge → rebuild cohorts on one definition → decompose → decide. **R** two measurement
issues that *interact*, and the sophisticated route fixes one while silently inheriting the other.
**S** grade the bridged default rate, the decomposition, the provision impact and the sign-off decision.
**T** accept bridge-then-cohort or a joint decomposition. **U** low. **V** low — the policy amendment fixes
the definitions. **W** definition-of-default changes and their provision impact are a live regulatory
topic. **X** family: measurement/definition change × cohort dynamics · variants in healthcare coding,
safety reporting, churn definitions. **Y** distinct from P03 (instrument change with an overlap) because
the mechanism interacts with seasoning and the bridge alone is insufficient. **Z** ADMITTED.

---

## P18 — The return-visit rate that rose without any patients returning more
**C** healthcare operations · **D** quality analytics lead · **E** the 30-day return-visit rate rose from
7.8 % to 9.6 % across the network, breaching a payer quality threshold; the clinical director insists
nothing changed in practice. **F** a payer quality penalty and a remediation programme, plus reputational
reporting. **G** patient administration records, clinical coding with a dated guidance revision, the payer
measure specification (with its own dated amendment), referral pathways, a **re-coded validation sample**
(200 encounters coded under both guidance versions by the audit team), clinic-level volumes, an EHR upgrade
note, case-mix data. **H** (1) care quality deteriorated; (2) the coding-guidance revision moved encounters
into the numerator; (3) the measure's denominator changed (index-visit attribution); (4) case-mix shifted
toward higher-risk referrals; (5) an EHR upgrade changed how follow-ups are recorded, creating duplicates.
**I** numerator **and** denominator are defined by codes whose guidance changed, and the payer measure's
own amendment changed attribution; a genuine-change estimate requires both to be held fixed.
**J** the return-visit rate on a single, fixed specification (numerator, denominator, attribution) and the
decomposition of the observed rise into coding, attribution, case-mix and genuine components.
**K** the re-coded validation sample as a bridge · a fixed-specification recomputation from raw encounters ·
risk-adjusted comparison for case-mix; accepted if the decomposition agrees. **L** a careful risk-adjusted
analysis: hierarchical logistic model with clinic random effects and patient risk covariates, concluding
the rise survives adjustment and is therefore real. **M** the risk adjustment is appropriate, the model is
well diagnosed, and the rise persists after adjustment — exactly the argument a quality team would make.
**N** observed-vs-expected calibrates; clinic effects shrink sensibly; volumes tie. **O** the **re-coded
sample**: under the old guidance the same encounters give a materially lower numerator, and the
adjustment cannot remove a numerator definition change. Second route: duplicate-encounter detection after
the EHR upgrade explains a further part. **P** patient-reported follow-up contact from the PRO survey — an
independent measurement of the underlying behaviour. **Q** reproduce the rise → enumerate definition vs
behaviour → find the re-coded sample → bridge numerator and denominator → detect duplicates → risk-adjust
the residual → decide. **R** two definitional layers plus a data-quality layer; the sophisticated route is
the standard quality-measurement method and does not touch the definitions. **S** grade the
fixed-specification rate, the four-way decomposition and the penalty exposure. **T** accept any bridge that
recovers the coding component. **U** low. **V** medium — the payer specification must be authoritative.
**W** coding-guidance and measure-specification changes are a recurrent cause of apparent quality shifts.
**X** family: definitional change in a regulated metric · variants in safety incident rates, ESG
reporting, education outcomes. **Y** new domain and new mechanism for the suite. **Z** ADMITTED.

---

## P19 — Site C looks worse because of who it treats
**C** healthcare operations · **D** operations scientist · **E** a site-performance review ranks clinic C
worst on 90-day functional-recovery outcomes; the proposal is to move complex referrals away from C.
**F** redirecting referrals for ~4,000 patients a year and a leadership change at C.
**G** patient administration, referral source and triage acuity, procedure codes, outcome measures with
completion flags (**PRO response is 71 % and differential by acuity and site**), clinician rosters, a
regional referral policy that sends complex cases to C, a natural experiment (a neighbouring provider
closed for 5 months, redirecting case mix), risk-adjustment model documentation.
**H** (1) C performs worse; (2) confounding by indication — C treats more complex cases;
(3) **outcome missingness is differential** (sicker patients answer less), so observed outcomes are
selected; (4) clinician mix rather than site; (5) the outcome measure was administered differently at C.
**I** two selection layers stack: **who is referred** and **who responds**. Risk adjustment addresses the
first and *cannot* address the second; and the decision needs a transported estimate for the
population that would be redirected. **J** site effect on outcome for a defined population, with
missing-outcome mechanism handled, and the effect transported to the referral population the decision
moves. **K** inverse-probability-of-response weighting or multiple imputation with an auxiliary predictor ·
the provider-closure period as a natural experiment · a sensitivity analysis over MNAR assumptions;
accepted if consistent. **L** a thorough risk-adjusted hierarchical model with acuity, comorbidity, age
and procedure fixed effects and a site random effect, reporting C's adjusted outcome as significantly
worse with a well-calibrated observed-vs-expected. **M** the risk adjustment is state-of-the-practice,
calibration is good, and the site effect survives every covariate the team has. **N** O/E calibration;
covariate balance; shrinkage sensible; volumes tie. **O** **response propensity**: modelling who answers
shows C's non-responders are systematically sicker; IPW-adjusted outcomes move C toward the middle. And
the **closure natural experiment** gives C a period with a different mix — its outcomes track the mix,
not the site. **P** an administrative outcome with complete capture (re-operation or emergency
readmission) that does not depend on survey response. **Q** reproduce the ranking → adjust for mix →
notice response rates differ → model response → re-weight → use the closure period → transport to the
redirect population → decide. **R** two stacked selection mechanisms with only one addressable by
covariate adjustment; three commitments (population, missingness, transport). **S** grade the
response-weighted site effects, the closure-period estimate, the transported effect and the referral
decision. **T** accept IPW, imputation or the natural experiment if the site ordering and magnitude agree.
**U** low. **V** medium — must state which population the decision applies to. **W** differential PRO
response and confounding by indication are the two standard objections to provider league tables.
**X** family: stacked selection + transport · variants in education, employment programmes, insurance.
**Y** distinct from G05: no staggered treatment; the mechanisms are missingness and transport.
**Z** ADMITTED.

---

## P20 — The no-show model got worse at exactly the moment we started using it
**C** healthcare operations · **D** applied scientist · **E** a no-show model deployed to drive reminder
calls has seen AUC fall from 0.78 to 0.66 in six months; the vendor blames data drift and proposes
retraining on recent data. **F** a decision to retrain, replace, or change the reminder policy, affecting
clinic utilisation worth £3 m. **G** appointment records, model scores and versions, the reminder-policy
engine (call the top 20 % of scores, with a documented ramp), call outcome logs, a **holdback clinic set**
(10 % never received score-driven reminders), patient contact history, monitoring dashboards with drift
alarms, the vendor's monitoring report, an upstream feature backfill note.
**H** (1) genuine population drift; (2) **the policy changed the outcome the model predicts** — reminded
patients attend, so the model's own successes destroy its measured discrimination (performativity);
(3) label leakage removed by a pipeline fix, so the earlier AUC was inflated; (4) the upstream backfill
changed a feature's historical values, making the training-time and serving-time distributions differ;
(5) case-mix change from a new referral source. **I** the evaluation population and the outcome are both
**endogenous to the model's deployment**; measured AUC conflates model degradation with policy success.
**J** model discrimination on a policy-invariant population (the holdback), the causal effect of reminders,
and the decision of whether to retrain — plus the value of the current policy.
**K** holdback-set evaluation · a policy-aware decomposition (predicted vs realised no-show under
treatment) · a feature-vintage audit to test the backfill hypothesis; accepted if consistent.
**L** a rigorous drift analysis: PSI/KS on every feature, a temporal cross-validation showing degradation,
and a retrained model that restores AUC 0.77 on recent data. **M** drift metrics are elevated, the
degradation is monotone in time, and retraining demonstrably fixes the metric — a textbook MLOps
response. **N** PSI thresholds; retrained model validates on a recent holdout; monitoring reconciles.
**O** the **holdback clinics**: AUC there is still 0.77, so the model has not degraded — the treated
population's outcomes changed. And the retrained model, evaluated on the holdback, is *worse*, because it
learned the policy's footprint. Second route: a feature-vintage replay shows the backfill altered training
values only, explaining part of the gap. **P** the reminder-call effect estimated from the holdback
contrast — an independent quantity that tells you the policy is working. **Q** reproduce the drop →
enumerate drift vs policy feedback → find the holdback → evaluate there → compare retrained model on
holdback → audit the backfill → decide (do not retrain; change the monitoring) → repair.
**R** the sophisticated route is the industry-standard remedy and makes the system worse; three commitments
(evaluation population, outcome under treatment, feature vintage). **S** grade holdback AUC, the treated-
population decomposition, the backfill component, and the retrain/no-retrain decision. **T** accept
holdback evaluation or a policy-aware correction that reproduces it. **U** low — the holdback must be
discoverable from the policy engine config, not named in the prompt. **V** medium. **W** performativity
in deployed risk models, and "retraining on policy-contaminated data", are documented MLOps hazards.
**X** family: policy feedback on evaluation · variants in credit, fraud, churn saves, maintenance.
**Y** distinct from Task02 (leakage in *features*) — here the *labels and population* are policy-induced,
and the wrong action is retraining. **Z** ADMITTED.
