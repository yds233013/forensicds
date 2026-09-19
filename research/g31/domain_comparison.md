# G31 domain comparison

Seven candidate domains for a task on **model evaluation under selectively observed and delayed outcomes**,
scored before any DGP was written. Research only; no task files, no model.

The capability we are trying to isolate needs a domain where **three different reasons for a missing label
coexist and require different repairs**:

1. **structural non-observation** — an operational action prevents the outcome from ever occurring;
2. **selective verification** — an investigation process produces high-quality labels for a non-random subset;
3. **delay / right-censoring** — outcomes mature slowly and recent cohorts are incomplete.

A domain scores well only if all three are *native* to how the business actually runs, not bolted on.

## Scorecard

| Criterion | A. Payment fraud | B. Credit underwriting | C. Trust & safety | D. Healthcare follow-up | E. Marketplace review | F. Insurance claims |
|---|---|---|---|---|---|---|
| Selective labelling natural | **strong** — blocked never settles | **strong** — rejected never repays | medium | medium | strong | strong |
| Delayed maturity natural | **strong** — chargebacks over weeks–months | **very strong** — default over years | weak — abuse reports are fast | strong | weak | **strong** |
| Intervention alters observability | **strong** — block removes the outcome entirely | **strong** | medium — a ban prevents further abuse but the label exists | weak — treatment changes the outcome, not its observability | strong | medium |
| Realistic business decision | **strong** — ship v7 or not | strong | strong | strong | medium | medium |
| Defensible ground truth | **strong** — Y* = "would charge back if allowed" is a clean potential outcome | weak — "would have repaid" over 3 years is far from the data | medium | **weak** — latent health state is contested | medium | medium |
| Multiple legitimate estimators | **strong** | medium | medium | medium | medium | medium |
| Convincing wrong analyses | **strong** | strong | strong | strong | medium | medium |
| Distinct from Task02/G05/G10/G24 | **strong** | medium | medium | medium | weak | medium |
| Deterministic verification feasible | **strong** | medium | strong | weak | strong | medium |

## Why each non-selected domain was rejected

**B. Credit underwriting / loan default.** The selective-labelling structure is the textbook one (reject inference)
and is arguably *more* famous than fraud. Two disqualifiers. First, **maturity is measured in years**: a realistic
extract cannot contain matured outcomes for recent vintages at all, so the delay mechanism stops being a
correctable nuisance and becomes a hard identification wall — the honest answer collapses to "wait". Second,
**the ground truth is not defensible**: "would this rejected applicant have defaulted" depends on a
counterfactual credit trajectory, and any generator I write would be asserting it rather than deriving it.

**C. Trust & safety / abuse detection.** Selective labelling is real but delay is not — abuse reports arrive in
hours. Removing the delay mechanism removes one of the three legs and leaves a pure selection problem, which is
thinner than we want. It is also the domain where "the intervention changes the outcome" (banning changes
subsequent behaviour) is hardest to keep out, which would drag the task back toward causal inference and G05.

**D. Healthcare risk / follow-up.** The outcome is genuinely latent and contested (was the patient actually
high-risk, or did the follow-up help?), so a deterministic verifier would have to assert a ground truth that a
competent analyst could reasonably dispute. That violates the "two competent analysts must not defensibly
disagree" gate. It also carries real-world sensitivity we have no reason to take on for a benchmark.

**E. Marketplace quality / manually reviewed listings.** Selective verification is excellent here, but there is
no natural delayed-maturity mechanism and no structural non-observation: a delisted item's quality is still
knowable. Two of three legs missing.

**F. Insurance claims / investigation.** Delay and investigation selection are both natural, but the "action
prevents the outcome" leg is weak — investigating a claim does not stop the loss from having occurred. It also
overlaps G10's structure (a censored quantity with an operational trigger) more than is comfortable.

**G. Other domains considered and dropped quickly.** Ad click fraud (labels are proprietary and arbitrary);
churn-prevention outreach (the intervention changes the outcome — this is G05 again); manufacturing defect
inspection (no delay, no counterfactual); content recommendation quality (this is G24).

## Selected domain: **A. Payment fraud / chargebacks**

It is the only candidate where all three legs are simultaneously native and where the latent outcome has a clean,
uncontroversial definition:

> **Y\* = would this authorisation attempt result in a fraud chargeback if it were allowed to settle?**

This is a potential outcome with an operational meaning that a payments risk analyst would recognise immediately,
and one the generator can define exactly.

The three legs map onto real operational artefacts:

| Leg | Mechanism | Why it is native |
|---|---|---|
| structural non-observation | a **blocked** authorisation never settles, so no chargeback can ever occur | this is what blocking *means*; it is not a modelling convenience |
| selective verification | the **manual review queue** is worked top-down by incumbent score under a capacity limit; worked cases get an investigator determination, unworked cases are declined at SLA and get nothing | queue capacity and score-ordered triage are how every review operation runs |
| delay / censoring | **chargebacks** arrive over weeks to months with segment-specific lag; the extract right-censors recent cohorts | card-network dispute windows are the reason this is true |

And it supplies the identification device that makes the estimand recoverable at all: a **logged bypass holdout**,
where a known fraction of would-be-blocked and would-be-reviewed authorisations is deliberately allowed through so
the risk team can keep measuring the population it is intervening on. This is standard practice at payment risk
teams, it has a paper trail (a policy document, a probability column, a decision reason code), and it is exactly
the artefact a naive analysis ignores.

## The specific reason this domain is distinct from what we already measure

Three of our built tasks already probe adjacent things, and the payments framing separates cleanly from each:

- **the outcome is missing for three different reasons at once**, each needing a different repair, and fixing any
  two still leaves a biased answer;
- **the object being estimated is a model comparison**, not a treatment effect (G05) and not a policy value under
  a logged stochastic policy (G24);
- **the missingness is not a function of the outcome given the covariates in the obvious way** — it is a function
  of an *operational action* that was itself driven by the incumbent model whose successor is now being evaluated.

That last point is the one that has no analogue anywhere in the current benchmark: **the thing being evaluated
created the population it is being evaluated on.**

## Residual risk carried into the design

The bypass holdout is the identification device, and it is also the single artefact that, if spotted, unlocks the
task. The design must ensure that *finding* it is not the whole problem — an agent that finds the holdout and
weights by it naively still has to get the maturity horizon, the review-band selection and the target population
right. This is tested explicitly in the simulation gate (`W9_holdout_only`, `W3_mature_settled_only`,
`W7_ipw_on_v6_band`).
