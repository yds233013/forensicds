# 02 — Complete project history

Reconstructed from `git log` (106 commits, `20896fc` … `7e6d4d7`), from dated handoff documents, and from
job artifacts. **Commits are VERIFIED FROM ARTIFACT.** Work after 2026-09-25 was never committed, so its
chronology comes from file timestamps and from `OVERNIGHT_FINAL10_PROGRESS.md` (append-only) — labelled
**REPORTED** where no commit backs it. Nothing here is invented; gaps are stated as gaps.

## Phase 0 — scaffolding (2026-09-12)

`20896fc` *Project scaffolding and research framing for ForensicDS*. The working name is ForensicDS;
earlier correspondence also uses "CERL". **UNKNOWN:** no artifact in this repository documents a CERL
phase preceding `20896fc`, so if one existed it lived elsewhere. The history below therefore begins at
2026-09-12.

## Phase 1 — generation 1, tasks 01-06 (2026-09-12 → 09-13)

A fast six-task sprint, each following the same arc: design → environment+generator → Harbor definition →
verifier → oracle → dev tooling and mutation suite → validation → Gemini baseline.

| task | built | validation commit | Gemini baseline |
|---|---|---|---|
| `01-revenue-reconciliation` | `9f36052`…`5486c5a` | `a6a884e` Oracle 1, Nop 0, 28/28 mutations | `ea1ce40` |
| `02-renewal-risk-regression` | `7348129`…`a8c1ae5` | `0f9a21c` Oracle 1, Nop 0, 21/21 mutations, harbor check 11/11 | `46ae439` |
| `02…__explicit-invariant` | `31ea5ee` | — | `f4f440a` (paired ablation) |
| `03-lead-score-evaluation` | `f77c099`…`46b1b77` | — | `e893b1d` |
| `04-retention-metrics-regression` | `c5835f9` | — | `e893b1d` |
| `05-onboarding-experiment-readout` | `7e6d746` | — | `e893b1d` |
| `06-usage-statement-close` | `10746ea` | — | `b2fc98b` **3/3 — "too easy"** |

**The first hypothesis revision happens here.** `b2fc98b` and `e893b1d` record that several generation-1
tasks were solved 3/3 by the target model. The project's framing document (`4ba24ca`, *Benchmark docs:
hypothesis, distribution matrix, cross-task review, taxonomy*) is written in the same window. The
conclusion drawn — visible in the subsequent design tournaments — is that *plausible-looking data-science
incidents are not automatically hard*, and that difficulty had to be engineered from the scientific
structure rather than from surface messiness.

## Phase 2 — generation 2 and 3 design tournaments (2026-09-13)

`599d996` builds a 30-candidate pool with hardness scoring and a top-15 selection; `d256f8a` details the
top 15; `06ad14a` runs a design tournament with simulations and shortlists 8 for implementation. This is
the project's deliberate move from "write another task" to "select from a scored pool".

## Phase 3 — generation-3 builds, G08 → G24 (2026-09-14 → 09-17)

| task | build | baseline | recorded verdict |
|---|---|---|---|
| `g08-forecast-accuracy-vintages` | `e07103d` | `cbd8a68` | **1/3, pass@3 1, "medium-hard"** |
| `g10-censored-demand` | `3efed5c` (research `b9f48b1`) | `87b7ba7` | **0/3, "frontier-hard"** |
| `g24-recommender-ope` | `2e21788` (audit `84726dc`) | `c79d788` | **0/3, "hard, near-miss"** |
| `g05-sco-rollout-gate` | `a13a1a3` (6 calibration rounds), mutations 38/38 `2fc7e5e` | later | — |

Note `b9f48b1`: *"estimand-first design"*. By G10 the method had inverted — define the business estimand
first, then build a world in which the plausible analysis answers a different question.

## Phase 4 — the attrition period, G34 → G44 (2026-09-21 → 09-22)

This is the most informative stretch for understanding the final ten, because most of it is rejection.

| id | outcome | commit |
|---|---|---|
| `g36-tou-capacity-gate` | v1.1 **abandoned** (development-only) after a forecast-only counterexample search; v1 closed as development-only | `063330c`, `30026c6` |
| `g37` | **DROP** (research only) — measurement-system change | `81ed909` |
| `g38` | **DROP** (research only) | `dcb0445` |
| `g39` | **SEARCH AGAIN** — structural-object tournament, research only | `b2d6401` |
| `g40` | **dropped at stage 2** in "deadline mode" | `35239d6` |
| `g41-service-parts-rebalancing` | built, frozen `3f31849e44d9e392`, baseline **1/3** | `cbb682b`, `b9f9311`, `ee16d72` |
| `g42-contractor-safety-rate` | built, frozen `4b4ded75469d229a`, baseline **3/3 development-only** | `ee16d72`, `6972157`, `cdb08a7` |
| `g43` | **rejected pre-build on principle 17** | `88784ff` |
| `g44-screening-precision` | built, frozen `e688a53ec78348cb`, "solved on its object 3/3" | `e1fe21c`, `bc28cc7`, `8b24e99` |

`dcb0445` records a *failure meta-analysis* and design principles 15-16; `cdb08a7` adds 17-18; `8b24e99`
adds 19. **INFERENCE:** the numbered design principles were the mechanism by which rejections were turned
into reusable constraints. Their full text is in the research directory, not reproduced here.

## Phase 5 — the five-task submission (2026-09-22)

`156b612` *Final validation: Oracle=1/Nop=0 re-run on all five final tasks; identity via Harbor TrialLock
digest*, then `e44c937` *Submission ready: TB3 rubric checks, supporting evidence, final audit PASS*.
`submission_5task_fallback.zip` (`c8561aad8300df6c…`) is this artifact and has been **untouched since**.

`d78f6da` and `9e09ba5` are worth noting as process hygiene: the audit script was changed to refuse to run
while a Harbor job was still writing into `jobs/`.

## Phase 6 — prospective tasks P22, P20, P31 (2026-09-23 → 09-24)

`568a201` adds all three **with criterion-level grading** — the first tasks in the project to emit
per-criterion rewards, which is why the entire criterion-level analysis in this dossier rests on them plus
`g50`. `aeddc1c` freezes them. `5337221` records a pre-exposure record; `57e2252` records
**9 valid trials across P22/P20/P31**; `5235aa7` is a 32-section prospective-results handoff.

This phase is where the project's hypothesis became testable at the capability level rather than only at
the pass/fail level.

## Phase 7 — interlude (2026-09-25)

`516dbc1` and `7e6d4d7` add an unrelated Mercor APEX fellowship proposal. **This is the last commit.**
Everything after is uncommitted.

## Phase 8 — the final ten and G50 (2026-09-28 → 09-30, UNCOMMITTED)

**REPORTED, from dated handoffs and the progress log.**

- `HANDOFF_2026-09-28_ABUNDANT_RESUME.md`, `HANDOFF_2026-09-28_FORENSICDS_FINAL10_DESIGN.md` — the
  final-ten design phase resumes.
- `HANDOFF_G50_PREEXPOSURE.md`, `…_V2_SCIENTIFIC_SPEC.md`, `…_FINAL_PRETARGET_VALIDATION.md`,
  `…_V21_FINAL_PRETARGET.md` (2026-09-29 → 09-30) — G50 is built and validated to destruction across four
  handoffs. Its documented history includes: a withdrawn R2 estimator, a scientific-spec window
  inconsistency, a latent-versus-recorded lateness verifier bug found by the oracle failing, a contract
  ambiguity in `boost_share`, the break-even-not-binding defect (D3) fixed by a fifth world, and the
  `ld.so.cache` refusal (D4) found by the first real agent run.
- `OVERNIGHT_FINAL10_PROGRESS.md` (append-only, 10 entries) — the final-ten assembly, the `p20` sign
  defect (D1), the `02` image-layer leak (D2).
- `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md` (2026-09-30) — the submission handoff.
- `submission_final10.zip` built and hashed; `SUBMISSION_SHA256.txt` records
  `629476cd886bd16eeb206e952c26be41370f9f79b149fa21cda0ecdf7779af7e`. **RERUN: verified this session.**

## Phase 9 — the Claude cross-model experiment (2026-09-30 → 10-01, UNCOMMITTED)

`CLAUDE_CROSSMODEL_EVAL.md` (09-30) pre-registers the experiment **before any Claude trial existed** —
including the coding rules — then records a hard stop: the only available Anthropic credential was the one
that had been printed in plaintext in a working transcript, and it had not been rotated.

`CLAUDE_VS_GEMINI.md` (10-01) records the executed run after rotation: 10 valid trials, then credit
exhaustion (`billing_error`), then a resumed run to 27 valid trials across 9 tasks, with `g50` unmeasurable
(D5).

## How the hypotheses changed, in order

1. **Initial framing (09-12/09-13).** Realistic data-science incidents will be hard for agents.
   → **Disconfirmed within two days**: tasks 03, 05, 06 scored 3/3.
2. **Second framing (09-13 onward).** Difficulty must come from the *scientific structure* — the incumbent
   analysis must be a correct computation of the wrong quantity. → Survives; it is the design rule of
   every final task.
3. **Third framing (09-14, `b9f48b1`).** Estimand-first design: define the decision quantity, then build a
   world where the plausible route answers something else. → Survives.
4. **Fourth framing (09-23, `568a201`).** Pass/fail cannot locate a capability gap; criterion-level
   rewards are needed. → Survives, and is the reason this dossier can say anything mechanistic at all.
5. **Fifth framing (09-30/10-01).** The gap is a frontier-agent capability gap.
   → **Substantially weakened** by the Claude arm: 5 of 9 tasks fell to one frontier model (chapter 10).

## Defects, fixes and freezes, consolidated

See `09_BENCHMARK_INTEGRITY.md`. Summary: 7 audited entries, of which 4 were found by this project's own
audits, 1 by the first real agent run, 1 by a cross-model run, and 1 was a false alarm in an integrity
script. Two required version forks (`p20`→v1.1, `02`→v1.1); one was fixed pre-exposure (`g50` `hidden_d`);
one remains unresolved (`g50` × `claude-code`).

## What this history does not contain

- **UNKNOWN:** any CERL-era work preceding `20896fc`.
- **UNKNOWN:** the per-candidate reasoning for most generation-3 rejections beyond the commit subjects;
  the detail lives in `research/` which this chapter cites rather than reproduces.
- **UNKNOWN:** exact wall-clock dates for Phase 8-9 steps beyond file mtimes, because that work was never
  committed. This is a real gap in the record and the progress log is the only ordering evidence.
