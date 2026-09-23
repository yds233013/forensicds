# Candidates P31–P32 — added because of the external benchmark review

Two gaps the review made unavoidable. **P31** exists because a suite in which the published number is
always wrong is gamed by always disagreeing (BAITBENCH's lesson generalised: measure discrimination, not
contrarianism). **P32** exists because exactly one benchmark reviewed (CausalDS) scores abstention, and no
data-agent benchmark scores "these data cannot answer that question; here is the experiment that would".

---

## P31 — The complaint that was wrong
**C** retail supply chain / commercial · **D** demand-science analyst · **E** the commercial director
escalates that the forecasting team's service-level report is "obviously wrong": it claims 97.1 % fill rate
for a category in which three key accounts have logged shortfalls, and he has a supplier's own report
showing 92 %. He wants the metric rebuilt and the team's bonus gate reviewed. **F** a bonus gate, a
supplier dispute worth £1.8 m, and whether to rebuild a reporting pipeline that is in fact sound.
**G** order lines with requested and confirmed quantities and dates, delivery confirmations, the fill-rate
definition in the customer supply agreement (line fill vs case fill vs order fill, measured at **confirmed**
quantity), the supplier's own report with its methodology appendix (measuring **order** fill against
*requested* quantity), the three accounts' shortfall tickets, a returns/rejection log, the incumbent
reporting code, an internal note from the reporting team defending the number.
**H** (1) the report is wrong; (2) **the report is right and the supplier's number answers a different
question** (different fill definition and denominator); (3) both are right and the three accounts are a
genuine tail the aggregate hides; (4) the shortfall tickets double-count partial deliveries;
(5) a returns issue is being counted as a shortfall. **I** two organisations are computing **different
metrics with the same name**, and the contractual definition adjudicates; separately, a correct aggregate
can coexist with a real, material tail. **J** fill rate on the contractual definition, the reconciliation to
the supplier's definition, and the account-level tail — plus an explicit finding about which number governs.
**K** recompute both definitions and bridge · account-level decomposition · ticket reconciliation; all
accepted. **L** a diligent rebuild of the metric from raw order lines that reproduces the *supplier's*
92 %, presented as "the corrected fill rate", because the analyst took "requested quantity" as the
denominator (which is what the complainant's evidence implies). **M** it ties to the order ledger, it
explains the escalation, it agrees with an external party's report, and it vindicates the stakeholder who
raised the issue. **N** ties to raw orders; matches the supplier's figure; reproduces the three accounts'
shortfalls. **O** the **supply agreement**: the contractual denominator is confirmed quantity, and the
supplier's appendix says otherwise — so the two numbers are bridgeable, not contradictory. A second route:
the tickets, reconciled, show 40 % are returns-driven, which the fill definition excludes by contract.
**P** the customers' own goods-receipt confirmations. **Q** reproduce both → find the definitional
difference → bridge → decompose to the tail → reconcile tickets → conclude the report is correct, the
complaint identifies a real tail, and the supplier's number measures something else → decide (no rebuild;
open a tail remediation; reject the supplier claim). **R** the difficulty is *resisting* a plausible,
socially-endorsed correction; the graded object includes "the incumbent is correct", which nothing in the
phase-1 suite does. **S** grade both definitions' values, the bridge, the tail decomposition, and the
verdict (which number governs); hidden extracts vary whether the incumbent is right — **in one extract the
incumbent is genuinely wrong**, so "always defer" fails as surely as "always overturn". **T** accept any
bridge that recovers both figures. **U** low — the agreement must be read, not quoted in the prompt.
**V** low — the contract is authoritative. **W** metric-definition disputes between a retailer and a
supplier are routine commercial reality. **X** family: **defer-or-overturn discrimination** — every world
should contain one. **Y** wholly new: all five current tasks have a wrong published number, which is a
structural bias in the suite. **Z** ADMITTED, and flagged as a **required archetype**, not merely a candidate.

---

## P32 — The question these data cannot answer
**C** marketing / commercial analytics · **D** measurement scientist · **E** the CMO asks for the
incremental effect of a national brand campaign that ran everywhere, at the same time, with no holdout, and
wants a number for the board in a week. The analytics team has already produced one (a pre/post lift of
+6.4 %). **F** a £25 m renewal decision, and a precedent for how the company measures brand media.
**G** national spend and GRP data, weekly sales, a pre/post analysis notebook, a competitor activity file, a
price and distribution history, a **regional media-weight variation file** (media bought by TV region with
materially different weights, not randomised but plausibly exogenous to demand), a prior year's geo holdout
on a different campaign, the measurement policy stating what standard of evidence the board requires, and a
seasonality/weather series. **H** (1) +6.4 % is the effect; (2) the effect is **not identified** from
national pre/post — there is no counterfactual; (3) regional media-weight variation offers a weak,
assumption-laden identification route; (4) competitor activity and a price change confound the window;
(5) the prior geo holdout can bound a plausible range by transport. **I** the honest object may be a
**bound plus a design**, not a point estimate: the available data cannot identify the effect at the standard
the policy requires, and the correct deliverable says so and specifies the experiment that would.
**J** either (a) a defensible identified estimate from regional weight variation **with its assumptions
stated and tested**, or (b) a declaration of non-identifiability with a bound and a concrete experimental
design (holdout geography, power, duration, cost) — and in both cases an explicit statement of what the
+6.4 % actually measures. **K** regional weight-variation model with placebo and pre-trend tests ·
transport from the prior holdout to bound the effect · explicit non-identification with a design;
**all three accepted, and a bare point estimate without assumption tests is not**. **L** a sophisticated
causal-impact analysis: a Bayesian structural time-series (CausalImpact-style) on national sales with
competitor spend, price and weather as controls, reporting +5.1 % with a credible interval and good
posterior predictive checks. **M** the model is well specified, the pre-period fit is excellent, the
controls are sensible, and the interval looks honest — but every "control" series is national, so there is
no untreated unit anywhere in the data. **N** posterior predictive checks pass; pre-period fit is tight;
ties to finance revenue; the interval excludes zero. **O** a **placebo in time**: fit the same model to a
pre-campaign window and it "detects" an effect of similar magnitude. Second route: the regional
weight-variation estimate is far smaller and its pre-trend test fails in two regions, showing the weight
variation is not exogenous — which is itself the finding that the design cannot support the claim.
**P** the prior year's geo holdout as an external anchor on plausible magnitude. **Q** reproduce +6.4 % →
ask what the counterfactual is → attempt a BSTS and run a time placebo → discover it fires → try regional
variation → test pre-trends → conclude non-identification at the required standard → bound the effect →
specify the experiment → decide (renew at a reduced commitment with a holdout built in). **R** the graded
deliverable includes a **negative epistemic result**, which nothing in the suite or (per the review) in any
data-agent benchmark grades; three commitments (identification feasibility, bound, design).
**S** grade: the placebo-in-time result, the regional-variation estimate and its pre-trend diagnostics, the
bound, the required experiment's power/duration, and the verdict field (`identified` / `not identified at
the policy standard`). Hidden extracts vary whether identification *is* available — in one extract the
regional variation passes its tests and a point estimate is the correct answer, so "always abstain" fails.
**T** the three routes are accepted; what is graded is the diagnostic outcomes and the verdict, not the
method. **U** medium — the policy's evidence standard must be discoverable but the verdict must not be.
**V** **high, and this is the task's main risk** — mitigated by a measurement policy that states the
evidence standard (e.g. "brand-media renewals above £10 m require a design with an untreated comparison"),
so "not identified" is a *contractual* judgement, not an aesthetic one. **W** national brand campaigns
without holdouts, and boards demanding a number anyway, are the everyday reality of marketing measurement;
Decision Lab's published example of returning *"No valid model found. Run a geo-holdout experiment."* is the
target behaviour. **X** family: **identifiability verdict + design deliverable** — one per world.
**Y** wholly new: no existing ForensicDS task can be answered "you cannot answer this from these data".
**Z** ADMITTED with the ambiguity mitigation mandatory; **flagged as a required archetype**.
