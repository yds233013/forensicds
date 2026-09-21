# IGQA — v1.1

## Part 1 — response under R_load (unchanged record, from the halted calibration stage)
- (1) Computational independence **PASS**: truth A (world helpers) vs truth B (contract-only
  reimplementation) agree to about 1e-16 on all fixtures. Estimator route A (load ratio) vs route B
  (absolute reduction ÷ baseline) differ by 2.4e-16.
- (2) Semantic independence **PASS**: the contract text yields R_load. R_season is excluded by the
  stated evaluation point.

| fixture | R_load |
|---|---|
| visible | 0.0763716529 |
| hidden_a | 0.0534018673 |
| hidden_b | 0.1713685284 |
| hidden_c | 0.0531190986 |
| hidden_d | 0.1119853131 |

## Part 2 — after the O2 response-removal decision

| quantity | semantic | computational | status |
|---|---|---|---|
| `target_peak_kw` | **PASS**: "mean peak-window kW per residential customer … every customer on the tariff … under the forecast weather" admits one reading | **PASS**: F1/F2/F3 independent (v1 K9, pairwise \|t\| ≤ 1.82); SE_REF reproduced to ~4e-9 | reward-bearing (proposed) |
| `procurement_decision` | **PASS**: ceiling stated in the memo | algebraically forced by the forecast and the 3.057 kW ceiling | reward-bearing (proposed) |
| `estate_tou_response_at_target_cdd` | the definition is identified (Part 1) | the definition is computable (Part 1) | **NOT REWARD-BEARING — diagnostic / report-only.** It is **not** described as passing IGQA on account of being ungraded. It **fails gradability**: its estimate cannot be separated from a nearby wrong aggregation (0.92 vs 0.99 SE_REF). |

**IGQA is necessary but not sufficient.** The forecast passes IGQA and still fails the section-9
counterexample search (CE06).
