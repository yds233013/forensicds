# G25 design gate: search release gate under judgment-pool bias

**Decision: GO to Phase 0 → STOPPED at the gate (§7).** The redesign and required fixes are recorded; the simulation gate did not separate the design's central attractor, so no implementation was started. The design is detailed, its traps are principled, and its required
fixes are cheap and specific. Unlike G01, its statistical layer does not duplicate an existing task: G24 estimates a
policy value from logged decisions, while G25 estimates a *measurement* (a ranking metric under complete judgments)
from an audit sample whose frame is defined by the broken harness.

- **Sources re-read:** `research/gen3_designs/G25_search_judgment_pool.md` (505 lines, design only),
  `research/gen3_candidate_pool.md` §G25, `research/gen3_design_tournament.md` (R3 review; rank 7 post-tournament),
  `research/gen3_implementation_shortlist.md` §S7.
- **Nothing is built. No model has been run.**

## 1. Capability and why it is still missing

> Can an agent estimate what a ranking metric **would be under complete judgments**, when the judgment pool was built
> from the incumbent ranker, label identity spans three query-key generations and two rating scales, and the only
> handle on unjudged results is an audit sample whose frame was defined by the broken harness?

Current coverage: entity grain (01), point-in-time state (02, G08), evaluation population (03), KPI lifecycle (04,
06), randomisation unit (05), censoring (G10), off-policy evaluation (G24), causal panels (G05). G25 adds
**measurement repair under incomplete, heterogeneous labels**, and it is the only remaining design whose estimand is a
metric rather than an effect.

## 2. Chain, with the object at each step

| Step | Object | Natural wrong object |
|---|---|---|
| Business decision | ship candidate B or not, at threshold Δ ≥ −0.005 | trust the A/B lift (price-driven) |
| Estimand | NDCG@10 as if every product in both lists were judged on the gate scale | condensed lists (drop unjudged); unjudged = 0 |
| Query identity | `qnorm_v3(display_query)` from the round manifest | `qnorm_v3(query_key)` — wrong for fraction queries, and collision twins receive a twin's labels |
| Product identity | GTIN when present, else doc_id | doc_id only, so 3P offers of judged products look unjudged |
| Label semantics | RG-5 {4}→2, {3,2,1}→1, {0}→0, from guideline wording | linear map, round-half-even, clip |
| Label currency | latest `judged_at` supersedes | max, mean or first |
| Unjudged slots | expected gain from R09 pairs **still unlabelled after resolution** | the full R09 frame (which includes pairs that resolution labels), or the labelled-slot mean |
| Decision | threshold on the estimated Δ | — |

Two partial repairs make B look **worse** (join fixed alone: Δ −0.034; plus scales: −0.031), which reinforces the
wrong conclusion. That is the property that raised this design from rank 14 to 7 in the tournament.

## 3. Required fixes (from the tournament and shortlist), all adopted

| Fix | Reason | Status in v2 |
|---|---|---|
| Add `task_id` to judgments | collision twins are otherwise ambiguous to resolve | adopted |
| Widen the frame-restriction trap to ≥ 2.5 τ | in v1 it was ≈1.5 τ, too close | **to be verified by the Phase-0 gate** |
| Remove key form and scale from `rounds.yaml` | it was a recipe: it told the agent both the join rule and the scale map | adopted; both must be inferred from manifests, label ranges and guidelines |
| Remove `gtin` from judgments | forces the catalog join that carries the product-grain insight | adopted |
| Express RG-3 "Partial" as rater examples, not a crosswalk | avoid stating the mapping | adopted |
| Remove the historical "unjudged = not relevant" line from the gate doc | it contradicts the instruction's estimand | adopted |

## 4. What the Phase-0 gate must establish

The identity, scale, product-grain and supersession errors are **deterministic**: they are caught by the exact
resolved-qrels table, and no simulation is needed to know they fail. The gate therefore targets the one statistical
step:

1. **Accepted panel within tolerance:** global-mean imputation, rank-bucket imputation, a seeded bootstrap over the
   audit sample, and an expected-DCG/expected-IDCG variant.
2. **The frame trap ≥ 2.5 τ:** estimating expected gain from the *whole* R09 frame instead of the pairs still
   unlabelled after resolution.
3. **Condensed lists and unjudged = 0 reliably outside tolerance**, and on the wrong side of the decision in at least
   one regime.
4. **Scale-map errors** (linear, round-half-even, clip) measured; they are also caught by the table, so the gate only
   needs their metric effect for the report.
5. **Decision margins** ≥ 4 SE(Δ) in every fixture, per the design's own rule.

**Stop conditions.** If the accepted panel cannot be separated from the frame-mean estimator without a tolerance that
also admits condensed lists, or if a defensible stratification choice moves the estimate by more than the tolerance,
G25 stops and is documented like G01.

## 5. Risks carried into the build

- **Underspecification of A's unlabelled slots** (4% of A's slots are outside R09's frame). The design bounds the bias
  at ≤0.002 and folds it into τ. The pilot must confirm that a principled alternative (A's unlabelled = 0) stays
  inside τ_A, otherwise the task rejects a defensible answer.
- **Expected-gain vs plug-in IDCG.** Both must pass; the pilot measures the gap.
- **Headroom.** An agent that knows inferred/statistical IR metrics may go straight to the audit sample. The remaining
  difficulty is then the frame restriction and the exact table.

## 6. Decision

**GO to Phase 0.** Build the simulation gate first (`research/g25/pilot/`), then the task only if the gate passes.

## 7. Phase-0 result: STOPPED at the gate

Three pilot iterations (`research/g25/pilot/`, 4 regimes × 20 seeds, 10 calibration + 10 validation each). The gate
targeted the one statistical step: estimating the unjudged slots' contribution.

| Iteration | Change (with rationale) | Outcome |
|---|---|---|
| 1 | design parameters as written | B worse in every regime (no "pass" world); condensed lists accidentally near-correct in one regime |
| 2 | B's labelled slots genuinely better (design's intent); the gate document specifies the IDCG convention; harness-frame slots made clearly better than truly-new ones | frame trap reached 2.35 τ; **condensed lists passed 10/10 in three of four regimes** |
| 3 | unlabelled slots concentrated at top ranks (semantic retrieval places new products high — a realism change) | frame trap 2.51 τ ✓, unjudged = 0 at 2.64 τ ✓, labelled-mean 4.87 τ ✓; **condensed lists still pass 7/10 worlds in two regimes** |

### Findings

1. **Condensed lists are not materially biased at k = 10 in this generator.** The design targeted B +0.038; the pilot
   measures a much smaller error, because condensing both *removes* weak slots (losing their gain) and *promotes*
   labelled ones, and at rank 10 the tail discounts make these nearly cancel. The design's central claim — that the
   textbook fix is clearly wrong here — is not reproduced.
2. **The metric levels are not gradeable at useful precision.** The accepted panel's RMSE on `ndcg10_A` and
   `ndcg10_B` is 0.004–0.014, dominated by audit sampling error that is *common* to every valid estimator. Tolerances
   wide enough for valid variation (τ up to 0.042) also admit both IDCG conventions and, in some regimes, condensed
   lists. Only Δ is well determined (RMSE 0.0027–0.0036), because the sampling error is shared between A and B.
3. **The tournament's required fixes are otherwise achievable:** with the frame contrast widened, the
   frame-restriction trap reaches 2.51 τ, above the required 2.5 τ.

### Blocker

> The design's headline attractor (condensed lists) is not reliably separated by the graded metric, and the metric's
> levels cannot be graded at a precision that excludes it without also rejecting defensible estimator variation.

Grading Δ alone does not rescue it: condensed's Δ error sits at roughly the Δ tolerance.

**Options for the maintainer:**
1. **Re-scope the estimand to Δ only** and re-derive the attractor: find a wrong handling of unjudged slots whose Δ
   bias is large (unjudged = 0, labelled-mean imputation and the frame-mean estimator all qualify at 2.5–4.9 τ), and
   drop the claim that condensed lists are the trap. The task then tests *sampling-frame reasoning* rather than "the
   textbook fix is wrong".
2. **Change the metric to one where condensing is clearly wrong** — e.g. a recall-oriented or coverage-weighted
   measure, or a deeper cutoff (k = 20+) where removing top slots cannot be offset by promotion.
3. **Drop G25** and keep the identity/scale/product-grain half as a deterministic task, which would then overlap
   Task 01/02 rather than adding a measurement capability.

No task files were created for G25.
