# Task 01 — Gemini 3 Flash Preview baseline (diagnosis condition)

Status: exploratory baseline, n = 3. Task frozen at commit `a6a884e` (clean tree) for the whole run.
Machine-readable per-trial table: `research/task01_trials.csv`.
Every behavioural claim below cites trajectory step ids (ATIF `step_id`; agent steps are even numbers)
from `jobs/task01-gemini3flash-diagnosis-paid/<trial>/agent/trajectory.json`.

## 1. Experiment setup

| Item | Value |
|------|-------|
| Task | `candidates/01-revenue-reconciliation` (diagnosis instruction), commit `a6a884e`, unmodified |
| Harbor | 0.21.0, docker environment, arm64 |
| Agent / model | `gemini-cli` 0.59.0 / `google/gemini-3-flash-preview` (paid tier) |
| Command | `harbor run -p candidates/01-revenue-reconciliation -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task01-gemini3flash-diagnosis-paid --artifact /workspace -y` |
| Credentials | `GEMINI_API_KEY` loaded from `~/.zshrc` inside the command; `GOOGLE_API_KEY` unset; key never printed; job logs scanned for the key: absent |
| Artifacts kept per trial | ATIF `trajectory.json`, native `gemini-cli.trajectory.jsonl`, `gemini-cli.txt` (agent stdout/stderr), `verifier/{reward.txt,ctrf.json,test-stdout.txt}`, `result.json`, final `/workspace` (collected after the agent, before the verifier) |
| Derived evidence (not committed) | `<trial>/analysis/{timeline.txt,diff.patch,changed_files.txt,integrity.json,reconcile.txt}` via `tools/analysis/` |
| Runtime / cost | 6 m 27 s wall clock for the job; 3.54 M input tokens (2.80 M cached), 52 k output; $0.67 total |

**Excluded runs (infrastructure failures, never part of statistics):**
`task01-gemini3flash-diagnosis__INVALID-api-key-rejected` (HTTP 400 `API_KEY_INVALID`),
`task01-gemini3flash-diagnosis__INVALID-free-tier-quota` (free-tier daily quota, trials cut off at 9–17 steps),
`task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped` (free-tier 5 RPM; stopped within a minute).
The paid job had 0 exceptions, 0 retries and no API errors in any agent log.

Note on reading rewards: `tests/test.sh` writes a `0` placeholder to `reward.txt` before pytest and overwrites
it with `1` on success. A live monitor that reads `reward.txt` mid-verification can see a transient 0. All rewards
below are taken from Harbor's finalized `result.json` and agree with `test-stdout.txt`.

## 2. Baseline results

| Trial | Reward | Verifier | Agent steps | Agent time | Cost |
|-------|-------:|----------|------------:|-----------:|-----:|
| T1 `dT496ZB` | **1** | 28 passed | 26 | 104 s | $0.18 |
| T2 `wkRynfY` | **1** | 28 passed | 42 | 130 s | $0.23 |
| T3 `DuhAh5u` | **0** | 20 passed, 8 failed | 47 | 169 s | $0.26 |

- **Empirical trial success rate:** 2/3 = 0.67. This is the unbiased estimator of pass@1 from n = 3
  (Wilson 95% interval ≈ 0.21–0.94); it is not a precise pass@1 measurement.
- **pass@3** (at least one of these three independent attempts passes): **1**.
  (Harbor's summary table prints "Pass@2 = 1.000"; pass@3 is also 1.)
- No reward hacking: none of the three trajectories references `/tests`, `/solution`, `/logs/verifier`,
  `reward.txt` or `test_revenue`; source-extract digests of all three final workspaces equal a pristine
  regeneration; each trial modified only `src/revrec/accounts.py`.

## 3. Per-trial analysis

### T1 `dT496ZB` — pass

**A. Evidence acquisition (order).** README, data dictionary, Finance tie-out (2) → FX announcement,
`fx.py`, `recognition.py` (4) → revenue recognition policy; `fx_rates` for July/August and
`accounting_periods` queried in SQLite (6) → `extract.py` (8) → `pipeline.toml` (10) → invoices with
`replaces_invoice_id` and a posted-and-replaced check (12–16) → **Account Identity Standard** (18) →
`accounts.py` and the migration register (20) → first 100 lines of the CRM export (22) → `grep` of legacy
account `ACC-838658` (24) → `billing_accounts` (26) → `pipeline.py` (28) → reproduce run (30) → July dashboard
figure (32) → `billing_accounts` schema (34) → `checks.py` (36) → edits (38, 40) → run (42) → July (44) →
restatement spot check (46) → `publish.py` (48) → final run (50).
Never inspected: migration-wave, price, SLA and territory announcements; `deployments.csv`; CHANGELOG;
scheduler and pipeline logs; billing revenue export CSVs; runbook. Did not recompute billing revenue from
`billing.db` (used the tie-out figures). Compared July vs August using tie-out/dashboard figures (2, 32, 44).
Localized to specific accounts by reading CRM rows for `BA-230024` (22–24); did not quantify excess per account.

**B. Hypotheses.** First substantive hypothesis: the August FX update (reasoning at 2 and 4). Falsified at 6
(announcement says ~1–2% FX move vs 8.49%; rates as expected). Then: extraction filters (tax/posted, 8–10,
consistent with policy); replaced invoices double-counted (12–16, falsified by an empty SQL result). Then moved
to attribution after reading the identity standard (18). One intermediate thought summary at 26 claimed July was
also double counted; the agent checked July at 32 and it tied. Beliefs were updated on evidence each time.

**C. Localization.** Recognized that joining revenue rows to CRM history on `billing_account_id` duplicates rows
when a billing account has both a legacy (`Migrated`, `primary`) record and a successor (`legacy` link) in effect
(26 reasoning; final message 52). No explicit cardinality query; the multiplication was inferred from the CRM rows
and the join/filter code. Understood the migration and identity semantics from the standard (26, 34) and
distinguished the symptom (duplicates) from the cause (attribution should start from billing ownership and follow
lineage, not CRM link history).

**D. Repair.** Rewrote `attribute_accounts` (38) and removed the unused history helper (40): owner from
`billing_accounts.crm_account_id` → effective migrations (`cutover_in_progress`/`completed`) followed to the end
with a cycle guard → attributes from current CRM records (de-duplicated by `account_id`, a reference table, not
revenue rows). **Causal repair.** No dedupe of monetary rows, no filters, no hard-coded ids/months, no source edits;
chains handled; scheduled migrations excluded.

**E. Validation (agent's own).** Re-ran the pipeline (42, 50); August total equals the billing figure (42); July
still ties (44); historical restatement spot check for one billing account (46); reviewed rounding in
`publish.py` (48). Not done: segment or account-level reconciliation beyond one spot check, non-migrated accounts,
explicit duplicate-key check (the run log showed 6,187 fct rows but the agent did not comment on it), idempotence
comparison, generalization tests.

### T2 `wkRynfY` — pass

**A. Evidence acquisition (order).** README, docs listing, tie-out (2) → announcements listing, FX update,
**SLA incident**, revenue policy (4) → data dictionary, `recognition.py`, `extract.py` (6) → `pipeline.toml` (8) →
credit-note queries: sample, SLA count, SLA credits inside the extract query, August SLA credit sum (10–14) →
pipeline log (16) → **migration wave announcement** (18) → `accounts.py` (20) → `grep legacy` in the CRM export (22) →
CRM rows for `BA-230024` (24) → July and August warehouse attribution for that customer (26–28) → fct rows for
`BA-230024` in August showing each invoice line twice under two account names (30) → **identity standard** (32) →
`billing_accounts` schema (34) → full migration register (36) → chain accounts `ACC-637177`/`ACC-961118` (38–40) →
August revenue of migrated accounts (42) → **total double-counted amount = 489,967.91** (44) → `pipeline.py` (46),
`fx.py` (48) → current-record duplication check in the CRM export (50–52) → edit (54) → run (56) → validation
(58–80). Never inspected: deployments, CHANGELOG, price or realignment announcements, billing export CSVs.
Did not recompute billing revenue from `billing.db`.

**B. Hypotheses.** First substantive hypothesis: credit notes / SLA credits (8–14). The agent observed that
including credits should lower, not raise, revenue (14 reasoning) and moved on. The migration announcement (18)
came before opening `accounts.py` (20). No distractor caused premature convergence.

**C. Localization.** Strongest of the three: showed identical `source_id`s duplicated under legacy and successor
names (30) and quantified the duplicated revenue exactly equal to Finance's variance (44). Checked a migration chain
explicitly (38–40). Read the identity standard (32) before designing the repair. Symptom and root cause were
distinguished (final message).

**D. Repair.** Replaced `attribute_accounts` (54): billing owner → effective migration chain (fixed-point
iteration) → current CRM attributes; merges on a one-row-per-billing-account mapping. **Causal repair.** No
dedupe of revenue rows, filters, hard-coding or source edits.

**E. Validation (agent's own).** July and August totals (58); **zero duplicated (source_id, revenue_month) keys**
after the fix (60); a migrated customer's August revenue and July restatement (62–64); no null accounts or
attributes (66–68); August credit notes and FX rates (72–76); dashboard extract (78). Not done: other months
individually, segment reconciliation, non-migrated accounts, idempotence, generalization.

### T3 `DuhAh5u` — fail

**A. Evidence acquisition (order).** README, tie-out, billing export and dashboard CSVs (2; several reads failed
because of a wrong `workspace/` path prefix, corrected at 6–8) → data dictionary (8) → reproduce run (10) →
`recognition.py`, `pipeline.py`, **`accounts.py`**, `fx.py` (12–18) → head of migration register (20) → CRM rows
for `BA-230003` (22) → August invoice-line sums for that billing account (24–26) → CRM rows for completed-migration
and consolidation accounts (28–34) → primary-link counts (34) → `extract.py` (36) → legacy-link count = 8 (38) →
further CRM rows (40–50) → edit v1 (52) → run (54) → monthly totals (56) → row-level diff of schedule vs attributed
(58–66) → CRM and invoice line for the dropped row (68–76) → edit v2 (78) → run and validation (80–92).
**Never opened** the Account Identity Standard, the revenue recognition policy, any announcement, deployments,
CHANGELOG or logs. At 84 the reasoning states it is "drilling down into the documentation in `/workspace/docs`";
no documentation read follows.

**B. Hypotheses.** No distractors were investigated. The first substantive hypothesis was an edge case in the
`attribute_accounts` validity filter (18). It was confirmed as double counting when a billing account matches a
`primary` link on the legacy `Migrated` record and a `legacy` link on the successor (40–44). The reasoning at 40
connects the gap to "21" rows (6,208 fct vs 6,187 schedule rows in the run output at 10).

**C. Localization.** Found the multiplication mechanism (**symptom and join-level cause found**). Did not identify
the semantic root cause (attribution must come from billing ownership plus register lineage, and history must be
restated). It treated the CRM point-in-time record as the intended semantics; at 78 it concluded "a single level of
lookup is sufficient".

**D. Repair.** v1 (52): keep only `primary` CRM links. That dropped a revenue row on `BA-230283` (staged migration
whose legacy record closed 2026-08-28), so August came out $128,259.48 below billing (56). The agent traced the
missing row (58–68). v2 (78) kept the as-of CRM join and single-hop successor mapping and added
`sort_values("billing_link_type")` + `drop_duplicates(subset=["source_type","source_id","revenue_month"])`.
This is the pre-registered mutation `dedupe_prefer_primary_single_hop` (see `report/task01_validation.md`).
**Symptom patch.** No hard-coded ids or months, no source edits, company totals tie on the visible data; history is
not restated and chains resolve one hop only. The final message (94) says attribution follows "the established
finance policy", a document it never opened.

**E. Validation (agent's own).** Monthly totals for all 12 periods (56, 82), including July; located and fixed a
regression it introduced (56–78) using a row-level diff; August currency totals (84), dashboard extract (86),
August segment totals (88), monthly report (90). Not done: any account-level check after the fix, any check against
the documented standards, idempotence, generalization.

**F. Classification.** Dominant **F5 — symptom patch instead of causal repair** (sort + drop_duplicates on the
revenue key while keeping the non-canonical attribution). Secondary **F0** (never read the identity standard or
policy that the instruction points to) and **F7** (validated only company, segment and currency totals). A defensible
alternative dominant label is F0, since not reading the standard is the earliest irrecoverable step. F5 is chosen
because the implemented change is the dedupe pattern the taxonomy defines as F5, and T3 did inspect the data and
code evidence needed to find the mechanism.

## 4. Verifier analysis

| Trial | Passed | Failed | Visible checks | Hidden checks | Integrity | Grain | Attribution | Reports / dashboard |
|-------|-------:|-------:|----------------|---------------|-----------|-------|-------------|---------------------|
| T1 | 28 | 0 | all pass | all pass | pass | pass | pass | pass |
| T2 | 28 | 0 | all pass | all pass | pass | pass | pass | pass |
| T3 | 20 | 8 | 3 fail | 5 fail | pass | visible pass; hidden_a fail | fail (visible, hidden_a, hidden_b) | account report fail; monthly, segment and dashboard pass (visible) |

T3 failed checks (assertion text from `verifier/test-stdout.txt`):

1. `test_revenue_rows_attributed_to_canonical_account` — 214 fct rows on the wrong account (e.g. `IL-02000001`
   2025-09: got `ACC-254822`, expected `ACC-588612`).
2. `test_migrated_customers_account_revenue` — 87 canonical-account month mismatches (e.g. 2025-09 `ACC-190095`:
   got 0.00, expected 131,122.96).
3. `test_account_and_segment_reports` — `rpt_account_monthly_revenue` 177 mismatches.
4. `test_hidden_snapshot_source_grain[hidden_a]` — 5 legitimate revenue rows missing (incl. credit note `CN-070011`).
5. `test_hidden_snapshot_attribution[hidden_a]` — 154 rows misattributed.
6. `test_hidden_snapshot_attribution[hidden_b]` — 73 rows misattributed.
7. `test_hidden_snapshot_reports[hidden_a]` — company totals wrong: 2025-10 got 2,316,375.98 vs 2,448,856.21;
   2025-11 got 2,388,355.61 vs 2,537,226.79.
8. `test_hidden_snapshot_reports[hidden_b]` — 55 account-month mismatches.

**The case the hidden fixtures were built for occurred.** T3's repair ties every visible monthly total, the
visible fct grain, segment report and dashboard. On `hidden_a` the same code loses revenue: a staged migration whose
legacy record closes mid-month and whose successor has no copied legacy link leaves those rows with no in-effect CRM
match, so they are dropped before dedupe. The failure is the invariant ("every billing row, attributed through
billing ownership and lineage"), not the visible incident. The visible attribution checks already reject the fix
independently (history not restated).

## 5. Model failure vs benchmark failure — T3

**Did the model fail because the task is difficult, or because the task is bad?** The evidence supports a
**genuine model failure**:

| Possible benchmark flaw | Finding |
|-------------------------|---------|
| Missing necessary information | No. Canonical attribution and restatement are specified in `docs/data/account_identity_standard.md` §2–5; the instruction requires correctness "under our finance and data standards in `/workspace/docs/` … at every level … account". T1 and T2 read that file and implemented it. |
| Contradictory documentation | None surfaced. T3 read no document that contradicts the standard; `accounts.py`'s docstring describes the existing (buggy) as-of behaviour, which the agent treated as authoritative. |
| Ambiguous business rules | The rules T3 violated (history restatement, lineage chains, never dropping billing rows) are explicit. |
| Inaccessible evidence / environment / dependency failure | No. All files readable; pipeline ran; no tool errors besides T3's own wrong path prefix, which it corrected. |
| Verifier bug / over-specificity | No. Failures are semantic (misattribution, dropped revenue). The fix matches a pre-registered invalid shortcut. |
| Correct alternative rejected | No. T3's output violates the documented standard; its hidden_a totals do not tie to billing. |
| Timeout / Harbor malfunction | No. The agent ended itself after 169 s; 0 exceptions. |

## 6. Cross-trial comparison

**Same capability boundary.** All three trials localized the multiplication mechanism quickly: T1 by step 26
(~50 s), T2 by 30 (~45 s), T3 by 40–44 (~60 s). The discriminating behaviour was whether the agent **consulted
the business-semantics documentation before designing the repair**:

| Behaviour | T1 (pass) | T2 (pass) | T3 (fail) |
|-----------|-----------|-----------|-----------|
| Read Account Identity Standard before editing | yes (18) | yes (32) | **no** |
| Read revenue recognition policy | yes (6) | yes (4) | no |
| Used billing `billing_accounts.crm_account_id` as owner | yes | yes | no |
| Repair shape | canonical mapping | canonical mapping | as-of join + dedupe |
| Investigated distractors | FX, replaced invoices | SLA credits, FX (read) | none |
| Quantitative localization | no (inspection) | yes (duplicated sum = variance) | row-count gap + row diff |
| Validated beyond totals | 1 restatement spot check | duplicate-key count, 1 restatement, nulls | no |

T3 in fact did more debugging work (47 steps, two fix iterations, a precise row diff) but anchored on the existing
code's point-in-time semantics. T1 and T2 both transcribed the standard's algorithm almost verbatim (T1's new
docstring enumerates the standard's §3 steps). The successful runs did not validate much more than T3 did. Their
advantage came from reading the specification, not from deeper validation.

## 7. What made diagnosis easy (evidence from the trajectories)

1. **Short symptom-to-code distance.** A 9-module pipeline; all three agents opened `accounts.py` within ~20–30 s of starting
   (T3 at step 16). Its docstring mentions migrated accounts and successors.
2. **Grep-able evidence.** `grep legacy` or a `grep` for one billing account in the CRM export immediately shows the
   `Migrated`/`primary` + `legacy` pair (T2 at 22–24, T1 at 24, T3 at 22). The migration register lists the affected
   legacy billing accounts, all effective in August.
3. **Distractors are cheap to falsify.** The FX announcement itself states the effect is under 1% (T1 at 6); credit
   notes reduce revenue (T2 at 14).
4. **The repair algorithm is written down.** The identity standard §3 is a step-by-step procedure; both passing
   agents implemented it directly once read.
5. **Small search space and fast feedback.** The pipeline runs in under 1 s, and totals tie or don't immediately.

## 8. Behavioural metrics

| Metric | T1 | T2 | T3 |
|--------|----|----|----|
| Inspected identity documentation | yes | yes | no |
| Inspected migration data (register + CRM) | yes | yes | yes |
| Explicit join-cardinality / duplicate-key measurement | no | yes | yes (row counts, row diff) |
| Localized duplicated monetary rows | yes (inspection) | yes (quantified) | yes |
| Found semantic root cause | yes | yes | no (mechanism only) |
| Implemented semantically correct repair | yes | yes | no |
| Adequate regression validation (history, accounts, non-migrated, idempotence) | partial | partial | no |

## 9. Research interpretation

**Assessment: TOO EASY** for the final benchmark's stated target (pass@3 < 30%). pass@3 = 1 and 2/3 trials
passed in about two minutes each. The task is nonetheless informative. The single failure is exactly the
failure mode the task was designed to detect (dedupe symptom patch that ties totals, rejected by account-level and
hidden-fixture invariants), and it separated agents by whether they read the governing semantics.

**Causal-localization hypothesis:** **DOES NOT YET TEST.** In this task, localization of the multiplication
mechanism succeeded in 3/3 trials within about a minute. The one failure happened after localization, at semantic
repair (not consulting the standard). If anything, this is weak evidence against localization being the bottleneck
*here*. But the task's localization distance is short (tiny pipeline, grep-able CRM evidence, all migrations in the
symptom month), so it is not a meaningful test of the hypothesis. Three trials are exploratory only.

## 10. Localized-condition ablation (drafted, not run)

Given 3/3 localization success, running the localized condition on Task 01 as-is has low information value (the
diagnosis condition is already near ceiling on localization). The draft below is kept for completeness. It removes
component localization only and keeps the semantics reference identical to the diagnosis condition, so a paired
comparison would isolate localization rather than disclose the repair.

> **To:** Revenue Analytics
> **From:** Finance Controllership
> **Re:** August 2026 close — recognized revenue does not tie to billing
>
> During the August close, recognized revenue for August in the executive revenue dashboard came out roughly 8–9%
> above the billing system's recognized revenue report. Billing is the source of truth; July tied out to the cent.
> Our tie-out note and the billing exports are in `/workspace/reports/finance/`.
>
> We have traced the overstatement to the **customer account attribution step** of the `revrec` pipeline
> (`src/revrec/accounts.py`): for accounts involved in the August CRM account migrations, individual recognized
> revenue rows are being matched to more than one account record and are counted more than once. Please repair the
> attribution so that every recognized revenue row keeps its billing grain (exactly one row per source document per
> month) and is attributed to the correct customer account.
>
> Requirements 1–5: identical to the diagnosis instruction (same command and outputs, correctness under
> `/workspace/docs/` standards for every period and level, must generalize to future extracts with no special-casing,
> no changes under `/workspace/data/`, validate and regenerate outputs).

## 11. Limitations

- n = 3 trials of one model on one task; success-rate interval is wide (≈ 0.21–0.94).
- Model thought summaries (`reasoning_content`) are summaries emitted by gemini-cli, not full reasoning; claims
  here rely on tool calls and outputs, with thought summaries used only where quoted.
- Evidence-touch indices match file paths and strings in tool arguments; they record what was opened, not what was
  understood. Every cited behaviour was checked against the rendered timeline.
- All trials ran concurrently from the same image; no cross-trial interaction was observed or possible.

## 12. Recommended next experiment

**A larger, pre-registered diagnosis-condition sample on the unchanged task** (e.g. 10 additional trials of the
same command, all pooled with these 3, none discarded). It costs about $2.50 and answers the question these three
trials raise but cannot settle: how often does the observed failure mode (skipping the identity standard → dedupe
patch) occur, and is success consistently determined by reading the specification? That rate decides the design
direction for a second-order incident. Running the localized ablation first would be less informative, because
localization already succeeded in every trial.
