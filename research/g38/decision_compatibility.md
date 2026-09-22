# Decision / tolerance compatibility — **FAIL**

Rollout rule: expand iff Q1 ≥ 75 defects averted per enrollee (break-even, fixed before simulation).

| fixture | E[truth Q1] | distance to 75 | distance / SE_REF(Q1) |
|---|---|---|---|
| visible | 238.8 | 163.8 | 3.54 |
| hidden_a | 0.0 | 75.0 | **1.34** |
| hidden_b | 211.7 | 136.7 | 2.29 |
| hidden_c | 387.9 | 312.9 | 7.94 |
| hidden_d | 28.9 | 46.1 | **1.43** |

- Any tolerance that admits the valid families (≥ ~2.6 SE_REF for V2 alone at p99; 5.67 for the full
  valid set) **exceeds the distance** on hidden_a, hidden_b and hidden_d.
- A numerically accepted Q1 could therefore imply the wrong decision on those fixtures.
- The business threshold was not moved, and fixture effect sizes were not re-chosen.
