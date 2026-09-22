# Counterexample search (R1) — HARD GATE: **FAILED**

Every wrong and ambiguous route from the existing 200-draw run. Units are SE_REF (the RMSE of V2).
- "detect" = |error| shown in ≥ 99 % of draws.
- WRONG_BOUND = detect on the second-best fixture.
- Combinations are included: W04b (exclude trigger + seasonal), W07 (exclude trigger + DiD), W28
  (exclude trigger + EB shrinkage), W26 (correct model with a wrong fixed ρ), W24 (correct model with
  contaminated hyperparameters).

| method | kind | bias Q1 (SE_REF) vis/a/b/c/d | RMSE-ish SD Q1 | detect (p01) per fixture | WRONG_BOUND (2nd) | decision correct % vis/a/b/c/d |
|---|---|---|---|---|---|---|
| W04b_pre_mean_excl_trigger_seasonal | wrong | -1.0 / -0.5 / -2.2 / -0.5 / -0.4 | 1.0 / 1.3 / 1.4 / 1.0 / 0.5 | 0.0 / 0.0 / 0.2 / 0.0 / 0.0 | 0.02 | 100 / 99 / 48 / 100 / 100 |
| W09_match_S_historical_any_month | ambiguous | +0.3 / +0.6 / -0.4 / +0.3 / -0.3 | 1.3 / 1.1 / 1.3 / 1.4 / 0.6 | 0.0 / 0.1 / 0.0 / 0.0 / 0.0 | 0.02 | 100 / 80 / 94 / 100 / 100 |
| W24_hyperparameters_from_all_months | wrong | +0.1 / +0.1 / +0.1 / +0.2 / +0.8 | 1.0 / 1.0 / 1.0 / 0.9 / 0.6 | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | 0.02 | 100 / 93 / 99 / 100 / 86 |
| W16_v2_no_seasonality | wrong | -0.6 / -0.5 / -0.5 / -1.5 / +0.4 | 1.0 / 1.0 / 1.0 / 1.0 / 0.6 | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | 0.02 | 100 / 99 / 97 / 100 / 94 |
| W26_v2_fixed_rho_half | wrong | +0.2 / +0.5 / -1.3 / +0.2 / +0.3 | 1.0 / 0.9 / 1.1 / 0.9 / 0.5 | 0.0 / 0.0 / 0.1 / 0.0 / 0.0 | 0.02 | 100 / 88 / 89 / 100 / 96 |
| W28_pre_mean_excl_trigger_shrunk_to_fleet | wrong | -0.9 / -0.4 / -2.1 / -0.2 / -0.4 | 1.0 / 1.3 / 1.4 / 1.0 / 0.5 | 0.0 / 0.0 / 0.2 / 0.0 / 0.0 | 0.03 | 100 / 99 / 52 / 100 / 99 |
| W27_v1_fit_all_unit_months | ambiguous | -0.5 / -0.2 / -0.6 / -0.2 / -0.2 | 1.3 / 1.6 / 1.3 / 1.4 / 0.6 | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | 0.03 | 99 / 92 / 93 / 100 / 97 |
| W22_v1_no_seasonal_adjustment | wrong | +0.1 / +0.1 / +0.1 / +0.1 / +0.1 | 1.8 / 1.9 / 1.6 / 1.6 / 0.7 | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | 0.03 | 100 / 86 / 98 / 100 / 96 |
| W14_v2_no_measurement_noise | wrong | +0.1 / +0.3 / -1.0 / +0.6 / +0.3 | 1.0 / 1.0 / 1.1 / 0.9 / 0.4 | 0.0 / 0.0 / 0.0 / 0.0 / 0.0 | 0.03 | 100 / 92 / 92 / 100 / 97 |
| W07_did_excluding_trigger_window | wrong | -1.5 / -1.0 / -2.9 / -1.0 / -0.6 | 1.1 / 1.2 / 1.4 / 1.0 / 0.5 | 0.0 / 0.0 / 0.5 / 0.0 / 0.0 | 0.03 | 99 / 100 / 28 / 100 / 100 |
| W21_v2_iid_transient | wrong | -0.6 / -0.2 / -2.0 / -0.3 / +0.3 | 1.0 / 1.1 / 1.3 / 0.9 / 0.4 | 0.0 / 0.0 / 0.2 / 0.0 / 0.0 | 0.04 | 100 / 98 / 58 / 100 / 96 |
| W13_q2_supplier_average | wrong | +0.2 / +0.1 / +0.2 / +0.3 / +0.8 | 1.0 / 1.0 / 1.0 / 1.0 / 0.6 | 0.0 / 0.0 / 0.0 / 0.0 / 0.7 | 0.04 | 100 / 93 / 100 / 100 / 86 |
| W05_did_never_enrolled | wrong | -0.9 / -0.4 / -2.4 / -0.7 / -0.4 | 1.0 / 1.2 / 1.3 / 1.0 / 0.5 | 0.0 / 0.0 / 0.3 / 0.0 / 0.0 | 0.05 | 100 / 98 / 44 / 100 / 100 |
| W17_wrong_time_zero | wrong | -0.6 / +0.1 / -0.4 / -1.3 / +0.3 | 0.9 / 0.9 / 0.8 / 0.9 / 0.6 | 0.1 / 0.0 / 0.0 / 0.5 / 0.0 | 0.06 | 100 / 97 / 100 / 100 / 95 |
| W23_launch_cohort_only | wrong | +1.3 / +0.2 / +0.7 / +2.3 / +1.3 | 1.9 / 2.3 / 1.8 / 1.7 / 1.5 | 0.1 / 0.0 / 0.0 / 0.1 / 0.0 | 0.09 | 100 / 82 / 97 / 100 / 66 |
| W12_raw_counts | wrong | -1.2 / -0.6 / -2.3 / -1.8 / -0.6 | 1.1 / 1.2 / 1.3 / 1.1 / 0.5 | 0.0 / 0.0 / 0.1 / 0.1 / 0.0 | 0.09 | 100 / 100 / 44 / 100 / 100 |
| W01_pre_post_trigger_window | wrong | +2.0 / +2.7 / +0.5 / -1.8 / +0.7 | 1.3 / 1.1 / 1.1 / 1.4 / 0.5 | 0.1 / 0.2 / 0.0 / 0.0 / 0.0 | 0.10 | 100 / 10 / 99 / 100 / 96 |
| W03_all_pre_mean | wrong | -1.2 / -0.6 / -2.4 / -1.8 / -0.6 | 1.0 / 1.1 / 1.3 / 1.0 / 0.5 | 0.0 / 0.0 / 0.2 / 0.1 / 0.1 | 0.10 | 100 / 99 / 44 / 100 / 100 |
| W20_treated_trend_extrapolation | wrong | +1.4 / +1.3 / +1.5 / -3.4 / -0.1 | 1.7 / 1.4 / 1.7 / 1.9 / 0.7 | 0.0 / 0.1 / 0.0 / 0.6 / 0.0 | 0.10 | 100 / 52 / 99 / 100 / 98 |
| W04_pre_mean_excluding_trigger | wrong | -1.6 / -1.1 / -2.7 / -1.8 / -0.8 | 1.0 / 1.2 / 1.4 / 1.0 / 0.5 | 0.1 / 0.0 / 0.3 / 0.1 / 0.0 | 0.13 | 99 / 100 / 31 / 100 / 100 |
| W10_match_H_only_historical | wrong | -2.9 / -2.2 / -3.6 / -1.5 / -1.3 | 1.3 / 1.6 / 1.6 / 1.4 / 0.6 | 0.2 / 0.3 / 0.8 / 0.1 / 0.3 | 0.31 | 72 / 100 / 15 / 100 / 100 |
| W08_match_trigger_value_contemporaneous | wrong | -3.4 / -2.7 / -3.5 / -5.8 / -1.5 | 2.0 / 1.6 / 1.8 / 2.4 / 0.8 | 0.2 / 0.1 / 0.5 / 1.9 / 0.3 | 0.46 | 51 / 99 / 21 / 85 / 100 |
| W02_dashboard_ppm_change | wrong | +2.0 / +2.7 / +0.5 / -1.8 / +0.7 | 1.3 / 1.1 / 1.1 / 1.4 / 0.5 | 0.5 / 1.4 / 0.0 / 0.0 / 0.7 | 0.71 | 100 / 10 / 99 / 100 / 96 |
| W06_event_study_ref_trigger_window | wrong | +3.7 / +4.1 / +1.8 / +1.4 / +1.3 | 1.4 / 1.3 / 1.2 / 1.4 / 0.6 | 0.7 / 1.6 / 0.1 / 0.1 / 0.1 | 0.72 | 100 / 0 / 100 / 100 / 65 |
| W11_rd_extrapolation | ambiguous | -2.9 / -2.6 / -3.0 / -4.0 / -2.1 | 1.6 / 1.2 / 1.4 / 1.9 / 0.9 | 0.2 / 0.1 / 0.6 / 0.8 / 1.0 | 0.82 | 74 / 100 / 22 / 100 / 100 |
| W18_future_info_filter | wrong | -5.4 / -0.4 / -4.3 / -9.4 / -0.4 | 1.4 / 1.3 / 1.0 / 1.8 / 0.6 | 4.0 / 0.0 / 3.2 / 10.1 / 0.0 | 4.00 | 2 / 94 / 0 / 4 / 99 |
| W15_population_mean_cf | wrong | -10.9 / -8.4 / -9.9 / -19.7 / -3.8 | 2.0 / 1.5 / 1.8 / 3.2 / 1.0 | 17.8 / 14.3 / 18.1 / 39.4 / 6.4 | 18.08 | 0 / 100 / 0 / 0 / 100 |

## Closest wrong routes
- **W04b** (pre-mean excluding the trigger window, seasonally adjusted): bias −0.4 … −2.2, WRONG_BOUND **0.02**.
- **W16** (V2 without seasonality) and **W26** (V2 with ρ fixed at 0.5): bias ≤ 1.5, WRONG_BOUND 0.02.
- **W21** (iid transients): bias −0.3 … −2.0.
- **W05/W07** (DiD variants): bias up to −3.1, but volatile.

The naive **dashboard (W01)** has a bias of +2.0 SE_REF on visible and +2.7 on hidden_a
(≈ +104 and +158 defects per enrollee). That is business-material, and it still fails the detect
criterion (0.10), because its own spread overlaps zero.

**No exclusion rule was invented.**
