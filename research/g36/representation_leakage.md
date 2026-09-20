# G36 representation-leakage audit

Probes on the simulated representation. The question is whether the regime, or the answer, can be
recovered without doing the analysis.

| regime | corr(segment, opt-in) | corr(row order, segment) | pilot households |
|---|---|---|---|
| visible | +0.231 | -0.031 | 503 |
| hidden_a_strong_selection | +0.346 | +0.025 | 576 |
| hidden_b_flat_in_heat | +0.214 | +0.007 | 525 |
| hidden_c_fades_in_heat | +0.227 | -0.008 | 554 |
| hidden_d_high_response | +0.206 | +0.026 | 499 |

## Necessary metadata vs answer leakage

**`corr(segment, opt-in)` is supposed to be non-zero.** It *is* the selection the task is about, it
is visible to the analyst by design, and quantifying it is step one of the correct analysis. It is
experimental metadata, not leakage: knowing precisely who opted in does not give the target
forecast, because the response magnitude and its temperature dependence still have to be estimated
and transported.

The distinction matters because a naive leakage audit would flag this and a design change to hide it
would destroy the task.

## Genuine leakage probes — all clean

- **row order** carries no segment signal (|r| <= 0.031);
- **pilot size** does not separate regimes (499-576, overlapping);
- **historical metrics** do not separate regimes (holdout R2 0.747-0.757, RMSE 0.726-0.749 - see
  `simulation_results.md` s4); this is the same-history property and it is load-bearing;
- **regime names** exist only in the research code and must never reach a workspace.

## Requirements for any future build

1. Segment labels must be operational (`apartment`, `large_house_pool`), never response-coded.
2. Household and meter identifiers must be label-shuffled and row order randomised before
   serialisation.
3. The pilot enrolment log is a **required** artefact - identification depends on it - and must
   carry enrolment timestamps preceding the pilot start, with no response information.
4. The target-summer weather forecast must be present (the analyst needs it) and the target summer's
   *outcomes* must be absent (they do not exist at decision time).
5. No artefact may contain the true response parameters, the damping coefficient, or any regime
   label.
6. Hidden regimes must not be distinguishable by dataset size, file layout or household counts.
