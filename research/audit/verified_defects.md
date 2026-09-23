# Audit 2026-09-23 — defects verified directly against the repository

## D1. Task02 **explicit-invariant variant** has a contradicted instruction (F8). NOT in the final suite.

The variant differs from the base task by exactly one added paragraph:

> "…A source record or field value may be used only if it had landed in the warehouse before 00:00 UTC
> on that prediction date; warehouse availability is determined by `synced_at`, not merely the
> source-system change time."

But the graded reference does not apply that rule to support tickets —
`candidates/02-renewal-risk-regression/tests/reference.py:73`:

```sql
SELECT account_id, opened_at, severity, closed_at FROM support_tickets
```

`synced_at` is not even selected. And `docs/feature_dictionary.md` defines those features by event time
only: "`tickets_90d` | tickets opened before `P` and at most 90 days before `P`".

Consequence in the runs: **3/3 variant trials added a `synced_at` filter to `support.py`; 0/3 base trials
did**, and all three variant trials then failed `test_contract_usage_support_features` with the same
columns and the same off-by-one-in-one-direction signature. Trial `j5oNxeF` passes 15 of 19 checks —
including CRM point-in-time, Customer Success point-in-time, model specification and all three hidden
evaluations, with AUC 0.7826 against a reference 0.7806 — and loses the reward solely on that
instruction-induced edit.

**Status: the variant's 0/3 is not interpretable as a model failure and must not be compared with the
base task's 0/3.** The base Task02 (the one in the final suite) is unaffected: its instruction contains
no such paragraph and its three failures are independent reconstruction defects (below).

## D2. Base Task02's failures bind on the object, not on a metric tolerance

Assertion counts per trial (`grep -c` on the verifier stdout):

| trial | point-in-time feature-value failures | metric-gate failures |
|---|---|---|
| JctTpSi | 10 | 8 |
| nXXMdDm | 8 | 10 |
| pf9zaPc | 10 | 10 |
| 6LSZCFK (variant) | 10 | 3 |
| 95Q6LAG (variant) | 12 | 9 |
| j5oNxeF (variant) | 8 | 0 |

Every trial fails the feature-value reconstruction itself. The ROC-AUC / rank-correlation gates are
never the only binding constraint — in `j5oNxeF` they never fire at all. The two near-threshold rank
correlations (0.9773, 0.9798 against 0.98) therefore do **not** explain any failure.

## D3. The report's F10 claim for G05 is imprecise

Report §5 says "G05: 2/3, 'stop' was correct". Extract-level record (a `'decision': None` entry in the
verifier payload means the decision check passed on that extract):

- MMGNYFS: decision wrong on the visible extract (`continue`, expected `stop`); correct on the three hidden.
- PYhR2eh: correct on all four.
- rsDKTXQ: decision wrong on one hidden extract (`stop`, expected `continue`); correct on the other three.

Only **one** of three G05 trials is decision-correct on every graded extract; 10 of 12 extract-level
decisions are right. The claim should be restated at extract level.

## D4. G36's "0/3" is misleading as a statement about model behaviour

G36 is excluded from every aggregate and stays excluded. But the record should describe what happened.
The frozen grader computed the estate response as the **household-share-weighted** mean of per-segment
fractional responses, while the contract the agent reads asks for the estate-wide fractional reduction
in **load**. Because segment baselines and segment responses covary in the generator, the two
definitions differ by a stable **+23 %** on every fixture.

Consequence: trials `gtUvxU3` and `gZDvdHD` failed **only** `estate_tou_response_at_target_cdd`, and
only on two of four hidden fixtures; `target_peak_kw` and `procurement_decision` passed everywhere.
Under the corrected estimand both are within 0.02–0.30× tolerance on every fixture. Only `9ireeNt`
failed for a genuine modelling reason (it transported a constant absolute kW reduction beyond the
pilot's CDD range, and inverted the hidden_c decision).

**Honest statement: G36 was 0/3 as graded and would have been 2/3 under a correct grader; one of the
three failures is a real model failure.** Reporting it as "0/3, contaminated" without that annotation
overstates the benchmark's difficulty evidence in the project's own favour.

## D5. How detectable was the G36 verifier defect from trajectories alone? Not at all.

No trial showed confusion about the graded quantity. All three derived a load-ratio form in one or two
lines and moved on; two emitted the same value to fifteen significant figures. The detectable signature
was in the **verifier output**, not the reasoning: a *constant multiplicative offset* (ratios clustered
at 1.232 and 1.259), confined to one field, with the headline quantity and the decision correct on every
fixture.

**Rule for future audits: a near-miss that is a constant ratio across fixtures, concentrated in one
graded field, with the decision correct, is a task-definition signature — audit the contract before
writing a model post-mortem.**
