# ForensicDS distribution matrix (Tasks 01–05)

What the five built tasks cover, and where they overlap. Baseline results are only those actually run
(`google/gemini-3-flash-preview`, gemini-cli, Harbor 0.21.0, 3 trials per condition). Tasks 03–05 have **no model
trials**; nothing below about them is a model result.

## 1. Task identity

| | 01 Revenue reconciliation | 02 Renewal-risk regression | 03 Lead-score evaluation | 04 Retention metrics | 05 Experiment readout |
|---|---|---|---|---|---|
| Domain | Finance / revenue accounting | Customer success / ML | RevOps / ML monitoring | Finance / board KPIs | Product analytics / experimentation |
| Artifact repaired | Python revenue pipeline (pandas) | Python feature pipeline + sklearn model | Python evaluation pipeline (pandas/sklearn) | SQL semantic layer (SQLite models) | Python readout pipeline (pandas) |
| Mechanism class | Entity grain / identity (join fan-out after account migrations) | Temporal leakage (current-state tables read for historical examples) | Selective labels / evaluation population under a model feedback loop | Metric population semantics (business state replaced by CRM proxy) | Causal identification (randomization unit, asymmetric exposure trigger, identity) |
| Capability isolated | Grain and canonical-identity reasoning across joins and history | Point-in-time availability reasoning | Estimand reasoning: whose outcomes measure the model's intended use | Definition-to-data mapping across cohort, lifecycle, bridge, segments | Preserving randomization: unit, arm, population, reference time |
| Statistical reasoning required | Low (accounting identities) | Medium (leakage, AUC) | High (selection, ITT vs per-protocol) — but the agent edits only the population; metrics code unchanged | Low–medium (cohort ratios, bridge identity) | High (ITT, SRM, triggered analysis, unit) — estimator code unchanged; graded object is the unit table |

## 2. Evidence and grading

| | 01 | 02 | 03 | 04 | 05 |
|---|---|---|---|---|---|
| Modalities | code, SQLite, CSV, Markdown docs, logs | code, SQLite, docs, notes, monitoring outputs | code, SQLite, config, docs, JSON reports, logs, notes | SQL, Python runner, SQLite, CSV (published/board), docs, logs, notes | code, config, SQLite, JSON readouts, docs (plan, metrics, platform), incident report, logs, notes |
| Evidence sources needed | billing extract, CRM grain, migration register, identity standard | model card (prediction point), data dictionary (current vs history, load schedules), migration/incident notes | model card (estimand), router design (holdout, SDR queue order), evaluation definition, routing events | metrics handbook, data dictionary (CRM created_at semantics), SQL models, published figures | experiment plan (unit, population, instrumentation), platform docs (triggered analysis, assignment, SDK cache), assignments vs exposures |
| Invariant | revenue lines at invoice-line grain, attributed to canonical account over history | features use only data loaded before the prediction time | evaluation cohort = intake exploration holdout, intent-to-treat, matured, any-channel 60-day label | cohort = ARR > 0 on S; handbook movements incl. reactivation; segment by starting ARR | as-assigned eligible workspaces (first assignment row), matured, 14-day workspace activation from assignment |
| Grading grain | invoice line × account × month | example × feature (72,400 cells) + model behaviour | lead (membership, label, score) + report | (quarter, account) classification + quarterly and segment metrics | workspace (membership, arm, stratum, outcome) + readout and decision |
| Tempting shortcut | drop_duplicates / filter migrated rows | drop or neutralise leaky features; change-time availability | worked leads only; per-protocol holdout; latest routing state | exclude ABM accounts; first contract signing; fix NRR only | exposure-triggered workspaces; latest assignment row; user-level ITT |
| Aggregate metric enough to validate? | No (account-level attribution) | No (AUC close under partial fixes) | No (AUC nearly identical for ITT, per-protocol, latest routing) | No (NRR right, bridge/segments wrong) | No (several wrong populations give "inconclusive") |
| Hidden generalisation mechanism | 3 generated snapshots: other migration patterns and months | 3 extracts: other load schedules, outages, partner syncs | 3 extracts: holdout share, router versions, re-routing, pauses, self-serve, boundaries | 3 extracts: win-backs/short terms, early signing and renewal gaps, segment crossings and CRM noise | 3 extracts: null/positive/negative effects, reversed logging asymmetry, re-bucketing, eligibility, maturity |
| Verifier checks (incl. parametrized) | 28 | 19 | 14 | 18 | 14 |
| Pipeline sandbox in verifier | no | no | yes | yes | yes |
| Mutation suite | 28 cases | 21 cases | 24 cases | 24 cases | 27 cases (1 informational) |

## 3. Status and baseline

| | 01 | 02 | 03 | 04 | 05 |
|---|---|---|---|---|---|
| Oracle / Nop (Harbor) | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |
| harbor check | did not complete (setup timeout, no key at the time) | 11/11 | 11/11 | 11/11 | 11/11 |
| Independent adversarial review | substitute rubric review | done | done + cross-task, fixes applied | done + cross-task, fixes applied | done + cross-task, fixes applied |
| Gemini baseline (diagnosis) | 2/3 passed, pass@3 = 1 | 0/3, pass@3 = 0 | not run | not run | not run |
| Other conditions | — | explicit-invariant ablation 0/3, **confounded** by wording (one failure is a condition-design flaw) | — | — | — |
| Assessment | too easy for target | meets target on n = 3 | pre-baseline; cross-task review: risk of being too easy | pre-baseline; risk of being too easy | pre-baseline; moderate risk |

## 4. Overlap and gaps

- **Shared scaffold.** All five tasks use the same shape: memo + repository + SQLite extract + docs + history;
  a single command regenerates outputs; the verifier re-runs it on the pristine extract and three hidden extracts.
  An agent that learns "compare the CHANGELOG with the definition docs" gets a head start on 03–05 (see
  `cross_task_review.md`).
- **Two "population" tasks.** 03 (evaluation population) and 04 (metric cohort) both repair *who is counted*.
  They differ in reasoning type (statistical selection vs definitional state) and in artifact (pandas vs SQL), but
  a benchmark reader could see them as one family. 05 is also partly a population repair (who is analyzed), with
  added causal/unit reasoning.
- **Not covered:** streaming/event-time data (the old 04 idea), unit-of-measure/currency versioning, many-to-many
  allocations, training-label lag (old 06), data-quality incidents where the *data* rather than the code is wrong.
- **Artifact diversity:** one SQL task (04); the rest are pandas pipelines.
