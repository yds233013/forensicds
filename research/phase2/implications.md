# Phase 2 — training implications, alignment, and what we still do not know

## Training-data implication (exploratory; no result is claimed)

If H1 survives prospective validation, the artefact the project produces is unusual: a **labelled
epistemic trajectory** rather than a problem–answer pair. Each frozen task can emit

```
evidence → hypotheses entertained → the object committed to → the checks run (L1/L2/L3)
        → the discriminating test available → whether it was run → the contradiction encountered
        → whether the interpretation was revised → the corrected analysis → independent validation
        → the decision
```

with the *correct* path known because the world is simulated, and the *taken* path recorded because the
trajectory is logged. Two things this could plausibly support, stated as possibilities:

1. **Process-level supervision for an epistemic behaviour rather than an arithmetic one.** Existing
   process-reward work supervises steps of a derivation; here the supervisable step is "did you obtain
   evidence that could have refuted you". Whether a reward model can learn that is an open question.
2. **Counterfactual pairs at the commitment point.** Because the world is a generator, the same incident
   can be emitted with the discriminating evidence present or absent, and with the wrong interpretation
   true or false. That yields matched pairs in which the *only* difference is whether testing would have
   paid — the natural training signal for "test when it discriminates", as opposed to "always test",
   which is a cost.

**What we must not claim.** We have not trained anything, have not shown that failure-aware trajectories
improve any model, and have no evidence that supervising this behaviour generalises. The honest statement
is that the benchmark produces the *kind* of data such an experiment would need, and that the experiment
is not part of this project.

## Abundant alignment

| requirement | how this phase answers it |
|---|---|
| **narrow slice** | one capability — discriminating-evidence selection under competing interpretations — defined without reference to any model's behaviour, with a four-part admission test that rejects tasks failing it (four of the phase-1 pilot tasks would have been rejected) |
| **real distribution** | 30 candidates across ~17 professional domains, each traced to a documented practitioner failure structure rather than invented; three enterprise worlds so the artefacts are organisational rather than puzzle-shaped |
| **headroom** | headroom is *designed* rather than discovered: the separation, decision-margin and stated-object gates are model-free, and the phase-1 evidence shows they predict difficulty (five stated-object tasks solved, four derived-object tasks not) |
| **curation** | 30 candidates → scored on 12 design dimensions → 10 → 6, with rejections recorded and one displacement explicitly attributed to the diversity constraint rather than to score |
| **1,000-task scaling** | a generative signature with named cardinalities, an anti-clone rule that operates on mechanism × object class × discriminating-test class, and an expert workflow with the measured cost basis from phase 1 (engineering cost per task fell ≈2.5× once the harness was reusable) |
| **failure analysis** | the phase-1 audit already corrected its own headline claim; this phase pre-registers six predictions with disconfirming outcomes and eight rival hypotheses with discriminators |

## Uncertainties

1. Whether H1 survives at all, and whether it survives on a second model family.
2. Whether "discriminating test available and cheap" can be operationalised consistently by a second
   author, or whether it is an author-dependent judgement.
3. Whether the decision-margin gate can be satisfied without making tasks feel knife-edge — phase 1 shows
   both failure modes (too wide: the decision survives everything; too narrow: the task grades precision).
4. Whether three commitments per task is achievable without artificial stacking; the first build will tell.
5. Whether world-level artefacts help or leak: a shared world could let an agent learn the world's habits
   in a way that substitutes for reasoning.
6. Whether a human expert baseline is affordable, and without one, whether any claim about professional
   difficulty is defensible.
7. Whether grading a *diagnostic* (the A3 condition) can be done without prescribing a method.
8. How much of the phase-1 "no falsification" result is disposition and how much is the framing of our own
   instructions (rival A8) — untested.

## Recommended build order (build nothing yet)

1. **P22 (gauge recalibration)** first. Cheapest world (one plant, one instrument), a physical bridge that
   makes the ground truth unarguable, low ambiguity, and it tests the H1 loop with an *elementary* method —
   which separates H1 from rival A6 (domain knowledge) better than any other candidate.
2. **P20 (no-show model)** second. The strongest single test of H1: the naive action is the industry's
   standard remedy, and the correct action is to *not* act. Also the natural host for the A3
   (falsification-as-deliverable) paired condition.
3. **P27 (roster)** third. Carries the constrained-optimisation dimension the final five lack, and its
   independent rules engine is the cleanest discriminating artefact in the set.
4. **P13 (limit increase)** fourth — highest scientific depth, but the most expensive world to author.
5. **P02 (elasticity)** fifth.
6. **P07 (unit economics)** sixth.

Rationale for the order: start where the ground truth is least arguable and the world is cheapest, and
place the two tasks that most sharply discriminate H1 from its rivals (P22 for A6, P20 for A1/A3) before
the expensive ones.
