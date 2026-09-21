# Fixture coverage (C1, D2)

detect = the error in SE_REF that a method shows in ≥ 99 % of draws. A method counts as rejected by
a fixture only if detect exceeds VALID_BOUND (5.57), the smallest tolerance that admits every valid
family. That tolerance has **zero** valid-side headroom, which is itself a failure.

| method | kind | vis | a | b | c | d | rejected at min admissible tol (> 5.57) |
|---|---|---|---|---|---|---|---|
| X01_deconvolve_on_wrong_scale | wrong_counterexample | 0.0 | 0.0 | 0.1 | 0.0 | 0.0 | 0/5 |
| X02_offset_mean_deming_variance | wrong_counterexample | 0.0 | 0.2 | 0.0 | 3.5 | 0.0 | 0/5 |
| W09_subtract_wrong_instrument | wrong | 0.0 | 1.7 | 6.5 | 0.8 | 0.0 | 1/5 |
| X06_deming_ignore_scan_averaging_in_delta | wrong_counterexample | 2.3 | 1.7 | 1.8 | 1.9 | 1.7 | 0/5 |
| W11_bridge_variance_as_production | wrong | 0.4 | 2.5 | 0.2 | 0.4 | 2.0 | 0/5 |
| X08_geometric_mean_regression | wrong_counterexample | 0.0 | 2.3 | 3.0 | 2.0 | 0.0 | 0/5 |
| X03_predict_each_part_then_sd | wrong_counterexample | 2.4 | 0.1 | 5.6 | 2.2 | 0.7 | 1/5 |
| W19_block_repeatability_deconvolution | wrong | 2.6 | 0.0 | 6.0 | 1.3 | 0.1 | 1/5 |
| X05_attenuation_corrected_single_reading_reliability | wrong_counterexample | 2.7 | 0.1 | 10.7 | 1.4 | 0.3 | 1/5 |
| W17_orthogonal_regression | wrong | 0.0 | 3.2 | 4.4 | 1.1 | 0.1 | 0/5 |
| W13_correct_post_raw_pre | wrong | 2.8 | 3.4 | 2.2 | 5.2 | 2.5 | 0/5 |
| W08_subtract_per_scan_variance | wrong | 3.6 | 0.2 | 10.9 | 3.2 | 1.0 | 1/5 |
| X09_deming_ratio_from_blocks | wrong_counterexample | 5.1 | 0.2 | 9.7 | 3.7 | 2.9 | 1/5 |
| W12_duplicate_difference_not_halved | wrong | 3.6 | 2.6 | 10.9 | 5.2 | 2.2 | 1/5 |
| W07_deming_no_deconvolution | wrong | 3.3 | 3.4 | 6.8 | 5.2 | 2.5 | 1/5 |
| W15_ratio_calibration | wrong | 5.2 | 5.5 | 1.8 | 6.1 | 3.5 | 1/5 |
| W18_deming_ratio_inverted | wrong | 0.1 | 6.5 | 9.1 | 3.0 | 0.6 | 2/5 |
| W05_ols_old_on_new_inverted | wrong | 6.7 | 3.8 | 12.8 | 5.6 | 5.7 | 4/5 |
| W16_cpk_within_coil | wrong | 6.3 | 12.8 | 4.1 | 3.8 | 8.2 | 3/5 |
| X04_common_sigma_pre_post | wrong_counterexample | 0.0 | 8.5 | 0.0 | 0.0 | 10.0 | 2/5 |
| W04_ols_new_on_old | wrong | 7.9 | 9.3 | 5.2 | 10.7 | 6.5 | 4/5 |
| X07_ols_with_deconvolution_both_periods_offset_mean | wrong_counterexample | 7.9 | 9.3 | 5.2 | 10.7 | 6.5 | 4/5 |
| W06_ols_single_scan | wrong | 7.8 | 9.3 | 4.7 | 11.0 | 6.2 | 4/5 |
| W10_add_variance | wrong | 8.0 | 7.7 | 14.2 | 10.7 | 6.5 | 5/5 |
| W03_bridge_mean_offset | wrong | 11.9 | 4.2 | 11.8 | 12.0 | 2.5 | 3/5 |
| W24_correct_mean_raw_sd | wrong | 11.9 | 3.6 | 11.8 | 12.0 | 0.4 | 3/5 |
| W21_pre_period_carryover | wrong | 0.8 | 17.7 | 0.1 | 37.7 | 14.5 | 3/5 |
| W22_pooled_old_new_raw | wrong | 55.6 | 39.1 | 63.2 | 20.8 | 45.7 | 5/5 |
| W02_vendor_block_calibration | wrong | 57.2 | 35.3 | 63.1 | 11.5 | 43.3 | 5/5 |
| W20_blocks_only | wrong | 57.2 | 35.3 | 63.1 | 11.5 | 43.3 | 5/5 |
| W01_raw_post | wrong | 62.4 | 41.6 | 69.9 | 14.0 | 49.2 | 5/5 |
| W23_correct_sd_raw_mean | wrong | 62.4 | 41.6 | 69.9 | 14.0 | 49.2 | 5/5 |

**Summary:**
- Only **16 of 32** wrong or counterexample methods are rejected by ≥ 2 fixtures.
- Rejections per fixture: visible 13, hidden_a 13, **hidden_b 18**, hidden_c 14, hidden_d 13.
  hidden_b, the noisiest new gauge, carries the most second-order discrimination.
- **W07 (no measurement-error deconvolution, the core EIV error) is rejected on only 1/5.** Even with
  F2 excluded (VALID_BOUND ≈ 3), several second-order routes remain at < 3 on ≥ 4 fixtures.
- **Gate: FAIL.**
