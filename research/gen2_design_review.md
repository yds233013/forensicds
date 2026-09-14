# Generation-2 adversarial design review (Tasks 06–09)

Date: 2026-09-14. The review combines an independent agent review with my own pre-review notes. The reviewer read the
four designs plus the gen-1 lessons and did not have the authoring context. All designs were revised afterwards
(each design doc now has a §23 "Post-review revisions" section). Only Task 06 proceeds to implementation.

## 1. Comparison across designs (as originally written)

| Question | 06 usage statements | 07 cost allocation | 08 API version change | 09 negative control |
|---|---|---|---|---|
| Solvable by transcribing one document? | No; about 70% from vendor spec + contract + runbook together | Nearly: policy + worked residual example | Nearly: changelog sentence | Yes: parity log + catalog + schema field names |
| Helper giving away implementation? | Only if batch-era statement code were present | Engine comments; `cpu_request` next to `cpu_usage` | Old-version handler; DQ registration template | Mix-adjusted metric implementation |
| One grep reveals the cause? | 3 of 4 defects via ADR wording | Basis only | Most | Yes |
| Published number as answer key? | Tie-out notebook = key for the *wrong* rule (deliberate); batch history = key for the *right* rule on ungraded months (undecided) | History contradicted engine story | Payouts ≈ exact net key | None |
| Root cause location | Local code (internal release) | Infra change exposing code assumption | External + stale cache | None |
| Aggregates prove correctness? | Partly (money telescoping) | No | Mostly (net) | Yes |
| Requires data inspection? | Yes | Moderate | Yes (guided) | Trivial |
| Broader than one filter? | Yes | Yes (shallow) | Yes | N/A |
| Several plausible wrong repairs? | Yes | Yes | Some | Caught by rerun |
| Rule uniquely recoverable? | **No** (about 16 ambiguities) | **No** (blocking gaps) | **No** (event-id / re-export semantics) | Not at 1e-6 tolerance |
| Hidden fixtures add hidden rules? | hidden_a, hidden_b drifted | hidden_b, hidden_c | hidden_a, hidden_b | No (report not generalised) |
| Distinct from 01–05? | Mostly (close cutoff ≈ Task 02) | Partly (ownership ≈ Task 01) | Overlaps Task 06 (idempotent fold) | Storyline ≈ Task 03's mix distractor |
| Likely difficulty | Frontier, with underspecification risk | Underspecified | Easy–moderate | Too easy |

## 2. Key findings by design

### Task 06

1. **Internal contradictions.**
   - A v2 dedupe "by event_id keep first" cannot let replays through, yet the story needs August replay duplicates.
   - A "February-rate adjustment" in a world without February data and with only a September rate change.
   - Northwind must be EU for the outage story.
   - Batch-era knowledge at close was not defined identically to the reference.
   - hidden_b lateness contradicted the vendor spec.
2. **Close vs issuance ambiguity.** The contract keyed on "issued" but the runbook keyed on close, while the September run
   is late. This was the most serious ambiguity.
3. **Unresolved grading ambiguities.**
   - Adjustment money formula and rounding.
   - Zero lines.
   - Months eligible for adjustment.
   - Label vs provenance of issued lines.
   - Mart coverage.
   - Window alignment.
   - Close boundary.
   - Void representation.
   - "Commitment" implying a minimum fee.
4. **Leaky prose.**
   - ADR wording named receipt windowing and event-id dedupe.
   - Vendor spec said "idempotency key (event_id, rev)" and "out-of-order delivery possible", effectively §5.1 verbatim.
5. **Hidden-rule drift.** Out-of-order revisions and second adjustments appeared only in hidden fixtures.
6. **Root-cause location is again local code.** Diversity must come from 08 and 09.

### Task 07

- The billing export as designed (`day × project × SKU`) cannot yield pool-day cost. **Blocking.**
- History was said to be requests-consistent while the engine had been usage-based since 2025. **Contradiction.**
- Undefined allocation bases (storage, GPU), unresolved max(request, usage) alternative, ill-posed two-way rounding, and
  hidden rules for empty pools and partial commitments.

### Task 08

- The changelog sentence nearly transcribes the change.
- A contradiction between "cumulative on the charge" and "latest cumulative per refund id".
- Re-export event-id semantics undefined.
- `refund.updated` re-sends duplicate Task 06's idempotency.
- Payouts are an exact net key with no attractor.

### Task 09

- The report schema enum, the `rate_current_at_baseline_mix` field, the catalog definition and the parity log together
  leak the answer.
- Numeric grading at 1e-6 is ill-posed over week/window/pooling choices.
- "Primary dimension" has no criterion.
- The storyline recycles Task 03's low-intent campaign.
- **Better design:** a *twin incident*, where the same workspace carries one genuine defect in a secondary metric and one
  real mix shift. It is graded behaviourally: fix one, leave the other byte-identical on hidden extracts.

## 3. Decisions

| Design | Decision | Main revisions |
|---|---|---|
| 06 | **Implement first** after must-fixes | See `task06_design.md` §23 |
| 07 | Redesign before build | Billing lines carry cluster/pool/namespace cost-allocation labels. History comes from a previous requests-based engine version, with a 2025-11 regression to usage basis masked until consolidation. Bursting namespaces falsify max(request, usage). Every category's basis defined via policy facts. Empty pools and partial commitments visible. Rounding per category column only |
| 08 | Revise before build | Vendor changelog reduced to "refund object semantics updated; see API reference", with stale reference docs. Drop status-update re-sends (overlap with 06). Specify re-export manifest and event-id semantics; partial re-export visible. Add payout reserves/holds for the fraud merchants so exact payout matching is a wrong target |
| 09 | Replace with twin-incident negative control | One genuine defect in a secondary metric plus one real composition change (not a low-intent campaign; e.g. app-store feature or regional launch). Graded behaviourally: defect fixed, conversion metric outputs byte-identical on hidden extracts, no enum report |

## 4. Why Task 06 first

- Of the four designs, it is the only one whose difficulty comes from reconstructing an invariant across grains (the
  Task 02 lesson).
- Its authority hierarchy is the most defensible: contract and vendor semantics outrank the ADR rationale and the
  finance tie-out.
- Its deliberate attractor (the tie-out notebook) is falsifiable from data.
- Its main weakness (underspecification) is fixable with *evidence* (reproducible batch-era history, data dictionary
  properties) rather than more algorithmic prose.
- 07 and 09 need structural redesign. 08 overlaps 06 and should follow once 06's semantics are fixed.

## 5. Residual concerns carried into implementation

- **Root-cause location.** Task 06 is again an internal release. 08 (external) and 09 (none/twin) must supply diversity.
- **Close cutoff vs Task 02.** The received-before-close cutoff overlaps Task 02's load-time cutoff. It is accepted as one
  component among four.
- **Reproducible history.** Batch-era statements reproducible from raw landing are a backtest key for the correct rule on
  ungraded months. This is accepted deliberately, because it rewards the graded-grain validation the baselines lacked.
  It may reduce headroom and is flagged for baseline interpretation.
- **Exact-detail count.** Target 10–12; re-counted after implementation (see `task06_design.md` §23).
