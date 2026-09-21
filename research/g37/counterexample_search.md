# Counterexample search (C1) — HARD GATE: **FAILED**

Methods were added **beyond** the preregistered panel and labelled before scoring:
- `X01` rescale, then deconvolve (wrong order)
- `X02` offset-mapped mean + Deming variance
- `X03` best-linear-predictor per part, then SD
- `X04` common σ pre/post
- `X05` single-reading reliability applied to 2-scan means
- `X06` Deming δ ignoring scan averaging
- `X07` OLS + deconvolution + offset mean
- `X08` geometric-mean regression
- `X09` Deming δ from blocks
- `X10` robust median/MAD, a legitimate variant

| closest wrong routes | mechanism | bias (SE_REF) by fixture, D2 | detect 2nd fixture | fixtures rejecting at min admissible tol |
|---|---|---|---|---|
| **X01 deconvolve on the wrong scale** | error ∝ σ_n²(1 − 1/b²)/σ², second-order in (b − 1) × noise share | Ppk +1.4, −0.3, +1.4, +1.1, −0.3 | **0.04** | 0/5 |
| **X02 offset-only mean mapping** | error ∝ (b − 1)(μ_post − μ_bridge) | mean +1.6, −4.0, 0.0, +6.7, +1.7 | 0.18 | 0/5 |
| W09 wrong instrument's variance | ∝ \|σ_o² − σ_n²/2\| / σ² | Ppk −0.7, +3.6, −5.5, +1.9, +0.8 | 1.66 | 1/5 |
| X06 δ ignoring scan averaging | slope bias via δ | Ppk −5.1, −4.4, −4.0, −5.7, −4.6 (bias large, but volatile) | 1.91 | 0/5 |
| W11 bridge variance | 2-coil bridge variance is volatile | Ppk +5.6 … +26.8 (bias), volatile | 2.01 | 0/5 |

## Neutral redesigns tried (logged; none targeted a specific method)

| iteration | change | VALID_BOUND | WRONG_BOUND | ratio |
|---|---|---|---|---|
| D1 | SPC-sample volumes | 5.76 | 0.04 (X01) | 0.01 |
| D2 | realistic in-line volumes (every part logged; manual bridge capped at 4k) | 5.57 | 0.04 (X01) | 0.01 |
| D3 | **feasibility-frontier probe, not a design**: reliability ≤ 0.6, \|b − 1\| ≥ 0.25 (unrealistic gauges) | 5.70 | 0.17 (X02) | 0.03 |

**Why it is structural.** The same quantity that makes second-order mistakes large (measurement
error as a share of the observed variance, and scale distortion) also inflates the valid
estimators' uncertainty. So the ratio cannot be pushed past 3 by choosing regimes. X02's effect
depends on (b − 1)·Δμ, not on gauge quality.

**No exclusion rule was invented.**
