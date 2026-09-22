# G40 fast search (deadline mode) — Stage-1/2 record

## Stage 1 screen
- **Partial-compliance experiment readout: dropped at Stage 1.** It overlaps with Task05
  (exposure / compliance identification), which Gemini solved 3/3.
- **ALERT: carried to Stage 2.** Challenger fraud model evaluated at a fixed SIU (special
  investigations unit) capacity of 1.5 % of claims, on a dual-frame stratified review sample.

## Stage 2 (`sim/alert_sim.py`, 5 regimes × 150 draws; pre-registered statistics in its docstring)
| | |
|---|---|
| VALID_BOUND | 2.76 SE_REF (HT union-π, post-stratified cells, Hájek) |
| WRONG_BOUND | 1.69 SE_REF (precision from unweighted alerted rows: a locally reasonable near-miss; inclusion probabilities are nearly constant within the alert set) |
| next-closest wrong | plain unweighted metrics, 3.30 |
| **ratio** | **0.61 → DROP** |
| decision gate | the challenger recall-gain truth (−0.074 … +0.036 by regime) is within about 1 SE_REF (0.011–0.023) of the 2 pp policy line: fails |

First-order wrong objects separate strongly, at 7–65 SE_REF:
- equal threshold instead of equal budget;
- budget in sample units;
- frame-1 weights only;
- sum of inverse rates;
- top-decile recall.

This is the G37/G38 pattern again: estimation designs have near-miss variants inside the legitimate
noise.

## Deadline decision
No further task generation. The final suite is selected from the measured, frozen pool.
