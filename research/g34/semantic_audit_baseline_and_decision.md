# G34 audit I — existing baseline reinterpretation, and final decision

Performed **after** audits A–H were complete. No trial was rerun and nothing was changed.

| trial | reward | Q1 | Q2 | decision | interpretation it matches |
|---|---|---|---|---|---|
| hLbWzqK (1) | 1 | 0.357034 | 0.544248 | expanded | V00 exactly (AJ + KM) |
| UPCLpLx (2) | 0 | 0.275667 | 0.544248 | baseline | **C02 exactly** (events ≤ 36 months / N, with units censored at cut-off counted as still carrying the original assembly): 2481/9000 |
| SdvVPQN (3) | 1 | 0.357034 | 0.544248 | expanded | V00 exactly |

**Could trial 2's failure be a legitimate alternative reading?** No.
- The contract and memo ask for outcomes "by 36 months of service age". For a unit commissioned
  less than 36 months before cut-off, that outcome is **unknown**, not "still original". The
  dictionary says a no-WO unit was running "**on that date**" (the cut-off), not at 36 months.
- The one legitimate reading that avoids survival machinery (C05, crude shares in the
  complete-follow-up cohort) gives Q1 = 0.357, "expanded", and **passes**.
- C02 is rejected by 21–33 × tolerance on every extract and flips the business decision.

**The baseline stands: 2/3, pass@3 = 1.** No semantic evidence supports altering it.

## G34 FINAL DECISION: **B — MINOR DOCUMENTATION RISK, BASELINE REMAINS VALID**

Why B and not A. Two residual prose risks:
1. The engineering quantity is defined by prose ("handled in the standard way") rather than by
   formula. Every alternative reading is excluded by the wording and measured as rejected.
2. The memo's "today's installed base" sits beside the contract's "installed base in the extract".
   The contract governs, and the prose reading (C10) is rejected.

Neither changed any trial's outcome. Neither is an F8: the verifier grades exactly what the contract
and notes define. **G34 is unmodified**; checksum `f14dd0c0dbcd763c`.
