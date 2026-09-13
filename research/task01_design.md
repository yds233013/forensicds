# Task 01 — Enterprise Revenue Reconciliation (design)

Harbor task: `candidates/01-revenue-reconciliation` (`forensicds/revenue-reconciliation-01`).
Validation evidence: `report/task01_validation.md`.

## 1. Business scenario

A B2B SaaS company closes August 2026. Finance Controllership's tie-out shows the executive
dashboard's August recognized revenue is **$6,262,353.69** against billing's **$5,772,385.78**
(**+$489,967.91, +8.49%**). July tied to the cent ($5,595,593.63). The dashboard is held. The
Revenue Analytics team (the agent) owns the `revrec` pipeline that builds the warehouse tables
and dashboard extracts from nightly Billing and CRM extracts.

The agent gets only this symptom and the desired outcome (fix the pipeline so figures are right
for all periods and levels, generalize to future closes, don't touch source extracts, validate).

## 2. Environment (agent-visible `/workspace`)

```
README.md, CHANGELOG.md
data/billing/billing.db                  Billing extract (SQLite)            authoritative
data/crm/crm_accounts_export.csv         CRM account export                   enrichment metadata
data/crm/account_migrations.csv          Billing Ops migration register       lineage system of record
src/revrec/{cli,config,extract,recognition,fx,accounts,checks,publish,pipeline}.py
config/{pipeline,metrics,dashboard}.toml
docs/finance/{revenue_recognition_policy,month_end_close_runbook}.md
docs/data/{account_identity_standard,data_dictionary}.md
docs/announcements/  territory realignment, Growth price change, enterprise migration wave 1, FX update, SLA incident
logs/pipeline/revrec_2026-09-03T06-10-44.log   close run (row counts per stage)
logs/scheduler/revrec_runs.csv, logs/deployments.csv
reports/exec_dashboard/*.csv             current (wrong) dashboard extracts
reports/finance/billing_recognized_revenue_2026-0{7,8}.csv, close_tieout_2026-08.md
warehouse/analytics.db                   current (wrong) warehouse
```

Runtime: `python:3.12-slim-bookworm`, pandas 2.2.3 / numpy 2.1.3 pinned, `sqlite3` CLI.
The generator (`environment/build/world.py`, stdlib only, seed 73019) and the Finance artifact
script run at build time and are deleted from the image.

## 3. Schemas and grains

### Billing (authoritative)
| Table | Grain | Key columns |
|-------|-------|-------------|
| `billing_accounts` | billing account | `billing_account_id`, `crm_account_id` (owner, immutable) |
| `plans` | plan price version | `plan_code`, `plan_version` |
| `subscriptions` | subscription | `subscription_id`, `billing_account_id` |
| `invoices` | invoice | `invoice_id`, `status` posted/draft/void, `replaces_invoice_id` |
| `invoice_lines` | invoice line | `invoice_line_id`, `line_type`, `amount_minor`, service period |
| `credit_notes` | credit note | `credit_note_id`, `invoice_line_id`, `issued_date` |
| `fx_rates` | (currency, month) | `usd_per_unit` |
| `accounting_periods` | month | `status` closed/closing/open |

Visible snapshot: 352 billing accounts, 3,722 invoices (23 void, 91 draft), 7,071 lines
(287 groups of identical legitimate lines on the same invoice), 79 credit notes (34 SLA credits in August),
USD/EUR/GBP, 12 reportable months (2025-09..2026-08) plus an open September.

### CRM export — grain: (account record version × linked billing account)
SCD-2 style history: `valid_from`/`valid_to`, `is_current`, attributes, `lifecycle_status`
(Active/Churned/Migrated), `successor_account_id`, `billing_account_id`, `billing_link_type`
(`primary` | `legacy`). 472 rows / 350 accounts.

### Migration register — grain: legacy → successor relation
`cutover_mode` immediate/staged, `status` scheduled/cutover_in_progress/completed. 13 rows:
3 immediate (Feb–Apr; the March successor is migrated again in August → chain), 8 staged rows
in August (5 Enterprise transfers — one with cutover closed 2026-08-28 — a 2-way consolidation,
and the Mid-Market chain's second hop), 2 scheduled for September.

### Warehouse (outputs)
| Table | Grain |
|-------|-------|
| `fct_recognized_revenue` | (`source_type`, `source_id`, `revenue_month`) |
| `rpt_monthly_recognized_revenue` | `revenue_month` |
| `rpt_account_monthly_revenue` | (`revenue_month`, `account_id`) |
| `rpt_segment_monthly_revenue` | (`revenue_month`, `segment`) |

## 4. Hidden causal chain

1. **Code (latent since 3.1.0/3.2.0)** — `revrec/accounts.py` joins every recognition row to the
   CRM export on `billing_account_id`, keeps every record *in effect at the revenue month end*,
   and maps `successor_account_id` one hop. The export's grain is version × link, so this join is
   only one-to-one while each billing account has exactly one link row in effect at any date.
2. **Historical validity** — owner changes create non-overlapping versions (still 1:1).
   Immediate-cutover migrations (Feb–Apr) close the legacy record on the effective date, and the
   CRM tool did not yet copy billing links to successors (still 1:1).
3. **Operational change** — CRM migration tool 2.1.0 (deployed 2026-07-20, `logs/deployments.csv`)
   adds staged cutover support and copies predecessor billing links to successors as `legacy`.
4. **Business event** — Enterprise wave 1 (August) uses staged cutovers: the legacy CRM record
   stays open in `Migrated` status until sign-off, while prepaid annual terms keep recognizing on
   the legacy billing account (billing history is never moved).
5. **Mechanism** — for August, each affected legacy billing account matches two in-effect CRM
   rows (legacy `Migrated` primary link + successor `legacy` link); the chain account's billing
   account also matches two. pandas `merge` silently multiplies those rows; no exception; the DQ
   gates (non-null account, FX coverage, segments, period coverage) all pass.
6. **Symptom** — 21 source rows on 7 legacy billing accounts are doubled; August +$489,967.91.
   The account whose cutover closed on 2026-08-28 is *not* duplicated (its legacy record is no
   longer in effect at month end) — a realistic subset.
7. **Second manifestation of the same defect** — history before each migration is attributed to
   the legacy account (point-in-time CRM record), not the canonical account the Identity
   Standard requires; 183 account-month figures are wrong across all periods while company and
   segment totals still tie (which is why July "reconciled").

July and all earlier months are unaffected because no staged migration (overlapping identity
representations) existed before August — not because of any month logic.

## 5. Plausible hypotheses and distinguishing evidence

| Hypothesis | Real event in the world | Evidence that rules it out |
|------------|-------------------------|----------------------------|
| Recognition refactor bug (3.4.0 deployed 2026-08-18) | vectorized schedule | schedule_rows (6,187) equals the legitimate source key count; July unchanged on re-run; per-line allocations sum to line amounts; excess is exactly whole duplicated rows |
| FX translation | EUR +2%, GBP +1% in August | billing report uses the same rates; local-currency totals differ by the same rows; FX effect < 1% |
| Growth price increase | $45→$49 from Aug 1 | appears in billing too (both sides) |
| SLA credits | 34 credit notes in August | reduce revenue; present in both; would push dashboard *down* |
| Territory realignment | ~30% accounts get new CRM versions on Aug 1 | versions end-date the previous day; no overlap; affected rows are not on realigned accounts |
| Dashboard config change | segment tile source change | extracts come from warehouse; warehouse itself is wrong |
| Data duplication in billing | — | billing keys unique; duplicates only appear after enrichment |

Localizing evidence: `fct` has 6,208 rows vs 6,187 schedule rows (pipeline log); duplicated keys
all in 2026-08 on billing accounts listed as `legacy_billing_account_id` with
`cutover_mode = staged`; CRM export shows those billing accounts under two accounts
(`primary` on a `Migrated` record with empty `valid_to`, `legacy` on the successor); migration
announcement + CRM tool deploy explain why this started in August.

## 6. Intended repair

Replace the attribution step with a mapping that has **exactly one row per billing account**:

1. owner = `billing_accounts.crm_account_id` (system of record for ownership);
2. canonical = follow effective (`status != scheduled`) register rows legacy → successor until
   none (chains; consolidations are many-to-one; cycle guard);
3. attributes = canonical account's current CRM record;
4. join `many_to_one` (validated) and assert the row count is unchanged.

Equivalent correct variants are accepted (e.g. owner from CRM `primary` links, lineage from
current CRM successor pointers) — verified by the mutation suite's `alt_correct_*` controls.

## 7. Invalid shortcuts (all verified to score 0)

`drop_duplicates()`; dedupe on the fct key (fixes totals, not history); dedupe on invoice id or
line content (drops identical legitimate lines); primary links only (drops revenue after a legacy
record closes); excluding `Migrated` records; hard-coded account/billing-account lists; August-only
branches; scaling or dividing by a constant; writing correct outputs by hand; editing the CRM export
or billing.db; deleting migrated customers; following scheduled migrations; single-hop successor;
canonical via CRM legacy links; as-of primary + register chain; and three *overfit* adversaries
that get visible attribution right but dedupe by keep-first/hard-coded ids/August branch — these
pass every visible check and are rejected only by the hidden snapshots.

## 8. Verifier strategy

`tests/test_revenue.py` (27 checks, binary reward) never inspects source code. It:

- regenerates the pristine visible extracts from `tests/world.py` (byte-identical copy of the
  build generator) and compares logical digests with `/workspace/data` (**integrity**);
- installs pristine extracts, deletes outputs and re-runs the documented pipeline command
  **twice** (idempotence);
- compares the warehouse and dashboard extracts with `tests/reference.py`, a pure-Python,
  pandas-free implementation of the policy and identity standard: fct key set == legitimate
  source grain, per-row amount/billing account/canonical account/segment, monthly totals for every
  period (July and August named), gross vs credit split, migrated and non-migrated account-month
  revenue, segment reports, identical lines preserved, tax/void/draft/open-period exclusion;
- repeats grain, attribution and report checks on **three hidden snapshots** generated from
  `tests/scenarios.py`.

Test-only dependencies are installed into an isolated venv in `test.sh`; the agent's pipeline runs
with the image's analytics Python. Tolerances: $0.005 per fct row, $0.02 per cent-rounded aggregate.

## 9. Hidden fixtures

| Snapshot | Calendar | Novel patterns |
|----------|----------|----------------|
| `hidden_a` | 2025-01..2025-11 | staged→staged chain (3 rows per source row under the naive join from Nov), 3-way staged consolidation, staged cutover whose successor has **no** legacy links and whose legacy record closes mid-month (naive join drops rows), migration effective in the open period (history restated, no reported month changes), 3 migrated legacy accounts receiving SLA credits, look-alike account ids, a scheduled migration |
| `hidden_b` | 2024-07..2025-03 | legacy record closing on the last day of the month (boundary), 2-way immediate consolidation of monthly customers, immediate migrations with and without copied links, different price change date, look-alike id |
| `hidden_c` | 2026-01..2026-06 | no migrations at all (empty register) — regression guard for over-engineered fixes |

All snapshots use different seeds, id ranges and account sets, so no literal id, amount, month
or ratio from the visible data is valid there. Oracle matches the reference exactly on all three;
the incident-time pipeline fails `hidden_a` and `hidden_b`.

## 10. Expected failure modes (hypothesized)

- F1: blame the 3.4.0 recognition refactor or FX; edit recognition/fx code.
- F2/F3: notice duplicate fct keys but stop at "remove duplicates" (F5).
- F4: understand staged migrations but keep the as-of CRM join and dedupe by preferring primary
  links, leaving history on legacy accounts; or follow scheduled migrations; or one hop only.
- F6: content-based dedupe kills identical seat-block lines.
- F7: fix August only in validation; never compare account-level history to the standard; forget
  to regenerate outputs.

## 11. Realism risks and mitigations

| Risk | Mitigation / residual |
|------|-----------------------|
| Restating pre-migration history under the successor could be seen as a second requirement | Stated explicitly in the Identity Standard (§3–4), the migration announcement and `config/metrics.toml`; instruction requires correctness "at every level … account" per `docs/`. Documented as the same root cause (non-canonical identity resolution). Residual: agents that skip docs fail — intended. |
| The docs (announcement, data dictionary) describe staged cutovers and legacy links fairly directly | They describe CRM behaviour, not the pipeline; the agent must still connect them to `accounts.py` and to the 21 multiplied rows. Reviewed for pointers (see validation report). |
| Pipeline log shows schedule_rows ≠ fct rows | Realistic observability; requires noticing and tracing. |
| Scale is modest (7k lines) | Enough that eyeballing fails; small enough for fast, deterministic verification. |
| Recognition simplifications (credit notes fully in issue month; daily ratable) | Policy states them explicitly; identical in reference and pipeline; not the object of the task. |
| Generator artifacts (e.g. renewal on Aug 1 then migration Aug 3) | Plausible business timing; documented in announcement. |
| Agent could tamper with the analytics Python used by the verifier | Out of scope for honest agents; verifier deps isolated in a venv; reward-hacking review of passing trajectories. |
