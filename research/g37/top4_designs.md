# Top-4 deep round — simulation-only prototypes

All four use the same pre-registered window definitions (`sim/analyze_c1.py` docstring):

- **VALID_BOUND** = max p99 of |err| / SE_REF over the valid methods
- **detect** = p01 of |err| / SE_REF, i.e. an error shown in ≥ 99 % of draws
- **WRONG_BOUND(m)** = detect on the method's **second**-best fixture
- **Requirement:** ratio ≥ 3

Code: `sim/c1_gauge.py`, `sim/analyze_c1.py`, `sim/proto_others.py`. Results: `sim/*.json`.

| | C1 in-line gauge / latent Ppk | C2 assay transfer / lot Ppk | C7 inspection migration / prevalence | C9 CD-SEM fleet / wafer SD |
|---|---|---|---|---|
| latent DGP | coil effect (τ) + part (ω); pre/post windows, 40 coils | lot potency N(μ, σ_L) | Bernoulli(p) defects | wafer CD N(45, σ_w) |
| old instrument | contact gauge O = X + e_o (reference method) | HPLC, duplicates | human inspection | 3 matched tools |
| new instrument | laser N = NOM + c + b(X − NOM) + e_n, dual scan | UPLC N = 100 + c + b(X − 100) + e, duplicates | camera: sens / spec | 4th tool: offset + own repeatability |
| bridge | 3–4k parts, 2 coils, both gauges; old check re-measures; new dual scans; vendor steel blocks (non-commutable) | 40 retained lots on both, in duplicate | 8,000-unit audit; gold on all camera positives + 10 % of negatives | golden wafer 10× per tool |
| production sampling | pre: 1,600 SPC readings; post: 1,600 (D1) or 16,000 in-line (D2) | 60 lots/yr | 250,000 camera decisions | 600 wafers, random dispatch |
| target | latent μ₁, σ₁, Ppk₁, σ₀ | latent Ppk | p | σ_w |
| threshold | Ppk 1.33 (industry/CSR) | Ppk 1.33 (CPV policy) | 0.50 % (contract) | 1.2 nm (internal) |
| valid estimators | F1 Deming; F2 attenuation-corrected OLS; F3 replicate covariance (+ L1, L2 variants) | Deming; moments | weighted Rogan–Gladen; PPV/NPV | tool fixed-effect ANOVA; golden offsets |
| wrong estimators | 24 W + 9 X (below) | 6 | 3 | 5 |
| fixtures | 5 regimes (unchanged process / real deterioration / noisy gauge / mean-limited / shifted-low) | 3 | 3 | 3 |
| **VALID_BOUND** | **5.57** (D2) | 5.51 | 3.42 | 8.53 (after relabelling "reference tool only" as valid; was 2.91) |
| **WRONG_BOUND** (hardest) | **0.04** (X01 deconvolve on wrong scale) | 0.02 (offset-only) | 0.01 (PPV-only) | 0.03 (pooled repeatability) |
| **ratio** | **0.01** | 0.00 | 0.00 | 0.01 |
| other fatal findings | many second-order routes within 0–3 SE_REF | latent SD not identifiable at 60 lots/yr (SE_REF ≈ 40 % of σ_L; Ppk unbounded when the deconvolved variance goes negative) | SE ≈ 30 % of p; truth within 1.4 SE of the threshold | "reference tool only" is actually an unbiased, inefficient *valid* estimator (mislabelled wrong, now corrected); first-order errors only 2.5–5 SE |

All four fail the window gate. C1 is the strongest, because its first-order errors are separated at
5–60 SE_REF. It is analysed in full in the remaining files.
