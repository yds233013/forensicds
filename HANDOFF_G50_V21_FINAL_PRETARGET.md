# G50 v2.1 — FINAL PRE-TARGET HANDOFF
### Boost courier-incentive national-rollout decision · verifier built · adversarially validated
Generated 2026-09-30. Zero target-model calls. Nothing committed, nothing pushed.

---

## 1. EXECUTIVE VERDICT

**READY, under a narrowed capability claim.**

Both stop conditions from the previous turn are resolved on the terms ChatGPT set.

- **B1** is fixed by the single authorised sentence in `instruction.md`. The task now names an executable
  entry point, says the agent may rewrite whatever sits behind it, and says that command is what will be
  re-run. It prescribes no analytical method.
- **B2** is resolved by relaxing the three invariants that were unenforceable or misclassified. R2,
  post-treatment weighting and a one-week pre-period are **not** verifier failures. They are recorded as
  limits on G50's discriminating power, not as scientific endorsements.

The verifier is built, runs inside Harbor 0.21.0, and re-executes the agent's own command against four
privately regenerated worlds. Oracle = 1. Nop = 0. Incumbent = 0. Six criteria, graded from observable
evidence only, no model judge anywhere.

Building and attacking the verifier turned up more than the two stop conditions, and the honest summary
is that none of it is a plumbing defect and three items narrow what G50 can be cited for:

- **Three discriminating-power gaps.** The break-even threshold is never binding, so `M_threshold_ignored`
  passes (§21). A non-randomised comparison group is accepted, so `M_holdout_as_control` passes (§20). And
  the one-week pre-period invariant turns out to be **week-dependent** — rejected on two of the four
  possible choices, accepted on the other two — which is neither what v2 claimed nor what B2 assumed (§4).
- **Four documentation defects in frozen or sibling files**, plus four more in author-facing metadata. All
  eight are documentation-only; none changes a number, a decision or an agent-visible fact; all are reported
  in §31 for ChatGPT rather than silently repaired.
- **Two defects in my own verifier, found by the oracle and by an attack rather than by reasoning**, both
  fixed: the panel was graded against latent rather than recorded lateness (§15), and the graded artefacts
  under `/logs/verifier` were writable by the pipeline user (§24, not exploitable for reward, verified).
- **One defect in my test harness**, which briefly made an isolation result look like a task hole when it
  was not (§24, §29).
- **`harbor check` was never completed**, for environment reasons. Classified LIMITATION, with the reasoning
  in §27.

None of this is blocking. All of it is inside the §5/§6 boundary, and §35 lists the seventeen limitations
that remain.

---

## 2. B1 — THE EXECUTION CONTRACT (the only change to a frozen file)

`candidates/g50-courier-boost-rollout/instruction.md`

Before:

```
Produce `out/readout.json` and `out/market_week_panel.csv` exactly as the output contract specifies, and leave
the code that produced them in `/workspace`.
```

After:

```
Produce `out/readout.json` and `out/market_week_panel.csv` exactly as the output contract specifies. Leave the
implementation in place in `/workspace`, with

    python -m northline_eval readout --db data/northline.sqlite --out out

producing both outputs. You may rewrite whatever sits behind that command; it is the command I will re-run.
```

**Verified before writing it** that this is the entry point the frozen package already exposes:
`environment/workspace/northline_eval/__main__.py` → `cli.py` accepts the subcommand `readout` with
`--db` and `--out`, and `solution/solve.sh` invokes exactly this string. The sentence therefore documents
the existing contract; it does not introduce a new one.

What it establishes, and nothing more:

| establishes | how |
|---|---|
| which command the verifier re-runs | names it literally |
| that the implementation may be rewritten | "You may rewrite whatever sits behind that command" |
| that outputs must come from it | "with … producing both outputs" |

What it deliberately does **not** say: nothing about phase 1, difference-in-differences, pre-period
adjustment, weighting basis, interference, SUTVA, R2, the unit of inference, or any other step of the
science. Word-for-word it is a packaging instruction. The three numbered constraints below it in
`instruction.md` are unchanged.

---

## 3. PRE-VERIFIER FREEZE v2.1

Sequence followed, in order:

1. **Before the edit**, the v2 manifest (`PRE_VERIFIER_MANIFEST.txt`, body digest `0dbc9470ed483848`,
   28 files) was re-verified. Zero drift.
2. The B1 edit was applied to `instruction.md` and to nothing else.
3. A new manifest was written: `PRE_VERIFIER_MANIFEST_V21.txt`.

| | |
|---|---|
| superseded digest (v2) | `0dbc9470ed483848` |
| new aggregate digest (v2.1) | `e4b4ea294a032dda` |
| files covered | 28 |
| files changed | exactly 1 |
| changed file | `instruction.md` |
| old sha256 | `2436e0518c8e97309b768446e88757c0ae544e324f594c23758031466856c5c9` |
| new sha256 | `6a9ebdd6246b9a56b197a92df27eced4005989152c85a257f86f61e6ca5909da` |
| other 27 files | byte-identical, individually confirmed |

The 27 unchanged files include every file §4 of the brief protects: `environment/build/world.py` and its
copy `tests/world.py` (`9f8e76a0…`), `tests/scenarios.py` (`69191a9b…`), the business memo
(`85be2630…`), the experiment plan (`58dee9e8…`), the dispatch note (`2a308b9b…`), the output contract
(`b87b6291…`), the readout (`ed272177…`), and all seven incumbent package modules.

**A manifest-verification bug from the previous turn, disclosed again for the record.** The first shell
loop that checked v2 reported all 28 files as drifted because `cut` was not on `PATH` inside the loop, so
every "current" hash was the empty string. The check was re-run in Python and showed zero drift. A false
freeze-break report is worse than the bug, so it stays on the record.

---

## 4. B2 — RESOLUTION BY RELAXING UNENFORCEABLE / MISCLASSIFIED INVARIANTS

Three things the v2 specification listed as required verifier failures are **not** required verifier
failures in v2.1.

| withdrawn invariant | measured max deviation from the frozen anchor, over four worlds | verdict |
|---|---|---|
| R2 — boost-share dose-response extrapolated from 0 to 1 | 0.717 pp | **accepted — not discriminated** |
| post-treatment (phase-1 volume) weighting | 0.814 pp | **accepted — not discriminated** |
| one-week pre-period estimation window | **0.587 to 1.658 pp, depending on which week** | **partially enforceable — see below** |

against a tolerance of 1.303 pp. The reference itself deviates by 0.811 pp.

**The one-week invariant is the interesting case, and my earlier estimate of it was wrong.** Running it
through the real verifier rather than an offline script showed that its fate depends entirely on *which*
of the four pre-programme weeks is used:

| one-week window | visible | hidden_a | hidden_b | hidden_c | max | verdict at 1.303 |
|---|---|---|---|---|---|---|
| week 0 | 0.587 | 0.466 | 0.419 | 0.332 | 0.587 | accepted |
| week 1 | 0.841 | 0.684 | 0.515 | 0.225 | 0.841 | accepted |
| week 2 | 1.276 | 0.219 | **1.426** | 0.745 | 1.426 | **rejected on hidden_b** |
| week 3 (most recent) | 0.506 | 0.039 | 0.676 | **1.658** | 1.658 | **rejected on hidden_c** |
| all four weeks (reference) | 0.811 | 0.329 | 0.762 | 0.077 | 0.811 | accepted |

So a one-week pre-period is rejected on **two of the four possible choices** and accepted on the other two.
That is worse than either "must fail" or "accepted": it means G50's treatment of this dimension is
**arbitrary**, and a procedure that is valid but noisier can fail for picking the most recent pre-week
instead of the earliest. It is recorded as a limitation (§35), not as an enforced invariant. The verifier
run that established it is `I_1wk`, which uses week 3 and scores **0**, failing `quantitative_result` on
`hidden_c` alone with −10.970 against an anchor of −9.313.

### The precise claim about R2

G50 **cannot distinguish R2 in this synthetic world.** The reason is a property of the world, not a
property of R2:

- the realised dose-response of the late-delivery rate in boost share is close to linear over the range
  the design actually visits, so a coefficient fitted across that range and extrapolated to share 1
  lands near the 0-to-1 contrast; and
- the priority mechanism is **mean-preserving** within a market-hour — a boosted offer moves ahead of an
  unboosted one in one queue, so what one order gains another loses — which removes the curvature that
  would otherwise punish extrapolation through the interference region.

**This is a limitation of G50's discriminating power.** It is recorded as such, and it is not a finding
that R2 is a sound estimator for a marketplace rollout under interference. G50 provides no evidence
either way on that question, and nothing in this handoff should be read as providing it.

Per the standing prohibitions, none of the following was done to change this: the DGP was not modified,
dose-response curvature was not increased, no weighting-basis field and no reasoning field were added to
the output contract, and no hidden world was engineered to punish R2.

---

## 5. THE NARROWED CAPABILITY CLAIM — WHAT G50 MAY CLAIM

A reward of 1 on G50 is evidence that the model did all of the following, on four worlds it had never
seen, through one procedure it wrote:

1. **Reconstructed the metric population and the market-week evidence** from the warehouse: the correct
   delivered, Boost-eligible population, market attribution through zones, the Monday-labelled week grain,
   and courier hours from shift rows — exactly, to the recorded value, in all 280 market-weeks of each
   world.
2. **Reconstructed the arm contrast** the incumbent readout reports, to within 0.25 pp.
3. **Distinguished the arm contrast from the rollout quantity** — reported two numbers that differ, where
   the memo's decision quantity is the second one.
4. **Used the market-level experimental information** rather than only the order-randomised phase: the
   reported decision quantity lands within 1.303 pp of the world-specific rollout effect on all four
   worlds, which no route confined to the phase-2 arm contrast achieves (the arm contrast is 3.35–9.39 pp
   away from it, depending on the world).
5. **Reported finite-cluster uncertainty rather than order-level pseudoreplication**: an interval at
   least 2.0 pp wide, containing its own estimate and the rollout effect, over at most 40 declared
   independent units.
6. **Measured the courier-supply response** where that response is reliably discriminating, rather than
   reading the arm-level capacity identity that cannot fail.
7. **Reached the right final decision** under the memo's rule as written, on all four worlds, where two
   worlds say roll out and two say do not.
8. **Wrote a procedure that generalises**: the same command, unmodified, produced all of this on three
   sibling worlds with different seeds and different hidden channel parameters.

---

## 6. WHAT G50 MUST NOT CLAIM FROM REWARD ALONE

Reward is evidence of the eight items above and of nothing else. In particular a reward of 1 is **not**
evidence that the model:

1. reasoned explicitly about interference, or represented it at all;
2. understands SUTVA, or could state where it fails here;
3. arrived at its estimator through the intended causal warrant rather than by trial against the
   observable quantities;
4. distinguished pre-treatment from post-treatment weights — those are observationally equivalent in
   this world to within 0.002 pp of each other (0.811 vs 0.814 max deviation) and both pass;
5. used exactly four pre-period weeks — two of the four one-week windows also pass, and the other two
   fail, so a pass carries no information about the window and a failure may carry none either (§4);
6. rejected R2 for the intended theoretical reason, or rejected it at all — R2 passes;
7. holds the reference solution's causal justification. **Passing G50 does not imply the reference's
   reasoning.** Several procedures with materially different justifications pass.

The honest one-line summary: **G50 grades the reconstruction of a scientific object and a decision, not
the reasoning that reaches them.**

---

## 7. FILES CREATED / MODIFIED THIS TURN

Modified (frozen, under the B1 authorisation):

```
candidates/g50-courier-boost-rollout/instruction.md          2436e051… -> 6a9ebdd6…
```

Created — freeze record:

```
candidates/g50-courier-boost-rollout/PRE_VERIFIER_MANIFEST_V21.txt
```

Created — verifier (none of these is covered by the scientific manifest):

```
candidates/g50-courier-boost-rollout/tests/test_boost.py
candidates/g50-courier-boost-rollout/tests/test.sh
candidates/g50-courier-boost-rollout/tests/runtime_manifest.aarch64.sha256
candidates/g50-courier-boost-rollout/tests/runtime_manifest.x86_64.sha256
candidates/g50-courier-boost-rollout/tests/wheels/{iniconfig,packaging,pluggy,pygments,pytest,pytest_json_ctrf}-*.whl
candidates/g50-courier-boost-rollout/tests/wheels/requirements.txt
```

`tests/world.py` and `tests/scenarios.py` already existed and are unchanged. **No scientific file, no
document, no dataset, no seed, no parameter and no decision rule was touched.**

Created — this handoff:

```
HANDOFF_G50_V21_FINAL_PRETARGET.md
```

---

## 8. VERIFIER ARCHITECTURE

`tests/test.sh` is the Harbor entry point and does the sandboxing; `tests/test_boost.py` does the grading.

```
test.sh
 ├─ kill every process that started before the verifier's own exec chain,
 │    except the container's main command (identified by the stdio it inherited from PID 1,
 │    not by start time, which a loaded host makes unreliable)
 ├─ chown -R 0:0 /workspace ; chmod 700 /workspace     <- the pipeline user cannot read the workspace
 ├─ chmod 700 /tests                                   <- nor the generator, scenarios or verifier
 ├─ prove both of the above with setpriv, refuse to grade if either is readable
 ├─ refuse if /etc/ld.so.preload exists
 ├─ verify the per-architecture runtime manifest (see §12); refuse on any mismatch
 ├─ refuse if the loader drop-in file list changed
 ├─ refuse if any pytest configuration file is present
 ├─ build /tmp/pipeline-python: a setpriv shim running the image python as uid 65534
 ├─ build /tmp/verifier-venv from hash-pinned wheels, --no-index --require-hashes
 └─ pytest --noconftest -c /dev/null --rootdir=/tests test_boost.py
      └─ for each of the four worlds:
           build the world from the generator (private, in-process)
           copy the agent's code to an opaque scratch directory, excluding data/ and out/
           write that world's warehouse into the scratch tree, read-only
           delete the scratch output directory
           run `python -m northline_eval readout --db data/northline.sqlite --out out`
             as uid 65534, cwd = scratch, PYTHONPATH = scratch only
           refuse the outputs unless they are regular files newer than the run
           grade the six criteria against the authoritative quantities
      └─ write /logs/verifier/criteria.json and g50_detail.json
test.sh
 └─ merge criteria into /logs/verifier/reward.json as criterion_* plus the headline reward
```

**No LLM judges anything.** Every criterion is a numeric or string comparison against a quantity computed
by the generator.

---

## 9. HOW RE-EXECUTION IS MADE REAL

Seven mechanisms, each answering a specific way a submission could avoid doing the work:

| attack | mechanism |
|---|---|
| ship a correct `readout.json`, unrelated code | `out/` is never copied into the scratch tree, and the scratch tree is the only cwd the command runs in |
| re-read `/workspace/out` from inside the run | `/workspace` is root-owned mode 700; the pipeline runs as uid 65534 |
| leave stale outputs in place | the scratch `out/` is deleted before the run, and each produced file must be a regular file with mtime at or after the run's start |
| hardcode the visible world's answer | three sibling worlds with different seeds and different hidden channel parameters, all graded, conjunctively |
| branch on which world is running | scratch directories are named `r0`…`r3` in an opaque `mkdtemp` root; no world name appears in any path, environment variable or argument the submission can see |
| read the generator, the scenario specs or the verifier | `/tests` is mode 700 and the check is proven with `setpriv` before grading starts |
| exit 0 without recomputing | a non-zero exit fails immediately, and an exit 0 that produces nothing fails on the missing-output check |

---

## 10. THE SIX CRITERIA

Each criterion must hold on **all four** worlds. Task reward is 1 only if all six hold.

### `evidence_reconstruction`
- **observable evidence** — `out/market_week_panel.csv` and `orders_analysed`.
- **pass rule** — header exactly the seven contract columns in order; the market-week key set exactly the
  280 market-weeks of the world, no duplicates, no extras; `orders` and `late_orders` exact integers;
  `late_rate_pct` and `courier_hours` within 1e-4; `boost_share` a proportion that is ~0 before the
  programme and non-zero in phase 2; `orders_analysed` exactly the phase-2 enrolled metric population.
- **failure mode caught** — wrong metric population (cancelled orders, ineligible channels), wrong market
  attribution (zone read as market), wrong week grain, courier hours not aggregated from shift rows.
- **cannot distinguish** — which of the two defensible `boost_share` conventions was used (see §20).

### `scientific_object`
- **observable evidence** — `order_arm_contrast_pp` and `programme_effect_pp`.
- **pass rule** — the arm contrast within 0.25 pp of the world's realised arm contrast, **and** the
  programme effect at least 1.5 pp away from it.
- **failure mode caught** — reporting the arm contrast as the decision quantity; the incumbent's whole
  error.
- **cannot distinguish** — *why* the two numbers differ. A submission that produces a different number
  for a wrong reason passes this criterion and is then caught by `quantitative_result`.

### `quantitative_result`
- **observable evidence** — `programme_effect_pp`.
- **pass rule** — within 1.303 pp of the world's rollout effect.
- **failure mode caught** — using the arm contrast (3.35–9.39 pp away), omitting the pre-period
  adjustment (up to 7.34 pp away), swapping the phase-1 groups (up to 20.03 pp away).
- **cannot distinguish** — which of six near-equivalent market-level estimators was used, including R2.

### `uncertainty`
- **observable evidence** — the two interval bounds and `inference_unit_n`.
- **pass rule** — a real interval; it contains the submission's own estimate; width in [2.0, 25.0] pp;
  it contains the rollout effect within 0.5 pp of slack; `inference_unit_n` an integer in [2, 40].
- **failure mode caught** — order-level pseudoreplication (order-level widths are 0.867–0.931 pp, 4.6–7.1x
  narrower than the market-level reference), declaring the order count or the market-week count as the
  inference unit, zero-width and reversed intervals.
- **cannot distinguish** — HC1 from clustered from bootstrap standard errors; the exact degrees of
  freedom. The band is set on absolute width, so it does not encode the reference's standard error.

### `courier_supply_response`
- **observable evidence** — `courier_hours_response_pct`.
- **pass rule** — within `max(1.20, 0.12 × |anchor|)` of the world's courier-supply response.
- **failure mode caught** — the designed trap: the phase-2 arm-level capacity identity, which cannot fail
  because the arms share one courier pool; and un-normalised hours (a ratio of totals rather than of
  hours per order).
- **cannot distinguish** — four defensible definitional variants of "hours per order, on versus off". On
  `hidden_b` it has little power in absolute terms (§20).

### `decision`
- **observable evidence** — `decision`.
- **pass rule** — exactly `roll_out` or `do_not_roll_out`, equal to the memo rule applied to the world's
  rollout effect.
- **failure mode caught** — a constant answer (fails on two of four worlds either way), a flipped answer,
  ignoring the £0.19/£12.70 break-even and rolling out on any reduction.
- **cannot distinguish** — whether the rule was applied or the answer was guessed; two worlds each way
  makes a coin-flip a 1-in-16 pass, and the other five criteria are the real gate.

---

## 11. WHY THERE IS NO SEPARATE `identification` CRITERION

The brief permits one "only if the final state contains defensible observable evidence for it", and
forbids inventing a criterion to preserve the old schema.

The final state contains no field that evidences identification. The output contract has exactly eight
keys; there is no weighting-basis field and no warrant field, and §4 forbids adding one. Everything an
`identification` criterion could have tested is already tested elsewhere and would be a relabelling:

- that the market rather than the order is the unit of inference → `uncertainty`, via `inference_unit_n`
  and the interval width;
- that the estimand is the rollout quantity rather than the arm contrast → `scientific_object`;
- that the market-level design was used at all → `quantitative_result`, which no order-level route can
  satisfy.

So `identification` is **folded into `uncertainty`**, and the criterion list is six rather than seven.
The v2 candidate name `estimator_implementation` was also dropped: every rule it could have carried was
either identical to `quantitative_result` or unobservable. What replaced it is
`courier_supply_response`, which names exactly what it grades.

---

## 12. RUNTIME INTEGRITY PINNING

`tests/runtime_manifest.<arch>.sha256` pins, by sha256:

- `/usr/local/bin/python3.12`, `libpython3.12.so.1.0`, and the **entire** `/usr/local/lib/python3.12`
  tree including `site-packages` — 8,209 files on arm64, 7,788 on amd64;
- the 16 coreutils / util-linux / bash binaries `test.sh` itself invokes;
- the **shared-object closure** of all of the above, resolved with `ldd`: 33 libraries including `libc`,
  `libsqlite3`, `libcrypto` and the dynamic loader;
- `/etc/ld.so.conf`, `/etc/ld.so.cache` and the `ld.so.conf.d` drop-ins.

`test.sh` additionally compares the file *list* under the library tree and under `ld.so.conf.d` against
the manifest, so a file cannot be **added** and slip past a file-by-file hash check.

Two decisions worth flagging:

- **`site-packages` is inside the manifest, and the verifier venv is created with
  `--system-site-packages`.** The generator imports `numpy`, so the verifier must see the image's pinned
  analytics stack. Exposing it is safe precisely because it is hashed: an agent that patches `numpy` to
  subvert the generator changes a manifested file and the verifier refuses to grade. This is stricter
  than the P22 pattern G50 inherited, which manifests the standard library but excludes `site-packages`.
- **The manifest is per-architecture.** The pinned base tag is a multi-architecture manifest list, so the
  interpreter and every compiled extension differ between amd64 and arm64. `test.sh` selects
  `runtime_manifest.$(uname -m).sha256` and refuses if there is none. **This is a latent bug in the
  sibling tasks**: P22 and the others ship a single `runtime_manifest.sha256` generated on whichever
  machine built them, so a P22 verifier built on arm64 will refuse to grade on an amd64 Harbor host. It
  is out of scope here (§4 forbids modifying other tasks) but it is flagged in §33.

---

## 13. AUTHORITATIVE QUANTITIES AND THE TRUTH ANCHOR

| world | rollout effect | arm contrast | gap | courier response | break-even | margin | decision |
|---|---|---|---|---|---|---|---|
| visible | +2.0559 | −5.1189 | 7.175 | +2.8621 | 1.4961 | +3.552 | `do_not_roll_out` |
| hidden_a | −9.8437 | −6.4940 | 3.350 | +24.3612 | 1.4961 | +8.348 | `roll_out` |
| hidden_b | +5.0671 | −4.3223 | 9.389 | +1.7561 | 1.4961 | +6.563 | `do_not_roll_out` |
| hidden_c | −9.3128 | −5.3917 | 3.921 | +12.3240 | 1.4961 | +7.817 | `roll_out` |

`rollout effect` and `courier response` come from the frozen `world.truth()`. `arm contrast` is computed
by the verifier from the **recorded** delivery times (§17). `margin` is the distance from the break-even
threshold in the direction the decision falls.

Two properties this table establishes, both load-bearing:

- **The decision cannot be flipped by a legitimate estimator choice.** The smallest margin is 3.552 pp;
  the largest deviation any accepted route shows is 1.072 pp. The memo's rule also requires the interval
  to exclude zero, which raised a concern in the previous turn that two routes of different precision
  might disagree. They cannot: on the two `roll_out` worlds the effect is 3.1–3.8 interval half-widths
  from zero. This is now measured rather than hoped.
- **Neither a constant magnitude nor a constant decision survives.** The rollout effect spans 14.9 pp,
  the courier response 22.6 pp, and the decision splits two-two.

---

## 14. THE THIRD DEFECT: WHICH WINDOW `truth()` EVALUATES

Found while wiring the verifier to the frozen anchor.

`environment/build/world.py` evaluates the business estimand over the **programme window** — phase 1 plus
phase 2 — via `win = w["prog_mh"][o] & pop`. `HANDOFF_G50_V2_SCIENTIFIC_SPEC.md` §9 and its §19 table
instead quote values computed over the **phase-1 window alone**.

| world | programme window (frozen code) | phase-1 window (v2 spec §9) | gap |
|---|---|---|---|
| visible | +2.056 | +2.188 | 0.132 |
| hidden_a | −9.844 | −10.064 | 0.220 |
| hidden_b | +5.067 | +5.267 | 0.200 |
| hidden_c | −9.313 | −9.871 | 0.558 |

**Decisions are identical under both readings on all four worlds.** The disagreement is documentation, not
science.

**Resolved without touching any frozen file**, by adopting the frozen `world.truth()` as the authoritative
anchor. That reading is also the one the other authorities support: v2 spec §5 describes the programme
window, and the agent-visible memo says "under trading conditions like those of the programme period".
The v2 spec §9 and §19 table are therefore **wrong** and are corrected by this handoff. No DGP, no seed,
no decision and no agent-visible file changes.

Adopting it improves every measured property of the task:

| | phase-1 anchor (v2) | programme anchor (v2.1) |
|---|---|---|
| reference max deviation | 0.949 | **0.811** |
| tolerance `max(1.0, 1.6 × ref)` | 1.518 | **1.303** |
| raw-arm-contrast separation ratio | 2.01 | **2.55** |
| reference interval contains truth | 3 of 4 worlds | **4 of 4** |

---

## 15. THE FOURTH DEFECT: RECORDED VERSUS LATENT LATENESS

The generator computes its latent `late` flag from unrounded delivery times, but `write_sqlite` stores
`orders.delivered_after_min` rounded to two decimals. Orders whose delivery time sits within 0.005 min of
the promise therefore flip between the two.

| world | flips | of metric population | rate | effect on the arm contrast |
|---|---|---|---|---|
| visible | 50 | 341,266 | 1.47 / 10k | 0.0079 pp |
| hidden_a | 56 | 309,966 | 1.81 / 10k | 0.0249 pp |
| hidden_b | 51 | 340,427 | 1.50 / 10k | 0.0017 pp |
| hidden_c | 57 | 274,562 | 2.08 / 10k | 0.0042 pp |

This mattered: the verifier's first oracle run failed `evidence_reconstruction` on 43–49 market-weeks per
world, because the verifier was grading `late_orders` against the latent flag while the agent can only
see the recorded value. **The agent was right and the verifier was wrong.** The verifier now derives
lateness the way the analyst must — `round(delivered_after_min, 2) > promised_minutes` — for the panel and
for the arm contrast. The rollout effect keeps `world.truth()` as its anchor because it is a contrast of
potential outcomes with no recorded counterpart; the same discretisation moves it by under 0.01 pp.

**A consequence that is a genuine, immaterial inconsistency in a frozen file:** the
`market_week_baseline` convenience table is built from the latent flag, so its `late_orders` differ from a
recomputation over the same pre-period market-weeks by 10–14 orders out of roughly 100,000 per world.
An analyst who cross-checks the baseline table against their own recomputation will find a discrepancy of
order 0.01 pp. It cannot change any decision and it is not gradable either way. Reported, not fixed.

---

## 16. COMPLETE TOLERANCE TABLE

| quantity | rule | value | what sets it |
|---|---|---|---|
| `programme_effect_pp` | absolute | **1.303 pp** | `max(1.0, 1.6 × 0.811)`, 1.6x the reference's own worst deviation over four worlds, fixed before the mutation suite ran |
| `order_arm_contrast_pp` | absolute | **0.25 pp** | a reconstruction, not an estimate; the recorded-vs-latent effect is ≤0.025 pp |
| arm-contrast vs programme-effect gap | minimum | **1.5 pp** | the true gap is 3.350–9.389 pp; 2.23x headroom at the tightest |
| `courier_hours_response_pct` | mixed | **max(1.20, 0.12 × \|anchor\|)** | see §20 |
| interval width | band | **[2.0, 25.0] pp** | market-level widths are 3.97–6.29 pp; order-level are 0.867–0.931 pp |
| interval contains rollout effect | with slack | **0.5 pp** | a 95 % interval legitimately misses 1 time in 20 |
| `inference_unit_n` | band | **[2, 40]** | 20 markets; an order count or a market-week count fails |
| panel `orders`, `late_orders`, `orders_analysed` | exact | — | integers reconstructible exactly |
| panel `late_rate_pct`, `courier_hours` | absolute | **1e-4** | CSV float formatting |

### Separation at the tolerance that matters

Max deviation of `programme_effect_pp` from the frozen anchor, over all four worlds:

Per world, and by max and min over the four:

| route | visible | hidden_a | hidden_b | hidden_c | max | min | verdict at 1.303 |
|---|---|---|---|---|---|---|---|
| R2 — boost-share dose-response | — | — | — | — | 0.717 | — | accepted (B2) |
| I_1wk[week 0] | 0.587 | 0.466 | 0.419 | 0.332 | 0.587 | 0.332 | accepted |
| **D_ow — reference** | 0.811 | 0.329 | 0.762 | 0.077 | **0.811** | 0.077 | accepted |
| H_post — post-treatment weights | 0.814 | 0.352 | 0.796 | 0.045 | 0.814 | 0.045 | accepted (B2) |
| I_1wk[week 1] | 0.841 | 0.684 | 0.515 | 0.225 | 0.841 | 0.225 | accepted |
| D_pool — arm-level pooled pre/post | 0.789 | 0.451 | 0.858 | 0.099 | 0.858 | 0.099 | accepted |
| D_panel — weighted two-way FE | — | — | — | — | 0.804 | — | accepted |
| D_mu — market-unweighted | 0.604 | 0.706 | 1.082 | 0.822 | 1.082 | 0.604 | accepted |
| **M_holdout_as_control — never-enrolled markets as the comparison group** | 0.311 | 0.615 | 1.198 | 0.493 | **1.198** | 0.311 | **accepted — missed true-negative (§35)** |
| I_1wk[week 2] | 1.276 | 0.219 | 1.426 | 0.745 | 1.426 | 0.219 | rejected on hidden_b |
| I_1wk[week 3] | 0.506 | 0.039 | 0.676 | 1.658 | 1.658 | 0.039 | rejected on hidden_c |
| P_ow — no pre-period adjustment, estate-weighted | 2.967 | 0.466 | 3.524 | 0.050 | 3.524 | 0.050 | rejected on 2 of 4 |
| P_mu — no pre-period adjustment, market-unweighted | 0.182 | 0.648 | 7.346 | 0.851 | 7.346 | 0.182 | rejected on 1 of 4 |
| **naive — the raw arm contrast** | 7.175 | 3.350 | 9.389 | 3.921 | 9.389 | **3.350** | **rejected on 4 of 4** |
| L_swap — phase-1 groups reversed | 3.301 | 20.016 | 9.373 | 18.702 | 20.016 | 3.301 | rejected on 4 of 4 |

Minimum separation of the raw arm contrast from the tolerance edge: **3.350 pp**, a ratio of **2.57x**.

### Why the tolerance was not re-tuned after seeing this

The admissible range is bounded below by the noisiest legitimate route (1.658, `I_1wk[week 3]`) and above
by the closest route that **must** be rejected (3.301, `L_swap`; the naive arm contrast is at 3.350). Any
tolerance in (1.658, 3.301) rejects everything that has to be rejected. Raising 1.303 → 1.75 would admit
all four one-week windows and change nothing else: the next route up is P_ow at 3.524.

**The tolerance stays at 1.303.** Two reasons:

1. **1.303 was derived before the mutation results, by a stated rule** — `max(1.0, 1.6 × 0.811)`, 1.6 times
   the reference's own worst deviation. Moving it after seeing which mutations pass would be tuning the
   tolerance to the mutation suite, which is exactly the overfitting a benchmark must not do.
2. **The cost of raising it is concentrated on the thing the task exists to test.** At 1.303 the naive arm
   contrast — the incumbent's whole error — separates by 2.57x. At 2.3, the midpoint of the admissible
   range, it separates by 1.46x. Admitting the two least precise one-week variants is not worth halving
   the margin on the criterion that carries the benchmark's claim.

The consequence is a false-negative risk, stated plainly in §35: an otherwise correct submission that
adjusts against only the most recent pre-programme week fails on `hidden_c`. **ChatGPT can overrule this
with one number** — see the decision packet.

---

## 17. TOLERANCE REVIEW: THE ≥3 SEPARATION HEURISTIC

The previous turn treated "every wrong route must separate by at least 3x the tolerance" as a gate. **It
was an author-created quality gate, not part of the assignment**, and v2.1 does not require it. It is
retired, and the measured separations are reported as they are rather than engineered upward:

| separation | measured | under the old heuristic |
|---|---|---|
| programme effect, raw arm contrast vs tolerance | 2.55x | would have failed |
| courier response, worst legitimate variant vs tolerance | 1.39x (on `hidden_b`) | would have failed |

Both are reported as limitations in §36 rather than as blockers. Nothing was changed in the world to move
either number: the improvement from 2.01x to 2.55x came entirely from resolving the §14 documentation
defect in favour of the frozen code, not from touching the DGP.

---

## 18. `courier_hours_response_pct` — GATE OR REQUIRED OUTPUT

**Decision: it gates.** The contract is unchanged; the field was already required.

Four defensible definitions of "the percentage change in courier hours per order attributable to Boost
being on rather than off", all measured in phase 1 where Boost was set at the market level:

| world | anchor | V1 pooled | V2 market-unweighted | V3 pre-adjusted | V4 market-week weighted | tolerance | worst legit | headroom |
|---|---|---|---|---|---|---|---|---|
| visible | +2.862 | +2.872 | +2.796 | +2.935 | +2.872 | 1.200 | 0.073 | 16.5x |
| hidden_a | +24.361 | +25.103 | +26.057 | +25.622 | +25.103 | 2.923 | 1.696 | 1.72x |
| hidden_b | +1.756 | +2.609 | +2.620 | +1.882 | +2.609 | 1.200 | 0.864 | **1.39x** |
| hidden_c | +12.324 | +11.814 | +12.213 | +12.011 | +11.814 | 1.479 | 0.510 | 2.90x |

All four variants pass on all four worlds. A flat absolute band cannot do this — the signal ranges from
1.8 pp to 24.4 pp — which is why the rule is mixed.

**Why it gates despite the thin margin.** The trap it exists to catch is the incumbent's arm-level
capacity identity, which cannot fail because the two arms draw on one courier pool. The verifier measured
the incumbent at 0 on all four worlds, on this criterion, every run. And a submission that answers with
the *arm-size imbalance* instead (a constant ≈+22.5 % in every world) lands inside tolerance on
`hidden_a` by coincidence — and is still rejected, because the criterion is conjunctive across worlds and
it fails on the other three. The cross-world conjunction, not the per-world band, is what carries this
criterion.

**Its honest limit:** on `hidden_b`, where `beta_supply` is 0.018 and the true response is only +1.756 pp,
any answer in roughly [0.56, 2.96] passes. On that world the criterion tests that the analyst measured
courier supply at market level in phase 1 at all, not that they measured it well.

---

## 19. V1 → V2 → V2.1 MUTATION MAPPING

Three mutations are removed from the expected-failure set by B2 and **kept as diagnostic probes** with the
status "not discriminated / accepted in this world". The evidence is preserved, not deleted.

| v2 id | mutation | v2 expectation | v2.1 status |
|---|---|---|---|
| **H** | post-treatment realised-volume weighting | must fail | **accepted — not discriminated.** 0.814 pp max, vs the reference's 0.811. Pre- and post-treatment weights are observationally equivalent here because the estimand fixes the weights on the pre-programme mix by construction, so a volume response cannot move it. Retained as a probe. |
| **I** | one-week pre-period window | must fail | **partially enforced, arbitrarily.** Rejected on 2 of the 4 possible week choices, accepted on the other 2 (§4). Pre-period adjustment is a finite-sample accuracy correction, not identification: randomisation already delivers unbiasedness in expectation, so shortening the window costs precision, not validity. G50 therefore rejects a valid-but-noisier procedure roughly half the time, depending on an arbitrary choice. **Neither B2's "accept" nor v2's "must fail" describes what the verifier actually does.** Retained as a probe with this status. |
| **X** | R2 boost-share dose-response | must fail | **accepted — not discriminated.** 0.717 pp max, the closest of any route. Cause in §4. Retained as a probe. |

The other v1 mappings stand as recorded in the previous turn's §12, with one correction: mutation **D/D′**
(no pre-period adjustment) is reported here as `P_ow` / `P_mu` and is rejected on 2 of 4 and 1 of 4 worlds
respectively. It therefore fails the conjunctive suite but is **not** rejected on every world. That is
stated as a limitation rather than dressed up as a pass.

---

## 20. LEGITIMATE ROUTE RESULTS

Every route below was submitted as real code, installed into `/workspace`, and re-executed by the verifier
against all four worlds. Columns are the six criteria in the order
E `evidence_reconstruction` · S `scientific_object` · Q `quantitative_result` · U `uncertainty` ·
C `courier_supply_response` · D `decision`. `worlds` is per-world overall pass/fail in the order
visible / hidden_a / hidden_b / hidden_c.

| submission | what it is | reward | E | S | Q | U | C | D | worlds |
|---|---|---|---|---|---|---|---|---|---|
| `oracle` | the reference: pre-adjusted, estate-weighted, market-level WLS with HC1 | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `D_panel` | weighted two-way fixed effects over pre + phase-1 market-weeks, treat×post, clustered on market | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `D_pool` | arm-level pooled pre/post difference in differences, market-level interval | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `D_mu` | market-unweighted difference in differences, two-sample t on the market deltas | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `H_post` | reference, but weighted on phase-1 (post-treatment) order volume — **withdrawn invariant H** | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `R2_boostshare` | late rate on the configured boost share, market and week FE, extrapolated 0→1 — **withdrawn invariant X** | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `I_1wk` | reference on a one-week pre-period (most recent week) — **withdrawn invariant I** | **0** | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | PPPf |
| `M_holdout_as_control` | never-enrolled holdout markets used as the phase-1 comparison group | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `P_ow_unadjusted` | phase-1 contrast with no pre-period adjustment, estate-weighted | **0** | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | fPfP |
| `P_mu_unadjusted` | phase-1 contrast with no pre-period adjustment, market-unweighted | **0** | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | PPfP |
| `L_swap_arms` | phase-1 on and off groups reversed | **0** | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | ffff |

**Six of eleven score 1.** The four intended difference-in-differences routes all pass, which is the
minimum a task must satisfy to be fair. Two withdrawn invariants (H, X) pass, as B2 concluded. The third
(I) fails, on one world, for the reason set out in §4. Two routes that get the scientific object right but
omit the pre-period adjustment fail. The swapped-arm route fails.

Two of these results are **missed true-negatives** and are discussed in §35:

- `M_holdout_as_control` replaces the randomised phase-1 off group with the four never-enrolled holdout
  markets — a non-randomised comparison — and passes on all four worlds (max deviation 1.198 pp). After
  pre-period differencing the holdout markets are exchangeable enough that G50 cannot tell the difference.
  This is the same class of blind spot as R2: the world does not punish the weaker warrant.
- `P_ow_unadjusted` and `P_mu_unadjusted` fail the suite but are **not** rejected on every world — P_ow
  passes on hidden_a and hidden_c, P_mu on three of four. A single-world version of G50 would not reject
  them.


---

## 21. COMPLETE MUTATION RESULTS

| submission | what it is | reward | E | S | Q | U | C | D | worlds |
|---|---|---|---|---|---|---|---|---|---|
| `nop` | no action at all — the incumbent package is what gets re-run | **0** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `incumbent` | the shipped analysis, run unmodified | **0** | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_right_decision_wrong_quantity` | correct decision string, arm contrast reported as the decision quantity | **0** | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ffff |
| `M_order_level_se` | correct point estimate, order-level interval width | **0** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ffff |
| `M_order_count_as_unit` | correct everything, order count declared as the inference unit | **0** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ffff |
| `M_market_week_as_unit` | correct everything, market-week count declared as the inference unit | **0** | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ffff |
| `M_cancelled_in_denominator` | cancelled orders counted in the metric population | **0** | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ffff |
| `M_all_channels` | scheduled and corporate orders counted in the metric population | **0** | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ffff |
| `M_zone_as_market` | zone treated as the market | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_phase_swap` | phase-2 weeks used where the phase-1 soak should be | **0** | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_courier_not_per_order` | courier hours compared as totals, not per order | **0** | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ffff |
| `M_courier_arm_identity` | the incumbent's phase-2 arm-level capacity identity | **0** | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | fPff |
| `M_decision_flipped` | correct analysis, decision inverted | **0** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ffff |
| `M_constant_roll_out` | always `roll_out` | **0** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | fPfP |
| `M_constant_do_not_roll_out` | always `do_not_roll_out` | **0** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | PfPf |
| `M_threshold_ignored` | roll out on any reduction, ignoring the £0.19/£12.70 break-even | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `M_excluded_in_control` | ineligible-channel orders relabelled into the phase-2 control arm | **1** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | PPPP |
| `M_hardcode_visible` | run once, then replace the analysis with a copy of `/workspace/out` | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_hardcode_literal` | run once, then bake the resulting JSON in as a literal | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | Pfff |
| `M_stale_outputs_only` | run once, then make the analysis a no-op | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_no_executable` | correct outputs, then delete the module entry point | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_command_exits_nonzero` | entry point exits 3 | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |
| `M_command_exits_zero_no_work` | entry point exits 0 without doing anything | **0** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ffff |

**21 of 23 mutations are correctly rejected.** Three results deserve comment because of *how* they fail:

- **`M_hardcode_literal` passes on `visible` alone** (`Pfff`). It runs the correct analysis once, reads its
  own output, and bakes it in as a Python literal. That is the strongest form of the hardcoding attack, and
  the only thing that defeats it is re-execution against worlds the submission has never seen. This single
  row is the clearest evidence that the re-execution design is load-bearing rather than decorative.
- **`M_courier_arm_identity` passes on `hidden_a` alone** (`fPff`). The incumbent's arm-level capacity
  identity answers with the arm-size imbalance, a near-constant ≈+22.5 % in every world, and `hidden_a`'s
  true courier response happens to be +24.4 %. It is rejected because the criterion is conjunctive across
  worlds, not because the per-world band caught it — exactly as §18 predicted analytically.
- **`M_constant_roll_out` and `M_constant_do_not_roll_out` are mirror images** (`fPfP` and `PfPf`), each
  failing exactly two worlds. The decision split is genuinely two-two, so a constant answer cannot exceed
  a 1-in-16 chance of passing.

### The two that are not rejected

- **`M_threshold_ignored` — reward 1. A real gap.** See the subsection below.
- **`M_excluded_in_control` — reward 1, but the mutation is vacuous.** It relabels `arm = 'excluded'` rows
  into the control arm. Those rows are precisely the corporate and scheduled-channel orders
  (`0` standard-channel orders carry that label in any world), which `warehouse.orders()` already drops on
  `order_channel = 'standard'` before any arm is read. The mutation therefore changes nothing and its
  reward carries no information. It is reported as an **invalid mutation**, not as a missed true-negative.
  The v1 concern it was meant to represent — holdout *markets* used as a comparison group — is
  `M_holdout_as_control`, which is a genuine miss (§20, §35).

### The break-even threshold is never binding — a real gap in discriminating power

`M_threshold_ignored` replaces the memo's rule with "roll out on any reduction at all" and **scores 1**.
It is a genuine true-negative — `instruction.md` constraint 3 requires the decision to follow the memo
rule as written — and G50 does not catch it.

The cause is structural, not an oversight in the mutation:

| world | rollout effect | memo rule (≥1.4961 pp reduction **and** interval excludes zero) | "any reduction" rule | discriminates? |
|---|---|---|---|---|
| visible | +2.0559 | `do_not_roll_out` | `do_not_roll_out` | no |
| hidden_a | −9.8437 | `roll_out` | `roll_out` | no |
| hidden_b | +5.0671 | `do_not_roll_out` | `do_not_roll_out` | no |
| hidden_c | −9.3128 | `roll_out` | `roll_out` | no |

**No world places the effect between 0 and −1.4961 pp**, so the £0.19 ÷ £12.70 break-even arithmetic — a
real piece of the task's business content — is never exercised. The `decision` criterion tests the *sign*
of the effect, not the threshold. The interval-excludes-zero clause is likewise never binding: on the two
`roll_out` worlds the effect sits 3.1–3.8 interval half-widths from zero.

**This is a consequence of a design decision made two turns ago, and the trade-off is real.** The visible
world's effect originally sat 0.09 pp from the threshold, which made the decision knife-edge: legitimate
routes with different precision disagreed on the answer. Moving the effect away from the threshold fixed
that and created this. The two requirements are in tension, and the tension is arithmetic:

- the worst accepted route deviates by **1.072 pp** (`D_mu`);
- the threshold is **1.4961 pp**;
- so any world whose effect lies in (0, −1.4961) has an accepted-route band of width 2.14 pp straddling a
  threshold only 1.50 pp from zero, and some accepted route lands on the wrong side.

**The one place both can hold.** An effect in roughly **[−0.35, −0.10] pp** satisfies both: every accepted
route reads above −1.4961 and therefore reaches `do_not_roll_out` under the memo rule, while most read
below zero and therefore reach `roll_out` under the "any reduction" rule.

| candidate fifth-world effect | accepted-route band | every route reaches the memo answer | threshold binding |
|---|---|---|---|
| −0.20 | [−1.272, +0.872] | **yes** | **yes** |
| −0.30 | [−1.372, +0.772] | **yes** | **yes** |
| −0.50 | [−1.572, +0.572] | no | yes |
| −0.80 | [−1.872, +0.272] | no | yes |
| −1.20 | [−2.272, −0.128] | no | yes |

**Not implemented.** A fifth world means editing `tests/scenarios.py`, which is in the v2.1 manifest and on
§4's protected list. It is offered as a concrete, calibrated remedy for ChatGPT to authorise or decline —
see the decision packet. Until then the limitation stands: **G50 does not verify that the agent applied
the break-even threshold, only that it got the direction right.**

---

## 22. VERIFIER ATTACK RESULTS — THE GRADING FUNCTION

Forty adversarial outputs driven directly through `test_boost.py`'s own `grade()` with the real
anchors of the `visible` world, so the code under test is exactly the code the container runs.
Attacks on the sandbox rather than on the grading logic are in §24.

| case | E S Q U C D | reward | intended | first reason |
|---|---|---|---|---|
| `CONTROL_good_submission` | 1 1 1 1 1 1 | 1 | pass ✓ |  |
| `A_malformed_json` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not parseable JSON: Unterminated string starting at: line 1 co… |
| `A_nan` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not parseable JSON: readout.json contains the non-JSON constan… |
| `A_infinity` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not parseable JSON: readout.json contains the non-JSON constan… |
| `A_negative_infinity` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not parseable JSON: readout.json contains the non-JSON constan… |
| `A_numeric_strings` | 0 0 0 0 0 0 | 0 | fail ✓ | orders_analysed is not a finite int: '115424' |
| `A_bool_for_int` | 0 0 0 0 0 0 | 0 | fail ✓ | inference_unit_n is not a finite int: True |
| `A_null_field` | 0 0 0 0 0 0 | 0 | fail ✓ | programme_effect_pp is not a finite float: None |
| `A_json_array` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not a JSON object |
| `A_json_string` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not a JSON object |
| `A_empty_file` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json is not parseable JSON: Expecting value: line 1 column 1 (char 0) |
| `A_extra_key` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json keys are ['control_arm_vs_holdout_pp', 'courier_hours_response_pc… |
| `A_missing_key` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json keys are ['decision', 'inference_unit_n', 'order_arm_contrast_pp'… |
| `A_reversed_ci` | 1 1 1 0 1 1 | 0 | fail ✓ | interval is not an interval: [4.6859, -0.5741] |
| `A_zero_width_ci` | 1 1 1 0 1 1 | 0 | fail ✓ | interval is not an interval: [2.0559, 2.0559] |
| `A_absurd_ci` | 1 1 1 0 1 1 | 0 | fail ✓ | interval width 2000.000 pp exceeds 25.0: uninformative |
| `A_ci_excludes_own_estimate` | 1 1 1 0 1 1 | 0 | fail ✓ | interval [+5.056, +11.056] does not contain the estimate +2.056 |
| `A_zero_width_space_decision` | 1 1 1 1 1 0 | 0 | fail ✓ | decision 'do_not_roll_out\u200b' != 'do_not_roll_out' |
| `A_decision_uppercase` | 1 1 1 1 1 0 | 0 | fail ✓ | decision 'DO_NOT_ROLL_OUT' != 'do_not_roll_out' |
| `A_decision_whitespace` | 1 1 1 1 1 0 | 0 | fail ✓ | decision ' do_not_roll_out ' != 'do_not_roll_out' |
| `A_inference_unit_zero` | 1 1 1 0 1 1 | 0 | fail ✓ | inference_unit_n 0 is not a count of independent randomisation units (2..40) |
| `A_inference_unit_one` | 1 1 1 0 1 1 | 0 | fail ✓ | inference_unit_n 1 is not a count of independent randomisation units (2..40) |
| `A_inference_unit_41` | 1 1 1 0 1 1 | 0 | fail ✓ | inference_unit_n 41 is not a count of independent randomisation units (2..40) |
| `A_inference_unit_40_boundary` | 1 1 1 1 1 1 | 1 | pass ✓ |  |
| `A_effect_offset_just_inside_1.3` | 1 1 1 1 1 1 | 1 | pass ✓ |  |
| `A_effect_offset_just_outside_1.31` | 1 1 0 1 1 1 | 0 | fail ✓ | programme_effect_pp +3.366 is 1.310 pp from the rollout effect +2.056 (toleran… |
| `A_effect_offset_exact_edge_1.303` | 1 1 0 1 1 1 | 0 | fail ✓ | programme_effect_pp +3.359 is 1.303 pp from the rollout effect +2.056 (toleran… |
| `A_contrast_off_by_0.24` | 1 1 1 1 1 1 | 1 | pass ✓ |  |
| `A_contrast_off_by_0.26` | 1 0 1 1 1 1 | 0 | fail ✓ | order_arm_contrast_pp off by 0.260 pp (> 0.25) |
| `A_courier_at_tolerance` | 1 1 1 1 1 1 | 1 | pass ✓ |  |
| `A_courier_over_tolerance` | 1 1 1 1 0 1 | 0 | fail ✓ | courier_hours_response_pct +4.072 is 1.210 from +2.862 (tolerance 1.200) |
| `A_orders_analysed_off_by_one` | 0 1 1 1 1 1 | 0 | fail ✓ | orders_analysed 115425 != 115424 (metric population, phase 2, enrolled markets) |
| `A_panel_duplicated` | 0 1 1 1 1 1 | 0 | fail ✓ | 280 duplicate market-week rows in the panel |
| `A_panel_subset` | 0 1 1 1 1 1 | 0 | fail ✓ | 221 market-weeks missing from the panel, e.g. [('MKT-005', '2026-04-27'), ('MK… |
| `A_panel_extra_market_week` | 0 1 1 1 1 1 | 0 | fail ✓ | 1 market-weeks in the panel are not in the warehouse window, e.g. [('MKT-099',… |
| `A_panel_header_reordered` | 0 1 1 1 1 1 | 0 | fail ✓ | panel header is ['week_start', 'market_id', 'orders', 'late_orders', 'late_rat… |
| `A_panel_boost_share_1_in_pre` | 0 1 1 1 1 1 | 0 | fail ✓ | panel boost_share outside [0.0, 0.02] wrong in 20 market-weeks, e.g. [('MKT-00… |
| `A_panel_empty` | 0 1 1 1 1 1 | 0 | fail ✓ | 280 market-weeks missing from the panel, e.g. [('MKT-001', '2026-04-06'), ('MK… |
| `A_no_outputs_at_all` | 0 0 0 0 0 0 | 0 | fail ✓ | readout.json was not produced as a regular file by the frozen command |
| `A_nonzero_exit` | 0 0 0 0 0 0 | 0 | fail ✓ | the frozen command exited 3: boom |

**Zero mismatches.** Every case scored as intended. The five that score 1 are the control plus four
deliberate just-inside-the-boundary probes (`inference_unit_n = 40`, effect offset +1.30 against a
1.303 tolerance, contrast offset +0.24 against 0.25, courier offset +1.19 against 1.20), each paired
with a just-outside twin that scores 0. The tolerance edges are therefore verified from both sides.

One detail worth recording: `A_effect_offset_exact_edge_1.303` **fails**. Rounding the perturbed
estimate to four decimals puts its deviation at 1.3030000000000002, marginally over the bound. The
edge is inclusive as written (`<=`); a value that lands exactly on it after rounding may fall either
way. This is immaterial at 1e-16 but it is stated rather than hidden.

---

## 23. RE-EXECUTION IS REAL — THE FIVE REQUIRED PROOFS

| required proof | submission | result |
|---|---|---|
| correct JSON + unrelated code **fails** | `M_hardcode_visible` — run once, then replace the analysis with a copy of `/workspace/out` | **0**, all six criteria fail on all four worlds. `/workspace` is root-owned mode 700 and the pipeline runs as uid 65534, so the copy source is unreachable and nothing is produced. |
| copied incumbent + hardcoded corrected JSON **fails** | `M_hardcode_literal` — bake the correct visible answer in as a literal | **0**. Passes `visible` only; fails all six criteria on the three unseen worlds. |
| stale outputs **fail** | `M_stale_outputs_only` — produce correct outputs once, then make the analysis a no-op | **0**, all six on all four. The scratch `out/` is deleted before every run and each file must post-date it. |
| visible-world hardcoding **fails** | `M_hardcode_literal`, `M_constant_roll_out`, `M_constant_do_not_roll_out` | **0** in every case. No constant magnitude or constant decision survives four worlds. |
| a valid **rewritten** implementation behind the required command **passes** | `D_panel`, `D_pool`, `D_mu`, `H_post`, `R2_boostshare` — each a materially different estimator appended over the reference | **1** in every case. The verifier invokes `python -m northline_eval readout …` and does not care what sits behind it. |

Two further execution proofs, not on the required list:

| | submission | result |
|---|---|---|
| a command that exits non-zero fails immediately | `M_command_exits_nonzero` | **0** — `the frozen command exited 3` |
| a command that exits 0 without working fails | `M_command_exits_zero_no_work` | **0** — `readout.json was not produced as a regular file by the frozen command` |
| deleting the entry point fails | `M_no_executable` | **0**, all six on all four |

---

## 24. SANDBOX AND ISOLATION ATTACK RESULTS

**A correction to how this was first measured, because it changed the conclusion.** The first isolation
probe reported `uid=0`, `cwd=/workspace`, and successful reads of `/tests/world.py`, `/tests/scenarios.py`
and `/tests/test_boost.py`. Those readings came from the **agent** phase, not from the verifier's
re-execution — the giveaways being `AGENT_CMD` in the environment, `tests-ro` in the root listing, and
`/logs/verifier/reward.txt` not yet existing. My own test harness had copied the tests into place *before*
running the agent command, which real Harbor does not do. **The flaw was in the harness, not the task.** The
harness was fixed to create `/tests` only for the verifier phase, the probe was rewritten to surface its
findings through a graded field so that it reports from inside the re-execution, and the world-name
branching attack was re-run under the corrected ordering.

### What the re-executed submission can actually reach

Reported by the submission itself, from inside the verifier's re-execution:

```
uid = 65534
cwd = /tmp/g50-wqksobbj/r0
parent directory listing            PermissionError
/tests/world.py                     PermissionError
/tests/scenarios.py                 PermissionError
/tests/test_boost.py                PermissionError
/tests/runtime_manifest.*.sha256    PermissionError
/workspace/README.md                PermissionError
/workspace/out/readout.json         PermissionError
environment  HOME LC_CTYPE MPLBACKEND OMP_NUM_THREADS OPENBLAS_NUM_THREADS PATH PWD
             PYTHONDONTWRITEBYTECODE PYTHONPATH SHLVL
```

Every claim §9 makes is confirmed. The generator, the scenario specs and the verifier are unreachable; the
original workspace and its outputs are unreachable; the scratch directory is opaquely named and its parent
is not even listable, so the submission cannot tell how many worlds exist or which one it is in; and no
environment variable names a world.

### Results

| attack | reward | what happened |
|---|---|---|
| `A_symlink_readout` — replace `out/readout.json` with a symlink to `/tests/world.py` | **0** | rejected: not a regular file |
| `A_symlink_out_dir` — write elsewhere and symlink `out/` to it | **0** | rejected: not a regular file |
| `A_probe_from_verifier` — enumerate what is reachable, report it through a graded field | **0** | reached nothing it should not; failed only `decision`, because the probe string is not a valid decision |
| `A_world_name_branching` — hash the surroundings and answer per world | **0** | nothing to branch on; failed `decision` on the guess |
| `A_world_name_branching2` — same, re-run with `/tests` absent during the agent phase | **0** | same result |
| `A_late_background_write` — a background thread rewrites the output after the run returns | **0** | the verifier reads the outputs at the point the command returns |
| `A_write_reward` — write `/etc/ld.so.preload` as root during the agent phase | **0** | **`verifier: /etc/ld.so.preload present; refusing to grade`** — the refusal path fires on the most serious available tamper |
| `A_write_from_verifier` — from the re-execution, forge `reward.txt`, `reward.json`, `criteria.json` | **0** | see below |

### One real finding: the graded artefacts were writable, and are now closed

The re-executed submission, as uid 65534, **could** write `/logs/verifier/reward.txt`, `reward.json` and
`criteria.json`. It could not write `/tests`, `/etc/ld.so.preload` or `site-packages`.

**It is not exploitable for reward**, and that was verified rather than argued: the submission wrote `1`
into `reward.txt` and the final recorded reward was **`0`**, with the genuine criterion values. `test.sh`
derives the reward from pytest's exit status and rewrites both files afterwards, and `test_boost.py` writes
the real `criteria.json` after the four-world loop, so a forgery is always overwritten. Exiting 0 requires
every criterion to genuinely pass.

It is still fragile — the only thing preventing forgery is write ordering — so `test.sh` now chowns
`/logs/verifier` to root and sets mode 700 before pytest runs.

**And the hardening does not take effect on this machine, which is also reported rather than hidden.**
Re-running the same attack after the change shows the writes still succeeding, because Docker Desktop on
macOS presents bind-mounted files as world-writable however they are chmod'd. On a Linux Harbor host
`/logs` is an ordinary directory and the mode will hold. Rather than claim a protection that cannot be
verified here, `test.sh` now probes the mount with `setpriv` and prints an explicit warning when the
artefacts are writable, stating that the reward is still taken from the exit status. That warning fires on
this machine and should not fire on a Linux host.

---

## 25. CROSS-ARCHITECTURE VALIDATION

| | arm64 (native) | amd64 (emulated) |
|---|---|---|
| runtime manifest | `runtime_manifest.aarch64.sha256`, 8,209 files, 4 loader-config entries | `runtime_manifest.x86_64.sha256`, 7,792 files, 4 loader-config entries |
| manifest verification | passes | passes |
| oracle reward | **1**, all six criteria | **1**, all six criteria |
| refusals | none | none |

The per-architecture selection in `test.sh` works: the verifier grades correctly on both, and refuses with
`no pinned runtime manifest for <arch>` on any architecture without one. The amd64 manifest was generated
under emulation on this machine, not on a native amd64 host, which remains the untested case (§35).

---

## 26. HARBOR ORACLE, NOP AND INCUMBENT

Real `harbor run`, not the local docker harness:

```bash
harbor run -p candidates/g50-courier-boost-rollout -a oracle -k 1 -n 1 -o jobs --job-name g50-v21-oracle -y
harbor run -p candidates/g50-courier-boost-rollout -a nop    -k 1 -n 1 -o jobs --job-name g50-v21-nop    -y
```

| agent | `reward.txt` | `reward.json` |
|---|---|---|
| `oracle` | **1** | `{"criterion_courier_supply_response": 1, "criterion_decision": 1, "criterion_evidence_reconstruction": 1, "criterion_quantitative_result": 1, "criterion_scientific_object": 1, "criterion_uncertainty": 1, "reward": 1}` |
| `nop` | **0** | `{"criterion_courier_supply_response": 0, "criterion_decision": 0, "criterion_evidence_reconstruction": 1, "criterion_quantitative_result": 0, "criterion_scientific_object": 0, "criterion_uncertainty": 0, "reward": 0}` |

Both completed with `rc=0`; artefacts in `jobs/g50-v21-oracle` and `jobs/g50-v21-nop`, logs in
`logs/g50-v21-oracle.log` and `logs/g50-v21-nop.log`. Criterion-level rewards reach Harbor intact, which is
what the flat `criterion_*` map in `reward.json` exists to do.

**`nop` is the incumbent.** Doing nothing leaves the shipped package in place, and the execution contract
means that is what gets re-run — so `nop` and a deliberate incumbent submission produce byte-identical
results, and the one criterion the incumbent earns is `evidence_reconstruction`. Its metric population,
market attribution, week grain and courier hours are all correct; what it gets wrong is the science.

Final verifier state, re-confirmed after the last hardening edit: **oracle 1, nop 0, zero refusals,
82.5 s wall clock for four worlds.**

---

## 27. HARBOR CHECK — NOT COMPLETED, AND WHY

`harbor check candidates/g50-courier-boost-rollout` could not run to completion here. Two attempts, two
different failures, neither of them a property of the task:

| attempt | failure | classification |
|---|---|---|
| first | `AgentSetupTimeoutError: Agent setup timed out after 360.0 seconds` | **environment** — up to seven containers were running at the time; sibling tasks in this repo need `agent_setup_timeout_multiplier: 3.0` on this machine, and `g08` carries an `__INVALID-agent-setup-timeout` job recording the same thing |
| second | the check's scaffold agent returned `Not logged in · Please run /login` | **environment** — `harbor check` drives a Claude Code agent, and this session has no interactive login for it |

Artefacts: `jobs/2026-09-30__00-00-44/check_report.json` and
`jobs/2026-09-30__01-25-19/check_report.json`.

**Classification: LIMITATION, not BLOCKING.** `harbor check` exercises the task through a scaffold agent,
which is a readiness signal about instructions and environment, not about the verifier. Everything it would
have tested about the verifier is covered directly: the real `harbor run` oracle and nop in §26, the 40-case
grading suite in §22, the 23-mutation suite in §21, the sandbox suite in §24, and the reproducibility pair
in §28. What remains genuinely untested is how a scaffolded agent experiences the instructions — which is
exactly what the first Gemini trial measures. **It must be run before G50 is treated as validated for
scaffold-agent use**, on an idle host with an authenticated agent.

---

## 28. REPRODUCIBILITY

**Generator determinism, measured across every run of this turn.** Each container run regenerates all four
worlds from the seeds in `world.VISIBLE_SPEC` and `tests/scenarios.py`, independently, in a fresh container.
Across **23 runs × 4 worlds = 92 independent regenerations**, the printed anchors take exactly four distinct
values — one per world — with no drift in any graded quantity:

```
visible   effect +2.0559  contrast -5.1189  courier  +2.8621  do_not_roll_out  orders 115424
hidden_a  effect -9.8437  contrast -6.4940  courier +24.3612  roll_out         orders 108418
hidden_b  effect +5.0671  contrast -4.3223  courier  +1.7561  do_not_roll_out  orders 121035
hidden_c  effect -9.3128  contrast -5.3917  courier +12.3240  roll_out         orders  89448
```

**Delete-and-rerun.** The verifier deletes the scratch `out/` directory before every world and requires each
produced file to be a regular file with an mtime at or after the run's start, so every graded number in
every run was produced by that run. This is not an add-on test; it is the only path through the verifier.

---

## 29. PROVENANCE OF THE VALIDATION RESULTS

Which artefact each number in §§20–27 came from, stated plainly because the verifier was edited during the
validation campaign.

- **`tests/test_boost.py` — the file that computes every criterion — was final before any result reported
  here was produced.** Its last change was the `boost_share` relaxation (§20), which preceded every route,
  mutation and attack run in the tables.
- **`tests/test.sh` changed twice afterwards**, both times in the refuse-to-grade preamble and never in the
  grading path: the shared-library and loader-configuration pinning (§12), and G50's own canary GUID (§31,
  D8). A run graded under the earlier preamble produces identical criteria, because `test_boost.py` is what
  grades. The final `test.sh` is nevertheless exercised end-to-end by `selftest_manifest` (reward 1, zero
  refusals), by `repro_a` and `repro_b` (§28), and by the Harbor runs in §27.
- **Three results predate the `boost_share` relaxation**: the first `oracle`, `nop` and `incumbent` runs.
  The relaxation is strictly weaker than what it replaced, so it cannot have changed a pass to a fail; and
  all three are re-established against the final artefact by `selftest_manifest` and by the Harbor
  `oracle` / `nop` runs in §27.
- **One result was discarded, not reported.** The very first `oracle` run failed `evidence_reconstruction`
  because of the latent-versus-recorded lateness bug in the verifier (§15). It is described in §15 and is
  not counted in any table.
- **One more result was superseded, not reported as evidence.** The first isolation probe
  (`A_probe_isolation`, reward 1) measured the agent phase rather than the verifier's re-execution, because
  of the harness flaw described in §24. Its reward carries no information and it is excluded from the §24
  table, which reports the corrected `A_probe_from_verifier` instead. `A_world_name_branching` was re-run
  under the corrected harness as `A_world_name_branching2`; both score 0.
- **Timings in §29 are from the uncontended runs only.** Up to seven containers ran concurrently on a
  2-CPU-per-container host during this campaign, and the contended wall-clock figures (up to 682 s) measure
  the host, not the verifier.

---

## 30. POST-VERIFIER LEAKAGE AUDIT

The final image was exported with `docker save` and **every one of its 13 layer blobs** was scanned, by
member name and by file content, for: `world.py`, `VISIBLE_SPEC`, `delta_accept_min`, `beta_supply`,
`eta_density`, `gamma_idle`, `hidden_a`, `hidden_b`, `hidden_c`, the three hidden seeds `730221`, `884413`,
`196077`, `rollout_effect_pp`, `late_all`, `late_none`, and `def truth`.

| result | |
|---|---|
| generator present in any layer | **NONE** — no `tmp/build`, no `build/world.py` member in any blob |
| scenario specs present | **NONE** |
| hidden seeds present in any author-written file | **NONE** |
| total pattern hits | 40, **all inside the pinned Python/numpy/pandas/scipy/statsmodels distribution** |

The 40 hits are coincidences in third-party code: `hidden_a` matches pandas' `_hidden_attrs`, `hidden_c`
matches a numpy f2py test fixture and pandas' Styler `hidden_columns`, `196077` / `730221` / `884413`
appear as digit runs inside statsmodels and scipy test-data CSVs, `late_all` matches statsmodels'
`simulate_all`, and `def truth` is in the standard library's `operator.py`. None is reachable as
information about G50.

The shipped workspace is exactly 25 entries — the 24 author-written files in the v2.1 manifest's
agent-visible groups plus the generated `data/northline.sqlite`. Nothing else.

Environment, configuration and metadata:

| surface | contents | leak |
|---|---|---|
| `Config.Env` | `PATH`, `LANG`, `GPG_KEY`, `PYTHON_VERSION`, `PYTHON_SHA256`, `DEBIAN_FRONTEND`, `PYTHONDONTWRITEBYTECODE`, `PYTHONPATH=/workspace` | none |
| `Config.Cmd` / `WorkingDir` | `["python3"]`, `/workspace` | none |
| image history | the `COPY --from=extract /workspace/` line names the stage but carries none of its contents | none |
| git metadata | no `.git`, no `.gitignore`, no VCS artefact anywhere in the image | none |
| `PATH` | the base image's, unmodified | none |

The multi-stage build is doing its job: the generator runs in the `extract` stage and only
`/workspace` is copied forward.

---

## 31. DOCUMENTATION DEFECTS FOUND IN FROZEN OR SIBLING FILES — REPORTED, NOT FIXED

§4 of the brief forbids changing the scientific world, and `task.toml` is covered by the v2.1 manifest,
so none of these was repaired. Each is documentation-only: no number, no decision and no agent-visible
fact depends on any of them.

| # | file | defect | impact |
|---|---|---|---|
| D1 | `HANDOFF_G50_V2_SCIENTIFIC_SPEC.md` §9 and the §19 table | quote the estimand over the phase-1 window; the frozen code, v2 §5 and the agent-visible memo all use the programme window | corrected by §14 of this handoff. Decisions identical either way. |
| D2 | `environment/build/world.py`, `truth()` docstring | says pre-programme weights are taken over "the three weeks BEFORE the programme"; the code uses `w_of < w["PW"]` = **four** weeks, which is what the memo specifies | comment only, agent-invisible (the generator is in no image layer). Code and memo agree; the docstring does not. |
| D3 | `environment/build/world.py`, `market_week_baseline` | the table's `late_orders` come from the latent lateness flag, so they differ from a recomputation over the same market-weeks by 10–14 orders in ~100,000 (§15) | an analyst cross-checking the baseline table finds a ~0.01 pp discrepancy. Cannot change a decision. |
| D4 | `task.toml` `difficulty_explanation` | says the phase-1 soak ran "three weeks"; `soak_weeks = 4` | author-facing metadata; `task.toml` is not in the image |
| D5 | `task.toml` `solution_explanation` step 4 | instructs computing `control_arm_vs_holdout_pp`, a field **removed** from the output contract in v2 | author-facing metadata; misleads a future reader of the solution sketch |
| D6 | `task.toml` `[environment]` | `network_mode = "public"` | the task needs no network. `none` would be tighter. Not a leak in itself — nothing secret is in the container — but it is an unnecessary surface |
| D7 | sibling tasks' `tests/runtime_manifest.sha256` | single-architecture, generated on whichever machine built them; the pinned base tag is a manifest list | **a P22-pattern verifier built on arm64 refuses to grade on an amd64 host.** G50 ships per-architecture manifests (§12). Out of scope here; needs a decision for the other tasks. |
| D8 | `tests/test.sh` canary GUID | G50 inherited P22's GUID when the file was seeded from it | given its own GUID this turn (`tests/test.sh` is verifier-only, not manifest-covered). Note that a canary in `test.sh` can never detect instruction leakage, because the agent never sees `test.sh`; `instruction.md` carries no canary line and is frozen. |

**None of D1–D8 is blocking.** D2, D4 and D5 are one-line comment edits if ChatGPT authorises a manifest
bump. D6 and D7 are policy questions. D3 would require regenerating the world and is not worth it.

---

## 32. RED TEAM — REVIEWER A: senior marketplace experimentation scientist

*Reviewing against the narrowed claim in §5, not against the v2 claim.*

**What I accept.** The scientific object is real and the trap is the right trap. A per-order incentive that
buys queue position in a shared dispatch queue measures redistribution, and the arm contrast is the correct
estimate of the wrong quantity. I have signed off analyses with this exact error. The phase-1 soak being
"the design the analyst rejected for being underpowered" is a true-to-life detail — that is how the
market-level evidence usually comes to exist and get ignored. The capacity check that cannot fail is the
best single piece of design here: it is exactly the reassurance an analyst produces to close the question.

**What I push back on.** The programme effect the verifier grades sits 3.35–9.39 pp from the arm contrast,
which is a very large gap. In a real marketplace the redistribution share is rarely that dominant. A model
could notice that the two numbers must differ a lot and search for *any* market-level estimator until the
gap appears, without ever representing why. §6 concedes this, and I want it stated in the report and not
only in the handoff.

**On courier supply.** Grading it is right — the supply response is the channel that actually survives
rollout — but `hidden_b` gives it almost no power. I would rather one world have no gradable supply
response at all and say so than have a criterion that passes on a 0.86 pp error against a 1.76 pp signal.

**Verdict: accept.** The narrowed claim is the claim the evidence supports.

## 33. RED TEAM — REVIEWER B: causal inference researcher

**The identification story is sound, and narrower than it first looks.** Phase 1 randomises at the market
level, which is the level the rollout counterfactual is defined at, so the on/off contrast identifies the
policy effect under between-market exchangeability. Phase 2 randomises within market, so it identifies a
conditional-on-others'-treatment contrast, which is not the policy effect when the treatment is rival.
That is a textbook unit-of-intervention problem and the task poses it honestly.

**Where I insist on precision.** The pre-period adjustment is **not** part of identification. Randomisation
already gives unbiasedness in expectation; with eight markets an arm the realised baseline imbalance is up
to 3.06 pp against a 1.4961 pp threshold, so the adjustment is a finite-sample accuracy correction. The
handoff says this (§19, mutation I) and the verifier is consistent with it — a one-week window passes. Good.
A verifier that *required* four weeks would have been claiming identification for a precision device.

**On R2.** §4 is the right answer and I am satisfied it is not a dodge. The mean-preserving priority
mechanism is what kills the curvature, and without curvature a linear dose-response extrapolation to full
treatment is not detectably wrong in this world. Note what this means: G50 cannot be cited as evidence
about extrapolation-through-interference at all. The handoff says so. Do not let that sentence get lost.

**One real concern.** The interval criterion requires the interval to contain the rollout effect with 0.5 pp
of slack. That is a coverage test on a single draw. A 95 % interval misses one time in twenty by
construction, and you are running four worlds, so the probability a *correct* procedure fails somewhere is
of order 1 − 0.95⁴ ≈ 19 % before the slack. The slack plus the generous width band reduce it, but it is
not zero, and a correct submission can fail G50 for being unlucky. The reference contains truth on 4 of 4,
which is reassuring but is one sample.

**Verdict: accept, with the coverage caveat recorded as a limitation.**

## 34. RED TEAM — REVIEWER C: benchmark / verifier engineer

**The hard parts are done properly.** Re-execution against privately regenerated worlds is the only
construction that makes "correct JSON plus unrelated code" fail, and it is implemented without a loophole
I can find: `out/` never travels, `/workspace` is closed to the pipeline user, the scratch output directory
is deleted, produced files must post-date the run, and the scratch directories are named `r0`…`r3` inside
an opaque `mkdtemp` root so there is nothing to branch on. Hashing `site-packages` and then exposing it
via `--system-site-packages` is the right trade and is better than the pattern it was copied from. Pinning
the `ldd` closure and `ld.so.cache` closes the subversion path that the sibling tasks leave open.

**Bugs I would have caught in review, and the author caught first.** The latent-versus-recorded lateness
bug (§15) is the kind of thing that ships and then fails every legitimate submission on one criterion; it
was found by the oracle failing, which is the right way round. The `boost_share` ambiguity (§20) is the
same class and was handled by weakening the rule to what both conventions agree on rather than by picking
one and hoping.

**What I still do not like.**

1. **The bootstrap limit.** The manifest is verified by `sha256sum`, which the manifest also covers, using
   a `libc` the manifest also covers. An agent with root in the episode that could rewrite both
   consistently would defeat the check. Pinning the library closure raises the bar a lot; it does not
   remove the circularity. No container-internal verifier can.
2. **Wall-clock.** Four world builds plus four pipeline runs is 60–100 s of CPU, and the generator
   simulates each world three times (factual, all-treated, none-treated). Under a loaded Harbor host this
   is the slowest verifier in the set.
3. **The amd64 manifest is generated under emulation** on this machine, not on a native amd64 host. It is
   validated by an emulated run, which exercises the same code path, but a native host is the real test.

**Verdict: accept.** The verifier grades what it claims to grade and nothing it cannot observe.

---

## 35. ALL REMAINING LIMITATIONS

Ordered by how much they constrain what G50 can be cited for.

1. **G50 does not grade reasoning.** Six criteria, all computed from eight numbers and a panel. A model that
   reaches the right object by search rather than by causal argument gets the same 1. §6 is the operative
   list of what reward does not evidence.
2. **R2, post-treatment weights and a one-week pre-window are not discriminated.** §4 and §19. The first of
   these means G50 provides **no** evidence about extrapolation through an interference region.
3. **Interval coverage is a probabilistic criterion.** A correct procedure whose 95 % interval happens to
   miss on one of four worlds fails `uncertainty`. The 0.5 pp slack and the wide [2.0, 25.0] band reduce the
   risk but do not remove it. Measured: 16 of 16 interval-world combinations across the four accepted
   difference-in-differences routes contained the rollout effect.
4. **`courier_supply_response` is nearly powerless on `hidden_b`.** True response +1.756 pp, tolerance
   ±1.200 pp. §18. It is carried by the cross-world conjunction, not by that world.
5. **Omitting the pre-period adjustment is not rejected on every world.** `P_ow` fails on 2 of 4 and `P_mu`
   on 1 of 4. The suite rejects them; a single-world version of G50 would not.
6. **The raw arm contrast separates by 2.55x, not 3x.** §17. Retired heuristic, reported measurement.
7. **One `boost_share` convention cannot be distinguished from the other.** §20. Two defensible sources
   exist for phase-1 market-weeks and the output contract does not disambiguate them, so the panel rule was
   weakened to what both agree on.
8. **The verifier's integrity check is circular at the root.** §34, item 1.
9. **The amd64 runtime manifest was generated under emulation.** Validated by an emulated run; a native
   amd64 host is the untested case.
10. **The world is synthetic and the mechanism is imposed.** Mean-preserving priority in a single
    market-hour queue is a modelling choice, not a measured property of any real marketplace. Everything
    G50 concludes is conditional on it.
11. **Runtime is the highest in the candidate set.** §29.
12. **Eight documentation defects remain unfixed**, six of them in manifest-covered or sibling files. §31.
13. **`M_threshold_ignored` passes: the break-even threshold is never binding.** G50 tests the sign of the
    effect, not the £0.19 ÷ £12.70 arithmetic, and the interval-excludes-zero clause is never binding either.
    §21. A calibrated fifth world is the remedy and needs authorisation.
14. **`M_holdout_as_control` passes: a non-randomised comparison group is accepted.** §20.
15. **`harbor check` was never completed**, for environment reasons (host load, then a missing agent login).
    The scaffold-agent experience of the instructions is therefore untested. §27.
16. **The graded artefacts under `/logs/verifier` are writable by the pipeline user on a mode-ignoring bind
    mount.** Not exploitable for reward — verified, not argued — and `test.sh` now both hardens the directory
    and prints an explicit warning when the mount defeats the hardening. §24.
17. **One mutation in the suite is vacuous.** `M_excluded_in_control` changes nothing, so the suite is
    effectively 22 mutations, not 23. §21.

---

## 36. FINAL FREEZE MANIFEST

Five independent hash groups, so that a later reader can tell which kind of change a digest shift
represents. Group A changing means the model sees something different. Group B changing means the science
changed. Group C changing means only the grading changed. Group E is the whole task.

# G50 v2.1 FINAL FREEZE MANIFEST
# generated 2026-09-30 · five independent hash groups

### A. TARGET-VISIBLE (what the model sees)   (19 files)
f150e537679965cc38dd1dc911c082aa0c883c92b24885fc87e15f2c3b3a2a79  candidates/g50-courier-boost-rollout/environment/workspace/README.md
d7152b2cc2d0da0ac3eb738858dfb98b63323446d88e443f4a5277450ed2ae03  candidates/g50-courier-boost-rollout/environment/workspace/docs/boost_programme_brief.md
74ed72e23742fb5dab969eaf307fb76022f1268be9ae38448b34e8a51ba42748  candidates/g50-courier-boost-rollout/environment/workspace/docs/courier_supply_note.md
5770c95e6c57bd4b4f7c80dfa98a82224f7e45286f12c93b235697d9771f342b  candidates/g50-courier-boost-rollout/environment/workspace/docs/data_dictionary.md
2a308b9b8ae50a22e932da5bf6a272b4581f131952bff75bd0d542dba7325d3e  candidates/g50-courier-boost-rollout/environment/workspace/docs/dispatch_offer_queue.md
58dee9e89641d5ef89bae5152372e0284f759c5cc9d3495dfa501795837d1869  candidates/g50-courier-boost-rollout/environment/workspace/docs/experiment_plan.md
5407b056a8110ca341db45b7f66fdbc93d51890e468f6228fc4d10900344677f  candidates/g50-courier-boost-rollout/environment/workspace/docs/metric_definitions.md
b87b6291c351a274a7399a7b95ff46696c907ccbeb90a645f5afeeb7b8002cfd  candidates/g50-courier-boost-rollout/environment/workspace/docs/outputs/readout_contract.md
85be2630e8ed239ad77202649abc4a28a73b2548a2f5c54c721498dea8bdb8a0  candidates/g50-courier-boost-rollout/environment/workspace/docs/rollout_decision_memo.md
2d8d61cc7c9769bcd3e9943f926c00fe34d0f20b50ee3485095746e74d6f81ec  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/__init__.py
692ea27ba2cca6aeb886ef6a7b9432f06df5dfb74635e9352245d9947754d466  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/__main__.py
453404d0f0c911a2c4f1fee3f02f1d40d163d7e63a5da69b43afe3cdbc2927c5  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/cli.py
6e9027e35e1c9f6392ddfb5a6925a19dd8c47e3421ce71f002d0f14ceae9596a  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/effects.py
80f11a81f021cbc3c4d54569cad117dee4c3e36a7290f13e1ef1cf7c71181b58  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/panel.py
01cf1a50ab5b332a8ef3cea4c02283e1700d2b330125b04e3bff005b82928b60  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/report.py
6b70102d2a2aa26d102a29ab1a5ae0caa0a71ffef74c930137284a17a479e2b3  candidates/g50-courier-boost-rollout/environment/workspace/northline_eval/warehouse.py
2e2cb61038550cd9c67ad6905827c97d41b77c530b643840ec22dc2392d86e6f  candidates/g50-courier-boost-rollout/environment/workspace/notebooks/analyst_note.md
ed2721773b93eda6fa381edaeda57db4dc28ee4d3db8e6834d94e340137cccbb  candidates/g50-courier-boost-rollout/environment/workspace/reports/boost_readout_2026-06.md
6a9ebdd6246b9a56b197a92df27eced4005989152c85a257f86f61e6ca5909da  candidates/g50-courier-boost-rollout/instruction.md
AGGREGATE A: ba92e8ccdcecdb58   files=19

### B. GENERATOR AND SCENARIO SPECS (never in the image)   (3 files)
9f8e76a0ddc1153fcf19a4af9d54ad07b675000b61a332e35f4a6143e4d35a3e  candidates/g50-courier-boost-rollout/environment/build/world.py
69191a9be6d0eb85315ac293a4b95812c944c32a49022a3805e5020c923942fa  candidates/g50-courier-boost-rollout/tests/scenarios.py
9f8e76a0ddc1153fcf19a4af9d54ad07b675000b61a332e35f4a6143e4d35a3e  candidates/g50-courier-boost-rollout/tests/world.py
AGGREGATE B: 808fc7a1729c5f06   files=3

### C. VERIFIER-ONLY   (11 files)
d1a5d8e07f4473fd0cd4b43fafa78fdfadbe7f62e29db8bf8c9dcf1500dfd3a1  candidates/g50-courier-boost-rollout/tests/runtime_manifest.aarch64.sha256
aceb3d8947ab63e96fa1ecd97c908c618e999d4ef20f0db37728ae0f019b4b82  candidates/g50-courier-boost-rollout/tests/runtime_manifest.x86_64.sha256
2ff5d405af27aee20b55478f7ebc1085630fea8e99d9214eba23821184504e2a  candidates/g50-courier-boost-rollout/tests/test.sh
0c90168965641713d5fb1cc5541f87f92001816abae952795f48d3953425171d  candidates/g50-courier-boost-rollout/tests/test_boost.py
f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12  candidates/g50-courier-boost-rollout/tests/wheels/iniconfig-2.3.0-py3-none-any.whl
d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c  candidates/g50-courier-boost-rollout/tests/wheels/packaging-26.3-py3-none-any.whl
e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746  candidates/g50-courier-boost-rollout/tests/wheels/pluggy-1.6.0-py3-none-any.whl
2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9  candidates/g50-courier-boost-rollout/tests/wheels/pygments-2.21.0-py3-none-any.whl
539c70ba6fcead8e78eebbf1115e8b589e7565830d7d006a8723f19ac8a0afb7  candidates/g50-courier-boost-rollout/tests/wheels/pytest-8.4.1-py3-none-any.whl
e82fd1d69be2f92385bc33540063e5ad7b17b36de67764c84f3ceb9815a895e9  candidates/g50-courier-boost-rollout/tests/wheels/pytest_json_ctrf-0.3.5-py3-none-any.whl
bac688aaeaa13c4f22f1f2220b23c63d19eaa86f3d682eddf26793298815630d  candidates/g50-courier-boost-rollout/tests/wheels/requirements.txt
AGGREGATE C: 73c9c754ce7d2303   files=11

### D. ORACLE / REFERENCE   (3 files)
9f06eae8cba92abe68f1f1dd850d8e3d9eeb4a29404abe65f6ce09d84af6d863  candidates/g50-courier-boost-rollout/solution/northline_eval/effects.py
dec94dc2de1de1233154782a4457fec770801496866ecc02ce546c171017d5bc  candidates/g50-courier-boost-rollout/solution/northline_eval/report.py
7d2d5c31ba43a9fdbc3831a1e823e7b1e670babd9bc77037b22aed5cb45e932a  candidates/g50-courier-boost-rollout/solution/solve.sh
AGGREGATE D: 23a5fa730ee9dacc   files=3

### E. COMPLETE TASK   (41 files)
AGGREGATE E: ff5f17c9caf70107   files=41

---

## 37. TARGET EXPOSURE STATUS

**ZERO. No target model has ever seen G50.** No Gemini, no `google/gemini-3-flash-preview`, no other target
model. `harbor run` was invoked only with the `oracle` and `nop` built-in agents, which execute a shell
script and nothing respectively; `harbor check` runs its own scaffold agent and is reported in §33 with its
result. Nothing in this turn consulted any target model's behaviour, and no trial artefact from this turn
contains a model completion.

## 38. EXACT GEMINI COMMANDS — PRINTED, NOT EXECUTED

The verdict is READY under the narrowed claim, so these are printed as the brief authorises. **They have
not been run.**

```bash
harbor run -p candidates/g50-courier-boost-rollout -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name g50-gemini3flash-baseline-1 -y
```

```bash
harbor run -p candidates/g50-courier-boost-rollout -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name g50-gemini3flash-baseline-2 -y
```

```bash
harbor run -p candidates/g50-courier-boost-rollout -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name g50-gemini3flash-baseline-3 -y
```

Notes for whoever runs them:

- Sibling tasks in this repo needed `agent_setup_timeout_multiplier: 3.0` on this machine; `g08` has an
  `__INVALID-agent-setup-timeout` job recording what happens without it, and `harbor check` timed out at
  360 s during this turn purely from host load. Set the multiplier or run on an idle host.
- The verifier takes **87 s** uncontended for four worlds and the task allows 5400 s, so verifier time is
  not the constraint; agent setup is.
- Run them **one at a time.** Concurrency on this machine is what produced every timeout observed this turn.
- **`-k 1 -n 1` per command, three separate job names.** Three independent single trials, not `-k 3`, so
  that one crashed trial does not contaminate the other two.

## 39. FINAL VERDICT AND CHATGPT DECISION PACKET

### Verdict

**READY — under the narrowed capability claim in §5, and with three limitations that are ChatGPT's to accept
or remedy.** Both stop conditions are resolved. The verifier exists, re-executes, is deterministic, and
cannot be defeated by any of the 63 adversarial submissions tried. What it grades is narrower than v2
claimed, and §§5–6 say exactly how much narrower.

Not blocking, but on the record: G50 does not test the break-even threshold (§21), it treats a one-week
pre-period arbitrarily (§4), and it accepts a non-randomised comparison group (§20). None of these is a
plumbing defect; each is a limit on what a reward of 1 evidences, and each is already inside the §5/§6
boundary.

### Decision packet

1. **Did the v2 manifest reproduce before the edit?** Yes — 28/28, `0dbc9470ed483848`, zero drift.
2. **Was exactly one frozen file changed?** Yes — `instruction.md`, `2436e051…` → `6a9ebdd6…`. The other 27
   are byte-identical. New digest `e4b4ea294a032dda`.
3. **Does the B1 sentence prescribe any science?** No. It names the command, permits rewriting behind it,
   and requires the outputs to come from it. §2 sets out what it establishes and what it withholds.
4. **Was the command verified against the frozen package first?** Yes — `__main__.py` → `cli.py` accepts
   `readout --db --out`, and `solution/solve.sh` already invoked that exact string.
5. **What does the verifier grade?** Six criteria, all from observable output: evidence reconstruction,
   scientific object, quantitative result, uncertainty, courier supply response, decision. §10.
6. **Is there an `identification` criterion?** No — folded into `uncertainty`. The final state contains no
   field that evidences identification, and inventing one would have been a relabelling. §11.
7. **Does any model judge anything?** No. Every criterion is a numeric or string comparison against a
   generator-computed quantity.
8. **Does it re-execute the submitted procedure?** Yes, four times per grading, against privately
   regenerated worlds. §9, §23.
9. **Can hardcoded JSON plus unrelated code pass?** No. `M_hardcode_visible` = 0 on all six criteria on all
   four worlds. `M_hardcode_literal` = 0, passing `visible` alone.
10. **Can stale outputs pass?** No. `M_stale_outputs_only` = 0 everywhere.
11. **Can a submission branch on which world it is in?** Not from anything the verifier exposes:
    the re-execution runs as uid 65534 in an opaquely named
    scratch directory whose parent is not listable, with `/tests`, `/workspace` and the original outputs all
    returning `PermissionError`, and no environment variable naming a world. Measured from inside the
    re-execution itself (§24). `A_world_name_branching` scores 0.
12. **Can pseudoreplicated uncertainty pass?** No. `M_order_level_se`, `M_order_count_as_unit` and
    `M_market_week_as_unit` each score 0, failing `uncertainty` alone and passing the other five — the
    criterion is doing precisely its own job and nothing else's.
13. **Can right-decision-wrong-science pass?** No. `M_right_decision_wrong_quantity` scores 0: it earns
    `decision` and `courier_supply_response`, and fails `scientific_object`, `quantitative_result` and
    `uncertainty` on all four worlds.
14. **Can R2 pass?** **Yes — confirmed through the real verifier, 1 on all four worlds.** §4 states the
    reason precisely and confines the claim: G50 cannot distinguish R2 here, and provides no evidence about
    extrapolation through interference.
15. **Can post-treatment weighting pass?** Yes, `H_post` = 1. 0.814 pp max against the reference's 0.811.
16. **Can a one-week pre-period pass?** **It depends which week, and that is the finding.** Weeks 0 and 1
    pass; weeks 2 and 3 fail. §4. Neither v2's "must fail" nor B2's "accept" describes the behaviour.
17. **Which legitimate alternatives pass?** All four intended difference-in-differences routes — `D_ow`
    (reference), `D_panel`, `D_pool`, `D_mu` — plus `H_post` and `R2`. §20.
18. **Did every mutation behave as intended?** No. **21 of 23 rejected.** `M_threshold_ignored` passes and is
    a real gap (§21). `M_excluded_in_control` passes but is a vacuous mutation that changes nothing, and is
    reported as invalid rather than as a miss.
19. **Did every verifier attack behave as intended?** Yes. 40 malformed-output cases through the grading
    function: zero mismatches, the only passes being four deliberate just-inside-the-boundary probes.
    Five sandbox attacks through the container: all 0, including a symlinked
    `readout.json`, a symlinked `out/`, a background thread rewriting the output after the run, and an
    `/etc/ld.so.preload` written as root during the agent phase — which triggers the refuse-to-grade path.
    One real finding, now hardened and honestly reported: the graded artefacts under `/logs/verifier` were
    writable by the pipeline user. Forging them does not change the reward (verified: a submission wrote `1`
    into `reward.txt` and was recorded as `0`), because the reward comes from pytest's exit status. §24.
20. **Oracle, nop, incumbent rewards?** Real `harbor run`: **oracle 1, nop 0**, both with full
    criterion-level `reward.json`. `nop` *is* the incumbent under the execution contract, and a separate
    incumbent submission gives byte-identical results. Re-confirmed after the final hardening edit:
    oracle 1, nop 0, 82.5 s, zero refusals. §26.
21. **What does the incumbent earn and lose?** It earns `evidence_reconstruction` on all four worlds — its
    metric population, market attribution, week grain and courier hours are all correct — and loses the
    other five. It fails for scientific reasons, not plumbing. `nop` is byte-identical to `incumbent`,
    because doing nothing leaves the incumbent package to be re-run, which is the execution contract
    working as intended.
22. **Harbor check outcome?** **Not completed, and classified LIMITATION rather than BLOCKING.**
    Two attempts failed for environment reasons — a 360 s agent-setup timeout under host load, then
    `Not logged in · Please run /login` from the check's scaffold agent. Neither is a property of the task,
    and everything `harbor check` would test about the verifier is covered directly elsewhere. What stays
    untested is the scaffold-agent experience of the instructions. §27.
23. **Is the verifier deterministic?** Yes. 92 independent world regenerations across 23 container runs
    produced four distinct anchor sets and no drift. §28.
24. **Total verifier runtime?** **87 s** for four worlds, uncontended, against a 5400 s allowance. Every
    longer figure observed this turn was host contention from running up to seven containers at once.
25. **Any leakage?** None. 13 layer blobs scanned by name and content: no generator, no scenario specs, no
    hidden seeds. All 40 pattern hits are coincidences inside the pinned third-party distribution. §30.
26. **Any hidden simulator assumption required of the agent?** No — the market-level route is recoverable
    from the dispatch note, `experiment_config` and the visible baseline spread. But the converse remains
    the live issue: several procedures that do **not** follow that route reach the same number (R2, H_post,
    `M_holdout_as_control`), which is why §§5–6 exist.
27. **Any verifier overfitting?** No evidence of it — all four intended routes pass, and the tolerance was
    fixed by a stated rule before the mutation suite ran and **deliberately not moved afterwards** (§16).
    The opposite pressure is the real one: the verifier cannot be made more selective without either
    changing the world or failing legitimate procedures.

### Decisions requested, in priority order

**1. The break-even threshold (§21). Recommended: add a fifth world.** `tests/scenarios.py` gains one spec
whose rollout effect lands in [−0.35, −0.10] pp. That is the only band where the threshold binds while every
accepted route still reaches the memo answer, and it also makes the interval-excludes-zero clause binding
for the first time. Cost: a manifest bump, a recalibration pass, and roughly 22 s more verifier time.
Requires your authorisation because `scenarios.py` is on §4's protected list. **Declining is defensible** —
the limitation is recorded either way, and the threshold is business arithmetic rather than the causal
content the task is about.

**2. The tolerance (§16). Recommended: leave it at 1.303.** Any value in (1.658, 3.301) is admissible. 1.75
would admit all four one-week windows at no cost to any other rejection; 1.303 preserves 2.57x separation
from the naive arm contrast, which is the criterion carrying the benchmark's claim. I have left it where the
pre-registered rule put it. **One number from you changes it.**

**3. `M_holdout_as_control` (§20). Recommended: accept as a limitation.** Using the never-enrolled markets as
the comparison group is a weaker warrant that this world does not punish. Making it fail would mean giving
the holdout markets a different trend, which is a change to the DGP.

**4. Documentation defects D1–D8 (§31).** D2, D4 and D5 are one-line comment fixes behind a manifest bump.
D6 (`network_mode = "public"` → `"none"`) is a one-line hardening. **D7 is the one I would act on
independently of G50**: the sibling tasks' single-architecture runtime manifests mean a verifier built on
arm64 refuses to grade on an amd64 host, which would silently score those tasks 0.

**5. Gemini.** §38 prints the three commands. My recommendation is to **run them only after deciding item 1**,
because a fifth world changes what the first measurement measures, and G50 has exactly one clean
pre-exposure baseline to spend.
