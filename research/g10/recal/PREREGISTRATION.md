# G10 tolerance recalibration: pre-registration

Written 2026-09-14, after the independent reviews and the generator change, and before any validation result was
inspected.

## Why recalibrate
- **Adversarial review.** The v3 forecast was the generator's true mean plus noise, and v4 was built from realised
  arrivals, so forecasts leaked truth. Forecasts are now built only from past observed sales: v3 is a 28-day moving
  average, and v4 is trained on clean days and then frozen.
- **Statistical review.** The tolerances came from the pilot generator. Other changes since the pilot:
  - the short-hours double count was fixed;
  - hidden seasons were changed for realism;
  - the multipliers were retuned: visible 1.8 / 1.25 / 1.8; hidden_a lean 1.15; hidden_b 2.4 / 2.0 / 2.4.

## Protocol
The pilot protocol is unchanged, but now runs on the task generator and the DB-based estimators
(`tools/g10/recalibrate.py`).
- **Calibration:** seeds 7000 + 13i, i = 0..4, for each of 4 regimes. Correct estimators: nb, em, nb_common_alpha,
  nb_4week. Tolerance = max(floor, 1.5 × max |error|).
- **Validation:** seeds 9000 + 13i, i = 0..4, for each regime.
  - The same correct estimators.
  - Wrong methods: sales, drop_censored, per_day_scale, uniform_time_scale, mean_rate_impute, poisson_offset,
    daily_censored_poisson, forecast_impute, profile_all_days, nb_no_promo, forecast_prior, v3_prior, nb_plugin and
    fe_profile.
  - Probe: nb_lognormal.

## Floors and caps (fixed now, from the reviews, independent of validation outcomes)

| Family | Floor | Cap | Reason |
|---|---|---|---|
| Demand totals | 1.5% | — | unchanged |
| Lost units | 6% | — | unchanged |
| Forecast bias | **1.0 pp** (was 0.5) | — | 6% lost-unit accuracy × ~20% post-LEAN lost share ≈ 1.2 pp. The old 0.5 pp silently bound lost units to ~2.5% (statistical review). |
| Category change | 1.5 pp | **2.0 pp** | cap equals the 2 pp action-grading margin, so an estimate inside tolerance cannot flip a graded action (statistical review) |

If a calibrated tolerance exceeds its cap, the calibration fails and the cause is investigated.

## Decision rules
1. **Gate:** every correct estimator passes every validation world (20/20). Otherwise the gate fails: investigate
   first, never widen tolerances ad hoc.
2. **Wrong methods:** each must fail in every regime's majority of seeds, and must fail at least one graded extract.
   A wrong method that passes ≥ 3/5 worlds of some regime is recorded as insufficiently separated in that regime.
3. **Probe nb_lognormal (Poisson-lognormal day shock):**
   - **Passes ≥ 18/20:** treat as an acceptable correct alternative. No action.
   - **Fails ≥ 18/20 with a median worst ratio ≥ 1.3:** record it as an intended discriminator: the day-shock tail
     assumption, checkable by likelihood comparison on uncensored days.
   - **Otherwise (borderline):** the grade is a coin flip for a defensible analysis. Add an explicit resolution:
     - either document an observable fact that settles the shock shape (e.g. from store operations), or
     - include nb_lognormal among the calibration estimators and re-derive tolerances, then re-check rule 2.
