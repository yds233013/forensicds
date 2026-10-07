# HANDOFF — G50 final pre-target validation
**Date:** 2026-09-29 · **Task:** `candidates/g50-courier-boost-rollout`
**Verdict: NOT READY. Two stop conditions fired. The Harbor verifier was deliberately not built.**
**Zero target-model exposures. Nothing committed.**

---

## 1. EXECUTIVE VERDICT

The scientific freeze reproduced exactly (28/28 files, aggregate `0dbc9470ed483848`) and the truth table
reproduced exactly. I then stopped, twice, before building the verifier:

> **STOP 1 — the frozen `instruction.md` does not establish an execution contract.** It says "leave the code
> that produced them in `/workspace`" but never names the command the verifier will re-run. Every other
> ForensicDS task states it explicitly (P22: *"Leave the repaired package in place, with `python -m quality
> report --db data/inspection.sqlite --out out` producing the outputs."*). Without that sentence, an agent who
> writes a standalone `analysis.py` and leaves `northline_eval` untouched **satisfies the instruction** while
> defeating re-execution — the verifier would re-run the unmodified incumbent and fail a correct submission.
> Fixing this requires editing a manifest-covered file, which §0 forbids me from doing silently.

> **STOP 2 — three procedures that the v2 specification declares invalid are numerically indistinguishable
> from the reference on all four worlds.** Measured deviations from latent truth (reference = 0.949 max):
> withdrawn R2 **0.848**, post-treatment weighting **0.983**, a wrong one-week pre-period window **1.002**.
> R2 is *closer to truth than the reference on three of four worlds*. No tolerance that admits the reference
> can reject them, and the frozen output contract contains no field that distinguishes them. The v2
> invariants "R2 remains withdrawn" and "post-treatment weighting must not substitute for pre-treatment
> weights" are therefore **unenforceable by any verifier built on the frozen contract**.

STOP 2 is the substantive finding and it is not a verifier engineering gap. It is a property of the task.
§11 and §28 of the brief make it an immediate stop, and it is a decision for ChatGPT, not for me: either the
invariants are relaxed with stated reasons, or the contract or DGP has to change.

## 2. PRE-VERIFIER MANIFEST VERIFICATION

**PASS. 28 covered files, zero drift, aggregate digest `0dbc9470ed483848` — matches the expected value.**

Recomputed with Python (`hashlib.sha256` per file, compared against the manifest body; body re-hashed for the
aggregate).

**Disclosure about my own process:** my first verification attempt was a shell loop that reported all 28 files
as drifted. That was a bug in the check — `cut` failed inside the loop, so every "current" hash came back
empty. I re-ran it in Python before reporting anything. No file had drifted. I am recording this because a
false freeze-break report would have been worse than the bug.

## 3. FILES CREATED / MODIFIED

**No file inside `candidates/g50-courier-boost-rollout/` was created, modified or deleted in this turn.** The
manifest proves it.

Created at the repository root: `HANDOFF_G50_FINAL_PRETARGET_VALIDATION.md` (this file).

No existing ForensicDS task, verifier, tolerance, hidden extract or prospective artifact was touched;
`research/phase3/analysis_plan.md` and the five-task fallback archive are unchanged (§32).

## 4. VERIFIER ARCHITECTURE

**Designed, not built.** The intended architecture, for the record:

- `tests/test.sh` on the P22/G24 pattern: kill agent-orphaned processes by start time excluding the container's
  own stdio-sharing main command; `chown` the workspace to `nobody`; `chmod 700 /tests` with refuse-to-grade if
  the pipeline user can read it; runtime-manifest integrity check against the pinned base image; reject stray
  `pytest.ini`/`conftest.py`; build an isolated verifier venv with `-S`, `--isolated --no-index
  --require-hashes` from `tests/wheels/`; run pytest with `--noconftest -c /dev/null`; write `reward.txt` and a
  flat `reward.json` merging `criterion_*` keys.
- `tests/test_boost.py`: for each of the four extracts, regenerate the warehouse from the frozen generator into
  a scratch workspace, delete `out/`, re-execute **the agent's submitted procedure**, and compare
  `out/readout.json` and `out/market_week_panel.csv` against `world.truth()`.
- The agent's pipeline runs as `nobody` via a `PIPELINE_PYTHON` shim so it cannot read `/tests`.

**The blocking gap is the third bullet's first clause.** "Re-execute the agent's submitted procedure" requires
knowing what to execute. See STOP 1.

## 5. FINAL OUTPUT CONTRACT

Verified against the frozen `docs/outputs/readout_contract.md`: **exactly 8 fields**, and
`control_arm_vs_holdout_pp` and `analysis_unit` are **absent** (grep count 0). Nothing removed during the
scientific audit has been restored, and I added no benchmark-shaped field.

`out/market_week_panel.csv` — `market_id, week_start, orders, late_orders, late_rate_pct, boost_share,
courier_hours`.

`out/readout.json` — `orders_analysed`, `order_arm_contrast_pp`, `programme_effect_pp`,
`programme_effect_ci_low_pp`, `programme_effect_ci_high_pp`, `inference_unit_n`,
`courier_hours_response_pct`, `decision`.

**Finding against §3's escape clause.** The frozen contract *can* support trustworthy verification of the
decision, the headline quantity, the panel, the population and the inference unit. It **cannot** support
verification of *which weighting basis* or *which identification route* produced the number, because it
exposes no field that differs between the reference and the three invalid procedures in STOP 2. That is the
mechanism of STOP 2.

## 6. CRITERION-LEVEL GRADING

Designed; the observable final-state evidence for each, and which are discriminating:

| criterion | observable evidence | discriminating? |
|---|---|---|
| `evidence_reconstruction` | `market_week_panel.csv` rows/columns match the regenerated panel; `orders_analysed` exact | **yes** — catches eligibility, zone→market, cancelled-order and week-alignment errors |
| `scientific_object` | `order_arm_contrast_pp` within 0.25 pp **and** `programme_effect_pp` not equal to it | **yes** for the incumbent; **no** for R2/post-weighting |
| `identification` | `inference_unit_n` ≤ 40, and `courier_hours_response_pct` within tolerance | **yes** for order-level inference; partial for the rest |
| `estimator_implementation` | panel `boost_share`, `courier_hours` columns | **yes** |
| `quantitative_result` | `programme_effect_pp` within 1.518 pp of latent truth | **yes** for the naive and unadjusted routes; **no** for R2/post-weighting/wrong-window |
| `uncertainty` | interval contains truth, width within band, **wider than the arm-contrast interval** | **yes** — this is the pseudoreplication catch |
| `decision` | exact string match | partial — right on 2 of 4 worlds for the incumbent |

Overall reward = conjunction over all seven criteria on all four worlds. A correct decision alone cannot pass
(it fails `quantitative_result` and `uncertainty`); a correct number alone cannot pass (it fails `uncertainty`
and, for a hardcoded value, the multi-world re-execution).

## 7. MULTI-WORLD EXECUTION DESIGN

Designed: regenerate each extract deterministically into a private scratch tree; copy the agent's `/workspace`
code but not its `out/`; run the procedure; compare. World names and scenario parameters never reach the
submission; `out/` is deleted before every run so world *N*'s output cannot satisfy world *N+1*.

**Not implemented** — blocked by STOP 1.

## 8. RECOMPUTED TRUTH TABLE

Recomputed independently from the frozen generator (not copied from the handoff). **Reproduces
`HANDOFF_G50_V2_SCIENTIFIC_SPEC.md` §19 exactly.**

| world | latent truth | reference est. | error | 95 % interval | arm contrast | courier hrs | inference units | orders | late rate | decision |
|---|---|---|---|---|---|---|---|---|---|---|
| visible | **+2.187** | +1.241 | 0.946 | [−1.39, +3.87] | −5.111 | +2.86 % | 16 | 115,424 | 20.48 % | `do_not_roll_out` |
| hidden_a | **−10.064** | −10.187 | 0.123 | [−13.33, −7.04] | −6.519 | +24.36 % | 16 | 108,418 | 17.08 % | `roll_out` |
| hidden_b | **+5.267** | +4.318 | 0.949 | [+2.33, +6.30] | −4.324 | +1.76 % | 16 | 121,035 | 18.32 % | `do_not_roll_out` |
| hidden_c | **−9.871** | −9.410 | 0.461 | [−11.86, −6.96] | −5.388 | +12.32 % | 16 | 89,448 | 15.27 % | `roll_out` |

Break-even recomputed from the memo's own figures (0.19 / 12.70 × 100) = **1.4961 pp**. Pre-programme market
weights span 0.028–0.131 across worlds. Metric population = delivered, `order_channel = 'standard'`. Target
period = the phase-1 window. All as specified.

**One apparent mismatch, traced to my own audit script and corrected.** My first pass computed the arm
contrast over all phase-2 orders in the metric population, which silently placed the four never-enrolled
markets' orders in the control arm (they carry no `arm` label, so `boosted` is false). That gave −3.980 /
−7.014 / −2.373 / −5.407. Restricting to enrolled, arm-labelled orders gives −5.111 / −6.519 / −4.324 /
−5.388, which matches `world.truth()` and the handoff to the fourth decimal. **The task was right; my script
was wrong.** Usefully, this is exactly v1 mutation M12 ("holdout markets included in the phase-2 control arm")
and it shifts the contrast by up to 1.95 pp — comfortably outside a 0.25 pp tolerance, so that mutation is
demonstrably catchable.

## 9. COMPLETE TOLERANCE TABLE

Recalibrated from the frozen task, not taken from the handoff. Rule: `max(1.0, 1.6 × worst reference
deviation)`, absolute, in percentage points.

| field | authoritative quantity | tol | abs/rel | justification | reference deviation per world | worst legitimate alternative | incumbent | minimum separation |
|---|---|---|---|---|---|---|---|---|
| `programme_effect_pp` | `world.truth()["rollout_effect_pp"]` | **1.518** | abs | 1.6 × worst reference deviation (0.949). The residual is estimator sampling error from 16 clusters with heterogeneous effects, not bias | 0.946 / 0.123 / 0.949 / 0.461 | D_mu 1.272 | 3.05–7.64 | **3.050** → ratio **2.01** |
| `order_arm_contrast_pp` | arm contrast on enrolled, arm-labelled metric population | **0.25** | abs | a fully specified data functional; two independent implementations agree to <0.03 | ≤0.025 | — | ≤0.025 (passes by design) | M12 shifts it 0.02–1.95 |
| `courier_hours_response_pct` | `courier_supply_response_pct` | **1.40** | abs | 1.6 × worst reference deviation (0.853) | 0.010 / 0.742 / 0.853 / 0.510 | — | 1.96–22.42 | **1.957** → ratio **1.40** |
| `orders_analysed` | metric-population count | exact | — | integer count | 0 | 0 | 0 |
| `inference_unit_n` | ≤ 40 | threshold | — | separates market-level from order-level inference | 16 | 16 | 89,448–121,035 | decisive |
| interval | contains truth; width in [0.25, 4.0] × reference; wider than the arm-contrast interval | — | rel | the pseudoreplication catch | — | — | arm interval ≈ ±0.45 pp vs reference ±2.5–3.1 pp | decisive |
| `decision` | memo rule on latent truth | exact | — | margins 3.68–8.57 pp from break-even | 0 | 0 | wrong on 2 of 4 |

**Boundary behaviour is not yet tested** (needs the verifier). Two ratios are below the ≥3 heuristic:
`programme_effect_pp` at 2.01 and `courier_hours_response_pct` at 1.40. Both reject the incumbent on every
world.

**§8's escape clause is engaged.** Legitimate and illegitimate science *cannot* be separated on
`programme_effect_pp` by any defensible tolerance — see §11. That is STOP 2.

## 10. LEGITIMATE ALTERNATIVE RESULTS

Deviation from latent truth, per world, tolerance 1.518:

| route | visible | hidden_a | hidden_b | hidden_c | max | verdict |
|---|---|---|---|---|---|---|
| **D_ow** pre-adjusted, estate-weighted, WLS/HC1 at market (reference) | 0.946 | 0.123 | 0.949 | 0.461 | 0.949 | ✅ passes |
| **D_panel** weighted two-way FE panel, treat × post | 0.936 | 0.108 | 0.948 | 0.442 | 0.948 | ✅ passes |
| **D_pool** arm-level pooled pre/post | 0.924 | 0.244 | 1.046 | 0.439 | 1.046 | ✅ passes |
| **D_mu** pre-adjusted, market-unweighted | 0.733 | 0.496 | 1.272 | 0.299 | 1.272 | ✅ passes (different weighting, acknowledged in v2) |

All four legitimate routes pass on all four worlds. **No verifier overfitting to the reference on this axis.**
Intervals and `inference_unit_n` were computed for D_ow only (WLS/HC1, 16 units); the other three would need
their own interval procedures, which is verifier work not reached.

## 11. R2 WITHDRAWAL TEST — **FAILED**

Implemented R2 as specified: market-week panel regression of late rate on realised boost share over all
enrolled weeks, with market and week fixed effects, weighted by market-week orders, coefficient read as the
S=1 vs S=0 contrast.

| world | R2 estimate deviation from truth | reference deviation |
|---|---|---|
| visible | **0.848** | 0.946 |
| hidden_a | **0.274** | 0.123 |
| hidden_b | **0.448** | 0.949 |
| hidden_c | **0.301** | 0.461 |
| **max** | **0.848** | 0.949 |

**R2 is numerically closer to latent truth than the reference estimator on three of four worlds, and has a
smaller worst-case deviation.** It passes `quantitative_result` on every world at any tolerance that admits
the reference. It also supplies a market-clustered interval and `inference_unit_n = 16`, so it passes
`identification` and `uncertainty` as designed.

**Which criteria fail to distinguish it: all seven.** R2 reconstructs the same panel, reports the same arm
contrast, computes a number inside tolerance, clusters at the market, produces a plausible interval, and
reaches the correct decision on all four worlds. The frozen contract exposes nothing that differs.

I did not blacklist the method. The brief requires rejection on procedural grounds, and there are none
available: R2's defect is that its *justification* is circular (it presupposes the mean-preserving priority
mechanism the task exists to diagnose), and a verifier grading final state cannot observe a justification.

**Per §11 and §28: STOP.**

## 12. V1 → V2 MUTATION MAPPING

| v1 ID | original defect | status | v2 equivalent | expected | reason |
|---|---|---|---|---|---|
| M00 | reference unmodified | **STILL VALID** | M00 | 1 | — |
| M01 | incumbent arm contrast as programme effect | **STILL VALID** | A | 0 | measured: rejected 3.05–7.64 pp |
| M02 | correct effect, `analysis_unit = "order"` | **MODIFIED** | G (`inference_unit_n` = order count) | 0 | field replaced in v2 |
| M03 | `analysis_unit = "market"`, arm contrast as the number | **MODIFIED** | C | 0 | same field replacement |
| M04 | phase-1 contrast at order level (pseudoreplication) | **STILL VALID** | E | 0 | interval-width criterion |
| M05 | market-level effect, order-level two-proportion interval | **STILL VALID** | E/F | 0 | interval-width criterion |
| M06 | correct effect, wrong decision | **STILL VALID** | S | 0 | — |
| M07 | correct decision, arm contrast as the number | **STILL VALID** | T | 0 | — |
| M08 | hard-coded visible readout | **STILL VALID** | W | 0 | needs multi-world re-execution |
| M09 | `control_arm_vs_holdout_pp` without pre-differencing | **REMOVED** | — | — | field removed from the v2 contract (§16 of v2) |
| M10 | phase-1 on/off swapped | **STILL VALID** | L | 0 | measured: rejected 3.43–20.25 pp |
| M11 | soak markets taken as all 16 rather than the 8 on | **STILL VALID** | M | 0 | — |
| M12 | holdout markets in the phase-2 control arm | **STILL VALID** | Q-adjacent | 0 | measured: shifts arm contrast 0.02–1.95 pp |
| M13 | cancelled orders counted as not-late | **STILL VALID** | O | 0 | — |
| M14 | courier hours not divided by orders | **STILL VALID** | R | 0 | — |
| M15 | R2 panel regression | **STATUS REVERSED TWICE** | X | was "must pass" in v1 → "must fail" in v2 → **now measured indistinguishable** | STOP 2 |
| M16 | market-level DiD against the pre-period | **SUPERSEDED** | — | — | this *became* the v2 reference |
| M17 | always `roll_out` | **STILL VALID** | U | 0 | fails on visible + hidden_b |
| M18 | always `do_not_roll_out` | **STILL VALID** | V | 0 | fails on hidden_a + hidden_c |

New in v2: H (post-treatment weighting), I (wrong pre-period window), J (equal-market weighting = D_mu),
K (wrong target period), N (phase-2 treated as market-level), P (eligibility/channel), Y (missing
uncertainty), Z (missing executable analysis).

## 13. COMPLETE V2 MUTATION RESULTS

Estimator-class mutations were measurable **without** the verifier, by computing each procedure's estimate on
all four worlds and comparing with latent truth. Artifact-class mutations (hardcoding, stale output, malformed
JSON) require the verifier and were **not reached**.

| id | mutation | expected | measured deviation per world | actual | intended reason? |
|---|---|---|---|---|---|
| A | incumbent arm contrast as programme effect | 0 | 6.17 / 3.05 / 7.64 / 4.46 | **rejected on all 4** | ✅ |
| D | phase-1 market-level, raw post-only, estate-weighted | 0 | 3.10 / **0.26** / 3.72 / **0.59** | rejected on 2 of 4 | ⚠ partial — fails the suite, not every world |
| D′ | raw post-only, market-unweighted | 0 | **0.31** / **0.44** / 7.54 / **0.33** | rejected on 1 of 4 | ⚠ partial |
| **H** | **post-treatment realised-volume weighting** | **0** | 0.949 / 0.145 / 0.983 / 0.494 | **PASSES ALL 4** | ❌ **STOP 2** |
| **I** | **wrong pre-period window (last week only)** | **0** | 1.002 / 0.067 / 0.945 / 0.448 | **PASSES ALL 4** | ❌ **STOP 2** |
| J | equal-market weighting (= D_mu) | pass per v2 | 0.733 / 0.496 / 1.272 / 0.299 | passes all 4 | ✅ as v2 intends |
| L | phase-1 arms swapped | 0 | 3.43 / 20.25 / 9.59 / 19.28 | **rejected on all 4** | ✅ |
| Q-adj | holdout markets in the phase-2 control arm | 0 | arm contrast shifts 0.02–1.95 pp | rejected where >0.25 | ✅ on 2 of 4 |
| U | always `roll_out` | 0 | wrong decision on visible, hidden_b | rejected | ✅ |
| V | always `do_not_roll_out` | 0 | wrong decision on hidden_a, hidden_c | rejected | ✅ |
| **X** | **withdrawn R2** | **0** | 0.848 / 0.274 / 0.448 / 0.301 | **PASSES ALL 4** | ❌ **STOP 2** |
| B, C, E, F, G, K, M, N, O, P, R, S, T, W, Y, Z | — | 0 | — | **NOT REACHED** | verifier required |

11 of 26 mutations measured; **three fail to be rejected**, and all three are procedures the v2 specification
declares invalid.

## 14. RIGHT-DECISION-WRONG-SCIENCE RESULTS

Partially reached.

| submission | decision correct? | rejected? | by which criterion |
|---|---|---|---|
| incumbent on **hidden_a** | yes (`roll_out`) | **yes** | `quantitative_result` (3.05 pp), `identification` (`inference_unit_n` = 108,418), `uncertainty` (interval ±0.45 pp) |
| incumbent on **hidden_c** | yes (`roll_out`) | **yes** | same three |
| correct decision + arm contrast as the number | yes | **yes** | `quantitative_result`, `uncertainty` |
| correct decision + unadjusted estimator where it happens to agree | yes | **only on some worlds** (D′ rejected on 1 of 4) | fails the suite via hidden_b |
| correct decision + hardcoded number | yes | **NOT TESTED** | needs multi-world re-execution |
| correct decision + wrong inference unit | yes | **NOT TESTED** | criterion designed, verifier not built |

No tested case passed. Two cases remain untested because they depend on the blocked execution contract.

## 15. VERIFIER ATTACK RESULTS

**NOT REACHED.** All ~30 attacks in §15 of the brief depend on a built verifier. None was run. I will not
claim any attack result I did not execute.

## 16. REPRODUCIBILITY RESULTS

**NOT REACHED** for the Harbor path. What *was* established in the v2 turn and re-confirmed here: the
generator is deterministic (same seeds → identical truth table across runs), and the reference solution
reproduces its own artifacts when run from a clean workspace with `out/` removed. The hash-level
delete-rerun-compare protocol was not run.

## 17. HARBOR ORACLE RESULT

**NOT RUN.** No verifier exists, so there is nothing for Harbor to grade. The reference was validated outside
Harbor in the v2 turn: passes all four worlds, errors 0.946 / 0.123 / 0.949 / 0.461.

## 18. HARBOR NOP RESULT

**NOT RUN**, same reason.

## 19. INCUMBENT RESULT

Not through Harbor. Measured end to end through the incumbent package in the v2 turn, and the estimator-level
numbers re-confirmed here:

| world | `programme_effect_pp` | dev | `inference_unit_n` | courier hrs | dev | decision | verdict |
|---|---|---|---|---|---|---|---|
| visible | −5.119 | 7.31 ✗ | 115,424 ✗ | +0.557 | 2.31 ✗ | wrong ✗ | FAIL |
| hidden_a | −6.494 | 3.57 ✗ | 108,418 ✗ | +1.944 | 22.42 ✗ | right, wrong quantity | FAIL |
| hidden_b | −4.322 | 9.59 ✗ | 121,035 ✗ | −0.201 | 1.96 ✗ | wrong ✗ | FAIL |
| hidden_c | −5.392 | 4.48 ✗ | 89,448 ✗ | +0.727 | 11.60 ✗ | right, wrong quantity | FAIL |

**It fails for the right reasons, which is the strongest available result.** It runs cleanly, reconstructs the
evidence correctly, computes the arm contrast correctly (deviation ≤0.025 pp on all four — it would pass
`evidence_reconstruction` and the `order_arm_contrast_pp` half of `scientific_object`), and produces
schema-valid artifacts. It fails on the scientific object, the quantity, the inference unit and the
uncertainty — not on plumbing.

## 20. CLEAN CONTAINER RESULT

**NOT REACHED.** No `docker build` was attempted this turn. The Dockerfile is unchanged and manifest-covered.

## 21. RUNTIME / PERFORMANCE

Measured on the host, not in a container: world generation ≈ 5–6 s per extract; SQLite ≈ 55 MB per extract;
full reference analysis ≈ 20–30 s per extract. A four-world verifier would therefore cost roughly 2–3 minutes
of generation plus analysis, well inside the 5,400 s verifier timeout. **No optimisation was applied, so no
before/after numerical-identity proof is needed.**

## 22. POST-VERIFIER LEAKAGE AUDIT

**Workspace-level audit re-confirmed** (unchanged from the pre-exposure turn): zero occurrences of
`interference`, `SUTVA`, `spillover`, `displacement`, `zero-sum`, `redistribut`, `saturation`, `cluster`,
`pseudorep`, `unit of analysis`, `contaminat` in any agent-visible file; no truth constant present; no
generator, scenario, truth or manifest file inside `environment/workspace/`; the Dockerfile is multi-stage so
`environment/build/world.py` is absent from every layer of the final image.

**Image-level, layer-level, environment-variable, mount, PATH and git-metadata audits: NOT REACHED** — they
require the built image and the verifier files, neither of which exists.

## 23. SCIENTIFIC CONSISTENCY AUDIT

Frozen files checked against `HANDOFF_G50_V2_SCIENTIFIC_SPEC.md`:

| invariant | status |
|---|---|
| business estimand = estate-wide late-delivery effect | ✅ verbatim in the memo |
| weights = pre-programme share of estate orders | ✅ in the memo; ✅ implemented in `truth()` |
| target conditions = programme-period | ✅ memo; ✅ truth evaluated on the phase-1 window |
| phase 1 = market-level randomisation at full saturation | ✅ `experiment_config`, plan |
| phase 2 = order-level inside a shared pool | ✅ plan, dispatch note |
| phase 2's arm contrast is not the rollout estimand | ✅ nothing in the workspace claims it is |
| pre-period adjustment is accuracy, not identification | ✅ not mislabelled anywhere |
| `control_arm_vs_holdout_pp` not required | ✅ absent from the contract |
| holdout = optional independent validation | ✅ |
| reference estimator ≠ latent truth | ✅ four levels kept distinct |
| legitimate alternatives accepted | ✅ four routes pass |
| **R2 remains withdrawn** | ❌ **unenforceable** — §11 |
| **post-treatment weighting rejected where invalid** | ❌ **unenforceable** — §13 H |

Eleven of thirteen hold. The two failures are STOP 2.

## 24. HARBOR CHECK — EVERY CRITERION

**NOT RUN.** §24 of the brief gates it behind "all deterministic validation above passes". It did not pass.
Running an LLM evaluator now would spend money to audit a task with two known blocking defects.

## 25. REVIEWER A — senior marketplace experimentation scientist

*"The science of the world is right and I said so last time. What I would now say is that your validation has
found something more interesting than a bug: the boost-share regression gets the right answer here. That is
not an accident of your tolerance, it is because your dose-response is close to linear and your priority
mechanism is mean-preserving. In a real marketplace I would expect curvature and I would not trust that
regression — but in **this** world it works, and you cannot grade a justification.*

*My honest read is that you have to choose. Either accept it as a valid route in this world and say why, or
change the world so the curvature is big enough that the regression is visibly wrong. You cannot keep the
withdrawal and also keep the world."*

**Objections:** R2 unenforceable → **BLOCKING**. Everything else from the v2 review → unchanged.

## 26. REVIEWER B — causal inference researcher

*"Two separate things are being conflated and you should separate them. Post-treatment weighting and the
one-week pre-window are **not invalid estimators in this world** — volume does not respond to treatment, so
post-weights equal pre-weights in expectation, and a shorter pre-window is just noisier. Your own v2 table
classified denominator invariance as 'no longer load-bearing'. If it is not load-bearing, an estimator that
relies on it is not wrong, and grading it as wrong would be punishing a correct answer. I would relax those
two invariants rather than call them defects.*

*R2 is genuinely different. Its answer is right and its warrant is circular. That is a real epistemic problem
and no outcome-graded verifier can see it. If the benchmark's claim is 'this task tests whether the agent
reasons about interference', then an agent that reaches the right number by a route that presupposes the
answer is a false positive you cannot detect.*

*Also: your `programme_effect_pp` separation ratio is 2.01 and your courier-hours ratio is 1.40. Those are
thin, and they are thin because a 16-cluster design is imprecise. That is honest, but it is a real ceiling on
what this task can discriminate."*

**Objections:** H and I misclassified as invalid → **LIMITATION** (recommend relaxing the invariant);
R2 undetectable false positive → **BLOCKING**; thin separation ratios → **LIMITATION**.

## 27. REVIEWER C — benchmark / verifier engineer

*"You cannot ship this verifier because you cannot define what to execute. The instruction says 'leave the
code that produced them in /workspace' and stops there. Every other task in this repository names the command.
If you re-run `python -m northline_eval readout` and the candidate wrote `analysis.py`, you fail a correct
submission and you will never know why. If instead you only grade static files, then hardcoded JSON with
unrelated code passes and the whole four-world design collapses. One sentence in the instruction fixes it, and
it is a sentence about packaging, not about science — but it is inside your frozen manifest, so it is not your
call.*

*Second: even with that fixed, re-execution does not save you from R2 or post-weighting. Those are real
procedures that recompute correctly in every world. Re-execution catches hardcoding and staleness, not wrong
warrants. Do not oversell it."*

**Objections:** no execution contract → **BLOCKING**; re-execution does not address STOP 2 → **RESOLVED as a
scoping statement** (it was never claimed to).

## 28. ALL REMAINING LIMITATIONS

1. `programme_effect_pp` separation ratio **2.01**; `courier_hours_response_pct` ratio **1.40**. Both below the
   ≥3 heuristic; both reject the incumbent on every world.
2. The unadjusted phase-1 contrast is rejected on only 2 of 4 worlds (estate-weighted) or 1 of 4
   (market-unweighted). It fails the suite; it is not rejected everywhere.
3. No falsification artifact is graded (consequence of removing the holdout field in v2).
4. 15 of 26 mutations and all ~30 verifier attacks remain untested.
5. Docker build, Harbor Oracle/Nop, Harbor check, image-layer leakage audit all unreached.
6. Class-C simplifications remaining: cancellation non-response, constant couriers-per-order, no novelty
   effect. **One of them — volume non-response — is now the direct cause of H passing.**

## 29. FINAL FREEZE MANIFEST

**NOT CREATED.** §26 permits a freeze only if every listed condition passes. Two stop conditions fired.

The pre-verifier scientific manifest is intact and unchanged: 28 files, aggregate **`0dbc9470ed483848`**.

## 30. TARGET EXPOSURE STATUS

**ZERO. No target model has ever seen G50.** No Gemini, no `google/gemini-3-flash-preview`, no other target
model, no `harbor run`, no `harbor check`. Nothing in this turn consulted any model's behaviour.

## 31. EXACT GEMINI COMMANDS — NOT EXECUTED

**Deliberately not printed.** §27 authorises printing them "if and only if final verdict is READY". The verdict
is NOT READY, so printing them would be misleading.

## 32. GIT STATUS / CHANGED FILES

```
?? HANDOFF_2026-09-28_ABUNDANT_RESUME.md
?? HANDOFF_2026-09-28_FORENSICDS_FINAL10_DESIGN.md
?? HANDOFF_G50_PREEXPOSURE.md
?? HANDOFF_G50_V2_SCIENTIFIC_SPEC.md
?? HANDOFF_G50_FINAL_PRETARGET_VALIDATION.md      <- new this turn
?? candidates/g50-courier-boost-rollout/          <- unchanged this turn
?? submission_5task_fallback.zip
```

Nothing committed, nothing pushed. Frozen five-task checksums, the three prospective manifests,
`research/phase3/analysis_plan.md` (`c590cb56…`) and the fallback archive (`c8561aad…`) all recompute to their
recorded values.

## 33. FINAL VERDICT

**NOT READY.** Two blocking defects:

- **B1 (packaging, one sentence):** the frozen `instruction.md` establishes no execution contract, so the
  verifier cannot re-execute the submitted procedure without risking false negatives on legitimate
  submissions. Requires editing a manifest-covered file.
- **B2 (scientific, structural):** withdrawn R2, post-treatment weighting and a wrong pre-period window are
  numerically indistinguishable from the reference on all four worlds. Two v2 invariants are unenforceable.

B1 is trivial to fix and is ChatGPT's call because the file is frozen. **B2 is the real finding** and needs a
scientific decision, not an engineering one.

## 34. CHATGPT DECISION PACKET

1. **Did the manifest reproduce exactly?** Yes — 28/28 files, aggregate `0dbc9470ed483848`.
2. **Were any frozen scientific files modified?** No. None, this turn.
3. **What does the verifier grade?** Designed to grade seven criteria against regenerated latent truth in four
   worlds. **Not built.**
4. **Does it execute the submitted procedure?** No — blocked by B1.
5. **Does the same procedure run across all four worlds?** Designed to; not implemented.
6. **Can a hardcoded visible answer pass?** Untested. It would be caught by multi-world re-execution, which is
   blocked.
7. **Can hardcoded JSON + unrelated code pass?** Untested, same reason. Under static-only grading it *would*
   pass, which is why static-only grading is not acceptable.
8. **Can correct-decision-wrong-science pass?** Not in any case tested: the incumbent on hidden_a and hidden_c
   gets the right decision and is rejected on three criteria each. Two variants untested.
9. **Can numerically lucky wrong science pass?** **Yes — this is B2.** Post-treatment weighting (max dev
   0.983) and a one-week pre-window (1.002) pass on all four worlds.
10. **Can pseudoreplicated uncertainty pass?** Designed to be caught by the interval-width criterion (incumbent
    interval ±0.45 pp vs reference ±2.5–3.1 pp). Untested.
11. **Can post-treatment weighting pass?** **Yes.** B2.
12. **Can R2 pass?** **Yes, and it beats the reference** — max deviation 0.848 vs 0.949. B2.
13. **Which legitimate alternatives pass?** All four: D_ow, D_panel, D_pool, D_mu.
14. **Did every mutation behave as intended?** No. 11 of 26 measured; 8 behaved correctly, 3 failed to be
    rejected (H, I, X), and D/D′ are rejected on only some worlds.
15. **Did every verifier attack behave as intended?** Not run.
16. **Oracle reward?** Not run (no verifier). Reference passes all four worlds outside Harbor.
17. **Nop reward?** Not run.
18. **Incumbent reward?** Would be 0. Measured: fails on all four worlds.
19. **What did the incumbent pass and fail?** Passes evidence reconstruction and the arm contrast (≤0.025 pp);
    fails the scientific object, the quantity (3.05–7.64 pp), the inference unit (order count) and the
    uncertainty. It fails for scientific reasons, not plumbing.
20. **Harbor-check outcome?** Not run — gated behind deterministic validation, which did not pass.
21. **Clean container?** Not attempted.
22. **Total verifier runtime?** Not measured; estimated 2–3 minutes for four worlds from host timings.
23. **Any leakage?** None found at workspace level. Image-level audit not reached.
24. **Any hidden simulator assumption required by the agent?** No — the correct route is recoverable from the
    dispatch note, the experiment config and the visible baseline spread. But the *converse* is now the
    problem: three procedures that do **not** follow that route reach the same number.
25. **Any unresolved scientific ambiguity?** Yes — whether H and I should be accepted (Reviewer B says yes) and
    whether R2's circular warrant can be tolerated (Reviewer A and B say it cannot be detected).
26. **Any verifier overfitting?** No evidence of it: all four legitimate routes pass. The problem is the
    opposite — the verifier cannot be made *selective* enough.
27. **What limitations remain?** §28, six items.
28. **Final freeze hashes?** None created. Pre-verifier manifest unchanged at `0dbc9470ed483848`.
29. **Has any target model seen G50?** **No. Zero exposures.**
30. **Should ChatGPT authorise the first three Gemini trials?** **NO.** Not until B1 and B2 are decided. B2 in
    particular determines what the task can honestly claim to measure, and spending G50's one clean
    pre-exposure measurement before that is settled would waste it.

**Recommended decisions for ChatGPT, in order:**

- **B1:** authorise adding one sentence to `instruction.md` naming the entry point, in P22's exact form
  ("Leave the repaired package in place, with `python -m northline_eval readout --db data/northline.sqlite
  --out out` producing the outputs"), then re-issue the pre-verifier manifest with a new digest.
- **B2:** choose one of — (a) relax the H and I invariants as Reviewer B argues, and accept R2 as valid *in
  this world* with the circularity recorded as a known limitation of outcome grading; (b) increase the
  dose-response curvature in the DGP so the boost-share regression is measurably wrong, which is a scientific
  change requiring full recalibration; or (c) add a contract field that exposes the weighting basis, which
  scaffolds the solution and which v2 deliberately moved away from.

My own view, offered but not acted on: **(a)**. H and I are not wrong in this world, and R2's defect is a
warrant problem that no outcome-graded benchmark can detect — saying so plainly is better science than
engineering a world to punish it.
