# Generation-3 implementation shortlist (8 candidates)

Date: 2026-09-14.

**Inputs:**
- `research/gen3_candidate_pool.md` (30 concepts)
- `research/gen3_scoring.md` (ranking)
- `research/gen3_designs/` (15 designs)
- `research/gen3_design_tournament.md` (adversarial review and post-tournament ranking)

**Status:** nothing here is implemented, and no model has been run against any candidate. Tasks 01–06 are unchanged.
"Expected hardness" is a design-time prior, not a measurement.

## Selection rule

The eight are chosen as follows:

1. Take the post-tournament ranking (tournament §6).
2. Keep at most two designs per kernel family.
3. Require each selected design to add a capability no earlier selection tests.
4. Exclude WEAK and REJECT verdicts.

The top seven post-tournament designs are selected directly. **Slot 8 goes to G05 (rank 11) instead of G17 (rank 8).**

- G17's differentiation from Task 01 is unproven, R1 rated it borderline WEAK, and its hardness depends on removing a
  deal-register key.
- G05 is the only causal-panel design in the pool. Simulation confirmed its core traps (g−1 base in the install dip,
  +0.042 overall; region×week FE alone, +0.015). Only its memo headline is infeasible, which is a narrative fix, not a
  mechanism fix.

| # | Design | Post-tournament rank | Kernel family | Primary failure class exposed |
|---|---|---|---|---|
| S1 | G08 forecast vintages | 4 | Point-in-time state | Per-origin knowledge time vs per-refit series (Task 02 transfer test) |
| S2 | G24 recommender OPE | 5 | Randomised exploration / IPW | Decision-grain propensities under slates, positions and reloads |
| S3 | G23 readmission episodes | 6 | Identity / episode grain | Episode construction across facilities and vocabularies; inflated trusted baseline |
| S4 | G10 censored demand | 1 | Censoring / latent estimation | Stopping-time censoring; observed sales ≠ demand |
| S5 | G11 training–serving skew | 2 | Point-in-time state (+ embedded negative control) | Multi-feature serving-time semantics; genuine drift must not be "fixed" |
| S6 | G05 staggered rollout DiD | 11 (diversity override) | Causal panel | Base-period contamination, non-comparable weeks, trade-area confounding |
| S7 | G25 search judgment pool | 7 | Identity + audit-sample estimand | Label identity/scale reconciliation; a partial fix worsens the decision |
| S8 | G01 collections label maturity | 3 | Censoring / immature labels (+ light policy layer) | Label maturity × value date × acquired-book source completeness |

**Alternates, in order:**

1. G17 (replaces S6 if G05's symptom rework fails simulation, or S7 if G25's margins fail).
2. G21 (replaces S8 if G01's generator cost or margins fail; the censoring rule must be fixed first).
3. G20 (only with a principled policy-path trap).

**Not shortlisted:**
- G02, G14 and G30 (WEAK).
- G26 (REJECT as a headroom task; its idea is embedded in S5).

**Family balance:**

- Two designs share the point-in-time family (S1, S5). This is deliberate: it is the only family with a proven 0/3
  result, and the build order uses S1 to decide whether S5 is worth its cost.
- Two designs touch censoring (S4 demand; S8 labels). Their estimation problems differ: S4 is a stopping-time demand
  estimator graded against truth; S8 is a deterministic maturity/label state table.
- S2 is the only design whose main grade is a propensity-weighted estimator. S8's policy layer is capped at one pooled
  check so it does not duplicate S2.

---

## S1: G08 forecast vintages

- **Why selected:**
  - Strongest realism in its panel (9).
  - Deterministic exact grading.
  - Its hard core (features as-of the 06:00 London issue instant; training membership as-of each monthly refit;
    scoring against the first valid settlement run) is the same class as Task 02's only proven 0/3 failure, moved to a
    different domain (energy/volume forecasting) with different artifacts.
- **Unique capability tested:** reconstructing per-forecast-origin knowledge state across three clocks at once:
  - publication/withdrawal status history;
  - vendor `available_at` for hindcasts;
  - local issue time across DST.

  It also requires distinguishing a KPI's first-valid vintage from its latest revision.
- **Expected hardness:** MEDIUM-HARD. Prior for Gemini 3 Flash: 0–1/3.
  - The main risk to that prior is that a strong agent writes a timestamp as-of join straight away; the real bites are
    withdrawn runs, DST and vendor-B `available_at`.
- **Implementation cost:** ≈4 build-days (generator for runs/revisions/withdrawals/weather vintages; faulty repo; stdlib
  reference; 3 hidden worlds; mutation suite).
- **Verifier strategy:**
  - **Exact checks:** feature matrix per (series, origin) and training-membership manifest per refit, with features in
    canonical column order.
  - **Scoring check:** exact settlement-vintage actuals table.
  - **Predictions:** not graded bit-for-bit, because HGBR is column-order sensitive (tournament §3 #13). If graded at
    all, they are recomputed by the verifier from the agent's features.
  - **Hidden fixtures** vary DST alignment, withdrawal frequency and vendor switch dates. At least one mechanism is
    absent from the visible snapshot window.
- **Required fixes before build:**
  - Remove `v_latest_volumes`.
  - Limit `feature_snapshots` to non-incident days.
  - Specify vendor precedence after 2026-06-15 and "latest run" ordering (`run_ts` vs `available_at`).
  - Remove variants A/B as the advertised wrong path; make the timestamp-as-of-join-with-current-status the documented
    natural wrong implementation.
- **Main validity risk:** the snapshot tables and published KPI CSV still act as row-level answer keys, or "real-time
  vs revised training data" is a legitimate modelling choice the verifier would reject. Mitigation: the instruction
  states the backtest's purpose (replicate what the live system knew), and hidden fixtures move incident days outside
  snapshot coverage.

## S2: G24 recommender off-policy evaluation

- **Why selected:**
  - Highest novelty and specification score in R1's panel (uniqueness 8, verifier 8).
  - The only design whose central grade is a statistical estimate against generator ground truth with a principled SE
    tolerance.
  - It establishes the truth-with-tolerance verifier pattern that S4, S6, S7 and S8 reuse.
  - Its interaction is genuinely natural: the on-policy per-serve check (~0.34) agrees with the biased estimator,
    not with the per-decision truth.
- **Unique capability tested:** deriving propensities at the right decision grain for slate/position logging, then
  collapsing reloads into decisions:
  - item-in-slot marginal per device layout;
  - 10-minute cache reload collapse;
  - on-policy sanity check at the right grain;
  - launch decision under paired uncertainty.
- **Expected hardness:** MEDIUM-HARD. Prior: 1/3.
  - OPE-literate agents may do this well once the logging marginal is found. The non-trivial Plackett–Luce marginal
    is what keeps it from being textbook.
- **Implementation cost:** ≈4.5 build-days (logging-policy simulator with Plackett–Luce marginals; click model with
  position bias; extract cut from ~170MB to ≤40MB; tolerance pilot).
- **Verifier strategy:**
  - Policy values for three candidates within ±3 SE of generator truth (SE computed by the verifier from the realised
    log).
  - Exact launch decision.
  - Exact decision-grouping table on a sampled window.
  - Hidden fixtures vary logging temperature, layout mix and which candidate truly wins.
- **Required fixes before build:**
  - Non-trivial logging marginal (softmax/Plackett–Luce over v6 scores).
  - Delete the `unpaired_ci` mutation (unpaired SE ≈1.08× paired; it would pass).
  - Specify window-boundary decisions and view/click consistency.
  - Reduce extract size.
  - Phase-0 margin simulation: oracle pass ≥99%; the position-unaware SNIPS, 1/M and per-serve estimators each fail
    ≥99%.
- **Main validity risk:** headroom. A frontier agent that knows slate OPE may solve it in ~35 actions. Second risk:
  SNIPS with weights ~M⁵ has heavy tails, so tolerance pilots may force a wide band that admits wrong estimators.

## S3: G23 readmission episodes

- **Why selected:**
  - Most realistic design in the pool (realism 9).
  - Cleanest deterministic grading (verifier 8).
  - Its attractors sit on the path: the "sicker patients" notebook, the disposition map, the death-censoring review
    notes.
  - Its trusted historical baseline (14.8%) is itself inflated, so "matches the old number" is the wrong validation.
- **Unique capability tested:** episode construction across facilities whose codes mean different things. Transfers
  coded "Other Facility" (70) must be recovered from the receiving hospital's point-of-origin code. Eligibility and
  score come from the episode's final stay; planned readmissions come from procedure/diagnosis tables; deaths stay in
  the denominator. The agent must also reject a plausible trusted aggregate.
- **Expected hardness:** MEDIUM. Prior: 1/3.
  - Healthcare-measure priors are strong, and gaps-and-islands gives transitive chains for free. Headroom comes from
    the vocabulary trap plus the inflated baseline.
- **Implementation cost:** ≈3.5 build-days (encounter generator across 6 hospitals; procedure/diagnosis tables; stdlib
  episode reference; 3 hidden worlds).
- **Verifier strategy:**
  - Exact episode table (stay → episode id).
  - Exact index-eligibility and outcome table.
  - Rate and AUC recomputed by the verifier from the agent's scored index stays.
  - Hidden fixtures vary the share of 70-coded transfers, back-transfer frequency and planned-procedure mix.
- **Required fixes before build:**
  - Rebuild the timezone mechanism so it changes membership (make back-transfers common, or use discharge-instant vs
    admission-instant ordering), or drop it.
  - Every true 70-coded transfer carries origin 4, and non-transfers carry a clearly non-transfer origin.
  - Add "calendar day at the discharging hospital" to the measure glossary.
  - Thin the measure document to definitions plus a worked historical case; no sentence stating episode propagation.
- **Main validity risk:** the either-side documentation rule (disposition 02 OR origin 4) is an institutional
  convention that a clinically sophisticated agent might override. Mitigation: make clinical truth and the documented
  rule coincide in the generator, so no correct-in-reality answer fails.

## S4: G10 censored demand

- **Why selected:**
  - Highest post-tournament score (76): cheap-solve 8, natural-wrong 8, investigation 8, realism 9, difficulty 9.
  - Every natural repair fails for a principled reason: drop zeros, clean days only, trailing mean, and even
    sales ÷ in-stock fraction (biased +25% at inventory 8 on sell-out days).
  - The design author fell into this last trap, which is strong evidence it is natural.
- **Unique capability tested:** recognising that stock-out time is a stopping time and estimating latent demand with
  a censoring-aware method. It also requires reconstructing true in-stock intervals from effective-time inventory
  events rather than a close-snapshot flag that misses ~42% of stockout days, with local store hours and DST.
- **Expected hardness:** HARD. Prior: 0/3.
- **Implementation cost:** ≈5 build-days after the scope cut (inventory event generator with posting vs effective
  times and count corrections; Poisson intraday demand; censored-Poisson reference; tolerance pilot; 3 hidden worlds
  including one where the v4 model truly is better).
- **Verifier strategy:**
  - Exact stockout-interval / flag table.
  - Demand estimates graded against generator E[D] with stratified tolerance: by inventory level, and separately on
    sell-out days, where the profile-scaling bias concentrates.
  - Exact model-comparison decision.
  - The hidden fixture flips which model is better.
- **Required fixes before build:**
  - Censoring-aware oracle derived from the generator.
  - Re-measure every margin.
  - Drop substitution grading; consider dropping POS outages.
  - Rewrite the `in_stock_minutes` contract in business language.
  - Resolve the shrink contradiction.
- **Kill criterion (Phase 0):** if no tolerance simultaneously passes two independent correct censoring-aware
  estimators ≥99% and fails profile-scaling ≥99% on sell-out strata, drop the estimator grade. Keep only the exact
  interval table and decision, or abandon.
- **Main validity risk:** any correct estimator family (censored Poisson MLE, Kaplan–Meier-style intraday profile,
  EM) must pass. If they disagree by more than the bias being detected, the task is ungradable.

## S5: G11 training–serving skew (scope-cut, with embedded negative control)

- **Why selected:**
  - Highest pre-tournament composite (76.0), with difficulty 9.
  - It generalises Task 02's failure from one renewal model to an online-serving feature contract, with several
    features whose knowledge times differ.
  - After the scope cut and the embedded control, it combines the benchmark's strongest hardness family with the only
    principled negative control in the pool.
- **Unique capability tested:** serving-time semantics per feature:
  - M1: which published snapshot existed at request time, including failed runs and cadence;
  - M4: identity mapping at ingest vs at request, for merges;
  - M6: `on_miss` defaults and expired vs stored-NULL.

  Plus deciding that one flagged skew is genuine population drift (a new city launch) and leaving it unchanged.
- **Expected hardness:** HARD. Prior: 0/3.
- **Implementation cost:** ≈5 build-days after the cut (the original estimate exceeded 4 days for 5 mechanisms; the
  cut removes two mechanisms but adds the control feature and its hidden fixture).
- **Verifier strategy:**
  - Exact training-feature matrix for the three repaired features.
  - Exact equality of the drift feature with the untouched original.
  - Registry-driven `on_miss`/expiry per field.
  - No 1e-6 prediction check.
  - Hidden fixtures vary run-failure calendars, merge rates and whether the drift feature drifts.
  - Every graded mechanism must be determinable from ≥30 logged serving rows or a fact table; otherwise it is graded
    only at per-feature threshold level.
- **Required fixes before build:**
  - Apply the scope cut.
  - Resolve expiry semantics (key-level vs field-level) in `feature_views.yaml`.
  - Design the drift feature so the skew report ranks it top-2.
  - Serving logs must cover too few rows to diff every mechanism: they sample ~0.65%, and one mechanism is absent from
    the logged window.
- **Main validity risk:** cost, and serving logs acting as row-level answer keys. Second risk: the negative control is
  passed by agents that never engage the drift feature. Mitigation: the memo asks for every flagged feature to be
  resolved or justified, and the verifier requires an explanation entry for it in the incident output. That entry is
  graded by exact enum (`genuine_drift`), not free text.
- **Go/no-go:** build only after S1's baseline. If Gemini 3 Flash scores ≥2/3 on S1, re-examine whether S5's
  mechanisms add hardness beyond S1 before spending 5 days.

## S6: G05 staggered rollout difference-in-differences

- **Why selected:** the only observational causal-inference design in the pool. Its two core traps are principled and
  confirmed by simulation:
  - an event-study/CS base week that falls inside install closures;
  - a competitor-closure confounder that region×week FE alone does not remove.

  Fiscal calendar (Sunday-start, 53-week year) and install-log go-live add realistic state reconstruction.
- **Unique capability tested:** choosing comparison periods that satisfy the estimand when the treatment itself
  disrupts the pre-period, and finding a store-level confounder through heterogeneity (W3/R4) or a placebo rather than
  a named table.
- **Expected hardness:** MEDIUM-HARD. Prior: 1/3.
  - Imputation/CS-literate agents may pass once the non-comparable weeks are found.
- **Implementation cost:** ≈4 build-days (store-week panel generator with install dips, ramps, region seasonality,
  trade-area overlap; symptom rework; tolerance pilot).
- **Verifier strategy:**
  - Overall and per-wave ATT within ±τ of generator truth; τ from the Phase-0 pilot.
  - Exact comparable-week panel flags.
  - Exact go-live week per store.
  - Accepted specifications: imputation, CS with a valid base, region×week FE + exposure.
  - Hidden fixtures vary wave timing, confounder location and effect sign (one negative).
- **Required fixes before build:**
  - Replace the TWFE −2.3% symptom with a simulated-feasible one (e.g., the event-study readout in the memo is
    inflated by the dip).
  - Put region×week effects in the oracle, or remove the region×season term.
  - Accept region×week + exposure explicitly.
  - Move competitor data into a realistic wider warehouse; don't name ValuMart.
  - Make hidden_a competitor openings visibly sized, or drop them.
- **Main validity risk:** rejecting reasonable specifications, and the dependence on finding the confounder. If the
  confounder can't be found without a neon sign, the task becomes underspecified. If it can be found easily, it
  becomes easy. The Phase-0 pilot must show that the no-confounder estimator fails *per wave* (W3) with margin, not
  only overall.

## S7: G25 search judgment pool

- **Why selected:**
  - Rose most in the tournament (#14 → #7).
  - Its attractor is genuine and on path: fixing the join first makes candidate B look *worse* (Δ −0.034), reinforcing
    the wrong launch conclusion.
  - Re-canonicalising stored keys through `qnorm_v3(query_key)` is the natural reuse of existing library code and is
    wrong (fraction normalisation bug).
  - Fixes are cheap.
- **Unique capability tested:** reconciling relevance labels across rounds with different query-key forms, grading
  scales and product grain (GTIN offer inheritance). It then requires estimating unjudged relevance from the right
  audit frame: R09 pairs still unlabelled *after* resolution.
- **Expected hardness:** MEDIUM-HARD. Prior: 1/3.
- **Implementation cost:** ≈3.5 build-days (query/offer/judgment generator across rounds; normaliser versions;
  audit sample; NDCG reference).
- **Verifier strategy:**
  - Exact resolved-qrels table (query, product, gain).
  - ΔNDCG within ±τ of generator truth ("as if every product judged").
  - Exact launch decision.
  - Hidden fixtures vary the collision rate, the share of 3P GTIN offers and which candidate truly wins.
- **Required fixes before build:**
  - Add `task_id` to judgments (collision twins).
  - Widen the frame-restriction trap to ≥2.5τ.
  - Remove key form and scale from `rounds.yaml`.
  - Remove `gtin` from judgments so the catalog join is required.
  - Express the RG-3 "Partial" guideline as rater examples rather than a crosswalk.
- **Main validity risk:** underspecification of expected-gain vs plug-in IDCG, and of A's 4% unlabelled share outside
  R09's frame. The tolerance absorbs both, and the pilot must confirm that absorbing them does not also admit the
  unrestricted-frame estimator.

## S8: G01 collections label maturity

- **Why selected:**
  - Third post-tournament (69).
  - Its chain of natural wrong repairs is the best in the pool: early-read filter only → value dates plus a global
    30-day maturity → per-source max-coverage watermark → unweighted untreated pool.
  - The acquired servicer's held June file is visible only at row or manifest level.
- **Unique capability tested:** building a label-state table where maturity depends jointly on value date vs posting
  date and on per-source file completeness for an acquired book. The agent must recognise that a coverage watermark
  per source is not per-episode completeness.
- **Expected hardness:** HARD. Prior: 0–1/3.
- **Implementation cost:** ≈5.5 build-days, the most expensive (hub and servicer payment generators; monthly file
  manifests with a held file; episode reference; policy layer; hidden worlds).
- **Verifier strategy:**
  - Exact episode-label table (primary grade).
  - Exact per-source completeness table.
  - Vintage AUC recomputed by the verifier from the agent's labels.
  - One pooled above-threshold cure-uplift check against truth, SE-gated (status graded only where |truth − threshold|
    ≥ 2.5 SE).
  - Hidden fixtures move the held file, change servicer cadence and alter maturity lag.
- **Required fixes before build:**
  - Reduce the policy layer to the pooled check, or remove it if Phase-0 margins fail. This keeps S8 from duplicating
    S2.
  - Adopt the mid-month re-cut.
  - Define episode→source completeness.
  - Keep the README output schema from naming uplift or strategy periods.
  - Drop PH-2 pause and informative censoring (R6).
  - Resolve early-cure-incomplete-window and HPF + hub-payment conventions.
- **Main validity risk:** exact label-table conventions are brittle (early cure with an incomplete window; accounts
  with both servicer and hub payments). Mitigation: every convention must be determinable from the dictionary or a
  worked historical example, and the mutation suite includes two independent correct implementations written from
  the agent-visible docs only.
- **Replacement trigger:** if the generator exceeds ~6 build-days or Phase-0 fails, replace with G21 (after its
  censoring rule swap).

---

## Build order (maximises early information)

Easiest-first would tell us little. This order resolves the largest uncertainties first, reuses verifier
infrastructure, and puts the most expensive builds behind go/no-go gates.

| Step | What | Information gained | Gate for |
|---|---|---|---|
| **0** | **Phase-0 margin simulations** (no models, no task files) for S4 G10, S2 G24, S6 G05, S7 G25, S8 G01. Each shows oracle pass ≥99% and each named wrong estimator failing ≥99% at the chosen tolerance. ≈2 build-days total. | Which truth-graded designs are gradable at all. The tournament found broken margins in 6 of 15 designs, so this is the cheapest way to avoid building ungradable tasks. | S2, S4, S6, S7, S8 |
| **1** | **S1 G08** | Does Task 02's per-row knowledge-state failure transfer to a new domain and artifact set? This is the benchmark's only proven-hard family. | S5 go/no-go |
| **2** | **S2 G24** | Is a *statistical* estimator task (graded against generator truth) hard for frontier agents, independently of state reconstruction? Also builds the truth-with-SE-tolerance verifier and hidden-world machinery reused by S4/S6/S7/S8. | Effort allocation between statistical and state tasks |
| **3** | **S3 G23** | Does thinning documentation alone (definitions plus worked example, no propagation sentence) create headroom on a deterministic grain task? Tests whether the "don't over-document" lesson is sufficient. It is also cheap (≈3.5 days), so this evidence arrives before the expensive builds. | How aggressively to thin docs in S4–S8 |
| **4** | **S4 G10** | The hardest expected task; combines state reconstruction (in-stock intervals) with a censoring estimator. Reuses S2's tolerance machinery and S3's doc-thinning evidence. | — |
| **5** | **S5 G11** | Only if S1 shows headroom. Multi-feature serving semantics plus the negative control. | — |
| **6** | **S6 G05** | Causal-panel coverage. Its symptom rework and tolerance pilot build on S2/S4 experience. | — |
| **7** | **S7 G25** | Identity reconciliation plus audit-frame estimation with an on-path worsening attractor. | — |
| **8** | **S8 G01** | Most expensive. Built last, so its policy layer can be cut or dropped based on S2's result (if S2 shows IPW-over-exploration is easy, keep only the label-state core), and its doc thinning follows S3's evidence. Replace with G21 if gated out. | — |

**Recommended baselining cadence (for later approval; nothing is run now):** baseline each task as soon as its
validation passes, in pairs (1–2, 3–4, 5–6, 7–8). Build decisions can then react to evidence, which the gates above
assume.

**Total effort:** ≈35.5 build-days for the eight tasks (S1 4, S2 4.5, S3 3.5, S4 5, S5 5, S6 4, S7 3.5, S8 5.5), plus
≈2 days of Phase 0, plus validation/mutation/harbor-check overhead already included per task.

The two gated tasks (S5, S8) account for 10.5 days. If both are gated out and replaced by alternates (G17 ≈4,
G21 ≈4), the total falls to ≈33.

## Per-build acceptance checklist (lessons from Tasks 03/05/06 and this tournament)

1. **No answer key in the workspace.** For every agent-visible file: could a reader write the fix from this file
   alone? If yes, rewrite it as facts, examples or schema.
2. **No helper-code answer.** Faulty code contains no target cutoff, no nearly-correct branch and no fix comment.
3. **The stated natural wrong implementation is real.** Before sign-off, an independent reviewer writes the first
   repair they would make from the memo and the first-read files. It must fail the verifier.
4. **Margins are measured.** For truth-graded outputs, Phase-0 numbers are regenerated from the actual generator, not
   the design prose.
5. **Attractors are on the path.** Tempting evidence appears in files every agent must read (memo-cited reports, the
   faulty pipeline, the KPI table), not in optional notes.
6. **Validation needs row/state checks.** At least one hidden fixture passes the visible aggregate but fails a
   row/state table under the natural wrong repair.
7. **Standard harness.** Oracle 1 / Nop 0; mutation suite; `harbor check`; sandboxed verifier pattern from Tasks
   03–06; secret scan; frozen checksums for Tasks 01–06 unchanged.
