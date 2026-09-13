# Cross-task adversarial review (Tasks 01–05)

Date: 2026-09-13. Reviewer: an independent agent with no authoring context. It had read-only access to all five
tasks, built every workspace and ran local verifiers, and ran no models. Per-task reviews of 03, 04 and 05 were
separate; see each `report/taskNN_validation.md`.

This document records what the reviewer found, what was changed, and what remains open. Tasks 01 and 02 are
**frozen** (baselines exist), so findings about them are recorded but not fixed.

## 1. Findings and actions

### 1.1 Verifier template exploits (must-fix)

| Finding | Evidence | Action |
|---------|----------|--------|
| Agent code can import the hidden reference at grading time: the pipeline subprocess inherits `TESTS_DIR`, and `/tests/reference.py` is readable | Reviewer: 14/14 on Task 03 with a ~12-line import in `cohort.py`. Our control on Task 05: the same cheat scores 1 on a harness without the sandbox | **03–05:** the pipeline runs as uid 65534 via `setpriv`, `/tests` is `chmod 700`, hidden extracts sit in root-only temp dirs, and verifier variables are stripped from the pipeline env. An `import_verifier_reference` mutation is in all three suites (expected 0) |
| A pre-seeded `/tmp/verifier-venv` with a fake pytest makes `test.sh` report success | Reviewer PoC: pip reported "satisfied", `python -m pytest` exited 0 | **03–05:** `rm -rf` plus `venv --clear` before install; grading is refused if a `sitecustomize`/`usercustomize` start-up hook is importable |
| Residual: an agent running as root can still tamper with the base interpreter in other ways (e.g. `.pth` files, or patching the stdlib) | not demonstrated | **Open.** Mitigation: the reward-hacking grep in `failure_taxonomy.md`; a stronger fix needs Harbor to run tests in a fresh container |
| Same exploits in 01 and 02 | same harness shape | **Open (frozen tasks).** Must be fixed before these tasks are used again, which would make them new task versions |
| Timeout budgets implicit (03–05: 1200 s verifier vs up to 6 × 300 s pipeline runs) | task.toml | Verifier timeout raised to 2400 s in 03–05 (actual runs take seconds) |

### 1.2 Difficulty and shared tells

| Finding | Evidence | Action |
|---------|----------|--------|
| **Task 03:** a one-line filter (any `exploration_holdout` routing event) passed 14/14, because holdout never appeared outside intake events | reviewer PoC | Router releases now re-evaluate unworked leads with the holdout draw re-applied (documented in the router doc and deployment log). Visible: 625 release events; "any holdout event" adds 54 leads and "latest routing state" differs on 66. New mutation `any_holdout_routing_event` |
| **Task 04:** published cohort counts equal the correct counts exactly (answer key for membership) | reviewer reproduced 978…1265 | 3% of renewals are now papered 100–240 days after the term starts. Published counts differ by 2–7 per quarter, e.g. 2024-Q3 971 published vs 978 correct |
| **Task 05:** the buggy `units.py` scaffolds the fix (first-row dedupe, eligibility, cutoff helper); `min_active_users` is unused by the buggy code | code | Not changed; documented as a difficulty risk. Expert estimate lowered to 60 min |
| CHANGELOG entry prefixes name the faulty module (all five) | `cohort:`, `customer_quarter:`, `units:` | **03–05:** prefixes removed. **01–02:** open (frozen) |
| Docstring in the faulty module restates the buggy rationale | 03 `cohort.py`, 05 `units.py` (04 was already removed) | Rewritten to neutral one-line docstrings |
| Loaded-but-unused data points at the fix (03 loads `routing_events`/`sdr_activities`; 05 loads `memberships`) | `sources.py` | **Open.** Removing loads changes the oracle and mutation scaffolding; low severity |
| Same memo and requirements template; same repo layout; always an internal release as the cause | difflib 0.43–0.49 between 03/04/05 requirements | **Open.** A structural limitation of the current set, see §2 |
| Invariant stated almost verbatim in docs (03 evaluation definition, 05 plan/platform docs) | quotes | **Deliberate trade-off.** harbor check `behavior_in_task_description` failed on 03 before the property sentence was added. Recorded as the main difficulty risk for 03–05 |

### 1.3 Calibration (reviewer's estimate of exact details a passing repair needs)

| Task | Before fixes | After fixes (our count) | Model evidence |
|------|-------------|--------------------------|----------------|
| 01 | ~6 | — (frozen) | 2/3 pass, pass@3 = 1 |
| 02 | ~9–10 | — (frozen) | diagnosis 0/3 |
| 03 | 1 | 4: intake decision (not any/latest), ITT (not per-protocol), inclusive window bounds, `<= 60 days` any-channel label | none |
| 04 | 4 | 4, with no exact membership key and inclusive/exclusive segment thresholds tested | none |
| 05 | ~6 (3 pre-scaffolded) | 7: workspace unit, first assignment row, eligibility, maturity (explicit cutoff), ≥3 distinct users, window from assignment with a lower bound, estimator unchanged | none |

Reviewer's judgement: 03 and 04 look closer to Task 01 (too easy) than to Task 02, and 05 falls between them. We
agree that **03–05 are at risk of pass@3 > 30%**. That is an empirical question for the baselines, and the tasks
were not tuned against any model.

### 1.4 Redundancy and diversity

- 03, 04 and 05 share the same agent action: rewrite one population/unit module; metric and estimator code stay
  unchanged; graded by set equality of IDs plus downstream metrics. The reasoning differs: selection under feedback,
  proxy vs business state, and randomization unit with a post-treatment trigger. The *edit* does not.
- The label "high statistical content" in `distribution_matrix.md` overstated what is graded. No statistic is
  computed or changed by the agent in 03 or 05. The matrix now describes this as statistical *reasoning* content.
- All five tasks are B2B SaaS, SQLite plus a Python CLI; one SQL task, no notebooks/dbt/parquet.
- Missing mechanism classes: data-side defects (late or duplicated data, schema drift); timezone, DST and unit
  errors; many-to-many allocation; event idempotency; training-label lag; a "no bug" mix-shift control; peeking or
  multiple testing; observational confounding; two interacting causes.

### 1.5 Hidden fixtures

- No undocumented rules found. However, `benchmark_hypothesis.md` §5.4 said every hidden mechanism *exists in the
  visible extract*. That is not literally true: 03 hidden_b's re-routed holdout leads and pauses, and 05 hidden_a's
  `starter` plan, are documented but absent from the visible data. §5.4 now says "documented in the visible
  workspace".
- Single points of detection remain:
  - 03 `label_strictly_before_day_60` (hidden_c)
  - 04 `segment_boundaries_inclusive`, `reactivation_requires_ended_spell`, `overfit_reactivation_lookback_540d`
  - 05 `overfit_visible_strata` and `overfit_visible_self_serve_plans` (hidden_a)
  - 05 `window_end_inclusive` is not detected at all (informational probe)

### 1.6 Research-document integrity

| Finding | Action |
|---------|--------|
| Stale Task 03 numbers in `task.toml`, `solve.sh` and design §7 | Fixed |
| Task 04 design contradictions (header comment; mutation counts) | Fixed |
| `benchmark_hypothesis.md` §5.2 "No exact answer key in history" overstated (membership counts matched in 03 and 04) | 04 fixed by very-late signings. 03's 1.4.2 `n_leads` still equals the correct count for 1.x months, which is disclosed |
| `benchmark_hypothesis.md` redefines H1 relative to `hypothesis.md` while saying "supersedes nothing"; 03–05 cannot test the recognition side of H1 | Wording corrected in §3 |
| `task02_explicit_invariant_analysis.md` overstates in two places: "inference was a real bottleneck for the grain" when the disclosure stated the grain; "eliminated the grain error that caused every diagnosis failure" when two trials also needed other fixes | **Not edited** (historical baseline artifact, frozen tonight). Recorded here and as a morning decision |
| README task-status table stale | Updated |
| Citations (Lakkaraju 2017, Perdomo 2020, Sculley 2015, Kohavi/Tang/Xu 2020, Fabijan 2019) | Reviewer judged them real; still marked "to verify" |

### 1.7 Realism (open)

- Five companies share one repo template and one memo template, and executives write CLI commands into memos.
- Organisations are tidy: documentation is complete and correct, the CHANGELOG matches deployments exactly, and
  referential integrity is perfect.
- There is no git history, unit tests or CI; git would be the natural way to find the regression.
- Every incident has the same shape: one internal cause, a recent release, and a stakeholder pushing a decision.
- Data are small; every task except 02 runs in seconds.

## 2. Recommendations not yet implemented

1. Harden the 01 and 02 harnesses; this creates new versions of those tasks. Decide whether baselines must be re-run.
2. Add at least one task where the cause is data-side or external and an internal release is the distractor.
3. Vary templates: memo voice, repository layout, whether a CHANGELOG exists, and git history with unrelated commits.
4. Add a second detecting fixture for each single-point mutation.
5. Correct the two overstatements in the Task 02 ablation analysis (needs owner approval to edit a baseline doc).
6. Consider removing unused loads (03 `routing_events`/`sdr_activities`, 05 `memberships`) and the scaffolded helpers
   in 05.
