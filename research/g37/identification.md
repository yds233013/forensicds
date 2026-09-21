# Identification (C1)

Every parameter is learned from **visible** evidence. None needs generator-only knowledge.

| parameter | learned from | method |
|---|---|---|
| σ_o² (old repeatability) | check re-measures in pre-production (every 5th part, ≈ 320 pairs) | mean(d²)/2; also from the parallel-run structure (F3) |
| σ_n² (new per-scan repeatability, on parts) | dual scans in the parallel run (3–4k pairs) | var(N₁ − N₂)/2; also var(N) − cov(N₁, N₂) (F3) |
| b (new scale on parts, reference units) | parallel run: cov(O, N̄) with an error-variance correction (F1/F2) **or** cov(N₁, N₂)/cov(O, N̄) (F3, no variance subtraction) | EIV |
| c (new offset at nominal) | parallel-run means given b | — |
| μ₁, σ₁ (post latent) | post production (station value = 2-scan mean) with b, c, σ_n²/2 | map, then deconvolve |
| σ₀ (pre latent) | pre production with σ_o² | deconvolve |

- **Not identified from blocks:** the steel blocks are non-commutable with coated parts, so they
  identify neither b nor c, and the block repeatability ≠ the repeatability on parts.
- **Old vs new vs latent variation:** separable. The old gauge has check repeats, the new has dual
  scans, and the parallel run gives the cross-covariance. The model is just-identified from the
  parallel run alone (F3) and over-identified with the external repeats (F1/F2).

**Identification is not the problem. Separation (the tolerance window) is.**
