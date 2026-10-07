# HANDOFF — resuming the Abundant AI Research take-home
**Audit date:** 2026-09-28 · **Repository:** `/Users/yashshah2311/forensicds` · **Mode:** read-only audit

Self-contained. Every number below was recomputed from repository files during this audit unless explicitly
marked as quoted-from-a-document. Where a document and the underlying evidence disagree, both are given and the
disagreement is reported rather than repaired.

---

## 1. REPOSITORY STATE

| item | value |
|---|---|
| current branch | **`final10`** |
| HEAD | **`7e6d4d760995c7bd3729a8cbba31e5a31a8801fe`** |
| HEAD subject | `Final editorial pass on the Mercor APEX proposal` |
| HEAD date / author | 2026-09-25 22:17:00 −0700 · `yds2330 <yashshah2311@berkeley.edu>` |
| `git status --porcelain` | one line only: `?? submission_5task_fallback.zip` |
| tracked working tree | **clean** — no modified, staged, deleted or renamed tracked file |
| remotes | **none configured** (`git remote -v` is empty), so nothing in this repository has ever been pushed |

### Branches

| branch | commit | relation |
|---|---|---|
| `main` | `8cf774e` "Ignore local validation stdout captures" | **ancestor of `final10`** |
| `fallback-5task-submission` | `8cf774e` | **identical to `main`** (`main..fallback-5task-submission` is empty) |
| `final10` (checked out) | `7e6d4d7` | contains everything on `main` plus 31 further commits |

`final10..main` is empty, so nothing exists on `main` that is missing from `final10`. **The Phase-3 freeze commit
and all prospective evidence exist only on `final10`.**

### Tag

| tag | type | target commit | message contents |
|---|---|---|---|
| `phase3-freeze-2026-09-24` | **annotated tag object** `bedb131` | **`aeddc1c06d6584df1554abe8b101f0d2ca6af12c`** ("FREEZE P22, P20, P31", 2026-09-23 23:24:43 −0700) | the three task digests, and "Oracle 1 / Nop 0 on all three at freeze. No target model run." |

Note for anyone verifying: `git tag -l` prints the **tag object** hash `bedb131`; the **commit** it points at is
`aeddc1c`. These are not in conflict.

### Relevant commits, newest first

```
7e6d4d7 2026-09-25 Final editorial pass on the Mercor APEX proposal        <- Mercor only
516dbc1 2026-09-25 Add Mercor APEX fellowship proposal: research, ...      <- Mercor only
5235aa7 2026-09-24 Prospective results handoff (32 sections)
57e2252 2026-09-24 Prospective target-model results: 9 valid trials, P22/P20/P31
5337221 2026-09-24 Pre-exposure record for the prospective target-model evaluation
aeddc1c 2026-09-23 FREEZE P22, P20, P31                                    <- tagged
b691bde 2026-09-23 Add phase 3 implementation handoff (38 sections)
568a201 2026-09-23 Add prospective tasks P22, P20 and P31 with criterion-level grading
039cf42 2026-09-23 Scientific audit of the benchmark (read-only, zero model spend)
e44c937 2026-09-22 Submission ready: TB3 rubric checks, supporting evidence, final audit PASS
```

### Dirty / untracked

Exactly one untracked file: **`submission_5task_fallback.zip`**. `.gitignore` excludes `submission/` and
`submission.zip`, so **no submission archive has ever been under version control**. The archive exists only on
local disk.

---

## 2. ORIGINAL ABUNDANT ASSIGNMENT

> **The original assignment text is NOT in this repository.** This is not an inference — the repository says so
> itself, in `research/audit/abundant_requirements.md`, first line: *"Caveat recorded first: the original
> assignment text is not in the repository. `grep -ril "abundant|take-home"` over all tracked Markdown returns
> nothing."* I re-ran that search this audit and confirm it: the only files mentioning "abundant" are
> `research/audit/abundant_requirements.md`, `research/audit/AUDIT_2026-09-23.md`,
> `research/phase2/implications.md`, `research/phase2/HANDOFF_2026-09-23.md` and
> `research/g39_search/invariants.md`, and none of them quotes the assignment. There is no PDF, no
> `ASSIGNMENT.md`, no email export.

What the repository does contain is an **18-item restatement by the project owner**, recorded in
`research/audit/abundant_requirements.md` and audited on 2026-09-23. Reproduced verbatim as a list, with its
provenance attached:

1. 5–10 tasks
2. Harbor task format
3. ≥3 target-model trials per task
4. <30 % pass@3 headroom target
5. Oracle = 1, Nop = 0
6. `harbor check` (task-quality rubric)
7. Logs shipped
8. Report
9. Distribution justification
10. Difficulty profile
11. Research awareness
12. Scale plan
13. Failure analysis from trajectories
14. Automation disclosure
15. Trajectory inspection
16. Tasks representative of real DS work
17. Failures from genuine difficulty, not ambiguity / environment / verifier defects
18. Piloting more candidates and curating down

**Additionally verifiable from the repository, not from a restatement:** the target model is
`google/gemini-3-flash-preview` run through the `gemini-cli` agent on Harbor 0.21.0. This is not just asserted —
it is the model string in every counted trial's `result.json`
(`stats.evals["gemini-cli__gemini-3-flash-preview__adhoc"]`), and `research/phase3/analysis_plan.md` and the
exposure ledger both name it. So requirement "Gemini 3 Flash Preview" is **corroborated by artifacts even though
the assignment wording is not located.**

**Items in the audit brief I could not locate any repository source for, and therefore mark NOT LOCATED:**
- the exact required task count (the restatement says 5–10; no source document)
- the exact pass@3 threshold and whether it was a target or a hard bar (restated as "<30 % headroom target")
- any packaging/submission format requirement (file layout, archive name, delivery channel) — **nothing in the
  repository states one.** `scripts/build_submission.sh` produces `submission/` + `submission.zip`, which is a
  project convention, not a documented requirement.
- any word limit, page limit or required section list for the write-up
- whether plots were required at all (three exist; no requirement text found)
- whether pass@1 specifically was required alongside pass@3

---

## 3. BENCHMARK INVENTORY

All rewards below were read from `jobs/*/*/verifier/reward.txt` and cross-checked against Harbor's own
`jobs/*/result.json` → `stats.evals[...].reward_stats.reward`. "Trials" = `google/gemini-3-flash-preview` solver
trials. A full census found **20 task identities with at least one Gemini solver trial and 64 such trials in
total.**

### The shipped five

| task ID | path | one-sentence description | capability tested | Oracle | Nop | `harbor check` | mutation validation | trials | results | status |
|---|---|---|---|---|---|---|---|---|---|---|
| **Task02** | `candidates/02-renewal-risk-regression` | A renewal-risk model's AUC jumped after a feature-pipeline change; reconstruct point-in-time features and re-evaluate | temporal state reconstruction / point-in-time correctness (leakage) | **1** (`final-oracle-…`, also `task02-oracle-1/2`) | **0** (`final-nop-…`, `task02-nop-1/2`) | **1** (`task02-check-1`, 11/11 default rubric; `tb3-check-…` reward 1 with 10 of 35 TB3 criteria failing) | **21/21 as expected** (`report/task02_mutations.txt`, `CHAIN_EXIT=0`) | 3 | 0, 0, 0 | **INCLUDED** |
| **G05** | `candidates/g05-sco-rollout-gate` | A staggered self-checkout rollout's measured uplift gates tranche 2; recover the identified effect | identification under staggered adoption | **1** (`final-oracle-…`, `g05-oracle-prebaseline`) | **0** (both) | **1** (`g05-check-prebaseline` 11/11; `tb3-check-…` reward 1, 8 of 35 TB3 criteria fail) | **38/38 as expected** (`research/g05/shortcuts_report.json`, 38 entries) | 3 counted (+1 adjudicated invalid) | 0, 0, 0 | **INCLUDED** |
| **G10** | `candidates/g10-censored-demand` | Replenishment demand is censored by stockouts; recover unconstrained demand and re-decide | informative censoring / mis-specified uncertainty | **1** (`final-oracle-…`, `g10-oracle-prebaseline`) | **0** (both) | **1** (`g10-check-prebaseline` 11/11; `tb3-check-…` reward 1, 5 of 35 fail) | **33/33 as expected** (`research/g10/shortcuts_report.json`, 33 entries) | 3 | 0, 0, 0 | **INCLUDED** |
| **G24** | `candidates/g24-recommender-ope` | Off-policy evaluation of a recommender slate policy against a launch rule | off-policy evaluation / correct decision unit | **1** (`final-oracle-…`, `g24-oracle-prebaseline`) | **0** (both) | **1** (`g24-check-prebaseline` 11/11; `tb3-check-…` reward 1, 5 of 35 fail) | **30/30 as expected** (`research/g24/shortcuts_report.json`, 30 entries) | 3 | 0, 0, 0 | **INCLUDED** |
| **G34** | `candidates/g34-fleet-reliability-gate` | FY27 spare-assembly build depends on 36-month failure share; the incumbent computes net risk where the procurement rule needs crude risk | competing risks — right method family, wrong statistical object (F9) | **1** (`final-oracle-…`, `g34-oracle-v1`) | **0** (`final-nop-…`, `g34-nop-final`) | **1** (job `2026-09-20__01-29-33`, 11/11 default rubric; `tb3-check-…` reward 1, 9 of 35 fail incl. a **disputed** `anti_cheat_robustness`) | **21/21 as expected** — recorded in `report/g34_prebaseline_validation.md` §A13; **the raw result file was written to `/tmp/g34_mutations2.csv`, which no longer exists** | 3 | `hLbWzqK` **1**, `UPCLpLx` **0**, `SdvVPQN` **1** | **INCLUDED** (the suite's single calibration anchor) |

### The three prospective tasks (frozen, not part of the five)

| task ID | description | capability tested | Oracle | Nop | `harbor check` | mutations | trials | results | status |
|---|---|---|---|---|---|---|---|---|---|
| **P22** `candidates/p22-gauge-recalibration` | A machined-part defect rate breached a 5.5 % supply-agreement limit; a gauge has drifted, and the residual must be attributed across material / measurement / tooling / operator | measurement-system change with a physical bridge; **which reference a pass/fail decision is made against** | **1** ×3 (`freeze-p22-oracle`, `p22-oracle-1/2`, `validate-p22-oracle-14645`) | **0** ×3 | **NONE — no `harbor check` was ever run on P22** | **15/15 as expected** (`tools/p22/mutation_results.txt`) | 3 | 0, 0, 0 | frozen; **not in any submission** |
| **P20** `candidates/p20-noshow-monitoring` | A clinic no-show model degraded after a reminder-policy change; decide retain / replace / remediate | policy feedback on the **evaluation population**; as-of feature correctness | **1** ×3 | **0** ×3 | **NONE** | **15/15** (`tools/p20/mutation_results.txt`) | 3 | 0, 0, 0 | frozen; not in any submission |
| **P31** `candidates/p31-fill-rate-dispute` | Supplier and customer compute "fill rate" differently; a contract with an unexecuted Schedule 4 must adjudicate, including abstention | which **instrument governs**, whether the incumbent code implements it, and whether the evidence settles it | **1** ×3 | **0** ×3 | **NONE** | **15/15** (`tools/p31/mutation_results.txt`) | 3 | 0, 0, 0 | frozen; not in any submission |

### Everything else measured (context for curation, none shipped)

| task | description (short) | trials | rewards | pass@3 | Oracle/Nop verified | status |
|---|---|---|---|---|---|---|
| task01 `01-revenue-reconciliation` | recognized revenue 8–9 % above billing | 6 recorded (3 counted in `results.json`) | census: 0,0,0,1,1,0 · `results.json`: 0,1,1 | 1 | 1 / 0 | development only |
| task02-EI `02-renewal-risk-regression__explicit-invariant` | instruction ablation of Task02 | 3 | 0,0,0 | 0 | 1 / 0 | **WITHDRAWN as evidence** — the audit found its added paragraph contradicted by its own graded reference |
| task03 `03-lead-score-evaluation` | lead-score model monitoring | 3 | 1,1,1 | 1 | 1 / 0 | development only; audit calls it documentation-lookup |
| task04 `04-retention-metrics-regression` | retention metric regression | 3 | 0,0,1 | 1 | 1 / 0 | development only; one material attractor noted |
| task05 `05-onboarding-experiment-readout` | experiment readout | 3 | 1,1,1 | 1 | 1 / 0 | development only; documentation-lookup |
| task06 `06-usage-statement-close` | usage-based billing close | 3 | 1,1,1 | 1 | 1 / 0 | development only; two leaks noted |
| g08 `g08-forecast-accuracy-vintages` | forecast accuracy across vintages | 3 | 0,0,1 | 1 | 1 / 0 | development only |
| g35 `g35-dispatch-priority-gate` | dispatch interference | 3 | 1,1,1 | 1 | 1 / 0 | development only; documentation-lookup |
| g36 `g36-tou-capacity-gate` | time-of-use capacity gate | 3 | 0,0,0 | 0 as graded | 1 / 0 | **EXCLUDED — confirmed verifier defect** (household-weighted answer graded against a load-weighted contract). Audit: 2/3 under a corrected estimand |
| g41 `g41-service-parts-rebalancing` | service-parts rebalancing optimum | 3 | 0,1,0 | 1 | 1 / 0 (note: `g41-oracle-v2/v3/probe2` = 0 during development, fixed by `g41-oracle-fix1/2/3` = 1) | built after packaging; `harbor check` **1** (`tb3-check-g41`) |
| g42 `g42-contractor-safety-rate` | contractor safety rate | 3 | 1,1,1 | 1 | 1 / 0 | built after packaging; documentation-lookup |
| g44 `g44-screening-precision` | payments-fraud screening precision | 3 | 0,1,1 | 1 | 1 / 0 | built after packaging |
| G37, G38, G39, G40, G43, G42-v1, G44-v1 | rejected pre-build | 0 | — | — | — | never built / never run |

`scripts/final10_frozen_checksums.txt` freezes G41 (`3f31849e44d9e392`), G42 (`4b4ded75469d229a`) and G44
(`e688a53ec78348cb`) — evidence that a ten-task expansion was started on the `final10` branch and **not
completed**. No 10-task submission artifact exists.

---

## 4. FIVE-TASK FALLBACK

### The exact five

From `scripts/final_tasks.json`: **Task02, G05, G10, G24, G34** (paths as in §3).

### Exact per-trial outcomes (recomputed from `jobs/`, not from the JSON)

| task | trial ID | job | reward |
|---|---|---|---|
| task02 | `02-renewal-risk-regression__nXXMdDm` | `task02-gemini3flash-diagnosis` | 0 |
| task02 | `02-renewal-risk-regression__pf9zaPc` | `task02-gemini3flash-diagnosis` | 0 |
| task02 | `02-renewal-risk-regression__JctTpSi` | `task02-gemini3flash-diagnosis` | 0 |
| g05 | `g05-sco-rollout-gate__PYhR2eh` | `g05-gemini3flash-baseline-1` | 0 |
| g05 | `g05-sco-rollout-gate__MMGNYFS` | `g05-gemini3flash-baseline-1` | 0 |
| g05 | `g05-sco-rollout-gate__rsDKTXQ` | `g05-gemini3flash-baseline-2` | 0 |
| g10 | `g10-censored-demand__eMXZbBi` | `g10-gemini3flash-baseline-1` | 0 |
| g10 | `g10-censored-demand__cLtM9yi` | `g10-gemini3flash-baseline-1` | 0 |
| g10 | `g10-censored-demand__LhEU3ny` | `g10-gemini3flash-baseline-1` | 0 |
| g24 | `g24-recommender-ope__wVmAykK` | `g24-gemini3flash-baseline-1` | 0 |
| g24 | `g24-recommender-ope__a8zVL7h` | `g24-gemini3flash-baseline-1` | 0 |
| g24 | `g24-recommender-ope__ykNY8fD` | `g24-gemini3flash-baseline-1` | 0 |
| g34 | `g34-fleet-reliability-gate__hLbWzqK` | `g34-gemini3flash-baseline-1` | **1** |
| g34 | `g34-fleet-reliability-gate__UPCLpLx` | `g34-gemini3flash-baseline-2` | 0 |
| g34 | `g34-fleet-reliability-gate__SdvVPQN` | `g34-gemini3flash-baseline-3` | **1** |

One trial excluded as infrastructure-invalid and replaced: **`g05-sco-rollout-gate__JnK5hsR`** (container torn
down before grading; root cause documented in `research/harness_process_sweep_defect.md`).

### Aggregates (recomputed)

| metric | value |
|---|---|
| trial-level successes | **2 / 15 = 13.33 %** (report quotes Wilson 95 %: 3.7–37.9 %) |
| task-level pass@3 | **1 / 5 = 20 %** (only G34) |
| per-task pass@1 | task02 0.000 · g05 0.000 · g10 0.000 · g24 0.000 · g34 0.667 |
| per-task passes | task02 0 · g05 0 · g10 0 · g24 0 · **g34 2** |

### ⚠ Bookkeeping contradiction found in `scripts/final_tasks.json`

The file pairs `valid_trials` with a parallel `rewards` array. For **G34 the pairing is wrong**:

| trial | `final_tasks.json` says | Harbor `result.json` + `reward.txt` say |
|---|---|---|
| `…__hLbWzqK` | 0.0 | **1.0** |
| `…__UPCLpLx` | 1.0 | **0.0** |
| `…__SdvVPQN` | 1.0 | 1.0 |

The multiset `{1,0,1}` is the same, so **every aggregate is unaffected**. `report/REPORT.md` §4 prints
"SdvVPQN 1 · UPCLpLx 0 · hLbWzqK 1", which is **correct**, and `report/data/results.json` records g34 as
`[1.0, 0.0, 1.0]`, also correct. **The error is confined to `scripts/final_tasks.json` and does not reach the
write-up.** Not repaired in this audit, per instruction.

### Validation status

| check | result |
|---|---|
| Oracle = 1 | **5 / 5** (`jobs/final-oracle-*`, all reward 1) |
| Nop = 0 | **5 / 5** (`jobs/final-nop-*`, all reward 0) |
| `harbor check`, Harbor default rubric | **5 / 5 reward 1, 11/11 criteria, no non-pass** |
| `harbor check`, TB3 task-implementation rubric | **5 / 5 reward 1**, but **5–10 of 35 criteria fail per task** (recurring: `task_toml_schema`, `expert_time_estimate`, `category_and_tags`, `separate_verifier_configured`, `verifier_execution_isolation`). One G34 finding (`anti_cheat_robustness`) is **disputed in writing** in `report/VALIDATION.md` with a stated basis: `tests/` is uploaded inside `Verifier.verify()` after the agent session, and no trajectory references `/tests`, `/solution`, `test.sh`, `reward.txt` or `/logs/verifier` |
| mutation suites | Task02 21/21 · G05 38/38 · G10 33/33 · G24 30/30 · G34 21/21. **G34's raw artifact is missing** (was `/tmp/g34_mutations2.csv`); only the prose record survives |
| frozen dirhashes | **all 5 MATCH** `scripts/frozen_checksums.txt`, recomputed this audit with the documented command: `02-renewal-risk-regression f696367794c1a25f` · `g05-sco-rollout-gate 77a6e432d9d2cba2` · `g10-censored-demand 047195e7a12d34cd` · `g24-recommender-ope 2c9cc2055ef796a5` · `g34-fleet-reliability-gate f14dd0c0dbcd763c` |

### Archive

| property | value |
|---|---|
| path | `submission_5task_fallback.zip` (repository root, **untracked**) |
| size | **8,471,008 bytes** |
| sha256 | **`c8561aad8300df6c832921fa5b86ea669def1cb04bbaba2e649e9919c5a9c760`** |
| mtime | 2026-09-22 15:28 |
| contents | 1,495 files, 16,227,089 bytes uncompressed: `samples/` (all five tasks incl. `task.toml`, `instruction.md`, `environment/`, `tests/`, `solution/`), `logs/<task>/trials/*` for all 15 trials, `report/REPORT.md`, `report/TRIALS.md`, `report/VALIDATION.md`, `report/figures/*.png`, `report/supporting/*`, `report/data/results.json` |
| relation to `submission.zip` | **byte-for-byte identical** — same sha256, same size. `submission.zip` differs only in mtime (02:33 vs 15:28). The "fallback" is a copy, not a different build |
| does it match the frozen task state? | **Yes.** I extracted `samples/*` to a temp dir and diffed against `candidates/`. The only differences are directories present in the working tree and absent from the archive: `notes/`, `data/`, `notebooks/`, `reports/`, `out/`, `tests/__pycache__`. **Every one has zero git-tracked files** — they are local build artifacts, and `candidates/*/environment/workspace/data/` is explicitly `.gitignore`d. No tracked task file differs |

### Is it immediately submittable?

**Mechanically yes; scientifically it ships a superseded failure analysis.** The archive is complete, internally
consistent, validated, and matches the frozen tasks. But `report/REPORT.md` inside it (sha256
`3085b6a33495948e8c88a46753b5838dbc58f1165fe1d472363222b11cc7f0b0`, byte-identical to the working-tree copy) still
contains three claims that the repository's own later audit revised — see §6 and §7 requirement 13.

---

## 5. PROSPECTIVE EXPERIMENT

### Preregistered question and predictions

Source: **`research/phase3/analysis_plan.md`**, sha256
`c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824`. `git log --all` shows this file has **exactly
one commit in its entire history — `aeddc1c`, the freeze commit.** It has never been modified.

The plan states its own purpose: *"Written and committed at freeze, before any target-model contact… so that the
labelling rules and the disconfirming outcomes cannot be chosen after the results are seen."*

Seven predictions, each with a pre-stated disconfirming outcome (quoted):

| # | prediction | disconfirmed if |
|---|---|---|
| P1 | in ≥70 % of failed trials, no inventoried L3 (discriminating/falsification) route was attempted | L3 routes are attempted in more than 30 % of failures |
| P2 | trials attempting any L3 route pass at a higher rate than those that do not | rates equal or inverted |
| P3 | the first consequential error is at a commitment step in ≥60 % of failures | failures dominated by arithmetic or implementation errors |
| P4 | ≥2 of every 5 failures pass ≥3 of their own coherence checks | failures are incoherent rather than coherent |
| P5 | `criterion_decision` = 1 with another criterion = 0 in 20–50 % of failures | decisions fail whenever quantities fail, or share outside band |
| P6 | revision after a self-produced contradiction occurs in <20 % of trials that produce one | revision is frequent |
| P7 | on P31, wrong verdicts skew toward `incumbent_incorrect` where the incumbent is right | symmetric, or skewed toward deference |

The plan also states in advance: *"With nine trials per model family the confidence intervals are wide; no
prediction is claimed to be settled by this set alone. The set is sized to detect a gross departure, not to
estimate a rate."*

### Frozen tasks and freeze provenance

| task | `lock.json` → `task.digest` (in the plan) | dirhash manifest | recomputed this audit |
|---|---|---|---|
| p22-gauge-recalibration | `sha256:72fedb37da7b48c8488ad8afbcdf0d46b501dcdb52a6b05698a20370425629a7` | `a0570585c3927b53` | **`a0570585c3927b53` MATCH** |
| p20-noshow-monitoring | `sha256:f033ea1f5a8876514566174e8a99cf36d24e09cd54e9bba7ddfb5c16ffe60d8a` | `2c3c374b07f233fa` | **`2c3c374b07f233fa` MATCH** |
| p31-fill-rate-dispute | `sha256:3208a6d39014bff924784636da9a0837d528833f22e0666197d445330821f3ae` | `e18bf13d6080f987` | **`e18bf13d6080f987` MATCH** |

Freeze commit `aeddc1c`, tagged `phase3-freeze-2026-09-24`. Manifest: `research/phase3/completed_freeze_manifest.txt`.
Recomputation command (from `tools/bench/freeze_manifest.sh`):
`git ls-files <task> | xargs shasum -a 256 | shasum -a 256 | cut -c1-16`.

### Protocol

Exactly three valid trials per task, sequential, one trial per Harbor job, all on the frozen digest. Validity
adjudicated **from job artefacts alone, before any reasoning was read** (plan §2). Invalid causes enumerated in
advance: API/quota/auth error, agent-setup timeout, verifier never executed, or the documented container-teardown
signature. Spend stop threshold $10.

### Model

**`google/gemini-3-flash-preview`** via the `gemini-cli` agent, Harbor 0.21.0 — recorded in every adjudication
JSON and every `result.json`. **One model family only**; a second family was deliberately not run, so rival A7
(single-model artefact) cannot be discriminated.

### Valid / invalid runs

**9 valid, 0 invalid, 0 replacements.** All nine `research/phase3/exposure/adjudication_*.json` files carry
`"verdict": "VALID"`, `"invalid_reasons": []`, and `"digest_matches_freeze": true`.

Additionally, `research/phase3/exposure/collected_db_digests.txt` verifies that **all nine agents worked on the
frozen extract, unmodified** — every read-only input database digest matches the frozen expectation
(`appointments.sqlite 9540a0115be159bb` ×3, `inspection.sqlite 0ddb25a0799f1be0` ×3,
`service.sqlite 5065cf4081dce124` ×3).

### Exact results

| task | successes / 3 | pass@1 | pass@3 | trial-level |
|---|---|---|---|---|
| P22 | **0/3** | 0.000 | 0 | `rBUvW2D` 0 · `nt5YXX8` 0 · `DxMjiB7` 0 — all failed `quantitative_results`, `decision` |
| P20 | **0/3** | 0.000 | 0 | `TirBLuz` 0 (failed `quantitative_results`) · `iwPaF7u` 0 (`identification`, `quantitative_results`) · `c654dzn` 0 (`identification`, `quantitative_results`, `decision`) |
| P31 | **0/3** | 0.000 | 0 | `GyUgp7D` 0 (**all seven criteria failed**) · `AjqzDN8` 0 (`identification`, `decision`) · `3fnpGae` 0 (`identification`, `decision`) |
| **aggregate** | **0 / 9** | 0.000 | **0 / 3** | — |

### Criterion totals across all 9 valid trials

| criterion | passes |
|---|---|
| `evidence_reconstruction` | **8/9** |
| `scientific_object` | **8/9** |
| `identification` | **4/9** |
| `estimator_implementation` | **8/9** |
| `quantitative_results` | **2/9** |
| `independent_validation` | **8/9** |
| `decision` | **2/9** |

This is the instrument the prospective phase added: every task is 0/3 on binary reward while separating cleanly
on five of seven criteria.

### Cost

`research/phase3/exposure/cost_ledger.txt`: **$1.4667 total**, per trial $0.0068–$0.2725. Stop threshold $10.00
**not reached**. The $0.0068 outlier is `p31-prospective-1` (23,987 input / 693 output tokens).

### Were the predictions supported?

Quoted from `research/phase3/HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md` §24, which states *"No overall research
conclusion is drawn."*

| # | observed | status |
|---|---|---|
| **P1** | **1 of 9 failed trials (11 %)** attempted no L3 route; the other 8 attempted ≥1, and 6 attempted ≥2 | **DISCONFIRMED.** The plan's own stated disconfirming outcome (">30 % of failures attempt L3") is met |
| **P2** | 0/8 among L3-attempting, 0/1 among non-attempting | **NOT EVALUABLE** — with zero successes the comparison is undefined |
| **P3** | commitment-step first errors 5 of 9 (**56 %**) vs the ≥60 % prediction; estimator-step 3 of 9; no analysis performed 1 of 9 | **just below threshold**, n = 9 |
| **P4** | **8 of 9 (89 %)** performed ≥1 passing in-frame coherence check while the analysis was wrong | **observed above threshold** |
| **P5** | **2 of 9 (22 %)** on the frozen strict definition | **inside the 20–50 % band** |
| **P6** | **8 of 8 applicable trials (100 %)** revised at least once | **DISCONFIRMED.** Stated disconfirming outcome ("revision is frequent") is met |
| **P7** | **0** wrong verdicts were `incumbent_incorrect`; observed instead `incumbent_correct` where deferral was required, and `not_determinable` where a verdict was determinable | **predicted direction NOT observed** |

**Direct answer to "was the discriminating-test-omission hypothesis supported?" — NO.** P1 is the instantiation of
that hypothesis on this set, and its pre-registered disconfirming outcome was met. Phase 1 had observed zero
falsification-class tests across 45 trials; prospectively, **8 of 9 trials attempted at least one inventoried
discriminating route and still failed.** The results handoff §27 states this explicitly and refuses to carry the
phase-1 figure into any prospective claim.

No prediction was rewritten, re-labelled or reinterpreted: §746 of the results handoff records "no preregistered
prediction changed — P1–P7 as frozen; P7 reported as not observed rather than revised."

### Exploratory / post-hoc observations (labelled as such in the source, §26)

1. **`p31-prospective-1` produced no output.** Four trajectory steps; step 2 read the supply agreement including
   Schedule 4's "[To be agreed]"; step 4 recorded **zero completion tokens** and the session ended. No code run,
   no output written. *The frozen taxonomy has no label for this; recorded OTHER/UNCLASSIFIED.*
2. Near-identical answers across P22's three trials (same offsets 7.81 / 0.30 µm, same corrected rate 3.81 %)
   despite step counts of 56, 94 and 60.
3. The incumbent pipeline's docstring — *"Tooling was on schedule and no operator or shift effect reaches
   significance"* — propagated into the final code of two of three P22 trials.
4. P20's false-positive feed audit is *consistent with* merging two attribution categories; the trajectories were
   not instrumented to confirm the mechanism.
5. P20's programme effect was wrong in **sign** in two trials while correct in magnitude to within 0.3 pp of a
   10.849 pp truth.

---

## 6. WHAT THE EVIDENCE ACTUALLY SAYS

### Strongest defensible conclusions

1. **`gemini-3-flash-preview` solves 1 of 5 final tasks at pass@3 (2 of 15 trials)**, on frozen tasks, one Harbor
   digest per task, Oracle 1 / Nop 0 / check-rubric 1 each. Mechanically reverified this audit.
2. **All 13 failed final-suite trials are model-side failures**, reproducible from the agents' own submitted code,
   with zero environment friction.
3. **Recognition of the problem class is not the bottleneck.** In every failed final-suite trial the agent
   identified the broad class; prospectively, `evidence_reconstruction` and `scientific_object` each passed 8/9
   while `quantitative_results` passed 2/9.
4. **Coherence checks computed inside a wrong frame reliably confirm it.** Demonstrated in ≥5 phase-1 trials and
   in 8 of 9 prospective trials.
5. **A decision-only grader would materially overstate performance.** 6 of 13 failed phase-1 trials reached the
   correct business decision with wrong quantities (on G24, 3/3 trials and 12/12 extract-level decisions).
   Criterion-level grading makes this visible: prospectively `decision` passed 2/9 while
   `independent_validation` passed 8/9.
6. **Difficulty is concentrated at estimand and identification selection**, not at evidence volume or horizon:
   every 0/3 task was reconstructed correctly at the operational-state layer and failed at one identifiable step.
7. **The prospective set is harder than the shipped five**: 0/9 with 0/3 tasks at pass@3, versus 2/15 and 1/5.

### Unsupported conclusions — do not claim

1. **NOT** that F9 (right method family, wrong statistical object) dominates. `report/REPORT.md` says "10 of the
   13"; the 2026-09-23 audit says **4–6 under a strict bar** and names F1/F4 as dominant, adding F11
   (coherence stopping).
2. **NOT** "no failed trial ran a falsification check." The audit found **one** trial ran a falsification-class
   check (on its diagnosis, not its estimator) — and the prospective set found **8 of 9 trials attempted a
   discriminating route.**
3. **NOT** that agents omit discriminating tests as a general disposition. That is the hypothesis the prospective
   experiment was built to test, and **P1's disconfirming outcome was met.**
4. **NOT** that the suite measures long-horizon capability. Failures occur early; trials used 4–14 minutes of a
   90-minute budget; the hardest tasks were not the longest.
5. **NOT** that these represent professional multi-hour work. The 90–300 minute estimates are **author
   judgements**; no human has attempted any task under measurement.
6. **NOT** that the pilot pool is uniformly high quality. The audit's own test calls Task03, Task05, G35 and G42
   documentation-lookup tasks; Task06 has two leaks.
7. **NOT** that the benchmark is defect-free. Two confirmed task-side defects (G36 verifier; Task02
   explicit-invariant variant), both outside the five, plus an attractor in Task04 and an accepted-family
   narrowing in G10.
8. **NOT** anything causal from 15 tasks and one model. "Stated vs derived" was judged after results were known.
9. **NOT** that 20 % pass@3 generalises to a stronger model, a different harness, or more trials. n = 3 per task;
   the G05 gate estimate varied across four runs by more than the distance between truth and the threshold.
10. **NOT** that the suite's 20 % is unbiased — it was selected using the same trials it reports, so it is
    biased **low**.

### Contradictions between current documents and frozen evidence — reported, not repaired

| # | contradiction | evidence |
|---|---|---|
| **C1** | `scripts/final_tasks.json` pairs G34's trial IDs with the wrong rewards (`hLbWzqK` 0.0 vs actual 1.0; `UPCLpLx` 1.0 vs actual 0.0) | Harbor `result.json` for `g34-gemini3flash-baseline-1/2`, and `reward.txt`. Aggregates unaffected; `REPORT.md` and `results.json` are correct |
| **C2** | `report/REPORT.md` — **in the working tree and inside the shipped archive** — still asserts "10 of the 13 failed trials are of this kind", "In 5 of the 13 the business decision was correct anyway", and "**No failed trial ran a falsification check**" | The 2026-09-23 audit revises these to 4–6, **6 of 13**, and "one trial ran a falsification-class check". `REPORT.md` last committed `e44c937` (2026-09-22); audit committed `039cf42` (2026-09-23). **The shipped write-up predates its own audit** |
| **C3** | Two different measured populations are quoted without being distinguished: `REPORT.md` and `results.json` say **12 measured pilot tasks / 36 trials / 18 successes / 8 with pass@3**; the audit and the prospective handoff say **15 measured tasks / 45 valid trials**. Both are derivable — the 15 adds G41, G42, G44, built after packaging — but **the "zero falsification across 45 trials" claim rests on a population that is not the one in the shipped report** | `report/data/results.json` `pilot_summary`; `research/audit/AUDIT_2026-09-23.md` §2 |
| **C4** | Phase 1: "no falsification-class checks across 45 trials." Prospective: "8 of 9 trials attempted at least one L3 discriminating route." | `AUDIT_2026-09-23.md` §19.4 vs `HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md` §24 P1. The results handoff already refuses to pool them (§27); no document yet reconciles them for a reader |
| **C5** | G34's mutation result (21/21) survives only as prose. The raw artifact was written to `/tmp/g34_mutations2.csv`, which **no longer exists**; the other four shipped tasks have durable JSON/TXT | `report/g34_prebaseline_validation.md` §189, §A13; `ls /tmp/g34_mutations2.csv` → absent |
| **C6** | `harbor check` passes at reward 1 for all five, but under the **TB3 rubric** 5–10 of 35 criteria fail per task. Saying "`harbor check` passed" without that qualification overstates it | `report/VALIDATION.md` |

### Important limitations

n = 3 per task and one model family. Selection-on-reported-trials bias. Synthetic generators (exact truth, at the
cost of realistic noise). Binary reward in the five-task suite (criterion-level only in the prospective three).
Verifier hardening below TB3's separate-verifier bar. AI-assisted authoring throughout, under gates that
demonstrably missed the G36 contract/verifier mismatch. **No `harbor check` was ever run on P22, P20 or P31.**

---

## 7. ABUNDANT REQUIREMENTS MATRIX

Requirements as restated in `research/audit/abundant_requirements.md` — **the source assignment is not in the
repository** (§2), so "Requirement" here means "requirement as restated by the project owner".

| # | Requirement | Evidence | Status | Remaining action |
|---|---|---|---|---|
| 1 | requested number of tasks (restated 5–10) | 5 tasks in `scripts/final_tasks.json`, 5 in the archive's `samples/` | **MET** against the restatement · **exact number NOT LOCATED** | none, unless the true requirement was ≥6 |
| 2 | real/professional distribution requirement | `REPORT.md` §1; `research/distribution_matrix.md` | **MET WITH CAVEAT** — the audit finds the slice was named *after* the tasks were built, and the five span two task architectures | disclose both in §1/§10 |
| 3 | difficulty target (<30 % pass@3) | **1/5 = 20 %** recomputed | **MET as a point estimate** | state the 3.6–62.4 % interval and the low-bias selection effect |
| 4 | Gemini 3 Flash Preview | `gemini-cli__gemini-3-flash-preview__adhoc` in all 15 counted `result.json`s | **MET**, corroborated by artifacts | none |
| 5 | ≥3 trials/task | 15 counted trials, exactly 3 per task, each on one Harbor task digest | **MET** | none |
| 6 | Harbor format | all five have `task.toml`, `instruction.md`, `environment/Dockerfile`, `tests/test.sh`, `solution/solve.sh`; Harbor 0.21.0 | **MET** | none |
| 7 | Oracle = 1 | `jobs/final-oracle-*` reward 1 ×5 (plus prebaseline duplicates) | **MET** | none |
| 8 | Nop = 0 | `jobs/final-nop-*` reward 0 ×5 | **MET** | none |
| 9 | `harbor check` | default rubric 11/11 ×5, reward 1; TB3 rubric reward 1 ×5 but **5–10 of 35 criteria fail each** | **MET, with a material qualification** | qualify the claim in the report; decide whether to contest the TB3 findings beyond the one already disputed |
| 10 | trajectory inspection | per-task analyses in `research/*_gemini_analysis.md`, `research/g*/G*_gemini_baseline_analysis.md`, re-read and partly revised by the audit; `REPORT.md` §6 | **MET** | fold the audit's revisions in |
| 11 | write-up requirements | `report/REPORT.md`, 524 lines / ~4,635 words, 12 sections + 3 appendices | **MET in form** · **content superseded** (C2) | **apply the audit's 7 required corrections** |
| 12 | distribution/difficulty analysis | `REPORT.md` §1–§2; `figures/difficulty_curve.png` | **MET WITH CAVEAT** — expert-time estimates are author judgements with no human trials | mark them as estimates |
| 13 | failure analysis | `REPORT.md` §5–§6 | **NOT CURRENT** — three claims revised by the audit still stand in the shipped text | **the single most important fix before submission** |
| 14 | pass@1 / pass@3 | pass@1 per task and pass@3 = 1/5 in `REPORT.md` §4 and `results.json` | **MET** · requirement wording **NOT LOCATED** | none |
| 15 | plots | `report/figures/{difficulty_curve,failure_modes,pilot_successes}.png`, generated 2026-09-22 by `scripts/make_figures.py` | **MET** · requirement **NOT LOCATED** | `failure_modes.png` encodes the superseded taxonomy counts — regenerate if §5 is corrected |
| 16 | research-awareness discussion | `REPORT.md` §8: MLE-bench, DSBench, InfiAgent-DABench, DSAEval, DAB, DataSpace, UniDataBench, DataCross, AvalancheBench | **MET** | optional: the phase-2 corpus in `research/phase2/literature.md` is richer |
| 17 | scaling plan | `REPORT.md` §9: mechanism × domain skin × data regime × incumbent bug × decision rule, with QA gate and costs | **MET** | none |
| 18 | packaging/submission | `submission_5task_fallback.zip`, sha256 `c8561aad…`, 1,495 files | **archive exists and is complete** · **requirement itself NOT LOCATED** | confirm the required format/channel from the original assignment, which is not in the repo |
| 19 | automation disclosure | `REPORT.md` §11 | **MET** | none |
| 20 | genuine difficulty, not defects | audit §13: all 13 failed final-suite trials trace to model-side defects; G36 excluded before submission; Task02-EI not in the suite | **MET for the shipped five** | disclose the Task02-EI withdrawal and the G10 narrowing |
| 21 | piloting and curating down | 12 tasks in `results.json` / 15 in the audit; ~20 concepts rejected pre-build with recorded gates | **MET** | state which population the count refers to (C3) |

---

## 8. EXISTING WRITE-UP / ANALYSIS ARTIFACTS

| path | purpose | current? | safe to use? | superseded? |
|---|---|---|---|---|
| `report/REPORT.md` (524 lines, sha256 `3085b6a3…`) | the submission write-up | **NO** — last committed 2026-09-22, before the 2026-09-23 audit | **only after the seven corrections** | §5 and §6 failure-mode claims superseded by `research/audit/AUDIT_2026-09-23.md`; §4 results and §10 limitations are accurate |
| `report/TRIALS.md` | Appendix C: trial IDs, invalid runs, costs; generated from raw `result.json` | yes | **yes** | no |
| `report/VALIDATION.md` | Appendix B: Oracle/Nop by Harbor `TrialLock` digest; both check rubrics; the disputed TB3 finding | yes | **yes** — and it is the only place the TB3 criterion-level failures are disclosed | no |
| `report/figures/difficulty_curve.png` | pilot difficulty distribution | yes | yes | no |
| `report/figures/pilot_successes.png` | per-task pilot outcomes | yes | yes | no |
| `report/figures/failure_modes.png` | failure-mode counts | **NO** | **not without regeneration** | encodes the F9 10/13 counts the audit revised |
| `report/data/results.json` | machine-readable pilot (12 tasks/36 trials) + final (5/15) + excluded + costs | yes | **yes** — and it is **correct** on G34 where `final_tasks.json` is not | no |
| `report/task0{1..6}_mutations.{txt,json}`, `report/g08_mutations.*` | mutation-suite outputs | yes | yes | no; **note there is no `g05/g10/g24/g34` file here** — those live in `research/g*/shortcuts_report.json` and, for G34, only in prose |
| `report/{task0*,g05,g08,g10,g24,g34,g35}_*validation.md` | per-task pre-baseline validation | yes | yes | no |
| `research/audit/AUDIT_2026-09-23.md` (24 sections) | read-only scientific audit; **supersedes REPORT.md §5–§6**; §19 can-claim / §20 cannot-claim / §23 recommended action | yes | **yes — the authoritative failure analysis** | no |
| `research/audit/abundant_requirements.md` | 18-item requirement audit; records that the assignment text is missing | yes | yes | no |
| `research/phase3/analysis_plan.md` (sha256 `c590cb56…`) | the preregistered plan | yes, and **immutable** — one commit ever | **yes** | no |
| `research/phase3/HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md` (32 sections) | prospective results, P1–P7 verdicts, trajectory analyses, cost, integrity | yes | **yes** | no |
| `research/phase3/HANDOFF_2026-09-24.md` (38 sections) | phase-3 implementation handoff | yes | yes | no |
| `research/phase3/exposure/*` | adjudications ×9, cost ledger, first-pass results, db digests, belief-update scan, truth reference | yes | **yes — primary evidence** | no |
| `research/phase3/comparison_with_five.md` | what P22/P20/P31 add over the five; DP3/DP6 gaps | yes | yes | no |
| `research/phase2/HANDOFF_2026-09-23.md` (2,152 lines) | phase-2 research handoff: world architecture, DP1–DP22, rivals A1–A8, literature | yes | yes | no |
| `research/task_design_failure_analysis.md`, `research/cross_task_*.md`, `research/*_gemini_analysis.md` | trajectory-level analyses | yes, but predate the audit | **check against the audit before quoting** | partly |
| `scripts/final_tasks.json` | the five tasks + counted trial IDs + rewards | **NO — G34 reward pairing is wrong (C1)** | use only for the task list and trial IDs | reward values superseded by `jobs/` and `results.json` |
| `scripts/frozen_checksums.txt` | dirhashes of the five | yes — **all 5 recomputed MATCH** | yes | no |
| `scripts/final10_frozen_checksums.txt` | dirhashes of G41/G42/G44 | yes | yes | evidence of an **abandoned** 10-task expansion |
| `submission.zip` / `submission_5task_fallback.zip` | the packaged deliverable, **byte-identical**, sha256 `c8561aad…` | archive is complete and matches frozen tasks | **yes mechanically**; it embeds the superseded `REPORT.md` | not superseded as a package; its report is |
| `HANDOFF_2026-09-25_MERCOR_PROPOSAL.md`, `HANDOFF_2026-09-25_MERCOR_FINAL.md` | Mercor fellowship proposal handoffs | current for Mercor | **not Abundant deliverables** | no |

---

## 9. MERCOR SEPARATION

### What the Mercor work changed, mechanically

`git diff --stat 5235aa7..HEAD` (prospective-results commit → HEAD): **15 files, 3,320 insertions, 0 deletions.**
Every change is a **new file**. No existing file was modified or deleted.

`git diff --name-status 5235aa7..HEAD -- candidates/ research/phase3/ jobs/ tools/ scripts/ report/ submission/`
returns exactly **one** line:

```
A	tools/bench/visible_vs_family.py
```

— an **added**, read-only analysis script. Nothing under `candidates/`, `research/phase3/`, `jobs/`, `scripts/`,
`report/` or `submission/` was modified.

**Mercor-only files (safe to ignore entirely for Abundant):**
`research/mercor_apex/{RESEARCH_GAP, RELATED_WORK, IDEA_RED_TEAM, METHODOLOGY, EXPERIMENT_DESIGN,
THREE_MONTH_PLAN, SOURCES, PROPOSAL_FULL, PROPOSAL_SHORT, REVIEW, PILOT_VERIFICATION}.md`,
`research/mercor_apex/mutation_visible_vs_family.json`, `tools/bench/visible_vs_family.py`,
`HANDOFF_2026-09-25_MERCOR_PROPOSAL.md`, `HANDOFF_2026-09-25_MERCOR_FINAL.md`.

**Confirmed: nothing affecting frozen prospective results changed during the Mercor work.** `analysis_plan.md` has
one commit in its entire history. All three prospective dirhashes and all five final-suite dirhashes recompute to
their frozen values. All nine adjudications and all nine database digests are unchanged and matching.

### What the Mercor work newly computed, and its epistemic status

Two quantities were produced that **do not exist anywhere in the preregistered plan**:

1. **A visible-extract-only re-slice of the nine frozen trials.** By re-reading the frozen `criteria_notes.txt`
   and restricting attention to the *visible* extract, the Mercor work reports P22 **3/3**, P20 **0/3**, P31
   **1/3** → **4/9**, against the preregistered whole-family result of **0/9**. This is a **post-hoc
   re-slicing of a frozen metric**, computed 2026-09-25. It corrected a claim the Mercor brief had asserted (that
   P20 was also 3/3 on the visible extract — it was not; all three P20 trials failed `quantitative_results` on
   the *visible* extract).
2. **A model-free mutation calibration** (`tools/bench/visible_vs_family.py` →
   `research/mercor_apex/mutation_visible_vs_family.json`): of 42 defective single-defect mutants across P22/P20/P31,
   **30 caught numerically on the visible world, 10 caught only by a hidden sibling, 2 numerically invisible on
   all four** (those two caught by procedure-inspecting criteria). All three reference procedures pass 4/4.
   Computed 2026-09-25, after the results were known.

### What may inform the Abundant write-up

- **Nothing that is not already in the frozen phase-3 record.** The prospective results, criterion totals, cost
  ledger, adjudications and P1–P7 verdicts all predate the Mercor work and are independently citable.
- The Mercor work's *reading* of the P22 mechanism — that all three trials hard-coded `"tooling": 0.0`, that
  `wear` appears zero times in all three trajectories, and that the frozen tooling truth is 0.167 pp on the
  visible extract versus 3.083 pp on hidden_c — is **descriptive of frozen artifacts and verifiable from them**
  (`jobs/p22-prospective-*/…/verifier/criteria_notes.txt` reads
  `attribution_pp[material] 3.92 vs 0.817` and
  `decision: hidden_c: supplier_decision 'raise_supplier_nonconformance' vs 'no_supplier_action'`). That is
  usable as a **worked example**, cited to the frozen evidence rather than to the Mercor documents.

### What must NOT be presented as prospective Abundant evidence

1. **The 4/9 visible-only figure.** It is not the preregistered metric, it was computed after the results were
   seen, and presenting it as a prospective finding would misrepresent the plan.
2. **The 23.8 % (10/42) sibling-only detection rate.** Post-hoc, model-free, three self-authored worlds, defects
   written by the worlds' own author. The Mercor documents themselves label it "pilot calibration, not prevalence".
3. **"Conditional correctness" as a framing for what ForensicDS measured.** It is a *different research question*,
   formulated after the fact. ForensicDS's preregistered question was about discriminating-test behaviour, and
   that prediction was disconfirmed.
4. **Any claim that the world-family design "detects what single-instance grading misses" as a prospective
   result.** It is a post-hoc property of the instrument, not a preregistered finding.
5. **Any Mercor-side novelty or literature claim.** Irrelevant to Abundant and unverified against the shipped
   report's §8.

---

## 10. REMAINING WORK

### A. MUST finish before submission

1. **Correct `report/REPORT.md` §5–§6 to the audited failure analysis.** The audit's seven required corrections
   (`AUDIT_2026-09-23.md` §23), all report-only:
   (i) replace the F9 10/13 table with the audit counts, naming F1 and F4 as dominant and adding F11 (coherence
   stopping) with its five instances; (ii) restate the G05 F10 claim at extract level (one of three trials
   decision-correct on all four extracts; 10 of 12 extract-level decisions right); (iii) add the
   falsification-route evidence — what each task shipped and that it was not taken; (iv) annotate G36 as "0/3 as
   graded; 2/3 under the corrected estimand; one genuine model failure"; (v) disclose that the Task02
   explicit-invariant ablation is contradicted by its own reference implementation and withdraw it as evidence;
   (vi) disclose the G10 accepted-family narrowing; (vii) state that the five span two task architectures and
   that Task03/05/06/G35/G42 are documentation-lookup tasks by the audit's own test.
2. **Fix the "No failed trial ran a falsification check" sentence** (line 40). The audit found one such check.
3. **Regenerate `report/figures/failure_modes.png`** after (1), since it encodes the superseded counts.
4. **Rebuild the archive** after the report changes, and record the new sha256. The current archive embeds the
   uncorrected report.
5. **Decide and state which measured population the report uses** (12 tasks/36 trials vs 15/45) and make every
   count in the report consistent with that choice (C3).
6. **Qualify the `harbor check` claim** so it does not read as "35/35 TB3 criteria passed" (C6).
7. **Recover the original assignment text from outside the repository** and re-check requirements 1, 3, 14, 15 and
   18 against it. Five requirements are currently NOT LOCATED, including the packaging requirement.

### B. SHOULD improve — evidence already exists, no new runs needed

1. **Fix the G34 reward pairing in `scripts/final_tasks.json`** (C1). One-line correction; aggregates unchanged.
2. **Add the prospective experiment as a separate, clearly-labelled section or appendix.** 9 valid trials, 0/9,
   criterion-level results, $1.4667, preregistered plan with its sha256, and **the honest report that P1 and P6
   were disconfirmed and P7's direction was not observed.** A disconfirmed preregistered prediction, reported as
   such, is stronger evidence of method than a confirmed post-hoc one. Requires zero new runs.
3. **Reconcile C4 in prose** — phase 1 saw no falsification-class checks in 45 trials; prospectively 8 of 9
   attempted a discriminating route and still failed. Both are in the repository; no document yet explains them
   together for a reader.
4. **Note G34's missing mutation artifact** (C5) in Appendix B, rather than letting a reader assume a durable file
   exists.
5. **Move the criterion-level grading story forward.** It is the sharpest methodological contribution in the
   repository and appears nowhere in the shipped report.
6. **State the Wilson intervals wherever 13.3 % and 20 % appear** — already computed in §10 of the report but not
   attached to the headline numbers.

### C. OPTIONAL / not worth doing

1. Expanding to a 10-task suite. G41/G42/G44 are frozen, but the audit's own finding is that the marginal new task
   got *easier* (two of three are reading tasks), and its recommendation was explicitly **not** to build more.
2. Rewriting `research/*_gemini_analysis.md` to match the audit. Supporting material; the report is what is read.
3. Contesting the remaining TB3 criterion failures beyond the one already disputed. `harbor check` returns
   reward 1 regardless.
4. Re-running `harbor check` on P22/P20/P31. They are not in the submission, and it costs model spend.
5. Enriching the related-work section from the phase-2 corpus. §8 already satisfies the requirement.

### DO NOT TOUCH — would contaminate or invalidate frozen evidence

1. **`research/phase3/analysis_plan.md`** — sha256 `c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824`,
   one commit in its history. Any edit destroys the preregistration and with it the only reason the 0/9 result is
   scientifically meaningful.
2. **`candidates/p22-gauge-recalibration`, `candidates/p20-noshow-monitoring`, `candidates/p31-fill-rate-dispute`** —
   frozen at `a0570585c3927b53` / `2c3c374b07f233fa` / `e18bf13d6080f987` under tag `phase3-freeze-2026-09-24`.
   No file, tolerance, hidden extract, generator or verifier.
3. **`candidates/02-renewal-risk-regression`, `g05-sco-rollout-gate`, `g10-censored-demand`,
   `g24-recommender-ope`, `g34-fleet-reliability-gate`** — frozen at the five dirhashes in
   `scripts/frozen_checksums.txt`; the 15 counted trials ran on those exact digests. Changing any file breaks the
   identity between the shipped results and the shipped tasks.
4. **`jobs/`** — all 64 Gemini solver trials plus every Oracle/Nop/check run. The nine prospective trial
   directories are deliberately force-added to git because the trajectories are the primary evidence.
5. **`research/phase3/exposure/`** — the nine adjudications, cost ledger, first-pass results, database digests,
   belief-update scan and truth reference. These were written before any reasoning was interpreted.
6. **`research/phase3/completed_freeze_manifest.txt`** and the tag `phase3-freeze-2026-09-24`.
7. **The P1–P7 verdicts** in `HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md` §24. Re-labelling a disconfirmed
   prediction is the one move that would make the whole prospective phase worthless.
8. **`submission.zip`** — keep at least one pristine copy of the current package before rebuilding anything, so
   the 2026-09-22 state stays recoverable. Both archives are currently byte-identical, so overwriting one without
   preserving the other loses the only snapshot.
9. **Git history.** No rebase, amend, tag move or force push. The freeze tag's value is that it is old.

---

## 11. RECOMMENDED NEXT DECISION FOR CHATGPT

**I am not making this decision.** Three realistic paths follow from the evidence.

### Path 1 — Submit the five-task suite with a corrected failure analysis, prospective work excluded

Apply the seven audit corrections, regenerate the failure-mode figure, rebuild the archive, submit.

- **Cost:** report editing only. No model spend. Probably a day.
- **Gets you:** every restated requirement met; 1/5 = 20 % pass@3 against a <30 % target; a failure analysis that
  matches the trajectories; no unresolved internal contradiction.
- **Trade-off:** discards the strongest methodological work in the repository. The preregistered experiment, the
  criterion-level instrument and a disconfirmed-then-honestly-reported hypothesis all stay invisible. It is the
  safest submission and the least impressive one. It is also what the repository's own audit recommended
  (`AUDIT_2026-09-23.md` §23, option D) — though that recommendation was written **before** the prospective
  experiment ran.

### Path 2 — Submit the five-task suite plus the prospective experiment as a labelled research appendix

Path 1, plus a clearly separated section: preregistered plan with its sha256, frozen digests, 9/9 valid trials,
0/9, the seven-criterion breakdown, $1.4667, and the verdicts **including P1 and P6 disconfirmed and P7's
direction not observed**.

- **Cost:** Path 1 plus writing. Still no model spend — every number already exists.
- **Gets you:** demonstrated ability to preregister, freeze, execute under protocol, and **report a disconfirmed
  hypothesis without reframing it.** For a research role that is usually the most informative signal available.
  It also supplies the thing the five-task suite lacks — criterion-level grading that separates decision
  correctness from scientific correctness.
- **Trade-off:** you must handle C4 in the open. The submission would contain "no falsification checks in 45
  trials" *and* "8 of 9 prospective trials attempted a discriminating route and still failed." Handled well that
  is a real contribution; handled badly it reads as a contradiction. It also lengthens the write-up, and the
  prospective tasks have **no `harbor check`**, so they must be presented as a research experiment rather than as
  additional benchmark tasks.

### Path 3 — Re-scope the submission around the prospective set as the headline

Lead with P22/P20/P31, criterion-level grading and the preregistration; demote the five to a pilot.

- **Cost:** substantial rewriting, plus `harbor check` on three tasks (model spend) if they are to be presented as
  benchmark tasks rather than as an experiment.
- **Gets you:** the most scientifically interesting story, and the only one where the headline metric is
  criterion-level rather than binary.
- **Trade-off:** **the prospective set does not satisfy the restated requirements as a benchmark.** Three tasks
  against a 5–10 restatement, no `harbor check`, 0/9 with 0/3 tasks at pass@3 — which may read as *too* hard
  rather than well-calibrated. It also inverts the curation story the five-task suite tells. I judge this the
  weakest path against the requirements as restated, and I flag that judgement as mine.

**The gap that no path closes from existing evidence:** five requirements are NOT LOCATED because the assignment
text is not in the repository, including the packaging requirement. That is a retrieval task, not an
experimental one.

---

## 12. HANDOFF EVIDENCE

### Git

```
branch               final10
HEAD                 7e6d4d760995c7bd3729a8cbba31e5a31a8801fe
main                 8cf774e  (ancestor of final10)
fallback-5task-...   8cf774e  (identical to main)
tag                  phase3-freeze-2026-09-24  ->  tag object bedb131  ->  commit aeddc1c06d6584df1554abe8b101f0d2ca6af12c
remotes              none
untracked            submission_5task_fallback.zip   (only untracked path)
Mercor diff          git diff --stat 5235aa7..HEAD  =  15 files, 3320 insertions, 0 deletions
Mercor diff scoped   git diff --name-status 5235aa7..HEAD -- candidates/ research/phase3/ jobs/ tools/ scripts/ report/ submission/
                     =  A  tools/bench/visible_vs_family.py     (one added file, nothing modified)
```

### Frozen checksums — every one recomputed during this audit

Command: `git ls-files <path> | xargs shasum -a 256 | shasum -a 256 | cut -c1-16`

```
candidates/02-renewal-risk-regression      f696367794c1a25f   MATCH
candidates/g05-sco-rollout-gate            77a6e432d9d2cba2   MATCH
candidates/g10-censored-demand             047195e7a12d34cd   MATCH
candidates/g24-recommender-ope             2c9cc2055ef796a5   MATCH
candidates/g34-fleet-reliability-gate      f14dd0c0dbcd763c   MATCH
candidates/p22-gauge-recalibration         a0570585c3927b53   MATCH
candidates/p20-noshow-monitoring           2c3c374b07f233fa   MATCH
candidates/p31-fill-rate-dispute           e18bf13d6080f987   MATCH
```

### Harbor task digests (prospective, from the preregistered plan)

```
p22  sha256:72fedb37da7b48c8488ad8afbcdf0d46b501dcdb52a6b05698a20370425629a7
p20  sha256:f033ea1f5a8876514566174e8a99cf36d24e09cd54e9bba7ddfb5c16ffe60d8a
p31  sha256:3208a6d39014bff924784636da9a0837d528833f22e0666197d445330821f3ae
```

### File hashes

```
research/phase3/analysis_plan.md   c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824
report/REPORT.md                   3085b6a33495948e8c88a46753b5838dbc58f1165fe1d472363222b11cc7f0b0
submission.zip                     c8561aad8300df6c832921fa5b86ea669def1cb04bbaba2e649e9919c5a9c760   8,471,008 bytes
submission_5task_fallback.zip      c8561aad8300df6c832921fa5b86ea669def1cb04bbaba2e649e9919c5a9c760   8,471,008 bytes  (identical)
```

The working-tree and in-archive copies of `report/REPORT.md` have the **same** sha256, which is how I established
that the archive embeds the uncorrected report.

### Five-task suite

```
tasks        Task02, G05, G10, G24, G34
trials       15 counted (3 per task) + 1 adjudicated invalid (g05-sco-rollout-gate__JnK5hsR)
successes    2 / 15 = 13.33 %
pass@3       1 / 5 = 20 %   (G34 only)
per-trial    hLbWzqK=1  UPCLpLx=0  SdvVPQN=1   (all other 12 trials = 0)
oracle       jobs/final-oracle-*        reward 1 x5
nop          jobs/final-nop-*           reward 0 x5
check        default rubric 11/11 x5; tb3-check-* reward 1 x5 with 5-10 of 35 criteria failing each
mutations    task02 21/21 · g05 38/38 · g10 33/33 · g24 30/30 · g34 21/21 (raw artifact lost)
```

### Prospective experiment

```
plan         research/phase3/analysis_plan.md, sha256 c590cb56..., ONE commit ever (aeddc1c)
tasks        P22, P20, P31, frozen and tagged
model        google/gemini-3-flash-preview via gemini-cli, Harbor 0.21.0, one family only
trials       9 VALID, 0 invalid, 0 replacements; all digest_matches_freeze = true
db digests   9/9 MATCH the frozen extracts (collected_db_digests.txt)
results      0/9 successes; pass@3 = 0/3; per task 0/3, 0/3, 0/3
criteria     evidence_reconstruction 8/9 · scientific_object 8/9 · identification 4/9
             estimator_implementation 8/9 · quantitative_results 2/9
             independent_validation 8/9 · decision 2/9
cost         $1.4667 total ($0.0068 - $0.2725 per trial); $10 stop threshold NOT reached
verdicts     P1 DISCONFIRMED (1/9 = 11 % attempted no L3 route; 8 of 9 did attempt one)
             P2 NOT EVALUABLE (0 successes)
             P3 56 % vs >=60 % predicted - just below
             P4 89 % - above threshold
             P5 22 % - inside the 20-50 % band
             P6 DISCONFIRMED (8 of 8 applicable trials revised)
             P7 predicted direction NOT observed (0 wrong verdicts were incumbent_incorrect)
mutations    P22 15/15 · P20 15/15 · P31 15/15
harbor check NONE on any of the three
```

### Measured-population reconciliation (source of contradiction C3)

```
report/data/results.json  pilot_summary : 12 tasks, 36 trials, 18 successes, 8 with pass@3
                          final_summary : 5 tasks, 15 trials, 2 successes, 1 with pass@3
                          costs         : gemini_all_runs $6.5351 · g36 $0.3554
                                          task02 ablation $0.7474 · harbor_check $14.4273
AUDIT_2026-09-23.md  §2   : 15 measured tasks, 45 valid trials
                            = the 12 above + G41 + G42 + G44 (built after the 2026-09-22 packaging)
full jobs/ census         : 20 task identities with >=1 Gemini solver trial; 64 such trials total
```

### Key paths

```
research/audit/AUDIT_2026-09-23.md                          authoritative failure analysis (supersedes REPORT §5-6)
research/audit/abundant_requirements.md                     18-item requirement audit + the missing-assignment caveat
research/phase3/analysis_plan.md                            THE PREREGISTRATION - do not modify
research/phase3/HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md   prospective results, 32 sections
research/phase3/exposure/                                   adjudications, cost ledger, db digests, first-pass results
research/phase3/comparison_with_five.md                     what P22/P20/P31 add over the five
report/REPORT.md                                            the write-up - NEEDS the seven corrections
report/VALIDATION.md                                        only place the TB3 criterion failures are disclosed
report/data/results.json                                    correct on G34 where final_tasks.json is not
scripts/final_tasks.json                                    G34 reward pairing is WRONG (C1)
scripts/frozen_checksums.txt                                the five dirhashes - all verified
research/mercor_apex/                                       Mercor only - not Abundant evidence
```

---

## Explicit confirmations

- **No model run performed in this audit.** No Harbor job, no Gemini call, no API request of any kind. Every
  number was read from files already on disk or recomputed with `git`, `shasum`, `unzip -l`, `diff` and `python3`.
- **No benchmark task changed.** `git status` shows no modification under `candidates/`; all eight frozen
  dirhashes recompute to their recorded values.
- **No verifier, tolerance or hidden extract changed.** Nothing under any task's `tests/` or generator was
  written to.
- **No prospective result changed.** `research/phase3/` and `jobs/` are untouched; `analysis_plan.md` still has
  exactly one commit in its history.
- **No submission archive overwritten.** Both zips retain sha256 `c8561aad8300df6c832921fa5b86ea669def1cb04bbaba2e649e9919c5a9c760`.
  The archive was read with `unzip -l` and extracted to a temporary directory that was then deleted.
- **No git history rewritten.** No commit, amend, rebase, tag or branch operation was performed. This audit made
  no commit at all.
- **Nothing pushed.** The repository has no remote configured.
- **Nothing submitted.**
