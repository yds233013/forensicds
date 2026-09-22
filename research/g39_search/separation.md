# Structural-separation gate

**Pre-registered:**
- TOL = 0.5 % of the quantity's natural scale;
- VALID_BOUND = max(TOL, p99 of valid-route disagreement);
- WRONG_BOUND = min over wrong objects of the p05 error on the second-best regime;
- pass ≥ 3, prefer ≥ 5, strong ≥ 10.

## Exact-object tolerance (why 0.5 %)
The valid routes agree to ≤ 1e-9, so no sampling-based SE exists (principle: do not manufacture
pseudo-uncertainty). The tolerance is set by **legitimate reporting conventions**: three significant
figures, integer cores, minutes vs hours, rounding. 0.5 % covers them in every concept. It was not
chosen after seeing results.

| concept | VALID_BOUND | WRONG_BOUND (panel) | hardest panel wrong | ratio (panel) | wrong objects ≥ 10× tol (2 regimes) | < 3× tol | after counterexample search |
|---|---|---|---|---|---|---|---|
| A1_take_or_pay | 0.005 | 0.0000 | W01_lp_ignore_commitments | **0.00** | 3 / 12 | 7 | — |
| A2_atp_rebalancing | 0.005 | 0.0000 | W02_all_inbound_counted | **0.00** | 1 / 11 | 9 | — |
| A3_shared_bottleneck_mix | 0.005 | 0.0000 | W02_nominal_calendar_hours | **0.00** | 2 / 10 | 7 | — |
| A4_cloud_commitment | 0.005 | 0.0000 | W02_pool_regions | **0.00** | 4 / 11 | 4 | min over hybrids 0.0000 (X01_pooled_then_split_by_share) → ratio 0.00 |
| B1_fleet_oee | 0.005 | 0.0006 | W05_product_of_mean_factors | **0.12** | 4 / 10 | 4 | — |
| B2_labour_hours | 0.005 | 0.0011 | W03_network_average_rate | **0.22** | 6 / 10 | 4 | — |
| B3_dc_power_headroom | 0.005 | 0.0000 | W08_pooled_across_halls | **0.00** | 9 / 10 | 1 | min over hybrids 0.0141 (X01_round_down_to_12kW_rack_increments) → ratio 0.00 |
| B4_capacity_factor | 0.005 | 0.0004 | W05_capacity_weighted_unit_cf | **0.09** | 3 / 10 | 5 | — |
| C1_rolled_throughput_yield | 0.005 | 0.0001 | W06_completions_weighted | **0.02** | 7 / 10 | 3 | — |
| C2_forecast_accuracy | 0.005 | 0.0204 | W09_exclude_zero_actual_rows | **4.07** | 7 / 10 | 0 | min over hybrids 0.0000 (X01_active_proxy_any_actual_gt0) → ratio 0.00 |
| C3_like_for_like | 0.005 | 0.0000 | W06_cutoff_12_months | **0.00** | 1 / 10 | 5 | — |
| C4_recall_deployment_mix | 0.005 | 0.0005 | W06_target_mix_eval_rates | **0.10** | 0 / 10 | 10 | — |

**Result: 0 / 12 pass after the counterexample search.**
- C2 passed the preregistered panel (4.07) but fails the hybrid search.
- B3 has 9 of 10 wrong objects ≥ 10 × tolerance. It fails on one conditional trap (pooling halls) and
  one hybrid (rack-increment rounding, 2.8 ×).

## Why separation fails in deterministic structural tasks
The weak wrong objects fall into two mechanisms.

1. **Conditional traps.** A wrong object differs from the truth only when its trap is *active* in
   that world:
   - commitments bind (A1 W01/W02);
   - an urgent need-by makes a transfer infeasible (A2 W03);
   - a hall is oversubscribed (B3 W08);
   - a store sits at the 12-month cutoff (C3 W06);
   - an active SKU has no sales (C2 X01).

   Otherwise it coincides **exactly**. Such traps bite hard in one regime (A1 W01: 35 % error when
   demand is below commitments) and not at all elsewhere, so they fail the "≥ 95 % of worlds in
   ≥ 2 regimes" requirement.
2. **Genuine near-equivalences** (G36/CE06-type): weighting variants that differ by 0.1–5 % in
   typical data:
   - C4 recall weightings;
   - B1 mean vs pooled OEE;
   - C1 completions-weighted RTY;
   - B2 network-average rate;
   - A4 regional pooling.
