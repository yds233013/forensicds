# P31 — world and evidence register

World: **Meridian Retail Group**, ambient grocery category, and its supplier Brendale Ambient. Quarter ending
2026-06-30; escalation dated 2026-07-13.

## A / B / C classification

### A — information the professional already has

| artefact | contents |
|---|---|
| `docs/customer_supply_agreement.md` | Schedule 2 §7: line fill at **confirmed** quantity (§7.1–7.2); a line with **no confirmation recorded is not filled and is not excluded** (§7.2); period by **requested delivery date**, despatch not used (§7.3); customer-cancelled lines excluded and **returns are not a fill-rate event** (§7.4); the 95.0 % account floor (§7.5). **Schedule 4** records amended quantities and leaves the measurement basis for an amended line "[To be agreed]" — and is unexecuted |
| `docs/supplier_report_methodology.md` | the supplier's case fill at **requested** quantity, net of returns, windowed on **despatch** |
| `docs/table_dictionary.md` | the seven tables, including that `confirmed_qty` is null where no confirmation was recorded and that `goods_receipts` is an independent system |
| `docs/outputs/readout_contract.md` | the output specification, including the three-valued verdict and the two decision thresholds |
| `reports/commercial_escalation.md` | the escalation, the £1.8 m claim and the 96.0 % bonus gate |
| `reports/demand_science_response.md` | the reporting team's defence, and its admission that the tickets were never reconciled |
| `notes/correspondence.md` | Schedule 4 circulated 2025-11-04, chased 2026-01-19, never executed |
| `service/` | the package that produced the published figure |

### B — information they would have to investigate

| artefact | what it settles | why it is not obvious |
|---|---|---|
| `order_lines.confirmed_qty` nulls | whether the published figure is the agreement's figure | the defect is in a `COUNT` over a nullable column; the code looks right |
| `order_lines.amended_qty` volume in period | whether Schedule 4's gap is material | immaterial on three extracts, decisive on one |
| `returns` joined to `shortfall_tickets` | how many "shortfalls" the agreement excludes | the ticket log is taken at face value by everyone in the story |
| `goods_receipts` | the contractual figure from a different system | independent of the despatch records |
| per-account rates against §7.5 | the real finding the escalation is right about | the aggregate hides it |
| `despatch_date` vs `requested_delivery_date` at the period edges | the date-window component of the bridge | small but non-zero |

### C — generator and verifier only

`_conf_effective`; the allocation and under-delivery shares; the tail-account flags; `scenarios.py`; `truth()`,
`published_rate()`, `latent_check()`.

## Trap register

| # | trap | where visible | what it catches |
|---|---|---|---|
| T1 | the supplier's figure is reproducible from the order book, and reproducing it feels like "the corrected number" | `order_lines` | the socially endorsed wrong answer (mutation M01) |
| T2 | three (or five) accounts really are several points below the floor | per-account rates | dismissing the escalation entirely |
| T3 | roughly two fifths of the tickets point at a line carrying a return | `returns` × `shortfall_tickets` | taking the ticket log as a shortfall count |
| T4 | the reporting code's denominator skips lines with no confirmation | `service/metrics.py` vs §7.2 | never auditing the code against the clause |
| T5 | on one extract there are no such lines at all, so the same code is **correct** | the data | judging code in the abstract rather than on this extract |
| T6 | Schedule 4 is unexecuted and material on one extract | the agreement + correspondence | asserting a point estimate where the instrument admits two |
| T7 | on that extract the two readings straddle the account floor but agree on the bonus gate | the data | collapsing both consequences to one verdict |
| T8 | an account sits within 0.07 pp of the floor on two extracts | per-account rates | (verifier-side) grading a knife-edge count exactly |

## Legitimate ambiguity

Schedule 4's basis — **deliberate and the point of the task**. Both readings are computed; neither is preferred;
each consequence is settled only where they agree.

## Why this is a valid defer-or-overturn control

| extract | published vs contractual | Schedule 4 material? | correct verdict |
|---|---|---|---|
| visible | equal | no | `incumbent_correct` |
| hidden_a | +4.47 pp too high | no | `incumbent_incorrect` |
| hidden_b | equal | no | `incumbent_correct` |
| hidden_c | equal | **yes** | `not_determinable_from_available_evidence` |

Always overturning fails on visible, hidden_b and hidden_c. Always accepting fails on hidden_a and hidden_c.
Always deferring fails on visible, hidden_a and hidden_b. All three habits are tested as mutations (M07, M09,
M08) and all three score 0.
