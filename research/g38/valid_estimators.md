# Valid estimator families (R1) — existing 200-draw run

| family | estimator | visible evidence | assumptions | algorithm | bias (SE_REF) | SD (SE_REF) | failure modes |
|---|---|---|---|---|---|---|---|
| **V1 pseudo-episode calibration** | Poisson GLM of post-6 defects on log S* and log H* (offset: seasonal exposure), fitted on the **same trigger rule applied retroactively** in months 11–16 (untreated); predicts the enrollee counterfactual | pre-programme panel | stationarity; log-linear conditional mean | IRLS | +0.07 … +0.17 | **0.76–1.85** (inefficient: ~90 pseudo-episodes) | model form; era drift |
| **V2 state-space / EB latent risk** | random intercept + AR(1) shock on log rates, Poisson noise 1/(D+0.5); hyperparameters from pre-era autocovariances; Kalman-filtered counterfactual with log-normal correction | full panel pre-enrolment | log-normal AR(1) form; Gaussian approximation to Poisson | moment fit + Kalman filter | +0.11 … +0.30, **+0.81 on hidden_d** (small counts break the log-Gaussian approximation) | 0.53–0.99 (defines SE_REF) | approximation bias at low counts |
| L1 V1 with S only | legitimate: the conditional mean given S is valid under the same-rule selection | | | | +0.04 … +0.18 | 0.79–1.71 | |
| L2 V1 on all crossings | variant | | | | −0.42 … −0.06 | 0.79–1.62 | |
| L3 NN matching on (S*, H*) vs same-rule pseudo-episodes | matching variant of V1 | | | | −0.51 … −0.30 | 0.58–1.59 | |

- **Independence.** V1 and V2 use different evidence (pseudo-episode outcomes vs autocovariance
  structure), different assumptions and different algorithms. They share no code for the graded
  quantity. The seasonal index is computed separately in each.
- **Disagreement.** The mean difference is ≤ 0.2 SE_REF except on hidden_d, where V2's +0.8
  approximation bias shows.
- **Key point for the window.** Even the *efficient* family carries SD ≈ 1 SE_REF by definition. That
  SD is dominated by **irreducible** uncertainty: the realised future shocks of each enrollee
  (`tolerance_window.md`).
