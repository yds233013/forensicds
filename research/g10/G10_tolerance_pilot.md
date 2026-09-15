# G10 tolerance / identifiability pilot: hard gate result

**Status: PASSED.** Approved to build.

- **Nothing built, no model run.** Only the pilot generator and estimators existed.
- **Code:**
  - `research/g10/pilot/g10_world.py`: data-generating process, standard library, used by the build;
  - `pilot_estimators.py`: estimators and graded quantities;
  - `run_pilot.py`: seeds × regimes;
  - `summarize.py`, `validate.py`.
- **Results:**
  - `pilot_results_5seeds_base7000.json`: calibration;
  - `pilot_results_5seeds_base9000.json`: validation;
  - `tolerances_from_calibration.json`.

## 1. Protocol

1. **Generate worlds.** Worlds come from the final intended process:
   - regimes: visible, hidden_a, hidden_b (negative control / weak censoring), hidden_c;
   - calibration seeds 7000 + 13i (5 per regime); validation seeds 9000 + 13i (5 per regime);
   - 40 worlds in total, about 172k store-SKU-days each.
2. **Run estimators on observable data only.** Truth is used only for scoring.
3. **Fix tolerances on calibration.** Tolerance = 1.5 × the maximum absolute error of the four correct estimators over
   calibration seeds × regimes, with floors:
   - category change 1.5 pp;
   - forecast bias 0.5 pp;
   - demand totals 1.5%;
   - lost units 6%.
4. **Validate on fresh seeds.** Apply the fixed tolerances to validation seeds. Action labels are graded only where the
   truth is ≥ 2 pp from a ±5% threshold (149 of 160 category-world cases).

**Graded quantities** (verifier candidates; all against realised generator truth):

| Quantity | Grain |
|---|---|
| Σ expected demand | period × arm × promo (8 strata) |
| Σ lost units | period × arm and period × promo (8 strata) |
| Category baseline change | post vs pre; per category (8) |
| Buy-plan action | per category (8) |
| Forecast bias | v3 pre (all stores); v4 post (LEAN-26 stores) |

## 2. Tolerances (fixed on calibration seeds)

| Quantity | Tolerance |
|---|---|
| Category baseline change | 1.50–2.21 pp (per category) |
| Forecast bias | 0.50 pp (v3 pre), 0.56 pp (v4 post LEAN) |
| Σ expected demand, period × arm × promo | 1.50–1.86% |
| Σ lost units, period × arm / period × promo | 6.0–7.0% |

Floors are well above noise: correct-estimator error was ≤ 0.36% on large demand strata and ≤ 2.9% on lost strata.
Worst observed correct errors are 1.58 pp on category change and 0.34 pp on bias.

## 3. Validation result (fresh seeds, fixed tolerances)

**Correct estimators:**

| Estimator | Worlds passed | Reward (all 4 regimes) | Actions | Worst ratio (error / tolerance) |
|---|---|---|---|---|
| C1 NB likelihood, traffic-weighted exposure offset, per-category α, posterior imputation | **20/20** | **5/5** | 149/149 | 0.61 |
| C2 same with a common α | **20/20** | **5/5** | 149/149 | 0.76 |
| C3 EM over latent day intensities (Gamma–Poisson), independent iteration | **20/20** | **5/5** | 149/149 | 0.63 |
| C4 NB with 4-week (not weekly) category season | **20/20** | **5/5** | 149/149 | 0.61 |

**Natural wrong methods:**

| Wrong method (the assumption that fails) | Worlds passed | Reward | Weakest world (ratio) | Per-regime minimum ratio (visible / a / b / c) |
|---|---|---|---|---|
| W_A sales = demand | 0/20 | 0/5 | 21.2 | 42.0 / 54.7 / 21.2 / 43.7 |
| W_B drop censored days (selection on outcome) | 0/20 | 0/5 | 19.3 | 38.0 / 46.6 / 19.3 / 38.6 |
| W_C per-day sales ÷ traffic in-stock share (stopping-time bias) | 0/20 | 0/5 | 10.7 | 15.4 / 14.1 / 10.7 / 15.0 |
| W_C2 uniform-time in-stock scaling (ignores traffic shape) | 0/20 | 0/5 | 2.86 | 4.5 / 10.7 / 4.4 / 2.9 |
| W_D impute lost at uncensored-day mean rate (ignores that censoring is informative) | 0/20 | 0/5 | 10.5 | 21.2 / 29.8 / 10.5 / 19.9 |
| W_F Poisson GLM with exposure offset (ignores overdispersion × informative exposure) | 0/20 | 0/5 | 7.55 | 12.2 / 17.8 / 7.6 / 10.5 |
| W_T daily censored Poisson / Tobit-style (misspecified tail, no intraday information) | 0/20 | 0/5 | 9.76 | 14.0 / 17.4 / 9.8 / 11.4 |
| W_G forecast imputation (circular: forecast drives inventory) | 0/20 | 0/5 | 18.6 | 33.3 / 37.4 / 18.6 / 35.3 |
| W_H traffic profile estimated from all days (censored evenings bias the shape) | 0/20 | 0/5 | 1.07 | 3.0 / 2.7 / **1.07** / 3.1 |
| W_I NB without promotion covariate (censoring depends on an omitted covariate) | 0/20 | 0/5 | 1.80 | 2.4 / 2.6 / 1.8 / 2.9 |

**Reading.**
- Every wrong method is caught in every world.
- W_H is weakly separated only in the weak-censoring negative-control regime (1.07×). The visible extract and the other
  hidden regimes catch it at ≥ 2.7×, so its reward is 0 in every seed.
- W_I (1.8×) is the narrowest, principled "plausible" failure.

## 4. Intermediate plausible success

On calibration worlds, several wrong methods reproduce the decision-level output (category trends and buy-plan
actions) while example-level and lost-sales state is wrong:

| Wrong method | Category trends within tolerance | Actions correct (validation) | Demand totals within tolerance |
|---|---|---|---|
| W_H profile from all days | 20/20 worlds | 149/149 | 5/20 |
| W_I NB without promo | 19/20 | 149/149 | 0/20 |
| W_C2 uniform-time scaling | 7/20 | 148/149 | 0/20 |
| W_F Poisson offset | 4/20 | 126/149 | 0/20 |

A planner reading only category trends would accept W_H and W_I. Their lost-sales cost and strata totals are wrong
by 1.8–3.1× tolerance.

## 5. Identifiability checks

1. **Consistency.** All four correct estimators recover realised aggregates with errors far inside tolerance in every
   regime: they differ in iteration scheme, dispersion structure and season granularity. The estimand is recoverable
   and not tied to one implementation.
2. **Negative control.** hidden_b has weak censoring, a high share of holdout stores and no promo cut. Correct
   estimators do not manufacture demand there (strata totals within 0.4%). The upward-biased per-day scaling is caught
   at 10.7×.
3. **Evidence-supplied assumptions.** All A1–A5 (design §3) are observable or documented facts:
   - intraday shape: hourly sales on fully in-stock days and in holdout stores;
   - overdispersion: variance of uncensored daily sales;
   - stopping rule: order-up-to docs and inventory tables;
   - lost-shopper behaviour: store operations doc;
   - trading hours: calendar.
4. **Decision margins.** Truth baseline changes are:
   - ≈ −2% (flat categories);
   - −12 to −14% (declining);
   - +13 to +18% (growing).

   Action grading skips category-world cases within 2 pp of a threshold (11 of 160 in validation).

## 6. Decisions carried into the build

- **Verifier tolerances:** use `tolerances_from_calibration.json` (per quantity) unchanged.
- **Calendars:** hidden regimes will also shift calendar dates, go-live week and holiday dates, so hard-coded dates
  fail. Rerun a confirmation on the task generator with final hidden specs (2 seeds × 4 regimes, C1 and the four
  closest wrong methods) before validation sign-off.
- **Mutation suite:** includes all ten wrong methods plus overfits, patches and cheats. At least three independently
  structured correct implementations (C1 pandas oracle, C3 EM, C4-style statsmodels / season variant).
