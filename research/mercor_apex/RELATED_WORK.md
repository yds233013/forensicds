# Related work: what is already taken, and what is left

This is written as a threat assessment, not a survey. For each cluster the question is: **what claim does this
work remove from us?** Verification status of every citation is tracked in `SOURCES.md`; 2026 preprints were
located by a literature agent and the load-bearing ones independently re-checked against arXiv.

## The headline finding, stated before the detail

**Every component of the idea already exists in the literature, and two-of-three combinations exist in 2026 work.
Combine Turk (arXiv:2605.30590) with CausalDS (arXiv:2607.08093) and roughly 85 % of a naive version of this
proposal is already published.** Both are 2026 preprints and both name the remaining piece as future work. This
is not a reason to abandon the project; it is a reason to state the contribution as a narrow mechanical move
rather than as a new paradigm, and to expect a reviewer to have read both.

---

## 1. The closest single paper: Turk, *Counterfactual Evaluation Reveals Hidden Capability Profiles in Clinical LLMs and Agents* (arXiv:2605.30590)

224 expert-annotated oncology tumour-board cases mutated along five pre-registered clinical intervention families
(biomarker flips, prior-treatment failures, biomarker removals, surgery-status changes, stage perturbations). A
**Causal Sensitivity Score** "scores in {0,0.5,1.0} whether each model's recommendations update in the
pre-registered correct direction", with all five fields "committed before any model is evaluated". CSS and a
coverage rubric rank six frontier models in nearly opposite orders — every model changes rank. It transfers to
ReAct-style tool-using agents. *(The design implies the mutations are undisclosed — baseline packet versus mutated
packet — but the paper never states this in words, so do not cite it as a stated property.)*

**What this removes from us.** We cannot claim the idea of hidden, pre-registered, decision-relevant variants of a
professional case, nor the finding that variant-based scoring reorders a leaderboard, nor that this is novel in a
high-stakes professional domain. All three are Turk's.

**What it leaves.** Sensitivity only — there are no no-change control interventions, so invariance-where-it-should-hold
is never scored — regex no-op mutations are *discarded* from the scored set rather than used as controls. Nor is
abstention scored: "A model that correctly refuses to update on any of these is scored 0.0 under the pre-registered
rule", and the author concedes pre-registration "cannot distinguish causal-sensitivity failure from correct refusal
of incoherent or non-actionable inputs." It perturbs *individual cases*; there is no shared artifact corpus held
fixed across a family. Critically for cost, each variant is a **fresh prompt to the model**: N variants cost N
inferences.

**A caveat we must carry, because it weakens our differentiation.** The abstention gap is a property of v1, and the
author has already committed to closing it: Appendix M ("Camera-Ready Refinements") states "we will add a 0.5 credit
when the model's rationale explicitly identifies the inserted scenario as medically incoherent and leaves
recommendations unchanged." So "Turk does not score deferral" is true today and may not be true in six months. Our
contribution must not rest on it, and in the narrowed framing (§10) it does not.

## 2. The closest paper in our own domain: *CausalDS* (arXiv:2607.08093)

Each instance is a hidden sampled SCM plus generated data files plus a graph-audited narrative in a realistic
domain, spanning all three rungs of Pearl's ladder, with an observation model producing measurement corruption.
Decisively, "the agent must first decide whether this population estimand is identifiable … and abstain when it is
not" — abstention is a first-class scored outcome against hidden ground truth that includes each target's
identifiability status. **Two separate appendices already run matched-variant ablations.** Appendix A.12 swaps
verbalizations of one fixed formal problem: "one representative member's clean data and private ground truth are
mapped back onto every member's variable names, so all members share the same numbers, the same scoring target, and
the same private truth", with the normative criterion stated outright — a competent agent "would score identically
on all four members". Appendix A.13 runs one scene under three observation views, and states that the observation
layer is "designed to change how hard an identified functional is to estimate from the released files while
preserving the conceptual SCM, the target estimand, and the identifiability label", and "never flips an
identifiability label".

**What this removes from us.** We cannot claim deferral-on-non-identifiability as a scored outcome in data science,
nor hidden latent structure in a data-science agent benchmark, nor even the matched-variant invariance idea in the
abstract — it is in their appendix with the normative criterion spelled out.

**What it leaves, and this is the whole remaining opening.** Neither ablation varies the mechanism: A.12 varies
only surface verbalization over an identical formal problem, and A.13 explicitly preserves the conceptual SCM, the
target estimand and the identifiability label. So the one contrast we care about — where the *correct decision
differs between siblings* — is never built, in A.13 by stated design. The matched designs are diagnostic ablations on two
open-weight models, not the graded object; main grading is per-instance accuracy plus an abstention metric. And
each scene gets a freshly sampled SCM with its own story, so there is no persistent professional rule corpus — data
dictionary, contract, policy, protocol — held constant across a family. Their stated future work asks for "more
systematic stress tests via targeted exams for abstention, quantitative skills, and counterfactual reasoning."

## 3. The paper whose scoring architecture we most resemble: *Policy Invariance as a Reliability Test for LLM Safety Judges* (arXiv:2605.06161)

The only work I found that integrates all three legs into one number: invariance under certified-equivalent
rewrites, directional sensitivity under intentional strict-to-lenient threshold shifts, and ambiguity-aware
calibration so that instability concentrates on genuinely ambiguous cases — aggregated into a Policy Invariance
Score. Its finding is the one we expect: judges "respond to meaningful normative shifts and to meaningless
structural rewrites with comparable strength, and cannot tell the two apart."

**What this removes from us.** The *scoring architecture* — invariance + sensitivity + a calibration/ambiguity leg
in one score. We must not present that triple as our contribution.

**What it leaves.** It is our structural inverse: the graded subject is a judge's verdict, what varies is the
policy wording, and the world is held fixed. We vary the latent world with the policy held fixed, and grade an
agent's analysis. Different object, different variable, same arithmetic.

## 4. The closest paper on "grade the pattern, not the instance": *AgentAbstain* (arXiv:2607.10059)

263 paired tasks across 42 executable sandbox environments, each pair a should-act task and a should-abstain
variant produced by a controlled perturbation to the instruction, tool, or environment state, scored by **paired
accuracy** — correct on both sides. Best agent 59.5 %.

**What this removes from us.** Making the pattern across controlled variants the graded unit rather than the
instance. That was going to be our most distinctive scoring move and it is published.

**What it leaves.** The graded output is binary act/abstain, not a substantive analysis; the perturbed thing is an
instruction, tool or environment fact, not a latent causal mechanism; and there is no invariance leg.

## 5. The closest paper on re-execution: *ReplaySCM: A Benchmark for Executable Causal Mechanism Induction from Interventions* (arXiv:2605.08197)

1,300 items in which the agent emits a mechanism in a Boolean DSL, scored by **replay on held-out intervention
worlds**: "Scoring uses replay behavior rather than formula strings, so syntactically different mechanisms receive
credit when they behave correctly", under Ordered / Block-order / Hidden-order / Hidden-roots disclosure settings.

**What this removes from us.** The mechanical core — evaluate the submitted artifact by replaying it on worlds the
agent never saw — is published. This is the single most important citation for us to be honest about, because it
is the move we intend to lead with.

**What it leaves.** The artifact is a Boolean-DSL mechanism over a synthetic causal item; there is no professional
deliverable, no document estate, no decision, no deferral, and no invariance/sensitivity distinction. Replay is
used to grant equivalence credit, not to detect an untested auxiliary assumption inside an otherwise correct
professional analysis. Nearby: *CausaLab* (arXiv:2605.26029) scores both task success and fidelity of the
recovered mechanism — GPT-5.2-high reaches 92 % task accuracy against 0.471 all-edge F1, which is the same
"right answer, unrecovered mechanism" dissociation we predict, in a synthetic setting.

## 6. Professional-domain deferral is already occupied: *CliniCARE-Bench: Clinical Calibrated Audit of Medical Reasoning in EHR* (arXiv:2608.07796) and *READY or Not* (arXiv:2609.02095)

25 clinician-validated scenarios as 750 MIMIC-IV cases over 16 systems. "Each case demands one of four verdicts:
Yes, No, Indeterminate: Lack of Data, or Indeterminate: Medically Ambiguous", and "abstention is thus built into the
evaluation standard, not bolted on as a post hoc confidence threshold." Defect-free accuracy runs "4.8–14.8
percentage points below accuracy on the same report-present runs, and this correction changes the ordering of
systems."

**What this removes from us.** Any claim to novelty for deferral credit in professional work, or for the finding
that a stricter composite reorders a leaderboard. Both taken. Also see *AbstentionBench* (arXiv:2506.09038) for
underspecification-driven abstention at scale.

**What it leaves.** Deferral tied to a *variant* in which identification actually disappears — i.e. the same
analysis, the same corpus, and a sibling world where the estimand is not recoverable. Theirs is a fixed property
of the case.

## 7. Ancestors we must cite and must not claim

- **CheckList** (Ribeiro et al., ACL 2020) already has INV ("label-preserving perturbations … expect the
  prediction to remain the same") and DIR ("the label is expected to change in a certain way"). The invariance /
  sensitivity *pair* is twenty-six years of software engineering and six years of NLP old. Related: **contrast
  sets** (Gardner et al., EMNLP Findings 2020), **counterfactually-augmented data** (Kaushik et al., ICLR 2020).
- **Metamorphic testing** is the correct classical framing: Chen, Cheung & Yiu 1998; Segura et al., IEEE TSE 2016;
  Chen et al., ACM CSUR 2018; for ML, Murphy et al. 2008, Xie et al. JSS 2011, DeepTest (ICSE 2018); for LLMs,
  arXiv:2605.13898 (93 primary studies, now covering agentic closed-loop testing) and Cho et al., ICSME 2025.
  Applied to code agents: *A Jagged Frontier* (arXiv:2608.18389) runs SWE-bench under semantics-preserving
  transformations for up to a 6.7 pp resolve-rate drop — **invariance direction only, no sensitivity controls.**
- **Programmatic variants where the answer changes**: GSM-Symbolic (ICLR 2025) and its GSM-NoOp invariance probe,
  GSM1k, MATH(), DyVal, Mystery Blocksworld/PlanBench, and **RE-IMAGINE** (ICML 2025, arXiv:2506.15455), which is
  the closest generator design — Pearl-ladder observe/mutate/imagine over a mutated symbolic representation. Graded
  by per-variant accuracy; no deferral.
- **Reasoning or Reciting?** (NAACL 2024) runs counterfactual task variants but **states the altered rules in the
  prompt**. Our variants are hidden. That is a real distinction and a small one.
- **The world-family container is built, three times**: METR's Task Standard has an explicit `variants` dict over
  ~200 families, but frames variants as a difficulty/hint ladder each scored against its own ground truth, with no
  cross-variant aggregation; Procgen and *Quantifying Generalization in RL* have shared rules with a varying latent
  seed and generalization as the measured quantity, but measure mean return over i.i.d. samples, not paired
  contrasts; **Alchemy** (NeurIPS 2021 D&B) resamples a hidden causal structure per episode but expects
  within-episode discovery and grades by reward. **Do not claim the formalism**: contextual MDPs (Hallak et al.
  2015) already have "dynamics depend on a hidden static context", and epistemic POMDPs (Ghosh et al. 2021) are the
  principled argument for crediting deferral.
- **Grading the analysis rather than the answer, in professional data work**: **BLADE** (EMNLP Findings 2024) grades
  536 ground-truth analysis decisions against independent expert analyses and accepts a multiverse of justifiable
  approaches — one real world per question. **AvalancheBench** (arXiv:2605.24183) scores recovery of the segments,
  drivers and events behind the data from a known latent world; best agent recovers 26 % of the rubric. One latent
  world per case, no family. *Note: "latent world" is already taken as a term of art in enterprise analytics, and
  arXiv:2606.14574 uses "latent" for silent state-propagation errors — we should avoid both phrasings.*
- **Process supervision**: *Let's Verify Step by Step* (ICLR 2024); **ProcessBench** (arXiv:2412.06559), whose
  output space — find the earliest erroneous step *or* conclude all steps are correct — is deferral-shaped; and
  most importantly **OpenRCA 2.0** (arXiv:2606.27154), which grades the causal path via Path Reachability / Node F1
  / Edge F1 using fault injection to reconstruct ground-truth propagation, and finds that agents "identify at
  least one correct root-cause service in 76.0 % of cases but ground that service in a verified causal propagation
  path to the observed symptom in only 61.5 %". That 14.5-point gap is the
  best existing published evidence for the failure mode we target, and it is in a controlled-latent-state setting.
  It builds no variant families and scores no deferral.
- **Underspecification** (D'Amour et al., JMLR 2022) is the closest conceptual statement of the problem and a clean
  differentiator: they vary the *predictor* and hold the data-generating process fixed; we hold the analysis fixed
  and vary the DGP. **Counterfactual invariance to spurious correlations** (Veitch et al., NeurIPS 2021) is the
  formal statement of the invariance leg alone. Also shortcut learning (Geirhos et al. 2020), WILDS, DomainBed,
  Spawrious.
- **Consistency checks without ground truth** (Fluri, Paleka & Tramèr, SaTML 2024) is the one prior work grading a
  *signature* in both directions — identical chess boards must agree, added felony charges should move a bail
  decision. It abandons ground truth; we do not. The consistency literature otherwise treats all change as defect:
  ParaRel, **BECEL** (COLING 2022 — a taxonomy of consistency types, and the most direct competitor to our
  vocabulary), sycophancy, option-order sensitivity. We must explicitly distinguish cross-world consistency from
  **self-consistency decoding** (Wang et al. 2022); reviewers conflate them.
- **The statistical ancestor a reviewer will raise**: Steegen, Tuerlinckx, Vanpaemel & Gelman, *Increasing
  Transparency Through a Multiverse Analysis* (2016). A multiverse varies the **analysis** over one dataset; we
  vary the **world** under one analysis. State it before they do. BLADE already imported the multiverse framing
  into agent evaluation.
- **Hidden-test benchmarks hide an oracle, never a mechanism**: SWE-bench hides the test patch, MLE-bench a private
  split, LiveCodeBench and LiveBench control contamination temporally, Terminal-Bench hides a verifier and holds out
  tasks. **ARC-AGI-2** is the nearest — each task has a latent rule — but the rule is inferable within the task, the
  output is one grid, and there is no cross-variant or abstention credit. The sharpest motivating contrast:
  **SWE-bench Verified's human screening deliberately removed under-specified issues.** The field's response to
  identification failure has been to delete those instances. APEX-Accounting deleted 24 of them. We propose to
  score them.

## 8. Does anything hold all three legs at once?

| | professional domain, shared artifact corpus | hidden variants where a latent **mechanism** differs and the correct **decision** flips | invariance + sensitivity + deferral graded **jointly** | siblings cost compute, not inference |
|---|---|---|---|---|
| Turk CSS 2605.30590 | yes | inputs, not mechanisms | sensitivity only | no — N prompts |
| CausalDS 2607.08093 | partial (synthetic narratives) | hidden, but mechanism held fixed | abstention yes, invariance diagnostic-only | no |
| Policy Invariance 2605.06161 | policies, not work | no (policy wording varies) | **all three, one score** — on a judge | n/a |
| AgentAbstain 2607.10059 | sandboxes | instruction/tool/env, not mechanism | pairwise act/abstain only | no |
| ReplaySCM 2605.08197 | no | intervention worlds, synthetic | no | **yes** |
| CliniCARE-Bench 2608.07796 | yes | no variants | abstention + grounding | no |
| OpenRCA 2.0 2606.27154 | yes (SRE) | controlled via fault injection, no families | no | no |
| METR `variants` | yes | difficulty ladder | no | n/a |
| BLADE / AvalancheBench | yes | single world | no | no |
| **APEX (all four)** | **yes, best in class** | **no** | **no** | **no** |

**No row in this table is complete on the evidence I gathered.** The final column is where the space looks least
crowded, and it is also the column that makes the other three affordable. This is a survey of what I found, not a proof
of absence.

## 9. Explicit negative findings

Searched for and did not find: any APEX work grading conditional correctness (see `RESEARCH_GAP.md` §3); any METR
publication doing latent-state variant contrasts, as opposed to the `variants` difficulty ladder in the task
standard; any UK AISI / Inspect eval running one task family under different latent ground truth with
invariance-versus-sensitivity scoring; any benchmark jointly scoring invariance, sensitivity and deferral over
hidden variants of a shared professional artifact corpus.

## 10. What this means for how the contribution must be stated

Three moves survive the audit, and only three:

1. **The decision-flip contrast.** I did not find work that builds paired variants in which the same surface world and
   the same professional artifacts yield an *opposite correct decision* because one latent mechanism differs. CausalDS
   deliberately holds the conceptual SCM fixed; Turk perturbs case inputs; RE-IMAGINE mutates symbolically but
   discloses. Lead with this rather than with "invariance and sensitivity", which is CheckList's.
2. **Re-execution of a professional deliverable, not re-prompting.** ReplaySCM has replay for Boolean mechanisms;
   I did not find it applied to a professional analysis against a professional document estate. This is what makes N siblings
   cost seconds of CPU instead of N rollouts, which is what makes the design a candidate for a real benchmark
   rather than a paper-scale demonstration — and it is what makes contamination resistance structural rather than
   rhetorical.
3. **A shared professional rule corpus persisting across a variant family.** TheAgentCompany has the artifacts and
   one world; METR has the family container and no mechanism contrast; APEX has the best artifacts in the field and
   one world per task. I did not find a work that combines them.

Everything else in the design is borrowed, and the write-up should say so.
