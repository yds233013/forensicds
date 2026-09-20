# G36 build recommendation

# RECOMMENDATION: **A — BUILD G36**

## Why

G36 passes the gate G35 failed, by a measured and decisive margin. Handing the analyst either key
insight for free still leaves **10-12 sd of error and at least one wrong capacity decision**; only
holding both insights *and* executing a four-ingredient decomposition reaches 0.9 sd and five correct
decisions. That is the property the whole phase was built to find, and it is the difference between
a vocabulary benchmark and a scientific one. Every other gate also passes on measurement rather than
assertion: 45 sd of mechanism strength, a coherent incumbent model that holds out at R2 0.75 and is
still wrong by 45 sd, a same-history/different-future pair whose backtests differ by 2.6 % while
their decisions are opposite, no shortcut above 4/5, and decision margins of 3.5-14.9 sd.

## Kill criteria

| | criterion | verdict |
|---|---|---|
| K1 | target not identifiable | **survives** - pilot + weather forecast + customer master identify it without future outcomes |
| K2 | **recognition hands over estimator** | **survives** - 10-12 sd remains after either insight |
| K3 | correct-table version trivial | **survives** - perfect table handed over, 45 sd separation remains |
| K4 | historical model close enough | **survives** - 45 sd, 2 wrong decisions |
| K5 | latest-window close enough | **survives** - identical to historical, no tariff in the window |
| K6 | simple reweighting works | **survives** - reweighting outcomes (`W11`) errs 43 sd; reweighting effects alone (`W8`) errs 11.6 sd |
| K7 | pilot mean works | **survives** - `W7` errs 27 sd, 3 wrong decisions; `C7` reaches 4/5 decisions but misses values by up to 0.24 |
| K8 | constant decision works | **survives** - 3/5 and 2/5 |
| K9 | valid estimators disagree | **survives as measured**, but see the risk below |
| K10 | coherent wrong passes | **survives** - incumbent holds out at R2 0.75 and errs 45 sd |
| K11 | mechanism weak | **survives** - 45 sd |
| K12 | generator-only truth required | **survives** - evidence audit clean, 6 facts explicitly refused |
| K13 | unrealistic pilot | **survives** - opt-in tariff trials with randomisation inside are standard utility practice |
| K14 | collapses into G08 | **survives** - no vintage problem; the correct-table gate proves it |
| K15 | collapses into G05 | **survives** - graded object is an operational level, not an effect; `W7` (the pure effect) errs 27 sd |
| K16 | generic distribution shift | **survives** - covariate-shift reweighting is `W11`, wrong by 43 sd |
| K17 | one textbook technique | **survives** - two orthogonal transports plus a stable/unstable decomposition |
| K18 | only one implementation accepted | **partially open** - see risk 1 |
| K19 | threshold drives difficulty | **survives** - margins 3.5-14.9 sd |
| K20 | representation leaks regime | **survives** - row order \|r\| <= 0.031; histories statistically indistinguishable |
| K21 | difficulty is ETL | **survives by construction** - the panel runs on perfect inputs |
| K22 | needs huge data | **survives** - 6 000 households x 60 days x 4 summers is a few MB |

## The three risks I would not paper over

**1. The three "valid routes" are one estimand written three ways.** They agree to 0.0000 because
they are algebraic rearrangements, not independent methods. The brief asks for two genuinely
legitimate routes and the simulation does not yet demonstrate that. Implementation must build and
measure a hierarchical/partial-pooling estimator and a regression-with-interaction form, and if they
disagree materially, K9 is live and the accepted set and tolerance both need revisiting. **This is
the single most important open item.**

**2. `C7_pilot_mean` reaches 4/5 decisions.** Its forecast is within 1 sd of truth on the *visible*
extract and badly wrong on two hidden ones. That is exactly what hidden regimes are for, but it
means the graded set must include the forecast value and the hidden extracts must carry equal
weight. An implementation that graded only the visible extract would be solvable by averaging the
pilot.

**3. `hidden_a` and `hidden_c` have 3.5 sd margins.** Comfortable versus G34's 0.14 sd defect, but
the tightest in the set. Implementation should re-measure `SE_REF` from the real generator at full
scale before fixing any tolerance, rather than inheriting these numbers.

## S0-S9 prediction

| stage | predicted load |
|---|---|
| S0 incident recognition | low-medium - the memo states the dispute plainly |
| S1 evidence discovery | **medium-high** - the pilot enrolment log must be found and joined to the customer master |
| S2 operational reconstruction | **low, deliberately** - the correct-table gate shows separation does not come from here |
| S3 target/estimand | **HIGH** - a level under a future policy, not an effect |
| S4 statistical object | **HIGH** - stable/unstable decomposition |
| S5 identification | **HIGH** - two orthogonal transports |
| S6 estimator | medium - several arithmetic forms work once the object is right |
| S7 falsification | **HIGH** - response-vs-CDD and opt-in-vs-population are the two checks that separate correct from `W8`/`W9` |
| S8 uncertainty | not graded initially |
| S9 decision | low - a stated numeric gate |

**Difficulty spans S3-S7**, which is the brief's stated preference and broader than G35 (S3-S5).

## Estimates

| item | estimate |
|---|---|
| implementation complexity | **medium-high**, comparable to G35. Generator ~280 lines stdlib-only, oracle ~140, verifier ~280, 3 hidden fixtures, ~25 mutations |
| build + validation | one working session |
| `harbor check` | 1-2 invocations, **$0.45-0.95** |
| 3-trial Gemini baseline | **$0.15-0.25** (G34 $0.124, G35 $0.188) |
| total to freeze | **~$0.45-0.95**; baseline separately authorised |
