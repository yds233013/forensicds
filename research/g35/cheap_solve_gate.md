# G35 cheap-solve gate

Each shortcut is scored on whether it reproduces the **launch decision** in all four regimes, and on
how far its number sits from `tau_policy`.  Truth decisions: **L h h L**.

| shortcut | visible | hidden_a | hidden_b | hidden_c | decisions | verdict |
|---|---|---|---|---|---|---|
| C5 constant launch | - | - | - | - | L L L L | **2/4** fails |
| C6 constant hold | - | - | - | - | h h h h | **2/4** fails |
| C4 published dashboard number | 0.194 | 0.240 | 0.013 | 0.245 | L L h L | **3/4** fails |
| C10 one saturation level (25% arm) | 0.247 | 0.423 | 0.016 | 0.338 | L L L L | **2/4** fails |
| C16 treatment counts | 0.426 | 0.433 | 0.392 | 0.409 | L L L L | **2/4** fails |
| C17 market-size correlate | -0.047 | -0.084 | -0.053 | -0.164 | h h h h | **2/4** fails |
| C7 largest markets only | 0.041 | 0.013 | 0.005 | 0.070 | L h h L | 4/4 - **not a shortcut** |
| C3 saturation-outcome slope | 0.043 | 0.007 | 0.006 | 0.064 | L h h L | 4/4 - **not a shortcut** |

## Result **PASS**, with an important reclassification

No shortcut that **ignores the saturation structure** solves the task.  Constant decisions, the
published dashboard number, a single saturation arm, treatment counts and market size all fail.

Two entries on the brief's list turned out **not to be shortcuts at all in this design**, and are
reclassified rather than counted as passes:

- **C3 "treatment share vs outcome correlation"** is a weighted regression of block outcome on assigned
  saturation.  Because the estimand *is* the saturation contrast and the response is close to linear
  over `[0,1]`, its slope is a legitimate crude estimator of `tau_policy`.  It is family V2 in
  rougher clothing.
- **C7 "largest markets only"** is the valid contrast computed on a subsample.  Wasteful, not wrong.

## What this tells us about where the difficulty sits

The honest reading: **once an analyst recognises that assigned saturation is the variable that matters,
several quite different analyses land close to the truth.**  The difficulty of G35 is concentrated in
the recognition step and in keeping the three objects apart - not in estimator craft.

That is the same shape as G34, whose baseline came in at 2/3.  It is recorded here as the principal
difficulty risk (see `adversarial_review.md` and `build_recommendation.md`) rather than discovered
after a baseline.
