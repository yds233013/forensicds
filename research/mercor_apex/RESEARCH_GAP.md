# What APEX already does, and the one thing it does not

Research date 2026-09-25. Everything attributed to Mercor below comes from the four APEX papers, the
`mercor.com/apex` pages, the Archipelago harness, the released datasets, or the fellowship posting.
Provenance and verification status for every item is in `SOURCES.md`. Where two Mercor sources conflict I say so
rather than choosing.

---

## 1. The APEX family as it actually stands

There are exactly four APEX papers. An exhaustive arXiv enumeration (`all:"AI Productivity Index"`,
`all:APEX AND all:Mercor`, `au:Vidgen`) returns no fifth.

| benchmark | what it evaluates | scale (site, 2026-09-25) | leaderboard metric |
|---|---|---|---|
| APEX-1 | single-turn deliverables: IB associate, management consultant, big-law associate, primary-care MD | 300 tasks on `/apex/`; **400** on the leaderboard page — unresolved conflict | mean rubric score |
| APEX-Agents v1.1 | long-horizon, cross-application tasks in IB, consulting, corporate law | 240 tasks / 31 worlds | Pass@1, Pass@4, Pass^4 |
| APEX-Accounting | month-end close: reconciliation, data entry, variance analysis, schedules & accruals | 160 tasks / 10 worlds / 2,186 criteria | mean criteria % passed @3 |
| APEX-SWE | integration and observability engineering | 200 tasks | Pass@1 |

Construction is **world-first and expert-authored**. APEX-Agents builds a world before it builds tasks —
professionals are assigned roles and deliver a project over 5–10 days, and only then are tasks written against the
resulting estate (mean 166 files per world, 8–20 tasks per world, 14.5 on average). APEX-Accounting goes further
and ships each world with a **trap register cataloguing every seeded contradiction**, plus a contamination
guarantee: every document is novel and screened against public sources.

This is a serious benchmark programme. Any proposal that treats it as naive is wrong, and a reviewer will know it.

## 2. Feature audit

| capability | APEX status |
|---|---|
| expert-authored rubrics | **yes**, everywhere (4.0–14.8 criteria/task) |
| held-out / private splits | **yes**, all four; dev-vs-held-out shift tables published |
| hidden tests the agent cannot see | **yes** for APEX-SWE and SWE-Marathon-Ext; hidden *rubrics* elsewhere |
| repeat-run reliability (pass^k) | **yes** for Agents and Accounting; no model exceeds 2.6 % Pass^8 on Accounting |
| multiple tasks per world | **yes** — 14.5 (Agents), 16 (Accounting) |
| multiple worlds per task | **no** — "each task is associated with a single world" |
| trajectory grading | **effectively no.** Both papers state the judge does *not* see the trajectory; Archipelago's `trajectory` verifier is marked COMING SOON. The methodology page claims otherwise and is unsupported by the papers and the code |
| intermediate / process criteria | **predominantly no.** APEX-Accounting's rubric spec requires "grading only the final answer, not intermediate steps"; APEX-SWE has process rubrics but excludes them from the leaderboard |
| hidden task variants (same task, different latent value, different correct answer) | **no** |
| counterfactual worlds | **no** — the word appears zero times in all four papers |
| robustness / invariance / perturbation evaluation | **no.** APEX-SWE's "Robustness Criteria" means defensive coding; APEX-Agents' "Sensitivity Analysis" is the finance workflow the agent performs, not a property of the benchmark |
| "would this analysis still be right under a different latent value?" | **not found** |

## 3. The direct answer to the question I was told to ask first

**In the APEX materials I reviewed — the four papers, the product and methodology pages, the blog, the released
datasets and the Archipelago harness — I did not find anything equivalent to the proposed method.** Keyword searches and
a documentation audit are evidence of absence *in those materials*, not proof that nothing equivalent exists anywhere;
unpublished or in-progress work could change this. The finding should be read with that limit, and it must be stated
carefully for a second reason: the absence is not oversight.

Across the four papers: `counterfactual` 0 hits, `latent` 0 hits, `perturb` 0 hits, `invarian` 0 hits,
`what-if` 0 hits. The only `variant` matches are MathML attributes. The only `sensitivity` matches are finance
task-category labels. The released datasets carry no variant or seed field — 240 tasks are 240 single instances.
Archipelago's config schema has no variant, seed or parameter-sweep primitive.

**Mercor has deliberately engineered in the opposite direction, and said so.** APEX-Agents 1.1's audits existed
"to ensure a single correct and well-specified answer exists"; on 1.1 "there is an unambiguous answer that models
can and should give". APEX-Accounting's QC verifies that each task "admits a single defensible answer", and the
team **removed 24 incomplete-information tasks** — the ones where a model should refuse or ask for clarification.

A proposal that reads this as a mistake will be dismissed. It is not a mistake: single-instantiation determinism is
the right call for *scoring*, because it makes criteria unambiguous and judge agreement high (97.1 % against expert
ground truth on Accounting). What it leaves unmeasured is a **different property** — whether the answer was
*conditioned on* the right latent quantity, or merely *coincided with* the modal one.

## 4. Why the gap is live rather than dormant

Three places where APEX's own text names the missing capability without measuring it:

1. **APEX-Agents 1.1 puts latent parameters in the world, fixed at one value.** "Working professionals typically
   don't specify parameters ad nauseam, so, to preserve realism, neither do our tasks. Instead, preferences are
   listed in communications, spreadsheets, and documentation." Their own illustrative example is
   median-versus-mean in an LBO model: "a banker doesn't usually submit an LBO model with separate cases … they
   pick one option." APEX instantiates *one* convention and grades against it. Under one instantiation you
   cannot separate *read the convention* from *guessed the modal convention*. They already observe the
   consequence — Kimi K3 gained +29.7 % Pass@1 at task level when it searched communications — without being able
   to attribute it.
2. **APEX-Accounting's own Limitations section asks for this.** Excluding human-in-the-loop tasks "removes a skill
   that real staff accountants exercise constantly; knowing when to ask a clarifying question rather than proceed
   on an assumption. This would increase realism if addressed in the task design."
3. **APEX-SWE's headline construct is unmeasured.** It defines "epistemic discipline … the capacity to distinguish
   between assumptions and verified facts" and then measures it only by whether one fixed answer passes its tests.

And the infrastructure gap is shippable-sized: Archipelago is Apache-2.0, actively maintained (pushed
2026-09-25), and its `trajectory` and `value` verifiers are unimplemented. A world-variant primitive plus a
conditional-correctness verifier is a contribution to a repository Mercor already runs.

## 5. Two further gaps that compose with it

**I found no APEX benchmark covering data science, analytics or quantitative analysis.** The four cover IB, consulting, law,
medicine, accounting and software engineering. The closest adjacencies — APEX-Accounting's Variance Analysis
category (28/160 tasks) and APEX-Agents' Sensitivity Analysis / Market Sizing / Variance-Performance workflow tags
— are analytics-shaped content graded as one-shot deliverables. Analytics is precisely the domain where a
deliverable is natively **re-executable** and where latent-assumption sensitivity is the professional risk.

**Only one of the four papers has a Limitations section.** APEX-Agents and APEX-SWE contain the word zero times.
That is itself a methodological gap a fellowship could address, though it is not the one I propose to.

## 6. Two Mercor-internal inconsistencies not to repeat as fact

- APEX-1 task count: 300 on `/apex/` and `/apex/methodology/`, 400 on the leaderboard page and in the paper.
- The methodology page states APEX-Agents grades "rubrics over final deliverables **and agent trajectories**",
  contradicted by APEX-Agents §4.2 ("the judge takes in … **but not the agent trajectory**") and by Archipelago's
  unimplemented `trajectory` verifier. The paper relies on the judge *not* seeing trajectories as its
  self-preference mitigation, so the page is very likely the stale artefact.

## 7. Corrections to the brief I was given

- **The fellowship posting contains no "navigation" focus area.** The word appears zero times in the page's raw
  HTML. **"Negotiation" appears once**, in a different bullet — "New economic benchmarks — negotiation, management,
  and other capabilities that carry economic value but resist standard task formats" — which is almost certainly the
  source of the misreading. The bullet actually intended reads, verbatim: "Novel evaluation methodology:
  contamination resistance, rubric design, human-vs-model grading agreement, cost-adjusted scoring." All four named
  sub-items are real; the category label is not.
- **The posting states no deadline** — it says "Duration: 3–6 months, rolling admission", and was live on
  2026-09-25 (published 2026-08-22; stipend $40,000 for 3 months or $80,000 for 6). The only "closes" substrings on
  the page are inside the word "closest". The circulated "26 September 2026" date appears only on third-party
  aggregators and could not be corroborated from any Mercor-controlled page. Treat the date as unverified but act as
  though it is imminent.
- **APEX is Mercor's, not Anthropic's.** APEX-1 is *The AI Productivity Index* (Vidgen et al., Mercor). The
  Anthropic Economic Index is usage telemetry, not an eval. The natural external comparison is OpenAI's GDPval.
- A separate and newer Mercor programme — the **$5M AI Research Fund Grants**, posted 2026-09-22 — specifies a
  one-to-two-page expression of interest and names "measuring whether benchmark performance translates into
  reliable performance on realistic tasks" and "complex, ambiguous, or underspecified tasks" among its wanted
  topics. It is institution-routed with a 12-month non-compete, so it is a decision for the applicant, not for me.

## 8. The gap, stated in one paragraph

APEX measures whether a frontier agent can produce the professional deliverable that is correct in the one world
it was shown. It does not measure whether the deliverable is correct *because* the agent identified the mechanism
that makes it correct. Those two come apart exactly when a decision-relevant latent quantity is small, absent or
conventional in the observed world and large in a neighbouring one — which is the ordinary condition of
professional analysis, and the condition under which an analysis is redeployed next month. I found no APEX benchmark,
blog, dataset or harness that tests it, and APEX's own published design decisions — one defensible answer per task, one
world per task, final-output-only grading, incomplete-information tasks removed — mean that as published it does not.
