# G34 — survival / time-to-event analysis

**Status: design + simulation + adversarial testing only. Recommendation: B — REDESIGN.**
No Harbor task, no `candidates/g34-*`, no model run, no API spend.

## What was tested

Domain: **industrial rotating-equipment fleet**, overhaul-interval decision. Condition-monitoring
platform went live mid-life, so units entered the observable record at their current age.

Core as designed: **time origin + delayed entry (left truncation)**, with planned overhaul as
independent censoring. Estimand: net probability of unplanned failure in age window (18, 30]
given failure-free at 18.

## Outcome

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
