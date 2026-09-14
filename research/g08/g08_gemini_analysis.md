# G08: Gemini 3 Flash Preview baseline

Status: exploratory baseline, n = 3 valid trials. G08 frozen at commit `e07103d` (clean tree; content checksum
`b1f0fa1304fb88f5`). Tasks 01–06 untouched.

- Per-trial table: `research/g08/g08_trials.csv`.
- Step ids refer to ATIF `step_id`s in `jobs/g08-gemini3flash-baseline-2/<trial>/agent/trajectory.json`.
- Derived views (not committed): `<trial>/analysis/timeline.txt`.
- Evidence tools: `tools/analysis/g08_evidence.py`, `tools/analysis/g08_rerun_agent_code.py`.

## 1. Setup and validity

| Item | Value |
|---|---|
| Command (proposed) | `harbor run -p candidates/g08-forecast-accuracy-vintages -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name g08-gemini3flash-baseline-1 --artifact /workspace -y` |
| Attempt 1 | **INVALID, not counted.** All 3 trials raised `AgentSetupTimeoutError`: gemini-cli installation (nvm + `npm install -g @google/gemini-cli`) exceeded Harbor's 360 s agent-setup limit. 0 agent steps, no model calls. Directory renamed `jobs/g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout`. |
| Valid run | Same command, job `g08-gemini3flash-baseline-2`, plus `--agent-setup-timeout-multiplier 3`. This is infrastructure only: agent execution time, task and verifier are unchanged. Setup then took 5 m 17 s–5 m 28 s per trial. |
| Infrastructure | 0 exceptions, 0 retries. No quota/429/API errors in any agent log. Job 21 m 15 s. |
| Cost | **$0.958** (0.269 + 0.365 + 0.324) |
| Preserved | ATIF + native gemini-cli trajectories, verifier ctrf/stdout/reward, result metadata, final `/workspace` |

## 2. Results

| Trial | Reward | Verifier | Tool calls | Agent time | Head-to-head it reported |
|---|---:|---|---:|---:|---|
| `h7TpDUG` | 0 | 6 passed / 14 failed | 55 | 407 s | −13.15% (27,300 pairs) |
| `pXphfXM` | **1** | 20 / 0 | 66 | 483 s | −13.60% (26,999 pairs) |
| `wmwSU97` | 0 | 5 / 15 | 64 | 382 s | −13.30% (26,207 pairs) |

Reference head-to-head: −13.60% on 26,999 pairs. Deployed mart: −29.7%.

- **Empirical success rate:** 1/3 = 0.33. This estimates per-attempt success from three trials (Wilson 95% interval
  ≈ 0.06–0.79); it is not an exact pass@1.
- **pass@3:** 1.
- **Verification of the pass:** re-running `pXphfXM`'s submitted code on freshly regenerated visible and hidden
  extracts reproduces 0 mismatches on all four. It is a genuine, independently derived solution, not luck on the
  visible data.

**Verifier failures:**

| Check | h7TpDUG | wmwSU97 |
|---|---|---|
| warehouse unmodified, build, time, determinism | pass | pass |
| example set | pass | **fail**: 1,165 missing (issue-grain lock) |
| forecast in force | pass | pass (for present examples) |
| KPI month + status | **fail**: 693 (never unsettled) | **fail**: 301 scored that should be unsettled |
| settlement runs | **fail**: 67,340 (latest run of any type) | **fail**: 301 |
| actual / error | **fail**: 67,214 | **fail**: 301 |
| monthly KPI, head-to-head | **fail** | **fail** |
| hidden a / b / c | **fail** ×9 | **fail** ×9 |

Every failure is already visible; no trial passed the visible checks and failed only hidden fixtures.

## 3. Counterfactual attribution (submitted code, one targeted patch, 4 regenerated extracts)

| Trial | Patch | visible | hidden_a | hidden_b | hidden_c |
|---|---|---|---|---|---|
| h7TpDUG | none | 67,340 run-id / 693 status errors | 77,322 | 98,848 | 98,154 |
| h7TpDUG | charge basis at close (status replayed on `recorded_at`) replaces `settled_volumes_latest` | 301 status (partial classes) | 808 | 498 + 30 forecast | 168 |
| h7TpDUG | + unsettled unless every class settled | **PASS** | **PASS** | 30 forecast errors | **PASS** |
| wmwSU97 | none | 1,165 missing + 301 status | 1,830 + 1,022 | 6,430 + 542 | 2,265 + 352 |
| wmwSU97 | unit-grain forecast lock only | 301 status | 1,058 | 577 | 358 |
| wmwSU97 | all classes required only | 1,165 missing + 126 status | 1,830 + 529 | 6,430 + 218 | 2,265 + 318 |
| wmwSU97 | unit grain + status at close + all classes | 301 `actual_run_ids` only (partial run ids left on unsettled rows) | 808 | 498 | 168 |
| pXphfXM | none | **PASS** | **PASS** | **PASS** | **PASS** |

- **h7TpDUG's 30 hidden_b forecast errors are one latent bug.** It computes the gate as
  `tz_localize(midnight, Europe/London) + 11 h`. On the October DST changeover Sunday (2026-10-25) this puts the gate
  at 10:00 GMT and excludes a 10:45 scoped LONDON re-issue (30 values).
- **The 126 examples in wmwSU97** that still fail after the all-classes patch are exactly the withdrawal-notice
  cases: an IS run withdrawn before the close whose re-run came after it.

## 4. Per-trajectory reconstruction

### 4.1 pXphfXM: PASS (strongest trajectory)

**Investigation path:**
1. **2–8:** README, KPI doc, mart spec, data dictionary, close log, mart code, SQL.
2. **10–12:** settlement doc. "Charges are calculated on IS, not revised by later data."
3. **12–22:** January pack and incident log. At 22 it realises MIDLANDS IS was published after the January sign-off,
   and designs "active IS run as of close" from `run_status_history`, explicitly choosing `recorded_at <= T`.
4. **24–44:** `settled_volumes_latest` definition, head-to-head bug, models table, `forecast_latest`, dim/membership
   and restructure doc, historical join.
5. **48–56:** first rewrite (IS at close, membership, delivery month, unsettled, paired head-to-head). Result: −26%.
6. **68–74:** recomputes January on common forecasts. v4 3.5% vs pack 4.1%, "for the same forecasts". It refuses to
   accept the gap.
7. **74–78:** reads the day-ahead doc, inspects all v4 issues for one run day, finds the 12:40 post-gate re-issue,
   and designs the per-unit lock before an 11:00 UK gate.
8. **80–100:** zoneinfo gate table fails on the read-only DB; hand-rolls BST in SQL; three rebuilds.
9. **102–104:** January head-to-head −15.21% = pack. Stops.

**Checklist (16 items):**

| # | Item | Result |
|---|---|---|
| 1 | Investigation path | above |
| 2 | Time to first correct root cause | 16 s (IS basis); 52 s (status at close via `recorded_at`); gate at ~5 min |
| 3 | Artifacts | 21 distinct files: KPI doc, mart spec, data dictionary, settlement doc, January pack, incidents, day-ahead doc, restructure doc, code/SQL. Not read: forecast store doc, scorecard policy, billing retirement, notebook, release notes, review, thread. |
| 4 | Hypotheses considered/rejected | "v4 may predict final volumes better" (22, rejected on the KPI definition); "MIDLANDS coverage explains January" (70, insufficient); "different populations" (72, ruled out by pairing); post-gate forecasts (76, confirmed) |
| 5 | Distinguished clocks | run day vs delivery day yes; KPI close yes; publication yes; `recorded_at` yes; `effective_from` considered and not used |
| 6 | Forecast lock | yes |
| 7 | Scoped re-issues | handled incidentally by grouping on (model, run day, region, portfolio, delivery day); noticed a smaller 10:18 issue as a "regional quirk"; forecast store doc never read |
| 8 | Europe/London | yes (hand-rolled BST rule, correct on changeover days) |
| 9 | Historical membership | yes |
| 10 | IS not reconciliation | yes |
| 11 | Status as known at close | yes |
| 12 | Withdrawal notice availability | yes |
| 13 | Corrections | yes (the later-published correction is the latest IS) |
| 14 | Unsettled counted not scored | yes, including partial-class settlement (reasoned at 34/44) |
| 15 | Delivery month | yes |
| 16 | Common scored forecasts | yes |

**Validation:** row inspection of MIDLANDS January examples (mid-repair); final check aggregate but exact (January
head-to-head against the pack).

### 4.2 h7TpDUG: FAIL (closest to the classic "fix the forecast side, trust the data" failure)

**Investigation path:**
1. **2–6:** README, KPI doc, mart spec, the September review; notices signed-off vs restated differences; restructure
   doc.
2. **10–22:** mart code, SQL, data dictionary; `dim_portfolio` vs `portfolio_membership` (BUSINESS dropped, UMS
   moves).
3. **24:** head-to-head over production periods.
4. **30:** considers that reconciliation actuals change WAPE: "If A is going up from the reconciliation runs … I'm
   also considering the implications of scoring the most recent forecast". It follows only the forecast thread.
5. **30–36:** day-ahead doc, post-gate v4 re-issues.
6. **38–54:** rewrite: gate in Europe/London, per-unit dedupe, historical membership, delivery month, paired
   head-to-head. `settled_volumes_latest` kept as the actual.
7. **56–64:** January RESI WAPE 4.96%/4.18% vs signed-off 4.9%/4.1%; head-to-head −13.1%.
8. **66–78:** adds `unsettled` only when no volume exists.
9. **82–90:** final message claims outputs "verified against signed-off packs".

**Checklist:**

| # | Item | Result |
|---|---|---|
| 2 | Time to first correct root cause | 38 s (current portfolio dimension); 78 s (post-gate forecasts) |
| 3 | Artifacts | 17 files. Never opened: settlement doc, scorecard policy, billing retirement note, notebook, pack markdowns, pack history, incident log, forecast store doc. Never queried `run_status_history`. |
| 4 | Hypotheses | portfolio mapping (confirmed), reconciliation actuals (raised, **abandoned without evidence**), post-gate forecasts (confirmed), production-period head-to-head (confirmed), run-month KPI (confirmed) |
| 5 | Clocks | run vs delivery yes; KPI close, publication, `recorded_at` no; `effective_from` only for membership |
| 6–7 | Lock / scoped re-issues | correct grain incidentally; scoped re-issues never reasoned about |
| 8 | Europe/London | yes, but localizes midnight and adds 11 h (wrong on DST changeover Sundays; 30 hidden_b errors) |
| 9 | Membership | yes |
| 10–13 | IS / close / withdrawals / corrections | **no**: latest settled volume of any run type as of today |
| 14 | Unsettled | no (only when no volume at all; 0 on the visible extract) |
| 15–16 | Delivery month / pairing | yes / yes |

**Where reasoning stopped being correct:** step 30. The agent named the target-vintage question (reconciliation vs
the charged volume) and then committed to the forecast side. The actual was never re-examined, and the settlement doc
was never opened.

**Failure ladder:**

| Stage | Result |
|---|---|
| Broad diagnosis | partial (4 of 6 defect classes) |
| Semantic invariant | **wrong (actual = latest reconciliation)** ← first substantive failure |
| Grain | correct (incidental) |
| Historical state | wrong (no knowledge-at-close for actuals) |
| Implementation | two further defects (partial classes scored; DST-day gate) |
| Validation | one aggregate pack cell + headline |
| Final | 0 |

**Taxonomy:** F0 (relevant settlement evidence never inspected) with F7.

### 4.3 wmwSU97: FAIL (closest failed trajectory in understanding; furthest in implementation)

**Investigation path:**
1. **2–12:** README, KPI doc, mart spec, runs the mart, summary, review, January pack, day-ahead doc, code, SQL,
   data dictionary.
2. **14:** gate lock hypothesis.
3. **16–18:** settlement doc: "charges calculated on the IS … reconciliation … without affecting the original
   imbalance charge".
4. **20–28:** view definitions; late issues after 10:00 UTC; post-gate v4 re-issues; incident log.
5. **30:** "the pack was signed off before [MIDLANDS IS] was available … the mart must use data present at each
   month's `closed_at`".
6. **32–42:** duplicate IS runs, superseded runs, "IS and published" (current status).
7. **44:** refines to `published_at <= closed_at`.
8. **44–60:** notebook, close log, membership, dim, head-to-head, models, gate test in Europe/London.
9. **62:** states the full withdrawal rule: "if the withdrawal `recorded_at` is after the KPI close, the withdrawn run
   *was* the active run". It then writes a pandas rewrite that never loads `run_status_history`, selects the latest
   issue per (model, run day), and scores a forecast if any class has a volume.
10. **72:** head-to-head has only 270 pairs. It diagnoses "only one issue_id per (model, run_date)" but patches to
    "latest issue per model/run_date, keep all its rows" (still issue grain).
11. **78–80:** January BUSINESS v3 WAPE 5.2% vs pack 4.9%; attributes the gap to data differences and moves on.
12. **82–90:** head-to-head −13.3% "aligns closely with −15.2%"; final message.

**Checklist:**

| # | Item | Result |
|---|---|---|
| 2 | Time to first correct root cause | 28 s (gate); 35 s (IS basis); ~80 s (state at close); ~4 min (withdrawal `recorded_at` rule) |
| 3 | Artifacts | 20 files, incl. settlement doc, January pack, notebook, incident log. Not read: forecast store doc, scorecard policy, billing retirement, restructure doc. `run_status_history` never queried. |
| 4 | Hypotheses | gate (confirmed); reconciliation vs IS (confirmed); close cutoff (confirmed); duplicate published IS runs (rejected by query); current status (refined to at-close); v4 history in review "hallucinated" (misread of the review's month range) |
| 5 | Clocks | all distinguished in reasoning, incl. `recorded_at` vs close; `effective_from` not used |
| 6–7 | Lock / scoped re-issues | **no**: issue grain; scoped re-issues never discovered |
| 8 | Europe/London | yes (correct) |
| 9 | Membership | yes |
| 10 | IS not reconciliation | yes |
| 11–12 | Status at close / withdrawal notices | **reasoned, not implemented** (latest IS published by close) |
| 13 | Corrections | yes (the later-published correction is the latest IS) |
| 14 | Unsettled | partial (only when no class found; unsettled rows keep partial run ids) |
| 15–16 | Delivery month / pairing | yes / yes |

**Where reasoning stopped being correct:**
- The lock was designed at issue grain from the start (step 60, "filter locked issue IDs"). The forecast store's
  scoped re-issue semantics were never read.
- At step 62 the correct status rule was stated but dropped when writing code.
- At 72 and 80, two concrete anomalies (undercount, pack mismatch) were patched or rationalised instead of
  investigated.

**Failure ladder:**

| Stage | Result |
|---|---|
| Broad diagnosis | correct |
| Semantic invariant | correct (as reasoned) |
| Grain | **wrong (issue-level lock)** ← first substantive failure |
| Historical state | wrong in code (withdrawal knowledge omitted) |
| Implementation | wrong (partial classes, run ids on unsettled rows) |
| Validation | insufficient (pack mismatch dismissed) |
| Final | 0 |

**Taxonomy:** F4 with F7.

## 5. Intermediate plausible success

| Trial | Plausible intermediate state | Did it stop there? |
|---|---|---|
| h7TpDUG | Head-to-head −13.1% (truth −13.6%); January RESI WAPE 4.96% / 4.18% round to the pack's 4.9% / 4.1% even though every actual was a reconciliation run. 1-dp pack cells cannot distinguish the latest-reconciliation actual for this cell. | **Yes.** It then claimed pack verification. |
| wmwSU97 | Head-to-head −13.3%, "aligns closely with −15.2%"; example-level state wrong on 1,466 visible examples. A contradicting cell (5.2% vs 4.9%) was seen and dismissed. | **Yes** |
| pXphfXM | After the first rewrite, −26% overall and 3.5% v4 January WAPE: plausible, but mismatched against the pack on paired forecasts | **No.** It treated the mismatch as a defect, which led to the gate discovery. |

Across the three trials, the deciding behaviour was **whether a mismatch with the signed-off January pack was
treated as evidence or as noise**. The two failures stopped on a plausible headline; the pass stopped only on an exact
paired match.

## 6. Evidence-use pattern

| Artifact | h7 | pX | wm |
|---|:---:|:---:|:---:|
| KPI doc, mart spec, data dictionary, mart code/SQL | ✓ | ✓ | ✓ |
| day-ahead process | ✓ | ✓ | ✓ |
| settlement process | – | ✓ | ✓ |
| January pack markdown | – | ✓ | ✓ |
| September review | ✓ | – | ✓ |
| restructure doc | ✓ | ✓ | – |
| incident log | – | ✓ | ✓ |
| legacy notebook | – | – | ✓ |
| `run_status_history` queried | – | ✓ | – |
| **forecast store doc** (scoped re-issues) | – | – | – |
| **scorecard policy / billing retirement note** | – | – | – |
| release notes, thread, v4 note, pack history CSV, ops dashboard | – | – | – |

- No trial read the forecast store doc. Scoped re-issue handling was decided entirely by the dedupe key each agent
  happened to choose.
- No trial used the scorecard policy or billing retirement note. "State at close" was inferred from the January pack
  coverage note plus the incident log (pX, wm), or not at all (h7).
- The attractors (review, release notes, thread) were not decisive. h7's failure came from what it did **not** read,
  not from being persuaded.

## 7. Row-level vs aggregate validation

| Trial | Raw rows inspected | Row-level validation after repair | Aggregate validation |
|---|---|---|---|
| h7TpDUG | output head | none | 1 January cell + headline |
| pXphfXM | MIDLANDS Jan examples; all issues for one v4 run day | partial (unsettled rows mid-repair) | January paired head-to-head, exact |
| wmwSU97 | duplicate/superseded IS runs; output head | none | January KPI (mismatch dismissed) + headline |

No trial compared example-level state with an independent reconstruction or spot-checked a withdrawal, correction
or partial-settlement row after repair.

## 8. Investigation horizon vs Task 02 (same metric definitions, computed from ATIF)

| Task (trials) | ATIF steps | Tool calls | Files read (distinct) | Warehouse query calls* | Edit calls | Agent wall time |
|---|---|---|---|---|---|---|
| **G08** (h7, pX, wm) | 90 / 106 / 90 | 55 / 66 / 64 | 17 / 21 / 20 | 11 / 21 / 8 (+9 query scripts in wm) | 10 / 10 / 15 | 385 / 467 / 362 s |
| Task 02 (nXXM, pf9z, Jctt) | 84 / 84 / 94 | 51 / 49 / 57 | 23 / 24 / 22 | 7 / 8 / 7 | 10 / 3 / 10 | 278 / 195 / 267 s |
| Task 06 (9fGw, Yav3, fiJF) | 116 / 54 / 82 | 62 / 39 / 46 | 24 / 19 / 22 | 0 / 0 / 0 | 14 / 9 / 9 | 347 / 181 / 268 s |

\* Heuristic: shell calls containing sqlite/SELECT/read_sql.

| Measure | G08 (h7 / pX / wm), estimated from timelines | Task 02 |
|---|---|---|
| Distinct hypotheses tested | 6 / 9 / 9 | not counted with the same method; its analysis records trials going "straight to a point-in-time hypothesis" with no distractor explored |
| Hypothesis changes | 1 / 2 / 2 | at most 1 recorded correction per trial (e.g. `changed_at` → `synced_at` in JctTpSi) |
| Intermediate datasets/queries constructed | ~12 / ~22 / ~17 | 7–8 warehouse query calls (same heuristic) |

**Verdict on horizon:**
- G08 produced a **modestly longer** horizon than Task 02: about +15% tool calls, about +50% wall time, and 1.5–3×
  more warehouse querying and hypotheses tested.
- It read **fewer** distinct files.
- It did **not** produce a qualitatively longer reasoning chain: all three trials finished in 6–8 minutes and 55–66
  calls.
- The extra length went into data probing and repair iterations, not into consulting more evidence. Two of three
  trials still stopped early on an aggregate match.

## 9. Reward hacking and security

| Check | Result |
|---|---|
| Access to `/tests`, `/solution`, verifier files, generator or reference | none in any trial |
| Interpreter tampering, harbor references | none |
| `warehouse.sqlite` | unchanged in all trials (verifier digest check passed) |
| `g08_evidence.py` `db_write` hits | 4, all regex false positives on code text (`CREATE`/`replace` substrings); no write to the warehouse |
| Outputs / reports | no hand edits |
| Housekeeping | `wmwSU97` left 9 helper scripts in `/workspace`; `h7TpDUG` deleted its helpers |
| API keys | never printed |

## 10. Benchmark flaws discovered (G08 remains frozen; recorded for a future version)

1. **Partial-class settlement wording (F8, medium, not decisive in either failure).** The mart spec defines `scored`
   as "a settled volume is available" and `unsettled` as "no settled volume is available". Both failed trials read
   "any class settled" as scored.
   - The reference requires every class of the portfolio, because the KPI actual is the portfolio's charged volume.
     This is determinable, and pXphfXM reasoned it out explicitly.
   - But the wording invites the other reading. In the h7 counterfactual it is the only visible defect left once
     the actual is fixed (301 examples).
   - A future version should say "a settled volume is available for every settlement class of the portfolio".
2. **Scoped re-issue trap only partially exercised.** No trial read the forecast store doc. Two trials got the unit
   grain by default, one did not. The trap measures grouping-key choice more than understanding.
3. **One-decimal pack cells can confirm a wrong actual.** The January RESI cell rounds to the pack values under
   reconciliation actuals, and gave h7 a false confirmation. This is by design (packs must not be an answer key), but
   it is an attractor more powerful than intended.
4. **The review's head-to-head month range (2025-07 to 2026-08)** made wmwSU97 think v4 history was "hallucinated".
   Harmless, but a small realism wrinkle.
5. **Infrastructure.** gemini-cli setup needs more than 360 s on this host. Future baselines should pass
   `--agent-setup-timeout-multiplier 3`.

No flaw changes any reward: every failed trial has at least two independent substantive defects unrelated to item 1.

## 11. Comparison with Task 02

| | Task 02 | G08 |
|---|---|---|
| Rewards | 0 / 0 / 0 | 0 / 1 / 0 |
| pass@3 | 0 | 1 |
| Root cause recognised | 3/3 | 3/3 broad; 2/3 full invariant articulated; 1/3 fully implemented |
| First failure | state keyed at wrong grain / existence (after correct diagnosis) | h7 semantic (never investigated target vintage); wm grain (issue-level lock) |
| Validation | aggregate AUC only | one pack cell / headline in failures; exact paired pack match in the pass |
| Horizon | 49–57 calls, 195–278 s | 55–66 calls, 362–467 s |

**Common thread:** agents do not validate example-level state. The difference is that G08 supplies a coarse external
reference (signed-off packs). One trial used it rigorously and succeeded; the others under-used it.

## 12. Difficulty verdict

**USEFUL MEDIUM-HARD (1/3, pass@3 = 1).**
- **Harder than** Tasks 03, 05 and 06 (3/3 each). Comparable to Task 04 (1/3). **Easier than** Task 02 (0/3).
- **Headroom target not met:** pass@3 < 30% would require 0/3.
- **Failure modes are genuine and diverse:**
  - an uninvestigated target definition;
  - reasoning-to-code dropout;
  - issue-grain lock;
  - partial-settlement semantics;
  - a DST changeover-day bug;
  - premature stopping on plausible aggregates.
- **Most important finding:** in the one success, the decisive step was driven by the signed-off pack. That pack is
  also the artifact most likely to shorten the horizon for stronger agents.

## 13. Does G08 belong in the final benchmark?

**Yes, as a medium-hard candidate. Not as a headroom anchor on its own evidence.** It:
- discriminates behaviour (1/3 with three distinct failure paths);
- grades example-level state that aggregates do not reveal;
- has a genuine, non-lucky pass.

Its pass@3 of 1 on Gemini 3 Flash means it does not help reach the target distribution (pass@3 < 30%) unless
stronger baselines or larger n show lower success. Final inclusion should wait for the pool comparison.

G08 was not modified after the baseline. The partial-settlement wording (§10.1) would be fixed in any future version,
which would require a new uncontaminated baseline.

## 14. Implications for G10 and G11

- **G11 gate.** The shortlist builds G11 only if G08 shows meaningful headroom. It showed moderate headroom (1/3,
  pass@3 = 1) and a horizon only modestly longer than Task 02. **Recommendation: do not build G11 next.** G11 shares
  G08/Task 02's availability family, and G08 did not show that this family scales to frontier-hard when the
  documents are good.
- **What failed was not recognition but completion.** Agents dropped reasoned rules when writing code (wmwSU97),
  never investigated one component (h7TpDUG), and stopped on plausible aggregates (both). Tasks that need several
  independently verifiable state components, each invisible in the headline, create more failure opportunities than
  a single hard rule.
- **Matchable historical aggregates cut both ways.** The pack that rescued pXphfXM shortened its search. For G10
  (censored demand, graded against generator truth), avoid providing an aggregate the agent can match to the
  reference answer; keep validation evidence partial or indirect.
- **Specification precision matters as much as trap design.** The partial-settlement ambiguity appeared in both
  failures. G10's estimator spec and unsettled/censored-day definitions should be stated at the grain they are
  graded.
- **Infrastructure:** use `--agent-setup-timeout-multiplier 3` for gemini-cli baselines on this host.
