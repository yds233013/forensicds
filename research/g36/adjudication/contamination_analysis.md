# G36 adjudication - contamination analysis for every proposed change

We now know how `gemini-3-flash-preview` behaves on G36. Any post-baseline change must have an
**independent scientific justification**, and each is tested against one question:

> *Would I have proposed this if I had never seen the Gemini trajectories?*

If the answer is **NO**, the change is rejected. This is deliberately strict. It forbids designing a
revision to defeat the specific estimators that succeeded (T2 and T3, both segment-stratified and
equivalent to F1) or the one that failed (T1, a constant-kW restriction).

## An independence test for the adjudication itself

The response-definition finding would be suspect if it depended on which definition the trials used.
It does not:

> **Had all three trials computed the household-weighted response, the adjudication would reach the
> same conclusion** — the load-weighted definition is the correct estimand. The trials would then have
> passed the frozen verifier and *failed* the corrected one.

The correction is therefore not tuned toward a pass. It follows from the contract text and capacity
arithmetic regardless of outcome.

## Change-by-change

| # | proposed change | independent scientific motivation | would I propose it without the trajectories? | decision |
|---|---|---|---|---|
| **C1** | Grade `estate_tou_response_at_target_cdd` as the **load-weighted** reduction at the target mean CDD | contract wording ("fractional reduction in peak-window load"), capacity arithmetic, composition with the forecast (`response_estimand.md`) | **YES.** The defect exists independently of any model and is caught by IGQA part (2) with no model involved. The trajectories triggered the review; they do not determine the answer. | **ACCEPT** |
| **C2** | Recompute the oracle's response helper, `SE_REF` and tolerance for the response under C1, using the same measured-window procedure | mechanically required by C1 | **YES** | **ACCEPT** |
| **C3** | Keep the response graded (under C1) rather than dropping it | the contract asks for it; it is identifiable; it catches reporting-inconsistency analyses (`M28`, `M29`) | **YES** — the retention argument predates the baseline and is unchanged by it | **ACCEPT**, reclassified as a secondary check (see `recommendation.md`) |
| **C4** | Correct `task.toml` `difficulty_explanation` to say G36 primarily tests regime-dependent response transport, with selection pre-solved by the scaffold | factual accuracy about what the task measures | **YES** — the selection gap was derivable before the baseline from assumption A3 and the scaffold (`selection_transport_postmortem.md`). Agent-invisible. | **ACCEPT** |
| **C5** | Introduce any selection mechanism S1-S7 | S3 and S1 are scientifically strong | **NO.** I did not propose them pre-baseline, although the gap was derivable. Every option is specifically constructed to break segment stratification — the exact estimator T2 and T3 used. Choosing one now designs toward observed behaviour. | **REJECT** |
| **C6** | Remove the scaffold's estate weighting (S6) | the least artificial way to make selection live | **NO** — same reasoning. It also changes the agent-visible workspace. | **REJECT** |
| **C7** | Add documentation that nudges toward comparing enrolled and estate mixes | would make the selection diagnostic more likely | **NO** — motivated directly by the observation that no trial ran it | **REJECT** |
| **C8** | Move the response's evaluation point from the mean CDD to the season average (`R_season`) | more coherent with the season-average forecast | **YES** in motivation, but it is a design *improvement*, not a defect fix, and it changes the contract's stated evaluation point, which is agent-visible | **REJECT for this revision**; recorded for any new task |
| **C9** | Widen `hidden_c`'s margin, move the threshold, or touch forecast tolerances | none — the `hidden_c` false-negative concern did not materialise | **NO** | **REJECT** |
| **C10** | Constrain the treatment slope or otherwise target the T1 failure | none | **NO** | **REJECT** |

## Net effect

Only four changes survive, and **none of them touches an agent-visible artefact**:

- C1 and C2 change the verifier's truth definition, and correspondingly the oracle helper and response
  tolerance.
- C3 keeps an existing check.
- C4 corrects agent-invisible metadata.

The instruction, docs, contract, data, incumbent code, generator, fixtures, threshold and forecast
tolerances are all unchanged.

## Consequence for measurement

Because the agent-visible task would be **byte-identical** under the surviving changes, the three
existing trajectories were produced against exactly the task the revision would present. Model
sessions carry no memory between runs. Regrading them under the corrected verifier is therefore a
measurement of the revised task, not a counterfactual on a different one.

Whether a post-baseline verifier correction, triggered by baseline observations, may be regraded in
this way is a methodological decision for external review. **It is not assumed here.**
