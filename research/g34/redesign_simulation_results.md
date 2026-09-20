# G34 redesign — simulation results

All figures measured. Calibration seeds 1000–1099; validation seeds 1100–1599; disjoint blocks.
25,000 units per world, five regimes.

## R1 — validation against latent generator truth (the gate that would have dropped G34)

Truth is computed from latent event times: `q1 = P(T_fail ≤ 36 ∧ T_fail < T_overhaul ∧ T_fail < T_retire)`,
`q2 = P(T_fail ≤ 36)`. 12 worlds per regime.

| Regime | Q1 truth | Aalen–Johansen | cause-specific integration | discrete multistate | Q2 truth | 1 − KM |
|---|---|---|---|---|---|---|
| visible | 0.3299 | **−0.02%** | −0.21% | −0.40% | 0.5533 | +0.15% |
| failure_heavy | 0.4861 | **+0.02%** | −0.13% | −0.30% | 0.7417 | −0.27% |
| overhaul_heavy | 0.1929 | **+0.11%** | −0.04% | −0.20% | 0.5533 | +0.32% |
| retirement_heavy | 0.2716 | **−0.04%** | −0.18% | −0.33% | 0.5533 | −0.59% |
| mixed_low_risk | 0.2741 | **+0.03%** | −0.21% | −0.46% | 0.3712 | −0.30% |

Reference sd of AJ: 0.0030–0.0042. **R1 PASSES.** AJ recovers Q1 to within ±0.11% everywhere, and
1 − KM recovers Q2 to within ±0.6%.

## R5 — valid-family agreement

Three independent implementations of Q1 agree within **0.5%** of truth in every regime (AJ,
cause-specific hazard integration, monthly discrete multistate). Tolerance would be calibrated from
the least efficient of these, not from any wrong method.

## R7 — correct-event-table test (the decisive one)

Every method is handed the **correct** `(exit_age, role)` table, so all semantic reconstruction is
free. If separation vanished here, the task would be semantics-only and G34 would be dropped.

| Wrong object | visible | overhaul_heavy | mixed_low_risk |
|---|---|---|---|
| 1 − KM used for Q1 (competing treated as censoring) | +68.0% (**68 sd**) | +187.8% (**119 sd**) | +36.0% (**34 sd**) |
| AJ answer used for Q2 (crude substituted for net) | −40.2% (**67 sd**) | −65.1% (**118 sd**) | −25.9% (**33 sd**) |
| cumulative cause-specific hazard read as a probability | +122.0% (**122 sd**) | +269.5% (**171 sd**) | +59.9% (**57 sd**) |
| raw failure fraction | −21.4% (**22 sd**) | −16.6% (**11 sd**) | −25.2% (**24 sd**) |
| failure / (failure + overhaul) | +8.4% (**8 sd**) | +5.7% (**3.6 sd**) | +19.7% (**19 sd**) |

**R7 PASSES emphatically.** Separation runs from 3.6 to 171 sd with semantics handed over, so the
survival-specific statistical distinction — not the reconstruction — is carrying the task. This is
the opposite of the original G34 result and of G33.

The **Q1↔Q2 swap separates at 33–118 sd**. An agent that computes one quantity correctly and uses
it for the other question fails, which is the "distinguishes the business objects" property.

## R3 — textbook-shortcut attack

| Mapping | visible | overhaul_heavy | retirement_heavy | mixed_low_risk |
|---|---|---|---|---|
| correct | +0.0% | +0.1% | −0.0% | −0.1% |
| **C2 "overhaul competing, everything else censoring"** (the one-liner) | +13.2% (**14 sd**) | +8.8% (**7 sd**) | **+37.6% (65 sd)** | +17.5% (**16 sd**) |
| C1 all exits competing (admin censoring included) | −21.3% (23 sd) | −16.5% (14 sd) | −20.4% (35 sd) | −25.3% (23 sd) |
| C3 everything censored = 1 − KM | +67.3% (74 sd) | +186.4% (157 sd) | +104.6% (180 sd) | +35.2% (32 sd) |
| C7 mature cohorts only | +7.0% (8 sd) | +5.6% (5 sd) | +4.0% (7 sd) | +9.8% (9 sd) |

**R3 PASSES.** Recognising "this is competing risks, use Aalen–Johansen" is **not sufficient**: the
one-line mapping mis-roles retirement and fails at 7–65 sd, worst in the regime where retirement is
common. The analyst must decide each code's role, not just reach for the estimator.

## Inert-mechanism check, and the fix

Honest finding first: with transfers and telemetry gaps drawn **independently** of failure,
`C6 gaps-treated-as-exits` had an error of **0.1 sd — completely inert**. Independent censoring is
harmless, so the "not an exit" role was decoration.

Fix tested rather than assumed: vibration sensors degrade with the bearing they monitor, so a
telemetry gap often precedes an impending failure. With that correlation:

| | correct method | C6 gaps treated as exits |
|---|---|---|
| independent gaps (original) | −0.1% | **−0.1% (0.1 sd)** |
| **informative gaps (fixed)** | −0.1% | **−48.5% (51.2 sd)** |

The correct method is **unchanged** (−0.1% either way), because the correct handling is simply "a
gap is not an exit" — no inverse-probability weighting, so no collapse into G31. A build must adopt
the informative-gap version; the independent version would ship a decorative mechanism.

## R6 — decision structure

Gate: stock the enlarged pool iff Q1 > 0.28. 12 worlds per regime, unanimous within each:

| Regime | Q1 | decision |
|---|---|---|
| visible | 0.3293 | stock_high 12/12 |
| failure_heavy | 0.4853 | stock_high 12/12 |
| overhaul_heavy | 0.1929 | stock_base 12/12 |
| retirement_heavy | 0.2709 | stock_base 12/12 |
| mixed_low_risk | 0.2737 | stock_base 12/12 |

Two regimes high, three base, each unanimous — a 2-vs-2 fixture set defeats a constant answer
outright. Regimes differ by meaningful parameters (failure scale, overhaul interval, retirement
scale), not by seed selection.

**Decision-correct / analysis-wrong cases exist, and they flip by regime:**

| Method | visible | overhaul_heavy |
|---|---|---|
| 1 − KM (+67% / +186% wrong) | decision right **10/10** | decision wrong **0/10** |
| raw failure fraction (−21% / −17% wrong) | decision wrong 0/10 | decision right **10/10** |
| C2 overhaul-only mapping (+13% / +9% wrong) | decision right **10/10** | decision right **10/10** |

So decision-only grading would score badly wrong analyses as successes in every regime — the
property G24 and G05 showed is necessary.
