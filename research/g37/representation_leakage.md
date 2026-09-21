# Representation leakage audit (C1 design, not built)

| channel | risk | mitigation in the design |
|---|---|---|
| row order | the generation order could track coil / latent value | shuffle presentation (as in G34/G36) |
| sample counts | regimes could differ in volumes | identical volumes across fixtures (D2: 1,600 pre, 16,000 post, 4,000 bridge) |
| filenames / instrument IDs | the new gauge ID could encode the regime | constant IDs |
| bridge-study size, replicate counts | could reveal noise level | identical across fixtures |
| missingness | none in the design | — |
| metadata | vendor certificate identical across fixtures (blocks always "perfect") | by design |
| fixture shapes | the station value precision (rounding) could reveal the scan-averaging divisor | round all values to 1 µm in every fixture |

No leakage channel found in the design. Moot, because the task will not be built.
