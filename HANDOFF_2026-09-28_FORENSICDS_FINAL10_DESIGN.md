# HANDOFF — ForensicDS final-10 benchmark design
**Date:** 2026-09-28 · **Repository:** `/Users/yashshah2311/forensicds` · **Branch:** `final10` · **HEAD:** `7e6d4d7`
**Mode:** research and design only. Nothing built, nothing modified, no model run.

Self-contained. Every empirical number was recomputed from repository files during this phase unless marked as
quoted. Three previously unrecorded defects were found in **frozen** artifacts; they are reported, not repaired.

---

## 1. EXECUTIVE FINDING

### What ForensicDS actually measures

The original hypothesis — that agents fail because they omit the discriminating test — was **prospectively
disconfirmed**. 8 of 9 trials attempted at least one inventoried discriminating route and 8 of 8 applicable trials
revised after a contradiction. All nine still failed.

The frozen record already contains the sharper finding, and it is the correct foundation for the final 10.
`research/phase3/HANDOFF_2026-09-24_PROSPECTIVE_RESULTS.md` §18, verbatim:

> "Pattern: validation was performed on the quantity the trial regarded as the answer, and not on the quantities it
> had assumed. **In every failing case the unvalidated quantity is the one that failed.**"

And §19, on why the validation that *was* performed had no power:

> "**Yes, in 8 of 9 trials, and in every case the coherence check passed while the analysis was wrong.**"
> — p22 #3: *"I've double-checked the calculations for `attribution_pp`, and it's spot on… I'm pleased with the
> numerical consistency."* The five components sum to the observed change **by construction**, so this check
> cannot fail regardless of how the residual is allocated.

Combined with the phase-1 audit's mechanism (`research/audit/AUDIT_2026-09-23.md` §11), the capability under test
is this:

> **ForensicDS measures whether an agent can tell an arithmetic identity from a test.**
>
> An agent inherits messy operational evidence and a plausible incumbent analysis. It commits early to an object
> or an identifying assumption — usually in one code-writing step in the first third of the trajectory. Every
> check it then runs is computed *inside* that commitment, so the check is an identity that holds by
> construction and confirms the frame regardless of whether the frame is right. The agent validates what it
> computed and never validates what it assumed. The decision is then right or wrong by the margin, independently
> of everything above.

**Working descriptive label: COHERENT-BUT-WRONG ANALYTICAL COMMITMENT.** This is a description of an observed
pattern across 45 discovery trials and 9 prospective trials of **one** flash-tier model. It is not a causal claim,
it is not a claim about frontier models generally, and the prospective set was explicitly "sized to detect a gross
departure, not to estimate a rate."

### The single design consequence

Every task in the final 10 must contain **at least one decision-relevant quantity that the natural analysis path
assumes rather than estimates**, and the obvious internal check on that path must be an identity that holds
whether or not the assumption is true. This is the *assumed-quantity principle*, and it is what P22 accidentally
demonstrated: all three trials wrote `"tooling": 0.0` as a literal, their five components summed correctly by
construction, and the token `wear` appears **zero times** in all three trajectories.

### The strongest empirical regularity, and its one refinement

`research/audit/leakage_findings.md`: every task whose scientific object is **stated** in a workspace document was
solved (3/3 or 2/3); every task whose object must be **derived** from how the data came to exist was unsolved
(0/3) — with G34 the single exception. The refinement matters: G34 is "derived" but was solved 2/3 in **18–20
steps at $0.035/trial, twice without querying the warehouse at all**, because its derivation is one textbook
substitution (Kaplan–Meier → cumulative incidence). So:

> **Derived is necessary but not sufficient. The derivation must not be a one-step recall of a named estimator,
> and it must require reconstructing a process the data only partially records.**

---

## 2. EVIDENCE THAT MOTIVATED THE SLICE

The two evidence bases are kept strictly separate. They are **not** pooled anywhere in this document.

### 2a. Discovery / five-task evidence (2026-09-12 → 2026-09-22)

| quantity | value | provenance |
|---|---|---|
| shipped suite | Task02, G05, G10, G24, G34 | `scripts/final_tasks.json` |
| trial successes | **2 / 15 = 13.3 %** (Wilson 3.7–37.9 %) | recomputed from `jobs/*/verifier/reward.txt` |
| task pass@3 | **1 / 5 = 20 %** (G34 only) | recomputed |
| measured pool (as packaged) | 12 tasks / 36 trials / 18 successes / 8 with pass@3 | `report/data/results.json` |
| measured pool (audit, adds G41/G42/G44) | 15 tasks / 45 valid trials | `AUDIT_2026-09-23.md` §2 |
| Oracle / Nop | 1 ×5 / 0 ×5 | `jobs/final-oracle-*`, `jobs/final-nop-*` |
| falsification-class checks in 45 trials | **one**, and it was on a diagnosis rather than on the trial's own estimator | `AUDIT_2026-09-23.md` §19.4 |
| decision right, science wrong | **6 of 13** failed trials; on G24 3/3 trials and 12/12 extract-level decisions | `quantitative_evidence.md` §7 |

**Selection caveat, stated by the project itself:** "The suite was selected using the same trials we report. The
20 % figure is therefore an optimistic (low) estimate."

### 2b. Prospective evidence (frozen 2026-09-23, run 2026-09-24)

Pre-registered plan `research/phase3/analysis_plan.md`, sha256
`c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824`, **one commit in its entire history**.

| quantity | value |
|---|---|
| tasks | P22, P20, P31, frozen at `a0570585c3927b53` / `2c3c374b07f233fa` / `e18bf13d6080f987` (all re-verified this phase) |
| valid trials | **9 / 9**, 0 invalid, 0 replacements; all `digest_matches_freeze: true`; all nine input-DB digests MATCH |
| model | `google/gemini-3-flash-preview` via `gemini-cli`, one family only |
| result | **0 / 9 successes, 0 / 3 pass@3** |
| cost | **$1.4667** |
| criterion totals | evidence_reconstruction 8/9 · scientific_object 8/9 · identification 4/9 · estimator_implementation 8/9 · quantitative_results 2/9 · independent_validation 8/9 · decision 2/9 |

| prediction | observed | status |
|---|---|---|
| P1 — ≥70 % of failures attempt no discriminating route | **1 of 9 (11 %)**; 8 attempted one, 6 attempted two or more | **DISCONFIRMED** (plan's own disconfirming outcome met) |
| P2 — L3-attempting trials pass more | 0/8 vs 0/1 | **NOT EVALUABLE** |
| P3 — first error at a commitment step in ≥60 % | 5 of 9 (56 %) | just below threshold |
| P4 — ≥40 % of failures pass ≥3 own coherence checks | **8 of 9 (89 %)** | above threshold |
| P5 — decision right / quantity wrong in 20–50 % | 2 of 9 (22 %) | inside band |
| P6 — revision after self-contradiction in <20 % | **8 of 8 (100 %)** | **DISCONFIRMED** |
| P7 — P31 wrong verdicts skew to `incumbent_incorrect` | **0** did | direction not observed |

**This is the evidence that motivates the slice.** Recognition is not the bottleneck; route-taking is not the
bottleneck; revision is not the bottleneck. What fails is the validation of assumed quantities, and the reason is
structural: the checks available inside a committed frame are identities.

---

## 3. COMPLETE EXISTING-TASK AUDIT

Twenty task identities carry ≥1 `gemini-3-flash-preview` solver trial; 64 such trials exist. "Object stated?" is
from `research/audit/leakage_findings.md`, independently corroborated this phase.

| task | professional scenario / decision | statistical object | competing interpretation (the wrong one) | why it stays coherent | mechanism | Gemini | O/N | check | mutations | object stated? | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Task02** `02-renewal-risk-regression` | B2B SaaS renewal-risk model scored 0.936 offline, 0.750 live; **no decision is graded** | 25 features as of `renewal−90d`, admissible only if `synced_at <` cutoff; AUC of the fixed model | reconstruct on the business commit clock `changed_at` (misstates 149 visible examples), or neutralise the leaky features | eval AUC lands near the correct 0.78 for several wrong repairs; both hard-coded-schedule repairs pass all 16 visible checks and fail only `hidden_c` | availability-time provenance | 0,0,0 | 1/0 | 1 (11/11; TB3 10/35 fail) | 21/21 | **not stated** | **KEEP, must add a graded decision** |
| **G05** `g05-sco-rollout-gate` | 900-store self-checkout rollout; release tranche-2 capex iff gate ≥ 2.5 % | store-weighted causal uplift in **log net sales**, event weeks 12–25, transported to waves 5–6 **planned kit mix** | two-way FE with store+week only, on **basket size**, over the **pooled installed estate** (+5.5 %, +6.6 %) | the house method since the ESL readout; every wave individually significant with a monotone "learning curve"; the panel is byte-exact; the decision can still come out `stop` | staggered adoption + treatment-version transport | 0,0,0 | 1/0 | 1 (11/11; TB3 8/35 fail) | 38/38 | **not stated** | **KEEP** |
| **G10** `g10-censored-demand` | grocery replenishment; 8 category buy actions + extend LEAN-26 or not | per store-SKU-day posterior mean of latent demand given observed sales and in-stock exposure | "sales are demand on clean days" — drop or mean-fill stockout days, or scale by in-stock share | `lost = expected − sold ≥ 0` holds by construction; all three trials stopped once the ice-cream trend turned positive — the sign the brief supplied | latent quantity under endogenous censoring | 0,0,0 | 1/0 | 1 (11/11; TB3 5/35 fail) | 33/33 | **not stated** | **KEEP, two fixes** |
| **G24** `g24-recommender-ope` | streaming home-row ranker; launch v6 / v7 / v7_pd | expected home-row clicks **per slate decision** if π had served; propensity 1/m over the **eligible** pool | weight by the pre-filter pool K, or by the logged `propensity` (≈1e-7, logged *before* `rules.apply`), and treat each serve as a decision | every wrong variant reproduces the sign AB-1182 measured; the launch decision is right **3/3 trials, 12/12 extract-level** | logged-policy recovery (action space, propensity, decision unit) | 0,0,0 | 1/0 | 1 (11/11; TB3 5/35 fail) | 30/30 | **not stated** | **KEEP — strongest single task** |
| **G34** `g34-fleet-reliability-gate` | pump spares build; expanded vs baseline at 28 % | cause-specific cumulative incidence at 36 months, overhaul/retirement as **competing outcomes** | 1 − KM with overhaul and retirement censored — which is *correct* for the engineering question (0.5547) | four fractions sum to 1.000000 so conservation passes; the prose diagnosis is correct | outcome-role assignment | 0,1,1 | 1/0 | 1 (11/11; TB3 9/35 fail, one disputed) | 21/21 (raw artifact lost to `/tmp`) | not stated **but one-step** | **DROP from a stronger suite** |
| **G08** `g08-forecast-accuracy-vintages` | electricity supply; model board retires v3 or keeps it | paired WAPE of the **11:00 gate-locked** forecast against the **Initial Settlement** volume that was the live charge basis at KPI close | score against **latest settled volumes including reconciliation** — argued in the workspace by the Data Platform lead: *"the closest thing to the truth we have… restating history on the better data is the point"* | the January RESI pack cell **rounds to the published value under reconciliation actuals**, giving a false confirmation | decision-relevant vintage selection | 0,0,1 | 1/0 | 1 (×4) | 40/40 | **partly stated, across ~10 docs; no single doc states the object** | **PROMOTE with 2 fixes** |
| **G41** `g41-service-parts-rebalancing` | field-service parts; expedite or not at 40 units | minimum unmet demand over the **issuable, movable** feasible set, then least-cost plan attaining it | net-requirements planning: shortfall against nominal on-hand, filled greedily on cheapest lanes | arithmetic correct, depot totals tie, reconciles with last week's readout; both failures **named min-cost max-flow and implemented greedy augmentation without residual arcs** (68 unmet where 46 is achievable) | feasible-set reconstruction + optimum | 0,1,0 | 1/0 | **1 (TB3)** | 14 wrong states rejected on ≥3/4 | object stated, **execution** unstated | **PROMOTE** |
| **G42** `g42-contractor-safety-rate` | contractor TRIR | recordable cases per 200k hours worked | — | — | aggregation/denominator | 1,1,1 | 1/0 | none | 12 wrong separate | **stated** — every rule is in a table in a named doc | **REJECT** |
| **G44** `g44-screening-precision` | payments fraud screen; accept or remediate | precision transported to the contracted prevalence | precision on the flagged panel (5.1× the contracted fraud rate) | the two published figures corroborate each other; the screen genuinely has se 0.964 / sp 0.998 | prevalence transport | 0,1,1 | 1/0 | none | 12/12 on 4/4 | **partly** — target rate is **given** in the contract | **REWORK** |
| **P22** `p22-gauge-recalibration` | machined manifolds; raise supplier nonconformance or not (5.5 % limit) | instrument offset on a single measurement reference, corrected nonconforming rate, five-way attribution | attribute the residual to material and **assume tooling is zero** | the five components sum to the observed change **by construction** | measurement-system change | 0,0,0 | 1/0 | **NONE** | 15/15 + 2 exploit | not stated | frozen — see §5 |
| **P20** `p20-noshow-monitoring` | clinic no-show model; retain / replace / remediate | AUC on the policy-invariant holdback; reminder effect; 5-way AUC attribution | drift analysis + retrain on recent data (the industry's standard remedy, and the wrong action) | attribution components required to sum to `validation − monitored` and do, irrespective of correctness | policy feedback on the evaluation population | 0,0,0 | 1/0 | **NONE** | 15/15 + 2 exploit | not stated | frozen — see §5 |
| **P31** `p31-fill-rate-dispute` | supplier fill-rate dispute; adjudicate incl. abstention | which instrument governs; contractual fill rate; bridge; three three-valued adjudications | accept the incumbent, or overturn it, where the honest answer is that Schedule 4 is unexecuted | the bridge closes on the visible extract ("perfectly aligned") and is wrong on hidden_a | instrument governance + principled deferral | 0,0,0 | 1/0 | **NONE** | 15/15 + 2 exploit | not stated | frozen — **has a verified F8**, see §5 |
| task01 `01-revenue-reconciliation` | revenue reconciliation | canonical-account attribution, all periods | rival *causes*, not rival objects | — | join cardinality / entity resolution | 0,1,1 (+3 quota-invalid, +3 rpm-invalid) | 1/0 | 1 | — | **stated** (§3 is a numbered procedure; the discriminator was whether one file was opened) | OUT |
| task03 `03-lead-score-evaluation` | lead-score monitoring | AUC on the score-independent exploration holdout | none | — | selective labels | 1,1,1 | 1/0 | 1 | — | **stated — deliberately**, to satisfy the `behavior_in_task_description` rubric check | OUT |
| task04 `04-retention-metrics-regression` | board NRR | retention on the current extract | **reporting vintage**: `signed_at ≤ quarter_end + 12d`, which **reproduces six published quarters to 4 dp** because the workbook was generated with that rule | reproduces the published workbook exactly | reporting vintage vs restatement | 0,0,1 | 1/0 | 1 | — | partly; the attractor is unstated | OUT as built, mechanism noted |
| task05 `05-onboarding-experiment-readout` | experiment readout | ITT at the workspace unit | none — the pre-registration states all seven properties | — | post-treatment selection | 1,1,1 | 1/0 | 1 | — | **stated** (the plan is an answer key) | OUT |
| task06 `06-usage-statement-close` | usage billing close | bitemporal statement at close knowledge | none | — | bitemporal + non-linear rating | 1,1,1 | 1/0 | 1 | 29/29 | **stated** — two verified leaks: `statement_close()` is already correct in the agent's code, and `ledger/issued/` contains correct target output | OUT |
| G35 `g35-dispatch-priority-gate` | dispatch saturation pilot; fund FY27 at +1.5 pts | full-rollout policy effect τ_policy | **CW1** — the total effect in the 50 % arm, "a real causal effect at the wrong saturation", which flips the decision | CW2/CW3 pass every coherence check a reviewer would run | interference / general equilibrium | 1,1,1 | 1/0 | 1 | 12 wrong pre-registered | **stated** — the output contract performs the estimand selection | OUT as built, **mechanism is a top rebuild** |
| G36 `g36-tou-capacity-gate` | TOU tariff capacity; procure or defer | estate mean peak kW with the whole estate on tariff, under forecast weather | **W8** selection-fixed-only and **W9** temperature-fixed-only — each a correct diagnosis with a correct partial fix, each 10–12 sd wrong with a wrong procurement call | both are internally coherent and neither is a strawman | two-axis transport (selection × regime) | 0,0,0 as graded; **2/3 under a corrected estimand** | 1/0 | none | — | not stated | **artifact dead** (CE06 passes the forecast verifier with a wrong aggregation); **mechanism is the top rebuild** |
| Task02-EI `…__explicit-invariant` | instruction ablation | — | — | — | — | 0,0,0 | 1/0 | none | — | n/a | **OUT — confirmed F8**, `tests/reference.py` never selects `synced_at` for `support_tickets`; its 0/3 is uninterpretable |

---

## 4. CURRENT-FIVE AUDIT

The required question: **what exact competing interpretation makes this task scientifically interesting?**

| task | competing interpretation | convincing? | unique contribution |
|---|---|---|---|
| **G24** | weight by the pre-filter pool K, or by a logged propensity that was written *before* the rules layer ran, and treat a serve as a decision | **YES, strongest in the suite.** All three failures are byte-identical to pre-registered mutations | the only task that grades recovery of the **logging policy and the unit of analysis**, and the only one that demonstrates with measurement that decision-level grading is worthless here |
| **G10** | censoring is non-informative, so sales on clean days are demand | **YES** | the only task whose graded quantity is a **per-row latent posterior** and whose observation window is generated by the quantity being measured |
| **G05** | parallel trends across formats; the pooled installed estate stands in for waves 5–6 | **YES** | staggered adoption **plus** transport of a treatment-version-heterogeneous effect to a population not yet treated |
| **Task02** | reconstruct on the commit clock rather than the load clock | **PARTLY — and this is a finding.** There is no competing *object*. The rivals are rival *causes* of a metric jump and rival *operationalisations* of one agreed object | availability-time provenance at per-example grain. **But it grades no decision at all** — verified: its 13 test names contain nothing decision-like and `instruction.md` contains no decision language |
| **G34** | 1 − KM with overhaul/retirement censored | **NO.** The rival is *cited*, not entertained: `docs/engineering_note.md` says "Ours is not that question and our number should not be used for theirs", the output contract names both objects and asserts the four outcomes are "mutually exclusive outcomes of the same units", and the event dictionary disarms the telemetry trap **in bold** | little that G05 does not. Same test (estimand selection against a stated numeric trigger, published number correct for a neighbouring question) at a fraction of the depth |

### Are these five distinct scientific tests?

**Four are; one is not.** Ranked by distinctness: **G24 > G10 > G05 > Task02 >> G34**.

- **G05 ↔ G34 is the one real redundancy pair** — same capability, different depth. G34: 13 files, 4 tables, one
  textbook substitution, solved 2/3 in 18–20 steps at $0.035/trial, twice **without querying the warehouse at
  all**. Its tolerance multiplier was loosened 3.5 → 5.0 mid-build; its narrowest wrong-analysis margin is
  1.94 τ; the audit rates confidence in its difficulty "**LOW for G34**" and its own baseline analysis concludes
  it has "lower discriminating power … than its design intended".
- **Task02's structural gap:** the slice requires translating a result into a consequential professional
  decision. Task02 does not instantiate the back half. It is also the only gen-1 artifact (34 files, 10 tables),
  so the suite spans two architectures.
- **Two of the five are mislabelled.** Task02 and G10 are *operationalisation* tests — the estimand is stated in
  prose, the construction is not. Only G05, G24 and G34 are "wrong statistical object" tests. Any write-up
  putting all five under one heading is imprecise.

### Newly recorded concern in a shipped task

**G10's verifier installs its test dependencies from the public network at grade time.** Verified:
`candidates/g10-censored-demand/tests/test.sh:54` runs `pip install --no-cache-dir --quiet` with **no
`--no-index`, no `--require-hashes`**, and does not create the venv with `-S` or pass `--noconftest -c /dev/null`.
G24 does it correctly (`--isolated --no-index` from hash-pinned wheels shipped with the tests). This is a
reproducibility and supply-chain gap in a shipped task, already noted inside `g24_prebaseline_validation.md` §7.6.

---

## 5. P22 / P20 / P31 STATUS

All three: Oracle 1 / Nop 0 (three independent runs each), mutations **15/15 as expected + 2 exploit probes at 0**,
frozen manifests re-verified this phase. **`harbor check` was never run on any of them** — confirmed three ways
(`readiness.md` line 1: "`harbor check` was not run: it invokes an LLM judge"; the prospective handoff §4; and the
absence of any check job in `jobs/`).

### A. Would each independently qualify as a strong task?

| task | qualifies? | reasoning |
|---|---|---|
| **P22** | **YES** | The competing interpretation is real and the wrong route is *exactly* what happened: attribute the residual to material while assuming tooling is zero. Method deliberately elementary (paired differences, a proportion), difficulty entirely in identification — which is the design property that separates the hypothesis from "textbook-knowledge gap". |
| **P20** | **YES, and it is the best-designed of the three.** | The naive action (retrain — the vendor's own proposal and the industry's standard remedy) is the **wrong** action, so a lucky decision is unlikely. The holdback clinics are a genuinely policy-invariant population. |
| **P31** | **YES in mechanism, NO as frozen** | It is the only task in the entire repository that makes **principled deferral scoreable**, with `always_defer` and `always_overturn` both tested as mutations scoring 0. But see the verified defect below. |

### B. Unique mechanism each adds

- **P22** — measurement-system change: observed ≠ latent because the *instrument* changed. No other task has
  measurement error at all.
- **P20** — policy feedback: the evaluation population and the outcome are both endogenous to the model's own
  deployment. Opposite correct action to Task02 (do **not** rebuild the pipeline; change the evaluation).
- **P31** — instrument governance and abstention: two metrics under one name, adjudicated by a contract, where
  the honest answer on one extract is "the evidence does not settle this". Also the **only** task in the
  repository where the published number is *right* on some extracts (2 of 4) — the corrective for the structural
  bias that all five shipped tasks have a wrong published number, which an always-disagree agent games.

### C. ⚠ Does including an unchanged copy compromise the prospective interpretation?

**No — but a newly discovered defect changes the answer for P31.**

Three defects were found this phase by recomputing frozen truth read-only from each task's shipped
`tests/world.py` + `scenarios.py`. **I independently verified the first and it is confirmed.**

> **DEFECT 1 (verified by me, decisive). P31 hidden_c: frozen truth contradicts the agent-visible contract.**
>
> `environment/workspace/docs/outputs/readout_contract.md` lines 44–46, verbatim: *"Where the verdict is
> `not_determinable_from_available_evidence`, `bonus_gate_met` and `supplier_claim_payable` shall **also** be
> `not_determinable`."*
>
> Recomputed frozen truth on hidden_c: `incumbent_verdict = 'not_determinable_from_available_evidence'`,
> `supplier_claim_payable = 'not_determinable'`, **`bonus_gate_met = 'no'`**.
>
> **It bit a real trial.** `jobs/p31-prospective-3/.../criteria_notes.txt` records exactly one decision failure on
> hidden_c: `decision: hidden_c: bonus_gate_met 'not_determinable' vs 'no'`. The trial got `incumbent_verdict`
> right and `supplier_claim_payable` right, and failed **solely** on the field where it obeyed the contract.
>
> This is the same class as the G36 defect (`verified_defects.md` D4) and it is why `verified_defects.md` D5
> exists as a standing rule. P31 never had a `harbor check`.

> **DEFECT 2 (reported, not independently re-verified). P22: multiple-valid-method margins are understated.**
> `tolerances.py` and `audits.md` record worst-case accepted-route deviations of 0.75 µm and 0.47 pp. Recomputed
> across all four extracts, hidden_b gives **0.969 µm** against a 1.2 tolerance (1.24×, not the recorded
> "1.5–2×") and **0.683 pp** on `corrected_nonconforming_rate_pct` against 0.7 — i.e. **1.02×**. The route in
> question is the one `task.toml`'s own `solution_explanation` offers as equivalent.

> **DEFECT 3 (reported, not independently re-verified). P20: `feature_feed_defect` is non-zero when no feed
> defect exists.** `truth()` defines it as `hb_repaired − hb_asof`, which differs by the served scores' own noise
> (`score_noise_sd = 0.35`) even at `feed_defect_share = 0.00 %`. Measured: visible −0.00886, hidden_a −0.01712,
> hidden_c **−0.02446** against `ATTRIBUTION = 0.025`. An agent that correctly reports 0.000 for a cause it has
> just proved absent survives hidden_c by **0.00054 AUC**. This is a plausible partial explanation for the two
> prospective trials that reported feed-defect shares of 51.15 % and 63.80 % where truth is 0.00 %.

Also recorded: **P22's published report is not reproducible from its own extract** (report and instruction say
97.0 % → 92.8 % and "7.23 %"; the extract gives 97.25 % → 93.31 % and 6.692 %, so the published figure is 0.54 pp
outside the 0.3 pp tolerance on a number the agent is asked to reproduce). **P31's escalation memo quotes 97.5 % /
91.6 %** where `published_metrics` holds 97.65 / 91.51.

**Consequences for the research record — to be reported, not repaired in this phase:**
1. The prospective **overall** result (0/9, 0/3 pass@3) is unaffected: every trial fails on criteria independent of
   these defects.
2. The **criterion-level** claim `decision 2/9` now carries a known task-side contribution on P31 hidden_c. P31's
   `decision` 0/3 must be reported with that annotation.
3. P7's "direction not observed" is unaffected — no wrong verdict was `incumbent_incorrect`.
4. **Including P31 unchanged in a benchmark would ship a known contract/truth contradiction.** Fixing it breaks
   the freeze. Those are the only two options, and the choice is ChatGPT's.

### D. Can they be included while disclosing the separate prospective study? — **Yes, for P22 and P20.**
Their freeze commit, tag, manifests, plan hash and full results are already public in the repository. A benchmark
release can state: "these three tasks were frozen on 2026-09-23 and used in a separate pre-registered experiment;
their 0/9 result predates this benchmark and is reported at `research/phase3/`." That is more transparent than
most published benchmarks manage.

### E. Would inclusion bias the difficulty estimate? — **Yes, and in a knowable direction.**
We already know P22/P20/P31 are 0/3 each. Including them in a headline pass@3 imports that knowledge. The fix is
arithmetic, not judgement: **report two numbers** — pass@3 over the never-exposed tasks (unbiased) and pass@3 over
the whole suite (biased low, by exactly the same mechanism the five-task suite already discloses). Do not report
one number for a suite that mixes exposed and unexposed tasks.

---

## 6. G41 / G42 / G44 STATUS

### G41 — **PROMOTE**

Two genuinely plausible interpretations. (i) Shortfall against everything the extract shows in a depot, filled
greedily on cheapest lanes — *net-requirements planning*, the house method since the 2024 rewrite, and a method
every planner recognises. (ii) Shortfall against what can actually be **issued and moved**, as a lexicographic
optimum. The wrong route uses real evidence (the quarantined lot "is physically there"; the consignment stock is
on site; the cancelled PO is still a row), produces coherent output (0 shortfall, 53 units, $767.77, a
feasible-looking plan that reconciles with last week's published readout), survives naive validation (its
arithmetic is correct and the depot totals tie), and answers the wrong question — shortfall against *nominal*
on-hand rather than against issuable stock, which flips `expedite` to `no_expedite` on the extract that matters.

It is also **the only one of the six with a passing `harbor check`** (`tb3-check-g41`, reward 1).

**Caveat to record, not a blocker:** the *observed* discriminating step was execution, not interpretation. Both
failures (`RZW9reM`, `G6PJWX4`) imposed the correct feasible set, **named min-cost max-flow, and implemented greedy
augmentation without residual arcs** — reporting 68 unmet where 46 is achievable, and $2,224.64 where the true
minimum costs $2,868.08. Both are F4 + F10. Both **identified the defect themselves** — one mid-sentence, one in a
source comment working out the counterexample — and shipped anyway; one told the principal it "ensures the minimum
achievable shortfall". Neither computed an optimality bound. Two design notes before reuse: the shortfall exceeds
40 on 3 of 4 extracts, so a partly-correct feasible set can reach `expedite` for the wrong reason; and the oracle
itself required three repairs (`g41-oracle-fix1/2/3`) after v2/v3/probe2 scored 0, so the reference must be
re-verified.

### G42 — **REJECT**

The audit's documentation-lookup charge is **correct, and the repository already concedes it in three places.**
Every construction rule sits in a table in a document the instruction names: `hours_worked_policy.md` §1
enumerates the five `hour_type` values with yes/no, §2 puts agency in, §3 fixes site attribution, §4 pre-kills the
headcount × 2,000 denominator; `recordable_case_standard.md` §1 enumerates the four classifications, §2 fixes the
grain ("**one row per injured person**"), §3 fixes occurrence-vs-entry date, §4 case site, §5 agency;
`rate_contract.md` fixes aggregation ("The company rate is **not** the average of these"). The instruction removes
the interpretive frame outright — "the answer is not a matter of opinion" — and a third file, `hse_notes.md`,
independently flags four of the five errors. Tolerances (hours to 0.01, cases exact, rate to 1e-4) admit exactly
one route, because there is no second legitimate estimator. Empirically: **3/3 at $0.05–$0.07 per trial, 68–85 s,
three identical outputs.** Its own `baseline.md` concludes: "G42 is development-only and is not part of the final
suite", and states the lesson this project should keep — "the information that distinguishes the right object from
the wrong ones has to be something the analyst must *derive*, not something the documents state."

**Keep G42 as the cleanest development evidence for DP17 and as an honest negative result. Do not promote it.**

### G44 — **REWORK**

The mechanism passes the standard on paper and the wrong route is real: the published 0.9978 and 0.9480 both use
real evidence, both use a recognisable method (precision on a labelled set), both corroborate each other, and both
answer precision in a population carrying **5.1×** the contracted fraud rate. Twelve wrong objects separate 12/12
on 4/4 extracts, ten of them flipping the decision; the PPV transport identity appears in **no** workspace
document, verified as a pre-build gate.

It nevertheless did not discriminate (0,1,1 at $0.08–$0.11), and the reason is in the workspace, not the model.
Three scaffolds hand over the derivation's structure: (1) `performance_contract.md` requires `observed_precision`
**and** `contract_precision` as separate fields, glossing the second as "precision under clause 3.2" — so the
agent is told before it starts that two distinct quantities exist; (2) the instruction pre-announces the finding —
"tell me … **why the two figures in the published certificate are not the contract figure**"; (3)
`merchant_fraud_rate` is handed over as a contract term rather than recovered. The repository's own §22.5
anticipated this: "G44 came close but **stated the target rate in the contract**."

**Rework, if chosen:** collapse the two precision fields into one `certified_precision` and make the agent justify
the population; delete the pre-announcing clause; and make the target prevalence **recoverable rather than given**
(e.g. reconstruct it from chargeback history under the same known sampling design). That converts the task from
"apply an identity to clean inputs" into "reconstruct a process the data only partially records" — the property
that actually separates Task02/G05/G10/G24. **REWORK does not authorise modification now.**

---

## 7. FAILURE-MECHANISM TAXONOMY

Mechanism-level, not story-level. Each is defined by **what the analyst must distinguish**, and — the axis this
project's evidence actually supports — **what the frame-internal check confirms** versus **what a frame-external
check requires**. A mechanism earns a slot only if its frame-internal check is an identity that cannot fail.

| # | mechanism | what must be distinguished | why both readings are initially plausible | what resolves it | the coherent-but-wrong solution | the identity that cannot fail (what naive validation misses) | correct validation | decision that changes |
|---|---|---|---|---|---|---|---|---|
| **M1** | **Availability-time provenance** | when a fact became *true* vs when it became *visible* | both clocks are real columns with documented semantics; the commit clock is the more natural join | per-source load-delay records, an incident/replay log, a sync log | reconstruct state on the commit clock, per entity rather than per example | offline metrics land near the correct value for several wrong repairs, so the metric band confirms nothing | replay the feature join against what a query at that moment would have returned | whether to promote a model / trust its scores |
| **M2** | **Identification under staggered adoption + version transport** | the counterfactual trend, and the population the decision covers | two-way FE is the house method and every wave is individually significant | the assignment rule (formats sequenced differently), a never-treated stratum, a placebo outcome, a pre-trend by conditioning set | pooled two-way FE on the installed estate, on a neighbouring outcome | SEs shrink, significance holds, the pattern reads as a learning curve | pre-trend and negative control **under each candidate conditioning set**, then transport to the planned mix | release the next capex tranche |
| **M3** | **Latent quantity under endogenous censoring** | the quantity from its observation window, when the window is produced by the quantity | "sales on days we didn't sell out are demand" is true and nearly sufficient | the stopping-time semantics, hourly exposure, a weak-censoring control arm | drop or mean-fill censored days; scale by in-stock share | `lost = expected − sold ≥ 0` holds by construction; the qualitative complaint resolves | fit on exposure with the correct error family and validate on the weak-censoring arm | category buy actions; extend the programme |
| **M4** | **Logged-policy recovery** | the action space, the true propensity, and what one decision is | a `propensity` column exists and is documented; per-response CTR is what the A/B platform reports | the serving path's ordering (log *before* the rules layer), the cache key and TTL, an eligibility flag | IPS with the logged propensity or the pre-filter pool, per serve | an on-policy comparator computed at the **same wrong grain** agrees "astonishingly closely" | compare against an on-policy anchor at the **decision** grain | which ranker to launch |
| **M5** | **Measurement-system change (errors-in-variables)** | the latent quantity from the instrument that reports it | the vendor states an offset; new-on-old regression is the obvious bridge | retained reference standards, a second un-recalibrated instrument, a gauge R&R table | apply the vendor offset, or an OLS bridge (attenuated by regression dilution) | the components sum to the observed change **by construction**, whatever the allocation | estimate the bridge with both instruments' noise, then de-noise the variance | supplier escalation; capital request |
| **M6** | **Policy feedback on the evaluation population** | model degradation from policy success | drift is real, measurable, and the vendor's proposal; PSI/KS will show it | a policy-invariant holdback, a feature-vintage replay | full drift analysis + retrain on recent data, restoring the metric | attribution components sum to `validation − monitored` and do, irrespective of attribution | evaluate **the retrained model** on the holdback | retrain / replace / change the policy |
| **M7** | **Instrument governance and principled deferral** | which contractual definition governs, and whether the evidence settles it at all | both definitions are internally consistent and each has a stakeholder | the governing instrument, its amending schedule, an independent aggregate | pick the definition whose number supports the requester; or defer where determinable | the bridge between the two definitions **closes** on the visible extract | test whether the amending schedule was executed, and reconcile against the independent aggregate | pay / refuse / defer a contractual claim |
| **M8** | **Decision-relevant vintage selection** | the informational and economic state in which an estimate must be *graded* | "score against the best estimate of physical truth and restate as data improves" is defensible practice, and is argued by a named stakeholder | the economic-consequence definition, a settlement/withdrawal history with two clocks, a signed-off close log | score against the latest restated actuals | a signed-off historical pack cell **matches at one decimal place** under the wrong vintage | reproduce the signed-off figure under the close-state lock, and treat a mismatch as a defect | retire or keep a production model |
| **M9** | **Feasible-set reconstruction and optimum** | nominal availability from issuable, movable availability; and a maximal flow from a maximum flow | every row the wrong route counts physically exists; greedy augmentation looks like the named algorithm | availability policy, quarantine/consignment status, transit times against need-by | net-requirements planning, greedy cheapest-lane fill; or a named algorithm not actually implemented | the plan is feasible and the arithmetic ties; no optimality bound is ever computed | compute a dual/LP bound, or re-solve by an independent method | expedite or not |
| **M10** | **Two-axis effect transport (selection × regime)** *(uncovered)* | an effect on a self-selected sub-population in one regime from the same effect under a universal mandate in another | fixing *either* axis is a correct diagnosis with a correct partial fix | enrolment propensities by segment, a dose-response that fades out of support, an independent physical aggregate | fix selection only, or fix regime only — each 10–12 sd wrong with a wrong decision | the corrected number is plausible and the bookkeeping is internally consistent | reconcile the transported aggregate against measured physical data at the target condition | procure capacity or defer |

**Why this taxonomy is useful beyond these tasks.** The last two columns are authoring instructions, not
descriptions. To build a task in mechanism *k* you must supply (a) an identity the natural path will satisfy, and
(b) a frame-external check the workspace makes available but does not name. If you cannot state both, the task
will measure lookup or arithmetic.

**Explicitly dropped as a mechanism:** *outcome-role assignment* (G34). It is real, but its resolution is a
one-step substitution of a named estimator, so it fails the §1 refinement. It belongs in a difficulty curve as a
cheap positive control, not in a mechanism-diverse ten.

---

## 8. COVERAGE MATRIX

Architecture figures recomputed this phase (`workspace_files` = files under `environment/workspace`; tables =
`CREATE TABLE` count in the generator).

| task | mechanism | domain | architecture | published number wrong? | decision graded | hidden extracts | object stated? |
|---|---|---|---|---|---|---|---|
| Task02 | M1 availability provenance | B2B SaaS revenue/ML | 34 files, 10 tables, multi-system, gen-1 | yes | **NO** | 3 | no |
| G05 | M2 staggered adoption + transport | grocery retail capital | 15 files, 6 tables | yes | binary | 3 | no |
| G10 | M3 endogenous censoring | convenience retail replenishment | 22 files, 11 tables | yes | 8 × three-way + prose | 3 | no |
| G24 | M4 logged-policy recovery | streaming recommendations | 19 files, 4 tables | yes | three-valued | 3 | no |
| G34 | *(dropped)* outcome roles | industrial aftermarket | 13 files, 4 tables | wrong **for the asked question** | binary | 3 | no, but one-step |
| G08 | M8 vintage selection | electricity supply/trading | 24 files, 11 tables | yes | **prose only** | yes | partly (~10 docs) |
| G41 | M9 feasible set + optimum | field-service logistics | 12 files, 9 tables | yes | binary | 4 | object yes, execution no |
| G42 | *(reject)* aggregation | industrial services HSE | 13 files, 5 tables | yes | — | yes | **yes** |
| G44 | *(rework)* prevalence transport | payments fraud | 13 files, 4 tables | yes (two figures) | binary | 4 | partly |
| P22 | M5 measurement system | discrete manufacturing | 14 files, 8 tables | yes | binary | 3 |no |
| P20 | M6 policy feedback | healthcare operations | 14 files, 9 tables | yes | four-valued | 3 | no |
| P31 | M7 governance + deferral | industrial distribution | 13 files, 6 tables | **right on 2 of 4 extracts** | 3 × three-valued | 3 | no |
| G35 | M-interference *(mechanism only)* | delivery marketplace | — | yes | binary | yes | **yes** |
| G36 | M10 two-axis transport *(mechanism only)* | energy capacity | — | yes | binary | 4 | no |

### Overconcentration, measured

| property | count among the 12 viable built tasks | verdict |
|---|---|---|
| incumbent-analysis repair | **12 / 12** | **saturated — and this is the slice's contract shape, so it is acceptable** |
| published number wrong | **11 / 12** (only P31 has a correct published number on some extracts) | **over-concentrated.** An always-disagree agent is rewarded. DP3 violation |
| threshold/gate decision | 8 / 12 | over-concentrated |
| binary decision | 6 / 12; three-or-more-valued 5; none 1 | acceptable |
| single-table / single-system | 2 / 12 (G34, G42) | fine |
| causal-identification mechanism | 3 / 12 (G05, P20 partly, G36) | thin |
| no decision graded at all | **2 / 12** (Task02, G08) | **defect against the slice** |
| `harbor check` run | 9 / 12 — **not** P22, P20, P31, G42, G44 | gap |
| object stated (fails admission test 3) | 2 / 12 among viable (G42, and G35/task03/05/06 outside) | fine after rejects |

**Domain spread is adequate** (SaaS, grocery retail ×2, streaming, industrial aftermarket, energy ×2, field-service
logistics, HSE, payments, manufacturing, healthcare, industrial distribution, delivery marketplace) and is
secondary to mechanism diversity, as instructed.

---

## 9. GAPS

**Mechanism gaps — what the strongest existing set does not cover:**

1. **Two-axis effect transport (M10).** The only mechanism where *partial correctness is punished*: a correct
   diagnosis plus a correct partial fix is still 10–12 sd wrong with a wrong decision. Nothing in the shipped
   five has this property. The G36 artifact is dead; the mechanism is the single highest-value build.
2. **Interference / general equilibrium.** A partial-equilibrium contrast measured inside a mixed experiment is
   not the policy contrast. G35 has world-class supporting research (`wrong_methods.md`,
   `coherent_wrong_gate.md`, attractor CW1 = "a real causal effect at the wrong saturation" that flips the
   decision) and **all of it was neutralised by its own output contract**.
3. **A required falsification artifact.** No task grades a diagnostic — a pre-trend table, a negative control, a
   back-test — alongside the estimate. Given that exactly one falsification-class check appeared in 45 trials and
   that 8 of 9 prospective trials ran powerless checks, this is the most informative single addition available,
   and it directly instruments the §1 finding.
4. **Unit-of-inference / clustering.** Observations nested in clusters with treatment assigned at cluster level;
   re-fitting with the cluster as a random effect triples the SE and the effect vanishes. Designed as P23
   (score 55), displaced from the prospective six **for diversity, not quality**.
5. **Selective labels + performativity, stacked.** Designed as P13 (score 56, joint highest). Nothing in the
   built set stacks two selection mechanisms.
6. **Non-linear economic object.** Money that is not linear in quantity, so a correct quantity still gives the
   wrong amount. Task06 has it and is out on leakage grounds.
7. **Reporting vintage vs restatement-to-truth.** task04's attractor reproduces six published board quarters to
   4 dp. Real, and currently riding on one README sentence about a different artifact.

**Structural gaps, independent of mechanism:**

8. **Only one task has a correct published number on any extract.** Fix by requiring every new task to have at
   least one extract where the incumbent is right.
9. **Two tasks grade no decision** (Task02, G08).
10. **Five viable tasks have never had a `harbor check`.**
11. **One shipped task's verifier is not hermetic** (G10, network pip at grade time).
12. **No multi-incident shared world.** Every task is a standalone world; the phase-2 architecture designed for
    reuse and it was never exercised.

---

## 10. THREE FINAL-10 PLANS

No plan predicts whether any model will pass any task.

### PLAN A — strongest scientific benchmark (ignore convenience)

| # | slot | task | mechanism | domain | why included | Gemini exposure | research contribution |
|---|---|---|---|---|---|---|---|
| A1 | logged-policy recovery | **G24** existing | M4 | streaming | strongest single task; failures byte-identical to pre-registered mutations | 0/3 | proves decision-only grading is worthless here |
| A2 | endogenous censoring | **G10** existing + 2 fixes | M3 | convenience retail | only per-row latent posterior; only endogenous observation window | 0/3 | hardest object in the suite |
| A3 | availability provenance | **Task02** existing + **graded decision** | M1 | B2B SaaS | unique mechanism; currently missing the slice's back half | 0/3 | per-example × cutoff state reconstruction |
| A4 | staggered adoption + transport | **G05** existing | M2 | grocery capital | identification + transport to an untreated population | 0/3 | the conditioning-set failure |
| A5 | vintage selection | **G08** existing + wording fix + **graded decision** | M8 | electricity trading | the only unshipped task whose rival is argued by a named stakeholder and matches a signed-off figure | 1/3 | grading-state selection |
| A6 | feasible set + optimum | **G41** existing | M9 | field-service logistics | the only demonstrated second difficulty axis; passing `harbor check` | 1/3 | recognition ≠ execution |
| A7 | measurement system | **P22** unchanged, disclosed | M5 | manufacturing | elementary method, hard identification — separates the hypothesis from knowledge gaps | 0/3 frozen | the `"tooling": 0.0` case |
| A8 | policy feedback | **P20** unchanged, disclosed | M6 | healthcare ops | naive action is the wrong action | 0/3 frozen | opposite correct action to A3 |
| A9 | two-axis transport | **NEW-1** | M10 | energy or healthcare capacity | the only mechanism that punishes partial correctness | **none** | the strongest uncovered mechanism |
| A10 | governance + deferral **with a required falsification artifact** | **NEW-2** | M7 + gap 3 | industrial distribution or commercial analytics | makes abstention scoreable *and* grades a diagnostic; replaces P31, which has a verified F8 | **none** | closes DP3 and DP6 together |

Drops: G34 (redundant with A4, near-lookup), G42 (reject), G44 (rework, lower value), P31 (verified
contract/truth contradiction), task01/03/04/05/06, G35/G36 artifacts.
**New builds: 2. Existing modified: 3 (Task02, G10, G08). Never-exposed tasks: 2.**

### PLAN B — strongest benchmark requiring minimum new implementation

| # | task | mechanism | status | required work |
|---|---|---|---|---|
| B1 | G24 | M4 | shipped | none |
| B2 | G10 | M3 | shipped | harden `test.sh`; widen or document the NB-only acceptance set |
| B3 | G05 | M2 | shipped | record the 98.3 % pre-registration miss in the release notes |
| B4 | Task02 | M1 | shipped | none (accepts "no decision graded") |
| B5 | G34 | *(outcome roles)* | shipped | none (accepts near-lookup and the mid-build tolerance loosening) |
| B6 | G08 | M8 | development | one-sentence spec fix + re-baseline |
| B7 | G41 | M9 | development | re-verify the oracle |
| B8 | P22 | M5 | frozen | disclose; re-audit the 1.02× margin |
| B9 | P20 | M6 | frozen | disclose; re-audit `feature_feed_defect` |
| B10 | P31 | M7 | frozen | **disclose the verified F8, or fix and break the freeze** |

**New builds: 0. Existing modified: 2–4. Never-exposed tasks: 0.**
Cost: one re-baseline of G08 (3 trials) plus `harbor check` on the five that lack it.
What it sacrifices: every gap in §9 stays open; the published-number bias stays at 9/10; two tasks still grade no
decision; G34's redundancy and G05's overlap remain; **and the entire suite's difficulty is already known**, so the
benchmark reports no unbiased number at all.

### PLAN C — cleanest research design

Optimised for interpretable mechanism coverage and minimal selection / post-hoc contamination. The principle: a
difficulty estimate is only unbiased on tasks selected **before** their results were seen.

| # | task | mechanism | exposure | role |
|---|---|---|---|---|
| C1 | **G24** existing | M4 | 0/3 known | declared anchor — reported separately, never pooled |
| C2 | **G10** existing + fixes | M3 | 0/3 known | declared anchor |
| C3 | **G05** existing | M2 | 0/3 known | declared anchor |
| C4 | **NEW** P13 selective labels + performativity | stacked selection | none | unbiased |
| C5 | **NEW** P27 roster optimal and illegal | wrong feasible set + stochastic feasibility | none | unbiased |
| C6 | **NEW** P02 elasticity from chosen price changes | policy-induced variation | none | unbiased |
| C7 | **NEW** P23 alloy trial unit of inference | clustering / error structure | none | unbiased |
| C8 | **NEW** two-axis transport (G36 mechanism) | M10 | none | unbiased |
| C9 | **NEW** interference with CW1 live (G35 mechanism, contract stripped) | general equilibrium | none | unbiased |
| C10 | **NEW** non-identifiability verdict + required falsification artifact (P32) | deferral + gap 3 | none | unbiased |

**New builds: 7. Existing modified: 1. Never-exposed tasks: 7.**
All seven new slots already have design specifications, multiple-valid-method audits, ambiguity audits and
diversity checks written in `research/phase2/HANDOFF_2026-09-23.md` §16–§28, with scorecard totals 53–56.
It is the only plan that yields a defensible unbiased pass@3, and it costs the most.

---

## 11. RECOMMENDED PLAN

**Recommendation: PLAN A.** Not Plan B, which is the cheapest, and not Plan C, which is the most rigorous.

**Why not Plan B.** It preserves every defect this audit found. It ships a suite in which nine of ten tasks have a
wrong published number (so scepticism is rewarded — DP3), two tasks grade no decision, one pair is redundant
(G05/G34), one task's difficulty the project itself rates "LOW", and one task carries a **verified
contract/truth contradiction that has already caused a real trial to fail on a field where it obeyed the
contract**. Most importantly: every task in Plan B has been run against the target model, so the benchmark cannot
report a single number that is not contaminated by selection. Plan B is a repackaging, not a benchmark.

**Why not Plan C.** It is the right design and I cannot defend the schedule. Seven new tasks at the demonstrated
authoring cost (≈1,000–3,500 Python lines each, plus a pre-build gate suite that has rejected designs *after*
implementation — G36 v1.1 was abandoned on a counterexample search) is not a validated three-month plan, and the
project's own history is that **the marginal new task got easier, not harder**: of the three built after the five,
two are reading tasks by the audit's own test. Committing to seven new mechanisms at once repeats that mistake at
scale.

**Why Plan A.** It is the composition that fixes the defects rather than disclosing them, at two new builds:

1. It **drops the one redundant pair member** (G34) and replaces it with a mechanism nothing covers (M10), so
   mechanism count rises from 8 distinct to 10 distinct across 10 slots.
2. It **repairs the two slice violations** — Task02 and G08 gain graded decisions — so all ten tasks instantiate
   the full capability (reconstruct → identify → execute → decide) rather than eight of ten.
3. It **replaces P31 rather than shipping its defect**, while keeping the mechanism P31 uniquely contributes
   (deferral) and adding the most informative missing feature (a graded falsification artifact) to the same task.
4. It keeps the **published-number bias** fixable: NEW-2 is specified with a correct incumbent on at least one
   extract, taking the suite from 9/10-wrong to 8/10-wrong. That is an improvement, not a solution, and §14 says
   so.
5. It produces **two never-exposed tasks**, which is the minimum that allows an honest sentence of the form "on
   the two tasks whose results were not known when the suite was chosen, pass@3 was X". Plan B allows no such
   sentence.
6. Every existing slot it keeps has Oracle 1 / Nop 0, a mutation suite at 100 % as expected, and a frozen
   checksum that **recomputes correctly today**.

**What Plan A concedes, explicitly.** Eight of ten tasks have known Gemini results, so the headline suite pass@3
remains biased low and must be reported alongside the two-task unbiased figure. G05's 98.3 % pre-registration miss
and G10's narrow acceptance family stay in the suite with disclosure. P22 and P20 ship with the two newly found
near-threshold defects re-audited but their freeze intact — and if the re-audit finds either defect
decision-relevant, that slot must convert to a rebuild, which is a Plan-A-to-Plan-C drift ChatGPT should price now
rather than later.

---

## 12. NEW TASK DESIGNS

Two new tasks under Plan A. Both are designs only. **Nothing here authorises a build.**

### NEW-1 — Two-axis effect transport (selection × regime)

| # | field | specification |
|---|---|---|
| 1 | **working title** | `n1-tariff-capacity-transport` (mechanism M10; rebuilt from G36's mechanism, **new generator**) |
| 2 | **professional setting** | A distribution utility with 565k residential customers and a firm capacity ceiling; a mandatory time-of-use tariff is the mitigation for a forecast-warmer season. A **voluntary, opt-in** pilot with a randomised control measured the tariff's peak response. |
| 3 | **decision-maker** | Network planning, to the capacity committee |
| 4 | **consequential decision** | `procure` vs `defer` nine months of capacity lead time, against a ceiling derived from capacity economics (never from margin-maximisation — the G36 lesson) |
| 5 | **data / artifacts** | interval meter data by segment; enrolment records with segment propensities; the pilot's randomised arms; weather (CDD) history and the season forecast; an **independent physical aggregate** (SCADA feeder peaks) as a second derivation; the capacity memo; the tariff design note; the incumbent forecast pipeline |
| 6 | **incumbent analysis** | Applies the pilot's measured fractional response to the whole estate at the pilot season's weather |
| 7 | **correct object** | Expected mean peak-window kW per residential customer for the forecast season with the **whole estate** on the tariff — requiring the response to be re-weighted from the self-selected enrolled population to the estate **by load**, and re-evaluated at the forecast season's condition where the dose-response fades non-linearly |
| 8 | **competing interpretation** | Two, each a correct diagnosis with a correct partial fix: **(W8)** fix the opt-in selection bias and stop; **(W9)** fix the heat-damping of the response and stop |
| 9 | **why genuinely reasonable** | Each is written by an analyst who has correctly identified a real problem and corrected it. Neither is a strawman. In G36's measured panel each was still 10–12 sd wrong with a wrong procurement call. |
| 10 | **discriminating evidence** | segment enrolment propensities spanning ~0.03–0.22 against segment base loads spanning ~1.0–3.3 kW (so load-weighted ≠ household-weighted); the CDD-dependent fade visible within the pilot; **SCADA measured peak** for last season, which the naive model under-predicts with the error growing in adoption |
| 11 | **correct route** | Estimate segment-level dose-response on the randomised arms; re-weight to estate **load** shares; evaluate at the forecast condition; reconcile the aggregate against SCADA; propagate uncertainty to the ceiling comparison |
| 12 | **coherent-but-wrong route** | Selection-only or regime-only correction, or applying an **unweighted mean of segment responses** to a correctly computed estate load |
| 13 | **naive checks it survives** | the corrected figure is plausible; bookkeeping is internally consistent; `L1 = L0(1 − R)` composes arithmetically; the pilot's own randomised contrast is correctly estimated |
| 14 | **decisive validation** | reconcile the transported estate aggregate against SCADA at the **target** condition, and check that the response used composes with the graded headline (`L1 = L0(1 − R_load)` holds exactly only under load weighting) |
| 15 | **deliverable** | repaired pipeline + readout: segment responses, estate response at target condition, estate peak kW, the SCADA reconciliation, and `procurement_decision` |
| 16 | **grading** | deterministic against generator truth; graded quantities are latent generator values, not reference-implementation outputs; tolerances = max(floor, 1.5 × worst error of ≥2 legitimate estimator families over ≥20 calibration worlds), frozen before exposure |
| 17 | **accepted methods** | segment-level regression + load reweighting; a hierarchical model with segment random effects; a direct estimator on the randomised arms with post-stratification. All three must agree within tolerance on every extract or the task is not gradable (the G10 lesson) |
| 18 | **ambiguity risks** | which population "estate-wide" means; whether the evaluation point is the mean condition or the season distribution. **Both must be pinned in the contract in business language** — this is exactly where G36 failed (`R_load` vs `R_household`, and `R_season` as a legitimate alternative that failed the mechanical multiplier) |
| 19 | **leakage risks** | the tariff design note must not state the transport formula; enrolment propensities must not be handed over as a ready weighting vector; the scaffold must **not pre-solve the estate weighting** (G36's recorded defect) |
| 20 | **verifier-gaming risks** | hard-coding the visible answer; constant decisions (the ceiling must split decisions across extracts); satisfying the sum identity without correct attribution |
| 21 | **mutations needed** | selection-only; regime-only; unweighted segment mean applied to correct estate load (**the G36 CE06 counterexample — this one must fail**); vendor-stated response; constant absolute kW transported out of support; always-procure; always-defer; hard-coded visible |
| 22 | **reject before exposure if** | the identifiability window `max(valid err) < tol < min(wrong err)` cannot reach ratio ≥ 3 — **this is the gate G36 v1.1 failed** (worst legitimate 0.92 SE_REF vs wrong 0.99 SE_REF, a degenerate window), and it is why the artifact was abandoned rather than patched |

### NEW-2 — Non-identifiability verdict with a required falsification artifact

| # | field | specification |
|---|---|---|
| 1 | **working title** | `n2-campaign-identifiability` (mechanism M7 + gap 3; based on phase-2 candidate **P32**, scorecard 55) |
| 2 | **professional setting** | A national brand campaign ran everywhere, at the same time, with no holdout. The analytics team has already produced a pre/post lift of +6.4 %. |
| 3 | **decision-maker** | CMO and finance, to the board |
| 4 | **consequential decision** | a renewal decision on a large media budget **and** a precedent for how the company measures brand media. Decision space is three-valued: `renew`, `do_not_renew`, `not_identifiable_commission_design` |
| 5 | **data / artifacts** | national sales; regional media weight variation; competitor spend, price, weather; the incumbent causal-impact analysis; the measurement policy stating the evidential standard the decision requires; a prior campaign that *did* have a holdout |
| 6 | **incumbent analysis** | a Bayesian structural time-series (CausalImpact-style) on national sales with controls, reporting ≈+5 % with a credible interval and good posterior predictive checks |
| 7 | **correct object** | either (a) an identified estimate from regional weight variation **with its assumptions tested**, or (b) a declared non-identifiability with a bound **and** a concrete experimental design (holdout geography, power, duration, cost) — and in both cases an explicit statement of what the +6.4 % actually measures |
| 8 | **competing interpretation** | the BSTS counterfactual is a valid identified estimate |
| 9 | **why genuinely reasonable** | it is the standard method, it is well-fitted, its posterior predictive checks pass, and it is what the team has already produced |
| 10 | **discriminating evidence** | a **placebo in time** — fit the same model to a pre-campaign window and it "detects" an effect of similar magnitude; and the regional weight-variation estimate, whose pre-trend test fails in two regions |
| 11 | **correct route** | run the placebo-in-time; run the regional estimator and test its pre-trends; conclude identified-or-not against the stated evidential standard; if not identified, produce the design |
| 12 | **coherent-but-wrong route** | report the BSTS estimate with its interval; or defer on an extract where identification **is** available |
| 13 | **naive checks it survives** | posterior predictive checks, control-series fit, interval coverage on held-out pre-period — all pass inside the wrong frame |
| 14 | **decisive validation** | the placebo-in-time. It is the frame-external check, it is cheap, and it is not named anywhere in the workspace |
| 15 | **deliverable** | readout with the identification verdict, the bound or estimate, **a graded falsification artifact** (the placebo table: window, estimate, interval per placebo fit), and the decision |
| 16 | **grading** | deterministic. The placebo table is graded as data — window boundaries and estimates within tolerance — not judged as prose. Verdict and decision graded exactly |
| 17 | **accepted methods** | BSTS or synthetic control for the placebo; regional weight variation via panel FE or IV; a Manski-style bound. Any route reaching the correct verdict and decision passes |
| 18 | **ambiguity risks** | **highest of the two designs.** The evidential standard must be stated in the measurement policy in business language, or "is it identified?" is unanswerable. Two independent readers must derive the same standard from the documents before freeze |
| 19 | **leakage risks** | no document may name the placebo-in-time or state that the BSTS is invalid; the prior campaign's holdout must be present as evidence, not as an instruction |
| 20 | **verifier-gaming risks** | **always-defer is the primary exploit.** Mitigation is structural: **≥1 extract must be genuinely identified**, where deferral scores 0, and the incumbent's number must be **correct** on ≥1 extract (which also repairs the suite's DP3 bias). Hedging must score zero (DP22) |
| 21 | **mutations needed** | always-defer; always-renew; BSTS reported as identified; placebo run on the wrong window; regional estimate without the pre-trend test; correct verdict with a fabricated placebo table; hedged verdict listing multiple answers |
| 22 | **reject before exposure if** | the placebo's "detected effect" is not separated from the true effect by ≫ tolerance on every extract; or two independent readers derive different evidential standards from the documents; or `always_defer` cannot be made to fail |

---

## 13. PRE-EXPOSURE ADMISSION GATE

Every gate is model-free and must pass **before any target model sees the task**. Gates 1–17 are required; a single
failure blocks admission. Gates marked ⚠ were added because of a specific documented failure in this project.

**Scientific admission**
1. The professional scenario is credible and traceable to a documented real failure structure (DP12).
2. The decision is **explicit, graded, and consequential**, with a stated rule and threshold. ⚠ *Task02 and G08
   grade no decision.*
3. **≥2 initially defensible interpretations**, at least one of which yields a coherent result passing the
   organisation's normal checks.
4. ⚠ **The object is underdetermined by the workspace documents** — derivable only from how the data came to
   exist, or from an optimisation no document solves. *This is the test G42, task03, task05, task06 and G35 fail.*
5. ⚠ **The derivation is not a one-step recall of a named estimator.** *Added because of G34: derived, yet solved
   2/3 in 18–20 steps, twice without querying the warehouse.*
6. ⚠ **The assumed-quantity test.** At least one decision-relevant quantity is one the natural path *assumes*
   rather than estimates, and the obvious internal check on that path is an **identity that holds regardless**.
   Both must be written down before build. *This is the §1 finding made operational.*
7. **≥2 discriminating routes exist in the workspace, neither named**, each with its predicted outcome under each
   interpretation written down before build (DP20).
8. The decision margin is narrow enough that a wrong interpretation changes the decision on ≥half the extracts
   (DP18).
9. ⚠ **≥1 extract on which the incumbent's published number is correct**, so an always-disagree strategy fails
   (DP3). *Currently satisfied only by P31.*

**Gradability**
10. **Oracle = 1, Nop = 0**, on the frozen content, re-verified from a clean checkout.
11. **Deterministic verifier**; graded facts are generator truth, not a reference implementation's output (DP1).
12. ⚠ **Independently-derived truth (IGQA):** ≥2 estimator families with **no shared helper**. *Added because
    G36's oracle, wrong-method families and verifier shared one helper, so the independence gate could not catch
    the defect.*
13. ⚠ **Measured identifiability window**: `max(valid err) < tol < min(wrong err)` with ratio **≥ 3**, measured
    over ≥20 calibration worlds and validated on ≥20 fresh worlds, **before freeze**. *G36 v1.1 died here
    (0.92 vs 0.99 SE_REF). G34's narrowest margin is 1.94 τ and its multiplier was loosened mid-build.*
14. ⚠ **Accepted-method breadth**: ≥2 legitimate methods reach the graded quantities within tolerance, and if two
    defensible methods disagree materially the task is **not gradable** (DP19). *Added because G10's accepted
    family is Gamma-Poisson only.* Record each accepted route's worst margin honestly — ⚠ *P22's recorded 1.5–2×
    is 1.02× on one route by recomputation.*
15. ⚠ **Contract–truth consistency audit**: every propagation rule the agent-visible contract states must hold in
    `truth()` on **every** extract. *Added because of G36 (household- vs load-weighted) and the P31 hidden_c
    contradiction verified in §5, which made a compliant trial fail.*
16. **Fixture coverage**: every wrong method is rejected on ≥2 extracts; no single-fixture dependence. ⚠ *Task02's
    two overfit repairs are caught by `hidden_c` alone.*
17. **Decision arity**: decisions split across extracts so no constant answer passes; `always_X` mutations for
    every value of the decision.

**Integrity**
18. **Mutation/adversarial suite** at 100 % as expected, including a behaviour-preserving mutant that must score
    1. ⚠ Mutants must be **hash-checked against the oracle and each other** — *G34 had a mutant byte-identical to
    the oracle reporting a false pass, and a duplicate.*
19. **No answer leakage**: no document states the estimator, population rule, conditioning set, hidden regime or
    truth. ⚠ **No correct helper may remain in the faulty code, and no worked example of the target output may
    exist in the workspace** — *task06 failed both.*
20. **No verifier leakage**: `/tests` unreadable by the pipeline user with refuse-to-grade; ⚠ **hermetic verifier
    install from hash-pinned wheels with `--no-index --require-hashes`** — *G10 installs from the public network
    at grade time.*
21. **Hedging must score zero** (DP22): a mutation submitting the correct answer alongside distractors scores 0.
22. ⚠ **Instruction–reference consistency**: every sentence added to the instruction must be satisfied by the
    graded reference. *Added because Task02-EI's added paragraph is contradicted by `tests/reference.py`, which
    never selects `synced_at` for `support_tickets`.*
23. **`harbor check`** run and recorded, with criterion-level results disclosed, not just the binary reward. ⚠
    *Five viable tasks have never had one.*
24. **Two-reader specification test**: two independent readers derive the same estimand from the documents alone
    (DP21, Terminal-Bench's two-verifier test). Overspecification is audited as a defect too.
25. **Mechanism coverage**: the task adds a mechanism from §7 that no admitted task occupies.
26. ⚠ **Published-artifact reproducibility**: any number quoted in the instruction or a workspace report must be
    reproducible from the extract within the tolerance on that quantity. *P22's published 92.8 % / 7.23 % are not.*
27. **Freeze**: manifest hash recorded, pre-registered analysis plan committed, no post-exposure change to task,
    tolerance, extract or plan.

---

## 14. RESEARCH CLAIM BOUNDARIES

### A. What the existing evidence already establishes
1. `gemini-3-flash-preview` solves 1 of 5 shipped tasks at pass@3 (2 of 15 trials) on frozen tasks with Oracle 1 /
   Nop 0 / check 1 each, and 0 of 3 prospective tasks (0 of 9 trials).
2. All 13 failed shipped-suite trials are model-side, reproducible from the agents' own submitted code, with zero
   environment friction.
3. Recognition of the problem class is not the bottleneck: in every failed trial the agent identified the broad
   class; prospectively `evidence_reconstruction` and `scientific_object` each passed 8/9 while
   `quantitative_results` passed 2/9.
4. **Route-taking is not the bottleneck either.** 8 of 9 prospective trials obtained discriminating evidence
   against a serious rival; P1 was disconfirmed.
5. **Revision is not the bottleneck.** 8 of 8 applicable trials revised after a contradiction; P6 was
   disconfirmed.
6. Coherence checks computed inside a wrong frame reliably confirm it — 8 of 9 prospective trials, ≥5 discovery
   trials, and in every case the check passed while the analysis was wrong.
7. A decision-only grader would materially overstate performance: 6 of 13 discovery failures reached the correct
   decision with wrong quantities; on G24 3/3 trials and 12/12 extract-level decisions.
8. Difficulty tracks whether the object is stated or must be derived (15/15 tasks, one exception), and the
   exception is the cheapest task in the pool.

### B. What a 10-task benchmark could descriptively measure
1. Per-task and suite pass@1 / pass@3 / pass^3 for any model, on frozen tasks with criterion-level breakdown.
2. **Criterion-level profiles**: where in the chain (reconstruct → identify → execute → decide) each model fails.
   This is the instrument the shipped five lack and the prospective three added.
3. The **decision/science dissociation rate**: how often a model reaches the right decision on wrong quantities.
4. **Mechanism-level coverage**: which of the ten mechanisms a model handles, which it does not.
5. The **assumed-quantity failure rate**: how often the quantity that fails is one the model assumed rather than
   estimated — directly measurable from criterion-level results plus the pre-registered commitment list.
6. Cost per resolved task and the difficulty curve.

### C. What would require a new pre-registered experiment
1. Any causal claim about *why* models commit early — e.g. that a required falsification artifact changes the
   commitment. That needs the NEW-2 arm plus a paired condition without it.
2. Any claim that the pattern holds across model families. **One family has been run.** Rival A7 is undiscriminated.
3. Any claim that supplying the discriminating route does not help — the Task02-EI ablation designed to test the
   adjacent question is confounded by its own F8 and has been withdrawn.
4. Any claim about horizon length. Nothing measures it; failures occur early and trials used 4–14 minutes of a
   90-minute budget.
5. Any unbiased suite difficulty estimate. Requires tasks whose results were unknown at selection time.

### D. What must never be inferred from pass rates alone
1. That a low pass rate means the tasks are good. G36 was 0/3 **as graded** and 2/3 under a correct estimand.
2. That a high pass rate means the tasks are easy for the right reason. G34 passed 2/3 twice without querying the
   warehouse; G42 passed 3/3 by reading two tables.
3. That failures are genuine difficulty. Three F8s are on record (G36, Task02-EI, and now P31 hidden_c).
4. Anything causal from 15 tasks and one model, or that 20 % pass@3 transfers to another model or harness.
5. That these tasks represent professional multi-hour work — the 90–300 minute estimates are **author judgements
   with no human trials**.

### E. The proposed benchmark-level formulation

The brief's formulation:
> "Can an AI agent recover the decision-relevant scientific object from messy production evidence, correctly
> identify and execute the analysis that answers it, and make a defensible professional decision when a plausible
> but wrong analysis is available?"

**It is defensible but it is now slightly behind the evidence**, because it implies the failure is in recovery and
identification — and prospectively, recovery (8/9), identification-route-taking (8/9) and revision (8/8) all
happened. The refinement the evidence supports:

> **When a plausible wrong analysis is available and an agent's own checks are computed inside it, can the agent
> recover the decision-relevant scientific object, validate the quantities it *assumed* rather than only those it
> computed, and reach a professional decision that is right for the right reason?**

This keeps everything the original says, adds the one thing the prospective experiment actually found, and states
a property that is measurable from criterion-level grading plus a pre-registered commitment list. It also makes
the benchmark's own null result reportable: if models validate assumed quantities as readily as computed ones, the
design's premise is wrong and we say so.

---

## 15. IMPLEMENTATION ORDER

Under Plan A. No step begins before the previous step's gate passes.

| step | work | gate to pass | model spend |
|---|---|---|---|
| 0 | **Re-audit the three defects in §5** by recomputation, and decide P31's disposition | contract–truth consistency (gate 15) on P22/P20/P31 | **zero** |
| 1 | **Add a graded decision to Task02** and to **G08**; fix G08's partial-class spec wording | gates 2, 15, 22, 24 | zero |
| 2 | **Harden G10's verifier** (`--no-index --require-hashes`, `-S`, `--noconftest`); document or widen its accepted family | gates 14, 20 | zero |
| 3 | **Re-verify G41's oracle** (it needed three repairs) and re-run its mutation suite | gates 10, 18 | zero |
| 4 | **`harbor check`** on P22, P20, G41 re-check, and the two modified tasks | gate 23 | **paid evaluator** |
| 5 | **Re-baseline Task02, G08** (agent-visible changes invalidate prior baselines) | 3 valid trials each on one digest | **paid target model** |
| 6 | **NEW-1 design gate**: identifiability window ratio ≥ 3, IGQA with 2 independent families, CE-search incl. the G36 CE06 counterexample | gates 12, 13, 14, 21 — **build only if it passes** | zero |
| 7 | **Build NEW-1**, freeze, Oracle/Nop/mutations/harbor check | gates 1–27 | check only |
| 8 | **NEW-2 design gate**: two-reader evidential-standard test, placebo separation, `always_defer` fails | gates 3, 18, 20, 24 — **build only if it passes** | zero |
| 9 | **Build NEW-2**, freeze, full gate | gates 1–27 | check only |
| 10 | **Freeze the suite**, commit a pre-registered analysis plan naming the two never-exposed tasks as the unbiased subset | plan hashed before any exposure | zero |
| 11 | **Exposure** — see §16 | — | paid |

**Steps 0–3 and 6 and 8 cost no model spend at all.** Two of the three biggest risks (NEW-1's identifiability
window, NEW-2's ambiguity) are resolved before a line of task code is written.

---

## 16. TARGET-MODEL EXPOSURE PLAN

**Do not run any of this now.** Counts only.

| arm | trials | rationale |
|---|---|---|
| Re-baseline of modified existing tasks (Task02, G08) | 2 × 3 = **6** | agent-visible changes invalidate the prior baselines |
| NEW-1 baseline | **3** | matches the prospective protocol: 3 valid trials, sequential, one job each, one digest |
| NEW-2 baseline | **3** | same |
| Unchanged existing tasks (G24, G10, G05, G41, P22, P20) | **0** | their baselines stand on unchanged digests |
| **minimum total** | **12 new valid trials** | |
| Optional: reliability arm, pass^3 on the two new tasks | +2 × 2 = **4** | only if a reliability claim is wanted |
| Optional: second model family — **the single highest-value addition** | 10 × 3 = **30** | rival A7 (single-model artefact) is currently **undiscriminated**; one family is the largest limitation in the whole project |

**Protocol, inherited unchanged from `research/phase3/analysis_plan.md`:** exactly 3 valid trials per task,
sequential, one trial per job, all on one frozen digest; validity adjudicated from job artefacts **before** any
reasoning is read; invalid trials preserved and reported, never silently retried; at most one replacement per task
without a written reason; a pre-registered plan hashed and committed before the first call; a spend stop threshold.

---

## 17. COST ESTIMATE

All figures are **measured from this repository** (`jobs/*/result.json` → `stats.cost_usd`). No API price list is
used or assumed.

**Measured target-model cost per valid trial**

| task | measured | per trial |
|---|---|---|
| Task02 | $0.7022 / 3 trials | **$0.234** |
| G05 | $0.6009 / 4 trials | **$0.150** |
| G10 | $0.5843 / 3 | **$0.195** |
| G24 | $0.5136 / 3 | **$0.171** |
| G34 | $0.1244 / 3 | **$0.041** |
| G08 | $0.9583 / 3 | **$0.319** |
| G41 | $0.3553 / 3 | **$0.118** |
| P22 / P20 / P31 | $1.4667 / 9 | **$0.163** mean ($0.0068–$0.2725) |
| **overall** | ~$9.88 over ~64 trials | **≈ $0.155 / trial** |

**Measured `harbor check` cost (Claude evaluator, not the target model):** $0.3226 (G10), $0.5243 (G05), $0.5948
(G24), $1.05 (G41 TB3). Total recorded across all checks: **$14.4273** (`report/data/results.json`).

**Plan A exposure estimate**

| item | quantity | unit (measured) | estimate |
|---|---|---|---|
| minimum new valid trials | 12 | $0.155 | **≈ $1.90** |
| allowance for invalid trials and replacements (pilot rate was 0/9 invalid prospectively, but 9 invalid attempts occurred on task01/G08 earlier) | +50 % | — | **≈ $2.85** |
| `harbor check` on 5 tasks (2 modified, 2 new, 1 re-check) | 5 | $0.32–$1.05, mean ≈ $0.60 | **≈ $3.00** |
| **Plan A, minimum viable** | | | **≈ $6** |
| optional reliability arm (4 trials) | 4 | $0.155 | +$0.62 |
| optional second model family (30 trials) | 30 | $0.155 (unknown for another family — **flagged**) | +≈$5, **highly uncertain** |
| **Plan A with a second family** | | | **≈ $11** |

For comparison: **Plan B** ≈ 3 re-baseline trials + 5 checks ≈ **$3.50**. **Plan C** ≈ 21 new-task trials + 8
checks ≈ **$8**, but with 7 builds of engineering rather than 2.

**The dominant cost is not model spend.** Measured engineering cost is **≈1,000–3,500 Python lines per task**
(generator + verifier + solution + incumbent), falling ~2.5× as the harness matured. Two new tasks at the mature
rate is the real budget item, and the pre-build gates in §13 exist because that cost is sunk if a gate fails after
implementation — which has happened (G36 v1.1, abandoned on a counterexample search).

---

## 18. STOP RULES

Abandon a new task rather than force it into the benchmark when any of these fires. Each is traceable to a
specific event in this project.

1. **The identifiability window cannot reach ratio ≥ 3** after two calibration attempts. *G36 v1.1: worst
   legitimate 0.92 SE_REF against wrong 0.99 SE_REF. Widening the tolerance admits the wrong method; narrowing it
   fails the oracle. Stop.*
2. **A counterexample search finds a scientifically wrong route that passes.** *G36 CE06 passed at ≤ 0.29× of
   forecast tolerance on every extract with a wrong aggregation, and no response check could have caught it.
   The project's own conclusion: "a genuine second transport belongs in a new task designed from scratch."*
3. **Two defensible methods disagree materially and the disagreement cannot be made the graded object.** *DP19,
   the G10 mixing-family lesson.*
4. **The correct object turns out to be stated, and removing the statement breaks a `harbor check` criterion.**
   *task03's leak was installed deliberately to satisfy `behavior_in_task_description`. If the rubric and the
   science conflict, the task is the wrong vehicle — do not sacrifice the science.*
5. **The two-reader test yields different estimands** twice, after one clarification pass. *Terminal-Bench left
   28 of 89 tasks defective after ~3 reviewer-hours each; more reviewing is not the fix.*
6. **The natural wrong route is only plausible to a non-reader.** *G42: twelve wrong answers separate cleanly and
   none is plausible after ten minutes of reading. Separation without underdetermination is not a task.*
7. **The difficulty turns out to be one textbook substitution.** *G34: solved 2/3 in 18–20 steps, twice without
   querying the warehouse. Reclassify as a positive control; do not count it as a hard task.*
8. **The contract and the truth cannot be made consistent on every extract** without weakening the decision. *G36
   D4; P31 hidden_c.*
9. **`always_defer`, `always_agree` or `always_disagree` cannot be made to fail.** Abstention is unscoreable
   without this.
10. **A required agent-visible fix invalidates the baseline and the schedule cannot absorb a re-baseline.** Ship
    the task in a later wave rather than ship it undisclosed.
11. **Authoring exceeds ~1.5× the mature per-task cost** with gates still open. The project's own history is that
    the marginal task got easier; a task that is getting *more* expensive without getting harder is a sunk-cost
    trap.

---

## 19. NEXT ACTION FOR CHATGPT

**One decision is blocking, and it has two parts.**

### Decision 1 — Which composition: A, B or C?

I recommend **A** (§11): 10 slots, 8 existing, 2 new builds, 3 existing tasks modified, drops G34 and P31, adds
mechanisms M10 and a graded falsification artifact. Plan B is cheaper and preserves every defect in §5 and §9.
Plan C is cleaner and needs 7 new builds I cannot schedule honestly.

### Decision 2 — P31's disposition. This cannot be deferred.

The verified contract/truth contradiction (§5, DEFECT 1) makes all three options costly, and only you can choose:

| option | consequence |
|---|---|
| **(a) Exclude P31, build NEW-2 instead** *(Plan A as written)* | keeps the freeze intact and the prospective experiment fully interpretable; costs one new build; loses the only existing task with a correct published number |
| **(b) Include P31 unchanged, disclose the defect** | zero cost; ships a known contract/truth contradiction that has already made a compliant trial fail; a reviewer who finds it will question every other verifier |
| **(c) Fix P31's contract sentence or `truth()`** | cheapest repair (one sentence); **breaks the phase-3 freeze**, requires a new manifest and tag, and the 9-trial prospective result can no longer be described as being on the frozen artifacts |

I have not chosen. My own reading is that (c) is the most tempting and the most damaging, because the prospective
experiment's entire value is that its artifacts were frozen before exposure.

### Two things to confirm alongside those

3. **Should the suite report two pass@3 figures** — one over never-exposed tasks and one over the whole suite? I
   recommend yes; under Plan A the unbiased subset is 2 tasks, which is small and must be labelled as such.
4. **Is a second model family in scope?** It is the single highest-value addition (rival A7 is undiscriminated),
   costs ~30 trials at an unknown per-trial rate for another family, and is the largest limitation in the project.

### What happens on a yes

Steps 0–3, 6 and 8 of §15 execute with **zero model spend** and resolve the three §5 defects plus both new-task
design gates before any implementation. Nothing is built until a gate passes.

---

## 20. CONFIRMATIONS

- **Zero target-model calls.** No Gemini, no Harbor `run`, no `harbor check`, no API call to any model. All work
  was file reads plus two read-only recomputations (`python3 -B`, importing each task's shipped `tests/world.py`
  and `scenarios.py` in memory, calling `build()`/`truth()` only, writing nothing).
- **Zero new Harbor model trials.**
- **Zero existing task modifications.** All eight frozen checksums recompute to their recorded values, verified
  after every phase of this work: `02-renewal-risk-regression f696367794c1a25f`, `g05-sco-rollout-gate
  77a6e432d9d2cba2`, `g10-censored-demand 047195e7a12d34cd`, `g24-recommender-ope 2c9cc2055ef796a5`,
  `g34-fleet-reliability-gate f14dd0c0dbcd763c`, `p22-gauge-recalibration a0570585c3927b53`,
  `p20-noshow-monitoring 2c3c374b07f233fa`, `p31-fill-rate-dispute e18bf13d6080f987`.
- **Zero verifier modifications.**
- **Zero prospective modifications.** `research/phase3/` and `jobs/` untouched; the three defects in §5 are
  reported and left in place.
- **`research/phase3/analysis_plan.md` untouched** — sha256
  `c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824`, still one commit in its entire history.
- **Fallback archive untouched** — `submission_5task_fallback.zip` and `submission.zip` both still
  sha256 `c8561aad8300df6c832921fa5b86ea669def1cb04bbaba2e649e9919c5a9c760`, 8,471,008 bytes.
- **Nothing committed.** `git status` shows only the two untracked handoff files and the untracked archive.
- **Nothing pushed.** The repository has no remote configured.
- **Nothing submitted.**
