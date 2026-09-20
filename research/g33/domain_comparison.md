# G33 domain comparison

Eight domains scored before any generator was written. Research only.

| Criterion | A. B2B SaaS account | B. Payments merchant | C. Marketplace seller | D. Healthcare patient | E. Supplier / vendor | F. Advertiser | G. Household |
|---|---|---|---|---|---|---|---|
| Fragmentation realistic | strong | **strong** | strong | strong | **strong** | medium | strong |
| False merges realistic | strong | **strong** | medium | strong | **strong** | medium | **strong** |
| Migrations / history | **strong** | strong | medium | medium | **strong** | medium | weak |
| Multiple operational systems | strong | **strong** | medium | strong | **strong** | weak | medium |
| Measurable downstream consequence | strong | **strong** | medium | medium | **strong** | medium | medium |
| Defensible ground truth | medium | **strong** | medium | **weak** | **strong** | medium | weak |
| Statistical consequence of wrong resolution | strong | strong | medium | medium | **to be tested** | weak | medium |
| Invariant hides naturally | medium | strong | medium | medium | **strong** | weak | medium |
| Multiple legitimate approaches | medium | strong | medium | medium | **strong** | medium | medium |
| Shortcut resistance | **to be tested** | to be tested | weak | medium | **to be tested** | weak | weak |
| Distinct from Task 01 | **NO** | medium | medium | medium | **strong** | medium | medium |

**A (B2B SaaS account identity) was eliminated immediately**: Task 01 is a CRM account-migration
many-to-many mapping with revenue attribution downstream. Building G33 there would be Task 01 with more
edges, which the brief forbids.

**D (healthcare patient)** fails the defensible-ground-truth test and carries real-world sensitivity we have
no reason to take on. **C, F, G** have weak or absent temporal identity mechanisms.

**Selected: E, supplier / production-node identity**, with **B (payments merchant)** as the runner-up.

The reason for E over B: it offers the cleanest *relationship-vs-identity* pair. Two vendor codes under one
parent are a **relationship**, not a shared production node; one production node serving vendor codes under
two different parents (contract manufacturing) is **identity across a relationship boundary**. That pairing
defeats parent rollup in both directions at once, which no other domain does as naturally.

## Intended distinction from Task 01

| | Task 01 | G33 as designed |
|---|---|---|
| The entity | customer account; a business identity rule exists and is documented | production node; must be assembled from shipment records, a registry-change log and a vendor migration log |
| The defect | a migration made a documented mapping many-to-many; repair it | the recorded identifier is not the entity at any point in time, and several grains are computable |
| Downstream | revenue attribution and restatement | supply-node concentration against a board limit |
| Core question | "which rows belong to which account" | "what counts as one entity for *this* question" |

**Whether that distinction survives the design is tested in `simulation_results.md`. It did not.**
