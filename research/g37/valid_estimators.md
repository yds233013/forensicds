# Valid estimator families (C1)

| family | estimator | data consumed | assumptions | algorithm | shared code | expected bias | variance (SD / SE_REF, D2) |
|---|---|---|---|---|---|---|---|
| **F1 Deming** | b = Deming slope on (O, N̄) with δ = (σ̂_n²/2)/σ̂_o² | parallel run + dual scans + old check repeats | linear bridge, independent normal errors, δ known up to estimation | closed-form Deming | `moments`, `out` (mapping/deconvolution) | ≈ 0 (−0.12 … +0.06 SE) | 1.00 (defines SE_REF) |
| **F2 attenuation-corrected OLS** | b = cov(O, N̄) / (var(O) − σ̂_o²) | parallel run + old check repeats only | as F1; uses only the old gauge's error | reliability-ratio division | as F1 | ≈ 0 (≤ +0.26) | **1.2–2.1**: inefficient; it alone drives VALID_BOUND to 5.6 |
| **F3 replicate covariance** | b = cov(N₁, N₂) / cov(O, N̄); σ_n², σ_o² from the covariance structure | parallel run only (no external repeats, no variance subtraction for b) | as F1 | moment matching | as F1 | ≈ 0 | 0.84–1.03 |
| L1 Deming on single scans | variant | | | | | ≈ 0 | 1.2–1.3 |
| L2 moment via new-gauge error | b = (var(N̄) − σ̂_n²/2)/cov | variant | | | | ≈ 0 | 0.84–1.03 (≈ F3) |
| X10 median/MAD robust | variant | | normal data | | | ≈ 0 to +0.23 | 1.0–1.5 |

**Independence.** F1, F2 and F3 are three different estimators that use different subsets of the
evidence. F3 needs no external repeatability data at all. They are not algebraic rewrites of each
other. **Honest caveat:** a joint Gaussian MLE of the parallel run would be *just-identified* and
therefore algebraically equal to F3. It was deliberately **not** counted as a fourth family. All
families share the mapping/deconvolution step (`out`), because that step is definitional (map with
b, subtract the error variance of the reported value).

**Valid-family simulation (D2, 400 draws × 5 fixtures).** All biases are within ±0.26 SE_REF, and
the pairwise mean differences are ≤ 0.3 SE_REF. The families agree. VALID_BOUND is 5.57 with F2,
and about 3 if F2 is excluded. Excluding F2 does not change the verdict.
