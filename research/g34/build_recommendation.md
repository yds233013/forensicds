# G34 build recommendation

# **B. REDESIGN** — around the crude-risk / competing-risks core. Do not build the current design.

## 1. Why not A

Three measured disqualifiers for the design as specified:

1. **The survival-specific core is inert.** Left truncation moves the estimand by 7–10% against a
   correct-estimator sd of 2.3% (1.2–3.5 sd) and plateaus regardless of fleet age. Claiming it
   would repeat G31's inert-mechanism error.
2. **The other survival-specific mechanism is unusable.** Informative (condition-based) overhaul
   destroys identification — every estimator including the correct one lands 80% low. With
   age-based overhaul, treating it as independent censoring is *correct*, so the net-risk design
   contains no competing-risks content at all.
3. **What does separate is not survival reasoning.** Time origin (−48%) is Task 02's shape;
   removal-reason classification (+148%) is G08's shape; mature-cohort filtering (−67%) is
   Task 03 / G31's shape. After those, the statistics are one line. **K12 and K14.**

## 2. Why not C

The crude-risk variant was tested and is **an order of magnitude stronger than anything in the
net-risk design**: 1 − KM overstates the cause-specific cumulative incidence by **77–108%**,
at **40–65 sd**. That is survival-specific, it is the canonical competing-risks error, identification
is clean, and it is distinct from all seven existing tasks.

It is also a *different business question* — the fraction of units that actually fail before their
scheduled overhaul, which drives spares stocking and downtime budgeting, rather than whether to
extend the interval. A task could grade **both**, which would discriminate sharply: an analyst who
computes one quantity and uses it for the other decision fails, and that confusion is a genuine
survival-reasoning error rather than terminology recall.

## 3. What a redesign must establish, before anything is built

Pre-registered now so the decision cannot be made after seeing results.

| # | Requirement | Why |
|---|---|---|
| **R1** | **Verify Aalen–Johansen against generator truth**, not against 1 − KM | Test 5 compared two estimators to each other. AJ is theoretically consistent here, but this is unverified and is the single largest gap in the evidence |
| **R2** | The hard part must be **identifying which removals are competing events**, not choosing the estimator | otherwise it is K14, textbook recall. The four-reason removal taxonomy already supports this |
| **R3** | Grade **both** crude and net quantities, with the business documents making clear which decision needs which | this is what converts terminology into reasoning |
| **R4** | ≥2 valid families for the CIF (Aalen–Johansen, cause-specific hazard integration) agreeing within a few percent | K11. Note the first attempt here failed this until an actuarial correction was applied |
| **R5** | Regimes must vary the **hazard itself**, not only the observation process | four of five current regimes share the same truth (0.4048) |
| **R6** | Cheap-solve panel must include a one-line `lifelines` call and a constant decision, and both must fail | `C_km_default_no_thought` currently gets the decision right 7/7 |
| **R7** | Shuffle row order | records are currently emitted in `unit_id` order |

**If R1 fails, or if R2 cannot be made to carry the difficulty, drop the line.** Three consecutive
survival/observation-process designs failing would be sufficient evidence that this family of
capabilities is not buildable at our standard.

## 4. Assessments

**Realism** — good. An 18-month overhaul policy, a monitoring platform installed mid-fleet-life,
work-order removal reasons that do not map onto statistical categories, and 2351 failures against
5526 overhauls over 24 months are all operationally plausible. A reliability engineer would
recognise the incident.

**Ambiguity** — low, and this is a strength. Every graded fact has observable evidence (audit in
`cheap_solve_results.md`); the one assumption that matters (age-based vs condition-based overhaul)
is stated in a policy document and is checkable in the data.

**Biggest benchmark risk** — that the competing-risks variant reduces to knowing that 1 − KM is the
wrong estimator under competing risks. That is a fact, not a capability. R2 and R3 exist to prevent
it, and if they cannot, the task should be dropped.

**Build complexity** — comparable to G05: one generator, ~6 tables, ~5 documents, a verifier grading
risk-set state plus 4–6 numeric quantities plus the decision. Roughly 3–4 days after the redesign
gate passes.

**Estimated costs** — Harbor validation ~$0.5 per `harbor check` invocation, several invocations
(validation-model spend, not baseline); Gemini baseline 3 trials ~$0.50. **None to be spent until
R1–R7 are demonstrated.**

## 5. Process note

Two bugs in my own instruments were found before any conclusion was drawn: a generator producing
impossible records (`exit < entry`), caught by the "is this record even possible?" check that the
G33 post-mortem made mandatory; and a discrete-time estimator biased by mid-interval censoring,
caught by requiring valid families to agree. **Both would have produced a confidently wrong
recommendation.** The first appeared as a +36% bias in the *correct* estimator — which, had I not
stopped to isolate it, would have looked like evidence that the design was interesting.
