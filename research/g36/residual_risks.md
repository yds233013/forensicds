# G36 residual scientific risks

Written before the freeze decision, so the reviewer sees them as I see them.

## R1 - decision margins are thinner than G35's (the one to scrutinise first)

| fixture | margin | in SE_REF |
|---|---|---|
| hidden_b | 0.3296 | 18.5 |
| hidden_d | 0.0523 | 3.1 |
| visible | 0.0470 | 2.4 |
| hidden_a | 0.0639 | 2.3 |
| **hidden_c** | **0.0796** | **2.0** |

G35's floor was 5.3 sd; G36's is 2.0. `hidden_c` is tightest because its steep response curve (the
response quarters between pilot and target weather) amplifies extrapolation error, giving it the
largest SE_REF in the set at 0.0399.

**Why this is still gradeable:** the fixtures are frozen, so the question is not whether a random
draw decides correctly but whether the accepted estimators decide *these* draws correctly. All three
independent families get all five right on the frozen fixtures, and were unanimous and correct on
20 of 20 fresh draws. But a competent analyst using a slightly less efficient valid method could
plausibly land on the wrong side of `hidden_c`, and that would be a false negative attributable to
the benchmark rather than the analyst.

**What was NOT done about it:** the threshold was not moved, and the fixtures were not re-searched.
Moving either to widen margins is exactly the threshold-hacking rejected in
`threshold_provenance.md`. The margin is a consequence of an independently derived ceiling and an
even sweep of the realistic response range, and it is reported rather than engineered away.

## R2 - F3 carries a small measurable bias

The hierarchical family shows -0.0090 against truth over 20 draws (t = -3.07). That is the shrinkage
trade behaving as designed and is 0.6 sd of a single estimate - immaterial at a tolerance of
2.5 SE_REF - but it is real. If a future build tightens the tolerance materially, F3 should be
re-examined before it is retained in the accepted set.

## R3 - the estate-response check is partially redundant

Its error correlates with the forecast error at r = -0.82, so roughly a third of its variance is
independent. It earns its place because `M28_response_reported_zero` and `M29_response_sign_flipped`
are caught **only** by it - but it is not an independent second pillar, and a reviewer should not
read "two graded quantities" as "two independent tests".

## R4 - two graded quantities, one underlying analysis

Both graded numbers come from the same decomposition. An analyst who gets the transport right gets
both right; one who gets it wrong usually gets both wrong. The suite shows two exceptions (M28, M29),
which is why both are graded - but the effective number of independent scientific tests is closer to
one and a third than to two.

## R5 - difficulty is unmeasured against any model

No model has seen this task. The recognition-vs-execution gate is far stronger than G35's on
simulation (37-71 sd after a single insight, against G35's 11-12 sd), which is the reason to expect
a lower pass rate - but G35's own pre-registered prediction was directionally right about the
mechanism and still landed at the top of its range. **The band in
`model_failure_predictions.md` is 0/3 to 2/3 and remains a prediction, not a result.**

## R6 - the dataset is 21 MB

Larger than G34 (6.4 MB) and G35 (6.4 MB), because household-day load over two seasons for 6,000
customers is 565,000 rows. It is queried by SQL and never read raw, so it is not a context-length
trick, but it does make each verifier run and each `harbor check` slower. If a future variant needs
to be lighter, the history is heavily over-powered for the stable curve and could be sampled without
affecting identification.
