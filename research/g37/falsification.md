# Falsification diagnostics available to a strong analyst (C1)

1. **Family agreement.** Deming (F1) vs replicate covariance (F3): F3 needs no external
   repeatability, so disagreement flags a wrong δ or non-independent errors. In simulation the
   families agree within ≈ 0.3 SE_REF.
2. **Commutability check.** Block repeatability (0.0035) vs dual-scan repeatability on parts
   (0.005–0.012), and the block slope (≈ 1) vs the parts slope (0.90–1.15). The mismatch shows the
   certificate does not transfer.
3. **Bridge linearity / residual check.** Residuals vs fitted in the parallel run. The bridge range
   is narrow (2 coils), so linearity is weakly testable. This is a limitation.
4. **Pre/post latent stability.** σ₀ vs σ₁ after correction, which separates a real deterioration
   (hidden_a/d) from a gauge artefact (visible/b).
5. **Held-out coil.** Refit the bridge on one coil and predict the other.

At least two meaningful diagnostics exist (1, 2 and 4), so this gate passes.
