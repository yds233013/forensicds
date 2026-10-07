# Claude vs Gemini on the frozen ForensicDS final ten

| | |
|---|---|
| Claude | `claude-opus-5-5` via `claude-code` (Harbor 0.21.0) |
| Gemini | `google/gemini-3-flash-preview` via `gemini-cli` |
| tasks | the 10 frozen tasks, verified byte-identical before and after; **nothing was modified** |
| Claude valid trials | **27** across 9 tasks |
| Claude invalid trials | **24** — 20 `credit-balance-too-low`, 4 `verifier-refused` |
| Claude spend | **$23.0708** (Harbor `total_cost_usd`) |

## Headline

| metric | Gemini | Claude |
|---|---|---|
| valid trials | 31 | 27 |
| passes | 1 | 13 |
| aggregate trial pass rate | **3.2%** | **48.1%** |
| task-level pass@3 | **10%** (1 of 10) | **56%** (5 of 9) |

**Claude Opus 5.5 substantially outperforms Gemini 3 Flash on this benchmark.** The <30% pass@3 headroom
target holds for flash-tier Gemini and **does not hold** for frontier Claude.

## Per task

| task | mechanism | Gemini | Claude | outcome |
|---|---|---|---|---|
| `02-renewal-risk-regression` | point-in-time correctness / leakage | 0/3 | 3/3 | **Claude solves it, Gemini does not** |
| `g05-sco-rollout-gate` | staggered-adoption identification | 0/4 | 3/3 | **Claude solves it, Gemini does not** |
| `g10-censored-demand` | informative censoring | 0/3 | 0/3 | **both fail** |
| `g24-recommender-ope` | off-policy evaluation | 0/3 | 3/3 | **Claude solves it, Gemini does not** |
| `g36-tou-capacity-gate` | population definition under migration | 0/3 | 0/3 | **both fail** |
| `p20-noshow-monitoring` | policy feedback + vintage decomposition | 0/3 | 0/3 | **both fail** |
| `p22-gauge-recalibration` | measurement-system attribution | 0/3 | 1/3 | **Claude solves it, Gemini does not** |
| `p31-fill-rate-dispute` | contractual metric definition | 0/3 | 0/3 | **both fail** |
| `g50-courier-boost-rollout` | interference / unit of intervention | 0/3 | — no data | `g50` verifier refuses any scaffolded agent (see below) |
| `g08-forecast-accuracy-vintages` | data vintage / restated actuals | 1/3 | 3/3 | both pass |

**Claude solves 5 of the 9 tasks it was measured on** (`02`, `g05`, `g24`, `p22` 1/3, `g08`).
**Four tasks defeat frontier Opus on every trial**: `g10` (informative censoring), `g36` (population
definition under tariff migration), `p20` (policy feedback + vintage decomposition), `p31` (contractual
metric definition). Those four are the benchmark's durable core.

## Criterion-level comparison — the shape of the failure is identical

Verifier-derived, therefore genuinely comparable. Gemini 15 instrumented trials, Claude 9.

| criterion | Gemini | Claude |
|---|---|---|
| `evidence_reconstruction` | 14/15 (93%) | **9/9 (100%)** |
| `scientific_object` | 11/15 (73%) | **9/9 (100%)** |
| `independent_validation` | 11/12 (92%) | **9/9 (100%)** |
| `estimator_implementation` | 11/12 (92%) | 7/9 (78%) |
| `identification` | 5/12 (42%) | 4/9 (44%) |
| `decision` | 4/15 (27%) | 4/9 (44%) |
| **`quantitative_results`** | **2/12 (17%)** | **3/9 (33%)** |

**This is the central cross-model result.** Claude is uniformly better — and never once gets the framing
wrong (100% on evidence reconstruction and scientific object, where Gemini managed 93% and 73%). But the
*ordering* is unchanged: for both models the upstream criteria sit near ceiling and
`quantitative_results` is the floor. Claude roughly doubles the rate, 17% → 33%, and it is still the
worst-performing criterion by a wide margin.

The failure mode is therefore **cross-model in shape and model-specific in severity.** A stronger model
does not relocate the bottleneck; it widens the throat slightly.

## Decision-only over-credit — confirmed across models

| | Gemini | Claude |
|---|---|---|
| decision passed while the science failed | 4/15 (27%) | 3/9 (33%) |

All three Claude cases are `p20`, and they are **all three of its `p20` trials**:

| criterion | t1 | t2 | t3 |
|---|---|---|---|
| evidence_reconstruction | ✓ | ✓ | ✓ |
| scientific_object | ✓ | ✓ | ✓ |
| estimator_implementation | ✓ | ✓ | ✓ |
| independent_validation | ✓ | ✓ | ✓ |
| identification | ✗ | ✓ | ✗ |
| **decision** | **✓** | **✓** | **✓** |
| **quantitative_results** | **✗** | **✗** | **✗** |

Frontier Opus reaches the **correct decision** on all three trials while getting the **quantity wrong** on
all three. A decision-only rubric would have scored this task 3/3. This is the strongest single argument in
the project for criterion-level grading, and it now holds for both models.

## `g50` could not be measured, and why that is not a Claude result

`g50`'s frozen verifier hash-pins the runtime. Any agent scaffold that installs its own tooling changes a
pinned file, and the verifier refuses to grade. Four attempts, four refusals:
`interpreter, library tree or sandbox tools differ from the pinned image`.

The final attempt **de-confounds** it: the agent ran properly (16 steps, $0.66 spent) and the verifier still
refused. So this is a genuine verifier limitation for `claude-code`, not a billing artefact and not a model
failure. Fixing it would require modifying a frozen verifier, which this experiment prohibits, so `g50` is
reported as **0 valid Claude trials**.

This is the same defect class found during the Gemini campaign (`/etc/ld.so.cache` regenerated by
`apt-get`). The earlier fix handled `gemini-cli`'s installer; `claude-code` installs something else that
also trips it. **The lesson stands and is now doubly evidenced: a verifier validated only against
`oracle`/`nop` has not been validated against real scaffolds.**

## Behavioural rates remain withdrawn

| scaffold | median `reasoning_content` per trial |
|---|---|
| `gemini-cli` | 10,199 chars |
| `claude-code` | 1,003 chars |

`claude-code` emits roughly a tenth as much reasoning text into the trajectory, so every regex-over-reasoning
signal is depressed for Claude for instrumentation reasons. The raw numbers claim Claude "noticed an anomaly"
in 10% of trials while passing 13 of 27 — not credible. **Recognition, revision and revision-propagation
rates are therefore not reported for either arm in this comparison.** Answering those questions needs a
rubric scored from observable actions, not reasoning text.

What is reported above rests entirely on the identical frozen verifiers: reward, criterion results, and
the criterion-derived failure stage.

## Cost

| | |
|---|---|
| total | **$23.0708** |
| 27 valid trials | $23.0708 |
| 24 invalid trials | $0.66 (the 20 billing failures cost $0; the funded `g50` attempt cost $0.66) |
| median per valid trial | ~$0.80 |
| most expensive | `g10-censored-demand-1`, $3.08, 53 steps |

## Caveats

1. **Tier mismatch.** Frontier Opus against fast-tier Gemini Flash. Much of Claude's advantage is plausibly
   tier, not architecture. A tier-matched `claude-haiku-4-5` arm was designed and never run — **this is the
   single most valuable follow-up.**
2. **Three trials per task.** Small-sample counts; no significance claims. A 3/3 and a 0/3 are suggestive,
   not established.
3. **`g50` unmeasured** for Claude.
4. **Criterion comparison covers 4 tasks** (`p20`, `p22`, `p31`, `g50`) because the other six emit binary
   rewards only — the same limitation the Gemini report carries.
5. **Behavioural rates withdrawn** (above).
6. **20 trials were lost to credit exhaustion** mid-run and re-run after top-up. The re-run used the
   identical frozen tasks and command; trials are not mixed across versions.

**The benchmark was not modified at any point.** All ten tasks verified byte-identical before and after;
the runner refuses to execute against a drifted benchmark; Gemini trajectories untouched.
