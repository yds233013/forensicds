# ForensicDS — Research hypothesis

## Research question

Can frontier AI agents diagnose and repair consequential enterprise data failures when the
visible symptom is known but the true root cause is distributed across data, code, business
semantics, configuration, and operational history?

## Framing

Most coding benchmarks hand the agent a located defect (a failing test, a stack trace, an
issue that names the component). Enterprise data incidents rarely look like that. The typical
report is a *business* symptom ("August revenue is 8% too high") produced by a pipeline that
runs cleanly, passes its own data-quality gates and throws no error. The defect is a *semantic*
mismatch — a grain, identity, lifecycle or policy assumption that was true when the code was
written and silently stopped being true after an operational change elsewhere in the company.

Solving such an incident requires a chain of distinct competencies:

1. **Reconciliation** — establish the discrepancy quantitatively against the system of record.
2. **Localization** — narrow it by period, entity and pipeline stage.
3. **Lineage tracing** — follow the affected rows through the transformations.
4. **Semantic diagnosis** — identify which assumption (grain, identity, policy) is violated and
   why it changed (operational history).
5. **Hypothesis elimination** — rule out real but non-causal events with evidence.
6. **Semantic repair** — change the relationship, not the symptom, without collateral damage.
7. **Validation** — check invariants beyond the headline number (other periods, entity-level
   figures, grain), and generalization to future data.

## Hypotheses

**H1 (localization bottleneck).** Frontier agents fail these tasks more often at steps 1–4
(finding and understanding the cause) than at step 6 (implementing the repair once the cause
is known).
*Test:* paired conditions on identical environments/verifiers — **A. Diagnosis** (business
symptom only) vs **B. Localized** (instruction names the faulty relationship). Prediction:
pass@3(B) − pass@3(A) is large (≥ 30 points), and A-failures concentrate in taxonomy classes
F0–F3.

**H2 (symptom patching).** When agents do localize the symptom (e.g. duplicated rows), a
substantial fraction repair the symptom (de-duplicate, filter, rescale) rather than the
semantic relationship.
*Test:* share of trajectories classified F5 among those that reach F3 or beyond; verifier
account-level and hidden-snapshot invariants distinguish symptom patches from causal repairs.

**H3 (headline-number validation).** Agents validate against the reported headline number and
under-validate secondary invariants (history, entity level, grain).
*Test:* frequency of F6/F7 — repairs that tie the August total but break per-account history,
drop legitimate identical lines, or fail on unseen snapshots.

**H4 (distractor susceptibility).** Real, temporally coincident but non-causal events (deploys,
price changes, FX moves, CRM realignments) attract initial hypotheses and consume budget; weaker
agents commit to them.
*Test:* F1 frequency and which distractor is named first in the trajectory.

## Design principles for tasks

- The instruction contains the business symptom and the desired outcome only.
- Exactly one defensible underlying issue; several plausible alternative hypotheses.
- All information required for the correct repair exists in the environment (docs, data,
  history). Difficulty comes from investigation, not missing information, trivia, scale or
  broken tooling.
- Verifiers test semantic invariants on the visible snapshot **and** on hidden, generated
  snapshots with novel patterns, so symptom patches and overfitted repairs fail.
- Every task is validated with Oracle = 1, Nop = 0 and a mutation suite of plausible shortcut
  repairs that must score 0, plus alternative correct implementations that must score 1.

## Evaluation plan

- Model: `google/gemini-3-flash-preview` via Harbor's `gemini-cli` agent.
- ≥ 3 trials per task per condition; report pass@1 (mean) and pass@3.
- Target curated set: 5–10 tasks with pass@3 < 30% in condition A.
- Every failed trajectory is labelled with the failure taxonomy (`failure_taxonomy.md`), and
  every passed trajectory is checked for reward hacking.
- F8 (task-design issue) findings feed back into task revisions before results are reported.

## Update after the Task 01 baseline (2026-09-13)

Task 01 (Gemini 3 Flash, 3 diagnosis trials: 2 pass, pass@3 = 1) did **not** support H1 as the main
bottleneck: all three agents localized the row-multiplication defect within about a minute. The passing
agents read a document that specified the repair procedure; the failing agent skipped it and applied a
dedupe patch (`research/task01_gemini_analysis.md`).

**Working hypothesis H5 (latent invariant).** Frontier data agents can often identify a visible technical
defect but may fail to infer and preserve the latent business or statistical invariant that determines
the correct repair, especially when several technically plausible fixes improve aggregate metrics.

Design consequences for subsequent tasks:
- no document states the repair procedure; invariants are stated at the level a real organization
  would (model card, data dictionary), not as algorithms;
- several wrong repairs must produce plausible aggregate metrics, so success requires validating the
  invariant itself;
- hidden fixtures change the surface on which the invariant is exercised (fields, schedules, calendars).

Task 02 (`research/task02_design.md`) tests H5 through temporal provenance of ML training features.
H1 remains open; the localized/diagnosis paired design is kept for tasks where localization is non-trivial.
