# IGQA (pre-build)

| quantity | contract-derived definition | units | population | time zero | horizon | weighting | derivation 1 | derivation 2 | shared helpers | semantic | computational |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q1 | mean over enrollees of Σ_h E(λ⁰ − λ¹) (`estimand.md`) | defects | suppliers enrolled in months 24–29, first enrolment | first SDP month | 6 months | per enrollee | V2 state-space | V1 pseudo-episodes | none for the graded quantity; seasonal indices computed separately | **PASS** | **PASS**; **FAIL gradability** |
| Q2 | Σ E(λ⁰ − λ¹) / Σ E λ⁰ | fraction | same | same | same | ratio of sums | V2 | V1 | none | PASS | PASS; **FAIL gradability** |
| decision | Q1 ≥ 75 | — | — | — | — | — | forced | forced | — | PASS | forced |

Semantics are pinned and computation is independent. The failure is principle 11 / 16:
**identifiable ≠ gradable.**
