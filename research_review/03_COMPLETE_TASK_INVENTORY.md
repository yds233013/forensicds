# 03 — Complete task inventory

Every task directory that exists, every candidate that was proposed and never built, and the reason for
each disposition. Hashes and trial counts are **VERIFIED FROM ARTIFACT**
(`MACHINE_READABLE_INVENTORY.csv`, `ALL_TRIALS.csv`); dispositions cite commits where one exists.

**24 task directories** exist on disk. **10** are the final ten. **3** more ship in the
submission archive as clearly-marked extras. **5** candidates were proposed and never built.

## Tasks that were built

| task | status | files | aggregate sha256 | Gemini | Claude | instrumented |
|---|---|---|---|---|---|---|
| `02-renewal-risk-regression` | FINAL TEN | 55 | `b31eb4fe580477cf…` | 0/3 | 3/3 | no |
| `g05-sco-rollout-gate` | FINAL TEN | 39 | `7525ddb2ff902b42…` | 0/4 | 3/3 | no |
| `g08-forecast-accuracy-vintages` | FINAL TEN | 39 | `a7f073a3402b1bc1…` | 1/3 | 3/3 | no |
| `g10-censored-demand` | FINAL TEN | 40 | `7c72dd098ce3bfcd…` | 0/3 | 0/3 | no |
| `g24-recommender-ope` | FINAL TEN | 43 | `505e59ccf71f93da…` | 0/3 | 3/3 | no |
| `g36-tou-capacity-gate` | FINAL TEN | 37 | `6cb3dd64e37a1286…` | 0/3 | 0/3 | no |
| `g50-courier-boost-rollout` | FINAL TEN | 43 | `656a5a166d37962f…` | 0/3 | — | yes |
| `p20-noshow-monitoring` | FINAL TEN | 43 | `62943714d631e6a9…` | 0/3 | 0/3 | yes |
| `p22-gauge-recalibration` | FINAL TEN | 41 | `8da6ed0e70dff9aa…` | 0/3 | 1/3 | yes |
| `p31-fill-rate-dispute` | FINAL TEN | 40 | `67fb8e658f8a468c…` | 0/3 | 0/3 | yes |
| `01-revenue-reconciliation` | built gen-1 | 43 | `4a742731cb2f23d6…` | 2/3 | — | no |
| `02-renewal-risk-regression-v1.1` | remediation fork | 55 | `959a2dce4644f63c…` | — | — | — |
| `02-renewal-risk-regression__explicit-invariant` | ablation | 54 | `600c487c7525bbe1…` | 0/3 | — | no |
| `03-lead-score-evaluation` | built gen-1 | 33 | `8e57afe5d732edaa…` | 3/3 | — | no |
| `04-retention-metrics-regression` | built gen-1 | 36 | `42936d7b433ae804…` | 1/3 | — | no |
| `05-onboarding-experiment-readout` | built gen-1 | 34 | `6f5130ccf0d6ac4f…` | 3/3 | — | no |
| `06-usage-statement-close` | built gen-1 | 43 | `226bbb85dae1948d…` | 3/3 | — | no |
| `g34-fleet-reliability-gate` | built | 37 | `92abc89eb933214e…` | 2/3 | — | no |
| `g35-dispatch-priority-gate` | built | 35 | `8128163e6ccb3a32…` | 3/3 | — | no |
| `g36-tou-capacity-gate-v1.1` | abandoned | 36 | `6af91435c5da1672…` | — | — | — |
| `g41-service-parts-rebalancing` | built, frozen | 36 | `e603282196c909db…` | 1/3 | — | no |
| `g42-contractor-safety-rate` | built, frozen | 38 | `6c8fb5c700938234…` | 3/3 | — | no |
| `g44-screening-precision` | built, frozen | 38 | `85b36eb91cab0f5b…` | 2/3 | — | no |
| `p20-noshow-monitoring-v1.1` | remediation fork | 42 | `a4648f0778849b8a…` | 0/3 | — | yes |

### Disposition and reason, per task

**`01-revenue-reconciliation`** — *built gen-1.* Revenue reconciliation under staged account migrations. **Excluded** from the final ten: 2 of 3 Gemini trials passed, and its reconciliation mechanism overlaps `p31`.

**`02-renewal-risk-regression`** — *FINAL TEN.* Point-in-time correctness. Included as the only temporal-reconstruction task.

**`02-renewal-risk-regression-v1.1`** — *remediation fork.* Two-stage Dockerfile fixing defect D2. Agent-visible workspace byte-identical to v1. **Never trialled.**

**`02-renewal-risk-regression__explicit-invariant`** — *ablation.* Same world with the invariant stated outright in the instruction. **Not a separate task.** Scored 0/3, which is the project's evidence that difficulty is not concentrated in *noticing*.

**`03-lead-score-evaluation`** — *built gen-1.* **Excluded**: saturated, 3/3.

**`04-retention-metrics-regression`** — *built gen-1.* **Excluded**: 1/3, and its metric-regression mechanism overlaps `p31` with a weaker decision stake.

**`05-onboarding-experiment-readout`** — *built gen-1.* **Excluded**: saturated, 3/3.

**`06-usage-statement-close`** — *built gen-1.* **Excluded**: saturated, 3/3. Its baseline commit `b2fc98b` is explicitly labelled 'too easy' and triggered the first hypothesis revision.

**`g05-sco-rollout-gate`** — *FINAL TEN.* Staggered-adoption identification. Six calibration rounds, 38/38 mutations (`2fc7e5e`).

**`g08-forecast-accuracy-vintages`** — *FINAL TEN.* Data vintage / restated actuals. Included on mechanism uniqueness despite being the easiest of the ten (1/3 Gemini).

**`g10-censored-demand`** — *FINAL TEN.* Informative censoring, endogenous to the intervention. First 'estimand-first' design (`b9f48b1`).

**`g24-recommender-ope`** — *FINAL TEN.* Off-policy evaluation under a logging policy.

**`g34-fleet-reliability-gate`** — *built.* Competing risks / wrong statistical object. **Strongest excluded candidate** — a genuinely distinct mechanism, but 2 of 3 Gemini trials passed, so it contributes little headroom.

**`g35-dispatch-priority-gate`** — *built.* **Excluded**: saturated, 3/3.

**`g36-tou-capacity-gate`** — *FINAL TEN.* Population definition under tariff migration. Note `30026c6` closed v1 as *development-only*; it was later promoted into the final ten. **This is a documented status change** and is flagged in OPEN_QUESTIONS.

**`g36-tou-capacity-gate-v1.1`** — *abandoned.* `063330c`: abandoned after a forecast-only counterexample search; `d9eaf9e`: halted at response-tolerance calibration (degenerate window), left unfrozen. **Never trialled.**

**`g41-service-parts-rebalancing`** — *built, frozen.* `3f31849e44d9e392`. **Excluded**: 1/3, mechanism overlaps `g10`/`p31`, and its oracle history is unstable (`g41-oracle-v2`, `-v3`, `-probe2` recorded 0 before repair) — the weakest verifier robustness in the pool.

**`g42-contractor-safety-rate`** — *built, frozen.* `4b4ded75469d229a`. **Excluded**: 3/3, recorded as development-only.

**`g44-screening-precision`** — *built, frozen.* `e688a53ec78348cb`. **Excluded**: 'solved on its object 3/3' (`8b24e99`); calibration/threshold mechanism overlaps `p20`/`g36`.

**`g50-courier-boost-rollout`** — *FINAL TEN.* Interference / unit of intervention. The most heavily validated task in the project (four dedicated handoffs) and the only one that re-executes the agent's own command across five worlds.

**`p20-noshow-monitoring`** — *FINAL TEN.* Policy feedback + feature vintage + drift decomposition. Criterion-instrumented. Carries defect D1 (sign convention).

**`p20-noshow-monitoring-v1.1`** — *remediation fork.* Sign convention stated. **Separately exposed**: 3 Gemini trials, 0 passes, zero sign failures.

**`p22-gauge-recalibration`** — *FINAL TEN.* Measurement-system bias. Criterion-instrumented. Produced the dossier's sharpest single observation.

**`p31-fill-rate-dispute`** — *FINAL TEN.* Contractual metric definition. Criterion-instrumented. Shows the mirror-image failure shape.

## Candidates proposed and never built

These have no task directory. They are recoverable only from commit subjects and the `research/`
directory, and they matter because **the rejections are where the design rules came from**.

| id | subject | disposition |
|---|---|---|
| `g37` | measurement-system change | **DROP, research only** (`81ed909`). Mechanism later realised in `p22`. |
| `g38` | (see research dir) | **DROP, research only** (`dcb0445`), closed alongside a failure meta-analysis. |
| `g39` | structural-object tournament | **SEARCH AGAIN, research only** (`b2d6401`) — no acceptable instance found. |
| `g40` | ALERT | **Dropped at stage 2** in deadline mode (`35239d6`). |
| `g43` | (see research dir) | **Rejected pre-build on design principle 17** (`88784ff`) — the only candidate killed before any code was written. |

**INFERENCE:** the ratio is informative — of roughly 15 generation-3 candidates detailed in
`d256f8a`, 8 were shortlisted (`06ad14a`), and of the G34-G44 run only 4 reached a freeze while 5 were
dropped and 1 was rejected pre-build. The project discarded more than it kept.

## Why the five assignment blueprints were not built as new tasks

The final-ten assignment supplied five explicit new-task blueprints and instructed that a blueprint
already covered strongly must **not** be rebuilt. The audit result:

| blueprint | already covered by | verdict |
|---|---|---|
| 1 — SaaS retention / policy feedback / changing observation process | `02` (point-in-time correctness) + `p20` (policy feedback) | **covered — not built** |
| 2 — supply chain / stockout-censored demand / procurement | `g10` | **covered — not built** |
| 3 — fintech / delayed + selective labels | `g24` (logging-policy selection), `02` (label timing) | **partially covered — not built** |
| 4 — product experiment / repeated measures / unit of analysis | `g50` + `g05` | **covered — not built** |
| 5 — deployment / calibration / threshold / population shift | `p20` + `g36` + (excluded) `g44` | **covered — not built** |

**The one capability absent from the entire pool** is an *identification-removed* sibling world in which
the professionally correct answer is justified deferral — 'not identifiable from the available evidence'.
That is a sibling-world **variant**, not a distinct task, and it cannot be retrofitted to an already
exposed task without invalidating its exposure record. It is therefore carried as the highest-priority
generation template rather than built as an eleventh task competing for a slot. See `12_NEXT_EXPERIMENTS.md`.

## Built-versus-never-built, summarised

| category | count |
|---|---|
| task directories on disk | 24 |
| final ten | 10 |
| shipped extras (ablation + 2 remediation forks) | 3 |
| built but excluded from the final ten | 10 |
| built, abandoned, never trialled | 1 (`g36-tou-capacity-gate-v1.1`) |
| proposed, never built | 5 |

## Unresolved inventory questions

1. **`g36-tou-capacity-gate` status change.** Commit `30026c6` closes it as *development-only*; it
   nonetheless appears in the final ten. No artifact in this repository records the promotion decision.
   **UNKNOWN** — flagged in `OPEN_QUESTIONS.md`.
2. **`g36-tou-capacity-gate-v1.1`** was abandoned and left unfrozen but remains on disk; it is not in the
   submission archive and was never trialled.
3. **`submission.zip` is a byte-identical copy of `submission_5task_fallback.zip`.**
   **VERIFIED FROM ARTIFACT, RERUN:** both hash to `c8561aad8300df6c8329…`. It is not a third artifact,
   so the repository holds exactly two distinct submission archives: the five-task fallback and
   `submission_final10.zip`.
