# Generation-3 adversarial design tournament

Date: 2026-09-14.

- **Inputs:** the 15 detailed designs in `research/gen3_designs/` (commit d256f8a) and the scoring in
  `research/gen3_scoring.md`.
- **Output:** verdicts, penalties and a post-tournament ranking. These feed `research/gen3_implementation_shortlist.md`.

No model was run. No candidate was implemented. Tasks 01–06 were not modified.

## 1. Method

Three independent reviewer agents each received five designs, split so that each panel mixed high- and low-scored
designs:

| Panel | Designs |
|---|---|
| R1 | G11, G24, G10, G17, G02 |
| R2 | G08, G01, G21, G14, G26 |
| R3 | G05, G20, G23, G25, G30 |

Each reviewer was told to act as a strong frontier data agent and do four things:

1. Find the **cheapest successful path**: the fewest actions that would pass the verifier as designed.
2. Test whether the stated **natural wrong implementation** is what a strong agent would actually write, or a strawman.
3. Look for **answer keys** left in the agent-visible workspace: documents or tables that can be transcribed or matched.
4. Check the design's **statistical claims** with small simulations wherever a verifier tolerance or a trap depends on
   them.

Each reviewer scored every design from 1 to 10 on eight dimensions:

- **CS**: cheap-solve resistance
- **NW**: natural wrong path
- **INV**: investigation depth
- **SPEC**: specification/uniqueness
- **VER**: verifier soundness
- **REAL**: realism
- **DIFF**: expected difficulty
- **FEAS**: build feasibility

Each reviewer then gave one verdict: KEEP, KEEP WITH FIXES, WEAK or REJECT.

I then re-derived or re-ran the decisive numerical claims (§3). Every re-run claim reproduced. Scripts and a re-run log
are in `research/gen3_tournament_sims/`.

**Calibration caveat.** Each panel saw different designs, so scores compare better within a panel than across panels.
R1 scored cheap-solve resistance most generously (8 for G11 and G10); R3 gave nothing above 5. Some of that gap is
real, since R1's panel held the two top pre-tournament designs. The cross-panel adjustments in §5 are judgement calls
and are stated explicitly.

## 2. Scorecards and verdicts

| Design | CS | NW | INV | SPEC | VER | REAL | DIFF | FEAS | Verdict | Reviewer rank in panel |
|---|---|---|---|---|---|---|---|---|---|---|
| G11 training–serving skew | 8 | 7 | 7 | 4 | 5 | 7 | 9 | 3 | KEEP WITH FIXES (major scope cut) | R1 #2 |
| G24 recommender OPE | 6 | 6 | 6 | 8 | 8 | 7 | 6 | 5 | KEEP WITH FIXES | R1 #1 |
| G10 censored demand | 8 | 8 | 8 | 5 | 4 | 9 | 9 | 3 | KEEP WITH FIXES, gated on tolerance pilot | R1 #3 |
| G17 B2B entity resolution | 6 | 7 | 7 | 5 | 7 | 6 | 7 | 4 | KEEP WITH FIXES, borderline WEAK | R1 #4 |
| G02 calibration / sampling weights | 3 | 5 | 4 | 7 | 7 | 8 | 4 | 8 | WEAK | R1 #5 |
| G08 forecast vintages | 6 | 6 | 7 | 6 | 7 | 9 | 7 | 6 | KEEP WITH FIXES | R2 #1 |
| G01 collections label maturity | 7 | 7 | 8 | 5 | 4 | 8 | 8 | 3 | KEEP WITH FIXES | R2 #2 |
| G21 churn-save survival | 6 | 5 | 7 | 5 | 3 | 7 | 7 | 4 | KEEP WITH FIXES, conditional (core estimator wrong as written) | R2 #3 |
| G14 marketplace allocation | 5 | 6 | 6 | 6 | 7 | 6 | 5 | 7 | WEAK | R2 #4 |
| G26 twin incident / negative control | 3 | 2 | 4 | 7 | 6 | 8 | 3 | 6 | REJECT as headroom task | R2 #5 |
| G23 readmission episodes | 5 | 6 | 7 | 5 | 8 | 9 | 6 | 6 | KEEP WITH FIXES | R3 #1 |
| G25 search judgment pool | 5 | 6 | 7 | 6 | 6 | 8 | 6 | 7 | KEEP WITH FIXES | R3 #2 |
| G05 staggered rollout DiD | 5 | 4 | 6 | 6 | 5 | 7 | 5 | 6 | KEEP WITH FIXES (symptom infeasible) | R3 #3 |
| G20 telematics segmentation | 5 | 4 | 7 | 6 | 5 | 6 | 6 | 3 | KEEP WITH FIXES, borderline WEAK | R3 #4 |
| G30 fraud reject inference | 5 | 5 | 7 | 7 | 3 | 9 | 6 | 4 | WEAK as specified | R3 #5 |

## 3. Numerical findings that changed verdicts

Every claim marked ✔ was reproduced by a re-run in `research/gen3_tournament_sims/`. Claims marked (R) come from
reviewer simulations that were not re-run.

| # | Design | Finding | Consequence |
|---|---|---|---|
| 1 | G21 | ✔ The design's oracle rule "censor unresolved spells at spell_end" drops events in each unit's last 30 days of follow-up, so censoring depends on the outcome. KM S(180) comes out 0.545 vs a truth of 0.487. Administrative censoring at as-of − 30 gives 0.486. | The oracle as written would fail its own verifier (offer-arm τ 0.010). The correct and wrong rules must be swapped. |
| 2 | G21 | (R) The pooled-KM trap needs a large v1/v2 survival gap (holdout S180 0.315 vs 0.487). At that gap, pooled IPW-KM, which the design accepts, misses S_offer by −0.014. | The accepted/mutated estimator lists must be re-derived. |
| 3 | G10 | ✔ The design's reference "profile-scaling" estimator (sales ÷ in-stock fraction of expected demand) is biased on sell-out days, because stock-out time is a stopping time. Conditional on selling out: +56% at inventory 4, +25% at 8, +12% at 15. | The design author fell into the task's own trap. That is good evidence the trap is natural, but the oracle must be censoring-aware (censored Poisson / stopping-time-correct), and all separation margins must be re-measured. |
| 4 | G26 | ✔ The stated mixture gives 34.8% true September activation, not 40.3%. The Growth Ops patch as specified marks every iOS trial converted (≈50% overall, 100% iOS). | The attractor is absurd on sight, so the negative-control story fails. |
| 5 | G05 | ✔ Under the stated staggered rollout, static TWFE is **positive** (+0.011…+0.022). | The −2.3% "house estimator" symptom cannot be generated. The core traps (g−1 base in install dip +0.042; region×week FE only +0.015) do hold. |
| 6 | G05 | (R) An event-study reference week inside the install dip pushes every coefficient *up* by about 0.045, against the design's claimed −0.006. The generator has a region×season term but the oracle has only store and week FE, so the oracle is off by −0.004 on W1 and "no confounder adjustment" passes overall. | Oracle/generator mismatch. The oracle needs region×week effects, or the region×season term must be zero. |
| 7 | G30 | ✔ The cost difference rests on ≈8–10 sampled fraud-loss rows in the disagreement region. SE ≈ $75–117 per 1k vs the claimed $38. | τ = 3·SE ≈ $225–345 against a true difference of $220, so the wrong estimators cannot be separated. The verifier is unsound as specified. |
| 8 | G24 | ✔ Unpaired SE ≈ 1.08× paired SE. | The `unpaired_ci` mutation would pass. Remove or redesign it. |
| 9 | G24 | (R) Uniform shuffle makes the item-in-slot propensity 1/M, which is textbook. | Make the logging marginal non-trivial (Plackett–Luce/softmax over v6 scores, or a top-12 shuffle). |
| 10 | G23 | ✔ Parsing the new hospital's naive local times as UTC still links 100% of forward transfers. Only back-transfers (≈30% outside the window) and day-30/quarter boundaries break. | The design's "discovery 3" never happens. The timezone mechanism must be rebuilt or dropped. |
| 11 | G01 | (R) With Beta(2,3) scores and 32k episodes, band-5 holdout n is ≈126 (tol ≈0.10). Ignoring the policy gives +0.088 in band 4, only 1.3× tol (claimed 1.8×). Band-5 errors pass. An oracle using its own estimate picks the wrong status ≈10% of the time. | Per-band status grading is unsound. Pool the bands or grade status only where SE allows. |
| 12 | G02 | (R) Form edition proxies the sampling batch, so errors are uniform (≈−46%) across segments. The stated segment targets and the 71.5% loss ratio are unreachable. | Numbers are internally inconsistent, on top of textbook headroom risk. |
| 13 | G08 | (R) HGBR predictions are invariant to row order but not column order (up to 72.8 units after swapping two lag columns). | The verifier must build predictions from a canonical feature order, or grade features and training membership rather than predictions. |
| 14 | G20 | (R) Idle-boundary convention on 10-second sampling shifts the idle ratio by 0.004–0.006 against a ±0.005 tolerance. The generator guard band (55–65 s) is too narrow. | Coding style could decide pass/fail. Recalibrate on at least 3 independent implementations. |

## 4. Per-design adversarial summary

In the table below, "Cheapest successful path" is the reviewer's estimate for a strong agent against the design as
written.

| Design | Cheapest successful path (as designed) | Is the stated natural wrong path real? | Answer keys / neon signs found | Required fixes before build |
|---|---|---|---|---|
| **G11** | Compose 3 docs + feature-registry history + log `fv_runs`/`map_version` fields (~40–50 actions) | Yes: point-in-time join wrong on 4 of 5 features | Serving logs give row-level feedback. Exact grading of ~950k cells forces docs toward an algorithm spec. | Cut to 3 mechanisms (M1 publication/failed runs/cadence; M4 ingest vs request identity, merges only; M6 `on_miss` + expired vs NULL defined per field). Require ≥30 logged rows or fact-table determination per graded mechanism. Drop the 1e-6 prediction check. Resolve expiry semantics in `feature_views.yaml`. |
| **G24** | Uniform shuffle → slot-exact IPS (weight M) → decision grouping via `slate_cache.yaml` → dedupe clicks → paired bootstrap (~30–40) | Partly: position-unaware SNIPS is natural, but 1/M propensity is textbook | `slate_cache.yaml` is close to a recipe | Non-trivial logging marginal; remove/fix `unpaired_ci`; specify window boundaries and view/click consistency; shrink the ~170MB extract. |
| **G10** | Contract → close-snapshot flag audit → intraday inventory reconstruction → censored estimator (~50–60) | Yes: drop-zero, clean-days-only, trailing-mean, and even the author's own profile scaling | `in_stock_minutes` contract wording is too technical | Censoring-aware oracle and re-measured margins (a tolerance pilot is the gate). Cut substitution grading and possibly POS outages. Rewrite the contract in business language. Fix the shrink contradiction. |
| **G17** | Methodology doc + deal register `prior_parent_registration_id` (~35–45) | Yes: retroactive acquisitions give the right August 35.4% but wrong history | `prior_parent_registration_id`, Talon footnote | Fix MRR window (Q3-25 churn needs 2025-06). Make ownership changes discoverable from data. Cover agency handovers and divestitures. Justify identity rules. Differentiate from Task 01. |
| **G02** | `grep keep_rate` → manifest → weights → μ = −ln(1−p) (~25) | Weakly: faulty `calibrate.py` scaffolds prior correction | Keep-rate manifest | Re-derive segment effects. Add a non-textbook weight layer. Remove scaffolding. (Not shortlisted.) |
| **G08** | Model card + `train_job` + `views.sql` → rerun `v_latest_*` at each issue instant with zoneinfo and status history → diff against snapshots (~35–45) | Variants A/B are strawmen; the real bites are withdrawn runs, DST, vendor-B `available_at`, KPI actual timing | `v_latest_volumes` (one filter from correct); `feature_snapshots` allow row-by-row unit testing; published KPI CSV is an exact scoring key | Remove `v_latest_volumes`. Limit snapshots to non-incident days. Specify vendor precedence and run ordering. Canonical feature order. At least one hidden-fixture mechanism absent from the snapshot window. |
| **G01** | Model card + MRS-4 → dictionary (value date, hub close) → manifest table → CS-7 doc + `strategy_config_log` (~40) | Yes: R1/R3/R4/R9 form a genuine chain of plausible repairs | README output schema names CS-7 uplift and strategy periods; "worked under CS-5" line | Pool bands or raise holdout n about 4× and SE-gate the status grade. Mid-month re-cut. Define episode→source completeness. Keep the schema from naming the treatment. Cut the PH-2 pause and/or R6. |
| **G21** | KPI + lifecycle docs → account spells → `save_config_versions` → KM per version, eligible-weighted (~40) | No: the SRM notebook leads straight to stratification | "Invoices govern" is not load-bearing | Swap the censoring rule. Fix heterogeneity parameters and re-derive accepted/mutated estimators. Plant a real subscription-vs-invoice divergence. |
| **G14** | Seller agreement + support macros → bottom-up line table → reproduce recorded fees → GL 4010 tie (~35–45) | Mostly strawman: eligibility and `component` columns are in plain view | Support macros state both real rules; recorded fees reveal discounts; GL 4010 is an exact oracle | Remove macros. State 6100 refund-recovery postings. Add a statistical component. (Not shortlisted.) |
| **G26** | grep price → one GROUP BY → aware local date → diff vs `published/` (~25–35) | No | Memo says "if you conclude a metric does not need restating" | Fix numbers, make the patch subtle, remove the hint. Use as an easy anchor only. **Rejected as a headroom task.** |
| **G23** | Measure doc + model card → localize H6 → gaps-and-islands episodes → last-encounter eligibility → first subsequent episode (~40–50) | Partly: pairwise-only links and "drop H6" are strawmen; disposition-70/origin-4 is genuine | Measure document near-recipe | Rebuild the TZ mechanism so it changes membership (or drop it). Align documentation rule with clinical truth. Put the local-calendar-day rule in the glossary. Thin the measure doc to examples and a worked historical case. |
| **G25** | Gate report coverage → `qrels.py` → `rounds.yaml` → canonical `v3(display_query)` → RG-3 crosswalk → GTIN → R09 unlabelled mean (~40–50) | Yes: re-canonicalising via `qnorm_v3(query_key)` is genuinely wrong, and a partial fix makes B worse | `rounds.yaml` lists key form and scale; `gtin` on judgments; RG-3 "Partial" prose is the crosswalk | Add `task_id` to judgments (collision-twin ambiguity). Widen the frame trap to ≥2.5τ. Strip key form/scale from `rounds.yaml` and `gtin` from judgments. |
| **G05** | Contract + handbook → fiscal calendar + install log → R4 note names ValuMart → exposure → imputation (~30–35) | Partly: g−1 base and region×week-only are real; TWFE sign flip is infeasible | Handbook "comparable trading week" = `kpi_comparable` column; competitor tables sit unused in an 8-table warehouse | Replace the symptom with a simulated-feasible one. Reconcile oracle and generator seasonality. Accept region×week + exposure. Bury competitor data in a realistic warehouse and un-name ValuMart. |
| **G20** | Policy → message spec → ignition state machine → `sync_events` interpolation → idle ≥60 s (~40–50) | No: the memo requires policy definitions, so no agent tunes a gap threshold | `sync_events` table is named | Put a principled trap on the policy-transcription path. Recalibrate tolerances. Realistic clock failure (RTC reset). Cut simulator scope. |
| **G30** | `population.py` → decision flow doc → policy log → IPW weights → dispute state machine (~45–60) | Partly: selective labels are textbook; the dispute state machine is careful transcription | Decision flow doc points to the policy log; `analyst_override` reason code | Redesign variance, or grade on the realised sample design-based estimate plus exact tables. Add a principled trap on the IPW path (tier-dependent propensity). Cut rows/worlds (verifier >20 min). |

## 5. Cross-cutting findings

1. **Answer keys left in the workspace are the dominant defect.** Found in 12 of 15 designs: G08 snapshots and
   `v_latest_volumes`; G14 macros and recorded fees; G01 output schema; G26 memo hint; G17 deal register; G25
   `rounds.yaml`; G05 handbook and ValuMart note; G24 `slate_cache.yaml`; G02 keep-rate manifest; G30 decision flow;
   G23 measure doc; G11 serving logs. Authors wrote "facts, not recipes" but repeatedly placed a fact that *is* the
   recipe. This is the same failure that made Tasks 03/05 easy. **Build rule:** at the implementation review, every
   agent-visible artifact must pass a "could a reader write the fix from this file alone?" check.
2. **Strawman first wrong paths.** G20, G21, G14, G26 and parts of G08/G23 describe first repairs that a strong agent
   would not write. The Task 06 lesson ("traps on paths no agent chose") recurred at design time. Only G10, G11, G01,
   G17 and G25 have a first wrong repair that reviewers judged genuinely natural.
3. **Unverified separation margins.** G10, G21, G01, G05, G30 and G24 all had at least one tolerance or trap that
   failed or weakened under simulation. **Build rule:** every truth-with-tolerance verifier requires a margin
   simulation (oracle pass rate ≥99%, each named wrong estimator failing ≥99%) *before* workspace authoring.
4. **Authors fell into their own traps** (G10 profile scaling, G21 censoring). This is evidence those traps are
   natural even for careful designers. It also means oracles for statistical tasks must be derived from the generator,
   not from the design prose.
5. **Kernel families** (a strongest-per-family rule avoids a benchmark that tests one idea repeatedly):

   | Family | Designs | Existing tasks |
   |---|---|---|
   | Point-in-time / per-row knowledge state | G11, G08 (G10 partially) | Task 02 |
   | Randomised holdout / exploration IPW | G24, G30, G01 (policy layer), G21, G25 (audit sample), G02 | Tasks 03, 05 |
   | Identity / entity grain | G17, G23, G25 | Task 01 |
   | Censoring / latent-quantity estimation | G10, G21, G01 (immature labels) | — |
   | Causal panel | G05 | — |
   | Event segmentation / clocks | G20, G23 (TZ), G08 (DST) | Task 06 |
   | Accounting allocation / tie-out | G14 | Tasks 01, 06 |
   | Negative control | G26 | (rejected Task 09 concept) |

6. **Shared narrative template.** G20, G23 and G25 all use "new X onboarded on a date → metric jumped → notebook with
   the wrong story". Vary the incident framing across the final set.

## 6. Penalties and post-tournament ranking

**Post-tournament score** = 2 × (CS + NW + DIFF) + INV + SPEC + VER + REAL.

- Build feasibility is reported but not penalised, consistent with `gen3_scoring.md`.

**Penalties:**

- WEAK: −8.
- REJECT: excluded.
- Kernel overlap with a stronger design in the same family: −5. Applied to:
  - G21 (vs G01)
  - G17 (vs Task 01 and G11's identity maps)
  - G30 (vs G24/G25/Task 03)

| Rank | Design | Raw | Penalties | Final | Pre-tournament rank (composite) | Verdict |
|---|---|---|---|---|---|---|
| 1 | G10 censored demand | 76 | — | **76** | 2 (73.5) | KEEP WITH FIXES (gated) |
| 2 | G11 training–serving skew | 71 | — | **71** | 1 (76.0) | KEEP WITH FIXES (scope cut) |
| 3 | G01 collections label maturity | 69 | — | **69** | 3 (71) | KEEP WITH FIXES |
| 4 | G08 forecast vintages | 67 | — | **67** | 7 (70) | KEEP WITH FIXES |
| 5 | G24 recommender OPE | 65 | — | **65** | 5 (71) | KEEP WITH FIXES |
| 6 | G23 readmission episodes | 63 | — | **63** | 8 (70) | KEEP WITH FIXES |
| 7 | G25 search judgment pool | 61 | — | **61** | 14 (61.5) | KEEP WITH FIXES |
| 8 | G17 B2B entity resolution | 65 | −5 overlap | **60** | 13 (65.5) | KEEP WITH FIXES (borderline) |
| 9 | G20 telematics segmentation | 54 | — | **54** | 12 (67) | KEEP WITH FIXES (borderline) |
| 10 | G21 churn-save survival | 58 | −5 overlap | **53** | 4 (71) | KEEP WITH FIXES (conditional) |
| 11 | G05 staggered rollout DiD | 52 | — | **52** | 11 (67) | KEEP WITH FIXES |
| 12 | G14 marketplace allocation | 57 | −8 WEAK | **49** | 16 (57) | WEAK |
| 13 | G30 fraud reject inference | 58 | −8 WEAK, −5 overlap | **45** | 9 (69) | WEAK |
| 14 | G02 calibration / sampling weights | 50 | −8 WEAK | **42** | 6 (70.5) | WEAK |
| — | G26 twin incident | 41 | excluded | — | 10 (67.5) | REJECT (headroom); negative-control idea retained |

**Biggest movers:**

- **G02 fell** from #6 to #14 (textbook; inconsistent numbers).
- **G30 fell** from #9 to #13 (verifier variance).
- **G21 fell** from #4 to #10 (core estimator wrong; overlap with G01).
- **G25 rose** from #14 to #7: a genuinely natural wrong path where the partial fix makes the result worse, and cheap
  fixes.

**Rejected:** G26 as a standalone headroom task. Its negative-control concept (a flagged discrepancy that is genuine
behaviour and must not be "fixed") survives as an **embedded control** recommended for G11 (§7).

**Penalised but retained as alternates:**

- G17: first alternate.
- G21: second alternate. Its survival kernel is valuable if G01's generator proves too costly.
- G20: third alternate. It is distinctive, but needs a principled trap.
- G05: shortlisted anyway on distribution grounds; see the shortlist document.

## 7. Recommendations carried into the shortlist

- **G11 embedded negative control** (from G26 and alternate G27). One of the retained features shows a large
  train/serve distribution difference in the skew report that is genuine population drift (a new city launch), not a
  pipeline defect. Correct behaviour: repair the three skewed features and leave that one unchanged. It is graded by
  exact feature equality with the untouched column plus the hidden fixture where drift is absent. This adds a
  principled "don't fix it" decision on the path every agent takes, which G26 could not achieve.
- **Phase-0 margin simulations** are a hard gate for G10, G24, G05, G25 and G01 before any workspace authoring.
- **Answer-key review** at implementation time, applying cross-cutting finding 1 to every agent-visible file.
- **Build G08 before G11.** Both test the Task 02 family, and G08 is the cheaper probe of whether that hardness
  transfers to a new domain.
