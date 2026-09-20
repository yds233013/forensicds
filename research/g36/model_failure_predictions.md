# G36 pre-registered model failures

**Written before implementation and before any baseline**, as the G35 experience requires. G35's
K17 prediction proved correct and recording it in advance is what made the 3/3 outcome a measurement
rather than a surprise.

## Predicted failure modes, in expected order of frequency

1. **Recognises the tariff changes behaviour, then simply retrains on recent data.** Produces `W2`.
   No tariff exists in the training window, so retraining changes nothing material. Error 45 sd.
2. **Takes the pilot's headline reduction and applies it to the estate.** Produces `W7`. The single
   most likely failure: the pilot has one salient number and it is the wrong one. Error 27 sd,
   three wrong decisions.
3. **Corrects the opt-in selection, stops there.** Produces `W8`. The *sophisticated* failure - it
   names a real problem, fixes it, and documents the fix. Error 11.6 sd, one wrong decision.
4. **Notices the heat dependence, ignores who volunteered.** Produces `W9`. Error 10.6 sd, two wrong
   decisions.
5. **Forecasts the pilot population rather than the estate.** Produces `W10`.
6. **Reweights pilot outcomes rather than pilot effects.** Produces `W11` - covariate-shift reflex
   applied to an effect.
7. **Reports excellent backtest performance as evidence of validity.** The incumbent holds out at
   R2 0.75; a model that stops there has validated the wrong thing.
8. **Correct decision from a materially wrong forecast.** On `visible`, several wrong methods reach
   `procure` correctly while being 0.3 kW out. A verifier that graded only the decision would pass
   them.
9. **Never tests the transport assumption.** Produces a number without the response-vs-CDD plot or
   the opt-in-vs-population comparison - the two diagnostics that distinguish the correct answer.
10. **Finds one coherent specification and stops.** No placebo period, no leave-one-segment-out, no
    positivity check.

## What would count as a genuine solve

All of: stable curve from history; causal response from the pilot's control arm; response fitted
against CDD; reweighted to the population segment mix; evaluated at target weather; recomposed and
aggregated; compared to the gate. Plus at least one falsification attempt.

## Honest expectation

G34 scored 2/3 and G35 scored 3/3, both on "famous concept, one recognition step". G36's measured
recognition-vs-execution property is materially stronger - each insight alone leaves 10-12 sd - so a
lower pass rate is expected. **But that is a prediction, not a result**, and the same prediction for
G35 was right about the mechanism while still landing at the top of its range. I would put the
plausible band at **0/3 to 2/3** and would not be surprised by 3/3 if the model happens to reach for
both transports at once.
