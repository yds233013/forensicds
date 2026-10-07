# Real-distribution provenance — task02 (renewal-risk v2.4 in production)

1. **Professional role.** Revenue data scientist owning a churn/renewal-risk model.
2. **Industry.** B2B SaaS.
3. **Business decision.** Whether to release the Q3 retrain, and what Sales and Customer Success
   should be given to work from in the meantime. The model has been scoring live renewals since March.
4. **Realistic inherited artifacts.** The training/evaluation pipeline, the warehouse extract,
   monitoring reports that do not look like the evaluated model, a note from Sales saying the scores
   are not usable, and the February offline evaluation that justified promotion.
5. **Statistical/ML problem.** Point-in-time correctness. Features are time-windowed aggregates
   assembled from a store whose values are overwritten, so the training matrix contains information
   that did not exist at scoring time. The offline metric is inflated; the production metric is the
   honest one.
6. **Why this happens in real organizations.** Without point-in-time-correct joins, models leak future
   information and produce metrics that look good in training and collapse in production. The pattern
   is described as endemic wherever features are time-windowed aggregates, and training-serving skew —
   the live service returning different values from those trained on, because a cache is stale or code
   paths diverged — is named as the first thing to suspect when a model degrades in production rather
   than the algorithm.
7. **Public sources.**
   - Databricks, *Point-in-time feature joins*: https://docs.databricks.com/aws/en/machine-learning/feature-store/time-series
   - *Point-in-Time Correctness in Real-Time Machine Learning*: https://towardsdatascience.com/point-in-time-correctness-in-real-time-machine-learning-32770f322fb1/
   - *Feature Stores and Point-in-Time Correctness: The Bug That Silently Ruins ML Models*: https://dev.to/vaibhav7387/feature-stores-and-point-in-time-correctness-the-bug-that-silently-ruins-ml-models-51k4
   - ApXML, *Point-in-Time Correctness for Training Data*: https://apxml.com/courses/feature-stores-for-ml/chapter-3-data-consistency-quality/point-in-time-correctness
8. **What is synthetic.** The company, accounts, subscription history and feature values.
9. **What is preserved.** The gap between an offline evaluation and production monitoring as the
   *presenting symptom* rather than the diagnosis; multiple candidate explanations (population shift,
   label maturity, pipeline change, leakage) each with a professional reason to be considered; and the
   requirement to repair the pipeline and re-run, not merely to diagnose.
10. **Why it belongs.** It is the suite's temporal-reconstruction / leakage task and covers the SaaS
    retention blueprint. It is also the task with an explicit ablation sibling
    (`02-renewal-risk-regression__explicit-invariant`) that states the invariant outright; both scored
    0/3, which is direct evidence that the difficulty is not in *noticing* the issue.
