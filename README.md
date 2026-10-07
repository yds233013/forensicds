# ForensicDS

**A benchmark for decision-grade production data science — and a measured capability gap in two frontier agents.**

Ten Harbor tasks, each a realistic piece of *inherited* data-science work. An agent receives a business
memo, the messy operational warehouse behind it, the governing document that defines the decision — and an
analysis someone else already did that **runs, is well documented, and is a correct computation of the
wrong quantity.**

The agent has to notice, work out what is actually going on, and make a defensible business decision.

📊 **[Results and metrics →](METRICS.md)**  ·  📚 **[Full research dossier →](research_review/)**  ·  🧭 **[Start here if new →](research_review/00_READER_GUIDE.md)**

---

## Headline results

| | Gemini 3 Flash | Claude Opus 5.5 |
|---|---|---|
| valid trials | 31 | 27 |
| passing trials | **1** | **13** |
| trial pass rate | **3.2%** | **48.1%** |
| task-level pass@3 | **1/10** | **5/9** |

Both arms graded by the identical frozen verifiers. 45 further attempts were infrastructure failures and
are counted nowhere. [Full breakdown →](METRICS.md)

## The finding is not the difficulty

On the four tasks that emit per-capability sub-scores rather than a single pass/fail bit:

| capability | Gemini | Claude |
|---|---|---|
| reconstruct the evidence | 93% | **100%** |
| frame the right question | 73% | **100%** |
| validate its own work | 92% | **100%** |
| **produce the right number** | **17%** | **33%** |

Both models reconstruct the evidence and frame the right question at or near ceiling. **The
decision-relevant number is the floor for both.** Claude never once mis-framed a problem and still got the
number wrong two times in three. The *ordering* of difficulty is identical across models; only the severity
moves.

But it is **not one failure mode.** The 24 instrumented trials fall into **11 distinct failure patterns**,
including two that are mirror images — one task where the quantity is wrong and the *decision right*,
another where the quantity is *right* and the decision wrong. A single cause cannot produce both. The
defensible claim is a statistical regularity, not a shared mechanism.
[The audit →](research_review/08_FAILURE_MODE_AUDIT.md)

## The sharpest single observation

On `p22-gauge-recalibration` — a machining plant about to raise a contractual claim against a supplier —
all three Gemini trials produced **byte-identical, correct** output for the world they could see. They
correctly blamed the *measuring instrument* rather than the supplier, and correctly declined to escalate.

All three scored **0**, failing only on a hidden sibling world where *tooling* is the real cause:

```
quantitative_results: hidden_c: attribution_pp[tooling]  0.0  vs 3.083 (tol 0.8)
decision:            hidden_c: supplier_decision 'raise_supplier_nonconformance' vs 'no_supplier_action'
```

Their attribution code had no path that could ever assign the change to tooling. They wrote an analysis
that **encoded the explanation they found** rather than a method that recovers whichever explanation holds.

Claude passed that same task once in three — proving the generalisation is achievable, which makes the
Gemini result a capability observation rather than an artefact of task design.

## Why the tasks are hard

Each task is graded against **hidden sibling worlds**: the same company regenerated with a *different
underlying cause*. The agent never sees them. An analysis that hardcodes the mechanism it happened to find
passes the visible world and fails the rest. One task goes further and **re-executes the agent's own
command** against five unseen worlds.

| # | task | domain | mechanism |
|---|---|---|---|
| 1 | [`02-renewal-risk-regression`](candidates/02-renewal-risk-regression) | B2B SaaS | point-in-time correctness / label leakage |
| 2 | [`g05-sco-rollout-gate`](candidates/g05-sco-rollout-gate) | Retail capital | identification under staggered adoption |
| 3 | [`g10-censored-demand`](candidates/g10-censored-demand) | Demand planning | informative censoring, caused by the programme being evaluated |
| 4 | [`g24-recommender-ope`](candidates/g24-recommender-ope) | Personalisation | off-policy evaluation under a logging policy |
| 5 | [`g36-tou-capacity-gate`](candidates/g36-tou-capacity-gate) | Regulated utility | population definition under tariff migration |
| 6 | [`p20-noshow-monitoring`](candidates/p20-noshow-monitoring) | Healthcare MRM | policy feedback + feature vintage |
| 7 | [`p22-gauge-recalibration`](candidates/p22-gauge-recalibration) | Manufacturing QA | measurement-system bias vs process change |
| 8 | [`p31-fill-rate-dispute`](candidates/p31-fill-rate-dispute) | Retail + legal | contractual metric definition |
| 9 | [`g50-courier-boost-rollout`](candidates/g50-courier-boost-rollout) | Delivery marketplace | experimental interference |
| 10 | [`g08-forecast-accuracy-vintages`](candidates/g08-forecast-accuracy-vintages) | Energy trading | data vintages / restated actuals |

No two share a mechanism. Full chapters: [`research_review/tasks/`](research_review/tasks/)

### One worked example

In `g50`, a delivery platform tested a courier bonus, randomising it per order, and measured 4 points fewer
late deliveries on bonused orders. The analysis is done **correctly**.

But a bonused offer jumps the queue ahead of an unbonused one, and **the same couriers serve both**. The
measured gain is mostly one order winning at another's expense. Turn the bonus on for everyone and there is
no queue position left to win. The committee's decision needs *"what happens if everyone gets it?"*; the
experiment answers *"is it better to be bonused while others are not?"* Both numbers are computed
correctly. Only one answers the question.

All three Gemini trials reported the wrong one and recommended the expensive national rollout.

## Repository layout

| path | contents |
|---|---|
| [`METRICS.md`](METRICS.md) | **all results, criterion-level breakdowns and limitations** |
| [`research_review/`](research_review/) | 14-chapter research dossier (~121k words) |
| `research_review/tasks/` | one chapter per task |
| `research_review/trajectories/` | one case study per valid trial (58) |
| `research_review/*.csv` | machine-readable trial ledger, criterion results, task inventory |
| [`candidates/`](candidates/) | the Harbor tasks: instructions, generators, verifiers, reference solutions |
| [`report/`](report/) | the written research report |
| [`research/`](research/) | design docs, candidate tournaments, rejected designs, failure taxonomy |
| `crossmodel_logs/claude/` | raw Claude trial artefacts |
| [`scripts/`](scripts/) | validation, metrics and packaging automation |

## Reproducing the numbers

Every figure recomputes from raw grader output. No model calls needed:

```bash
python research_review/build_inventory.py   # trial ledger + criterion results + task inventory
python research_review/build_results.py     # per-arm result chapters
```

Re-validating a task requires [Harbor](https://pypi.org/project/harbor-cli/) 0.21.0 and Docker:

```bash
harbor run -p candidates/p22-gauge-recalibration -a oracle -k 1 -n 1 -o jobs -y   # expect reward 1
harbor run -p candidates/p22-gauge-recalibration -a nop    -k 1 -n 1 -o jobs -y   # expect reward 0
```

## Honest limitations

Stated up front rather than buried:

1. **The criterion-level finding rests on 4 of 10 tasks** and 24 of 58 trials. Those four share an
   authoring period and are all attribution problems — plausibly the family where a "right decision, wrong
   quantity" split is likeliest.
2. **The cross-model comparison is frontier Opus against fast-tier Flash.** Not tier-matched; much of
   Claude's advantage may be tier rather than architecture.
3. **Three trials per task.** A task at 0/3 is consistent with a true success rate up to ~0.3. No
   significance test is run and none should be inferred.
4. **Behavioural rates are withheld, not published.** The two scaffolds record very unequal amounts of
   reasoning text (median 10,199 vs 1,003 characters), so keyword-derived "recognition" rates would be an
   instrumentation artefact.
5. **Every world is synthetic** and its mechanism is an imposed model — literature-grounded, not measured
   from a real system.

Four defects were found in the benchmark itself, all by internal audit, all documented with impact and
remediation in [`research_review/09_BENCHMARK_INTEGRITY.md`](research_review/09_BENCHMARK_INTEGRITY.md).

## Notes on this repository

- **Not included:** raw Harbor job trees for the Gemini arm (~1.8 GB) beyond a curated tracked subset, and
  the built submission archives (one is 131 MB, above GitHub's per-file limit). Both are reproducible.
- Commit history was re-attributed to this account before publication; messages, dates and order are
  unchanged. Old→new hash map:
  [`research_review/COMMIT_HASH_MAP.txt`](research_review/COMMIT_HASH_MAP.txt).
- `research_review/README_ORIGINAL_5TASK.md` preserves the earlier README describing a superseded
  five-task suite.

---

*Benchmark tasks are frozen: verified byte-identical to the archive both models were evaluated against.*
