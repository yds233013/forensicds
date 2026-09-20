# G35 correct-data-table gate  (the G34 R7 equivalent)

## What was given away

Every analysis in the panel was handed a perfect analysis table:

- correct block boundaries (the city-day dispatch pool), no ambiguity about the interference group;
- the complete assignment log: saturation drawn per block, merchants drawn per block, all pre-dated;
- correct demand per merchant per day, correct fulfilment outcome, no missingness, no logging bug;
- correct adoption flags;
- no timestamp, entity-resolution, censoring or schema problem of any kind.

The only mistake left available is **estimating the wrong object**.

## Result

Worst valid-family error **0.0048**.  Weakest *reliable* wrong method error **0.0105**
(`W14_unweighted_blocks`, `hidden_b`).  Strongest wrong method error **0.5018** (`W5`, `hidden_a`).

Excluding `hidden_b` - the deliberate no-scarcity control - the weakest reliable wrong-method error
rises to **0.0237** and the separation ratio against the worst valid error is about **5x**.

## Conclusion

**PASS.**  Separation is not coming from data hygiene.  A team that cleans the data perfectly and then
runs the dashboard comparison is wrong by 4x to 39x the quantity it is trying to measure.

## The one caveat, stated plainly

`W10_realised_saturation` does **not** survive this gate as a trap: its errors (-0.015 to -0.000) are
comparable to, and on `hidden_c` smaller than, the worst valid error.  Size-tilted adoption makes
conditioning on realised exposure biased in principle but not dependably so.  It is recorded as an
ineffective trap and must not be counted toward separation.
