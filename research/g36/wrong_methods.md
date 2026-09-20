# G36 pre-registered wrong analyses

Fifteen wrong methods, registered before the gates ran. Errors are in kW against latent truth;
`*` marks a wrong business decision. Accepted-estimator sampling sd = 0.0142.

| code | analysis | why an analyst writes it | visible | hidden_a | hidden_b | hidden_c | hidden_d | wrong decisions |
|---|---|---|---|---|---|---|---|---|
| **W1** | historical model only | it is the incumbent, and it backtests at R2 0.75 | +0.331 | +0.333 | +0.466* | +0.321 | +0.638* | 2 |
| **W2** | retrain on the latest summer | "use the most recent data" | +0.330 | +0.331 | +0.465* | +0.321 | +0.640* | 2 |
| **W7** | pilot mean response, applied flat | the pilot is the only tariff evidence there is | -0.188* | -0.267* | -0.102 | -0.388* | -0.272 | 3 |
| **W8** | **selection fixed only** | understood opt-in bias, stopped there | -0.016 | +0.014 | +0.072 | **-0.165*** | +0.007 | 1 |
| **W9** | **temperature fixed only** | understood heat damping, stopped there | -0.087 | -0.151* | -0.075 | -0.075* | -0.113 | 2 |
| **W10** | forecast the pilot population, not the estate | the pilot is "the data we have" | +0.733 | +0.949 | +0.527* | +0.637 | +0.415* | 2 |
| **W11** | reweight pilot *outcomes* to the population mix | covariate-shift reflex applied to an effect | -0.558* | -0.515* | -0.380 | -0.607* | -0.382 | 3 |
| **W12** | condition on the peak-share mediator | it is a strong historical predictor | +0.331 | +0.333 | +0.466* | +0.321 | +0.638* | 2 |
| **W13** | apply the pilot's aggregate % reduction | simple, defensible-sounding | -0.241* | -0.271* | -0.226 | -0.523* | -0.387 | 3 |
| **W14** | intercept-only recalibration to the pilot control arm | "recalibrate to current conditions" | +1.139 | +1.400 | +1.234* | +1.122 | +1.427* | 2 |
| **W15** | seasonal naive on historical mean | the baseline every forecaster starts from | -0.003 | +0.050 | +0.193* | +0.121 | +0.323* | 2 |
| **W16** | right response, wrong load level | correct transport applied to the pilot's own level | +0.024 | +0.299 | +0.082* | -0.001 | +0.003 | 1 |

Three further pre-registered methods were **not implementable as distinct analyses** in this design
and are recorded as such rather than padded in: *time-decay weighting* and *change-point detection*
both reduce to W2 here because the historical period contains no tariff and therefore no break to
find; *drop the changed feature but keep a descendant* reduces to W12 because the tariff is not a
column in the historical table at all. They are honest non-entries, not separations.

## The two that carry the gate

`W8` and `W9` are the reason G36 is not G35. Each is written by an analyst who has **correctly
recognised** a real problem and fixed it - and each is still wrong, by 10-12 sd, with a wrong capacity
decision. Neither is a strawman: both are more sophisticated than the incumbent.

## Failure-taxonomy placement

- **W1, W2, W12, W15** - F9: right method family, wrong statistical object (a historical conditional
  reported as a future one).
- **W8, W9** - F9 in its most defensible form: a partially transported estimand.
- **W10, W11, W16** - F10-adjacent: right machinery, wrong population or wrong level.
- **W13, W14** - F5: patching a level rather than modelling the mechanism.
- **W7** - F1: the pilot's headline number taken as the answer.
