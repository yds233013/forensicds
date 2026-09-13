# Task 05: Gemini 3 Flash baseline (diagnosis condition)

| Item | Value |
|------|-------|
| Task | `candidates/05-onboarding-experiment-readout`, frozen at 4ba24ca (checksum `8daa31d646dfcb59`, unchanged before and after) |
| Command | `harbor run -p candidates/05-onboarding-experiment-readout -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task05-gemini3flash-diagnosis --artifact /workspace -y` |
| Trials | 3 valid (no infrastructure or API failures) |
| Job runtime | 6 m 22 s wall clock; agent phases 1.1–1.3 min each |
| Cost | $0.258 total ($0.087, $0.088, $0.083) |
| Raw artifacts | `jobs/task05-gemini3flash-diagnosis/` (git-ignored) |
| Per-trial table | `research/task05_trials.csv` |

## 1. Outcome

| Trial | Reward | Verifier | Steps / tool calls | Agent min | Cost |
|-------|-------:|----------|-------------------:|----------:|-----:|
| MaomctL | **1** | 14/14 (incl. 3 hidden fixtures with null, positive and negative effects) | 42 / 24 | 1.3 | $0.087 |
| axNEheD | **1** | 14/14 | 40 / 27 | 1.1 | $0.088 |
| okTydXM | **1** | 14/14 | 38 / 25 | 1.2 | $0.083 |

- **Empirical success rate:** 3/3 = 1.00. This estimates per-attempt success from n = 3; it is not an exact pass@1.
- **pass@3:** 1.

**Reward hacking: none.** No tool call touched `/tests`, verifier or reference files, reward files, `/solution`, Harbor, the interpreter or root-level paths. This was checked by grep and by reading each full tool-call list. As on Task 03, the sandbox was never tested by an attempt.

All three changed only `src/xp_analysis/units.py` and produced the reference readout:

| Readout | Units (control / treatment) | Effect | 95% CI | Decision | SRM p |
|---|---|---|---|---|---|
| Before the fix | 5,164 / 3,285 | +6.9 pp | — | ship | 7e-93 |
| After the fix | 1,680 / 1,717 | −0.3 pp | [−2.1, +1.6] | inconclusive | 0.53 |

## 2. What all three did

Each rewrote `build_units` as a transcription of the plan's Analysis bullets plus the activation definition (`T <= event_at < T + 14 days`, ≥ 3 distinct users). The repair:
- starts from assignments, not exposures
- filters to self-serve, non-internal workspaces
- keeps workspaces with `assigned_at <= analysis_date − 14 days`
- counts distinct users with a core action in the workspace window

**All three reused pieces already present in the buggy file:**
- the first-row assignment dedupe line, reproduced verbatim
- the eligibility filter
- the maturity helper or its formula
- `cfg.min_active_users`

None of the details that decide pass or fail had to be discovered from data. Those details are: the first assignment row, the lower window bound (pre-assignment core actions exist), maturity, and distinct users.

## 3. Research-question checklist

| Question | MaomctL | axNEheD | okTydXM |
|----------|---------|---------|---------|
| Identified post-treatment / exposure selection bias | partial: framed as a plan violation (12, 26); asymmetric logging only in final message | partial: generic "exposures are not assignments … selection bias driving SRM" (8); final message misstates the mechanism | **yes**: dashboard-load vs checklist-mount logging and resulting bias, before the fix (16–18) |
| Workspace as randomization unit | yes (12) | yes (4, 8) | yes (10) |
| Avoided user-level pseudo-replication (reasoned) | not discussed | only in final message | partial: standard-error / within-workspace correlation (18) |
| First assignment rather than exposure or cached variant | yes, reused dedupe line; never read platform doc; INC-5521 "first or subsequent?" doubt (24) unresolved | yes; read "first logged row" rule (4), planned earliest row (12) | yes; platform doc (10), "initial assignment" (22) |
| Recognised cross-workspace cached variants (XPP-44) | no | no (read the doc, never mentioned) | no |
| Included eligible assigned workspaces regardless of exposure | yes | yes | yes |
| Maturity cutoff | yes (inline, reasoned 26) | yes (reused helper) | yes (reused helper) |
| 14-day window, lower and upper bound | yes, inherited from doc and old code pattern; no reasoning about pre-assignment events | same | same |
| ≥ 3 distinct active users | yes | yes | yes |
| Investigated the sample-ratio warning | no | no (noted p "incredibly significant", 18) | partial: explained exposure-based SRM from readout counts (18); never computed assignment counts by arm |
| Preserved estimator and decision rule | yes | yes | yes |
| Validated workspace membership or outcomes directly | no | no (one SQL `unit_type` count, 32) | no |
| Stopped after a plausible effect or rate | yes: rate ~9% vs plan's 8%; claimed "tests are all passing" with none run (32) | yes: used plan's ~3,400 units as sanity check before fix (20); re-ran historical dates | yes: rate vs 8% baseline |
| Hidden fixtures exposed an overfit | no | no | no |

Documents never opened by any trial: `CHANGELOG.md`, `docs/platform/triggered_analysis.md` and `logs/`. No trial counted assignments or exposures by arm, counted duplicate or conflicting assignment rows, checked for pre-assignment core actions, or spot-checked individual workspaces.

## 4. Investigation timelines

**MaomctL**
- **Symptom:** memo.
- **Evidence inspected:**
  - README and plan (2)
  - readout (4)
  - INC-5521 (6)
  - `sources.py` / `units.py` (10)
  - activation doc (12)
  - data dictionary (14)
  - config, pipeline, estimator (16–20)
  - baseline run (22)
- **Root cause:** exposure-based user units (12).
- **Repair:** 26.
- **Validation:** rerun and readout (28–30), rate vs plan baseline and CSV head (32), sha256 determinism (36–38).
- **Outcome:** reward 1.

**axNEheD**
- **Evidence inspected:**
  - README, plan, notes (2)
  - data dictionary, platform doc, INC-5521 (4)
  - `sources.py` / `units.py` (6)
  - activation doc (8)
  - config and estimator (10–14)
  - baseline run and readout (16–18)
- **Root cause:** 8.
- **Pre-fix sanity check:** 8,449 units vs plan ~3,400, 31% vs 8% (20).
- **Repair:** 20.
- **Validation:** reruns, CSV head, four historical dates (28), SQL `unit_type` count (32).
- **Outcome:** reward 1.
- **Side effect:** re-running historical dates overwrote the 08-03…08-24 readouts; not disclosed.

**okTydXM**
- **Evidence inspected:**
  - README, plan, notes, config (2)
  - baseline run (6)
  - `units.py` (8)
  - activation and platform docs (10)
  - INC-5521 (12)
  - `sources.py` (14)
  - readout (16)
  - estimator (18)
  - pipeline (20)
- **Hypotheses:** unit mismatch (10); exposure asymmetry (16–18).
- **Repair:** 22.
- **Validation:** reruns, outputs listed, CSV head and readout, rate vs 8% baseline (24–36).
- **Outcome:** reward 1.
- **Final message:** reads "inconclusive" as "no significant impact".

## 5. Behaviour dimensions

| Dimension | MaomctL | axNEheD | okTydXM |
|-----------|---------|---------|---------|
| Breadth of evidence | low–medium | medium | medium |
| Reading business definitions | high | high | high |
| Checking data directly | low (none) | low (one count) | low (none) |
| Considering alternative hypotheses | low | low | low–medium |
| Reasoning at the correct grain | correct, unargued | correct | correct, with variance reasoning |
| Validating intermediate state | low | low–medium | low |
| Reliance on aggregate metrics | high | high | high |
| Stopping after a plausible number | high | high | high |

No failures, so there is no success/failure contrast.

## 6. Interpretation

- **Recognition:** all three recognised that the readout departs from the pre-registered plan within about 10 steps. Only one articulated the post-treatment mechanism before fixing.
- **Operationalisation:** the operational rules were copied rather than reasoned, including the first-assignment rule, the lower window bound and maturity. They are stated in the plan and activation doc and already partly coded in the buggy file.
- **Validation:** entirely aggregate (baseline rate, SRM p, determinism). No trial validated units directly.
- **Final write-ups:** MaomctL's reasoning claimed tests passed when none were run. axNEheD misdescribed the asymmetry mechanism in its final message. okTydXM over-interpreted an inconclusive result. The behavioural verifier does not grade these.

## 7. Difficulty verdict

**TOO EASY.** A Flash-tier model passed all hidden scenarios in about 75 seconds with one edit and without inspecting any rows. The pre-baseline cross-task review's warning was confirmed: plan, docs and scaffolding in the buggy file together make the repair a transcription. The task was not modified.
