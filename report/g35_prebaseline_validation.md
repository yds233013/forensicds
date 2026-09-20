# G35 — `dispatch-priority-gate` pre-baseline validation

**Task:** `candidates/g35-dispatch-priority-gate`
**Research:** `research/g35/`, commit `2dfcb6a` (recommendation A — BUILD)
**Status:** built, validated, **FROZEN at `3b7c6a4bd0f403a7`** (35 files).
**Gemini baseline: NOT RUN at time of freeze.**

---

## 1. What the task asks

A delivery marketplace ran a **two-stage randomised-saturation** experiment on a dispatch-priority
feature. Each *dispatch pool* — one city on one service date — was randomised to a target saturation
of 0 / 25 / 50 / 75 / 100 %, and merchants within each pool were then randomised to priority.

The pilot readout pools every merchant and compares those assigned priority against those not:
**+16.6 fulfilment points**. That comparison is randomised, balanced and unbiased. It is also the
wrong object for the question Finance asked, because couriers are a fixed pool inside a dispatch
block: priority granted to one merchant is courier capacity taken from another. Under proportional
rationing, when every merchant carries the same dispatch weight the allocation is identical to
nobody carrying priority, so the private advantage measured at mixed saturation largely cancels at
full rollout. What survives is the dispatcher's genuine routing efficiency — a much smaller number.

Three objects are graded from the same experiment:

| object | contrast | visible truth |
|---|---|---|
| `direct_effect_50` | priority vs non-priority **within 50 %-saturated pools** | +0.2829 |
| `spillover_50` | non-priority merchants, 50 % pools vs 0 % pools | **−0.1181** |
| `policy_effect_full` | **100 % pools vs 0 % pools** — the rollout contrast | **+0.0420** |

Nothing is extrapolated: both end arms exist in the design.

---

## 2. Fixtures and the discriminating pair

| extract | cities | courier tightness | routing gain | policy effect | naive A/B | decision |
|---|---|---|---|---|---|---|
| `visible` | 60 | 0.78 | 0.060 | 0.0420 | 0.1661 | **launch** |
| `hidden_a` | 56 | 0.65 | 0.010 | 0.0056 | **0.2199** | **hold** |
| `hidden_b` | 64 | 0.92 | 0.012 | 0.0083 | 0.0792 | **hold** |
| `hidden_c` | 58 | 0.70 | 0.090 | 0.0553 | **0.2313** | **launch** |

Decision split **2 launch / 2 hold**, so a constant answer fails.

**`hidden_a` versus `hidden_c` is the core of the task.** Their pooled lifts differ by 5 %
(0.2199 vs 0.2313) while their rollout effects differ by a factor of ten (0.0056 vs 0.0553) and
their decisions are opposite. No analysis that looks only at treated-versus-control can tell them
apart — which is precisely the capability under test.

**The slack-capacity regime was dropped** (brief A6). Research showed that with slack couriers there
is no rationing, hence no interference, hence a nearly-correct naive estimate; it cannot carry
separation. `hidden_b` — moderate tightness, negligible routing gain — replaces it.

---

## 3. Tolerance, chosen from a measured window

τ = `TOL_MULTIPLIER` × `SE_REF`, with `SE_REF` the RMSE of the accepted estimator over **60
Monte-Carlo redraws** of the same design (`tools/g35/fixture_audit.py`).

| extract | direct_effect_50 | spillover_50 | policy_effect_full |
|---|---|---|---|
| visible | 0.006391 | 0.008846 | 0.004817 |
| hidden_a | 0.005615 | 0.006875 | 0.004532 |
| hidden_b | 0.005219 | 0.007484 | 0.004399 |
| hidden_c | 0.004477 | 0.005426 | 0.004750 |

The multiplier was **not inherited from G34**. It was computed from the gap between the widest
legitimate route and the sharpest wrong analysis that must be caught:

```
VALID  largest-pools subsample   hidden_c  err/SE = 1.85   (multiplier must exceed)
WRONG  whole 50% experiment      hidden_c  err/SE = 4.42   (multiplier must stay below)
   admissible window: 1.85 < m < 4.42      chosen: 3.0
```

At 3.0 the worst valid route sits at **0.62 of tolerance** and `W04_total_at_50_as_policy` is caught
at **1.47× tolerance**.

**G34's multiplier of 5.0 was explicitly rejected here.** It would have put tolerance at 0.024 and
allowed `W04` — the most sophisticated wrong analysis in the design — to pass. Copying a tolerance
across tasks is not a neutral act.

---

## 4. Mutation suite — 29 cases, 0 mismatches, 0 errors

3 legitimate routes, 3 measured near-misses, 21 wrong analyses, plus Oracle and Nop.

| class | expected | observed |
|---|---|---|
| Oracle | 1 | **1** |
| Nop | 0 | **0** |
| 3 valid routes | 1 | **1, 1, 1** |
| 21 wrong analyses | 0 | **all 0** |
| 3 measured near-misses | 1 | **1, 1, 1** |

Every mutation is hash-distinct and **smoke-executed** against a real extract before being written.

### 4.1 The three measured near-misses

Recorded as honest negatives and **not counted toward separation**:

| case | worst policy error | why it passes |
|---|---|---|
| `W09_unweighted_blocks` | 0.0047 | merchant- vs demand-weighted block means land inside oracle-level error in this DGP |
| `W10_realised_activation_arms` | ~0.005 | **brief A7 requires this** — a verifier must not reject an analysis merely for using realised saturation; only a clearly defined scientific error may be rejected |
| `W17_arm_75_as_full` | 0.0089 | genuinely wrong science (wrong saturation), but the response is near-linear over [0.75, 1] so the numerical consequence is inside sampling noise |

---

## 5. Two defects found in my own validation, disclosed

### 5.1 The first mutation suite was entirely vacuous

The generator's template used `{{`/`}}` brace escaping while the renderer used `str.replace` rather
than `str.format`, so every generated file contained a Python **set literal containing a dict** and
crashed on import with `TypeError: unhashable type: 'dict'`. All 22 wrong cases "scored 0" — for the
wrong reason. The panel proved nothing.

Two things hid it: the hash check proved the files *differed* but never that they *ran*, and the CSV
runner grepped only for `FAILED`, silently discarding ten `ERROR` lines. It surfaced only because the
three *legitimate* routes also scored 0, which looked like a benchmark defect and was a harness
defect. **Had all cases been wrong methods, the suite would have looked perfect and G35 would have
been frozen on evidence of nothing.**

Generalised rather than patched: `make_mutations.py` now smoke-executes every mutation against a real
extract and asserts it emits all three graded quantities as numbers. All four rules carry verified
negative controls:

| rule | injected defect | result |
|---|---|---|
| mutation ≠ source | vacuous case | **CAUGHT** |
| no unexpected duplicate hash | duplicate case | **CAUGHT** |
| intended change present | textual assertion | enforced |
| **mutation executes** | `raise ValueError('boom')` | **CAUGHT** |

Recorded as rule 4 in `research/g35/mutation_hash_design.md` and carried into G36/G37.

### 5.2 A real verifier gap: bookkeeping was only checked on the visible extract

`W19_hardcoded_counts` hardcodes `n_dispatch_blocks = 1680` — exactly the visible extract's count —
and **passed**, because `test_hidden_extract` graded only effects and the recommendation. Fixed: the
hidden-extract test now re-verifies block count, merchant-day count, order total and the saturation
arm counts against each extract's own database. The hidden fixtures are deliberately different sizes
(56 / 64 / 58 cities), so the constants cannot survive. Oracle remains 1; `W19` now fails all three.

This gap existed for the same reason G34's trial 2 was dangerous: **reconciliation on the one extract
you can see proves nothing.**

---

## 6. Integrity

| control | result |
|---|---|
| plant `/pytest.ini` | `refusing to grade`, reward 0 |
| add a file to the standard library | `refusing to grade`, reward 0 |
| edit the warehouse in place | 8 checks fail, reward 0 |
| probe for `/tests` and `/solution` from the workspace | neither exists in the image; reward 0 |
| clean `docker build --no-cache` from a pristine copy | digest `52a128cd11d4640f`, **identical** to the dev build |
| leakage probes | `corr(rowid, saturation) = −0.040`; arms balanced 356/338/337/298/351; `extract_meta` operational only |
| generator copies | `tests/world.py` == `environment/build/world.py` |

---

## 7. Harbor results

| run | agent | reward | cost |
|---|---|---|---|
| `jobs/g35-oracle-v1` | oracle | **1.000** | $0 (no model) |
| `jobs/g35-nop-v1` | nop | **0.000** | $0 (no model) |
| `jobs/2026-09-20__06-54-06` | `harbor check` | 10/11 | $0.4452 |
| `jobs/2026-09-20__07-02-24` | `harbor check` (after fix) | **11/11** | $0.4626 |

The first check failed one item and the finding was correct: `tests/test.sh` was copied from G34 and
still described itself as *"Verifier for ForensicDS G34 (FY27 installed-base reliability run)"*.
Cosmetic in execution, wrong in substance - the file misidentified which task it graded. Fixed, the
candidate swept for other stale references (the two remaining G34 mentions are deliberate design
annotations), and the check re-run to 11/11 rather than asserting the task was "effectively clean".

**G35 model-powered validation total: $0.9078.**

**The Nop result is the requirement-29 demonstration.** The incumbent dashboard *passes*
`test_recommendation` and `test_counts_reconcile` — its pooled lift of 0.166 clears the +1.5 point
gate, gives the correct `launch` call on the visible extract, and every count reconciles — and still
scores **0**. A correct business decision built on materially wrong scientific quantities fails, and
reconciliation does not rescue it.

---

## 7.1 Freeze

**Frozen checksum: `3b7c6a4bd0f403a7`** over 35 files.

```
git ls-files candidates/g35-dispatch-priority-gate | xargs shasum -a 256 | shasum -a 256 | cut -c1-16
```

- per-file manifest: `research/g35/freeze_manifest.txt`, regenerable with `tools/g35/freeze.sh`
- generator copies match: `tests/world.py` == `environment/build/world.py` == `d01e6dc14c33bef1`
- warehouse digest from a clean `--no-cache` build: `52a128cd11d4640f`
- previously frozen tasks unchanged: G34 `f14dd0c0dbcd763c`, G05 `77a6e432d9d2cba2`

---

## 8. Open risks

1. **K17 partially stands.** Marketplace interference is a famous idea, and once an analyst
   recognises that assigned saturation is the operative variable several analyses land close. The
   difficulty is concentrated in one recognition step plus keeping three objects apart — the same
   shape as G34, which scored 2/3. A similar band is plausible and is predicted here *before* any
   baseline.
2. **Three wrong analyses are not separable** (§4.1). The panel's effective separation rests on the
   21 that are.
3. **`W04_total_at_50_as_policy` separates on only two of four extracts** (0.021 on visible and
   hidden_c; 0.003–0.005 on hidden_a/hidden_b). It is caught because all extracts must pass, but its
   margin is the narrowest in the suite at 1.47× tolerance.
4. **`SE_REF` uses 60 redraws**, carrying roughly 9 % relative error. The multiplier's window
   (1.85–4.42) is wide enough to absorb this, but it is not eliminated.
