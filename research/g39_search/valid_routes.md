# Valid routes (≥ 2 per concept, computing the same object)

| id | V1 | V2 | independence | measured disagreement (p99, relative) |
|---|---|---|---|---|
| A1 | LP epigraph (z ≥ x, z ≥ m) | sunk-commitment + merit order on p/y (exact for a separable single commodity) | different algorithm and formulation | < 0.5 % (≤ 1e-9) |
| A2 | LP transportation | Edmonds–Karp max-flow | independent algorithms | ≤ 1e-9 |
| A3 | LP | vertex enumeration (84 bases) | independent algorithms | ≤ 1e-9 |
| A4 | marginal-core rule | brute force over Q | independent | 0 |
| B1 | row-level sums | per-plant loss tree (A×P×Q), PPT-weighted | algebraic decomposition, separate code path | ≤ 1e-12 |
| B2 | site hours per unit | weekly UPH route | separate path | ≤ 1e-12 |
| B3 | hall usable − peak − reserved | module-path computation | separate path | ≤ 1e-12 |
| B4 | ΣE / Σ capacity-hours | capacity-hour-weighted unit CF | algebraic | ≤ 1e-12 |
| C1 | product of FPY, starts-weighted | first-pass flow propagation | separate path | ≤ 1e-12 |
| C2 | row-level WAPE | store-decomposed | separate path | ≤ 1e-12 |
| C3 | pooled comparable ratio | traffic-share route | separate path | ≤ 1e-12 |
| C4 | fraud-share weights | expected-count route | separate path | ≤ 1e-12 |

**Relabelled as valid** (pre-labelled wrong or alternative, found algebraically equivalent; disclosed):
- **A1 `W03_force_x_ge_m`.** Forcing purchases up to the minimum costs nothing extra, because the
  minimum is paid anyway.
- **A4 `X03_include_sunk_existing_in_cost`.** Same argmin.
- **C2 `X02` (MAE/mean actual) and `X03` (volume-weighted MAPE).** Both are algebraically WAPE.
- **Implementation error, not a wrong object: C3 `W10_relative_change_as_pp`.** It re-expressed the
  relative change on the pp scale, which is identical by construction. A real "relative-change"
  report would be in the wrong unit.
