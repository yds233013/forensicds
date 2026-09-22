# Deterministic invariants

| id | invariants available | constrain the intended object? |
|---|---|---|
| A1 | cost ≥ Σ p m (sunk floor); Σ y x ≥ D | partly: W03-type reformulations satisfy them too |
| A2 | flow conservation; shortfall ≥ Σ N − Σ trans | yes for feasibility; pooled netting violates arc feasibility |
| A3 | resource feasibility | yes |
| A4 | cost convexity in Q | yes |
| B1 | OEE = A × P × Q; Σ PPT | yes, but mean-of-plant also satisfies per-plant identities (G34 lesson) |
| B3 | headroom ≥ 0 per hall | **pooling violates it**, so the invariant catches W08 when a hall is negative |
| C1 | completions = starts × Π reported yield | the identity holds for the *wrong* object too (W01) |
| C2 | Σ\|e\| decomposition across stores | holds for both grains at their own level |
| C3/C4 | shares sum to 1 | hold for wrong weights |

**Invariants are abundant but mostly do not distinguish the intended object** (the G34 lesson:
coherence ≠ correctness).
