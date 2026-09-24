# P31 implementation specification — defer or overturn (fill-rate dispute)

Authoritative source: `HANDOFF_2026-09-23.md` §16 (P31 A–Z), plus §9/§10 DP3 and §25. P31's A–Z entry is
complete on mechanism but does **not** specify a deferral outcome; §6 of the implementation brief requires the
grading to distinguish justified deferral from justified acceptance. That extension is designed here and is
recorded as a deviation.

## 1. The professional incident

Meridian Retail Group's demand-science team publishes a weekly service-level report. For the ambient-grocery
category it reports **97.1 %** fill rate. The commercial director escalates that this is "obviously wrong":
three key accounts have logged shortfall tickets, and the supplier's own report shows **92 %**. He wants the
metric rebuilt and the reporting team's bonus gate reviewed.

## 2. The consequential decision

Three linked decisions, all with written rules:
* the **bonus gate** pays on the contractual fill rate exceeding 96.0 %;
* the **supplier claim** of £1.8 m is payable only if fill measured on the contractual definition breaches
  the agreement's 95.0 % floor;
* whether to **rebuild** the reporting pipeline.

## 3. Initially plausible explanations (5)

1. the report is wrong;
2. **the report is right and the supplier's number answers a different question** (different fill definition
   and different denominator);
3. both are right and the three accounts are a genuine tail the aggregate hides;
4. the shortfall tickets double-count partial deliveries;
5. a returns/rejection issue is being counted as a shortfall.

2, 3 and 5 are all partly true in the visible extract. That is the point: the incumbent aggregate is correct,
the complaint identifies a real tail, and the supplier's figure measures something else.

## 4. The analytical object to reconstruct

> Fill rate on the **contractual** definition (line fill measured at **confirmed** quantity, excluding
> returns and customer cancellations), the **bridge** to the supplier's definition (order fill measured at
> **requested** quantity), the **account-level tail**, and an explicit verdict on whether the incumbent
> number governs.

## 5. Data-generating process (generator truth; never shipped)

Order lines carry `requested_qty`, `confirmed_qty` (≤ requested when the supplier allocated short),
`delivered_qty`, a `cancelled_by_customer` flag, and a `return_qty` with a reason code.

* **Contractual metric**: over lines that are not customer-cancelled, a line is filled iff
  `delivered_qty >= confirmed_qty`; fill = filled lines / eligible lines. Returns are excluded by contract.
* **Supplier metric**: an *order* is filled iff every line has `delivered_qty >= requested_qty`; fill =
  filled orders / total orders, and returns are netted off delivered quantity.
* The gap decomposes exactly into four named components: denominator (requested vs confirmed), aggregation
  (order vs line), returns treatment, and date-window scope (the supplier reports on despatch date, the
  contract on requested delivery date).
* Three named accounts are given materially worse allocation, so their contractual line fill is ≈ **89 %**
  while the category aggregate is ≈ **97.1 %**.
* 40 % of shortfall tickets carry return reason codes, which the contract excludes.

**Extract-varying truth — this is the control:**

| extract | incumbent code | contract ambiguity | correct verdict |
|---|---|---|---|
| visible | correct | none | `incumbent_correct` |
| hidden A | **defective** — silently drops lines whose `confirmed_qty` is NULL, which the agreement counts as unfilled | none | `incumbent_incorrect` |
| hidden B | correct | none | `incumbent_correct` (larger tail, different returns share) |
| hidden C | correct | **Schedule 4 is marked "to be agreed" for customer-amended lines, and a dated email confirms it was never agreed**; those lines are material enough to move the number across the 96.0 % gate | `not_determinable_from_available_evidence`, with a reported bound |

So blind rejection fails on visible/B/C, blind acceptance fails on A/C, and blind deferral fails on
visible/A/B.

## 6. Identifiable quantities

| quantity | tolerance | note |
|---|---|---|
| `fill_rate_contract_pct` | ±0.15 pp | exact given the definition; tolerance covers rounding choices |
| `fill_rate_supplier_definition_pct` | ±0.3 pp | reproduces the supplier's appendix method |
| `bridge_pp` (4 named components + `other`) | ±0.4 pp each | must sum to the gap within ±0.2 pp |
| `account_fill_pct` for the three named accounts | ±0.3 pp each | |
| `accounts_below_floor` | exact | count of accounts under the 95.0 % contractual floor |
| `returns_driven_ticket_share_pct` | ±2 pp | |
| `incumbent_verdict` | exact, 3-way | `incumbent_correct` / `incumbent_incorrect` / `not_determinable_from_available_evidence` |
| `governing_definition` | exact | |
| `bonus_gate_met` | exact, 3-way (`yes`/`no`/`not_determinable`) | |
| `supplier_claim_payable` | exact, 3-way | |

On hidden C the point estimate of `fill_rate_contract_pct` is **not** graded; instead a **bound**
(`fill_rate_contract_low_pct`, `fill_rate_contract_high_pct`) is graded, bracketing the two readings of
Schedule 4. Grading a point estimate there would grade an unidentifiable quantity.

## 7. The correct investigation

Recompute the incumbent number from raw order lines → recompute the supplier's number → notice they are both
reproducible → read the supply agreement and the supplier's methodology appendix → identify the four
definitional differences → bridge the gap → decompose to account level and find the real tail → reconcile the
tickets and find the returns share → audit the incumbent code against the agreement clause by clause → issue
the verdict.

## 8. The sophisticated incorrect investigation

A diligent rebuild from raw order lines that reproduces the **supplier's** 92 % and presents it as "the
corrected fill rate", because the analyst took `requested_qty` as the denominator — which is what the
complainant's evidence implies. It ties to the order ledger, it matches an external party's report, it
explains the three accounts' tickets, and it vindicates the stakeholder who raised the issue. **Every
coherence check passes and the social pressure points the same way.**

## 9. Falsification opportunities (3)

| route | competing predictions | evidence |
|---|---|---|
| the supply agreement's definition clause | "report wrong" ⇒ the contract's denominator is requested quantity; "definitional" ⇒ it is confirmed quantity | agreement §7 + the supplier appendix |
| ticket reconciliation | "real shortfall" ⇒ tickets map to short deliveries; "returns" ⇒ 40 % carry return reason codes | ticket log + returns log |
| customers' goods-receipt confirmations | an independent third system that reproduces the contractual number, not the supplier's | GRN feed |

## 10. Deliverables and verifier strategy

`out/readout.json` with the quantities above and `out/account_fill.csv`. The verifier recomputes both
definitions from the raw lines with an independent implementation, checks the bridge sums, checks the tail,
and checks the three-way verdict fields. Because the verdict differs across extracts, a constant answer
cannot pass.

**The task title and instruction are neutral.** Nothing tells the agent that this is a control, that the
incumbent may be right, or that deferral is ever correct — the vocabulary simply admits it.
