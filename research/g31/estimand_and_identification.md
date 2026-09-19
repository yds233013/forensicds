# G31 estimand and identification

Written **before** any wrong method was designed, per the estimand-before-estimator rule.

## 1. The business incident

> **From:** VP Risk, PayCrest (payments processor)
> **To:** Decision Science
>
> Risk Science's readout says the v7 fraud model lifts caught-fraud value from 61% to 78% at the same
> intervention budget and recommends switching the whole book to v7 at the November policy release. Merchant
> Operations disagrees: chargeback recoveries in the marketplace book have been drifting up for two quarters, and
> they think v7 has been quietly running in shadow mode and looks better than it is.
>
> I have to sign the release. Tell me, per segment, how much fraud value each model actually catches at our
> current 4% intervention budget, and which model we should run in each segment.

The visible analysis (`W2_age_cutoff_30`) evaluates on settled authorisations older than 30 days, calling a
transaction fraudulent if a chargeback posted within 30 days. It is the analysis a competent analyst writes in an
afternoon, and it is wrong for two compounding reasons.

## 2. Prediction unit

A single **authorisation attempt**, scored once at authorisation time by both models from pre-decision features.

## 3. Latent outcome

```
Y*_i = 1  if authorisation i would incur a fraud chargeback were it allowed to settle
       0  otherwise
```

A potential outcome fixed before any decision. Blocking does not change `Y*`; it prevents `Y*` from being
realised.

## 4. Exact estimand

For model `m ∈ {v6, v7}` and segment `g`, let `τ_{m,g}` be the score threshold that flags exactly the segment's
**current intervention budget** `c_g` (block + review, 3.2–5.0% depending on segment):

```
τ_{m,g}  :  P( s_m ≥ τ_{m,g} | segment = g )  =  c_g
```

The graded quantity is **value-weighted fraud recall at the fixed budget, over the full eligible population**:

```
             Σ_{i ∈ g}  Y*_i · v_i · 1[ s_{m,i} ≥ τ_{m,g} ]
R_{m,g}  =  ─────────────────────────────────────────────────
                    Σ_{i ∈ g}  Y*_i · v_i

Δ_g      =  R_{v7,g} − R_{v6,g}

adopt_g  =  v7  iff  Δ_g ≥ 0.010,  else v6
```

Note three properties chosen deliberately:

- **the denominator runs over every authorisation in the segment**, blocked ones included, so the estimand cannot
  be computed on the settled population alone;
- **`τ` needs no labels** — both scores exist for every row, so the threshold is exact and is *not* a source of
  error. The whole difficulty is in the numerator and denominator;
- **the decision is per segment**, so a single global answer cannot be right.

**Graded set (proposed).** Not the decision alone — G05 and G24 both demonstrated why:

| # | Quantity | Why graded |
|---|---|---|
| 1 | `maturity_days` per segment | tests the delay mechanism in isolation |
| 2 | eligible population count per segment | tests that blocked rows are in the denominator |
| 3 | estimated fraud-value total per segment | tests selection handling, independent of either model |
| 4 | `R_v6,g`, `R_v7,g` (6 values) | the core metrics |
| 5 | `Δ_g` (3 values) | the comparison |
| 6 | `adopt_g` (3 decisions) | the business answer |

## 5. Identification

**Claim.** `R_{m,g}` is identified from the observable artefacts under assumptions I1–I5.

Decompose the population by band. Within segment `g`, for any function `h(Y*, v, s)`:

```
E[h] = P(ALLOW)·E[h | ALLOW] + P(REVIEW)·E[h | REVIEW] + P(BLOCK)·E[h | BLOCK]
```

Band membership is observed for every row, so the three weights are known exactly. Each conditional term is
identified as follows:

- **ALLOW band.** Every row settles. `Y*` is revealed as a chargeback after `delay`. Conditioning on
  `age ≥ T_g` (I3) gives a subsample that is random with respect to `Y*`, so `E[h | ALLOW]` is identified by the
  sample mean over mature allow rows.
- **REVIEW band.** Non-holdout rows are either worked (selected on `s6`) or declined (no label). Holdout rows are
  settled by a randomised, logged mechanism (I1), so `E[h | REVIEW]` is identified by the mature holdout rows.
- **BLOCK band.** Identical, via `q_block`.

Hence

```
              Σ_{i : labelled}  ŵ_i · Y_i · v_i · 1[s_{m,i} ≥ τ]
R̂_{m,g}  =  ───────────────────────────────────────────────────
                    Σ_{i : labelled}  ŵ_i · Y_i · v_i

ŵ_i = 1           for mature ALLOW rows
ŵ_i = 1/q_band_g  for mature holdout rows in REVIEW or BLOCK
```

### Assumptions

| | Assumption | How an analyst can check it from the workspace |
|---|---|---|
| **I1** | **Bypass is randomised and its probability is logged.** `holdout ⟂ (Y*, v, z) | band, segment`, with `q > 0` | the policy document states the programme and the rate; the decision table carries a reason code; the analyst can verify that holdout and non-holdout rows have the same score and value distributions within band |
| **I2** | **Blocking does not change `Y*`.** Declining an authorisation prevents settlement; it does not alter whether the attempt was fraudulent | domain fact, stated in the chargeback-operations document; testable only indirectly (bypassed and blocked rows should match on pre-decision covariates) |
| **I3** | **Maturity depends only on elapsed time.** `P(chargeback observed | Y*=1, settled, age ≥ T_g) = 1` for a segment-specific horizon `T_g`, and the lag is independent of `Y*` given segment | estimable from fully mature cohorts: the empirical lag distribution of posted chargebacks in the oldest cohorts, where nothing is censored |
| **I4** | **Investigator determinations are accurate** where they exist (`review_fraud = Y*`) | stated in the review-queue document; not load-bearing for the accepted estimators, which do not use them |
| **I5** | **Overlap.** Every (segment, band) cell contains mature holdout rows | directly countable in the data |

### Where identification would fail, and why it does not here

- If the bypass rate were **unlogged**, the block band would be unidentified and the honest answer would be
  partial identification (bounds). It is logged, by design — the programme exists precisely so the risk team can
  keep measuring.
- If the bypass were **not randomised** (e.g. analyst-chosen bypasses), I1 fails. The task must make the
  randomisation visible and checkable rather than merely asserted.
- If `T_g` exceeded the extract window, the maturity distribution would not be estimable. The window (365 days) is
  deliberately more than three times the longest lag (120 days).
- If blocking *changed* `Y*` — for example if declined customers retried successfully — I2 fails and the object
  becomes causal. The generator has no retry mechanism, and the task documents must say so explicitly rather than
  leaving it to inference.

### The ambiguity test

> Could two competent analysts reasonably reach different `adopt_g` answers because the task underspecifies
> identification?

They can reach different **numbers** — the four accepted families differ by a few tenths of a point of recall —
but the design intends that they cannot reach different **decisions**, because the true `|Δ_g|` (≈ 0.10–0.12) is
an order of magnitude larger than the spread across accepted estimators (≈ 0.003–0.015). That claim was measured rather than assumed - and the measurement, together with the adversarial
review, showed the design fails for other reasons: see `simulation_results.md` and `build_recommendation.md`.

One genuine ambiguity is acknowledged and must be resolved in the task text, not by the verifier: **whether the
budget is held fixed by rate or by expected review workload.** These give slightly different thresholds. The
readout contract must state "fixed flag rate, computed on the scored population" explicitly.

## 6. Why this is not Task 02

Task 02 is point-in-time **feature** state: the failure is using a feature value that did not exist at prediction
time. G31's features are fixed and correct; the problem is the **outcome**. Maturity reconstruction is one of
three mechanisms here and, on its own, is the *least* consequential: `W3_mature_settled_only` gets maturity
entirely right and is still badly wrong, because it evaluates on the settled population. If an agent solves G31
the way it would solve Task 02, it produces `W3`.

## 7. Why this is not G05

G05's object is a **treatment effect** — what did the rollout cause — and its difficulty is the identifying
assumption for a counterfactual trend. G31's object is a **property of two models on a fixed population**; no
counterfactual outcome is being estimated, because `Y*` is defined pre-decision and is unaffected by the action
(I2). Causal vocabulary enters only through the *observation* process, not the outcome. There is no parallel-trends
assumption, no control group, and no transport of an effect to a different population.

## 8. Why this is not G10

G10 estimates a **latent continuous quantity** (unconstrained demand) under censoring generated deterministically
by stockouts, with no randomised device — identification rests on a parametric latent model. G31's outcome is
binary and its missingness has a **randomised, logged component**, so identification is nonparametric. The
statistical work is reweighting and standardisation, not latent-variable modelling.

## 9. Why this is not G24

G24 evaluates a **policy value** under a logged stochastic policy, and its difficulty is reconstructing the
logging propensity and the decision grain. In G31 the action space is trivial (three bands, deterministic in `s6`)
and the historical policy is not the hard part — an agent can read it off directly. The hard part is that the
**outcome** is missing for three different reasons. And critically, **IPW is not the only route**: the simulation
tests a post-stratification estimator and an outcome-regression estimator that use no individual weights at all,
and both recover the estimand. If IPW were the only valid route, this task would be G24 in a different costume and
should be rejected on that ground alone.
