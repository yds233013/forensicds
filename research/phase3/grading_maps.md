# Scientific-chain grading maps

Harbor 0.21.0 **does** support criterion-level rewards. `harbor/verifier/verifier.py:227-232` reads
`/logs/verifier/reward.json` in preference to `reward.txt` and parses it as a flat `dict[str, float | int]`;
`harbor/cli/jobs.py:2061` takes the `"reward"` key as the headline. This was read from the installed package,
not assumed from the research handoff.

Each verifier therefore emits

```json
{"reward": 0|1, "criterion_<stage>": 0|1, ...}
```

The binary task reward is unchanged: `reward` is 1 only if every check on every graded extract passes. The seven
criteria are the stages the implementation brief asks to be separated, and **a criterion is 1 only if it holds on
all four extracts**. Harbor displays them as separate columns in its own results table.

| criterion | stage in the brief | what makes it 0 |
|---|---|---|
| `evidence_reconstruction` | 1. evidence reconstruction | the population, the published figures or the stated thresholds are not reproduced |
| `scientific_object` | 2. scientific object | the object itself is wrong — the reference, the population, or the governing definition |
| `identification` | 3. identification assumptions | the object is named but obtained on the wrong basis |
| `estimator_implementation` | 4. estimator / implementation | the artefact the analysis must leave does not exist, is malformed, or contradicts the readout |
| `quantitative_results` | 5. quantitative results | the decomposition or the component quantities are outside tolerance |
| `independent_validation` | 6. independent validation | the answer fails a check that does not depend on the agent's own frame |
| `decision` | 7. final decision or justified deferral | the decision, or any of the three adjudications in P31, is wrong |

## What each criterion grades, per task

### P22

| criterion | graded quantities |
|---|---|
| evidence_reconstruction | baseline and reported nonconforming rates; all four stratum breakdowns |
| scientific_object | `conformance_reference_offset_um` for **both** machines |
| identification | `corrected_nonconforming_rate_pct` |
| estimator_implementation | `part_dispositions.csv` exists, is well formed, has one row per post-window part, and its FAIL share equals the stated corrected rate to 0.15 pp; re-run determinism |
| quantitative_results | the five `attribution_pp` components, and that they sum to the observed change |
| independent_validation | the corrected rate must be consistent with the rate on the machine that was never adjusted — a route that uses no bridge |
| decision | `supplier_decision` under Schedule 3 §3.2 |

### P20

| criterion | graded quantities |
|---|---|
| evidence_reconstruction | `monitored_auc`, `validation_auc`, `retention_floor_auc` |
| scientific_object | `evaluation_population.clinic_ids` exactly, and `n_appointments` within 20 % |
| identification | all four entries of `auc_by_scoring` on that population |
| estimator_implementation | `evaluation_population.csv` lists exactly those clinics, its counts sum to the claimed n, re-run determinism |
| quantitative_results | `feed_defect_share_pct`, `programme_effect_pp`, the five `attribution_auc` components |
| independent_validation | the reported `as_served` figure must equal what the shipped scores give **on the population the readout itself declares**, plus closure of the decomposition |
| decision | `decision` under MRM-04 §4.3–§4.4 |

### P31

| criterion | graded quantities |
|---|---|
| evidence_reconstruction | both published figures reproduced from the order book |
| scientific_object | the contractual figure, the low/high range Schedule 4 admits, and `governing_definition` |
| identification | the four `bridge_pp` components |
| estimator_implementation | `account_fill.csv` consistent with the readout's below-floor count and with the escalating accounts' rates |
| quantitative_results | the account-level tail, the below-floor count (±1), the returns-driven ticket share |
| independent_validation | the bridge must close on the readout's own figures, and low ≤ point ≤ high |
| decision | all three of `incumbent_verdict`, `bonus_gate_met`, `supplier_claim_payable` |

## Two rules the brief requires, and how they are met

**A correct final decision must not compensate for wrong quantities.** The decision is one criterion of seven,
and the headline reward needs all seven. P22's mutation M06 (right decision, whole change credited to material)
and P20's M12 (right decision on the visible extract, all of the gap credited to drift) both score 0 while
failing only `quantitative_results` — which is exactly the phase-1 G24 failure mode made visible.

**A correct analysis must not be rejected for an irrelevant difference.** Nothing grades an algorithm, a
library, a file layout or a wording. Every accepted alternative route in §Multiple-valid-method is implemented
and passes; M00 in each suite is a legitimate alternative and scores 1.
