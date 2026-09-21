# G36-v1.1 — verifier-only adjudicated revision: HALTED AT TOLERANCE CALIBRATION (NOT FROZEN)

**Status: STOPPED WITHOUT FREEZE. Returned for external adjudication.**

G36-v1.1 was authorised as a minimal verifier-only correction of defect F8: the verifier graded the
estate response as household-weighted (`R_household = Σ p_s r_s`), while the contract describes a
load-weighted reduction (`R_load = (L0 − L1)/L0` at the target mean CDD).

| gate | result |
|---|---|
| Agent-visible byte identity (source) | **PASS** — 16 artefacts, 0 differ, manifest digest `7eea3d3745160c89` for both |
| IGQA (two derivations of R_load sharing no helper) | **PASS** — agreement ≤ 1e-16 on all 5 fixtures |
| Response K9 (F1/F2/F3, paired \|t\| < 3, unanimous decisions) | **PASS** — max pairwise \|t\| 1.11 |
| Response SE_REF remeasured (30 redraws) | done; forecast SE_REF reproduces v1 exactly |
| **Response tolerance, preregistered measured-window method** | **FAIL — degenerate window** (below) |
| Mutation suite, A–H, Oracle/Nop, tamper, clean builds, Harbor check | **NOT RUN** — halted upstream |
| Freeze | **NOT PERFORMED** |
| Replay of saved T1/T2/T3 submissions under v1.1 | **NOT PERFORMED** — the tolerance must be frozen first |

## Why it stopped

The same measured-window procedure used for v1 gives these bounds:

- lower bound (worst legitimate family): **0.92 SE_REF**
- upper bound (hardest wrong analysis, `segment_unweighted_mean`): **0.99 SE_REF**
- the mechanical multiplier rounds to **1.0**, which is *above* the upper bound. The window is
  empty after rounding, and `segment_unweighted_mean` is not caught on any fixture.

At that multiplier, legitimate estimators already sit at 0.90–0.92 of tolerance on hidden_b and
hidden_c. Valid analyses on fresh draws would fail routinely. The season-average variant (R_season),
the contract-deviant but domain-coherent reading, fails on hidden_c (1.22×) and hidden_d (1.18×).

These trigger three of the authorised STOP conditions:

1. The mutation suite would behave unexpectedly: `M34_segment_unweighted_mean_response` would pass.
2. A scientifically legitimate alternative fails at the mechanical tolerance.
3. The only ways to proceed are an exclusion or a threshold chosen after seeing this result. That is
   tuning around a failure.

See `tolerance_calibration.md` for the full analysis and a disclosed procedural lapse (a post-hoc
exclusion rule was added and then reverted, and it did not affect any artefact).

## Files

`change_manifest.md`, `agent_visible_identity.md`, `graded_quantity_audit.md`, `response_k9.md`,
`tolerance_calibration.md`, `mutation_results.md`, `validation_report.md`, `replay_results.md`,
`accounting.md`, plus the machine outputs `*.json`.
