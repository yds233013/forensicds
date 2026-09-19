# G31 legitimate estimator families

Four families, deliberately spanning different statistical machinery, so that a verifier tolerance cannot reward
one implementation recipe. Code: `g31_estimators.py`, dict `ACCEPTED`.

All four share exactly one requirement — they must handle **all three** missingness mechanisms — and differ in
everything else: weighting vs stratification vs modelling, and how much data they are willing to discard.

## A1. Horvitz–Thompson on the bypass holdout

**Machinery:** inverse-probability weighting.

```
labelled set : mature ALLOW rows  (weight 1)
             + mature holdout rows in REVIEW/BLOCK  (weight 1/q_band,g)
R̂ = Σ w·Y·v·1[s ≥ τ] / Σ w·Y·v
```

- **Assumptions:** I1 (randomised, logged bypass), I3 (maturity depends only on elapsed time), I5 (overlap).
- **Discards:** investigator determinations, and reviewed-and-released rows (their settlement is a deterministic
  function of `Y*`).
- **Expected finite-sample behaviour:** unbiased up to the usual ratio-estimator bias; variance dominated by the
  holdout count in the BLOCK band, which is the scarcest cell.

## A2. Post-stratification / direct standardisation

**Machinery:** cell means scaled by known population counts. **No individual weights at all.**

```
for each segment × v6-decile cell c:
    mean fraud value in c        ← estimated from the labelled rows in c
    mean captured fraud value    ← same
    scale both by N_c, the known population size of the cell
R̂ = Σ_c N_c · mean_captured_c / Σ_c N_c · mean_fraudvalue_c
```

- **Assumptions:** I1, I3, I5 — plus that the cells are fine enough that within-cell labelling is ignorable.
- **Why it matters for the design:** it reaches the same answer without ever computing a propensity. Its existence
  is the evidence that G31 is not "an IPW task".
- **Expected behaviour:** near-identical to A1 in this DGP, because the cell structure follows the band structure.
  Slightly more robust if the bypass rate were mis-stated; slightly less efficient with sparse cells.

## A3. Outcome regression (imputation)

**Machinery:** fit `P(Y* = 1 | s6, s7, log v)` on the rows where labelling is ignorable, predict for **every** row,
aggregate the predictions.

```
fit on : mature ALLOW + mature holdout rows, weighted by 1/q
predict: all rows in the segment
R̂ = Σ p̂·v·1[s ≥ τ] / Σ p̂·v      over the full population
```

- **Assumptions:** I1, I3, plus **correct specification of the outcome model in the score tail**.
- **This assumption is real and load-bearing.** The first implementation used a quadratic in the two scores and was
  visibly biased (−0.023, +0.010, −0.023 on the three segments — systematic, with tiny variance). Replacing it with
  a piecewise-linear spline basis with knots at 0.5/0.8/0.95/0.99 and a score interaction removed the bias. **A
  misspecified outcome model is a silent failure mode here**, not a noisy one, and that is worth recording: it
  means A3 is legitimate but the least forgiving of the four.
- **Expected behaviour:** the most efficient of the four when correctly specified, because it borrows strength
  across the whole population.

## A4. Fully mature cohort only

**Machinery:** discard every cohort that could still be censored (`age ≥ 120 days`), then apply A1's weighting.

- **Assumptions:** I1, I5. **Does not need I3** — it sidesteps the maturity question entirely instead of modelling
  it.
- **Cost:** discards roughly a third of the window.
- **Why it belongs:** it is the conservative analyst's answer, it is unambiguously valid, and it is the *least
  efficient* accepted method — which means it should set the verifier tolerance if the task is built. G05's gate
  showed the value of anchoring tolerance on a legitimate-but-noisy estimator rather than on the oracle.

## Comparison

| | A1 HT | A2 post-strat | A3 imputation | A4 mature cohort |
|---|---|---|---|---|
| Uses propensities | yes | **no** | in the fit weights only | yes |
| Uses a model of `Y*` | no | no | **yes** | no |
| Needs the maturity horizon | yes | yes | yes | **no** |
| Data discarded | recent cohorts | recent cohorts | recent cohorts | **~1/3 of the window** |
| Fails if the bypass rate is mis-stated | yes | partly | partly | yes |
| Fails if the outcome model is wrong | n/a | n/a | **yes, silently** | n/a |

## What is *not* a separate family

- **Doubly robust.** A combination of A1 and A3; it would pass, but listing it would be padding rather than a
  genuinely distinct route, and in this DGP it adds nothing A1 and A3 do not already demonstrate.
- **Partial identification / bounds.** Legitimate in a world where the bypass is unlogged. Here the bypass *is*
  logged, so bounds would be needlessly wide and would not answer the question asked. If the task were built with
  an unlogged bypass, bounds would become the only honest answer — and the decision would be "cannot identify",
  which the brief warns against using as an ambiguity escape hatch.
- **Survival modelling of the chargeback lag.** A more sophisticated way to do the maturity step than the 99th
  percentile horizon, but it is a component of A1/A2/A3, not an alternative to them.

## Why four families and not one

The brief's requirement is that the verifier must not reward one recipe. The four families disagree with each
other on every implementation axis — weights vs cells vs models, and which data to throw away — while agreeing on
the answer to within a few tenths of a point of recall. The measured spread (RMSE 0.008-0.013 on delta) is an order of magnitude below the true `Δ`, so the four
families are mutually consistent. That test passed; the design failed others - see `simulation_results.md`.
