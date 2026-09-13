# Task 05 — Onboarding experiment readout: unit, exposure and identity (design)

Harbor task: `candidates/05-onboarding-experiment-readout` (`forensicds/onboarding-experiment-readout-05`).
Validation: `report/task05_validation.md`. Status: pre-baseline; **no model trials run**.

## 1. Research question

Can an agent recover the *causal identification* of an experiment readout — which units were randomized, which
comparison the randomization licenses, and which logged data are post-treatment — when a platform-wide "improvement"
(exposure-triggered analysis) silently changes the unit and population, and can it re-implement the pre-registered
analysis exactly under messy assignment, exposure and identity data?

## 2. Enterprise setting

B2B SaaS product analytics. Experiment XP-231 tests an onboarding checklist for new workspaces. The experimentation
platform assigns workspaces at onboarding start (hash-based, stratum logged); the web SDK logs exposures from the
component that renders the experience; product events carry workspace context. Product Analytics' `xp_analysis`
package produces weekly readouts and the decision readout. A concurrent user-level pricing experiment (XP-240), an
assignment-cache incident (INC-5521), a dashboard performance release and a paid-social campaign all happen during
the test.

## 3. Visible symptom

Memo from the Head of Product Analytics: Growth wants to ship on the strength of a large significant lift that has
been positive every week; the readout logged a sample-ratio warning.

| Readout (2026-09-01) | Units control / treatment | Activation control / treatment | Effect | 95% CI | Decision | SRM p |
|----------------------|--------------------------:|-------------------------------:|-------:|--------|----------|------:|
| xp_analysis 3.1 (bug): exposed users | 5,164 / 3,285 | — | +6.9 pp | [+4.8, +9.0] | ship | 7e-93 |
| Pre-registered: as-assigned workspaces (oracle = reference) | 1,680 / 1,717 | ~8% | −0.3 pp | [−2.1, +1.6] | inconclusive | 0.53 |

Weekly bug readouts (logs/readout_runs.csv): +3.3 (3.0.0, inconclusive, no SRM field), +5.0, +6.3, +6.3, +7.0, +6.9 pp
("ship" from 2026-08-10). Numbers after the review changes (seed 5153, pre-assignment activity).

## 4. Hidden root cause

xp_analysis 3.0.0 (XPP-12) made readouts exposure-triggered: units are users with a logged exposure, in the logged
variant, with activation measured from first exposure. For XP-231 this is invalid because:

1. **Asymmetric trigger.** Control logs exposure on dashboard load; treatment logs when the checklist component
   mounts after a data fetch, which low-intent users often leave before. Exposed treatment users are selected on
   intent (the exposure is post-treatment and arm-dependent) → upward bias and SRM (8,904 vs 4,864 exposed users).
2. **Wrong unit.** Randomization is by workspace; users within a workspace are correlated and the primary metric is a
   workspace metric (≥3 active users). User-level units change the estimand and understate uncertainty.
3. **Identity.** The SDK caches a user's variant across workspaces (XPP-44), so exposure variants disagree with the
   workspace assignment for multi-workspace users (239 exposures in the visible extract).
4. **Reference time.** Activation is measured from first exposure instead of assignment.

## 5. Latent invariant

Analyze as randomized: unit = workspace; arm = variant of its first assignment row (later rows from SDK retries or
cache incidents do not change it); population = self-serve, non-internal workspaces with assigned_at + 14 days <= analysis date 00:00 UTC,
regardless of exposure; outcome = ≥3 distinct users with a core action in the workspace in
[assigned_at, assigned_at + 14 days); estimator = stratified difference in proportions (weights N_h/N, Neyman
variance, z = 1.96); decision rule from the plan. Exposure logs are never used to define units or arms.

## 6. Why this is real DS work

Triggered analysis, sample-ratio mismatch as a diagnostic, randomization-unit vs analysis-unit mismatches and
identity problems (users in multiple accounts, cached variants) are standard pitfalls in online controlled
experiments; practitioner literature on trustworthy online experiments discusses SRM checks, counterfactual logging
for triggered analysis, and cluster-randomized designs. (Sources to verify before publication, not re-checked in this
session: Kohavi, Tang & Xu, *Trustworthy Online Controlled Experiments*, Cambridge University Press, 2020; Fabijan et
al., "Diagnosing Sample Ratio Mismatch in Online Controlled Experiments", KDD 2019.)

## 7. Evidence graph

```
Memo: big significant lift, SRM warning, surprise
  ├─ reports/experiments + logs/readout_runs.csv: user counts 5,164 vs 3,285; SRM p < 1e-40 in every 3.1 run
  ├─ CHANGELOG 3.0.0 (exposure-triggered users) and 3.1.0 (SRM downgraded to warning)
  ├─ docs/experiments/XP-231_plan.md: unit workspace, analyzed as assigned, eligibility, 14d from assignment,
  │    stratified estimator, decision rule; Instrumentation: control logs on dashboard load, treatment on checklist mount
  ├─ docs/platform/triggered_analysis.md: triggered analysis valid only with identical trigger in every arm
  ├─ docs/platform/assignment_and_exposure.md: first assignment row binding; SDK cached variant (XPP-44); exposures
  │    are not an assignment record; platform assigns sales-assisted workspaces too
  ├─ docs/ops/INC-5521: re-assignment rows with other variants
  ├─ docs/metrics/activation.md: workspace activation (≥3 distinct users, T <= t < T+14d)
  └─ data: exposure counts by arm vs assignment counts; exposure variant vs assignment; duplicate assignment rows
        → rebuild units from xp_assignments + workspaces + product_events
```

## 8. Distractors (real events)

| Distractor | Why plausible | How falsified |
|------------|---------------|---------------|
| Dashboard performance release (07-21) | changes mount completion → exposure counts | affects treatment logging only; SRM persists; as-assigned counts balanced |
| INC-5521 re-bucketing | could explain SRM or arm contamination | small (43 conflicting workspaces); handled by the first-row rule; not the SRM source |
| Paid-social campaign (08-03) | low-intent signups dilute activation | affects both arms equally under randomization |
| XP-240 concurrent user experiment | interaction | independent hashing, different unit; filtered by experiment id |
| "Exposure SRM is noisy" (PM/platform lore) | normalises the warning | SRM on as-assigned workspaces is fine; exposed-user SRM is huge and arm-dependent |

## 9. Expected investigation paths

1. SRM on exposed users → compare with assignment counts (balanced) → exposure population is arm-dependent.
2. CHANGELOG 3.0.0 vs plan → readout no longer follows the plan's unit, population and reference time.
3. Instrumentation + triggered-analysis guidance → asymmetric trigger; exposure-variant disagreement → identity.
4. Rebuild units per plan; apply the platform's first-row rule, eligibility, maturity, workspace activation.
5. Validate: SRM on units, unit counts, assignment-vs-exposure diagnostics, independent SQL reconstruction.

## 10. Plausible incorrect repairs (all in the mutation suite)

| Repair | Why wrong |
|--------|-----------|
| Workspace-level but only exposed workspaces | still triggered on an asymmetric post-treatment event |
| Arm from exposure variant | cached variants; post-treatment |
| User-level ITT (members of assigned workspaces) | wrong unit and metric |
| Latest assignment row binding | re-bucketing rows are not the randomization |
| No maturity filter / window from creation / window from first exposure | censored outcomes; wrong reference time |
| Include sales-assisted or internal workspaces | not in the eligible population |
| Drop small workspaces, conflicting assignments, workspaces sharing members | post-hoc population edits |
| Activation threshold 2 / unstratified estimator / patch decision / edit exposures | change metric, estimator, outputs or source |
| Hard-coded strata, plan names, incident window, workspace ids | overfits (§12) |

## 11. Correct repair properties

Units only from assignments + workspace attributes; outcome only from product events in the workspace relative to
assignment; no exposure data; estimator and config unchanged; deterministic.

## 12. Hidden fixtures

| Fixture | Invariant tested | Surface changes | Shortcut targeted | Why same distribution |
|---------|------------------|-----------------|-------------------|------------------------|
| hidden_a (2026-04-01) | as-assigned units under strong exposure asymmetry and identity noise; null effect | checklist mount fails much more often; 18% agency users; `starter` self-serve plan; strata by plan and region; 6% SDK retries; no incident | triggered variants, exposure variant, visible strata / plan names | same logging, SDK cache and stratification mechanisms; stratum is logged by the platform |
| hidden_b (2026-12-15) | first assignment binding; decision can be "ship" | real positive effect; control logging drops (reversed asymmetry); larger teams; two cache incidents re-bucket 10–15%; 35% long onboarding delays | latest-row, incident-window overfit, creation anchoring | incidents, delays and team sizes exist in visible at lower rates |
| hidden_c (2027-03-01) | eligibility and maturity; decision can be "rollback" | real negative effect; 8% internal workspaces; 62% self-serve; late heavy enrollment | include internal/sales-assisted, no maturity, hard-coded ids | same mechanisms |

Correct vs bug decisions: hidden_a inconclusive (+0.4 pp) vs ship (+11.6 pp); hidden_b ship (+5.2 pp) vs ship (+7.3
pp, different CI); hidden_c rollback (−3.8 pp) vs rollback (−4.5 pp, different units). Every fixture (and the
visible extract) has core actions before assignment in late-onboarding workspaces (11 / 21 / 35 / 9 activation flips
if the window has no lower bound). No fixture adds an
undocumented rule.

## 13. Verifier

`tests/test_xp_readout.py` (14 checks): extract digest; run succeeds; one row per unit; unit membership; arm, stratum
and activation per unit; readout recomputed from the agent's units; readout vs reference (counts, rates, effect, SE,
CI, SRM, per-stratum, decision); byte-level determinism; hidden a/b/c × (units; readout). Reference: pure Python +
sqlite3.

## 14. Mutation strategy

`tools/task05/shortcuts.py`: Nop, oracle, SQL alternative, plain-Python alternative, 16 shortcuts, 4 overfits (visible
strata → hidden_a; visible plan names → hidden_a; INC-5521 window → hidden b/c; hard-coded ids → hidden), and one
informational boundary probe (`<=` window end), a no-lower-bound window shortcut and a reference-import cheat.

## 15. Risks

- The plan states the unit, population, metric and estimator; once the agent compares plan and code, the repair is
  clear. Difficulty rests on recognising that the "platform standard" is invalid here and on exact
  operationalisation (first-row rule, eligibility, maturity, reference time, workspace metric).
- The buggy `units.py` keeps useful pieces (eligibility filter, first-row stratum lookup, maturity helper), and the
  config's `min_active_users` is unused by the buggy code; both reduce search. Expert estimate lowered to 60 minutes.
- Verifier hardening (all of 03–05, after the Task 05 and cross-task reviews): the pipeline runs as uid 65534 with
  `/tests` unreadable and verifier variables removed; a reference-import cheat scored 1 without this and 0 with it.
- Window-end boundary (`<` vs `<=`) is practically untestable with second-resolution random timestamps (probe).
- Activation rates are low (~8%) because most new workspaces have fewer than 3 members; realistic for team
  activation but reduces power (by design the correct readout is inconclusive).
- The generator's treatment effect acts on users who see the checklist (cached variants create some contamination);
  ITT remains the plan's estimand, and the verifier grades the plan, not a "true" effect.

## 16. Relationship to Tasks 01–04

Task 01: join grain; Task 02: temporal availability; Task 03: evaluation estimand under a model feedback loop (who
has an unconfounded outcome); Task 04: KPI population semantics (business state vs CRM proxy). Task 05: causal
identification in a randomized experiment — randomization unit, post-treatment exposure selection, identity — with
an SRM symptom. It is the only task whose output is a causal decision.

## 17. Capability isolated

Experimental-design reasoning: preserving the randomization (unit, arm, population, reference time) when logged
exposure data offer a tempting but post-treatment, arm-dependent population, and validating with design diagnostics
(SRM, assignment/exposure consistency) rather than effect plausibility.
