# G35 coherent-but-wrong gate

The direct carry-forward of the G34 baseline finding: **internal consistency is not validation.**
G34 trial 2 produced four probabilities summing to exactly 1.000000 while using the wrong risk set and
reaching the wrong business decision; every coherence check passed.

## The constructed analyses

Each is internally consistent under the checks a reviewer would actually run.

### CW1 - total effect in the 50% arm, reported as the rollout effect

The most defensible wrong answer in the whole design.  It correctly measures the entire mixed
experiment: the treated mean, the control mean, the spillover, and the block-level total all
reconcile.  It is a **real causal effect, at the wrong saturation.**

| regime | value | error vs tau_policy | decision |
|---|---|---|---|
| visible | +0.0142 | **-0.0293** | hold (truth: launch) **WRONG** |
| hidden_a | -0.0087 | -0.0149 | hold (correct) |
| hidden_b | +0.0080 | +0.0017 | hold (correct) |
| hidden_c | +0.0342 | -0.0243 | launch (correct) |

It flips the decision on the visible regime - the one the agent sees.

### CW2 - direct + spillover summed into "total impact"

Both components are individually correct and the arithmetic is exact.  The composition is simply not
the policy contrast.  Errors **+0.008 to +0.241**; wrong decision on `hidden_a`.

### CW3 - naive A/B with order counts reconciled to the platform total

Treated orders plus control orders equal total platform orders, exactly.  Every bookkeeping identity
holds.  Errors **+0.006 to +0.234**; wrong decision on `hidden_a`.

## Result

**PASS.**  Two of the three coherent analyses reach a wrong launch decision in at least one regime, and
all three miss the graded effect size badly, while satisfying every consistency check available.

## Design consequence, carried into any build

A G35 verifier must **not** rely on coherence checks for its separation.  Specifically:

- an "effects decompose correctly" check would pass CW2;
- a "treated + control reconcile to the platform total" check would pass CW3;
- a "confidence interval computes" check passes all three.

Separation must come from **numeric comparison of all three graded objects against latent truth**, plus
the decision.  That is exactly the lesson G34's verifier taught, and it is why Q2 and Q3 are graded
rather than Q1 alone.
