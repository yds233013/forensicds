# G36 adjudication - recommendation

# DECISION: **A - MINIMAL ADJUDICATED REVISION** (not built)

## Reason

The response definition is the only defect in G36 as specified, and it can be corrected without
touching a single agent-visible artefact. The task's live mechanism - regime-dependent response
transport - is scientifically sound and produced exactly the failure it was designed to expose: a
model that recognised heat dependence, tested it on the extract it could see, and hardcoded a locally
valid restriction that does not transport. Every selection redesign is contaminated by knowledge of
the successful estimator and is rejected. Retirement would discard a valid, distinct task over a fixable
verifier error.

## What G36-v1.1 would change - exactly

| change | file | agent-visible? |
|---|---|---|
| grade `estate_tou_response_at_target_cdd` as **R_load** = `sum p_s L_s(c̄) r_s(c̄) / sum p_s L_s(c̄)` | `tests/test_capacity.py::_truth_values` | no |
| oracle response helper to R_load, so the Oracle stays correct | `solution/capacity_forecast/estimators.py` | no |
| `SE_REF` for the response re-measured under R_load, 30 redraws; multiplier from the measured-window procedure | `tests/scenarios.py` | no |
| `difficulty_explanation`: G36 primarily tests regime-dependent response transport; selection is pre-solved by the scaffold | `task.toml` | no |

## What would be deliberately unchanged

`instruction.md`; every document; `analysis_contract.md`, including the response field and its
wording; the warehouse and generator (`world.py`, both copies); all five fixtures; the 3.057 kW
threshold; the forecast `SE_REF` and tolerance; the incumbent scaffold; every other check. **The built
image, and therefore everything an agent sees, would be byte-identical to frozen G36.**

## Should the response still be graded?

**Yes - as a secondary check, not an independent separation pillar.**

- *Distinct scientific fact?* Partly. It is the figure a planner would quote ("the tariff cuts estate
  peak by 7.6 %"), and it isolates the transported behavioural effect. But under R_load it is close to
  algebraically determined by the tariff and no-tariff loads at the mean CDD.
- *Detects meaningful wrong analyses?* It catches `M28` and `M29`, which report an incoherent response
  beside a correct forecast. Those are reporting errors rather than scientific ones. Compensating-error
  analyses - a right forecast from wrong stable and response components - are the theoretical case for
  it; none has been demonstrated.
- *Identifiable?* Yes. SE 0.0043-0.0227 across fixtures under R_load.
- *Duplicates the forecast?* Substantially. On all three trials, grading forecast plus decision alone
  gives the same verdict as grading R_load.

An acceptable alternative, if the reviewer prefers minimal semantic surface: **stop grading the field**,
also verifier-only. That loses only `M28`/`M29` detection. Either choice gives identical outcomes on the
existing trajectories.

## Validation v1.1 would require before any freeze

1. **IGQA part (2):** a contract-only derivation of the response, written without reading the verifier,
   must agree with the new truth.
2. K9 for the response under R_load across F1/F2/F3, with the shared helper replaced by independent code
   in at least one family.
3. The full mutation suite, Oracle, Nop, tamper controls, clean rebuild and `harbor check`.
4. A byte-identity check of the built image and every agent-visible file against frozen G36.

## Selection: acknowledged, not repaired

G36-v1.1 would test **one** transport problem, not two. That is a narrowing of the original claim and
it is stated plainly. A genuine second transport (S3 "structural winners", or S1 within-segment
continuous selection) belongs in a **new task designed from scratch** under the
natural-implementation-path audit - not in a post-baseline revision of this one.

## What happens to the numbers

| | value | status | enters aggregate now? |
|---|---|---|---|
| original frozen G36 | **0/3**, pass@3 = 0 | **CONTAMINATED - F8 benchmark definition defect** | **no** |
| adjudicated replay under R_load | 2/3, pass@3 = 1 | counterfactual replay, not a baseline | **no** |

## Next action - for external review, not performed

Two decisions belong to the reviewer:

1. **Build G36-v1.1** as the verifier-only correction above - yes or no.
2. **How to measure it.** Because the agent-visible task would be byte-identical, the three existing
   trajectories are exact samples of v1.1, and regrading them is methodologically defensible. A fresh
   baseline would also be possible, since model sessions carry no memory, but it would spend three more
   trials measuring an agent-facing task that has already been measured. Until the reviewer decides,
   **original G36 remains development-only and contaminated**, and no G36 number enters the aggregate.
