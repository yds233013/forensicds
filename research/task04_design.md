# Task 04 — Retention metrics semantic-layer regression (design)

Harbor task: `candidates/04-retention-metrics-regression` (`forensicds/retention-metrics-regression-04`).
Validation: `report/task04_validation.md`. Status: pre-baseline; **no model trials run**.

## 1. Research question

Can an agent recover the *population semantics* of a business metric — who is in a retention cohort, and which
lifecycle state every account is in — when a metrics layer substitutes an operational proxy (CRM record existence)
for the business state (being a paying customer), and repair it consistently across numerator, denominator, lifecycle
categories and segment assignment, so that it holds on future extracts?

## 2. Enterprise setting

B2B SaaS finance. FP&A used to publish quarterly retention (NRR, GRR, logo churn, ARR bridge) from a workbook. In April
2026 Analytics Engineering moved retention into a SQL semantic layer over the billing/CRM warehouse (SQLite extract),
restating history. The layer feeds the quarterly board pack. Sales Ops creates CRM accounts for prospects long before
first contracts (outbound pre-creation since forever; an ABM target-list import since April 2025).

## 3. Visible symptom

VP FP&A memo and a CFO note: board NRR is 107.4% (Q2 2026) after 110.2% in Q1 (the first quarter published from the
layer), and the layer restates Q4 FY2025 at 109.2% against 101.1% published. Sales reports record new-logo signings, yet the ARR bridge's new ARR is small. Sales Ops
blames the 2025 price increase and a $1.15M enterprise expansion.

| Quarter | Published cohort | Published NRR | Layer 2.1 NRR (bug) | Correct NRR | Correct cohort | Bug cohort |
|---------|-----------------:|--------------:|--------------------:|------------:|---------------:|-----------:|
| 2024-Q3 | 971 | 0.991 | 1.012 | 0.994 | 978 | 1,012 |
| 2025-Q3 | 1,197 | 0.975 | 1.034 | 0.981 | 1,201 | 1,254 |
| 2025-Q4 | 1,263 | 1.011 | 1.092 | 1.024 | 1,265 | 1,329 |
| 2026-Q1 | (from the layer) | 1.102 | 1.102 | 1.028 | 1,344 | 1,423 |
| 2026-Q2 | — | — | 1.074 | 0.999 | 1,403 | 1,491 |

Quarter-end ARR totals are correct (FP&A reconciled them at sign-off) and GRR is barely affected, so the revenue data
look fine. Published figures differ slightly from a correct restatement because each quarter was published at quarter
end + 12 days, before late-signed backdated renewals reached billing (documented in the workspace README). After the
review, 3% of renewals are papered 100–240 days after the term starts, so published cohort counts also differ from a
correct restatement (by 2–7 customers) and the workbook is not an exact answer key.

## 4. Hidden root cause

`semantic/models/03_customer_quarter.sql` (2.0.0) treats an account as an existing customer when its CRM record was
created before the quarter. Pre-created prospect accounts that convert during the quarter enter the retention cohort
with zero starting ARR, and their new ARR is counted as cohort ending ARR (NRR up) and as expansion (bridge wrong); they
also dilute logo churn. Win-backs (accounts that were customers before, lapsed, and return) are never "reactivated".
Segments fall back to ending ARR for zero-start accounts. (The model's header comment originally stated the proxy as a
rule; removed after review so the faulty model is not self-labelling. CHANGELOG 2.0.0 still mentions "CRM account
data".)

## 5. Latent invariant

For every reporting quarter with start S and end E (first day of next quarter):

- cohort = accounts with ARR on S > 0 (ARR from recurring lines in effect, start inclusive, end exclusive);
- NRR, GRR, logo churn over that cohort only;
- every account with ARR on S or E in exactly one bridge category — expanded/contracted/churned/retained (cohort),
  reactivated (not a customer on S, customer on E, a customer on some earlier day), new (never a customer before S);
- segment from starting ARR for cohort accounts only.

Grain: (quarter, account). Business state comes from subscription lines, never from CRM record metadata or Sales Ops
contract categories.

## 6. Why this is real DS work

Retention/NRR definitions are a classic source of board-level metric errors: the cohort must be defined by customer
status at period start, and "new vs existing" is routinely proxied by CRM or booking fields that drift when sales
processes change (pre-created target accounts, reactivations booked as new business). Semantic-layer migrations that
restate history are a common moment for such regressions. The agent must reason about population semantics, not about
a single broken join or a wrong constant. (Industry definitions of NRR/GRR vary slightly; this task's definition is
fully specified by the workspace handbook. No external source is cited.)

## 7. Evidence graph

```
Memo/CFO note: NRR above published; restated quarters; low new ARR vs record signings
  ├─ reports/finance/retention_workbook_published.csv: cohort counts and NRR per published quarter (snapshot)
  ├─ reports/board/*.csv: layer outputs; cohort larger than published for the same quarter
  ├─ docs/finance/metrics_handbook.md: customer on D = ARR > 0; cohort = customers on S; bridge; segments
  ├─ docs/data/data_dictionary.md: crm_accounts.created_at = CRM record creation; contract_type = Sales Ops category
  ├─ CHANGELOG 2.0.0: "new logos vs existing customers from CRM account data"
  ├─ docs/ops/abm_program.md, logs/deployments.csv: ABM import (April 2025); price book; line split; big deal; reorg
  └─ data: accounts with created_at < S and ARR(S) = 0; accounts with earlier spells (win-backs)
        → rewrite customer_quarter by ARR state; check account-level classification and bridge identity
```

## 8. Distractors (real events)

| Distractor | Why plausible | How falsified |
|------------|---------------|---------------|
| 2025 price increase (+7% on renewals) | raises expansion and NRR | affects cohort ARR legitimately; does not change cohort size or explain restated 2024 quarters |
| $1.15M enterprise expansion (Feb 2026) | one deal inflates Q1 NRR | removing it moves NRR by ~2 pts; cohort count gap and 2024 restatements remain |
| Billing line split (Nov 2025) | line-grain change could double count | ARR boundary totals reconcile; split lines sum to the same ARR |
| CRM contract-type mislabels | "new_business" looks like the obvious new-logo marker | reactivations and mislabels make it wrong; handbook says ARR does not depend on categories |
| ABM program | pre-created accounts are the most visible offenders | outbound pre-creation predates ABM; win-backs are wrong independently |
| Published vs restated small differences | could look like the regression | late-signed backdated renewals (README); differences are tenths of a point, not 5–7 |

## 9. Expected investigation paths

1. Compare published vs layer cohort sizes for the same quarter → cohort membership differs, ARR totals do not.
2. Read handbook (customer on D) vs `03_customer_quarter.sql` (CRM creation) → proxy substitution.
3. Find zero-start cohort accounts; see they are prospects/ABM/outbound pre-created, and accounts with earlier spells.
4. Rewrite classification by ARR state; add the reactivation category; segment by starting ARR.
5. Validate at account level (classification counts), bridge identity, and against published figures within
   explainable tolerance — not only NRR.

## 10. Plausible incorrect repairs (all in the mutation suite)

| Repair | Why wrong |
|--------|-----------|
| Exclude ABM target-list accounts | outbound pre-creation and win-backs still wrong |
| First contract signed before S | early-signed new logos join the cohort; win-backs wrong |
| New = has a `new_business` contract starting in the quarter | CRM categories mislabeled; reactivations booked as new business |
| Fix `in_cohort` only | NRR right, bridge/movement/segments wrong |
| No reactivation category | win-backs counted as new |
| Segment by ending ARR | segment metrics wrong |
| Tenure-based cohort (any prior line) | win-backs inflate NRR |
| Renewal grace period (45 days) | handbook has no grace period; late renewals across S are reactivations |
| Drop pre-created rows | removes accounts from the bridge |
| Match published snapshot (ignore late-signed lines) | published figures are a snapshot; restatement uses today's extract |
| Ending ARR on the last day of the quarter | E is the first day of next quarter |
| Scale NRR / restore published values / edit CRM created_at | symptom patches / source edits |

## 11. Correct repair properties

Cohort and movements from ARR state at S and E; reactivation from any earlier recurring line; segment from starting
ARR; downstream models unchanged; deterministic; no dependence on `crm_accounts` fields or contract categories.

## 12. Hidden fixtures

| Fixture | Invariant tested | Surface changes | Shortcut targeted | Why same distribution |
|---------|------------------|-----------------|-------------------|------------------------|
| hidden_a (as of 2025-11-12) | reactivation and new-logo semantics | no ABM; 65% outbound pre-creation (60–400 days); 70% of churners return after 30–900 days; 35% short (1–3 month) terms | exclude-ABM, lookback windows, quarter-boundary snapshots for prior customer spells | pre-creation, win-backs and short terms exist in the visible extract at lower rates |
| hidden_b (as of 2026-02-20) | quarter-boundary state | renewals signed 30–160 days early; 45% of renewals have 3–40 day gaps; ABM from 2024 with 1–6 month leads; big deal in a different quarter | booking-date cohort, grace periods, visible quarters | early signing, renewal gaps and ABM are documented and present in visible |
| hidden_c (as of 2027-05-02) | segment and category independence | ARR scale ×2.6 (many accounts cross segment thresholds), 10 customers starting quarters at exactly 25,000.00 / 100,000.00 ARR (37 rows), 55% upsell, 25% downsell, 40% CRM contract-type mislabels, ABM 2026, price +9% | segment-by-ending-ARR, inclusive segment thresholds, CRM contract types, hard-coded quarters | same mechanisms at different rates; thresholds are stated in the handbook |

Every fixture inflates NRR under the bug (e.g. hidden_b 2025-Q4: 0.985 correct vs 1.083 bug). No hidden fixture
introduces a rule absent from the visible handbook.

## 13. Verifier

`tests/test_retention_metrics.py` (18 checks): warehouse digest; build succeeds (outputs deleted first); reporting
calendar; customer_quarter rows and boundary ARR; cohort membership; movements; segments; quarterly retention
metrics; ARR bridge + reconciliation identity; segment metrics; board CSVs equal the built tables; byte-deterministic
rebuild; hidden a/b/c × (customer_quarter semantics; all metrics). Reference: pure Python over sqlite3 rows
(`tests/reference.py`), no shared code with the workspace SQL. Money to ±$0.011, ratios to 1e-9.

## 14. Mutation strategy

`tools/task04/shortcuts.py`: Nop, oracle, alternative SQL (window CTE + segment lookup table), alternative Python
classification inside the build, 16 shortcuts (§10 plus inclusive segment thresholds and "reactivation requires a
spell ended before S"), 3 overfits (540-day reactivation lookback → hidden_a;
reactivation from quarter-boundary snapshots → hidden_a; correct logic only for visible quarters → hidden fixtures).

## 15. Risks

- Review estimate: a strong agent could finish in 20–30 minutes once it compares handbook and SQL; the expert
  estimate in task.toml was lowered to 60 minutes. Difficulty is mainly in *complete* repair (bridge, reactivation,
  segments) rather than discovery.
- Accounts billed without a CRM row would be dropped by the inner join to `crm_accounts` that the oracle keeps; no
  fixture has such accounts (CRM coverage is complete in the generator), so an inner-join implementation is not
  distinguished. Documented, not fixed.
- `reactivation_requires_ended_spell` is detected by few rows (lines ending exactly on a quarter start).

- The handbook fully defines the metric; the difficulty is noticing that the layer uses a proxy and repairing all
  downstream semantics, not guessing a definition. A careful reader of handbook vs SQL may find it quickly.
- `03_customer_quarter.sql` is the only model that joins `crm_accounts`; the bug output shows
  `reactivated_customers = 0` in every quarter. Both point at the faulty model once the handbook is read.
- The published workbook's cohort counts are close to (not equal to) the correct ones; they support diagnosis
  but cannot be matched exactly.
- SQLite float sums: the verifier tolerates cent-level differences; ratio tolerance 1e-6 (loosened after review; ratios rounded to 8 dp were rejected at 1e-9) relies on sums of values
  rounded to cents (alternative implementations using floats passed).
- Realism: CRM pre-creation of 25–65% of new logos is plausible for outbound-heavy sales teams but on the high side.

## 16. Relationship to Tasks 01–03

Task 01: entity grain of joins in revenue reconciliation. Task 02: temporal availability of features. Task 03:
statistical estimand of a model evaluation under a feedback loop. Task 04: business-state population semantics of a
KPI in a SQL semantic layer — no leakage, no model, no join fan-out; every row of revenue is correct.

## 17. Capability isolated

Metric-definition reasoning: mapping a documented business definition (customer status) to data state, detecting
proxy substitution, and preserving the definition consistently across cohort, lifecycle categories, bridge and
segments — validated at account grain rather than by headline plausibility.
