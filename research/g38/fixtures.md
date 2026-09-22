# Fixtures (5 regimes; scientific axes fixed before scoring)

| fixture | regime | enrollees | truth Q1 mean [p05, p95] | truth Q2 | SE_REF Q1 / Q2 | \|E Q1 − 75\| | distance / SE_REF | truth decision |
|---|---|---|---|---|---|---|---|---|
| visible | baseline (ρ .5, σ_η .30, δ̄ .25) | 84 | 238.8 [181.9, 320.0] | 0.251 | 46.2 / 0.0347 | 163.8 | 3.54 | expand |
| hidden_a | pure RTM (δ̄ 0, σ_η .40, ρ .3) | 101 | 0.0 [0.0, 0.0] | 0.000 | 56.0 / 0.0488 | 75.0 | 1.34 | hold |
| hidden_b | persistent shocks (ρ .8, δ̄ .20) | 85 | 211.7 [161.3, 276.2] | 0.201 | 59.6 / 0.0423 | 136.7 | 2.29 | expand |
| hidden_c | heterogeneity dominates (σ_α .8, σ_η .2, δ̄ .30) | 115 | 387.9 [299.6, 507.9] | 0.298 | 39.4 / 0.0203 | 312.9 | 7.94 | expand |
| hidden_d | small suppliers, strong season (δ̄ .12) | 114 | 28.9 [18.8, 42.3] | 0.122 | 32.2 / 0.0993 | 46.1 | 1.43 | hold |

**Axes:**
- effect size (0 → 0.30);
- transient variance and persistence (ρ 0.3 / 0.5 / 0.8);
- persistent heterogeneity (σ_α 0.55 / 0.80);
- exposure imbalance (hidden_d: small suppliers);
- seasonality (0.10 / 0.20).

No fixture was created or modified to kill a method.

## Coverage
In the existing run, only **W15** (5/5 fixtures) and **W18** (3/5) are rejected on ≥ 2 fixtures at
*any* tolerance at or above VALID_BOUND. Every other important wrong method is rejected on **0**
fixtures. Coverage is not one-fixture-dependent. It is **absent**.
