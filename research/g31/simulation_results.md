# G31 Phase-0 simulation results

**The gate was abandoned after one of four regimes.** Not because it failed — it passed, convincingly — but
because the independent adversarial review (`adversarial_review.md`) demonstrated that the world being measured is
defective in ways the gate cannot see. Continuing to measure a broken generator would have been waste.

Everything below is measured. Nothing is projected.

## 1. What the gate measured (regime `visible`, 10 calibration + 20 validation worlds)

Tolerance rule, pre-registered: τ = 3.5 × calibration RMSE of the **least efficient accepted estimator**, per
quantity. True deltas (validation mean): ecom_cnp **+0.1264**, marketplace **−0.1043**, travel **+0.1202**.
τ(Δ) = 0.042 / 0.050 / 0.041.

| Method | Kind | RMSE(Δ) | Worst ratio | Passes all quantities | Decision correct |
|---|---|---|---|---|---|
| A1 Horvitz–Thompson | accepted | 0.0116 | 0.83 | **20/20** | 20/20 |
| A2 post-stratification | accepted | 0.0114 | 0.82 | **20/20** | 20/20 |
| A3 outcome regression | accepted | 0.0075 | 0.53 | **20/20** | 20/20 |
| A4 mature cohort only | accepted | 0.0134 | 0.89 | **20/20** | 20/20 |
| W1 complete case | wrong | 0.0935 | 4.26 | 0/20 | 0/20 |
| W2 30-day cutoff | wrong | 0.1950 | 8.38 | 0/20 | 0/20 |
| W3 mature settled only | wrong | 0.1941 | 8.37 | 0/20 | 0/20 |
| W4 reviewed only | wrong | 0.5106 | 20.47 | 0/20 | 0/20 |
| W5 blocked = fraud | wrong | 0.0449 | 2.01 | 0/20 | **20/20** |
| W6 unlabelled = legit | wrong | 0.0935 | 4.26 | 0/20 | 0/20 |
| W7 IPW on v6 band | wrong | 0.0965 | 4.19 | 0/20 | 18/20 |
| W8 pooled segments | wrong | 0.1079 | 4.96 | 0/20 | 0/20 |
| W9 holdout only | wrong | 0.4408 | 20.47 | 0/20 | 0/20 |
| **W10 count recall** | *labelled wrong* | **0.0092** | **0.59** | **20/20** | 20/20 |

On its face this is a strong gate: four structurally different accepted estimators at 20/20 with worst ratios
0.53–0.89, and nine wrong analyses rejected at 2.0–20.5 τ, including two (W5, W7) that reach the correct decision
while failing every quantity — the decision-nontriviality property the brief requires.

**It is also misleading, and the next section is why.**

## 2. What the adversarial review found, and what I independently verified

I re-tested each decisive claim myself rather than accepting the review's numbers.

### 2.1 The task is defeated by a heuristic that uses no labels at all — **CONFIRMED**

`g31_sim.py` draws value as `v = base · mult_g^{Y*}` with `base ⟂ z`. Consequently the **gross transaction value**
summed over a model's top-k is a monotone function of that model's precision at k, and therefore of its recall.
Summing gross value — no chargebacks, no bypass, no weights, no maturity horizon — recovers the decision:

| Regime | ecom_cnp | marketplace | travel |
|---|---|---|---|
| visible | v7 = truth ✓ | v6 = truth ✓ | v7 = truth ✓ |
| v7_wins_everywhere | v7 ✓ | **v7 ✓** (the flip) | v7 ✓ |
| high_prev | v7 ✓ | v6 ✓ | v7 ✓ |

**9/9 in my test; 15/15 in the reviewer's independent 5-world test, including the regime-D decision flip.** This
alone is disqualifying: the entire observation-process reconstruction can be skipped.

### 2.2 `W10_count_recall` is not a wrong method — **CONFIRMED**

`fraud_value_mult` is a *within-segment constant*, so it cancels in a ratio. Measured difference between
value-weighted and count Δ: **+0.0008 / +0.0019 / −0.0040** against effects of 0.10–0.12. The gate table above
shows the consequence: W10 passes 20/20 with RMSE 0.0092, **better than three of the four accepted estimators.**
The task's designed decision-correct/analysis-wrong case does not exist.

### 2.3 The delay / censoring mechanism is inert — **CONFIRMED**

`delay` is drawn independently of `Y*`, `z`, `v` and the scores, so censoring removes a random fraction of
chargebacks from numerator and denominator alike and cancels in the ratio. Replacing the estimated maturity
horizon (43 / 87 / 65 days) with a deliberately wrong one:

| Maturity horizon used | shift in Δ, ecom | marketplace | travel |
|---|---|---|---|
| T = 0 (no handling at all) | +0.0028 | +0.0015 | −0.0058 |
| T = 30 (the condemned legacy cutoff) | −0.0009 | +0.0023 | −0.0055 |

Every shift is below the 0.010 adopt bar and below the accepted estimators' own RMSE. **The second of the three
mechanisms does not bite.** W2 and W3 fail for a different reason — they evaluate on the settled population — not
because of maturity.

### 2.4 The selective-verification mechanism is inert — **CONFIRMED**

`released = reviewed AND Y*=0` by construction, so reviewed-and-released rows contain **0 fraudulent rows of
12,049** and contribute exactly zero to both numerator and denominator of a fraud-value ratio. Including or
excluding them changes nothing. **The third mechanism does not bite either.**

### 2.5 The evaluation threshold is degenerate — **CONFIRMED**

`eval_block_rate` equals `block_rate + review_rate` to machine precision in **15 of 15** (segment, regime) cells.
The v6 evaluation threshold therefore *is* the band boundary, so `1[s6 ≥ τ_v6] ≡ (band ≠ ALLOW)`. This is why W4
and W9 return `recall_v6 = 1.000000` exactly and self-refute rather than failing for their intended reason.

### 2.6 Consequence

The design's central claim — *"fixing any two of the three mechanisms still leaves a biased answer"*
(`dgp_design.md` §5) — **is false as built.** There is one mechanism: inverse-probability weighting on the logged
bypass. The other two are decoration. A2 and A3 avoid explicit propensities but rest on the same single
identification, so the claim that G31 is "not an IPW task" does not survive either.

## 3. The methodological finding

**The Phase-0 gate protocol has a structural blind spot, and this is the second task where it mattered.**

The gate evaluates *estimators against truth*. It cannot detect a solver that never estimates anything — it has
no representation of "rank by score and sum the value". G05's gate had the same gap: it never tested a
heuristic either, and G05's baseline later showed the designed attractors never fired.

A gate that only measures estimator separation will certify a task that a heuristic defeats. **Any future Phase-0
gate should include an explicit cheap-solve panel — label-free heuristics, constant answers, and single-artefact
readings — scored the same way as the wrong analyses.** That is a change to the benchmark's method, and it is the
most transferable thing this turn produced.

## 4. Cost

No model was run. No API credits were spent. All compute was local numpy: roughly 40 pilot worlds across tuning,
refutation and one gate regime, at ~11 s per 1.31 M-row world.
