# Phase 2 — benchmark review (external, verified against primary sources)

Provenance note: arXiv identifiers below were checked against arxiv.org. Where a figure is quoted it was
read from the paper or an official leaderboard. Items that could not be verified are marked UNVERIFIED
and are not used to support any claim.

## The landscape

| benchmark | scale / format | grading | best reported | documented failure modes | what it does not test |
|---|---|---|---|---|---|
| **AvalancheBench** (arXiv:2605.24183) | 1 enterprise scenario, 18 rubric items; catalog + 23k transactions + 10k free-text reviews, no FK between them | rubric 0–5 per item, LLM judge; items **derived from a declared latent world Z** | 25.9 % of rubric (Snowflake CoCo as orchestrator) | generic segmentation (invents plausible segments); **merging two distinct temporal events into one**; "avalanche" error propagation | no wrong/misleading artifacts ("No dashboards or misleading artifacts"); no falsification; no estimand choice; no staged repair |
| **DataSpace / KDD Cup 2026** (arXiv:2608.03451) | 410 tasks, 7,439 artifacts, 15 GB; CSV/JSON/SQLite/MD/PDF/video | deterministic final-table comparison | Grok 4.5 66.34 % | of 136 best-model failures: **answer materialisation 52.2 %**, task intent 22.8 % | only the final table; no intermediate objects |
| **DAB** (arXiv:2603.20576) | 54 queries, 12 datasets, 4 DBMSs; ReAct + Docker | pass@k, substring/set match | Gemini-3-Pro 0.38 pass@1 (69 % @k=50) | over 1,147 annotated trajectories: **incorrect plan 40 %, incorrect implementation 45 %, incorrect data selection 15 %** | hands the agent a hints file describing the transformations applied — the opposite of a forensic setup |
| **DSAEval** (arXiv:2601.13591) | 641 problems, 285 datasets; 20-turn sessions, notebook + report | LLM judge, **0.3·reason + 0.3·code + 0.4·result** | Claude-Sonnet-4.5 8.164/10 | weakest on prediction/forecasting (5.86) and model training (6.33) | reasoning score is unanchored to a latent truth, so it measures articulated plausibility |
| **BLADE** (arXiv:2408.09667, EMNLP-F 2024) | 12 datasets/RQs, **536 ground-truth analysis decisions** from 11 experts | separate matchers for conceptual variables, transforms (data-flow-graph isomorphism) and models; **precision × coverage@k** | GPT-4o ReAct F1 44.8 | **expert–expert agreement 75 %/80 %; LM decisions match ground truth at 27 %/13 %**; model-with-correct-variables precision < 35 % | does not evaluate interpretation of results; single-table |
| **CausalReasoningBenchmark** (arXiv:2602.20571) | 173 queries, 132 real datasets, from 79 papers + 3 textbooks | grades a **structured identification spec field-by-field** *and* the estimate separately; bad-controls blacklist | GPT-5.3: **strategy 79.2 %, full identification spec 34.1 %** | control errors 39 missing / 18 post-treatment; **estimand confusion 46 (CATE→LATE in 29 of 44 RDD)** | — (authors: "the bottleneck … lies not in recognizing the broad category of research design, but in specifying its detailed components") |
| **CausalDS** (arXiv:2607.08093) | 953 SCM "scenes" + observation model with noisy proxies; 100-scene exam | grades identifiability, adjustment/forbidden sets, interval calibration, **abstention as first-class** | Claude Opus 4.8 82.4 % pass | **95 % ATE interval coverage collapses to 20–71 %**; frontier abstention accuracy 56–75 % | — |
| **Popper** (arXiv:2502.09858) | sequential falsification agent; TargetVal + DiscoveryBench | **executes falsification tests**; p→e-values, any-time-valid Type-I control | Type-I ≈ α; power 0.58–0.64; 9.7× faster than human experts | **misinterpreted p-values 35.9 %, ineffective falsification design 28.1 %, "test breaks implication" 17.2 %** | — |
| **CausalGame** (arXiv:2607.04293, ICML 2026 oral) | 14 SCM scenarios, agent-designed interventions, explore→commit | survival rate **plus** a rubric (causal reasoning 11 pts, experimental design 2) | Claude-Opus-4.5 68 % survival vs 78–85 % optimum | **only 5–7 % of sessions earn causal-reasoning credit**; component lock-in 74.4 %; reward hacking via leaked scenario IDs (+18.5 pts) | — |
| **BAITBENCH** (arXiv:2608.30724) | 3 synthetic tasks with planted shortcuts (entity-overlap leakage, near-duplicates, no-signal) | two-stage LLM judge, κ=0.872; public-vs-held-out gap as signal | — | **57.1 % of runs reward-hack**; anti-cheating prompting reduces it by only 6.21 pp | measures whether the agent *takes* the bait, not whether it *reports* it |
| **StatQA** (arXiv:**2406.07815**) | 11,623 examples, 78 tables | exact match on the (columns, methods) pair; no execution | GPT-4o 64.83 %; **human open-book 53.45 %** | **"LLMs primarily make applicability errors"** — right method family, assumptions unchecked | no execution, no estimand choice |
| **MLE-bench** (arXiv:2410.07095) | 75 Kaggle competitions, 24 h, submission.csv | Kaggle medal thresholds | leaderboard 64.44 % (submissions paused 2026-04) | "struggle to debug issues and recover from missteps"; **Known Issues list documents real target leakage treated as a defect to patch** | authors: "real-world AI R&D … may not even have a clear problem statement" |
| **KramaBench** (arXiv:2506.06541) | 104 tasks, 1,700 files, 24 sources | grades **pipeline design and per-sub-task implementation separately** | design 41.58 % vs implementation 19.75 % (GPT-o3) | 22 % of failures assume a user will clarify | — |
| **SCIRIGOR** (arXiv:2609.06192) | 100 cases, typed evidence graphs | scores claim-support paths; **localises the earliest unsupported relation** | 62.6 % soft / 18.0 % strict chain | **claims agree with faithful and unfaithful results at 91.8 % vs 91.0 %** | — |
| **OpenRCA** (ICLR 2025) / ORCA-bench (arXiv:2607.28545) / CUJBench (arXiv:2604.23455) | incident root-cause over 68 GB / live OTel telemetry / injected faults | JSON root cause; LLM judge + human re-scoring | **OpenRCA best 11.34 %**; ORCA-bench 25.3 % medium / 10.0 % hard; CUJBench 19.7 % | follow-up (arXiv:2602.09937) over 1,675 runs: **hallucinated data interpretation and incomplete exploration persist across all models**; "prompt engineering alone cannot resolve the dominant pitfalls" | software incidents, not scientific-object selection |
| gold-standard audits | Jin et al. (arXiv:2601.08778); ELT-Bench-Verified (arXiv:2603.29399) | — | — | **BIRD Mini-Dev 52.8 % and Spider 2.0-Snow 62.8 % gold error rates**; ELT-Bench: benchmark-attributable errors in 82.7 % of failed transformation tasks, 9.85 points of apparent progress from fixing the benchmark | — |

Also reviewed: Spider 2.0 (ICLR 2025 oral), BIRD / BIRD-CRITIC / **BIRD-INTERACT** (ICLR 2026 oral; ~7.5
turns/task, phase-level scoring; GPT-5 8.67 % c-Interact), LiveSQLBench (**"Business Rule Drift"** — the only
authoritative knowledge that changes across releases), TAG (position paper, 80 queries), DiscoveryBench,
QRData (GPT-4 58 % overall, **46.8 % causal**), ScienceAgentBench (best 32.4 %), DABstep (14.55 % hardest),
LongDS-Bench (best 48.45 %; **47-point early-to-late decline**), ConDABench, Era by Eon, FDABench,
AgenticDataBench, MLR-Bench, TraceBench, CausalVerify (**15.5 % execution–correctness gap**), Lit2Test,
Decision Lab (PyMC Labs; not a benchmark — a five-layer validity stack that returned *"No valid model found.
Run a geo-holdout experiment."* on an unidentifiable marketing-mix dataset).

## What the landscape already covers well

1. **Execution-grounded analytics over heterogeneous artefacts** — DataSpace, Spider 2.0, DAB, KramaBench.
2. **Long-horizon ML engineering** — MLE-bench and its lineage.
3. **Statistical method selection as a labelled choice** — StatQA, QRData.
4. **Identification-spec grading** — CausalReasoningBenchmark, CausalDS, CausalVerify (all 2026).
5. **Latent-world grading** — AvalancheBench, CausalDS, CausalGame, Era by Eon, TraceBench.
6. **Executed falsification with error control** — Popper (uniquely).
7. **Reward-hacking measurement** — BAITBENCH, CausalGame.
8. **Software incident RCA** — OpenRCA, ORCA-bench, CUJBench.

## What it does not cover — the gap this project can occupy

1. **No benchmark hands the agent a confident, authoritative, *wrong* prior analysis it must detect and
   overrule.** Every artefact in every benchmark reviewed is correct by construction; AvalancheBench states
   "No dashboards or misleading artifacts"; DAB supplies a hints file; BIRD supplies Oracle Knowledge.
   Nearest prior art is BAITBENCH (plants a shortcut but measures whether the agent *takes* it) and
   LiveSQLBench's Business Rule Drift.
2. **No benchmark frames the task as diagnosing and repairing a specific flawed prior analysis across
   stages.** BIRD-CRITIC repairs a *labelled-broken* SQL query; ELT-Bench builds a pipeline.
3. **Almost nothing measures whether an agent obtains evidence that could refute its own interpretation**
   in a professional setting. Popper does it in hypothesis-validation; CausalGame gives it 2 rubric points
   and finds 5–7 % uptake.
4. **Abstention / "this data cannot answer that" is scored in exactly one benchmark** (CausalDS) and in one
   non-benchmark system (Decision Lab), and in no data-agent benchmark.
5. **Leakage is treated as a benchmark defect rather than as the finding.** MLE-bench patches it; BAITBENCH
   shows 57.1 % of runs exploit it.
6. **Decision consequence is absent.** No benchmark reviewed ties the analysis to a stated business decision
   rule with a threshold and grades the decision alongside the quantities.

## Design lessons adopted (and one warning that changes our design)

1. **Anchor grading to a declared latent world**, and derive the graded quantities from it rather than from
   a reference answer (AvalancheBench).
2. **Grade the scientific object separately from the deliverable** — otherwise the score measures formatting
   (DataSpace: 52 % of best-model failures were materialisation; CausalReasoningBenchmark: strategy 79 % vs
   full spec 34 %; KramaBench: design 42 % vs implementation 20 %).
3. **⚠️ The wrong-but-authoritative artefact must not always be wrong.** A suite in which the prior report is
   always wrong is gamed by always disagreeing — that measures contrarianism. **Every world must contain
   authoritative artefacts that are correct and should be deferred to, and at least one task whose published
   number is right and whose complainant is wrong.** This is a new requirement for ForensicDS: the current
   five are all "the published number is wrong".
4. **Score detection-and-reporting of a defect, not merely avoidance** (BAITBENCH's inversion).
5. **Require a precommitted falsifying observation and require it to be executed**; grade
   implication-validity separately, because "the test does not actually refute the hypothesis" is a real and
   frequent failure (Popper: 17.2 %).
6. **Make abstention a scoreable outcome** where the honest answer is "this cannot be identified from these
   data; here is the experiment that would" (CausalDS; Decision Lab).
7. **Penalise merges and fluent wrongness.** Design at least one graded item that a plausible-sounding
   summary fails (AvalancheBench's merged events; SCIRIGOR's 91.8 % vs 91.0 % claim-agreement result).
8. **Instrument which stage the first error entered** rather than reporting only end-to-end (Traverse,
   SCIRIGOR, LongDS-Bench's 47-point decline).
9. **Audit the gold answers adversarially and report agreement.** Gold error rates of 52.8 % and 62.8 % have
   been measured in two flagship benchmarks; 9.85 points of apparent model progress in ELT-Bench came from
   fixing the benchmark. BLADE's expert–expert agreement of 75–80 % is the realistic ceiling.
10. **Prefer deterministic checks over judges** wherever the quantity is nameable (InfiAgent-DABench rejected
    LLM judging at 67 % human consistency; AvalancheBench flags judge bias and same-family contamination).
11. **Seal the simulator and log tool calls** — CausalGame documents agents recovering hidden scenario IDs
    for +18.5 points and 39 sessions declaring success below threshold.

## Things we should deliberately not copy

- Hint files, oracle knowledge and answer-bearing specs (DAB, BIRD, InfiAgent-DABench) — they remove the
  ambiguity that makes the work real.
- Insight-recall metrics (UniDataBench) — they reward hedged enumeration.
- Unanchored "reasoning" or "insightfulness" scores (DSAEval, DataCross) — DataCross's GPT-4o scores higher
  on Logic than on Factuality, i.e. the rubric rewards well-argued wrongness.
- A single scenario with a same-family judge (AvalancheBench's own limitation).
