# G34 simulation results

Five decisive tests. Two bugs in my own code were found and fixed before any conclusion was drawn;
both are recorded because the process matters more than the result.

## 0. Two bugs found in my own instruments

**Generator bug (found by the first pre-check).** The reference estimator appeared biased +36%. The
cause was mine: units whose latent failure or overhaul would have occurred *before* the monitoring
window were still being kept in the fleet, producing records with `exit < entry` — impossible fleet
records. Isolated by a controlled ladder (no censoring → truncation only → truncation unfiltered),
which reproduced the bogus 0.5775 against a truth of 0.4043 and confirmed the filtered version at
0.4033. **This is the "is the record even possible?" check earning its place**, exactly as the G33
post-mortem recommended.

**Estimator bug.** `V2` (discrete-time hazard) was biased −13% to −18%. Two causes: a risk set that
counted units entering mid-interval, and — after fixing that — the classic downward bias of a
monthly life-table when censoring is heavy inside the interval. Censoring here is heavy precisely
inside the decision window, because the overhaul falls at its start. Replacing it with an
**actuarial half-interval adjustment** brought the three valid families into agreement.

## 1. Is the core identifiable? (test 1)

| Overhaul policy | Truth | V1 left-truncated KM | Verdict |
|---|---|---|---|
| age-based, condition-independent | 0.4053 | 0.4058 (+0.1%) | identified ✓ |
| **condition-based (half of failures pre-empted)** | 0.4053 | **0.0800 (−80%)** | **not identified** |

Every method fails in the condition-based branch, correct ones included. **The informative-censoring
variant is unusable for a net estimand** — it would have to become a different task.

## 2. Valid-family agreement (test 2, K11)

After the actuarial fix, over 12 worlds per regime:

| Regime | truth | V1 KM | V2 actuarial | V3 Weibull MLE | spread |
|---|---|---|---|---|---|
| visible | 0.4035 | 0.3894 (−3.5%) | 0.3864 (−4.2%) | 0.4078 (+1.1%) | 5.3% |
| older_fleet | 0.4035 | 0.3844 (−4.7%) | 0.3799 (−5.8%) | 0.4015 (−0.5%) | 5.4% |
| robust_units | 0.2195 | 0.2110 (−3.9%) | 0.2084 (−5.1%) | 0.2209 (+0.6%) | 5.7% |

Three families within 5.3–5.7%. **Caveat recorded:** V3's precision (sd 0.012–0.026 vs 0.035–0.051)
is partly rigged — the generator is Weibull, so a Weibull MLE is correctly specified. It should not
be treated as evidence of parametric superiority.

## 3. Does each claimed mechanism separate? (test 3)

At 30,000 units, against the correct estimator's own sd of 0.0235:

| Method | bias | relative | |bias| / sd(V1) | bites? |
|---|---|---|---|---|
| V1 (correct) | +0.0013 | +0.3% | 0.1 | — |
| **W5 overhaul counted as the event** | +0.5897 | **+148%** | **25.1** | yes |
| **W2 monitoring clock (wrong time origin)** | −0.1919 | **−48%** | **8.2** | yes |
| W3 naive event rate | −0.0506 | −13% | 2.2 | marginal |
| **W1 ignore delayed entry** | −0.0279 | **−7.0%** | **1.2** | **no** |

## 4. Does delayed entry ever bite? (test 4)

| monitoring go-live | % entering at age > 0 | W1 bias | in sd of V1 |
|---|---|---|---|
| month 14 | 35.5% | −0.8% | 0.1 |
| month 36 | 43.5% | −10.0% | 2.2 |
| month 54 | 43.8% | −7.8% | 3.5 |
| month 84 | 43.8% | −8.9% | 1.1 |

The truncation fraction saturates near 44% and the bias plateaus at 8–10% regardless of fleet age.
**Left truncation is a weak, non-scalable mechanism here** — an order of magnitude below the time
origin (−48%) and the removal-reason error (+148%). It cannot be the core, and claiming it would
repeat the G31 inert-mechanism error.

## 5. The crude-risk variant (test 5)

Cause-specific cumulative incidence with planned overhaul as a **competing event** rather than
censoring, 20,000 units, 8 worlds:

| Regime | Aalen–Johansen CIF | 1 − KM | gap | in sd of AJ |
|---|---|---|---|---|
| visible | 0.2936 (sd 0.0035) | 0.5207 (sd 0.0155) | **+77.4%** | **65.2** |
| robust_units | 0.1498 (sd 0.0040) | 0.3118 (sd 0.0168) | **+108.1%** | **40.5** |

An order of magnitude stronger than anything in the net-risk design.

**Honest caveat: this test compares two estimators to each other, not to generator truth.**
Aalen–Johansen is theoretically consistent for the CIF under these conditions, so the gap is almost
certainly 1 − KM's bias — but verifying AJ against the latent truth is the first thing a redesign
must do, before anything else is built.

## 6. Constant-decision attack

| Regime | mean p_fail(18,30] | decisions over 12 worlds |
|---|---|---|
| visible / older_fleet / young_fleet / noisy_monitoring | 0.4048 | hold 12/12 |
| robust_units | 0.2184 | **extend 12/12** |

Pooled, constant "hold" is correct **48/60 = 80%**. Unlike G33, the decision is **unanimous within
each regime** rather than straddling by seed, so a frozen fixture set of two "hold" and two "extend"
extracts defeats a constant answer outright — the mechanism G05 already uses. Recorded as
manageable, not as a kill.

A secondary weakness: four of the five regimes share the same latent failure distribution and
therefore the same truth (0.4048). A build would need regimes that vary the hazard itself.
