# Task 06 validation report

Task: `candidates/06-usage-statement-close` (`forensicds/usage-statement-close-06`), generation 2 · Harbor 0.21.0 ·
Docker (arm64) · 2026-09-14. All results come from commands run **after** the independent review fixes (§7). Raw job
directories are in `jobs/` (git-ignored). **No model trials (Gemini or otherwise) have been run on this task.**

## 1. Incident reproduction (visible extract)

| Fact | Value |
|---|---|
| Deliveries / records / redelivered records | 71,461 / 71,140 / 321 |
| Events with vendor corrections / out-of-order corrections / voids | 2,311 / 272 / 194 |
| Deliveries received after the September close (2026-10-04 00:00 UTC), of which September windows | 751 / 28 |
| October windows received before the September close | 865 |
| Northwind August usage by event month (compute, API) vs allowance | 6,038.877 < 6,280; 89,533.271 < 93,110 |
| Northwind August issued statement (streaming consumer) | 6,463.944 ($618.05 overage); 95,544.756 ($460.17) |
| Issued charges Jul / Aug vs correct charges for those months | 238,616.10 vs 227,995.79; 262,868.34 vs 201,952.72 |
| Finance tie-out (statement quantity − committed collector volume), Jul and Aug | 0.000 on both meters (the tie-out reconciles the faulty rule) |
| Current pipeline reproduces the issued August statement | 52/52 lines identical |
| Reference reproduces batch-era issued statements (Apr, May, Jun) | 87/87, 93/93, 92/92 lines identical |
| Correct September close | 197 lines: 52 usage ($213,823.02), 145 adjustments ($−70,277.63) |

**Aggregate plausibility of wrong repairs (September close, visible):**

| Variant | Lines | Usage amount | Adjustment amount | Total | Northwind total |
|---|---:|---:|---:|---:|---:|
| `nop` | 52 | 235,500.16 | 0.00 | 235,500.16 | 0.00 |
| `alt_correct_plain_python` | 197 | 213,823.02 | -70,277.63 | 143,545.39 | -1,078.22 |
| `event_time_only` | 52 | 214,643.73 | 0.00 | 214,643.73 | 0.00 |
| `processing_time_dedupe_fixed` | 52 | 211,426.67 | 0.00 | 211,426.67 | 0.00 |
| `latest_received_revision` | 274 | 214,052.50 | -67,999.94 | 146,052.56 | -1,088.88 |
| `no_adjustments` | 52 | 213,823.02 | 0.00 | 213,823.02 | 0.00 |
| `adjustments_at_statement_rates` | 197 | 213,823.02 | -75,898.38 | 137,924.64 | -1,164.43 |
| `adjustments_linear` | 197 | 213,823.02 | -76,405.28 | 137,417.74 | -2,292.29 |
| `adjustments_from_extract_knowledge` | 197 | 213,823.02 | -70,277.63 | 143,545.39 | -1,078.22 |
| `adjust_against_usage_lines_only` | 311 | 213,823.02 | -65,587.06 | 148,235.96 | -907.24 |
| `window_end_attribution` | 364 | 214,229.29 | -74,351.80 | 139,877.49 | -1,155.51 |
| `overfit_record_last_receipt` | 197 | 213,823.02 | -70,277.63 | 143,545.39 | -1,078.22 |

Several wrong repairs look plausible on the headline, and three are identical to the correct close on the visible
extract. They are caught only by hidden fixtures (§4).

## 2. Hidden extracts

| Fixture | Statement | Deliveries | Issued history | Lines (usage / adjustment) | Targets |
|---|---|---:|---|---|---|
| hidden_a | 2026-02 | 40,601 | batch Oct–Nov, streaming Dec–Jan | 41 / 116 | mid-month us-east outage with longer resend window; 40% out-of-order corrections; voids; retries; rate change Jan |
| hidden_b | 2026-11 | 53,162 | batch, streaming, streaming, batch (adjusting), streaming | 45 / 119 | billed incl. earlier adjustments; corrections 30–70 days late; allowance amendments; outage across a month end |
| hidden_c | 2027-01 | about 82,000 | batch Sep–Oct, streaming Nov–Dec | 75 / 303 | year boundary; third meter; adjustment-only customer; outage ending exactly at the close (records at the close, resends after it); extract 10 days after close |

## 3. Harbor runs

| Run | Command | Reward | Verifier |
|-----|---------|-------:|----------|
| Oracle | `harbor run -p candidates/06-usage-statement-close -a oracle -o jobs --job-name task06-oracle-1 -y` | **1.0** | 21 passed |
| Nop | `harbor run -p candidates/06-usage-statement-close -a nop -o jobs --job-name task06-nop-1 -y` | **0.0** | 14 failed, 7 passed |

Nop passes only: sources unchanged, job succeeds, line grain, usage-line set on the visible extract, adjustment
quantity/amount (vacuous on an empty set; the adjustment-set check fails), determinism.

**Clean-checkout build.** Only git-trackable files (43) were copied and the image was built from that copy: OK. The
multi-stage build leaves no generator in the final image (`/tmp/build` absent), and `/workspace/jobs` is present.

## 4. Mutation suite (inside the task image, real sandboxed `tests/test.sh`)

Command: `python3 tools/task06/shortcuts.py --docker forensicds-task06:dev --jobs 3 --report report/task06_mutations.json`

| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |
|----------|--------------|---------:|-------:|------:|------:|-----------|
| `nop` | No change (Nop agent). | 0 | **0** | 5 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `oracle` | Reference solution (all three components). | 1 | **1** | 0 | 0 | — |
| `alt_correct_plain_python` | Independent correct close: plain-Python fold over deliveries, no pandas. | 1 | **1** | 0 | 0 | — |
| `alt_correct_sqlite` | Independent correct close: SQLite window functions for record identity, current revision and billed totals. | 1 | **1** | 0 | 0 | — |
| `event_time_only` | Bill all September usage in the extract by event month (records fixed); no close cutoff, no adjustments. | 0 | **0** | 4 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `processing_time_dedupe_fixed` | Keep receipt-window statements (the ADR design) but fix record identity: redeliveries and revisions handled. | 0 | **0** | 5 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `dedupe_all_by_event_id` | Treat every later delivery of an event id as a redelivery (keep the first received); everything else correct. | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `sum_all_deliveries` | No redelivery handling: every delivery counts; everything else correct. | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `ignore_corrections` | Replays removed, but corrections and voids ignored (first revision is kept). | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `latest_received_revision` | Current record = the revision received last (not the highest rev). | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `window_end_attribution` | Usage attributed to the month of window_end. | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `no_adjustments` | Correct September usage lines; earlier months are not adjusted. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `adjustments_at_statement_rates` | Adjustments rated with the statement month's rate card instead of the service month's. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `adjustments_linear` | Adjustments priced linearly at the service month's Tier 1 rate (ignores allowance and tiers). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `adjustments_from_extract_knowledge` | Adjustments computed from all records in the extract (ignores the close for earlier months). | 0 | **0** | 0 | 4 | hidden only: hidden_a/hidden_c |
| `adjust_against_usage_lines_only` | Billed-to-date taken from issued usage lines only (earlier adjustment lines ignored). | 0 | **0** | 4 | 4 | visible + hidden_a/hidden_b |
| `reissue_prior_months` | Rebill July and August as fresh usage lines at close knowledge instead of adjusting what was billed. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `mart_left_on_receipt_month` | Statement correct, but the usage mart still groups by receipt month. | 0 | **0** | 1 | 3 | visible + hidden_a/hidden_b/hidden_c |
| `fix_normalize_only` | Partial fix: record identity only (oracle normalize), mart and statement unchanged. | 0 | **0** | 5 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `fix_statement_only` | Partial fix: statement assembly and ledger (oracle), but the 24 h redelivery filter and receipt-month mart remain. | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `fix_normalize_and_mart_only` | Partial fix: record identity and event-month mart (oracle), statement still assembled from receipt windows. | 0 | **0** | 4 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `northwind_manual_credit` | Symptom patch: current pipeline plus hand-computed credits for Northwind's August overage. | 0 | **0** | 7 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `output_only_patch` | Run a correct close once, then leave the original job in place (outputs are regenerated by the verifier). | 0 | **0** | 5 | 9 | visible + hidden_a/hidden_b/hidden_c |
| `source_data_mutation` | Correct code, but repeated deliveries are deleted from raw/landing first. | 0 | **0** | 1 | 0 | visible only |
| `overfit_record_last_receipt` | Repeated deliveries collapsed keeping the most recent receipt (a record resent after the close drops out of it). | 0 | **0** | 0 | 2 | hidden only: hidden_c |
| `overfit_close_boundary_inclusive` | Records received exactly at the close counted in the closing statement (received_at <= close). | 0 | **0** | 0 | 2 | hidden only: hidden_c |
| `overfit_hardcoded_close_times` | Close cutoffs hard-coded for the months in this extract (other months fall back to the calendar month end). | 0 | **0** | 0 | 6 | hidden only: hidden_a/hidden_b/hidden_c |
| `overfit_hardcoded_rate_periods` | Rate cards restricted to the effective months present in this extract (2026-03, 2026-05, 2026-06, 2026-09). | 0 | **0** | 0 | 6 | hidden only: hidden_a/hidden_b/hidden_c |
| `import_verifier_reference` | Cheat: the close job computes the statement with the verifier's hidden reference if it can find it. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |

29/29 cases as expected.


**Visible-pass / hidden-fail repairs**, with the fixture that catches each:
- `adjustments_from_extract_knowledge`: hidden_a, hidden_c
- `overfit_record_last_receipt`: hidden_c only (a single detection point)
- `overfit_close_boundary_inclusive`: hidden_c only (a single detection point)
- `overfit_hardcoded_close_times`: all hidden
- `overfit_hardcoded_rate_periods`: all hidden

**Sandbox control.** `import_verifier_reference` was also run against a copy of `test.sh` with the sandbox removed: it
scored **reward 1 (21 passed)**. With the sandbox it scores 0.

## 5. harbor check

`harbor check candidates/06-usage-statement-close -c tools/task01/harbor_check_config.yaml -o jobs --job-name task06-check-1`
→ **11/11 pass**, run after the fixes.

## 6. Checks (21)

1. sources unchanged
2. job succeeds
3. usage mart
4. statement line grain + no later service months
5. usage-line set
6. usage-line quantities
7. usage-line amounts
8. adjustment-line set
9. adjustment quantities
10. adjustment amounts
11. summary (coverage, consistency with lines, reference totals, close timestamp)
12. byte-identical rerun
13–21. hidden a/b/c × (mart, lines, summary)

## 7. Independent adversarial review → changes

Reviewer: a separate agent. It built the workspace, wrote its own implementation (byte-identical to the oracle), ran
seven variants through the verifier, and probed the hidden extracts.

| Finding | Action |
|---|---|
| **Critical:** root and task `.gitignore` rule `jobs/` hid `environment/workspace/jobs/`; build from a clean checkout failed | Rule anchored to `/jobs/`; clean-checkout build verified |
| `close_at` compared as an exact string (equivalent `+00:00` form failed) | Compared as a timestamp; format documented |
| Keep-last-receipt dedupe and `<=` close boundary passed (no fixture exercised them) | hidden_c outage ends exactly at the close: Jan windows land on the close and pre-close records are resent after it. Two new overfit mutations are caught by hidden_c |
| AR queue ticket contradicted data; ISO week wrong | Tickets now reference customers whose July adjustments match; week 41 |
| Extreme money leverage (billed revenue 2.6× in two months); Northwind amendment lowered API allowance | Allowance ratio 0.60–0.95, trend 0.5%/month (correct July vs June +19%; August overbilled +30%). Amendment now raises both allowances |
| Tie-out notebook called an undefined function, was dated after issuance, and read the issued ledger | Function defined; dated before issuing; reads the statement output |
| Generator present in image layer history | Multi-stage Dockerfile |
| Hidden-month outputs left in `/workspace/out` after grading | Removed by the verifier |
| Instruction named no output paths | Paths named |
| Design §20 claim about the console export | Corrected (`research/task06_design.md` §24) |
| Batch-era statements are an exact backtest key for the rule (0 mismatches; wrong rules mismatch 2–75 lines) | **Not changed.** Accepted deliberately: rewards grain-level validation; likely reduces headroom |
| Docs nearly transcribe record identity, attribution and the close; adjustments must be derived | **Not changed.** Contract and vendor wording is realistic; recorded as a difficulty risk |
| `statements/export.py` already sums adjustment amounts (schema requires it) | **Not changed.** Mild scaffolding, recorded |
| Root agent could tamper with the base interpreter beyond the `sitecustomize` check | **Not changed.** Common Harbor limitation; trajectory greps are the backstop |

Re-validation from scratch after the fixes: clean-checkout build; local Nop 14 failed / Oracle 21 passed; mutation suite
29/29; Harbor Oracle 1.0 / Nop 0.0; harbor check 11/11.

## 8. Remaining risks

- **Transcription:**
  - Record identity, event-month attribution and the close are close to stated in the vendor spec, contract and billing
    schedule.
  - The adjustment rule is not stated as a procedure.
  - Batch history lets an agent backtest it exactly.
  - The reviewer estimated strong models might pass more than half the time.
- **Single detection points:** `overfit_record_last_receipt` and `overfit_close_boundary_inclusive` (hidden_c only).
- **Root-cause location:** an internal release again, like 01–05.
- **Close cutoff:** overlaps Task 02's load-time cutoff (one component of four).
- **Realism:** September carries $−70k of adjustments against $214k usage. This is consistent with the data, but large.
