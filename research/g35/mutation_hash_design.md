# G35 mutation-suite design rules  (from the G34 defect)

G34's validation shipped two defective mutations: `M21_oldest_cohort` was byte-identical to
`M00_oracle_equivalent` (the intended restriction was never generated, so "M21 passes" meant "the
oracle passes under another name"), and `M04_crude_for_q2` duplicated `M01_correctQ1_wrongQ2`.
Neither mis-graded anything, but apparent coverage was inflated by two and both were found by hashing
files, not by the suite.

**A mutation that fails to mutate reports a pass and looks like good news.**

## Rules, to be built into G35's validation from the start

1. **Hash every generated mutation.**  Record `sha256` of each emitted file in the suite's manifest.
2. **Fail the validation script on unexpected duplicate hashes.**  Equivalence must be declared in
   advance (`EXPECTED_EQUIVALENT = {...}`) or it is an error, not a curiosity.
3. **Diff each mutation against its source.**  Assert the diff is non-empty and that the intended
   token actually appears - e.g. `M_unweighted` must contain the unweighted mean call, and must *not*
   contain the demand-weight expression.
4. **Assert the semantic change, not just the textual one.**  Each mutation declares the graded
   quantity it is meant to corrupt; the harness asserts that quantity moves by at least a stated
   minimum on at least one fixture.  A mutation that changes code but not any graded number is as
   useless as one that changes nothing.
5. **Declare and verify the expected failing checks.**  Each mutation records which checks it should
   fail.  If it fails a different set, the suite reports a mismatch rather than a pass.
6. **Every valid-variation control must also be verified to differ from the oracle** - the specific
   defect that produced G34's phantom M21.
7. **Report the count of *distinct* cases**, never the count of files.

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
