# What these three add to the existing five

The shipped suite is Task02 (point-in-time feature reconstruction), G05 (staggered adoption), G10 (informative
censoring), G24 (off-policy evaluation) and G34 (competing risks), plus G08 and G41.

## Scientific additions

| axis | the existing five | P22 | P20 | P31 |
|---|---|---|---|---|
| mechanism | temporal state · staggered adoption · censoring · logging policy · competing risks | **measurement-system change** with a physical bridge | **policy feedback on the evaluation population** | **two metrics under one name, adjudicated by a contract** |
| what must be derived | an estimand or an operational state | the **reference** a pass/fail decision is made against | the **population** a metric is defined on | the **instrument** that governs, and whether it settles the question |
| published number | wrong in all five | wrong | wrong | **right on two of four extracts** |
| abstention | not scoreable anywhere | no | no | **yes, and correct on one extract** |
| decision vocabulary | binary | binary | **four-valued, with an ordering rule** | **three three-valued adjudications** |
| criterion-level grading | binary reward only | **7 criteria** | **7 criteria** | **7 criteria** |
| method difficulty | mostly statistical | deliberately **elementary** statistics, hard identification | standard MLOps tooling reaches the wrong answer | arithmetic is trivial; the instrument is the difficulty |

## The two structural gaps these close

**DP3 — the wrong-but-authoritative artefact must not always be wrong.** All five shipped tasks begin with a
wrong published number, so an agent that always disagrees scores well without doing forensics. P31 is the
corrective: two of its four extracts have a correct published figure, and always-overturn is tested as a
mutation and scores 0.

**DP6 — abstention must be scoreable.** Nothing in the shipped suite admits "the evidence does not settle
this". P31's `not_determinable_from_available_evidence` is correct on exactly one extract, and always-defer is
tested as a mutation and scores 0.

## The phase-1 finding these are built to test

Phase 1's audit found that **6 of 13 failed trials reached the right business decision with wrong scientific
quantities**, and that on G24 a decision-only grader would have scored 3/3 instead of 0/3. All three tasks grade
the quantities beneath the decision as separate criteria, so that failure mode is now visible rather than hidden:
P22's M06 and P20's M12 both get the decision right on the visible extract and score 0, failing only
`quantitative_results`.

Phase 1 also found **zero falsification tests across 45 trials**. Each of these tasks ships two or three
discriminating routes whose outcome is recorded (`research/phase3/audits.md`), and P22's and P20's
`independent_validation` criteria require the answer to survive a check computed outside the agent's own frame.

## Difficulty, honestly stated

P22 is deliberately **elementary in method** — paired differences and a proportion — and hard only in
identification. That is by design: it separates the project's hypothesis from the rival explanation that failures
are textbook-knowledge gaps. P31's arithmetic is the simplest in the suite; its difficulty is entirely in reading
an instrument against a code path and in resisting a socially endorsed correction. P20 is the closest to the
existing five in technical weight.

None of the three reaches its difficulty through file volume: the workspaces hold 12, 12 and 11 artefacts
respectively, against ~25–31 for the phase-1 tasks.
