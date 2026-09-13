# ForensicDS candidate matrix

Status legend: **built** (Oracle 1 / Nop 0 / mutation suite passing), *planned*, *idea*.

| # | Candidate | Business symptom | Hidden root cause (class) | Where the evidence is distributed | Main distractors | Verifier strategy | Status |
|---|-----------|------------------|---------------------------|-----------------------------------|------------------|-------------------|--------|
| 01 | Enterprise revenue reconciliation | August recognized revenue ~8.5% above billing; July ties | Entity grain / canonical identity: CRM as-of enrichment becomes one-to-many after staged account migrations (row multiplication) + non-canonical history | billing.db, CRM export grain, migration register, identity standard, migration announcement, CRM tool deploy | price change, FX move, territory realignment (new CRM versions), SLA credits, recognition refactor deploy, dashboard config change | reference re-implementation; grain/amount/attribution/report invariants on visible + 3 hidden generated snapshots; 22 shortcut mutations | **built** |
| 02 | Churn cohort metric drift | Logo churn for Q3 cohort doubles after a CRM export change | Lifecycle semantics: "Churned" status reused for downgrades-to-free after a product change; metric keyed on status instead of contract end | subscription events, product changelog, metric config, lifecycle docs | seasonality, pricing test, sales comp change | cohort-level invariants on hidden event logs | *planned* |
| 03 | Marketing attribution over-credit | Paid channel ROAS jumps 40% in one region | Time-zone / event-time vs processing-time window join after a tracking SDK release shifts timestamps to UTC | event stream, SDK release notes, attribution window config | campaign launch, budget change, bot traffic | per-conversion attribution invariants; hidden streams with DST edges | *planned* |
| 04 | Inventory valuation gap | Warehouse stock value 3% below ERP | Unit-of-measure conversion: supplier switched pack size; UoM table versioned but pipeline uses latest version for history | ERP extracts, UoM versions, supplier onboarding ticket | shrinkage report, FX, cycle-count adjustments | SKU×month valuation invariants; hidden UoM histories | *idea* |
| 05 | Model performance collapse | Fraud model precision drops after retrain; offline AUC fine | Label leakage removal broke: chargeback labels now arrive with a longer lag; training window includes unlabeled recent data as negatives | label table timestamps, ops runbook, retrain config | feature drift, class-imbalance change, new merchant segment | retrain on hidden data; check label cut-off semantics, not a metric threshold | *idea* |
| 06 | Payroll cost allocation | Department cost 12% high after reorg | Many-to-many employee↔cost-centre mapping during effective-dated transfers; allocation not split by effective days | HRIS history, finance allocation policy, reorg memo | raises, bonus accrual, headcount growth | employee×month allocation invariants; hidden reorgs | *idea* |
| 07 | Usage-based billing under-count | Metered revenue 5% low vs product telemetry | Idempotency key change in event pipeline treats retried legitimate events as duplicates for one event type | event schema changelog, dedupe config, API docs | outage, customer downgrade, sampling | event-level invariants with engineered retries in hidden streams | *idea* |

## Selection criteria for the final set

1. One defensible root cause; several real, falsifiable distractors.
2. Correct repair is semantic and generalizes; plausible shortcuts provably fail.
3. Evidence is distributed across ≥ 3 artifact types (data, code, docs/config, operational history).
4. Deterministic generator + hidden snapshots; Oracle = 1, Nop = 0.
5. Target pass@3 < 30% for `gemini-3-flash-preview` in the diagnosis condition, with F8 = 0 after review.
