# 00 — Reader's guide

This dossier documents a benchmark of ten data-science tasks and two experiments run against it. It
assumes **no background** in statistics, machine learning, AI agents, Harbor or reinforcement learning.
Every technical term is defined where it first appears.

## What the project is, in one paragraph

We built ten realistic work assignments for a company data scientist. Each one hands an AI system a
business problem, the messy operational data behind it, and — crucially — **an analysis someone else
already did that looks right and is wrong**. The AI has to notice, work out what is actually going on, and
make a business decision. Then we measured how often two different AI systems got it right. They mostly
did not, and *where* they failed turned out to be more interesting than *how often*.

## The vocabulary you need

| term | plain meaning |
|---|---|
| **agent** | an AI system that can take actions — read files, run code, write files — not just produce text |
| **scaffold** | the program wrapping the AI that decides which actions it can take. Two were used: `gemini-cli` and `claude-code`. The scaffold is *not* the AI model |
| **Harbor** | the framework that builds each task, runs an agent inside it, then grades the result |
| **task** | one complete assignment: a business memo, a data warehouse, an inherited analysis, and a grader |
| **verifier** | the grading program. It runs after the agent finishes and decides pass or fail |
| **reward** | 1 for pass, 0 for fail |
| **criteria** | optional sub-scores that say *which part* of the work was wrong. Only 4 of our 10 tasks have them, and that limitation runs through the whole dossier |
| **oracle** | a stand-in "agent" that just runs the known-correct answer. Proves a task is solvable |
| **nop** | an agent that does nothing. Proves the task isn't already solved when it arrives |
| **hidden / sibling world** | a second, third, fourth version of the same company with different seeds *and a different underlying cause*. The agent never sees these; the grader checks its work against all of them |
| **trial** | one attempt by one agent at one task |
| **valid / invalid trial** | valid = the agent ran and the grader graded it. Invalid = something broke (no credit, a crashed grader). **Invalid attempts are never counted as AI failures** |
| **pass@3** | did *any* of three attempts succeed? A coarse measure |
| **trial pass rate** | passing attempts ÷ all valid attempts. A different, finer measure |
| **estimand** | the precise quantity a decision actually needs. The heart of the project: the inherited analyses compute a number correctly, but it is **not this quantity** |

### One worked example of the core idea

In the task `g50`, a delivery company tested a courier bonus. They randomly gave the bonus to some
individual orders and not others, and measured 4 points fewer late deliveries on bonused orders. The
analysis is done correctly.

But a bonused order jumps the queue ahead of an unbonused one, and **the same couriers deliver both**. So
the measured gain is mostly one order winning at another order's expense. Turn the bonus on for everyone
and there is no queue position left to win — the benefit largely evaporates.

The company's decision needs *"what happens if we give everyone the bonus?"* The experiment answers
*"is it better to be bonused than not, while others are not?"* **Both numbers are correctly computed. Only
one answers the question.** Spotting that difference, and computing the right number instead, is what the
task tests. All three Gemini attempts reported the wrong one and recommended the expensive rollout.

## Chronological history

| when | what | evidence |
|---|---|---|
| **2026-09-12** | Project starts (`20896fc`). Six tasks built fast | git |
| **2026-09-13** | Three of those six are solved 3/3 — "too easy". **First hypothesis revision:** realistic-looking is not the same as hard | `b2fc98b` |
| **2026-09-13** | Switch to scored candidate pools and design tournaments (30 candidates → 15 → 8) | `599d996`, `06ad14a` |
| **2026-09-14→17** | Generation 3: `g08` (1/3), `g10` (0/3), `g24` (0/3), `g05`. **"Estimand-first design"** appears | `b9f48b1` |
| **2026-09-21→22** | Attrition: `g37`, `g38`, `g39`, `g40` dropped; `g43` rejected before any code; `g41`, `g42`, `g44` built but too easy or unstable | `81ed909`…`8b24e99` |
| **2026-09-22** | A **five-task** submission is finalised and frozen | `e44c937` |
| **2026-09-23→24** | `p22`, `p20`, `p31` built **with per-criterion grading** — the first tasks that can say *where* an analysis broke | `568a201` |
| **2026-09-28→30** | Final-ten assembly; `g50` built and validated across four dedicated handoffs; two self-found defects fixed in forks | handoffs, progress log |
| **2026-09-30** | Gemini results: 1 pass in 31 valid trials | `jobs/` |
| **2026-09-30→10-01** | Claude cross-model experiment: blocked on an unrotated credential, then run; 13 passes in 27 valid trials on 9 tasks | `crossmodel_logs/` |

Full detail with commits: `02_COMPLETE_PROJECT_HISTORY.md`.

## The three results worth knowing before you read anything else

1. **Difficulty is not the result.** Gemini 3 Flash passed 1 of 31 attempts. Claude Opus 5.5 passed 13 of
   27 and solved 5 of the 9 tasks it was graded on. **The benchmark's headroom claim holds for one model
   and fails for the other.**
2. **Where failures sit is the result.** On the four tasks that record sub-scores, agents reconstruct the
   evidence and frame the right question at near-ceiling rates, and the **decision-relevant number** is the
   floor. But there are **at least four distinguishable failure shapes**, not one — including two that are
   mirror images. A single explanation does not fit.
3. **We found four defects in our own benchmark**, one of which this dossier discovered: both arms' `p20`
   numbers are partly contaminated by an unstated sign convention. All are in chapter 09.

## Table of contents

**Start here** → `13_EXECUTIVE_SUMMARY.md` (2-4 pages)

### Orientation
- `00_READER_GUIDE.md` — this file
- `01_ASSIGNMENT_AND_SLICE.md` — what was asked, what we chose, and **why the original brief is not in the repository**
- `02_COMPLETE_PROJECT_HISTORY.md` — chronology from 106 commits
- `03_COMPLETE_TASK_INVENTORY.md` — all 24 task directories, 5 never-built candidates, every rejection reason

### How it works
- `04_ARCHITECTURE.md` — Harbor, Docker, verifiers, sandbox defences, with real code and line numbers
- `TASK_DEPENDENCY_MAPS.md` — what an analyst must discover, in order, per task
- `tasks/` — **one chapter per final task** (`tasks/INDEX.md`)

### Results
- `05_GEMINI_RESULTS.md`, `06_CLAUDE_RESULTS.md` — recomputed from raw reward files
- `10_CROSS_MODEL_COMPARISON.md` — the nine jointly graded tasks
- `07_SIDE_BY_SIDE_CASE_STUDIES.md` — paired attempts on the same task
- `trajectories/` — **one case study per valid trial, 58 of them** (`trajectories/INDEX.md`)
- `INFRASTRUCTURE_FAILURE_REGISTER.md` — the 45 attempts that were not graded

### Analysis
- `08_FAILURE_MODE_AUDIT.md` — the scientific core: does one failure mode explain the evidence?
- `09_BENCHMARK_INTEGRITY.md` — every defect, and which checks I reran myself
- `11_RESEARCH_AND_TRAINING_PLAN.md` — why this matters, and 10 → 1,000
- `12_NEXT_EXPERIMENTS.md` — prioritised, costed, with the smallest high-value experiment named

### Machine-readable and audit
- `MACHINE_READABLE_INVENTORY.csv`, `ALL_TRIALS.csv`, `CRITERION_RESULTS.csv`
- `EVIDENCE_INDEX.md`, `OPEN_QUESTIONS.md`, `REVIEW_CHECKLIST.md`

## How to read the evidence labels

Every substantive claim carries one:

- **VERIFIED FROM ARTIFACT** — I read the file or recomputed the number in this session
- **RERUN** — I independently re-executed a check a prior report had made
- **REPORTED BUT NOT REVERIFIED** — a prior report states it; I could not re-execute it (usually because
  Docker was unavailable)
- **INFERENCE** — my reading of the evidence, not a measurement
- **UNKNOWN** — the artifacts do not answer it, and I say so instead of guessing

If a claim has no label, treat it as descriptive scaffolding, not a finding.
