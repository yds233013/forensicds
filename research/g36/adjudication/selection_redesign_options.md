# G36 adjudication - can selection be made non-inert without artificiality?

**Research only. G36 is not edited.** Seven alternatives are scored on scientific merit, and then each
faces the contamination question separately in `contamination_analysis.md`: *would I have proposed
this if I had never seen the Gemini trajectories?*

Scores are 1-5, higher is better. "Auto-solved?" asks whether the natural edit to the provided
scaffold would solve the transport without the analyst recognising it.

| | alternative | realism | identifiable | causal selection correction | avoids generic reweighting | distinct from G24/G05 | competent analyst can solve | auto-solved by scaffold? | adds execution difficulty after recognition |
|---|---|---|---|---|---|---|---|---|---|
| **S1** | enrolment depends on a **continuous pre-period covariate within segment** (prior-season peak load), which also modifies the response | 4 | 5 | 5 | 3 | 4 | 5 | **no** | 4 |
| **S2** | enrolment skewed jointly over **segment x climate zone**; response modified by both | 4 | 4 | 5 | 3 | 4 | 4 | **partly** — only if the analyst stratifies on both | 3 |
| **S3** | **"structural winners"** self-select: households whose flat-tariff load is already off-peak-heavy enrol more, and that history-observable trait predicts response | **5** | 4 | 4 | 4 | 4 | 4 | **no** | **5** |
| **S4** | a **cross-cutting effect modifier** (`has_smart_thermostat`) in the customer master, not aligned with segment | 5 | 5 | 5 | 3 | 4 | 5 | **no** | 3 |
| **S5** | continuous participation probability, requiring **g-computation / IPW over a continuous covariate** | 3 | 4 | 5 | **2** | **2** — drifts toward G24's propensity reconstruction | 4 | no | 3 |
| **S6** | **remove the scaffold's estate weighting**: a pooled system-level incumbent instead of a per-segment one | 4 | 5 | 5 | 4 | 4 | 5 | **no** | 2 |
| **S7** | pilot run in a **different service territory** whose zone composition differs from the estate | 3 | 3 — needs zone-level exchangeability | 3 | 3 | 4 | 3 | no | 3 |

## Notes on each

- **S1** is the cleanest scientifically. Selection happens *within* segments on a covariate the
  analyst can reconstruct from history, so segment stratification alone is insufficient. It risks
  becoming "reweight by covariate", a familiar move.
- **S2** is weaker: it is S1 with a coarser second variable, and it is solved by stratifying on two
  columns instead of one.
- **S3** is the most realistic. Self-selection of structural winners is a documented property of
  voluntary time-of-use pilots, independent of anything seen in this project. It also has the
  richest execution after recognition: the analyst must construct the covariate from interval history
  before transporting over it.
- **S4** is realistic and clean, but the fix — stratify by the flag — is a single, obvious extra
  column once the flag is noticed.
- **S5** is rejected on distinctness. Its difficulty is propensity estimation, which is G24's ground.
- **S6** does not add a mechanism; it removes the handover. It is the least artificial change, but it
  only makes the *natural* path wrong; the fix remains "stratify and standardise", which T1's family
  of approaches already does.
- **S7** is rejected on identifiability: transport across territories needs a zone-level
  exchangeability assumption the analyst cannot check from the extract.

## Strongest scientifically

**S3**, then **S1**. Either would give G36 a genuine second transport.

## Why none is adopted for G36-v2

Scientific merit is not sufficient. Each option is evaluated against the contamination rule in
`contamination_analysis.md`, and **every one fails it**. They would have been legitimate design choices
before the baseline, and they are recorded as candidate mechanisms for a *new* task built from scratch
under the natural-implementation-path audit. They are not admissible as post-baseline changes to G36.
