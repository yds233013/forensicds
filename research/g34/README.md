# G34 — survival / time-to-event analysis

**Status: design + simulation + adversarial testing only. FINAL RECOMMENDATION: A — BUILD (not implemented).**

> The first design was rejected; its record is preserved unedited below and in `event_process.md`,
> `simulation_results.md`, `adversarial_review.md`, `build_recommendation.md`. The redesign is in the
> `redesign_*` files and `build_recommendation_v2.md`.
No Harbor task, no `candidates/g34-*`, no model run, no API spend.

## What was tested

Domain: **industrial rotating-equipment fleet**, overhaul-interval decision. Condition-monitoring
platform went live mid-life, so units entered the observable record at their current age.

Core as designed: **time origin + delayed entry (left truncation)**, with planned overhaul as
independent censoring. Estimand: net probability of unplanned failure in age window (18, 30]
given failure-free at 18.

## Outcome of the FIRST design (rejected, preserved)

**The design as specified fails, but one untested variant is very strong, and it was tested.**

| Mechanism | Effect on the estimand | Separates? |
|---|---|---|
| wrong time origin (monitoring clock) | −48% | **8.2 sd — yes** |
| removal-reason misclassification (overhaul as event) | +148% | **25 sd — yes** |
| mature-cohort filtering | −67% | yes |
| naive event rate | −13% | marginal (2.2 sd) |
| **delayed entry / left truncation** | **−7 to −10%** | **1.2–3.5 sd — NO** |
| **competing risks (informative CBM variant)** | destroys identification of the estimand | **unusable** |

The two genuinely survival-specific mechanisms were respectively **inert** and **unusable**. What
separated — clock choice, status-code semantics, population filtering — are Task 02 / G08 / Task 03
shapes with a textbook Kaplan-Meier bolted on. That is kill criteria K12 and K14.

**But** a late test of the crude-risk variant (cause-specific cumulative incidence instead of net
risk, with planned overhaul as a competing event rather than censoring) separates at **40–65 sd**:
1 − KM overstates the CIF by **77–108%**. That is the canonical competing-risks error, it is
survival-specific, and identification is clean.

See `build_recommendation.md` for the redesign specification and its pre-registered kill criteria.

## Files

| File | Contents |
|---|---|
| `domain_tournament.md` | nine domains and ten candidate hard cores, scored |
| `event_process.md` | event-state machine, DGP, estimand, identification |
| `simulation_results.md` | five decisive tests with numbers, including two bugs found in my own code |
| `cheap_solve_results.md` | cheap-solve panel, constant-decision attack, leakage audit |
| `adversarial_review.md` | hostile review by reasoning and code — no model call |
| `cross_task_matrix.md` | S0–S9 placement and distinctness against all seven prior tasks |
| `build_recommendation.md` | the B verdict, the redesign spec, kill criteria |
| `simulation.py`, `methods.py`, `precheck.py` | generator; 3 valid families, 9 wrong methods, 7 cheap heuristics |


---

# REDESIGN (second and final attempt) — recommendation **A. BUILD**

Rebuilt around the competing-risks / crude-risk finding. Same domain, new business question:
an aftermarket spares-planning dispute where **1 − KM is the right answer to one question and the
wrong answer to the other**.

| Gate | Result |
|---|---|
| **R1** valid estimators vs latent truth | Aalen–Johansen within **±0.11%** of Q1 truth in all 5 regimes |
| **R7** separation with the correct event table handed over | **3.6–171 sd** — survival reasoning carries the task |
| **R3** textbook one-liner ("overhaul competing, rest censoring") | fails at **7–65 sd** |
| **R5** three valid implementations | agree within **0.5%** |
| **R6** decision structure | 2 regimes high / 3 base, unanimous within regime |

Three fixes required before a build: shuffle row order; stop shipping the regime name; adopt the
informative-telemetry-gap version and either give `SITE_XFER` a consequence or delete it.

Redesign files: `redesign_event_process.md`, `crude_risk_estimand.md` (folded into the former),
`redesign_simulation.py`, `redesign_methods.py`, `redesign_simulation_results.md`,
`wrong_object_tournament.md`, `cheap_solve_redesign.md`, `adversarial_redesign_review.md`,
`build_recommendation_v2.md`.
