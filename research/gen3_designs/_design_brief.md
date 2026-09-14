# Brief for generation-3 detailed designs

This brief is for the authors of `research/gen3_designs/*.md`. Read it fully before writing.

## Context

ForensicDS is a Harbor benchmark of long-horizon, real-world data-science incident environments for frontier data
agents.

### What a built task looks like

Each built task contains:

- `instruction.md`: a stakeholder memo stating the symptom and the required outputs. It does not state the root cause.
- An agent-visible `/workspace`: a realistic repository plus data, docs, notes, logs, notebooks and reports.
- A deterministic standard-library world generator. It is deleted from the image and copied into `tests/`.
- A verifier (`tests/`). It:
  - re-runs the agent's pipeline as an unprivileged user that cannot read `/tests`;
  - compares with an independent reference or with generator ground truth;
  - runs the same command on 3 hidden extracts that vary documented mechanisms only;
  - gives a binary reward.
- An oracle solution, plus a mutation suite: Nop, Oracle, independent correct implementations, shortcuts, and
  visible-pass/hidden-fail overfits.

### Model evidence so far (Gemini 3 Flash, 3 trials per task)

| Task | Result | Why |
|---|---|---|
| 01 entity-grain revenue | 2/3 | — |
| 02 temporal leakage in renewal model | **0/3** | The invariant had to be reconstructed per example × cutoff across several feature families. The natural implementation used the wrong state grain. |
| 03 evaluation population | 3/3 | Invariant documented; scaffolding in faulty code |
| 04 retention semantic layer | 1/3 | Headroom came only from a trusted-number attractor |
| 05 experiment unit | 3/3 | Invariant documented; scaffolding in faulty code |
| 06 usage statement close | 3/3 | See below |

**Why Task 06 was too easy:**

- the target cutoff was already implemented in the faulty code;
- the adjustment summary was already implemented;
- the natural group/merge/subtract design was correct;
- attractor evidence was optional;
- traps targeted implementation paths no agent chose;
- one customer's line-level check was enough.

Read `research/task06_gemini_analysis.md` and `research/cross_task_gemini_analysis.md` for the detailed evidence.

## The central rule

**If the natural implementation path is also the correct one, the design is not hard enough.**

Design so that, after an agent recognises the failure class, the most obvious repair is wrong for a *principled*
data-science reason. Several reasonable approaches should be wrong.

## Mandatory hardness properties (satisfy most)

| | Property | Requirement |
|---|---|---|
| A | Multiple hypotheses | At least 3 plausible hypotheses, at least 2 supported by some real evidence; the correct one requires active reconciliation. |
| B | Distributed semantics | No single document states the full invariant. |
| C | No helper-code answer | Faulty code contains no target cutoffs or helpers, no nearly-correct branches, no unused oracle-like code, no fix comments, and not all necessary constants. |
| D | Natural wrong implementation | Stated explicitly and concretely. |
| E | Multiple grains/states | Mistakes between them matter. |
| F | Interacting failures | Two mechanisms interact, where realistic. |
| G | Plausible aggregates | Several wrong repairs give believable headline numbers. |
| H | Row/state validation required | Correctness needs row- or state-level checks. |
| I | Multi-component repair | Only when natural. |
| J | Attractor must matter | Tempting evidence lies on the path the agent must take, not in optional files. |
| K | Heterogeneous environment | SQLite/DuckDB, CSV/Parquet/JSONL, SQL, Python, notebooks, YAML, logs, model metadata, docs — but only artifacts that belong in the workflow. |

**Do not create difficulty with:** huge irrelevant trees, trivia, arbitrary ambiguity, confusing names, broken tools,
undocumented requirements, or verifier tricks.

**Do not over-document the invariant.** Your design document states the oracle truth. The agent-facing environment may
contain *facts* (system behaviour, contract terms, schemas, logs), but must not contain a paragraph that translates
directly into the correct code. For every agent-facing document you plan, say what it contains and why it does not give
the answer away.

## Verifier philosophy

- Grade behaviour and state, not code style.
- Where a statistical estimator is involved, prefer grading against generator ground truth with a principled tolerance.
  Examples: the true treatment effect, the true policy value, true demand, true relevance. Any valid method then passes
  while naive methods fail.
- If you grade against one reference estimator, justify why the estimator is uniquely implied by the evidence.
- Use deterministic tables (labels, cohorts, clusters, allocations, episodes, parity tables) wherever the invariant is
  deterministic.
- Hidden fixtures may change calendars, rates, magnitudes and which documented mechanism dominates. They must not
  introduce a rule absent from the visible workspace.
- Name every hidden-fixture/overfit pairing.

## Required sections (use these headings, numbered)

1. Research question
2. Enterprise setting
3. Visible symptom (what the instruction memo says; it must not name the cause)
4. Source distribution inspiration (the real-world practice this mirrors; do not invent citations; mark "to verify" if you mention literature)
5. Causal graph / ground truth (generator mechanisms with concrete parameters)
6. Latent statistical/business invariant (oracle truth, precise)
7. Grains and state variables
8. Evidence graph (artifact → what it shows; mark which are on the natural path)
9. Evidence authority hierarchy (conflicts and which governs, with justification)
10. Plausible hypotheses (at least 3; evidence for and against each)
11. Why each wrong hypothesis is plausible
12. Investigation path (expected sequence; 30–80 actions; where discoveries happen)
13. Natural wrong implementation (concrete code-level description, and what it gets wrong numerically)
14. Second-order failure modes (the next wrong repairs after the first is rejected)
15. Correct repair properties
16. Repair surfaces (files/components and why each must change)
17. Validation requirements (what an agent must check to be confident; which checks aggregates cannot replace)
18. Hidden fixture strategy (3 fixtures: invariant tested, surface change, overfit caught, why same distribution)
19. Mutation strategy (named mutations with expected outcomes: controls, shortcuts, partial fixes, overfits, cheat)
20. Alternative valid implementations (and how the verifier accepts them)
21. Verifier design (checks, tolerances, determinism, ground truth vs reference)
22. Answer-key leakage audit (for every artifact: could it be transcribed or matched?)
23. Underspecification audit (every ambiguity you can find and how evidence resolves it)
24. Expected trajectory length (and why)
25. Why harder than Tasks 03/05/06 (be concrete against the Task 06 failure list)
26. Comparison with Task 02
27. Benchmark risks (implementation cost, realism, gradability, overlap, headroom risk)

Also include at the top a short **"Workspace sketch"**: a file tree with a one-line purpose per file and the data sizes.

## Style and length

- Be concrete: schemas, column names, generator parameters, example numbers, faulty code behaviour.
- Target roughly 2,500–4,500 words per design.
- Be honest about risks. A design that is probably too easy or underspecified should say so.
- No invented citations or claims about real companies.
- Write only into `research/gen3_designs/<file named in research/gen3_scoring.md>`.
- Do not modify any other file.
