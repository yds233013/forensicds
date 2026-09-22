# Matching audit (R1) — the §12 subtlety, measured in the existing run

| matching design | what it conditions on | bias (SE_REF) vis / a / b / c / d | verdict |
|---|---|---|---|
| **contemporaneous, on trigger value** (W08) | untreated suppliers with the highest S at the same month (all below 1,500 by construction) | −3.4 / −2.7 / −3.5 / −5.8 / −1.5 | **wrong**: there is no untreated unit above the threshold, so "closest S" means lower S, a lower transient **and** a lower α |
| historical, on S only, any month (W09, labelled ambiguous) | pre-era supplier-months with similar S, not rule-selected | +0.3 / +0.6 / −0.4 / +0.3 / −0.3 | **effectively valid**: selection on a covariate is ignorable given that covariate |
| historical, on H only (W10) | long-run mean only | −2.9 / −2.2 / −3.6 / −1.5 / −1.3 | wrong: ignores the persisting part of the trigger shock |
| same-rule pseudo-episodes, on S only (L1) | S, among same-rule episodes | +0.04 … +0.18 | valid |
| same-rule pseudo-episodes, NN on (S*, H*) (L3) | S and H | −0.51 … −0.30 | valid (small NN bias) |

## Why they differ
- Matching on the trigger value **fails only when controls are drawn from a different selection
  regime**, i.e. contemporaneous units that did *not* cross.
- Against **historical** units at the same S, matching on S is valid. Conditioning on the selection
  variable itself removes the selection, whether or not long history is also used.
- The intended subtlety ("trigger-value matching fails, history matching works") is therefore
  **only half true**. It is a comparison-population issue, not an information-set issue.
