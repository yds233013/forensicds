# Task chapter — `g10-censored-demand`

**Harbor task name** `forensicds/censored-demand-g10` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 7200.0s · **network** `public`  
**Directory** `candidates/g10-censored-demand` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**A multi-category retailer, Demand Science.** An inventory-reduction programme called 'LEAN-26' went live.
The Q3 category review now shows baselines down in all eight categories and proposes cutting every buy —
including ice cream, in summer, while ice cream sales are up. The review feeds both the Q3 buy plan and the
decision whether to extend LEAN-26.

**The question:** What is the demand baseline per category, and should the buy plan be cut and LEAN-26 extended?

## B. Why this is genuinely a data-science problem

Demand planning under imperfect availability is a core supply-chain analytics problem, and the artefacts
(sales, inventory snapshots, stockout records, programme configuration) are exactly what a planner holds.

## C. The tempting but incorrect inherited analysis

Compute baselines from observed sales, and — in the most seductive version — restrict to 'clean'
stockout-free days to remove contamination. That filtering sounds like good hygiene.

## D. The actual scientific issue

**In everyday language.**

When a product is out of stock you cannot sell it, so sales understate what customers actually wanted.
LEAN-26 *caused* more stock-outs. So the programme has depressed the very numbers being used to judge it,
and keeping only in-stock days throws away exactly the periods that carry the information.

**Technically.**

**Informative censoring, endogenous to the intervention.** Observed sales are `min(demand, availability)`.
Censoring is not random: it is induced by the programme under evaluation, so selecting on availability
selects on the outcome. Latent demand must be reconstructed using inventory and stockout records, and the
baseline re-estimated on that reconstruction. Conditioning on stockout-free days is a collider-style
selection that biases the trend.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **22 files** |
| generator (never in the final image) | `environment/build/`: `history.py`, `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_demand_review.py`, `tolerances.json`, `truth.py`, `world.py` |
| reference solution | `solution/`: `demandsci/demand.py`, `demandsci/trends.py`, `demandsci/warehouse.py`, `solve.sh` |
| instruction | `instruction.md`, 19 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  RELEASES.md
  demandsci/__init__.py
  demandsci/__main__.py
  demandsci/cli.py
  demandsci/demand.py
  demandsci/impact.py
  demandsci/outputs.py
  demandsci/trends.py
  demandsci/warehouse.py
  docs/data/data_dictionary.md
  docs/models/v3_model_card.md
  docs/models/v4_model_card.md
  docs/outputs/review_outputs.md
  docs/planning/buy_plan_process.md
  docs/planning/demand_definitions.md
  docs/programmes/lean26.md
  docs/replenishment/order_up_to_policy.md
  docs/stores/store_operations.md
  notes/2026-09-16_category_managers.md
  requirements.txt
  sql/availability_kpi.sql
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
pipeline. Reference modules: `demandsci/demand.py`, `demandsci/trends.py`, `demandsci/warehouse.py`, `solve.sh`.
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
| gemini | `g10-gemini3flash-baseline-1` | `g10-censored-demand__LhEU3ny` | yes | 0 | [case study](../trajectories/gemini--g10-censored-demand--g10-gemini3flash-baseline-1--g10-censored-demand__LhEU3ny.md) |
| gemini | `g10-gemini3flash-baseline-1` | `g10-censored-demand__cLtM9yi` | yes | 0 | [case study](../trajectories/gemini--g10-censored-demand--g10-gemini3flash-baseline-1--g10-censored-demand__cLtM9yi.md) |
| gemini | `g10-gemini3flash-baseline-1` | `g10-censored-demand__eMXZbBi` | yes | 0 | [case study](../trajectories/gemini--g10-censored-demand--g10-gemini3flash-baseline-1--g10-censored-demand__eMXZbBi.md) |
| claude | `claude-g10-censored-demand-1` | `g10-censored-demand__GqeMapM` | yes | 0 | [case study](../trajectories/claude--g10-censored-demand--claude-g10-censored-demand-1--g10-censored-demand__GqeMapM.md) |
| claude | `claude-g10-censored-demand-2` | `g10-censored-demand__nK2oKkx` | yes | 0 | [case study](../trajectories/claude--g10-censored-demand--claude-g10-censored-demand-2--g10-censored-demand__nK2oKkx.md) |
| claude | `claude-g10-censored-demand-3` | `g10-censored-demand__bFRBxbA` | yes | 0 | [case study](../trajectories/claude--g10-censored-demand--claude-g10-censored-demand-3--g10-censored-demand__bFRBxbA.md) |

**Gemini: 0/3 valid trials passed. Claude: 0/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Yes, and it is one of the strongest instruments in the suite.** Both models fail every trial (0/3 and
0/3). Gemini's trajectories show heavy, correct engagement with censoring — 29-36 recorded mentions,
one trial recomputing the ice-cream baseline from -5.3% to +9.96% — and still 0/3. That is a direct
observation of correct mechanism engagement with a failing final quantity. **VERIFIED FROM ARTIFACT**
(see the trajectory chapters); the *cause* of the shortfall is **UNKNOWN** without criterion data.

## O. What a future *separately versioned* task should change

Instrument the per-category baselines and the decision separately. This is the highest-value instrumentation target in the suite, because it is the task where behavioural evidence and outcome most clearly diverge.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
