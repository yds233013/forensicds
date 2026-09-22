# Counterexample search (top 3: C2, B3, A4) — hybrids and locally reasonable alternatives

Labels were fixed before running (`sim/g39_counterexamples.py`), on the same worlds as the panel.

| concept | alternative | pre-label | 2nd-regime p05 | coincidence | median per regime |
|---|---|---|---|---|---|
| A4_cloud_commitment | X01_pooled_then_split_by_share | wrong | 0.0000 | 0.61 | 0.004 / 0.011 / 0.004 / 0.002 / 0.003 |
| A4_cloud_commitment | X02_ceil_vs_floor_quantile_rounding | valid-alt | 0.0000 | 0.90 | 0.003 / 0.002 / 0.002 / 0.002 / 0.003 |
| A4_cloud_commitment | X03_include_sunk_existing_in_cost | valid-alt | 0.0000 | 1.00 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 |
| A4_cloud_commitment | X04_p75_usage_rule_of_thumb | wrong | 0.1148 | 0.00 | 0.271 / 0.239 / 0.261 / 0.226 / 0.205 |
| A4_cloud_commitment | X05_weekday_only_profile | wrong | 0.0336 | 0.00 | 0.041 / 0.044 / 0.036 / 0.040 / 0.041 |
| B3_dc_power_headroom | X01_round_down_to_12kW_rack_increments | wrong | 0.0141 | 0.07 | 0.018 / 0.024 / 0.083 / 0.022 / 0.030 |
| B3_dc_power_headroom | X02_pf_applied_twice | wrong | 0.2636 | 0.07 | 0.280 / 0.277 / 0.999 / 0.339 / 0.384 |
| B3_dc_power_headroom | X03_reserved_half_counted | wrong | 0.0458 | 0.03 | 0.066 / 0.068 / 0.564 / 0.096 / 0.478 |
| B3_dc_power_headroom | X04_peak_minus_10pct_safety_on_usable | wrong | 0.2636 | 0.07 | 0.280 / 0.277 / 0.999 / 0.339 / 0.384 |
| B3_dc_power_headroom | X05_mean_of_avg_and_peak | wrong | 0.2419 | 0.01 | 0.138 / 0.137 / 3.579 / 0.413 / 0.219 |
| C2_forecast_accuracy | X01_active_proxy_any_actual_gt0 | wrong | 0.0000 | 1.00 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 |
| C2_forecast_accuracy | X02_mae_over_mean_actual | valid-alt | 0.0000 | 1.00 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 |
| C2_forecast_accuracy | X03_volume_weighted_mape | valid-alt | 0.0000 | 1.00 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 |
| C2_forecast_accuracy | X04_winsorised_errors_cap_3x_actual | wrong | 0.0057 | 0.24 | 0.009 / 0.024 / 0.011 / 0.008 / 0.002 |
| C2_forecast_accuracy | X05_exclude_zero_forecast_rows | wrong | 0.0007 | 0.68 | 0.002 / 0.125 / 0.002 / 0.002 / 0.003 |
| C2_forecast_accuracy | X06_mean_of_store_wape | wrong | 0.0051 | 0.17 | 0.014 / 0.070 / 0.016 / 0.013 / 0.004 |
| C2_forecast_accuracy | X07_drop_first_week | wrong | 0.0006 | 0.54 | 0.004 / 0.009 / 0.004 / 0.003 / 0.005 |

## Findings
- **C2.** "Active = any actual > 0" coincides in **100 %** of worlds. In this DGP no active SKU goes
  8 weeks × 10 stores without a sale, so the proxy is the object here. Excluding zero-forecast rows
  (coincidence 68 %), dropping the first week (54 %), winsorising errors (median ≈ 1 %) and the mean
  of store WAPEs (≈ 1.4 %) all sit within or near tolerance. **C2 fails.**
- **B3.** Rack-increment rounding (12 kW) lands at 1.8–8 % median. That is 2.8 × tolerance on the
  second-best regime, below 3. It is also a *legitimate operational convention*: the contract would
  have to pin continuous vs rack-granular headroom, which is a semantic risk. **B3 fails.**
- **A4.** Pooled-then-split-by-share coincides in 61 % of worlds. **A4 fails.**
- The relative errors on B3 have huge p99 values because the truth is ≈ 0 kW in some hot-hall worlds
  (a scale artefact); detection is unaffected.

No exclusion rule was invented.
