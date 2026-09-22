# Adversarial review (hostile reviewer)

| attack | outcome |
|---|---|
| estimand ambiguity | **Repelled.** ATT per enrollee and ratio of sums, pinned with time zero and horizon (`estimand.md`). |
| G05 overlap | **Repelled.** The exogenous-timing ablation collapses all naive biases to ≤ 0.4 SE_REF. |
| generic DiD solution | **Repelled.** DiD is biased (up to −3.1), but not reliably detectable. |
| recognition hands over the estimator | **Partly.** After H4 the work is real, but ungradable. |
| **wrong methods inside tolerance** | **SUCCEEDS.** WRONG_BOUND 0.02–0.03 at all three scales. |
| **unrealistic sample size** | **Repelled for realism.** 600 / 60 / 250 units are realistic. That realism is exactly why it fails. |
| one-fixture dependence | **Moot.** Coverage is absent, not concentrated. |
| threshold tuning | **Repelled.** Trigger and rollout were fixed before simulation; the 1-month trigger was explicitly rejected. |
| **cheap decision proxy** | **Partly succeeds.** The dashboard gets 4/5 decisions. |
| generator-only truth | **Repelled.** Identifiable in expectation. |
| unrealistic latent assumptions | **Repelled.** Log-normal AR(1) + Poisson is standard. |
| post-treatment leakage | Repelled (design). |
| overly exotic estimator | **Repelled.** State-space / EB and historical-episode calibration are standard SQM / analytics practice. |
| **decision/tolerance** | **SUCCEEDS.** 1.34 and 1.43 SE_REF distances. |

Three attacks succeed (wrong methods inside tolerance, decision/tolerance, and partly the cheap
proxy). Each is disqualifying.
