# Correct-table gate

Suppose the analyst receives a clean, pre-joined table with the *right* fields: good parts,
PPT, ATP, usable kW, FPY, active flags. Then:

| outcome | concepts |
|---|---|
| the remaining step is a one-line formula | B1, B2, B3, B4, C1, C2, C3, C4 |
| the difficulty is entirely in *knowing which field is right* (recognition, not execution) | the same eight |
| a small optimisation remains | A1–A4; after H2 it is textbook LP / newsvendor / max-flow |

**The gate fails or degrades for all B/C concepts, and degrades for A.** The hard part is semantic
reconciliation, which becomes ETL once the table is correct.
