# G24 Phase-0 simulation gate (identifiability, separation, tolerances)

**Status: PASSED.** Approved to build the Harbor task.

- **Nothing built, no model run.** Only the pilot generator and the estimator panel exist.
- **Code:** `research/g24/pilot/g24_sim.py` (data-generating process and regimes),
  `pilot_estimators.py` (panel), `run_gate.py` (calibration, validation, summary).
- **Results:** `research/g24/pilot/results/` (calibration, validation, tolerances, logs).

## 1. Pre-registered protocol (fixed before the runs below)

1. **Worlds.** Four regimes × seeds: calibration 3000 + 17i (6 per regime), validation 8000 + 17i (8 per regime).
   Each world is 160k slate decisions (45–50% exploration), with its own catalogue, pools, filtering, clicks and
   reloads.
2. **Truth.** Exact policy values over all decisions in the world (expectations under the click model, not click
   draws). No estimator is involved in the truth.
3. **Tolerance rule.** τ = **3.5 × SE** of the least efficient accepted estimator (slot-exact item-in-slot IPS),
   averaged over calibration seeds, per regime and quantity.
   - 3.5 rather than 3.0 because one reward requires 20 graded quantities (3 values + 2 lifts, on 4 extracts) to be
     inside simultaneously: at 3σ an unbiased oracle fails ≈5% of the time, at 3.5σ ≈1%.
4. **Pass for a method in a world** = every value and lift inside τ **and** the launch decision equal to truth.
5. **Gate criteria.**
   - every accepted estimator passes ≥ 99% of validation worlds;
   - every wrong method fails ≥ 99% of the worlds of at least one regime (a task reward requires passing all four
     extracts);
   - every true lift is ≥ 2.5σ from the decision boundary for the least efficient estimator;
   - no arbitrary modelling choice inside the accepted family decides pass/fail.

## 2. Regimes

| Regime | What changes | True values (v6 / v7 / v7_pd) | True decision |
|---|---|---|---|
| `visible` | base world: pools 8–14, filtering 10–45%, devices 45/30/25 | 0.358 / 0.348 (−2.5%) / 0.405 (+13%) | v7_pd |
| `tv_heavy` | TV 45% of traffic, much steeper TV examination curve, less exploration | 0.328 / 0.311 / 0.374 (+14%) | v7_pd |
| `no_launch` | wider pools 6–20, weaker v7_pd, stronger anti-ordering in v7 | 0.381 / 0.343 (−10%) / 0.310 (−18%) | v6 |
| `v7_wins` | v7 orders its good set correctly, weaker production ranker, mobile-heavy, more reloads | 0.332 / 0.376 (+13%) / 0.325 | v7 |

Margins for the least efficient estimator: +5.2σ (visible), +4.6σ (tv_heavy), −3.8σ / −7.5σ (no_launch), +4.9σ
(v7_wins).

## 3. Validation result (8 fresh seeds per regime, 32 worlds)

**Accepted estimators — all pass every world, worst error/tolerance ratio in brackets:**

| Estimator | Worlds | Decisions | Worst ratio |
|---|---|---|---|
| slot-exact item-in-slot IPS (weight m) | 32/32 | 32/32 | 0.8 |
| position-transfer IPS, per-device examination curves estimated from exploration | 32/32 | 32/32 | 0.4 |
| doubly robust (per-item reward model + slot-exact correction) | 32/32 | 32/32 | 0.7 |
| self-normalised slot-exact IPS | 32/32 | 32/32 | 0.7 |
| on-policy means for v6/v7 with paired IPS lifts | 32/32 | 32/32 | 0.7 |
| position-transfer IPS with a **pooled** examination curve | 32/32 | 32/32 | 0.4 |

The pooled-curve variant was proposed as a wrong method; the simulation shows it is unbiased enough in this
generator, so it is **reclassified as accepted**. Criterion 5 is satisfied: pooled vs per-device curves,
self-normalised vs raw, model-based vs model-free all pass.

**Wrong methods — worst ratio per regime (a method fails the task if it fails any extract):**

| Wrong method | visible | tv_heavy | no_launch | v7_wins | Worlds passed |
|---|---|---|---|---|---|
| IPS with the logged (pre-filter, slate-level) propensity, clipped + self-normalised | 26.1 | 22.1 | 17.1 | 23.9 | 0/32 |
| exact-slate replay on exploration | 16.0 | 20.1 | 11.2 | 15.6 | 0/32 |
| production-log replay (the existing gate) | 4.7 | 4.5 | 5.9 | 2.8 | 0/32 |
| serves treated as decisions | 4.3 | 4.6 | 3.8 | 4.7 | 0/32 |
| weight = pre-filter pool size K | 3.2 | 3.0 | 1.9 | 3.3 | 0/32 |
| direct method only | 3.3 | 3.0 | 2.2 | 2.7 | 0/32 |
| target slates built without the eligibility filter | 3.0 | 2.7 | 1.7 | 2.8 | 0/32 |
| keep-first-serve de-duplication | 2.4 | 2.2 | 1.8 | 2.5 | 0/32 |
| item-anywhere credit, no position transfer | 2.0 | 2.0 | 2.2 | 1.2 | 4/32 (only in v7_wins) |
| clipped weights (cap 10) | 1.3 | 1.1 | 2.8 | 1.1 | 19/32 (never in no_launch) |

Every wrong method fails **8/8 worlds in at least one regime**, so each scores 0 on the four graded extracts with
probability ≈ 1.

## 4. Attractor quality (why the wrong answers are believable)

- **Item-anywhere credit** (the natural "fix the propensity, keep matching items" path) ranks **v7 first** in three of
  four regimes with very tight intervals (lift SE ≈ 0.002), i.e. a confident wrong launch.
- **Production replay** (the deployed gate) reports a large positive lift for v7, agreeing with the item-anywhere
  estimate: two biased estimators agree with each other and with the team's prior.
- **Weight = K** and **serves as decisions** keep the right *ranking* in most regimes while the values are 2–5 τ off:
  a decision-level answer that looks right with wrong state underneath.

## 5. Identifiability checks

1. **Positivity.** Every target slate is a permutation of the eligible pool, so every target item-slot pair has
   logging probability 1/m ∈ [1/20, 1/6]. Weights are bounded; clipping is unnecessary and biases the result.
2. **Consistency across estimator families.** Six structurally different estimators agree with truth within 0.8 τ.
3. **The randomization is recoverable from observables.** m is the count of non-filtered candidates in the logged
   pool; the shuffle is uniform over their orderings, so the marginal is 1/m, and it never uses the logged propensity.
4. **On-policy anchors exist.** The production and A/B streams give on-policy means for v6 and v7 which any estimator
   can be checked against; the accepted panel agrees with them, the wrong methods do not.

## 6. Decisions carried into the build

- **Tolerances:** τ = 3.5 × SE_ref per quantity and extract, SE_ref from the slot-exact estimator, computed by the
  generator at build time and frozen in the task.
- **Seed screening:** the four graded extracts are accepted only if all six accepted estimators are within 2.5σ of
  truth and give the true decision, recorded in a fixture audit file.
- **Regimes:** visible, tv_heavy, no_launch and v7_wins as above.
- **Mutation suite:** the ten wrong methods above, plus mechanisms the pilot cannot express (TTL-based decision
  grouping errors: merging identical slates across TTL expiry, grouping by session only, relying on a cache flag) and
  overfits (hard-coded pool size, hard-coded examination curve, hard-coded launch, hard-coded device mix). Their
  margins must be re-measured on the real generator before validation sign-off.
- **The notebook attractor** in the workspace must produce *plausible* numbers (a value near the observed click rate
  that ranks v7 first), not the absurd scale the raw logged-propensity IPS produces. Its exact formula is fixed at
  build time and checked.
