# MAN-4471 first-pass yield — weeks 13–24
Quality engineering, issued 2026-06-15. Distribution: Operations, Purchasing, Plant Manager.

## Summary

First-pass yield on the BORE_DIA_42 feature has fallen from **97.0 %** (weeks 13–18) to **92.8 %**
(weeks 19–24). Scrap and rework on the feature is running at approximately £180 k per month.

The deterioration begins in week 19. Week 19 is also the week in which the bar stock changed from the H2 heat
family to the H3 family. Nonconforming rates by family over the whole period are:

| heat family | parts | nonconforming |
|---|---|---|
| H2 | 12,000 | 2.98 % |
| H3 | 12,000 | 7.23 % |

The difference is highly significant (one-way ANOVA on deviation by family, p < 1e-12; chi-square on
disposition by family, p < 1e-12).

## Method

`quality.report` recomputes the disposition rate from `inspection_results` for each six-week window, runs an
ANOVA of `measured_um` on heat family with week as a blocking factor, and produces control charts by shift and
by lot (attached separately). Cp/Cpk are recomputed on each window from the same readings.

Capability: Cpk falls from 0.74 to 0.53 across the step. The charts are in statistical control within each
window; the step at week 19 is a level shift, not a drift.

## Findings

1. The step is abrupt and coincides exactly with the H3 changeover.
2. H3 material tests harder (mean 191 HV against 185 HV for H2), consistent with a size change under the same
   cutting parameters.
3. Tool changes were on schedule throughout; cumulative hours at change are unremarkable.
4. No operator or shift effect reaches significance.

## Conclusion and recommendation

The nonconforming rate over the affected window is **7.23 %**, which exceeds the 5.5 % escalation threshold in
Schedule 3 §3.2 of the supply quality agreement. We recommend raising a supplier nonconformance against
Brendale Special Steels and initiating the supplier-change process, with a line stoppage held in reserve if
the rate does not recover within two weeks.

Purchasing has been asked to quantify the commercial exposure (estimated £2.4 m over the contract term).

*Prepared by: Quality Engineering. Reviewed by: Operations.*
