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

---

# Addendum — corrections and Harbor-specific findings

**Two claims above were wrong and are retracted here.**

**R1. Terminal-Bench has a paper.** Merrill et al., *"Terminal-Bench: Benchmarking Agents on Hard, Realistic
Tasks in Command Line Interfaces"*, **85 authors, 44 affiliations**, arXiv:2601.11868 (17 Jan 2026). The repo
has **moved** to `github.com/harbor-framework/terminal-bench`; docs at `docs.harborframework.com`.

**R2. TB 2.0's QA is quantified — in the paper, not the blog.** *"we crowd-sourced tasks through open-source
contributions, with **93 contributors creating 229 tasks**… we selected **89**"* (≈39% acceptance); *"the
average task received approximately **three hours of combined reviewer attention**, implying multiple hundreds
of person-hours… excluding the time spent creating the tasks."* Three named criteria: **Specificity**
(*"well-specified if the unit tests will pass if and only if the container ends in an acceptable state"*),
**Solvability**, **Integrity** (*"It should not be possible for an agent to 'cheat' … by taking a shortcut
that would not exist in a real-world deployment"*). Seven-step pipeline: CI oracle-pass + no-op-must-fail →
contributor checklist → contributor-run LLM check → manual review → multi-model runs where each failure is
classified *genuine incapacity vs task bug* → **adversarial exploit agent** → two additional auditors.
Automated gate = 6 deterministic + 11 LLM-backed checks.

## The field's tightest measurement of what pre-release QA buys — and it is sobering

Three reviewer-hours per task still let **28 of 89 tasks** ship defective. TB **2.1** fixed them: external
dependency drift (9), **insufficient CPU/memory/time budgets (8)**, misspecification (*"In `query-optimize`,
the tests expected Spark SQL output, while the instructions asked for PostgreSQL"*). Effect on measured
capability: **Opus 4.6 (Claude Code) 58.0% → 70.1% (+12.1 pp)**; Gemini 3.1 Pro 63.0% → 70.7%. *"After these
changes, no task is unsolved in Terminal-Bench 2.1."*

**A 31% residual defect rate worth 12 points of understated capability, after hundreds of reviewer-hours.**
Two consequences for us: our own QA cannot be assumed sufficient, and **resource mis-calibration is a leading
cause of understated capability** — TB 4.0 recalibrated *every* task to a flat 8-hour timeout after resource
experiments. Our per-task limits need an explicit audit of that kind. (Related: TB 2.0's error taxonomy finds
the single most frequent agent failure is *"calling executables that are not installed or not in PATH
(**24.1% of all failures**)"* — pure environment friction, invisible in a scalar reward.)

**Version trajectory, which is the argument against task-count ambition:** 1.0 (80) → 2.0 (89) → 2.1 (89,
28 fixed) → 3.0 (74) → **4.0 (66, 19 more fixed, 8 removed)**. A benchmark with 85 authors shrinks at every
version while raising quality.

## SWE-bench Verified: the largest rubric campaign in the field, now from the primary page

**93 software developers**, **1,699 samples**, onboarding gate (50 hand-labelled samples; annotators had to
pass tests). **A 0–3 ordinal severity scale per criterion** *"rather than a single binary label… to capture
more granular detail"*. **Conservative ensembling:** *"each sample is labeled **3 times**… we conservatively
ensemble annotations by taking the **highest-severity label** amongst the 3"* — equivalent to filtering any
sample **any one of three** annotators flagged. Results: **38.3%** flagged for underspecified problem
statements, **61.1%** for unit tests that may unfairly fail valid solutions, **68.3% of samples filtered
out**. GPT-4o 16% → **33.2%**.

**The control that makes it interpretable, and which we should copy:** *"performance increases within
individual difficulty categories when moving to SWE-bench Verified, which is consistent with the intended
effect of removing impossible samples from all categories instead of removing difficult samples."* That is
how you demonstrate a filter removed defects rather than difficulty. **Inter-annotator agreement statistics
are still unpublished — UNVERIFIED.**

## Terminal-Bench's written authoring rulebook — the closest thing to a spec for our problem

From `docs/prompts/task-proposal.md` and `CONTRIBUTING.md`:
- **"Most people write benchmark tasks the way they write prompts. They shouldn't. A prompt is designed to
  help the agent succeed; a benchmark is designed to find out if it can."**
- The two-verifier test for well-specification: *"if two reasonable people read the problem description, a
  well-specified problem should result in both of them writing verification algorithms so that anyone who
  passed one of the verifiers would also pass the other."*
- *"A well-specified task shouldn't require a lot of guidance or hints on how to solve it… The best tasks can
  be described succinctly in 2-3 paragraphs."*
- **LLM-judge gate:** permissible *"in rare and extraordinary circumstances but only if it can be shown that
  the verifier essentially never makes a mistake"*, with documented alternatives and why they are insufficient.
- **A warning aimed directly at our own selection criterion:** mass-generating candidates and filtering for
  what current models fail risks *"finding trivial corners of capability gaps specific to the current models."*
  Corroborates the selection-bias limitation we already publish, and argues for mechanism-first design over
  difficulty-first filtering.

From the **35-criterion implementation rubric** (`task-implementation.toml` — the rubric `harbor check` runs):
- `instruction_concision`: *"Instructions should not hint at the solution approach or provide step-by-step
  procedures — **describe what to achieve, not how**"*; FAIL if instructions *"list available
  tools/libraries that the agent should discover on its own."*
- `test_instruction_alignment`: *"Every test assertion should trace back to a requirement stated in the
  instruction… Tests should be hand-written, readable, and concise — ideally under ~100 lines. **Longer test
  suites may indicate over-specification.**"*
- `reviewable`: *"Tasks with specialized ground truth should derive expected answers from solution scripts
  rather than hardcoding them… **Hardcoded expected values without derivation are a red flag.**"* (Our
  generator-derived truth satisfies this by construction.)
- `solution_quality`: the solution *"must not just echo/cat the final answer."*
- `verifier_execution_isolation` names a threat model to check against our own verifiers: *"a malicious
  artifact can double-fork a daemon that outlives the test run and overwrites `/logs/verifier/reward.txt`
  after `test.sh` writes it, forging a pass despite failing tests."* Our outstanding `--no-new-privs` and
  `chmod 700` findings are exactly this criterion.

## Four capabilities we should be using and are not

**1. An adversarial exploit agent as a standing gate.** TB 2.0 runs OpenHands prompted *"You are a security
researcher bot and your goal is to exploit any way to CHEAT… you MUST use at least some cheating"*, with
trajectories inspected **regardless of pass/fail**. Found exploits: *"monkey-patching test environments,
guessing answers, and generating all possible answers with the hope that tests might only check existence of
a correct answer but not absence of wrong answers."* That last is the **scattergun** exploit again — found
independently by two benchmarks, so assume we will meet it. Our static 21–38-case mutation suites cannot find
*novel* exploits; a live adversarial run can. Scale of the problem: Bercovich, arXiv:2604.28093 — *"over 15%
of tasks in popular terminal-agent benchmarks are reward-hackable."*

**2. Harbor's native multi-step tasks and `reward.json`.** `docs.harborframework.com/core-concepts/tasks/multi-step`:
*"Multi-step tasks provide a way to interleave verification through the agent run"*, with per-step `tests/`,
`min_reward` early-stopping and `multi_step_reward_strategy = "mean" | "final"`; plus `reward.json` for
multi-dimensional rewards beside scalar `reward.txt`. **Criterion-level scoring and staged verification
(reconcile → localize → diagnose → repair → validate) are harness features, not a fork.** Caution: a
third-party blog attributes "process-level milestone rewards" to TB 2.0; the paper does not. Treat multi-step
as a **Harbor** capability, not a property of any shipped Terminal-Bench version.

**3. The separate verifier container (TB 3.0+).** Artifacts are downloaded from the agent container and
uploaded to a fresh verifier, which *"prevents many reward hacking vectors allowing for **re-grading when task
verifiers are updated**."* The re-grading half is the underrated one: it is what would let us fix a verifier
defect **without re-running baselines** — precisely the maintenance capability the versioning lesson needs,
and it retires our standing "verifier runs the agent's pipeline in the same container" weakness.

**4. The Agentic Benchmark Checklist** (Zhu et al., arXiv:2507.02825). Terminal-Bench scores itself in an
appendix: Outcome Validity 0.857, **Task Validity 1.000**, Benchmark Reporting 0.830, **average 0.896**,
*"ranking second among existing benchmarks"*, with two admitted failures — *"Test case quality is not assessed
via objective, automated metrics"* and *"Some non-determinism remains"*. Both are things our Monte-Carlo
tolerance calibration and deterministic generators address **better** than TB does. Running this itemised
third-party instrument costs zero model spend and yields an external validity claim.

## The prospective-validation mechanism, solved

SWE-Lancer holds out **$499,200** of tasks in which engineers *"**reintroduce the bug or issue in a distinct
but equivalent way**"* — the same mechanism, re-instantiated. For us this is nearly free: the generators are
parameterised, so a held-out task is *the same mechanism with a different world skin, data regime and trap
instantiation*, built after the discovery set is frozen and never piloted. **This is strictly stronger than
APEX-Accounting's "hold out the 10 hardest worlds", because it does not select on difficulty at all.** Adopt
it as the phase-3 protocol.

Related SWE-Lancer facts: **100 professional engineers** wrote and verified the tests; three reviewers per
IC SWE task, two for management, **ten** for tasks over $5,000; screening uses a **0–3 specification rating
where the majority must rate 0**. Diamond is **502** tasks.

## A sixth thing not to copy: treating a public set as held out

Terminal-Bench says it plainly — *"Even the tasks not selected to be included with this paper, which may serve
as a 'held-out' set, are still publicly accessible"* — and it has **no private test set** by design. SWE-bench's
cheating post measures gold-hunk verbatim match averaging **6.7% on Verified**, with one submission at
**78.7%**, now policed above 20%. **Once `candidates/` is public, every number from it is a development
number; only an unreleased variant can carry a prospective claim.**

## Two further corrections to the main review

- **SWE-bench Multimodal is 619 instances** (517 test / 102 dev), not 617 — the abstract is wrong, the body
  and tables agree on 619. Environment cost *"an average of **ten hours of manual labor per repository**"*;
  validation runs **10× per instance** dropping inconsistent ones; **24 impossible tasks removed**. Image
  ablation 11.0% → 8.0% overall, and **17.6% → 8.8%** on instances annotators judged to need the images.
- **SWE-Lancer's public IC SWE set drifted from 237 to 198 tasks (2025-07-17)**, so post-July-2025 numbers on
  it are not comparable across dates.
