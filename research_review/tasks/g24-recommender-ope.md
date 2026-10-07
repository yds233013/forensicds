# Task chapter — `g24-recommender-ope`

**Harbor task name** `forensicds/recommender-ope-g24` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 7200.0s · **network** `public`  
**Directory** `candidates/g24-recommender-ope` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**A consumer-internet retailer, Personalisation Analytics.** Three rankers are in play for the home row:
the deployed `v6`, a candidate `v7`, and `v7_pd`. The offline gate scored `v7` well above `v6` and `v7_pd`
higher still. But experiment AB-1182 measured `v7` **below** `v6` online, with no sample-ratio mismatch.
`v7_pd` has never been tested online and its number comes from the same gate.

**The question:** Which ranker should serve the home row next quarter?

## B. Why this is genuinely a data-science problem

Choosing a ranker from logged data is the central measurement problem of industrial recommendation, and
the offline/online disagreement here is the canonical symptom.

## C. The tempting but incorrect inherited analysis

Trust the offline gate's ranking metric. It is the team's established process, it ranks the candidates
confidently, and it is computed correctly on the data it is given.

## D. The actual scientific issue

**In everyday language.**

The logs only record what the *currently deployed* ranker chose to show. A new ranker that would have shown
different items has no data about them, so scoring it on these logs measures something other than how it
would actually perform.

**Technically.**

**Off-policy evaluation under a logging policy.** Logged bandit feedback gives rewards only for actions the
logging policy π₀ took. Estimating the value of a target policy π requires correcting for the exposure
process — e.g. inverse-propensity weighting `E[(π(a|x)/π₀(a|x))·r]`, with variance control — on the
evaluable population where π₀ had support. A ranking metric computed on raw logs is not an estimate of
π's online value, and the AB-1182 sign flip is the observable evidence of that.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **19 files** |
| generator (never in the final image) | `environment/build/`: `history.py`, `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_ope.py`, `truth.py`, `world.py` |
| reference solution | `solution/`: `recs_eval/cli.py`, `recs_eval/ope.py`, `recs_eval/yaml_lite.py`, `solve.sh` |
| instruction | `instruction.md`, 27 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  RELEASES.md
  docs/data/logging_schema.md
  docs/launch_policy.md
  docs/metrics/home_row.md
  docs/models/v6.md
  docs/models/v7.md
  docs/models/v7_pd.md
  docs/outputs/ope_outputs.md
  notes/2026-09-02_recs_sync.md
  recs_eval/__init__.py
  recs_eval/__main__.py
  recs_eval/cli.py
  recs_eval/logs.py
  recs_eval/metrics.py
  recs_eval/replay.py
  recs_eval/report.py
  serving/config/serving.yaml
  serving/ranker/serve.py
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (27 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `recs_eval/cli.py`, `recs_eval/ope.py`, `recs_eval/yaml_lite.py`, `solve.sh`.
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
| gemini | `g24-gemini3flash-baseline-1` | `g24-recommender-ope__a8zVL7h` | yes | 0 | [case study](../trajectories/gemini--g24-recommender-ope--g24-gemini3flash-baseline-1--g24-recommender-ope__a8zVL7h.md) |
| gemini | `g24-gemini3flash-baseline-1` | `g24-recommender-ope__wVmAykK` | yes | 0 | [case study](../trajectories/gemini--g24-recommender-ope--g24-gemini3flash-baseline-1--g24-recommender-ope__wVmAykK.md) |
| gemini | `g24-gemini3flash-baseline-1` | `g24-recommender-ope__ykNY8fD` | yes | 0 | [case study](../trajectories/gemini--g24-recommender-ope--g24-gemini3flash-baseline-1--g24-recommender-ope__ykNY8fD.md) |
| claude | `claude-g24-recommender-ope-1` | `g24-recommender-ope__ZQ6GV6b` | yes | 1 | [case study](../trajectories/claude--g24-recommender-ope--claude-g24-recommender-ope-1--g24-recommender-ope__ZQ6GV6b.md) |
| claude | `claude-g24-recommender-ope-1__INVALID-credit-balance-too-low` | `g24-recommender-ope__qP3oeYt` | **no** | 0 | — (invalid) |
| claude | `claude-g24-recommender-ope-2` | `g24-recommender-ope__iLg8dSn` | yes | 1 | [case study](../trajectories/claude--g24-recommender-ope--claude-g24-recommender-ope-2--g24-recommender-ope__iLg8dSn.md) |
| claude | `claude-g24-recommender-ope-2__INVALID-credit-balance-too-low` | `g24-recommender-ope__2GQAcaH` | **no** | 0 | — (invalid) |
| claude | `claude-g24-recommender-ope-3` | `g24-recommender-ope__irCRUcE` | yes | 1 | [case study](../trajectories/claude--g24-recommender-ope--claude-g24-recommender-ope-3--g24-recommender-ope__irCRUcE.md) |
| claude | `claude-g24-recommender-ope-3__INVALID-credit-balance-too-low` | `g24-recommender-ope__jYX6kuF` | **no** | 0 | — (invalid) |

**Gemini: 0/3 valid trials passed. Claude: 3/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Partly.** Claude 3/3, Gemini 0/3, so again a sharp difficulty split with no mechanism visibility.
Gemini's trajectories do record identifying the gate's 'Direct Match' estimator as biased, and one trial
diagnosed the bias in its *own* first correction — then still failed. **VERIFIED FROM ARTIFACT**;
cause **UNKNOWN**.

## O. What a future *separately versioned* task should change

Instrument policy-value estimate, evaluable-population definition, and decision separately; add a sibling world where the offline gate and the online result agree, so that trusting the gate is right for once.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
