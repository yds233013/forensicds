# Wrong-method panel (C1): 24 preregistered W-methods + 9 counterexamples

Every method runs on the same perfectly clean simulated tables, D2 volumes, 400 draws × 5 fixtures.
Classes map to the requested W1–W20:

| class | methods |
|---|---|
| ignore the change | W01, W22 |
| offset only | W02, W03 |
| OLS in the wrong direction / attenuation | W04, W05, W06 |
| calibrate the mean, not the variance | W07, W24 |
| variance from the wrong instrument | W09 |
| add instead of subtract | W10 |
| bridge variance as production variance | W11 |
| repeatability-divisor errors | W08, W12 |
| correct post only | W13 |
| ratio calibration | W15 |
| Cpk instead of Ppk | W16 |
| wrong error-variance ratio | W17, W18 |
| reference standards misused | W19, W20 |
| process assumed unchanged | W21 |
| correct variance, wrong mean | W23 |

Correct-decision-from-wrong-numbers cases appear in the decision columns.

Detection values are in `fixture_coverage.md`. Summary:
- **First-order** errors are separated at 5–70 SE_REF on most fixtures: raw, blocks, pooled scales,
  offset-only, OLS attenuation, adding variance, carry-over.
- **Second-order** errors sit at 0–4 SE_REF on most fixtures: wrong instrument, divisor, orthogonal
  regression, bridge variance, block repeatability, and even **W07 (no deconvolution at all)** on
  3/5 fixtures.
