# MRM-04 — Model risk management standard (extract)

Halcyon Health Partners. Issue 3. Applies to all models used to direct patient contact or clinical capacity.

## 4. Ongoing monitoring

### 4.1 Population

Performance monitoring shall be computed on a population whose outcomes are **not influenced by the model's own
use**. Where a model's output drives an intervention, the intervention changes the outcome being predicted, and
a metric computed on the intervened population measures the intervention as well as the model.

It is the model owner's responsibility to identify a suitable population from the deployment design and to
record which population was used in every monitoring submission.

### 4.2 Scoring basis

Monitoring shall state the scoring basis. Where a model's features are rebuilt after deployment, the figure
computed on the rebuilt features is not the figure the model achieved in service, and both shall be reported.

### 4.3 Retention floor

A model may be **retained** only while its discrimination on a population meeting §4.1, computed on the scores
it produced in service (§4.2), is

* within **0.04 AUC** of the validation figure recorded in the model registry, **and**
* not below **0.70 AUC**.

The lower of the two gives the retention floor.

### 4.4 Where the floor is breached

Where the floor is breached the model owner shall determine the cause and act in the following order.

1. **Feed integrity first.** If more than **5 %** of scored records in the window were served a feature value
   that does not agree with the source record or with the append-only event history, the finding is a defect in
   the feature feed. Where rescoring from the source restores discrimination above the floor, the required
   action is `remediate_feature_pipeline`. A model shall not be retrained or replaced to compensate for a
   defective feed.
2. **Candidate comparison.** Otherwise, if a candidate model's discrimination on the same population exceeds the
   incumbent's by more than **0.02 AUC**, the required action is `replace_with_v4` (or the candidate under
   consideration).
3. **Otherwise** the required action is `retrain_on_recent_data`.

A candidate trained on data from a period in which the incumbent's output directed an intervention shall be
evaluated on a population meeting §4.1 before any comparison under (2) is relied upon.

## 5. Records

Every monitoring submission shall record the population, the scoring basis, the validation figure it is
compared against, and the action taken.
