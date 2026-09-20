# G35 build recommendation

# RECOMMENDATION: **A - BUILD G35**

Every kill criterion was tested.  Two were hit during design and fixed by changing the design before
any model was run; one (`K17`) is a genuine residual risk and is documented rather than explained away.

---

## 1. Gate results

| gate | result |
|---|---|
| statistical validity (truth vs latent generator) | **PASS** - valid families unbiased to 0.005 |
| mechanism strength | **PASS** - naive analysis wrong by **4.2x to 38.7x** the true effect |
| correct-data-table | **PASS** - separation survives a perfect analysis table |
| cheap solve | **PASS** - no structure-ignoring shortcut reaches 4/4 |
| representation leakage | **PASS** - all probes within 0.06 of zero, AUC within 0.05 of chance |
| graded-fact evidence audit | **PASS** - 6 facts graded, 6 explicitly refused |
| coherent-but-wrong | **PASS** - all three coherent analyses miss badly, two flip a decision |
| constant decision | **PASS** - 2/4 either way |
| valid-family agreement (K11) | **PASS after fix** - worst family error 0.0048, unanimous decisions |
| decision margins | **PASS after fix** - 3 to 13 sd from the gate |

## 2. Kill criteria

| | criterion | verdict |
|---|---|---|
| K1 | naive A/B close enough | **survives** - 4.2x-38.7x off on three regimes |
| K2 | cluster-robust SE fixes it | **survives** - identical point estimate by construction |
| K3 | direct ~ deployment effect | **survives** - 0.006 vs 0.506 on `hidden_a` |
| K4 | interference too weak | **survives** - it is most of the measured effect |
| K5 | full-rollout effect not identified | **survives** - a 100% arm exists; nothing is extrapolated |
| K6 | one saturation level suffices | **survives after design change** - Q2/Q3 need the 50% arm |
| K7 | constant decision works | **survives** - 2/4 |
| K8 | published aggregate solves it | **survives** - 3/4 |
| K9 | market size predicts decision | **survives** - 2/4, corr -0.05 to -0.16 |
| K10 | correct-table separation lost | **survives** |
| K11 | valid estimators disagree | **survives after design change** |
| K12 | unrealistic parameters | **survives** - fulfilment 70-95%, effects 0.6-5.9 points |
| K13 | interference group ambiguous | **survives** - the city-day dispatch pool is an operational fact |
| K14 | hidden truth needs the generator | **survives** - 6 facts explicitly refused |
| K15 | collapses into G05 | **survives** - treatment is randomised; identification is not the battleground |
| K16 | collapses into G24 | **survives** - assignment probabilities known; no propensity estimated |
| K17 | merely "remember SUTVA" | **PARTIALLY LANDS - see s4** |
| K18 | one textbook formula solves it | **survives after design change** - three objects |
| K19 | coherent wrong analysis passes | **survives** - CW1/CW2/CW3 all fail |
| K20 | requires a particular implementation | **survives** - four families, no library requirement |

## 3. Two design failures caught, and what they cost

Both are the G34 lessons repeating, and both would have shipped an unusable task.

1. **The correct estimator could not decide two regimes** (margins 0.14 and 0.51 sd).  Identical in
   kind to G34's `hidden_a`, where the correct estimator exceeded its own tolerance.  Fixed by
   selecting operating points on the generator's physics.
2. **Valid estimators disagreed** (K11): with realistic city heterogeneity, only the design regression
   decided all regimes; the natural 0%-vs-100% contrast failed one.  Fixed by shrinking nuisance
   variance so the task tests the *estimand*, not variance reduction.

A third, smaller failure was in my own harness: truth and experiment drew different populations, which
manufactured a phantom bias in every valid estimator.  Fixed before any gate was believed.

## 4. The principal risk, stated plainly  (K17)

**Marketplace interference is famous.**  The cheap-solve gate shows that once an analyst recognises
assigned saturation as the operative variable, several different analyses land within 0.007 of the
truth.  The difficulty is concentrated in one recognition step plus keeping three objects apart.

This is the same shape as G34 - a famous concept (competing risks), one recognition step, then
straightforward implementation - and G34's baseline came in at **2/3** on `gemini-3-flash-preview`.

**Honest prediction: G35 will land in a similar band, plausibly 1/3 to 3/3.**  I am recording this
before any baseline rather than discovering it after.

Three reasons it is still worth building:

1. **The sophisticated wrong answers are genuinely tempting.**  `W3` - block fixed effects, the
   textbook remedy - is the *worst* analysis in the panel.  `CW1` correctly measures the entire mixed
   experiment and flips the visible decision.  Recognising interference does not save you.
2. **The `hidden_a`/`hidden_c` pair cannot be separated by any naive route.**  Nearly identical naive
   lifts (0.240 vs 0.245), opposite decisions, truths differing 9x.
3. **The failure is expensive and realistic** - shipping a feature whose entire measured benefit was
   displacement is a real and recurring industrial error.

## 5. Expected model failures, pre-registered

1. Notices interference, reports the direct effect as the rollout effect (`W5`).
2. Applies block fixed effects, believes the problem solved, lands on the most contaminated object
   in the design (`W3`).
3. Measures the mixed experiment correctly and reports it as the policy effect (`CW1`) - the most
   sophisticated failure available.
4. Correctly estimates direct and spillover, then composes them wrongly (`CW2`).
5. Conditions on realised adoption rather than assigned saturation (`W10`).
6. Averages markets unweighted when couriers are consumed by orders (`W14`).
7. Produces a coherent analysis with reconciled totals and performs no falsification (`CW3`).
8. Gets the launch decision right on the visible regime from the wrong effect size, and fails the
   hidden regimes.
9. Reports `hidden_b` with an interference correction applied as a slogan, misstating the magnitude.
10. Declares the full-rollout effect unidentified, having missed the 100% arm.

## 6. S0-S9 placement

| stage | load |
|---|---|
| S0 incident recognition | medium - Courier Ops state the objection in business language |
| S1 evidence discovery | medium - the assignment log must be found and understood |
| S2 operational-state reconstruction | **low** - deliberately so; the correct-table gate proves separation does not come from here |
| S3 target/estimand specification | **HIGH** - which saturation is the business asking about |
| S4 statistical object construction | **HIGH** - three objects from one experiment |
| S5 identification / assumptions | **HIGH** - which arms identify which object |
| S6 estimator implementation | low - once the object is chosen, several routes work |
| S7 falsification | medium - the spillover curve is the natural check |
| S8 uncertainty | low-medium - clustered inference at the block level |
| S9 business decision | medium - a stated numeric gate |

Confirmed hypothesis: **G35 loads S3-S5**, slightly earlier in the chain than the brief's S4-S5 guess,
because choosing *which saturation the question is about* is the first and hardest step.

## 7. Realism

An experimentation team at a delivery marketplace could meet this exactly.  Randomised-saturation
switchbacks over city-days are standard practice for dispatch changes; "the pilot lift was displacement"
is a routine and expensive dispute.  Scale: 60 cities x 28 days = 1 680 blocks, ~45 merchants per city,
roughly 75 000 merchant-day rows - a few megabytes, large enough to be real and small enough not to
waste agent time.  Fulfilment rates of 70-95% and effects of 0.6-5.9 points are ordinary.

## 8. Ambiguity

One genuine ambiguity, resolved in the task text and not by the verifier: **ITT versus effect on
adopters.**  Deployment inherits imperfect adoption, so the contract states the graded object is the
effect of making the feature available, compared on assigned saturation.

## 9. Biggest risk

**K17.**  Not validity - the task is scientifically sound and every measurable gate passes.  The risk
is that its difficulty rests on one famous recognition, which a capable model may make immediately.
The mitigation is the three-object graded set, which forces the agent to demonstrate the distinction
rather than name it.

## 10. Build estimate

| item | estimate |
|---|---|
| complexity | **medium-high** - comparable to G34.  Generator ~250 lines, oracle ~120, verifier ~260, hidden fixtures 3, mutation suite ~20 distinct cases |
| build + validation time | 1 working session, as G34 |
| `harbor check` | 1 invocation, **~$0.42** (G34's actual) |
| Gemini baseline, if later authorised | 3 sequential trials, **~$0.12-0.20** (G34's actual was $0.124406) |
| total model spend to freeze | **~$0.42**; baseline is a separate, separately-authorised decision |

## 11. What I did NOT do

No candidate directory, no Harbor task, no `harbor check`, no Gemini, no Claude benchmark run, no model
credits.  The adversarial review is reasoning, code and simulation only, as required.
