# 08 — Failure-mode audit

**The question.** We predicted a single phenomenon: *agents recognise the scientific problem, produce
locally coherent work, and still fail to recover the correct decision-relevant quantity.* This chapter
tests that against the criterion-level evidence and finds it **partly right and materially incomplete**.

## The original hypotheses and what happened to them

| # | prospective hypothesis | verdict | evidence |
|---|---|---|---|
| H1 | failures will be coherent, not incoherent | **SUPPORTED** | no valid trial produced non-running work; every failing analysis executed and was internally consistent |
| H2 | the agent commits early to one explanation and never revises | **DISCONFIRMED** | revision language appears throughout the Gemini trajectories, including a `g24` trial that diagnosed the bias in its own first correction |
| H3 | agents fail for lack of discriminating tests | **DISCONFIRMED** | `g10`: all three Gemini trials ran the discriminating reconstruction and one recomputed the ice-cream baseline from −5.3% to +9.96%, then still failed |
| H4 | the decision will sometimes be right for the wrong reasons | **SUPPORTED, measured** | see 'decision-only over-credit' below |
| H5 | stating the invariant explicitly will raise the pass rate | **DISCONFIRMED** | `02-renewal-risk-regression__explicit-invariant` scored 0/3 with the invariant stated outright |
| H6 | the failure is a single common mechanism | **NOT SUPPORTED** | eleven distinct criterion-failure shapes across 24 instrumented trials (below) |

A caution on H2 and H3. Those verdicts rest partly on reasoning-text signals, and chapter 10 establishes
that the two scaffolds record reasoning very unevenly (10,199 vs 1,003 median characters). The
**directional** claim — that revision and diagnosis demonstrably occur and do not guarantee success — is
supported by specific quoted artefacts. Any **rate** attached to it is not. Treated as INFERENCE, not
measurement.

## Decomposing the failures by stage

Across the **24 instrumented valid trials** (4 tasks: `p20`, `p22`, `p31`, `g50`; the other six emit a
binary reward and contribute nothing here):

| stage | criterion | failures |
|---|---|---|
| evidence / population | `evidence_reconstruction` | 1/24 |
| estimand / framing | `scientific_object` | 4/24 |
| identification | `identification` | 12/21 |
| implementation | `estimator_implementation` | 3/21 |
| **numerical result** | `quantitative_result(s)` | **19/24** |
| uncertainty | `uncertainty` (`g50` only) | 3/3 |
| self-validation | `independent_validation` | 1/21 |
| decision | `decision` | 16/24 |

The decision-relevant quantity is the **most frequently failed** stage. That is the kernel of truth in the
original hypothesis.

## But it is not one mechanism — there are at least four

The 24 trials fall into **11 distinct criterion-failure shapes**. Grouping them by what they
say about the analysis:

### Shape 1 — quantity wrong, decision wrong (attribution misallocated)

5 trials, all `p22`, both arms: `quantitative_results` and `decision` fail; evidence, framing, estimator,
identification and self-validation all pass. The three Gemini trials produced **byte-identical correct
visible-world output** and failed only the sibling world where tooling drives the yield loss, reporting
`attribution_pp[tooling] = 0.0` against an expected 3.083. **VERIFIED FROM ARTIFACT**
(`verifier/criteria_notes.txt`). The procedure encoded the mechanism it found rather than recovering
whichever mechanism held.

### Shape 2 — quantity wrong, decision RIGHT (decision-only over-credit)

7 trials pass `decision` while failing the quantity. **All three Claude `p20` trials do
this**, and Gemini does it on `p20` as well. A decision-only rubric would have scored those 3/3.

This is the most consequential finding for benchmark design in the whole project: the right answer was
reached from an analysis that does not support it, repeatedly, by a frontier model.

#### A material qualification discovered while building this dossier

Shape 2 is concentrated on `p20`, and **`p20` carries a known contract defect (D1): the sign convention
for `programme_effect_pp` is unstated in v1.** A field-level sign audit of every instrumented trial in
both arms (`build_inventory.py` data, re-derived here) finds:

| arm | task | sign-flip field failures | genuine field failures |
|---|---|---|---|
| gemini | `p20-noshow-monitoring` (v1) | **7** | 21 |
| gemini | `p20-noshow-monitoring-v1.1` (fixed) | **0** | 19 |
| claude | `p20-noshow-monitoring` (v1) | **12** | 16 |
| gemini | `p22`, `p31` | 0 | 6, 15 |
| claude | `p22`, `p31` | 0 | 4, 26 |

A sign flip means the agent's magnitude was within tolerance of the reference and the sign was inverted —
e.g. Claude reported `programme_effect_pp −10.57` against an expected `+10.849`, on all three trials, on
three worlds each.

**The cross-model experiment ran Claude on `p20` v1, not the fixed v1.1.** That was the right call for
comparability — both arms were graded on the identical frozen task — but it means **both arms' `p20`
quantity failures are partly contaminated by our own contract ambiguity**, and the clean control
(`p20-v1.1`, zero sign flips) exists for the Gemini arm only.

**Does Shape 2 survive?** Yes, but narrowed. Every single `p20` trial in both arms has *independent
genuine* quantity failures as well as sign flips (the table above; no trial is sign-only). So the
`quantitative_results` failures are real. But the *magnitude* of the quantity error is overstated by the
artifact, and any claim of the form "the model could not compute the programme effect" is **not
supportable** — on three Claude trials it computed the magnitude to within 0.3 pp and reported it with the
opposite convention.

**The defensible form of Shape 2:** on `p20`, agents reached the MRM-04-correct action while their
submitted attribution numbers (`attribution_auc[...]`, `feed_defect_share_pct`) were wrong — those
failures contain no sign artifact. The `programme_effect_pp` component should be set aside.

This qualification was **not recorded in any prior project document** and is the most significant
correction this dossier makes to its own earlier reporting.

### Shape 3 — quantity RIGHT, identification and decision wrong

4 trials pass the quantity and fail `decision`. Two Gemini `p31` trials and one Claude
`p31` trial produce correct bridge numbers and then fail `identification` and `decision` — they recover
the number and misread what it licenses under the contract. **This is the mirror image of Shape 2 and it
is fatal to a single-mechanism story.**

### Shape 4 — framing never recovered

4 trials fail `scientific_object`, all of them `g50`, all Gemini. They reported
`programme_effect_pp` identical to the arm contrast (within 0.000 pp), an order-level interval 1.882 pp
wide, the zero-power capacity identity (+0.366), and `decision: roll_out`. They never reframed the
estimand at all. **VERIFIED FROM ARTIFACT** (`verifier/test-stdout.txt`).

### And one full pass

`claude-p22-gauge-recalibration-2` passes all seven criteria — the only instrumented trial in the project
to do so. It establishes that the sibling-world generalisation `p22` demands is **achievable**, so the
Gemini result there is a capability observation and not a design artefact.

## All eleven shapes

| trials | criteria failed | tasks |
|---|---|---|
| 5 | `decision`, `quantitative_results` | `p22-gauge-recalibration` |
| 4 | `identification`, `quantitative_results` | `p20-noshow-monitoring`, `p20-noshow-monitoring-v1.1` |
| 3 | `quantitative_results` | `p20-noshow-monitoring`, `p20-noshow-monitoring-v1.1` |
| 3 | `decision`, `identification` | `p31-fill-rate-dispute` |
| 2 | `courier_supply_response`, `decision`, `quantitative_result`, `scientific_object`, `uncertainty` | `g50-courier-boost-rollout` |
| 2 | `decision`, `identification`, `quantitative_results` | `p20-noshow-monitoring`, `p20-noshow-monitoring-v1.1` |
| 1 | `decision`, `quantitative_result`, `scientific_object`, `uncertainty` | `g50-courier-boost-rollout` |
| 1 | `decision`, `estimator_implementation`, `evidence_reconstruction`, `identification`, `independent_validation`, `quantitative_results`, `scientific_object` | `p31-fill-rate-dispute` |
| 1 | **none — full pass** | `p22-gauge-recalibration` |
| 1 | `decision`, `estimator_implementation`, `identification`, `quantitative_results` | `p31-fill-rate-dispute` |
| 1 | `decision`, `estimator_implementation`, `identification` | `p31-fill-rate-dispute` |

## Does one failure mode explain the evidence?

**No.** The honest reading is:

1. **A shared *statistical regularity* exists.** The decision-relevant quantity is the most frequently
   failed criterion (19/24), and framing/evidence/validation criteria sit far above it. That
   ordering holds for both models (chapter 10).
2. **A shared *mechanism* is not established.** Four distinguishable shapes appear, including two that are
   mirror images (quantity-wrong-decision-right versus quantity-right-decision-wrong). A single cause
   cannot produce both.
3. **Identical-looking errors need not share a cause.** Two trials both failing `quantitative_results` may
   be failing for unrelated reasons — one because its procedure cannot express the right mechanism, another
   because it mis-assembled a population. The criterion records *where* the output was wrong, never *why*.
   Resolving this needs manual adjudication (chapter 12, experiment A), not more criteria.

**Revised statement of the phenomenon, as the evidence supports it:**

> On these tasks, agents reliably reconstruct the evidence and frame the scientific object, and the
> decision-relevant quantity is where their work most often breaks. The break has **several distinct
> shapes**, and in a substantial minority of trials the final decision is correct while the quantity
> supporting it is not.

## Selection bias — the largest threat to this chapter

Everything above rests on **4 of 10 tasks** and 24 of 58 valid trials. The four instrumented tasks are
not a random sample: they are the ones built latest, by which point criterion-level reporting existed.
Three of them (`p20`, `p22`, `p31`) share an author period and a verifier template, and all three are
attribution/decomposition tasks — which may be precisely the family where a 'right decision, wrong
quantity' split is most likely to arise.

Concretely, the six binary-reward tasks include **both** tasks where Claude went 3/3 (`02`, `g05`, `g24`,
`g08`) and two where both models went 0/3 (`g10`, `g36`). We therefore have **no criterion-level evidence
from any task Claude solved**, and none from `g10`, the task with the strongest behavioural evidence of
correct engagement. **This is the single most important limitation in the dossier**, and the cheapest fix
is instrumenting those six as new versions (chapter 12).

## What would falsify the revised statement

- Instrumenting `g10`/`g36` and finding failures concentrated in `evidence_reconstruction` rather than in
  the quantity would show the pattern is an artefact of the attribution-task family.
- Manual adjudication finding that the `p22` 'identical output' trials differ materially in their code
  would weaken the procedure-overfitting reading.
- A tier-matched Claude arm failing `scientific_object` as often as Gemini did on `g50` would show the
  framing advantage is tier, not model.
