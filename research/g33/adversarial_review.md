# G33 adversarial review

Performed by reasoning and code only — **no model call, no LLM critique**, per the brief. Every attack below
was executed against `simulation.py` / `methods.py`; results are in `simulation_results.md`.

**Verdict: BLOCK.**

## The killer objection

**The task collapses into a single semantic bit, and that bit is either given away or ambiguous.**

Measured: coarse *grain* errors (vendor-level, parent-level) move the business metric by 65–78% relative;
genuine *identity-reconstruction* errors (ignoring the registry history, mishandling splits, mis-assigning
unattributed lines) move it by 0.6–8%. So the task is decided entirely by whether the analyst aggregates at
the node grain rather than the vendor or parent grain. Everything the design was built to test — merges,
splits, renames, migrations, transfers, contract manufacturing — is numerically irrelevant once the grain
is right.

And that single bit cannot be positioned. If the task documents state that the unit is the production node
(they must, or competent analysts defensibly disagree and **K6** fires), the hard part is handed over and
**K8** fires. If they do not state it, the task is ambiguous. There is no version of this design that is
both well-posed and non-trivial.

## Attacks, with results

| Attack | Outcome |
|---|---|
| **Task 01 already tests this** | Partly true and worse than that: the estimands that *are* structurally sensitive to merging and splitting are the within-vs-between decompositions (churn vs expansion, revenue restatement), which is exactly Task 01's ground. The concentration metric chosen to escape Task 01 escaped by becoming insensitive. |
| **A simple approach solves it** | Yes — four cheap heuristics land within 0.004 of the truth on top-1 share, and counting lines instead of summing amounts is the most accurate of them. |
| **Raw/current IDs give the right metric** | Yes. Raw shipment codes: mean abs error 0.027 on a truth of 0.16–0.33. **K4.** |
| **The final decision can be guessed** | Yes. Constant `within_limit` is correct in 54/60 worlds across all five regimes, including the regime built to flip it. **K9.** |
| **A wrong mapping produces the right metrics** | Yes — W4, W5, W6, W9 all reproduce the decision and land within 0.004–0.016 of truth. **K12.** |
| **One authoritative table gives the mapping** | Close to it: the shipment record's ship-from code is ~92% of the answer, and the registry log supplies the rest mechanically. |
| **Downstream outcome leaks identity** | No, and this one it survives: amounts are identically distributed across nodes. |
| **Generator artefacts reveal clusters** | One real finding: vendor-count per node is a strong size proxy (28/20/5/8/4 for the top five, 1 each for the bottom five). Realistic, but it would let an analyst rank nodes without resolving spend. |
| **The ground truth is unknowable** | Not in the current draft — but an earlier draft *did* fail this, resolving registry splits by a material-group parity rule the analyst could never observe. It was rewritten before any gate was run. The near-miss is worth recording: this failure mode is easy to introduce and invisible without an explicit check. |
| **Verifier would overfit exact clusters** | Would have to grade node assignment up to relabeling, which is doable — but moot, since the assignment barely affects the graded metrics. |
| **Hidden regimes change the identity definition** | No; the invariant is preserved across all five. That part of the design is sound. |
| **The decision sits on a knife edge** | Yes, and this is independent of the above: the truth straddles the 25% limit as a function of seed (5 breach / 7 within_limit across 12 visible worlds). Which side a frozen fixture lands on would be an artefact of seed selection. |

## What the design got right

Worth recording so the next attempt does not rediscover it: the **relationship-vs-identity pairing** is
genuinely good. One node serving vendor codes under two parents (contract manufacturing) while two nodes sit
under one parent defeats parent rollup in both directions simultaneously, and the measurement confirms it
(W3 parent rollup: +65% relative error, wrong decision). The *mechanism* is sound. It is the estimand that
cannot transmit it.
