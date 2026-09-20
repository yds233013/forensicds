# G33 design: incident, entity model, estimand, methods

Research only. Generator: `simulation.py`. Methods: `methods.py`. No task files, no model run.

## 1. Business incident

> **From:** Chief Procurement Officer, a mid-size industrial manufacturer
> **To:** Supply Analytics
>
> The supply-risk dashboard says our largest single production node takes 18% of annual spend, comfortably
> inside the board's 25% single-node limit. Group Risk has rebuilt it from the legal-entity hierarchy and
> gets 33%, which would put us in breach and trigger the dual-sourcing programme. Both teams used the same
> spend ledger. Tell me which number is right and whether we are in breach.

## 2. Latent real-world object

A **production node**: one physical place where goods are made. Disruption risk attaches to the node — if it
stops, all spend produced there stops, whatever vendor code, legal entity or parent company the purchase
order named.

## 3. Observed identifiers and relationship types

| Observed | What it is | Identity or relationship? |
|---|---|---|
| `vendor_code` | a commercial relationship in the ERP | **relationship** — many per node; distributors span nodes |
| `parent_id` | who owns the vendor code | **relationship** — changes on acquisition; two parents can share one node |
| `asn_site_code` | ship-from code on the shipment record | **closest to identity**, but not 1:1 (see §4) |
| `material_group` | what was made | evidence that separates nodes sharing a legacy code |

## 4. Temporal identity model

Three registry events break the code↔node mapping, all recoverable from the artefacts:

| Event | Meaning | How it is recoverable |
|---|---|---|
| **rename** | node keeps identity, code changes | the registry event states old→new |
| **merge** | one node had been recorded under two legacy codes | the registry event states the two codes are one node |
| **split** | one legacy code had been covering two genuinely different nodes | after the rework the two report different codes, and their material groups are disjoint, so the post-rework map carries backward |

Plus two business events: **acquisition** (parent changes, node identity does not) and **production
transfer** (a material group's production moves node on a date; shipment records name the new node from
that date, so shipment-based attribution is right and vendor-master attribution is wrong).

## 5. Estimand, downstream analysis and decision

```
window   = trailing 12 months
A_n      = spend attributable to production node n over the window
top1     = max_n A_n / Σ_n A_n          top3, HHI, and node count also graded
decision = breach  iff top1 > 0.25
```

## 6. Entity-resolution invariant

> Two spend lines belong to the same unit **iff** they were produced at the same physical node on their
> respective dates. Sharing a vendor code, a parent, or a legacy registry code is evidence, not identity.

## 7. Ambiguity policy

8% of lines (22% in one regime) carry no shipment record. These are **not** graded as exact identity.
The documented rule spreads them across that vendor's observed ship-from mix in the same period. No graded
quantity requires a convention the analyst cannot observe — this was checked and an earlier draft that
violated it (a split resolvable only by a generator-internal parity rule) was rewritten.

## 8. Valid resolution families

| | Approach | Assumption |
|---|---|---|
| **V1** | union rename+merge edges, carve splits by material group, pro-rata the unattributed | registry log complete; material groups disjoint across split pairs |
| **V2** | resolve the post-rework period first, carry the map backward | same invariant, opposite direction |
| **V3** | same resolution, drop the unattributed lines instead of spreading them | additionally: missingness unrelated to node |

## 9. Pre-registered wrong methods

| Code | Method | Violated invariant |
|---|---|---|
| W1 | raw vendor codes | grain: relationship ≠ node |
| W2 | vendor codes after the migration log | grain, with the migration correctly applied |
| W3 | parent rollup | relationship treated as identity |
| W4 | raw shipment codes, no registry history | ignores rename/merge/split |
| W5 | renames only | ignores merge and split |
| W6 | every registry event unioned, splits included | treats a split as identity |
| W7 | transitive closure over codes+vendors+parents | mega-merge |
| W8 | drop lines with no shipment record | selective omission |
| W9 | unattributed lines to the vendor's largest node | ignores the documented pro-rata rule |
| W10 | attribute through the vendor master, not shipments | ignores production transfers |
| W11 | nodes sharing a post-acquisition parent merged | acquisition treated as historical identity |

## 10. Cheap-solve panel (built before the gate, per the G31 lesson)

`C_material_group`, `C_line_counts_raw_code`, `C_code_prefix`, `C_post_rework_only`,
`C_constant_breach`, `C_constant_within`, `C_full_history_window`, plus W1/W3/W4 re-run as heuristics.
