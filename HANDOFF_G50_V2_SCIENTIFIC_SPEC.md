# HANDOFF — G50 v2, final scientific specification before verifier construction
**Date:** 2026-09-29 · **Task:** `candidates/g50-courier-boost-rollout` · **Status:** scientific spec **COMPLETE**,
no BLOCKING issue. Verifier not built, by instruction. No target model run.

---

## 1. EXECUTIVE VERDICT

**The v1 defects found by the §36 red team are resolved.** The business estimand is now fully specified
(estate-wide, order-weighted, pre-programme weights, programme-period conditions); latent truth is computed
on exactly that definition; a persistent market-level performance difference plus a common seasonal movement
have been added, so the unadjusted phase-1 contrast is no longer reliable; and the reference estimator is a
pre-period-adjusted, estate-weighted, market-level analysis.

Measured end to end: **the reference passes all four extracts** (max deviation 0.961 pp against a 1.55 pp
tolerance) and **the unmodified incumbent fails all four** (programme-effect deviations 7.31 / 3.57 / 9.59 /
4.48 pp). Decisions split 2 `do_not_roll_out` / 2 `roll_out`, with margins of 3.68–8.57 pp from the
break-even threshold.

**One gate is not met and is recorded as a LIMITATION, not a blocker:** the naive-separation ratio is **2.33**
against my own ≥3 heuristic (final-10 gate 13). The shortfall is not a tolerance choice — it is the
irreducible sampling error of an estimator built on 16 randomised clusters with heterogeneous effects, and
closing it would require either flattening that heterogeneity or adding markets, both of which would damage
the realism or the mechanism. The naive value is nonetheless rejected on **every** extract.

**Proceed to verifier construction.**

## 2. DEFECTS FOUND IN V1

| # | defect | severity | status |
|---|---|---|---|
| D1 | Business estimand under-specified on **weighting** (estate-wide vs market-average; measured gap up to 0.331 pp). Same class as G36's household- vs load-weighted verifier mismatch | high | **FIXED** (§4, §8) |
| D2 | Business estimand under-specified on **target period** | high | **FIXED** (§9) |
| D3 | R2 (phase-2 boost-share panel regression extrapolated to S=1 vs S=0) listed as an accepted route although its validity presupposes the mechanism the task exists to diagnose | high | **WITHDRAWN** (§12) |
| D4 | Published readout dismissed the holdout comparison by asserting those markets were "our four newest and smallest" — measured: they are the **oldest** in all four extracts and **larger** in two of four | medium | **FIXED** in the previous turn |
| D5 | Three authored simplifications carried the reference estimator's accuracy: no time effect, demand/cancellation independent of treatment, couriers-per-order constant | medium | **partly fixed** — the time effect is now real (§10); the other two are reclassified and bounded (§14) |
| D6 | Output contract named the holdout diagnostic, telling the agent what to investigate | medium | **FIXED** — field removed (§16, §18) |
| D7 | Eligibility was only observable inside the phase-2 assignment table, so the metric population could not be built consistently for the pre-period | medium | **FIXED** — `order_channel` now on every order (§3) |

## 3. EXACT V2 CHANGES

**Data-generating process** (`environment/build/world.py`):
1. `market_offset_sd = 2.6` — a persistent per-market offset on travel minutes, identical in every week.
   This creates the between-market performance differences that make pre-period adjustment necessary.
2. `week_drift_min = 1.30` — a common seasonal movement across the window (a gentle rise and fall), identical
   in every market.
3. `order_channel ∈ {standard, scheduled, corporate}` on every order in every period; only `standard` is
   Boost-eligible. Replaces the phase-2-only `excluded` flag as the definition of the metric population.
4. Pre-period and soak windows lengthened from 3 to **4 weeks** each (window now 4 + 4 + 6 = 14 weeks). This
   reduces estimator sampling error without weakening the baseline-imbalance mechanism.
5. Counterfactual worlds now force S over the whole programme window (phase 1 + phase 2), not phase 2 alone.
6. `truth()` rewritten to the business estimand (§4/§5); `control_arm_vs_holdout_pp` removed from truth.

**Agent-visible documents:** rollout memo rewritten (estimand, weighting, period); metric definitions gain the
eligibility rule; data dictionary gains `order_channel`; experiment plan updated to four weeks and to explain
that markets differ persistently for reasons predating the programme; output contract de-scaffolded.

**Code:** incumbent `warehouse.py` filters the metric population and `report.py` emits the new contract;
reference `effects.py`/`report.py` implement the pre-period-adjusted estate-weighted market-level estimator.

## 4. FINAL BUSINESS ESTIMAND

From `docs/rollout_decision_memo.md`, verbatim:

> **The change in our estate-wide late-delivery rate — total late deliveries divided by total eligible
> deliveries across the enrolled markets — between running Boost on every eligible order and running it on
> none, under trading conditions like those of the programme period.**

with two definitional clauses, also verbatim:

> - **Estate-wide, not an average of markets.** … Where a market-by-market figure has to be combined, weight
>   each market by **its share of estate orders in the four weeks before the programme opened**. We fix the
>   weights on the pre-programme mix on purpose: Boost could itself shift where orders land, and the
>   weighting must not move with the thing being measured.
> - **Trading conditions like the programme period.** This is the effect under conditions comparable to those
>   we actually observed.

Formally, with `w_m` the market's share of pre-programme estate orders and `r_m(s)` its late rate under
market-level policy `s`:

```
τ  =  Σ_m  w_m · [ r_m(1) − r_m(0) ]        m over the 16 enrolled markets
```

No causal-inference vocabulary appears in the memo. **There is exactly one authoritative weighting
convention, and it is pre-treatment.**

## 5. LATENT SIMULATION TRUTH

`world.truth()["rollout_effect_pp"]` computes exactly the expression above by counterfactual re-simulation:
every order in the programme window is re-run with Boost on for all and with Boost off for all, holding every
stochastic draw fixed; each enrolled market's own contrast is taken over its programme-window orders in the
metric population; the market contrasts are combined with pre-programme order-share weights.

**These are four different objects and the handoff does not collapse them:**

| | object | where it lives |
|---|---|---|
| **A** | latent simulation truth — the counterfactual contrast, computable only inside the generator | `world.truth()` |
| **B** | the business estimand — the decision quantity, defined in business language | the rollout memo |
| **C** | what the design identifies — the phase-1 cluster-level contrast at full saturation | `experiment_config` |
| **D** | the reference estimator — a specific computation on observable data | `solution/northline_eval/effects.py` |

A and B are made to coincide by construction (that is what §4 fixes). C is what makes B recoverable. D is one
admissible way of doing C, and must be defensible from agent-visible evidence alone — see §14.

## 6. WHAT EACH EXPERIMENTAL PHASE IDENTIFIES

| phase | design | identifies | is it the estimand? |
|---|---|---|---|
| **Phase 2** (6 weeks) | order-level Bernoulli at p ∈ {0.25, 0.55}, independently per eligible order, within market-week | the **unit-level contrast at realised saturation p**: the difference between being boosted and not boosted while both arms draw on the same courier pool | **No.** The dominant term is queue position, which exists only because some orders are boosted and others are not. Under full rollout it is zero by construction. No assumption short of no-interference bridges the gap, and no-interference is false by construction |
| **Phase 1** (4 weeks) | market-level, 8 on / 8 off drawn by coin flip over the 16 enrolled markets, on-markets boosting **every** eligible order | the **cluster-level contrast at full saturation** on the enrolled markets under programme-period conditions | **Yes.** This is the estimand's contrast, by design |
| **4 never-enrolled markets** | not randomised against anything; they are the four oldest markets | nothing about the estimand | No — see §16 |

## 7. FINAL REFERENCE ESTIMATOR

| property | value |
|---|---|
| **unit of assignment** | market (phase 1) |
| **unit of analysis / inference** | market — 16 units, 14 degrees of freedom |
| **weighting** | market's share of **pre-programme** estate orders (fixed, pre-treatment) |
| **target population** | the 16 enrolled markets |
| **target period** | the programme period (phase-1 trading conditions) |
| **treatment contrast** | Boost on for every eligible order vs off for all of them |
| **outcome** | market late rate on the programme metric population (delivered, `order_channel = 'standard'`) |
| **estimator** | for each market, `Δ_m = r_m(soak weeks) − r_m(pre weeks)`; then weighted least squares of `Δ_m` on the treatment indicator with weights `w_m` |
| **uncertainty** | HC1 heteroskedasticity-robust standard error from the WLS fit, Student-t at 14 df |
| **decision** | the memo rule applied to the point estimate and interval |

**Why this and not the plain contrast.** Randomisation makes the unadjusted phase-1 contrast unbiased *in
expectation*. It does not make it accurate *in this sample*: with 8 markets an arm and a between-market
baseline spread of 7.3–9.9 pp, the realised baseline gap between the arms is up to **3.06 pp**, twice the
1.4961 pp decision threshold. Differencing each market against its own pre-programme weeks removes that
realised imbalance. **Pre-period adjustment here is a finite-sample accuracy correction, not an identification
device** — stated this way deliberately, because claiming it is needed for identification would be wrong.

## 8. WEIGHTING DERIVATION

The decision is a money decision: incentive spend per order against the cost of a late delivery. Both scale
with order volume, so the quantity the P&L sees is the **estate-wide rate**, not the average of market rates.
A market doing ten times the volume matters ten times as much.

Weighting by *realised* post-treatment volume would be unsafe: if Boost changed where orders land, the
contrast would mix a rate change with a composition change. **Pre-programme order shares are therefore fixed
as the weighting basis**, which makes `τ` a weighted average of market-level effects with constant weights
and immune to any volume response. This is a property of the definition, not of the simulator — it holds even
if demand responds strongly.

Measured consequence: with pre-period weights, the order-weighted and market-unweighted estimators now both
land inside tolerance (§13), so no G36-style weighting mismatch can occur. The memo pins one convention
anyway, for definiteness.

## 9. TARGET-PERIOD DERIVATION

The memo names "trading conditions like those of the programme period" and says explicitly that carrying the
figure to another season is a judgement for the committee rather than part of the number. Latent truth is
therefore evaluated over the **phase-1 window**, which is both what the design covers and what the memo
names. This removes the v1 mismatch in which truth was defined over phase-2 hours while the estimator used
phase-1 data — a gap measured at up to 0.90 pp once the seasonal movement was added.

## 10. TIME-EFFECT DESIGN

Two additions, the scientifically simplest form that makes the pre-period necessary:

1. **Persistent market-level performance differences** — a per-market offset on travel minutes, constant
   across all 14 weeks. Measured: between-market standard deviation of the pre-programme late rate is
   **7.33 – 9.87 pp** across the four extracts (it was ≈ 0 in v1).
2. **A common seasonal movement** — a gentle rise and fall of 1.30 minutes peak-to-trough on travel, identical
   in every market, so it affects both arms equally and is visible in the panel.

Neither was tuned against any model. They were tuned only until the unadjusted contrast became unreliable and
the adjusted one stayed accurate.

**Before and after** (deviation of each estimator from latent truth, max over the four extracts):

| estimator | v1 | v2 |
|---|---|---|
| unadjusted phase-1 contrast, estate-weighted | 0.190 | **4.16 → 1.55 after window lengthening; rejected on 2 of 4 extracts** |
| unadjusted phase-1 contrast, market-unweighted | 0.253 | **rejected on 1 of 4; flips the decision on hidden_b** |
| pre-period-adjusted, estate-weighted (**reference**) | 0.052 | **0.961** |
| pre-period-adjusted, market-unweighted | 0.112 | 1.272 |

The reference's deviation rose because the world is now genuinely noisier; that is the cost of realism.

## 11. WHY PRE-PERIOD ADJUSTMENT IS NEEDED

Not by declaration. The professional evidence establishes it:

- `experiment_plan.md` states phase 1 was split by coin flip over the enrolled markets — so the arms are
  comparable *in expectation*.
- The same document now states that markets differ persistently in delivery performance "for reasons that
  predate the programme — road network, restaurant density, courier mix", and that the pre-programme weeks
  are the reference for what each market looked like before anything changed.
- `market_week_baseline` supplies four pre-programme weeks for every market, so the realised gap is
  measurable.
- The rollout question concerns the programme period, which is later.

An analyst who computes the pre-programme late rate per market sees a spread of 7–10 pp and an arm gap of up
to 3.06 pp, against a decision threshold of 1.4961 pp. Comparing each market with its own earlier weeks is
then the obvious move. **The term "difference-in-differences" appears nowhere in the workspace.**

The sharpest demonstration is hidden_b: the unadjusted market-unweighted contrast is **−2.28 pp** (an
apparent improvement, which would trigger `roll_out`) while the truth is **+5.27 pp** (Boost makes the metric
worse). The entire sign flip is chance baseline imbalance.

## 12. R2 WITHDRAWAL

**R2 — the phase-2 boost-share panel regression extrapolated to S = 1 vs S = 0 — is withdrawn and must not be
listed as an accepted route.** Reasons, all measured in §36 of the pre-exposure handoff:

1. Only four support points on S: {0, 0.25, 0.55, 1.0}. Linearity cannot be tested with any power.
2. Measured curvature away from the 0-to-1 chord at S = 0.5: **+0.052 / −0.289 / +0.055 / −0.298 pp**.
3. It pools phase 1 and phase 2, which are different interventions in composition.
4. **Its validity presupposes the conclusion.** Phase 1 and phase 2 lie on one market-level dose-response
   curve only because a priority reordering is mean-preserving within a market-hour — which is exactly the
   insight the task exists to test. An analyst who could justify R2 has already solved the task.

## 13. VALID ALTERNATIVE ESTIMATORS

Measured against latent truth on all four extracts, tolerance 1.55 pp:

| route | max \|dev\| | valid? |
|---|---|---|
| **D_ow** pre-period-adjusted, estate-weighted, WLS + HC1 at the market (**reference**) | 0.961 | ✅ |
| **D_panel** market-week panel with market and week fixed effects, weighted by pre-programme orders, treatment × post interaction | 0.948 | ✅ |
| **D_pool** arm-level pooled rates, `(on_soak − on_pre) − (off_soak − off_pre)` | 1.046 | ✅ |
| **D_mu** pre-period-adjusted, market-unweighted | 1.272 | ✅ (inside tolerance; targets a slightly different weighting) |
| P_ow / P_mu unadjusted phase-1 contrasts | 1.55+ | ❌ rejected on 2 of 4 and 1 of 4 extracts |
| R2 panel-on-boost-share | — | ❌ withdrawn, §12 |

**Three genuinely distinct implementations remain valid** (D_ow, D_panel, D_pool), none kept merely to satisfy
a count: they differ in how the market-level comparison is formed and in how inference is taken, and all three
are things a competent analyst would write.

## 14. AUTHORED-ASSUMPTION TABLE

**A** = identified/testable from agent-visible evidence · **B** = stated professional scope assumption ·
**C** = synthetic-world simplification · **D** = unnecessary after v2.

| assumption | class | note |
|---|---|---|
| phase-1 split is randomised at market level | **A** | stated in the plan; pre-period balance is computable |
| phase 1 ran at full saturation | **A** | `boost_share_target = 1.0`, confirmable from order data |
| no interference between markets | **B** | queues are per market-hour; couriers carry a `market_id`. Stated scope |
| **period transportability** | **D** | no longer needed: the estimand is defined on programme-period conditions, which is what phase 1 covers |
| **estimator weighting matches the estimand** | **A** | the memo pins it; both weightings now pass anyway |
| **no post-treatment effect on the metric denominator** | **D** | no longer load-bearing: pre-programme weights make the estimand immune to a volume response by construction. Order volume still does not respond in the DGP (**C**), but the answer no longer depends on that |
| cancellation does not respond to treatment | **C** | cancelled orders are excluded by the metric definition; a lateness-driven cancellation response would change the metric population. Bounded: cancellation rate is 1.7–1.9 % and balanced across arms |
| couriers-per-order constant across markets | **C** | makes congestion scale-invariant, so the 8-vs-8 market-size imbalance cannot bias the contrast through congestion. §15 shows the estimator no longer relies on this |
| treatment-effect heterogeneity across markets | **A** | real and measured (per-market effects span several pp); the estimand is explicitly a weighted average, so heterogeneity is handled by definition rather than assumed away |
| market-size heterogeneity | **A** | visible in the data; handled by the pre-period weighting |

**No category-C assumption is load-bearing for the correct answer.** The two that remain (cancellation
response, couriers-per-order) affect the third decimal place and are bounded above by the tolerance.

## 15. PHASE-1 ARM-SIZE IMBALANCE ANALYSIS

**Why it happens.** 8-vs-8 randomisation over markets whose order volumes span roughly a factor of six.
Measured arm-volume ratios: **1.35 / 0.95 / 0.71 / 1.05**. This is ordinary cluster-randomisation noise, not a
defect and not a treatment effect.

**Does estate-wide weighting change the causal target?** Yes — it makes the target a volume-weighted average
of market effects rather than a simple average. That is the correct target, because the decision is a money
decision (§8).

**Does weighting by realised post-treatment volume introduce post-treatment weighting?** It would. That is
precisely why the memo fixes the weights on **pre-programme** order shares, which are available before
treatment and cannot be moved by it.

**What weighting is available before treatment?** The four pre-programme weeks in `market_week_baseline`, plus
the order table itself for those weeks. Both are in the workspace.

**Should pre-period order volume define the estate weights?** Yes, and it now does.

**Resolution.** The estimator was redesigned, not the data: markets enter with fixed pre-treatment weights, so
the arm-volume imbalance affects only the *precision* of the estimate, not its target. The residual reliance
on "couriers per order happens to be constant" is now confined to whether market size correlates with the
*late rate* — which the pre-period adjustment also removes, since any persistent size-related level difference
is differenced out.

## 16. HOLDOUT ROLE

**Classification: B — independent validation / falsification. Not required identification evidence.**

The estimand is identified by phase 1 alone. The comparison between the phase-2 control arm and the
never-enrolled markets corroborates that the control arm is contaminated — the key insight — but is not needed
to compute the answer, and the never-enrolled markets were not randomised against the enrolled ones.

**Decision: removed from the required output contract.** Requiring `control_arm_vs_holdout_pp` told the agent
that the control arm was worth examining, which is a substantial part of the insight. The agent may still
discover and use it. Measured values (pre-period-adjusted): **+2.9 / −1.7 / +3.8 / −1.6 pp** — note it is
*negative* on the two `roll_out` extracts, because there the courier-supply gain helps control orders too. It
is therefore genuinely informative rather than a one-way tell, which is a further reason not to hand it over.

**Cost of the decision, recorded honestly:** the task no longer grades a falsification artifact, which the
final-10 design listed as a desirable feature. That feature is deferred rather than faked.

## 17. FINAL AGENT-FACING OUTPUT CONTRACT

`out/market_week_panel.csv` — `market_id, week_start, orders, late_orders, late_rate_pct, boost_share,
courier_hours`, one row per market-week over the whole window.

`out/readout.json`:

| key | type |
|---|---|
| `orders_analysed` | int |
| `order_arm_contrast_pp` | number |
| `programme_effect_pp` | number |
| `programme_effect_ci_low_pp` | number |
| `programme_effect_ci_high_pp` | number |
| `inference_unit_n` | int — how many independent units the interval is computed over |
| `courier_hours_response_pct` | number |
| `decision` | `roll_out` or `do_not_roll_out` |

## 18. OUTPUT-SCAFFOLDING AUDIT

| field | would a competent analyst produce it for the business decision? | verdict |
|---|---|---|
| `programme_effect_pp` + interval | yes — it is the decision quantity | keep |
| `decision` | yes | keep |
| `orders_analysed` | yes — every readout states its population | keep |
| `order_arm_contrast_pp` | yes — the readout being challenged reported it; reproducing it is the first thing anyone does | keep |
| `inference_unit_n` | yes — a careful readout states what its interval is computed over. **Replaces v1's `analysis_unit`**, which named the concept ("unit of analysis") rather than asking for a number | keep, reworded |
| `courier_hours_response_pct` | yes — the incumbent already reported a courier-supply check, and the memo's question is why the rollout number differs from the trial number | keep |
| ~~`control_arm_vs_holdout_pp`~~ | **no** — naming it points at the diagnostic | **removed** (§16) |
| ~~`analysis_unit`~~ | no — a benchmark-shaped string field | **removed**, replaced by `inference_unit_n` |

Net: eight required fields, of which none names an intermediate scientific test.

## 19. ALL FOUR EXTRACT RESULTS

Latent truth on the §4 definition; reference = D_ow with WLS/HC1 at 14 df. All measured from the shipped
generator and the shipped reference solution, end to end through the incumbent package.

| extract | latent truth | reference est. | error | 95 % interval | arm contrast (naive) | unadj. phase-1 (estate) | unadj. (market-unw.) | holdout diag. | courier hrs | late rate | decision |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **visible** | **+2.188** | +1.245 | 0.943 | [−1.37, +3.86] | −5.119 | −0.92 | +1.87 | +2.9 | +2.87 % | 20.48 % | `do_not_roll_out` |
| **hidden_a** | **−10.064** | −10.172 | 0.108 | [−13.33, −7.02] | −6.494 | −10.32 | −10.50 | −1.7 | +25.10 % | 17.08 % | `roll_out` |
| **hidden_b** | **+5.267** | +4.306 | 0.961 | [+2.32, +6.29] | −4.322 | +1.55 | **−2.28** | +3.8 | +2.61 % | 18.32 % | `do_not_roll_out` |
| **hidden_c** | **−9.871** | −9.389 | 0.481 | [−11.84, −6.94] | −5.392 | −9.28 | −10.20 | −1.6 | +11.81 % | 15.27 % | `roll_out` |

Break-even threshold **1.4961 pp** (£0.19 incentive per boosted order ÷ £12.70 per late delivery).
Graded phase-2 populations: 115,424 / 108,418 / 121,035 / 89,448 orders.

**Calibrated tolerances** (`max(1.0, 1.6 × worst reference deviation)`): `programme_effect_pp` **1.55**;
`order_arm_contrast_pp` **0.25** (worst reference deviation 0.025); `courier_hours_response_pct` **1.40**
(worst 0.853).

**Hidden worlds test procedure, not magnitude:** the courier-hours response spans 2.6 % to 25.1 %, the truth
spans −10.1 to +5.3 pp, and the sign of the holdout diagnostic changes across extracts. No memorised constant
passes.

## 20. DECISION MARGINS

| extract | truth | distance from the −1.4961 threshold | reference interval vs threshold |
|---|---|---|---|
| visible | +2.188 | **3.68 pp** | interval lower bound −1.37 lies above the threshold |
| hidden_a | −10.064 | **8.57 pp** | interval entirely below |
| hidden_b | +5.267 | **6.76 pp** | interval entirely above |
| hidden_c | −9.871 | **8.37 pp** | interval entirely below |

No extract is knife-edge, and on all four the reference interval is decisive with respect to the threshold.
Decisions split 2 / 2.

## 21. INCUMBENT RESULTS

The unmodified incumbent package, run end to end on each extract:

| extract | `programme_effect_pp` | error | `inference_unit_n` | `courier_hours_response_pct` | error | decision | verdict |
|---|---|---|---|---|---|---|---|
| visible | −5.119 | **7.31** ✗ | 115,424 ✗ | +0.557 | 2.31 ✗ | `roll_out` vs `do_not_roll_out` ✗ | **FAIL** |
| hidden_a | −6.494 | **3.57** ✗ | 108,418 ✗ | +1.944 | 22.42 ✗ | `roll_out` — correct, wrong quantity | **FAIL** |
| hidden_b | −4.322 | **9.59** ✗ | 121,035 ✗ | −0.201 | 1.96 ✗ | `roll_out` vs `do_not_roll_out` ✗ | **FAIL** |
| hidden_c | −5.392 | **4.48** ✗ | 89,448 ✗ | +0.727 | 11.60 ✗ | `roll_out` — correct, wrong quantity | **FAIL** |

It reproduces `order_arm_contrast_pp` correctly on all four (deviation ≤ 0.025) — by design, since that field
exists to confirm evidence reconstruction. hidden_a and hidden_c remain **right-decision-wrong-science**: a
decision-only grader would score the incumbent 2 of 4 instead of 0 of 4.

## 22. WHY THE INCUMBENT REMAINS PLAUSIBLE

Unchanged by v2, and now with an extra reason. On the visible extract it reports a −5.1 pp improvement with a
95 % interval of about ±0.45 pp, and it passes every check it runs: realised boost share tracks the configured
target in every market-week; the enrolled and never-enrolled markets were comparable before the programme; the
effect appears in every enrolled market; and courier hours available to each arm are identical to within
**0.56 %** — a check that *cannot* fail, because the arms share the couriers.

v2 adds a second trap that is arguably stronger: an analyst who does notice the market-level soak and runs the
obvious unadjusted comparison gets **−2.28 pp on hidden_b** and recommends rollout, when the truth is
**+5.27 pp**. Getting to the market level is necessary and not sufficient.

## 23. REVIEWER A — marketplace experimentation scientist

*"Order-level randomisation of a courier-side incentive is something we do constantly, and it is exactly where
we get burned. The queue-priority story is right: if boosted offers pre-empt unboosted ones out of one pool,
the arm contrast is a redistribution and collapses at full rollout. So the diagnosis is correct.*

*My concerns are about the trial. Sixteen clusters over four weeks is a small experiment to put a national pay
term on, and the intervals here are ±2.5 to ±3.1 points. They happen to be decisive against a 1.5 point
threshold on all four worlds, which I checked, but that is partly luck of the effect sizes. I would also want
to know about novelty — couriers respond to a new guarantee differently in week one than in week twelve — and
nothing here models that. And the holdout markets are not a control group; I am glad they are not being used
as one."*

## 24. REVIEWER B — causal inference researcher

*"The estimand is now properly written down, which was my main objection. Fixed pre-treatment weights are the
right call and they make the target immune to a volume response, so the post-treatment weighting problem is
genuinely closed rather than assumed away.*

*I want to be precise about one thing the authors have got right and could easily have got wrong: because the
phase-1 split is randomised, the unadjusted contrast is unbiased in expectation. The pre-period adjustment is
not buying identification, it is buying finite-sample accuracy against a realised imbalance of up to three
points. The handoff says exactly that. Good.*

*Remaining: phase 2 identifies a saturation-specific direct effect and nothing here tries to use it, which is
correct. The withdrawal of the boost-share extrapolation is right and the circularity argument is the real
reason. What I cannot check from inside the task is whether couriers cross market boundaries; that is a scope
assumption and it should stay labelled as one."*

## 25. REVIEWER C — production data scientist inheriting the analysis

*"Practically: can I find phase 1 at all? Yes — the assignment table simply has no rows for those weeks, which
is the kind of thing that makes you go and read the config, and the config says the randomisation unit was the
market. That is a fair trail.*

*The pre-period matters and I would have found it: the baseline late rates across markets are spread over
seven to ten points, which is impossible to miss once you build the panel, and the two arms are visibly offset
before anything happened. Comparing each market to its own earlier weeks is what I would do.*

*What I am less sure about is the courier-hours number. I would report it because the old readout reported
one, but I would not have been confident it was the mechanism rather than a coincidence. And sixteen markets
with intervals this wide would make me ask for a bigger trial before signing a national pay term — which the
memo does not let me do, since the only options are roll out or do not."*

## 26. ALL REVIEWER OBJECTIONS + STATUS

| # | reviewer | objection | status |
|---|---|---|---|
| 1 | A | order-level randomisation cannot answer the rollout question under shared capacity | **RESOLVED** — this is the task |
| 2 | A | 16 clusters is a small trial; intervals ±2.5–3.1 pp | **LIMITATION** — real, and true of the professional situation. Intervals are decisive vs the threshold on all four extracts (§20) |
| 3 | A | no novelty/wear-in effect modelled | **LIMITATION** — a real marketplace phenomenon, absent here |
| 4 | A | holdout markets are not a control group | **RESOLVED** — not used for the estimand; §16 |
| 5 | B | estimand weighting unspecified | **RESOLVED** — §4, §8 |
| 6 | B | post-treatment weighting | **RESOLVED** — pre-programme weights, immune by construction |
| 7 | B | target period unspecified | **RESOLVED** — §9 |
| 8 | B | is pre-period adjustment an identification device? | **RESOLVED** — no, and the handoff says so (§7, §11) |
| 9 | B | couriers crossing markets | **LIMITATION** — stated scope assumption (class B) |
| 10 | B | R2 circularity | **RESOLVED** — withdrawn, §12 |
| 11 | C | is phase 1 discoverable? | **RESOLVED** — missing assignment rows force the config |
| 12 | C | is the pre-period issue visible? | **RESOLVED** — baseline spread 7.3–9.9 pp is unmissable in the panel |
| 13 | C | courier-hours number is hard to be confident in | **LIMITATION** — it is a mechanism quantity; tolerance 1.40 with worst reference deviation 0.853 |
| 14 | C | would want a bigger trial; memo forbids it | **RESOLVED** — the memo states the decision is binary and why |
| 15 | — | naive-separation ratio 2.33 < 3 (my own gate 13) | **LIMITATION** — §29 |

**No BLOCKING issue.**

## 27. LONG-HORIZON DEPENDENCY CHAIN

The real chain, as the reference workflow actually runs:

1. Reproduce the incumbent — join `orders → zones → markets`, apply the metric population (delivered,
   `order_channel = 'standard'`), align to Monday weeks.
2. **Notice the assignment table does not span the window** — soak-week orders have no row. A naive inner
   join deletes phase 1 silently.
3. Read `experiment_config` → **two randomisation units**, `market` then `order`, plus four `holdout` markets.
4. Read the dispatch note → boosted offers pre-empt unboosted ones in one per-market-hour queue; a courier
   carries one delivery at a time.
5. **Conclude the arm contrast is a within-pool comparison** and cannot answer the rollout question. Only
   reachable from 4.
6. Look for market-level variation → phase 1 is the only place it exists.
7. Build the market-week panel — a grain that appears in no source table, requiring courier hours aggregated
   from courier-hour records.
8. **See the baseline spread** (7.3–9.9 pp between markets) and the realised arm gap (up to 3.06 pp) in the
   pre-programme weeks.
9. Compare each market with its own pre-programme weeks rather than comparing arms directly. Only asked
   because of 8.
10. **Reconcile the weighting to the memo** — pre-programme estate shares, not a market average.
11. Take inference at the market, 16 units, not at the order.
12. Estimate the courier-hours response from phase 1 — requires step 3's finding.
13. Apply the economic rule and decide.

Steps 2→3→4→5→6 and 8→9→10→11 are genuine dependencies: each is a discovery that makes the next question
askable. Steps 7 and 13 are mechanical once the preceding discovery is made. **No agent has run this task, so
no measured step count exists**, and the 240-minute expert estimate in `task.toml` remains an author judgement
with no human trial.

## 28. OVERLAP WITH EXISTING FORENSICDS TASKS

Unchanged from the pre-exposure handoff §28 and re-checked after v2. Nearest relatives:

- **G24** — mis-recorded propensity and decision unit in a serving path. G50's assignment is correctly
  recorded; what is shared is the **resource**, not the logging.
- **G35** (development-only) — same mechanism family, but G35's output contract names all three estimands and
  states they differ, which performs the estimand selection for the agent; it was solved 3/3 in 18–32 steps.
  G50 names fields only, uses a shared-resource priority queue rather than randomised saturation, and
  identifies from a market-level soak rather than designed 0 %/50 %/100 % arms.
- **G05** — v2 adds a pre-period-adjustment step, which raises a superficial resemblance to G05's staggered
  adoption. The mechanisms remain distinct: G05's difficulty is choosing the conditioning set for a
  counterfactual trend under non-random staggering; G50's assignment is randomised and the adjustment is a
  finite-sample correction, not an identification strategy. Recorded as the closest new overlap introduced by
  v2.

**Mechanism contributed:** unit of intervention under a shared capacity constraint.

## 29. KNOWN LIMITATIONS

1. **Naive-separation ratio 2.33 < 3** (my own final-10 gate 13). Driven by irreducible estimator error from
   16 clusters with heterogeneous effects; the naive value is rejected on all four extracts.
2. **The unadjusted phase-1 contrast is rejected on only 2 of 4 extracts** (estate-weighted) or 1 of 4
   (market-unweighted). It fails the suite overall because all four must pass, and it flips the decision on
   hidden_b — but it is not rejected everywhere. Chance baseline imbalance is random; that is honest.
3. **`courier_hours_response_pct` has a modest margin**: worst reference deviation 0.853 against a 1.40
   tolerance, and the incumbent's smallest deviation is 1.96, a ratio of 1.40.
4. **The market-unweighted adjusted estimator also passes**, so the weighting specification is correct but not
   load-bearing for grading.
5. **No falsification artifact is graded** after removing the holdout field (§16).
6. **No novelty or wear-in effect** in the courier supply response.
7. **Cross-market courier movement** is assumed away (class B).
8. **Cancellation does not respond to lateness** (class C, bounded).
9. **14 weeks × 20 markets** produces a ~55 MB SQLite per extract; the verifier will regenerate four of them,
   which must be timed.
10. **Expert-time estimate is an author judgement**; no human has attempted the task.

## 30. PRE-VERIFIER SCIENTIFIC MANIFEST

Written to `candidates/g50-courier-boost-rollout/PRE_VERIFIER_MANIFEST.txt` — 28 hashed files covering the
DGP, the task instruction and metadata, every agent-visible document, the agent-visible incumbent package, the
reference estimator specification, and the Dockerfile.

**Aggregate digest of the manifest body: `0dbc9470ed483848`.**

This is **not** the benchmark freeze. Its purpose is to make visible exactly what changes once verifier
implementation begins.

## 31. FILES MODIFIED

All inside `candidates/g50-courier-boost-rollout/`, which is new and uncommitted:

```
environment/build/world.py                      DGP v2 + truth() on the business estimand
tests/world.py                                  copy of the above
environment/workspace/docs/rollout_decision_memo.md    estimand, weighting, period; diagnostic requirement removed
environment/workspace/docs/metric_definitions.md       eligibility by order_channel
environment/workspace/docs/data_dictionary.md          order_channel column
environment/workspace/docs/experiment_plan.md          four-week soak; persistent market differences
environment/workspace/docs/outputs/readout_contract.md de-scaffolded contract
environment/workspace/northline_eval/warehouse.py      metric population
environment/workspace/northline_eval/report.py         new contract
solution/northline_eval/effects.py                     reference estimator
solution/northline_eval/report.py                      new contract
PRE_VERIFIER_MANIFEST.txt                              new
```
Plus `HANDOFF_G50_V2_SCIENTIFIC_SPEC.md` (this file) at the repository root.

**No existing ForensicDS task, verifier, tolerance, hidden extract or prospective artifact was touched.** The
five frozen final-suite checksums and the three frozen prospective manifests all still recompute to their
recorded values; `research/phase3/analysis_plan.md` is unchanged.

## 32. TARGET-MODEL EXPOSURE STATUS

**NOT EXPOSED. Zero target-model calls, ever.** No Gemini, no other target model, no `harbor run`, no
`harbor check`. No v2 parameter was chosen with reference to any model's behaviour; the time effect was tuned
only until the unadjusted contrast became unreliable and the adjusted one stayed accurate.

## 33. EXACT NEXT STEP

Build the Harbor verifier against this specification: `tests/test_boost.py`, `tests/test.sh`,
`tests/wheels/` (hash-pinned), `tests/runtime_manifest.sha256`. Then the Docker build, Harbor Oracle = 1 and
Nop = 0, and the mutation suite (the 19 cases in the pre-exposure handoff §23, with the alternative-route
cases updated to D_panel and D_pool and the R2 case deleted). Freeze only after all of that passes.

Seven criteria, since `control_arm_vs_holdout_pp` is gone: evidence reconstruction, scientific object,
identification, estimator implementation, quantitative result, uncertainty, decision.

## 34. CHATGPT DECISION PACKET

- **Is the business estimand now fully specified?** Yes — quantity, weighting (pre-programme estate order
  shares), and period (programme-period conditions), all in business language with no causal vocabulary.
- **Does latent truth exactly match it?** Yes. `world.truth()` computes `Σ_m w_m [r_m(1) − r_m(0)]` over the
  phase-1 window with pre-programme weights, by counterfactual re-simulation.
- **What does phase 1 identify?** The cluster-level contrast at full saturation on the enrolled markets — the
  estimand's contrast, by design.
- **What does phase 2 identify?** The unit-level contrast at realised saturation, under interference.
- **Why can phase 2 not answer rollout?** Its dominant term is queue position, which exists only because some
  orders are boosted and others are not; at full rollout it is zero by construction.
- **Why is pre-period adjustment now required?** **Not for identification** — randomisation makes the
  unadjusted contrast unbiased in expectation. It is required for finite-sample accuracy: with 8 markets an
  arm and a baseline spread of 7.3–9.9 pp, the realised arm gap reaches 3.06 pp against a 1.4961 pp threshold,
  and on hidden_b the unadjusted contrast flips the decision.
- **What weighting is correct and why?** Estate-wide, order-weighted, on **pre-programme** shares — because
  the decision is a money decision that scales with volume, and pre-treatment weights cannot be moved by a
  treatment-induced change in order mix.
- **Does the reference estimator depend on any hidden simulator assumption?** No load-bearing one. Period
  transportability and denominator invariance are now class **D** (unnecessary). Two class-C simplifications
  remain — cancellation response and constant couriers-per-order — and both affect the third decimal only.
- **Which alternative estimators remain valid?** D_panel (weighted two-way fixed-effects panel) and D_pool
  (arm-level pooled pre/post), plus D_mu inside tolerance. Three distinct implementations.
- **Why was R2 rejected?** Four support points, untestable linearity, cross-phase transport, and — decisively —
  its validity presupposes the mean-preserving priority mechanism the task exists to diagnose.
- **What role does the holdout play?** Independent validation only. Removed from the required contract so it
  does not tell the agent where to look; its sign varies across extracts, so it is informative rather than a
  tell.
- **Did we reduce output-contract scaffolding?** Yes — `control_arm_vs_holdout_pp` removed, `analysis_unit`
  replaced by the numeric `inference_unit_n`. Eight fields remain, none naming an intermediate test.
- **Does the incumbent remain genuinely plausible?** Yes, and more so: it passes four legitimate checks
  including one that cannot fail, and v2 adds a second trap — the obvious market-level comparison still flips
  the decision on hidden_b.
- **Is the correct route recoverable entirely from agent-visible evidence?** Yes. Dispatch mechanics +
  experiment config + the visible baseline spread are sufficient; nothing requires `world.py`.
- **What assumptions remain?** Cross-market courier independence (B), cancellation non-response (C), constant
  couriers-per-order (C), no novelty effect (C).
- **Are any assumptions blocking?** No.
- **What makes it long-horizon now?** Thirteen steps with two genuine dependency runs (2→3→4→5→6 and
  8→9→10→11); v2 adds the baseline-discovery run.
- **Any scientific reason not to proceed to verifier construction?** No. The only open gate is the 2.33
  separation ratio, recorded as a limitation with its cause.
