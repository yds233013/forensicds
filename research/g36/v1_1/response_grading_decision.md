# Decision record — the estate response is not gradable (external decision O2)

## The finding that forced it
The preregistered measured-window calibration (`tolerance_calibration.md`, unchanged) gave:

- worst legitimate estimator error: **0.92 SE_REF**
- `segment_unweighted_mean` (a wrong aggregation): **0.99 SE_REF**

No tolerance admits the valid estimators and rejects the nearby wrong aggregation. The available data
do not identify R_load sharply enough to tell legitimate estimation from equal-segment weighting. So
the response cannot be an independently graded quantity. This is a property of the estimand in this
DGP, not a verifier that is too lax.

## Preserved development history (not softened)
1. **F8 defect.** The original G36 verifier graded `R_household = Σ p_s r_s`. The contract describes a
   load-weighted reduction (`research/g36/adjudication/response_estimand.md`).
2. **Correction adjudicated.** R_load = (L0 − L1)/L0 at the target mean CDD.
3. **Response K9 passed** under R_load (`response_k9.md`).
4. **Tolerance window failed** (0.92 vs 0.99).
5. **Post-hoc 1.3× separability rule.** After seeing the failed window I added a rule excluding wrong
   methods within 1.3 × the lower bound, which gave m = 2.4. The rule and its threshold were chosen
   after seeing the result. **It was reverted before any verifier modification, build, freeze or
   replay.** It was never written to `scenarios.py`, never built, and no saved submission was
   touched.
6. **External decision O2.** Make the response report-only. O1 (the exclusion rule) is explicitly
   not used.

## What O2 then required, and what happened
O2 was conditional on the forecast alone remaining a strong discriminator (authorisation §9). The
counterexample search (`counterexample_search.md`) found that it does not. A wrong modelling route
that composes the forecast with the segment-unweighted response passes the forecast verifier on every
graded extract. The O2 verifier edit was therefore **not applied**, and v1.1 is **ABANDONED,
DEVELOPMENT-ONLY**.
