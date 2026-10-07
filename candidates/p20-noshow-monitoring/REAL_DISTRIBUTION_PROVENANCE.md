# Real-distribution provenance — p20 (noshow-v3.1 monitoring submission)

1. **Professional role.** Model owner for a deployed clinical operations model, reporting under a
   model-risk standard.
2. **Industry.** Healthcare provider operations.
3. **Business decision.** Whether to adopt the vendor's retrained `noshow-v4.0`, remediate the feature
   pipeline, or take another action MRM-04 §4.3–§4.4 permits, before the winter capacity plan.
4. **Realistic inherited artifacts.** Appointment and outcome records, model score snapshots by
   scoring basis, the feature store and the source records it was built from, the reminder-programme
   configuration and clinic exclusions, the vendor's monitoring review, and MRM-04 itself.
5. **Statistical/ML problem.** Decomposing an observed AUC decline into population drift, feature-feed
   defect, feature vintage, and policy feedback — where the reminder programme the model drives has
   itself changed the outcome distribution — and evaluating on the population the standard specifies.
6. **Why this happens in real organizations.** Deployed models that trigger interventions change the
   outcomes they predict, so monitored performance is not a clean measure of model quality. Separately,
   served feature values can disagree with the source record when the store is refreshed on a different
   cadence than scoring — the training/serving and vintage problem — which degrades live AUC without any
   change in the model or the population. Model-risk standards exist precisely because these causes
   imply different remedies and the vendor's recommendation is not disinterested.
7. **Public sources.**
   - Databricks, *Point-in-time feature joins* (vintage/as-of semantics): https://docs.databricks.com/aws/en/machine-learning/feature-store/time-series
   - *Point-in-Time Correctness in Real-Time Machine Learning*: https://towardsdatascience.com/point-in-time-correctness-in-real-time-machine-learning-32770f322fb1/
8. **What is synthetic.** The provider, clinics, patients, appointments and model scores.
9. **What is preserved.** Four causes that are each professionally plausible for the same symptom, a
   governing standard that fixes the evaluation population and the admissible actions, a vendor with an
   incentive, and multiple scoring bases available in the evidence so the vintage question is answerable.
10. **Why it belongs.** It is the suite's healthcare and its policy-feedback task, and the only one
    where the decision space is constrained by a written model-risk standard. **Version note:** v1 is
    the exposed version; `p20-noshow-monitoring-v1.1` fixes a genuine contract defect found during this
    run (the sign convention for `programme_effect_pp` was unspecified). Both are reported.
