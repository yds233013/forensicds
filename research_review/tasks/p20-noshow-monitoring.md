# Task chapter — `p20-noshow-monitoring`

**Harbor task name** `forensicds/noshow-monitoring-p20` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 5400.0s · **network** `public`  
**Directory** `candidates/p20-noshow-monitoring` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**Halcyon Health Partners, clinical operations ML.** The model owner for `noshow-v3.1` must file a
monitoring submission under the written model-risk standard **MRM-04**. The vendor's review reports AUC
falling 0.77 → 0.71 and recommends adopting their retrained `noshow-v4.0`. Clinical Operations need a
decision before the winter capacity plan.

**The question:** Retain `v3.1`, remediate the feature pipeline, retrain, or replace with `v4.0` — whichever MRM-04 §4.3-§4.4 requires?

## B. Why this is genuinely a data-science problem

Model monitoring under a governance standard, with a vendor holding a commercial interest in the outcome,
is routine regulated-healthcare analytics.

## C. The tempting but incorrect inherited analysis

Accept the AUC decline at face value and adopt the vendor's retrained model. The vendor's review is
competent and its recommendation follows from its own numbers.

## D. The actual scientific issue

**In everyday language.**

Four different things could make the number fall: the patient mix changed; the served feature values
disagree with the source records; the features are stale relative to scoring time; or the reminder
programme the model drives has itself changed who shows up. Each implies a *different* remedy, and only
one of them is 'buy the vendor's new model'.

**Technically.**

**Decomposing a monitored-performance decline into four candidate causes** — population drift, feature-feed
defect, feature vintage, and policy feedback — evaluated on the population MRM-04 §4.1 specifies, with
several scoring bases available in the evidence (`as_served`, `record_features_asof_window`,
`feature_store_current`, `candidate_v4`). Policy feedback is the subtle one: a model that triggers
interventions changes its own outcome distribution, so monitored AUC is not a clean measure of model
quality.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **14 files** |
| generator (never in the final image) | `environment/build/`: `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_monitoring.py`, `tolerances.py`, `world.py` |
| reference solution | `solution/`: `mlops/__init__.py`, `mlops/__main__.py`, `mlops/cli.py`, `mlops/data.py`, `mlops/metrics.py`, `mlops/monitor.py`, `mlops/population.py`, `mlops/programme.py` … |
| instruction | `instruction.md`, 18 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  docs/model_risk_standard.md
  docs/outputs/readout_contract.md
  docs/reminder_programme_sop.md
  docs/table_dictionary.md
  mlops/__init__.py
  mlops/__main__.py
  mlops/cli.py
  mlops/data.py
  mlops/metrics.py
  mlops/monitor.py
  mlops/scoring.py
  notes/ops_notes.md
  reports/vendor_monitoring_report.md
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (18 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `mlops/__init__.py`, `mlops/__main__.py`, `mlops/cli.py`, `mlops/data.py`, `mlops/metrics.py`, `mlops/monitor.py`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits **criterion-level rewards**: `decision`, `estimator_implementation`, `evidence_reconstruction`, `identification`, `independent_validation`, `quantitative_results`, `scientific_object`. **VERIFIED FROM ARTIFACT** (`tests/test_monitoring.py`).

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
| gemini | `p20-prospective-1` | `p20-noshow-monitoring__TirBLuz` | yes | 0 | [case study](../trajectories/gemini--p20-noshow-monitoring--p20-prospective-1--p20-noshow-monitoring__TirBLuz.md) |
| gemini | `p20-prospective-2` | `p20-noshow-monitoring__iwPaF7u` | yes | 0 | [case study](../trajectories/gemini--p20-noshow-monitoring--p20-prospective-2--p20-noshow-monitoring__iwPaF7u.md) |
| gemini | `p20-prospective-3` | `p20-noshow-monitoring__c654dzn` | yes | 0 | [case study](../trajectories/gemini--p20-noshow-monitoring--p20-prospective-3--p20-noshow-monitoring__c654dzn.md) |
| claude | `claude-p20-noshow-monitoring-1` | `p20-noshow-monitoring__HtdVz3k` | yes | 0 | [case study](../trajectories/claude--p20-noshow-monitoring--claude-p20-noshow-monitoring-1--p20-noshow-monitoring__HtdVz3k.md) |
| claude | `claude-p20-noshow-monitoring-1__INVALID-credit-balance-too-low` | `p20-noshow-monitoring__PMcSqMB` | **no** | 0 | — (invalid) |
| claude | `claude-p20-noshow-monitoring-2` | `p20-noshow-monitoring__aG6TCgy` | yes | 0 | [case study](../trajectories/claude--p20-noshow-monitoring--claude-p20-noshow-monitoring-2--p20-noshow-monitoring__aG6TCgy.md) |
| claude | `claude-p20-noshow-monitoring-2__INVALID-credit-balance-too-low` | `p20-noshow-monitoring__8KA3gUX` | **no** | 0 | — (invalid) |
| claude | `claude-p20-noshow-monitoring-3` | `p20-noshow-monitoring__KKBaM5D` | yes | 0 | [case study](../trajectories/claude--p20-noshow-monitoring--claude-p20-noshow-monitoring-3--p20-noshow-monitoring__KKBaM5D.md) |
| claude | `claude-p20-noshow-monitoring-3__INVALID-credit-balance-too-low` | `p20-noshow-monitoring__HWJivHD` | **no** | 0 | — (invalid) |

**Gemini: 0/3 valid trials passed. Claude: 0/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Yes — this is the single best instrument in the suite for the central claim.** It is criterion-
instrumented (7 criteria, **VERIFIED FROM ARTIFACT**: `tests/test_monitoring.py` lines 7, 56) and both
models fail 0/3. The decisive observation: **all three Claude trials pass `decision` and fail
`quantitative_results`** — correct action, wrong number, three times out of three. Gemini shows the same
pattern on 2 of 3. This is *correct decisions supported by incorrect quantities*, measured rather than
inferred.

## O. What a future *separately versioned* task should change

Add a sibling world in which the vendor's recommendation is in fact correct, so that 'retain the model' cannot be a safe default. Also split `quantitative_results` into the four attribution components so the failing component is identifiable.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
