# Valid/wrong tolerance window — **FAIL at every scale**

Definitions were pre-registered in `sim/analyze_g38.py`, identical in form to G37.

| scale | VALID_BOUND (p99, SE_REF) | from | WRONG_BOUND | hardest wrong | ratio |
|---|---|---|---|---|---|
| R1 suppliers (600) | **5.67** | L1 on hidden_c | **0.02** | W04b | **≈ 0.00** |
| R2 warehouses (60) | **9.16** | L1 on visible | **0.02** | W14 | **≈ 0.00** |
| R3 depots (250) | **7.89** | L3 on hidden_c | **0.03** | W14 | **≈ 0.00** |

Required: ≥ 3 with headroom. **FAIL decisively.**

## Systematic bias vs sampling variance (R1)
- **Valid families.** Systematic bias ≤ 0.3 SE_REF, except V2 at +0.8 on hidden_d. Sampling SD
  0.5–1.9 SE_REF.
- **Wrong families.** Systematic bias mostly 0.3–3.6 SE_REF. Only W15 (−3.8 … −19.7) and W18
  (−0.4 … −9.4) have a bias that dominates their spread.

The overlap is not an artefact of the strict p01/p99 criterion. Even comparing **mean biases**, the
first-order dashboard error (≤ 2.7) is smaller than the valid bound implied by legitimate SDs
(≈ 2.6 at p99 for the efficient family alone).

## Why the window fails
- **A. Valid-estimator uncertainty.** The truth is each enrollee's realised untreated path. No
  correct analyst can predict an enrollee's *future* supplier-specific shocks, so the counterfactual
  carries irreducible uncertainty. At 84–118 enrollees this is 32–60 defects per enrollee, roughly
  the size of the business threshold (75).
- **B. First-order wrong methods.** At the operational 3-month trigger, the naive dashboard is only
  ≈ 2 SE_REF away (+2.0 visible, +2.7 pure-RTM).
- **C. Subtle wrong methods.** Excluding the trigger window, ordinary DiD, iid shocks and dropping
  seasonality land within ≈ 1 SE_REF of correct on most fixtures.

No verifier tolerance separates valid from important wrong analysis.
