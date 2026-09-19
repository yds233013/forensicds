# What would count as a scientifically interesting model failure on G31

Written **before** any model is run, so that the baseline cannot be interpreted after the fact. This is the G31
analogue of the pre-baseline predictions section that proved valuable (and largely wrong) for G05.

## Interesting — these are the measurements the task exists to make

| # | Failure | What it would tell us | Which wrong method it corresponds to |
|---|---|---|---|
| 1 | Notices delayed chargebacks, corrects the maturity horizon properly, evaluates on settled rows | **The single most valuable outcome.** It would show the model solves the famous problem and stops there — that its notion of "missing label" is exhausted by censoring | `W3_mature_settled_only` |
| 2 | Finds the bypass programme, weights by it, but forgets the allow band | Selection understood, target population wrong. The `rsDKTXQ` shape from G05 in a new setting | `W9_holdout_only` |
| 3 | Sees selection, reaches for inverse-probability weighting, uses the observed labelling rate instead of the logged bypass rate | The G24 shape: correct method family, wrong probability object — and here the right probability is *written down in a policy table*, so the failure is not one of inference but of object identification | `W7_ipw_on_v6_band` |
| 4 | Uses investigator determinations as ground truth because they are the highest-quality labels | Would show the model does not check positivity — the determinations exist only for the top of the band by construction | `W4_reviewed_only` |
| 5 | Everything correct, but recall computed per transaction rather than per dollar | **Decision-correct, analysis-wrong.** The business decision comes out right and every graded quantity is wrong | `W10_count_recall` |
| 6 | Correct analysis, then no self-check at all: no comparison of holdout vs non-holdout covariates, no mature-cohort-only robustness run, no alternative specification | Fifth independent confirmation of the benchmark's strongest finding (S7 failed by every trial of every task) | — |
| 7 | Treats blocked authorisations as fraud, or as legitimate | Would show the model resolves an unidentified quantity by assumption rather than by naming it as unidentified | `W5`, `W6` |
| 8 | Produces one pooled number for a question asked per segment | Would show the model answering the question it can answer rather than the one asked | `W8_pooled_segments` |
| 9 | **Solves it correctly.** Handles all three mechanisms, recovers per-segment deltas, recommends v7 in two segments and v6 in one | Would falsify the working hypothesis, which is the point of running it | — |

Failure 9 deserves emphasis. The task is designed so that a model **can** solve it: the bypass rate is logged, the
maturity horizon is estimable, the policy is documented, and four structurally different estimators all recover
the answer. If the hypothesis is wrong, G31 should show that.

## Uninteresting — would indicate a task or infrastructure defect, not a capability limit

- cannot find an artefact; cannot join two tables; SQL or pandas error
- missing package; pipeline will not run; container or verifier failure
- misreads a column name or a segment label
- runs out of time on a mechanical step (this would mean the task is too large, not too hard)
- produces the right analysis but fails the output contract on formatting
- disputes the estimand because the task text is ambiguous — **this is an F8 and a task defect**, and the
  readout contract must be specific enough (fixed flag rate, value-weighted, full eligible population) that it
  cannot happen

## Pre-registered predictions

Recorded now so they can be scored honestly later. G05's predictions were mostly wrong, which was itself the most
informative part of that baseline.

| # | Prediction | Confidence |
|---|---|---|
| P1 | At least one trial will correct the maturity horizon and stop there (`W3`) | high |
| P2 | No trial will run a self-check on its own specification (S7) | high |
| P3 | At least one trial will find the bypass programme | medium |
| P4 | No trial will notice the review band's positivity violation without being led to it | medium-high |
| P5 | At least one trial will get the per-segment decision right with wrong quantities | medium |
| P6 | The marketplace segment will be identified as anomalous by at least one trial, but for the wrong reason (slow chargebacks rather than the challenger's nuisance loading) | medium |
| P7 | pass@3 will be 0 | medium — this is a prediction, not a design target, and P7 being wrong is a good outcome |

**P7 must not become a design goal.** If simulation or review shows the task is solvable by a competent analysis,
that is a successful task, not a failed one.
