# Phase 2 — concepts considered and rejected (and the admission test that killed each)

Admission-test numbering as in `framework.md`; failing #1, #3, #5, #6, #7, #8, #10 or #14 is fatal.

| # | concept | fails | why |
|---|---|---|---|
| R01 | "find the leaked feature" — a model with target leakage the agent must locate | **#3, #9** | a correlation scan against the label finds it; one commitment; the answer is discoverable mechanically rather than derived |
| R02 | Simpson's-paradox exercise: aggregate and subgroup disagree, no operational mechanism | **#8, #14** | nothing must be reconstructed from how the data came to exist; no practitioner would meet it in this bare form. (Kept only where a *mechanism* generates the composition shift and the decision needs the total effect — P15) |
| R03 | "duplicated rows inflate revenue" | **#5, #9** | one dedupe; no coherent wrong *science*, only a bug |
| R04 | multiple-comparisons / p-hacking clean-up of an experiment dashboard | **#6, #10** | no in-workspace evidence discriminates "which tests should have been run"; the graded object would be a convention |
| R05 | A/B test with sample-ratio mismatch whose cause is named in an incident ticket | **#3** | the answer is stated; this is phase-1's Task05 failure mode |
| R06 | "which of these two models is better" | **#2, #5** | no decision with a rule; no plausible coherent wrong interpretation |
| R07 | data-quality audit (nulls, types, referential integrity) | **#1, #9** | engineering hygiene, not scientific work; one commitment |
| R08 | forecast-accuracy improvement contest | **#5, #6** | a better score is not a wrong interpretation; nothing discriminates interpretations |
| R09 | contrived Berkson's-paradox / collider vignette | **#14, #6** | recognisable only as a textbook exercise; the discriminating evidence would have to be invented |
| R10 | "reconcile two dashboards" | **#8** | bookkeeping; nothing about the data-generating process |
| R11 | time-zone / operational-day bug hunt | **#5, #9** | one commitment; the wrong answer is not scientifically coherent, just off by hours. (Retained only as *texture* inside other tasks) |
| R12 | measurement-error / errors-in-variables estimation refinement (phase-1 G37) | **#10** | phase-1 gates measured the valid/wrong separation window at ratio ≈0.01 — estimator noise exceeds the bias, so it is identifiable but not gradable |
| R13 | regression-to-the-mean under threshold-triggered intervention (phase-1 G38) | **#10** | same: window ratio ≈0.00 at three realistic scales. (The mechanism is retained inside P33, where an RCT-grade counterfactual exists) |
| R14 | comparable-store sales for a covenant test (phase-1 G42-v1) | **#9** | every material mechanism collapsed to one population filter; the aggregation and calendar traps moved the number by under a basis point |
| R15 | line-capacity rollforward and first-breach month (phase-1 G43) | **#3** | every rule (shift calendar, maintenance, changeovers, yield, firm window) is stated in the shop-floor documents; a reading task |
| R16 | assay PPV transported to a routine population (phase-1 G44-v1) | **#10** | because every screen-positive is confirmed, the routine PPV is directly countable, so two defensible estimators disagree and neither is uniquely gradable |
| R17 | fairness audit with no decision rule | **#2, #10** | no threshold, no consequence, and the graded object becomes a normative choice |
| R18 | "the discriminating test requires data the workspace does not contain" — a family of drafts | **#6, #7** | the most common failure of the author's own first drafts; recorded because the fix is always the same: put a randomised stratum, a dual-instrumented period, a retained-sample archive or an independent aggregate into the world *at authoring time*, or drop the concept |
| R19 | "always contradict the published number" suites | — (design-level) | not a single concept but a structural bias: phase-1's five final tasks all have a wrong published number. Rejected as a *pattern*; the fix is the P31 archetype and hidden extracts that vary which side is right |

**Rate:** 19 rejections against 36 admissions at the concept stage. Phase-1's observed rate at the *build*
gate was that roughly half of well-motivated designs fail; the two rates compound, so the expectation for
phase 2 should be ~36 concepts → ~18 surviving build gates → 6 shipped.
