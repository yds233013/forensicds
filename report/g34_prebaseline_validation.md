# G34 — `fleet-reliability-gate` pre-baseline validation

**Task:** `candidates/g34-fleet-reliability-gate`
**Status:** built, validated locally and under Harbor, **FROZEN at `f14dd0c0dbcd763c`**, **no baseline run**.
**Gemini baseline: NOT RUN.** No target-model trial of any kind has been executed against G34.

---

## 1. What the task asks

A pump manufacturer sizes its FY27 spare critical-assembly build on the share of the installed base whose
**original** critical assembly will suffer an unplanned failure within 36 months of service age. The FY27
procurement rule expands the build when that share exceeds **0.28**.

The incumbent pipeline in the workspace reports **55.2%**, which clears the trigger comfortably. The
incumbent is not incompetent: it follows each unit from commissioning and stops following it when anything
other than a failure ends the record. That is the correct way to recover **how long an assembly lasts**, and
it is exactly what the engineering note asks for in its own section. It is the wrong object for the
procurement rule, which is written on **what actually happens** to a unit's original assembly under the
current maintenance programme.

The two objects are both graded, from the same histories:

| | object | outcome roles |
|---|---|---|
| `aftermarket.*` | cause-specific cumulative incidence (crude risk) | overhaul and retirement are **outcomes**; cut-off is an incomplete record |
| `engineering.assembly_failure_rate_36m` | net risk, 1 − KM | overhaul, retirement **and** cut-off are all incomplete records |

This is failure mode **F9** — right method family, wrong statistical object — realised so that the *same*
analyst, on the *same* data, must produce both objects and keep them apart. The published 55.2% is not a
bug to be found; on the visible extract it is the correct answer to the engineering question
(truth 0.5547) and a badly wrong answer to the procurement question (truth 0.3598).

---

## 2. Graded facts and the evidence a real analyst would have

Every graded fact must be derivable from artefacts in the agent's workspace. Nothing is graded that
depends on generator-only knowledge.

| Graded fact | Evidence available in the workspace |
|---|---|
| `horizon_months` = 36 | stated in the FY27 rule, `docs/aftermarket_planning_memo.md` |
| `installed_base_units` | row count of `asset_register` |
| `event_counts.*` | `work_orders.wo_type`, with each code defined in `docs/event_dictionary.md` |
| `units_at_risk.{12,24,36}` | derivable from commissioning dates, work-order dates and the extract cut-off in `extract_meta` |
| `aftermarket.unplanned_failure_rate_36m` | the object is named by the procurement rule ("share of the installed base"); the SOP states an overhaul **exchanges the assembly, which is scrapped**, and that retirement is **commercial, not condition-driven** — so neither leaves an assembly that can still fail |
| `aftermarket.overhaul_rate_36m` | same; overhauls are scheduled on age **and the site's next planned shutdown window** (SOP), which is why they are not independent of age |
| `aftermarket.retirement_rate_36m` | same; SOP states retirement is a commercial decision |
| `aftermarket.still_original_assembly_36m` | the complement; the contract states the four are mutually exclusive outcomes of the same units |
| `engineering.assembly_failure_rate_36m` | `docs/engineering_note.md` asks for assembly life for the overhaul-interval review, which is the net-risk question |
| `recommendation` | the 0.28 trigger in the planning memo |

Two facts about the data that the agent must **infer and act on**, both documented:

- **A telemetry outage is not a removal.** `docs/maintenance_sop.md` states telemetry status is a separate
  feed and a channel outage is not a removal, and that vibration channels sit on the housings they monitor.
  The generator makes 55% of impending failures preceded by a gap, so censoring at outages is both the
  natural move and badly wrong (mutation M09 fails 6 checks).
- **The cut-off is an incomplete record for both objects.** Treating it as an outcome is mutation M10
  (fails 5 checks).

**No graded fact requires the generator.** Verified by `tools/g34/fixture_audit.py` and by the leakage
audit in §6.

### 2.1 Hint calibration in `instruction.md` — deliberate, and worth a reviewer's attention

The brief puts Operations' objection in plain business language: most assemblies "are swapped out at the
scheduled overhaul, or leave with the unit, long before anything fails in service". That is a
**domain** fact a real analyst would certainly be told in this meeting, and withholding it would make the
task a guessing game rather than a statistics problem. It is deliberately **not** a method hint — the
words "competing risks", "cumulative incidence", "censoring" and "Kaplan–Meier" appear nowhere in the
agent's environment.

The evidence that the hint is not sufficient: analysis **B**, the one-line competing-risks mapping written
by someone who has fully accepted Operations' point but censors retirement, still fails at 13.9–37.7 τ.
Knowing *that* overhaul removes an assembly does not tell you *which* codes take which role in which of
the two questions, and that is where every wrong analysis dies.

A reviewer may still judge this generous. It is a calibration choice, made once, before any model was
run, and it is not tuned afterwards.

---

## 3. Fixtures

Four extracts. One is visible in the agent's environment; three are hidden and never present in it.

| extract | n units | regime | q1 (crude, graded) | q2 (net) | decision |
|---|---|---|---|---|---|
| `visible` | 9000 | as documented | 0.3598 | 0.5547 | **expanded** |
| `hidden_a` | 8200 | longer assembly life (`wb_scale` 40 → 50) | 0.2523 | 0.4011 | **baseline** |
| `hidden_b` | 9600 | fleet wind-down (faster retirement) | 0.2526 | 0.5543 | **baseline** |
| `hidden_c` | 8800 | shorter assembly life (`wb_scale` 40 → 30) | 0.5484 | 0.7659 | **expanded** |

The decision splits 2 / 2, so a constant answer cannot pass (mutation M13, hard-coded `"expanded"`, is
caught by `hidden_a` and `hidden_b` and by nothing else — which is precisely what the hidden extracts are
for).

`hidden_b` is the sharpest case for the design: q2 = 0.5543, almost exactly the published 55.2%, while
q1 = 0.2526 sits **below** the trigger. An agent that reports the net risk against the procurement rule
gets the decision wrong in the direction that costs money.

---

## 4. Tolerance

τ = `TOL_MULTIPLIER` × `SE_REF`, where `SE_REF` is the **RMSE of the accepted estimator over 100
Monte-Carlo redraws of the same design** (`tools/g34/fixture_audit.py`). The tolerance is therefore
anchored on the accepted estimator's own sampling behaviour, not on a guess.

`TOL_MULTIPLIER = 5.0`, defined once in `tests/scenarios.py`.

| extract | quantity | truth | SE_REF | τ |
|---|---|---|---|---|
| visible | unplanned_failure_rate_36m | 0.3598 | 0.00275 | 0.01377 |
| visible | overhaul_rate_36m | 0.4104 | 0.00336 | 0.01682 |
| visible | retirement_rate_36m | 0.1736 | 0.00204 | 0.01021 |
| visible | still_original_assembly_36m | 0.0562 | 0.00214 | 0.01069 |
| visible | assembly_failure_rate_36m | 0.5547 | 0.00980 | 0.04900 |
| hidden_a | unplanned_failure_rate_36m | 0.2523 | 0.00260 | 0.01300 |
| hidden_a | overhaul_rate_36m | 0.4721 | 0.00337 | 0.01683 |
| hidden_a | retirement_rate_36m | 0.1967 | 0.00242 | 0.01209 |
| hidden_a | still_original_assembly_36m | 0.0789 | 0.00237 | 0.01187 |
| hidden_a | assembly_failure_rate_36m | 0.4011 | 0.00922 | 0.04610 |
| hidden_b | unplanned_failure_rate_36m | 0.2526 | 0.00247 | 0.01237 |
| hidden_b | overhaul_rate_36m | 0.2192 | 0.00266 | 0.01328 |
| hidden_b | retirement_rate_36m | 0.5050 | 0.00269 | 0.01344 |
| hidden_b | still_original_assembly_36m | 0.0232 | 0.00127 | 0.00633 |
| hidden_b | assembly_failure_rate_36m | 0.5543 | 0.01659 | 0.08295 |
| hidden_c | unplanned_failure_rate_36m | 0.5484 | 0.00299 | 0.01497 |
| hidden_c | overhaul_rate_36m | 0.2644 | 0.00309 | 0.01546 |
| hidden_c | retirement_rate_36m | 0.1576 | 0.00226 | 0.01129 |
| hidden_c | still_original_assembly_36m | 0.0295 | 0.00159 | 0.00794 |
| hidden_c | assembly_failure_rate_36m | 0.7659 | 0.00790 | 0.03951 |

The decision is graded exactly, not within tolerance.

### 4.1 The multiplier moved from 3.5 to 5.0 during the build — disclosed

This is a **loosening** and it deserves scrutiny. The sequence, in order, was:

1. At 3.5, the **correct** estimator exceeded its own tolerance on `hidden_a` (ratios 1.03 and 1.08).
2. The first response was to **fix the fixture, not the tolerance**: `hidden_a` had `overhaul_age = 17`,
   leaving only ~50 units at risk at 36 months. It was retuned to reach the `baseline` regime by a
   different route (`wb_scale = 50`), giving 379 at risk.
3. It was still marginal at 1.03. The cause was diagnosed as `SE_REF` itself: at 30 redraws it carries
   ~13% sampling error, and **20 numeric checks must pass jointly**, so a multiplier sized for a single
   2σ test is the wrong object. `SE_REF` was recomputed at 100 redraws and the multiplier raised to 5.0.

The honest characterisation: step 3 is a correction of a mis-specified tolerance, but a reviewer is
entitled to ask whether 3.5 with better-conditioned fixtures throughout would have been preferable. The
defence is the measured separation in §5 — the accepted estimator sits at ≤ 0.35 τ and the narrowest
wrong analysis at 1.94 τ, a 5.5× gap — not the multiplier itself.

---

## 5. Separation

### 5.1 Wrong-analysis panel (`tools/g34/agent_panel.py`)

Error against the accepted estimator, in tolerance units, worst over the five graded quantities. A value
above 1.0 means the extract rejects that analysis.

| analysis | hidden_a | hidden_b | hidden_c | visible |
|---|---|---|---|---|
| ACCEPTED (oracle) | 0.00 | 0.00 | 0.00 | 0.00 |
| A — polished 1−KM for both objects | 43.68 | 67.65 | 35.68 | 37.36 |
| B — one-line competing-risks mapping, retirement censored | 16.33 | 37.65 | 13.94 | 16.75 |
| C — raw event fractions | 60.97 | 122.30 | 69.06 | 62.50 |
| D — mature records only | **2.06** | **2.53** | **1.99** | **1.94** |
| E — censor at telemetry outage | 10.31 | 10.37 | 15.87 | 12.85 |
| F — every record end a competing outcome | 20.45 | 9.86 | 20.57 | 23.94 |
| G — cumulative hazard read as a probability | 36.79 | 38.78 | 52.49 | 27.38 |
| H — correct machinery, the two objects swapped | 11.15 | 23.73 | 14.45 | 13.59 |

**8 / 8 wrong analyses rejected by every extract.** Narrowest margin: D at 1.94 τ.

Accepted estimator vs **latent generator truth**, worst over quantities: visible 0.30, hidden_a 0.35,
hidden_b 0.28, hidden_c 0.13. The accepted estimator is unbiased against the thing being modelled, not
merely self-consistent.

### 5.2 Mutation suite (21 distinct cases, in-container, final tolerance)

`M00_oracle_equivalent` — an independent re-implementation of the accepted estimator — scores **1**.
`M21_oldest_cohort` — the complete-observation restriction, a legitimate route — scores **1**.
All nineteen wrong mutations score **0**. Full results in `tools/g34/` and `/tmp/g34_mutations2.csv`.

Two cases worth naming:

- `M13_hardcoded_decision` is caught **only** by `hidden_a` and `hidden_b`. Without hidden extracts with
  the opposite decision, a constant answer would pass.
- `M18_hardcoded_counts` is caught **only** by `test_event_counts_and_population`. The bookkeeping checks
  are not decoration.

### 5.3 A defect found in my own validation — disclosed

`M21_oldest_cohort`, `mutations/M21_oldest_cohort.py` and `mutations_extra/C_oldest_cohort.py` were
**byte-identical to `M00_oracle_equivalent`**: the cohort restriction was never written into the generated
file. The first mutation run therefore reported "M21 passes" while actually running the oracle under a
different name, and an earlier note in the research log that "C_oldest_cohort passed once with reward 1"
is explained by the same bug. `tools/g34/make_mutations.py` now generates M21 properly and the duplicate
file was deleted. **No conclusion in this report rests on the pre-fix run.**

Hash-checking the whole suite for the same defect then found a **second** instance:
`M04_crude_for_q2` was byte-identical to `M01_correctQ1_wrongQ2` — the same substitution defined twice
under different names. Both are genuinely wrong and both scored 0, so nothing was mis-graded, but the
suite's apparent coverage was inflated by one. The redundant name was **removed rather than replaced
with an invented case**, and the suite is now 21 distinct files with zero duplicate hashes.

The general lesson, recorded because it will recur: **a mutation that fails to mutate reports a pass and
looks like good news.** Pairwise hash-distinctness is now part of the suite's own acceptance, not an
afterthought.

### 5.4 Valid-but-wasteful routes — where the acceptance boundary actually sits

Re-measured after the fix, against the accepted estimator, in tolerance units:

| route | frozen draw (worst fixture) | worst over 20 redraws/fixture | verdict |
|---|---|---|---|
| complete-observation restriction (units with a full 36 months observed; keeps ~5 000 of 9 000) | 0.49 | **0.74** | **accepted**, robustly |
| arbitrary oldest-**quartile** restriction (discards 75%) | 1.33 (hidden_a) | 1.75 | **rejected** on 1 of 4 frozen extracts; fails 10–25% of redraws |
| narrowest **wrong** analysis (D, mature records only) | 1.94 | — | rejected |

The principled conservative route — restrict to units observed for the whole horizon — passes with
substantial margin. An *arbitrary further* subsample that discards fully-observed data straddles the
boundary. There is no room to admit it: doing so would start admitting D at 1.94.

**This supersedes my earlier statement that "the oldest-quartile analysis is valid but fails the
tolerance, and I am treating subsampling as outside the accepted set."** That framing was wrong on both
counts. Subsampling is *not* excluded by fiat — the principled version is accepted and measured. What is
rejected is one arbitrary variant with no additional validity, and the boundary is now a measured number
rather than a judgement call.

---

## 6. Leakage and integrity

Audited on the **packaged image**, not the source tree:

- no `/tests`, `/solution` or `/tmp/build` in the final image (multi-stage build discards the generator);
- zero hits for regime names, seeds, estimator names or truth values anywhere in the image;
- `assets`, `work_orders` and `telemetry_status` all shuffled before insert — rowid/unit_id correlations
  all |r| < 0.02, so generation order carries nothing;
- `extract_meta` contains operational keys only;
- 1555 of 2540 failures preceded by a telemetry gap (the informative-gap mechanism is live);
- `SITE_XFER` count 0 (removed per FIX 4).

**Clean-room reproducibility.** A `docker build --no-cache` from a pristine copy of the task tree
reproduces the warehouse digest exactly: `5ddb0c09a6620449`, 9000 asset rows, identical to the
development image.

**Verifier refusal paths fire.** Negative controls, each scoring 0:

| tamper | result |
|---|---|
| plant `/pytest.ini` | `verifier: pytest configuration file /pytest.ini present; refusing to grade` |
| add a file to the standard library | `verifier: files were added to or removed from the standard library; refusing to grade` |
| edit the warehouse in place | 9 checks fail, including `test_warehouse_unmodified` |

The `/tests`-unreadable-by-pipeline-user check passes under real Harbor. The earlier failure of that check
was an artefact of my **local** harness bind-mounting `/tests` under Docker Desktop virtiofs, which will
not accept `chmod`; it is not a property of Harbor.

**Maintenance note.** `tests/world.py` and `environment/build/world.py` are two copies of one generator and
are currently byte-identical (`037c8b7dea59c2df`). Nothing at runtime enforces that. Both are covered by
the freeze manifest, and any future edit must touch both or the hidden fixtures will silently stop
matching the visible extract.

---

## 6.1 The 14 checks

| section | checks |
|---|---|
| integrity | `test_warehouse_unmodified`, `test_pipeline_runs`, `test_rerun_is_deterministic` |
| schema and bookkeeping | `test_output_schema`, `test_event_counts_and_population`, `test_units_at_risk` |
| the statistical objects | `test_aftermarket_quantities`, `test_engineering_quantity`, `test_two_objects_are_different`, `test_probability_conservation`, `test_recommendation` |
| hidden extracts | `test_hidden_extract[hidden_a|hidden_b|hidden_c]` |

`test_two_objects_are_different` is the one that makes F9 explicit: an agent that reports the same number
for both questions fails even if that number is right for one of them.

---

## 7. Harbor results

| run | agent | trials | reward | cost |
|---|---|---|---|---|
| `jobs/g34-oracle-v1` | `oracle` | 1 | **1.000** | $0 (no model) |
| local harness | `nop` | 1 | **0** (6 failed / 8 passed) | $0 (no model) |

Nop fails `test_aftermarket_quantities`, `test_two_objects_are_different`,
`test_probability_conservation` and all three hidden extracts, while **passing**
`test_engineering_quantity` and `test_recommendation`. That is FIX 5 working as intended: an agent that
changes nothing still gets the published 55.2% and still gets the visible decision right, and still
scores 0.

**Model-powered validation cost is reported separately in §9.**

---

## 8. Acceptance gates A1–A20

| | gate | status |
|---|---|---|
| A1 | scientifically valid event process | PASS — six codes, four roles, two role-dependent on the question |
| A2 | Q1 verified against latent truth | PASS — accepted estimator ≤ 0.35 τ from truth on all four extracts |
| A3 | Q2 verified against latent truth | PASS — same measurement |
| A4 | independent valid estimators agree | PASS — M00 = 1; complete-observation route 0.74 τ |
| A5 | wrong-object separation | PASS — 1.94–122 τ, 8/8 rejected everywhere |
| A6 | correct-event-table separation survives | PASS |
| A7 | textbook shortcut fails | PASS — B at 13.9–37.7 τ |
| A8 | constant decision fails | PASS — 2/2 decision split; M13 caught |
| A9 | decision-only analyst fails | PASS — Nop scores 0 with the decision right |
| A10 | telemetry-gap mishandling fails | PASS — M09 fails 6 checks; E at 10.3–15.9 τ |
| A11 | Oracle = 1 | PASS — under real Harbor |
| A12 | Nop = 0 | PASS |
| A13 | mutation suite | PASS — 21/21 distinct cases as expected after the §5.3 fixes |
| A14 | cheap-solve suite | PASS — C (raw fractions) 60.9–122.3 τ; M14 (published 55.2) fails 6 checks |
| A15 | representation leakage clean | PASS — §6 |
| A16 | graded-fact evidence audit | PASS — §2 |
| A17 | hidden regimes preserve the invariant | PASS — see below |
| A18 | no generator-only truth | PASS — §2 |
| A19 | Harbor validation | PASS — `harbor check` 11/11, §9 |
| A20 | frozen checksums | PASS — G34 `f14dd0c0dbcd763c`; G05 unchanged at `77a6e432d9d2cba2`, §10 |

**A17 detail.** In the latent truth of every extract, the four aftermarket outcomes sum to 1
(`visible`, `hidden_b`, `hidden_c` exactly; `hidden_a` to 0.999999, the rounding of the stored truth),
and the net risk exceeds the crude risk in all four — 0.5547 > 0.3598, 0.4011 > 0.2523,
0.5543 > 0.2526, 0.7659 > 0.5484 — which is the ordering competing-risks theory requires. The hidden
regimes vary the operating conditions without breaking the structure that makes the task well posed.

**Previously frozen tasks untouched.** G05 re-verified at `77a6e432d9d2cba2` (expected value). `git
status` shows no working-tree change to any candidate other than `g34-fleet-reliability-gate`.

---

## 9. `harbor check`

**One invocation**, `jobs/2026-09-20__01-29-33`, `harbor check -c tools/task01/harbor_check_config.yaml`.

**Result: 11 / 11 checks pass.** No warnings, no failures.

| | |
|---|---|
| model | `claude-code` / `claude-sonnet-4-6` |
| invocations | 1 |
| **cost** | **$0.4196** |

This is a **validation** model run, not a solver or baseline run: the check agent reads the whole task
including `solution/` and `tests/` by design, and never attempts a solution. It does not contaminate a
future Gemini baseline — different vendor, different model, no cross-session persistence. The distinction
is set out in `research/harbor_check_protocol.md`.

Checks confirming the properties this report claims independently:

- **Tests Or Solution In Image** — "Neither tests/ nor solution/ is copied into any image layer."
- **Test Deps In Image** — pytest and friends exist only inside the verifier virtualenv.
- **Hardcoded Solution** — `solve.sh` "runs the full statistical pipeline to derive results from the
  SQLite data. It does not echo or cat any pre-computed answer."
- **Pinned Dependencies** — base image pinned by SHA256 digest; wheels hash-pinned.
- **Typos** — `TRUTH_KEY` in the tests matches the keys returned by `world.py`'s `truth()`.

**Project-wide model-powered validation spend after this invocation: $8.023692 over 17 jobs**
(previously $7.604092 over 16).

---

## 10. Freeze

**Frozen checksum: `f14dd0c0dbcd763c`**

Convention, identical to G05/G08/G10/G24:

```
git ls-files candidates/g34-fleet-reliability-gate | xargs shasum -a 256 | shasum -a 256 | cut -c1-16
```

- **37 files** under `candidates/g34-fleet-reliability-gate`
- per-file manifest: `research/g34/freeze_manifest.txt`, regenerable with `tools/g34/freeze.sh`
- generator copies match: `tests/world.py` == `environment/build/world.py` == `037c8b7dea59c2df`
- warehouse content digest, reproduced from a clean `--no-cache` build: `5ddb0c09a6620449`

From this point G34 is frozen. Any change to the task requires explicit authorisation and a new
checksum recorded here.

**Previously frozen tasks are unchanged.** G05 = `77a6e432d9d2cba2` (expected).

---

## 11. Open risks

1. **The multiplier was loosened mid-build** (§4.1). Measured separation is 5.5×, but the decision is
   disclosed rather than defended as obviously correct.
2. **D (mature records only) sits at 1.94 τ**, the narrowest margin in the suite. Under the earlier 3.5
   multiplier it sat at ~2.8 τ. It is rejected on all four extracts, but it is the analysis most likely to
   pass if any fixture were re-drawn unluckily.
3. **The two generator copies are unenforced** (§6).
4. **`SE_REF` at 100 redraws still carries ~7% sampling error.** The multiplier is sized to absorb this;
   it is not eliminated.
5. **My own mutation tooling produced two defective cases** (§5.3): one vacuous (identical to the oracle)
   and one redundant (identical to another mutation). Both were caught by hashing the files, not by the
   suite itself. The suite is now 21 distinct cases with zero duplicate hashes, but the class of error is
   worth carrying forward to G35+: a mutation that fails to mutate reports a pass and looks like good
   news, and a mutation duplicated under a second name inflates coverage silently.
