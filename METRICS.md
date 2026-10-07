# Results and metrics

Every number on this page is recomputed from raw grader output (`verifier/reward.txt`,
`verifier/criteria.json`) by [`research_review/build_results.py`](research_review/build_results.py).
Nothing is copied from a prior summary. Reproduce with:

```bash
python research_review/build_inventory.py   # -> the three CSVs
python research_review/build_results.py     # -> the per-arm result chapters
```

---

## Headline

| | Gemini 3 Flash | Claude Opus 5.5 |
|---|---|---|
| agent / scaffold | `gemini-cli` | `claude-code` |
| model id | `google/gemini-3-flash-preview` | `claude-opus-5-5` |
| tasks graded | **10** of 10 | **9** of 10 |
| valid trials | **31** | **27** |
| passing trials | **1** | **13** |
| trial pass rate | **3.2%** | **48.1%** |
| task-level pass@3 | **1/10 = 10%** | **5/9 = 56%** |
| measured API cost | not recorded by the scaffold | **$23.07** |

**Two different rates, not interchangeable.** *Trial pass rate* answers "how often does one attempt
succeed?". *Task-level pass@3* answers "how many tasks fall to three attempts?". With three trials per
task the second is coarse and high-variance.

---

## Per task

| # | task | domain | scientific mechanism | Gemini | Claude |
|---|---|---|---|---|---|
| 1 | [`02-renewal-risk-regression`](research_review/tasks/02-renewal-risk-regression.md) | B2B SaaS revenue | Point-in-time correctness / label leakage | 0/3 | 3/3 |
| 2 | [`g05-sco-rollout-gate`](research_review/tasks/g05-sco-rollout-gate.md) | Retail capital planning | Identification under staggered adoption | 0/4 | 3/3 |
| 3 | [`g10-censored-demand`](research_review/tasks/g10-censored-demand.md) | Retail demand planning | Informative censoring, endogenous to the programme | 0/3 | 0/3 |
| 4 | [`g24-recommender-ope`](research_review/tasks/g24-recommender-ope.md) | Consumer internet personalisation | Off-policy evaluation under a logging policy | 0/3 | 3/3 |
| 5 | [`g36-tou-capacity-gate`](research_review/tasks/g36-tou-capacity-gate.md) | Regulated electric utility | Population definition under tariff migration | 0/3 | 0/3 |
| 6 | [`p20-noshow-monitoring`](research_review/tasks/p20-noshow-monitoring.md) | Healthcare model risk | Policy feedback + feature vintage + drift decomposition | 0/3 | 0/3 |
| 7 | [`p22-gauge-recalibration`](research_review/tasks/p22-gauge-recalibration.md) | Precision manufacturing | Measurement-system bias vs process change | 0/3 | 1/3 |
| 8 | [`p31-fill-rate-dispute`](research_review/tasks/p31-fill-rate-dispute.md) | Grocery retail + legal | Contractual metric definition reconciliation | 0/3 | 0/3 |
| 9 | [`g50-courier-boost-rollout`](research_review/tasks/g50-courier-boost-rollout.md) | Delivery marketplace | Interference / unit of intervention | 0/3 | — |
| 10 | [`g08-forecast-accuracy-vintages`](research_review/tasks/g08-forecast-accuracy-vintages.md) | Energy trading analytics | Data vintage / restated actuals | 1/3 | 3/3 |

### Reading it

- **Claude solves 5 of the 9 tasks it was graded on**: `02`, `g05`, `g24`, `p22` (1/3), `g08`.
- **Four tasks defeat both models on every single trial**: `g10`, `g36`, `p20`, `p31`. These are the
  suite's durable core.
- **`g50` has no Claude grade.** Its verifier pins the container runtime by hash; the `claude-code`
  scaffold installs its own tooling, changes a pinned file, and the verifier refuses to grade rather than
  scoring unfairly. Four attempts, four refusals — including one where the agent demonstrably ran
  (16 steps, $0.66 billed). This is a **verifier incompatibility, not a model failure**, and repairing it
  would mean editing a frozen task, so it was left alone and reported.

---

## Criterion-level results — the actual finding

Four of the ten tasks emit per-capability sub-scores instead of a single bit. This is where the
interesting result lives.

| capability | criterion | Gemini | Claude |
|---|---|---|---|
| reconstruct the evidence | `evidence_reconstruction` | 14/15 (93%) | 9/9 (100%) |
| frame the right question | `scientific_object` | 11/15 (73%) | 9/9 (100%) |
| validate its own work | `independent_validation` | 11/12 (92%) | 9/9 (100%) |
| implement an estimator | `estimator_implementation` | 11/12 (92%) | 7/9 (78%) |
| argue identification | `identification` | 5/12 (42%) | 4/9 (44%) |
| reach the decision | `decision` | 4/15 (27%) | 4/9 (44%) |
| **produce the right number** | `quantitative_results` | 2/12 (17%) | 3/9 (33%) |

`g50` uses slightly different criterion names (`quantitative_result` singular, plus `uncertainty` and
`courier_supply_response`); since Claude never received a `g50` grade those appear for Gemini only:
`quantitative_result` 0/3, `uncertainty` 0/3, `courier_supply_response` 1/3.

### What this shows

Both models reconstruct the evidence and frame the right question at or near ceiling, and **the
decision-relevant number is the floor for both**. Claude never once mis-framed the problem — 100% on
evidence reconstruction, scientific object and self-validation — and still got the number wrong two times
in three.

**The ordering of difficulty across capabilities is identical for both models. Only the severity moves.**

---

## Failure shapes — why this is not one failure mode

The 24 instrumented valid trials fall into **11 distinct criterion-failure patterns**, including two that
are mirror images. A single cause cannot produce both:

| pattern | trials | what it means |
|---|---|---|
| quantity wrong **and** decision wrong | 5 (`p22`) | attribution misallocated; the procedure encoded the one mechanism it found |
| quantity wrong, **decision right** | 7 (`p20`) | right action from an analysis that does not support it |
| **quantity right**, identification + decision wrong | 4 (`p31`) | recovered the number, misread what it licenses |
| framing never recovered | 4 (`g50`) | reported the incumbent's quantity unchanged |
| all seven pass | 1 (`claude-p22-...-2`) | the only full pass in the project |

So the defensible claim is a **statistical regularity** — the decision-relevant quantity is the modal
failure — and **not** a shared internal mechanism. Identical-looking errors need not have identical causes.

---

## The sharpest single observation

On `p22-gauge-recalibration`, all three Gemini trials produced **byte-identical, correct** output for the
world they could see: they correctly blamed the measuring instrument rather than the bar-stock supplier,
and correctly declined to raise a contractual claim. All three then scored **0**, failing only on the
hidden sibling world where *tooling* is the true cause:

```
quantitative_results: hidden_c: attribution_pp[material] 3.92 vs 0.817 (tol 0.8)
quantitative_results: hidden_c: attribution_pp[tooling]   0.0  vs 3.083 (tol 0.8)
decision:            hidden_c: supplier_decision 'raise_supplier_nonconformance' vs 'no_supplier_action'
```

Their attribution code had no path that could ever assign the change to tooling. They wrote an analysis
that encoded the explanation they found rather than a method that recovers whichever explanation holds.

**Claude passed that same task once in three** — which proves the generalisation is achievable, so the
Gemini result is a capability observation rather than an artefact of task design. That single contrast is
the most load-bearing comparison in the project.

---

## Invalid attempts — excluded from every rate above

**45 attempts** produced no graded result and are counted nowhere. Full register:
[`research_review/INFRASTRUCTURE_FAILURE_REGISTER.md`](research_review/INFRASTRUCTURE_FAILURE_REGISTER.md).

| cause | count |
|---|---|
| `credit-balance-too-low` | 20 |
| `verifier-refused` | 6 |
| `agent-setup-timeout` | 3 |
| `verifier-refused-ldsocache` | 3 |
| `api-key-rejected` | 3 |
| `free-tier-quota` | 3 |
| `free-tier-rpm-stopped` | 3 |
| `session-interrupted-during-agent-setup` | 3 |
| `verifier-refused-agent-did-run` | 1 |

An ungraded attempt carries no information about model capability. One case is worth naming: when an
account hit a billing limit mid-run, the agent returned after 2 steps with an empty workspace and the
grader then **graded that empty submission**, writing a `criteria.json` with every criterion 0. Read from
the reward file alone that is indistinguishable from catastrophic model failure. Validity is therefore
derived from the **trajectory** (did the agent act?) and the **grader's stdout** (did it refuse?), never
from the reward value.

---

## Benchmark integrity

| check | result |
|---|---|
| all ten tasks byte-identical to the evaluated archive | **verified** |
| frozen task, verifier, tolerance or scoring rule modified during either evaluation | **none** |
| invalid attempts counted as model failures | **none** |
| agent-visible leakage of generator, solution or hidden worlds | **none across all ten** |
| grader exploits found | **none** |

Four defects were found in the benchmark itself, all by our own audits, all documented with their impact
and remediation in
[`research_review/09_BENCHMARK_INTEGRITY.md`](research_review/09_BENCHMARK_INTEGRITY.md). The most
consequential: one task's output contract never stated a sign convention, so some submissions reported the
right magnitude with the opposite sign. Both model arms inherited it. Every affected trial also failed on
independent grounds, so the pass rates stand — but any claim that a model "could not compute" that
quantity is **not supportable**, and the page saying so is part of the record.

---

## Limitations stated plainly

1. **The criterion-level finding rests on 4 of 10 tasks and 24 of 58 trials.** The four instrumented tasks
   share an authoring period and are all attribution/decomposition problems — plausibly the family where a
   "right decision, wrong quantity" split is most likely. This is a real selection-bias risk.
2. **The cross-model comparison is frontier Opus against fast-tier Flash.** Not tier-matched; much of
   Claude's advantage may be tier rather than architecture.
3. **Three trials per task.** A task recorded 0/3 is consistent with a true success probability up to
   roughly 0.3. No significance test is run and none should be inferred.
4. **Behavioural rates are not reported.** The two scaffolds record very unequal amounts of reasoning text
   (median 10,199 vs 1,003 characters per trial), so keyword-derived "recognition" or "revision" rates
   would be an instrumentation artefact. They are withdrawn rather than published.
5. **Every world is synthetic and its mechanism is an imposed model.** Literature-grounded, but not
   measured from a real system. All conclusions are conditional on them.

---

## Where the evidence lives

| artefact | path |
|---|---|
| full research dossier (14 chapters) | [`research_review/`](research_review/) |
| per-task chapters | [`research_review/tasks/`](research_review/tasks/) |
| one case study per valid trial (58) | [`research_review/trajectories/`](research_review/trajectories/) |
| machine-readable trial ledger | [`research_review/ALL_TRIALS.csv`](research_review/ALL_TRIALS.csv) |
| criterion results (missing values left empty, never zero-filled) | [`research_review/CRITERION_RESULTS.csv`](research_review/CRITERION_RESULTS.csv) |
| task inventory with hashes | [`research_review/MACHINE_READABLE_INVENTORY.csv`](research_review/MACHINE_READABLE_INVENTORY.csv) |
| claim → artefact mapping | [`research_review/EVIDENCE_INDEX.md`](research_review/EVIDENCE_INDEX.md) |
| the ten frozen tasks | [`candidates/`](candidates/) |
