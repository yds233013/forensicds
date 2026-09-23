# G42 target-model baseline — google/gemini-3-flash-preview

Three sequential trials on the frozen task (checksum `4b4ded75469d229a`, Harbor digest
`sha256:7f72f81cfbf899be2…`, identical in all three). All three carry a full grading report.

| Trial | Reward | Cost (USD) |
|---|---|---|
| `g42-…__qt3DhgZ` | 1 | 0.0600 |
| `g42-…__kmbXrGJ` | 1 | 0.0498 |
| `g42-…__qkMsACv` | 1 | 0.0746 |

**pass@3 = 3/3. G42 is development-only and is not part of the final suite.** Total spend $0.1844.

## Why it was solved

The risk was written down before the baseline ran, in §6 of `design.md`: the hardest step —
recognising which rows are hours worked — is *stated plainly in a policy document*, so once both
documents are read, execution is a filter plus a groupby. That is what happened, in all three trials,
at a median cost of six cents.

The wrong-object panel was not wrong: twelve constructions each move the rate materially, and a model
that missed any of them would have failed. The model missed none of them, because each one is written
down. Separation of wrong answers is necessary for a benchmark task and is **not** sufficient: the
information that distinguishes the right object from the wrong ones has to be something the analyst
must *derive*, not something the documents state.

## What this changes

This is the cleanest evidence in the project for the recognition-versus-execution principle, and it
sharpens it into a rule used for the remaining builds (principle 17 in
`research/benchmark_hypothesis.md`): **a task whose object is fully determined by rules written in the
workspace is a reading task, and this model class passes reading tasks.** The tasks this model does not
pass are those where the object has to be identified from the structure of the data-generating
situation (Task02, G05, G10, G24, G34) or where the execution is genuinely hard once identified (G41).

G42 stays in the repository as development evidence: it is a well-built task with a valid Oracle, a
clean mutation suite and an honest 3/3, and it is reported as such.
