# G38 recommendation — **C. DROP** (accepted by external review)

## Core finding
**G38 isolated the intended phenomenon.** Selection into the intervention is based on an extreme
stochastic realisation. The G05 ablation shows naive-method bias collapsing to ≈ 0 under exogenous
timing, so the difficulty is genuinely regression to the mean / endogenous threshold triggering, not
staggered-treatment confounding.

**But it cannot be sharply graded** at realistic enterprise scale and trigger policy:

| scale | VALID_BOUND | WRONG_BOUND | ratio |
|---|---|---|---|
| R1 suppliers (600) | 5.67 | 0.02 | ≈ 0.00 |
| R2 warehouses (60) | 9.16 | 0.02 | ≈ 0.00 |
| R3 depots (250) | 7.89 | 0.03 | ≈ 0.00 |

Required ≥ 3. **FAIL at all three scales.** Decision/tolerance compatibility also fails (hidden_a
1.34, hidden_d 1.43 SE_REF from the rollout line).

## Why
- **(A)** Irreducible counterfactual uncertainty: future supplier-specific shocks are unpredictable.
- **(B)** At the operational 3-month trigger, the naive dashboard is only ≈ 2 SE_REF away.
- **(C)** Subtle mistakes (exclude the trigger window, DiD, iid shocks, no seasonality) sit within
  ≈ 1 SE_REF.

## Major negative result: the trigger window
A 1-month trigger makes RTM bias large (≈ 7.3 SE_REF). Supplier-quality practice uses a rolling
quarter, so adopting a 1-month trigger would be **benchmark tuning for separation**. It is rejected
and will not be rerun.

## Prohibited rescues (none will be attempted)
| rescue | why prohibited |
|---|---|
| shorten the trigger window | it contradicts operational policy (above) |
| increase transient-shock variance / reduce persistent heterogeneity | noise engineered to amplify RTM, not taken from the business setting |
| enlarge the sample purely for verifier power | 600 suppliers is realistic; a multiple of it is not this incident |
| drop inefficient but legitimate estimators (V1, L1–L3) | it narrows the valid band artificially; a legitimate analyst may use them |
| tighten the tolerance | it would fail legitimate analyses |
| invent an exclusion rule for nearby wrong estimators | explicitly forbidden since G36 |
| select fixtures to amplify RTM | fixture engineering |
| alter the business threshold | the break-even is fixed by cost economics |
| add a reward-bearing intermediate | G36's lesson: intermediates need their own window, and none exists here |

**Any future RTM task must come from a different, naturally separable business setting, not a
retuned G38.**
