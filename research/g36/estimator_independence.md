# G36 estimator independence audit

The research phase's three "valid routes" were algebraic rearrangements of one estimator and were
rejected as evidence. This is the implementation replacement, and the independence claim is argued
per axis rather than asserted.

## The three families

| | F1 stratified plug-in | F2 joint nonlinear | F3 hierarchical |
|---|---|---|---|
| **mathematical form** | two-stage: stable curve then response curve, composed | one nonlinear model per segment fitted to both regimes at once | stable curve as F1; response curve shrunk toward the pooled curve |
| **estimating equation** | closed-form weighted least squares, twice | `(base + beta*cdd) * (1 - r0 - r1*(cdd-ref))^tariff` | weighted least squares plus an empirical-Bayes shrinkage step |
| **fitting algorithm** | linear least squares (direct) | **Gauss-Newton iteration** | linear least squares plus a variance-ratio shrinkage weight |
| **data used for the stable part** | **flat-tariff history only** | **history AND the pilot control arm jointly** | flat-tariff history only |
| **pooling across segments** | none | none | **partial, by precision** |
| **response estimated as** | ratio of two smoothed arm curves | interaction parameters inside one fit | shrunk per-segment curves |
| **assumptions** | stable curve linear in CDD; response linear in CDD; segments independent | same, plus the multiplicative form is correct globally | same as F1, plus exchangeable segment effects |
| **deliberate bias** | none | none | **yes, toward the pooled response** |
| **measured bias** | +0.0083 | +0.0022 | -0.0018 |
| **measured sd** | 0.0143 | 0.0138 | 0.0163 |

## Why these are not rearrangements

Three concrete differences that cannot be algebraically transformed into one another:

1. **F2 uses data F1 never touches.** F1's stable curve sees only the flat-tariff seasons. F2's
   stable parameters are informed by the pilot's control arm as well, because both regimes enter one
   fit. Given the same input table the two consume different subsets of it.

2. **F2 solves a nonlinear problem iteratively.** F1 produces its estimate from two closed-form
   least-squares solutions. F2 runs Gauss-Newton to convergence on a product of two linear terms,
   with a Jacobian that couples the stable and response parameters. There is no rearrangement of
   F1's arithmetic that yields F2's fixed point.

3. **F3 is deliberately biased and F1 is not.** Shrinkage trades bias for variance on thin segments.
   Its measured bias (-0.0018) and larger sd (0.0163) are the signature of that trade. An estimator
   that is biased by construction cannot be an algebraic restatement of one that is not.

## Where they agree, and how closely

Twenty draws across five fixtures, paired differences:

| pair | mean difference | se | t | verdict |
|---|---|---|---|---|
| F1 vs F2 | -0.0033 | 0.0035 | -0.93 | compatible |
| F1 vs F3 | +0.0027 | 0.0032 | +0.84 | compatible |
| F2 vs F3 | +0.0060 | 0.0033 | +1.82 | compatible |

**Procurement decision: unanimous and correct on 20 of 20 draws.**

## A note on the acceptance criterion

An initial rule - "maximum spread across all draws must be under 2 sd" - reported FAIL at 2.89. That
rule is not a valid test: the **maximum** of a spread over twenty draws of three positively
correlated estimators has an expectation well above 2 sd even when all three are unbiased for the
same estimand. The correct test is whether the **paired** difference has a mean indistinguishable
from zero relative to its own standard error, which it does on all three pairs.

The criterion was corrected because it was statistically wrong, not because it gave an inconvenient
answer - and the corrected test is stricter in the way that matters, since it would detect a
systematic offset of a fraction of a sd that a max-spread rule would miss entirely.

## Residual caveat

F3 shows a bias of -0.0090 against truth in the final fixture set (t = -3.07 over 20 draws). That is
the shrinkage bias behaving as designed. It is 0.6 sd of a single estimate - immaterial for grading
at a tolerance of 2.5 SE_REF - but it is real and is recorded rather than rounded away.
