# 11 — Research value, and scaling 10 → 1,000

Throughout: **COMPLETED** marks something this project actually did; **PROPOSED** marks a design that was
never executed.

## Why realistic data-science environments are worth building

Most agent evaluation asks *did the code run and did a metric improve?* The expensive failures in
professional data science are neither. They are failures to notice that the number being computed is not
the number the decision needs — and that error is **coherent**: the analysis runs, the diagnostics pass,
the interval is narrow, and the conclusion is wrong because the population, estimand, unit of
intervention, measuring instrument or observation process was not what the analyst assumed.

This project's evidence that such environments measure something real:

| observation | status |
|---|---|
| No valid trial produced non-executing work. Coding ability was never the binding constraint. | **COMPLETED**, chapter 08 |
| Agents read the governing document and reproduced the incumbent number, then failed downstream. | **COMPLETED**, chapters 07-08 |
| Stating the invariant outright did not produce a pass (`02…__explicit-invariant`, 0/3). | **COMPLETED** |
| On instrumented tasks, framing criteria sit near ceiling while the decision-relevant quantity is the floor. | **COMPLETED**, chapter 10 |
| In 7 instrumented trials the decision was right while the quantity was not. | **COMPLETED** (with the D1 qualification) |

And the honest counterweight: **5 of 9 tasks fell to one frontier model**. These environments discriminate
between model tiers today; they will not discriminate forever.

## Relationship to professional AI-agent evaluation

The benchmark's distinguishing properties, against the common alternatives:

| property | typical DS/ML benchmark | here |
|---|---|---|
| objective | a metric to maximise | a **decision** fixed by a document the agent is given |
| data | curated dataset | operational exhaust: joined, grainy, incomplete |
| a wrong answer already present | usually absent | **always present, and it executes** |
| generalisation | held-out split | **held-out *worlds* with different mechanisms** |
| credit | pass/fail | per-capability criteria (4 of 10 tasks) |

The third and fourth rows are the ones we would defend as contributions. An incumbent analysis that is a
correct computation of the wrong quantity cannot be solved by being a better programmer. A sibling world
in which a *different* mechanism dominates cannot be solved by a procedure that encodes the mechanism it
found — which is precisely what defeated all three `p22` Gemini trials.

## Scaling to 1,000 — the design

**The generative object is not the task.** It is the **(capability, mechanism, workflow)** triple, with the
task as one rendering. Reskinning a fixed world produces clones a model memorises; varying the mechanism
while holding the capability fixed produces genuinely distinct instances.

```
capability               (6)    the thing being measured
  × mechanism            (~12)  why the incumbent answer is the wrong quantity
  × professional workflow (~15) role · industry · decision · governing document
  × DGP parameterisation  (cont.) effect sizes, noise, selection strength
  × operational policy    (3-5) how the intervention or observation process changed
  × incumbent family      (4)   which plausible-but-wrong analysis is inherited
  × artifact surface      (3)   sqlite warehouse / CSV drop / notebook + parquet
  × sibling-world set     (5)   invariance · sensitivity · decision-flip ·
                                identification-removed · mechanism-strength
  × decision threshold    (3)   binding · far-from-binding · interval-dependent
```

### The anti-clone gate (the load-bearing idea) — **PROPOSED**

> An instance is admissible only if its reference solution produces the **wrong** answer on at least one
> other admissible instance.

This is computable — run instance A's reference against instance B's world — and it is exactly the property
that made the `p22` result observable. A cosmetic clone fails it by construction. **Without this gate,
"1,000 tasks" means 10 tasks in 100 costumes.**

### Capability axes to hold fixed while varying everything else

1. evidence lineage reconstruction
2. population / eligibility determination
3. scientific-object (estimand) selection
4. identification under a stated design
5. revision after contradiction, and propagation of that revision downstream
6. mapping a quantity to a written decision rule

### Mechanism templates, prioritised by what this project's evidence says is missing

1. **Identification-removed / justified deferral.** **Status corrected:** `p31` already implements one
   (`tests/world.py:300`, `readout_contract.md:42`) and **both models failed to produce the deferral**.
   The priority is therefore to *replicate* it across tasks, not to invent it.
2. **Two-revision chains.** Discover leakage → remove the feature → the model still looks strong →
   discover the evaluation population is itself selected → revise again. Current tasks force at most one
   pivot.
3. **Mechanism-swap siblings for every task.** `p22` shows this is what detects procedure-level
   overfitting. Every generated task should ship at least one world where a *different* named cause
   dominates.
4. **Delayed + selectively observed labels** (fraud, credit, clinical).
5. **Competing risks / wrong statistical object** — the `g34` mechanism, excluded for being too easy at
   flash tier; worth regenerating harder.

### Pipeline, with the gate that this project learned the hard way

| stage | what runs | gate |
|---|---|---|
| 1 specify | sample a triple; **write the dependency graph first** | ≥8 nodes, ≥1 branch with two professionally motivated hypotheses |
| 2 generate | seeded DGP, warehouse, operational artefacts, incumbent analysis, governing document | incumbent executes and reproduces its published number |
| 3 reference | reference solution + sibling worlds | reference passes on all worlds; incumbent fails on ≥1 |
| 4 **cross-check** | run every other instance's reference against this world | ≥1 foreign reference fails → distinct, not a clone |
| 5 adversarial | Oracle=1, Nop=0, mutation and malformed-output suites | 100% of mutations rejected; 0 grader exploits |
| 6 **scaffolded dry-run** | one trial per target scaffold, checking only that the verifier **graded** rather than refused | **mandatory** — see below |
| 7 contamination | search public sources for artefact names and numbers | no hit |
| 8 calibrate | 3 trials on each target model | keep if pass@3 < 0.3; retire above 0.7 |
| 9 expert review | a human reads the dependency graph and the incumbent | "a professional could have written this incumbent" |
| 10 freeze | five hash groups, then expose | any post-exposure change forks a new version |

**Stage 6 exists because of two real defects.** `g50` survived 63 adversarial submissions and was then
refused outright by the first real agent run (**D4**), because `oracle` and `nop` install nothing while
every real scaffold installs its own tooling. The same class of failure then blocked the entire Claude arm
on `g50` (**D5**), and it is still unresolved. **A verifier validated only against `oracle`/`nop` has not
been validated.**

Stages 2-7 are automatable; **stage 9 is the throughput limit** at roughly 30 minutes of expert time per
instance, i.e. ~500 expert-hours for 1,000 instances.

### Provenance and distribution design — **PROPOSED**

Every instance carries the ten-field provenance record used here, with the documented/unverified split
chapter 01 applies. Distribution monitored on three axes simultaneously — capability, mechanism, industry
— so that retirement does not silently empty one axis. Retire an instance when pass@3 exceeds 0.7 on the
frontier model; **by that rule 5 of the current 9 gradable tasks are already at or near retirement for
`claude-opus-5-5`.**

### Contamination control — **PROPOSED**

All data synthetic and seeded, so no real record can leak. The residual risks are (i) the *task text*
entering training corpora, and (ii) the mechanism being so canonical that a model recognises the setup.
Mitigations: a canary string per task; periodic re-generation under fresh seeds and fresh surface names;
and tracking pass-rate jumps that coincide with model releases rather than with task changes.

**A real finding on canaries from this project:** `g50`'s canary lives in `tests/test.sh`, which the agent
never sees — so it cannot detect instruction leakage at all. A canary belongs in `instruction.md`.

## Training reward and held-out evaluation

**The honest limit, stated plainly: Harbor verifies final state and does not supervise process.** A reward
of 1 reinforces whatever trajectory produced a correct final artifact, including a lucky one. **We do not
claim these tasks provide process supervision, and a naive RL loop on the binary reward would be a weak
signal.**

Three properties make them usable anyway:

1. **Criterion vectors are dense and honest.** Chapter 08 shows the criteria dissociate into 11 distinct
   failure shapes — that is a per-capability reward vector, not a scalar, and it localises credit without
   process labels.
2. **Sibling-world re-execution turns a generalisation property into a terminal reward.** `g50`'s verifier
   rewards a *procedure* that works on five unseen worlds. This is the closest thing to process
   supervision obtainable from final-state verification, and it targets the failure `p22` measured.
3. **The dependency graphs are ready-made process labels**, written before the tasks and held out of the
   agent's context (`TASK_DEPENDENCY_MAPS.md`).

**Held-out evaluation design — PROPOSED.** Hold out whole *(mechanism, workflow)* cells, not instances.
Training on 800 instances that include `p22`-style measurement-bias tasks and evaluating on a held-out
measurement-bias cell in a different industry tests transfer of the capability; holding out random
instances tests memorisation of surface detail.

**Behaviours training would plausibly improve**, in the order the evidence supports:

1. writing a *mechanism-recovering* procedure rather than a mechanism-specific one (the `p22` failure);
2. carrying a correct diagnosis through to a correct quantitative reconstruction (the modal failure);
3. propagating a revision into every downstream quantity, not only the one that triggered it;
4. declining when the evidence does not identify the target (`p31`'s deferral world, which **neither model
   produced**).

**Strongest seeds:** `g50` (reward already encodes generalisation), `p22` (cleanest mechanism-swap),
`p20` (densest criterion vector), `g10` (revision must propagate into the decision), `p31` (spec-reading
over metric-chasing, plus deferral). **Weakest:** `g36` and `g08` — largely single-step once identified,
so little internal structure to shape behaviour with.
