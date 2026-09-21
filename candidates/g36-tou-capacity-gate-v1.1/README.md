# G36-v1.1 - adjudicated verifier-only revision of G36

> **STATUS: UNFROZEN — HALTED AT RESPONSE TOLERANCE CALIBRATION (degenerate window). Not runnable: response SE_REF/multiplier intentionally unset. See research/g36/v1_1/.**

v1.1 corrects the graded definition of `estate_tou_response_at_target_cdd` to the load-weighted estate
reduction (L0 - L1) / L0 at the target mean CDD. Every agent-visible artefact is byte-identical to the
original frozen G36 (`candidates/g36-tou-capacity-gate`, 85197582fa38141d), which is preserved
unchanged. Selection transport is pre-solved by the representation; the task's primary challenge is
regime-dependent response transport. See research/g36/v1_1/.

---

# G36 - FY27 residential capacity gate

Forecasting under an intervention that changes one mechanism and not another.

A well-validated historical model (holdout R2 0.75) cannot answer a question about a regime that did
not exist when it was validated. A randomised pilot can - but only after being transported across
both the estate mix and the target season's weather. Fixing either transport alone still gives the
wrong capacity decision.

Research and gates: `research/g36/`. Threshold provenance: `research/g36/threshold_provenance.md`.
