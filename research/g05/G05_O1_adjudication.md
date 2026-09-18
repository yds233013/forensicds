# G05 risk O.1: methodological adjudication of the kit-conditioned DiD separation miss

Written 2026-09-18, before any G05 baseline. **Nothing in G05 was changed to produce this memo: no task, DGP,
estimator, verifier, tolerance, fixture or checksum. No simulation was re-run and no model was invoked.** The only
computation performed is binomial arithmetic on counts already recorded in
`research/g05/pilot/results/r6_adjudication.txt`.

**The finding under adjudication.** Kit-conditioned DiD (same-kit rather than same-format not-yet-installed
controls) fails 59 of 60 worlds in its best regime — 98.33% — against a pre-registered requirement of ≥99%.

---

## A. What the ≥99% criterion meant when it was pre-registered

From `G05_phase0_gate.md` §1.5, fixed before round 1:

> Every wrong analysis must fail ≥ 99% of the worlds of at least one regime. The reward requires all four extracts.

Three things are packed into that sentence, and they are not the same thing:

1. **The object.** A property of the *DGP*, estimated by Monte Carlo over randomly drawn worlds. It is a
   development-time screening rule about whether the design *generically* separates a wrong method — not a property
   of any shipped task instance.
2. **The purpose**, given by the second sentence: because the reward requires passing all four extracts, a wrong
   method that is reliably rejected by *one* regime cannot earn reward. The ≥99% rule was a **conservative proxy**
   for the joint requirement.
3. **The unit.** A per-(analysis, regime) pass-rate, compared against a sharp threshold expressed as a percentage.

Point 3 is where it breaks, and this was baked in before any result was seen.

## B. Does 59/60 constitute a literal criterion failure?

**Yes. Plainly, and without qualification.** 59/60 = 98.33% < 99%. The criterion is stated as a hard inequality,
the measurement is 98.33%, and the criterion is not met. Nothing below softens this; the rest of the memo is about
what the failure *means*, not about whether it occurred.

## C. What kind of failure is it?

**Primarily (3) — finite Monte Carlo resolution against an overly sharp criterion — with a component of (4): the
criterion was written in a unit its own pre-registered sample size cannot resolve.** Not (1), and not (2).

The decisive arithmetic, at n = 60 worlds per regime:

| Observation | Pass-rate value | 95% one-sided lower bound on the true fail probability (Clopper–Pearson) |
|---|---|---|
| 60/60 | 100.00% | **95.13%** |
| 59/60 | 98.33% | 92.34% |
| 58/60 | 96.67% | — |

Four consequences, each of which matters:

1. **99% is not on the measurement grid.** The achievable values adjacent to 100% are 100.00% and 98.33%. A ≥99%
   criterion at n = 60 is therefore not a 99% criterion at all — it is operationally identical to demanding
   **60/60**. The "0.67 percentage point shortfall" is not a shortfall of 0.67 points; it is **one world**, the
   minimum resolvable increment.
2. **A method that exactly satisfies the criterion would fail it 45% of the time.** If the true fail probability
   were exactly 0.99, then P(at least one pass in 60 draws) = 1 − 0.99⁶⁰ = **45.3%**. Observing 59/60 is therefore
   entirely consistent with a method whose true fail rate *meets* the requirement.
3. **Across the whole gate, an apparent violation was close to certain.** The round-6 gate evaluated 21 wrong
   analyses × 4 regimes. If every cell were exactly at 99%, the probability that at least one cell shows at least
   one pass is ≈ **1.000**. The gate was structurally guaranteed to produce a "miss" of this kind regardless of
   design quality.
4. **The 20 analyses that "passed" were never verified to meet the criterion either.** A 60/60 observation supports
   only a 95.13% lower bound — **below 99%**. So at n = 60, *no* wrong analysis in this gate was demonstrated to
   satisfy ≥99%, including every one recorded as passing. The criterion was unverifiable in both directions; the
   single recorded failure is the one place where that unverifiability became visible.

Why it is **not (1) benchmark-instance invalidity:** the shipped task grades four *frozen* extracts, on which the
method fails deterministically (§J).

Why it is **not (2) inadequate statistical separation:** separation on the frozen extracts is 1.06–1.92 τ against
an accepted worst of 0.36–0.67 τ, and the joint pass probability across the regime family is 1.6 × 10⁻⁵.

## D. How much evidence do we have that kit-conditioned DiD is invalid for the target estimand?

Strong, and — importantly — **analytic before it is statistical.**

1. **It violates the task's stated identifying assumption, by construction.** The design's assumption is conditional
   parallel trends **given format**, because format is the sequencing variable: Store Operations sequenced waves by
   format, and only *within* a format put rear-bagging-bay stores first. Untreated format trends differ materially
   (Supercentre +6.0%/yr, Market +1.0%, third format −1.0%). A control group matched on **kit** is not matched on
   format, so it carries a different untreated trend than the treated group. The bias is a direct consequence of
   the documented sequencing rule, not an artifact of any particular draw.
2. **Kit does not even nest format.** Kit has two levels and format three, and the mapping is many-to-many
   (bagging-bay availability varies within every format). Conditioning on kit therefore neither blocks nor
   approximates the format-trend channel.
3. **Deterministic rejection on all four shipped extracts:** 1.92 τ (visible), 1.47 τ (hidden_a), 1.06 τ
   (hidden_b), 1.60 τ (hidden_c) — `research/g05/fixture_audit.json`.
4. **236/240 worlds rejected in the pilot**, minimum ratio 0.61, joint pass probability 1.6 × 10⁻⁵.
5. **It is a documented member of the wrong panel from round 5**, added *before* round 6 was run, not discovered
   afterwards.

The classification "invalid for the target estimand" rests on (1) and (2), which no amount of Monte Carlo can
overturn. Items (3)–(5) measure *how* invalid, not *whether*.

## E. Why does it pass in that one world?

Because its bias is only moderately larger than the noise, and a pass is a conjunction that can be satisfied by
chance. Concretely:

- Its bias, expressed in tolerance units, sits around 1–2 τ on typical draws (frozen-extract ratios 1.06–1.92; pilot
  minimum ratio 0.61 in its most favourable regime).
- τ is 3.5 × the RMSE of the least efficient accepted estimator, so a world's noise routinely moves an estimate by
  several tenths of a τ.
- A world is "passed" only if **all five graded quantities and the decision** land inside τ simultaneously. In one
  draw of 60, the noise happened to offset the format-trend bias in every graded quantity at once.

This is an ordinary sampling event, not evidence that the method is sometimes correct. Its expected error is
non-zero in every regime; what varied was the realisation, not the estimand.

## F. Is occasional passing scientifically expected?

**Yes — necessarily, and a criterion that forbids it is asking for the wrong thing.**

Any biased estimator with a continuous sampling distribution has strictly positive probability of landing inside any
finite tolerance. Demanding a 100% failure rate is demanding either (a) a bias so large relative to τ that the
sampling distribution has negligible mass inside the tolerance — which would make the wrong method implausible as an
attractor, since obviously-absurd numbers do not tempt anyone — or (b) a degenerate noise distribution, which is not
a realistic DGP.

There is a design tension here worth stating explicitly: **the wrong analyses most worth including are precisely the
ones that occasionally pass.** `before_after` fails at 14.2 τ and passes nothing — and no competent analyst would
ever submit it. Kit-conditioned DiD is a near-miss at 1–2 τ, which is exactly why it is a realistic trap and exactly
why it sometimes lands inside the tolerance. A criterion that penalises near-misses selects against the traps the
benchmark most needs.

## G. Is the requirement better expressed as "wrong estimators reliably fail somewhere across the regime family"?

**Yes, and the existing evidence shows the per-regime rule is the weaker of the two guarantees.**

The reward requires passing **all four** extracts. The decision-relevant quantity is therefore the *joint* pass
probability. Compare:

| | Guarantee |
|---|---|
| Pre-registered per-regime rule, taken literally | fails ≥99% in one regime ⇒ joint pass probability **≤ 10⁻²** |
| What kit-conditioned DiD actually achieves | joint pass probability **1.6 × 10⁻⁵** |

The method that "failed" the criterion is **625× safer than the weakest method the criterion would have accepted.**
A wrong analysis failing exactly 99% in one regime and 0% in the other three would satisfy the pre-registered rule
while being far more likely to slip through than this one.

So the per-regime rule is not merely hard to measure — it is a **poor proxy** for the property the benchmark needs.
A better-formed criterion has three parts:

1. **Analytic:** the wrong method must violate a stated identifying assumption or target a different estimand — the
   primary basis for calling it wrong, ahead of any simulation.
2. **Joint, on the regime family:** estimated joint pass probability across all regimes below a pre-registered
   bound (e.g. 10⁻³), which is what the reward structure actually enforces.
3. **Deterministic, on the shipped instances:** the method must fail every frozen extract, with a recorded margin
   in τ — since the shipped task involves no sampling at all.

G05 satisfies all three. It fails only a proxy that its own sample size could not measure.

## H. Would changing the criterion now constitute post-hoc benchmark tuning?

**Yes. I want to be unambiguous about this, because the analysis above is persuasive and that is exactly what makes
it dangerous.**

Two things are simultaneously true:

- The methodological critique in §C and §G is **correct on its merits**, and would be correct if it had been written
  before round 6 was run.
- Adopting it *now*, after seeing which method failed and knowing the amendment would clear it, is **post-hoc**. The
  decision to amend is informed by the outcome. That is precisely the pattern pre-registration exists to prevent,
  and "my reasoning is sound" is the argument every post-hoc amendment makes.

A useful test: would this amendment have been proposed if kit-conditioned DiD had come in at 60/60? Almost
certainly not — the criterion's unmeasurability would have gone unnoticed, as it did for the other 20 analyses.
That counterfactual is the definition of an outcome-dependent decision.

The honest resolution is to separate **naming the defect** from **acting on it for this benchmark generation**: the
critique goes in the record now; the amended criterion is pre-registered for the *next* task, before its gate runs,
and G05 is never re-judged under it.

## I. Would changing the DGP or tolerance now be worse than transparently retaining the miss?

**Substantially worse, on four independent grounds.**

1. **It is the specific act the project prohibits.** "Silently change a tolerance after seeing failures" is on the
   forbidden list. Changing it *loudly* is better, but the scientific defect is identical: the tolerance would no
   longer be the pre-registered function of accepted-estimator RMSE; it would be a function of what the wrong panel
   did.
2. **It would invalidate everything downstream.** The frozen calibration, the 38-case mutation suite, the fixture
   audit, Oracle/Nop, `harbor check` and the clean-clone reproduction were all run against the current task content.
   A DGP or tolerance change alters the checksum (`77a6e432d9d2cba2`) and requires re-running all of it — days of
   work and a further ~$0.5 of check spend.
3. **It would buy nothing.** The shipped instances already reject the method on all four extracts. There is no
   defect in the artifact to repair — only a mismatch between a proxy criterion and its own resolution.
4. **It would damage exactly the property that makes this record valuable.** The G05 file already contains a failed
   round 5, recorded in full with its diagnosis. A reviewer can see that failures are reported rather than tuned
   away. Retro-fitting round 6 would convert that from evidence of discipline into evidence of selective reporting.

## J. Does the miss materially threaten the actual benchmark instances?

**No.**

The shipped task contains **no sampling**. Four extracts are frozen in the image; SE_ref is frozen in
`tests/scenarios.py`; the tolerances are fixed multiples of it. An agent submitting a kit-conditioned DiD is
rejected deterministically, every time, on every extract:

| Extract | kit-conditioned DiD | accepted worst | Reward requires |
|---|---|---|---|
| visible | 1.92 τ ✗ | 0.53 τ | all four |
| hidden_a | 1.47 τ ✗ | 0.44 τ | all four |
| hidden_b | **1.06 τ** ✗ | 0.67 τ | all four |
| hidden_c | 1.60 τ ✗ | 0.36 τ | all four |

The 98.33% figure describes the population of worlds the *generator could have produced*. It is a statement about
design robustness under reseeding, not about the four instances that ship.

**The one residual worth naming honestly:** hidden_b's margin is thin. The method fails there at 1.06 τ, so a ~6%
larger SE_ref would let it pass that single extract. It would still fail visible (1.92), hidden_a (1.47) and
hidden_c (1.60), and reward requires all four — so the thin margin does not change the outcome. But hidden_b is the
extract where accepted (0.67 τ) and wrong (1.06 τ) come closest anywhere in the task, and any future change to
SE_ref must re-check that gap specifically.

---

## Recommendation: **OPTION A**

**Keep G05 frozen exactly as it is; preserve the ≥99% criterion as written in the report; record this as one
criterion miss; proceed to baseline with the caveat.**

The reasoning, in order of weight:

1. **The artifact is sound, and the criterion is the thing that is defective.** The four shipped extracts reject the
   method deterministically; the joint pass probability is 625× better than the criterion's own implied guarantee;
   and the method is invalid on analytic grounds that no simulation can overturn. There is nothing in the benchmark
   to fix.
2. **Option B is post-hoc, however good its argument** (§H). The amendment is correct, and it will be worth
   pre-registering for the next task — but adopting it *after* seeing which method it would clear converts a sound
   methodological point into a rationalisation. The value of this repository's record comes from having reported a
   failed round 5 rather than absorbing it; the same discipline applies here.
3. **Option C is disproportionate and destructive** (§I). It discards a fully validated task to repair a proxy
   criterion's resolution, at the cost of the entire downstream validation chain.
4. **The caveat is cheap and the transparency is valuable.** "One of 21 wrong analyses was rejected in 236 of 240
   worlds rather than the pre-registered 237+, and fails all four shipped extracts deterministically" is a sentence
   a reviewer can evaluate in full. It costs the benchmark nothing and tells the reader that the criteria were
   applied rather than adjusted.

### What follows from Option A, concretely

1. `report/g05_prebaseline_validation.md` §9.1 already records the miss and states that no tolerance or DGP change
   was made in response. **Leave it as written.** This memo is referenced from it, not substituted for it.
2. The criterion stays as pre-registered in `G05_phase0_gate.md` §1.5. **Do not edit it.**
3. **Pre-register the improved criterion (§G, three parts) for the next task that reaches a Phase-0 gate, before
   that gate is run**, and record that it was adopted because of the resolution defect found here. Do not apply it
   retroactively to G05, G08, G10 or G24.
4. Any future Phase-0 gate that keeps a per-regime pass-rate rule must set the sample size so the threshold is
   resolvable: a ≥99% rule needs n ≥ 300 per regime to be distinguishable from 100% at all, and n in the low
   thousands to be estimated with useful precision.
5. When G05 is baselined, this miss does not need to qualify the baseline result. It qualifies the *design-gate
   record*, not the reward.

**Not recommended:** any change to G05's task, DGP, estimators, tolerances, fixtures or checksum. **Not authorised
by this memo:** any edit to `candidates/g05-sco-rollout-gate/`.
