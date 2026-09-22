# Trigger-window audit — EVALUATION ONLY (the operational window stays 3 months)

The trigger window is fixed by supplier-quality practice: a rolling quarter
(`threshold_provenance.md`). Other windows were **evaluated** on the visible regime (60 draws each;
`sim/aux_audits.json`). Bias is in SE_REF units, where SE_REF is the RMSE of the valid state-space
estimator for that window.

| rolling window L | enrollees | truth Q1 | SE_REF(Q1) | naive pre/post (W01) bias | V2 bias | V2 with iid transients (W21) | pre-mean excluding trigger (W04) |
|---|---|---|---|---|---|---|---|
| 1 month | 137 | 211 | 35.0 | **+7.3** | +0.5 | −0.9 | −2.0 |
| **3 months (policy)** | 85 | 242 | 46.0 | **+2.3** | +0.3 | −0.6 | −1.6 |
| 6 months | 60 | 251 | 54.1 | +0.5 | +0.3 | −0.1 | −1.0 |
| 12 months | 49 | 297 | 80.4 | −0.2 | −0.1 | −0.1 | −1.2 |

**Reading:**
- As expected, longer windows make regression to the mean vanish. At 6–12 months, even the naive
  dashboard is unbiased within noise.
- A 1-month window gives large RTM bias (7.3 SE). But a monthly escalation trigger is not what
  supplier-quality practice uses, so choosing it would be **tuning the trigger for separation**. It
  was not adopted.
- At the operational 3-month window, the first-order RTM error is only **2.3 SE_REF**, and the
  second-order errors are ≤ 1.6. That is the realistic middle ground, and it is too narrow
  (`tolerance_window.md`).
