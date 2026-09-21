# ForensicDS benchmark hypothesis (Tasks 01–05)

Refines `hypothesis.md` now that five tasks exist. H1 below replaces the original H1 (localization bottleneck); the
change was made **after** seeing Task 01/02 trajectories and is labelled as such. Evidence status is stated for every claim.
Model evidence so far: `google/gemini-3-flash-preview` via gemini-cli, 3 trials on Task 01 and 3 + 3 on Task 02. Tasks
03–05 have no model trials.

## 1. Research question

Can frontier data agents **recover, operationalise, preserve and validate latent business or statistical
invariants** when repairing enterprise data failures whose symptom is a plausible-looking number and whose cause is
a semantic assumption that stopped holding?

"Latent invariant" = a property the correct pipeline must satisfy that is not stated as a test or located by an
error, but is implied by business documents, system behaviour and data: an entity grain (01), a time of
availability (02), an estimand's population (03), a KPI's population and state semantics (04), a randomization's
unit and arm (05).

## 2. Capability decomposition

Each task requires the chain below; tasks differ in which link is hardest.

| Stage | Question | Hardest in |
|-------|----------|------------|
| R — Recover | What property should hold, and which document or data behaviour defines it? | 02 (prediction point vs load time), 03 (what the score is for; who has an outcome unaffected by it), 05 (why a platform standard is invalid here) |
| O — Operationalise | Exactly which rows, at which grain, with which boundaries and tie rules? | 01 (canonical identity across hops), 03 (intake decision, ITT, boundaries), 05 (first assignment row, eligibility, maturity, reference time) |
| P — Preserve | Does the repair keep everything else (other periods, categories, schema, other consumers)? | 04 (bridge, reactivation, segments besides NRR), 01 (history, identical lines) |
| V — Validate | Did the agent check the invariant at the right grain rather than a headline number? | all; aggregates are insufficient by construction in every task |

## 3. Hypotheses

**H1 — Operationalisation, not recognition, is the main bottleneck for current agents.**
Agents often name the right cause but implement it incompletely or at the wrong grain.
*Evidence so far:* Task 02 diagnosis — all three Gemini trajectories identified the leak; failures were an incorrect
repair (F4 ×2) and insufficient validation (F7). Task 01 — two of three passed; the failure was a symptom patch (F5).
*n = 6 trials on 2 tasks: suggestive only.* Tasks 03–05 were designed so that recognition is achievable from
documents while operationalisation has several exact, testable details. Consequence: 03–05 can test the
operationalisation side of H1 but **cannot falsify its recognition side**; that needs localized-vs-diagnosis pairs
or tasks whose cause is not stated as a documented property.
*Test:* label trajectories with the failure taxonomy; H1 predicts F4/F7 ≥ F0–F3 among failures.

**H2 — Telling an agent the invariant does not by itself make it pass.**
*Evidence so far:* none that can be relied on. The Task 02 explicit-invariant ablation scored 0/3, but its wording
introduced a confound: one trial failed only because of the wording, and the other two also carried it as a
secondary cause. It shows that **disclosure wording can itself create failures**. It does not show that disclosure
fails to help.
*Test:* a corrected-wording rerun of Task 02 and localized conditions for 03–05, run with the same verifiers.

**H3 — Agents validate headline numbers, not invariants.**
*Evidence so far:* Task 02 trajectories validated with AUC plausibility and no feature-value audit; Task 01's
failing trial validated totals only. Tasks 03–05 make the headline number deliberately non-diagnostic: AUC is nearly
identical under intent-to-treat, per-protocol and latest routing (03); NRR can be correct with a wrong bridge (04);
several wrong unit definitions give "inconclusive" (05).
*Test:* the share of failing trajectories whose final validation uses only aggregates.

**H4 — Plausible platform or process "improvements" are accepted uncritically.**
Tasks 03 (a "more stable" wider population), 04 (a semantic-layer migration) and 05 (exposure-triggered analysis
as platform standard) each hide the defect in a change described as an improvement.
*Evidence so far:* none; no trials have been run on 03–05.
*Test:* whether trajectories question the CHANGELOG rationale, and whether they read the guidance that limits it
(e.g. counterfactual logging in 05).

**H5 — Distractor susceptibility is lower than expected for frontier agents; the pressure is on completeness.**
*Evidence so far:* Task 02 agents were not derailed by distractors (weak evidence, n = 3).
*Test:* F1 frequency and first-hypothesis analysis on 03–05.

## 4. What Task 02 taught, without overstating it

- A task can reach pass@3 = 0 with genuine failures (Task 02 diagnosis) when the repair has many exact parts
  (25 features, per-field point-in-time rules, three load behaviours). Difficulty came from breadth of
  operationalisation, not from hiding the cause.
- The ablation's validity problem is itself a design lesson. Disclosure text must use the task's own semantics
  precisely; otherwise it creates a new failure mode, and the comparison measures the wording, not disclosure.
- Nothing about the size of the disclosure effect can be concluded from 0/3 vs 0/3.

## 5. Design principles now enforced

1. The graded behaviour is documented in the workspace (harbor check `behavior_in_task_description`). It is stated
   as a property, not as the implementation.
2. No exact answer key in history for the graded values: past outputs use a slightly different but documented
   definition or snapshot (03 sales-led labels; 04 publication-date snapshot incl. very late renewals). Residual:
   03's 1.4.2 `n_leads` equals the correct cohort size for those months.
3. Each task has at least one tempting repair that matches the headline, and verifier checks at the graded grain.
4. Hidden extracts only vary mechanisms documented in the visible workspace (most also occur in the visible data;
   exceptions: 03 re-routed holdout leads and pauses, 05 `starter` plan). Each targets named
   overfits; every visible-pass/hidden-fail overfit is recorded with the fixture that catches it.
5. At least two independent correct implementations (a different language or paradigm) must pass.
6. An adversarial review happens before any model trial. Its findings are fixed and re-validated from scratch.
7. The verifier sandboxes the agent's pipeline (unprivileged uid, unreadable `/tests`, stripped env, fresh venv),
   and every mutation suite contains a reference-import cheat (03–05; 01/02 not yet hardened).

### Added after G36 closure (2026-09-21) — see `research/g36/G36_FINAL_STATUS.md`

8. **Independent Graded-Quantity Audit (IGQA).** Every independently graded scientific quantity needs
   (A) *semantic independence*: a derivation from the contract / business question that never reads the
   verifier implementation; and (B) *computational independence*: at least two implementations
   sharing no defining helper, unless the quantity is algebraically forced by another independently
   validated quantity. If the contract does not pin a weighting or aggregation, the quantity fails (A).
9. **Natural implementation path.** Before building or freezing, answer: "What is the smallest
   plausible edit a competent analyst would make to the provided scaffold?" The intended difficulty
   must survive that route. G36's selection transport did not.
10. **Counterexample search before freeze.** A wrong-method panel is insufficient. Actively search for
    plausible *wrong scientific models* that accidentally fall inside tolerance (G36: CE06).
11. **Identifiability before grading.** Do not grade an intermediate quantity only because it is
    meaningful. There must be a non-trivial window, max(valid error) < tolerance < min(important
    wrong error), with adequate margin. G36's 0.92 vs 0.99 SE_REF is not adequate.
12. **Fixture coverage.** For every wrong method, record how many fixtures reject it. Flag any task
    where one fixture rejects a large share of the important wrong methods without an explicit
    scientific reason.
13. **Decision / tolerance compatibility.** For every decision-bearing continuous quantity, check
    whether tolerance > |truth − decision threshold|. If so, an accepted estimate can imply the wrong
    business decision. This must be designed and adjudicated before freeze.
14. **Recognition and execution.** Giving the key insight for free must not hand over the estimator.
    Execution errors must also produce differences large enough for the data and verifier to
    distinguish.

## 6. Predictions to check when baselines are run (pre-registered here, 2026-09-13)

| Task | Expected dominant failure | Rationale |
|------|---------------------------|-----------|
| 03 | F4: per-protocol or worked-lead population; boundary/label details | "if worked" intuition; SDR queue ordering must be connected to selection |
| 04 | F4/F7: NRR fixed but reactivation or segments wrong | handbook read for the cohort, less for the bridge |
| 05 | F4: workspace-level but exposure-triggered, or latest assignment row | exposure data look like cleaner evidence; the first-row rule lives in platform docs |

These are hypotheses about the model, not results. The target stays pass@3 < 30% per task, with F8 = 0 after review.
