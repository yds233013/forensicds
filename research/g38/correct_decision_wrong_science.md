# Correct decision / wrong science (R1)

The question: how many wrong methods produce the correct rollout decision despite wrong effect estimates?

| wrong method | fixtures with \|bias\| ≥ 1 SE_REF | min decision-correct rate over fixtures |
|---|---|---|
| W17_wrong_time_zero | 1/5 | 95 % |
| W16_v2_no_seasonality | 1/5 | 94 % |
| W14_v2_no_measurement_noise | 1/5 | 92 % |
| W26_v2_fixed_rho_half | 1/5 | 88 % |
| W24_hyperparameters_from_all_months | 0/5 | 86 % |
| W13_q2_supplier_average | 0/5 | 86 % |
| W22_v1_no_seasonal_adjustment | 0/5 | 86 % |
| W23_launch_cohort_only | 3/5 | 66 % |
| W21_v2_iid_transient | 1/5 | 58 % |
| W20_treated_trend_extrapolation | 4/5 | 52 % |
| W28_pre_mean_excl_trigger_shrunk_to_fleet | 1/5 | 52 % |
| W04b_pre_mean_excl_trigger_seasonal | 1/5 | 48 % |
| W05_did_never_enrolled | 1/5 | 44 % |
| W12_raw_counts | 3/5 | 44 % |
| W03_all_pre_mean | 3/5 | 44 % |
| W04_pre_mean_excluding_trigger | 4/5 | 31 % |
| W07_did_excluding_trigger_window | 3/5 | 28 % |
| W08_match_trigger_value_contemporaneous | 5/5 | 21 % |
| W10_match_H_only_historical | 5/5 | 15 % |
| W01_pre_post_trigger_window | 3/5 | 10 % |
| W02_dashboard_ppm_change | 3/5 | 10 % |
| W06_event_study_ref_trigger_window | 5/5 | 0 % |
| W18_future_info_filter | 3/5 | 0 % |
| W15_population_mean_cf | 5/5 | 0 % |

WRONG methods: 24; decision correct ≥ 90 % on ALL fixtures: 3; of those, with |bias| ≥ 1 SE_REF on ≥ 2 fixtures: 0

**Reading.** Only three wrong methods are decision-correct on every fixture, and none of them is
materially wrong on two or more fixtures. The expected G24/G10-style phenomenon ("right decision,
wrong science") **does not arise sharply here**. The reason is not that wrong methods are harmless.
It is that their errors are the same size as legitimate noise, so both the decision and the
continuous quantity are noisy for everyone. No continuous quantity carries gradable information
beyond the decision, **because no valid window exists for Q1 or Q2**.
