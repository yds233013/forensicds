# 07 — Side-by-side case studies

Paired Gemini and Claude attempts on the **same frozen task**. Everything quoted is from
`verifier/criteria_notes.txt`, `verifier/test-stdout.txt` or `agent/trajectory.json`.
**`g50` is deliberately absent** from the pairings: Claude never received a valid grade on it, and
comparing a grade against a non-grade would be a category error.

---

## 1. `p22-gauge-recalibration` — the clearest pair in the project

| | Gemini ×3 | Claude ×3 |
|---|---|---|
| reward | 0, 0, 0 | 0, **1**, 0 |
| steps | 56, 94, 60 | 18, 17, 18 |
| cost | not recorded | $0.83, $0.72, $0.71 |

**What Gemini did.** All three trials produced *byte-identical* visible-world output: `measurement_system`
2.88 pp, `material` 1.06 pp, `tooling` **0.0**, corrected rate 3.81%, `supplier_decision`
`no_supplier_action`. That is the **correct** visible-world answer — they exonerated the supplier and
identified the gauge. All three then failed on `hidden_c` alone:

```
quantitative_results: hidden_c: attribution_pp[material] 3.92 vs 0.817 (tol 0.8)
quantitative_results: hidden_c: attribution_pp[tooling]   0.0  vs 3.083 (tol 0.8)
decision:            hidden_c: supplier_decision 'raise_supplier_nonconformance' vs 'no_supplier_action'
```

**INFERENCE (supported by the identical outputs and the constant `tooling: 0.0`):** their attribution code
had no path that could assign the change to tooling. It encoded the mechanism found in the visible world.

**What Claude did differently.** Trial 2 passed **all seven criteria** — the only instrumented full pass in
the project, with an empty `criteria_notes.txt` because nothing was wrong. Trials 1 and 3 failed
`quantitative_results` and `decision`, i.e. the same shape as Gemini.

**Where they converge and diverge.** Both arms get the visible world right. Both arms *can* fail the
sibling world. Claude succeeds once in three. **The scientifically important consequence: the
generalisation this task demands is achievable, so Gemini's 0/3 is a capability observation and not a
design artifact.** That is the single most load-bearing comparison in the dossier.

**Was the final result scientifically correct?** For Claude trial 2, yes, on all four worlds. For the other
five trials, no — on `hidden_c` they would have raised a contractual claim against an innocent supplier.

---

## 2. `p20-noshow-monitoring` — correct decisions, wrong numbers, both arms

| | Gemini ×3 | Claude ×3 |
|---|---|---|
| reward | 0, 0, 0 | 0, 0, 0 |
| `decision` criterion | PASS, PASS, fail | **PASS, PASS, PASS** |
| `quantitative_results` | fail ×3 | fail ×3 |
| steps | 52, 52, 56 | 18, 17, 30 |

Claude trial 2 is the extreme case — **six of seven criteria pass** and only the quantity fails:

```
quantitative_results: visible:  programme_effect_pp  -10.57 vs  10.8490 (tol 3.0)
quantitative_results: hidden_a: programme_effect_pp  -10.63 vs  10.4310 (tol 3.0)
quantitative_results: hidden_b: attribution_auc[population_drift]   0.0937 vs 0.0005 (tol 0.025)
quantitative_results: hidden_b: attribution_auc[feature_feed_defect] -0.1935 vs 0.0932 (tol 0.025)
```

**The qualification that matters.** The `programme_effect_pp` lines are **sign flips** — magnitude within
0.3 pp, sign inverted — and they are an artifact of defect **D1** (the contract never states the
convention). Both arms ran on `p20` **v1**, so both inherit it. See chapter 09 D1 and chapter 08 Shape 2.

**What survives the qualification.** The `attribution_auc[...]` and `feed_defect_share_pct` failures carry
**no** sign artifact and are genuinely wrong — Claude reported population drift at 0.0937 against 0.0005,
and feed defect at −0.1935 against +0.0932. So both arms reached the MRM-04-correct action while
mis-apportioning the causes that are supposed to justify it.

**Converged behaviour:** both arms decomposed the decline, both evaluated on a defensible population, both
passed their own validation. **Diverged:** Claude got the decision right 3/3 where Gemini managed 2/3.

**Was the final result scientifically correct?** No, in either arm. The action was defensible; the
attribution supporting it was not.

---

## 3. `p31-fill-rate-dispute` — the mirror image

| | Gemini ×3 | Claude ×3 |
|---|---|---|
| reward | 0, 0, 0 | 0, 0, 0 |
| `quantitative_results` | fail, **PASS**, **PASS** | fail, **PASS**, **PASS** |
| `identification` | fail ×3 | fail ×3 |
| `decision` | fail ×3 | fail ×3 |

Two Gemini trials and two Claude trials **produce correct quantities and still fail**. From
`p31-prospective-3`:

```
identification: visible: bridge_pp[aggregation]       24.18  vs 1.831 (tol 0.4)
identification: visible: bridge_pp[denominator]      -26.42  vs -6.429 (tol 0.4)
identification: visible: bridge_pp[returns_treatment] -3.89  vs -1.521 (tol 0.4)
decision:       visible: incumbent_verdict 'not_determinable_from_available_ev…'
```

and from `p31-prospective-2`:

```
decision: hidden_c: incumbent_verdict 'incumbent_correct' vs 'not_determinable_from_available_evidence'
```

**This is the opposite of `p20`.** There the quantity was wrong and the decision right; here the headline
quantity passes and the *bridge decomposition* and the *verdict* fail. Note the expected verdict on
`hidden_c` is `not_determinable_from_available_evidence` — **`p31` already contains a justified-deferral
world**, and both models failed to produce the deferral.

**That is a correction to the project's own record**, which states that no task tests justified deferral.
`p31` does, in at least one sibling world. **VERIFIED FROM ARTIFACT.**

**Was the final result scientifically correct?** No. A wrong verdict here is a position on a £1.8m claim.

---

## 4. `g10-censored-demand` — both fail, with visible engagement

| | Gemini ×3 | Claude ×3 |
|---|---|---|
| reward | 0, 0, 0 | 0, 0, 0 |
| steps | 62, 72, 58 | 53, 34, 16 |
| cost | not recorded | **$3.08**, $1.74, $0.74 |

Binary reward, so **the break point is UNKNOWN for both arms**. What *is* observable:

- Gemini's recorded reasoning engages heavily with the mechanism (29-36 separate mentions of
  censoring/stockout across the three trials). One trial recomputed the ice-cream baseline from **−5.3% to
  +9.96%** and recorded that this "confirms that the Head of Planning was onto something". Another
  identified the selection bias in using stockout-free days only.
- Claude trial 1 is the most expensive trial in the whole cross-model arm (**$3.08, 53 steps**), and the
  effort declines sharply across its three trials (53 → 34 → 16 steps).

**Converged:** both arms fail every trial. **Diverged:** nothing measurable, because the task emits one bit.
**This is the clearest case for instrumenting the remaining six tasks** — we have strong behavioural
evidence of correct engagement and no ability to say where the work broke.

---

## 5. `g36-tou-capacity-gate` — both fail, and Claude barely engages

| | Gemini ×3 | Claude ×3 |
|---|---|---|
| reward | 0, 0, 0 | 0, 0, 0 |
| steps | 54, 44, 40 | **14, 15, 13** |
| cost | not recorded | $0.51, $0.51, $0.48 |

The step counts are the observation. Claude spent **13-15 steps** on a task Gemini spent 40-54 on, and
both failed. **INFERENCE (not established):** Claude may have terminated early rather than exhausted the
problem. The trajectories do not record a reason, so this is **not observable**.

**Converged:** total failure in both arms. This is the only pairing where Claude's effort is dramatically
*lower* than Gemini's, and it is the task where a scaffolded-stopping explanation is most plausible — which
is why controlled scaffolding intervention is experiment C in chapter 12.

---

## 6. `g08-forecast-accuracy-vintages` — the one Gemini success, and Claude's clean sweep

| | Gemini ×3 | Claude ×3 |
|---|---|---|
| reward | 0, **1**, 0 | **1, 1, 1** |
| steps | 90, **106**, 90 | 20, 17, 17 |
| cost | not recorded | $0.80, $0.70, $0.66 |

**The successful Gemini trial is the most effortful trial of its three** (106 steps vs 90 and 90) — the only
place in the data where, within a task, the passing trial did more work than the failing ones. One
instance; no rate should be read from it.

**Claude passes 3/3 in 17-20 steps**, roughly a fifth of Gemini's effort, on the task Gemini found hardest
to pass consistently.

**Was the final result scientifically correct?** For the four passing trials, yes by the verifier's
standard — vintage-correct accuracy computed and the retirement decision following from it. The task emits
only an `artifacts` criterion, so **no capability decomposition is available even for the successes.**

---

## What the pairings establish, and what they do not

**Establish:**
1. `p22`'s sibling-world generalisation is achievable (Claude 1/3) — so Gemini's 0/3 is a capability result.
2. Both models reach correct decisions from unsupported attributions on `p20` (with the D1 qualification).
3. Both models produce correct quantities and wrong verdicts on `p31` — a genuinely different shape.
4. `p31` contains a justified-deferral world, contradicting the project's own claim that none exists.
5. Four tasks (`g10`, `g36`, `p20`, `p31`) defeat both models on every trial.

**Do not establish:**
1. Any shared internal cause. Identical criterion patterns are consistent with different mechanisms.
2. Anything about *where* either model broke on `g10`, `g36`, `g05`, `02`, `g24` or `g08` — those are
   binary-reward tasks and the answer is **UNKNOWN**.
3. That Claude's lower step counts reflect efficiency rather than premature stopping.
