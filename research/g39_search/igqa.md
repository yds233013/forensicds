# IGQA (pre-build, top 12)

| check | result |
|---|---|
| **Semantic** | Every target was written mathematically from the business request (`family_*.md`) before simulation. **Pass** for all 12, with residual risks: B3 needs the peak definition and rack granularity pinned; C2 needs "active SKU" pinned by flag, not by sales. |
| **Computational** | Two independent routes per concept agree to ≤ 1e-9. **Pass** for all 12. |
| **Gradability** | **Fail** for all 12 (`separation.md`, `counterexamples.md`). |
