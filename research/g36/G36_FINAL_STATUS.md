# G36 — FINAL STATUS: CLOSED, DEVELOPMENT-ONLY (2026-09-21)

External review decision. **No further repair, no v1.2, no replay of the saved Gemini submissions,
no further G36 baseline.** Neither the original G36 nor the abandoned v1.1 may be modified.

## ORIGINAL G36 — `candidates/g36-tou-capacity-gate`
| | |
|---|---|
| checksum | `85197582fa38141d` (freeze commit `a2196df`) |
| raw Gemini trials | **0/3** |
| raw pass@3 | **0** |
| status | **CONTAMINATED BY F8 RESPONSE-DEFINITION DEFECT.** The verifier graded the household-weighted response; the contract describes a load-weighted one (`adjudication/response_estimand.md`) |
| aggregate eligible | **NO** |

## G36-v1.1 — `candidates/g36-tou-capacity-gate-v1.1`
| | |
|---|---|
| checksum | `ed811aa41868f8a5` (commit `063330c`) |
| status | **ABANDONED / DEVELOPMENT-ONLY** |
| reason | After the invalid response grading was removed (decision O2), **CE06** passes all five extracts at **0.10–0.29 × forecast tolerance**. CE06 is a scientifically wrong equal-segment aggregation of the tariff response, used inside the forecast. The generator therefore cannot support a sharp verifier for the intended aggregation distinction without post-hoc redesign. |
| saved-submission replay | **NOT PERFORMED** |
| fresh v1.1 baseline | **NOT RUN** |
| model calls during adjudication | **ZERO** |

## Preserved disclosures (not to be softened or deleted)
- **F8.** The verifier graded the wrong response estimand. The oracle, all three K9 families and the
  verifier shared one helper (`adjudication/graded_quantity_independence.md`).
- **Response tolerance window was degenerate.** Valid estimators miss by up to 0.92 SE_REF; the wrong
  `segment_unweighted_mean` misses by only 0.99 SE_REF (`v1_1/tolerance_calibration.md`).
- **An attempted post-hoc 1.3× separability rule was added and reverted.** It was reverted before
  any verifier modification, build, freeze or replay (`v1_1/tolerance_calibration.md`,
  `v1_1/response_grading_decision.md`).
- **Selection transport was pre-solved** by the scaffold's estate weighting and the output schema
  (`adjudication/selection_transport_postmortem.md`).
- **Development defects D1–D7** (`development_defect_log.md`), and the threshold re-derived from
  capacity economics after the margin-maximising 2.825 kW was rejected (`threshold_provenance.md`).

## Excluded changes (post-baseline benchmark engineering)
Tightening the forecast tolerance, restoring response grading, adding any intermediate check,
altering fixtures or the threshold, redesigning selection, tuning hidden_c, and creating v1.2 are all
excluded.

G36 appears in every pool table as: **raw 0/3 · pass@3 0 · CONTAMINATED F8 · DEVELOPMENT-ONLY ·
EXCLUDED FROM AGGREGATE.**
