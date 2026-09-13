# Task 02 — Renewal-risk temporal provenance (design)

Harbor task: `candidates/02-renewal-risk-regression` (`forensicds/renewal-risk-regression-02`).
Validation evidence: `report/task02_validation.md`. Status: built and validated; **no model trials run**.

## 1. Hypothesis this task tests

Updated ForensicDS hypothesis (after Task 01): frontier data agents can often identify a visible
technical defect but may fail to infer and preserve the latent business or statistical invariant that
determines the correct repair, especially when several technically plausible fixes improve aggregate
metrics.

Task 01 showed agents localize a row-multiplication defect quickly; the passing agents read an identity
standard that spelled out the repair procedure. Task 02 therefore changes the mechanism (statistical
validity of a model rather than a join), removes any document that states the repair procedure, and makes
several plausible repairs produce realistic-looking metrics while still violating the invariant.

**Semantic invariant.** For every training and evaluation example, every feature must be derivable only
from information the production scorer could have seen at that example's prediction time — here, rows
loaded into the warehouse (`synced_at`) before 00:00 UTC on the prediction date.

The model card states the prediction point and that training reproduces production scoring; the data
dictionary states load semantics. No document says which module is wrong or how to reconstruct state.

## 2. Why this is real enterprise data-science work

Point-in-time correctness of training data is a well-known and recurring source of silent failures in
applied ML (training/serving skew, "future leakage" from slowly changing dimensions, backfilled or
late-arriving data). The specific pattern — a data-platform migration removes snapshot tables, consumers
port readers to current-state objects, historical examples start reading today's state, offline metrics
jump, production degrades — is an ordinary consequence of warehouse modernisation. Diagnosing it requires
reconciling offline and live evidence, reading feature code against source semantics, and understanding
availability vs event time. We do not claim this failure class is novel; the task's contribution is a
controlled, verifiable instance with a hidden-fixture generalization test.

## 3. Visible symptom

Instruction: a Customer Analytics memo — v2.4 offline evaluation far above v2.3, Sales and CS say the
scores are unusable, monitoring "does not look like the model we evaluated", retrain on hold.

Workspace evidence of the symptom (all computed at build time, not typed):

| Artifact | v2.3 | v2.4 |
|----------|------|------|
| Offline ROC AUC (`reports/model_evaluation/eval_2025-08-15.json`, `eval_2026-02-15.json`) | 0.795 | 0.936 |
| Live ROC AUC on decided renewals (`reports/monitoring/live_performance_2026-08-10.*`) | 0.796 | 0.751 |
| Mean live score vs churn rate | 0.166 vs 15.9% | 0.337 vs 17.1% |
| Churn rate among the 30% lowest scores | 1.2% | 10.8% |

Re-running the incident-time pipeline on the current extract (as of 2026-08-15) gives eval AUC 0.926;
the correct pipeline gives 0.781.

## 4. Environment

`/workspace` (agent-visible):

```
README.md, CHANGELOG.md, requirements.lock
config/pipeline.toml
data/warehouse.db                      SQLite warehouse extract (authoritative)
src/renewal_risk/                      cli, config, examples, sources/warehouse, features/{registry,contract,usage,
                                       support,pipeline_signals,health,build}, model/{transforms,train,evaluate},
                                       reporting, pipeline, scoring
docs/model_card_renewal_risk.md        prediction point, label, examples/split, model spec, version history
docs/feature_dictionary.md             25 feature definitions + defaults
docs/data/warehouse_data_dictionary.md tables, grains, current vs history tables, load schedules, synced_at
docs/ops/2026-01_crm_v3_migration.md   snapshot tables decommissioned, v3 objects + field history
docs/ops/2025-11_inc1874_crm_replication.md  replication outage, replay semantics
docs/process/model_retraining_runbook.md
notes/experiments/2026-02-16_v2.4_retrain.md   (generated) DS attributes the lift to benign changes
notes/sales/2026-08-07_renewal_risk_feedback.md (generated) low-scored accounts that churned
reports/model_evaluation/, reports/monitoring/ (generated), artifacts/ (v2.4 Q1 run)
logs/deployments.csv, logs/scheduler/training_runs.csv
```

Runtime: `python:3.12-slim-bookworm`; numpy 2.1.3, pandas 2.2.3, scikit-learn 1.5.2 (pinned); `sqlite3`.
Generator (`build/world.py`, stdlib, seeded) and history builder are deleted from the image.

### Warehouse schema and grains

| Table | Grain | Notes |
|-------|-------|-------|
| `accounts` | account | static firmographics |
| `contracts` | contract term | annual; `renewal_date` |
| `renewal_outcomes` | decided renewal | label source; `decided_at`, `synced_at` |
| `usage_weekly` | account × week | loaded Monday after week close |
| `support_tickets` | ticket (current state) | `opened_at`, `closed_at` |
| `crm_opportunities` | opportunity (**current state**) | renewal/expansion; `lead_source` direct/partner |
| `crm_opportunity_field_history` | tracked-field change | creation writes one row per field; `changed_at`, `synced_at` |
| `cs_account_health` | account (**current state**) | score, color, NPS, sentiment |
| `cs_account_health_history` | tracked-field change | nightly batch load |
| `warehouse_sync_log` | connector incident | outage + replay |

Visible extract: 1,400 accounts, 4,042 contracts, 3,200 decided renewals (16.6% churn in examples),
187k usage rows, 28k tickets, 5,084 opportunities, 52k opportunity-history rows, 82k health-history rows.
Training run as of 2026-08-15: 2,896 examples (2,119 train / 777 eval), 25 features.

## 5. Hidden causal chain

1. **Operational change.** CRM v3 migration (2026-01-12) decommissioned `crm_opportunity_daily_snapshot`
   and `cs_health_daily_snapshot` (2026-01-31). v2.3 read those per prediction date — point-in-time by
   construction.
2. **Code change.** v2.4 (RA-DS-298) ported `sources/warehouse.py` readers to the v3 objects
   `crm_opportunities` / `cs_account_health`, which hold the latest values. `features/pipeline_signals.py`
   keeps an existence filter `created_at < prediction_date`, which looks like point-in-time handling;
   `features/health.py` has none.
3. **Mechanism.** Each historical example now sees how its renewal played out: closed stages, amounts
   set to 0, `Omitted` forecasts, competitors recorded on loss, falling health scores, negative NPS and
   sentiment, and even expansion opportunities closed long after the prediction date.
4. **Offline symptom.** The model leans on these outcome proxies (top coefficients on stage, amount ratio,
   health), offline AUC 0.93.
5. **Production symptom.** Daily scoring sees the world at score time, where those proxies do not yet
   exist; scores are mis-ranked and badly calibrated (live AUC below v2.3, many "safe" churners).

## 6. Why the repair is not a one-line fix (the latent invariant)

A correct repair must reconstruct opportunity and health state from field history with **availability =
warehouse load time**:

- CS health loads nightly (~01:30 UTC next day): a change made on the day before the prediction date is
  not yet available. Using `changed_at` misstates 93 health scores alone in the visible extract.
- INC-1874 (Nov 2025) paused CRM replication for two weeks; replayed rows keep `changed_at`.
- Partner-channel opportunities replicate weekly; their creation can be known in CRM (`created_at`) but
  not in the warehouse at the prediction time, so record **existence** must also be reconstructed.
- Tracked fields change legitimately before the cutoff (so creation-time values are wrong) and after it
  (renewer expansions, health improvements), so "drop fields that change" is wrong.
- `open_expansion_opps` requires the same reconstruction for other opportunities on the account.

Measured on the visible extract: `changed_at`-based availability misstates features for 149 examples
(101 train, 48 eval).

Tie semantics were made unambiguous by construction: within one record, replicated rows have strictly
increasing `synced_at` in commit order (verified: 0 same-field ties or inversions), and the data
dictionary states rows of one record are applied in commit order.

## 7. Evidence graph (what an investigator has to connect)

```
Sales note + monitoring (live AUC down, calibration off)  ─┐
Offline reports (0.79 → 0.94)                              ├─> "offline eval not representative of scoring"
Model card: prediction point = warehouse at 00:00 on P     ─┘
        │
        ├─ CHANGELOG 2.4.0 / deployments: several simultaneous changes (distractors + the reader port)
        ├─ features/*.py: contract/usage/support respect P; pipeline_signals/health read sources.warehouse loaders
        ├─ sources/warehouse.py → crm_opportunities / cs_account_health
        ├─ data dictionary: those are current-state objects; history tables exist; synced_at semantics; load schedules
        ├─ CRM v3 migration note: snapshot tables gone; field history complete with original timestamps
        ├─ INC-1874 note + warehouse_sync_log: replay; synced_at ≠ changed_at
        └─ data: compare current vs history as of P for examples; partner lead_source weekly loads
                 → reconstruct state as of P by synced_at for all affected features; keep definitions/defaults
```

No single grep reveals the problem: `synced_at` appears on every table; the leaky readers are ordinary
`SELECT`s; the existence filter in `pipeline_signals.py` looks correct.

## 8. Distractors (real events, falsifiable)

| Distractor | Where | Why plausible | How it is falsified |
|------------|-------|---------------|----------------------|
| `class_weight = "balanced"` | config, CHANGELOG, experiment note | changes probabilities/calibration (matches "scores look wrong") | on the incident features, retraining with `class_weight=None` gives AUC 0.9253 vs 0.9258 |
| Quantile winsorization | CHANGELOG | preprocessing change | without it AUC is 0.9247 vs 0.9258 |
| 3-year training window | CHANGELOG, note | more data | row counts; gap persists on any window |
| New feature `open_expansion_opps` | CHANGELOG, note | new feature coincides with jump | removing it leaves AUC at 0.9258; the CRM + health features alone reach 0.935 |
| scikit-learn 1.3 → 1.5 | CHANGELOG, lockfile | library upgrade | deterministic LR; same model on correct features reproduces v2.3-level AUC |
| "Cleaner CRM v3 data" | experiment note | believable narrative | current-state data is cleaner precisely because it is final state |
| CS health model recalibration (Feb) | deployments | health changes | monthly `health_score` changes continue at ~880–930/month through Nov 2025–Apr 2026 |
| Enterprise share of eval set | experiment note (computed) | mix shift | every segment is inflated: v2.3 0.77/0.78/0.81 vs v2.4 0.92/0.93/0.94 (Ent/MM/SMB) |

## 9. Verifier design (19 checks, binary reward)

`tests/test_renewal_risk.py` never inspects code. Module fixture: regenerate pristine visible extract,
compare logical digest with `/workspace/data/warehouse.db`; install pristine extract; delete outputs; run
`python -m renewal_risk run --config config/pipeline.toml --as-of 2026-08-15` twice; run `score`; for each
hidden fixture regenerate, install, run with its `--as-of`; restore the agent's extract and re-run default.

References: `tests/reference.py` (pure Python + sqlite3, examples and all 25 features at prediction time)
and `tests/reference_model.py` (independent implementation of the model-card spec, run with the image's
scikit-learn).

| Group | Check |
|-------|-------|
| A | warehouse extract unmodified |
| B | training run succeeds; examples = one per eligible renewal with documented prediction date/label/split; contract/usage/support features unchanged; CRM features point-in-time; health features point-in-time; one prediction per eval example and report ROC AUC/Brier/counts recomputed from predictions; eval AUC within 0.02 of the specified model on correct features and score Spearman ≥ 0.98; deterministic re-run; production scoring still covers due renewals |
| C (×3 hidden) | examples; all feature values point-in-time; predictions/report consistency + model behaviour |

Feature tolerance 1e-6 (the reference and oracle agree exactly on all 72,400 visible cells).

## 10. Hidden fixtures (designed before any model run)

| Fixture | Calendar | What changes | Shortcuts it targets |
|---------|----------|--------------|----------------------|
| `hidden_a` | as of 2025-12-10 | leakage mostly via CS health, NPS, sentiment and competitor-on-loss; reps rarely update CRM stage; CRM outage in June 2025; health batch 04:00 | CRM-only repairs; repairs tuned to the fields that leak most in the visible extract; hard-coded Nov-2025 outage |
| `hidden_b` | as of 2024-09-20 | 2–6 legitimate pre-cutoff changes per opportunity, frequent post-cutoff legitimate changes (expansions, health improvement), 2× expansion pipeline, no outages | creation-time values; "drop fields that change"; expansion handling |
| `hidden_c` | as of 2026-03-05 | two CRM outages at other dates, 35% partner deals synced Wednesdays 23:30, 30% late-created renewal opportunities, CS health loaded with a 2-day lag | `changed_at`/`created_at` availability; hard-coded outage windows, partner batch day or health lag |

Incident-time pipeline on hidden extracts: AUC 0.94 / 0.93 / 0.92; correct features: 0.79 / 0.79 / 0.78.

## 11. Mutation suite

`tools/task02/shortcuts.py` applies each repair attempt inside the task image and runs the real
`tests/test.sh`. Controls: Nop (0), oracle (1), SQLite window-function repair (1), pure-Python event-replay
repair (1), informational probe (oracle features, class weights reverted). Shortcuts (0): constant leaky
features; drop columns; neutralize known-leaky columns on current data; `changed_at` availability;
CRM-only; health-only; creation-time values; fixed cutoff date; filter examples; random split; fewer
training rows; weaker model; patched report; edited warehouse; **overfit** availability reverse-engineered
from this extract's outage window, partner Sunday batch and health lag; **overfit** outage windows read
from `warehouse_sync_log` plus hard-coded partner/health schedules. Results: `report/task02_validation.md`.

## 12. Expected agent investigation path

1. Read memo, Sales note, monitoring, offline reports → offline/production disagreement.
2. Suspect leakage or evaluation error; check split (temporal, correct) and distractor changes.
3. Inspect feature builders; notice CRM/CS readers use v3 objects; read data dictionary and migration note.
4. Verify empirically: compare current-state values with history for old examples (closed stages, zero
   amounts before the renewal was decided).
5. Design point-in-time reconstruction; discover `synced_at` vs `changed_at` via load schedules, INC-1874,
   partner deals; handle existence and expansion opportunities.
6. Validate: offline AUC returns to v2.3-like level; audit individual examples against history at `P`;
   confirm scoring still works.

## 13. Expected failure modes

- Stop at "leaky features" and drop/neutralize them (violates the instruction; F5).
- Point-in-time reconstruction on `changed_at` (latent availability invariant missed; F4).
- Fix CRM but not health, or skip `open_expansion_opps` / existence (partial synthesis; F4/F6).
- Validate only by the AUC landing near 0.78 (aggregate metrics cannot distinguish partial repairs; F7).
- Break production scoring through timestamp dtype handling (F6).

## 14. Benchmark-validity risks

| Risk | Mitigation / residual |
|------|-----------------------|
| Leakage is a well-known failure mode; strong agents may suspect it immediately | Intended: the discriminating difficulty is the availability semantics and complete synthesis, not recognizing "leakage". |
| `synced_at` availability could be seen as a hidden requirement | Model card fixes the prediction point to "the warehouse as it stands at the start of D (00:00 UTC)"; the data dictionary defines `synced_at` as load time on every table and documents per-source load delays (nightly CS batch, weekly partner batch, CRM pauses and replays); INC-1874 and `warehouse_sync_log` record the replay. Visible data exercises it (149 examples). |
| Exact feature equality could reject legitimate alternatives | Feature definitions and defaults are unchanged from existing code; two independently written correct repairs (SQL window functions, event replay) pass. |
| Model-behaviour thresholds | AUC band 0.02 and Spearman 0.98 are wide relative to deterministic reproduction (oracle matches reference exactly); probe results reported. |
| Verifier runtime (~2–5 min) | Six training runs, each capped at 300 s (stated in the instruction); verifier timeout 2,700 s. |
| Hidden fixture schedules differ from documented "typical" schedules | Deliberate: the data dictionary documents `synced_at` as the load time for every row; schedules are described as typical. |
| Generated notes/monitoring coherence | All numbers computed from the same data and code during the build. |

## 15. How Task 02 differs from Task 01

| | Task 01 | Task 02 |
|---|---|---|
| Mechanism | join cardinality / canonical identity | temporal provenance of ML features |
| Symptom | aggregate revenue overstatement | model looks better offline, worse in production |
| Faulty component | one small module named in docstrings | two readers behind a plausible existence filter, among 15 modules and 25 features |
| Repair procedure documented? | yes (identity standard §3) | no; invariant stated at model level, semantics at data level |
| Aggregate metric proves correctness? | totals tie for partial fixes | AUC ≈ 0.78 for several wrong repairs |
| Late-arriving data | none | nightly batch, outage replay, weekly partner sync |
| Hidden fixtures | migration patterns | leak channel, legitimate change density, load schedules |

## 16. Review log (independent rubric review, before any model run)

A fresh-context reviewer applied Harbor's default rubric (11/11 PASS) plus leakage, specification,
fairness, realism and distractor review; it reproduced Oracle 19/19 and the incident pipeline 10/19, and
measured that `synced_at < P` and "latest `changed_at` among rows loaded before P" are equivalent on all
four extracts while `changed_at < P` misstates 149 / 53 / 68 / 182 examples (visible / A / B / C).

| Finding | Resolution |
|---------|------------|
| Docs nearly stated the repair: migration note mapped each snapshot table to "object + field history"; INC-1874 note said replayed rows keep `changed_at` with `synced_at` = replay time; data dictionary stressed "updates overwrite the row"; model card said nothing loaded after the prediction moment can influence a score; CHANGELOG paired "snapshot for the prediction date" with the port | Migration note now says v3 objects replace the v2 tables and the audit tables were renamed (RevOps reporting); INC-1874 keeps operational facts only; dictionary states current values plainly; model card keeps the prediction point and that training reproduces it; CHANGELOG entries neutral |
| Empty `old_value` is not unique to creation rows | Dictionary: creation rows have `changed_at` = `created_at`; later changes from an empty value also have empty `old_value` |
| A load timestamp at exactly 00:00:00; ordering only held empirically | Generator guarantees strictly increasing load order per record and no load at 00:00:00; re-verified 0 ties/inversions/midnight loads |
| "v2 audit trail imported with original timestamps" conflicts with `synced_at` semantics | Dictionary: the audit trail has been replicated continuously since 2019 and was renamed at cutover |
| Boolean-formatted feature columns rejected | Verifier accepts True/False |
| 6 × 900 s run timeouts could exceed the verifier timeout; no runtime budget stated | 300 s per run, stated in the instruction; verifier timeout 2,700 s |
| v2.3 history used v2.4's feature and 3-year window | v2.3 artifacts use 24 features and a 2-year window |
| v2.3 scored after its snapshot sources were dropped | Scoring paused 2026-02-01 – 2026-03-01 (deployment log entry), no scores in that window |
| Closed tickets' `synced_at` reflected opening; accounts loaded after their first contract | `synced_at` follows the latest version; accounts load before contracts |
| Monitoring said "decided by 2026-08-10" but used all outcomes | Filtered to `decided_at` before 2026-08-10 |
| Self-disproving distractor text ("No effect on training", "recalculation unchanged", equal Enterprise shares in the note) | Removed / reworded (health weights recalibration now a concrete change) |

Accepted and documented: `open_expansion_opps` is itself partially leaky (it is part of the root cause, not
only a distractor); the live AUC gap (0.80 → 0.75) is modest, with the complaint carried mainly by calibration
and churn among low scores; `build/pit_reference.py` is a copy of the verifier reference used at build time and
deleted from the image (not reachable by the agent, but present in an intermediate layer).
