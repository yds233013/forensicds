# Phase 3 development log — scientific and engineering decisions

Chronological. Every entry is a decision that changed the science or the grading, with the reason. Defects found
in my own work are recorded as found, not silently fixed.

## Harness capability

**Criterion-level rewards are real in this installation.** Before designing the grading I read
`harbor/verifier/verifier.py` in the installed Harbor 0.21.0: lines 227–232 prefer `/logs/verifier/reward.json`
over `reward.txt` and parse it as a flat `dict[str, float|int]`; `harbor/cli/jobs.py:2061` uses the `"reward"`
key as the headline. Multi-step tasks and `StepConfig` also exist (`harbor/trial/multi_step.py`), but a
multi-step task would require splitting each incident into staged agent sessions, which changes what is being
measured; not adopted. `harbor check` invokes an LLM judge and was **not run** this phase.

## P22

1. **Calibrated the physics before writing any code.** σ_p = 13.3 µm and a ±30 µm tolerance give a 2.8 %
   nonconforming rate; a +8.2 µm offset takes the pooled rate to ~7.2 %. Both figures were chosen to match the
   plant story (97 % → 92.8 %), not to hit a difficulty target.
2. **Found and closed a one-document shortcut.** The first draft set the certificate's `as_left` figure to
   0.96 × the bore offset, so reading the certificate gave the answer to within 0.33 µm. Fixed by making the
   certificate report the deviation at the standard's length with a per-extract nuisance factor, which is what
   real metrology does; QP-07 §4 now states the non-mapping explicitly. The naive "scale by 42/100" route now
   errs by 0.5–2.2 µm and fails on 3 of 4 extracts.
3. **Found a defect in my own reference implementation.** The wear estimator fitted deviation on production
   week, which absorbed the week-19 heat-family step and reported 0.99 µm/week of wear where the design had
   none. Root cause: the generator's wear model accumulated across weeks, which is inconsistent with weekly
   insert changes. Reworked wear to be carried by `tool_hours`, so its slope is identified from variation inside
   each week and cannot absorb a step at the window boundary.
4. **Removed an unidentifiable graded quantity.** The operator component was defined as the absolute latent
   shift, which no estimator can recover: a shift common to every operator is not separable from a shift in the
   material. Redefined as the operator **contrast**, which a per-operator difference in differences does
   recover. Truth and the reference now agree to 0.04 pp on that component instead of 0.58 pp.
5. **Made the output contract hypothesis-symmetric.** An earlier draft asked for `bias_um`, which names the
   measurement hypothesis. Replaced with `conformance_reference_offset_um` per machine (traceable to QP-07 §3
   and to Schedule 3's own requirement to state the reference used) and `strata_nonconforming_rate_pct` over
   four strata, so the contract asks for the population breakdown without privileging any cause. The
   attribution vocabulary names all five candidate causes.
6. **Made "which rate does Schedule 3 name" consequential.** Discovered while enumerating mutations that no
   extract had the corrected rate and the material-attributable rate on opposite sides of the 5.5 % limit, so
   that commitment was not decision-relevant. Re-tuned hidden_c (extended insert-change interval, faster-wearing
   grade) so the two rates are 6.93 % and 3.85 %.
7. **Fixed a verifier defect the Nop run exposed.** A missing `corrected_nonconforming_rate_pct` silently
   **passed** `independent_validation`. Now fails.

## P20

8. **Rebuilt the generator loop.** The first version computed the as-of feature before any outcome existed, so
   in-window history never entered it and the model's strongest feature was almost always zero. Rewrote `build()`
   as a single chronological pass; the calling threshold now comes from the pre-programme score distribution,
   which removes the circularity and matches how a real programme fixes a threshold.
9. **Removed a look-ahead leak.** The as-of count included events dated after the booking date. Now bounded by
   `cutoff <= event < booked_on`, which is both correct and exactly reconstructible from the append-only log —
   the precondition for the vintage falsification route existing at all.
10. **Separated two mechanisms that one parameter controlled.** History density decides how informative the
    feature is; the backfill window decides how far the vintage moved it. Split into `seed_history_*` and
    `current_window_days`, so the visible extract is policy-feedback-dominant and hidden_c is vintage-dominant.
11. **Abandoned drift-as-shrinkage.** Weakening the coefficients lowers the achievable discrimination for *any*
    model, so no retrained candidate can win and `replace_with_v4` was unreachable. Replaced with a driver of
    attendance that postdates the model (`interpreter_required`), which the incumbent cannot see and a model
    fitted on recent data can. A coefficient rotation alone was also tried and rejected: it raised the
    incumbent's AUC instead of lowering it.
12. **Added the feed-defect mechanism and a fourth decision.** A failed enrichment join defaults every column it
    supplies, so the served scores lose their inputs while the outcome does not. MRM-04 §4.4 now states feed
    integrity **first**, which makes `remediate_feature_pipeline` correct on hidden_b and
    `replace_with_v4` the trap there.
13. **Do not grade a model the agent trains.** Its AUC depends on the model class, so it is not identifiable.
    The candidate is shipped as scores instead, which makes "is the candidate better on a policy-invariant
    population" a deterministic question.
14. **Moved the dashboard population to the whole network.** The vendor monitors everything and does not
    separate the excluded clinics; that is the realistic default and it makes separating them the discovery.
15. **Replaced a weak criterion.** `independent_validation` was internal closure of the decomposition, which the
    incumbent satisfies (it puts the whole gap in one term), so Nop scored 1 on it. Now it also requires the
    reported as-served figure to be what the shipped scores give **on the population the readout declares**.

## P31

16. **Completed the design the handoff left open.** P31's A–Z entry specifies the mechanism but no deferral
    outcome; the brief requires grading to distinguish justified deferral. Added Schedule 4, unexecuted on the
    measurement basis for amended lines, with dated correspondence confirming it was never agreed. Recorded as a
    deviation.
17. **Replaced order fill with case fill.** Order fill at requested quantity gives 7.6 %, which no supplier
    would publish. Case fill at requested quantity gives 91.6 %, which is the disagreement that actually occurs
    between a retailer and a supplier.
18. **Reordered the bridge.** Denominator-first produced a −29.8 pp step followed by +25.1 pp. Aggregation-first
    gives +2.1, −6.5, −1.5, −0.03 — the same exact decomposition, readable as a management explanation.
19. **Made the incumbent's defect latent rather than per-extract.** The shipped code is fixed, so a defect
    cannot be switched on per extract. The code counts its denominator with `COUNT(confirmed_qty)`, which skips
    lines with no confirmation — exactly the lines §7.2 counts as unfilled. `null_confirm_share` is zero on
    three extracts and 4.5 % on one, so the same code is correct on three and 4.47 pp wrong on one. This is
    better than the original design: the question becomes "is it right **on this extract**".
20. **Settled each consequence independently.** An earlier version reported both the bonus gate and the claim as
    `not_determinable` whenever Schedule 4 was material. On hidden_c the two readings agree on the gate and
    differ on the claim, so the honest answer is `no` and `not_determinable` respectively. Refined.
21. **Graded the below-floor count to ±1.** On two extracts an account sits within 0.07 pp of the floor. The
    substantive tail is graded through the escalating accounts' own rates, which are 1–7 pp below it.

## Rejected during this phase

* A `bias_um` field in P22's contract — names the answer's hypothesis (see 5).
* Grading P22's absolute operator shift — unidentifiable (see 4).
* Grading a P20 model the agent trains — not identifiable (see 13).
* Drift as coefficient shrinkage in P20 — makes the correct action unreachable (see 11).
* Order fill as P31's supplier metric — not plausible (see 17).
* Grading P31's below-floor count exactly — grades precision at a knife edge (see 21).
