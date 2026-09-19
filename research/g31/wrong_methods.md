# G31 pre-registered wrong analyses

Registered **before** the simulation gate was run. Code: `g31_estimators.py`, dict `WRONG`.

Ten of the fourteen candidate wrong methods listed in the brief arise naturally from this DGP. Four were dropped
because they have no purchase here and including them would be padding: *W9 (use current review policy to
reconstruct historical labels)* — the policy is stationary in the base world; *W11 (correct selection correction,
wrong target population)* — folded into `W9_holdout_only`, which is the natural form it takes here;
*W12 (correct metrics, wrong business utility)* — folded into `W10_count_recall`; *W13 (post-treatment
conditioning)* — realised concretely as `W3` and `W4` rather than as a separate abstract case.

| Code | Analysis | Why a competent analyst would write it | Assumption violated | Plausible-looking? | Could it still give the right decision? |
|---|---|---|---|---|---|
| **W1** | **Complete case.** Every row carrying any label — chargeback, investigator determination, or settled-with-no-chargeback — treated as representative | This is what "evaluate on labelled data" means to most practitioners. It uses the most data and looks maximally inclusive | I1 ignored: the labelled set is a v6-shaped selection of the population | Yes — produces sensible-looking recall in every segment | Tested |
| **W2** | **30-day age cutoff** (the legacy readout). Settled rows older than 30 days; fraud = chargeback within 30 days | The chargeback-ops document mentions a 30-day reporting convention; it is the obvious way to "handle" delay | I3 violated: 30 days is below the maturity horizon in every segment, and badly so in marketplace (~87 days) | Yes — it is the incident's own analysis | Tested |
| **W3** | **Mature settled only.** Maturity horizon estimated correctly per segment, then evaluate on settled rows | This is the *sophisticated* version of W2 and looks like a complete fix. An analyst who has read about censoring stops here | I1 ignored: the settled population excludes blocked rows and the unworked review band | Yes — and it is the most dangerous, because the analyst believes they have solved the problem | Tested |
| **W4** | **Reviewed only.** Evaluate on manually reviewed cases, which carry investigator-verified labels | These are the highest-quality labels in the business. "Use the gold labels" is a defensible instinct | Positivity: `P(reviewed | s6)` is 0 below the capacity cutoff. The reviewed set is the top of the review band by *v6 score* — the incumbent's own selection | Yes — small n, clean labels, plausible numbers | Tested |
| **W5** | **Blocked = fraud.** Treat every blocked authorisation as fraudulent | "The model blocked it for a reason"; also the conservative choice a risk manager might defend | Asserts `Y*=1` where `Y*` is unobserved; mechanically rewards whichever model agrees with v6 | Partly — it is obviously crude, but it is common in practice | Tested |
| **W6** | **Unlabelled = legitimate.** Any row without a positive label counts as `Y*=0` | The default behaviour of a left join followed by `fillna(0)`. Rarely a conscious decision | Same as W5 in the other direction; understates fraud everywhere the labels are missing | Yes — it is invisible in code review | Tested |
| **W7** | **IPW on the v6 band share.** Reweight labelled rows by (band population / band labelled count) | An analyst who has correctly identified that selection exists, and reaches for reweighting, but uses the *observed labelling rate* instead of the *logged bypass probability* | The labelled rate inside the review band is contaminated by the score-ordered review selection; weighting by it does not restore representativeness | **Very** — this is a correct-looking method with the wrong weight, the G24 failure shape | Tested |
| **W8** | **Pooled segments.** Correct correction, estimated once on the whole book, applied to every segment | Pooling for stability is standard when per-segment samples look thin | Ignores the heterogeneity that *is* the answer: the observation process and the model's edge both vary by segment | Yes — and it yields one tidy number, which is what an executive asked for | Tested |
| **W9** | **Holdout only.** Use only the randomised bypass rows, with correct weights | The holdout is the clean randomised sample; using only it feels rigorous and avoids all selection worries | Wrong target population: the holdout covers only BLOCK and REVIEW, so the denominator omits the allow band entirely | Yes — it is *more* statistically sophisticated than several accepted methods and still wrong | Tested |
| **W10** | **Count recall.** Observation process handled correctly, but recall computed per transaction rather than per dollar | The word "recall" defaults to counts; value-weighting is an extra step that must be read out of the business case | Right statistical object, wrong business object: the gate is defined on fraud **value**, and fraud value is concentrated differently from fraud count (marketplace fraud is 1.9× the value) | Yes — the analysis is otherwise flawless | **This is the designed decision-correct / analysis-wrong case** |

## Why W3, W7 and W9 matter most

These three are the reason the task is worth building, if it is.

- **W3** is an analyst who solved the *famous* problem (censoring) and stopped. It is Task 02's lesson applied
  correctly and still failing.
- **W7** is an analyst who diagnosed selection correctly and then reconstructed the wrong probability — the exact
  shape of the G24 baseline failure, transplanted into a setting where the correct probability is written down in
  a policy document.
- **W9** is an analyst who did everything right statistically and answered a different question. It is the shape
  of the `rsDKTXQ` failure in G05: the estimator is sound, the population is wrong.

If the gate shows these three are not separated, the task has no core and should be dropped.

## Pre-registered criterion

Applying the improved criterion from `research/g05/G05_O1_adjudication.md` §G, agreed there for "the next gate"
and used here for the first time, rather than the per-regime pass-rate rule that proved unmeasurable at n = 20:

1. **Analytic invalidity.** Each wrong method must violate a *stated* assumption (I1–I5) or target a different
   estimand. Recorded in the table above; this is the primary basis for calling a method wrong.
2. **Joint separation.** Estimated probability of a wrong method passing every regime simultaneously below
   **10⁻³**, computed from per-regime pass rates as independent draws.
3. **Deterministic failure on the graded fixture.** If the task is built, every wrong method must fail the
   specific frozen extracts, with the margin in tolerance units recorded.

Criterion 3 cannot be evaluated until fixtures exist. Criterion 2 was evaluated for one regime only before the
gate was abandoned. **`W10_count_recall` was subsequently shown NOT to be a wrong method at all** - it is
algebraically equivalent to the accepted estimators in this DGP. See `simulation_results.md` §2.2.
