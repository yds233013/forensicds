# G35 mutation-suite design rules  (from the G34 defect)

G34's validation shipped two defective mutations: `M21_oldest_cohort` was byte-identical to
`M00_oracle_equivalent` (the intended restriction was never generated, so "M21 passes" meant "the
oracle passes under another name"), and `M04_crude_for_q2` duplicated `M01_correctQ1_wrongQ2`.
Neither mis-graded anything, but apparent coverage was inflated by two and both were found by hashing
files, not by the suite.

**A mutation that fails to mutate reports a pass and looks like good news.**

## Addendum, learned during G35 implementation

The rules below were written after G34 and they were still not enough. G35's first mutation suite
passed every distinctness check and was **completely vacuous**: the generator's template used
`{{`/`}}` brace escaping while the renderer used `str.replace` rather than `str.format`, so every
generated file contained a Python *set literal containing a dict* and crashed on import with
`TypeError: unhashable type: 'dict'`. All twenty-two wrong cases "scored 0" - for the wrong reason.

Two things hid it. The hash check proved the files *differed*; nothing proved they *ran*. And the
CSV runner grepped only for `FAILED`, silently discarding the ten `ERROR` lines that would have
exposed it at once. It surfaced only because the three legitimate routes also scored 0, which looked
like a benchmark defect and was actually a harness defect. Had every case been a wrong method, the
panel would have looked perfect and the task would have been frozen on evidence of nothing.

**Rule 4 below is the generalisation: a mutation that does not RUN is as useless as one that does
not mutate, and both look like success from the outside.**

## Rules, to be built into G35's validation from the start

1. **Hash every generated mutation.**  Record `sha256` of each emitted file in the suite's manifest.
2. **Fail the validation script on unexpected duplicate hashes.**  Equivalence must be declared in
   advance (`EXPECTED_EQUIVALENT = {...}`) or it is an error, not a curiosity.
3. **Diff each mutation against its source.**  Assert the diff is non-empty and that the intended
   token actually appears - e.g. `M_unweighted` must contain the unweighted mean call, and must *not*
   contain the demand-weight expression.
4. **Smoke-execute every mutation before writing it.** Run it against a small real extract and
   assert it emits every graded quantity as a number. Fail the generator otherwise. Report ERRORs
   separately from FAILUREs in any suite runner, so a crash can never be mistaken for a rejection.
5. **Assert the semantic change, not just the textual one.**  Each mutation declares the graded
   quantity it is meant to corrupt; the harness asserts that quantity moves by at least a stated
   minimum on at least one fixture.  A mutation that changes code but not any graded number is as
   useless as one that changes nothing.
6. **Declare and verify the expected failing checks.**  Each mutation records which checks it should
   fail.  If it fails a different set, the suite reports a mismatch rather than a pass.
7. **Every valid-variation control must also be verified to differ from the oracle** - the specific
   defect that produced G34's phantom M21.
8. **Report the count of *distinct* cases**, never the count of files.

## Applied to G35's known panel

| mutation family | graded quantity it must move | minimum movement |
|---|---|---|
| naive A/B as policy effect | Q1 | >= 0.05 on `hidden_a` |
| direct effect as policy effect | Q1 | >= 0.25 on `hidden_a` |
| total-at-50% as policy effect | Q1 | >= 0.02 on `visible` |
| unweighted block means | Q1 | >= 0.01 on `visible` |
| swap Q1 and Q2 | Q1 and Q2 | >= 0.25 on `visible` |
| spillover sign flipped | Q3 | >= 0.10 on `visible` |
| block FE direct effect | Q1 | >= 0.25 on `hidden_a` |

`W10 realised saturation` is explicitly **excluded** from the separation-carrying set: measured
movement is 0.000-0.015, below any defensible minimum.
