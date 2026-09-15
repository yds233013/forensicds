# G10 recalibration round 2: result

**Gate: PASSED** under the rules in `PREREGISTRATION_2.md`.

**Artifacts** (in `research/g10/recal/`):
- `cal_*.json`, `val_*.json`: raw aggregates and errors per regime × seed × method;
- `tolerances_recal.json`: installed as `candidates/g10-censored-demand/tests/tolerances.json`;
- `worst_errors_calibration.txt`;
- `validation_summary.txt`;
- `graded_extracts/ratios_round2.txt`.

Round 1 is archived in `round1/`, and its deviation is recorded in `DEVIATION.md`.

## Tolerances

| Family | Tolerance |
|---|---|
| Demand totals | 1.5% (post × lean × promo: 1.63%) |
| Lost units | 6.0% (pre × promo: 7.1%) |
| Category change | 1.5–1.79 pp (all ≤ 2.0 pp cap) |
| Forecast bias | 1.0 pp (floor) |

## Validation (fresh seeds 9000 + 13i, 5 per regime, 20 worlds)
- **Correct specifications** (nb, em, nb_4week, store_week, sep_cat, alpha_sku, promo_common, cat_period_only,
  store_only): **20/20 each**, worst error/tolerance ratio 0.86 (sep_cat), all graded actions correct.
- **Wrong methods, weakest world ratio:**

  | Method | Weakest ratio | Worlds passed |
  |---|---|---|
  | sales | 16.7 | 0/20 |
  | drop_censored | 15.4 | 0/20 |
  | forecast_impute | 15.4 | 0/20 |
  | mean_rate_impute | 8.9 | 0/20 |
  | per_day_scale | 7.5 | 0/20 |
  | daily_censored_poisson | 7.1 | 0/20 |
  | poisson_offset | 5.7 | 0/20 |
  | nb_plugin | 5.4 | 0/20 |
  | uniform_time_scale | 3.3 | 0/20 |
  | nb_no_promo | 2.1 | 0/20 |
  | forecast_prior | 1.6 | 0/20 |
  | profile_all_days | 0.67 | 4/20, all in hidden_b; fails visible, hidden_a and hidden_c in 5/5 |
  | v3_prior | 0.77 | 2/20, both in hidden_b; fails visible, hidden_a and hidden_c in 5/5 |

- **Probes:**

  | Probe | Worlds passed | Ratio range |
  |---|---|---|
  | nb_common_alpha | 19/20 | 0.17–1.16 |
  | nb_lognormal | 8/20 | 0.64–1.49 |
  | fe_profile | 7/20 | 0.32–1.78 |

## Graded extracts (visible, hidden_a, hidden_b, hidden_c)
- **Correct implementations, all PASS on all four:**
  - reference oracle (pandas joint MLE);
  - Gibbs data augmentation;
  - nb, em, nb_4week, store_week, sep_cat, alpha_sku, promo_common, cat_period_only, store_only.

  Worst ratio 0.68 (sep_cat, visible, lost).
- **Faulty deployed code and all 14 wrong methods, including holdout_transfer:** fail at least one extract (reward 0).
  Smallest per-method worst ratios:

  | Method | Worst ratio | Extract |
  |---|---|---|
  | profile_all_days | 2.36 | hidden_c |
  | v3_prior | 3.86 | hidden_a |
  | nb_no_promo | 4.33 | hidden_a |
  | forecast_prior | 4.79 | hidden_c |

- **Probes:** each fails at least one extract.

  | Probe | Failing ratio | Extract |
  |---|---|---|
  | nb_common_alpha | 1.59 | hidden_a, category change |
  | nb_lognormal | 1.23 | visible, lost |
  | fe_profile | 1.51 | visible, lost |

## Residual validity risks
- **nb_common_alpha is effectively inside tolerance on fresh seeds (19/20).** On the graded extracts only hidden_a
  (category change, 1.59×) excludes it.
  - Its assumption (one dispersion for all categories) is rejected by the data: LR ≥ 1130 on 7 df
    (`tools/g10/lrtest_dispersion.py`).
  - But its reward-0 outcome depends on that one extract. Other implementations of common α could land either side.
  - Classify it as a near-miss whose grade is not robust. It is not a principled, well-separated wrong method.
- **nb_lognormal and fe_profile fail by 1.2–1.5× on the graded extracts.** Their assumptions are data-checkable
  (NB log-lik +280 to +750 over lognormal; the fixed-effects profile is inconsistent under sell-out stopping), but
  separation is thin.
- **hidden_b is a weak-censoring control, not a null.** It does not grade near-zero loss.
