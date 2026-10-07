# HANDOFF — G50 pre-exposure
**Date:** 2026-09-28 · **Task:** `candidates/g50-courier-boost-rollout` · **Branch:** `final10`
**Status:** ⚠ **NOT READY FOR TARGET EXPOSURE.** The scientific core is built and numerically validated; the
Harbor verifier, the Docker build, the Harbor Oracle/Nop runs and the mutation suite are **not built**. §34
lists exactly what remains. No target model was run.

---

## 1. TASK SUMMARY

A two-sided delivery marketplace (Northline, 20 markets) randomised a courier incentive ("Boost") **per
order** and measured a 4.0 percentage-point reduction in the late-delivery rate over 120,671 orders. The
programme readout recommends national rollout.

Boost works by placing a boosted offer **ahead of unboosted offers in the same market-hour offer queue**. A
courier who takes a boosted order is unavailable to an unboosted one. The arm contrast therefore measures how
much better it is to be boosted than not while both arms draw on **one shared courier pool** — almost
entirely a redistribution. With Boost on for everyone there is no queue position left to gain.

The rollout decision is written on a different quantity: the change in the late-delivery rate if Boost were
on for **every** eligible order rather than none. On the visible extract that quantity is **+1.70 pp** — Boost
makes the metric slightly *worse* — against a break-even threshold of 1.4961 pp. The correct decision is
`do_not_roll_out`; the incumbent says `roll_out`.

## 2. PROFESSIONAL SCENARIO

Boost attaches a guaranteed minimum payout to an individual delivery offer. Couriers deliberate over marginal
offers; deliberation shows up as acceptance latency, which is the part of the delivery clock the platform
controls. Operations piloted Boost in two phases: a three-week **market-level soak** (8 markets on, 8 off,
drawn by coin flip over 16 enrolled markets) to catch payout and fraud incidents, then six weeks of
**order-level randomisation** in those 16 markets with the share ramped once after an earnings-volatility
review. Four further markets were never enrolled and ran through phase 2 as a holdout.

The July investment committee will approve or decline national rollout. The Finance director wants the
recommendation re-derived from the warehouse.

## 3. WHY THIS BELONGS IN FORENSICDS

It instantiates the project's own working phenomenon exactly. The incumbent analysis:

- inspects the right evidence (assignment, config, the metric population),
- is **technically correct** for the quantity it computes,
- passes every legitimate check it runs — sample-ratio, pre-period balance, per-market consistency,
- produces a tight interval (four tenths of a point),
- and **runs a capacity check that cannot fail**: courier hours available to each arm are identical to within
  **0.078 %**, because the arms share the same couriers. Reading that as "capacity is not confounding the
  comparison" is the designed trap.

That last item is the *assumed-quantity principle* from the final-10 design made concrete: the quantity the
incumbent assumes (that the arms are independent draws on capacity) is the one that fails, and the check it
runs on that quantity is an identity that holds regardless.

## 4. MECHANISM BEING TESTED

**Unit of intervention under a shared capacity constraint.** The agent must distinguish:

- the **contrast between treated and untreated units inside a shared-resource system**, which is a
  redistribution and is what order-level randomisation identifies; from
- the **effect of switching the system as a whole**, which is what the rollout decision needs.

Formally, a pure priority reordering is zero-sum in mean assignment delay: with N orders, T boosted and K
couriers, the boost/control gap is `N/(2K) × cycle` regardless of T, while the market-hour mean is invariant
to T. What survives a full rollout is only the non-redistributive part.

## 5. LONG-HORIZON DEPENDENCY CHAIN

Each step below is only reachable from the previous one's finding.

1. **Reproduce the incumbent.** Requires joining `orders → zones → markets` (orders carry no `market_id`),
   applying the metric population (delivered only; `arm='excluded'` dropped), and aligning order timestamps
   to the Monday `week_start` convention.
2. **Notice the assignment table does not cover the whole window.** Soak-week orders have **no** row in
   `experiment_assignment`; a naive inner join silently deletes phase 1. This is what sends the agent to
   `experiment_config`.
3. **Read the config and find two randomisation units.** `randomisation_unit` is `market` in phase 1 and
   `order` in phase 2, with four markets at `status='holdout'`.
4. **Read the dispatch note and find the shared queue.** Boosted offers are placed ahead of unboosted ones in
   the same market-hour queue; a courier carries one delivery at a time.
5. **Realise the arm contrast is a within-pool comparison.** Only reachable from 4.
6. **Find the market-level variation.** Only phase 1 and the holdout markets vary Boost at the market level.
7. **Build the market-week panel** — a different grain from the order table, requiring courier hours
   aggregated from `courier_shifts` (courier-hour grain).
8. **Estimate the programme effect at the market level** with the market as the unit of inference, accepting
   the wide interval that 8-vs-8 markets gives. This is the design the incumbent's note rejects for being
   underpowered.
9. **Compute the required diagnostic** — control arm vs never-enrolled markets, differenced against the
   pre-programme weeks — and notice the incumbent skipped the differencing.
10. **Estimate the courier-hours response** from phase 1, which requires knowing phase 1 was market-level.
11. **Apply the memo rule** and decide.

Steps 2→3→4→5→6 are a genuine chain: each is a discovery that makes the next question askable.

## 6. ENVIRONMENT / FILE INVENTORY

18 workspace files, 72 KB before the generated warehouse.

| path | purpose |
|---|---|
| `environment/workspace/README.md` | orientation |
| `docs/boost_programme_brief.md` | what Boost is, what it costs, what it does not change |
| `docs/metric_definitions.md` | late-rate definition, metric population, week convention, market attribution, courier hours |
| `docs/experiment_plan.md` | both phases, the coin-flip split, the ramp, eligibility, the holdout |
| `docs/dispatch_offer_queue.md` | **the mechanism**: boosted offers ahead of unboosted in the same market-hour queue; one delivery at a time |
| `docs/courier_supply_note.md` | **the mechanism**: online hours track expected earnings per hour by market; denser pool shortens pickup distance |
| `docs/rollout_decision_memo.md` | the quantity the decision is made on, the £0.19/£12.70 derivation, the rule, and the required diagnostic |
| `docs/data_dictionary.md` | nine tables |
| `docs/outputs/readout_contract.md` | output schema — field names and types only |
| `northline_eval/{__init__,__main__,cli,warehouse,panel,effects,report}.py` | the incumbent package |
| `reports/boost_readout_2026-06.md` | the published readout recommending rollout |
| `notebooks/analyst_note.md` | the analyst's reasoning, including why phase 2 was preferred |
| `data/northline.sqlite` | generated at image build: 9 tables, 320,932 orders, 49 MB |

Not in the image: `environment/build/world.py` (generator, multi-stage Docker keeps it out of every layer),
`tests/`, `solution/`.

## 7. DATA-GENERATING PROCESS

Deterministic, seeded, numpy only. 20 markets × 12 weeks (3 pre + 3 soak + 6 phase-2) × 7 days × 12 hours.
Orders per market-hour ~ Poisson(λ), λ = base × market scale × day-of-week × hour-of-day.

Per order: queue position is a random permutation with **all boosted offers ahead of all unboosted**;
`accept_delay = base_accept − δ·boosted + (position/K) × queue_min_per_slot`; `service = prep + travel ×
(1 − η·density) × (1 + γ·S)`; late if `accept + service > promise`.

Three channels, deliberately separable:

| channel | parameter | acts on | survives full rollout? |
|---|---|---|---|
| queue priority | `queue_min_per_slot` | position within the market-hour | **no — exactly zero-sum** |
| direct acceptance | `delta_accept_min` | every boosted order | yes |
| courier supply → density | `beta_supply`, `eta_density` | `K` at market-week level, then travel | yes |
| idling cost | `gamma_idle` | travel at market-week level | yes (as a cost) |

`K_mw = K_base × (1 + β·S_mw)` where `S` is the **market-week** configured share, so within a market-week the
supply channel affects both arms equally and the arm contrast differences it out entirely.

Messiness, each with a professional reason: orders carry `zone_id` only; soak orders have no assignment row;
`arm='excluded'` for scheduled-ahead and corporate orders; cancelled orders have null delivery times and are
excluded by the metric definition; courier shifts at courier-hour grain; config at market-week grain; a
storm event and a dispatcher release in `ops_events` that are genuinely irrelevant.

## 8. ASSIGNMENT MECHANISM

- **Phase 1 (weeks 4–6):** market-level. 16 enrolled markets split 8/8 by coin flip before the phase opened.
  On-markets ran Boost on every eligible order; off-markets none.
- **Phase 2 (weeks 7–12):** order-level, independent Bernoulli per eligible order at the configured
  market-week probability (0.25 for two weeks, then 0.55). Four never-enrolled markets stay off.
- Realised share tracks the target: **max |z| = 2.09 across 96 market-weeks** (no sample-ratio mismatch).

## 9. TRUE SCIENTIFIC OBJECT / ESTIMAND

> The expected change in the late-delivery rate if Boost were enabled for every eligible order in every
> enrolled market, versus enabled for none of them — in percentage points, negative for an improvement.

Computed in the generator by **counterfactual re-simulation of the same market-hours** with all orders boosted
and with none boosted, holding every stochastic draw fixed. It is never computed by a reference estimator.

## 10. INCUMBENT ANALYSIS

`northline_eval` loads the metric population, computes the phase-2 arm difference with a two-proportion
interval, writes the contract artefacts, and sets `programme_effect_pp` **to the arm contrast** with
`analysis_unit = "order"`. Its `checks` subcommand runs sample-ratio, pre-period balance, per-market
consistency, courier-hours-by-arm and a raw control-vs-holdout comparison. It runs clean and fast.

## 11. WHY THE INCUMBENT IS PLAUSIBLE

Measured on the visible extract:

| check | result | reads as |
|---|---|---|
| arm contrast | **−3.994 pp**, 95 % CI [−4.399, −3.589] | a large, precisely measured win |
| sample ratio, 96 market-weeks | max abs z = **2.09** | assignment is clean |
| pre-period balance | enrolled 14.55 % vs holdout 15.30 % late | groups comparable |
| per-market consistency | all **16/16** markets negative, −3.4 to −4.6 pp | not one market or week |
| courier hours per arm | boost 9.53 h vs control 9.54 h, gap **−0.078 %** | "capacity is not confounding" |

The order-level randomisation is real, the estimator is right for the arm contrast, and the analyst's note
gives a *correct* reason for preferring phase 2: 8-vs-8 markets over three weeks gives an interval several
points wide, against four tenths of a point from 120k orders.

## 12. WHY IT IS WRONG FOR THE DECISION

The arm contrast is `(boosted outcome) − (unboosted outcome)` **while both arms compete for the same
couriers**. Its dominant term is the queue-position gap `N/(2K) × cycle`, which exists only because some
orders are boosted and others are not. Under full rollout every order is boosted, the queue ordering is a
uniform permutation again, and that term is zero by construction.

The courier-hours check cannot detect this: the arms are order-level labels on a shared pool, so any per-arm
capacity measure is identical by construction. It is an identity, not a test.

The corroborating evidence is present and misread: the phase-2 **control arm runs 2.44 pp worse than the
never-enrolled markets**, which the readout dismisses as the holdout markets being "our four newest and
smallest". The memo requires that comparison to be differenced against the pre-programme weeks, which removes
exactly that level difference; done properly it is **+3.185 pp**.

## 13. CORRECT ANALYTICAL ROUTE

1. Market-week panel over the whole window: orders joined through zones, metric population, Monday weeks,
   courier hours aggregated from `courier_shifts`.
2. Programme effect from **phase 1**, where Boost was assigned at the market level: contrast on-markets
   against off-markets on market-week late rate, with the **market** as the unit of inference and a two-group
   interval on 14 degrees of freedom.
3. Report the arm contrast separately — it is not the rollout quantity.
4. Control-arm vs never-enrolled DiD exactly as the memo specifies.
5. Courier-hours response from phase 1: courier hours per order, on-markets vs off-markets.
6. Apply the memo rule.

## 14. ACCEPTED ALTERNATIVE ROUTES

**Revised 2026-09-29 after the identification audit in §36. The panel-regression route previously listed here
has been withdrawn.** All accepted routes use only the phase-1 market-level randomisation (plus the pre-period
for the difference-in-differences variants). Measured deviation from latent truth across all four extracts:

| route | description | max \|dev\| | budget used (tol 1.00 pp) |
|---|---|---|---|
| **R1** (reference) | market-unweighted difference in phase-1 market-week late rates, market as the unit | 0.253 | 25 % |
| **R4** | order-weighted (estate-wide) phase-1 contrast, market-level inference | 0.190 | 19 % |
| **R3** | market-unweighted difference-in-differences of phase 1 against the pre-period | **0.052** | 5 % |
| **R3b** | order-weighted difference-in-differences | 0.112 | 11 % |
| ~~R2~~ | ~~market-week panel regression of late rate on boost share with market and week fixed effects, extrapolated to S=1 vs S=0~~ | ~~0.32~~ | **WITHDRAWN — see §36.4** |

Four genuinely distinct legitimate routes remain, so DP19 (≥2 accepted methods) is satisfied without R2.

## 15. GROUND-TRUTH NUMBERS

From the shipped generator (`tests/world.py` + `tests/scenarios.py`), all four extracts:

| extract | rollout effect (graded) | arm contrast | control-vs-holdout DiD | courier-hours response | graded orders | late rate | decision |
|---|---|---|---|---|---|---|---|
| visible | **+1.696** | −3.998 | +3.185 | +2.823 % | 120,671 | 15.48 % | `do_not_roll_out` |
| hidden_a | **−9.096** | −5.821 | −1.400 | +25.114 % | 113,319 | 15.38 % | `roll_out` |
| hidden_b | **+4.439** | −3.659 | +3.457 | +2.171 % | 126,566 | 14.93 % | `do_not_roll_out` |
| hidden_c | **−8.275** | −5.164 | −2.411 | +12.080 % | 93,014 | 13.20 % | `roll_out` |

Break-even threshold **1.4961 pp** = £0.19 incentive per boosted order ÷ £12.70 per late delivery.

Separation and margin, measured:

- **|arm contrast − truth|** = 5.69 / 3.28 / 8.10 / 3.11 pp. Minimum 3.11 against a 1.00 pp tolerance → the
  incumbent quantity is rejected on every extract, ratio **3.11**.
- **Distance from the decision threshold** = 3.19 / 7.60 / 5.94 / 6.78 pp. No extract is knife-edge.
- **Courier-hours response** spans 2.2 % to 25.1 %, so no memorised magnitude passes.
- Decisions split **2 `do_not_roll_out` / 2 `roll_out`**, so no constant decision passes.

## 16. BUSINESS DECISION RULE

From `docs/rollout_decision_memo.md`:

- `roll_out` — the estimated change is a reduction of at least **1.4961 pp** *and* the 95 % interval excludes
  zero.
- `do_not_roll_out` — otherwise.

Derived in the memo from realised incentive spend (£0.19 per boosted order, from `incentive_ledger`) against
the cost of a late delivery (£2.50 service credit + £10.20 expected retention loss = £12.70). The interval
clause is satisfied on every extract whenever the point estimate clears the bar, so it is present and
meaningful but **non-binding here** — which is deliberate, so that two routes with different interval widths
cannot reach different decisions.

## 17. CORRECT FINAL DECISION

Visible extract: **`do_not_roll_out`** (+1.696 pp, i.e. Boost slightly worsens the late rate at full
rollout). Hidden extracts as tabulated in §15.

## 18. VERIFIER DESIGN

**⚠ NOT BUILT.** The design is fixed and the tolerances are calibrated, but no `tests/test_boost.py`,
`tests/test.sh`, `tests/wheels/` or `tests/runtime_manifest.sha256` exists yet.

Intended design, following the P22/G24 pattern: regenerate each of the four extracts from the frozen
generator at grade time, re-run the agent's submitted pipeline against each, and compare
`out/readout.json` and `out/market_week_panel.csv` against generator truth. Deterministic throughout; **no
LLM judge is needed or proposed** — every graded field is a number, an integer count, a small enumerated
string, or a CSV of numbers.

Calibrated tolerances (`max(floor, 1.6 × worst oracle deviation)`):

| field | tolerance | worst oracle deviation | worst incumbent deviation |
|---|---|---|---|
| `programme_effect_pp` | **1.00** | 0.184 | 8.091 |
| `order_arm_contrast_pp` | **0.25** | 0.011 | 0.011 (passes — by design) |
| `control_arm_vs_holdout_pp` | **0.35** | 0.007 | 0.748 (fails on visible only) |
| `courier_hours_response_pct` | **1.00** | 0.354 | 2.072 |
| `orders_analysed` | exact | exact | exact (passes — by design) |
| `decision` | exact | exact | fails on 2 of 4 |
| `analysis_unit` | in {market, market_week, market_week_cluster} | passes | fails on 4 of 4 |

Interval fields: must contain truth, have width within [0.25, 4.0] × the reference width, and be **wider than
the arm-contrast interval** (a pseudoreplication check). Not yet implemented or calibrated.

## 19. CRITERION-LEVEL GRADING

Intended map (Harbor reads a flat `reward.json`; the binary reward stays the conjunction):

| criterion | graded on |
|---|---|
| `evidence_reconstruction` | `market_week_panel.csv` + `orders_analysed` |
| `scientific_object` | `analysis_unit` + `order_arm_contrast_pp` reported separately from `programme_effect_pp` |
| `identification` | `courier_hours_response_pct` |
| `estimator_implementation` | panel `boost_share` and `courier_hours` columns |
| `quantitative_results` | `programme_effect_pp` |
| `uncertainty` | interval contains truth, plausible width, wider than the arm-contrast interval |
| `independent_validation` | `control_arm_vs_holdout_pp` |
| `decision` | `decision` |

## 20. ORACLE RESULT

**Validated outside Harbor, on all four extracts — PASS.** The reference solution was run against a freshly
generated workspace for each extract and compared with generator truth:

| extract | programme effect dev | control-vs-holdout dev | courier-hours dev | arm contrast dev | decision | unit | n |
|---|---|---|---|---|---|---|---|
| visible | 0.017 | 0.000 | 0.117 | 0.004 | ✅ | ✅ | ✅ |
| hidden_a | 0.184 | 0.006 | 0.011 | 0.011 | ✅ | ✅ | ✅ |
| hidden_b | 0.111 | 0.007 | 0.182 | 0.006 | ✅ | ✅ | ✅ |
| hidden_c | 0.155 | 0.006 | 0.354 | 0.001 | ✅ | ✅ | ✅ |

**Harbor Oracle has NOT been run** (no verifier, no image).

## 21. NOP RESULT

**Not run.** No verifier exists. However the **unmodified incumbent** — the strongest possible "do nothing but
run what is there" submission, and a far harder test than Nop — was measured on all four extracts and
**fails all four**:

| extract | programme effect dev | decision | unit | courier-hours dev |
|---|---|---|---|---|
| visible | **5.690** ✗ | `roll_out` vs `do_not_roll_out` ✗ | `order` ✗ | 2.901 ✗ |
| hidden_a | **3.264** ✗ | right decision, wrong quantity | `order` ✗ | 22.956 ✗ |
| hidden_b | **8.091** ✗ | `roll_out` vs `do_not_roll_out` ✗ | `order` ✗ | 2.072 ✗ |
| hidden_c | **3.110** ✗ | right decision, wrong quantity | `order` ✗ | 11.016 ✗ |

hidden_a and hidden_c are deliberately **right-decision-wrong-science** extracts: a decision-only grader would
score the incumbent 2 of 4 instead of 0 of 4.

## 22. HARBOR CHECK RESULT

**Deliberately not run, and this is a policy decision rather than an omission.** `harbor check` invokes an LLM
evaluator agent (`claude-code` on a Sonnet model), which the repository has costed at $0.32–$1.05 per task.
The brief for this turn permitted it only "if available without target-model execution"; it is not. The
phase-3 precedent is the same — `research/phase3/readiness.md` line 1: "`harbor check` was not run: it invokes
an LLM judge." It should be run before freeze, as a recorded cost.

## 23. COMPLETE MUTATION TABLE

**⚠ NOT BUILT.** Zero mutations have been written or run. The suite the task needs, with the expected verdict:

| # | mutation | must score |
|---|---|---|
| M00 | reference solution, unmodified | **1** |
| M01 | incumbent arm contrast as the programme effect | 0 |
| M02 | correct market-level effect, `analysis_unit = "order"` | 0 |
| M03 | `analysis_unit = "market"` but the arm contrast as the number | 0 |
| M04 | phase-1 contrast at **order** level (pseudoreplication: right point estimate, interval ~10× too narrow) | 0 |
| M05 | market-level effect with the two-proportion order-level interval | 0 |
| M06 | correct effect, wrong decision (rule misapplied) | 0 |
| M07 | correct decision, arm contrast as the number | 0 |
| M08 | hard-coded visible readout | 0 |
| M09 | `control_arm_vs_holdout_pp` without the pre-period differencing | 0 |
| M10 | phase-1 on/off groups swapped | 0 |
| M11 | soak markets taken as all 16 enrolled rather than the 8 on | 0 |
| M12 | holdout markets included in the phase-2 "control" arm | 0 |
| M13 | cancelled orders counted as not-late | 0 |
| M14 | courier hours not divided by orders (market size not divided out) | 0 |
| M15 | **legitimate alternative**: R2 panel regression with market and week FE, clustered | **1** |
| M16 | **legitimate alternative**: market-level DiD of phase 1 against the pre-period | **1** |
| M17 | always `roll_out` | 0 |
| M18 | always `do_not_roll_out` | 0 |

M15 and M16 are the ones that matter most: if a scientifically valid alternative fails, the tolerances are
overfitted to the reference.

## 24. ANTI-LEAKAGE AUDIT

**Scan of the agent-visible workspace — clean.** Zero occurrences of `interference`, `SUTVA`, `spillover`,
`displacement`, `zero-sum`, `redistribut`, `saturation`, `cluster`, `pseudorep`, `unit of analysis`,
`contaminat`, `not comparable`. No truth-like constant (1.696, 9.09, 4.43, 8.27, 2.82, 25.1, 12.0, 3.18)
appears in any workspace file. No generator, scenarios, truth or manifest file is inside the workspace. The
incumbent code contains no comment identifying the defect. The Dockerfile is multi-stage so
`environment/build/world.py` is absent from every layer of the final image.

**Two deliberate partial scaffolds, recorded honestly:**

1. The output contract asks for `control_arm_vs_holdout_pp`, and the memo requires that comparison alongside
   any experiment result. That hints the control arm is worth examining. It is justified as the "required
   falsification artifact" the final-10 design asked for, and as realistic governance — but it is a hint, and
   it is the same category of scaffold that neutralised G44.
2. `docs/dispatch_offer_queue.md` states the queue ordering mechanically, and
   `docs/courier_supply_note.md` states that online hours track expected earnings. Both are mechanisms an
   operator would document. Neither states any implication for the analysis.

**Not yet audited:** the built Docker image layers, `git` history of the task directory, and environment
variables inside the container. Those require the image, which does not exist yet.

## 25. AMBIGUITY AUDIT

| question | finding |
|---|---|
| Is the estimand dictated by the decision? | **Yes.** The memo states the quantity in business language ("if Boost were enabled for every eligible order in every enrolled market, compared with … none of them") and the rollout is explicitly all-or-nothing, so no partial-rollout estimand is on the table. |
| Could another legitimate estimand give a different answer? | The arm contrast is a legitimate *quantity* but not the one the memo names. A market-level effect estimated from phase 2's ramp variation alone would be underpowered but not wrong; it lands in the same band (R2). |
| Is assignment sufficiently documented? | Yes — `experiment_config.randomisation_unit`, `boost_share_target`, `status`, plus the plan and `ops_events`. |
| Is interference real in the generated world? | **Yes, mechanically.** Boosted orders take queue positions ahead of unboosted ones in a pool of size K. Measured: latent control-arm contamination is +2.71 / −1.79 / +3.54 / −1.74 pp across the extracts. |
| Is the correct analysis identifiable? | Yes — phase 1 sets Boost at the market level across 8 on / 8 off markets, and four never-enrolled markets run through phase 2. |
| Would the verifier falsely reject a legitimate alternative? | **Unknown — this is the largest open risk.** Two routes were measured and agree (max deviation 0.32 pp), but M15/M16 have not been run against a verifier that does not exist. |
| Is the threshold defensible? | Yes, derived in the memo from £0.19 / £12.70 with both figures traceable (`incentive_ledger`; the service-credit and retention values are stated policy). |
| Does any conclusion rest on an arbitrary author choice? | The £10.20 retention value is an author choice, stated as policy. It moves the threshold but every extract sits 3.2–7.6 pp from it, so no decision turns on it. |
| Could a strong human disagree? | A reviewer could argue the phase-1 estimate is too imprecise to act on — which is why the memo's interval clause exists and why it is satisfied on every extract. I could not construct a defensible reading in which the arm contrast answers the memo's question. |

**Two ambiguities fixed during construction, recorded:** (i) an earlier design put the visible truth 0.09 pp
from the decision threshold, so two legitimate routes could have reached different decisions — the extracts
were retuned to sit ≥3.19 pp clear; (ii) the decision rule originally depended on the interval's upper bound,
which two routes with different precision could have decided differently — the rule now turns on the point
estimate with a non-binding informativeness clause.

## 26. REALISM AUDIT

The **synthetic dataset is not real** and is not claimed to be. The workflow is.

Order-level randomisation of courier-side incentives is standard practice in delivery marketplaces, and the
interference it creates through a shared courier pool is a known and documented problem in that industry —
which is why marketplaces run switchback and region-level designs. The specific artefacts are things an
industry data scientist would inherit: an experiment config table with a randomisation unit and a ramped
probability, an assignment table that covers only part of the window, courier shift records at courier-hour
grain, a pre-period metric table, an incentive ledger, an ops event log, a published readout, and a working
note. The decision (approve or decline a national courier-pay term) and the threshold (incentive cost against
the cost of a late delivery) are both ordinary.

The misleading incumbent approach is the realistic one: it is what the larger, tighter experiment supports,
and the analyst's stated reason for preferring it over the soak — power — is correct as far as it goes.

**Weakness:** 20 markets × 12 weeks with Poisson arrivals and normal service times is a simplification of
marketplace dynamics. The queue model is a priority permutation rather than a simulated dispatcher.

## 27. LONG-HORIZON AUDIT

Not a file-count claim. Using only the reference workflow, the genuine dependencies are:

- Step 2 (soak orders absent from `experiment_assignment`) is discoverable only by reconciling the order
  table against the assignment table — a **left join and a count**, not a document.
- Step 6 (where market-level variation exists) is only askable once step 5 has established that the arm
  contrast is a within-pool comparison.
- Step 8's unit of inference (market, 14 df) follows from step 3's `randomisation_unit = market`.
- Step 10's courier-hours estimator requires step 3's finding, because it must be computed on phase 1.
- The panel at step 7 is a different grain from every source table and is required by steps 8 and 10.

**Honest limits:** the chain is ~11 steps, not 60. Two of the steps (the panel, the DiD) are mechanical once
the preceding discovery is made. The task has not been run by any agent, so no measured step count exists,
and the expert-time estimate in `task.toml` (240 min) is an **author judgement with no human trial**.

## 28. OVERLAP AUDIT AGAINST EXISTING TASKS

| task | mechanism | G50 is not this because |
|---|---|---|
| **Task02** | availability-time provenance | nothing temporal or point-in-time; no feature reconstruction; the arm labels are correct |
| **G05** | staggered adoption + version transport | assignment is randomised and clean, not staggered by format; the problem is the unit, not the counterfactual trend |
| **G10** | latent quantity under endogenous censoring | nothing is censored; every order has an observed outcome |
| **G24** | logged-policy recovery (propensity, action space, decision unit) | closest relative. G24's propensity and decision unit are *mis-recorded by the serving path*; G50's assignment is correctly recorded and the units are genuinely independent draws — what is shared is the **resource**, not the logging |
| **G34** | outcome-role assignment | no time-to-event object |
| **P20** | policy feedback on the evaluation population | the population is not endogenous to a model's deployment; the contamination is between concurrent units, not across time |
| **P22** | measurement-system change | the metric is measured correctly throughout |
| **P31** | instrument governance + deferral | one definition, no contract dispute, no abstention |
| **G41** | feasible-set reconstruction + optimum | no optimisation |
| **G35** (development-only) | interference / general equilibrium | **the real overlap.** G35 is the same mechanism family. The difference is that G35's output contract names all three estimands, defines the spillover arms verbatim, and states "these three effects are different quantities and are expected to differ" — which performs the estimand selection for the agent, and G35 was solved 3/3 in 18–32 steps. G50's contract names fields only. G50 also uses a **shared-resource** mechanism with a zero-sum priority queue rather than a randomised-saturation design, and its identification comes from a market-level soak plus a holdout rather than from designed 0 %/50 %/100 % arms. |

**New mechanism contributed:** unit of intervention under a shared capacity constraint — the contrast between
treated and untreated units inside one resource pool versus switching the pool as a whole. Not covered by any
shipped task.

## 29. KNOWN LIMITATIONS

1. **No verifier, no image, no Harbor run, no mutations.** §34.
2. The `control_arm_vs_holdout_pp` criterion discriminates the incumbent on **only 1 of 4 extracts** (the
   pre-period difference happens to be small on the other three). It is a weak criterion as calibrated.
3. The courier-hours separation ratio is **2.07**, below the ≥3 heuristic the final-10 gate sets, though the
   criterion does reject the incumbent on all four extracts.
4. `order_arm_contrast_pp` and `orders_analysed` are passed by the incumbent **by design** — they exist to
   confirm evidence reconstruction, not to discriminate.
5. The output contract asking for the holdout comparison is a partial scaffold (§24).
6. Two routes measured, not four. A GLM and a pre-period DiD are untested.
7. The 49 MB SQLite regenerated four times at grade time will make the verifier slow; budget and measure it.
8. Expert-time estimate is an author judgement with no human trial.
9. Interval grading is designed but neither implemented nor calibrated.

## 30. FROZEN FILE CHECKSUMS

**Not frozen.** Freezing before the verifier exists and the mutation suite passes would violate the gate. For
reference, the current state of the task-visible tree:

```
$ find candidates/g50-courier-boost-rollout -type f -not -path '*__pycache__*' | wc -l
```
27 files (18 workspace, generator, task.toml, instruction.md, README.md, tests/{world,scenarios}.py,
solution/{3 files}).

A freeze manifest must be computed with the project's standard command once the task is complete:
`git ls-files candidates/g50-courier-boost-rollout | xargs shasum -a 256 | shasum -a 256 | cut -c1-16`.

## 31. TARGET EXPOSURE STATUS

**NOT EXPOSED. Zero target-model calls.** No Gemini, no other target model, no `harbor run` with any agent, no
`harbor check`. No design decision in this turn was informed by any model's behaviour — the extracts were
tuned solely against latent truth, route agreement, decision margins and separation ratios.

## 32. EXACT NEXT COMMANDS

Non-model commands, safe to run now:

```bash
cd /Users/yashshah2311/forensicds
python3 candidates/g50-courier-boost-rollout/environment/build/world.py /tmp/g50ws
docker build -t forensicds-g50:dev candidates/g50-courier-boost-rollout/environment
```

**Do not run** the following until the verifier and mutation suite exist and pass — and never as part of
construction:

```bash
# harbor run -p candidates/g50-courier-boost-rollout -a oracle -o jobs   # after the verifier exists
# harbor run -p candidates/g50-courier-boost-rollout -a nop    -o jobs   # after the verifier exists
# harbor check ...                                                       # invokes an LLM evaluator; costed
# any command naming google/gemini-3-flash-preview                       # forbidden until freeze
```

## 33. GIT STATUS / CHANGED FILES

Nothing committed, nothing pushed. Untracked additions only:

```
?? candidates/g50-courier-boost-rollout/     (27 files, new)
?? HANDOFF_G50_PREEXPOSURE.md                (this file)
?? HANDOFF_2026-09-28_ABUNDANT_RESUME.md     (earlier this session)
?? HANDOFF_2026-09-28_FORENSICDS_FINAL10_DESIGN.md  (earlier this session)
?? submission_5task_fallback.zip             (pre-existing)
```

No existing task, verifier, tolerance, hidden extract, prospective artifact or archive was touched. All eight
previously frozen checksums still recompute to their recorded values, and
`research/phase3/analysis_plan.md` still hashes to `c590cb5677ce…` with one commit in its history.

## 34. FINAL VERDICT: **NOT READY FOR TARGET EXPOSURE**

**What is done and validated:**

- ✅ Professional scenario credible; decision consequential and explicit with a derived threshold
- ✅ Two genuinely plausible interpretations; the wrong one uses real evidence, a recognisable method,
  produces coherent output, and passes five legitimate checks including one that **cannot fail**
- ✅ Evidence discriminates them (phase-1 market-level assignment + four holdout markets)
- ✅ Scientific object well defined and computed by counterfactual re-simulation, not by a reference estimator
- ✅ Correct analysis identifiable; **reference solution recovers truth on all 4 extracts** (max deviation
  0.184 pp on the headline quantity against a 1.00 pp tolerance)
- ✅ Incumbent **fails all 4 extracts**; 2 of 4 are right-decision-wrong-science
- ✅ Decisions split 2/2; no extract within 3.19 pp of the threshold; naive separation ratio 3.11
- ✅ Two legitimate routes agree with each other (≤0.32 pp) and imply the same decision everywhere
- ✅ Anti-leakage scan of the workspace clean; generator excluded from all image layers
- ✅ Adds a mechanism no shipped task covers

**What is missing — all of it blocking:**

1. ❌ **Harbor verifier** — `tests/test_boost.py`, `tests/test.sh`, `tests/wheels/` (hash-pinned),
   `tests/runtime_manifest.sha256`. Designed and calibrated in §18/§19; not written.
2. ❌ **Docker image build** — never attempted.
3. ❌ **Harbor Oracle = 1** — validated outside Harbor only.
4. ❌ **Harbor Nop = 0** — never run.
5. ❌ **Mutation suite** — 19 cases specified in §23; **zero written, zero run**. This is the single largest
   risk: the project has two recorded verifier defects (G36's household-vs-load weighting, P31's
   contract/truth contradiction) that a mutation suite of this kind is what catches.
6. ❌ **Legitimate-alternative acceptance (M15, M16)** — untested, so the tolerances may be overfitted.
7. ❌ **Interval grading** — designed, not implemented or calibrated.
8. ❌ **Image-layer, git-history and environment-variable leakage audit** — needs the image.
9. ❌ **`harbor check`** — deliberately deferred (§22).
10. ❌ **Freeze manifest** — must not be computed before 1–8 pass.

I did not force the task through. The judgement: the verifier is the component this project has twice shipped
defective, and writing it without the mutation suite to validate it would repeat that mistake at the exact
point where it has already cost the project two tasks.

## 35. CHATGPT HANDOFF

**What exactly makes G50 hard?** The agent must work out that a correctly randomised, correctly analysed,
tightly estimated treatment effect answers a different question from the one the decision is written on,
because the treated and untreated units draw on the same courier pool. Nothing in the workspace says so. The
two facts that imply it — boosted offers are placed ahead of unboosted offers in the same market-hour queue,
and a courier carries one delivery at a time — are stated as dispatch mechanics with no analytical
implication drawn.

**Is the difficulty reasoning or friction?** Reasoning. The friction is small and each piece has a
professional reason: orders carry `zone_id` not `market_id`; soak orders have no assignment row; the metric
population excludes cancelled and `excluded` orders; courier shifts are at courier-hour grain. Total
workspace is 18 files and 72 KB. There is no parsing trap, no encoding problem, and no irrelevant bulk.

**What is the plausible wrong analytical frame?** That phase 2's order-level randomisation identifies the
rollout effect, so the arm contrast is the answer — supported by 120,671 orders, a clean sample-ratio check,
pre-period balance, consistency across all 16 markets, and a capacity check showing the arms have identical
courier hours.

**What evidence forces the correct frame?** The dispatch note's queue ordering plus one-delivery-at-a-time;
phase 1's `randomisation_unit = market` with 8 on and 8 off markets; four markets at `status = 'holdout'`
running through phase 2; and the control arm sitting 3.19 pp worse than the holdout once differenced against
the pre-period as the memo requires.

**Can the wrong analysis pass naive validation?** Yes, and that is the point. It passes sample-ratio
(max |z| = 2.09 over 96 market-weeks), pre-period balance (14.55 % vs 15.30 %), per-market consistency (16/16
negative, −3.4 to −4.6 pp), and a courier-capacity check that returns a **−0.078 %** gap — a check that
cannot fail, because the arms share the couriers.

**What makes it long-horizon?** The eleven-step chain in §5, of which steps 2→3→4→5→6 are genuine
dependencies: the missing assignment rows send the agent to the config, the config reveals two randomisation
units, the dispatch note explains why that matters, and only then is "where does market-level variation
exist?" an askable question.

**How does it differ from the existing tasks?** §28 in full. The nearest relatives are G24 (whose logging path
mis-records the propensity and the decision unit, where G50's assignment is correctly recorded and the units
are genuinely independent draws on a **shared resource**) and the development-only G35 (same mechanism family,
but G35's output contract names all three estimands and says they differ, which is why it was solved 3/3 in
18–32 steps).

**Did every mutation behave correctly?** **No mutations were written or run.** The 19-case suite is specified
in §23. The two proxies that were measured behaved correctly: the reference passes all four extracts and the
unmodified incumbent fails all four.

**Is there any unresolved ambiguity?** Two fixed during construction and recorded in §25 (a knife-edge
decision threshold, and a decision rule that depended on interval width). One remains open: whether a
legitimate alternative estimator would be falsely rejected. Two routes were measured and agree within
0.32 pp, but M15/M16 have not been tested against a verifier.

**Is there any leakage?** None found in the agent-visible workspace (§24). Two deliberate partial scaffolds
are recorded: the contract asks for the holdout comparison, and the dispatch/supply notes state the mechanisms
(without their implications). The image, git history and container environment have **not** been audited
because no image exists.

**Is there any reason not to expose this to Gemini yet?** Yes — ten of them, in §34. Exposing it now would
burn the task's one clean pre-exposure measurement against a verifier that does not exist.

**What exact evidence should ChatGPT inspect before authorising exposure?**

1. `tests/test_boost.py` — once written, confirm every graded field is compared against `world.truth()` and
   not against the reference implementation's output.
2. The **mutation table with real results**, especially M04 (pseudoreplication), M15 and M16 (legitimate
   alternatives must pass), and M08 (hard-coded).
3. Harbor `jobs/*/verifier/reward.txt` for a real Oracle (1) and Nop (0).
4. A re-run of the oracle/incumbent comparison in §20/§21 from the frozen generator, confirming the numbers
   in §15 reproduce exactly.
5. The tolerance table in §18 against the measured oracle deviations — in particular whether
   `control_arm_vs_holdout_pp` should be dropped or re-specified, given it discriminates on only 1 of 4
   extracts.
6. The image-layer leakage audit, once an image exists.
7. The freeze manifest, computed only after 1–6.

---

### Explicit confirmations

- **Zero target-model calls.** No Gemini, no other target model, no `harbor run`, no `harbor check`.
- **No existing task, verifier, tolerance, hidden extract or prospective artifact modified.** All eight frozen
  checksums recompute to their recorded values.
- **`research/phase3/analysis_plan.md` untouched** (`c590cb5677ce…`, one commit in its history).
- **Five-task fallback archive untouched** (`c8561aad8300df6c…`, 8,471,008 bytes).
- **Nothing committed. Nothing pushed. Nothing submitted. No git history rewritten.**
- **No design decision was tuned against any model's behaviour.**


---

# 36. ESTIMAND AND IDENTIFICATION AUDIT (added 2026-09-29)

Prompted by the challenge that closeness to generator truth does not establish scientific validity. Every
number below was measured from the shipped generator; nothing is argued from design intent.

## 36.1 The four levels, separated

**(1) Latent simulation truth, `T_sim`.** `mean(late | every order boosted) − mean(late | no order boosted)`
over delivered, eligible orders in the **phase-2 market-hours of the 16 enrolled markets**, with every
stochastic draw held fixed. Order-weighted. A within-sample, same-period, paired counterfactual. This is what
`world.truth()` returns as `rollout_effect_pp`.

**(2) The causal estimand the business question implies, `τ_policy`.** From the memo: the change in the
late-delivery rate if Boost were enabled for every eligible order in every enrolled market versus none of
them. Formally `E[Y(1)] − E[Y(0)]` over the enrolled-market order population.

> ⚠ **Two things the memo fails to pin down, and both are real defects.**
> - **Weighting.** "The late-delivery rate" could mean the estate-wide rate (total late ÷ total orders) or the
>   average of market late rates. Measured gap between the two readings: **0.022 / 0.000 / 0.178 / 0.331 pp**
>   across the four extracts. This is the same class of defect as G36's household-weighted-versus-load-weighted
>   verifier mismatch (`research/audit/verified_defects.md` D4).
> - **Target period.** `T_sim` is defined over phase-2 hours; the memo names no period.

**(3) What the randomised design actually identifies.**

| design | identifies | is it `τ_policy`? |
|---|---|---|
| **Phase 2** — order-level Bernoulli, p ∈ {0.25, 0.55}, within market-week | the unit-level contrast `E[Y_i(boosted, S=p)] − E[Y_i(unboosted, S=p)]` **at realised saturation p, under interference** | **No**, and no assumption short of no-interference makes it so — and no-interference is false by construction |
| **Phase 1** — market-level, 8 on / 8 off drawn by coin flip over the 16 enrolled markets, 3 weeks | the **cluster-level ATE at full saturation** on the 16 enrolled markets over those weeks | **Yes**, restricted to the phase-1 period |
| **The four never-enrolled markets** | nothing about `τ_policy` — they are outside the estimand's population, and they were **not randomly selected** (they are the four oldest markets by index) | No; they serve only the required diagnostic |

The identification of `τ_policy` therefore rests entirely on **phase 1**, whose full-saturation, market-level
assignment is the estimand's contrast by construction. **That is a property of the design, not of the
simulation.** This is the core of the task and it survives the audit.

**(4) The reference estimator, R1.** Difference in the unweighted mean of market-week late rates between the 8
phase-1 on-markets and the 8 off-markets, market as the unit of inference, two-sample t interval on 14 df.

## 36.2 Assumptions under which each route identifies `τ_policy`, and whether the analyst can check them

| # | assumption | verifiable inside the task? | measured magnitude if violated |
|---|---|---|---|
| a | phase-1 split is randomised at market level | ✅ stated in `experiment_plan.md`; pre-period balance is checkable | — |
| b | phase 1 ran at full saturation (every eligible order boosted) | ✅ `experiment_config.boost_share_target = 1.0`, and confirmable from the order data | — |
| c | no interference **between** markets (courier pools are market-specific) | ✅ queues are per market-hour; couriers carry a `market_id` | — |
| d | **period transportability** — the phase-1 effect equals the effect in the target period | ❌ **only weakly.** The analyst can check that the pre-period is stable; they cannot check that a treatment *effect* is time-invariant | measured phase-1 vs phase-2 contrast gap **0.037–0.073 pp** — it holds because the DGP has no week, trend or seasonal term |
| e | the estimator's weighting matches the estimand's | ❌ **the memo does not say which**, so this is unanswerable in-task | **0.000–0.331 pp** |
| f | no post-treatment effect on the metric denominator (order volume, cancellation) | ❌ **essentially not checkable.** The analyst would see phase-1 arm sizes differing by up to **35 %** (visible: 4,534 vs 3,354 orders/market; hidden_b 3,441 vs 4,844), which looks alarming but is ordinary 8-vs-8 randomisation noise | λ carries no S term and cancellation is drawn independently of Boost, so the violation is exactly zero — **authored** |
| g | the late rate does not depend on market size | ❌ authored: `K_base = couriers_per_order × λ` exactly, so congestion `N/K` is scale-invariant. If couriers-per-order varied by market, the 35 % arm-size imbalance would bias the contrast | zero by construction |

**R2 additionally required**, and this is why it is withdrawn:

| # | assumption | verifiable? |
|---|---|---|
| h | the market-level dose-response is **linear in S** over [0, 1] | ❌ the analyst has four support points {0, 0.25, 0.55, 1.0} and no power to test curvature. Measured deviation from the 0-to-1 chord at S = 0.5: **+0.052 / −0.289 / +0.055 / −0.298 pp** |
| i | phase 1 and phase 2 lie on the **same** dose-response curve — i.e. the market-level outcome depends on S only through S, not on how S was achieved | ❌ **circular.** This is true in the DGP only because a priority reordering is mean-preserving within a market-hour — which is precisely the insight the task exists to test. R2's validity presupposes the conclusion |

Measured dose-response (market-level late rate %, S applied uniformly to enrolled phase-2 hours):

```
visible   S=0:14.649  0.25:15.099  0.5:15.549  0.75:15.999  1.0:16.344
hidden_a  S=0:19.762  0.25:17.356  0.5:14.925  0.75:12.716  1.0:10.666
hidden_b  S=0:12.924  0.25:13.967  0.5:15.198  0.75:16.182  1.0:17.362
hidden_c  S=0:17.129  0.25:14.844  0.5:12.693  0.75:10.658  1.0: 8.854
```

Monotone and near-linear in all four — itself an authored property.

## 36.3 Point-by-point answers to the challenge

- **Does 8-vs-8 over a three-week market-level soak identify the full-rollout effect?** For the **contrast**,
  yes — market-level assignment at full saturation is the estimand's contrast, by design. For the **target
  period and population**, only under assumption (d) and the memo's silence on period. The *precision* is
  another matter: 14 df gives intervals of roughly ±1 pp, which is why the incumbent rejected this design, and
  why the memo's interval clause was deliberately made non-binding.
- **Do treatment-induced courier-supply changes create post-treatment variables the analysis conditions on?**
  **No.** R1 uses only the market-week late rate. `courier_hours` is a treatment-affected mediator and is
  *measured* (as `courier_hours_response_pct`) but never conditioned on. R2 did not condition on it either.
  The denominator (order count) is unaffected because λ carries no S term — assumption (f), authored.
- **Is extrapolating the phase-2 boost-share relationship to S=1 vs S=0 justified by the observed support?**
  The endpoints 0 and 1 **are** observed, in phase 1 — so it is interpolation, not extrapolation. But pooling
  phase 1 with phase 2 in a single linear slope requires (h) and (i), and (i) is circular. **R2 withdrawn.**
- **Do phase 1 and phase 2 correspond to the same intervention?** Not in composition. At S = 1 there is no
  priority differential; at S = 0.55 there is, and it redistributes within the market-hour. They coincide at
  the *market level* only because the reordering is mean-preserving — the task's own punchline.
- **Do the four never-enrolled markets create a selection or generalisability problem?** Not for `τ_policy`,
  which the memo scopes to enrolled markets. They were **not randomly selected** (they are the four oldest by
  index), so using them as controls for the headline estimand would be a selection problem. The reference does
  not. They are used only for the required diagnostic, which is a DiD and therefore removes the level
  difference their non-random selection creates.
- **Does market-level heterogeneity change the estimand?** Yes. Per-market effects span **+0.00 to +2.89 pp**
  (visible) and **−10.97 to −6.79 pp** (hidden_a). `corr(per-market effect, market size)` is **+0.070 / +0.001
  / −0.302 / +0.631** — on hidden_c the correlation is 0.63, by chance with 16 markets. Under heterogeneity
  correlated with size, order-weighted and market-unweighted estimands genuinely differ; measured gap up to
  **0.331 pp**. The memo must pin the weighting.
- **Does any estimator appear correct only because the DGP was authored to make it correct?** **Partly, and
  this is the honest answer.** Three authored simplifications each remove a source of bias that would exist in
  a real marketplace: no week or seasonal term (so (d) holds trivially); demand and cancellation independent of
  lateness (so (f) holds exactly); and couriers-per-order constant across markets (so (g) holds exactly). Each
  contributes ≲ 0.1–0.3 pp. The **decision** on every extract is 3.19–7.60 pp clear of the threshold, so no
  decision turns on any of them — but the third-decimal agreement between R1 and `T_sim` does partly rely on
  them.

## 36.4 Verdict on the challenge

**The core identification argument is sound and does not depend on privileged knowledge of `world.py`.** An
analyst who reads the dispatch note and the experiment plan learns that (i) boosted offers pre-empt unboosted
ones in a shared per-market-hour queue, (ii) phase 2 randomised within that shared pool, and (iii) phase 1
assigned at the market level at full saturation. From those three documented facts alone it follows that phase
2 does not identify the rollout quantity and phase 1 does. That is a design argument available entirely
in-task, and it is what separates the correct answer from the incumbent's.

**But the task as built is not yet scientifically clean**, for three measured reasons:

1. **The estimand is under-specified** (weighting, and target period). Up to 0.331 pp. Same defect class as
   G36 D4. **Must be fixed in `docs/rollout_decision_memo.md` before freeze**, and `world.truth()` must be
   defined over the population and period the memo names.
2. **R2 was wrongly listed as an accepted route.** Now withdrawn (§14). Its validity is circular.
3. **Three assumptions hold only because they were authored** ((d), (f), (g)). They must be recorded as scope
   limitations, and a v2 should introduce a modest week effect so that the difference-in-differences routes are
   *required* rather than merely available — which would also make R1-without-differencing fail and force the
   stronger analysis.

**Fixed during this audit, because both were unambiguous defects:**

4. The published readout dismissed the holdout comparison by asserting the never-enrolled markets were "our
   four newest and smallest". Measured: they are the **oldest** in all four extracts (launched 2024-04-13 to
   06-03 against 2024-06-20 to 2025-03-02), and **larger** in two of four (visible 16,519 vs 15,568 orders per
   market; hidden_c 15,370 vs 12,062). The claim was checkably false and inconsistent across extracts — a
   P22-class defect and an accidental shortcut. Replaced with a **methodological** misjudgement that is not
   checkably false: the analyst dismisses the comparison because the never-enrolled markets "were never
   randomised against the enrolled ones", which sounds right, is not a factual error, and is wrong for the
   better reason that the memo's differencing removes exactly the level gap being appealed to. The analyst note
   was corrected to match.

**G50 remains NOT READY.** The reasons in §34 stand unchanged, and items 1–3 above are added to them. The
scientific core — the DGP, the calibration, the four clean routes, the incumbent's coherent wrongness — has now
been audited against the standard asked for and holds up; the remaining work is the verifier, the mutation
suite, and closing the estimand specification.

