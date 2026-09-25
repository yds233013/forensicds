# Three-month plan

13 weeks at 30–40 h/week. The plan is feasible for one reason: the hardest infrastructure already exists and has
been run end to end. What the fellowship buys is expert labour, model breadth, and the independent authorship that
the existing pilot conspicuously lacks.

## What already exists (built and exercised, not planned)

| component | state |
|---|---|
| parameterised world generator producing a visible instance + hidden siblings from one corpus | working, three worlds |
| verifier that re-executes the agent's submitted pipeline against each regenerated sibling and emits per-criterion rewards | working, frozen |
| defect-injection harness over a reference analysis | working, 45 defects |
| freeze / digest-pinning / hash-pinned offline install / pre-registered analysis plan | used for a real exposure run |
| an executed prospective evaluation under that protocol | 9/9 valid trials, zero protocol violations, $1.47 |
| the visible-versus-family calibration | computed: 30/42 visible, 10/42 family-only, 2/42 neither |

This is roughly the engineering that would otherwise consume the first six weeks.

## Schedule

**Weeks 1–2 — specification and the reference family.**
Write the family specification format (corpus + parameter vector + sibling expectations + tolerances). Port the
existing generator and verifier to it. Build **family 1** end to end as the reference implementation, including all
8 siblings and the reference analysis. Recruit the expert panel and brief the three independent roles
(sibling adjudicators, rubric authors, defect authors) so that none of them ever sees the others' material.
*Gate: family 1's reference analysis passes 8/8 and the degraded-oracle control fails the family.*

**Weeks 3–6 — author families 2–6.**
One family per week with the sixth week as slack, each on a different mechanism class. Expert adjudication of flip
and identification-removed siblings runs in parallel and continuously, not in a batch at the end — a sibling that
two experts do not agree on is discarded that week, not in month 3. Leak check and seed-only control per family.
*Gate at week 6: at least 5 valid families, each with ≥2 validated flip siblings — a floor, not a target of eight.
Fewer than 5 means the model study narrows rather than the adjudication standard loosening. **The discard rate is
recorded per family and reported as a finding**, because it is the number a future benchmark team needs in order to
budget this.*

**Week 6 — freeze and pre-register.**
Freeze corpora, generators, seeds, verifiers, tolerances and sibling expectations. Hash and commit the analysis
plan with all four hypotheses, the Δ ≥ 10 pp decision rule, the composition threshold and the multiplicity
correction. **Nothing after this point may change a tolerance or an expectation.** This is the protocol the pilot
already ran under.

**Weeks 7–8 — E1, the model-free primary experiment.**
150 defects authored by experts who did not author the worlds. Two independent expert rubrics per family, written
against the visible sibling only. Run all three instruments over the defect bank: visible-instance grading, visible
rubric grading, family grading. Compute Δ with the cluster bootstrap.
*This is the experiment that can end the project, and it happens before the expensive one.* **Gate: if Δ < 10 pp,
stop the model study as designed and pivot the remaining five weeks to reporting the negative result properly —
which is a publishable methodological finding about the sufficiency of expert rubrics and a direct answer to a
question APEX has an interest in.*

**Weeks 9–10 — E2 and E3, the model study.**
180 primary rollouts (6 models × 6 families × 5) and 162 fresh-rollout runs for the replay-validity arm. Sibling
gradings are compute-only. Expert baseline solves collected in parallel.

**Week 11 — ablations, controls, failure coding.**
Sibling-count curve, sibling-type ablation, tolerance sensitivity, judge-with-trajectory arm. Two independent
experts code every family-only failure; κ reported. All five controls re-verified against the final data.

**Weeks 11–12, in parallel — the accounting transfer probe (committed).**
Two weeks, scoped to a yes/no engineering question: can a family be authored from an existing trap register? Uses
APEX-Accounting's public dev-set world. Deliverable is one family plus a written account of what the trap register
did and did not supply. **Accounting is the intended application** — the corpus, the world architecture and the
enumerated mechanisms already exist there — so this is the bridge from the validation domain to the applied one and
is not droppable slack. If week 11 overruns, the fresh-rollout arm narrows to two families first.

**Week 13 — deliverables.**
Paper draft; released generator, families, defect bank, rubrics and adjudication records; the family verifier
implemented against Archipelago's verifier interface with its `trajectory`/`value` conventions respected.

## Budget

**Expert labour ≈ 30 expert-days**, the dominant cost:

| role | volume | estimate |
|---|---|---|
| family authoring review | 6 families × 2 days | 12 days |
| sibling adjudication (blind, 2 experts) | ~48 siblings × 0.5 h × 2 | 6 days |
| rubric authoring (2 independent per family) | 6 × 4 h × 2 | 6 days |
| defect authoring | 150 × 20 min | 6 days |
| expert baseline solves | 12 solves | 4 days |
| failure coding | ~40 cases × 0.5 h × 2 | 3 days |

Discarded siblings and re-adjudication are budgeted at 20 % on top. Roles are kept disjoint by design; an expert
who authored a family may not adjudicate, rubric or defect it.

**Compute and model spend ≈ $1,000–2,000.** 342 rollouts at an allowance of $3 for frontier long-horizon agents;
1,440 sibling gradings cost CPU seconds. The pilot's nine rollouts with four worlds each cost $1.4667 total, which
is the measured basis for this estimate.

## Risks, and what happens

| risk | probability | response |
|---|---|---|
| flip siblings fail expert adjudication at a high rate | medium | the discard rate is itself a reported finding about how hard it is to construct decision-flipping variants; the model study narrows to validated families |
| Δ < 10 pp — expert rubrics are sufficient | **real, and the point of the week-8 gate** | report the negative result; it answers a question Mercor has an operational interest in |
| fresh rollouts succeed where replay fails (H3 null) | medium | the metric survives, the interpretation changes to artifact brittleness, and the paper says so in the abstract |
| six families is too few for the Δ CI | high | acknowledged in the design; the deliverable is the generator that makes family 7 cheap |
| a frontier vendor's agent harness is unavailable | low | the model sample is specified as ≥4 developers, not as named models |
| authoring runs long | medium | the fresh-rollout arm narrows to 2 families first, then the model count to 4; the transfer probe is no longer the first thing to drop |

## The authoring-rate assumption, and its weakness

The one-family-per-week rate is the plan's load-bearing assumption and it deserves to be stated with its evidence.
The pilot's three parameterised families, their verifiers and 45 defect suites were built and frozen inside a single
implementation phase — days, not weeks — but by one author with heavy tooling assistance and no external adjudication,
which is the easy case. **The plan therefore assumes expert review, not engineering, is the bottleneck.** That
assumption may be wrong in either direction, and the week-6 gate accepts five families rather than six because of it.

## What is deliberately not in the plan

**Six families is not a benchmark and the deliverable is not claimed to be one.** What ships is a method, a generator,
a specification format, a family verifier against Archipelago's interface, and the evidence about whether the
instrument detects anything that cheaper instruments do not. Six families is the sample size for that claim. Making it
a benchmark is the follow-on, and it is cheap precisely because the generator exists.

No second full domain. No website. No leaderboard. No public release before the results are written up. No claim about
real enterprise data, which the method's generative-authoring requirement forbids.
