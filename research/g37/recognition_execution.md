# Recognition-vs-execution gate (C1, D2)

Each hint condition is operationalised as the natural route set an analyst holding that hint would
use. Values are detect = the error (SE_REF) shown in ≥ 99 % of draws, on the second-best fixture.

| condition | natural routes | detect (2nd fixture) | verdict |
|---|---|---|---|
| **H0** no hint | raw dashboard (W01); vendor block certificate (W02) | 62.4; 57.2 | fail clearly |
| **H1** "the apparent change may be the gauge" | bridge mean offset (W03); OLS new~old (W04); OLS inverted (W05); ratio (W15) | 11.9; 9.3; 6.7; 5.5 | fail clearly |
| **H2** "both gauges have error, OLS is biased" | Deming/orthogonal mapping without deconvolution (W07); orthogonal regression (W17); geometric-mean regression (X08) | 5.2; 3.2; 2.3 | W07 fails; **W17 and X08 are within the noise band** |
| **H3** both insights | Deming + subtract the new gauge's error variance | passes. Its remaining variants (divisor, instrument, scale order, shrinkage, offset-mean) sit at **0.04–3.6** | **residual steps are numerically invisible** |

**Gate result: FAIL.** After H3, the remaining statistical work (the correct divisor for 2-scan
means, the correct instrument's variance, rescaling before deconvolution, overall vs within) exists
conceptually. But the data cannot distinguish getting it right from getting it slightly wrong. H3
effectively reduces to "Deming, then subtract a variance", which the pre-registered rule counts as a
failure.
