# Correct-table gate (R1)

Every simulation operates on perfectly clean panels:
- counts, exposures and enrolment months for every supplier-month;
- no missing data, no ETL, no discovery.

On those tables, the wrong methods are still wrong **in expectation**: W01 +2.0 … +2.7, W08 up to
−5.8, W15 up to −19.7 SE_REF. So the difficulty is statistical, not data preparation.

**The gate passes, but that does not rescue the task:** "wrong in expectation" is not
"distinguishable in a finite sample" (`tolerance_window.md`).
