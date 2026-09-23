# Phase 2 — WORLD → TASK architecture in professional agent benchmarks

Reviewed with primary sources only; items the reviewer could not source primarily are marked
**UNVERIFIED** and must not be quoted as fact.

**Correction to an assumption this project was carrying:** *APEX-Finance, APEX-Consulting and APEX-Law
do not exist as standalone benchmarks.* Investment banking, management consulting and corporate law are
**domains inside APEX-Agents**; medicine is a fourth domain inside APEX-1. The product list is APEX-1
(300 tasks, 4 domains), APEX-Agents (v1.1: 240 tasks, 3 domains), APEX-Accounting (160), APEX-SWE (200),
plus ten "Extended" variants grafting Mercor tasks onto public benchmarks.

## The four world→task mechanics actually in use

**(i) Let experts do the job, keep the exhaust.** APEX-Agents (arXiv:2601.14242): professionals were
*"assigned to teams, given roles (e.g., partner, associate), and tasked with delivering the project over
5-10 days"*; they *"sent emails and messages, conducted research, scoped deliverables, and iterated on the
work products."* The world's files are residue of real work, so distractors, stale numbers and
contradictory threads are authentic. **33 worlds, mean 166 files each, 8–20 tasks per world (mean 14.5),
mean human task time 1.82 h.** Tasks are written only *after* the world is finished.

**(ii) Specify the world as a document, with the traps enumerated first.** APEX-Accounting
(arXiv:2607.27189v2) — the single most transferable paragraph in the review: *"First, we ran a cross-world
scoping pass to assign each world a high-level profile, balanced across the full set. Second, we gave each
world a detailed specification: a description of every file, every task to be built (**including the
deliberate traps each is meant to catch**), and a **trap register** cataloging every seeded
contradiction."* 10 worlds × 16 tasks; each world *"a self-contained company frozen at month-end close"*;
73.1 unique required input files per task.

**(iii) Stand up real self-hosted services and seed one company.** TheAgentCompany (arXiv:2412.14161):
GitLab + ownCloud + Plane + RocketChat, **17 named personas** with roles and channel access, 5 project
teams, LLM-simulated colleagues → **175 tasks** from one world, platform requirements summing to 237
because tasks span services.

**(iv) Compose tasks from verified atoms.** τ²-bench 15 atomic groups → 2,285 composites → 114 sampled;
WorkArena 33 templates → 19,912 instances; 341 workflows → 682 L2/L3 tasks.

**Reset semantics.** Archipelago re-populates world state per run and grades *"by comparing before-and-after
snapshots"*; WorkArena wraps every task in `setup()`/`teardown()`. **Nobody implements true inter-task state
dependency.** The realism that works is *one deep, information-rich world with many independent tasks over
it* — not a chained storyline. This is directly applicable to us: a shared world costs nothing in
independence.

**The fifth mechanic, and the one closest to our own instruments:** CORE-Bench (arXiv:2409.11363) amortises
**one** capsule into **three** tasks by varying only what the agent is given — Easy (the successful run's
output), Medium (Dockerfile + README), Hard (README only). Same world, same questions, three difficulties,
purely by information ablation.

## How the field stops the prompt from stating the solution

1. **Terminal-Bench's written spec** (tbench.ai/news/writing-a-good-terminal-bench-task) — quotable and
   almost identical to our DP17/DP18: *"Difficulty should come from the problem itself"*; tasks are bad
   *"when they are hard because the required output format is fussy, the environment is needlessly awkward,
   or the instructions hide assumptions"*; instructions must *"state an unambiguous objective… and avoid
   turning the task into a guided tutorial"*, reading *"like something you would give to a strong engineer:
   clear, direct, and sufficient, with the tests responsible for checking the outcome."*
2. **APEX-Accounting's prompt rule:** prompts *"are concise and include a clear expectation of the final
   output but **do not explain the methods where a competent accountant would already know them**."*
3. **Latent-variable withholding (CRMArena):** the variables that determine the answers are computed in the
   generator and **never uploaded** — the answer is absent from the world, not merely from the prompt.
4. **Visibility partitions:** PaperBench agents *"are not shown the rubric"*, *"To prevent overfitting to the
   evaluation criteria."*
5. **Explicit known/unknown splits** (τ²-bench) with a user simulator told to *"Disclose information
   progressively."*

**Three published measurements of how much the prompt was carrying — the strongest external validation of
our recognition/execution gate:**
- WorkArena, same world: **L1 (procedure in the prompt) 42.7% → L2 (in chat) 3.0% → L3 (ticket + KB) 0%.**
- GDPval **Under-contextualized** ablation — prompts cut to *"42% the length (by token count)"*, removing
  *"where to locate specific data within reference files, how to approach the problem"*: GPT-5 *"performed
  worse as it struggled to figure out requisite context."*
- CRMArena-Pro, same instance single-turn vs multi-turn: **58% → 35%.**

**The counter-pressure, which we must respect:** OSWorld-Verified moved *toward* specification — *"explicit
format requirements"*, *"specified exact file paths"* — because under-specification generated **false
negatives**, not difficulty. SWE-Bench+ shows the other failure: solution leakage in issue text plus weak
tests meant *"67.72% of resolved instances didn't truly fix the issue."*
**Rule: specify the ask and the output contract exhaustively; specify the method never.** Those are
different axes and conflating them turns a diagnosis benchmark into a tutorial.

## Grading the chain, not only the deliverable — the two precedents that matter

**OpenRCA 2.0** grades a predicted **causal propagation graph** against an annotated one: Path Reachability
(correct root-cause service *and* a valid path to a ground-truth alarm node), Node F1, Edge F1, alongside
outcome Exact Match. The payoff number is **ungrounded diagnosis: AnySvc 76.0% vs Path Reachability 61.5%,
a 14.5 pp gap of agents that named the right service without being able to show why** — verbatim,
*"step-wise causal ground truth raises the standard from correct localization to correct reasoning"* and
*"outcome-only evaluation hides this failure mode."* This is the metric shape for instrumenting our H2/H3.

**BLADE** (EMNLP-F 2024) grades the **decision set** — conceptual variables, transform data-flow graphs
matched by graph isomorphism, model specs — with **Coverage@k over justifiable alternatives**. Expert
agreement 75%/80%; LM-proposed decisions agreed at only 27%/13%. Coverage@10 **below 13%** for statistical
models and **below 27%** for operationalising variables, against ~78–82% on the same decisions in
multiple-choice form. And its own stated limit, which is our opening: it *"does not evaluate an agent's
ability to interpret the results of data analyses."*

**FrontierScience** is the rubric version: *"The grading rubric assesses not only the accuracy of the final
answer, but also the correctness of intermediate reasoning steps."*

**The explicit argument against**, which we should weigh: APEX-Accounting's rubric rule is *"Outcome-based:
Grading only the final answer, not intermediate steps"*, and its judge sees the output **but not the
trajectory**. OSWorld 2.0's middle path is the one to take: reward **externalised intermediate artefacts**
(files, logs, written findings the agent must produce), never the chain-of-thought — it found that state
kept *"only in compressed reasoning or chain-of-thought context"* is exactly where agents lose information,
and that agents spend **under 7% of budget on self-correction**.

## Numbers to calibrate against

| quantity | field | ForensicDS today |
|---|---|---|
| files per world | APEX-Agents **166**, APEX-Accounting 73 required inputs/task | **~25–31** |
| tasks per world | **14.5** (Agents), **16** (Accounting), 175/world (TheAgentCompany) | **1** |
| criteria per task | 4.06 / 13.7 / 14.8 / ~416 (PaperBench leaves) | binary reward + per-check logs |
| reliability metric | pass@1, pass@8 **and pass^8** (Agents Pass^8 0.3–13.4%; Accounting 2.6%) | pass@3 only |
| independent re-solve | 20% of tasks (Agents → **10% needed fixes**); 20 tasks (Accounting → **3/276 criteria, 1.1%**) | Oracle=1 only |
| dev / held-out | CORE-Bench 45/45 (test GPG-encrypted); MLE-Bench 7 dev; PaperBench 2 dev; APEX-Accounting **11th world = dev, 10 hardest = benchmark** | none |
| authoring cost | TheAgentCompany **~17 person-hours/task**; PaperBench *"many tens of hours"* per rubric | — |
| judge validation | Accounting **1,687 expert labels, 97.1% acc**; Agents 747 labels, 98.5% | n/a (deterministic) |

**The selection bias every difficulty-filtered suite inherits, named only by APEX-Accounting:** *"Task
selection filtering by three frontier models introduces a risk that the models used to filter the tasks…
have depressed scores."* We name the same bias; the structural fix is a dev world for calibration and a
prospectively-built reported suite — which is exactly the protocol this phase pre-registers.

**The exploit to design against before it appears.** APEX-Agents v1.1 found **scattergunning**: *"models
provide multiple answers despite having a single answer that is well-specified by the environment"*, which
pays whenever *"binary rubric items… only check for inclusion of correct information. Only one answer needs
to be right."* Our numeric verifiers are immune; **the moment we add a findings artefact we inherit it.**
Their three-part fix — audit for well-specification, make the judge score hedged items **zero**, forbid
hedging in the prompt — plus one of ours: a mutation case that submits the correct cause alongside three
distractors and must score 0.

**Confounds larger than most model gaps.** Tool interface: bash vs typed tools moves TheAgentCompany by
**21.8–24.5 pp** and APEX-Agents by 4.8–7.4 pp at 19–72% fewer tokens (arXiv:2609.11999). Scaffold: on
CORE-Bench, *"Codex CLI outperforms the CORE-Agent scaffold by ≈44 pp"* on the same model. Our single-harness
limitation is therefore understated, not overstated.

**Not to copy.** (1) GDPval-style blinded pairwise human grading — *"over an hour"* per comparison, 70.8%
human IRR, admitted style leakage; we would trade a deterministic verifier for a 71%-agreement preference
signal. (2) An LLM judge as primary grader, and never a judge model that also appears on the leaderboard
(APEX-Agents grades with Gemini 3 Flash while it competes, and concedes self-preference risk).
(3) Breadth at the cost of separability — APEX-Agents cut 480→240, CORE-Bench 90→39, MLE-Bench paused
submissions, τ-bench needed 53 tasks fixed post-release. (4) Counting infrastructure failures as agent
failures (APEX-SWE reports 18% "Infrastructure Failure" inside its *agent* taxonomy without stating those
runs were excluded). (5) Treating "may not ask clarifying questions" as a virtue rather than a constraint
we accept for determinism.

**Governing quote for the maintenance discipline:** *"Benchmarks are not static artifacts. They are software
and we should maintain them like software."* (APEX-Agents v1.1)
