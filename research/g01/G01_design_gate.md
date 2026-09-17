# G01 design gate: collections label maturity and the observation process

**Decision: REDESIGN specified, then STOPPED at the Phase-0 gate (§8).** The redesign is recorded below; its simulation gate did not establish separation on the graded statistics, so no implementation was started. The original design's core is sound and unusually well matched to the
capability we still lack, but three of its layers duplicate tasks we have since built and validated, and the tournament
found its graded statistics fragile. This document records the fresh review and specifies G01 v2.

- **Sources re-read:** `research/gen3_designs/G01_collections_label_maturity.md` (655 lines, design only),
  `research/gen3_candidate_pool.md` §G01, `research/gen3_design_tournament.md` (R2 review, finding #11),
  `research/gen3_scoring.md`, `research/gen3_implementation_shortlist.md` §S8,
  `research/gen3_tournament_sims/reviewer_g01*.py`.
- **Nothing is built. No model has been run.**

## 1. What the original design proposed

A consumer lender's collections "cure" model appears to degrade (AUC 0.74 → 0.67). Three mechanisms interact:
labels observed through posting systems with source-specific completeness; early outcomes maturing first; and a
score-driven contact policy that changes the outcomes the model is evaluated against. The agent rebuilds an exact
label table and evaluable population, then estimates performance against the model's documented target (cure under the
strategy the model was developed for), which after the policy change is only observed in a randomised holdout, and
finally reaches a model-risk status decision.

## 2. Findings from the tournament that remain binding

| Finding | Status | Consequence for v2 |
|---|---|---|
| Band-5 holdout n ≈ 126, tolerance ≈ 0.10; ignoring the policy gives +0.088 in band 4, only 1.3× tolerance; band-5 errors pass; an oracle using its own estimate picks the wrong status ≈ 10% of the time | reviewer simulation | The holdout-weighted target estimator is the fragile part. v2 removes it. |
| Cheapest path ≈ 40 actions | reviewer | Acceptable if the path is genuinely sequential; v2 keeps four dependent discoveries. |
| Answer keys: the README output schema names CS-7 uplift and strategy periods; the model card's "worked under CS-5" line | reviewer | v2 has no uplift output and no strategy period in the schema. |
| Exact label conventions are brittle (early cure with an incomplete window; HPF vs hub conventions) | shortlist risk | v2 grades the label *and* the evaluability state explicitly, and the conventions are stated as KPI facts. |
| Implementation cost ≈ 5.5 build-days, the most expensive in the pool | shortlist | v2 cuts the holdout, the uplift readout and the PH-2 pause. |

## 3. Overlap with what we have now built

This is the decisive change since the tournament: G24 and G05 now exist and are validated.

| Layer of G01 v1 | Overlaps | Verdict |
|---|---|---|
| Holdout cell with changing inclusion probability, inverse-probability-weighted target AUC | **G24** (item-in-slot IPW over a randomised exploration stream, decision-grain weighting) | Cut. It would make G01 a second propensity-weighting task, and it is exactly the layer the tournament found statistically fragile. |
| Treatment changes the *outcome* the model is judged against | **G05** (treatment versions, populations, transport) | Cut as an estimand. Policy is kept, but acting on *observation*, not on the target outcome. |
| Value date vs posting date as availability semantics | **Task 02** (`synced_at` vs `changed_at`) | Keep, but it is not the hard part: it is the first discovery, not the last. |
| Per-source, per-window completeness with a delivery gap | none | **This is the unique core.** |
| Informative selection: early outcomes are observable earlier, so "label known" is an outcome-dependent population | partially G10 (censoring) but G10 estimates a latent quantity; here the question is *which rows may be evaluated at all* | **Keep as the second core.** |

## 4. G01 v2: the redesign

### 4.1 The capability under test

> Can an agent decide **whether an observed outcome may be treated as a label yet**, when label availability is
> produced by posting systems, file deliveries and an operational policy — and therefore which rows a model may be
> evaluated on?

Not "use old enough labels": the maturity of a row is not a function of its age. It is a function of *which system
owes the data, what that system has delivered, and for which dates*.

### 4.2 The 25 design-gate questions

1. **Real workflow.** Monthly model-monitoring job for a collections propensity model at a consumer lender; Credit
   Risk Analytics owns the job, Model Risk owns the status decision under a model-performance standard.
2. **Business decision.** Model status: `keep`, `recalibrate` or `retire`, which gates whether the score keeps driving
   collections prioritisation.
3. **Incident.** Monitors show AUC falling 0.74 → 0.67 over two quarters and observed cure far below predicted. Credit
   Risk proposes retirement; an analyst deep-dive blames feature drift (PSI is genuinely up); Collections says cures
   are fine.
4. **Prediction unit.** A collections episode (an account rolling to 30 days past due), scored once at entry.
5. **Outcome / label.** `cure_30d`: arrears cleared within 30 days of entry, judged on payment **value dates**.
6. **When the label matures.** When every value date in the episode's 30-day window is known to be fully loaded for
   the system that owes those payments — not when 30 days have passed.
7. **How historical policy affects observation.** From March the escalation policy routes high-score episodes to an
   early-contact team. Early contact makes cures happen *sooner inside the window*; it does not change the 30-day cure
   outcome. Because cures post when they happen, treated episodes' labels become *determined* earlier, so any
   population built from "labels we already know" is selected on score and on outcome.
8. **Are missing labels informative?** Yes, twice over: (a) an episode that cured early is already determined while a
   non-curer of the same vintage is not; (b) the policy makes that asymmetry score-dependent.
9. **Target estimand.** Deterministic: the model's discrimination and calibration over the **evaluable population** —
   episodes whose 30-day window is fully loaded — per vintage and per portfolio, plus the status decision from the
   model-performance standard.
10. **Population.** Evaluable episodes, defined by window completeness per source. Not "label determined"; not "entry
    older than N days".
11. **Operational action.** The status decision, plus the corrected monitor the committee reads.
12. **DGP.** §4.3.
13. **Identification assumptions.** Cure is a deterministic function of value-dated payments; window completeness is
    determined by system state (hub close log, servicer file manifest), not inferred from observed payments;
    evaluability is independent of the outcome *conditional* on window completeness.
14. **Evidence graph.** Monitors and notebook (symptom) → job code (posting-date labels, "known outcome" population)
    → warehouse dictionary (value date) → per-source posting behaviour → hub close log and servicer manifest (the
    gap) → policy log (why determination is score-dependent) → standard (status thresholds).
15. **Natural wrong analyses.** §4.4.
16. **Plausible wrong numbers.** The faulty monitor's 0.668; a maturity-filtered 0.681; an acquired-book-excluded
    0.738; all near-plausible against a development AUC of 0.742.
17. **Scientific diagnostics available.** Cure-rate-by-entry-day within a vintage; determined vs undetermined split;
    posting-lag distribution by source and channel; coverage months per file; PSI decomposed by portfolio; a
    "label-freeze" replay (recompute a past monitor as of its run date).
18. **Hidden regimes.** Different delivery cadence and a different gap month; a genuine calibration shift in one
    portfolio (status truly `recalibrate`); a genuine discrimination decay (status truly `retire`).
19. **Verifier state.** Exact episode label table (`cure_30d`, `determined`, `evaluable`), exact evaluable counts per
    vintage × portfolio, vintage metrics recomputed from the agent's own labels, and the status decision. Mostly
    **deterministic**, which removes the v1 tolerance fragility.
20. **Alternative valid implementations.** SQL or pandas; any correct completeness reconstruction; metrics by any
    standard AUC implementation (ties are avoided by construction).
21. **Cheap-solve routes.** §4.5.
22. **Overlap with Task 02.** Task 02 is feature state at prediction time; G01 is outcome state at evaluation time.
    Different side of the model, different mechanism (file delivery and posting rather than sync lag).
23. **Overlap with G10.** G10 estimates a latent quantity under stopping-time censoring; G01 decides evaluability and
    then computes deterministic metrics. No latent-variable estimation.
24. **Overlap with G24.** None after the cut: no propensities, no weighting, no counterfactual policy value.
25. **Unique contribution.** Selective observation of outcomes as an *eligibility* problem, with policy feedback
    acting on label availability rather than on the outcome.

### 4.3 Data-generating process (v2)

- Episodes at DPD30 entry, in-house portfolio from month 1 and an acquired portfolio boarded part-way through.
- Score at entry; true cure probability = logit(score) (calibrated in the visible world).
- Cure timing: gamma-distributed day within the window; early-contact episodes cure sooner **within** the window, with
  the same 30-day cure probability.
- Payments post through the **hub** (0–6 days after value date by channel) or, for the acquired book, through a
  **monthly servicer file** whose coverage month posts on load. One monthly file is held for reconciliation, creating
  a coverage gap, and a later file is loaded normally, so coverage is not contiguous.
- System state is published: a nightly hub close log (`complete_through_value_date`) and a file manifest with
  coverage start/end and load time.
- Distractors: portfolio composition shifts PSI; posting-lag change on one channel.

### 4.4 Natural wrong analyses (to be separated by the Phase-0 gate)

| # | Analysis | Wrong object |
|---|---|---|
| W1 | keep posting-date labels, add a 30-day maturity filter | label date semantics |
| W2 | value-date labels, global 30-day maturity | ignores per-source completeness |
| W3 | per-source *maximum* coverage watermark | ignores the gap |
| W4 | empirical posting-lag percentile as a watermark | lag ≠ completeness |
| W5 | contiguous-from-first-month coverage | needlessly drops post-gap windows |
| W6 | population = "label determined" | informative selection (the core trap) |
| W7 | exclude the acquired portfolio | wrong population; the standard names all scored episodes |
| W8 | evaluate on all scored episodes regardless of completeness | mixes immature vintages |
| W9 | recompute history with today's completeness but the old population rule | partial repair |

### 4.5 Cheap-solve pre-audit

- One grep (`value_date`) fixes labels only: that is W2, which fails.
- One doc (the performance standard) fixes maturity only: W1/W8, which fail.
- Excluding the acquired book (W7) reproduces the pre-acquisition AUC of 0.741, which is *plausible* and wrong.
- No helper exists for the close log or the manifest; the faulty job never reads them.
- "Wait 60 days" (a conservative global buffer) still fails on the gap month.

## 5. Novelty test (required by the brief)

The correct repair is **not** "use only old enough labels", not one date filter, not a documented maturity threshold:

- maturity is per episode **and** per source, and for the acquired book it is per *coverage month*, with a gap;
- the evaluable population is not the set of known labels, and the difference is outcome- and score-dependent;
- the policy changes *when labels appear*, so the same population rule behaves differently before and after March.

An agent that fixes only one of these gets a plausible, wrong monitor.

## 6. What is cut relative to v1, and why

| Cut | Reason |
|---|---|
| CS-7 holdout, inverse-probability-weighted target AUC, uplift readout | duplicates G24; the tournament showed its tolerances are fragile (band-5 n ≈ 126) |
| "Target outcome under the development strategy" estimand | duplicates G05's population/treatment-version reasoning; replaced by policy acting on observation |
| PH-2 hub pause | a second, redundant completeness mechanism; the servicer gap is the load-bearing one |
| Per-band status thresholds | replaced by portfolio-level calibration and discrimination checks that are deterministic given the label table |

## 7. Decision

**REDESIGN, then build**, in this order:
1. Phase-0 simulation gate on the v2 DGP (accepted vs W1–W9 separation, over many worlds and regimes) — **the next
   deliverable**;
2. only if that passes: the Harbor task, to the same standard as G05 (realistic workspace, distributed evidence,
   hidden regimes, intermediate-state verifier, mutation suite, adversarial and statistical review, answer-key and
   cheap-solve audits, Oracle/Nop, harbor check, clean clone).

**Stop conditions:** if the gate cannot separate W3/W5/W6 from the accepted family without arbitrary tolerances, or if
the label conventions prove brittle, G01 is stopped and documented rather than tuned.

## 8. Phase-0 attempt and outcome: STOPPED

Two DGP iterations were run on the v2 design (`research/g01/pilot/`, 4 regimes × 1 seed for structure, full
seed sweeps not reached). The gate question was whether the **graded statistics** separate the accepted rule from the
natural wrong analyses. They do not.

### Iteration 1 (as specified in §4)

| Analysis | visible status | acquired-miscalibrated status | truth |
|---|---|---|---|
| reference / sql_style | keep | recalibrate | keep / recalibrate |
| posting-date labels (W1) | recalibrate | recalibrate | ✗ separated only in visible |
| global 30-day maturity (W2) | keep | recalibrate | **not separated** |
| max-coverage watermark (W3) | keep | recalibrate | **not separated** |
| empirical-lag watermark (W4) | keep | recalibrate | **not separated** |
| contiguous coverage (W5) | keep | recalibrate | **not separated** |
| label-determined population (W6) | keep | keep | separated only in the miscalibrated regime |
| exclude acquired (W7) | keep | keep | separated only in the miscalibrated regime |
| all scored (W8) | keep | recalibrate | **not separated** |

AUCs differed by ≤ 0.001 between the reference and most wrong analyses.

### Iteration 2: status read from the most recent evaluable vintages

Rationale (not threshold-chasing): monitoring reads recent vintages, and recent vintages are exactly the ones whose
windows are not yet complete, so this is where the selection question has consequences. Acquired-book latency was
lengthened (load day 24 of M+1) and the policy timing shift strengthened (median cure day 4 vs 16).

Result: status now separates W1 and W8 in visible, W1/W2/W8 in the miscalibrated regime, and W1/W6/W8 in the
late-cadence regime — but **W3, W4, W5, W7 and W9 still reproduce the correct status in every regime**, and no
analysis separates in the score-decay regime, where the real decay dominates everything.

### Why I stopped rather than iterate again

- Two iterations already moved the DGP. A third round aimed at making W3/W4/W5 flip a status would be tuning the
  generator against the mutation list, which is the failure mode the G05 gate protocol exists to prevent.
- The remaining separation would come from **exact table equality** (label, determined, evaluable, per-vintage counts).
  That is a strong verifier, but it makes G01 a deterministic state-reconstruction task: the Task 02 / Task 06 family,
  not the delayed-outcome statistics slice the benchmark still lacks.
- Restoring the statistical layer means restoring the CS-7 holdout and inverse-probability-weighted target, which
  duplicates G24 and is the layer the tournament measured as fragile (band-5 holdout n ≈ 126, oracle status wrong
  ≈ 10% of the time).

### Blocker, stated for the maintainer

> G01 cannot be both (a) statistically discriminating on its graded business decision and (b) non-overlapping with
> G24, without a new mechanism that neither v1 nor v2 supplies.

**Options, in the order I would consider them:**
1. **Accept the deterministic framing.** Build G01 as an exact label-state and evaluability task with a status
   decision, and describe its capability honestly as *outcome-state reconstruction* (sibling of Task 02, not of G10 or
   G24). Cheapest to build, and the verifier is exact. It probably will not add a new failure class.
2. **Find a genuinely different statistical layer for delayed outcomes**, e.g. grading a *forecast* of the eventual
   mature metric from partially observed vintages (an estimation problem whose truth is the matured value), which is
   distinct from both censored-demand estimation (G10) and policy-value estimation (G24). This is a new design, not a
   repair of v1.
3. **Drop G01** and spend the effort on a different slice, given that G05, G10 and G24 already cover causal panels,
   censoring and off-policy evaluation.

No further G01 work was done. Nothing was built, and no task files exist for G01.
