# Natural implementation path (R1) — from existing results

| smallest plausible analysis | method | bias (SE_REF) vis / a / b / c / d | detect on the 2nd fixture | decision correct |
|---|---|---|---|---|
| pre/post treated only (trigger window vs post) | W01 | +2.0 / +2.7 / +0.5 / −1.8 / +0.7 | 0.10 | 100 / 10 / 99 / 100 / 96 % |
| company dashboard % change | W02 | same Q1; Q2 unweighted | 0.71 | same |
| average pre vs post | W03 | −1.2 / −0.6 / −2.4 / −1.8 / −0.6 | 0.10 | |
| exclude the trigger window | W04 | −1.6 / −1.1 / −2.7 / −1.8 / −0.8 | 0.13 | |
| matched on trigger value (contemporaneous) | W08 | −3.4 / −2.7 / −3.5 / −5.8 / −1.5 | 0.46 | |
| matched on long-run mean | W10 | −2.9 / −2.2 / −3.6 / −1.5 / −1.3 | 0.31 | |
| DiD with unit/time FE | W05 | −0.9 / −0.4 / −2.4 / −0.7 / −0.4 | 0.05 | |
| event study, trigger reference | W06 | +3.7 / +4.1 / +1.8 / +1.4 / +1.3 | 0.72 | |
| regress post on trigger value (RD extrapolation) | W11 | −2.9 / −2.6 / −3.0 / −4.0 / −2.1 | 0.82 | |
| historical average as counterfactual (fleet) | W15 | −10.9 / −8.4 / −9.9 / −19.7 / −3.8 | **18.1** | |

- The natural path is **wrong in expectation**: pre/post biases reach 2–4 SE_REF, often 100+ defects
  per enrollee.
- It is **not reliably rejectable**, because the p01 detection on the second-best fixture is ≤ 0.8
  for every route except W15. Only the crude fleet-average counterfactual separates.
