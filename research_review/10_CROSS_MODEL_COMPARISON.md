# 10 — Cross-model comparison

**VERIFIED FROM ARTIFACT.** Recomputed by `build_results.py` from `verifier/reward.txt` and
`verifier/criteria.json`. Invalid attempts excluded (`INFRASTRUCTURE_FAILURE_REGISTER.md`).

## The comparison that is valid: nine jointly graded tasks

`g50` is excluded because Claude has **no valid trial** on it (verifier refusal, chapter 09). Comparing
a Gemini grade against a Claude non-grade would be a category error.

| task | mechanism | Gemini | Claude | outcome |
|---|---|---|---|---|
| `02-renewal-risk-regression` | point-in-time correctness / label leakage | 0/3 | 3/3 | **Claude passes, Gemini does not** |
| `g05-sco-rollout-gate` | identification under staggered adoption | 0/4 | 3/3 | **Claude passes, Gemini does not** |
| `g10-censored-demand` | informative censoring | 0/3 | 0/3 | **both fail every trial** |
| `g24-recommender-ope` | off-policy evaluation | 0/3 | 3/3 | **Claude passes, Gemini does not** |
| `g36-tou-capacity-gate` | population definition under tariff migration | 0/3 | 0/3 | **both fail every trial** |
| `p20-noshow-monitoring` | policy feedback + feature vintage | 0/3 | 0/3 | **both fail every trial** |
| `p22-gauge-recalibration` | measurement-system bias | 0/3 | 1/3 | **Claude passes, Gemini does not** |
| `p31-fill-rate-dispute` | contractual metric definition | 0/3 | 0/3 | **both fail every trial** |
| `g08-forecast-accuracy-vintages` | data vintage / restated actuals | 1/3 | 3/3 | both pass |
| **joint total** | | **1/28** | **13/27** | |

| metric (nine joint tasks) | Gemini | Claude |
|---|---|---|
| trial pass rate | **3.6%** | **48.1%** |
| tasks with ≥1 pass | **1 of 9** | **5 of 9** |
| task-level pass@3 | **11%** | **56%** |

## The full Gemini ten-task result, reported separately

Gemini was graded on all ten: **1/31 trials = 3.2%**, task-level
pass@3 **10%** (1 of 10). This is the figure in the official submission and it is
reproduced here exactly. It is **not** the right number to compare against Claude, because Claude's
denominator is nine tasks.

## Criterion-level comparison

Verifier-derived, therefore comparable in kind. Sample sizes differ and are shown.

| criterion | Gemini | Claude |
|---|---|---|
| `evidence_reconstruction` | 14/15 (93%) | 9/9 (100%) |
| `scientific_object` | 11/15 (73%) | 9/9 (100%) |
| `independent_validation` | 11/12 (92%) | 9/9 (100%) |
| `estimator_implementation` | 11/12 (92%) | 7/9 (78%) |
| `identification` | 5/12 (42%) | 4/9 (44%) |
| `decision` | 4/15 (27%) | 4/9 (44%) |
| `quantitative_results` | 2/12 (17%) | 3/9 (33%) |
| `quantitative_result` | 0/3 (0%) | — not instrumented |
| `uncertainty` | 0/3 (0%) | — not instrumented |
| `courier_supply_response` | 1/3 (33%) | — not instrumented |

`quantitative_result` (singular) and `uncertainty` and `courier_supply_response` are `g50`-only
criterion names, so they appear for Gemini alone — Claude never received a `g50` grade.

### Reading the table

On the four tasks instrumented for both arms, Claude is better on every criterion that concerns framing
and worse on none that concerns it: **100% on evidence reconstruction, scientific object and independent
validation**, where Gemini managed 93%, 73% and 92%. Yet `quantitative_results` remains the **lowest**
criterion for Claude (33%) just as it is for Gemini (17%).

**What this supports:** the *ordering* of difficulty across capabilities is the same for both models,
and getting the number right is the hardest step for both.

**What this does not support:** any claim that the two models fail for the same internal reason. Two
models missing the same criterion is consistent with one shared cause and with several different causes
(chapter 08).

## Tier and scaffold differences — the dominant confound

| | Gemini arm | Claude arm |
|---|---|---|
| model | `gemini-3-flash-preview` — a **fast/flash tier** preview model | `claude-opus-5-5` — a **frontier tier** model |
| agent | `gemini-cli` | `claude-code` |
| median reasoning text recorded per trial | 10,199 chars | 1,003 chars |
| trials per task | 3 (4 on `g05`) | 3 |

**This is not a matched comparison.** A frontier model beating a flash-tier model is the expected
result, and most of the gap is plausibly tier rather than architecture or training. The experiment that
would separate them — a tier-matched `claude-haiku-4-5` arm — was designed and **never run**
(chapter 12, experiment B).

The scaffolds also differ in how much they record. `claude-code` writes roughly a tenth as much
reasoning text into the trajectory. **Keyword counts over reasoning text are therefore not reported as
behavioural facts anywhere in this dossier.** The raw counts would claim Claude 'noticed an anomaly' in
10% of trials while passing 13 of 27 — not credible, and an instrumentation artefact.

## Uncertainty

Three trials per task. A task recorded 0/3 is consistent with a true per-trial success probability up to
roughly 0.3 at 95% confidence; a task recorded 3/3 is consistent with a true probability as low as about
0.4. **No significance test is run and none should be inferred.** The per-task verdicts in the first
table are directional, not established.

With 9 tasks the task-level pass@3 difference (1/9 vs 5/9) is the more robust signal, and even that
rests on a single configuration of each model.

## What the cross-model evidence supports, stated precisely

1. **SUPPORTED:** Claude Opus 5.5 substantially outperforms Gemini 3 Flash on this benchmark. The
   <30% pass@3 headroom property holds for the flash-tier model and **does not hold** for the frontier
   model (5 of 9 tasks fall).
2. **SUPPORTED:** four tasks resist every trial from both models — `g10`, `g36`, `p20`, `p31`.
3. **SUPPORTED:** on instrumented tasks, the hardest criterion for both arms is the decision-relevant
   quantity, and framing criteria are near ceiling for Claude.
4. **NOT SUPPORTED:** that the benchmark measures a *frontier* capability gap in general. Five of nine
   tasks fell to one frontier model.
5. **NOT SUPPORTED:** that the two models share a single internal failure mechanism.
6. **NOT SUPPORTED:** any behavioural comparison of recognition, revision or revision-propagation rates.
