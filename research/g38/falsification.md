# Falsification diagnostics available to a strong analyst

1. **Pseudo-trigger dates.** Apply the rule in the pre-programme era (months 11–16). The "effect"
   there must be ≈ 0. This is the evidence V1 uses; a placebo on it tests V2.
2. **Pre-treatment placebo.** Shift t0 back six months for enrollees and estimate an "effect" on
   untreated months.
3. **Counterfactual calibration on historical trigger episodes.** Compare predicted and realised
   post-6 counts for pseudo-episodes.
4. **Residual mean reversion.** Autocorrelation of filtered residuals (a check on ρ).
5. **V1 vs V2 agreement.** Independent evidence; they agree within ≈ 0.2 SE_REF except for the
   small-count approximation (hidden_d).

At least two meaningful diagnostics exist, so the gate passes. They were not run as separate
experiments, because new simulation was prohibited. They are available by construction.
