# G25 — Search ranker blocked by the offline gate: judgment-pool bias, broken query join, mixed rating scales

Status: design only. Nothing built, no model run. Candidate definition: `research/gen3_candidate_pool.md` §G25.
All numbers are **generator targets** to be calibrated and asserted at build time.

## Workspace sketch

```
/workspace                                           (~70 MB)
  README.md                          search-quality repo; how the release gate runs
  CHANGELOG.md                       search_gate releases (4.2: gate sample re-canonicalised with current QNORM)
  config/gate.yaml                   gate sample path, rankers, k = 10, threshold −0.005, judgments paths
  data/
    catalog/offers.parquet           410k offers: doc_id, gtin (nullable), seller_type 1P/3P, product_type, title, attrs, listed_at
    gate/gate_queries_2026-07.csv    2,000 gate queries: gate_query_id, sampled_raw_query, frequency_band, sampled_at
    runs/2026-07-02/A_top10.csv      production ranker ltr-2025.11: gate_query_id, rank, doc_id
    runs/2026-07-02/B_top10.csv      candidate ltr-2026.06-sem: same schema
    judging/
      judgments.parquet              ~210k rows: judgment_id, round_id, query_key, doc_id, gtin, label, rater_id, judged_at
      rounds.yaml                    per round: dates, guideline doc, query_key_form (raw | qnorm_v2 | qnorm_v3), pool description
      manifests/R01..R09.csv         judging tasks sent to vendor: task_id, query_key, display_query, doc_id, pooled_from
  qnorm/                             production query normaliser library: v3 (current), legacy/v2.py (kept for replay tools)
    CHANGELOG.md                     v3.0 (2026-05-12): unit normalisation, plural folding, stopwords; QN-88 fraction fix
  docs/
    raters/RG-3_guidelines.md        3-point guidelines (rounds R01–R06)
    raters/RG-5_guidelines.md        5-point guidelines (rounds R07–R09)
    raters/vendor_sow.md             judging process: tasks, re-judging, delivery format
    search_quality/release_gate.md   gate metric (NDCG@10, gain 2^g − 1 on the gate grade scale, IDCG definition), threshold
    search_quality/pool_audit_2026-07.md  why R09 was commissioned; sampling frame and size
    catalog/marketplace_launch.md    3P marketplace (2026-02): offers for existing GTINs and new products
  search_gate/                       faulty harness: qrels.py, metrics.py, run.py, report.py
  reports/gate/                      2026-03 (A vs A−1), 2026-07-03 (B blocked: Δ −0.031); coverage tables
  reports/ab/AB-771_readout.md       B vs A online: purchases/session +2.3%, avg purchased price −8.7%, weekly effects
  notes/2026-07-10_gate_block_thread.md  Search PM vs Relevance lead; "raters don't understand 3P listings"
```

## 1. Research question

Can an agent estimate what a ranking metric *would be under complete human judgments* when the judgment pool is
biased toward the production ranker, judgments are keyed by three generations of query strings, and two rating scales
with different category semantics are mixed — and reach the correct release decision without over-trusting either the
blocked gate or a favourable A/B?

Capability: **measurement repair under incomplete, heterogeneous labels** — reconstructing label identity (query and
product grain), harmonising scales from guideline semantics, and estimating the contribution of genuinely unlabelled
results from a probability sample whose frame was defined by the broken harness.

## 2. Enterprise setting

A home-improvement marketplace's search team gates ranker releases on offline NDCG@10 over a monthly sample of 2,000
queries, using human relevance judgments bought from a rater vendor in rounds. Pools come from the production ranker
of the day. A 3P marketplace launched in February 2026, adding third-party offers for existing products (same GTIN,
new `doc_id`) and genuinely new products. Query normalisation (QNORM) v3 launched in May. Candidate ranker B adds
semantic retrieval and indexes 3P offers aggressively.

## 3. Visible symptom (instruction memo)

From the VP Search:

> The gate blocked ltr-2026.06-sem (B): NDCG@10 is 3 points below production. The online test (AB-771) says B sells
> more. Relevance says the gate is the gate; the PM says the gate is stale. I can't ship on a gate I don't trust or
> override it on an A/B I don't understand. Tell me whether B is actually worse on relevance, fix the gate, and give
> me the decision.

Required outputs:

1. `cd /workspace && python -m search_gate.run --month 2026-07` writes:
   - `out/gate/qrels_resolved.csv` — every (gate query, doc_id) pair in either top-10 list whose gate-scale grade is
     determined by our human judgments, with columns `gate_query_id, doc_id, grade` (0/1/2). Pairs our judgments do
     not determine are left out.
   - `out/gate/summary.json` — `ndcg10_A`, `ndcg10_B`, `delta`, `decision` (`pass` / `block`), `n_queries`.
     The NDCG values are the gate metric **as it would be if every product in both lists had been judged by our raters
     under the gate's grade scale**, averaged over the gate sample.
2. Judgments, manifests, catalog, runs and guidelines are authoritative; do not modify. No hand-edited outputs.
3. No special cases for particular queries, rounds or products; the same command runs on future months.

The memo names neither pooling, canonicalisation nor scales.

## 4. Source distribution inspiration

- Pooling bias and the treatment of unjudged documents; condensed lists; inferred/statistical metrics from sampled
  judgments (Buckley & Voorhees 2004, bpref; Sakai 2007 condensed lists; Yilmaz & Aslam 2006 infAP; Yilmaz, Kanoulas &
  Aslam 2008 infNDCG / statAP — to verify).
- Graded relevance scale revisions in commercial rater programmes and the need for crosswalks (practitioner
  experience; no citation).
- Query canonicalisation changes breaking joins to historical labels is a common data-engineering incident.
- A/B metrics driven by price/assortment rather than relevance (practitioner experience).

## 5. Causal graph / ground truth

```
raw query ─► QNORM(version at time) ─► query_key stored per round
                                         │
canonical intent c = qnorm_v3(display_query) ─┬─► true category T(c, product) ∈ {Exact, Close, Substitute, Related, Irrelevant}
                                              │          │
product = gtin (or doc_id if gtin null) ◄─ offer doc_id  └─► rater label = scale_map_round(noisy(T))
                                              │
rankers A, B ─► top-10 offers per gate query ─► true NDCG@10 using gate grade g(T)
```

**True categories.** Generated per (canonical query, product) from query intent attributes vs product attributes:
Exact (all stated attributes), Close (differs on minor attribute: colour, finish, pack quantity), Substitute (same
product type, differs on a major attribute: size, capacity, brand, power source), Related (accessory or complement
used with the queried item), Irrelevant (anything else, including same-category products with a different function).

**Gate grade** (truth; implied by RG-3 semantics): Exact → 2; Close, Substitute, Related → 1; Irrelevant → 0.
RG-3 "Relevant" requires every attribute the customer typed ("if the customer typed *white*, an almond one is
Partial"); RG-3 "Partial" covers "a variant, a substitute, or a product used with the item the customer asked for";
RG-3 "Not relevant" is anything else. This partition {4} | {3, 2, 1} | {0} was chosen so that **no simple arithmetic
map** (x/2 with banker's or half-up rounding, floor, ceil, clip at 2) reproduces it; each misclassifies at least one
RG-5 level that is common in B's lists (Close or Related).

**Rater model.** A judgment draws a category with 6% noise to an adjacent category (Exact↔Close more often), then
writes the round's scale: RG-3 labels 0/1/2 (Not relevant / Partial / Relevant); RG-5 labels 0–4 (Irrelevant /
Related / Substitute / Close / Exact).

**Rounds** (in `rounds.yaml`):

| Round | Dates | Scale | query_key_form | Pool |
|---|---|---|---|---|
| R01–R03 | 2025-01..06 | RG-3 | raw | top-10 of production rankers then |
| R04–R06 | 2025-09..2026-02 | RG-3 | qnorm_v2 | top-10 of production |
| R07 | 2026-04 | RG-5 | qnorm_v2 | top-10 of A |
| R08 | 2026-06 | RG-5 | qnorm_v3 | top-10 of A + top-5 of an early B build |
| R09 | 2026-07-08 | RG-5 | qnorm_v3 | pool audit: 1,500 pairs sampled uniformly from B top-10 pairs **unlabelled in the gate harness v4.2 as of 2026-07-03** |

`manifests/R*.csv` record `display_query` (the customer query shown to raters) for every task.

**QNORM.** v2: lowercase, strip punctuation including `/` (bug QN-88 turns `1/2 in` into `12 in`), collapse spaces.
v3: lowercase, fraction and unit normalisation (`1/2 in`, `1/2"`, `half inch` → `0.5 inch`), plural folding, stopword
removal. v3∘v2 ≠ v3 for fraction queries: `qnorm_v3("12 in pipe") = "12 inch pipe"` but
`qnorm_v3("1/2 in pipe") = "0.5 inch pipe"`. Visible: 34% of gate queries have v3 ≠ v2 form; 4.1% are fraction queries;
23 gate queries have a v2-collision twin (a different real query with the same v2 key).

**Catalog.** 3P offers share GTIN with a 1P offer for 58% of 3P offers; 4% of offers have null GTIN.

**Rankings.** B places 3P offers of judged GTINs in 31% of its top-10 slots, genuinely new products in 15%, and
accessories (Related) more often than A for tool queries. A's lists contain 4% unlabelled new products.

**True mean NDCG@10** (complete true grades; IDCG over all products labelled for the query in the complete pool =
historical judged products ∪ both top-10 lists):

| Variant (visible) | A | B | Δ | Decision |
|---|---:|---:|---:|---|
| **Truth** | 0.612 | 0.630 | +0.018 | pass |
| Harness as is | 0.574 | 0.543 | −0.031 | block |
| Join fixed (display_query→v3), raw labels, unlabelled = 0 | 0.590 | 0.556 | −0.034 | block |
| + scale harmonised | 0.602 | 0.571 | −0.031 | block |
| + product-level (GTIN) labels, rest = 0 | 0.610 | 0.596 | −0.014 | block |
| + R09 audit labels used directly, rest = 0 | 0.610 | 0.603 | −0.007 | block |
| + condensed lists for the rest | 0.614 | 0.668 | +0.054 | pass (B +0.038) |
| Linear scale map (gain 2^(label/2) − 1), all else correct | 0.621 | 0.655 | +0.034 | pass (B +0.025) |
| Correct, rest imputed from R09 (rank-bucket expected gain) | 0.611 | 0.628 | +0.017 | pass |

Genuinely unlabelled (after correct resolution) B slots: 15%, true mean gain 0.62 vs 1.41 for labelled B slots — new
3P products are on average less relevant, which is why condensing fails.

**A/B (AB-771).** Purchases/session +2.3% [+1.1, +3.5]; revenue/session −0.4%; average purchased price −8.7%; weekly
effects +3.1, +2.2, +1.6%. Generator: purchase probability depends on relevance and a price-elasticity term; B's
cheaper 3P offers drive about two thirds of the purchase lift.

## 6. Latent statistical/business invariant

1. **Query identity** of a judgment = `qnorm_v3(display_query)` from the round manifest — not `query_key`, and not
   `qnorm_v3(query_key)` (wrong for QN-88 fraction keys; can mis-assign to a collision twin).
2. **Label identity** is (canonical query, product), product = GTIN when present, else doc_id — RG-3/RG-5 say raters
   judge the product and must ignore seller, price and shipping.
3. **Scale crosswalk** from category semantics: RG-5 {4} → 2, {3, 2, 1} → 1, {0} → 0. Not linear: RG-5 "Close"
   (minor attribute differs) is RG-3 Partial because RG-3 Relevant requires every typed attribute, and RG-5 "Related"
   (product used with the queried item) is RG-3 Partial by RG-3's own wording.
4. **Supersession:** for the same (canonical query, product), the latest `judged_at` harmonised label governs
   (vendor SOW: re-judgments supersede).
5. **Estimand:** complete-judgment NDCG. Unlabelled results are neither irrelevant nor removable; their expected
   contribution is estimated from R09, a uniform sample of a frame that contains every genuinely unlabelled B pair
   (harness-unlabelled ⊇ truly unlabelled), so R09 ∩ unlabelled is a uniform sample of the unlabelled set. A's small
   unlabelled share uses the same estimate (documented residual).
6. **Decision:** pass iff NDCG_B ≥ NDCG_A − 0.005.

## 7. Grains and state variables

| Grain | Key | Mistake |
|---|---|---|
| Stored judgment key | `query_key` (form varies by round) | string-joined to v3 gate queries |
| Rater-facing query | `display_query` in manifest | ignored |
| Canonical query | `qnorm_v3(display_query)` | computed from `query_key` |
| Offer | `doc_id` | labels keyed by offer |
| Product | `gtin` (fallback doc_id) | 3P offers of judged products treated as unjudged |
| Round / scale | `round_id` → guideline | labels treated as one scale |
| Label version | `judged_at` | max label, mean label, or first label |
| Ranked list slot | (gate_query_id, rank) | condensed: slots removed and ranks shifted |
| Sampling frame | R09 frame (harness v4.2 unlabelled B pairs) | audit treated as representative of all B slots |

## 8. Evidence graph

(★ natural path)

| Artifact | Shows |
|---|---|
| ★ memo, `reports/gate/2026-07-03` | Δ −0.031; coverage@10 A 0.71, B 0.44 (March report: A 0.93) |
| ★ `search_gate/qrels.py` | dict keyed by `(query_key, doc_id)`; gate query canonicalised with `qnorm.v3`; missing → grade 0 |
| ★ `search_gate/metrics.py` | gain 2^label − 1 on raw label; IDCG from all labels for the query |
| ★ CHANGELOG 4.2 | "gate sample canonicalised with the current QNORM version" |
| ★ `judgments.parquet` | label range 0–4 in some rounds; `query_key` forms visibly differ (`1/2`-less keys, plurals) |
| `rounds.yaml` + manifests | key form per round; `display_query`; pool sources |
| `qnorm/CHANGELOG.md` | v3 rules; QN-88 fraction bug in v2 |
| RG-3 / RG-5 | category definitions with examples; "judge the product, not the offer" |
| `vendor_sow.md` | re-judged pairs supersede; delivery keys |
| `pool_audit_2026-07.md` | R09 frame = pairs unlabelled in harness 4.2 as of 2026-07-03, uniform, 1,500 pairs; motivated by PM complaint |
| `marketplace_launch.md` | 3P offers attach to existing GTINs; new 3P products |
| ★ `AB-771_readout.md`, notes thread | purchase lift, price shift, decaying weekly effect |
| data: R06/R07 overlap (1,140 pairs judged under both scales) | empirical crosswalk: RG-5 4→RG-3 2 in 93%, RG-5 3→RG-3 1 in 89%, RG-5 1→RG-3 1 in 90% |

## 9. Evidence authority hierarchy

1. **Rater guidelines and vendor SOW** — define what a label means and which label is current. Govern label semantics.
2. **Round manifests and `rounds.yaml`** — what raters were shown and how keys were written. Govern query identity
   over `query_key`.
3. **QNORM library and changelog** — the canonical form used by search today (v3); v2 behaviour for legacy keys.
4. **Release gate doc** — metric, grade scale (gate scale = RG-3), IDCG, threshold. Governs the decision.
5. **Pool audit doc** — sampling frame and design of R09.
6. **Harness code, gate reports** — under review.
7. **A/B readout, PM/Relevance thread, model notes** — context; not a relevance measurement.

Conflicts:
- Harness joins on `query_key`; manifests show raters saw `display_query`. Manifests govern.
- Numeric intuition says RG-5 3 ("Close", second-best) should be RG-3 2 and RG-5 1 ("Related", second-worst) should
  be RG-3 0. The gate doc says grades are on the RG-3 scale, and RG-3's definitions put both in Partial. Semantics
  govern; the R06/R07 overlap confirms empirically.
- A/B purchases up vs relevance: the gate doc defines release relevance by NDCG; purchases are a business metric
  confounded by price. The A/B does not override the gate; it motivates checking it.
- PM thread: "raters mark 3P listings irrelevant". False: 3P offers are mostly unjudged, not judged irrelevant (checkable).

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 ★ | B is genuinely less relevant; A/B lift is price-driven | gate Δ −0.031; purchased price −8.7%; B shows more accessories (true) | Δ is driven by unlabelled slots and lost joins; complete-judgment estimate +0.018 |
| H2 ★ | A/B lift is novelty; B regresses long-term | weekly effect 3.1 → 1.6% | irrelevant to the relevance gate; decaying effect is compatible with price/novelty but says nothing about NDCG |
| H3 | Gate is biased by unjudged 3P/new docs | coverage 0.44 vs 0.71 | — (true, partial) |
| H4 ★ | Gate broke at QNORM v3 (join), B is fine once joins are restored | A coverage dropped 0.93 → 0.71 after v3; CHANGELOG 4.2 | fixing the join alone leaves Δ −0.034 (worse) because raw RG-5 gains favour A (R07 pooled A) |
| H5 ★ | Condensed lists are the standard fix for unjudged docs | IR literature; gives a pass | estimand is complete-judgment NDCG; R09 shows unlabelled products are less relevant; condensing overstates B by 0.038 |

## 11. Why each wrong hypothesis is plausible

- **H1** has two real supports: the price shift is real and B really shows more accessories. An agent that "confirms"
  the gate by spot-checking accessory results finds true examples.
- **H4** is a genuine bug with a dated trigger; an agent that fixes it sees coverage recover and may stop — but the
  number gets worse, which *reinforces* H1.
- **H5** is the textbook repair, and in many benchmarks condensed lists are acceptable; here the instruction's estimand
  and the audit sample rule it out on evidence.
- **Scale naïveté** (keep raw labels or map linearly) is plausible because both scales are "graded relevance" and
  `metrics.py` already uses exponential gain.

## 12. Investigation path (≈40–70 actions)

1. (1–6) Memo, gate report, A/B, thread. Discovery: coverage collapse; B's coverage 0.44.
2. (7–12) Run harness; read `qrels.py`, `metrics.py`, CHANGELOG. Discovery: v3 canonical join.
3. (13–20) Inspect `judgments.parquet`: label distributions by round (0–4 appear from R07), `query_key` forms. Read
   `rounds.yaml`. Discovery: three key forms, two scales.
4. (21–28) QNORM changelog, `legacy/v2.py`; test `qnorm_v3(query_key)` on sample keys; find fraction mismatches and
   collision twins; open manifests → `display_query`. **Decision point:** v3(query_key) (wrong) vs v3(display_query).
5. (29–34) RG-3 vs RG-5; derive crosswalk; validate on R06/R07 overlap.
6. (35–40) Unlabelled B slots: join catalog; notice 3P offers share GTIN with judged 1P offers; guidelines "judge the
   product". Discovery: product-level labels.
7. (41–48) Remaining unlabelled: read pool audit doc; understand frame; restrict R09 to still-unlabelled pairs; compare
   their grades to labelled slots at the same ranks. Discovery: condensing is biased.
8. (49–58) Implement: resolved qrels (exact table), expected gain for unlabelled slots (by rank bucket or global),
   IDCG handling, NDCG per query, means, decision.
9. (59–66) Validate: per-query spot checks of resolved labels against raw judgments and manifests; sensitivity of Δ to
   imputation choice (bucketed vs global vs bootstrap of R09); rerun determinism.

## 13. Natural wrong implementation

**NW1 — "fix the join, drop unjudged" (condensed lists after re-canonicalising keys):**

```python
j = judgments.assign(qkey=judgments.query_key.map(qnorm.v3))          # re-canonicalise stored key
j["grade"] = np.where(j.round_id.isin(RG5_ROUNDS), (j.label / 2).round(), j.label)   # or label.clip(upper=2)
qrels = j.sort_values("judged_at").groupby(["qkey", "doc_id"]).grade.last()
for ranker in (A, B):
    lst = ranker.merge(gate, on="gate_query_id")
    lst = lst[lst.set_index(["canonical", "doc_id"]).index.isin(qrels.index)]   # condensed
    lst["rank"] = lst.groupby("gate_query_id").cumcount() + 1
```

Numeric consequences on visible:
- `qnorm.v3(query_key)` mis-keys 4.1% fraction queries: 78 gate queries lose judgments; 23 collision twins receive
  their twin's labels (e.g. `1/2 in pipe` labels applied to `12 in pipe`). Exact table wrong (~1,900 pairs).
- `(label/2).round()` (numpy/pandas round-half-to-even) maps RG-5 {0, 1} → 0, {2} → 1, {3, 4} → 2: Close becomes
  Relevant (+) and Related becomes Not relevant (−). B has many Related accessories and A's R07/R08 pool has many
  Close variants, so the net effect is A +0.011, B −0.004 on visible. `clip(upper=2)` maps 3 → 2, 2 → 2, 1 → 1:
  B +0.022. Fractional grades (label/2 in the exponent) inflate both, B more (+0.025).
- doc_id-level labels leave 31% of B slots (3P offers of judged products) unlabelled; condensing removes them and
  promotes lower-ranked labelled items.
- Result: A 0.618, B 0.671 → pass (right decision, B value +0.041 off). Hidden_a (B truly worse) passes wrongly.

**NW2 — "unjudged = 0 is conservative; fix join and scales"**: A 0.602, B 0.571 → block. The "principled
conservative" choice, wrong estimand.

## 14. Second-order failure modes

1. Product-level labels added but remaining unlabelled = 0 → Δ −0.014 block.
2. R09 labels merged as ordinary judgments, rest = 0 → Δ −0.007 block (the audit is used as labels but not as a sample).
3. R09 used to estimate expected gain for **all** harness-unlabelled slots (the full frame), then applied only after
   GTIN resolution → double use: frame mean gain (1.02) > truly-unlabelled mean gain (0.62) → B +0.020 → fails τ.
4. Imputation with the mean gain of labelled slots → equivalent to condensing in expectation → B +0.03.
5. Imputed docs excluded from IDCG while included in DCG → NDCG > 1 for some queries; mean B +0.015.
6. Supersession by max label or majority → exact table wrong on 3.2% of re-judged pairs; small metric effect.
7. Dropping queries with any unlabelled result → population change (1,120 queries left): A 0.655, B 0.690.
8. Using `gtin` inheritance across queries (product labelled for any query) → table wrong, B +0.06.

## 15. Correct repair properties

- Judgment query identity from manifests (`display_query`) through the current canonicaliser.
- Product-level label resolution; doc_id fallback for null GTIN.
- Crosswalk derived from guideline semantics, applied per round's scale; latest judgment supersedes.
- Resolved table contains only pairs determined by human judgments (including R09).
- Unlabelled slots contribute an estimated expected gain derived from the R09 ∩ unlabelled subsample (any reasonable
  stratification), consistently in DCG and IDCG; queries all retained.
- Decision from the gate threshold.

## 16. Repair surfaces

| Surface | Why |
|---|---|
| `search_gate/qrels.py` | key identity (manifest → v3), product grain, scale crosswalk, supersession |
| `search_gate/metrics.py` | unlabelled handling (expected gain), IDCG consistency |
| new/extended sampling module | use R09 as a probability sample restricted to the resolved-unlabelled set |
| `search_gate/run.py`, `report.py` | outputs and decision |

## 17. Validation requirements

- **Row-level label audit:** for sampled gate queries, trace each resolved label to judgment rows, manifest
  `display_query`, round scale and GTIN. Check collision twins explicitly. Aggregate coverage cannot show mis-assigned
  labels (coverage rises under NW1's mis-join too).
- **Crosswalk validation** on R06/R07 overlap pairs.
- **Frame check:** R09 pairs are all harness-unlabelled; after resolution, how many R09 pairs remain unlabelled; compare
  their grade distribution with labelled B slots at the same ranks.
- **Sensitivity:** Δ under bucketed/global/bootstrap imputation stays above −0.005 (it does: +0.014 to +0.020).
- **IDCG sanity:** NDCG ≤ 1 per query.

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface change | Overfit caught | Why same distribution |
|---|---|---|---|---|
| `hidden_a` "B_worse" (month 2025-11) | estimand (not condensed); decision can be block | truth Δ −0.022 (B's new products poor); unlabelled B slots 22%, mean gain 0.41; R09-style audit 900 pairs; rounds R01–R07 only with RG-5 introduced at R06 | condensed lists (pass, wrong); hard-coded "pass"; round-id-keyed scale map (`R07+ is 5-point`) | same guidelines, SOW, QNORM versions; scale assignment read from `rounds.yaml` |
| `hidden_b` "scale_dominant" (2026-10) | crosswalk and key identity | RG-5 rounds pooled mostly from the B prototype, so raw labels favour **B**; 9% fraction queries, 61 collision twins; manifests keyed by v2 for three RG-5 rounds; truth Δ +0.024 | raw/linear scales (pass, but values off); `qnorm_v3(query_key)`; hard-coded key form per round id | same QNORM bug, same manifests schema |
| `hidden_c` "tail_heavy" (2027-01) | product grain and sample-based estimate | 50% tail queries; GTIN null for 12% of offers; unlabelled B slots 25%, audit 2,500 pairs; truth Δ +0.012 → pass; "GTIN labels, rest = 0" gives Δ −0.019 block | expected gain hard-coded from visible R09 (0.62 → truth here 0.88); GTIN-only identity (no doc_id fallback) | null GTINs exist in visible (4%) |

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` (manifest→v3, GTIN/doc fallback, crosswalk, latest supersedes, R09∩unlabelled rank-bucket expected gain) | 1 |
| `alt_global_mean_impute` (single expected gain) | 1 |
| `alt_bootstrap_impute` (per-query expected DCG via 200 seeded R09 bootstrap draws, mean) | 1 |
| `alt_sql` (DuckDB implementation of resolution; Python metric) | 1 |
| `join_fix_only` | 0 |
| `unjudged_zero` (all resolution correct, rest = 0) | 0 (values; hidden_c decision) |
| `condensed_lists` | 0 (values; hidden_a decision) |
| `recanon_query_key` (qnorm_v3(query_key)) | 0 (table; hidden_b values) |
| `linear_scale`, `round_half_even_scale`, `clip_scale` | 0 (values / table) |
| `doc_id_labels_only` | 0 |
| `audit_as_labels_only` | 0 |
| `frame_mean_impute` (R09 full frame mean) | 0 (values) |
| `max_label_supersession` | 0 (table) |
| `drop_incomplete_queries` | 0 (values, n_queries) |
| `idcg_excludes_imputed` | 0 (values) |
| `gtin_across_queries` | 0 (table) |
| overfit `hardcode_expected_gain_0.62` | 0 (hidden_a, hidden_c) |
| overfit `hardcode_round_scales` (R07+ = RG-5) | 0 (hidden_a) |
| overfit `hardcode_decision_pass` | 0 (hidden_a) |
| cheat: read `/tests` | 0 |

## 20. Alternative valid implementations

Accepted: any stratification of expected gain for unlabelled slots (none, rank bucket, frequency band, product type,
seller type) provided it is estimated from R09 pairs that remain unlabelled after resolution; computing expected DCG
and expected IDCG then taking the ratio, or averaging NDCG over imputation draws; treating the IDCG via expected
gains or via a plug-in rounding — within tolerance. Resolution may be SQL or Python; the table is graded as a set.
Using the R09 labels (as judgments) for pairs that are in R09 is required by the table definition; using them also in
the estimate is natural.

## 21. Verifier design

- **A.** Inputs unchanged; command succeeds; schemas.
- **B.** `qrels_resolved.csv` exact: set of (gate_query_id, doc_id) and grades vs the generator's deterministic
  resolution rule (§6.1–6.4). Missing and extra rows reported separately.
- **C.** `summary.json`: `n_queries` = 2,000; |ndcg10_A − truth| ≤ τ_A; |ndcg10_B − truth| ≤ τ_B; |delta − truth| ≤ τ_Δ.
- **D.** Decision exact. **E.** Determinism. **F.** B–D on hidden fixtures.

### Tolerance analysis

Sources of error for a valid estimator relative to complete-judgment truth:
1. **Rater noise on labelled pairs** — truth uses latent categories, labels are noisy. Identical for all valid methods;
   its effect on the mean is computed exactly by the generator (visible: A −0.002, B −0.001) and **folded into
   truth used by the verifier** — i.e. the verifier's truth is complete-judgment NDCG with the *actual* resolved labels
   for labelled pairs and latent grades for unlabelled pairs. No tolerance is spent on it.
2. **Sampling error of the expected gain** for unlabelled slots. Visible: unlabelled B slots u = 15% (3,000 slots);
   R09 ∩ unlabelled ≈ 500 pairs; gain sd ≈ 0.85 → SE(mean gain) ≈ 0.038. The sensitivity of mean NDCG_B to the
   unlabelled-slot mean gain ḡ_U is ∂NDCG_B/∂ḡ_U ≈ 0.061 per unit of gain (generator computes it exactly by finite
   difference; it reflects the 15% slot share, their rank discounts and per-query IDCG). SE(NDCG_B) ≈ 0.061 × 0.038 ≈ 0.0023. A: u = 4%, SE ≈ 0.0006.
   SE(Δ) ≈ 0.0022 (positively correlated through the shared ḡ_U).
3. **Stratification / nonlinearity bias** — expected gain in the ratio (Jensen), stratum choice. Panel measurement on
   visible: largest deviation among accepted variants 0.0031 (B).
4. **A's unlabelled slots imputed from a B-frame sample** — generator draws A's unlabelled products from the same
   new-product distribution; bias ≤ 0.002 by construction (documented residual risk).

Tolerances per fixture: τ = max(0.008, 3.5 × SE₂ + max panel bias₃ + bound₄). Visible: τ_B ≈ 3.5 × 0.0023 + 0.0031 +
0.002 ≈ 0.013; τ_A ≈ 0.008; τ_Δ ≈ 0.013. Seed screening: accept only seeds where every accepted variant lies within
0.7τ of truth. Wrong variants' errors (visible): unlabelled = 0 → B −0.034 (2.6τ); condensed → B +0.038; frame-mean
imputation → B +0.020 (1.5τ); round-half-even crosswalk → A +0.011 and B −0.004 → Δ −0.015 (1.2τ; also caught by
table); linear → B +0.025. Decision margin: truth Δ +0.018 vs threshold −0.005 = 0.023 ≈ 10 SE(Δ). Fixture design
rule: |truth Δ + 0.005| ≥ 0.012 and ≥ 4 SE(Δ) (hidden_c: 0.017).

## 22. Answer-key leakage audit (including cheap-solve audit)

| Artifact | Leak? | Why not an answer key |
|---|---|---|
| RG-3 / RG-5 | define categories | no crosswalk table; the partition is inferred from wording and checked on overlap data |
| vendor SOW | supersession | a process fact; does not mention query keys or products |
| manifests | `display_query` | a field; must be recognised as the rater-facing identity |
| QNORM changelog | QN-88 | documents a bug fix for search traffic, says nothing about judgments |
| pool audit doc | R09 frame and design | necessary to use R09 correctly; it says "to size the unjudged problem", not how to estimate NDCG |
| release gate doc | metric, IDCG, threshold | definition; its "unjudged = not relevant" line was removed in favour of the instruction's estimand to avoid a conflict (see §23) |
| marketplace launch | GTIN sharing | fact about catalog |
| A/B, thread | none | attractors |

**Cheap-solve audit.**
- *One grep:* `grep -ri unjudged` hits the harness and the pool-audit doc (motivation). `grep -r gtin` hits the catalog
  doc and schema. No single grep yields the estimator.
- *One doc:* the pool audit doc is the most dangerous: if it says "use R09 to estimate the relevance of unjudged
  results", the sampling step becomes transcription. It must describe purpose ("quantify how many unjudged B results
  are relevant, for the gate-methodology discussion") and design only. Even so, the frame subtlety (frame ⊋ truly
  unlabelled) remains.
- *One SQL:* `SELECT ... JOIN manifests USING (query_key, doc_id)` fixes identity but not scale, product grain or
  unlabelled slots.
- *Filter:* "drop RG-5 rounds" → loses R07–R09 (A's recent labels and the audit) → B ≈ 0.55, block.
- *Helper:* `qnorm/legacy/v2.py` exists (legitimate library code). It lets an agent confirm QN-88; it does not recover
  raw queries (v2 is lossy) — the manifest is still needed.
- *Old report:* March gate report is A vs A−1 under the old harness with v2 canonicalisation; restoring v2
  canonicalisation for the gate sample would rejoin R04–R07 (raw → v2 matches) but lose R08/R09 (v3 keys) and still
  mix scales and ignore 3P → Δ −0.028 block.
- *Restoring behaviour:* reverting harness 4.2 → 4.1 gives exactly the previous bullet.
- *Trusting the A/B:* passes on hidden fixtures where truth passes, fails hidden_a, and values fail everywhere.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Condensed lists vs inferred metrics vs unjudged = 0 | instruction fixes the estimand ("as if every product had been judged"); condensed and zero are different estimands. R09 exists and is a probability sample, so estimation is possible without invention |
| Gate doc historically said "unjudged results count as not relevant" | the design removes that line from `release_gate.md` (keep the metric and IDCG definition only); CHANGELOG 3.0 mentions unjudged = 0 as a harness implementation choice, which is lower authority than the instruction |
| Which query string identifies a judgment | manifests + SOW ("raters are shown the customer query as sampled"); `query_key` described as "storage key, normalised per round configuration" |
| Is a 3P offer of a judged product judged? | RG-3/RG-5: "judge the product; seller, price, delivery and condition do not affect the label"; catalog: GTIN identifies the product. Null GTIN → offer-level only (no inference by title similarity; generator makes title-twins with null GTIN differ in relevance 30% of the time, so inference would be wrong and is excluded from the table) |
| Label conflicts across rounds/variants | SOW: the latest delivered judgment for a query–product pair supersedes. Generator guarantees distinct `judged_at` |
| Crosswalk for RG-5 "Related" | RG-3 Partial wording includes "used with"; overlap data confirms |
| IDCG under complete judgments | gate doc: ideal ordering of all labelled products for the query; with complete judgments this is historical labelled products ∪ both lists; expected-gain IDCG accepted within tolerance |
| Imputation stratification | not specified; tolerance covers the panel; generator keeps unlabelled gain roughly homogeneous across ranks (rank effect ≤ 0.1 gain) so stratification choice matters little |
| A's unlabelled slots (not in R09 frame) | residual; small share; bounded bias built into tolerance. Alternative: agent reports A with unlabelled = 0 → error −0.006 (< τ_A 0.008). Honest risk: tolerance absorbs a principled disagreement |
| Queries whose canonical form merges two gate queries | generator ensures gate sample is unique on v3 canonical form |
| NDCG for a query with zero ideal gain | generator guarantees ≥ 1 labelled product with grade ≥ 1 per gate query |
| Whether R09 labels belong in `qrels_resolved.csv` | they are human judgments → included; instruction wording "determined by our human judgments" |

## 24. Expected trajectory length

40–70 actions, 60–100 expert minutes. The bug trail (coverage drop → join) is short; the long part is three
successive re-estimations, each giving a plausible but still-blocking or overshooting Δ, plus manifest/QNORM
forensics and a sampling-frame argument.

## 25. Why harder than Tasks 03/05/06

- No scaffolding: the harness has no scale handling, product grain or sampling logic; `qnorm.v3` applied to
  `query_key` is the tempting reuse and is wrong.
- The natural repair sequence (fix join → map scale → drop or zero unjudged) is wrong at each step for a different
  principled reason, and two of the partial repairs make B look *worse*, reinforcing the wrong hypothesis.
- The attractor (A/B lift, price shift) is in the memo; the coverage evidence that points to the bug is in the gate
  report the agent must open.
- Row-level label tracing is required: coverage and NDCG move in believable directions under mis-joins.
- Unlike Task 06, the "group/merge" design produces the wrong estimand; the correct answer needs a probability
  sample argument.

## 26. Comparison with Task 02

Task 02 required reconstructing state at example × cutoff; G25 requires reconstructing label identity at canonical
query × product × latest judgment and a statistical estimate at slot grain. Both have many partial repairs that move
the headline metric toward plausibility. G25 is likely comparable to Task 02 in difficulty: the identity and scale
rules are more discoverable than Task 02's availability semantics, but the estimand step adds a statistical layer
Task 02 lacked.

## 27. Benchmark risks

- **Headroom:** a knowledgeable agent may jump to "inferred NDCG with the audit sample". Remaining difficulty: frame
  restriction, crosswalk partition, manifest identity, exact table. If passes are fast, hidden_b's collision twins and
  hidden_c's null-GTIN share carry the weight.
- **Underspecification:** highest around A's unlabelled slots and the historical "unjudged = 0" convention. The
  estimand sentence in the instruction is load-bearing; harbor's behaviour-in-description check is satisfied by it.
- **Realism:** perfectly consistent QNORM behaviour and a clean audit frame are tidier than reality; rater noise is
  modest. The partition {4}|{3,2,1}|{0} was chosen for non-arithmetic reasons and must read naturally in RG-3 prose —
  a writing risk.
- **Implementation cost: medium.** Query-attribute generator for categories, QNORM v2/v3 implementations, rounds with
  pools, audit sampling from the harness frame, analytic derivative for tolerance.
- **Gradability:** exact table is fully deterministic; metric tolerances are principled but depend on the panel.
- **Overlap:** low with Tasks 01–06; conceptual overlap with G24 (incomplete feedback) — different mechanism (labels
  vs clicks).
