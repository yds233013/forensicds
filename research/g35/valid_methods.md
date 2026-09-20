# G35 legitimate estimator families

Four families that reach `tau_policy` by different machinery.  Code: `simulation.py::est_f1`, keys
prefixed `V_`.  Errors against latent truth, fulfilment-rate points.

| family | machinery | visible | hidden_a | hidden_b | hidden_c |
|---|---|---|---|---|---|
| **V1 saturation contrast** | demand-weighted block means, 100% arm minus 0% arm | -0.0002 | -0.0013 | -0.0012 | +0.0048 |
| **V2 saturation curve** | weighted fit of block outcome on saturation, evaluated at 1 vs 0 | -0.0001 | +0.0004 | -0.0014 | +0.0037 |
| **V3 design regression** | block regression with city and day effects plus saturation indicators | +0.0017 | -0.0002 | +0.0006 | +0.0028 |
| **V4 arm means** | mean of each of the five arms, differenced | -0.0002 | -0.0013 | -0.0012 | +0.0048 |

**Worst error across all four families and all four regimes: 0.0048.**  All four agree on all four
launch decisions.  This satisfies K11 and is the property that took the most design work to obtain.

## How K11 was nearly failed, and what fixed it

The first working design gave block-level courier capacity a large city component
(`cap_city_sigma = 0.15`).  Every family remained unbiased, but the simple contrast picked up a
standard deviation of 0.009-0.015 against effects of 0.006-0.059, and **only the design regression
decided all four regimes correctly**.  That is a K11 violation: the most natural correct analysis -
comparing the fully-treated arm with the untreated arm - would have failed the task.

The fix was to shrink nuisance heterogeneity (`cap_city_sigma` 0.15 -> 0.06, `cap_day_sigma`
0.08 -> 0.04), not to bless one estimator.  **G35 is a task about choosing the right estimand; it must
not become a task about variance reduction.**  After the change the four families agree to 0.005.

## Deliberately not separate families

- **Horvitz-Thompson with explicit design weights.**  Under complete randomisation of a fixed
  saturation it reduces algebraically to V1.  Listing it would be padding.
- **Cluster-robust inference.**  A variance method, not an estimator.  Applying it to the naive point
  estimate is W2 and is wrong; applying it to V1 is correct and changes nothing about the point.
- **Mixed-effects models.**  An efficiency refinement of V3 with the same estimand.

## A valid-but-restricted route, measured

Restricting to the **largest quartile of blocks** and applying V1 gives 0.041 / 0.013 / 0.005 / 0.070
against truths of 0.043 / 0.006 / 0.006 / 0.059 - all four decisions correct, errors up to 0.007.  It
is a legitimate if wasteful analysis and, unlike G34's oldest-quartile case, it survives.  Any
tolerance must be set wide enough to admit it.
