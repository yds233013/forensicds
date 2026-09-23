# Phase 2 — the proposed narrow slice, stated without reference to any model's behaviour

## The slice

> **Decision-grade analytics repair under competing interpretations.**
>
> An organisation already computes a number. A named decision with a stated rule rides on it. The number
> may be wrong — for a *scientific* reason rather than a crash — and the evidence available admits several
> defensible interpretations. The data scientist must reconstruct how the data came to exist, determine
> which evidence discriminates among the interpretations, obtain it, revise if it contradicts them, repair
> the pipeline, and make the decision defensibly.

The capability under test is one thing: **discriminating-evidence selection**. The professional
instantiation is deliberately broad — ~17 domains in the candidate pool — because a narrow capability
measured in one domain is indistinguishable from domain knowledge.

## Admission test (a task is in the slice only if all hold)

1. an **incumbent artefact** produces a specific number, and the reasoning that produced it is inspectable;
2. a **named decision with a stated rule and threshold** rides on that number;
3. the correct scientific object is **underdetermined by the workspace documents** — it must be derived from
   how the data came to exist, or from an optimisation no document solves;
4. **≥3 initially defensible interpretations**, at least one of which yields a coherent, plausible result
   that passes the organisation's normal checks;
5. **≥2 discriminating routes exist in the workspace**, neither named, each with a predicted outcome under
   each interpretation;
6. the answer is **deterministic given the extract**, and plausible wrong answers are separated from it by
   more than the reporting precision;
7. the **decision margin** is narrow enough that a wrong interpretation changes the decision on at least
   half the graded extracts;
8. **≥2 legitimate methods** reach the same graded quantities within tolerance.

## In scope

Tabular and semi-structured enterprise systems of record (warehouses, event logs, ledgers, landing zones,
instrument logs, decision logs with policy versions); an incumbent pipeline in Python or SQL that must be
repaired and re-run; heterogeneous supporting evidence including artefacts that are **authoritative and
wrong** *and* artefacts that are **authoritative and right**; causal, statistical, operational-research and
economic estimands; deterministic latent truth with hidden regimes; a decision rule with a threshold;
grading of the quantities beneath the decision as well as the decision; and — as two required archetypes per
world — one incident where the published number is **correct** and one where the honest deliverable is
**"not identifiable from these data; here is the design that would be"**.

## Out of scope

Leaderboard model training; unstructured or multimodal inputs as the primary object; visualisation;
open-ended "insight generation" needing an LLM judge; tasks whose correct object is stated in a document the
agent reads anyway; tasks whose decision margin is so wide that any moderate error preserves the decision;
tasks whose accepted answer family is narrower than the analysis they claim to test; and tasks where the
discriminating evidence is not present in the workspace.

## Why this slice and not a broader or narrower one

- **Narrower** ("estimand selection in causal inference") would exclude the two difficulty axes the project
  has actually demonstrated — execution-hard optimisation (phase-1 G41, where two of three trials named
  min-cost flow and implemented a greedy augmentation) and economic-object errors — and would make the
  benchmark a re-run of CausalReasoningBenchmark and CausalDS.
- **Broader** ("enterprise data science") admits documentation-lookup tasks; four of phase 1's twelve pilot
  tasks were exactly that, and three of them scored 3/3.
- **Defined by the failure mode** ("F9 tasks") would be circular, and phase 1's own audit showed the
  preferred failure label was over-counted by roughly double.
