# G35 pre-registered wrong analyses

Registered **before** the gates were run.  Code: `simulation.py::est_f1`, `gates.py::coherent_wrong`.
Errors below are against `tau_policy`, in fulfilment-rate points, measured on the frozen regimes.

| Code | Analysis | Why a competent analyst writes it | What it actually estimates | visible | hidden_a | hidden_b | hidden_c |
|---|---|---|---|---|---|---|---|
| **W1** | **Naive A/B**: pool every merchant, treated vs control | this *is* the experiment dashboard | a saturation-weighted mixture of direct effects | +0.151 | +0.234 | +0.006 | +0.187 |
| **W2** | W1 with **cluster-robust SEs** | "we accounted for clustering" | identical point estimate; only the interval changes | +0.151 | +0.234 | +0.006 | +0.187 |
| **W3** | **Block fixed effects** + individual treatment dummy | the textbook fix for clustered designs | the within-block direct effect, the most interference-contaminated object of all | +0.314 | +0.460 | +0.015 | +0.371 |
| **W5** | **Direct effect at 50%** reported as the rollout effect | the analyst has understood interference exists and measured it at the experiment's modal saturation | `tau_direct(0.5)` | +0.297 | +0.502 | +0.007 | +0.389 |
| **W6** | Treated units in **100% blocks** vs controls drawn from **mixed** blocks | uses the full-rollout arm, which feels right | contaminated: the controls are spillover-damaged | +0.130 | +0.197 | +0.002 | +0.148 |
| **W10** | Condition on **realised** adoption share rather than assigned saturation | realised exposure "is what actually happened" | post-treatment conditioning; adoption rises with merchant size | -0.015 | -0.008 | -0.000 | -0.003 |
| **W13** | **Treated units only**, against the grand mean | a before/after instinct applied to a cross-section | nothing coherent | +0.052 | +0.109 | +0.000 | +0.066 |
| **W14** | Block means **unweighted by demand** | "average the markets" | the merchant-weighted effect, when couriers are consumed by orders | -0.040 | -0.024 | -0.011 | -0.026 |
| **CW1** | **Total effect in the 50% arm** reported as the rollout effect | the most sophisticated wrong answer: correctly measures the whole mixed experiment | `E[Y(pi=.5)] - E[Y(pi=0)]`, a real effect at the wrong saturation | -0.029 | -0.015 | +0.002 | -0.024 |
| **CW2** | **direct + spillover** summed into "total impact" | both components correct; the composition looks like a decomposition | neither object | +0.145 | +0.241 | +0.008 | +0.205 |
| **CW3** | Naive A/B presented with **order counts reconciled to the platform total** | every bookkeeping check passes | same as W1 | +0.151 | +0.234 | +0.006 | +0.187 |
| **C10** | Direct effect measured in the **25% arm** only | one saturation level is enough | `tau_direct(0.25)` | +0.204 | +0.417 | +0.001 | +0.280 |

## Two honest negatives

Two pre-registered wrong methods turned out **not to be reliably wrong in this DGP**, and are recorded
as such rather than quietly dropped:

- **W10 (realised saturation).**  Errors of -0.015 to -0.000.  On `hidden_c` its error (0.003) is
  *smaller* than the worst valid estimator's (0.005).  Size-tilted adoption makes it biased in
  principle, but not enough to be a dependable trap.  It must not be relied on for separation.
- **hidden_b_slack disarms almost every wrong method.**  With slack courier capacity there is no
  rationing, so there is no interference, so the naive comparison is nearly right (+0.006).  This is
  scientifically correct behaviour, not a design defect: it is the regime that tests whether the
  agent's method is *principled* rather than reflexively "always apply the interference correction".
  Separation in that regime comes from the other graded objects, not from Q1.

## Failure-taxonomy placement

- **W1, W2, W3, W5, W6, C10** - F9: right method family, wrong statistical object.
- **CW1** - F9 in its most defensible form: a correct effect at the wrong saturation.
- **W10** - F7: conditioning on a post-treatment quantity.
- **W14** - F10-adjacent: right object, wrong weighting, and therefore sometimes the wrong decision.
- **CW2, CW3** - the G34 lesson made concrete: internally coherent, externally wrong.
