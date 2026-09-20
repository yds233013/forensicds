# G36 coherent-but-wrong gate

The direct carry-forward of the G34 baseline finding and the G35 verifier design: **internal
coherence and historical validation are not validity for a changed regime.**

## The construction

`W1_historical_only` is not an invented strawman. It is the utility's production forecasting model:
a per-segment regression of peak load on cooling-degree-days, fitted on three summers of history.

It passes every check a professional review would apply:

| check | result |
|---|---|
| out-of-sample holdout on an unseen summer | **R2 0.747 - 0.757** across regimes |
| residual diagnostics | clean by construction - the historical DGP is exactly this model |
| calibration on history | exact |
| reconciliation of segment forecasts to the total | exact |
| plausible, defensible narrative | "our model has held up for three years" |

And it is wrong about the target summer by **+0.32 to +0.64 kW (23 to 45 sd)**, recommending
`procure` on two regimes where the truth is `defer`.

## Why it stays wrong

The mechanism it omits **did not exist during the period it was validated on**. There is no
historical diagnostic - no residual plot, no holdout, no cross-validation fold - that can reveal a
tariff response in data collected before the tariff existed. The only evidence that can is the
pilot, which lies outside the model's training frame entirely.

## Consequence for the verifier

A G36 verifier must **not** grant credit for historical fit quality, and must not rely on coherence
checks for separation. Specifically:

- a "backtest R2 above threshold" check would pass the incumbent;
- a "segment forecasts reconcile to total" check would pass the incumbent;
- a "residuals are white" check would pass the incumbent.

Separation must come from **numeric comparison of the target-regime forecast against latent truth**,
plus the decision. The same conclusion G34 and G35 reached, arrived at independently here.

## A second coherent-wrong case

`W8_selection_fixed_only` is subtler and more valuable. It produces a professionally reasoned
analysis that explicitly identifies opt-in bias, corrects it, and documents the correction. Its
write-up would read as *more* rigorous than the correct answer's, because it names a real problem and
shows its work. It is wrong by 11.6 sd on `hidden_c` and defers capacity that is genuinely needed.
