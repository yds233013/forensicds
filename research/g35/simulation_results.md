# G35 simulation results

`simulation.py` (design, truth, estimators) and `gates.py` (coherent-wrong, cheap solves).
No model call, no container, no network.  Runtime ~30 s.

## 1. Mechanism-strength gate  **PASS**

Truth by counterfactual replay on the *same* demand and capacity draw as the experiment.

| regime | tau_policy | decision | naive A/B | naive error | direct(0.5) | spillover(0.5) | naive / truth |
|---|---|---|---|---|---|---|---|
| visible | 0.0434 | launch | 0.1942 | +0.1508 | 0.3329 | -0.1420 | **4.5x** |
| hidden_a_tight_hollow | 0.0062 | hold | 0.2397 | +0.2336 | 0.5056 | -0.2448 | **38.7x** |
| hidden_b_slack | 0.0063 | hold | 0.0126 | +0.0064 | 0.0193 | -0.0061 | 2.0x |
| hidden_c_tight_real | 0.0585 | launch | 0.2452 | +0.1867 | 0.4499 | -0.1913 | **4.2x** |

`hidden_a` is the sharpest case in the set: the **largest** naive lift in the whole design (+0.240)
sits on the **smallest** true effect (+0.006).  Almost all of the measured lift is displacement.

`hidden_b` is the deliberate negative control: slack courier capacity means no rationing, hence no
interference, hence a nearly-correct naive estimate.  Interference strength is a consequence of
scarcity, and the design shows that rather than asserting it.

## 2. A measurement bug in my own harness, and its correction

The first run showed every valid estimator carrying a +0.003 to +0.009 bias and getting 2 of 5
decisions wrong.  Cause: `truth_f1` seeded its block draw with `seed + 7777` while `world_f1` used
`seed`, so the "truth" was the estimand of a **different population** than the one the experiment
sampled.  Fixed by forcing both through `_block_draw`.  Post-fix bias is -0.0012 to +0.0004.
No conclusion in this document predates the fix.

## 3. Correct-data-table gate  **PASS**

Every analysis receives perfect operational semantics - correct block boundaries, correct assignment
log, correct demand, correct outcome definition.  The only remaining mistake available is ignoring
interference or targeting the wrong saturation.

| analysis | visible | hidden_a | hidden_b | hidden_c |
|---|---|---|---|---|
| V1 saturation contrast | -0.0002 | -0.0013 | -0.0012 | +0.0048 |
| V2 saturation curve | -0.0001 | +0.0004 | -0.0014 | +0.0037 |
| V3 design regression | +0.0017 | -0.0002 | +0.0006 | +0.0028 |
| V4 arm means | -0.0002 | -0.0013 | -0.0012 | +0.0048 |
| W1 naive A/B | +0.1508 | +0.2336 | +0.0064 | +0.1867 |
| W3 block FE direct | +0.3137 | +0.4603 | +0.0148 | +0.3711 |
| W5 direct as policy | +0.2973 | +0.5018 | +0.0068 | +0.3885 |
| W6 full vs mixed controls | +0.1301 | +0.1965 | +0.0024 | +0.1479 |
| W13 treated only | +0.0522 | +0.1091 | +0.0001 | +0.0664 |
| W14 unweighted blocks | -0.0401 | -0.0237 | -0.0105 | -0.0261 |
| W10 realised saturation | -0.0150 | -0.0075 | -0.0001 | -0.0033 |

Separation survives a perfect data table.  **G35 is an interference benchmark, not a data-cleaning
benchmark.**

## 4. Three graded objects are separately estimable  **PASS**

Bias and sampling sd over 12 replications per regime:

| regime | object | truth | bias | sd |
|---|---|---|---|---|
| visible | direct(0.5) | 0.3329 | +0.0013 | 0.0035 |
| visible | spillover(0.5) | -0.1422 | +0.0004 | 0.0048 |
| hidden_a | direct(0.5) | 0.5056 | +0.0018 | 0.0040 |
| hidden_a | spillover(0.5) | -0.2444 | -0.0014 | 0.0064 |
| hidden_b | direct(0.5) | 0.0193 | -0.0016 | 0.0022 |
| hidden_b | spillover(0.5) | -0.0061 | +0.0022 | 0.0026 |
| hidden_c | direct(0.5) | 0.4499 | +0.0013 | 0.0042 |
| hidden_c | spillover(0.5) | -0.1913 | -0.0027 | 0.0060 |

The three objects differ by up to two orders of magnitude within one regime.

## 5. Decision margins  **PASS**

Distance from the 0.015 gate in units of the design regression's sd (~0.0024-0.0038):

| regime | tau_policy | distance to gate | margin |
|---|---|---|---|
| visible | 0.0434 | 0.0284 | ~9 sd |
| hidden_a | 0.0062 | 0.0088 | ~3 sd |
| hidden_b | 0.0063 | 0.0087 | ~3 sd |
| hidden_c | 0.0585 | 0.0435 | ~13 sd |

An earlier regime set had margins of **0.14 sd and 0.51 sd** - the correct estimator could not decide
them.  That is G34's `hidden_a` defect repeating, and it was fixed by choosing operating points on the
physics of the generator, before any model was run.  It is regime selection, not tolerance tuning.

## 6. Finalist comparison: why the auction incident lost

| | dispatch priority (I1) | bid optimiser (I2) |
|---|---|---|
| truth `tau_policy` | 0.0434 | -0.1307 |
| naive A/B | 0.1942 | -0.0816 |
| valid saturation contrast | 0.0432 | -0.1144 |
| **naive error / abs(truth)** | **3.5x** | **0.6x** |

In a second-price auction the private gain from better bidding and the social loss from a higher
clearing price partly offset *within the same advertiser's surplus*, so the naive estimate is wrong but
not dramatically wrong.  Dispatch priority separates by an order of magnitude more.  **Measured, not
assumed.**
