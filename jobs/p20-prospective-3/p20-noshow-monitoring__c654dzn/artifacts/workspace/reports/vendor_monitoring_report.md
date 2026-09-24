# noshow-v3.1 — monitoring review and retrain proposal
Prepared by Calder Analytics (model vendor) for Halcyon Health Partners. 2026-07-02.

## Summary

`noshow-v3.1` has lost discrimination since deployment. Against a validation figure of **0.774 AUC**, the
monitoring series for the most recent twelve weeks stands at **0.702 AUC**, a fall of 7.2 points.

We attribute the fall to data drift and recommend adopting the retrained `noshow-v4.0`.

## Evidence

**Feature drift.** Population Stability Index against the training period exceeds the usual 0.2 action
threshold on four features, and the referral mix has changed materially since month 4 with the arrival of the
partnership source. Lead times on partnership referrals run roughly eight days longer.

**Monotone decline.** The weekly AUC series in `monitoring_metrics` declines through the period. The decline is
not confined to any one clinic group.

**Temporal validation.** Training on the earlier part of the period and testing on the later part reproduces
the decline, which rules out an evaluation artefact.

**Retrain restores performance.** `noshow-v4.0`, fitted on data from the programme period onward, achieves
0.79 AUC when validated on a recent holdout drawn from the clinics the programme covers. Scores for every
appointment in the extract are supplied in `model_scores` so that Halcyon can reproduce this.

## Recommendation

Adopt `noshow-v4.0`. We further recommend moving to a quarterly retrain cadence, since the drift we observe
appears to be ongoing rather than a one-off shift.

## Notes

The monitoring series is computed from the feature store as it currently stands, which we rebuilt in week 33
when the no-show count window was widened. We have not recomputed the series on the earlier feature definition.
