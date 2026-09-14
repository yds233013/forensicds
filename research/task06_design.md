# Task 06: Usage-metered statements under late, replayed and revised meter records (design)

Status: design (generation 2). Harbor task to be built at `candidates/06-usage-statement-close`. No model trials.
Numbers marked "(build)" are filled in from the generated data at implementation time.

## 1. Research question

Can an agent reconstruct **which usage belongs to which billing period and statement** when arrival order,
event chronology and record revisions diverge? The repair must combine four things:
- delivery semantics (at-least-once replays)
- record semantics (revisions and voids supersede)
- event-time attribution (half-open usage windows)
- a processing-time finalization rule (statement close)

Against immutable, previously issued statements, the agent must produce correct prior-period adjustments, rated under the
terms of the month the usage occurred in. Several partial repairs leave total billed quantity reconciled to collector volume.

The question differs from Task 02's "what was available at prediction time?". Here the question is **"which events
count for which analytical window and which statement, and what has already been billed?"**

## 2. Enterprise setting

Cobalt Data (fictional) sells a managed data platform to about 30 enterprise customers. Each customer has per-meter
monthly commitments and tiered overage rates (rate cards with effective months).

Usage flows through these systems:
- **Vendor edge collector (`meterd`):** emits usage records for fixed 4-hour UTC windows, delivered at-least-once to a
  landing zone (gzipped JSONL partitioned by receive date).
- **Metering pipeline:** normalises records, builds a usage mart (feeds the customer usage console and capacity
  dashboards), and produces monthly usage statements.
- **Billing system:** statements are exported to it and invoiced. Issued statements are immutable.

On 2026-07-06 the nightly batch loader was replaced by a streaming consumer (ADR-0012).

## 3. Visible symptom

The instruction is a note from the Corporate Controller. It carries no hint about late data:
- Northwind Logistics disputes its August invoice (support ticket attached). They were "well under commitment" in August
  according to their usage console, yet were charged overage.
- Two other customers queried July statements.
- The September statement run is on hold until billing is trusted.
- Finance's reconciliation notebook shows statement quantities tie out to collector volume every month, so the Controller
  is not sure the pipeline is wrong.
- The controller asks the team to find out what is wrong, fix the metering and statement pipeline, produce the September
  statements and a restated usage mart, and not touch raw data or issued statements.

## 4. Ground-truth causal structure

Operational events (all real, generated deterministically):

1. **Streaming cutover on 2026-07-06.** The new consumer:
   - (a) dedupes by `event_id` keeping the first-received delivery, which drops revisions and voids;
   - (b) builds the usage mart by receive date;
   - (c) builds each statement from records *received* between the previous close and this close, labelled as the
     statement month and rated at that month's terms;
   - (d) produces no prior-period adjustments.

   The July and August statements were issued by this code. The batch-era March–June statements were correct and
   included adjustment lines.
2. **EU edge collector outage, 2026-08-30 14:00 to 2026-09-02 09:00 UTC.** Buffered records are delivered on recovery,
   and the collector also replays the last 6 hours of already-delivered records (duplicates with new `delivery_id`s).
3. **Vendor reconciliation revisions.** A nightly vendor job re-emits about 3% of windows as `rev+1` with corrected
   quantities, up to about 12 days later. About 0.3% of windows are voided (a new revision with quantity 0).
4. **Ordinary edge lateness.** About 2% of windows arrive hours to days late. A few arrive after the next statement close.
5. **Rate card version 2026-09.** Tier rates increase about 8% from September service months.
6. **The September statement run is delayed to 2026-10-06.** The extract therefore contains deliveries received after
   the September close (2026-10-04 00:00 UTC). Some are late September usage and some are revisions to September windows.

Consequences under the current code:
- The August statement for Northwind contains early-September usage (received before 2026-09-04) and EU replay duplicates.
- That pushes August over commit, while event-time August usage is under commit.
- Late July usage was billed as August. July records with windows 1–3 July received before the June close were never
  billed at all.
- Total billed quantity still equals total delivered records by receive window, which is exactly Finance's tie-out.

## 5. Latent invariant

1. A usage record is identified by `event_id`.
   - Deliveries with the same `(event_id, rev)` are the same record; a replay is not new usage.
   - The highest `rev` supersedes lower ones regardless of arrival order.
   - A void is a revision with quantity 0.
2. Usage belongs to the UTC calendar month containing its window: half-open `[window_start, window_end)`, so a window
   ending at 00:00 on the 1st belongs to the previous month.
3. The statement for month S closes at 72 h after S ends. It reflects exactly the records received (first delivery)
   before close.
   - It bills S's usage rated with S's terms.
   - For every earlier service month M, it bills the difference between usage known at close and what issued statements
     have already billed for M (all issued lines for M, including earlier adjustments). The money is the difference
     between rating the known quantity and the billed amount, using M's terms, commitment and tiers.
   - Records received after close wait for the next statement.
4. The usage mart reflects current knowledge (all deliveries in the extract) by service month, not by receive date.

Grains: delivery → record (event_id, rev) → event (event_id) → customer × meter × service month → statement line
(statement month × customer × meter × line type × service month).

## 6. Why this is real DS work

Event-time versus processing-time windowing, at-least-once delivery, idempotency keys, late data with a finalization
watermark, and rerating against immutable invoices are day-to-day problems in usage-based billing, metering and
streaming analytics.

A streaming migration that silently switches to arrival-time windows while totals still reconcile is a realistic and
costly failure. Commitments and tiers make money non-linear in quantity, so moving usage between months changes what
customers owe even when totals match.

(Sources on streaming semantics, such as the Dataflow model paper by Akidau et al., VLDB 2015, are background only. Not
re-checked in this session.)

## 7. Evidence graph

```
Controller note + Northwind ticket (console: August under commit; invoice: overage)
  ├─ billing/issued/statement_2026-08.csv: Northwind August line quantity > console August total
  ├─ finance/reconciliation_2026-08.ipynb: billed quantity == collector volume by receive window (reconciles; non-diagnostic)
  ├─ docs/adr/ADR-0012-streaming-usage-consumer.md: "records are windowed by receipt to keep statements reconciled to
  │     collector offsets"; "redeliveries are dropped by event id"
  ├─ vendor/meterd/DELIVERY.md: at-least-once; idempotency key (event_id, rev); revisions supersede; voids; out-of-order
  │     delivery possible; windows are [window_start, window_end) UTC
  ├─ contracts/order_form_terms.md: usage measured per UTC calendar month in which it occurs; commitments apply to each
  │     month separately; usage reported after a statement is issued is invoiced on a later statement as an adjustment
  │     for the month in which it occurred
  ├─ ops/billing_close_runbook.md: statement close = 72 h after month end; statement run at close; issued statements
  │     are never re-issued
  ├─ billing/issued/statement_2026-04..06.csv: batch-era adjustment lines (incl. zero-amount lines; a February-rate
  │     adjustment on a post-rate-change statement) -> how adjustments were rated historically
  ├─ ops/incidents/INC-2291 (EU collector outage + replay)
  ├─ raw/landing/received_date=*/: data shows replays, revisions, voids, month-boundary windows, post-close arrivals
  └─ config/rate_cards.csv: effective-dated terms incl. the September rate change
        → repair normalize (record identity), mart (event time), statement (close + adjustments + service-month rating)
```

## 8. Conflicting evidence and authority hierarchy

| Evidence | Says | Authority |
|---|---|---|
| Contract terms (order form) | how usage is attributed and invoiced | **governs** billing semantics |
| Vendor delivery spec | what a record, revision, replay and window mean | **governs** source semantics |
| Billing close runbook | when a statement closes; issued statements immutable | **governs** process timing |
| Issued statements | what was actually billed (fact) | authoritative for *billed amounts*, not for correct usage |
| Customer usage console export (Northwind, as of 2026-09-12) | event-time usage by day, current knowledge at export time | supporting evidence; later revisions make it differ slightly from final numbers, and it is not a statement |
| Finance reconciliation notebook | billed quantity = collector volume by receive window | plausible but non-diagnostic; it validates the wrong invariant |
| ADR-0012 rationale | receipt windows "keep statements reconciled" | design intent of the faulty change; overridden by contract |
| Capacity dashboard JSON (processing-time) | smooth daily volumes | operational view; not billing |

The hierarchy is defensible: contracts and vendor contracts define semantics; operational artifacts are evidence.

## 9. Distractors

| Distractor | Why plausible | How falsified |
|---|---|---|
| September rate card increase | "charges went up" | affects September service months only; August dispute predates it |
| Northwind commitment amendment (June) | commit changed | amendment raises commit; August under commit by event time either way |
| EU outage | looks like "lost data" | nothing lost; buffered records arrive, and replays duplicate |
| Customer console lag | "console is stale" | console is event-time and current as of export; differences come from later revisions |
| Tier boundary change in rating code (release notes) | rating bug suspicion | `rate()` unchanged and correct; tests of rating against history pass |

## 10. Expected investigation paths

1. Compare Northwind console August total with the issued August line.
2. Inspect raw deliveries: event windows in September inside the August statement's receive window; duplicate
   `(event_id, rev)` pairs around the outage; higher revisions ignored.
3. Read ADR-0012 against the vendor spec and contract terms.
4. Inspect historical batch-era statements to see how adjustments were issued and rated.
5. Repair normalisation, the mart and statement generation; produce September with adjustments for June–August as needed.
6. Validate:
   - per customer × meter × service month, knowledge at close vs billed;
   - every adjustment re-derivable;
   - totals across all statements equal final rated usage for closed months;
   - no post-close records included.

## 11. Plausible incorrect hypotheses

- A rating bug in tiers or commitments.
- Northwind's commitment is misconfigured.
- The outage lost usage, so bill estimated usage.
- The console is wrong (dashboard lag).
- The rate card change on 09-01 broke August.
- Finance tie-out proves billing is right, so the dispute is a customer misunderstanding.

## 12. Plausible incorrect repairs

| Repair | Why wrong | Visible aggregate plausibility |
|---|---|---|
| Event-time only: bill all S-month usage in the extract, no adjustments | includes post-close records; never corrects July/August | September looks right to the customer console |
| Processing-time only, dedupe fixed | still misattributes months | quantities reconcile to collector |
| Dedupe all by `event_id` keeping last received | revisions delivered out of order are resolved wrongly | visible: no out-of-order revisions, so passes visible (overfit) |
| Sum all deliveries of all revisions | double counts | inflated |
| Ignore corrections (keep rev 1) | voids and revisions ignored | small differences |
| Attribute by `window_end` | last window of month shifts | tiny, month-boundary only |
| Adjustments at statement-month (September) rates | rerating rule wrong | small money differences |
| Adjustments priced linearly at overage rate | ignores commitment headroom | plausible credits |
| Adjustments vs original usage lines only (ignore issued adjustments) | double-adjusts months already adjusted | visible may pass; hidden_b catches |
| Reissue July/August instead of adjusting | violates immutability; output schema has no reissue | statement totals differ |
| Credit Northwind manually | symptom patch | dispute "resolved" |
| Drop records received during outage recovery (hard-coded window) | overfit to the incident | visible passes; hidden fixtures catch |

## 13. Correct repair properties

- Record identity and revision resolution independent of arrival order.
- Event-time attribution by window start.
- Statement built from knowledge at close (first delivery before close).
- Adjustments against all issued lines for each service month, rated with that month's terms.
- Mart from current knowledge.
- No change to raw data, issued statements or rate cards; no customer-specific or date-specific constants.
- Deterministic output.

## 14. Components that must change

1. `metering/normalize.py`: record identity (replays vs revisions, voids).
2. `metering/usage_mart.py`: service-month attribution (event time, window semantics).
3. `billing/statement.py`:
   - close cutoff for inclusion;
   - event-time grouping;
   - reading issued statements;
   - adjustment lines rated with service-month terms.

`billing/rating.py` (tiers) and `billing/terms.py` (rate cards) are correct and must not change.

A partial fix of any one component fails at least one graded output.

## 15. Data and grain semantics

| Object | Grain | Key fields |
|---|---|---|
| Delivery (JSONL line) | one per delivery | `delivery_id`, `received_at`, `collector`, `record{event_id, rev, customer_id, meter, window_start, window_end, quantity}` |
| Record | `(event_id, rev)` | first `received_at` = when known |
| Event | `event_id` | quantity of highest known rev |
| Service month | `customer_id × meter × YYYY-MM` of `window_start` | sum of event quantities |
| Rate card | `customer_id × meter × effective_month` | commit, tier1_units, tier1_rate, tier2_rate |
| Issued line | `statement_month × customer × meter × line_type × service_month` | quantity (3 dp), amount (2 dp) |
| Output mart | `customer × meter × service_month` | quantity |
| Output statement lines | as issued line | quantity, amount |
| Output summary | `customer` | usage_amount, adjustment_amount, total_amount |

Rating: `charge(terms, q) = r1·min(o, T1) + r2·max(0, o − T1)`, where `o = max(0, q − commit)`. Rounded to cents half-up.

## 16. Hidden fixture design

| Fixture | Invariant tested | Surface changes | Overfit targeted | Same distribution because |
|---|---|---|---|---|
| hidden_a (statement 2026-05; cutover 2026-03) | revision resolution by `rev` independent of arrival order | revisions delivered out of order (rev 2 before rev 1 replay); voids replayed; outage mid-month | keep-last-received dedupe; hard-coded outage window | out-of-order delivery is in the vendor spec |
| hidden_b (statement 2026-11) | billed = all issued lines incl. adjustments; very late usage | issued history mixes batch and v2 statements; a month adjusted once is corrected again; 2–3 month lateness; commitment change between months | "adjust vs original usage line"; adjustments at statement rates | adjustments exist in visible batch history |
| hidden_c (statement 2027-01, year boundary) | close cutoff and event-time windows | no outage; extract 10 days after close with many post-close arrivals; heavy S+1 usage received before close; a third meter; a customer with adjustments but no current usage | event-time-only; processing-time; calendar-year string handling | same record and contract semantics |

No hidden fixture introduces a rule absent from the visible workspace.

## 17. Mutation-suite plan

- **Controls:**
  - Nop → 0
  - Oracle → 1
  - independent correct implementation (plain-Python streaming fold, no pandas) → 1
  - SQL implementation (sqlite) → 1
- **Shortcuts (→ 0):**
  - event-time only
  - processing-time only with dedupe fixed
  - dedupe all by event_id (keep first)
  - sum all deliveries
  - ignore corrections
  - `window_end` attribution
  - adjustments at statement rates
  - linear adjustments
  - no adjustments
  - adjustments from extract knowledge (not close)
  - mart fixed only
  - normalize fixed only
  - statement fixed but mart not
  - output-only patch (edit CSVs)
  - source-data mutation (delete replays)
  - Northwind manual credit
  - reissue July/August
- **Visible overfits (→ 0 via hidden):**
  - keep-last-received revision (hidden_a)
  - adjust vs original lines only (hidden_b)
  - hard-coded outage recovery dedupe window (hidden_a/b/c)
  - hard-coded close timestamp for 2026-09 (hidden)
- **Cheat:** import verifier reference → 0 (sandbox).

## 18. Verifier plan

`tests/test.sh` uses the sandboxed pipeline pattern from Tasks 03–05. `tests/test_statement_close.py` runs these checks:

1. raw landing and issued statements unchanged (digest)
2. `make`-equivalent commands succeed
3. mart grain
4. mart quantities
5. statement line grain and types
6. usage lines (quantity, amount)
7. adjustment line set
8. adjustment quantities
9. adjustment amounts
10. summary equals lines
11. no statement line for service months ≥ S+1
12. determinism
13. hidden a/b/c × (mart; statement lines; summary)

The reference is an independent pure-Python fold over deliveries.

## 19. Alternate-valid-solution considerations

- Adjustment lines with zero quantity delta are not emitted. Lines with nonzero quantity delta and zero money delta are
  emitted (batch history shows this).
- Quantity comparison at 3 dp; amounts at cents.
- Line ordering and extra columns tolerated.
- A single adjustment line per (customer, meter, service_month); history shows aggregation per month.
- Usage lines are only emitted for quantity > 0 (history).
- Whether to include months before the landing retention window: no such months exist (world starts at retention start).

## 20. Leakage and answer-key audit

- **Console export:** covers only Northwind August as of 2026-09-12. Later revisions (build: count) make it differ from final
  August; it contains no statement or adjustment numbers.
- **Batch-era history:** shows the adjustment convention, but its months are not graded outputs.
- **Notebook:** reconciles the wrong invariant.
- No document contains the algorithm. The contract states business terms; the vendor spec states record semantics;
  the runbook states timing.
- The faulty modules contain no adjustment helper, no unused issued-statement loader, and no commented alternative.

## 21. Difficulty rationale relative to Task 02

Task 02 needed per-example point-in-time reconstruction across feature families. Task 06 needs a bitemporal combination:
- event-time attribution
- processing-time close
- record identity
- rerating against an external immutable ledger

It must be applied across three outputs. Several partial fixes produce plausible statements, and the money is non-linear
in quantity. Recognising "late data" is easy; getting all interacting rules right at the statement-line grain is not.

## 22. Benchmark-validity risks

- **Contract wording.** Too explicit makes it transcribable; too vague makes it underspecified. Mitigation: facts only,
  plus history as the operational convention; review checks uniqueness.
- **Complexity.** The number of rules may make it hard for non-semantic reasons, e.g. rounding. Mitigation: rounding is
  standard (cents half-up on each rated charge); history demonstrates it.
- **Instruction pointer.** The memo mentions the September run is late, which is realistic. The close cutoff must still
  be derived from the runbook.
- **Mart vs statement semantics** (current knowledge vs close knowledge) is a second axis. Data docs define the mart as
  what the console reads.
- **Size.** About 80k deliveries per world keeps verifier runtime reasonable.

## 23. Post-review revisions (binding for implementation)

These revisions follow `research/gen2_design_review.md`. Where they conflict with §1–22, this section wins.

1. **v2 dedupe is TTL-scoped.** The streaming consumer drops a delivery if a delivery with the same `event_id` was
   seen in the previous 24 hours (state-store TTL). The consequences are:
   - replays ~3 days after the original survive and double count;
   - revisions arriving within 24 h are dropped;
   - revisions arriving later are counted in addition to the original.

   v2 statements are built from micro-batches received in `[previous close, close)`, labelled with the statement
   month, and rated at statement-month terms. They carry no adjustments.
2. **Customer and rate changes.**
   - Northwind is an EU customer.
   - Rate-card changes: 2026-05 (history evidence) and 2026-09.
   - No February references.
   - "Commitment" is renamed **included units** (prepaid allowance); usage charge = overage tiers above the included units.
3. **Close vs issuance resolved in favour of close.**
   - The contract keys on the close.
   - The runbook states: close = 00:00 UTC on the 4th day of the following month; records received at or after close
     are handled on a later statement.
   - Batch history contains one late run: the May statement issued 06-05, which excludes records received 06-04 to
     06-05. The cutoff is therefore demonstrable from data.
4. **Batch-era statements are exactly reproducible under the reference rule.** The March–June statements are generated
   by the reference semantics at close. The raw data contains:
   - replays;
   - voids;
   - out-of-order revisions (rev 1 re-delivered after rev 2);
   - a month-boundary window (20:00–00:00 on the last day of a month);
   - a zero-money adjustment;
   - a month adjusted twice;
   - a revision received more than 30 days late.

   Visible data therefore exposes keep-last-received and adjust-vs-usage-lines-only.
5. **Data dictionary properties** (definitions, not procedures):
   - an issued line bills the month in its `service_month` column;
   - windows are aligned to 4-hour UTC boundaries and never straddle months;
   - a void is a record whose quantity is 0;
   - redeliveries of the same record revision are identical;
   - the usage mart covers every customer × meter × service month with any known record, as currently known;
   - summary rows cover every customer with any statement line.
6. **Money rule unambiguous by construction.**
   - Adjustment amount = `round_half_up(charge(M, q_known_at_close))` − Σ issued amounts for M.
   - The generator guarantees Σ issued amounts for M = `round_half_up(charge(M, Σ issued quantities for M))`, so the
     `charge(new) − charge(billed_qty)` formulation is equivalent.
   - Verifier tolerances: quantity ±0.0005; amount ±0.011 per line.
   - Lines with zero quantity and zero amount, and zero-quantity usage lines, are ignored.
7. **De-leaked prose.**
   - ADR-0012 describes "offset-aligned micro-batches assembled into the statement for the period".
   - The dedupe comment mentions redeliveries only.
   - The vendor spec says delivery is at-least-once, `rev` increments on each vendor correction, the highest `rev` is
     current, and windows are `[window_start, window_end)`.
   - It no longer says "idempotency key" or "out-of-order possible".
   - Batch statement code lived in the billing team's orchestration repo and is absent. The workspace has no git history.
8. **Tie-out notebook.** It defines "collector volume" explicitly: records committed per micro-batch, by statement
   window. The attractor is exact and inspectable.
9. **Hidden fixtures.** They vary surface and rates of documented mechanisms only.
   - Out-of-order revisions and re-adjustments exist visibly.
   - hidden_b lateness matches the revised vendor spec ("corrections typically within 12 days; later corrections occur").
   - The visible-pass / hidden-fail overfits are hard-coded outage window, hard-coded close timestamps or statement
     months, hard-coded cutover date, and hard-coded customer lists. They are measured in the mutation suite.
10. **Exact-detail count target: about 12.**
    1. record revision identity
    2. highest rev
    3. void
    4. window-start month
    5. close cutoff
    6. usage lines at statement-month terms
    7. adjustments vs all issued lines
    8. adjustments rated at service-month terms
    9. mart current knowledge
    10. post-close exclusion
    11. summary coverage
    12. statement month ≥ S+1 excluded

## 24. Implementation notes and post-build review corrections (2026-09-14)

- §20 correction: the Northwind console export (as of 2026-09-12) equals usage known at the September close for its
  August cells; no later revisions touched Northwind's August windows. It is an exact key for 2 mart cells / 2 of about
  145 adjustment lines, not for the statement.
- Batch-era statements (March–June) are reproducible exactly under the reference rule (0 line mismatches), and
  plausible wrong rules mismatch them (cutoff at `issued_at`: 2/12/2 lines; billed from usage lines only: 0/35/75). This is
  an exact backtest key for the rule on ungraded months, accepted deliberately (it rewards grain-level validation) and
  a likely source of reduced headroom.
- Money leverage reduced after review (allowance ratio 0.60–0.95, trend 0.5%/month). The Northwind amendment now raises
  both allowances. The AR queue references customers whose July adjustments match their queries.
- hidden_c's connectivity loss ends exactly at the close. Some Jan-window records land exactly at the close, and records
  sent before the close are resent after it. This makes `received_at <= close` and keep-last-receipt dedupe detectable.
- The verifier compares `close_at` as a timestamp and removes hidden-month outputs after grading. The Docker build is
  multi-stage, so the generator is not in any layer of the final image. `.gitignore` no longer hides `workspace/jobs/`.
