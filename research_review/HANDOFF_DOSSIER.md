# Dossier handoff

Built 2026-10-02 from `/Users/yashshah2311/forensicds` at HEAD `7e6d4d7`. No frozen task, verifier,
tolerance, dataset or scoring rule was modified. No paid model call was made. No secret appears in any
generated file (scanned).

## Chapter status

| chapter | status | basis |
|---|---|---|
| `00_READER_GUIDE.md` | **complete** | authored; chronology from git |
| `01_ASSIGNMENT_AND_SLICE.md` | **complete, with a caveat that matters** | the original brief is **not in the repository**; requirements are restatements |
| `02_COMPLETE_PROJECT_HISTORY.md` | **complete to 2026-09-25**, REPORTED thereafter | 106 commits verified; Phase 8-9 uncommitted |
| `03_COMPLETE_TASK_INVENTORY.md` | **complete** | 24 directories + 5 never-built candidates |
| `04_ARCHITECTURE.md` | **complete** | real file paths and line numbers |
| `tasks/` (10 + index) | **complete** | structure generated from artifacts; analysis authored |
| `TASK_DEPENDENCY_MAPS.md` | **complete** | 10 maps, depths 8-12, break points marked UNKNOWN where binary-reward |
| `05_GEMINI_RESULTS.md` | **complete** | recomputed from raw rewards |
| `06_CLAUDE_RESULTS.md` | **complete** | recomputed from raw rewards |
| `07_SIDE_BY_SIDE_CASE_STUDIES.md` | **complete** | 6 pairings, `g50` deliberately excluded |
| `trajectories/` (58 + index) | **complete on observable fields** | template-generated from raw JSON; not hand-narrated individually |
| `INFRASTRUCTURE_FAILURE_REGISTER.md` | **complete** | all 45 invalid attempts |
| `08_FAILURE_MODE_AUDIT.md` | **complete** | 24 instrumented trials, 11 shapes |
| `09_BENCHMARK_INTEGRITY.md` | **complete** | 7 defects; 5 checks reran, 3 could not |
| `10_CROSS_MODEL_COMPARISON.md` | **complete** | 9 jointly graded tasks |
| `11_RESEARCH_AND_TRAINING_PLAN.md` | **complete** | COMPLETED/PROPOSED labelled throughout |
| `12_NEXT_EXPERIMENTS.md` | **complete** | 6 experiments, costed where grounded |
| `13_EXECUTIVE_SUMMARY.md` | **complete** | — |
| CSVs, `EVIDENCE_INDEX`, `OPEN_QUESTIONS`, `REVIEW_CHECKLIST` | **complete** | — |

## Independently verified in this session

- All ten final tasks **byte-identical** to `submission_final10.zip` (fresh extraction, re-diffed).
- Archive hashes: final-ten `629476cd…` OK; fallback `c8561aad…` unchanged; `submission.zip` is a
  byte-identical copy of the fallback.
- Gemini **31 valid / 1 pass / 3.2% / pass@3 10%** — reproduces the prior report exactly.
- Claude **27 valid / 13 passes / 48.1% / pass@3 56%** over 9 measured tasks.
- 45 invalid attempts isolated; **none counted as a model failure**.
- Criterion instrumentation: exactly 5 directories, with file/line citations.
- 11 distinct criterion-failure shapes across 24 instrumented valid trials.
- Defect re-checks: D1 (sign convention absent in v1, present in v1.1), D2 (static), D3 (`hidden_d`
  present), D4 (`ld.so.cache` pin removed, resolution check in place), D7 (drift false alarm).

## Evidence that was missing

| missing | consequence |
|---|---|
| the original Abundant assignment text | every requirement is a restatement; two restatements disagree on task count |
| Docker daemon unavailable | D2 layer extraction, D3 strengthening and `g50`'s adversarial record are **REPORTED, NOT REVERIFIED**; the D5 diagnostic could not run |
| criterion data for 6 of 10 tasks | chapter 08 rests on 4 tasks / 24 trials — the dossier's largest limitation |
| Gemini per-trial cost | `gemini-cli` trajectories record no `total_cost_usd` |
| `out/` artifacts in several archived workspaces | produced numbers recoverable only from verifier notes; case studies say "not observable" |
| commits after 2026-09-25 | Phase 8-9 ordering rests on the progress log and file mtimes |
| any promotion record for `g36` | closed as development-only yet shipped; **UNKNOWN** |

## Corrections this dossier makes to the project's own record

1. **Both arms' `p20` quantity numbers are partly contaminated by defect D1.** 12 sign-flip field failures
   across Claude's three trials, 7 across Gemini's v1 trials, **0** in the fixed `p20-v1.1`. Claude was run
   on v1. No trial fails on sign alone, so `p20`'s 0/3 stands — but "the model could not compute the
   programme effect" is **not supportable**. **Not recorded anywhere previously.**
2. **`p31` already implements justified deferral.** `tests/world.py:300` returns
   `not_determinable_from_available_evidence`, and it is in the agent-visible contract
   (`readout_contract.md:42`). `report/FINAL_REPORT.md:982` and
   `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md:794` both state no such world exists. **They are wrong**, and
   both models failed to produce the deferral — an unrecognised result.
3. **`g50`'s Claude refusal is not the `ld.so.cache` defect recurring.** That fix is verifiably in place;
   a different pinned file is tripped and which one is **UNKNOWN**.
4. **`README.md:26` documents the superseded five-task suite.**
5. **My own first-pass instrumentation detection was wrong** (regex over `tests/`), and was corrected from
   observed trial evidence. Recorded in chapter 09 rather than silently fixed.

## Defects in the dossier build, found and fixed before completion

- **Duplicated trials:** the first case-study generation collided jobs holding multiple trials into one
  filename — 48 files for 58 trials. Slugs now include the trial id; 58/58 reconciled.
- **`p31-prospective-1` borderline:** 4 steps, 23,987 prompt tokens, 5 tool calls, no outputs. Counted
  valid (the agent ran) and flagged BORDERLINE with a stated sensitivity.

## The recommended next experiment

**Manual trajectory adjudication of the four jointly failed tasks** (`g10`, `g36`, `p20`, `p31`) — two
blind coders against a fixed stage codebook, with the four passing `g08` trials as positive controls.

- **Cost: $0 in model spend**, ~6-10 hours of analyst time.
- **Why it is first:** chapter 08 establishes that the decision-relevant quantity is the modal failure and
  explicitly declines to claim a shared cause, because two of the eleven failure shapes are mirror images.
  Adjudication is the only thing that resolves that, and no quantity of further trials will.
- **Pair it with** re-reading the six `p31` trajectories for deferral behaviour (also free), which
  converts finding 2 above into a measured result.

Second: a **controlled scaffolding intervention** (~$15) — Claude used 13-15 steps on `g36` where Gemini
used 40-54 and both failed, so premature stopping is the largest live threat to the validity of every
number here.

## One-line verdict

The benchmark is intact and the numbers reproduce. Its headroom claim holds for flash-tier Gemini and
**fails** for frontier Claude. The durable result is not difficulty but localisation: on the tasks that can
tell us, agents frame the problem correctly at near-ceiling rates and get the decision-relevant number
wrong most of the time — in **at least four distinguishable ways**, not one.
