# Phase 2 — the research gap and the proposed contribution

## What the field already measures well

| capability | who measures it | where it stands |
|---|---|---|
| execution-grounded analytics over heterogeneous artefacts | DataSpace, Spider 2.0, DAB, KramaBench, DABstep | best 66 % (DataSpace), 0.38 pass@1 (DAB), 14.55 % on DABstep's hardest tier |
| long-horizon ML engineering | MLE-bench and lineage | leaderboard 64 % medals (submissions paused) |
| statistical method selection as a labelled choice | StatQA, QRData | GPT-4o 64.8 % (StatQA); GPT-4 46.8 % on QRData's causal split |
| identification-spec grading | CausalReasoningBenchmark, CausalDS, CausalVerify (all 2026) | full identification spec 34.1 %; ATE interval coverage collapsing to 20–71 % |
| latent-world grading | AvalancheBench, CausalDS, CausalGame, Era by Eon, TraceBench | 25.9 % of rubric recovered (AvalancheBench) |
| executed falsification with error control | Popper (alone) | Type-I ≈ α, power 0.58–0.64 |
| reward-hacking measurement | BAITBENCH, CausalGame | 57.1 % of runs hack |
| software incident RCA | OpenRCA, ORCA-bench, CUJBench | 11.3 % / 25.3 % / 19.7 % |

## What nothing measures

1. **Diagnosing and repairing a specific flawed prior *analysis*, across stages, in an organisational
   setting.** BIRD-CRITIC repairs a *labelled-broken* SQL query; ELT-Bench builds a pipeline; OpenRCA
   diagnoses a software incident. No benchmark asks: here is a number an organisation already computed, a
   decision that rides on it, and a set of artefacts that includes the reasoning that produced it — is it
   right, and if not, why?
2. **Wrong-but-authoritative artefacts.** Every artefact in every reviewed benchmark is correct by
   construction. AvalancheBench states "No dashboards or misleading artifacts"; DAB supplies a hints file
   describing the transformations applied; BIRD supplies "Oracle Knowledge".
3. **Whether the agent obtains evidence that could refute its own interpretation**, in a professional
   setting with a decision attached. Popper does this for hypothesis validation on biomedical tables;
   CausalGame gives it two rubric points and finds 5–7 % uptake.
4. **"These data cannot answer that question; here is the experiment that would."** Scored in CausalDS and
   in one non-benchmark system (PyMC Labs' Decision Lab, which on an unidentifiable marketing-mix dataset
   returned *"No valid model found. Run a geo-holdout experiment."*). No data-agent benchmark scores it.
5. **A consequential business decision with a stated rule and threshold, graded alongside the quantities.**
   Absent everywhere reviewed.

## The proposed contribution, stated narrowly

> **A prospective test of whether frontier data-science agents can tell "my analysis is internally
> coherent" from "my scientific interpretation is valid", in production incidents where several
> interpretations are initially defensible, a discriminating test is available and cheap, and a named
> decision rides on the answer.**

Four things make it a contribution rather than another analytics benchmark:

1. **The incident architecture.** An incumbent artefact produces a specific number; the workspace contains
   the reasoning that produced it, the stakeholders who disagree about it, and the evidence that can
   adjudicate. This is the shape of the work and it is not represented in the literature.
2. **Discovery/validation separation.** The 15 measured tasks are the discovery set; the prospective set is
   frozen before any target-model contact, with six pre-registered predictions and eight rival hypotheses
   carrying explicit discriminators. No reviewed benchmark separates these, and several refine tasks after
   observing model failures.
3. **Layered validation as a graded object.** L1 coherence / L2 robustness / L3 falsification are
   distinguished by construction, the wrong route is designed to pass L1 and often L2, and the L3 route is
   present but never named. Two archetypes extend this: defer-or-overturn (P31) and identifiability-verdict
   (P32).
4. **Decision-linked grading of the quantities beneath the decision.** Justified empirically: 6 of 13
   phase-1 failures reached the right decision with wrong quantities, and on one task a decision-only grader
   would have scored 3/3 instead of 0/3.

## Honest positioning

This is **not** a claim to have measured a new capability yet; phase 1 is a discovery set and its own audit
corrected its headline. It is a claim that the *design* occupies territory the surveyed field leaves empty,
and that the prospective protocol can distinguish the project's preferred explanation from eight rivals.
The nearest relatives — AvalancheBench (latent-world recovery), CausalReasoningBenchmark (identification-spec
grading) and Popper (executed falsification) — each cover one axis; the combination, in an organisational
incident with a decision attached, is unoccupied.
