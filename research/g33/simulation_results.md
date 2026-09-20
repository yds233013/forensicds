# G33 simulation results — statistical gate, cheap-solve gate, leakage audit

All figures measured. No model was run. Five diagnostics; the design fails three kill criteria.

## 1. Statistical gate (visible regime, seed 11)

Truth: top1 = 0.2305, top3 = 0.5283, HHI = 0.1272, 21 nodes → `within_limit`.

| Method | top1 | |err| | nodes | decision |
|---|---|---|---|---|
| **V1 registry graph** | 0.2300 | 0.0005 | 20 | ✓ |
| **V2 two-pass** | 0.2300 | 0.0005 | 20 | ✓ |
| **V3 drop unattributed** | 0.2266 | 0.0039 | 20 | ✓ |
| W1 raw vendor | 0.0584 | **0.1721** | 70 | ✓ (by luck) |
| W3 parent rollup | 0.3310 | **0.1005** | 8 | ✗ |
| W4 raw shipment codes | 0.2266 | **0.0039** | 29 | ✓ |
| W5 renames only | 0.2266 | 0.0039 | 24 | ✓ |
| W6 all events unioned | 0.2266 | 0.0039 | 18 | ✓ |
| W7 transitive closure | 1.0000 | 0.7695 | 1 | ✗ |
| W9 unattributed → vendor primary | 0.2313 | **0.0007** | 20 | ✓ |
| W10 vendor-master attribution | 0.2462 | 0.0157 | 13 | ✓ |
| W11 acquisition as identity | 0.2971 | 0.0665 | 6 | ✗ |

The three valid families agree to 4 decimal places. **So do four of the wrong ones.**

## 2. Diagnostic 1 — the entity work does not reach the metric

Over 12 visible worlds, mean |top1 error| for methods that skip entity resolution entirely:

| Method | mean abs error | truth top1 range |
|---|---|---|
| W9 unattributed → vendor primary | **0.0034** | 0.16 – 0.33 |
| W5 renames only | **0.0149** | |
| W4 / W8 raw shipment codes | **0.0269** | |
| W10 vendor-master attribution | 0.0476 | |

The true top node was touched by a registry event in only 1 of the 6 worlds inspected. Registry merges,
splits and renames hit a handful of the ~21 nodes, almost never the largest, and their effects partly
cancel in a ratio. **Kill criterion K12 fires: entity errors do not materially affect the result.**
**K4 fires: raw identifiers give essentially the correct metric.**

## 3. Diagnostic 2 — the ranking does not need resolution either

Re-framing the question as "*which* node is largest" does not rescue it: the raw-shipment-code argmax
agrees with the fully resolved argmax in **11 of 12 worlds**.

## 4. Diagnostic 3 — which metrics discriminate at all

Mean relative error over 12 worlds:

| Method | top1 | top3 | HHI | node count |
|---|---|---|---|---|
| V1 (valid) | 0.000 | 0.000 | 0.002 | −0.004 |
| **W4 raw shipment codes** | **−0.078** | −0.079 | −0.142 | **+0.355** |
| W1 raw vendor | −0.778 | −0.752 | −0.825 | +2.428 |
| W3 parent rollup | +0.653 | +0.471 | +0.917 | −0.630 |
| **W6 all events unioned** | **+0.079** | +0.058 | +0.087 | −0.143 |
| **W9 unattributed → primary** | **+0.006** | +0.003 | +0.007 | −0.004 |

Only the **coarse grain errors** (vendor, parent) move the business metric. The errors that represent real
identity-reconstruction mistakes — W4, W6, W9 — sit at 0.6–8% relative error, inside the noise a frozen
fixture would carry.

## 5. Diagnostic 4 — constant-decision attack (K9)

Truth decision over 12 worlds in each of the five regimes:

| Regime | breach | within_limit |
|---|---|---|
| visible | 2 | **10** |
| migration_heavy | 2 | **10** |
| ownership_heavy | 2 | **10** |
| fragmented_below_limit | 0 | **12** |
| thin_asn | 2 | **10** |

**Answering `within_limit` unconditionally is correct in 54 of 60 worlds — 90%.** The regime built
specifically to flip the answer (`fragmented_below_limit`) produced the same decision as the visible one.
The truth also straddles the 25% limit as a function of seed, so which side a frozen fixture lands on is an
artefact of seed choice. **K9 fires.**

## 6. Diagnostic 5 — would a per-entity *rate* metric rescue it?

Synthesising a per-line defect flag with node-level propensity, metric = "number of nodes whose defect rate
exceeds 3%" (truth: 4.5 flagged of 16.1 eligible):

| Grouping | flagged-count error | eligible-count error |
|---|---|---|
| V1 resolved | +0.10 | −0.40 |
| **W4 raw shipment codes** | **+0.60** | +1.90 |
| W1 raw vendor | **+12.90** | +39.30 |
| W3 parent rollup | **−2.20** | −8.30 |

A rate metric is far more sensitive — but **only to grain errors**. The identity-reconstruction error (W4)
still moves the flagged count by 0.6 of 4.5, ~13%, while choosing the wrong grain moves it by 3–4×.

## 7. Representation-leakage audit

| Check | Result |
|---|---|
| Node index encodes size (node 0 is boosted) | latent node 0 is the true top in **1/12** worlds — the Dirichlet dominates the boost, so no usable index leak |
| Row order / adjacency | rows permuted at generation; no leak |
| Material group as a node proxy | 1.86–2.19 nodes per material group — partial evidence, not a proxy |
| Amount distribution | identical lognormal across nodes; no size leak |
| **Vendor-count per node** | **top-5 nodes by spend have 28/20/5/8/4 vendor codes, bottom-5 have 1 each** — a real, if realistic, size proxy that would let an analyst rank nodes without resolving spend |
| Code prefix (500/700/800) | groups renamed/split codes into 3 buckets; produces top1 ≈ 0.90, obviously wrong |

Only the vendor-count proxy would need fixing, and it is the least of the design's problems.

## 8. Cheap-solve panel

| Heuristic | top1 error (visible) | decision correct |
|---|---|---|
| `C_constant_within` | n/a | **90% across all regimes** |
| `C_post_rework_only` | 0.0041 | ✓ |
| `C_full_history_window` | 0.0035 | ✓ |
| `C_line_counts_raw_code` (counts, not amounts) | 0.0003 | ✓ |
| `C_raw_site` | 0.0039 | ✓ |
| `C_material_group` | 0.1209 | ✓ |
| `C_code_prefix` | 0.6663 | ✗ |

**Four heuristics that do no entity resolution land within 0.004 of the truth.** Counting lines instead of
summing spend — which discards the amount column entirely — is the single most accurate cheap solve.
