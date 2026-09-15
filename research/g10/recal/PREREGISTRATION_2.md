# G10 recalibration round 2: pre-registration

Written 2026-09-15, before round-2 calibration or validation was run.

## Trigger
- **A false failure on a graded extract.** Round-1 tolerances were fitted to nb, em and nb_4week. On the graded
  extracts, a separate NB fit per category, a defensible correct specification from the statistical review, failed
  visible on `lost::post0_lean0`: +8.6% against a 6.07% tolerance.
- **The failing stratum is small.** It holds lost units in the 4 holdout stores before go-live: about 7.0k units. Even
  nb sits at +4.2% there.
- **Two problems:**
  1. The calibration base (three NB fits with the same covariates) understates legitimate variation across defensible
     specifications.
  2. The before-go-live lean/holdout split grades a stratum with no decision value: before go-live both arms had the
     same policy.

## Changes (fixed now)

### Graded lost-unit strata

| Before go-live | From go-live |
|---|---|
| all stores | LEAN-26 arm |
| promo / non-promo | holdout arm |
| — | promo / non-promo |

- `lost_share` is graded for the two from-go-live arms.
- The before-go-live per-arm values in `programme_impact.json` stay required, and are checked for consistency with
  `demand_history.csv` only.

### Correct specification set (calibration and validation)
All use NB with traffic-weighted in-stock exposure and posterior imputation:
- `nb`: IPF, store×period + SKU + weekday + category×week + category×promo, α per category;
- `em`: EM over latent intensities;
- `nb_4week`: 4-week category season;
- `store_week`: store×week instead of store×period;
- `sep_cat`: separate fit per category (store×period×category, SKU, category×weekday, category×week, category promo);
- `alpha_sku`: dispersion per SKU;
- `promo_common`: one promotion effect for all categories;
- `cat_period_only`: category×period level, no within-period season;
- `store_only`: store effect without period.

Excluded: `nb_common_alpha`, rejected by the data (DEVIATION.md). It stays a probe with `nb_lognormal` and
`fe_profile`.

### Unchanged
- Floors: totals 1.5%, lost 6%, bias 1.0 pp, category change 1.5 pp. Cap: category change 2.0 pp.
- Multiplier 1.5 × max |error| over the correct set and calibration seeds 7000 + 13i, i = 0..4, per regime.
- Validation on seeds 9000 + 13i, i = 0..4.

## Decision rules
1. **Gate:** every correct specification passes every validation world. A breach of a cap fails the gate. In either
   case, investigate before any further change.
2. **Wrong methods** (sales, drop_censored, per_day_scale, uniform_time_scale, mean_rate_impute, poisson_offset,
   daily_censored_poisson, forecast_impute, profile_all_days, nb_no_promo, forecast_prior, v3_prior, nb_plugin):
   - each must fail every graded extract set, i.e. reward 0 on the four graded extracts;
   - its validation pass rate per regime is reported;
   - a wrong method passing all four graded extracts is a gate failure.
3. **Probes** are reported, not gated.
4. **Separation:** the report gives every method's error/tolerance ratio on the graded extracts.
