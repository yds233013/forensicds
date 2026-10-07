# Task chapter — `g08-forecast-accuracy-vintages`

**Harbor task name** `forensicds/forecast-accuracy-vintages-g08` · **difficulty** `hard` · **agent timeout** 3600.0s · **verifier timeout** 4800.0s · **network** `public`  
**Directory** `candidates/g08-forecast-accuracy-vintages` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**An energy/commodity trading desk, Trading Analytics engineering.** In July an 'accuracy mart' replaced
the notebook that produced the monthly forecast-accuracy packs. The September review built from the mart
puts `v4`'s WAPE 29.7% below `v3`'s and recommends retiring `v3`. The model board will act on it.

**The question:** Is `v4` genuinely more accurate than `v3`, and should `v3` be retired?

## B. Why this is genuinely a data-science problem

Measuring forecast accuracy against a restated actuals series is a real and widely mis-handled
analytics-engineering problem.

## C. The tempting but incorrect inherited analysis

Compute WAPE of each model's forecasts against the current actuals table. The mart is well engineered and
its numbers reconcile internally.

## D. The actual scientific issue

**In everyday language.**

The 'actuals' get revised after the fact. If you score an old forecast against today's revised numbers you
are mixing up how good the forecast was with how much the truth later changed — and the two models made
their forecasts at different times, so the comparison is not fair.

**Technically.**

**Vintage-correct accuracy measurement.** A forecast made at origin *t* must be scored against the actuals
*as of* a consistently defined vintage, not against the latest restated series. Using revised data
exaggerates apparent performance and makes models with different forecast origins incomparable; the
accuracy statistic otherwise reflects both forecast error and revision history.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **24 files** |
| generator (never in the final image) | `environment/build/`: `history.py`, `world.py` |
| verifier | `tests/`: `reference.py`, `scenarios.py`, `test.sh`, `test_accuracy_mart.py`, `world.py` |
| reference solution | `solution/`: `fcaccuracy/kpi.py`, `fcaccuracy/mart.py`, `solve.sh` |
| instruction | `instruction.md`, 19 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  RELEASES.md
  docs/data/data_dictionary.md
  docs/finance/billing_feed_retirement_2026.md
  docs/finance/scorecard_policy.md
  docs/forecasting/forecast_store.md
  docs/kpi/forecast_accuracy_kpi.md
  docs/mart/accuracy_mart.md
  docs/models/v4_release_note.md
  docs/portfolio/portfolio_restructure_2026.md
  docs/settlement/settlement_process.md
  docs/trading/day_ahead_process.md
  fcaccuracy/__init__.py
  fcaccuracy/__main__.py
  fcaccuracy/cli.py
  fcaccuracy/kpi.py
  fcaccuracy/mart.py
  fcaccuracy/outputs.py
  fcaccuracy/warehouse.py
  notebooks/kpi_pack_legacy.ipynb
  notes/2026-09-22_accuracy_thread.md
  ops/settlement_incidents.md
  requirements.txt
  sql/accuracy_examples.sql
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (19 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `fcaccuracy/kpi.py`, `fcaccuracy/mart.py`, `solve.sh`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits a **single binary reward** only. Criterion-level attribution of its failures is therefore **UNKNOWN** — not zero. This is the dossier's main instrumentation gap.

It does **not** check reasoning, method identity, or any intermediate state the agent does not write
to disk. Legitimate alternative implementations pass as long as the graded outputs fall within
tolerance on every world.

## K. Hidden worlds and adversarial validation

Sibling worlds: `hidden_a`, `hidden_b`, `hidden_c`. The same submitted procedure is graded on each, so an analysis that encodes the mechanism it happened to
find in the visible world is distinguishable from one that recovers whichever mechanism holds.

## L. Known defects, limitations and exposure integrity

See `../09_BENCHMARK_INTEGRITY.md` for the audited defect register. Exposure: this task version is the
one both arms were graded on, and it was **not** modified after exposure.

## M. Every trial outcome

| arm | job | trial | valid | reward | case study |
|---|---|---|---|---|---|
| gemini | `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | `g08-forecast-accuracy-vintages__YGnxp6B` | **no** | — | — (invalid) |
| gemini | `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | `g08-forecast-accuracy-vintages__fPfGQX3` | **no** | — | — (invalid) |
| gemini | `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | `g08-forecast-accuracy-vintages__hd7ACNA` | **no** | — | — (invalid) |
| gemini | `g08-gemini3flash-baseline-2` | `g08-forecast-accuracy-vintages__h7TpDUG` | yes | 0 | [case study](../trajectories/gemini--g08-forecast-accuracy-vintages--g08-gemini3flash-baseline-2--g08-forecast-accuracy-vintages__h7TpDUG.md) |
| gemini | `g08-gemini3flash-baseline-2` | `g08-forecast-accuracy-vintages__pXphfXM` | yes | 1 | [case study](../trajectories/gemini--g08-forecast-accuracy-vintages--g08-gemini3flash-baseline-2--g08-forecast-accuracy-vintages__pXphfXM.md) |
| gemini | `g08-gemini3flash-baseline-2` | `g08-forecast-accuracy-vintages__wmwSU97` | yes | 0 | [case study](../trajectories/gemini--g08-forecast-accuracy-vintages--g08-gemini3flash-baseline-2--g08-forecast-accuracy-vintages__wmwSU97.md) |
| claude | `claude-g08-forecast-accuracy-vintages-1` | `g08-forecast-accuracy-vintages__j6FX37i` | yes | 1 | [case study](../trajectories/claude--g08-forecast-accuracy-vintages--claude-g08-forecast-accuracy-vintages-1--g08-forecast-accuracy-vintages__j6FX37i.md) |
| claude | `claude-g08-forecast-accuracy-vintages-1__INVALID-credit-balance-too-low` | `g08-forecast-accuracy-vintages__e3KqGBF` | **no** | 0 | — (invalid) |
| claude | `claude-g08-forecast-accuracy-vintages-2` | `g08-forecast-accuracy-vintages__VdRBa3e` | yes | 1 | [case study](../trajectories/claude--g08-forecast-accuracy-vintages--claude-g08-forecast-accuracy-vintages-2--g08-forecast-accuracy-vintages__VdRBa3e.md) |
| claude | `claude-g08-forecast-accuracy-vintages-2__INVALID-credit-balance-too-low` | `g08-forecast-accuracy-vintages__oV2yYFj` | **no** | 0 | — (invalid) |
| claude | `claude-g08-forecast-accuracy-vintages-3` | `g08-forecast-accuracy-vintages__U8hBtiE` | yes | 1 | [case study](../trajectories/claude--g08-forecast-accuracy-vintages--claude-g08-forecast-accuracy-vintages-3--g08-forecast-accuracy-vintages__U8hBtiE.md) |
| claude | `claude-g08-forecast-accuracy-vintages-3__INVALID-credit-balance-too-low` | `g08-forecast-accuracy-vintages__n6N9fyt` | **no** | 0 | — (invalid) |

**Gemini: 1/3 valid trials passed. Claude: 3/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Weakly.** Gemini 1/3 and Claude 3/3, so it is the easiest of the ten. It earns its place on mechanism
uniqueness — no other final task's defect lives in the *temporal semantics of the evidence table* — rather
than on headroom. Its single `artifacts` criterion is not a capability decomposition.

## O. What a future *separately versioned* task should change

Instrument it properly, and make the restatement pattern adversarial (e.g. revisions correlated with forecast error) so that a vintage-naive computation is wrong by more than it is here.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
