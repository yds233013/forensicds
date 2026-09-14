# Task 08: Payment processor API version changes refund semantics (design)

Status: design (generation 2). Not built. No model trials.

## 1. Research question

Can an agent establish from data behaviour, vendor change evidence and downstream symptoms that an **external source
contract changed**, and repair the ingestion adapter and cached history instead of "fixing" downstream metrics?

## 2. Enterprise setting

Tessellate (fictional marketplace) settles payments through processor Parcelpay (fictional). Payments Analytics
ingests Parcelpay's daily event exports per connected merchant account into:

- a normalized payments ledger (one row per charge: captured, refunded, disputed, fees);
- the merchant refund-rate KPI (risk operations);
- features for the merchant risk model;
- the payout reconciliation report.

A cached normalized ledger (parquet or CSV snapshots by month) is rebuilt incrementally from new exports only.

## 3. Visible symptom

- **Risk Ops:** the refund-rate KPI for recently onboarded merchants tripled in July; the risk model auto-throttled 14
  merchants.
- **Finance:** payout reconciliation shows ledger net settlement below Parcelpay payout reports for those merchants.
- **Engineering:** "no ingestion code changed since April"; a fraud campaign against two merchants is under
  investigation.

## 4. Ground-truth causal structure

1. **Pinned API versions.** Parcelpay pins an API version per connected account. Accounts created or upgraded after
   2026-06-15 use version `2026-06-15`. In that version:
   - (a) `refund` event objects report `amount` as the **cumulative** refunded amount on the charge at event time, and
     the new field `amount_increment` carries the increment;
   - (b) `refund.updated` events are emitted on status transitions (pending → succeeded), re-sending the object;
   - (c) dispute fees move from `dispute.amount` netting into separate `balance_adjustment` objects.
2. **Mixed versions.** Merchants upgrade on their own dates, so the export mixes versions. Each event envelope carries
   `api_version`.
3. **Historical backfill.** On 07-08, Parcelpay re-exported June events for upgraded accounts under the new version.
   The local cache still holds June rows built from the old exports, and the incremental loader skipped re-exported
   files already marked processed.
4. **Unchanged adapter.** The local adapter still sums `refund.amount` over `refund.*` events and nets dispute amounts.
   It is correct for old-version events and wrong for new ones.
5. **Distractor.** A real fraud campaign raised refunds for two merchants in July.

## 5. Latent invariant

- **Normalization is version-aware per event.** Refunded total per charge equals:
  - old version: the sum of `refund.created` amounts;
  - new version: the sum of `amount_increment` across `refund.created`, excluding `refund.updated` re-sends, or
    equivalently the latest cumulative amount per refund id.
- Refund status follows the latest event.
- Dispute losses and fees are taken from the objects that carry them in each version.
- Refunded never exceeds captured.
- Cached history derived from superseded exports must be rebuilt from the current raw exports.
- Downstream KPI, feature and reconciliation math is unchanged.

Grains: event envelope (api_version) → object (refund id, charge id) → charge ledger row → merchant-day KPI.

## 6. Why this is real DS work

Vendor API version changes, cumulative-versus-incremental field semantics, status-update re-sends, and vendor
backfills are frequent causes of silent metric breaks in payments and fintech analytics. Proving a source-contract
change requires distribution analysis:
- per-charge refund sequences that increase monotonically;
- refunded amounts exceeding captured amounts;
- a pattern that splits cleanly by `api_version`;
- agreement with an authoritative external report (payouts).

## 7. Evidence graph

```
Risk/Finance symptoms (KPI spike for new merchants; ledger < payouts)
  ├─ raw exports: api_version in envelope; refund amounts monotone per charge; refunded > captured only for new version
  ├─ vendor/parcelpay_changelog_excerpt.md: "refund objects expose running totals; status transitions emit updates"
  │     (a summary without field-level detail)
  ├─ vendor API reference snapshot (old version pages only; stale docs)
  ├─ payouts/: Parcelpay payout reports (authoritative for money moved)
  ├─ cache/ledger_2026-06.csv vs raw re-exported June files (manifest shows re-export dates)
  ├─ loader state file: re-exported files marked processed
  └─ notes: fraud campaign; "no code changes"
        → version-aware adapter + cache rebuild + refund<=capture guard
```

## 8. Conflicting evidence and authority hierarchy

| Evidence | Authority |
|---|---|
| Raw event exports (current) | **governs** facts |
| Parcelpay payout reports | **governs** money moved; used for validation |
| Vendor changelog excerpt | supporting; incomplete |
| Stale vendor API reference | superseded for new-version accounts |
| Local cache | derived; stale for backfilled months |
| KPI dashboard and risk model scores | derived symptoms |
| Engineering "no code change" | true but irrelevant |

## 9. Distractors

- **Fraud campaign on two merchants.** Real refunds; they pass the refund ≤ capture check and match payouts.
- **July seasonality in refunds (returns season).** Small and uniform across versions.
- **FX conversion service update.** Affects non-USD presentment only; ledger stores settlement currency.

## 10. Expected investigation paths

1. Split the KPI by merchant cohort, then by `api_version`.
2. Inspect per-charge refund event sequences.
3. Reconcile ledger vs payout reports per merchant and day.
4. Read the changelog excerpt.
5. Implement version-aware parsing.
6. Detect re-exported June files and rebuild the cache.
7. Add a guard.
8. Validate against payouts per merchant.

## 11. Plausible incorrect hypotheses

- The fraud wave explains everything.
- New merchants are riskier.
- The KPI formula is wrong.
- The payout report is delayed.

## 12. Plausible incorrect repairs

| Repair | Why wrong |
|---|---|
| Cap refunded at captured | hides overcount; still wrong for partials |
| Drop `refund.updated` events only | cumulative amounts still over-summed |
| Take max amount per charge for all versions | wrong for old-version multi-refund charges |
| Switch semantics by date (≥ 06-15) instead of per event `api_version` | merchants upgrade on different dates |
| Switch by account creation date | upgraded old accounts |
| Exclude new merchants from KPI | population patch |
| Fix adapter but not cache | June wrong |
| Rescale KPI to June baseline | symptom patch |

## 13. Correct repair properties

- Per-event version dispatch.
- Idempotent refund resolution.
- Dispute and fee objects handled per version.
- Cache rebuilt for re-exported periods, determined from the manifest and data, not from hard-coded months.
- Guard added.
- Downstream code untouched.

## 14. Components that must change

1. `adapters/parcelpay/events.py`: version-aware normalization.
2. `ledger/build.py` and the cache or loader state: rebuild re-exported partitions.
3. `quality/checks.py`: refund ≤ capture guard. The existing DQ framework expects registered checks.

## 15. Data and grain semantics

- Export file: `account × export_date × version`.
- Event: `event_id` with `type`, `api_version`, `created`, `data.object`.
- Object: `charge_id` or `refund_id`.
- Ledger: `charge_id` → captured, refunded, dispute_loss, fees, net.
- KPI: `merchant × day` refund rate.
- Payouts: `merchant × payout_date` amount.

## 16. Hidden fixture design

| Fixture | Invariant tested | Surface changes | Overfit targeted |
|---|---|---|---|
| hidden_a | per-event version dispatch | merchants upgrading on different dates, including mid-charge lifecycle (refund events on both versions for one charge) | date-based or account-based switch |
| hidden_b | cache rebuild from manifest | re-export of two different months; a partially re-exported month | hard-coded June rebuild |
| hidden_c | multi-refund and partial semantics | many partial refunds; zero-decimal currency; disputes with fees | max-per-charge; cap-at-capture |

## 17. Mutation-suite plan

Nop, Oracle, alternate implementation, each §12 repair, partial fixes (adapter only; cache only), output patch, raw
mutation, date-switch overfit, June-only rebuild overfit, cheat.

## 18. Verifier plan

1. Raw and payouts integrity.
2. Run succeeds.
3. Ledger grain.
4. Ledger values per charge.
5. KPI per merchant-day.
6. Payout reconciliation within cents for all merchants.
7. Cache partitions equal a full rebuild.
8. Guard behaviour on a hidden malformed fixture, using the quarantine output documented in the DQ framework README.
9. Downstream modules byte-identical, as a behavioural check that KPI outputs equal the reference given a correct ledger.
10. Hidden a/b/c.

## 19. Alternate-valid-solution considerations

- For new-version refunds, `amount_increment` summation and latest-cumulative-per-refund are equivalent when both are
  present; the generator guarantees consistency.
- Guard: quarantine vs raise. The DQ framework README defines quarantine, so only that is graded.

## 20. Leakage and answer-key audit

- The changelog excerpt is a high-level summary. Field semantics must be confirmed in data.
- Payout reports validate totals per merchant but do not reveal per-charge ledger rows.
- No local helper for the new version exists.

## 21. Difficulty rationale relative to Task 02

Discovery requires data distribution analysis across versions. The repair spans an adapter, cache state and a guard.
Several downstream patches restore the KPI while leaving the ledger wrong.

## 22. Benchmark-validity risks

- **Vendor changelog specificity.** Too vague makes it underspecified; too specific makes it transcribable.
- **Guard grading.** Can become a hidden requirement unless the DQ framework contract is explicit.
- **Cache realism.** Loader state must be discoverable.
- **Overlap with Task 06 on "revisions."** Semantics differ: cumulative vs incremental, not supersession.

## 23. Post-review revisions required before build

See `research/gen2_design_review.md` §2–3. This design is **not approved for implementation** until those revisions
are incorporated. The required changes are listed in the review's decision table.
