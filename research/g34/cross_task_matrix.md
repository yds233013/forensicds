# G34 distinctness and S0–S9 placement

## Distinctness, tested rather than asserted

| Task | Its object | G34-as-designed | Verdict |
|---|---|---|---|
| **Task 02** | feature state at prediction time | the separating error is **using the monitoring timestamp instead of the commissioning date** — a timestamp-semantics error | **overlaps materially** |
| **G08** | historical/vintage semantic reconstruction | the second separating error is **mapping four work-order removal reasons onto statistical roles** — a status-code semantics error | **overlaps materially** |
| **G10** | latent continuous demand under stockout censoring | G34's outcome is a binary event time, its censoring has no latent-quantity model, and the machinery is risk sets rather than a latent distribution | **distinct** |
| **G24** | policy value under a logged stochastic policy | no propensities, no actions, no counterfactual policy | **distinct** |
| **G05** | treatment effect under staggered adoption | no treatment, no counterfactual trend, no control group | **distinct** |
| **G31** | selectively observed labels | the informative-censoring variant *would* have collapsed into this — and it was rejected on test, for that reason among others | **distinct only because that variant was cut** |
| **G33** | entity resolution | no identity reconstruction | **distinct** |

The distinctness claim holds against four of seven tasks and **fails against Task 02 and G08 for
exactly the parts of the design that carry the separation**. That is the core of the rejection.

## S0–S9 placement

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 |
|---|---|---|---|---|---|---|---|---|---|---|
| **G34 intended** | — | — | support | **core** | **core** | support | — | — | — | — |
| **G34 measured** | — | — | **core** | core | support | — | — | — | — | — |

Intended: S3–S4 (what is the time-to-event object). Measured: the separation is carried by **S2**
(reconstructing the age clock and the removal semantics) with S3 (net vs crude estimand) second.
S5 — the identification assumptions that make left truncation and competing risks matter — turned
out to carry almost nothing, which is precisely the problem.

**The crude-risk variant would move the centre of mass to S3/S4**: net risk and crude risk are
different statistical objects answering different business questions, and choosing between them is
not a reconstruction step. That is the argument for redesign rather than drop.
