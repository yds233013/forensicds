# 05 — Gemini results (`google/gemini-3-flash-preview`, agent `gemini-cli`)

All numbers recomputed directly from `verifier/reward.txt` and `verifier/criteria.json` in the raw
trial directories by `research_review/build_results.py`. **VERIFIED FROM ARTIFACT.**

## Two different rates, not interchangeable

- **Trial pass rate** = passing trials ÷ valid trials. Answers *how often does one attempt succeed?*
- **Task-level pass@3** = tasks with ≥1 pass ÷ tasks measured. Answers *how many tasks fall to three
  attempts?* With 3 trials per task this is a coarse, high-variance statistic.

## Suite

| metric | value |
|---|---|
| valid trials | **31** |
| passing trials | **1** |
| trial pass rate | **3.2%** |
| tasks measured | 10 of 10 |
| tasks with ≥1 pass | 1 |
| task-level pass@3 | **10.0%** (over the 10 measured) |
| invalid attempts excluded | 18 |

## Per task

| task | valid | passes | trial pass rate | pass@3 |
|---|---|---|---|---|
| `02-renewal-risk-regression` | 3 | 0 | 0.0% | 0 |
| `g05-sco-rollout-gate` | 4 | 0 | 0.0% | 0 |
| `g10-censored-demand` | 3 | 0 | 0.0% | 0 |
| `g24-recommender-ope` | 3 | 0 | 0.0% | 0 |
| `g36-tou-capacity-gate` | 3 | 0 | 0.0% | 0 |
| `p20-noshow-monitoring` | 3 | 0 | 0.0% | 0 |
| `p22-gauge-recalibration` | 3 | 0 | 0.0% | 0 |
| `p31-fill-rate-dispute` | 3 | 0 | 0.0% | 0 |
| `g50-courier-boost-rollout` | 3 | 0 | 0.0% | 0 |
| `g08-forecast-accuracy-vintages` | 3 | 1 | 33.3% | 1 |

## Invalid attempts

Excluded from every rate above. Detail: `INFRASTRUCTURE_FAILURE_REGISTER.md`.

| cause | count |
|---|---|
| `agent-setup-timeout` | 3 |
| `verifier-refused-ldsocache` | 3 |
| `api-key-rejected` | 3 |
| `free-tier-quota` | 3 |
| `free-tier-rpm-stopped` | 3 |
| `session-interrupted-during-agent-setup` | 3 |

## Criterion-level results

Only four of the ten tasks emit per-criterion rewards (`p20`, `p22`, `p31`, `g50`). The other six
emit a single binary reward, so criterion attribution for them is **UNKNOWN, not zero**.

Instrumented valid trials in this arm: **15**.

| criterion | passed / instrumented | rate |
|---|---|---|
| `quantitative_result` | 0/3 | 0% |
| `uncertainty` | 0/3 | 0% |
| `quantitative_results` | 2/12 | 17% |
| `decision` | 4/15 | 27% |
| `courier_supply_response` | 1/3 | 33% |
| `identification` | 5/12 | 42% |
| `scientific_object` | 11/15 | 73% |
| `estimator_implementation` | 11/12 | 92% |
| `independent_validation` | 11/12 | 92% |
| `evidence_reconstruction` | 14/15 | 93% |

## Reconciliation with earlier reports

The project's own `report/FINAL_REPORT.md` and `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md` state
31 valid trials, 1 pass, 3.2% trial pass rate and 10% task-level pass@3. **This recomputation
reproduces those figures exactly**, so the earlier report is confirmed against raw artifacts rather
than merely restated.

Note `g05-sco-rollout-gate` carries **4** valid Gemini trials, not 3 — one extra job
(`g05-gemini3flash-baseline-2`) was run. All four are counted; none is discarded.

## Context the headline rate omits

Across **all 21** exposed tasks (including the eleven excluded from the final ten) Gemini recorded
67 valid trials. Five excluded tasks scored 3/3 (`03`, `05`, `06`, `g35`, `g42`). The final ten are a
deliberately selected hard subset; the model is not globally incapable on this task family.

