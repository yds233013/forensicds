# G36 cheap-solve panel

Each shortcut scored on how many of the five regimes' decisions it reproduces. Truth: **p p d p d**.

| shortcut | visible | hidden_a | hidden_b | hidden_c | hidden_d | decisions |
|---|---|---|---|---|---|---|
| C1 historical model output | 3.329 | 3.308 | 3.286 | 3.264 | 3.345 | 3/5 |
| C3 last value | 2.992 | 3.012 | 3.013 | 3.103 | 3.017 | 3/5 |
| C4 seasonal naive | 2.995 | 3.025 | 3.014 | 3.063 | 3.030 | 3/5 |
| C6 historical mean | 2.995 | 3.025 | 3.014 | 3.063 | 3.030 | 3/5 |
| **C7 pilot mean** | 2.988 | 3.180 | 2.866 | 2.706 | 2.615 | **4/5** |
| C9 constant "procure" | - | - | - | - | - | 3/5 |
| C10 constant "defer" | - | - | - | - | - | 2/5 |
| C11 largest segment only | 3.344 | 3.328 | 3.266 | 3.223 | 3.326 | 3/5 |
| C13 latest period | 2.992 | 3.012 | 3.013 | 3.103 | 3.017 | 3/5 |
| C15 intervention flag (flat 10 % rule of thumb) | 2.695 | 2.723 | 2.712 | 2.757 | 2.727 | 2/5 |
| C17 aggregate pilot pre/post | 2.480 | 2.473 | 2.379 | 2.271 | 2.102 | 2/5 |
| C24 linear extrapolation | 2.994 | 2.997 | 3.009 | 3.137 | 3.005 | 3/5 |

## Verdict — **PASS**, with the strongest shortcut named

**No shortcut reproduces all five decisions.** The best is `C7_pilot_mean` at 4/5.

`C7` deserves attention because it is the closest thing to a dangerous shortcut in the design. Its
forecast *values* are: 2.988 vs truth 2.998 on `visible` (error 0.010, inside 1 sd), but 3.180 vs
2.975 on `hidden_a` (error 0.205) and 2.706 vs 2.943 on `hidden_c` (error 0.237). It is
near-perfect on the extract the analyst can see and badly wrong on two hidden regimes - which is
precisely why hidden regimes exist, and why the graded set must include the forecast value and not
only the decision.

Under a rule that every regime must pass, C7 fails. But an implementation that graded only the
visible extract would be solved by taking the pilot average, and that must not happen.

## Constant decision — **PASS**

Constant "procure" 3/5, constant "defer" 2/5. The split is driven by structural parameters
(response magnitude, heat damping), not by seed selection; no seeds were screened for outcome.
