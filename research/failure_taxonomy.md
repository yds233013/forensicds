# ForensicDS failure taxonomy

Used to label every trajectory that does not earn reward (and to sanity-check those that do).
Assign the **earliest** stage at which the trajectory went irrecoverably wrong as the primary
label; secondary labels are allowed. Cite trajectory step numbers as evidence.

| Code | Name | Operational definition | Typical trajectory evidence |
|------|------|------------------------|-----------------------------|
| F0 | Failed to inspect relevant evidence | Never opened the system of record or the code/data needed to reason about the symptom; acted on assumptions. | No queries against billing data; no read of the pipeline stage that produces the affected metric; edits made before any reconciliation. |
| F1 | Incorrect initial hypothesis (committed) | Adopted a plausible but wrong cause and never falsified it. | Changes FX logic, reverts the recent deploy, edits pricing/credit handling, blames territory realignment; no evidence checked against the hypothesis. |
| F2 | Insufficient reconciliation / localization | Recomputed or compared totals but did not narrow by period, entity or stage. | Compares only the August total; never compares per billing account / per row; cannot say which rows are excess. |
| F3 | Found suspicious symptom, not root cause | Localized the symptom (e.g. duplicated rows, specific accounts) but did not identify the violated semantic relationship or why it changed. | Notes "duplicates in fct" or lists the affected accounts, but never reads the identity/migration semantics or the CRM grain. |
| F4 | Found root cause, incorrect repair | Correctly articulates the cause but the implemented change is semantically wrong or incomplete. | States that staged migrations make the join one-to-many, but e.g. keeps as-of CRM join and follows only one successor hop, ignores scheduled status, or picks the legacy account for history. |
| F5 | Symptom patch instead of causal repair | Makes the headline number match without fixing the relationship. | `drop_duplicates`, filtering migrated/legacy rows, hard-coded account ids, month-specific branches, scaling factors, editing outputs or source data. |
| F6 | Collateral data loss / regression | Repair removes or distorts legitimate data or breaks other behaviour. | Drops identical legitimate invoice lines, removes revenue of migrated customers, breaks other months, changes schema, pipeline no longer runs on other snapshots. |
| F7 | Correct repair, insufficient validation | The core change is right but the agent did not validate enough to catch a residual defect or left outputs stale. | Fix correct in code but outputs not regenerated; checked only August; did not check account-level restatement; tiny residual bug that simple invariant checks would reveal. |
| F8 | Verifier / task-design issue | The failure is attributable to the task, not the model. | Instruction ambiguity, doc contradiction, environment/tooling failure, verifier rejecting a defensible solution, timeouts caused by infrastructure. **Triggers a task revision.** |

## Labelling procedure

1. Read the verifier output (`verifier/ctrf.json`, `test-stdout.txt`) to see which invariants failed.
2. Read the trajectory end-to-end; mark the first step where the agent (a) reconciles against
   billing, (b) localizes to accounts/rows, (c) opens `revrec/accounts.py`, (d) reads the identity
   standard / migration register / CRM grain, (e) states a root cause, (f) edits code.
3. Assign the primary label from the earliest failing stage; add secondary labels.
4. For any reward = 1 trajectory, run the `reward_hacking` check (edits to tests, reads of
   `/solution`, writes to `/logs/verifier`).
5. Record in `samples/<task>/<trial>/label.json`:
   `{"trial": ..., "reward": ..., "primary": "F3", "secondary": ["F7"], "evidence_steps": [..], "notes": "..."}`.

## Task 01 mapping of verifier failures to likely labels

| Failing invariants (test names) | Most likely label |
|---------------------------------|-------------------|
| everything except integrity/idempotence/non-migrated (same as Nop) | F0/F1/F2 (no effective change) |
| `test_*_unmodified` | F5 (source data edited) |
| grain + monthly totals, attribution OK | F6 (rows lost) or F4 |
| attribution / migrated account / account reports only (visible) | F4 (history not restated, single hop, scheduled followed) or F5 (dedupe) |
| hidden snapshots only | F5 (overfitted: ids, months, constants) or F4 (as-of join retained) |
| identical invoice lines | F6 (content-based dedupe) |
| pipeline runs / dashboard extracts | F6 (interface broken) or F7 (outputs not regenerated) |
