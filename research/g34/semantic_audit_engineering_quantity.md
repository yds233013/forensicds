# G34 audit D — the engineering quantity (`engineering.assembly_failure_rate_36m`)

## What it is (contract-only, then confirmed)
| question | answer | where it is pinned |
|---|---|---|
| physical object | the service life of a **critical assembly** (bearing pack + shaft seal) | engineering note: "a property of the assembly, not of the maintenance programme" |
| estimand | probability that an assembly **would fail by 36 months of service age were it never removed** for overhaul or retirement (net / latent failure risk) | "how long does a critical assembly last … we do not see the failure that would have happened later" |
| units | proportion (0–1) | contract: "All rates are proportions of the installed base"; the key ends `_rate_36m` |
| denominator | **original assemblies of every unit in the installed base** (one per unit). Not surviving units, not overhauled units, not per unit-time | contract "proportions of the installed base"; the dictionary records only the original assembly's life |
| expectation / probability / count / rate | a **probability** (cumulative risk by 36 months), not a hazard, MTTF or count | "rate … proportion"; the `_36m` suffix |
| censoring | administrative cut-off **plus** overhaul and retirement treated as censoring ("incomplete … in the ordinary way … handled in the standard way") | engineering note |
| overhaul / competing events | **censor, do not count as survival and do not count as failure**; valid because removal is not condition-driven (SOP §1, §3; note's proviso) | SOP + note |
| weighting | each assembly once | contract (installed-base proportion) |
| horizon | 36 months | key and contract `horizon_months` |
| population | installed base in the extract | contract |

## Every plausible interpretation (tested in `counterexamples.py`)
| id | interpretation | formula | business meaning | measured vs truth (max err/tol over 4 extracts) | ruled out by visible wording? |
|---|---|---|---|---|---|
| **E01** | net risk, censor overhaul + retirement + admin | 1 − KM_FAIL(36) | assembly life | **≤ 0.35** (passes) | — this **is** the wording |
| E05 | Nelson–Aalen 1 − exp(−Ĥ) | | same | 0.35 (passes) | legitimate variant |
| E06 | Weibull MLE with censoring | | same | 0.40 (passes) | legitimate variant |
| E10 | KM on the complete-follow-up cohort | | same | 0.35 (passes) | legitimate variant |
| E02 | CIF of failure (the aftermarket number) | AJ | what the fleet will actually see | 5.55 (rejected, and by the gap test) | **yes**: "Aftermarket are asking a different question … our number should not be used for theirs" |
| E03 | retired units treated as never failing | KM with retired kept at risk to ∞ | — | 4.80 | **yes**: retirement is "incomplete … we do not see the failure that would have happened later" |
| E04 | overhauled assemblies treated as never failing | same, for overhaul | — | 3.84 | **yes**: same sentence; "removes assemblies … whether or not they were close to failing" |
| E07 | failure given not removed: F/(F + S) | ratio | — | 7.87 | yes: an ad hoc conditioning with no reading in the note |
| E08 | horizon 24 months (the overhaul interval) | 1 − KM(24) | — | 7.47 | **yes**: `_36m`, `horizon_months: 36` |
| E09 | complete-case denominator | fails ≤ 36 / (fails ≤ 36 ∪ exit > 36) | — | 8.86 | yes: drops censored units without justification |
| E11 | any removal: 1 − S_all(36) | | assembly *removal*, not failure | 11.27 | **yes**: "before it fails" |
| E12 | crude failures ≤ 36 / N | | observed failures only | 8.73 | **yes**: "incomplete … in the ordinary way" |
| — | hazard rate / MTTF | | | not a proportion | **yes**: "All rates are proportions" |
| — | include replacement assemblies after overhaul | | | not observable (one WO per unit) | yes: the dictionary records only the original assembly |

**Could two competent analysts derive different formulas?** They could choose different *estimators*
(KM, NA, parametric, cohort KM), and all of those pass. **No second estimand survives the wording.**
The only readings that differ are ones the note or the contract explicitly excludes.

**Residual risk.** The quantity is pinned **by prose, not formula**. "Handled in the standard way" is
the only method pointer, so an analyst must know that independent competing removal is handled by
censoring. That is the scientific skill being tested, not an ambiguity. Classification: **pinned,
with minor documentation risk.**
