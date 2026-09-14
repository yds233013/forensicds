# Task 06: Gemini 3 Flash baseline (diagnosis condition)

| Item | Value |
|------|-------|
| Task | `candidates/06-usage-statement-close`, frozen at commit 10746ea (file checksum `cd572b17bd537b4d`, unchanged before and after) |
| Command | `harbor run -p candidates/06-usage-statement-close -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task06-gemini3flash-diagnosis --artifact /workspace -y` |
| Agent | gemini-cli, `gemini-3-flash-preview` |
| Trials | 3 valid (no infrastructure or API failures; Harbor exceptions = 0) |
| Job runtime | 11 m 30 s (agent phases 3.3–6.0 min) |
| Cost | **$0.888** total (Harbor-reported: $0.405, $0.209, $0.274) |
| Raw artifacts | `jobs/task06-gemini3flash-diagnosis/` (git-ignored) |
| Per-trial table | `research/task06_trials.csv` |

Method: objective evidence from `tools/analysis/trial_evidence.py` (verifier results, cost, reward-hacking greps); code
diffs against the frozen workspace; step-cited reading of every tool call and all reasoning text in each ATIF
trajectory. Step numbers are ATIF step ids; elapsed times are from step 1. Nothing is inferred that is absent from the
trajectories.

## 1. Outcome

| Trial | Reward | Verifier | Steps / tool calls | Agent min | Cost |
|-------|-------:|----------|-------------------:|----------:|-----:|
| 9fGwNFp | **1** | 21/21 (incl. 3 hidden extracts × 3) | 116 / 62 | 6.0 | $0.405 |
| Yav3hqK | **1** | 21/21 | 54 / 39 | 3.3 | $0.209 |
| fiJFbgG | **1** | 21/21 | 82 / 46 | 4.7 | $0.274 |

- **Empirical success rate:** 3/3 = 1.00. This is an estimator from n = 3, not an exact pass@1.
- **pass@3:** 1.
- **Reward hacking:** none. No tool call touched `/tests`, the reference, hidden fixtures, `/solution`, `/logs/verifier`, reward files, Harbor, site-packages/`sitecustomize`, or root-level paths. This was checked by grep over all tool-call arguments and by reading every command. `test_sources_unmodified` passed in all three.
- **Sandbox:** never tested by an attempt.

## 2. What the three repairs look like

All three changed the same three components: `normalize`, `usage_mart` and `assemble`, with ledger reading inline or in a new
module. Each ended with essentially the oracle's semantics:

- **Record identity.**
  - Yav3hqK: `drop_duplicates(["event_id", "rev"])`.
  - 9fGwNFp and fiJFbgG: kept the 24 h TTL filter but keyed it on `(event_id, rev)`. This has no effect: the first
    delivery is always kept, and surviving identical copies collapse when the highest `rev` per event is chosen.
- **Usage mart:** highest `rev` per event over all deliveries, grouped by `window_start` month.
- **Statement:**
  1. filter `received_at < statement_close(month)`;
  2. take the highest `rev` per event, by `window_start` month;
  3. merge with the sum of all issued lines for each service month;
  4. line quantity = known − billed;
  5. amount = `usage_charge(terms_for(service_month), known)` − billed amount;
  6. the line type is `usage` when service month = S, otherwise `adjustment`.

**Benchmark flaw.** The close boundary was **inherited from the faulty code**. The faulty `assemble.py` already filtered
`(received_at >= opens) & (received_at < closes)` using the existing `statement_close()` helper, and all three agents
simply dropped the lower bound. None discussed `<` versus `<=`, records received after the close, or the delayed
September run.

## 3. Task-specific questions

| # | Question | 9fGwNFp | Yav3hqK | fiJFbgG |
|---|---|---|---|---|
| 1 | Event identity (event_id + rev) | yes (TTL re-keyed 58; highest rev downstream 60/66). At 44 it briefly planned highest-rev selection inside `normalize`, which would have admitted post-close revisions | yes (26 justified by "identical records" in vendor doc; 30) | yes (32; 38) |
| 2 | Highest rev current | yes (doc 42; data 48) | yes (12/24) | yes (12) |
| 2 | Voids | implicit (never mentioned) | implicit (never mentioned) | **explicit** (12) |
| 2 | Duplicate / revision / replay / correction distinguished | revisions vs repeats yes; replays and outage never discussed | by counts (22: 321 repeated deliveries, 2,310 revised events); replays not discussed | revisions yes; replays not discussed |
| 3 | Event month = `window_start` | yes (14–20); `window_end` never considered | yes (12/16) | yes (28–30) |
| 4 | Current-knowledge mart vs close knowledge | yes, implicit | **yes, explicit** (24: filter by close, then latest revision; docstring 30) | yes, implicit |
| 5 | Close boundary | `received_at < 2026-10-04T00:00Z` via existing helper; runbook read (22); `<` inherited, not discussed | same; contract and runbook never read; noticed extract ends 10-06 (24–26) but did not connect it to the close | same; contract and runbook not read; a debug script hard-coded a **wrong** close `2026-10-03` (66), never used in production |
| 6 | Prior-period adjustments | yes (plan 42 from instruction + contract §4.3–4.4 paraphrase 28; batch adjustment lines seen 50) | yes (reasoning 12/18; `export.py` summing adjustments 20); never looked at batch-era adjustment lines | yes (plan 32; Northwind batch adjustment lines 34) |
| 7 | Billed incl. prior adjustments | **yes, checked** (94–96: Northwind March billed includes the April adjustment) | yes by code (sums *all* ledger files, no `< S` filter; asserted, not checked) | yes by code (sums issued lines `< S`); not discussed |
| 8 | Rate card of service month | yes (50; code 66) | code only (28) | yes (44) |
| 9 | Allowances/tiers recomputed (not Δq × rate) | **yes, explicit** (50) | yes (24) | yes (code; thin reasoning 38) |
| 10 | Components repaired | normalize, mart, statement | normalize, mart, statement, new ledger module, job | normalize, mart, statement, job |

## 4. Evidence use

| Evidence | 9fGwNFp | Yav3hqK | fiJFbgG |
|---|---|---|---|
| Customer dispute email / AR queue | no | yes (4) | no |
| Console export | no | no | no |
| Issued statement ledger | Aug (30), Northwind Mar (80), all files grep (50) | Aug only (12) | Aug (22–24), Northwind Jul (32), Northwind cross-month (34) |
| Finance tie-out notebook | no | no | no |
| ADR-0012 | no | no | no |
| Vendor delivery doc | yes (42) | yes (10) | yes (10) |
| Contract §4 / billing schedule | yes (26) | no | no |
| Runbook | yes (22) | no | no |
| Incident note INC-2291 | no | no | no |
| Raw JSONL deliveries | pandas (14–20, 44, 48) | pandas counts (16, 22) | zgrep (16–20) |
| Batch-era statements with adjustment lines | yes (50, 80, 94–96) | no | Northwind lines only (34) |

Questions:

- **A. Trusted the tie-out because it reconciled?** Not applicable. No agent opened the tie-out notebook, so the designed
  attractor was never encountered.
- **B. Realised the tie-out shares the wrong semantics?** Not applicable, for the same reason.
- **C. Backtested against March–June statements?**
  - 9fGwNFp: partial. It noticed that Northwind's batch-era months had zero delta (96/104) but never reproduced a statement.
  - Yav3hqK and fiJFbgG: no.
  - Nobody used the batch history as an exact backtest.
- **D. Inspected raw revisions?** Yes in 9fGwNFp and fiJFbgG. Yav3hqK counted them only.
- **E. Distinguished authoritative from internally consistent evidence?**
  - Only 9fGwNFp used the contract and runbook as rules.
  - The other two took the close from the faulty code and the adjustment convention from the data catalog, `export.py`
    and the ledger.
  - None confronted a reconciling-but-wrong artifact: no tie-out, and no attempt to reconcile with the console.

## 5. Investigation timelines

**9fGwNFp**

| Elapsed | Step(s) | What happened |
|---|---|---|
| 0:00 | 1 | SYMPTOM: controller memo |
| — | 4–12 | Code, config, calendar |
| 0:25 | 14 | Hypothesis: receipt window vs usage month |
| 0:42 | 20 | Confirmed: 22 Northwind August-window records received before 4 Sep counted in August |
| ~1:00 | 22–26 | Runbook, contract; contract §4.3–4.4 paraphrased (28) |
| — | 30–32 | Issued ledger (Aug), rate cards |
| 2:10 | 42 | Root cause + plan: highest revision, window month, delta against billed |
| 2:21 | 44–48 | Discovered revisions summed or dropped; inspected an event history |
| 2:46 | 50 | Found batch-era adjustment lines; rule: charge difference under the service month's card, not Δq |
| 3:14 | 58–66 | Edits |
| — | 68 | **v1 wrong:** ledger path bug made billed = 0, so full history was rebilled as adjustments (364 lines) |
| — | 72–80 | Noticed via Northwind March adjustment = full-month usage |
| 4:16 | 84 | Fixed (197 lines) |
| — | 90–108 | Validation, all on Northwind: lines, billed sums per service month, August mart cell, summary |
| 5:46 | 116 | Final message. RESULT: reward 1 |

**Yav3hqK**

| Elapsed | Step(s) | What happened |
|---|---|---|
| 0:00 | 1 | SYMPTOM |
| — | 2–8 | README, catalog, inbox, code |
| 0:19 | 8 | Hypothesis: receipt-time misalignment |
| 0:34 | 12 | `received_at` vs `window_start`; revisions; "adjustment in a subsequent billing cycle" |
| 0:52 | 16 | Northwind August windows received 1–3 Sep |
| 1:37 | 22 | Counts of repeated deliveries and revised events |
| 1:49 | 24 | Full rule set: close filter, then latest revision, then charge delta against billed |
| — | — | Never reproduced the issued August statement (its script used the wrong window 3 Aug–3 Sep: 94,918 vs 95,544 left open) |
| 1:57 | 26–34 | Edits |
| 2:24 | 38 | Crash (fixed 40) |
| 2:33 | 42 | Correct output |
| — | 44–50 | Validation, all on Northwind: lines, August mart cells, summary; mart head |
| 3:01 | 54 | Final message (claims idempotency and a rerun check that never happened). RESULT: reward 1 |

**fiJFbgG**

| Elapsed | Step(s) | What happened |
|---|---|---|
| 0:00 | 1 | SYMPTOM |
| — | 2–8 | README, catalog, code, config |
| 0:18 | 10 | Vendor doc; hypothesis: time-window mismatch |
| 0:23 | 12 | Revision and void semantics |
| 0:35 | 16–20 | Raw JSONL: late Northwind records, rev ≥ 2 lines |
| — | 22–26 | August ledger, rate cards |
| 1:09 | 32 | Revisions dropped or double counted; delta plan |
| 1:26 | 34 | Northwind batch-era adjustment lines (incl. a 0.00 line and the 06-05 late issue) |
| 2:24 | 38–50 | Edits |
| 3:15 | 52 | Crash |
| 3:39 | 62 | **v2:** ledger parsed as floats, giving 364 lines with spurious `-0.000 / 0.00` adjustments; money aggregates effectively unchanged |
| — | 64–66 | Noticed on Northwind by eye |
| — | 70 | Parsing fixed |
| 4:03 | 72 | Correct output |
| — | 72–76 | Validation, all on Northwind: lines, August mart cells, summary |
| 4:28 | 82 | Final message (claims console consistency without opening the console export). RESULT: reward 1 |

## 6. Validation behaviour

| | Validation actions | Grain | Aggregate-only? |
|---|---|---|---|
| 9fGwNFp | Northwind lines; Northwind billed totals per service month vs ledger; Northwind August mart cell; line count; summary | one account, line level | no, but single-account |
| Yav3hqK | Northwind lines; Northwind August mart cells; Northwind summary; mart head and row count | one account | no, but single-account |
| fiJFbgG | Northwind lines; Northwind August mart cells; summary | one account | no, but single-account |

What no trial checked:

- statement-cutoff membership (which records fell before the close);
- revision histories after the fix;
- adjustment lines for any customer other than Northwind;
- the console export;
- a backtest of batch-era statements;
- a determinism diff.

Implausible or noisy intermediate outputs and how they were caught:

- **9fGwNFp:** full-history rebill. It was obviously wrong at line level and was caught on Northwind.
- **fiJFbgG:** float-parsed ledger gave zero-amount noise lines. Money totals were unchanged, so a totals-only check would
  have shipped it. It was caught by eye on Northwind.

Validation was single-customer line inspection. It was better than Tasks 03–05's pure aggregates, but not systematic.

## 7. Shortcut and failure-mode checklist

| Failure mode | Present in final code? | Present at any point? |
|---|---|---|
| Receipt-month attribution | no | no (only in the original code) |
| Event-time-only (ignore close knowledge) | no | no |
| Processing-time-only | no | no |
| Keep-last-received dedupe | no | no |
| Arbitrary 24 h dedupe window | kept but inert (9fGwNFp, fiJFbgG, keyed on event_id+rev) | yes |
| Dedupe-all by event_id | no | no |
| Ignoring revisions / voids | no | no |
| Ignoring adjustments | no | no |
| Recomputing all history instead of adjustments | no | 9fGwNFp v1, as a path bug (not a design choice) |
| Current rate card for old usage | no | no |
| Hard-coded close dates / rate periods | no | debug scripts only (fiJFbgG used a wrong `2026-10-03` close in a script) |
| Output-only patch / source-data modification | no | no |
| Northwind-only fix | no (general code), but validation was Northwind-only | — |
| Matching a target dollar amount | no | no |

Latent issue not exercised by the verifier: Yav3hqK's ledger loader sums every `statement_*.csv`, including statements
for month S or later. Re-running an already issued month would net to zero. No fixture contains an issued statement for
S, so this is a small verifier coverage gap.

## 8. Root cause, invariant, repair

| | 9fGwNFp | Yav3hqK | fiJFbgG |
|---|---|---|---|
| Root cause identified | yes (step 14, +0:25) | yes (step 8, +0:19) | yes (step 10, +0:18) |
| Full invariant recovered | yes | yes (billed-incl-adjustments not examined) | yes |
| Repair complete | yes | yes | yes |
| Dominant failure category | none | none | none |
| Closest point to failure | step 44 plan to take highest rev inside `normalize` (would admit post-close revisions); ledger path bug | never reproduced the issued August statement; unfiltered ledger loader | float-parsed ledger with aggregate-identical output; hard-coded wrong close in a debug script |
| Hidden fixture exposed overfitting | no | no | no |

## 9. Interpretation

Agent-side:

1. **Root cause** was hypothesised in 18–25 seconds, and the full rule set was in place by 1:49–2:46.
2. **The designed conflicts were never encountered.** No agent opened the tie-out, the ADR, the console export or the
   incident note, and only one read the contract. The authority hierarchy the task was built around was irrelevant to
   passing.
3. **The repair was largely assembled from existing pieces:**
   - vendor doc sentences (highest rev; identical redeliveries; half-open windows);
   - the data catalog (mart "as currently known"; `service_month` bills that month; `usage` / `adjustment` line types);
   - the instruction ("issued statements are final");
   - **existing code:** `statement_close()`, the `received_at < closes` filter, `usage_charge()`,
     `terms_for(..., month)`, and `export.py` already summing adjustment amounts.
4. **The one rule that had to be derived fell out of the default design.** Adjustment amount = charge of known quantity
   under the service month's card minus everything billed is what a straightforward pandas "group, merge, subtract"
   produces. That design automatically includes prior adjustments and the service-month card.
5. **None of the planted traps was approached:** keep-last-receipt, `<=`, adjust-vs-usage-lines-only, extract knowledge
   for adjustments, statement-month rates, linear rerating. They are traps for alternative designs the model never
   considered.

Benchmark-side:

1. **Scaffolding in the faulty code.** The close boundary and calendar helper were inherited, contradicting design §23.7's
   "no helper-code transcription path" intent. `export.py`'s adjustment summation is a further hint.
2. **Unused attractors.** The tie-out notebook, ADR and console export never influenced behaviour. The attractor only
   works if an agent validates against it.
3. **Unused backtest key.** Batch-era history, accepted as a backtest key, was not used, so it did not reduce headroom
   here. Headroom was already absent.
4. **Hidden fixtures did not discriminate** between careful and shallow agents. Every hidden-fixture trap targets a
   design none of the agents chose.

## 10. Difficulty verdict

**TOO EASY.**
- Reward: 3/3 in 3–6 minutes at $0.21–0.41 per trial.
- Trajectory quality: correct semantics reached quickly, with thin evidence use and Northwind-only validation.
- The hardest distinction the task was meant to test (close knowledge vs current knowledge, boundary placement) was
  inherited from the faulty code rather than inferred.

The task is valid, not broken: no benchmark flaw caused a false pass, and the verifier correctly rejects every
pre-registered wrong design. But it does not probe the intended capability.

At most it could serve as an easy anchor for "event-time vs receipt-time billing with revisions". Its distance from
Task 03/05-level ease is small.

## 11. Comparison with Task 02

| Dimension | Task 02 (0/3) | Task 06 (3/3) |
|---|---|---|
| Time to root-cause discovery | 20–81 s (leak identified quickly) | 18–25 s |
| Semantic rules required | about 9–10 exact details across 11 CRM/health features | about 12 on paper, but about 5 were inherited from code or transcribed from docs; about 1 had to be derived (adjustment amount), and it is the default design |
| Investigation breadth | moderate; key incident/sync-log evidence unread | narrow; tie-out, ADR, console, incident note unread by all; contract read by 1/3 |
| Components repaired | 2–3 feature builders plus per-example state | 3 (normalize, mart, statement) |
| Grain/state reconstruction | per example × prediction cutoff × field, as-of joins; all 3 agents failed the grain | one cutoff per statement plus highest rev per event; natural groupby grain |
| Raw data use | little example-level checking | all 3 looked at raw deliveries and revisions |
| Documentation usefulness | necessary but not sufficient (availability semantics had to be inferred) | nearly sufficient when combined with existing code |
| Aggregate-only validation | 3/3 (AUC) | 0/3 aggregate-only, but single-account validation |
| Distance of failures from correct | each failure 1–2 grouping keys away | no conceptual near-misses; only implementation bugs, fixed |

**Was Task 06 genuinely harder than Tasks 03/05?** Marginally.

- Evidence of more work:
  - roughly 1.5–2× the steps (54–116 vs 38–76);
  - 2–3× the cost ($0.21–0.41 vs $0.08–0.19);
  - more raw-data inspection;
  - two trials hit and fixed real bugs.
- Evidence the capability level was not higher: the outcome (3/3), the speed of discovery and the transcriptive
  character are the same as Tasks 03/05.

**Was it as hard as Task 02?** No, for four reasons:

- **Structure.** The repair decomposes along a natural groupby structure (event → month → statement) instead of per-example
  point-in-time state.
- **Inherited cutoff.** The close cutoff, which is the element closest to Task 02's difficulty, was already in the code.
- **Default design.** The adjustment rule is what a straightforward merge-and-subtract implementation produces.
- **Dormant traps.** None of the designed traps is triggered by a naive-but-correct design. Task 02's trap (wrong state
  grain) is the natural naive implementation.

## 12. Final-benchmark quality

**Not likely to be final-benchmark quality as a headroom task.**

- Its validation and review quality are good: 29/29 mutations, harbor check 11/11, sandbox verified.
- It could be kept as an easy anchor, but Tasks 01/04 already fill that role.
- Lessons for generation 2 (no changes made to Task 06):
  - Do not leave the target cutoff or calendar helpers in faulty code.
  - Traps must lie on the *natural* implementation path, not on alternative designs. Task 02's lesson again.
  - Attractors only work if reaching the answer requires engaging with them.
