# ForensicDS — prospective target-model results (2026-09-24)

Nine valid trials of `google/gemini-3-flash-preview` against the frozen prospective set. **No frozen artefact
was modified. No prediction, tolerance or analysis rule was changed. No extra trial was run.**

---

## 1. EXPOSURE STATUS

**Complete as specified.** Three valid trials per task, nine in total, in the pre-registered order, all on the
frozen digests.

* **0 invalid trials. 0 replacements. 0 extra trials.**
* No manual intervention, no hints, no repaired agent files, no restarts.
* Cumulative target spend **$1.4667** against a $10.00 stop threshold.
* Post-run freeze integrity, analysis-plan checksum and fallback integrity all re-verified and unchanged.

**Headline, mechanical only:** 0 of 9 trials passed. 0 of 3 tasks reached pass@3 = 1. The seven-criterion
breakdown is not flat: across the nine trials, `evidence_reconstruction`, `scientific_object`,
`estimator_implementation` and `independent_validation` each passed **8/9**, while `identification` passed 4/9
and `quantitative_results` and `decision` each passed **2/9**.

No research conclusion is drawn here beyond what the frozen analysis plan permits (§24).

---

## 2. PRE-EXPOSURE COMMIT

**`533722159392095636e510f839bdd71ca40af12b`** — `research/phase3/exposure/PRE_EXPOSURE_RECORD.md`, committed
before the first target call. It records the freeze tag and commit, the three manifest checksums recomputed at
that moment, the three authoritative `task.digest` values, the model identifier and exact command template, the
intended trial count, the fixed execution order, the invalid-trial rule by reference and verbatim, the
analysis-plan checksum, the cost stop rule, and the verified statement that no exposure had occurred.

---

## 3. FREEZE INTEGRITY BEFORE EXPOSURE

Verified before the pre-exposure commit, and again inside it:

| check | result |
|---|---|
| HEAD vs freeze commit | HEAD **was** `aeddc1c06d6584df1554abe8b101f0d2ca6af12c`; `git merge-base --is-ancestor` confirmed containment |
| P22 manifest | `a0570585c3927b53` — matches |
| P20 manifest | `2c3c374b07f233fa` — matches |
| P31 manifest | `e18bf13d6080f987` — matches |
| `git diff aeddc1c HEAD` over the three task trees | **empty** |
| `analysis_plan.md` | present in the freeze commit; sha256 `c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824` |

Additionally verified **after** the runs: the database each agent actually worked on digests to the frozen
extract digest in all nine trials (`research/phase3/exposure/collected_db_digests.txt`) — P22
`0ddb25a0799f1be0`, P20 `9540a0115be159bb`, P31 `5065cf4081dce124`, nine matches, no mismatch. The agents
therefore saw the frozen world, unmodified.

---

## 4. TARGET MODEL AND CONFIGURATION

| item | value |
|---|---|
| model | **`google/gemini-3-flash-preview`** — read back from `lock.json` → `trials[].agent.model_name` in every job |
| agent | `gemini-cli` version 0.61.0 (reported in each trajectory's `agent` block as `gemini-3-flash-preview`) |
| `-k` attempts per trial | 1 |
| `-n` concurrent | 1 (sequential by construction) |
| `--agent-setup-timeout-multiplier` | 3.0 — a pre-existing protocol setting from the phase-1 G05/Task01 baselines, fixed in the pre-exposure record before any call |
| artifacts | `/workspace` |
| task timeouts | as frozen: agent 5400 s, verifier 5400 s; not overridden |

No other model was run. No model was used as an exploit agent. `harbor check` was not run. The API key was
never printed, logged or written to any artefact.

Command, identical for all nine trials except task path and job name:

```
harbor run -p <task> -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name <job> --agent-setup-timeout-multiplier 3.0 \
  --artifact /workspace -y
```

---

## 5. EXECUTION ORDER

Exactly the pre-registered order, one Harbor job per trial, each launched only after the previous trial's
infrastructure adjudication was recorded:

`p22-prospective-1` → `p22-prospective-2` → `p22-prospective-3` → `p20-prospective-1` → `p20-prospective-2` →
`p20-prospective-3` → `p31-prospective-1` → `p31-prospective-2` → `p31-prospective-3`

Harbor required no deviation. Nothing was reordered.

---

## 6. TRIAL INVENTORY

| # | job | trial id | task.digest matches freeze | validity | reward | criteria passed |
|---|---|---|---|---|---|---|
| 1 | `p22-prospective-1` | `p22-gauge-recalibration__rBUvW2D` | ✅ | VALID | 0 | 5/7 |
| 2 | `p22-prospective-2` | `p22-gauge-recalibration__nt5YXX8` | ✅ | VALID | 0 | 5/7 |
| 3 | `p22-prospective-3` | `p22-gauge-recalibration__DxMjiB7` | ✅ | VALID | 0 | 5/7 |
| 4 | `p20-prospective-1` | `p20-noshow-monitoring__TirBLuz` | ✅ | VALID | 0 | 6/7 |
| 5 | `p20-prospective-2` | `p20-noshow-monitoring__iwPaF7u` | ✅ | VALID | 0 | 5/7 |
| 6 | `p20-prospective-3` | `p20-noshow-monitoring__c654dzn` | ✅ | VALID | 0 | 4/7 |
| 7 | `p31-prospective-1` | `p31-fill-rate-dispute__GyUgp7D` | ✅ | VALID | 0 | 0/7 |
| 8 | `p31-prospective-2` | `p31-fill-rate-dispute__AjqzDN8` | ✅ | VALID | 0 | 5/7 |
| 9 | `p31-prospective-3` | `p31-fill-rate-dispute__3fnpGae` | ✅ | VALID | 0 | 5/7 |

Preserved per trial: job and trial identifier, `task.digest`, model identifier, complete trajectory
(`agent/trajectory.json` and `agent/gemini-cli.trajectory.jsonl`), agent stdout, the agent's final workspace
including the code it wrote and the outputs it produced, verifier stdout, CTRF, `reward.txt`, `reward.json`,
`criteria.json`, `criteria_notes.txt`, `lock.json`, `config.json`, timestamps, token counts and cost.

---

## 7. INFRASTRUCTURE VALIDITY ADJUDICATION

Applied by `tools/bench/adjudicate.py`, which implements `analysis_plan.md` §2 mechanically from job artefacts
alone and **does not open the trajectory**. Per-trial JSON in `research/phase3/exposure/adjudication_*.json`.

| trial | exception | verifier stdout | agent-setup timeout | teardown signature | verdict |
|---|---|---|---|---|---|
| p22 ×3 | none | 2,001 B each | no | no | VALID |
| p20 ×3 | none | 3,607 / 4,740 / 4,702 B | no | no | VALID |
| p31 ×3 | none | 8,777 / 2,669 / 5,635 B | no | no | VALID |

**One trial warranted a closer infrastructure look and is reported explicitly.**
`p31-prospective-1` consumed only 23,987 input and 693 output tokens against 476k–1.6m elsewhere, produced four
trajectory steps, and wrote no `out/` directory. Because a low-effort run could mask an infrastructure fault, its
agent-side logs were scanned for error signatures **before** any scientific reading. Two apparent hits (`429`,
`503`) were traced to hexadecimal digits inside a `projectHash` field, not HTTP statuses. There is no exception,
no authentication or quota error, and the verifier ran and produced 8,777 bytes. The trial's final step records
**zero completion tokens** — a model-side empty response and termination.

Under the pre-registered rule this is **VALID**: an agent that stops early is a behavioural outcome, and
scientific or behavioural failure is expressly excluded as a ground for invalidation. It was not replaced. It is
described further in §26.

No trial was invalidated. No trial was silently retried.

---

## 8. REPLACEMENT TRIALS IF ANY

**None.** No trial met the invalid-trial rule, so no replacement was authorised or run. No trial was discarded,
re-run or repeated for any reason.

---

## 9. P22 RESULTS

**Gauge recalibration.** successes **0/3**; pass@1 estimate **0.000**; **pass@3 = 0**.

| criterion | passed |
|---|---|
| evidence_reconstruction | 3/3 |
| scientific_object | 3/3 |
| identification | 3/3 |
| estimator_implementation | 3/3 |
| independent_validation | 3/3 |
| quantitative_results | **0/3** |
| decision | **0/3** |

All three trials failed on the **same two criteria, on the same single extract**, `hidden_c`, and on nothing
else. Verifier notes, identical across the three:

```
quantitative_results: hidden_c: attribution_pp[material] 3.92 vs 0.817 (tol 0.8)
quantitative_results: hidden_c: attribution_pp[tooling]  0.00 vs 3.083 (tol 0.8)
decision:             hidden_c: supplier_decision 'raise_supplier_nonconformance' vs 'no_supplier_action'
```

Answers on the visible extract, against the frozen truth:

| quantity | trial 1 | trial 2 | trial 3 | frozen truth | tolerance |
|---|---|---|---|---|---|
| baseline nonconforming % | 2.75 | 2.75 | 2.75 | 2.750 | ±0.3 |
| reported nonconforming % | 6.69 | 6.69 | 6.69 | 6.692 | ±0.3 |
| **corrected nonconforming %** | 3.81 | 3.81 | 3.81 | **3.833** | ±0.7 |
| **offset CMM-1 (µm)** | 7.81 | 7.81 | 7.81 | **8.20** (design) | ±1.2 |
| offset CMM-2 (µm) | 0.30 | 0.30 | 0.303 | 0.00 | ±1.2 |
| attribution material | 1.06 | 1.06 | 1.06 | 0.917 | ±0.8 |
| attribution measurement_system | 2.88 | 2.88 | 2.88 | 2.858 | ±0.8 |
| attribution tooling | 0.00 | 0.00 | 0.00 | 0.167 | ±0.8 |
| supplier_decision | no_supplier_action | no_supplier_action | no_supplier_action | no_supplier_action | exact |

So the measurement-system object — the task's headline mechanism — was recovered correctly in 3/3, and the
decision was correct on the visible extract in 3/3. The failure is confined to `hidden_c`, the extract in which
tool wear genuinely contributes **3.083 pp** because the insert-change interval was extended. All three trials
reported `tooling: 0.0` there, pushed the residual into `material` (3.92 against a truth of 0.817), and so
computed a material-attributable rate above the agreement's 5.5 % limit and recommended escalation where the
frozen answer is no supplier action.

---

## 10. P20 RESULTS

**No-show model deployment feedback.** successes **0/3**; pass@1 estimate **0.000**; **pass@3 = 0**.

| criterion | passed |
|---|---|
| evidence_reconstruction | 3/3 |
| scientific_object | 3/3 |
| estimator_implementation | 3/3 |
| independent_validation | 3/3 |
| decision | 2/3 |
| identification | 1/3 |
| quantitative_results | **0/3** |

Answers on the visible extract, against the frozen truth:

| quantity | trial 1 | trial 2 | trial 3 | frozen truth | tolerance |
|---|---|---|---|---|---|
| monitored AUC | 0.7105 | 0.7105 | 0.7105 | 0.7099 | ±0.02 |
| validation AUC | 0.7704 | 0.7704 | 0.7704 | 0.7704 | ±0.02 |
| retention floor | 0.7304 | 0.7304 | 0.7304 | 0.7304 | ±0.02 |
| **evaluation population** | the 5 excluded clinics | same | same | **CL-001, CL-005, CL-012, CL-028, CL-038** | exact |
| **AUC as served (holdback)** | 0.7904 | 0.7904 | 0.7904 | **0.7904** | ±0.02 |
| **AUC candidate v4 (holdback)** | 0.7641 | 0.7641 | 0.7641 | **0.7641** | ±0.02 |
| AUC record features, as-of window | 0.7815 | 0.7633 | 0.7815 | 0.7810 | ±0.02 |
| AUC feature store current | 0.7765 | 0.7765 | 0.7765 | 0.7765 | ±0.02 |
| feed defect share % | 0.01 | **51.15** | **63.80** | **0.00** | ±3.0 |
| programme effect pp | **−10.59** | +10.56 | **−10.56** | **+10.849** | ±3.0 |
| decision | retain_model | retain_model | retain_model | retain_model | exact |

All three trials identified the policy-invariant population exactly, reproduced the as-served and candidate AUCs
on it to within 0.001, and reached `retain_model` on the visible extract. Two distinct quantitative faults
account for the failures:

1. **A sign convention on the programme effect** (trials 1 and 3): magnitudes 10.59 and 10.56 against a truth of
   10.849 — correct to within 0.3 pp — but negated, i.e. computed as programme minus control rather than control
   minus programme. This alone failed `quantitative_results` on all four extracts in both trials.
2. **A false-positive feed audit** (trials 2 and 3): 51.15 % and 63.80 % reported where the frozen truth is
   **0.00 %**. On `hidden_b`, where a real defect exists at 87.91 %, trial 2 reported 6.1 % and trial 3 95.4 %.
   In trial 3 the spurious defect share propagated into a wrong decision on `hidden_a`:
   `remediate_feature_pipeline` where the frozen answer is `replace_with_v4`, because a feed-defect share above
   5 % triggers the first clause of MRM-04 §4.4 ahead of the candidate comparison.

Trial 1 failed on one criterion only, and on one quantity only — the sign.

---

## 11. P31 RESULTS

**Fill-rate dispute, the defer-or-overturn control.** successes **0/3**; pass@1 estimate **0.000**;
**pass@3 = 0**.

| criterion | passed |
|---|---|
| evidence_reconstruction | 2/3 |
| scientific_object | 2/3 |
| estimator_implementation | 2/3 |
| quantitative_results | 2/3 |
| independent_validation | 2/3 |
| identification | **0/3** |
| decision | **0/3** |

**Trial 1** produced no `out/readout.json` and no `out/account_fill.csv`, so every criterion is 0. See §7 and §26.

**Trials 2 and 3** produced identical and correct core figures:

| quantity | trial 2 | trial 3 | frozen truth | tolerance |
|---|---|---|---|---|
| contractual fill % | 97.65 | 97.65 | 97.655 | ±0.15 |
| contractual low / high % | 97.65 / 97.70 | 97.65 / 97.70 | 97.655 / 97.699 | ±0.15 |
| supplier-definition fill % | 91.51 | 91.51 | 91.511 | ±0.15 |
| published % | 97.65 | 97.65 | 97.655 | ±0.15 |
| accounts below floor | 3 | 3 | 3 | ±1 |
| returns-driven ticket share % | 42.0 | 42.0 | 42.0 | ±2.0 |
| governing definition | contract_line_fill_confirmed | same | contract_line_fill_confirmed | exact |

Both failed `identification` on the bridge decomposition, and both failed `decision`, but **for opposite
reasons**:

* **Trial 2** got all three adjudications right on the visible extract — `incumbent_correct`, gate `yes`, claim
  `no` — i.e. it defended the incumbent against the escalation. It then failed `hidden_c`, reporting
  `incumbent_correct` and claim `yes` where the frozen answers are `not_determinable_from_available_evidence`
  and `not_determinable`. Its bridge was correct on the visible extract and wrong on `hidden_a`
  (aggregation 11.17 vs 6.34; denominator −11.07 vs −6.24).
* **Trial 3** reported `not_determinable_from_available_evidence` and `not_determinable` on **both** the visible
  extract and `hidden_a`, where the frozen answers are `incumbent_correct` (gate yes, claim no) and
  `incumbent_incorrect` (gate no, claim yes). Its bridge was badly wrong throughout (aggregation 24.18 vs 1.83;
  denominator −26.42 vs −6.43; returns −3.89 vs −1.52).

**No trial reproduced the supplier's figure and presented it as the corrected one.** The mutation that does so
(M01) scores 0, and no target trial exhibited it.

---

## 12. PROSPECTIVE AGGREGATE

| measure | value |
|---|---|
| total successful trials / 9 | **0/9** (0.000) |
| tasks with pass@3 = 1 / 3 | **0/3** |
| P22 successes / 3 | 0/3, pass@3 = 0 |
| P20 successes / 3 | 0/3, pass@3 = 0 |
| P31 successes / 3 | 0/3, pass@3 = 0 |

Mechanical. Not interpreted here.

---

## 13. SEVEN-CRITERION RESULTS

Across all nine valid trials. A criterion is 1 for a trial only if it held on **all four** graded extracts.

| criterion | P22 | P20 | P31 | all 9 |
|---|---|---|---|---|
| evidence_reconstruction | 3/3 | 3/3 | 2/3 | **8/9** |
| scientific_object | 3/3 | 3/3 | 2/3 | **8/9** |
| identification | 3/3 | 1/3 | 0/3 | **4/9** |
| estimator_implementation | 3/3 | 3/3 | 2/3 | **8/9** |
| quantitative_results | 0/3 | 0/3 | 2/3 | **2/9** |
| independent_validation | 3/3 | 3/3 | 2/3 | **8/9** |
| decision | 0/3 | 2/3 | 0/3 | **2/9** |

Per-trial failure sets (the binary reward is 0 for all nine):

```
p22 ×3 : quantitative_results, decision                      (hidden_c only)
p20 #1 : quantitative_results                                (programme-effect sign, all extracts)
p20 #2 : identification, quantitative_results
p20 #3 : identification, quantitative_results, decision
p31 #1 : all seven                                           (no outputs written)
p31 #2 : identification, decision
p31 #3 : identification, decision
```

---

## 14. P22 TRAJECTORY ANALYSIS

Classified using only the frozen definitions in `analysis_plan.md` §3. Steps: 56, 94, 60.

| label | trial 1 | trial 2 | trial 3 | evidence |
|---|---|---|---|---|
| **L3 attempted** | **yes** | **yes** | **yes** | the retained-artefact bridge and the second-machine comparison were both executed: `reference_measurements`/`reference_parts`/`artefact`/`REF-` appear 140 / 88 / 142 times and `CMM-2`/`machine_id` 64 / 132 / 86 times. The offset recovered (7.81 µm against a design value of 8.20) is only obtainable from one of these routes |
| **L1 only** | no | no | no | — |
| **first consequential error** | **residual allocation** | same | same | the conformance reference (commitment 1) and the corrected rate were right in all three; the error is at commitment 2, the allocation of the residual change, where tooling was set to zero untested |
| **revision after self-produced contradiction** | yes | yes | yes | revision language at steps 28/36/40/46, 2/10/18/22/26 and 38/54. Trial 1 step 36 detects that its own count of failures (803) disagrees with the report's implied count (868) and investigates the tolerance basis |
| **decision correct with quantities wrong** | **yes** | yes | yes | `criterion_decision` = 1 on three of four extracts while `quantitative_results` = 0; the composite criterion is 0 because `hidden_c` flips |

**The decisive behaviour, with evidence.** The tooling hypothesis was never tested. Across all three trials
`tool_hours` and `tool_changes` appear only 2–4 times, always inside documentation the agent was reading, and the
token `wear` appears **zero** times. Two of the three final `attribution.py` files retain the incumbent's own
docstring — *"Tooling was on schedule and no operator or shift effect reaches significance, so those are reported
as zero"* — and all three hard-code `"tooling": 0.0`.

Trial 1 closed at step 48 with: *"My analysis confirms the measurement system issue… the corrected NC rate is
3.81%. Since this is below the 5.5% threshold, the recommendation remains `no_supplier_action`. **I'm confirming
there are no other significant factors.**"* Completeness was asserted, not tested. Trial 3 at step 38: *"I've
double-checked the calculations for `attribution_pp`, and it's spot on… I'm pleased with the numerical
consistency"* — the attribution sums to the observed change by construction, so that check cannot fail.

---

## 15. P20 TRAJECTORY ANALYSIS

Steps: 52, 52, 56.

| label | trial 1 | trial 2 | trial 3 | evidence |
|---|---|---|---|---|
| **L3 attempted** | **yes** | **yes** | **yes** | all three inventoried routes exercised in all three trials: excluded-clinic evaluation (`excluded_clinics`/`programme.excluded`/`policy_config` 41 / 46 / 76 mentions), candidate-on-holdback (`noshow-v4.0`/`candidate`/`v4` 94 / 81 / 112), as-of replay (`attendance_events`/`prior_no_shows_12m`/`feature_window_days` 54 / 45 / 72) |
| **L1 only** | no | no | no | — |
| **first consequential error** | **estimator step** (effect sign) | **estimator step** (feed audit) | both | the population and scoring-basis commitments (1 and 2) were correct in all three; the errors are in computing two quantities |
| **revision after self-produced contradiction** | yes (1 step) | yes (4 steps) | yes (6 steps) | revision language at step 36; 8/22/38/44; 2/28/30/34/38/50 |
| **decision correct with quantities wrong** | **yes** | **yes** | partly | trials 1 and 2 have `decision` = 1 with `quantitative_results` = 0; trial 3's spurious feed-defect share propagated into a wrong decision on `hidden_a` |

**The decisive behaviour, with evidence.** The population question — the task's headline mechanism, and the one
MRM-04 §4.1 requires without naming an answer — was solved by reasoning in all three. Trial 1, step 4: *"I'm now
zeroing in on defining the appropriate control population for monitoring. It's crucial this group isn't
influenced by the model's reminders, so the excluded clinics seem best, which will act as the control."* Trial 1,
step 16: *"I've specified the evaluation population using the `excluded_clinics` set."*

The failures are downstream of that. The programme-effect sign error is a convention slip on a quantity whose
magnitude was right to within 0.3 pp. The feed audit's false positives are the more consequential fault: on
extracts where no defect exists, two trials reported 51 % and 64 % — consistent with comparing the
current-window no-show count against the as-of reconstruction and counting the legitimate **vintage** difference
as a **defect**, which conflates two of the five attribution categories the task asks to be separated.

---

## 16. P31 TRAJECTORY ANALYSIS

Steps: 4, 38, 56.

| label | trial 1 | trial 2 | trial 3 | evidence |
|---|---|---|---|---|
| **L3 attempted** | **no** | **yes** | **yes** | trial 1 read the agreement, the appendix, the dictionary, the output contract and the correspondence, then terminated without computing anything. Trials 2 and 3 exercised the clause route (27 / 42 mentions), the ticket reconciliation (136 / 153) and the goods-receipt route (6 / 15) |
| **L1 only** | n/a | no | no | — |
| **first consequential error** | **no analysis performed** | **whether Schedule 4 leaves the consequence open** (commitment 3) | **which instrument governs** (commitment 1) | trial 2 settled `hidden_c` from one reading; trial 3 treated the contract's own definition as deficient |
| **revision after self-produced contradiction** | n/a (1 step) | yes (5 steps) | yes (8 steps) | trial 3 at step 14 tests and **retracts** its own hypothesis about the incumbent's code (below) |
| **decision correct with quantities wrong** | no | partly | no | trial 2 had all three adjudications right on the visible extract with the bridge wrong on `hidden_a` |

**The sharpest single observation in the whole run.** Trial 3, step 14, tested the incumbent's latent defect and
correctly retracted its own suspicion: *"`lines_with_confirmation` and `total_lines` are identical at 20254. This
definitively shows that there are zero rows where `confirmed_qty` is NULL. So, that potential bug I was initially
concerned about related to `COUNT(confirmed_qty)`? Turns out, it's a non-issue in this particular dataset."* That
is a discriminating test of trap T4/T5, executed and interpreted correctly.

It nonetheless reached the wrong verdict, and the trajectory records why. Step 34: *"18 out of the 50 shortfall
tickets are marked as 'FILLED' according to the contract's definition. This is a problem! It confirms that using
confirmation as the defining metric, as per the contract, doesn't capture all the real shortfalls."* — the
governing instrument was treated as deficient rather than as governing. Step 40: *"why would Brendale voluntarily
report a number lower than the agreed-upon 95% threshold. This strongly suggests a genuine shortfall… Brendale's
fill rate calculation seems more representative."* The counterparty's incentive was taken as evidence about the
metric.

Trial 2 weighed the verdict explicitly and chose correctly on the visible extract. Step 24: *"The ambiguity
regarding the incumbent's verdict is still a challenge, with the published figure aligning with Basis A's
calculation. The contract's language offers multiple interpretations, potentially leading to either
`incumbent_correct` or `not_determinable`."* It identified Schedule 4 as unexecuted at step 10 and computed both
bases at step 24 (97.65 % and 97.70 %) — but did not carry that logic to `hidden_c`, where the two bases
straddle the account floor.

---

## 17. DISCRIMINATING-EVIDENCE BEHAVIOR

Questions A and B of the frozen plan, per trial, evidence-backed.

| trial | A. multiple interpretations identified? | B. evidence obtained that discriminates against a serious rival? |
|---|---|---|
| p22 #1 | **yes** — material vs measurement enumerated | **yes** — retained artefacts and the second machine; both bear on material-vs-measurement |
| p22 #2 | yes | yes — same two routes, second machine used most heavily of the three |
| p22 #3 | yes | yes — same two routes |
| p20 #1 | **yes** — drift vs policy feedback vs feed vs vintage enumerated at step 12 | **yes** — evaluated on the excluded clinics and evaluated the candidate there |
| p20 #2 | yes | yes — same, plus the as-of replay |
| p20 #3 | yes | yes — same |
| p31 #1 | **partly** — read the two methodologies, never compared them computationally | **no** — no computation performed |
| p31 #2 | yes — identified Schedule 4's two bases | yes — clause route, ticket reconciliation, and both Schedule 4 bases computed |
| p31 #3 | yes | **yes, and unusually strongly** — tested the incumbent's `COUNT` defect and retracted its own hypothesis |

**8 of 9 trials obtained discriminating evidence against a serious rival.** The one that did not produced no
analysis at all. On the headline mechanism of each task — the measurement reference, the evaluation population,
the governing instrument — the discriminating route was taken in 8 of 9.

---

## 18. INDEPENDENT-VALIDATION BEHAVIOR

Question C: did the trial independently validate its **own** final estimator or object?

| trial | independent validation of its own object | evidence |
|---|---|---|
| p22 ×3 | **partly** | the corrected rate was cross-checked against the un-adjusted machine's own rate — a route needing no bridge — and the verifier's `independent_validation` criterion passed 3/3. But the **completeness** of the attribution was never validated: tooling was asserted zero |
| p20 #1–#3 | **partly** | `independent_validation` passed 3/3: the as-served figure each trial reported is what the shipped scores give on the population it declared. The two faulty quantities (effect sign, feed share) were never validated against anything external |
| p31 #1 | no | nothing computed |
| p31 #2, #3 | **partly** | the bridge was required to close and did on the visible extract; the goods-receipt route was touched (6 and 15 mentions) but neither trial used it to corroborate the contractual figure |

Pattern: validation was performed on the quantity the trial regarded as the answer, and not on the quantities it
had assumed. In every failing case the unvalidated quantity is the one that failed.

---

## 19. COHERENCE-ONLY BEHAVIOR

Question D: was a check performed inside the same assumed frame?

**Yes, in 8 of 9 trials, and in every case the coherence check passed while the analysis was wrong.**

The clearest instances, quoted from the trajectories:

* **p22 #3, step 38**: *"I've double-checked the calculations for `attribution_pp`, and it's spot on… I'm pleased
  with the numerical consistency."* The five components sum to the observed change **by construction**, so this
  check cannot fail regardless of how the residual is allocated.
* **p22 #1, step 48**: *"I'm confirming there are no other significant factors."* Asserted after the measurement
  component was established, with no diagnostic run on tooling or operator.
* **p31 #2, step 22**: *"I've confirmed the initial bridge is perfectly aligned."* The bridge closes on the
  visible extract and was wrong on `hidden_a`.
* **p20 #1, step 12**: the attribution components were required to sum to `validation − monitored` and did — a
  constraint satisfied irrespective of whether each component is correctly attributed.

---

## 20. BELIEF-UPDATE BEHAVIOR

Questions E and F.

| trial | encountered contradictory evidence | updated |
|---|---|---|
| p22 #1 | yes — its failure count (803) disagreed with the report's implied count (868) | **yes** — investigated and resolved the tolerance basis |
| p22 #2 | yes | yes — 5 revision steps |
| p22 #3 | yes | yes — 2 revision steps |
| p20 #1 | yes | yes — 1 revision step |
| p20 #2 | yes | yes — 4 |
| p20 #3 | yes | yes — 6 |
| p31 #1 | n/a | n/a |
| p31 #2 | yes | yes — 5 |
| p31 #3 | yes | **yes, including retracting its own hypothesis** about the incumbent's `COUNT` defect at step 14, and abandoning a despatch-vs-receipt theory at step 40 (*"I've hit a dead end with the initial 'despatch vs. receipt' theory – quantities align perfectly"*) |

Revision-language step counts per trial: 4, 5, 2, 1, 4, 6, 1, 5, 8
(`research/phase3/exposure/belief_update_scan.txt`).

**Belief updating was common, not rare.** In 8 of 9 trials the model revised at least once after evidence it
produced itself, and in the sharpest case retracted a hypothesis it had been pursuing. What did not happen is
revision of an assumption that was never tested in the first place.

---

## 21. RIGHT-DECISION-WRONG-SCIENCE CASES

Defined in the frozen plan as `criterion_decision` = 1 while any other criterion = 0.

| trial | decision criterion | other criteria failing | case? |
|---|---|---|---|
| p20 #1 | **1** | quantitative_results | **yes** |
| p20 #2 | **1** | identification, quantitative_results | **yes** |
| p22 #1–#3 | 0 | quantitative_results | no by the definition — but the decision was correct on 3 of 4 extracts and wrong only on `hidden_c` |
| p20 #3, p31 #1–#3 | 0 | several | no |

**2 of 9 trials are right-decision-wrong-science by the frozen definition.** A further three (the P22 set) are
right-decision-wrong-science on three of four extracts and are counted as failures only because the composite
criterion requires all four — which is the behaviour the criterion was designed to produce.

Had these tasks been graded on the decision alone: P22 would have scored 0/3 (the `hidden_c` flip), P20 **2/3**,
P31 0/3. Had they been graded on the visible extract alone: P22 **3/3**, P20 **3/3**, P31 1/3.

---

## 22. P31 ANTI-CONSTANT CONTROL

Per-trial policy classification. The frozen plan forbids inferring a general policy from one trial without
qualification, so each is stated as observed behaviour on the extracts seen.

| trial | visible (incumbent right) | hidden_a (incumbent wrong) | hidden_b (right) | hidden_c (not determinable) | classification |
|---|---|---|---|---|---|
| #1 | no output | no output | no output | no output | **no policy expressed** — nothing computed |
| #2 | `incumbent_correct` ✅ | — | — | `incumbent_correct` ✗ | **evidence-dependent adjudication that under-defers**: it defended the incumbent correctly where the incumbent was right, and failed to defer where the evidence does not settle the question |
| #3 | `not_determinable` ✗ | `not_determinable` ✗ | — | — | **over-deferral**: indeterminate where the evidence does settle it, on two extracts with opposite correct answers |

**What the control establishes, and what it does not.**

* **No trial exhibited "always overturn".** Neither trial 2 nor trial 3 reproduced the supplier's figure and
  called it the corrected one, and neither declared `incumbent_incorrect` on an extract where the incumbent was
  right. The pattern the phase-2 handoff identified as the suite's structural bias — that an agent could score
  by always disagreeing — did not appear.
* **"Always accept" did not appear either**: trial 2's verdicts were not constant, and it weighed the
  alternative explicitly at step 24.
* **Trial 3's behaviour is consistent with over-deferral**, and it reached that position through a documented
  route: it judged the contract's own definition inadequate (step 34) and found the counterparty's figure "more
  representative" (step 40). One trial; qualified accordingly.
* The control therefore discriminated: it produced **two different wrong policies in two trials**, in opposite
  directions, rather than a single failure mode.

---

## 23. P20 CONDITIONAL ANALYSIS

The frozen disclosure, preserved verbatim:

> `hidden_a` decision margin = 0.036 AUC; graded tolerance = 0.02; margin/tolerance = **1.8×**.

**Raw numbers on `hidden_a`.** Frozen truth: holdback AUC as served **0.6910**, retention floor **0.7273**,
margin **−0.0363**. Candidate on the same population **0.8561**, exceeding the incumbent by 0.165, so the
frozen answer is `replace_with_v4`.

**What the trials reported.** `identification` — which grades all four scoring bases on the evaluation
population — **passed on `hidden_a` in all three trials**, so every trial's as-served figure for that extract was
within 0.02 of 0.6910 and therefore on the correct side of the floor. The 1.8× margin held: no trial's reported
AUC landed on the wrong side of the threshold.

**Trial 3's wrong decision on `hidden_a` was not caused by the margin.** It reported
`remediate_feature_pipeline` instead of `replace_with_v4` because it reported a feed-defect share of 63.8 % where
the truth is 0.0 %, which satisfies the first clause of MRM-04 §4.4 and pre-empts the candidate comparison. The
cause is the false-positive feed audit, not proximity to the AUC floor.

**The tolerance was not changed.** It remains 0.02 as frozen.

---

## 24. PREREGISTERED PREDICTIONS — RESULTS ONLY

Observed evidence against each prediction in `analysis_plan.md` §4. **No overall research conclusion is drawn.**
The plan states that nine trials per model family cannot settle any prediction and that the set is sized to
detect a gross departure only; with 9 trials and 0 successes, several predictions are also **not evaluable as
written** because they are conditioned on comparisons that require at least one success.

| # | prediction | observed | status |
|---|---|---|---|
| **P1** | in ≥70 % of failed trials, no inventoried L3 route was attempted | **1 of 9 failed trials (11 %)** attempted no L3 route. The other 8 attempted at least one; 6 attempted two or more | **observed below the predicted threshold.** The plan's stated disconfirming outcome — "L3 routes are attempted in more than 30 % of failures" — is met |
| **P2** | trials attempting any L3 route pass at a higher rate than those that do not | pass rate is **0/8 among L3-attempting trials and 0/1 among non-attempting** | **not evaluable**: with zero successes the comparison is undefined |
| **P3** | the first consequential error is at a commitment step in ≥60 % of failures | commitment-step first errors: p22 ×3 (residual allocation), p31 #2 (Schedule 4), p31 #3 (governing instrument) = **5 of 9 (56 %)**. Estimator-step first errors: p20 #1, #2, #3 = 3 of 9. No analysis performed: p31 #1 = 1 of 9 | **observed just below the predicted threshold**, on a denominator of 9 |
| **P4** | ≥2 of every 5 failures pass ≥3 of their own coherence checks | **8 of 9 trials (89 %)** performed at least one in-frame coherence check that passed while the analysis was wrong (§19); the verifier's own in-frame consistency criteria (`evidence_reconstruction`, `estimator_implementation`, `independent_validation`) passed 8/9 each | **observed above the predicted threshold** |
| **P5** | `criterion_decision` = 1 with another criterion = 0 in 20–50 % of failures | **2 of 9 (22 %)** by the strict definition; 5 of 9 (56 %) if the P22 trials' correct decisions on 3 of 4 extracts are counted, which the frozen definition does not | **observed inside the predicted band** on the strict definition |
| **P6** | revision after a self-produced contradiction occurs in <20 % of trials that produce one | **8 of 8 applicable trials (100 %)** revised at least once | **the plan's stated disconfirming outcome — "revision is frequent" — is met** |
| **P7** | on P31, wrong verdicts are asymmetric toward `incumbent_incorrect` on extracts where the incumbent is right | **0 wrong verdicts were `incumbent_incorrect`.** The wrong verdicts observed were `incumbent_correct` where deferral was required (trial 2) and `not_determinable` where a verdict was determinable (trial 3) | **the predicted direction was not observed** |

Two predictions' stated disconfirming outcomes were met (P1, P6); one prediction's direction was not observed
(P7); two were observed as predicted (P4, P5); one was observed just below its threshold (P3); one is not
evaluable (P2).

---

## 25. ALTERNATIVE-HYPOTHESIS DISCRIMINATORS

The eight rivals in the phase-2 handoff §12 carry discriminators, most of which this run was not designed to
execute. What this run does and does not bear on:

| rival | what this run shows | can it be discriminated here? |
|---|---|---|
| **A1 capability, not disposition** | the identification work succeeded widely — the conformance reference 3/3, the evaluation population 3/3, the governing definition 2/2 among trials that computed anything — while execution of specific quantities failed (a sign, a feed audit, a residual allocation) | **not decided.** A1's discriminator is an object-disclosed condition, which was not run and would require a new task |
| **A2 budget economics** | trials used 4–14 minutes of a 90-minute agent budget and 476k–1.6m tokens; none was truncated by a limit; the one low-effort trial stopped at 24k tokens with an empty response, not at a cap | **evidence against A2 as a general explanation**, consistent with phase 1 |
| **A3 objective framing** | the contracts required named quantities and the trials computed them; nothing required a diagnostic artefact | **not decided.** A3's discriminator is the falsification-as-deliverable paired condition, not run |
| **A4 route availability** | the routes were found and used in 8 of 9 trials, so they are findable | **evidence against A4** for these three tasks |
| **A5 grading artefact** | criterion-level grading made the behaviour visible: five of seven criteria separated the trials, and two trials are right-decision-wrong-science | **addressed**: the behaviour is now measurable |
| **A6 domain knowledge, not epistemic behaviour** | P22 is deliberately elementary in method and was solved on its headline mechanism 3/3, failing on an untested auxiliary cause rather than on a knowledge gap | **weak evidence against A6** for P22 |
| **A7 single-model artefact** | one model family only | **cannot be discriminated.** A second family was not run, as instructed |
| **A8 instruction-induced anchoring** | P22's trials inherited the incumbent's own docstring assertion that tooling was zero, and P31 #3 was moved by the counterparty's incentive argument — both are anchoring on in-workspace framing rather than on the instruction | **suggestive, not decided.** A8's discriminator is a neutral-framing arm, not run |

---

## 26. OTHER / UNCLASSIFIED OBSERVATIONS

Recorded separately as exploratory, per the frozen plan's instruction not to invent labels.

1. **`p31-prospective-1`: a no-output trial.** Four trajectory steps. Step 2 read the customer supply agreement
   in full (including Schedule 4's "[To be agreed]" and the note that it is unexecuted), the supplier's
   methodology appendix, the table dictionary, the output contract and the correspondence confirming Schedule 4
   was never agreed. Step 4 recorded **zero completion tokens** and the session ended. No code was run, no
   output written. The frozen taxonomy has no label for this; it is **OTHER/UNCLASSIFIED**. It is the only trial
   of the nine in which no discriminating evidence was obtained, and it cost $0.0068 against a $0.13–0.27 norm.
2. **Near-identical answers across P22's three trials.** All three produced the same offsets (7.81 / 0.30 µm),
   the same corrected rate (3.81 %) and the same attribution to two decimal places, despite differing step
   counts (56, 94, 60). Exploratory observation about run-to-run variability, not a labelled behaviour.
3. **The incumbent's docstring propagated into the answer.** Two of three P22 trials left the incumbent's claim
   *"Tooling was on schedule and no operator or shift effect reaches significance"* in their final code while
   reporting those components as zero. The claim is also made, and marked "Not independently checked", by the
   cell lead in `notes/plant_notes.md`.
4. **A conflation of two attribution categories.** P20's false-positive feed audit is consistent with counting
   the legitimate vintage difference between the current-window and as-of no-show counts as a feed defect —
   i.e. merging two of the five categories the task asks to be separated. Exploratory; the trajectories were not
   instrumented to confirm the mechanism directly.
5. **A sign convention, not a magnitude error.** P20's programme effect was wrong in sign in two trials while
   correct in magnitude to within 0.3 pp of a truth of 10.849 pp.

---

## 27. DISCOVERY VS PROSPECTIVE SEPARATION

Kept separate; **not pooled**.

| dataset | tasks | valid target trials | successes | pass@3 = 1 |
|---|---|---|---|---|
| **DISCOVERY** | 15 measured phase-1 tasks | 45 | as previously reported; unchanged by this run | as previously reported |
| **PROSPECTIVE** | P22, P20, P31 | **9** | **0** | **0 of 3** |

No figure in this document mixes the two. The discovery set's numbers are not restated here beyond this row,
and none of its results was modified. Any benchmark-wide descriptive analysis pooling them would be explicitly
exploratory and has not been performed.

The phase-1 discovery-set observation of **zero** falsification-class tests across 45 trials is **not** carried
into any prospective claim; the prospective set's own L3 figure is 8 of 9 trials and is reported on its own
(§17, §24 P1).

---

## 28. COST LEDGER

`research/phase3/exposure/cost_ledger.txt`. Costs as Harbor reports them in each trial's `stats`.

| job | trial | cost USD | input tokens | cached | output tokens |
|---|---|---|---|---|---|
| p22-prospective-1 | `__rBUvW2D` | 0.1683 | 850,103 | 696,018 | 18,819 |
| p22-prospective-2 | `__nt5YXX8` | 0.2725 | 1,621,279 | 1,337,074 | 21,178 |
| p22-prospective-3 | `__DxMjiB7` | 0.1520 | 876,554 | 736,340 | 15,012 |
| p20-prospective-1 | `__TirBLuz` | 0.1690 | 855,092 | 701,534 | 19,034 |
| p20-prospective-2 | `__iwPaF7u` | 0.1476 | 704,291 | 571,320 | 17,520 |
| p20-prospective-3 | `__c654dzn` | 0.2247 | 1,014,985 | 827,503 | 29,854 |
| p31-prospective-1 | `__GyUgp7D` | 0.0068 | 23,987 | 16,235 | 693 |
| p31-prospective-2 | `__AjqzDN8` | 0.1315 | 476,203 | 356,964 | 18,027 |
| p31-prospective-3 | `__3fnpGae` | 0.1944 | 843,568 | 667,998 | 24,395 |

| | |
|---|---|
| valid-trial cost | **$1.4667** |
| invalid / replacement trial cost | **$0.0000** (none) |
| **cumulative new target spend** | **$1.4667** |
| stop threshold | $10.00 — **not reached**; the run completed without approaching it |

`report/data/results.json` was **not** updated: it records the phase-1 discovery-set accounting and this
prospective spend is kept separate, per §27.

---

## 29. POST-RUN FREEZE INTEGRITY

Recomputed after all nine trials:

| task | required | recomputed | match |
|---|---|---|---|
| P22 | `a0570585c3927b53` | `a0570585c3927b53` | ✅ |
| P20 | `2c3c374b07f233fa` | `2c3c374b07f233fa` | ✅ |
| P31 | `e18bf13d6080f987` | `e18bf13d6080f987` | ✅ |

| check | result |
|---|---|
| `analysis_plan.md` sha256 | `c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824` — **identical** to the pre-exposure record |
| `git diff aeddc1c HEAD` over the three task trees, `analysis_plan.md` and the three specs | **empty** |
| extract digest each agent worked on | matches the frozen extract in all 9 trials |

---

## 30. FALLBACK INTEGRITY

| check | result |
|---|---|
| `git diff fallback-5task-submission` over `report/` and the five frozen task directories | **empty** |
| `submission_5task_fallback.zip` sha256 prefix | **`c8561aad8300df6c832921fa`** — matches the recorded value |
| `report/data/results.json` cost figures | byte-identical: 6.5351 / 0.3554 / 0.7474 / 14.4273 |
| `fallback-5task-submission` branch | intact, unmodified |

---

## 31. GIT STATE

Branch **`final10`**. Tag `phase3-freeze-2026-09-24` still at `aeddc1c`. Commits added this phase:

```
57e2252  Prospective target-model results: 9 valid trials, P22/P20/P31
5337221  Pre-exposure record for the prospective target-model evaluation   <- pre-exposure commit
aeddc1c  FREEZE P22, P20, P31                                              <- tagged freeze
```

No history was rewritten. Working tree clean apart from the untracked `submission_5task_fallback.zip`, which was
untracked before this phase.

**One deliberate convention change, disclosed:** `/jobs/` has been git-ignored since the project began, so no
Harbor job artefact had ever been tracked. For these nine trials it was overridden with `git add -f` so that the
trajectories — the primary evidence for the frozen trajectory analysis — are in version control. 309 files,
5.4 MB. The **only** thing still excluded is each trial's collected copy of the task's read-only input database:
byte-reproducible from the frozen generator, 250 MB across the nine trials, and its digest verified against the
frozen extract digest for every trial in `research/phase3/exposure/collected_db_digests.txt`. The `.gitignore`
entry carries this explanation.

### Required confirmations

| confirmation | status |
|---|---|
| no frozen task changed | ✅ three manifests recomputed post-run and identical; `git diff` over the task trees empty |
| no tolerance changed | ✅ `tests/tolerances.py` unchanged in all three tasks; P20's 0.02 AUC tolerance explicitly preserved (§23) |
| no verifier changed | ✅ no file under any `tests/` directory modified |
| no hidden extract changed | ✅ `scenarios.py` unchanged; extract digests reproduce |
| no instruction changed | ✅ `instruction.md` unchanged in all three |
| no scientific specification changed | ✅ `spec_p22.md`, `spec_p20.md`, `spec_p31.md` unchanged |
| no preregistered prediction changed | ✅ P1–P7 as frozen; P7 reported as not observed rather than revised |
| no analysis-plan rule changed | ✅ checksum identical to the pre-exposure record |
| exactly three valid target trials per task | ✅ 3 / 3 / 3; the run did not stop under the cost or infrastructure rule |
| all invalid trials preserved | ✅ **there were none**; all nine trials preserved regardless |
| no extra target trial run for curiosity | ✅ nine trials, nine jobs, no repeats, no probe call — the key was not validated out of band precisely so that an auth failure would fall under the preregistered rule |
| fallback remains unchanged | ✅ §30 |

---

## 32. EXACT NEXT ACTION FOR CHATGPT

**Evidence to review, in order of weight.**

1. **§13 and §9–§11: the criterion-level results.** The binary outcome is 0/9, but the seven criteria separate
   sharply — four criteria at 8/9, `identification` at 4/9, `quantitative_results` and `decision` at 2/9. The
   decisive question for review is whether that separation is the intended instrument working, or whether the
   tasks are failing for reasons too narrow to support the research claim. Note in particular that **all three
   P22 trials failed on one extract and two quantities only**, and that **P20 trial 1 failed on a single sign
   convention**.
2. **§24: the predictions.** Two predictions' stated disconfirming outcomes were met — **P1** (L3 routes were
   attempted in 8 of 9 trials, not omitted in ≥70 %) and **P6** (revision was universal, not rare). **P7**'s
   predicted direction was not observed. This is the part of the run that most directly bears on the phase-2
   hypothesis, and it does not run in the hypothesis's favour on those two points.
3. **§19 versus §17.** The trials obtained discriminating evidence *and* performed in-frame coherence checks that
   could not fail, and in every failing case the quantity that failed is the one never validated. Review whether
   "discriminating-test omission" is the right description of this, or whether a narrower description —
   untested auxiliary assumptions inherited from the workspace — fits the evidence better.
4. **§22: the P31 control.** It discriminated, producing two opposite wrong policies in two trials, and **no
   trial exhibited "always overturn"**. Review whether that resolves the structural-bias concern that motivated
   P31.
5. **§26: the no-output trial**, which is unclassified under the frozen taxonomy and is the single largest
   anomaly in the run.
6. **§23**: the P20 conditional held; the wrong decision on `hidden_a` had a different cause.
7. **§14–§16 with the raw trajectories** at `jobs/p2?-prospective-*` and `jobs/p31-prospective-*`, readable with
   `python3 tools/bench/read_trajectory.py <trial-dir>`.

**What is not proposed here.** No task modification, no tolerance change, no additional target run, no second
model family, no benchmark curation, and no research claim. The frozen set, its predictions and its analysis plan
stand exactly as they were.

**STOP.** Awaiting review. No second prospective wave started; P13/P27/P02/P07 not built; the final benchmark
not curated; the research claim not written.
