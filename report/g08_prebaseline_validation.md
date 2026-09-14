# G08 pre-baseline validation: forecast accuracy under settlement vintages

- Task: `candidates/g08-forecast-accuracy-vintages/`
- Design and revision log: `research/g08/G08_build_design.md` (§17 is the as-built record)
- Dev tools: `tools/g08/`

No model was run against the task. Tasks 01–06 are unchanged (checksums in §9).

## 1. Final validation results (final version)

| Check | Command / tool | Result |
|---|---|---|
| Oracle (Harbor) | `harbor run -p candidates/g08-forecast-accuracy-vintages -a oracle -o jobs --job-name g08-oracle-5 -y` | **1.0** (20 passed; 3m53s) |
| Nop (Harbor) | `harbor run -p candidates/g08-forecast-accuracy-vintages -a nop -o jobs --job-name g08-nop-5 -y` | **0.0** (16 failed, 4 passed) |
| Mutation suite (task image, real `test.sh`) | `python3 tools/g08/shortcuts.py --docker forensicds-g08:dev --jobs 4` | **40/40 as expected** |
| harbor check | `harbor check candidates/g08-forecast-accuracy-vintages -c tools/task01/harbor_check_config.yaml -o jobs --job-name g08-check-4` | **11/11 pass** |
| Reference = oracle = alternative implementations, all 4 extracts | `tools/g08/quickcheck.py {oracle, alt_sqlite.py, alt_replay.py, variant_mart.py} <4 extracts>` | 16/16 PASS |
| Reference vs generator bookkeeping | `tools/g08/calibrate.py` | 0 mismatches |
| Generator invariants | `validate_runs` asserted at every build | hold on all 4 extracts |

Per-case mutation output: `report/g08_mutations.txt` / `.json`.

## 2. Validation history

1. **First build.** Harbor Oracle 1.0 (g08-oracle-1) and Nop 0.0 (g08-nop-1). The first mutation run was stopped when
   the review changed the task.
2. **Independent adversarial review 1.** Grading was sound, but the task was easier than Task 02 on paper. The review
   also raised timeout, tolerance, generator-invariant and timeline issues. All were fixed (design §17.2).
3. **Mutation suite r2:** 40/40. **Independent adversarial review 2:** no blocking issues. The effective-time trap
   duplicated an existing mutation; the stale incident note and 2-dp pack head-to-heads were fixed (design §17.4). The
   Harbor runs in flight were stopped.
4. **Mutation suite r3:** 40/40. Harbor Oracle 1.0 / Nop 0.0 (g08-oracle-3 / g08-nop-3). harbor check 10/11:
   `behavior_in_tests` failed because the memo's 5-minute build limit was not tested. Fixed: the memo states
   10 minutes, and `test_build_time` enforces it.
5. **Final re-run (r4):**
   - mutation suite 40/40 with 20 checks;
   - Harbor Oracle 1.0 / Nop 0.0 (g08-oracle-4 / g08-nop-4);
   - harbor check 10/11: the model-graded `behavior_in_task_description` wanted the memo to spell out charge-basis and
     gate semantics. It had passed in the two previous checks. Spelling those out would name the root cause, so
     instead the memo now names the KPI definition document it already refers to ("as we define it").
6. **Final (r5, after that one-line memo change):** Harbor Oracle 1.0, Nop 0.0, harbor check 11/11. The mutation
   suite is unaffected by instruction text; its r4 result stands.

## 3. Extract statistics

| Extract | Settlement runs | IS runs | Withdrawal re-runs | Data corrections | IS status changes recorded after the close of a run published before it (of which withdrawals) | Scoped re-issues | Closed months | Examples | Unsettled |
|---|---|---|---|---|---|---|---|---|---|
| visible | 58,172 | 14,905 | 621 | 520 | 236 (44) | 21 | 14 | 70,854 | 693 |
| hidden_a | 64,355 | 16,651 | 1,962 | 960 | 565 (171) | 34 | 15 | 77,364 | 2,807 |
| hidden_b | 36,020 | 10,306 | 353 | 389 | 125 (32) | 84 | 8 | 103,968 | 657 |
| hidden_c | 44,340 | 10,981 | 604 | 1,524 | 226 (37) | 34 | 10 | 98,280 | 484 |

**Visible headlines:**

| Source | v4 vs v3 |
|---|---|
| Deployed mart (the review) | −29.7% |
| January pack | −15.2% |
| Truth, 26,999 common forecasts | −13.6% (v3 4.196%, v4 3.625%) |

## 4. How wrong repairs move examples and headline (visible extract, from `tools/g08/calibrate.py`)

| Wrong repair | Examples differing (key / value) | v4 vs v3 head-to-head |
|---|---|---|
| truth | 0 / 0 | −13.60% |
| latest current run, any type | 0 / 67,340 | −13.15% |
| EST (first published) | 0 / 70,854 | −10.28% |
| IS, current status | 0 / 3,294 | −13.86% |
| IS scheduled run | 0 / 3,408 | −13.14% |
| latest run of any type at close | 0 / 31,150 | −13.14% |
| corrections of any run type | 0 / 21 | −13.60% |
| IS published by close, current status | 0 / 2,601 | −13.85% |
| latest IS published by close, status ignored | 0 / 126 | −13.59% |
| status reconstructed on `effective_from` | 0 / 467 | −13.70% |
| one global cutoff (as-of) | 0 / 3,294 | −13.86% |
| UTC gate | 0 / 865 | −13.54% |
| issue-grain lock | 1,165 / 0 | −13.60% |
| latest issue (post-gate included) | 0 / 22,973 | −26.13% |
| scheduled issue only | 798 / 233 | −13.55% |
| current portfolio dimension | 0 / 27,307 | −11.57% |
| mapping by run date | 0 / 1,334 | −13.56% |
| KPI month by run date | 1,344 / 8,652 | −13.62% |
| unsettled scored on latest | 0 / 693 | −13.76% |
| unsettled dropped | 693 / 0 | −13.60% |
| head-to-head over production periods | 0 / 0 | −23.73% |
| deployed mart semantics | 14,356 / 55,493 | −30.03% |

Most wrong repairs give a head-to-head within about 0.5 pp of the truth, so only example-level state separates them.

## 5. Mutation suite (final, 20 checks per case)

| Class | Cases | Result |
|---|---|---|
| Controls | nop (0); oracle, alt_correct_plain_python, alt_correct_sqlite_windows, alt_correct_event_replay (1) | all as expected |
| Wrong actual | latest current, first-published EST, IS current status, IS scheduled run, latest any type at close, corrections any type, published-by-close current status, latest IS published by close (status ignored), status by effective time, loaded_at knowledge time, one global cutoff, at forecast creation, drop revised periods, unsettled fallback, unsettled dropped | all 0 |
| Wrong forecast / grain / KPI | latest issue, UTC gate, issue-grain lock, scheduled only, current dimension, mapping by run date, KPI month by run date, head-to-head over production periods | all 0 |
| Partial / patch / cheat | actuals only, actuals + forecasts, everything but mapping, metric-only patch, output-only patch, warehouse edit, import verifier reference | all 0 |
| Overfits (visible pass, hidden fail) | hard-coded close timestamps (hidden a/b/c), portfolio membership (a/b/c), model pair (c), horizons 1..7 (b), as-of (a/b/c) | all 0, failing only `test_hidden_*` |

## 6. Answer-key audit (agent-visible artifacts)

| Artifact | Contains | Could it be transcribed or matched? |
|---|---|---|
| `instruction.md` | symptom (−29.7% review, −15.2% January pack), outputs, no special-casing, points to KPI doc | No cause, run, clock, gate or grain named |
| `README.md`, `RELEASES.md` | repo map; mart decisions, 5 wrong and 4 correct | Decisions presented as improvements, mixed with correct ones |
| `fcaccuracy/*`, `sql/accuracy_examples.sql` | deployed mart | No close, status-history, gate or membership logic; `monthly_kpi` aggregation already correct (not a vintage rule) |
| `docs/kpi/forecast_accuracy_kpi.md` | definition: forecast traded on vs volume charged on; delivery month; pack at close | Definition only; no runs, clocks or knowledge time |
| `docs/finance/scorecard_policy.md` | months final at sign-off; no restatement | Governance fact |
| `docs/finance/billing_feed_retirement_2026.md` | retired snapshot = volume the charge was calculated on, requested per month | Describes a retired artifact; historical snapshots not in the extract |
| `docs/settlement/settlement_process.md` | run types, IS charged, reconciliation, withdrawal notices (charge stands until notice received), corrections | Process facts; does not connect them to the close |
| `docs/data/data_dictionary.md` | `effective_from` vs `recorded_at`, current status, `loaded_at` backfill, SCD2 membership, current dim | Schema facts; both clocks described neutrally |
| `docs/trading/day_ahead_process.md`, `docs/forecasting/forecast_store.md` | 11:00 UK gate lock; scoped re-issues | Operational facts; no timezone conversion or table logic |
| `docs/portfolio/portfolio_restructure_2026.md`, `docs/models/v4_release_note.md` | restructure dates; v4 auto re-issue (attractor) | Facts |
| `notebooks/kpi_pack_legacy.ipynb` | joins retired feeds; run at close; paired head-to-head | Not runnable; no reconstruction of either feed |
| `reports/kpi_packs/*` | WAPE at 1 dp by model × portfolio × month; 1-dp head-to-heads; January coverage note | Aggregates only; no counts. Legacy months only (July/August produced by the mart). Rules can be compared, examples cannot be recovered; hidden extracts have no packs |
| `reports/accuracy_review_2026-09.md`, `reports/ops/…`, `out/accuracy/` | mart/EST outputs | Wrong semantics by construction |
| `notes/…thread`, `ops/settlement_incidents.md` | conflicting opinions; incident facts | Opinion and facts |

**Cheap paths tested and failing:**
- one document;
- one WHERE clause (IS + current status);
- matching packs;
- restoring the notebook (feeds retired);
- current/final actuals;
- `status_effective_from` shortcut;
- latest IS published by close;
- re-run lag heuristics (review 2: none pass any extract).

## 7. Adversarial review findings and fixes

See design §17.2 and §17.4.

**Review 1** (easier than Task 02; timeouts; tolerance; generator invariant; untracked files; timeline). Fixed by:
- the effective-vs-recorded status clock with long-tail withdrawal notices;
- count-free packs;
- a 10-minute graded build limit with 660 s per build and 4800 s total;
- WAPE tolerance 1e-7 with an unrounded spec;
- `validate_runs` assertions and a boundary-template fix;
- a consistent timeline, mixed release notes, and a KPI doc sentence removed;
- `PYTEST*` env stripped; test.sh 755.

**Review 2** (no blocking issues). Fixed by:
- the effective-time trap made distinct from current status (supersession effective at correction);
- the near-miss mutation added;
- stale incident note; 1-dp pack head-to-heads; notebook columns.

## 8. Unresolved risks

- **Headroom.** Review 2 rated the task roughly on par with Task 02 on paper, not clearly harder.
  - Each component has a supporting doc sentence.
  - Packs can still reject whole candidate rules at 1 dp: the current-status or effective-time rules mismatch
    many cells.
  - A strong agent that validates against packs may reach the correct rule in ~30–40 actions.
- **Most likely model failures:**
  - latest IS by close without checking withdrawal notices (126 examples, pack signal nearly invisible);
  - the effective-time or current-status clock;
  - UTC gate or scheduled-only lock;
  - scoped re-issue grain;
  - mapping by run day.
- **Contestable semantics.**
  - Charge basis "as it stood at close" relies on scorecard policy + notebook + billing note + settlement doc.
    Reviewers judged it determinable, but an agent could still argue for restating closed months.
  - Unsettled at close (not carried forward) is supported by the January coverage note.
- **Hidden extracts.** They exercise documented rules in situations that are rare in the visible extract: horizons
  1..10 ("currently D+1 to D+7"), an EV portfolio, three models, correction chains. A sensible agent hard-codes none
  of these, but the risk is not zero.
- **Verifier cost.** About 3 minutes for the oracle in Harbor; 5 pipeline builds plus 4 world generations. A slow
  but legal pipeline (≤10 min per build) fits within 4800 s.
- **Domain realism.** The settlement run names are generic and fictional; no real market is claimed.

## 9. Git, security, frozen tasks

- **Frozen checksums** (`git ls-files <task> | xargs shasum -a 256 | shasum -a 256 | cut -c1-16`), all equal to the
  baseline:

  | Task | Checksum |
  |---|---|
  | 01 | 67259f9d0d438f7c |
  | 02 | f696367794c1a25f |
  | 02-explicit | 0e8200bd6d99c77b |
  | 03 | a8443d183fe160e6 |
  | 04 | 885b541eb480a020 |
  | 05 | 8daa31d646dfcb59 |
  | 06 | cd572b17bd537b4d |

- **Image:** multi-stage build; the final image contains `/workspace` only. No generator, reference, tests or
  solution (checked by `find` in the image and by harbor check).
- **Verifier sandbox:** pipeline as uid 65534, `/tests` 700, verifier env and `PYTEST*` variables stripped, fresh
  venv, start-up hooks refused. The reference-import cheat scores 0.
- **Secrets:** no API keys or credentials in task, tools, research or report files (secret scan before commit). Keys
  were only loaded into the environment for harbor check, never printed.
- **Models:** none run against G08.
