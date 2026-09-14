# Task 09: Negative control, a "broken" conversion metric that is actually a mix shift (design)

Status: design (generation 2). Not built. No model trials. The gradability analysis is in §18 and §22.

## 1. Research question

Can an agent resist assuming that an incident implies a pipeline bug? The task tests whether it can:

- verify that the metric pipeline is semantically correct;
- establish the real data-generating explanation with deterministic evidence;
- avoid a fake correction;
- where warranted, add only a monitoring guardrail.

## 2. Enterprise setting

Lumen (fictional) sells a self-serve analytics product. Its trial-to-paid conversion metric (trials started in week W
that convert within 21 days) is computed by `growth_metrics`, a Python and SQL pipeline over a product events warehouse
extract. The metric feeds the growth dashboard and the paid-acquisition bidding model.

## 3. Visible symptom

- The VP Growth writes that conversion "collapsed" from 14.1% to 10.6% in the weeks after a 2026-09-01 deploy that
  refactored the trial attribution tables. They believe the refactor broke the metric.
- They ask for the metric to be fixed and the bidding model inputs corrected before Q4 budgets.

## 4. Ground-truth causal structure

No pipeline defect. The following are all real in the data:

- A partner co-marketing campaign (channel `partner_referral`, launched 2026-09-02) tripled trial volume from a
  low-intent segment. Its conversion rate is 3–4%, stable over the whole period.
- Within-channel conversion rates for organic, paid search and sales-assisted are unchanged.
- The 09-01 attribution refactor renamed columns and moved the channel derivation into a view. Outputs are identical
  before and after (the logs include a parity check).
- A pricing-page A/B test ran 09-08 to 09-22 with no effect.

## 5. Latent invariant

- The metric definition is unchanged and correct.
- The overall decline equals the weighted combination of stable within-segment rates under a changed channel mix.
- Recomputing the pipeline on raw events reproduces the dashboard.
- A correct response keeps the computation, documents the mix shift with segment-level evidence, and at most adds a
  mix-shift monitor.

## 6. Why this is real DS work

Simpson's-paradox and composition effects are among the most common "broken metric" false alarms in growth analytics.
Separating a pipeline defect from a real population change requires:

- reproducing the metric from raw data;
- checking refactor parity;
- segmenting by plausible dimensions;
- quantifying mix vs rate effects, for example through direct standardization.

## 7. Evidence graph

```
VP memo (refactor broke conversion)
  ├─ deploy log + attribution refactor PR description + parity check log (row-level parity passed)
  ├─ metrics catalog: conversion definition (unchanged)
  ├─ warehouse: trials by channel/plan/region/week; conversions
  ├─ marketing calendar: partner campaign 09-02
  ├─ experiment registry: pricing test (null result)
  └─ dashboard export: overall conversion by week
        → recompute metric (matches) → segment → mix shift in channel; stable within-channel rates
```

## 8. Conflicting evidence and authority hierarchy

| Evidence | Authority |
|---|---|
| Raw warehouse events | **governs** facts |
| Metrics catalog definition | **governs** metric semantics |
| Parity check log | supporting (can be re-run) |
| VP memo causal claim | hypothesis, not evidence |
| Dashboard | derived, and correct |
| Pricing test readout | supporting null |

## 9. Distractors

- The attribution refactor on the same date.
- The pricing A/B test.
- A timezone change note for the events collector, which affects hourly charts only.
- A small real data delay on 09-15, recovered within 6 hours; the metric uses 21-day windows.

## 10. Expected investigation paths

1. Recompute the metric from raw data and confirm it matches the dashboard.
2. Inspect the refactor diff and the parity log.
3. Segment by channel, plan and region.
4. Find the mix change in channel.
5. Quantify the within-channel rates and the rate at baseline mix.
6. Write the report.
7. Optionally add a channel-mix monitor to the monitoring config.

## 11. Plausible incorrect hypotheses

- The refactor broke channel attribution.
- Conversions are delayed (a window issue).
- The pricing test hurt conversion.
- Bot trials.

## 12. Plausible incorrect repairs (all fake corrections)

- Exclude `partner_referral` from the metric.
- Reweight to the pre-campaign mix inside the metric.
- Extend the conversion window.
- Revert the refactor.
- Drop trials from partner-referred emails as "bots".
- Rescale to the baseline.

## 13. Correct repair properties

- Metric pipeline outputs unchanged on the visible and hidden extracts.
- Structured incident report with correct segment-level numbers and the correct classification.
- An optional monitor that does not alter metric outputs.

## 14. Components that must change

- **None in the metric computation.** This is intentional for a negative control.
- **Required new artifact:** `reports/incident_conversion_2026-09.json`, conforming to the incident report schema
  documented in `docs/incident_report_schema.md`, which the analytics team uses for all metric incidents.
- **Optional:** `monitoring/monitors.yaml` entry.

## 15. Data and grain semantics

- Trial: `trial_id` with `started_at`, `channel`, `plan`, `region`.
- Conversion: `trial_id` with `paid_at`.
- Metric: `week × overall`; converted within 21 days of `started_at`.
- Report schema:
  - `classification` (enum: `pipeline_defect`, `data_delay`, `population_mix_shift`, `within_segment_rate_change`,
    `no_change`)
  - `pipeline_verified` (bool)
  - `baseline_weeks`, `current_weeks`
  - `segments[]` by dimension, each with trials, conversion rate and share in both periods
  - `primary_dimension`
  - `rate_current_at_baseline_mix`

## 16. Hidden fixture design

Hidden fixtures serve two purposes.

**(a) Rerun the unchanged pipeline on hidden extracts and compare with the reference.** This catches fake corrections
that change metric code.

**(b) Grade the report against the visible extract only.** The report is a one-time incident artefact.

Option (b) keeps the negative control objective but loses a generalisation test of the analysis. The alternative is to
require a reusable `explain_change` command that is run on hidden extracts with different true causes (plan mix, region
mix, genuine within-segment decline). This is stronger but makes the task partly "write a generic analysis tool", which
is less realistic.

**Decision:** use (a) plus a visible report. Add one hidden extract where there is a genuine within-segment decline and
no mix shift, to ensure the pipeline itself is not modified in a way that hides it.

## 17. Mutation-suite plan

- **Nop:** no report, so reward 0. This establishes that "didn't edit anything" alone fails.
- **Oracle:** unchanged pipeline plus a correct report and monitor.
- **Alternate correct:** a report with a different but valid segment ordering and extra dimensions.
- **Fake corrections:** each §12 repair, with a correct-looking report.
- **Report errors:**
  - wrong classification
  - `pipeline_defect` claimed
  - wrong primary dimension
  - numbers off
  - claimed parity without data
- **Output patch:** edit the dashboard CSV.
- **Source mutation.**
- **Cheat.**

## 18. Verifier plan

1. Raw integrity.
2. Pipeline outputs on visible and hidden extracts equal the reference, i.e. no fake correction.
3. Report exists and validates against the schema.
4. Classification is `population_mix_shift` and `pipeline_verified` is true.
5. `primary_dimension` is `channel`.
6. Segment numbers for the channel dimension match the reference, to 1e-6.
7. `rate_current_at_baseline_mix` is within 1e-6 of the reference. Direct standardization is defined in the metrics
   catalog, where a "mix-adjusted conversion" metric already exists for the board deck. This is a metric definition,
   not a repair algorithm.
8. Any monitor config is valid YAML and does not alter metric outputs.

Is this deterministic and objectively gradable? **Yes**, provided:

- the report schema is documented;
- the standardized-rate metric definition already exists in the catalog;
- the baseline and current week ranges are fixed by the incident template (the memo gives the weeks).

The main residual subjectivity (free-text explanation) is not graded.

## 19. Alternate-valid-solution considerations

- Agents might report additional dimensions (accepted).
- They might choose different baseline weeks. Not allowed: the memo fixes the weeks.
- They might add a monitor or not. Optional, not graded beyond not altering outputs.

## 20. Leakage and answer-key audit

- The schema's enum lists `population_mix_shift` among five options. That is a hint, but a multiple-choice
  classification with numeric evidence requirements.
- The catalog's mix-adjusted metric existing may point toward mix. Mitigation: the catalog lists several board metrics,
  and mix adjustment is one of them.

## 21. Difficulty rationale relative to Task 02

It is not harder in implementation. The difficulty is epistemic: an agent primed to "fix the bug" will change the
metric. Success requires verification and quantitative explanation, not code change.

## 22. Benchmark-validity risks

- **Hints.** The report schema and catalog definition could hint the answer. The review must weigh this.
- **Nop.** Nop fails only because no report exists. This is acceptable: the task requires an incident report.
- **Realism.** Graded incident reports are unusual but defensible (a structured incident template).
- **Headroom.** If agents always write the report correctly, the task is an easy anchor for "no bug". Its value is
  measuring false-positive repairs.

## 23. Post-review revisions required before build

See `research/gen2_design_review.md` §2–3. This design is **not approved for implementation** until those revisions
are incorporated. The required changes are listed in the review's decision table.
