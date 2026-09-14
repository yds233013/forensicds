# Task 07: Shared-cluster cost allocation after a platform consolidation (design)

Status: design (generation 2). Not built. No model trials.

## 1. Research question

When a shared economic quantity (cloud cost and commitment credits) must be split across many entities through
many-to-many relationships, can an agent reconstruct the latent allocation semantics correctly?

The agent has to work out:
- the allocation population
- the weighting basis
- credit eligibility
- the timing grain
- residual (rounding) treatment

The hard part is that every plausible repair preserves the grand total, so a reconciliation against the cloud invoice
cannot tell right from wrong.

## 2. Enterprise setting

Halcyon (fictional) runs three products (Insights, Pipelines, Studio) plus an internal Shared Platform cost centre on a
cloud Kubernetes estate. FinOps publishes a monthly **showback**: product × cost category (compute, memory, GPU,
storage, commitment credit). This feeds product gross margin in the monthly business review.

Inputs:
- **Cloud billing export:** daily line items per SKU and project, with credits.
- **Commitment inventory:** 1-year committed-use purchases per machine family.
- **Cluster metrics:** hourly node capacity and namespace resource requests and usage, per node pool.
- **Namespace registry:** effective-dated ownership.
- **FinOps allocation policy:** a business document, not code.

## 3. Visible symptom

- The Insights product VP escalates: Insights gross margin fell from 71% to 58% in August, while Pipelines margin rose
  4 points. Engineering says Insights' footprint did not grow.
- FinOps replies that August showback ties to the cloud invoice to the cent, "so allocation is right".
- A finance analyst's workbook "adjusts" shared namespaces 50/50, and leadership has already seen those numbers.

## 4. Ground-truth causal structure

On 2026-08-01, Platform Engineering consolidated three clusters into one. This was a data and infrastructure change,
not an allocation-code release. Three things changed:

1. Node pools are now shared across products and mix machine families: N2 (commitment-covered) and E2 (not covered).
2. Several namespaces are now co-owned, recorded in the registry as effective-dated shares. For example, `ingest-shared`
   is 70% Pipelines / 30% Insights from 08-01, and 50/50 from 08-18.
3. GPU pools moved to the shared project.

The allocation engine is unchanged since 2025. It still assumes the pre-consolidation world:
- one namespace maps to one product: it takes the registry's first owner and ignores shares and effective dates;
- a pool's cost is allocated by namespace CPU **usage**;
- the monthly commitment credit, booked at billing-account level, is spread across **all** compute cost.

Before consolidation these assumptions happened to be harmless: dedicated clusters, one family per pool, and near-equal
usage and requests.

## 5. Latent invariant

For each day and node pool:
- **Core and RAM costs.** Pool vCPU cost (core SKUs) is allocated by namespace CPU **requests** × hours. Pool RAM cost
  is allocated by memory requests × hours.
- **Idle capacity.** The unrequested share of capacity is a tenant cost, allocated in proportion to requests.
- **Commitment credits.** Credits apply only to cost of eligible machine families (from the commitment inventory),
  across all projects. Each namespace receives credit in proportion to its allocated eligible cost.
- **Products.** Namespace amounts are converted to products using the shares effective **on that day**.
- **Empty pools.** A pool-day with no requests is charged to Shared Platform.
- **Rounding.** Monthly product × category amounts are rounded to cents. The residual is distributed by largest
  remainder, with ties broken by product id, so the categories sum to the invoice exactly.

Grains: SKU line (day × project × SKU) → pool-day resource cost → namespace-day → product-day (shares) →
product-month category.

## 6. Why this is real DS work

Showback and chargeback are core FinOps analytics. Commitment amortisation, shared-cost and idle-cost policies,
many-to-many ownership, and exact-total rounding all recur in cloud cost management. Whether allocation is
requests-based or usage-based is a well-known policy choice.

Allocation errors change product P&L and investment decisions while totals remain perfect.

## 7. Evidence graph

```
VP escalation + FinOps reply (ties to invoice) + analyst workbook (50/50)
  ├─ finops/policy/allocation_policy.md: tenants pay for capacity they reserve; idle is a tenant cost; commitments
  │     benefit the workloads they cover; ownership per registry
  ├─ billing export: core vs RAM SKU lines; credit lines at billing-account level (type=COMMITTED_USE)
  ├─ commitments/inventory.csv: families covered (N2, N2D) and hourly commitment
  ├─ vendor SKU catalog excerpt: SKU → machine family, resource type
  ├─ metrics/: hourly requests and usage per namespace per pool; pool node labels show mixed families after 08-01
  ├─ registry/namespaces.csv: effective-dated shares (changes mid-month)
  ├─ platform/consolidation_rfc.md + change calendar
  └─ engine code: owner = first registry row; weights = CPU usage; credits spread over all compute
        → rebuild allocation: pool resource split, requests basis, credit eligibility, daily shares, residuals
```

## 8. Conflicting evidence and authority hierarchy

| Evidence | Says | Authority |
|---|---|---|
| Allocation policy | business rules (reservation-based, idle to tenants, credits to covered workloads) | **governs** |
| Namespace registry | ownership shares with effective dates | **governs** ownership |
| Billing export and commitment inventory | costs, credits, coverage | **governs** amounts and eligibility |
| Cluster metrics | requests and usage | measurement (authoritative for quantities) |
| Analyst workbook (50/50) | leadership-visible numbers | derived; contradicts registry |
| FinOps "ties to invoice" | total reconciliation | necessary, not sufficient |
| Engine README ("allocate by utilisation for fairness") | legacy intent | superseded by policy v3 (2025-11) |

## 9. Distractors

- **August GPU price increase.** Real, but applies only to GPU SKUs that Insights barely uses.
- **Insights traffic growth.** +6% requests, much smaller than the margin swing.
- **Storage re-tiering.** Changes storage cost for all products.
- **A new Studio batch job.** Raises usage but has low requests.

## 10. Expected investigation paths

1. Decompose the margin swing by cost category. Compute and credits drive it.
2. Compare allocation weights under requests vs usage per pool.
3. Find co-owned namespaces and mid-month share changes in the registry.
4. Find that credit lines are account-level, and that E2 and GPU cost receives credit under the current engine.
5. Rebuild at the daily pool grain.
6. Validate:
   - product totals reconcile;
   - per-pool allocations sum to pool cost;
   - credits sum to credit lines and land only on eligible cost;
   - shares applied by date.

## 11. Plausible incorrect hypotheses

- Insights genuinely got more expensive (the GPU price change).
- The workbook 50/50 fix is right.
- The metrics pipeline undercounts Insights.
- The invoice is wrong.

## 12. Plausible incorrect repairs

| Repair | Why wrong | Total preserved? |
|---|---|---|
| Apply registry shares but keep usage basis | policy is reservation-based | yes |
| Requests basis but CPU requests for RAM cost too | resource-specific basis | yes |
| Idle to Shared Platform | policy: idle is a tenant cost | yes |
| Credits spread over all compute (unchanged) | eligibility | yes |
| Credits by requested vCPU across all pools | eligibility and basis | yes |
| Month-end shares for the whole month | effective dating | yes |
| 50/50 for co-owned namespaces (workbook) | registry governs | yes |
| Round per day then sum | residual drift, off by cents | nearly |
| Scale Insights back to July margin | symptom patch | yes |

## 13. Correct repair properties

- Daily pool-level allocation by resource-specific requests, with idle included.
- Credit eligibility determined by family.
- Effective-dated shares.
- Exact-total residual rule.
- No hard-coded namespaces, products, dates or families.

## 14. Components that must change

1. `ingest/billing_export.py`: split core, RAM and credit lines. It currently merges resource types.
2. `allocation/weights.py`: requests basis per resource, including idle.
3. `allocation/credits.py`: eligibility and attribution.
4. `allocation/ownership.py`: effective-dated shares.
5. `reporting/showback.py`: residual rule.

## 15. Data and grain semantics

- SKU line: `usage_date × project × sku_id` with `cost` and `credits[]`.
- Pool-hour capacity: `pool × hour` giving vCPU and GiB.
- Namespace-hour: `pool × namespace × hour` with requests and usage.
- Registry: `namespace × product × effective_from` with share.
- Commitments: `family × region × period` with hourly commitment amount.
- Output: `product × month × category` with amount (cents), plus a `namespace × day` allocation audit table.

## 16. Hidden fixture design

| Fixture | Invariant tested | Surface changes | Overfit targeted |
|---|---|---|---|
| hidden_a | effective-dated shares; many-to-many | three co-owned namespaces with two share changes; a new product appears mid-month | month-end shares; hard-coded namespaces |
| hidden_b | credit eligibility | commitment covering a different family (C3); partially utilised commitment; GPU in a covered family | "N2-only" hard-code; spread over compute |
| hidden_c | idle and empty pools; residuals | pools with zero requests some days; many cent ties | idle to platform; naive rounding |

## 17. Mutation-suite plan

- **Controls:** Nop; Oracle; alternate SQL implementation; plain-Python implementation.
- **Shortcuts:** each §12 repair.
- **Partial fixes:** shares only; basis only; credits only.
- **Patches:** output patch; registry edit; workbook adoption.
- **Overfits:**
  - hard-coded consolidation date split
  - hard-coded eligible families
  - hard-coded shared namespace list
- **Cheat:** reference import.

## 18. Verifier plan

1. Integrity of billing export, metrics and registry.
2. Run succeeds.
3. Showback grain.
4. Product × category amounts.
5. Totals reconcile to invoice.
6. Credits only on eligible cost (namespace audit table).
7. Pool-day allocations sum to pool cost.
8. Shares applied by date (audit).
9. Residual rule.
10. Determinism.
11. Hidden a/b/c.

## 19. Alternate-valid-solution considerations

- Requests are sampled hourly. Hour-level vs day-level aggregation of requests gives the same result if the cost per
  pool-day is uniform per hour; the generator makes pool cost daily.
- Cents residual: the policy example states the convention (a fact, not code).

## 20. Leakage and answer-key audit

- The workbook numbers are wrong (50/50). Leadership numbers are pre-fix.
- No document states the pipeline algorithm; the policy states principles.
- The engine contains no unused requests-based helper.

## 21. Difficulty rationale relative to Task 02

The invariant spans four interacting allocation decisions at a daily pool grain. Totals are non-diagnostic by
construction. Several repairs each fix one decision and look like a margin recovery.

## 22. Benchmark-validity risks

- **Policy uniqueness.** Requests vs usage, and idle treatment, must be unambiguous from the policy and the history of
  pre-consolidation showbacks. Mitigation: pre-consolidation months are consistent only with a requests basis, because
  requests and usage diverge for batch namespaces even then.
- **Residual rule.** It needs an evidence source (the policy's worked example).
- **Scale.** Hourly metrics make data volume heavy; aggregate to 4-hour samples.
- **Overlap with Task 01.** Attribution across entities, but different mechanism (allocation weights, not a join
  fan-out).

## 23. Post-review revisions required before build

See `research/gen2_design_review.md` §2–3. This design is **not approved for implementation** until those revisions
are incorporated. The required changes are listed in the review's decision table.
