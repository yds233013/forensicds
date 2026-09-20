# G35 adversarial review

By reasoning, code and simulation.  **No model call was used**, in accordance with the brief.

## Attack 1 - "this is just remember SUTVA"  (K17)  **PARTIALLY LANDS**

*The attack:* marketplace interference is one of the most written-about topics in industrial
experimentation.  Any competent analyst has met "cluster randomise to handle interference".  The task
may reduce to recognising a famous keyword.

*Defence:* recognition is necessary but demonstrably not sufficient.  `W5` and `CW1` are written by an
analyst who has fully accepted interference, measured it, and still reports the wrong object - errors
of 0.30-0.50 and -0.029 respectively, with `CW1` flipping the visible decision.  `W3`, the textbook
"block fixed effects" fix, is the **worst** analysis in the panel (0.31-0.46).  Reaching for the
standard remedy actively hurts.

*Residual risk:* real.  The cheap-solve gate shows that once saturation is recognised as the operative
variable, several different analyses land close.  **The difficulty is concentrated in one recognition
step.**  This is the same shape as G34, which scored 2/3.  Recorded as the principal risk, not
dismissed.

## Attack 2 - "one formula solves it"  (K18)  **DEFEATED, by design change**

*The attack:* `mean(pi=1) - mean(pi=0)` is a single line.

*Defence:* it yields only Q1.  Q2 and Q3 require the 50% arm and different contrasts, and the three
objects differ by up to two orders of magnitude.  This is precisely why the graded set is three objects
plus the decision rather than the decision alone - a change made *because* of the G34 baseline, where
grading a single object would have let a wrong analysis through.

## Attack 3 - "the intermediate saturation arms are decorative"  (K6)  **DEFEATED, by design change**

Under a Q1-only grading they would be, and the honest answer would have been to cut them or drop the
design.  Grading Q2 and Q3 makes the 50% arm load-bearing.  The 25% and 75% arms remain support for
the saturation-curve family (V2) and for a falsification check; they are not separately graded.

## Attack 4 - "the correct estimator cannot decide"  **LANDED, then fixed**

The first regime set produced decision margins of **0.14 sd and 0.51 sd** for the correct estimator -
it could not tell launch from hold.  This is exactly G34's `hidden_a` defect.  Fixed by choosing
operating points on the physics of the generator (margins now 3-13 sd), before any model was run.
Had this not been caught, the task would have shipped ungradeable.

## Attack 5 - "valid estimators disagree"  (K11)  **LANDED, then fixed**

With `cap_city_sigma = 0.15`, only the design regression decided all regimes correctly; the natural
0%-vs-100% contrast failed one.  A task that punishes the most obvious correct analysis is broken.
Fixed by shrinking nuisance heterogeneity rather than by blessing one estimator.  Worst valid-family
error is now 0.0048 with unanimous decisions.

## Attack 6 - "the wrong methods are strawmen"  **DEFEATED**

`W1` is the actual experiment dashboard.  `W3` is the standard textbook remedy.  `W5` is written by
someone who understood the problem.  `CW1` correctly measures the entire mixed experiment and is wrong
only about which saturation the business asked about.  None is a strawman; the weakest of them is the
*most sophisticated* one.

## Attack 7 - "interference is an artefact of proportional rationing"  **DEFEATED**

The zero-sum property is not tuned: under proportional rationing, when every merchant carries the same
dispatch weight the allocation is identical regardless of the weight's value.  Any rationing rule that
is invariant to a common rescaling of weights gives the same limit.  The result is structural.

## Attack 8 - "hidden_b is a broken regime"  **DEFEATED, reclassified**

In `hidden_b` the naive analysis is nearly right.  That is not a defect: slack capacity means no
rationing means no interference.  It is the regime that distinguishes a principled method from a
memorised correction, and its separation comes from Q2/Q3 rather than Q1.

## Attack 9 - "W10 and W14 are padding"  **W10 LANDS**

`W14` bites once city sizes vary realistically (errors -0.011 to -0.040).  `W10` does not: its errors
(-0.015 to -0.000) are comparable to the valid families' and on `hidden_c` smaller.  **Recorded as an
ineffective trap.**  It is kept in the taxonomy as a documented negative, not counted toward
separation.

## Attack 10 - "it collapses into G05 or G24"  **DEFEATED**

See `cross_task_matrix.md`.  G05's difficulty is identifying a counterfactual trend from a staggered
rollout; here treatment is randomised and identification of the naive object is beyond dispute - the
problem is that the naive object is the wrong one.  G24 reconstructs logging propensities for actions
that were never randomised; here assignment probabilities are known by design and no propensity is
estimated.

## Attacks that failed to find anything

- **Leakage**: all probes within 0.06 of zero, AUC within 0.05 of chance.
- **Constant decision**: 2/4 either way.
- **Data-cleaning shortcut**: separation survives a perfect analysis table.
- **Published number**: 3/4.
