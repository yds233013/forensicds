# G05 Gemini 3 Flash baseline: results and trajectory analysis

**Task:** `candidates/g05-sco-rollout-gate/`, frozen at checksum `77a6e432d9d2cba2` (Harbor task checksum
`56c1d86ea2ca9df1d0581ce67400347f9c1ecf16499c9da679bc636bc140510b`, identical in all three trial records).

**Run:** `g05-gemini3flash-baseline-1`, 2026-09-18 02:44:29–03:05:35 PDT (21m 05s wall clock), Harbor 0.21.0,
`gemini-cli` / `google/gemini-3-flash-preview`, `-k 3 -n 3`, `--agent-setup-timeout-multiplier 3`.

> **STATUS: COMPLETE. See §14 for the final baseline.** Baseline collection on G05 is finished; no further Gemini
> run will be made on this task. The official quantitative baseline is the three **valid** trials
> `MMGNYFS`, `PYhR2eh`, `rsDKTXQ`. `JnK5hsR` is excluded quantitatively (invalid infrastructure trial) and survives
> as labelled qualitative evidence only. Sections 1–13 below are the original record of the **first run** and are
> retained unedited, including their "0/3" phrasing, which at the time counted `JnK5hsR`. Read §14 for the corrected
> figures and the full chronology.

**Headline (as written before adjudication, first run only): 0 successes. Empirical success rate 0/3 (2/2 among
unambiguously valid trials). pass@3 = 0.**

**The task was not modified before, during or after this run.** No tuning against model behaviour. One trial's
verifier did not execute and is reported as **apparently invalid**; no replacement was launched.

---

## 0. Pre-baseline predictions vs observed results

Kept separate, as required. Predictions are from `report/g05_prebaseline_validation.md` and
`research/g05/G05_phase0_gate.md`, written before any model saw the task.

| # | Pre-baseline prediction | Observed | Verdict |
|---|---|---|---|
| P1 | The basket-size outcome error is the primary attractor; agents will anchor on +8.0%/+5.5% | **All three switched to net sales within ~2 minutes.** Nobody anchored on basket size | **WRONG** |
| P2 | Static TWFE on net sales (+6.7%, the FP&A number) is the second attractor | **All three kept the house TWFE family** but re-specified the treatment window, so they did not reproduce +6.7% either | **PARTLY RIGHT** (mechanism right, number not reproduced) |
| P3 | The population/transport step (installed estate → waves 5–6 kit mix) is the hardest step | **All three did it correctly**, and unprompted | **WRONG** |
| P4 | Planned vs actual go-live will trip agents up | **All three used the install log.** The panel passed on all four extracts | **WRONG** |
| P5 | Install-closure comparability will trip agents up | **All three used `store_closures`.** Panel passed | **WRONG** |
| P6 | Agents will not perform available falsification | **Confirmed: zero pre-trend, placebo or negative-control checks in any trial** | **RIGHT** |
| P7 | Decision-only grading would be insufficient; F10 cases exist | **Confirmed: PYhR2eh got the decision right with every effect out of tolerance** | **RIGHT** |
| P8 | Grading the panel below the decision is necessary to separate | **Inverted: the panel was the easy part and passed everywhere; the estimator separated** | **WRONG, but the grader still worked** |

**The task is hard for a reason we did not predict.** We expected failure at *state reconstruction* (timing,
eligibility, population). Failure occurred at *identification* — specifically the conditioning set — while state
reconstruction succeeded completely.

---

## 1. Raw results

| | `JnK5hsR` | `MMGNYFS` | `PYhR2eh` |
|---|---|---|---|
| Reward | **0** | **0** | **0** |
| Valid? | **APPARENTLY INVALID** (§2) | **VALID** | **VALID** |
| Total trial wall clock | 16m 16s | 19m 53s | 21m 05s |
| Environment setup | 63 s | 77 s | 43 s |
| Agent setup (Node + gemini-cli) | 10m 54s | 10m 37s | 11m 14s |
| **Agent execution** | **3m 46s** | **4m 26s** | **4m 59s** |
| Verifier | **2.18 s (did not execute)** | 2m 56s (pytest 150.98 s) | 3m 40s (pytest 190.23 s) |
| Cost | $0.10997395 | $0.15518505 | $0.15248315 |
| Input tokens | 497,702 | 863,178 | 766,705 |
| Cached tokens | 401,069 | 733,231 | 619,123 |
| Output tokens | 13,868 | 17,850 | 15,912 |
| Trajectory steps (Harbor) | 42 | 64 | 66 |
| Tool calls | 38 | 42 | 38 |
| — of which shell | 10 | 19 | 19 |
| Files inspected | 10 | 10 | 11 |
| Files modified | 9 (4 pipeline + 5 scratch) | 3 (pipeline) | 3 (pipeline) |
| Termination | completed, final summary written | completed, final summary written | completed, final summary written |
| Exception | none | none | none |

**Empirical success rate over three trials: 0/3.** Among the two trials whose verifier executed: 0/2.
**pass@3 = 0** (Harbor also reports pass@2 = 0.000). This is *not* an exact pass@1 estimate.

**Cost:** Gemini baseline total **$0.41764215** (sum of the three trials). Reported separately from the
**validation** spend of $0.52425255 (`harbor check`, claude-sonnet-4-6) — see `research/harbor_check_protocol.md`.

### Verifier outcomes

| Check | `MMGNYFS` | `PYhR2eh` |
|---|---|---|
| `test_warehouse_unmodified` | pass | pass |
| `test_gate_succeeds` | pass | pass |
| `test_run_time` | pass | pass |
| **`test_analysis_panel`** | **pass** | **pass** |
| `test_rerun_is_deterministic` | pass | pass |
| **`test_hidden_panel` (a, b, c)** | **pass ×3** | **pass ×3** |
| `test_effects` | **fail** | **fail** |
| `test_intervals` | **fail** | **fail** |
| `test_decision` | **fail** | **pass** |
| `test_hidden_effects_and_decision` (a, b, c) | **fail ×3** | **fail ×3** |
| Totals | 6 failed / 8 passed | 5 failed / 9 passed |

**Both graded trials reconstructed the analysis panel exactly — on the visible extract and on all three hidden
extracts.** Actual go-live week, event-week origin, comparability and log net sales all byte-correct. Every failure
is in the estimated effects.

### Outputs vs truth (visible extract; per-extract tolerances)

Truth: wave 1 **0.04061**, wave 2 **0.03427**, wave 3 **0.03087**, wave 4 **0.01906**, gate **0.01065**,
decision **stop**. Visible τ: wave 1 0.00659, wave 2 0.00724, wave 3 0.00515, wave 4 0.00683, gate 0.00456.

| Quantity | `JnK5hsR` | `MMGNYFS` | `PYhR2eh` |
|---|---|---|---|
| wave 1 | 0.0388 | 0.0719 | 0.0906 (err 0.05003 = **7.6 τ**) |
| wave 2 | 0.0279 | 0.0675 | 0.0722 (err 0.03788 = **5.2 τ**) |
| wave 3 | 0.0133 | 0.0543 | 0.0570 (err 0.02610 = **5.1 τ**) |
| wave 4 | −0.0095 | 0.0287 | 0.0297 (err 0.01060 = **1.6 τ**) |
| **gate** | **−0.0117** | **0.0268** | **0.0157** (err 0.00509 = **1.12 τ**) |
| decision | **stop** ✓ | **continue** ✗ | **stop** ✓ |
| kit effects (full / compact) | 0.0339 / −0.0304 | 0.0717 / 0.0083 | 0.0844 / −0.0125 |

Truth kit effects ≈ **+0.043 full / −0.003 compact**.

**Three runs of the same model on the same frozen extract produced gate figures of −1.17%, +1.57% and +2.68% —
spanning the 2.5% hurdle, and flipping the business decision between trials.** Run-to-run variance is larger than
the distance between the truth and the hurdle. That is the single most striking measurement in this baseline.

---

## 2. Trial `JnK5hsR`: apparently invalid, reported not replaced

**The agent completed normally.** It read 10 files, edited all four pipeline modules, ran the pipeline twice,
produced `out/analysis_panel.csv` (6.9 MB) and `out/readout.json`, ran two side analyses, cleaned up its scratch
scripts and delivered a final recommendation ("STOP", gate −1.17%).

**The verifier then produced nothing.** Evidence:

| Observation | `JnK5hsR` | other two |
|---|---|---|
| Verifier duration | **2.18 s** | 176 s / 220 s |
| `verifier/test-stdout.txt` | **0 bytes** | 15,525 / 13,588 bytes |
| `verifier/ctrf.json` | **absent** | present |
| Tests collected | **none** | 14 |
| `reward.txt` | `0` | `0` |

`tests/test.sh` writes `echo 0 > /logs/verifier/reward.txt` as its second statement and every refusal path echoes a
`verifier: …; refusing to grade` line to **stdout**. Stdout is empty, so no refusal was reached and no test ran: the
script died between its first statement and any output.

**What was ruled out.** The trajectory contains no `pip install`, no `pytest.ini`/`conftest.py`/`pyproject.toml`,
no `.pth`, no site-packages or stdlib writes, and no pip config. The only files the agent touched outside
`sco_readout/` were five scratch `.py` files in `/workspace`, which it deleted itself. The warehouse was not
modified. So this is not a tamper case caught by the hardened verifier — a tamper would have printed a refusal line.

**Most plausible mechanism, stated as a hypothesis, not a finding.** `test.sh`'s third block kills every process
that started after container init and before the verifier's own exec chain. The agent's shell commands ran in their
own process groups (PGIDs 1825–1901 in the trajectory), and some may have outlived the session. This is the same
class of interaction as the G24 incident, where the sweep killed Harbor's container main command and produced
reward 0 in 0.8 s; that was fixed by sparing init-era processes (`TBOOT`), but the fix protects PID-1-era processes,
not Harbor's later exec plumbing. **I did not reproduce it, and no re-run was performed.**

**Classification under the stated rule.** "Verifier unable to execute for infrastructure reasons" → **invalid**.
But the cause may be a verifier/harness interaction belonging to the task, which would make it **F8** rather than
neutral infrastructure. Both readings are recorded; adjudication is the maintainer's.

**Its substantive outcome is nevertheless determinate.** Grading its own `readout.json` offline against the frozen
truth: gate −0.01166 vs 0.01065 → error 0.02231 = **4.9 τ**; wave 4 −0.0095 vs 0.01906 → error 0.02852 = **4.2 τ**;
wave 3 error 0.01758 = **3.4 τ**. It would have scored **0**. The invalidity concerns the measurement's status, not
the outcome.

**No fourth trial was launched.**

---

## 3. Reasoning chronology (stages 1–12)

✓ = done correctly, ~ = partially, ✗ = not done or wrong.

| Stage | `JnK5hsR` | `MMGNYFS` | `PYhR2eh` |
|---|---|---|---|
| 1 Incident recognition | ~ read the conflict in the prompt; only PYhR2eh opened the programme readout and FP&A notebook | ~ | ✓ |
| 2 **Outcome: net sales not basket** | **✓** (msg 20) | **✓** (msg 33) | **✓** (msg 17) |
| 3 **Actual vs planned go-live** | **✓** `install_log WHERE event='go_live'` | **✓** (also verified 536/536 kit match) | **✓** (explicitly checked 536 planned = 536 live) |
| 4 **Event time / comparability** | ✓ closures → non-comparable (plus `txns>0`) | **✓** closures only | **✓** closures only |
| 5 Staggered adoption / forbidden comparisons | ✗ kept static TWFE; added ramp dummy only | ✗ same | ✗ same |
| 6 **Conditioning: format** | **✗ never considered** | **✗ never considered** | **✗ never considered** |
| 7 **Treatment version: full vs compact kit** | **✓** | **✓** | **✓** |
| 8 **Population: installed ≠ waves 5–6** | **✓** explicit | **✓** explicit | **✓** explicit |
| 9 **Transport by kit mix** | **✓** 0.709·compact + 0.291·full | **✓** 258/106 weights | **✓** same |
| 10 Run-rate window e ∈ [12,25] | ✓ | ✓ | ✓ |
| 11 Uncertainty | ~ store-clustered sandwich SE, delta-method for the gate; **intervals failed** | ~ same | ~ same |
| 12 Business decision vs 2.5% hurdle | ✓ (stop) | ✓ rule applied; **wrong input** → continue | ✓ (stop) |

**Stages 2, 3, 4, 7, 8, 9, 10 — seven of twelve, including every one we expected to be hard — were passed by all
three trials.** Stage 6 was failed by all three, identically, and that single omission produced every numerical
failure.

### The shared error, precisely

All three fit **store fixed effects + calendar-week fixed effects** (the house `_demean` routine), with dummies for
ramp / run-rate / post periods, and estimated kit effects as interactions. None conditioned on **format**.

Waves were sequenced by format, and untreated formats trend differently (Supercentre +6.0%/yr, Market +1.0%,
Neighbourhood −1.0%). With only store + week effects, the treated-wave indicator absorbs the differential format
trend, which inflates every wave effect and both kit effects. This is exactly the wrong analysis recorded in the
Phase-0 panel as `imp_unconditional` — rejected there at a minimum ratio of **4.57 τ**, against ≤ 0.54 τ for the
format-conditional accepted estimator.

**Not one of the three read `docs/store_ops/wave_sequencing_2024-11.md`** — the document that states the sequencing
rule. None read `docs/programmes/sco2_programme_brief.md` or the `notes/` directory either.

---

## 4. Attractor behaviour

| Attractor | Encounter | Believed? | Challenged? | Returned to? |
|---|---|---|---|---|
| **A. Programme +8.0% / +5.5% basket, continue** | JnK5hsR: never opened the report, inferred from `cli.py`'s `outcome="log_basket"`. MMGNYFS: same. PYhR2eh: read the report at msg 87 (**after** its answer) | **No** — all three rejected the basket outcome on documentary grounds within ~2 min | Yes, immediately: the business case gate is on net sales | No |
| **B. FP&A +6.7% net sales, continue** | PYhR2eh grepped the notebook at msg 90; the others never opened it | **No** | PYhR2eh reconciled its 2.9% wave-4 run-rate against the notebook's 1.73% "treated" figure and correctly attributed the gap to ramp-period inclusion | No |
| **C. Installed-estate pooled effect** | All three computed per-kit effects instead | **No** | Explicitly rejected: "the program readout and notebook both assumed the full-kit uplift would extend to waves 5-6, dominated by the compact kit" (PYhR2eh msg 92) | No |
| **D. Other plausible aggregates** | — | JnK5hsR's own −1.17% and MMGNYFS's +2.68% are novel wrong numbers, not repeats of a published one | — | — |

**The designed attractors did not work.** All three agents identified the outcome error, the population error and
the transport requirement without being led — and then produced *new* wrong numbers of their own. There is no
sign-matching-with-an-external-artifact effect here, which is the mechanism G24's baseline exhibited.

One agreement effect did appear, in the opposite direction: MMGNYFS noted that its declining wave effects
(0.080 → 0.025) "strongly match the increasing compact fractions (7% → 52%)" and wrote that this **"validates the
approach"** (msg 47). A coherent story between two of its own biased outputs raised its confidence. The correlation
is real but is equally consistent with the format confound it never tested.

---

## 5. Falsification analysis

| Diagnostic | Available? | JnK5hsR | MMGNYFS | PYhR2eh |
|---|---|---|---|---|
| Pre-trend / event-time placebo | yes | **omitted** | **omitted** | **omitted** |
| Pharmacy negative control (`pharmacy_sales` is in the same table they queried) | yes | **omitted** | **omitted** | **omitted** |
| Kit-specific effects | yes | **used** | **used** | **used** |
| Mediator decomposition (sales = txns + basket) | yes | **used** (ran log_basket by kit, msg 54) | omitted | partial (reasoned about "trip consolidation") |
| Actual vs planned timing check | yes | implicit (used actual) | **used** (536/536 kit match, date ranges) | **used** (536 = 536 store check) |
| Closure / comparability investigation | yes | used | **used** (spot-checked two closure weeks in the output panel) | used |
| Within-kit stability across formats and waves | yes | **omitted** | **omitted** | **omitted** |
| Target-population composition | yes | **used** | **used** | **used** |
| Unconditional vs format-conditional comparison | yes | **omitted** | **omitted** | **omitted** |

**Available but not used:** pre-trends, placebo, pharmacy negative control, within-kit stability, and any
specification comparison. These are precisely the checks that would have exposed the missing format conditioning —
the pharmacy control reads +0.0115 under an unconditional design against +0.0011 under a format-conditional one,
with a true effect of zero.

**Used but misinterpreted:** JnK5hsR's basket check. It found compact-kit basket effect −1.37% and reacted with
"I'm puzzled… perhaps they used a simple average" (msg 56) — it treated a symptom of its *own* bias as evidence
about the Programme team's method, and did not test its own specification. MMGNYFS's wave-effect/kit-fraction
correlation (§4) is the second case: a real pattern read as confirmation rather than as a confound.

**Nobody validated after obtaining a plausible number.** Post-convergence activity was formatting and contract
compliance only:

| Trial | Confident at | Terminated at | Post-confidence activity |
|---|---|---|---|
| JnK5hsR | msg 50 (tool call ~24) | msg 62 (38) | two side checks, then scratch-file cleanup |
| MMGNYFS | msg 68 (tool call ~30) | msg 95 (42) | panel spot-checks, contract-column checks |
| PYhR2eh | msg 77 (tool call ~28) | msg 98 (38) | read programme report and FP&A notebook to *explain* its answer |

**Premature convergence with unused opportunity: yes, in all three.** Agent execution took **3m46s–4m59s** against a
20-minute pipeline runtime allowance and no evidence of a wall-clock constraint. Each stopped with ~75% of its
apparent budget unused. PYhR2eh's last reads were confirmatory — it opened the rival analyses only after fixing its
own answer, to explain the discrepancy rather than to test itself.

---

## 6. First irreversible failure and F-classification

| Trial | First irreversible point | Why | Primary | Secondary |
|---|---|---|---|---|
| `JnK5hsR` | **msg 27** — rewrote `panel.py` and kept `_demean` on store + week only | Every later number inherits the unconditional specification. The transport step, correct in itself, propagates biased kit effects | **F9** | F0 (sequencing doc never opened), F7 (no falsification) |
| `MMGNYFS` | **msg 48** — same, when it chose "(kit, run-rate) dummies with store/week demeaning" | Same. Its decision flip is downstream of the same bias | **F9** | F0, F7, F1 (treated the wave/kit-fraction correlation as validating) |
| `PYhR2eh` | **msg 57** — same, at the `panel.py`/`estimate.py` rewrite | Same | **F9 + F10** | F0, F7 |

**No new taxonomy category is needed.** F9 (right method family, wrong statistical object) covers all three
precisely: the object here is the **conditioning set**, i.e. the identifying assumption, rather than the unit or the
population.

**F10 is confirmed independently.** `PYhR2eh` returned the correct business decision (stop) with **every graded
effect outside tolerance** — gate 1.12 τ, waves 5.1–7.6 τ — and passed `test_decision` on the visible extract while
failing all three hidden extracts. A decision-only grader would have scored it a success. This is the second
independent confirmation of F10 after G24, and the first where the correct decision coexists with a *state* that is
entirely correct, which makes it a cleaner instance.

---

## 7. Reasoning → implementation gaps

Genuine gaps were **rare** — which is itself the finding. These agents implemented what they said.

| Trial | Said | Implemented | Gap? |
|---|---|---|---|
| all three | "use actual go-live from the install log" | did exactly that | **no gap** |
| all three | "exclude non-comparable weeks (closures)" | did exactly that | **no gap** |
| all three | "gate is on net sales" | did exactly that | **no gap** |
| all three | "transport by the waves 5–6 kit mix" | did exactly that | **no gap** |
| `JnK5hsR` | comparable = no closure | implemented `(customer_txns > 0) & is_closed.isna()` — added an unstated transactions condition | **minor gap**; its panel was never graded |
| `PYhR2eh` | "excluded the ramp-up period, starting the comparison at week 26 post go-live" (msg 95) | actually used e ∈ [12,25], i.e. from week 13 | **narration error only**; the code is right |
| `MMGNYFS` | declining wave effects "match the increasing compact fractions… this validates the approach" | no test performed | **reasoning gap**: confirmation asserted, never checked |
| all three | — | never stated a parallel-trends assumption at all | **omission, not a gap** |

**This distinguishes G05 from G24 sharply.** G24's trials repeatedly said the right thing and implemented a different
object (weighting by K while describing m). G05's trials implemented their stated plan faithfully; the plan was
missing a step nobody articulated. The failure is a **blind spot**, not a slip.

---

## 8. Decision-correct / analysis-wrong

| | `JnK5hsR` | `MMGNYFS` | `PYhR2eh` |
|---|---|---|---|
| Final decision correct (visible)? | ✓ stop | ✗ continue | ✓ stop |
| Transported gate effect correct? | ✗ (4.9 τ) | ✗ | ✗ (1.12 τ) |
| Kit effects correct? | ✗ compact −3.04% vs −0.3% | ✗ compact +0.83%, full +7.17% vs +4.3% | ✗ full +8.44% |
| Wave effects correct? | ✗ 2 of 4 outside | ✗ all 4 outside | ✗ all 4 outside |
| **Analysis panel correct?** | not graded | **✓ all four extracts** | **✓ all four extracts** |
| **Event time correct?** | not graded | **✓** | **✓** |
| **Population correct?** | ✓ (waves 5–6, kit-weighted) | ✓ | ✓ |
| Classification | F9 | F9 | **F10** (+F9) |

**Two of three trials reached the correct business decision with wrong numbers.** Had G05 graded only the decision,
this baseline would read 2/3 or 3/3 on the visible extract. The hidden extracts and the effect tolerances are what
make it 0/3. **This is the central benchmark hypothesis, and it is confirmed.**

---

## 9. Verifier failure → substantive cause

Every failing check in both graded trials traces to **one** conceptual error.

```
test_effects (visible)              →  wave and gate effects inflated
test_hidden_effects_and_decision ×3 →  same, on three other extracts
test_intervals                      →  CIs centred on the biased estimate;
                                       "interval does not cover truth when doubled"
test_decision (MMGNYFS only)        →  gate 0.0268 > hurdle because the bias pushed it over
        ↑
   all five/six failures
        ↑
  kit and wave effects biased upward by the differential format trend
        ↑
  store + calendar-week fixed effects, no format conditioning
        ↑
  the wave-sequencing rule (format first, bay within format) was never read
        →  F9
```

**One conceptual error produced 5 of 5 (PYhR2eh) and 6 of 6 (MMGNYFS) failing checks.** No trial failed for two
independent reasons. The interval failures are not a separate defect: the intervals are internally consistent and
fail only because they are centred in the wrong place.

---

## 10. Counterfactual patch analysis

The smallest scientifically legitimate correction, for each trial: **replace calendar-week fixed effects with
format × week fixed effects** (one line in `_demean`, or equivalently restrict controls to same-format
not-yet-installed stores).

| Trial | Smallest patch | Classification | Confidence |
|---|---|---|---|
| `PYhR2eh` | format × week effects | **ONE-PATCH NEAR MISS** | High for the gate (already 1.12 τ); moderate for the waves |
| `MMGNYFS` | format × week effects | **ONE-PATCH NEAR MISS** | Moderate — same single change, but its errors are larger and its decision must also flip |
| `JnK5hsR` | format × week effects | **ONE-PATCH (unverified)** | Lower — its wave-4 estimate is negative, suggesting a second issue in its transition-dummy handling |

**Basis for the classification, without re-running anything.** The Phase-0 panel already measures exactly this
contrast on the same generator: `imp_unconditional` (store + week only) is rejected at a minimum of **4.57 τ**,
while `imp_format_week` passes at **≤ 0.54 τ**, and `cs_format_notyet` at ≤ 0.66 τ. Format conditioning is the
dominant term by an order of magnitude. The agents' remaining choices — static TWFE with ramp/post dummies rather
than imputation or a 2×2 design — are second-order in that panel.

**I did not run the patched code.** A deterministic check via `tools/g05/quickcheck.py` would settle it and costs no
model spend; it was not performed because this instruction ends at documentation.

**No trial was a fundamental reasoning failure.** All three built a defensible estimator with the correct estimand,
the correct population and the correct transport, and missed one conditioning variable.

---

## 11. Benchmark-validity review (possible F8)

| Question | Finding |
|---|---|
| Was the required evidence visible? | **Yes.** `docs/store_ops/wave_sequencing_2024-11.md` states the sequencing rule and no trial opened it. `stores.format` is in the first table every trial queried. The evidence was present and ignored, not hidden |
| Was terminology sufficiently specified? | **Yes.** All three derived "uplift = log points", "run-rate = weeks 13–26", and the 2.5% hurdle from the glossary and business case without difficulty, and agreed with each other |
| Did the verifier reject a defensible causal analysis? | **No.** An unconditional TWFE under format-driven sequencing with differing format trends is not defensible; it is the textbook confounding case, and it is a pre-registered wrong analysis (`imp_unconditional`, 4.57 τ) |
| Did infrastructure affect behaviour? | **Yes, for `JnK5hsR`** — its verifier did not execute (§2). Not for the other two |
| Did timeout matter? | **No.** Agent execution was 3m46s–4m59s; `test_run_time` passed in both graded trials |
| Did the task reward an oracle-specific implementation? | **No.** Seven structurally different accepted implementations pass, spanning imputation and 2×2 designs, three conditioning sets, two control pools and four base periods. None of the three agents' estimators is close to any of them on the conditioning axis |
| Was a hidden rule required? | **No** |

**One possible F8, confined to `JnK5hsR`:** the verifier's stray-process sweep may have interacted with the agent's
leftover process groups. Recorded here against the frozen version; **the task was not changed.** If it recurs on a
future baseline, the sweep is the first thing to examine.

**One design observation, not a defect.** The attractors (+8.0%/+5.5%/+6.7%) were bypassed by every trial, so the
"two analyses agree" mechanism was never exercised. The task remains hard, but *not for the reason it was designed
to be hard*. The discriminating power came from the effect tolerances and the hidden extracts, not from the
attractors.

---

## 12. Comparison with Task 02, G08, G10, G24

| | Failure locus | Decision correct while values wrong? | State reconstruction |
|---|---|---|---|
| **Task 02** | temporal state / per-example grain — failure *at* state | n/a | failed |
| **G08** | semantic reconstruction + multi-component repair — target vintage never investigated | partly | failed |
| **G10** | correct censoring diagnosis, inadequate latent statistical model (9.7–68 τ) | no | n/a |
| **G24** | correct OPE family, wrong action space / decision unit (0.8–4.3 τ) | **yes, 12/12** | partial |
| **G05** | **correct state, correct estimand, correct population, wrong conditioning set** (1.1–7.6 τ) | **yes, 2/3** | **passed completely, 4/4 extracts** |

**The emerging pattern is reproduced, with one link broken.**

- broad diagnosis correct — **yes, and more completely than in any previous task**
- plausible method selected — **yes** (panel FE + kit interaction + transport)
- applied to the wrong object — **yes**, the conditioning set
- plausible aggregate agreeing with an organisational number — **no, this link is absent.** All three rejected the
  published figures and produced novel wrong numbers
- available falsification omitted — **yes, completely**
- premature confidence — **yes**, ~4 minutes of ~20 available

**What is new in G05.** In G08, G10 and G24 the model failed while reconstructing the situation. Here the model
reconstructed the situation *perfectly* — exact panel state on four extracts, correct estimand, correct population,
correct transport, unprompted — and still failed, because it never asked **what makes the comparison valid**. It
chose an estimator without ever stating an identifying assumption, and therefore had nothing to check.

**Proposed refinement, F9a: identification-assumption blindness.** A sub-case of F9 where state, estimand and
population are all correct and the error is the conditioning set or control group — i.e. the assumption under which
the estimator is unbiased was never articulated, so its violation was never testable. Distinct from G24's F9, where
the *object* of estimation was wrong. Recorded as an observation from three trials; not promoted to a taxonomy code
until a second task reproduces it.

---

## 13. Verdict on the benchmark thesis

**G05 supports the thesis and strengthens it in one place while weakening it in another.**

**Supports.** pass@3 = 0 with no trial closer than 1.12 τ on the gate and 5 τ on the waves. F10 confirmed
independently: 2 of 3 correct decisions on wrong analysis. Grading below the decision is demonstrably necessary.

**Strengthens.** This is the first task where the model's *reconstruction* is flawless and the failure is purely
inferential. It shows the benchmark can isolate statistical reasoning from data-wrangling competence — a claim that
G08/G10/G24 could not cleanly make, because in those tasks the model also failed at reconstruction.

**Weakens.** The designed attractor mechanism did not fire. The pre-baseline document argues at length that the
+8.0%/+5.5%/+6.7% figures make the wrong answer tempting; no trial was tempted. The difficulty is real but resides
somewhere other than where the design predicted, and the "trusted external number" mechanism — central to the G24
findings and to the F10 hypothesis — was not reproduced here.

**Include in the final benchmark: yes.** It is one of only three measured tasks at pass@3 = 0, it is the only one
testing causal identification, its failures are diagnostic rather than noisy, and all three trials failed the same
way — which indicates a genuine capability boundary rather than variance. The run-to-run spread in the gate figure
(−1.17% / +1.57% / +2.68%) is itself a useful measurement: the model cannot reliably reach the same answer twice.

### Candidate-set arithmetic toward pass@3 < 30%

| Task | pass@3 | Status |
|---|---|---|
| 01 revenue reconciliation | 1 | easy anchor |
| 02 renewal-risk regression | 0 | include |
| 03 lead-score evaluation | 1 | development only |
| 04 retention metrics | 1 | undecided |
| 05 onboarding experiment | 1 | development only |
| 06 usage statement close | 1 | development only |
| G08 forecast vintages | 1 | medium-hard candidate |
| G10 censored demand | 0 | include |
| G24 recommender OPE | 0 | include |
| **G05 SCO rollout gate** | **0** | **include** |

**Four measured tasks at 0, five at 1** (02-explicit-invariant is an ablation, not a set member). A benchmark of
{02, G05, G10, G24} measures **pass@3 = 0/4 = 0%**; adding G08 gives 1/5 = 20%; adding G08 and one easy anchor
gives 1/6 ≈ 17%. **The target is now reachable from measured tasks** — the first time that has been true. It was not
before G05: with only {02, G10, G24} the set was too small to defend as a benchmark.

Caveat: 0/4 from three trials each is 12 trials total. The interval on that estimate is wide, and G05's own
run-to-run variance shows how much a single trial can move.

---

# 14. Final baseline: replacement trial `rsDKTXQ` and the official three-trial result

## 14.0 Chronology (recorded exactly as it happened)

1. **G05 was frozen before any Gemini baseline** — checksum `77a6e432d9d2cba2`, commit `0b86b03`.
2. The initial run (`g05-gemini3flash-baseline-1`, 2026-09-18 02:44 PDT) attempted **three** trials.
3. **`JnK5hsR`'s verifier failed before grading**: it ran 2.18 s, collected no tests, wrote no stdout and produced
   no `ctrf.json`.
4. A **forensic adjudication** classified it **(B) INVALID INFRASTRUCTURE FAILURE, confidence MEDIUM**
   (`research/g05/G05_JnK5hsR_validity_forensics.md`, commit `939f1cd`).
5. **The adjudication happened BEFORE the replacement was run**, and was committed before it.
6. **No benchmark modification occurred at any point** — not before, during or after. The task, DGP, fixtures,
   verifier, tolerances, SE_ref and hidden extracts are untouched; `candidates/` has not changed since the freeze.
7. **Exactly one replacement trial was authorised and run** (`-k 1 -n 1`). No further trial was launched, and none
   will be.
8. The replacement ran against the **identical frozen task**: Harbor `task_checksum`
   `56c1d86ea2ca9df1d0581ce67400347f9c1ecf16499c9da679bc636bc140510b`, the same value recorded in all three
   first-run trials; repository checksum `77a6e432d9d2cba2` before and after.
9. **The final quantitative baseline uses exactly three valid trials**: `MMGNYFS`, `PYhR2eh`, `rsDKTXQ`.
10. **`JnK5hsR` remains qualitative evidence only** and is excluded from successes/3, empirical success rate,
    pass@3 and valid-trial cost statistics.

Operational note: before the replacement, ten unrelated development containers (relay, ledgerai, expertops, mongo)
were **stopped** — not deleted, no volumes removed, no configuration or memory allocation changed — leaving the
7.654 GiB Docker VM entirely free. This removed the resource contention present during the first run. Nothing about
the task changed.

## 14.1 The replacement trial

| | `rsDKTXQ` |
|---|---|
| Job | `g05-gemini3flash-baseline-2` |
| **Validity** | **VALID** — verifier executed fully: 79.13 s, 14 tests collected, `ctrf.json` written, 13,536 bytes of stdout, 5 failed / 9 passed. No exception, no timeout, workspace intact, identical task checksum |
| **Reward** | **0** |
| Cost | **$0.18330740** |
| Trial wall clock | 326.34 s (5m 26s) |
| Environment setup | 7.13 s |
| Agent setup | 43.54 s |
| **Agent execution** | **171.23 s (2m 51s)** |
| Verifier | 79.13 s |
| Tokens | 926,497 in / 743,738 cached / 18,247 out |
| Tool calls | **46** (25 shell, 12 read_file, 4 replace, 4 update_topic, 1 list_directory) |
| Files inspected | 11 |
| Files modified | 3 (`sco_readout/{cli,panel,estimate}.py`) |

### Verifier result

| Check | Result |
|---|---|
| `test_warehouse_unmodified`, `test_gate_succeeds`, `test_run_time`, `test_rerun_is_deterministic` | pass |
| **`test_analysis_panel`** | **pass** |
| **`test_hidden_panel` (a, b, c)** | **pass ×3** |
| **`test_decision`** | **pass** |
| `test_effects` | **fail** |
| `test_intervals` | **fail** |
| `test_hidden_effects_and_decision` (a, b, c) | **fail ×3** |

Visible extract (truth: wave 1 0.04061, wave 2 0.03427, wave 3 0.03087, wave 4 0.01906, gate 0.01065, **stop**):

| Quantity | Estimate | Error | τ | Ratio |
|---|---|---|---|---|
| wave 1 | 0.04099 | +0.00038 | 0.00659 | 0.06 **pass** |
| wave 2 | 0.02767 | −0.00660 | 0.00724 | 0.91 **pass** |
| wave 3 | 0.01086 | −0.02000 | 0.00515 | **3.9 fail** |
| wave 4 | −0.01150 | −0.03056 | 0.00683 | **4.5 fail** |
| **gate** | **0.01741** | **+0.00676** | 0.00456 | **1.48 fail** |
| decision | **stop** | — | — | **correct** |

## 14.2 Reasoning chronology (analysed independently)

| Stage | `rsDKTXQ` |
|---|---|
| A **Outcome: net sales not basket** | **✓** identified at MSG 102–107 |
| B **Actual vs planned go-live** | **✓** `install_log WHERE event='go_live'`; later explicitly diagnosed the legacy code's use of `planned_go_live` as "the key driver" of the inflated figures |
| C **Comparable time / closures** | **✓** `comparable = is_closure.isna()`; it also spotted and rejected the legacy `customer_txns > 0` rule as mishandling partially closed stores |
| D **Event window e ∈ [12,25]** | **✓** with a separate `is_bedding_in` dummy for 0–11 |
| E **Staggered adoption** | **✗** static TWFE retained; already-treated stores remain implicit controls |
| F **Sequencing / identification** | **✗ partially approached and dropped.** It queried `layout_survey.rear_bagging_bay` by wave (waves 5/6: 140 no-bay vs 51 bay, 118 vs 55) and so found the *kit determinant* — but never connected bay → format → sequencing, and never formed an identifying assumption |
| G **Conditioning on format** | **✗** `_demean` remains store + calendar-week only |
| H **Kit heterogeneity (full vs compact)** | **✓ recognised** — tracked full-kit share falling 93% (wave 1) → 48% (wave 4) |
| I **Target population (waves 5–6)** | **✓ recognised** explicitly |
| J **Transport by kit mix** | **✗ CONSIDERED AND DELIBERATELY REJECTED** (§14.3) |
| K **Uncertainty** | ~ store-clustered sandwich SEs; `test_intervals` failed because the intervals are centred on biased estimates |
| L **Business gate vs 2.5%** | **✓** compared 1.74% to the hurdle, concluded stop |

## 14.3 The decisive finding: a wrong estimand chosen *because* the decision was insensitive to it

This trial is **not** a repeat of the first three. It reached the transport step, understood it, and then argued
itself out of it — on the grounds that the business decision would be the same either way. Its own reasoning
(MSG 101–102, paraphrased from the recorded thoughts):

- *"Including kit type in the regression model seems essential to accurately estimate the effect"* — the correct
  instinct, stated explicitly;
- *"analysis_panel.csv doesn't include kit type data, which is problematic"* — it treated the output contract's
  column list as a reason not to use kit;
- *"Using the 1.74% average from earlier waves seems defensible, and it supports a 'stop' recommendation"*;
- *"If I use the 1.74% average of Waves 1-4, it's defensible, given the later waves are anticipated to be worse.
  The 'stop' recommendation based on this is **safe**."*

It then shipped `gate_effect = twfe(...)`, the **pooled installed-estate run-rate effect** — the pre-registered
wrong analysis `wrong_gate_pooled_installed`.

**The reasoning is decision-driven, not estimand-driven.** Knowing the answer would be "stop" either way, it
selected the estimator that was easier to defend rather than the one the gate is defined on. This is a sharper and
more troubling instance of the F10 pattern than anything in the first run: not *"correct decision reached with
wrong values by accident"*, but *"wrong quantity chosen deliberately because the decision was robust to it."*

## 14.4 Document discovery

| Question | Answer |
|---|---|
| Did it open `docs/store_ops/wave_sequencing_2024-11.md`? | **No.** Still unopened by any of the four trials |
| What it read instead | `README.md`, business case, KPI handbook, glossary, readout contract, **`docs/programmes/sco2_programme_brief.md`** (first trial to read it), the FP&A notebook, and all four pipeline modules |
| Alternative legitimate route attempted | **Yes, partially.** It went to the data rather than the documents, querying `layout_survey.rear_bagging_bay` by wave — the mechanism that determines kit. That is a scientifically legitimate route to the sequencing story |
| Did the inference affect implementation? | **No.** It used the bay counts only to characterise the waves 5–6 kit mix, then discarded the mix entirely (§14.3). It never asked what the bay rule implies for the *control group* |

Opening the sequencing document is not required for success; this trial shows the empirical route exists and was
begun. It was abandoned one step short of the identifying assumption.

## 14.5 Falsification behaviour

| Diagnostic | Classification |
|---|---|
| Pre-trends | **AVAILABLE BUT OMITTED** |
| Event study | **AVAILABLE BUT OMITTED** |
| Placebo | **AVAILABLE BUT OMITTED** |
| Pharmacy negative control | **AVAILABLE BUT OMITTED** |
| Kit-specific effects | **AVAILABLE BUT OMITTED** — it computed kit *shares*, never kit *effects*, despite calling them essential |
| Mediator decomposition | **AVAILABLE BUT OMITTED** — explicitly deferred: *"I've decided to postpone testing the log_basket function for the moment"* |
| Actual-vs-planned timing | **USED CORRECTLY** — traced the legacy figures to `planned_go_live` |
| Closure / comparability investigation | **USED CORRECTLY** — compared its own rule against the legacy `customer_txns > 0` rule and tested the effect of dropping the `comparable` filter |
| Within-kit stability | **AVAILABLE BUT OMITTED** |
| Alternative specifications | **AVAILABLE BUT OMITTED** — no comparison of conditioning sets, control pools or base periods |
| Target-population composition | **USED BUT MISINTERPRETED** — it measured the composition correctly, then concluded the composition could be ignored |

**This trial falsified the legacy analysis but never its own.** Every check it ran was aimed at explaining why the
Programme/FP&A numbers were wrong; none was aimed at testing its own specification.

## 14.6 Premature convergence

| | |
|---|---|
| Main hypothesis formed | ~MSG 102–107 / tool call ~10 (switch to net sales, run-rate window) |
| Became confident | ~MSG 101–104 / tool call ~40, when it settled on the pooled 1.74% as "safe" |
| Validation performed afterward | a non-positive-sales sanity check, a re-run, and a `cat` of the output |
| Terminated | MSG 113, after issuing a literal no-op shell command *"just to trigger the final response phase"* |
| Time used / available | **171 s of agent execution** against `agent.timeout_sec = 5400` and a 20-minute pipeline allowance |

It stopped after obtaining a locally plausible result while every listed falsification remained unused. Short
trajectories are not failure in themselves; here the unused opportunity is explicit — it named the checks it was
skipping.

## 14.7 Reasoning → implementation

| Pattern | Present? |
|---|---|
| Mentions format but fails to condition on it | **No** — format is never mentioned at all. This is a reasoning gap, not an implementation gap |
| Recognises actual go-live but uses planned | no — implemented correctly |
| Recognises closures but includes contaminated periods | no — implemented correctly |
| **Recognises kit heterogeneity but pools kits** | **YES — the defining failure.** Said kit conditioning was "essential", implemented a pooled estimate |
| **Recognises the waves 5–6 population but reports the installed estate** | **YES** — same act |
| Recognises transport but uses wrong weights | n/a — no transport performed |
| Criticises TWFE but implements forbidden comparisons | partially — it criticised the legacy TWFE's *inputs* (dates, comparability), never its identification |
| Identifies run-rate but averages the wrong window | no — window implemented correctly |

**Both failures are reasoning failures, not implementation failures.** The code does exactly what the agent decided
to do. The missing format conditioning was never considered; the abandoned transport was considered and rejected on
an explicitly stated (and wrong) rationale.

## 14.8 First substantive failure and F-category

**Earliest determining point: MSG 101–102**, where it chose the pooled installed-estate average over kit transport.
The estimator specification (store + week demeaning) was already fixed earlier at MSG 212–229 without any
identification argument, so two independent errors were locked in before any output existed.

| | |
|---|---|
| **Primary: F9** | right method family (panel FE with a run-rate dummy), wrong statistical objects — the **population** (installed estate, not waves 5–6) and the **conditioning set** (no format) |
| **Secondary: F10** | correct business decision (stop) with the gate 1.48 τ out and two wave effects 3.9–4.5 τ out |
| Secondary: F0 | the sequencing document was never opened, and the bay query was not followed through |
| Secondary: F7 | no validation of its own specification |

**F9a is NOT promoted.** This trajectory does not independently support it: `rsDKTXQ`'s primary error is a
*population/transport* error — an object error of the classic G24 kind — not purely an identification-assumption
blindness. F9a therefore remains a one-task observation from the first run, unpromoted.

## 14.9 Decision-correct / analysis-wrong

| | `rsDKTXQ` |
|---|---|
| Final decision | **stop** |
| Decision correct? | **Yes** (visible); `test_decision` passed |
| Transported effect correct? | **No** — no transport performed; gate 1.48 τ out |
| Kit effects correct? | **Not produced** |
| Wave effects correct? | **Partly** — waves 1–2 within tolerance, waves 3–4 out at 3.9 τ and 4.5 τ |
| Analysis panel correct? | **Yes — visible and all three hidden extracts** |
| Event time correct? | **Yes** |
| Target population correct? | **No** — installed estate used as the gate population |
| Uncertainty correct? | **No** — `test_intervals` failed; intervals do not cover truth even when doubled |

**F10 recorded.** Decision-only grading would have scored this trial a success.

## 14.10 Counterfactual patch

**MULTI-PATCH FAILURE.** Two independent corrections are required:

1. transport kit-specific effects onto the waves 5–6 kit mix (~71% compact) instead of reporting the pooled
   installed-estate effect — this alone addresses the gate;
2. replace calendar-week fixed effects with format × week effects — this alone addresses waves 3–4, whose errors
   (3.9 τ, 4.5 τ) are of the same form and magnitude as the other trials'.

Neither suffices alone: patch 1 leaves the wave effects failing, and patch 2 leaves the gate targeting the wrong
population. This distinguishes `rsDKTXQ` from `MMGNYFS` and `PYhR2eh`, which were one-patch near misses.

No patched version was executed and G05 was not modified.

## 14.11 Official baseline statistics

**Valid trials:** `g05-sco-rollout-gate__MMGNYFS`, `g05-sco-rollout-gate__PYhR2eh`, `g05-sco-rollout-gate__rsDKTXQ`.

| | |
|---|---|
| **Empirical success rate over three valid trials** | **0 / 3** (not an exact pass@1) |
| **pass@3** | **0** — no valid trial succeeded |
| Excluded | `JnK5hsR` (invalid infrastructure trial) |

## 14.12 Cost accounting

| Category | Amount |
|---|---|
| Original three attempted Gemini trials (run 1) | $0.41764215 |
| — of which invalid `JnK5hsR` | $0.10997395 |
| — valid `MMGNYFS` | $0.15518505 |
| — valid `PYhR2eh` | $0.15248315 |
| Replacement `rsDKTXQ` | **$0.18330740** |
| **A. Total Gemini spend including the invalid attempt** | **$0.60094955** |
| **B. Official valid-baseline Gemini spend** | **$0.49097560** |
| **C. Validation-model spend (`harbor check`, claude-sonnet-4-6)** | **$0.52425255** |

B and C are different categories and must not be summed as one figure.

## 14.13 Cross-trial synthesis (three valid trials only)

| Question | Count |
|---|---|
| Correctly reconstructed business/data state (panel exact on 4/4 extracts) | **3 / 3** |
| Identified the correct causal estimand | **2 / 3** (`rsDKTXQ` chose the pooled installed estate) |
| Discovered format sequencing | **0 / 3** |
| Implemented format conditioning | **0 / 3** |
| Performed meaningful falsification of their own analysis | **0 / 3** |
| Reached the correct business decision | **2 / 3** (`PYhR2eh`, `rsDKTXQ`) |
| Correct decision despite incorrect analysis (F10) | **2 / 3** |
| One-patch near misses | **2 / 3** (`rsDKTXQ` is multi-patch) |
| Failed for the same conceptual reason | **3 / 3 share the missing format conditioning**; `rsDKTXQ` carries an additional independent population error |

**`JnK5hsR`, qualitative only (excluded from every count above).** Its trajectory matched `MMGNYFS`/`PYhR2eh`
closely: net sales, actual go-live, closures, run-rate window and kit transport all correct, with store + week
fixed effects and no format conditioning, reaching gate −1.17% and a correct "stop". It is consistent with the
valid trials and adds no separate finding. Its verifier never ran, so it contributes no graded evidence.

## 14.14 Scientific conclusion for G05

**G05 is hard for a reason the design did not predict, and the reason is stable across trials.**

- **State reconstruction is not the barrier.** All three valid trials rebuilt the analysis panel exactly — actual
  go-live, event-time origin, comparability, log net sales — on the visible extract *and* all three hidden
  extracts. The deterministic layer we expected to separate agents separated nobody.
- **Identification is the barrier.** No trial conditioned on format, and none stated an identifying assumption at
  all. The estimator was chosen by convention (the house method) and by output-contract convenience, never by an
  argument about what makes the comparison valid.
- **The designed attractors never fired.** All four trials rejected +8.0%/+5.5% (basket) and +6.7% (TWFE net sales)
  within minutes, on documentary grounds, and produced novel wrong numbers of their own.
- **A new mechanism appeared in `rsDKTXQ`:** the estimand was chosen *because* the decision was insensitive to it.
  That is decision-driven estimand selection, and it is the strongest argument yet for grading quantities beneath
  the decision.
- **Falsification is absent, uniformly.** Zero pre-trend, placebo, negative-control, within-kit or specification
  checks across three valid trials, each of which stopped after ~3–5 minutes with most of its budget unused.

**This changes the emerging thesis in one respect.** Across G08, G10 and G24 the pattern was *diagnosis correct →
plausible method → wrong object → agreement with a trusted external number → premature stop*. In G05 the
"agreement with a trusted number" link is **absent** — the trials actively refuted the organisation's figures —
and is replaced by **self-consistency and defensibility**: they stopped because their own answer was coherent and
easy to defend, not because it matched someone else's.

## 14.15 Comparison with Task 02, G08, G10, G24

| Task | Capability | Where it fails | Distinct from G05? |
|---|---|---|---|
| Task 02 | temporal state / per-example analytical grain | *at* state reconstruction | Yes — G05's trials reconstruct state perfectly |
| G08 | multi-component semantic reconstruction | target vintage never investigated; multi-part repair incomplete | Yes — G05 needs no multi-part repair |
| G10 | latent-demand inference under informative censoring | correct censoring diagnosis, inadequate latent model | Related but distinct: G10 is a modelling failure, G05 an identification failure |
| G24 | off-policy evaluation | correct OPE family, wrong action space / decision unit | Closest sibling — both are object errors. G24's object is the *action/decision representation*; G05's is the *control group and target population* |
| **G05** | **causal identification under staggered rollout: confounded sequencing, heterogeneous treatment versions, target-population transport** | **conditioning set and population, with state fully correct** | — |

**G05 adds a distinct capability.** It is the only task in the pool where the model must state an identifying
assumption and choose a control group, and the only one where failure is isolated from data-wrangling competence.
Its overlap with G24 is real but bounded: G24 can be failed by mis-representing the logged decision, which is a
reconstruction error; G05 cannot — reconstruction there was flawless and the task still separated.

## 14.16 Final-benchmark recommendation

**Include G05.**

| Criterion | Assessment |
|---|---|
| Empirical difficulty | pass@3 = 0 over three valid trials; nearest miss 1.12 τ on the gate, with waves 5–7 τ out |
| Realism | a staged retail rollout with an install log, closure records, a layout survey and a capital gate — all mechanisms documented |
| Distinct capability | causal identification and target-population transport; not covered elsewhere |
| Verifier validity | Oracle 1 / Nop 0, `harbor check` 11/11, clean clone reproduced, 38/38 mutations, 7 accepted implementations pass. One infrastructure failure in four runs (§14.0) is an operational risk, not a grading defect |
| Trajectory informativeness | **high** — failures are diagnostic, consistent, and traceable to a single named omission |
| Benchmark ambiguity | none found; no trial complained of missing or contradictory evidence, and all four derived the same definitions from the documents |
| Redundancy | bounded overlap with G24 (§14.15) |

Two caveats to carry forward, neither justifying a change to the frozen task: the **attractors never fire**, so the
task's difficulty does not come from where the design says it does; and the **verifier's stray-process sweep** is an
operational hazard worth watching on any future run (`research/g05/G05_JnK5hsR_validity_forensics.md` §4).

## 14.17 Candidate-set arithmetic (measured tasks only)

| Task | pass@3 | Valid trials |
|---|---|---|
| Task 02 | **0** | 3 |
| G05 | **0** | 3 (`MMGNYFS`, `PYhR2eh`, `rsDKTXQ`) |
| G10 | **0** | 3 |
| G24 | **0** | 3 |
| G08 | **1** | 3 |

- {Task 02, G05, G10, G24} → **0 / 4 = 0%**
- {Task 02, G05, G08, G10, G24} → **1 / 5 = 20%**
- Adding one easy anchor (Task 01, pass@3 = 1) → **2 / 6 ≈ 33%** — above target

**A five-task core of {Task 02, G05, G08, G10, G24} measures 20% pass@3, below the <30% target**, on 15 valid
trials. Adding an easy anchor pushes it over, so the anchor decision is now a real constraint rather than a
formality. `JnK5hsR` is **not** counted as a fourth G05 trial anywhere in this arithmetic, and no unmeasured task
is included in the denominator.
