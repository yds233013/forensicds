# G36 adjudication - why the selection transport was inert

## What was intended

G36 was designed with two orthogonal transport problems between the pilot and the estate:

- **A. Selection.** Voluntary enrolment over-represents controllable premises (0.32x-2.49x by segment).
- **B. Heat dependence.** The response fades with cooling demand, and the pilot season was milder than
  the target.

The research-phase recognition gate reported that the selection insight alone left 37 sd of error.

## What the baseline showed

| | T1 | T2 | T3 |
|---|---|---|---|
| selection recognised | no | yes | yes |
| **selection executed correctly** | **yes** | **yes** | **yes** |
| enrolled mix compared with estate mix | no | no | no |

All three executed the selection transport correctly, including the trial that never mentioned
selection. None ran the diagnostic the design expected to separate correct analysts from wrong ones.

## Why: three artefacts that together hand the solution over

### 1. The DGP puts selection and effect modification on the same single variable

```
world.py   e = rng.random() < sp["optin_prop"][seg[h]]          # enrolment depends only on segment
world.py   sp["resp0"][seg_idx] * damp                           # response varies only by segment
```

This is exactly the research-phase identification assumption **A3** ("segment membership captures
the effect modification"). Under A3, within a segment the enrolled households are exchangeable with
the estate's households. **Stratifying by segment and weighting by estate shares is therefore not
just a valid correction; it is the entire correction.** No residual selection exists within a segment.

### 2. The incumbent scaffold already performs estate standardisation

```
incumbent.py:19   shares = frames["customers"]["segment_code"].value_counts(normalize=True)
incumbent.py:23   for s in shares.index:
incumbent.py:32       total += float(shares[s]) * fc
```

The production model the agent is handed already loops over segments and weights by **estate**
composition from the customer master. The natural edit, which is the one all three trials made, is to
insert a per-segment tariff response inside that loop. That edit inherits estate weighting for free.

### 3. The output contract requires a segment-stratified, estate-weighted result

```
analysis_contract.md   "estate_segment_shares": {...}     - share of the estate in each segment
analysis_contract.md   "segment_target_peak_kw": {...}    - per-segment mean peak-window kW
```

The schema asks for per-segment forecasts and estate shares, and the reconciliation check requires the
first to weight by the second to the headline. The contract specifies the correct aggregation path.

## So how can selection be failed at all?

Only by **pooling across segments** — estimating one tariff response from all enrolled households and
applying it to the estate. The mutation panel confirms this route fails (`M07_pilot_effect_flat`,
`M18_aggregate_effect_uniform`). But pooling means actively discarding the scaffold's per-segment
structure. An analyst extending the code in place does not do it.

## Where the research-phase gate went wrong

The gate measured "selection-naive" as `M09_temperature_fixed_only`, an analysis that weights by the
**enrolled** mix. That is a genuine error, but it is not the error a natural analyst makes: replacing
the scaffold's estate shares with enrolled shares requires deliberate work against the code provided.
The natural selection-naive analysis is the pooled one, and the scaffold steers away from it.

**The gate was measured against the wrong counterfactual analyst.** It correctly established that
selection *can* matter numerically. It did not establish that selection is *live* for an analyst
working from the artefacts provided.

## Was this knowable before the baseline?

**Yes.** A3 was written into `research/g36/identification.md`, the scaffold was written by me, and
the contract fields were chosen by me. A "natural implementation path" audit, asking what the
minimal edit to the incumbent does, would have shown selection was pre-solved. I did not run that
audit. The trajectories exposed the gap, but did not create it.

That matters for the redesign question (`contamination_analysis.md`): a gap that was derivable
without the model does not license a redesign chosen in the light of the model's behaviour.

## General lesson

**A transport problem is inert when the variable driving selection is the same variable the scaffold
or output contract already asks the analyst to stratify and standardise over.** Before claiming two
orthogonal difficulties, trace the minimal edit to the provided code and check whether it solves
either one by construction.
