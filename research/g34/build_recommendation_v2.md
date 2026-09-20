# G34 redesign — final recommendation

# **A. BUILD** (do not implement yet; awaiting authorisation)

Every gate in the brief was run. All seven requirements pass, and none of the seventeen kill
criteria fires.

## Gate status

| | Requirement | Status | Evidence |
|---|---|---|---|
| **R1** | valid estimators recover latent truth | **PASS** | AJ within ±0.11% of Q1 truth in all 5 regimes; 1 − KM within ±0.6% of Q2 truth |
| **R2** | event-role identification must matter | **PASS** | the one-line mapping fails at 7–65 sd; six codes, four roles, two of which change role between the two questions |
| **R3** | textbook shortcut must fail | **PASS** | "use Aalen–Johansen" is necessary and not sufficient |
| **R4** | wrong-object tournament | **PASS** | 9 pre-registered wrong objects, biases 3.6–171 sd, directions all explained |
| **R5** | multiple valid implementations | **PASS** | AJ, cause-specific hazard integration, discrete multistate agree within 0.5% |
| **R6** | decision structure | **PASS** | 2 regimes high / 3 base, unanimous within regime; both decision-correct-analysis-wrong and decision-wrong cases present, flipping by regime |
| **R7** | distinctness after semantics handed over | **PASS** | separation 3.6–171 sd with the correct event table supplied |

## Kill criteria

None fires. The two that came closest:

- **K3** (one-line mapping solves it): the one-liner gets the *decision* right in all four regimes
  tested, but is 6–38% wrong on the graded quantities. Defeated by grading quantities, which is
  already policy.
- **K9 / K15** (semantics dominate, task becomes Task 02 / G08): explicitly tested by R7 and
  decisively refuted — this is the single most important result of the redesign.

## Why this succeeds where the original G34, G31 and G33 failed

The failure mode in all three was the same: **the mechanism that was supposed to make the task hard
did not move the graded quantity.** Left truncation moved it 7–10% (1.2–3.5 sd). Entity errors moved
G33's concentration metric 0.6–8%. G31's delay and verification legs moved nothing at all.

Here the mechanism moves the graded quantity by **36–188%**, and it keeps moving it when every piece
of semantic reconstruction is handed to the solver for free. The competing-risks structure is not
decoration on top of a reconstruction task; it is the task.

## What a build must fix first

1. **Shuffle row order** (currently `unit_id` order).
2. **Do not ship the regime name** — the pilot's `observed()` passes `spec`, which contains it.
3. **Adopt the informative-telemetry-gap version.** With independent gaps the "not an exit" role is
   inert (0.1 sd); with the realistic correlation it is 51 sd, and the correct method is unchanged.
4. **Either give `SITE_XFER` a real consequence or delete it.** It is currently decorative.
5. **State in the validation report** that a decision-only reading overstates performance here,
   because the one-line mapping gets the decision right while being 6–38% wrong.

## Assessments

**Realism.** A pump manufacturer's aftermarket planning dispute, a 24-month overhaul SOP, work-order
codes that do not map onto statistical roles, and a fleet where overhauls outnumber failures — a
reliability engineer would recognise all of it. The 55% in the incident is exactly what 1 − KM
returns, which is why the dispute is real rather than manufactured.

**Ambiguity.** Low. Every graded fact has named operational evidence. The one genuine subtlety —
that Q1 needs neither I2 nor I3 while Q2 needs both — is a feature: it is the reason Q1 is the safer
planning number, and noticing it is a mark of a good analysis rather than a requirement for a
passing one.

**Biggest remaining risk.** That a future model recognises "competing risks" and reaches for
Aalen–Johansen without thinking about retirement, gets the decision right, and a casual reading
scores it as a success. Mitigated by grading Q1, Q2, per-cause incidence and risk-set counts.

**S0–S9 placement.** Intended and measured at **S3–S4**: specifying which statistical object answers
which business question, and constructing it. S2 is present but explicitly not load-bearing (R7).
This is the first candidate in the pool to sit squarely at S3–S4 with S2 neutralised by test.

**Build complexity.** Comparable to G05: one generator, ~5 tables (asset register, work orders,
event dictionary, site register, extract metadata), ~4 documents (maintenance SOP, aftermarket
planning memo, engineering query, event dictionary), a verifier grading the event table, Q1, Q2,
per-cause incidence, risk-set counts and the decision. Roughly 3–4 days.

**Costs.** `harbor check` ≈ $0.5 per invocation, several invocations (validation-model spend, not
baseline). Gemini baseline 3 trials ≈ $0.50. Nothing to be spent until authorised.

## Distinctness

| Task | Distinct? | Why |
|---|---|---|
| Task 02 | **yes, by test** | R7 hands over all timestamp/state reconstruction and separation survives at 3.6–171 sd |
| G08 | **yes, by test** | same test; status-code semantics are handed over |
| G10 | yes | binary event time with an observed competing process, not a latent continuous quantity |
| G24 | yes | no propensities, no actions, no policy value |
| G05 | yes | no treatment, no counterfactual trend, no control group |
| G31 | yes | censoring here is independent by construction; the correct handling needs no reweighting |
| G33 | yes | no identity reconstruction |

**Recommendation: A — BUILD.** Not implemented. Awaiting explicit authorisation.
