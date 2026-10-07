# 06 — Claude results (`claude-opus-5-5`, agent `claude-code`)

All numbers recomputed directly from `verifier/reward.txt` and `verifier/criteria.json` in the raw
trial directories by `research_review/build_results.py`. **VERIFIED FROM ARTIFACT.**

## Two different rates, not interchangeable

- **Trial pass rate** = passing trials ÷ valid trials. Answers *how often does one attempt succeed?*
- **Task-level pass@3** = tasks with ≥1 pass ÷ tasks measured. Answers *how many tasks fall to three
  attempts?* With 3 trials per task this is a coarse, high-variance statistic.

## Suite

| metric | value |
|---|---|
| valid trials | **27** |
| passing trials | **13** |
| trial pass rate | **48.1%** |
| tasks measured | 9 of 10 |
| tasks with ≥1 pass | 5 |
| task-level pass@3 | **55.6%** (over the 9 measured) |
| invalid attempts excluded | 27 |

## Per task

| task | valid | passes | trial pass rate | pass@3 |
|---|---|---|---|---|
| `02-renewal-risk-regression` | 3 | 3 | 100.0% | 1 |
| `g05-sco-rollout-gate` | 3 | 3 | 100.0% | 1 |
| `g10-censored-demand` | 3 | 0 | 0.0% | 0 |
| `g24-recommender-ope` | 3 | 3 | 100.0% | 1 |
| `g36-tou-capacity-gate` | 3 | 0 | 0.0% | 0 |
| `p20-noshow-monitoring` | 3 | 0 | 0.0% | 0 |
| `p22-gauge-recalibration` | 3 | 1 | 33.3% | 1 |
| `p31-fill-rate-dispute` | 3 | 0 | 0.0% | 0 |
| `g50-courier-boost-rollout` | 0 | — | — | **not measured** |
| `g08-forecast-accuracy-vintages` | 3 | 3 | 100.0% | 1 |

## Invalid attempts

Excluded from every rate above. Detail: `INFRASTRUCTURE_FAILURE_REGISTER.md`.

| cause | count |
|---|---|
| `credit-balance-too-low` | 20 |
| `verifier-refused` | 6 |
| `verifier-refused-agent-did-run` | 1 |

## Criterion-level results

Only four of the ten tasks emit per-criterion rewards (`p20`, `p22`, `p31`, `g50`). The other six
emit a single binary reward, so criterion attribution for them is **UNKNOWN, not zero**.

Instrumented valid trials in this arm: **9**.

| criterion | passed / instrumented | rate |
|---|---|---|
| `quantitative_results` | 3/9 | 33% |
| `decision` | 4/9 | 44% |
| `identification` | 4/9 | 44% |
| `estimator_implementation` | 7/9 | 78% |
| `evidence_reconstruction` | 9/9 | 100% |
| `independent_validation` | 9/9 | 100% |
| `scientific_object` | 9/9 | 100% |

## What is missing and why

`g50-courier-boost-rollout` has **zero** valid Claude trials. Four attempts, four verifier refusals:
`interpreter, library sandbox tools differ from the pinned image; refusing to grade`. The final attempt
is the de-confounding one — the agent ran (16 recorded steps, $0.66 billed) and the verifier still
refused — so this is a **verifier incompatibility**, not a Claude failure. Repairing it would require
editing a frozen verifier, which the cross-model protocol prohibits.

Consequently Claude's task-level pass@3 is computed over **9** measured tasks, and any Gemini-vs-Claude
suite comparison must use the nine jointly graded tasks (chapter 10).

## Cost and runtime (recorded)

| | |
|---|---|
| total billed (Harbor `total_cost_usd`, summed over all trajectories) | **$23.07** |
| median per valid trial | ~$0.80 |
| most expensive single trial | `claude-g10-censored-demand-1`, $3.08, 53 steps |
| typical wall clock | ~4 minutes per trial |

The 20 `credit-balance-too-low` attempts cost $0.00. The run was interrupted by credit exhaustion and
resumed after top-up against the identical frozen tasks; trials are not mixed across task versions.

