# Audit 2026-09-23 — failure-label revisions required by the evidence

The report's §5 table assigns 10/13 failed final-suite trials to **F9 (right method family, wrong
statistical object)**. Re-derived trial by trial from trajectories, submitted code and verifier output,
that count does not hold. F9 requires *both* that the method family was substantially right *and* that
the object receiving it was wrong. Several trials fail the second half: the object was right and the
**estimator or its execution** was wrong, which is F4.

| trial | report label | audit label | why |
|---|---|---|---|
| g24 a8zVL7h | F9 | **F9-A** (+F9-G, F7, F10) | slot-exact IPS correct; weighted by the **pre-filter** pool `candidate_count` (K) while the target slates were built from the **eligible** pool (m) — the estimator's action space contradicts the policy's |
| g24 wVmAykK | F9 | **F9-A** (+F9-G, F7, F10) | same K-vs-m error, plus every *serve* treated as a decision unit |
| g24 ykNY8fD | F9 | **F9-G** (+F7, F10) | the only trial to derive the eligible-set propensity correctly; lost on the decision unit (kept only creating serves, discarded cached re-serves' clicks) |
| g34 UPCLpLx | F10 (in `research/g34/…`) | **F4** (+F7) | the object was right (four competing-risk outcomes, correct schema, correct prose); the estimator divided by the full cohort `n` instead of the risk set `n − i`. **F10 cannot apply: its business decision was wrong** (`baseline` vs `expanded`) |
| g08 h7TpDUG | F0 (in `research/g08/…`) | **F9-T** (+F0 scoped to the actual side) | forecast-side point-in-time reconstruction correct and passing its checks; scored against the latest reconciliation volume rather than the imbalance-charge basis — a different quantity |
| g08 wmwSU97 | — | **F4** (+F2, F3) | named all five defect classes correctly in prose, then implemented the forecast lock at issue grain and never loaded `run_status_history` |
| task02 JctTpSi | F7 (in `research/task02_…`) | **F4** (+F7) | its repair mis-valued 1,538 of 2,896 `health_score` values by dropping the per-example cutoff from the dedupe key — that is a broken repair, not a substantially correct one |
| task02 nXXMdDm | F4 | **F4** (+F7) | agreed |
| task02 pf9zaPc | F4 | **F4** (+F9-T secondary, F7) | used `changed_at` (source commit time) instead of `synced_at` (warehouse availability) throughout |
| task04 3SUW3gh | F4 | **F4** (+F7) | correct lifecycle repair plus one unwarranted extra rule imported from a README description of a *different artefact* |
| task04 AEZ8pU4 | F4 | **F4** (+F7) | same, and it stated the correct principle before reversing it |
| task01 DuhAh5u | F5 | **F3** (+F1; F9-T defensible) | never opened the governing identity standard; shipped a `sort_values`+`drop_duplicates` patch over the unchanged wrong join |

**Revised F9 count for the final five: 4 of 13** (g24 ×3, task02 pf9zaPc as a secondary), not 10 of 13,
under a strict reading. If G08 h7TpDUG is counted (G08 is not in the final five), the measured pool
contains 5 clear F9s.

**The dominant label across the measured pool is F4** — root cause correctly identified, repair
semantically wrong — usually accompanied by **F7** (no validation that could have exposed it).

## Proposed taxonomy revision

The evidence separates two things the current F9 conflates, and adds one the taxonomy lacks:

- **F9 (object)** — the method family is right and the *quantity it is applied to* is wrong: wrong
  population, grain, temporal state, denominator, counterfactual, action space, decision unit,
  resource set, hierarchy or economic object. Keep, with the subtypes; require the evidence bar.
- **F4 (execution)** — the object is right and the *estimator implementing it* is wrong. This is the
  majority label and the current write-up under-counts it.
- **NEW — F11 (coherence stopping)**: the agent ran a check, obtained agreement, and treated agreement
  as confirmation when the check could not have discriminated. This is not "no validation" (F7); it is
  validation whose discriminating power is zero, and it is what actually terminated most trials.
  Evidence: g24 wVmAykK computing position-wise IPS (0.305) against an on-policy figure (0.2975)
  **at the same wrong grain** and calling it "astonishingly close… highly accurate"; g08 h7TpDUG
  matching the January pack at one decimal place with every actual drawn from the wrong run type;
  task02 nXXMdDm and pf9zaPc accepting AUC 0.7697/0.7698 as confirmation against a correct 0.7806;
  task04 3SUW3gh reproducing six published quarters exactly by adopting the rule that produced them.
