# Recognition vs execution (H0 / H1 / H2)

| id | H1 (failure class revealed) | H2 (exact trap revealed) | execution left under H2 | verdict |
|---|---|---|---|---|
| A1 | "contracts matter" | "commitments are sunk; rank by price per good part" | formulate a small LP / greedy | **collapses**: two sentences give the method |
| A2 | "stock isn't all available" | "use ATP and lead-time-feasible transfers" | build a transport / max-flow | moderate |
| A3 | "a shared resource" | "the paint shop binds" | LP | collapses (OR) |
| A4 | "commitment sizing" | "newsvendor on the hourly regional residual, in cores, net of expiring commitments" | compute a quantile per region | **collapses** |
| B1 | "OEE definitions differ" | "Σ good × ideal cycle time / planned production time; cavities" | one aggregation | **collapses** |
| B2 | "units differ" | "convert per site; direct hours" | one conversion per site | collapses |
| B3 | "usable ≠ nameplate" | the five engineering facts | a formula | **collapses** |
| B4 | "capacity basis" | "AC / derated MW × COD hours" | a formula | collapses |
| C1 | "rework hides losses" | "RTY = Π FPY, starts-weighted" | a formula | collapses |
| C2 | "aggregation level" | "SKU-store-week, active SKUs" | one groupby | **collapses** |
| C3 | "comparable stores" | "the 13-month rule, exclude remodels/closures" | filter + ratio | collapses |
| C4 | "mix shift" | "weight by forecast fraud share" | a weighted mean | collapses |

**Structural finding: the pinning / execution tension.** To be semantically sharp (principle 8), the
contract must pin the object's definition. For deterministic B and C objects, **pinning the
definition is pinning the computation**. Only A2 (and partly A1/A3) retain execution after H2, and
those have OR character.
