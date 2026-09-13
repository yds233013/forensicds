# Task 01 validation report

Task: `candidates/01-revenue-reconciliation` · Harbor 0.21.0 · Docker (arm64) · 2026-09-12.
All results below were produced by commands actually run; raw Harbor job directories are in `jobs/`
(git-ignored).

## 1. Incident reproduction (buggy pipeline, visible snapshot)

| Month | Billing recognized revenue (USD) | Dashboard (USD) | Variance | % |
|-------|------:|------:|------:|----:|
| 2025-09 … 2026-06 | ties every month | ties | 0.00 | 0.000 |
| 2026-07 | 5,595,593.63 | 5,595,593.63 | 0.00 | 0.000 |
| 2026-08 | 5,772,385.78 | 6,262,353.69 | +489,967.91 | +8.488 |

- `fct_recognized_revenue`: 6,208 rows vs 6,187 legitimate (source × month) keys; 21 keys multiplied,
  0 missing; all multiplied keys are in 2026-08 on 7 legacy billing accounts of staged migrations
  (including the chain account). The staged migration whose cutover closed 2026-08-28 is not multiplied.
- 183 account-month figures differ from canonical attribution across all 12 periods (pre-migration
  history on legacy accounts) while company and segment totals tie.
- Tool: `python3 tools/task01/reconcile.py <workspace>`.

## 2. Harbor runs

| Run | Command | Reward | Verifier |
|-----|---------|--------|----------|
| Oracle | `harbor run -p candidates/01-revenue-reconciliation -a oracle -o jobs --job-name task01-oracle-2` | **1.0** | 28 passed |
| Nop | `harbor run -p candidates/01-revenue-reconciliation -a nop -o jobs --job-name task01-nop-2` | **0.0** | 15 failed, 13 passed |

(Earlier pre-review runs `task01-oracle-1` / `task01-nop-1` on the 27-check verifier: 1.0 / 0.0.)

Nop passes exactly the invariants a no-op should: source integrity (3), pipeline runs, non-migrated
accounts unchanged, non-revenue exclusion, idempotence, hidden pipelines run (3), and the no-migration
hidden snapshot (3).

## 3. Hidden fixtures

| Snapshot | Incident-time pipeline | Oracle |
|----------|------------------------|--------|
| `hidden_a` | Aug–Nov +4.3% … +12.7%; 29 multiplied keys (incl. triple), 5 rows dropped (successor without links, mid-month close); 105 account-month mismatches | exact (0 mismatches) |
| `hidden_b` | 2025-03 +5.1% (month-end boundary); 56 account-month mismatches | exact |
| `hidden_c` | ties (no migrations) — regression guard | exact |

## 4. Anti-gaming mutation suite (inside the task image, real `tests/test.sh`)

Command: `python3 tools/task01/shortcuts.py --docker forensicds-task01:dev --report report/task01_mutations.json`
Result: **28/28 cases scored as expected**. "Visible/hidden fails" = number of failing checks in each section.

| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |
|----------|--------------|---------:|-------:|------:|------:|-----------|
| `nop` | No changes (equivalent to Nop agent). | 0 | **0** | 9 | 6 | visible + hidden |
| `oracle` | Reference solution. | 1 | **1** | 0 | 0 | — |
| `alt_correct_crm_primary_owner` | Different correct implementation: owner from CRM primary links, lineage from CRM successor pointers | 1 | **1** | 0 | 0 | — |
| `alt_correct_sql_mapping_with_guard` | Oracle mapping plus an extra grain guard in the pipeline (defensive, still correct). | 1 | **1** | 0 | 0 | — |
| `blanket_drop_duplicates` | rows.drop_duplicates() after enrichment. | 0 | **0** | 9 | 6 | visible + hidden |
| `dedupe_source_grain_keep_first` | drop_duplicates on (source_type, source_id, revenue_month): fixes totals, not identity. | 0 | **0** | 3 | 5 | visible + hidden |
| `dedupe_by_invoice_id` | Naive invoice-level dedupe. | 0 | **0** | 10 | 8 | visible + hidden |
| `dedupe_by_line_content` | Dedupe on invoice + amount + currency (kills identical legitimate lines). | 0 | **0** | 10 | 8 | visible + hidden |
| `primary_links_only` | Keep only CRM rows whose billing_link_type is primary. | 0 | **0** | 8 | 5 | visible + hidden |
| `exclude_migrated_records` | Drop CRM record versions in Migrated status. | 0 | **0** | 3 | 5 | visible + hidden |
| `hardcoded_account_filter` | Filter the (visible) problematic billing accounts' legacy CRM rows by literal id list. | 0 | **0** | 3 | 6 | visible + hidden |
| `august_only_dedupe` | Month-specific special case. | 0 | **0** | 3 | 6 | visible + hidden |
| `hardcoded_total_scaling` | Scale August fct amounts so the total equals the billing figure (literal). | 0 | **0** | 9 | 6 | visible + hidden |
| `divide_by_constant` | Divide August by the observed overstatement ratio. | 0 | **0** | 10 | 6 | visible + hidden |
| `output_only_patch` | Correct numbers written straight into warehouse + dashboard outputs; pipeline code untouched. | 0 | **0** | 9 | 6 | visible + hidden |
| `edit_crm_export` | Delete legacy billing-link rows from the CRM export (source data edit). | 0 | **0** | 10 | 6 | visible + hidden |
| `edit_billing_db` | Delete the August revenue rows of legacy billing accounts from billing.db (source data edit). | 0 | **0** | 10 | 6 | visible + hidden |
| `delete_migrated_customers` | Drop all revenue of accounts involved in migrations. | 0 | **0** | 8 | 4 | visible + hidden |
| `dedupe_prefer_primary_single_hop` | Plausible partial fix: keep one CRM match per revenue row (primary first); history not restated. | 0 | **0** | 3 | 5 | visible + hidden |
| `canonical_via_crm_links` | Canonical = current non-migrated CRM account holding any link to the billing account. | 0 | **0** | 7 | 4 | visible + hidden |
| `asof_primary_then_register_chain` | As-of primary link for ownership, then follow the register chain: loses rows once a legacy record closes. | 0 | **0** | 7 | 2 | visible + hidden |
| `follow_scheduled_migrations` | Oracle logic but also following *scheduled* migrations (attributes to accounts that do not exist yet). | 0 | **0** | 6 | 2 | visible + hidden |
| `single_hop_canonical` | Oracle logic with a single successor hop (no chain resolution). | 0 | **0** | 3 | 2 | visible + hidden |
| `overfit_asof_canonical_grain_dedupe` | Correct canonical attribution + keep-first dedupe on the as-of join: passes visible, loses rows when a | 0 | **0** | 0 | 2 | hidden only |
| `overfit_canonical_hardcoded_ids` | Correct canonical attribution + literal list of visible legacy billing accounts to de-duplicate. | 0 | **0** | 0 | 6 | hidden only |
| `overfit_canonical_august_branch` | Correct canonical attribution + month-specific de-duplication for 2026-08. | 0 | **0** | 0 | 6 | hidden only |
| `attributes_from_owner_record` | Oracle canonical account_id, but name/segment/region from the owning (legacy) account's current CRM | 0 | **0** | 2 | 4 | visible + hidden |
| `ignore_migrations_after_close` | Oracle logic, but migrations effective after the last reportable period are not followed. | 0 | **0** | 0 | 2 | hidden only |

Observations
- Totals-only repairs (keep-first dedupe, excluding Migrated records, id filters, August branch,
  prefer-primary) already fail on visible data through account-level canonical attribution.
- Three overfit adversaries with *correct visible attribution* pass all 22 visible checks and are
  rejected only by hidden snapshots — the hidden fixtures are necessary, not decorative.
- Two semantically different correct implementations (owner from billing vs CRM primary links;
  lineage from register vs CRM successor pointers; with/without an extra grain assertion) score 1,
  so the verifier is not coupled to the oracle's code.

## 5. Determinism

Verified inside the image: extracts in `/workspace` equal a fresh regeneration; two regenerations are
byte-identical (including the SQLite file); two pipeline runs produce identical warehouse tables; host
regenerations under different `PYTHONHASHSEED` values produce identical digests.

## 6. Task-quality check

`harbor check candidates/01-revenue-reconciliation` was run and **did not complete**: the claude-code
evaluator's setup exceeded the 360 s agent-setup timeout (`jobs/task01-check-1`), and no
`ANTHROPIC_API_KEY` is configured in this environment (credentials were deliberately not sourced from the
OS keychain). To run it with a key:

```bash
ANTHROPIC_API_KEY=... harbor check candidates/01-revenue-reconciliation -c tools/task01/harbor_check_config.yaml -o jobs
```

As a substitute, a fresh-context reviewer agent applied the identical default rubric
(`harbor/cli/quality_checker/default-rubric.toml`) plus leakage/ambiguity/fairness/realism review:
**11/11 criteria PASS**. All actionable findings were fixed (see `research/task01_design.md` §12), then
Oracle, Nop and the full mutation suite were re-run (results above are post-fix).

## 7. Known residual risks

- A CRM-only canonical mapping passes (semantically equivalent on all fixtures).
- Hidden runs swap only the three configured source extracts; a pipeline that newly depends on
  Finance's report exports would behave unexpectedly on hidden snapshots.
- Documentation necessarily specifies canonical attribution; agents that read the Identity Standard
  early get substantial guidance on the *repair* (not on the location of the defect).
- Pass rate for frontier agents is unmeasured; calibration to < 30% pass@3 requires model runs.
