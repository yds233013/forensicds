# Task 03 — Lead-score evaluation population (design)

Harbor task: `candidates/03-lead-score-evaluation` (`forensicds/lead-score-evaluation-03`).
Validation: `report/task03_validation.md`. Status: pre-baseline; **no model trials run**.

## 1. Research question

Can an agent recover the *evaluation estimand* of a deployed model — which population's outcomes measure what the
score is used for — when an operational feedback loop (the model's own routing decisions) changes which outcomes
exist, and preserve it at the correct grain (intake assignment, intent-to-treat) rather than accepting the population
that happens to have labels?

This isolates a statistical-design capability distinct from Task 02: nothing is leaked in time; every label in the
buggy population is *true*. The failure is that many labels are outcomes of a different treatment.

## 2. Enterprise setting

B2B SaaS inbound funnel. An inbound lead-score model (`lsm-3.2`) scores every accepted lead at intake; the router sends
leads at or above a threshold to the SDR queue, a random 10% exploration holdout to the SDR queue regardless of score,
and the rest to marketing nurture. SDRs can manually claim nurture leads; territory changes re-route SDR-queue leads.
RevOps Analytics runs a monthly evaluation (`lead_eval`) that informs champion health and the router threshold.

## 3. Visible symptom

Memo from the Head of RevOps: evaluations for August/September show the champion much stronger; Sales Development
proposes retiring the holdout and raising the threshold; inbound conversion hasn't moved.

Workspace evidence (all computed at build time from the same data and code):

| Report (as of) | Code | n_leads | ROC AUC | Top-decile lift | Recommended threshold |
|----------------|------|--------:|--------:|----------------:|----------------------:|
| 2026-07-01 | 1.4.2 | 853 | 0.755 | 3.04 | 0.162 |
| 2026-08-01 | 2.0.0 | 8,197 | 0.848 | 3.95 | 0.297 |
| 2026-09-01 | 2.0.3 | 8,733 | 0.848 | 3.98 | 0.284 |

Correct evaluation for 2026-09-01: n = 920, conversion 11.7%, AUC 0.754, lift 3.24, recommended threshold 0.151 —
the buggy report would move the router threshold in the wrong direction and justify retiring the holdout.

The 1.4.2 reports are *not* an answer key: 1.x labelled outcomes from sales-led CRM opportunities only (RA-512 note:
v1-era consumers missed self-serve purchases), so re-running the fixed pipeline for a 1.x month reproduces n_leads but
not the metrics exactly. (Changed after the adversarial review; see `report/task03_validation.md`.)

## 4. Hidden root cause

lead_eval 2.0.0 (RA-512) switched outcomes to RevOps lifecycle v2, which records `converted_60d` for every accepted
lead, and "expanded" the evaluation population to all matured accepted leads. The score estimates P(convert within 60
days | lead is routed to the SDR queue). The router uses the score to choose who goes to SDRs; nurture leads rarely convert
because nobody works them. Their (true) non-conversions are outcomes of not being treated, so the evaluation rewards
the model for its own routing decisions — a self-fulfilling feedback loop.

## 5. Latent invariant

The evaluation metric must be computed over the population whose outcome *under the estimand's treatment (routed to
the SDR queue)* is observed independently of the score: the exploration holdout, **as assigned at intake**, **intent-to-treat**
(holdout leads SDRs failed to reach remain in), restricted to accepted leads in the evaluation window whose 60-day
outcome window has closed, labelled by closed-won within 60 days of creation, scored by the champion intake score.

Grains: lead × intake routing decision (first routing event); temporal: creation window + 60-day maturity at the
as-of date; outcome: closed-won regardless of channel.

## 6. Why this is real DS work

Evaluating a model whose decisions determine which outcomes are observed is a recurring practical problem in credit,
fraud, hiring, lead routing and recommendation (known in the literature as the selective labels problem and, when the
prediction changes the outcome, as performative prediction; feedback loops are also listed among ML technical-debt
risks). Exploration holdouts / randomized control slices are the standard operational remedy. The specific pattern —
a data-platform improvement makes outcomes "available" for everyone, and a well-meaning analyst widens the evaluation
population — is plausible and consequential (it drives a decision to remove the holdout).

Sources to verify before publication (not re-checked online in this session): Lakkaraju et al., "The Selective Labels
Problem: Evaluating Algorithmic Predictions in the Presence of Unobservables", KDD 2017; Perdomo et al., "Performative
Prediction", ICML 2020; Sculley et al., "Hidden Technical Debt in Machine Learning Systems", NeurIPS 2015.

## 7. Evidence graph

```
Memo: evaluation much stronger; conversion flat; proposal to retire holdout
  ├─ reports/model_monitoring: n_leads 852 → 8,193 at the 2.0 release; AUC jump coincides
  ├─ CHANGELOG / deployments: lead_eval 2.0.0 "evaluation population expanded" (RA-512); router threshold change; webinar
  │   campaign; challenger shadow; SDR onboarding (distractors)
  ├─ model card: score = P(convert | routed to SDR queue); router uses it to decide who SDRs receive
  ├─ router design: threshold, nurture (no SDR follow-up), exploration holdout (random draw in the intake decision;
  │   pauses), SDR queue worked highest-score-first (low scores miss SLA), manual claims, territory re-routes
  ├─ evaluation definition: what it measures (cohort whose treatment is not determined by the evaluated score),
  │   window (inclusive bounds), maturity, outcome (any channel, <= 60 days), metrics
  ├─ RA-512 note: lifecycle v2 computes converted_60d for all accepted leads
  ├─ RevOps conversion note: 60-day conversion by month, flat
  └─ data: routing_events (initial vs later), sdr_activities (who was worked), conversions (self-serve vs sales-led)
        → population = intake exploration holdout (ITT) within window
```

## 8. Distractors (real events)

| Distractor | Why plausible | How falsified |
|------------|---------------|---------------|
| Router threshold 0.30 → 0.22 (2026-06-15) | changes who is worked | 1.4.2 July report (holdout) already includes June cohorts and did not jump |
| June webinar series (+60% volume, low intent) | easy negatives can raise AUC | holdout AUC is stable; jump coincides with the 2.0 release, not June cohorts |
| lsm-3.3 shadow challenger scores (June) | evaluation could have picked up the wrong model | config and cohort use the champion; score check |
| Two SDRs onboarded (July) | worked-lead conversion changes | affects outcomes, not ranking of the random slice |
| Lifecycle v2 migration | changes outcome source | label is equivalent to conversions-derived label; the population change is the effect |

## 9. Expected investigation paths

1. Compare report history: n_leads ×10 and AUC jump at 2.0.0 → population change, not model change.
2. Read CHANGELOG/RA-512 → population widened because outcomes became available.
3. Ask what the score estimates and how it is used (model card, router) → recognise the feedback loop.
4. Identify the random slice (exploration holdout) and its membership rule (intake, SLA misses stay in).
5. Rebuild the cohort; validate by comparing populations (all / worked / holdout ITT / per-protocol) and cohort
   membership, not only AUC.

## 10. Plausible incorrect repairs

| Repair | Why wrong | AUC it produces (visible) |
|--------|-----------|---------------------------|
| Worked leads only ("outcomes observed under treatment") | selected on score and rep judgement | 0.667 |
| All accepted leads (the 2.0 bug) | nurture outcomes are outcomes of the router's decision | 0.848 |
| Holdout, worked only (per-protocol) | SDRs work highest score first, so who is reached depends on the score; threshold 0.215 vs 0.151 | 0.746 |
| Holdout by latest routing event | re-routes change membership | = correct on visible; wrong on hidden_b |
| Leads currently in SDR queue | routed + claimed + holdout | — |
| Threshold-routed leads only | range-restricted | — |
| Reconstruct random slice as sub-threshold SDR leads | drops above-threshold holdout leads | — |
| SDR "qualified" as the label | downstream operational decision | — |
| Sales-led conversions only | outcome definition includes self-serve | — |
| Remove maturity filter | censored outcomes as negatives | — |
| Exclusive window bounds / labels `< 60 days` | contradict documented inclusive bounds (midnight partner imports, CRM close dates) | ≈ correct |
| Make history match 1.4.2 exactly | 1.x counted sales-led conversions only | — |
| Re-weight worked leads | unknown claim propensities; not the documented metric | — |
| Patch report numbers / change target / edit extract | symptom patches | — |

## 11. Correct repair properties

Membership from the first routing event per lead; no dependence on `sdr_activities`; window/maturity/outcome/score
unchanged; metrics code unchanged; deterministic ordering.

## 12. Hidden fixture design

| Fixture | Invariant tested | Surface changes | Shortcut targeted | Why same distribution |
|---------|------------------|-----------------|-------------------|------------------------|
| hidden_a (as of 2025-10-01) | ITT at intake under heavy selection | 5% holdout, three router versions in window, reps claim far more nurture leads, 12% SLA misses, content campaign | worked-only, per-protocol, visible router versions | same router policies and documented semantics; only rates/calendar differ |
| hidden_b (as of 2026-03-01) | membership fixed at intake | 15% holdout, three-week holdout pause (recorded in `router_config_log`), 35% of holdout leads territory re-routed; boundary leads on both window ends | latest-routing-state holdout (visible has no re-routed holdout leads); holdout-share sanity guards | re-routing and pauses are documented router behaviours |
| hidden_c (as of 2027-01-01) | outcome definition, maturity, boundaries | strong self-serve purchasing by unworked leads, 35% of deals closing around day 56–80 (one exactly on day 60), 14% rejected, more partner (midnight) leads; 7 holdout leads created exactly on the window start | sales-led-only labels, all-leads variants, maturity, exclusive bounds, `< 60` labels | self-serve, late closes, midnight partner imports and CRM close dates all exist in the visible extract |

No hidden fixture introduces a rule absent from the visible documentation.

## 13. Verifier design

`tests/test_lead_eval.py` (14 checks): extract digest; run succeeds; one row per lead; cohort membership (missing and
extra reported separately); labels and champion scores; report recomputed from the agent's own cohort (catches patched
numbers); report vs reference (AUC, conversion, top decile, calibration bins, recommended threshold, by source);
byte-level determinism; hidden fixtures (membership; labels/scores/report). Metrics exact to 1e-6 because the cohort
fully determines them. Reference: pure Python + sqlite3.

## 14. Mutation strategy

`tools/task03/shortcuts.py`: Nop, oracle, SQL alternative, plain-Python alternative, 15 shortcuts (including exclusive
window bounds and strict `< 60 day` labels), 3 overfits (latest routing policy → hidden_b; visible router versions →
hidden fixtures; hard-coded holdout ids → hidden fixtures). Results: `report/task03_mutations.txt`.

## 15. Risks / possible flaws

- The evaluation definition now states the population *property* (treatment not determined by the evaluated score),
  added so the graded behaviour is documented (harbor check `behavior_in_task_description`). Together with the router
  doc this makes the repair recognisable once the population change is noticed; the remaining difficulty is
  operationalising it (intake decision, ITT, boundaries, outcome channels) and validating by membership.
- The symptom-to-cause path is short (n_leads ×10 at the 2.0.0 release → CHANGELOG). Distractors are real but each is
  refuted by one fact. This task likely tests *operationalisation* more than *discovery*.
- Holdout cohort is small (~900 leads, ~110 conversions): metrics are noisy month to month, but deterministic for
  grading.
- Timeline: hidden_a's as-of (2025-10-01) precedes the visible model card's history; hidden extracts are separate
  synthetic worlds and only the documented mechanisms are held fixed.
- An agent could argue for IPW over worked leads; it is not the documented metric and relies on unknown claim
  propensities; the instruction forbids re-weighting.
- The verifier cannot detect a correct cohort produced by an unprincipled route (e.g. hard-coded rule that happens to
  match); hidden fixtures reduce this.

## 16. Relationship to Tasks 01/02

Task 01: entity grain of joins; Task 02: temporal availability of features. Task 03: statistical estimand of an
evaluation under a feedback loop — no join or time-leak defect; the data are correct and complete.

## 17. Capability isolated

Evaluation design reasoning: mapping a model's intended use and the operational treatment mechanism to the population
on which its performance is identifiable, and validating by population rather than by metric plausibility.
