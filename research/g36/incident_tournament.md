# G36 incident tournament

Nine incidents written; three taken to formal design; two simulated.

Rejection rule applied throughout: **if "notice the policy changed" immediately tells the analyst
what to compute, reject.**

## The nine

### I1 - Mandatory time-of-use tariff, peak capacity procurement (domain B) -> **SIMULATED, SELECTED**
A utility must decide whether to procure peaking capacity for next summer. Three summers of flat-
tariff history; a mandatory TOU tariff starts before the target summer; a voluntary TOU pilot ran
last summer with randomisation inside the opt-in group.
*Why recognition is not enough:* two orthogonal transport problems (opt-in selection, heat damping).

### I2 - Algorithmic repricing, promotional plan sign-off (domain A) -> **SIMULATED, runner-up**
Historical prices were manager-set and endogenous; a randomised price test ran in volunteer stores;
an algorithm will discount deeper than the test did.
*Measured weaker:* see `simulation_results.md` s6.

### I3 - Scheduler change, cluster capacity plan (domain C) -> formal design only
A new bin-packing scheduler changes queue depth, which is a **descendant** of the intervention and a
strong historical predictor of runtime. Shadow-mode output exists for a subset of clusters.
*Strong mediator trap*, but the target quantity depends on a workload mix that is itself forecast,
which stacks a second forecasting problem and muddies the estimand.

### I4 - Conservation programme, water demand (domain K) -> rejected
Nearly isomorphic to I1 with a weaker stable mechanism (no clean physics analogue) and thinner
evidence for heterogeneity.

### I5 - Procurement rule change, supplier lead times (domain F) -> rejected
Once the sourcing rule is known, the forecast is a reweighted mixture of stable per-supplier
distributions. **Recognition hands over the estimator.** This is the G35 failure exactly.

### I6 - Contract auto-renewal change, churn forecast (domain E) -> rejected
The post-change renewal decision is not identified from pre-change data or any realistic pilot.
Fails the identifiability gate (K1).

### I7 - IVR deflection change, call handle time (domain I) -> rejected
The intervention changes the *mix* of calls reaching an agent. Again a mixture reweight.

### I8 - Maintenance policy change, throughput (domain H) -> rejected for this round
Viable, and the stable/unstable split is clean, but the evidence for the changed mechanism would
have to be a long pilot; the realistic version needs more elapsed time than the incident allows.

### I9 - Carrier mix change, transit time (domain L) -> rejected
Covariate shift with extra steps.

## Top three carried to formal design

| rank | incident | decisive property |
|---|---|---|
| **1** | **I1 TOU tariff** | two orthogonal transport problems, both realistic, both necessary |
| 2 | I2 repricing | confounded history plus two transports, but a noisy estimand |
| 3 | I3 scheduler | excellent mediator trap, weakened by a nested workload forecast |

## The rejection that matters most

**I5 (supplier lead times) is the clearest illustration of the G35 trap.** It looks sophisticated -
structural change, policy intervention, mixture forecasting - and it collapses the moment the analyst
says "the sourcing rule changed", because the remaining work is a weighted average of per-supplier
distributions that the data hands over directly. It was rejected for exactly the reason G35 should
have been caught earlier.
