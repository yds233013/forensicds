# G36 recognition-vs-execution gate

**The gate that exists because G35 failed it.**

G35's post-mortem: once the model said "saturation is the operative variable", the correct analysis
was `mean(pi=1) - mean(pi=0)`. Recognition handed over the estimator, and Gemini scored 3/3.

## Method

Hand the analyst an insight **for free**, then measure the best analysis that insight alone
supports. Errors are in units of the accepted estimator's sampling sd (0.0142 kW).

| insight given away | visible | hidden_a | hidden_b | hidden_c | hidden_d | **worst** | wrong decisions |
|---|---|---|---|---|---|---|---|
| **H0** nothing | 0.2 | 3.5 | 13.6 | 8.5 | 22.7 | **22.7 sd** | **2 / 5** |
| **H1** "the pilot's response does not transport to the population" | 1.1 | 1.0 | 5.1 | 11.6 | 0.5 | **11.6 sd** | **1 / 5** |
| **H2** "the response depends on temperature" | 6.1 | 10.6 | 5.3 | 5.3 | 7.9 | **10.6 sd** | **2 / 5** |
| **H1 + H2** both | 0.9 | 0.2 | 0.5 | 0.7 | 0.9 | **0.9 sd** | **0 / 5** |

## Verdict: **PASS**

Giving away either insight on its own still leaves an error of **10-12 sd** and at least one wrong
business decision. Only holding both *and* executing the decomposition correctly reaches 0.9 sd and
five correct decisions.

Concretely, the analyst who is told H1 and acts on it produces `W8_selection_fixed_only`: reweight
the pilot response to the population segment mix, then apply it. That is a real improvement over
doing nothing - and on `hidden_c`, where response collapses in heat, it is wrong by 11.6 sd and
recommends deferring capacity that is actually needed.

The analyst told H2 produces `W9_temperature_fixed_only`: evaluate the response curve at the target
summer's weather, but keep the pilot's over-responsive population. Wrong by 10.6 sd and wrong on two
regimes.

## Why the two insights are orthogonal

They are different physical facts about different objects:

- **H1 is about *who*.** Opt-in households own smart thermostats and controllable loads; the
  population does not. Fixing it means reweighting an *effect* by the distribution of an effect
  modifier.
- **H2 is about *when*.** The pilot summer was mild (CDD 8.6) and the target is forecast hot
  (CDD 12.4); response fades as air conditioning saturates. Fixing it means evaluating a fitted
  response *curve* at a different point.

Neither implies the other, and no single reweighting does both. This is the structural property the
domain tournament weighted x3 to find.

## Work remaining after full recognition

Even an analyst holding both insights must still:

1. estimate the stable weather-load relationship per segment from history;
2. estimate the causal response per segment from the pilot, using the control arm;
3. fit how that response varies with CDD, over the pilot's own CDD range;
4. reweight segment responses to the population mix;
5. evaluate the curve at the target summer's forecast weather;
6. recompose stable x (1 - transported response) and aggregate;
7. compare against the capacity gate.

Recognition unlocks steps 4 and 5. Steps 1-3, 6 and 7 remain in every case.
