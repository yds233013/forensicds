# G35 constant-decision test and hidden regimes

## Constant-decision test  **PASS**

| strategy | correct decisions |
|---|---|
| always "launch" | 2 / 4 |
| always "hold" | 2 / 4 |

The regime set splits 2/2 by construction, and the split is driven by a scientifically meaningful
parameter (`delta`, the genuine routing efficiency) rather than by a seed choice.

## The four regimes

All share one experimental design, one estimand and one gate.  The correct method transfers unchanged;
the wrong methods fail differently in each.

| regime | courier capacity ratio | delta | tau_policy | decision | character |
|---|---|---|---|---|---|
| **visible** | 0.78 | 0.060 | 0.0434 | launch | tight market, real routing gain that survives full rollout |
| **hidden_a_tight_hollow** | 0.65 | 0.010 | 0.0062 | hold | very tight market, almost no real gain: **largest naive lift in the set sits on the smallest true effect** |
| **hidden_b_slack** | 1.05 | 0.030 | 0.0063 | hold | slack couriers: no rationing, so no interference, so the naive analysis is nearly right |
| **hidden_c_tight_real** | 0.70 | 0.090 | 0.0585 | launch | very tight market, large real gain |

## Why these four

- They vary **supply elasticity / market tightness** and **interference strength**, which the brief
  lists as legitimate regime dimensions.
- They do **not** change what treatment means: dispatch priority is the same intervention everywhere.
- `hidden_a` and `hidden_c` are the discriminating pair: nearly identical tightness and nearly
  identical naive lift (0.240 vs 0.245), opposite decisions (hold vs launch).  **No analysis that looks
  only at the treated-vs-control comparison can tell them apart.**  That pair is the core of the task.
- `hidden_b` is the negative control: an agent that reflexively applies an interference correction
  still gets it right, but an agent that has learned "the naive number is always inflated" as a slogan
  will misreport the magnitude.

## Decision flips

`hidden_a` -> `hidden_c` flips the decision while the naive estimate barely moves (0.240 -> 0.245, a
2% change) and the truth moves 9x (0.006 -> 0.059).  This is the designed reversal.
