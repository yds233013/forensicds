# G44 target-model baseline — google/gemini-3-flash-preview

Three sequential trials on the frozen task (checksum `e688a53ec78348cb`, Harbor digest
`sha256:1fa0fa3eeeb4ac8…`, identical in all three). All three carry a full grading report.

| Trial | Reward | Cost (USD) | What it got wrong |
|---|---|---|---|
| `g44-…__fLYxEq8` | 0 | 0.0768 | **only** `flagged_transactions`: 1,713 counted from the review table instead of 1,762 from the transaction table |
| `g44-…__UxvdT7t` | 1 | 0.0834 | — |
| `g44-…__sHDR6rJ` | 1 | 0.1089 | — |

**pass@3 = 2/3.** Total spend $0.2691. G44 is **development-only**: the suite already carries its two
permitted solved tasks (G34, G41).

## The honest reading is stronger than 2/3

The failing trial got the sensitivity, the specificity, the weighted evidence, the base-rate transport
and the certification decision **right on all four extracts**. Its only error was a bookkeeping count —
how many transactions the screen flagged — taken from the review table, which omits the cases still
pending. On the scientific object this task exists to measure, the model was correct in three trials out
of three.

Reporting this as "the model fails G44 one time in three" would be false precision about an incidental
field, so the task is recorded as **solved 3/3 on its object**, with the single reward-0 explained.

## The prediction was wrong, and that is the finding

`design.md` recorded, before the baseline: *0/3 or 1/3, with the dominant failure being the base-rate
transport*. Neither happened. All three trials:

- excluded ad-hoc reviews and pending cases from the evidence;
- read `quality_sample_one_in` from the extract and weighted the sampled passes by it;
- read `merchant_fraud_rate` from the contract and applied `se·p / (se·p + (1−sp)(1−p))`;
- and stated plainly that the published certificate quoted the wrong populations.

So the derivation this task was built around — that precision does not transport and that a one-in-N
sample needs weighting — is **not** a discriminating difficulty for this model class, even though no
document in the workspace stated it. Principle 17 is necessary and not sufficient: *unstated* is not the
same as *hard*. What made Task02, G05, G10, G24 and G34 discriminating is not merely that the object was
unstated, but that recovering it required reconstructing a process the data only partially records —
as-of feature timing, staggered exposure, censoring, logging policy, competing risks — rather than
applying a standard identity to quantities the extract hands over cleanly.

This is recorded as principle 19 in `research/benchmark_hypothesis.md`.
