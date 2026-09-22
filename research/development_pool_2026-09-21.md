# Development pool snapshot — 2026-09-21 (after G36 closure, the G34 semantic audit, and G37/G38 research drops)

No task was selected or dropped to reach the < 30 % target. All figures come from existing frozen
records. No trial was run.

| task | valid trials | successes | raw pass@3 | scientific status | primary failure stage | final-candidate status |
|---|---|---|---|---|---|---|
| Task02 | 3 | 0 | 0 | clean; frozen | execution: root cause found, repair wrong (F4, with F7); per-example historical state | candidate |
| G05 | 3 (1 invalid infra trial replaced, adjudicated) | 0 | 0 | clean; frozen `77a6e432d9d2cba2` | execution: causal effects out of tolerance with decision right (F10 observed) | candidate |
| G10 | 3 | 0 | 0 | clean; frozen | execution after recognition: forecast-based imputation of censored demand | candidate |
| G24 | 3 | 0 | 0 | clean; frozen | statistical object / grain one step off (near-miss) | candidate |
| G08 | 3 | 1 | 1 | clean; frozen | vintage/state reconstruction (F4 with F7) | candidate |
| G34 | 3 | 2 | 1 | **semantic audit B**: minor documentation risk, baseline valid; frozen `f14dd0c0dbcd763c` | execution: administrative censoring counted as survival (1 trial) | candidate |
| G35 | 3 | 3 | 1 | clean but easy once interference is named; frozen `3b7c6a4bd0f403a7` | none observed | candidate (easy anchor) or development-only: **maintainer decision, still open** |
| **G36** | 3 | 0 | **0** | **CONTAMINATED F8 · DEVELOPMENT-ONLY** | (not interpretable: verifier defect) | **EXCLUDED FROM AGGREGATE** |
| **G37** | 0 (none run) | — | — | **RESEARCH-ONLY DROP**: no valid/wrong window (ratio ≈ 0.01) | pre-build: tolerance-window gate | **EXCLUDED** (no trials) |
| **G38** | 0 (none run) | — | — | **RESEARCH-ONLY DROP**: no valid/wrong window (ratio ≈ 0.00 at 3 scales) | pre-build: tolerance-window gate | **EXCLUDED** (no trials) |

## Arithmetic (G36, G37 and G38 excluded; G36's 0/3 is not used, G37/G38 have no trials)
- **Seven eligible tasks:** pass@3 = 3/7 = **42.9 %**. Task successes are 0+0+0+0+1+2+3 = 6 of 21
  trials (28.6 %).
- The G35 inclusion question is unchanged and remains open. It is recorded, not resolved by
  arithmetic.

## Implications
- The pool stays above the < 30 % task-level target. The G34 audit does not change this, because its
  baseline stands.
- G36 contributes no measurement. Its value is methodological: principles 8–14 in
  `benchmark_hypothesis.md`.
- Reaching the target honestly requires new tasks that are genuinely harder in a *new* dimension,
  not the removal of G35/G34/G08.
