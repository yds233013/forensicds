# G36 concept map

Not a literature survey. The purpose is to separate failure modes that are genuinely different, so
the design can target one of them rather than "distribution shift" in general.

## The distinctions that matter

| concept | what changes | what an analyst must do | is it G36? |
|---|---|---|---|
| **covariate shift** | `P(X)` moves, `P(Y\|X)` stable | reweight by `P*(X)/P(X)` | **no** - reweighting alone solves it, kill criterion K6 |
| **concept shift** | `P(Y\|X)` moves | nothing is transportable without new data | **no** - if nothing transports, the target is unidentifiable (K1) |
| **structural break** | a time series changes level or slope | detect and refit after the break | **no** - a break detector plus a post-break mean solves it |
| **intervention-induced change** | a *named action* changes a *specific mechanism*, leaving others intact | decompose, decide what transports, estimate the changed part from new evidence, recompose at the target | **YES** |
| **invariant prediction** | some conditionals are stable across environments | find the stable set | close, but usually framed as feature selection |
| **transportability** | effects measured in one population applied to another | reweight *effects* by effect-modifier distribution | **a component of G36**, not the whole task |
| **policy-sensitive feature** | a predictor is itself set by the policy being changed | must not be conditioned on as if exogenous | **a trap inside G36** |
| **descendant of intervention (mediator)** | a predictor is caused by the intervention | conditioning on it blocks the very effect being forecast | **a trap inside G36** |

## The shape G36 needs

The G35 post-mortem is the binding constraint. G35 failed because **recognition handed over the
estimator**: once "saturation matters" was said, the answer was `mean(pi=1) - mean(pi=0)`.

So G36 must have **more than one orthogonal transport problem**, such that naming the phenomenon
solves at most one of them. Concretely the design needs:

1. a **stable** mechanism estimable from history (so history is not useless);
2. an **unstable** mechanism estimable only from new evidence (so history is not sufficient);
3. **two independent reasons** the new evidence does not transport directly to the target;
4. a target quantity that is **identified** from what the analyst can see.

Point 3 is the innovation over G35. Fixing one transport problem and not the other must still be
wrong, and measurably so.

## Why "forecasting" rather than "effect estimation"

If the graded object were a treatment effect, this becomes G05. The graded object here is a
**forecast of an operational quantity under a named future policy**, which requires composing a
causal ingredient with a stable non-causal one. Neither ingredient alone answers the question.
