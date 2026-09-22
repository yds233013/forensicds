# G38 DGP (simulation prototype, R1 supplier SDP)

```
alpha_i ~ N(log 600 ppm, sa²)                  persistent supplier propensity (process capability)
u_it     = rho·u_i,t−1 + eta_it,  eta ~ N(0, se²)  supplier-specific transient shocks (lots, staff, tooling)
s_t      = season · sin(2πt/12)                 fleet-wide seasonality (common, removable)
λ⁰_it    = exp(alpha_i + s_t + u_it)            latent untreated defect rate
E_it     = E_i · exp(0.15 z),  E_i ~ logN(log Emed, Esd)   parts received (exposure varies ~100×)
D_it     ~ Poisson(E_it · λ_it),  λ = λ⁰(1 − δ_i) while enrolled, δ_i ~ clip(N(δ̄, 0.08), 0, 0.6)
trigger  : end of month t ∈ 23..28, rolling-3-month ppm > 1,500 and not yet enrolled → enrol at t+1 for 6 months
```

The model has four components, and no more:
- a persistent level;
- serially correlated supplier-specific shocks;
- a common seasonal pattern;
- Poisson observation noise.

The treatment effect is multiplicative. There is no secular trend (to stay off G05 ground), no
spill-over, and no exit.

- **Scale:** 600 suppliers, 36 months, 84–118 enrollees per fixture. This matches a mid-size
  tier-1's active supplier base.
- **Why RTM occurs.** The trigger fires on D in months t0−3..t0−1. A supplier crosses 1,500 ppm
  because α is high *or* because u and Poisson noise are high in that window. Conditional on
  crossing, E[u_{t0−1} + Poisson noise] > 0. Afterwards the Poisson noise is fresh and u decays at
  rate ρ, so the observed rate falls even with δ = 0.
- **Why it is not RTM alone.** α varies more than the transient does (sa 0.55–0.80 on the log
  scale). Enrollees therefore differ in persistent risk, and the counterfactual must separate the
  persistent level from the part of the shock that *persists* (ρ) and the part that does not.
