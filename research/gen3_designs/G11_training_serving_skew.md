# G11: Dispatch-ETA training-serving skew across several feature families

Status: design only. Nothing built, no model run. All numbers are generator design targets, to be recalibrated at build.

## Workspace sketch

```
/workspace
├── README.md                                  repo purpose, CLI usage (build-training / train / score / parity); no semantics
├── config/eta_v5.yaml                         training window, feature list, HGBR hyper-parameters, output paths
├── src/etaml/
│   ├── cli.py                                 subcommands; `--extract` points at the extract bundle
│   ├── extract.py                             loaders for SQLite, JSONL.gz logs, YAML
│   ├── population.py                          courier assignments of delivered orders → one request row each (correct)
│   ├── labels.py                              label = delivered_at − assigned_at, minutes, from `orders` (correct)
│   ├── features/request.py                    pickup_km, dropoff_km, hour_of_week, basket_items (clean)
│   ├── features/restaurant.py                 prep_p50_7d, recent_delay_60m (faulty)
│   ├── features/courier.py                    trips_28d, acceptance_rate_7d, avg_speed_28d (faulty)
│   ├── features/weather.py                    precip_mm_1h via pit.asof_join on loaded_at (clean; "innocent")
│   ├── features/pit.py                        generic Feast-style as-of join: entity_ts vs feature event_ts, ttl
│   ├── train.py / evaluate.py / score.py      model spec from config; offline eval; score a JSONL vector file
│   └── parity.py                              platform-team parity check (see §8)
├── extract/                                   replaced wholesale by each hidden fixture
│   ├── warehouse.sqlite                       ~150 MB (tables in §5)
│   ├── serving_logs/served_vectors.jsonl.gz   ~1,250 logged vectors, 2026-06-15 → 2026-08-30 (2 % sample)
│   └── serving_config/
│       ├── feature_views.yaml                 exported registry: view type, entity key, ttl, on_miss, materialization SQL
│       └── feature_views_history.csv          registry change log (view, field, old, new, effective_at)
├── docs/
│   ├── model_card_dispatch_eta.md             prediction point, label, population, feature list, model spec, versions
│   ├── feature_dictionary.md                  business definitions of the 10 features (windows, units)
│   ├── data/warehouse_dictionary.md           tables, grains, "current values" semantics, ingest columns
│   ├── platform/feature_store_overview.md     batch vs stream views, publication, TTL, on_miss, replica reads
│   ├── platform/vector_logger.md              sampling, record schema, logger_version
│   ├── identity/courier_identity_service.md   refs vs courier ids, map versions, merges/splits, activation QA
│   └── ops/order_corrections_process.md       tablet undo, ops review back-fills, courier-app fixes
├── reports/
│   ├── offline_eval_v4.json, offline_eval_v5.json
│   ├── online/eta_error_daily.csv             online MAE by day × zone, 2026-07-01 → 2026-09-11
│   ├── monitoring/feature_drift_2026-09-08.json   PSI per feature, train window vs first week online
│   └── parity/parity_check_2026-08-31.json    output of parity.py ("all features within tolerance")
├── notes/ds/2026-08-28_v5_retrain.md          (generated) author attributes gain to courier features + more data
├── notes/incident/2026-09-10_eta_regression_thread.md  (generated) Slack export: ops, platform, DS positions
├── notebooks/v5_feature_importance.ipynb      (generated, executed) permutation importance, SHAP-like bars
└── ops/serving_deploys.csv, ops/serving_CHANGELOG.md
```

Sizes: 190k training rows (800 assignments/day × 238 days), 214k orders, 460k courier offers, 214k trips, 1,050
courier refs → 960 courier ids, 180 restaurants, 41 identity-map versions, ~1,150 materialization runs.

## 1. Research question

When several features of a production model are skewed between offline training and online serving for *different*
system reasons, can an agent reconstruct, for every historical request, the vector the serving system *would have
served*, rather than the vector that was *knowable* at request time, and validate the rebuild below the aggregate level
using a small, partly corrupt serving-log sample that covers only the end of the training window?

## 2. Enterprise setting

A food-delivery marketplace predicts delivery duration at the moment a courier is assigned ("dispatch ETA"); the
number is shown to the customer and feeds batching decisions. DS owns the training repository; the Platform team owns
the online feature store and serving (their code is *not* in the repo, only an exported registry, run metadata,
deploy log and docs). A vector logger samples served requests. Model v5 (retrained 2026-08-28, deployed 2026-09-01)
added restaurant and courier dynamic features over v4.

## 3. Visible symptom

Instruction memo (Head of Marketplace Science):

> v5 looked like our best ETA model offline (MAE 5.71 vs 6.42 min for v4) and it made the customer ETA worse online:
> +9% MAE in the first ten days. Platform says their parity check is green; the retrain notes say the gains came from
> the new courier features; Ops blames the new-zone launch. I don't want a rollback to v4 and I don't want features
> removed: the dispatch team needs the v5 signals. Fix the training pipeline so that the next retrain is trustworthy.
>
> 1. `python -m etaml build-training --extract extract --start 2026-01-05 --end 2026-08-30` must write
>    `out/training/rows.parquet` (one row per request, the columns in the model card) and `python -m etaml train`
>    then `python -m etaml score --vectors <file>` must work as documented in the README. Same commands will be run on
>    other extracts.
> 2. `extract/` is authoritative; do not modify it. Keep the model card's population, label, feature list and model
>    specification.
> 3. No special handling of particular dates, restaurants, couriers, runs or incidents.
> 4. Write `out/parity/parity_report.md` explaining what you found and how you checked it.

It does not say "skew", "serving", "snapshot", "identity", "correction" or "default".

## 4. Source distribution inspiration

- Training-serving skew is a widely described production-ML failure; the "log features at serving time and train on
  them" remedy and its cold-start problem are standard practice (Google's "Rules of ML" discusses logging served
  features; to verify exact wording).
- Feature-store point-in-time joins (Feast-style `get_historical_features`) join on event timestamp with a TTL; they do
  not model online materialization cadence or publication lag. This is the natural-wrong helper.
- Identity resolution with versioned maps and late activation; streaming aggregates that are not re-keyed after merges.
- Operational back-fills of event timestamps (kitchen tablets marking ready early, later corrected).
- Sentinel defaults (−1) online vs NaN offline in tree models with native missing handling.

No company-specific claims.

## 5. Causal graph / ground truth

The generator simulates the marketplace *and* the serving system, and stores for every request the exact vector served
(`truth_served`, never shipped) plus the true label.

**World.** 180 restaurants in 9 zones; 1,050 courier refs; orders with `placed_at, accepted_at, promised_ready_at,
ready_at, assigned_at, picked_up_at, delivered_at`. Prep time lognormal(μ by restaurant, σ 0.35); delivery duration
driven by prep, distance, courier speed, rain. Zone Z9 launches 2026-08-17 (real mix shift, distractor).

**M1 Batch materialization (`restaurant_stats` view → `prep_p50_7d`).**
- Cadence: daily run at watermark 00:00 UTC until 2026-04-19; every 6 h (00/06/12/18) from 2026-04-20.
- Each run: `started_at = watermark + U(3, 20) min`, `published_at = started_at + U(20, 70) min`; 2.5% of runs
  `status='failed'` (publish nothing).
- A run writes a row for a restaurant iff ≥1 order has `ready_at_asof(started_at)` in `[W−7d, W)`; value =
  `percentile_cont(0.5)` of `(ready_at − accepted_at)` minutes over those orders if count ≥ 10, else NULL.
- Online row persists until overwritten or `ttl` (30 h from its run's `published_at`) expires → `on_miss` (NaN for this
  view).
- Served at `t`: value from the most recent successful run with `published_at ≤ t` that wrote the restaurant, if within
  TTL; else `on_miss`.

**M2 Timestamp corrections.** 7,600 corrections on `ready_at`, `picked_up_at`, `delivered_at`:
- `tablet_undo` (32%): `corrected_at` 1–8 min after the original.
- `ops_review` (55%): 1–12 days later; `ready_at` shifts +4 to +25 min.
- `courier_app_fix` (13%): 2–40 h later; on `picked_up_at` / `delivered_at`.

`orders` holds corrected values. `ts_asof(τ)` = latest correction with `corrected_at ≤ τ`, else the original. Stream
views apply corrections as retractions at `corrected_at` (τ = request time); batch views read the replica at
`started_at` (τ = run start). The label uses final corrected values.

**M3 Stream view `restaurant_live` → `recent_delay_60m`.** Mean of `ready_at_asof(t) − promised_ready_at` (min) over the
restaurant's orders with `ready_at_asof(t) ∈ [t−60m, t)`. No orders → key expired → `on_miss` = 0.0.

**M4 Identity.**
- `identity_map_versions`: 41 weekly versions with `created_at` and `activated_at`; activation QA lag 0–4 days.
- Changes: 58 merges (duplicate accounts) and 3 splits (erroneous merge reverted).
- Serving resolves the request's `courier_ref` with the version active at `t` (max `activated_at ≤ t`).
- Stream counters (`courier_activity` view) are keyed by the courier_id resolved **at the event's `ingested_at`** and
  are never re-keyed.
- `ingested_at = event + U(2, 40) s`, plus a documented stream backlog (INC-3310, 2026-03-11 13:00–17:40) delaying
  ingest by 20–95 min.

**M5 Courier stream features** at `t`, over events with `ingested_at < t` whose ingest-time courier_id equals the
request's courier_id:
- `trips_28d` = trips with `completed_at ∈ [t−28d, t)`.
- `acceptance_rate_7d` = accepted / offered over offers in `[t−7d, t)`; count 0 → key expired → `on_miss`; count 1–4
  → stored NULL → NaN.
- `avg_speed_28d` = mean `distance_km / (delivered_at_asof(t) − picked_up_at_asof(t))` in km/h; count 0 → `on_miss`.

**M6 Default semantics change.** `feature_views_history.csv`: on 2026-04-20 `courier_activity.on_miss` changed from
`null` to `-1` (serving release 3.8). This affects all three courier features: before it, expired keys served NaN;
after it, −1 (including `trips_28d`, where offline naturally computes 0).

**M7 Innocent feature.** `precip_mm_1h` = precipitation of the last complete hour with `loaded_at ≤ t` (the faulty code
already does exactly this). Monsoon onset 2026-08-25 → PSI 0.41 in the drift report. Served == offline.

**M8 Logger bug.** `logger_version 1.2` (2026-07-08 → 2026-07-11) wrote `trips_28d` and `acceptance_rate_7d` swapped
whenever a view reloaded (every record in that period). Fixed in 1.3 (serving_CHANGELOG).

**Faulty v5 builder (incident code).**
- `restaurant.py` reads warehouse hourly rollups `feat_restaurant_hourly` (dbt, over corrected `orders`) joined on
  `floor(assigned_at, hour)` **inclusive**, so up to 59 min of future orders are included; `recent_delay` likewise.
- `courier.py` maps every event and request with the **latest** identity map, windows on `completed_at`, NaN for
  empty.

**Model.** `HistGradientBoostingRegressor(loss="absolute_error", learning_rate=0.06, max_iter=350, max_leaf_nodes=31,
min_samples_leaf=40, l2_regularization=1.0, early_stopping=False, random_state=7)` on the 10 features; temporal
split: last 21 days of the window are offline eval.

## 6. Latent statistical/business invariant

For every request `r` (courier assignment at time `t`), each training feature must equal the value the online
feature service returned at `t`. That value is determined by the view's own publication mechanism:

- latest successful published run within TTL, computed on replica state at run start;
- stream state at `t` with corrections applied as of `t`;
- identity resolved per side at its own time: request at `t`, each event at its ingest;
- `on_miss` semantics in force at `t`, distinguishing expired keys from stored nulls.

The label is the final corrected duration. No function of the feature's *event-time* history alone satisfies this;
the invariant lives at grain request × view publication state.

## 7. Grains and state variables

| Grain | State |
|---|---|
| request (assignment) | `t`, restaurant_id, courier_ref, served vector, label |
| restaurant × materialization run | watermark, started_at, published_at, status, written value / NULL / not written |
| order × timestamp field × correction | original, corrected, corrected_at |
| courier_ref × map version | courier_id; version created_at / activated_at |
| trip/offer event | event time, ingested_at, ingest-time courier_id |
| feature view × registry version | ttl, on_miss, effective_at |
| logged vector | served_at, logger_version, fv run id, map_version |

Mistakes between request-time and run-start-time state (M1×M2), and between request-time and ingest-time identity (M4),
are the core grain errors.

## 8. Evidence graph

(★ = on the natural path; almost every agent will open it.)

| Artifact | What it shows |
|---|---|
| ★ memo | offline better, online worse; parity "green"; no rollback / no feature removal |
| ★ `reports/online/eta_error_daily.csv` | MAE up in all zones incl. old ones (against pure mix shift); Z9 worse |
| ★ `offline_eval_v5.json` / v4 | offline 5.71 vs 6.42 |
| ★ `monitoring/feature_drift_2026-09-08.json` | PSI: precip 0.41 (innocent), prep_p50 0.12, trips_28d 0.03, acceptance 0.06 (the −1 mass looks like a small bin shift) |
| ★ `parity/parity_check_2026-08-31.json` + `parity.py` | per-feature mean relative diff < 10% on logged rows, NaN pairs dropped, −1 treated as missing → "PASS" for all features |
| ★ `serving_logs/served_vectors.jsonl.gz` | row-level truth for 2% of Jun 15–Aug 30; fields `fv_runs.restaurant_stats`, `map_version`, `logger_version` |
| ★ `features/*.py`, `pit.py` | hourly inclusive join (obvious leak), latest map, NaN defaults |
| `docs/platform/feature_store_overview.md` | batch views materialized per `materialization_runs`; reads return the most recently *published* values; failed runs publish nothing; TTL / on_miss; "batch views read the operational replica at run start"; "stream views apply upstream retractions" |
| `serving_config/feature_views.yaml` | per view: type, entity, ttl, on_miss (current), materialization SQL (percentile_cont) |
| `serving_config/feature_views_history.csv` | on_miss change on 2026-04-20 |
| `docs/identity/courier_identity_service.md` | versions are created weekly, activated after QA; "consumers load the active version"; stream processors resolve at ingest; historical aggregates are not rewritten |
| `docs/ops/order_corrections_process.md` | three correction sources and their timing; corrections are applied to the replica when approved (`corrected_at`) |
| `docs/data/warehouse_dictionary.md` | `orders` = current (corrected) values; `order_corrections` audit; `ingested_at` meaning |
| `ops/serving_CHANGELOG.md` | 3.8 on_miss change; logger 1.3 "fix column order after view reload" |
| `ops/serving_deploys.csv` | releases incl. 3.8 on 2026-04-20, logger 1.3 on 2026-07-11 |
| `notes/ds/v5_retrain.md` | "courier features +0.4 min; more data" (plausible, partly true offline) |
| `notes/incident/...thread.md` | Ops: Z9 launch; Platform: parity green; DS: "maybe overfit, v5 has 350 trees" |
| `materialization_runs`, `identity_map_versions` tables | cadence change, failures, activation lag |
| INC-3310 note (in thread + `ops/`) | stream backlog timing |

## 9. Evidence authority hierarchy

1. **Model card: the prediction point and "training rows reproduce the online request".** This governs *what* is
   graded. The card says the model is trained "on the features the dispatch service receives". It does not say how to
   compute them.
2. **Extract system-of-record tables** (`materialization_runs`, identity versions, corrections, ingest columns) and the
   exported registry with its history. These are facts about serving behaviour.
3. **Platform and identity docs.** They are generic mechanism descriptions and are subordinate to the tables where
   tables are more specific (e.g., actual publication times beat "runs every 6 hours").
4. **Serving logs** are direct observations, but a sample, only for Jun 15+, and corrupt for logger 1.2. They validate;
   they do not define pre-June semantics (the on_miss change and the daily cadence predate logging).
5. **Parity report, drift report, retrain note, thread.** These are derived or opinion artifacts.
   - The parity report conflicts with row-level log comparison. The logs govern, because `parity.py` visibly drops
     NaN/−1 pairs and uses a 10% relative tolerance.
   - The drift report is a distribution statement, not a parity statement.

## 10. Plausible hypotheses

| H | Evidence for | Evidence against |
|---|---|---|
| H1 v5 overfit (bigger model) ★ | 350 vs 200 trees; train/eval gap slightly larger; thread says so | offline eval is temporal and still improves; v4 spec retrained on v5 table also degrades online in replay; row-level logs mismatch |
| H2 traffic mix shift (Z9 launch, monsoon) ★ | Z9 MAE highest; precip PSI 0.41 | MAE rose in Z1–Z8 from Sep 1 before monsoon peak; logged precip matches offline exactly |
| H3 "the obvious leak" (hourly inclusive join) is the whole story ★ | code clearly includes future orders; removing it lowers offline gain | logs still mismatch prep_p50 on ~97% of rows after a PIT-on-event-time fix |
| H4 training-serving skew, several mechanisms | logs vs rebuild per feature; run ids in logs; registry history | parity report "green" |
| H5 logging bug makes logs unusable ★ | logger 1.3 fix; swapped columns visible Jul 8–11 | bug is bounded by logger_version; all other rows are consistent |

## 11. Why each wrong hypothesis is plausible

- **H1:** retrain notes and a larger model are the classic post-deploy suspects; offline/online gaps are
  folk-attributed to overfitting.
- **H2:** a real launch and real weather drift coincide with deploy; the drift report ranks precip first, and the
  dashboard aggregate cannot separate them.
- **H3:** a genuine leak exists and is the first thing a strong agent finds. Fixing it produces a plausible offline
  MAE of 5.98 (between v4 and v5). This is the headline attractor.
- **H5:** the logs genuinely contain a bug, so dismissing log mismatches as "logger issues" is tempting.

## 12. Investigation path (≈ 45–75 actions)

1. (1–6) Memo, README, model card, reports, online errors by zone. Discovery: degradation is not only Z9.
2. (7–12) Features code. Discovery: hourly inclusive join (leak), latest map, NaN defaults. Many agents stop and
   implement a PIT-on-event-time rebuild here (§13).
3. (13–18) Drift and parity reports, `parity.py`. The careful agent notices the NaN-dropping and 10% relative tolerance.
4. (19–26) Load logs; compare the rebuilt table to logged vectors per feature at row level. Discovery: prep_p50
   mismatches almost everywhere; logs carry `fv_runs.restaurant_stats` run ids that are *older* than the latest
   scheduled watermark for requests shortly after 00/06/12/18.
5. (27–33) `materialization_runs`: publication lag, failed runs, cadence change in April. Implement snapshot
   resolution; mismatches drop to ~1.5%. The residual sits on restaurants with recent `ops_review` corrections →
   read the corrections doc → replica state at `started_at`.
6. (34–40) Courier features: mismatches concentrate on couriers with merges. Identity doc and map versions; first try
   request-time map for all events (still wrong for merges inside the window); then ingest-time mapping;
   created_at vs activated_at.
7. (41–47) Acceptance / trips defaults: logs show both −1 and NaN for acceptance; relate to offer counts (0 vs 1–4);
   YAML `on_miss`; `feature_views_history.csv` shows pre-April NaN. Realise the logs cannot validate Jan–Apr.
8. (48–52) recent_delay: residual on `tablet_undo` orders → as-of `t`, not "original everywhere".
9. (53–58) Logger 1.2 rows: swapped values; exclude by `logger_version`, not by dates.
10. (59–66) Labels: confirm the label uses final values (model card: "delivered time after ops review") and was not
    accidentally switched to as-of.
11. (67–75) Validation below aggregate (§17), retrain, score, determinism, write report.

## 13. Natural wrong implementation

"Point-in-time join on event time for everything" using the repo's own `pit.py` or pandas `merge_asof`:

- prep_p50 and recent_delay: rolling windows ending exactly at `t` over `orders` (corrected values).
- Courier: windows on `completed_at < t` / `offered_at < t`, still latest map (or map at `t` for everything).
- Defaults: NaN, or `fillna(-1)` after reading the YAML.
- Label unchanged.

What it gets wrong (design targets, fraction of 190k rows differing from `truth_served`):

| Feature | Faulty v5 | PIT-on-event-time |
|---|---|---|
| prep_p50_7d | 98% | 96% (window end ≠ snapshot watermark; any order in the gap moves the median) |
| recent_delay_60m | 31% | 2.6% (ops_review back-fills) + 1.1% (empty window: NaN vs 0.0) |
| trips_28d | 9% | 4.4% (merges, latest map) + 1.9% (0 vs −1 after April) |
| acceptance_rate_7d | 11% | 3.1% (merges) + 4.9% (expired vs null semantics) |
| avg_speed_28d | 12% | 5.8% |

- Offline MAE after the PIT fix: 5.98 (looks like "the leak is fixed").
- Online replay MAE (verifier's held-out Sep 1–14 served vectors): faulty 6.96, PIT 6.55, oracle 6.12, v4 6.38.

The PIT model is still worse than v4 online, but the agent cannot see online replay for a new model. The only
visible signal is logs, and only if compared per row.

## 14. Second-order failure modes

After a first rejection:

1. **Snapshot = `floor(t, 6h)`.** Scheduled watermark, ignoring publication lag, failed runs and the pre-April daily
   cadence. prep_p50 mismatch 14% (Jan–Apr nearly all rows).
2. **Snapshot resolution correct, but the window computed on corrected `orders`** (or corrections as of `t`). Mismatch
   1.4%.
3. **"Original timestamps everywhere"** (undo all corrections). Breaks recent_delay for `tablet_undo` (0.9%), avg_speed,
   and, if applied to labels, **every corrected label** (2.8% of labels).
4. **Map at request time for all history.** Merges within 28 d: trips_28d 2.2%.
5. **Map by `created_at`.** 0.6%.
6. **`fillna(-1)` for courier features over all history** using the current YAML. Wrong for Jan 5–Apr 19 expired keys
   (1.3%); also turns 1–4-offer NULLs into −1 (3.6%).
7. **Override rebuilt rows with logged vectors where available.** Harmless on valid rows, wrong on logger-1.2 rows,
   irrelevant for 99% of rows.
8. **Retrain on the 1,250 logged vectors.** Online replay MAE 6.71, and the rebuilt table is still wrong.
9. **Learn an offline→served mapping** (isotonic per feature from logs). prep_p50 still 80% mismatched (not a
   function of the fresh value).
10. **Drop prep_p50** (most skewed) and retrain. Violates the feature list; online replay 6.41.
11. **"Fix" precip** (clip/log-transform or drop): breaks an innocent feature.

## 15. Correct repair properties

- Batch view resolution by actual `published_at`, `status`, TTL; per-run written/NULL/unwritten state; replica state at
  `started_at` (corrections with `corrected_at ≤ started_at`).
- Stream views as of `t` with retractions (`corrected_at ≤ t`) and `ingested_at < t` visibility.
- Identity: request resolved by version active (`activated_at`) at `t`; each event resolved by version active at its
  `ingested_at`; splits handled by the same rule.
- `on_miss` from registry history effective at `t`; expired key (no events in window) vs stored NULL (count below
  minimum).
- Labels from final corrected values; population unchanged.
- All parameters read from the extract (runs, versions, registry, history), none hard-coded.
- Innocent feature untouched.

## 16. Repair surfaces

| Surface | Why it must change |
|---|---|
| `features/restaurant.py` | snapshot resolution + replica-at-run-start; recent_delay as-of `t`, `on_miss` 0.0 |
| `features/courier.py` | ingest-time identity, request-time identity, visibility by `ingested_at`, default semantics |
| new or extended loader in `extract.py` | `materialization_runs`, `order_corrections`, identity versions, registry history (the faulty loaders do not read them) |
| `parity.py` (optional but natural) | row-level comparison with NaN/−1 distinction, logger_version exclusion |
| `out/parity/parity_report.md` | deliverable (not behaviourally graded beyond existence) |
| untouched | population, labels, model spec, weather |

## 17. Validation requirements

- **Row-level comparison against logged vectors,** per feature, exact equality with NaN ≠ −1, excluding logger 1.2 by
  `logger_version`. Aggregates cannot replace this: the PIT rebuild moves offline MAE and PSI in plausible directions.
- **Stratified inspection of residual mismatches** by mechanism: rows just after a watermark, restaurants with
  corrections, couriers with merges, zero/low-count couriers.
- **Pre-logging reasoning:** logs cannot validate Jan–Apr. The agent must reason from `materialization_runs` (daily
  cadence) and registry history (on_miss change) and spot-check that daily-cadence rows use the 00:00 run, and that
  Jan–Apr expired keys are NaN.
- **Label audit** on corrected orders.
- **Determinism** (rebuild twice).

## 18. Hidden fixture strategy

All fixtures regenerate the whole extract, including a *different* log sample. Mechanisms and table schemas are
identical to visible; only parameters and dominance change.

| Fixture | Invariant stressed | Surface change | Overfit caught | Why same distribution |
|---|---|---|---|---|
| **hidden_a** "publication" | latest successful published run within TTL | 4 h cadence from Mar, 12 h before; publish lag 10–150 min; 6% failed runs incl. one double failure → TTL 20 h in YAML expires every restaurant for ~4 h (NaN) | `floor(t, 6h)`; hard-coded 45-min lag; hard-coded failed run ids; hard-coded TTL 30 h | cadence, failures, TTL all exist in visible tables/YAML |
| **hidden_b** "identity & corrections" | ingest-time vs request-time identity; correction as-of per consumer | 11% couriers merged, 9 splits, activation lag 0–6 d; stream backlog on another date; 55% tablet_undo; on_miss change on 2026-02-09 for `courier_activity`; logger 1.2 on other dates; logs 1% from 2026-05-02 | request-time map for history; `created_at`; original-everywhere; hard-coded bug dates; hard-coded 2026-04-20 | merges, splits, backlog, undo, registry change, logger bug all present in visible |
| **hidden_c** "defaults & innocent drift" | expired vs NULL; on_miss effective dating; innocence | many new couriers and 12 restaurants with week-long closures; registry changes `restaurant_live.on_miss` 0.0 → −1 mid-window; no weather drift, but basket_items drift (menu redesign); logs start after all registry changes | `fillna` by hard-coded values; zero for empty counts; "transform drifted feature"; using current YAML for history | same registry history mechanism; drift is a monitoring artifact only |

## 19. Mutation strategy

| Mutation | Class | Expected |
|---|---|---|
| `nop` | control | 0 |
| `oracle` | control | 1 |
| `independent_sql` (SQLite window functions + Python identity replay) | alt correct | 1 |
| `event_replay_simulator` (chronological event loop maintaining store state) | alt correct | 1 |
| `leak_fix_only` (hour-exclusive join) | partial | 0 (visible) |
| `pit_event_time` | natural wrong | 0 |
| `snapshot_floor_schedule` | second-order | 0 |
| `snapshot_ignore_failed_runs` | partial | 0 |
| `snapshot_corrected_orders` / `snapshot_corrections_asof_request` | partial | 0 |
| `original_timestamps_everywhere` | wrong | 0 |
| `labels_asof_request` | wrong | 0 |
| `latest_identity_map` / `request_time_map_all_events` / `map_created_at` | partial | 0 |
| `fillna_minus1_all_history` / `nan_all_defaults` / `zero_empty_counts` | partial | 0 |
| `drop_prep_p50` / `drop_most_skewed` | shortcut | 0 (feature-list check) |
| `retrain_on_logged_sample` | shortcut | 0 |
| `offline_to_served_isotonic` | shortcut | 0 |
| `override_with_logs` (on top of PIT) | cheat-ish | 0 |
| `oracle_plus_log_override_no_logger_filter` | overfit-ish | 0 (visible, v1.2 rows) |
| `oracle_hardcoded_bug_dates` | overfit | visible 1 / hidden_b 0 |
| `oracle_hardcoded_onmiss_date` | overfit | visible 1 / hidden_b, hidden_c 0 |
| `oracle_hardcoded_ttl_cadence` | overfit | visible 1 / hidden_a 0 |
| `oracle_transform_precip` | wrong | 0 |
| `oracle_v4_hyperparams` | spec change | 0 (model check) |
| `edited_extract`, `patched_rows_file` | cheat | 0 |

Informational probes: oracle features + faulty labels; oracle with ingest visibility ignored (backlog only; expected
small but nonzero mismatch).

## 20. Alternative valid implementations

- SQL window-function reconstruction vs event-replay simulation vs per-view vectorised pandas `merge_asof` chains.
  All produce identical values because the generator guarantees:
  - no event at exactly a boundary instant (microsecond jitter, strictly ordered publications);
  - medians via a stated `percentile_cont` (materialization SQL in the YAML);
  - no ties in `activated_at`.
- Median via numpy `median` equals `percentile_cont(0.5)`; accepted.
- Output dtypes: float64 or float32 within 1e-5, nullable ints for counts, −1 stored as a number. NaN must be NaN; the
  verifier checks NaN-ness and value separately.
- Extra columns in `rows.parquet` are ignored. Row order is ignored (keyed by `request_id`).

## 21. Verifier design

Harness as in Task 06: regenerate the pristine extract, compare its digest, run the agent's commands as an unprivileged
user, then repeat for each hidden fixture.

**A. Integrity.** Extract unmodified; commands succeed; no network.

**B. Visible.**
1. Row set equals the reference population (`request_id` set).
2. Labels within 1e-6.
3. Per feature, exact match to `truth_served` (abs 1e-5 floats, NaN-ness exact, −1 exact) on **100% of rows**, since
   reference and oracle agree exactly. Failure output reports mismatches by mechanism stratum for review, not for the
   agent.
4. Feature list and column names per model card.
5. `train` on the agent's rows, then `score` on the hidden Sep 1–14 served-vector file (JSONL, same schema as logs).
   Predictions within 1e-6 of the reference model trained on reference rows. Online replay MAE is reported
   (informational).
6. Determinism: rebuild twice, byte-identical parquet content after sort.
7. Parity report exists and is non-empty (not graded further; see risks).

**C. Hidden ×3.** Checks 1–5 on each fixture.

**Ground truth vs reference.** `truth_served` comes from the generator's serving simulator. `tests/reference.py` is an
independent SQL implementation. The build asserts that they agree on all four extracts. The model check uses a fixed
specification, so it is uniquely implied by the model card.

**Runtime.** Visible build ~90 s, hidden (120–150 days, 500 req/day) ~40 s each, 4 × HGBR fits of ~20 s. Total
< 10 min.

## 22. Answer-key leakage audit (with cheap-solve audit)

| Artifact | Could it be transcribed or matched? |
|---|---|
| `feature_store_overview.md` | States generic mechanics (publication, TTL, on_miss, replica read at run start, retractions). It does not tie them to the training builder, does not mention identity-at-ingest, and does not say "compute features as of the run start". Multiple sentences must be composed with tables. Medium-low risk; build review must strike any sentence of the form "to reproduce served values, …". |
| `feature_views.yaml` | Materialization SQL gives the aggregate definition only (no watermark resolution, no correction state). Current `on_miss` alone is wrong for history. |
| `feature_views_history.csv` | Fact table; must be joined by effective time. |
| identity doc | Says stream processors resolve at ingest and aggregates are not rewritten. This is the most direct statement; it still requires versioned joins per event and per request. Accepted as a system fact. |
| corrections doc | Describes sources and timings; does not say which consumers see what. |
| serving logs | Row-level truth for ~0.65% of training rows; include run ids and map_version, which make mechanisms *discoverable*, not transcribable. Logger 1.2 rows are wrong. |
| parity report | Wrong-semantics artifact; matching it gives "PASS" for any rebuild. |
| offline eval v4/v5, notes, notebook | No feature values. |
| `pit.py` | Generic helper with the wrong semantics; no watermark, no identity, no default logic. No TODOs. |
| faulty builders | No run tables loaded, no correction tables loaded, no version joins; no commented-out code. |

**Cheap-solve audit.**

| Cheap path | Result |
|---|---|
| One grep (`on_miss`, `published_at`) | Finds YAML and docs; still requires five mechanism implementations. Fails. |
| One doc | Platform overview covers M1 / M3 partially; not M2 timing per consumer, M4, M6. Fails. |
| One SQL | Snapshot resolution is one SQL, but covers one of five features. Fails. |
| One filter | No filter repairs a value mismatch. Fails. |
| Existing helper | `pit.py` is the natural-wrong path. Fails. |
| Copy logged vectors | Covers 0.65% of graded rows; hidden logs differ; logger 1.2 rows wrong. Fails. |
| Retrain on logs | Row check fails; model check fails. Fails. |
| Learn mapping from logs | Skew not a function of offline value. Fails. |
| Match an old report | Parity report "green" matches the faulty rebuild. Fails. |
| Restore previous behaviour | v4 had no dynamic features; rollback forbidden and the feature-list check fails. Fails. |
| Fit until logs match 100% | **Partial risk:** with correct post-April logic it passes all logged rows, but pre-April rows (daily cadence, NaN on_miss) are unlogged. An agent that hard-codes 6 h or current on_miss passes logs and fails visible rows. This is the intended trap, not a leak. |

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| "Served" vs "knowable" as the training target | Model card: rows reproduce the dispatch service's request; memo: "trustworthy retrain" after online failure; logs show served values. A DS could argue for "fresher offline features and change serving"; the memo forbids changing serving (not in repo). Risk: M. |
| Run with `published_at == t` | Generator never produces equality. |
| Median definition | Materialization SQL `percentile_cont(0.5)`. |
| TTL anchor (published_at vs watermark) | Overview says "since publication"; logs make it visible once in the visible extract (a 30 h gap after a double failure on 2026-07-19 shows NaN). |
| Expired vs NULL for courier features | YAML: `min_events: 5 → null`; overview: expired keys return `on_miss`; logs show both values. |
| Stream visibility `ingested_at < t` vs `≤` | No equality by construction. |
| Backlog window effect small (0.2% of rows) | Accepted as part of the invariant; hidden_b increases it. Could be judged pedantic → keep documented in `warehouse_dictionary` ("ingested_at is when the stream processor consumed the event"). |
| Split versions (un-merge) | Same rule; identity doc describes splits as new versions. |
| Label corrections after extract | None; extract is final. |
| Logger 1.2 scope | CHANGELOG + `logger_version` field. |
| Whether "fix serving" is acceptable | Memo: fix the training pipeline; serving not in repo. |
| Float dtype | Tolerance 1e-5. |

## 24. Expected trajectory length

50–90 tool calls, 25–60 min for a strong agent:
- five mechanisms, each discovered by residual analysis against logs, not by reading one file;
- a validation loop of rebuild → compare → stratify → read doc → rebuild at least 4 times;
- generating 190k rows with per-request state takes non-trivial engineering (per-view merge_asof chains, per-event
  identity resolution).

## 25. Why harder than Tasks 03/05/06

| Task 06 flaw | G11 |
|---|---|
| Target cutoff already in faulty code | The faulty code has no run tables, no correction or identity-version loaders, and no defaults logic; the only time helper (`pit.py`) is wrong. |
| Adjustment summary already implemented | No partial implementation of snapshot resolution or ingest-time identity exists. |
| Natural group/merge/subtract design correct | The natural design (PIT on event time) is wrong on 4 of 5 dynamic features. |
| Attractor optional | Parity and drift reports are cited in the memo; the obvious leak is in the first file opened. |
| Traps on unchosen paths | Every trap (PIT, floor-to-schedule, request-time map, fillna −1, original timestamps) is the next repair a strong agent would choose. |
| One customer's line-level check enough | No single restaurant or courier exhibits all mechanisms; per-feature row-level comparison over hundreds of logged rows plus reasoning for unlogged periods is required. |

## 26. Comparison with Task 02

- **Shared:** per-example × cutoff state reconstruction; "availability ≠ event time".
- **Harder:**
  - *Five* heterogeneous availability mechanisms, where Task 02 had one (load time). Their state times differ per
    consumer: run start, request time, ingest time.
  - An identity dimension with per-side versioning.
  - Default semantics.
  - A validation source that is partial and partly corrupt, and that silently fails to cover the earlier regime.
- **Easier:** logs give row-level feedback that Task 02 lacked. Task 02's agents never checked a row; here the
  natural workflow invites it. Headroom depends on whether agents reason beyond the logged period and past the first
  plausible residual.
- **Overlap risk:** an agent primed by Task 02-style leakage will jump to PIT joins, which is exactly the designed
  wrong path.

## 27. Benchmark risks

- **Implementation cost: H.**
  - The generator must simulate the serving system exactly.
  - The reference must be independent: SQL vs the event-simulating generator.
  - Budget ~3–4 engineer-days, plus review for exact-equality edge cases (microsecond ordering, percentile
    interpolation, float32 in parquet).
- **Realism: H.** Every mechanism is common. The combination in one model is dense but plausible for a first
  dynamic-feature launch.
- **Gradability: H** (exact truth). Residual risk: dtype and NaN handling in parquet; mitigated by tolerant readers.
- **Underspecification: M.**
  - The ingest-backlog detail and the TTL-after-double-failure detail are the two most likely "pedantic" complaints.
  - Option: drop the backlog if review judges it unfair (it changes only ~0.2% of rows).
- **Leakage: L–M.** The identity doc's "resolve at ingest" sentence is the most direct. Build review must trim the
  platform overview to mechanism facts.
- **Headroom risk: M.**
  - Logs make iterative convergence possible for post-April semantics.
  - Difficulty then concentrates on pre-logging regimes (cadence, on_miss history) and on identity and correction
    per-consumer timing.
  - If a pilot shows easy passes, remove `fv_runs` / `map_version` from logs. This makes discovery harder but still
    fair, because the run table and version table remain.
- **Overlap:** Task 02 (point-in-time) moderate. G27 (negative control with serving logs) shares artifacts; do not
  build both with the same logger design.
- **Verifier runtime:** acceptable (< 10 min).
