# G10 recalibration: deviation from the pre-registration

## What failed
- **Cap breached.** Calibration with the four pre-registered correct estimators exceeded the 2.0 pp category-change
  cap:

  | Category | Tolerance (pp) |
  |---|---|
  | Breakfast cereals | 2.56 |
  | Household cleaning | 3.30 |
  | Soups & broths | 2.96 |

- **Gate failed.** In validation, nb_common_alpha passed only 17/20 worlds. Its failing ratios were 1.05, 1.10 and
  1.19 (hidden_a, hidden_b, visible).

## Investigation
- **Source of the breach.** The breach came only from `nb_common_alpha`, with category-change errors up to 2.20 pp.
- **Other estimators are well inside the cap.**
  - Worst calibration error of nb / em / nb_4week: 1.18 pp, giving tolerance 1.77, inside the cap.
  - On validation seeds the three pass 20/20 (worst ratio 0.74), with every action correct.
- **Cause: systematic misspecification, not noise.**
  - The generator's day-shock dispersion differs by category (α 2.5–6, scaled per regime).
  - A common α under-disperses sell-out days in low-α categories.
  - Those categories (Snacks, Household cleaning, Soups) carry the largest errors.
- **The data reject a common α in every graded extract.** `/private/tmp/claude-501/lrtest.py`, NB with traffic-weighted
  in-stock exposure, per-category vs common α, likelihood ratio on 7 df:

  | Extract | LR, per-category vs common α | log-lik NB − Poisson-lognormal |
  |---|---|---|
  | visible | 1130 (p < 1e-200) | +281 |
  | hidden_a | 1733 | +751 |
  | hidden_b | 1419 | +399 |
  | hidden_c | 1158 | +327 |

  The same test decisively favours the Gamma (NB) shock over the Poisson-lognormal probe.

## Deviation
- **Reclassification.** nb_common_alpha moves from "correct" to "near-miss probe": its assumption is invalid and
  rejected by an elementary check on the observed data.
- **Tolerances.** Re-derived from nb, em and nb_4week with the pre-registered floors and caps, and installed unchanged
  as `candidates/g10-censored-demand/tests/tolerances.json`.
- **Consequence for the calibration base.** It is narrower: three NB-family estimators, differing in fitting
  algorithm (IPF with grid α; EM) and season granularity.
  - Additional correct implementations (the pandas joint-MLE oracle and the Gibbs sampler) are checked on the graded
    extracts and in the mutation suite.
  - Alternative specifications from the statistical review (store × week, SKU-level α, one promo lift for all
    categories, category × period season, store only) are re-checked on the graded extracts.

## Near-miss band (recorded as validity risk, not as pass/fail guarantees)

| Method | Assumption | Validation worlds passed | Ratio range | Data check |
|---|---|---|---|---|
| nb_common_alpha | common dispersion | 17/20 | 0.19–1.19 | LR ≥ 1130 on 7 df |
| nb_lognormal | lognormal day shock | 8/20 | 0.64–1.49 | NB log-lik higher by 280–750 |
| fe_profile | traffic shape from per-day fixed-effects likelihood (inconsistent under sell-out stopping) | 7/20; fails visible and hidden_c in 5/5 seeds | — | profile from full-in-stock days differs systematically |
| profile_all_days | profile from censored days | 4/20; fails visible, hidden_a and hidden_c in 5/5 seeds | — | — |
| v3_prior | legacy forecast as prior | 2/20; fails visible, hidden_a and hidden_c in 5/5 seeds | — | — |

The reward on the fixed graded extracts is what matters. Each method's outcome there is reported in
`report/g10_prebaseline_validation.md`.
