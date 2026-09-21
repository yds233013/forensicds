# Tolerance window (C1) — **FAIL**

Definitions were pre-registered in `sim/analyze_c1.py` before the full run.

| design | VALID_BOUND (p99, SE_REF) | WRONG_BOUND (p01, 2nd fixture) | hardest wrong | ratio | proposed tolerance |
|---|---|---|---|---|---|
| D1 | 5.76 (F2, hidden_c) | 0.04 | X01 | 0.01 | **none exists** |
| D2 | 5.57 (F2, hidden_c) | 0.04 | X01 | 0.01 | **none exists** |
| D3 (probe) | 5.70 | 0.17 | X02 | 0.03 | **none exists** |

**Sensitivity (not a rule):**
- Removing the inefficient F2 family lowers VALID_BOUND to ≈ 3.
- Ignoring X01 and X02 moves WRONG_BOUND to ≈ 1.7 (W09).
- Even the most favourable reading therefore gives a ratio < 1.

The requirement is ≥ 3. **Recommendation from this gate: DROP or REDESIGN. No multiplier was chosen.**
