# Environment validation and scientific red-team findings

## Environment validation

| check | method | result |
|---|---|---|
| extract reproducibility | build each image twice, the second with `--no-cache`, and digest every row of every table | **identical**: P22 `0ddb25a0799f1be0`, P20 `9540a0115be159bb`, P31 `5065cf4081dce124` |
| deterministic grading | `test_rerun_is_deterministic` runs the pipeline twice on the same database and compares both output files byte for byte | passes in all three Oracle runs |
| the extract is not modified | `test_database_unmodified` regenerates the visible extract and compares digests | passes |
| artefact permissions | the verifier `chown`s `/workspace` to 65534, sets `/tests` to mode 700, and **refuses to grade** if the pipeline user can read `/tests/world.py` | 0 refusals across all Oracle and Nop runs, i.e. the protection held |
| runtime integrity | `sha256sum -c runtime_manifest.sha256` over the interpreter, standard library and sandbox tools, plus a check that nothing was added to the standard library and no start-up hook or pytest configuration file exists | 0 refusals |
| dependency isolation | the verifier builds a fresh venv with `python -I -S -m venv`, then installs from hash-pinned wheels shipped in `tests/wheels` with `--no-index --require-hashes` and `PIP_CONFIG_FILE=/dev/null` | passes; the analytics interpreter the pipeline uses is the image's, unprivileged |
| unprivileged execution | the agent's pipeline runs via `setpriv --reuid=65534 --regid=65534 --clear-groups` | passes |
| resource limits do not bind | whole-trial wall clock, including the verifier regenerating and grading four extracts | **P22 32 s, P20 1 m 42 s, P31 34 s** against agent and verifier timeouts of 5,400 s each |
| hidden specs excluded from the image | `environment/build/` contains only `world.py`; `scenarios.py` lives in `tests/` and the final image stage copies only `/workspace` | verified by `validate_phase3.sh` §4 |
| secret scan | `scripts/secret_scan.sh` | no findings |

## Red-team findings

Acting as a sceptical external reviewer, with the evidence for each answer.

**Could the agent solve this by reading one document?** No. P22's calibration certificate is the obvious
candidate and is deliberately non-diagnostic: mutation M02 reads it and scales it by the length ratio, and scores
0 (its error is 0.5–2.2 µm against a 1.2 µm tolerance, failing on 3 of 4 extracts). P20's standard requires a
policy-invariant population and names none. P31's agreement settles the definition but not the arithmetic, the
tail, the ticket reconciliation or Schedule 4.

**Could a sophisticated but wrong analysis pass?** 45 mutations across the three tasks, each a single plausible
scientific defect, and **0 unexpected passes**. The sharpest are P22 M06 (correct rate, whole change credited to
material, correct decision) and P20 M12 (the vendor's own account), which score 0 while failing only
`quantitative_results` — the phase-1 G24 failure mode now visible.

**Could a legitimate alternative fail?** M00 in each suite is a different legitimate route and scores 1. For P22
all four accepted routes were measured: worst deviation from the design value is 0.75 µm on the offset (tolerance
1.2) and 0.47 pp on the corrected rate (tolerance 0.7).

**Is the intended object identifiable?** Two quantities were removed for failing this: P22's absolute operator
shift (only contrasts are identifiable) and any P20 model the agent trains itself (model-class dependent). P31
grades a **range** where Schedule 4 is unexecuted rather than a point estimate.

**Does the falsification route genuinely distinguish the hypotheses?** Recorded with predicted and actual
outcomes in `audits.md`. Each route's outcome differs by hypothesis, the evidence is in the agent's workspace,
and on P20's hidden_a the same route comes out the *other* way — which is what makes it a test rather than a
signpost.

**Is the final decision consequential?** It changes across extracts in all three tasks: P22 escalate vs not on
hidden_b; P20 three different actions; P31 three different verdicts.

**Could a model succeed by always challenging, or always defending, the incumbent?** Tested directly as P31 M07,
M09 and M08. All three score 0, each failing only `decision`.

**Are we grading the scientific result or matching the reference implementation?** The truth is computed from the
generator's own objects; the reference solution computes from the shipped SQLite through SQL joins, its own AUC
implementation and its own as-of reconstruction. They agree because both correctly compute well-defined
quantities, and a *different* implementation of the same definition (M00) also passes. The one shared definition
is the scoring formula in P20, which is **published in the model registry**, so any correct implementation must
match it.

**Is this professional work or an elaborate puzzle?** Each mechanism is a documented practitioner failure
structure: gauge bias after recalibration, performativity in a deployed risk model, and a
retailer-versus-supplier metric-definition dispute. The artefacts are the ones those seats actually hold.

## Residual weaknesses, disclosed

1. **P31's date-window commitment is weakly graded.** The window change moves the category rate by only 0.03 pp,
   inside the 0.15 pp tolerance, so mutation M05 is not caught by `scientific_object`; it is caught by
   `estimator_implementation` and `quantitative_results` through the account-level rates and the CSV. The
   commitment is therefore graded indirectly rather than directly.
2. **P20's contract partially hints at the shape of the answer** by requiring an `evaluation_population` field.
   It does not say which population, and the chain from there is three steps (contract → MRM-04 §4.1 → the
   policy configuration), but an agent is told that the population is a choice it must make.
3. **P22's stratum breakdown could be produced without understanding it.** The four strata are descriptive and
   cheap to compute; they are graded under `evidence_reconstruction` precisely because they are not the
   scientific work. The science is graded by criteria 2, 3 and 5.
4. **No adversarial exploit agent was run.** No suitable non-target-model agent was available and running a
   target model is forbidden this phase. The hand-written exploit probes are a weaker substitute and are
   labelled as such.
5. **No human expert baseline and no independent re-solve.** Oracle = 1 proves a solution exists; it does not
   prove a competent practitioner finds it from the instruction alone. The phase-2 handoff identifies this as the
   only instrument that separates "hard" from "under-specified", and it has not been run.
6. **P20's hidden_a margin is the thinnest in the suite** at 0.036 AUC below the retention floor, against a
   graded tolerance of 0.02. It is a 1.8× margin, which is adequate but is the least comfortable figure here.
7. **Single author.** Every specification, generator, verifier and mutation in this phase was written by one
   author, so the ambiguity audit's "two independent readers" requirement is met only in the weak sense that the
   verifier and the reference solution were derived separately from the written specification.
