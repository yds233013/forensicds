# Task 04: Gemini 3 Flash baseline (diagnosis condition)

| Item | Value |
|------|-------|
| Task | `candidates/04-retention-metrics-regression`, frozen at 4ba24ca (checksum `885b541eb480a020`, unchanged before and after) |
| Command | `harbor run -p candidates/04-retention-metrics-regression -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task04-gemini3flash-diagnosis --artifact /workspace -y` |
| Trials | 3 valid (no infrastructure or API failures) |
| Agent time | 1.5–2.0 min per trial |
| Cost | $0.420 total ($0.127, $0.131, $0.161) |
| Raw artifacts | `jobs/task04-gemini3flash-diagnosis/` (git-ignored) |
| Per-trial table | `research/task04_trials.csv` |

## 1. Outcome

| Trial | Reward | Verifier | Steps / tool calls | Agent min | Cost |
|-------|-------:|----------|-------------------:|----------:|-----:|
| ok6i587 | **1** | 18/18 | 34 / 26 | 1.5 | $0.127 |
| 3SUW3gh | **0** | 13 failed (7 visible, 6 hidden) | 32 / 32 | 2.0 | $0.131 |
| AEZ8pU4 | **0** | 13 failed (7 visible, 6 hidden) | 56 / 35 | 1.9 | $0.161 |

- **Empirical success rate: 1/3 = 0.33.** This estimates per-attempt success from n = 3; it is not an exact pass@1.
- **pass@3 = 1.**

**Reward hacking: none** in any trial. Checked by grep over every tool-call argument and by reading the trajectories.

## 2. The decisive fact: all three got the lifecycle semantics right

All three rewrote `semantic/models/03_customer_quarter.sql` with handbook-correct logic on their first edit, about 20 steps in:
- cohort = `start_arr > 0`
- the CRM `created_at` proxy removed from classification
- reactivated = an earlier recurring line starting before S, otherwise new
- segment from starting ARR for cohort rows only, NULL otherwise

**The two failures came from one extra rule.** Both edited `01_stg_recurring_lines.sql` and `02_arr_boundaries.sql` to keep only lines whose contract `signed_at <= quarter end + 12 days`, and reused that cutoff in the reactivation logic.

**Counterfactual:** I removed only that filter from each failed trial's own 03 logic and kept the frozen 01/02 models. **Both then pass 18/18.** This was run locally on the visible and hidden extracts.

**Why the filter was attractive:**
- The workspace README describes the published FP&A workbook as "quarter end + 12 days; not restated for later bookings".
- Applying that exact rule reproduces **all six** published quarters in the reporting window: cohort count, NRR, GRR and logo churn to 4 dp, verified on both failed trials' final outputs.
- Our design and validation docs said the workbook "is not an exact answer key". That is true only for the *correct* logic, not for someone who re-implements the snapshot rule. **That design claim was wrong** and is recorded as a benchmark finding (§7).

## 3. Research-question checklist

| Question | ok6i587 (1) | 3SUW3gh (0) | AEZ8pU4 (0) |
|----------|-------------|-------------|-------------|
| Identified cohort/population semantics as the issue | yes (suspected 10, queried zero-start cohort accounts 14–18, stated 22) | yes (suspected 8, stated 12: 79 zero-start cohort accounts in 2026-Q1) | yes (20: 170 accounts created long before first line) |
| ARR > 0 at quarter start for cohort | yes | yes | yes |
| Incorrectly used CRM account existence | no for classification; kept an inner join to `crm_accounts` as a row filter (harmless here: CRM coverage is complete) | no (join removed) | no (join removed) |
| Reactivations / win-backs | correct (MIN recurring start < S) | correct logic, but over snapshot-filtered lines | correct logic, but over snapshot-filtered lines |
| Starting vs ending ARR; segment by starting ARR | yes / yes | yes / yes | yes / yes |
| Movement classification | correct | correct given its (wrong) ARR | correct given its (wrong) ARR |
| Quarter boundaries preserved | yes | S/E dates unchanged; ARR on a date now depends on signing cutoff | same |
| ARR bridge reconciles | in reasoning only (22); it does reconcile | in reasoning only; noticed Q4-end ≠ Q1-start ARR (18) and dismissed it as "different reports" | in reasoning only; chose per-quarter cutoff "so the bridge will be internally consistent" (20) |
| Validated account-quarter classifications | before the fix only (2 accounts) | no | no |
| Stopped once NRR/GRR or published numbers looked right | yes: read board CSVs (26–28); residual gap to published noted, never investigated | yes: "figures … match … cohort customers, starting ARR, and NRR for Q4 2025" (26) | yes: scalar NRR and ARR queries compared with published (36–48) |
| Patched dashboard/output | no | no | no |
| Hard-coded thresholds/lookbacks | no | +12-day publication lag for every quarter | same |
| Hidden fixtures exposed an overfit | n/a | the snapshot rule fails all hidden customer_quarter and metric checks | same |

## 4. Failed trials: taxonomy

| | 3SUW3gh | AEZ8pU4 |
|---|---|---|
| Dominant | **F4**: root cause found, repair adds a wrong rule | **F4** |
| Secondary | F6: 21 visible account-quarters dropped, 51 movements and 5 cohort flags differ. F5 flavour: the rule exists to reproduce published figures. F8 contribution (§7) | same |
| Genuine? | **Genuine, with a task-ambiguity contribution** | same |
| First conceptual mistake | Step 14 rejected the handbook-correct 2025-Q4 NRR (1.0239) as "still not the target", then read the README snapshot description as a rule the layer must implement ("as stated in the README") | Step 2 framed "past quarters have been restated" as the defect. Step 10 floated `signed_at`. Step 16 briefly held the correct view (a Q4-starting contract signed later still belongs to Q4). Step 20 reversed: "filtering by `signed_at` is crucial to avoid restatements" |
| Final implementation mistake | `signed_at <= DATE(q.end_date,'+12 days')` in 02 and in 03's history CTE, applied to all quarters including unpublished 2026-Q1/Q2 and every future extract | Same filter in the 02 join and 03 reactivation `EXISTS` |
| Visible failures | rows/boundary ARR, cohort, movements, segments, quarterly metrics, bridge, segment metrics | same |
| Hidden failures | hidden_a/b/c × (customer_quarter, metrics) | same |
| Aggregates plausible despite wrong state? | **Yes**: exact match to published history; per-quarter bridge identity holds; 2026 NRR plausible | **Yes** |

**Case for task ambiguity (F8 contribution):**
- The memo lists restating published quarters as part of the problem, and the CFO note says "I can't take a restatement of published numbers".
- The README gives the snapshot rule with its exact parameter, and that rule reproduces the workbook exactly.
- `docs/semantic_layer/README.md` says FP&A signed off after reconciling against the workbook. No trial opened it.

**Case for genuine error:**
- Requirement 1 says every metric follows the handbook, and the handbook defines ARR on a date only by line dates.
- The README describes the *old workbook*; it does not set a rule for the layer.
- CHANGELOG 2.0.0 and the deployment log say history was restated by design. Neither failed trial opened them.
- The filter drops accounts (requirement 2) and applies to unpublished and future quarters (requirement 3).
- Both agents noticed the ARR continuity break and rationalised it.
- 3SUW3gh had the correct value in hand; AEZ8pU4 briefly stated the correct principle.

**Verdict: genuine failures, with a design attractor that made the wrong goal unusually well confirmed.**

## 5. Investigation timelines

**ok6i587 (success)**
- SYMPTOM: board NRR above published.
- Evidence and hypothesis:
  - README, CFO note, handbook and data dictionary (2)
  - config, published CSV, baseline build (4); board CSV (6)
  - models 01–05 (8–12)
  - hypothesis: zero-start accounts in the cohort; account-level queries on 2 accounts (14–18); calendar.py (20)
- Repair: root cause and a single write of 03 (22).
- Validation: rebuild (24), board CSVs (26, 28: "small discrepancy persists" vs published 2025-Q4, not chased), final build (30).
- Outcome: 18/18.
- The final message attributes the residual gap to the README's no-restatement snapshot, which it asserted but never tested. Operational docs, CHANGELOG and distractors were not read.

**3SUW3gh (failure)**
- Evidence and hypotheses:
  - docs (2); published and board CSVs (4); all models (6); build.py (8)
  - ops docs: billing split, pricing, ABM (10)
  - aggregate cohort query and CRM root cause (12)
  - "not the target" and the snapshot hypothesis; late-signed lines query (14)
  - calendar (16); signing-date distribution to "verify the 12-day cutoff" (18)
- Repair: edits to 01/02/03 (20), rebuild (22).
- Validation: CSVs compared to published (24–26), config (28).
- Outcome: 13 failed.
- The final message calls a "missing reporting cutoff" a root cause and claims an FP&A standard that is not in the handbook.

**AEZ8pU4 (failure)**
- Evidence and hypotheses:
  - docs (2); CSVs and model listing (4); 01/02 (6); schema (8)
  - `signed_at` idea (10); late-signed query (14); 04 (16, briefly correct view); 03 (18)
  - root cause + cutoff decision + 170-account query (20); 05 (22); baseline build (24)
- Repair: edits 01 (26), 02 (28), 03 (32).
- Validation: rebuild (34); scalar NRR/ARR checks against published (36–48); referential integrity (50); build (52).
- Outcome: 13 failed.

## 6. Success vs failure: behaviour differences

| Dimension | ok6i587 | 3SUW3gh | AEZ8pU4 |
|-----------|---------|---------|---------|
| Breadth of evidence | low–medium | medium (read ops docs) | low–medium |
| Reading business definitions | high | medium (handbook used for cohort, not ARR) | medium (recalled ARR definition, then overrode it) |
| Checking data directly | medium (pre-fix, account level) | medium (aggregate) | medium |
| Considering alternatives | low | low–medium | low–medium |
| Correct grain | high | medium | medium |
| Validating intermediate state | low | low | low |
| Reliance on published or aggregate metrics | medium | **high** | **high** |
| Stopping after a plausible number | high | high | high |

- The success did **not** validate more thoroughly than the failures; no trial checked account-quarter state after its fix.
- What separated them was the target each chose after the fix. The success accepted "much closer to published". The failures treated exact agreement with published history as the goal and found a documented rule that achieves it.
- This is the H3 failure mode (validating against a headline or reference number instead of the invariant). Here it destroyed a correct repair rather than hiding an incorrect one.

## 7. Benchmark findings (task not modified)

1. **The published workbook is effectively an exact answer key for a wrong rule.** The very-late-renewal change added after review stops the *correct* logic from matching the workbook. The README's precise "+12 days" rule still reproduces it exactly. The design and validation claim "not an exact answer key" is inaccurate as written.
2. The signals that restatement is intended (CHANGELOG 2.0.0, deployment log "history restated") live in files the failing agents never opened. The memo and CFO note frame restatement negatively.
3. The lifecycle repair itself is mechanical: all three wrote it correctly on the first attempt, right after reading the handbook.

## 8. Difficulty verdict

**USEFUL EASY ANCHOR, with an underspecification risk.**
- **The recognition and lifecycle mapping the task was built to test** was solved 3/3 in about 2 minutes.
- **Headroom does not come from the latent invariant.** It comes from one attractor: a documented snapshot rule that exactly reproduces the published figures.
- **What the failures do show** is informative about validation behaviour: agents optimising agreement with a trusted historical number over the business definition.
- **What they are not** is evidence that retention lifecycle semantics are hard for this model.
