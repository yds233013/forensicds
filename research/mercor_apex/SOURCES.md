# Sources

All access dates 2026-09-25 unless stated. **Verification column:** `V` = the arXiv abstract page and, where a quote
is used, the full text were fetched and the claim confirmed verbatim; `A` = located by a research agent and reported
from a primary source, but not independently re-fetched by me; `U` = unverified, do not cite without checking.
`P` = primary (the work itself, its authors' own page, or its code), `S` = secondary.

**Rule applied throughout: no statistic appears in the proposal unless its row here is `V` or the number was computed
from this repository.** Rows marked `A` support framing and positioning only.

---

## 1. Mercor / APEX — primary

| # | source | id / URL | date | used for | P/S | ver |
|---|---|---|---|---|---|---|
| M1 | *The AI Productivity Index (APEX)*, Bertie Vidgen et al., Mercor | arXiv:2509.25721 | 30 Sep 2025 (v6 16 Dec 2025) | four jobs; expert-authored rubric + sources; 400 held-out cases; 14.81 criteria/task; "economically valuable tasks in four jobs"; criteria "analogous to unit tests" | P | V (existence, title, date); A (quotes) |
| M2 | *APEX-Agents*, Vidgen et al., Mercor | arXiv:2601.14242 | 20 Jan 2026 | world-first construction; 166 files/world; 14.5 tasks/world; "each task is associated with a single world"; judge receives "…but not the agent trajectory"; Pass^8; 92/480 single-criterion tasks; web search off | P | V (existence, title, date); A (quotes) |
| M3 | *APEX-Accounting*, Julien Benchek et al., Mercor + Ramp | arXiv:2607.27189 | 29 Jul 2026 (v2 30 Jul) | trap register of "every seeded contradiction"; contamination screening; "admits a single defensible answer"; 24 incomplete-information tasks removed; grading "only the final answer, not intermediate steps"; Limitations §6; 2,186 criteria; 97.1 % judge agreement; 2.6 % Pass^8 | P | V (existence, title, date); A (quotes) |
| M4 | *APEX-SWE*, Abhi Kottamasu et al., Mercor | arXiv:2601.08806 | 13 Jan 2026 | "epistemic discipline"; Robustness Criteria = defensive coding; rubric scores excluded from leaderboard | P | V (existence, title, date); A (quotes) |
| M5 | APEX index + leaderboards | mercor.com/apex/ | live | current task counts and top scores; the 300-vs-400 conflict | P | A |
| M6 | APEX methodology page | mercor.com/apex/methodology/ | live | the "and agent trajectories" claim that the papers contradict; stale APEX-Accounting entry | P | A |
| M7 | *Introducing APEX-Agents 1.1* | mercor.com/blog/introducing-apex-agents-1-1/ | 8 Sep 2026 | "ensuring a single correct and well-specified answer exists"; "there is an unambiguous answer"; discoverable conventions in communications; median-vs-mean LBO example; scattergunning penalties; Pass^4 | P | A |
| M8 | Archipelago harness | github.com/Mercor-Intelligence/archipelago | pushed 25 Sep 2026 | verifier types `output`; `trajectory` and `value` marked COMING SOON; no variant/seed primitive | P | A |
| M9 | apex-agents-v1.1 dataset | huggingface.co/datasets/mercor/apex-agents-v1.1 | live | 240 tasks / 31 worlds; each task one instance in one world; no variant field | P | A |
| M10 | Mercor Research Fellowship — APEX | mercor.com/careers/a0a98be0-d856-4129-b500-c0a3e412ef01/ | published 22 Aug 2026 | focus areas verbatim; "rolling admission"; no deadline; "navigation" absent, "negotiation" present once; $40k/3mo, $80k/6mo | P | **V** |
| M11 | Mercor AI Research Fund Grants ($5M) | jobs.ashbyhq.com/mercor/e1f6792d-… | published 22 Sep 2026 | one-to-two-page EOI; wanted topics incl. underspecified tasks; institution-routed; 12-month non-compete | P | A |
| M12 | *SWE-Marathon-Ext* | mercor.com/blog/swe-marathon-ext-… | 11 Aug 2026 | hidden pytest suites over a spec-only build | P | A |

## 2. The closest prior work — all independently verified

| # | source | id | date | claim used | ver |
|---|---|---|---|---|---|
| C1 | *Counterfactual Evaluation Reveals Hidden Capability Profiles in Clinical LLMs and Agents*, Matt Turk (Protege Data Lab; RLEval) | arXiv:2605.30590 | 28 May 2026 | CSS "scores in {0,0.5,1.0} whether each model's recommendations update in the pre-registered correct direction"; fields "committed before any model is evaluated"; "A model that correctly refuses to update … is scored 0.0"; regex no-op mutations excluded from the scored set; **Appendix M commits the camera-ready to adding a refusal-credit branch** | **V** |
| C2 | *CausalDS: Benchmarking Causal Reasoning in Data-Science Agents*, Andrej Leban, Yuekai Sun | arXiv:2607.08093 | 9 Jul 2026 | abstain when not identifiable; **A.12** "all members share the same numbers, the same scoring target, and the same private truth" / "would score identically on all four members"; **A.13** "preserving the conceptual SCM, the target estimand, and the identifiability label" / "never flips an identifiability label" | **V** |
| C3 | *Beyond Accuracy: Policy Invariance as a Reliability Test for LLM Safety Judges*, Shihao Weng et al. | arXiv:2605.06161 | 7 May 2026 | `PIS = max(0, 1 − (w₁·Δflip^cert + w₂·(1−R_dir) + w₃·U_rate)·S)` "summarizes a judge's reliability across all three principles"; graded subject is the judge | **V** |
| C4 | *AgentAbstain: Do LLM Agents Know When Not to Act?*, Xun Liu et al. | arXiv:2607.10059 | 11 Jul 2026 | "263 paired tasks (526 individual tasks) instantiated in 42 MCP sandbox environments"; pairs differ "in exactly one of q, e, or τ"; "The best model (Gemini 3.1 Pro) achieves only 59.5% Paired Accuracy" | **V** |
| C5 | *ReplaySCM: A Benchmark for Executable Causal Mechanism Induction from Interventions*, Serafim Batzoglou | arXiv:2605.08197 | 5 May 2026 | "Scoring uses replay behavior rather than formula strings, so syntactically different mechanisms receive credit when they behave correctly" | **V** |
| C6 | *OpenRCA 2.0: From Outcome Labels to Causal Process Supervision*, Aoyang Fang et al. | arXiv:2606.27154 | 25 Jun 2026 (v2 30 Jun) | 500 instances; Path Reachability / Node F1 / Edge F1; agents "identify at least one correct root-cause service in 76.0% of cases but ground that service in a verified causal propagation path … in only 61.5%" | **V** |
| C7 | *CliniCARE-Bench: Clinical Calibrated Audit of Medical Reasoning in EHR*, Veronica Chatrath et al. | arXiv:2608.07796 | 7 Aug 2026 | four verdicts incl. "Indeterminate: Lack of Data" and "Indeterminate: Medically Ambiguous"; "abstention is … not bolted on as a post hoc confidence threshold"; defect-free accuracy "4.8–14.8 percentage points below" and "changes the ordering of systems" | **V** |

## 3. Supporting literature — existence and title verified, claims reported

| source | id | date | used for | ver |
|---|---|---|---|---|
| *AvalancheBench: Evaluating Enterprise Data Agents Through Latent World Recovery*, Kleczek et al. | arXiv:2605.24183 | 22 May 2026 | latent-world recovery scored against a known world; 26 % rubric recovery; **"latent world" is already a term of art** | V (title/date), A (claim) |
| *CausaLab*, Junlin Yang et al. | arXiv:2605.26029 | 25 May 2026 | task success vs recovered-mechanism fidelity (92 % vs 0.471 F1) | V (title/date), A |
| *RE-IMAGINE: Symbolic Benchmark Synthesis for Reasoning Evaluation*, Xinnuo Xu et al. | arXiv:2506.15455 | 18 Jun 2025 | Pearl-ladder observe/mutate/imagine variant generator | V (title/date), A |
| *Bidirectional Empowerment of Metamorphic Testing and LLMs: A Systematic Survey*, Zheng Zheng et al. | arXiv:2605.13898 | 12 May 2026 | 93 primary studies; MRs over agent trajectories and environment states | V (title/date), A |
| *A Jagged Frontier: Evaluating Robustness of Code Agents to Semantics-Preserving Transformations*, Hasan Najib Mahmud et al. | arXiv:2608.18389 | 18 Aug 2026 | SWE-bench under semantics-preserving transformations, up to 6.7 pp drop; invariance-only | V (title/date), A |
| *Executable Counterfactuals*, Aniket Vashishtha et al. | arXiv:2510.01539 | 2 Oct 2025 | forces the abduction step | V (title/date), A |
| *SCIRIGOR: Evaluating Open-Ended Scientific Analysis Beyond Final Scores*, Bowen Liu et al. | arXiv:2609.06192 | 5 Sep 2026 | claim-support-path scoring; claims agree with faithful and unfaithful results at near-identical rates | V (title/date), A |
| *CausalGame*, Zhenhao Chen et al. | arXiv:2607.04293 | 5 Jul 2026 | protocol design + explanation report; 5–7 % of sessions earn causal-reasoning rubric credit | V (title/date), A |
| *CLadder*, Zhijing Jin et al. | arXiv:2312.04350 | 7 Dec 2023 | causal-inference question benchmark | V | 
| *Learning the Difference that Makes a Difference with Counterfactually-Augmented Data*, Kaushik, Hovy, Lipton | **arXiv:1909.12434** | 26 Sep 2019 (ICLR 2020) | human counterfactual revision of documents. **Corrected from a wrong ID (1910.12543 is a physics paper) caught in verification** | **V** |
| *AbstentionBench*, Kirichenko et al. (Meta FAIR) | arXiv:2506.09038 | 2025 | underspecification-driven abstention at scale | A |
| *READY or Not: Reliable Enterprise Agent Deployment* | arXiv:2609.02095 | Sep 2026 | qualifying agents under oversight policies | A |
| *ProcessBench*, Chujie Zheng et al. | arXiv:2412.06559 | Dec 2024 | earliest erroneous step *or* all-correct — deferral-shaped output | A |

## 4. Established prior work cited as ancestry (pre-cutoff, standard references)

CheckList — Ribeiro, Wu, Guestrin, Singh, ACL 2020 (arXiv:2005.04118), INV/DIR relation types · Contrast sets —
Gardner et al., EMNLP Findings 2020 (arXiv:2004.02709) · Metamorphic testing — Chen, Cheung & Yiu 1998; Segura et
al., IEEE TSE 2016; Chen et al., ACM CSUR 51(1), 2018; DeepTest, ICSE 2018 · GSM-Symbolic — Mirzadeh et al., ICLR
2025 (arXiv:2410.05229), incl. GSM-NoOp · *Reasoning or Reciting?* — Wu et al., NAACL 2024 (arXiv:2307.02477) ·
METR Task Standard `variants` — github.com/METR/task-standard · Procgen — Cobbe et al., ICML 2020
(arXiv:1912.01588); *Quantifying Generalization in RL* — ICML 2019 (arXiv:1812.02341) · Alchemy — Wang et al.,
NeurIPS 2021 D&B (arXiv:2102.02926) · Contextual MDPs — Hallak, Di Castro & Mannor (arXiv:1502.02259) · Epistemic
POMDPs — Ghosh et al., NeurIPS 2021 (arXiv:2107.06277) · BLADE — Gu et al., EMNLP Findings 2024 (arXiv:2408.09667)
· *Let's Verify Step by Step* — Lightman et al., ICLR 2024 (arXiv:2305.20050) · Underspecification — D'Amour et al.,
JMLR 23(226), 2022 (arXiv:2011.03395) · Counterfactual invariance — Veitch, D'Amour, Yadlowsky & Eisenstein,
NeurIPS 2021 (arXiv:2106.00545) · Shortcut learning — Geirhos et al., Nature MI 2020 (arXiv:2004.07780) ·
*Evaluating Superhuman Models with Consistency Checks* — Fluri, Paleka & Tramèr, SaTML 2024 (arXiv:2306.09983) ·
BECEL — Jang, Kwon & Lukasiewicz, COLING 2022 · Self-consistency — Wang et al. (arXiv:2203.11171), cited only to be
distinguished · Multiverse analysis — Steegen, Tuerlinckx, Vanpaemel & Gelman, *Perspectives on Psychological
Science* 11(5), 2016 · SWE-bench — Jimenez et al., ICLR 2024 (arXiv:2310.06770), incl. Verified's removal of
under-specified issues · MLE-bench (arXiv:2410.07095) · ARC-AGI-2 (arXiv:2505.11831) · GDPval, OpenAI
(arXiv:2510.04374) · Off-policy "counterfactual evaluation" — Bottou et al., JMLR 14, 2013, cited only to
disambiguate the term.

## 5. Repository evidence (all numbers computed here, not cited)

| claim | where it comes from |
|---|---|
| 4/9 visible-instance passes → 0/9 family passes; P22 3/3 → 0/3; P20 0/3 → 0/3; P31 1/3 → 0/3 | `research/mercor_apex/PILOT_VERIFICATION.md`, recomputed from the frozen verifiers' `criteria_notes.txt` |
| P22 tooling truth 0.167 pp visible / 3.083 pp hidden_c; ±0.8 pp tolerance; `"tooling": 0.0` literal in all three trials; `wear` appears 0 times in all three trajectories | same, from frozen task truth and stored trajectories |
| 42 defective mutants: 30 visible (71 %), 10 family-only (24 %), 2 neither (5 %); 3/3 references pass 4/4 | `tools/bench/visible_vs_family.py` → `mutation_visible_vs_family.json` |
| 2 mutants invisible on all four worlds are caught by `estimator_implementation` / `evidence_reconstruction` | frozen `tools/p22/mutation_results.txt` |
| nine trials = $1.4667 total; 4 worlds graded per trial; 32 s wall clock for the P22 reference trial | `research/phase3/exposure/cost_ledger.txt` and the job logs |
| 9/9 valid trials, zero protocol violations, pre-registered plan hashed before exposure | `research/phase3/HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md`, `analysis_plan.md` (sha256 `c590cb56…`) |

## 6. Known unverified items — not used in the proposal

The literature agent flagged these as located but not confirmed, and none of them carries a claim in
`PROPOSAL_FULL.md`: Spawrious author list; Naik et al. (COLING 2018) arXiv ID; BECEL and *Ask Again Then Fail* page
numbers; Steegen et al. page numbers; ARC-AGI-3 (arXiv:2603.24621) and the ARC-AGI-2 technical report
(arXiv:2603.06590); "Hack-Verifiable Terminal Bench" (arXiv:2608.22103); Era by Eon (arXiv:2609.09853); DI-Bench
(arXiv:2609.05776); *Agent Psychometrics* (arXiv:2604.00594); Simmer (arXiv:2606.14574); DiscoveryWorld parametric
variation details; the aggregator-reported 26 September 2026 fellowship deadline. **One further warning:
arXiv:2604.20938 is a different "HARBOR" and is not the Harbor CLI used in this repository.**
