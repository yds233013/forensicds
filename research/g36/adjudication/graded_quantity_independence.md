# Independent Graded-Quantity Audit (IGQA)

## Why K9 missed the G36 defect

K9 required three genuinely independent estimator families to agree on the headline forecast. They did:
different algorithms, different pooling, different data for the stable component. That establishes
**computational** independence for `target_peak_kw`.

It established nothing about `estate_tou_response_at_target_cdd`. All three families produced that
quantity through **one shared helper**, `estimators.estate_response_at_target_cdd`, which implements a
household-weighted definition. The verifier's `_truth_values` used the same definition. So the oracle,
all three reference families, the mutation suite and the verifier truth agreed with each other
perfectly, because they were **one definition written once and called everywhere**.

Two further structural reasons made the defect invisible:

1. **Mutations perturb values, not definitions.** `M28_response_reported_zero` and
   `M29_response_sign_flipped` corrupt the number a correct pipeline produces. No mutation asked
   "what if the definition itself is different?"
2. **The truth came from the generator, and the generator's truth used my definition.** A
   latent-truth check guards against estimator bias. It cannot guard against grading the wrong
   estimand, because the latent truth is computed for whatever estimand the verifier author chose.

**A verifier can be statistically robust about the main estimand and still be semantically wrong about
an intermediate one.**

## The rule

> **For every graded quantity Q, the audit must show both:**
>
> **(1) Computational independence** — at least two derivations of Q sharing no code path, no helper
> and no intermediate function agree within calibrated sampling error; **or** Q is an algebraic
> function of other graded quantities that each satisfy (1).
>
> **(2) Semantic independence** — at least one derivation of Q is written **from the contract text
> alone**, by a procedure that never reads the verifier's truth function or the oracle, and it agrees
> with the verifier's truth definition. Where the contract admits more than one reading, the audit must
> list the readings, and the contract must be tightened until only one survives.
>
> A quantity whose aggregation or weighting is not pinned by the contract fails (2) automatically.

Part (2) is the new element. Part (1) alone would have passed G36's response, because two families
could have been given separate copies of the same wrong definition.

## Retrospective application to G36

| graded quantity | (1) computational | (2) semantic | verdict |
|---|---|---|---|
| `target_peak_kw` | **PASS** — F1/F2/F3 independent, pairwise \|t\| <= 1.82 | **PASS** — "mean peak-window kW per residential customer … whole estate on the tariff … forecast weather" admits one reading | **PASS** |
| `estate_tou_response_at_target_cdd` | **FAIL** — one shared helper | **FAIL** — weighting unpinned; the natural reading (load-weighted) contradicts the verifier (household-weighted) | **FAIL — F8** |
| `procurement_decision` | forced: forecast >= stated ceiling | the ceiling and comparison are stated in the memo | **PASS** (algebraically forced) |
| bookkeeping (counts, shares, target CDD mean) | verifier recomputes from the database independently of the agent | definitions are counts | **PASS** |

## Retrospective risk scan of the other frozen tasks

A desk audit of each task's contract against its verifier truth. **No task was modified, no model was
run, and no new validation was executed.** The question asked of each graded aggregate is whether its
weighting or aggregation is pinned by the text the agent reads.

| task | graded aggregates | is the aggregation pinned by the contract? | truth consistent? | IGQA risk |
|---|---|---|---|---|
| **G05** | `effect_by_wave`, `gate_effect` | **yes** — glossary: "the simple average across the stores concerned (each store counts once, whatever its size), because capital is committed per store"; gate "as planned" per the business case | truth is "store-weighted" | **LOW** |
| **G10** | `expected_demand`, `lost_units`, category baselines, `lost_share`, `forecast_bias_pct` | **yes** — formula-level ("sum over the category's store-SKUs of each store-SKU's average …", "`lost_units` divided by the same rows' summed `expected_demand`") | formulas | **LOW** |
| **G24** | ranker `value`, `lift_vs_v6`, launch | **yes** — "home-row clicks per slate decision over the extract's decisions" | per-decision mean | **LOW** |
| **G34** | four cumulative-incidence shares, engineering net risk, `units_at_risk` | shares **yes** ("proportions of the installed base … mutually exclusive outcomes"); engineering quantity **by prose** in the engineering note; `units_at_risk` defined in the contract | latent CIF / net risk | **LOW-MEDIUM** — the engineering quantity is defined conceptually rather than by formula; a contract-only derivation has not been recorded |
| **G35** | direct, spillover, policy effects | **yes** — "demand weighted: orders, not merchants, are the unit" | demand-weighted | **LOW** — and the measured near-miss `W09_unweighted_blocks` showed the alternative weighting landed inside tolerance in that DGP anyway |

**Protective factor.** Every earlier task whose graded aggregate had a weighting choice stated that
choice in the agent-facing text, usually with a business reason. G36's response was the only graded
aggregate whose weighting was left unpinned, and the verifier chose the reading the wording argues
against.

**Recommended follow-up, not performed.** Record a contract-only derivation for G34's engineering
quantity, the one residual prose-defined estimand in the frozen set.

## How IGQA would have caught G36

Part (2) requires writing the response from the contract text without reading `_truth_values`. Any
such derivation reads "fractional reduction in peak-window **load**" and computes a load ratio, then
disagrees with the verifier by 1.23x. The defect would have been found before the freeze.
