# G31 adversarial review

**VERDICT: BLOCK.**

Independent adversarial review, 2026-09-19. Read-only. Evidence: 5 worlds drawn from `g31_sim.py`
(`visible` seeds 777/778/779, `v7_wins_everywhere` 801, `high_prev` 802), plus ablation estimators written
to `/tmp` that do not touch the repository. No task files exist yet; nothing was modified.

The design documents are unusually careful and the prose is honest about several risks. That makes no
difference to the conclusion. The task, as specified, is defeated by a heuristic that uses no outcome label
at all; two of its three advertised mechanisms are numerically inert; one of its ten pre-registered wrong
methods is mathematically equivalent to the estimand; and the project's own G01 gate already recorded the
reason not to build it.

---

## 0. What the world actually contains (measured, not asserted)

Truth for `visible` seed 777:

| quantity | ecom_cnp | marketplace | travel |
|---|---|---|---|
| `recall_v6` | 0.3485 | 0.3826 | 0.3093 |
| `recall_v7` | 0.4760 | 0.2813 | 0.4098 |
| `Δ` | **+0.1275** | **−0.1014** | **+0.1005** |
| `adopt` | v7 | **v6** | v7 |

Decision string `ecom_cnp:v7|marketplace:v6|travel:v7` in 4 of the 5 worlds I drew; only
`v7_wins_everywhere` flips marketplace. The entire gradeable signal in the task is **one bit: marketplace**.
Everything below follows from that.

---

## A. CHEAP SOLVES

### A1. The task is solved with no labels whatsoever. (15/15 segment-decisions correct)

`g31_sim.py:122-123` draws value as

```python
v = np.exp(rng.normal(spec["log_value_mu"][g], spec["log_value_sd"], n))
v = np.where(y == 1, v * spec["fraud_value_mult"][g], v)
```

so `v = base · mult_g^{Y*}` with `base ⟂ (z, s6, s7)`. Therefore, for the top-`c_g` set of any score `m`
within segment `g` (the *same* cardinality for both models, because `eval_block_rate` is a rate):

```
Σ_{top(m)} v  =  Σ_{top(m)} base_i  +  (mult_g − 1) · Σ_{top(m)} base_i · Y*_i
E[Σ_{top(m)} base]  identical for v6 and v7   (base independent of both scores)
⇒  E[Σ_{top(v7)} v] − E[Σ_{top(v6)} v]  =  (mult_g − 1)/mult_g · (total fraud value) · Δ_g
⇒  sign( Σ_{top(v7)} v − Σ_{top(v6)} v )  =  sign( Δ_g )
```

So **"which model's top 4% captures more gross transaction value" is an exact sign-proxy for Δ_g and requires
no chargebacks, no investigator determinations, no holdout flag, no maturity horizon, no weights.** It is also
the single most natural sanity check a payments analyst performs ("how much value do we stop at today's
budget?"), which means an agent can stumble into it while *not* solving the task.

Measured, per segment, as `(Σ_top v7 − Σ_top v6)/Σ_top v6`:

| world | ecom_cnp | marketplace | travel | decision | correct? |
|---|---|---|---|---|---|
| visible 777 | +4.69% | −7.98% | +3.30% | v7\|v6\|v7 | ✅ |
| visible 778 | +2.33% | −6.57% | +2.82% | v7\|v6\|v7 | ✅ |
| visible 779 | +3.53% | −8.68% | +2.28% | v7\|v6\|v7 | ✅ |
| v7_wins 801 | +3.07% | **+5.76%** | +4.49% | v7\|v7\|v7 | ✅ |
| high_prev 802 | +4.03% | −8.36% | +4.71% | v7\|v6\|v7 | ✅ |

**15/15.** It even tracks the regime flip in world 801. Random half-splits of world 777 agree with each other
and with truth in all three segments, so this is not a knife-edge: the margin is 2–9% against a sampling
noise that is visibly an order of magnitude smaller.

This single finding is sufficient to block. The task claims to measure "can the agent reason about the
observation process". An agent that ignores the observation process entirely, never opens the chargeback
table, and sums a value column gets the graded decision right in every world I tested.

### A2. Constant answers score well

`v7|v6|v7` is truth in 4 of 5 regimes. The only regime that flips it is `v7_wins_everywhere`, and it flips it
by changing exactly one number, `gamma7["marketplace"]` (`g31_sim.py:86`), from 0.95 to 0.15. Hidden extracts
drawn from `high_prev`, `slow_cb_big_holdout` or `tight_capacity` are all `v7|v6|v7` by construction — they do
not touch `gamma7` at all. Unless the shipped fixture set is at least half `v7_wins_everywhere`, a constant
string passes.

Per-segment, the picture is worse. Of the 30 segment-decisions produced by the 10 pre-registered wrong
methods on world 777, **21 are correct (70%)** — and "always answer v7" alone scores 20/30 (67%).

### A3. Plain complete-case gets 2 of 3 segments right, every world

`W1_complete_case` returns `ecom_cnp:v7|marketplace:v7|travel:v7` in 5/5 worlds. It is right about
ecom_cnp and travel every time. So does `W2_age_cutoff_30` (the incident's own analysis), `W3`, `W6`, `W8`.
Two thirds of the graded decision is free.

Worse: **three** pre-registered wrong methods produce the **exactly correct decision string**:

- `W5_blocked_is_fraud` (world 777),
- `W7_ipw_on_v6_band` (5/5 worlds — this is the flagship "G24-shape" wrong analysis),
- `W10_count_recall` (5/5, by design).

`W7`'s marketplace Δ on world 777 is **+0.00017** against an adopt bar of 0.010. It gets the right decision
because a wildly wrong estimate (truth −0.1014) happened to land 1.7% of the way to the bar. That is not
separation; that is luck, and it will not be stable across seeds.

### A4. The answer is written in the prompt

`estimand_and_identification.md:12-16`:

> "chargeback recoveries in the **marketplace** book have been drifting up for two quarters, and they think v7
> has been quietly running in shadow mode and **looks better than it is**."

The one bit of gradeable signal is stated in the business brief, attributed to a named stakeholder, in the
correct direction, for the correct segment. Combined with the "always v7" prior for the other two segments,
an agent can produce the graded decision from the email alone. The design has no defence here — G24's
baseline analysis already recorded that all three trials stopped as soon as the sign matched a trusted
external number, and this design hands the model that number up front.

### A5. Marketplace is the odd one out on five superficial dimensions at once

`marketplace` has, simultaneously, the highest `a` (−6.2 vs −6.6/−7.0), the highest `fraud_value_mult` (1.9 vs
1.25/1.3), the highest `block_rate` and `review_rate`, the lowest `review_capacity` (0.40), the longest
`delay_mu` (3.3), and `gamma7 = 0.95` vs 0.10/0.15. Any agent that tabulates per-segment descriptives will see
marketplace flagged in every column. It does not need to know *why* marketplace is different to bet that it
is the segment where the answer differs.

---

## B. SCIENTIFIC VALIDITY

### B1. The maturity leg is inert. Ignoring censoring entirely changes nothing.

I ran the accepted HT estimator with the maturity horizon set to **zero** (`L1_noMaturity`: use every row,
however recent, with the raw `chargeback` flag), with a flat 30 days (`L2_T30` — i.e. the *wrong* horizon that
`W2` is condemned for), and with a flat 120 (`L2b`). Against `A1_ht_holdout` with the estimated per-segment
horizon:

| world | max \|Δ(L1) − Δ(A1)\| | max \|Δ(L2_T30) − Δ(A1)\| | decision |
|---|---|---|---|
| visible 778 | 0.0036 | 0.0022 | identical |
| visible 779 | 0.0036 | 0.0012 | identical |
| v7_wins 801 | 0.0091 | 0.0055 | identical |
| high_prev 802 | 0.0066 | 0.0059 | identical |

Every one of these is **below the 0.010 adopt bar** and far below `A1`'s own sampling error against truth
(up to 0.0256, §D1). This is not a surprise — it is forced by the design. `I3` states the lag is independent
of `Y*` given segment; recall is a *ratio* whose numerator and denominator are both fraud-value sums; a
score-neutral random deletion of frauds cancels. The censoring mechanism was designed to be ignorable, and it
is, completely.

So `maturity_days` is testable only as a standalone graded number, which is recipe-matching (§D3), and the
"delay / right-censoring" leg contributes **zero** to every quantity anyone cares about. One of three legs is
decoration.

### B2. The selective-verification leg is also inert, and the stated reason for excluding released rows is wrong.

`dgp_design.md:142-144` says the `released = reviewed AND Y*=0` simplification "is precisely why the accepted
estimators must exclude them rather than use their chargeback outcomes." That is backwards. Released rows
have `Y* = 0`, so `Y*·v = 0`; they contribute **exactly zero** to both the numerator and the denominator of a
fraud-value-weighted recall. Including them cannot bias anything.

Measured: `L4_inclReleased` (A1 with reviewed-and-released rows added back, unweighted) is **identical to A1
to four decimal places on all six recall levels in all four worlds**. Not close — identical.

So the review-capacity mechanism, the score-ordered queue, the positivity violation below the capacity
cutoff, and the "investigators are perfect" simplification are all, jointly, worth 0.0000 on every graded
quantity. What is left of the review band is only that 88% of it is unlabelled — which is the *same*
correction as the block band.

### B3. Therefore: the "three missingness mechanisms" are one mechanism.

After B1 and B2, the complete statistical content of G31 is:

> Fraud value inside `band > 0` is observed only through the logged bypass at rate `q`. Multiply those rows
> by `1/q`. Add the allow band. Done.

That is a single inverse-probability weight, with a **known, logged, constant, two-valued** propensity. It is
one correction wearing three coats. The claim in `dgp_design.md:104-105` — "Fixing any two of the three still
leaves a biased answer. That is the design's central claim" — is false as measured: fixing mechanism 1 alone,
with mechanisms 2 and 3 not merely unfixed but actively ignored, recovers the estimand to within 0.009.

### B4. `eval_block_rate` is exactly `block_rate + review_rate`, in every segment of every regime.

`g31_sim.py:59-60, 69`: 0.010+0.030 = 0.040; 0.012+0.038 = 0.050; 0.008+0.024 = 0.032. I verified the identity
holds exactly for all 5 regimes × 3 segments, and verified in-world that
`1[s6 ≥ τ_v6] ≡ (band != ALLOW)` for **100.0000%** of rows in 12/12 segment-worlds.

Consequences:

- `R_v6,g` is definitionally "the share of fraud value the current policy already intervenes on". No
  threshold computation is needed; `band` *is* the v6 flag. A rules-lawyering agent reads it off the
  decisions table.
- The `s6` threshold coincides with the boundary of the selectively-observed region, which is exactly the
  configuration that makes `W4_reviewed_only` and `W9_holdout_only` return `recall_v6 = 1.000000` in all three
  segments (measured, world 777). A method whose output is *exactly 1.000* in every segment is not a
  "plausible wrong analysis" that an agent might ship — it is a self-refuting artefact that any analyst
  discards in five seconds. `wrong_methods.md` calls W9 "*more* statistically sophisticated than several
  accepted methods and still wrong" and names it one of the three methods that make the task worth building.
  It returns 1.000, 1.000, 1.000.

### B5. Value weighting adds variance and zero signal — which makes `W10` not a wrong method.

Because `v = base · mult_g^{Y*}` with `base ⟂ z` (§A1), `E[v | Y*=1, s]` is **constant in `s`**. Value-weighted
recall and count recall therefore have the *same* expectation within segment; `mult_g` cancels out of the
ratio entirely. The claim in `wrong_methods.md` that "fraud value is concentrated differently from fraud count
(marketplace fraud is 1.9× the value)" is a between-segment constant that has no within-segment effect on a
ratio.

Measured, worst-case absolute error against truth over 4 worlds and all 9 graded quantities:

| quantity | max err, accepted (A1/A3) | **W10 (a "wrong" method)** | W7 | W1 |
|---|---|---|---|---|
| `recall_v6.ecom_cnp` | 0.0144 | **0.0025** | 0.1020 | 0.1131 |
| `recall_v7.ecom_cnp` | 0.0134 | **0.0005** | 0.0186 | 0.0434 |
| `recall_v6.marketplace` | 0.0117 | **0.0007** | 0.1067 | 0.1480 |
| `recall_v7.marketplace` | 0.0139 | **0.0021** | 0.0088 | 0.0303 |
| `recall_v6.travel` | 0.0160 | **0.0002** | 0.1011 | 0.0805 |
| `recall_v7.travel` | 0.0167 | **0.0011** | 0.0129 | 0.0244 |
| `delta.*` (worst) | 0.0256 | **0.0037** | 0.0761 | 0.0561 |

**`W10_count_recall` is closer to the ground truth than both accepted estimators, on every graded quantity, in
every world.** It is not "the designed decision-correct / analysis-wrong case"; it is a correct estimator of
the same quantity, and the value-weighting in the estimand is pure added variance. Shipping W10 in the
mutation suite would produce a mutation that cannot fail.

Fixing this requires making `v` depend on `z` — which immediately makes §A1's label-free heuristic *more*
powerful, not less. The two defects are coupled.

### B6. Positivity, post-treatment conditioning, `Y*` as a potential outcome

These are the parts the design gets right, and I could not break them:

- Positivity holds where claimed (`q_block = 0.25`, `q_review = 0.12`, strictly positive, no covariate-driven
  zeros). The review-capacity positivity violation is real but, per B2, consequential for nothing.
- `Y*` is drawn before any decision (`g31_sim.py:121`) and no downstream variable feeds back into it. The
  "blocking does not change `Y*`" claim is true *in the generator*. It is not true in the world (§E4), but it
  is not an internal inconsistency.
- Band is post-treatment but is a deterministic function of the pre-decision `s6`, so conditioning on it is
  conditioning on `s6`, which is legitimate.

### B7. The ratio estimator is noisy enough to matter, and the bar is decorative

Across 5 worlds, `A1`'s error on Δ reaches **0.0256** and `A1` vs `A3` disagree by up to **0.0212**. The adopt
bar is **0.010**. So the accepted estimators' own sampling spread is 2–2.6× the decision bar. The decisions
are nevertheless stable — but only because the design put `|Δ|` at 0.10, ten times the bar. The bar therefore
does no work: it never binds, and an agent that reports Δ with a sign and no magnitude discipline passes.

An estimate of the block-band contribution rests on roughly **455–847 fraud events per segment** (world 777:
ecom 582, marketplace 847, travel 455) carrying weight 4. That is where the 0.02 noise comes from.

### B8. 25% bypass and 3.5–5.4% prevalence

Both are flagged as open items in `dgp_design.md:132-141`, correctly, and both are worse than the document
admits:

- **Prevalence.** 3.5–5.4% of transactions ending in a *fraud chargeback* is not "at the very top of what a
  real processor would see". Card-network fraud-monitoring programmes escalate around 0.9% of value; a book
  running 4% by count would be terminated, not analysed. The realistic figure is 25–100× lower. This is not
  cosmetic: every power claim in the design is computed at the inflated rate, and §B7 already shows the
  estimator is marginal *at* 4%. At 0.5% the holdout block band would carry ~70 fraud events per segment and
  the accepted estimators' Δ noise would exceed |Δ| for at least one segment.
- **Bypass.** `q_block = 0.25` **identical across all three segments and constant across all 365 days**, with
  no ramp, no pause, no value cap, no loss budget. Deliberately settling a quarter of the transactions your
  model is most confident are fraud, at a band that is roughly half fraud, for a full year, is not a holdout
  programme — it is an uncapped loss. Real champion-challenger bypasses in payments run 0.5–2%, are usually
  ticket-capped, and are frequently review-band-only. The perfectly flat rate is the single most
  archaeologically implausible artefact in the extract, and an agent will find it *because* it is flat.

### B9. The maturity horizon is not a well-defined quantity

`delay` is `LogNormal` **capped at 120** (`g31_sim.py:153-156`). The true support is therefore [1, 120] and the
true maturity horizon is **120 days**, exactly. `maturity_days()` instead returns the 99th percentile of
observed lags: 43–44 / 85–90 / 63–67. Those are a convention, not a fact. An analyst who reads the
chargeback-operations document, sees the 120-day dispute window, and uses 120 is *more* correct than the
reference and produces different numbers (`L2b` differs from `A1` by up to 0.02 on levels). See §D3.

---

## C. REDUNDANCY

### C1. The project has already rejected this task, in writing, by name.

`candidate_selection.md`, G01 row:

> "**G01 collections label maturity** — label maturity × observation process × policy feedback … **design
> gate: REDESIGN specified, Phase-0 stopped** … HARD but blocked: graded statistics do not separate the
> population errors **without restoring the G24-duplicating IPW layer**."

and

> "Two Phase-0 iterations showed **the business decision is insensitive to the population errors**."

G31 is "label maturity × observation process × policy feedback" with `collections` replaced by `payments`,
and it *is* the restored IPW layer. Both of G01's recorded blockers reproduce here exactly and independently:
the decision is insensitive to the population errors (§A3: 21/30 wrong segment-decisions correct), and the
only load-bearing statistical content is IPW with a logged propensity (§B3). G31 is G01's rejected option,
re-proposed without the redesign.

### C2. It is Task 03, which is already built and scores 3/3 (TOO EASY).

`task03_design.md:8-11`:

> "Can an agent recover the *evaluation estimand* of a deployed model — which population's outcomes measure
> what the score is used for — when **an operational feedback loop (the model's own routing decisions) changes
> which outcomes exist**, and preserve it at the correct grain … rather than accepting the population that
> happens to have labels?"

`domain_comparison.md:95-96` states G31's distinguishing claim as:

> "**the thing being evaluated created the population it is being evaluated on.**"

These are the same sentence. `candidate_selection.md` records Task 03 at pass@3 = 1, 3/3, **"TOO EASY"**,
demoted to "pilot/development only". The prior for a second task on the same mechanism is that it is easy,
and §A1–A3 confirm it.

### C3. It is G24 with the hard part deleted.

G24's difficulty is *reconstructing* an unlogged propensity through a rules layer and a cache TTL. G31's
propensity is `q = 0.25` or `0.12`, written in a policy document, constant, two-valued, and exposed as a
column. `estimand_and_identification.md:168-175` pre-empts this by noting that post-stratification (`A2`) and
outcome regression (`A3`) also work — but `A2` and `A3` both call `_unbiased_sample()`
(`g31_estimators.py:99, 99`), i.e. they are IPW with extra steps bolted on top of the identical weighted
sample. There is no genuinely weight-free accepted estimator in the file. The stated escape from the G24
charge does not exist in the code.

### C4. It is G25's blocked gradeability problem.

G25 was stopped because "metric levels not gradeable at useful precision". §B5/§D1 show the same thing here,
measured: accepted-estimator error up to 0.026 on Δ, with a pre-registered wrong method at 0.004.

---

## D. GRADEABILITY

### D1. No tolerance separates accepted from wrong.

To admit `A1` and `A3` (both explicitly accepted) the tolerance on recall levels must be ≥ 0.017 absolute and
on Δ ≥ 0.026. At that tolerance:

- `W10_count_recall` passes everything, comfortably, in every world (max error 0.0037). It is not gradeable
  as wrong at *any* tolerance, because it is not wrong (§B5).
- `W7_ipw_on_v6_band` is inside the accepted band on `recall_v7.marketplace` (0.0088 vs 0.0139 accepted) and
  `recall_v7.travel` (0.0129 vs 0.0167) in its best world. Two of six level quantities do not separate.
- `W1_complete_case` reaches 0.0244 on `recall_v7.travel` and 0.0303 on `recall_v7.marketplace`, against an
  accepted band of 0.017 — separated, but by less than 2×, on a single-world basis that has not been
  characterised over the seed distribution.

The pre-registered criterion in `wrong_methods.md` demands joint pass probability below 10⁻³. `W10`'s pass
probability is ≈ 1.

### D2. Five of the six graded groups are the same number.

The graded set is `maturity_days`, eligible population count, fraud-value total, `R_{m,g}`, `Δ_g`, `adopt_g`.

- `Δ_g` is `R_v7 − R_v6`; `adopt_g` is `sign(Δ_g − 0.010)`. Not independent.
- `R_{m,g}` share a denominator with the fraud-value total; given the total, the two recalls are the same
  weighted sum split two ways.
- The eligible population count is `n` per segment — 438,000, 438,000, 438,000 (`seg_share` is 1.0/1.0/1.0 in
  the base regime). It is a `COUNT(*)` on a table, with no join, no dedup, no filter. It tests nothing, and
  it is constant across segments, which makes it a giveaway rather than a check.

So the six groups collapse to roughly two independent facts: the weighted fraud-value total, and
`maturity_days`. The G05/G24 lesson ("grade estimands, not only decisions") is nominally honoured and
substantively not.

### D3. A correct analysis can legitimately disagree with the reference — on the one quantity that isolates a mechanism.

`maturity_days` has no ground truth. The generator caps delay at 120 (`g31_sim.py:155`), so 120 is the
defensible answer from the documents; the reference uses an arbitrary 99th-percentile convention
(`g31_estimators.py:20`) giving 44/86/65; a 95th percentile, a 99.5th percentile, a Kaplan–Meier horizon, or
"the dispute window in the ops document" all give different, defensible numbers. Grading it rewards one
implementation recipe. Not grading it removes the only quantity that isolates a mechanism — and, per §B1,
that mechanism does not move any other number anyway.

### D4. A decision-only grader scores this task ~70%

Per §A3. And a quantity-grader is defeated by §D1. There is no configuration in between that works.

---

## E. REALISM

A senior payments-risk data scientist would not recognise this incident. Specifics:

1. **Volume.** 1,200 authorisations per segment per day = **3,600/day, 1.31M/year** for an entity that has a
   VP Risk, three merchant verticals, a staffed manual-review queue with SLA auto-decline, and a formal bypass
   holdout programme. That is the org chart of a processor doing 10⁸–10⁹ authorisations a year. 3,600/day is a
   single mid-sized merchant, and it would not staff a review queue at all.
2. **Prevalence.** 3.5–5.4% fraud-chargeback rate (§B8). Off by 25–100×.
3. **No retries.** `I2` ("blocking does not change `Y*`") is defended as a "domain fact". It is the opposite
   of a domain fact in CNP payments: a declined attempt is retried, often within seconds, often on another
   card or another BIN, often successfully. "What happens to the traffic you decline" is the *first* question
   a payments risk analyst asks about a bypass holdout. The design removes the domain's signature
   complication and then cites its absence as a strength.
4. **Unworked reviews are auto-declined.** 30–80% of the review band is declined without ever being looked at
   (`review_capacity` 0.20–0.70). Real review queues time out to **approve**, or the authorisation expires and
   the merchant retries; silently declining 60% of a flagged-but-unreviewed band would produce a merchant
   revolt and an approval-rate incident long before it produced a modelling problem.
5. **Perfect investigators.** `released = reviewed & (y == 0)` (`g31_sim.py:149`) means the reviewed-and-released
   population has an observed chargeback rate of **exactly 0.000**, in every segment, every month. That is not
   a simplification an analyst overlooks; it is a number that screams. In reality manual review runs 60–85%
   precision and the release population has a non-trivial chargeback rate — that rate is, in fact, the single
   most-watched number in a review operation.
6. **A flat, segment-invariant, year-long 25% block-band bypass** (§B8).
7. **No entity structure.** `z` is one i.i.d. standard normal per row. No cardholders, no BINs, no issuers, no
   devices, no merchants within a segment, no velocity, no fraud rings, no bursts. Fraud is the canonical
   clustered, bursty, entity-linked phenomenon; here every transaction is independent. Any variance estimate
   an agent computes would be right in this world and wrong in every real one, which is a bad thing to teach
   a benchmark to reward.
8. **Equal, flat volumes.** `seg_share = {1.0, 1.0, 1.0}` and uniform `day`. Travel has the same volume as
   ecom, every day of the year, with no seasonality — in a segment whose defining feature is seasonality.
9. **The headline numbers in the brief match nothing.** The VP's email says v7 "lifts caught-fraud value from
   **61% to 78%**". The analysis the email is describing, `W2_age_cutoff_30`, produces v6 = **7.6–9.7%** and
   v7 = **22.6–38.9%** across my worlds. No estimator in `g31_estimators.py` — accepted or wrong — produces
   anything near 61%/78% for v6/v7 in any segment or pooled. The narrative and the generator are not
   connected.
10. **Look-ahead in the score construction.** `_rank01` (`g31_sim.py:103-109`) ranks each score over the whole
    year at once, so a January transaction's score depends on December's transactions. Cosmetic for the
    estimand; a leak a careful analyst would notice and be confused by.

---

## F. THE KILLER OBJECTION

**The task's entire gradeable content is one bit — "is marketplace the segment where v7 is worse?" — and that
bit is available three separate ways without doing any of the work the task claims to measure: it is stated in
the business brief in the correct direction for the correct segment; it is recoverable at 15/15 accuracy by
summing a transaction-value column over each model's top 4% with no outcome label, no weights, no maturity
horizon and no holdout; and it is signposted by marketplace being the visible outlier on five independent
descriptive dimensions at once.** Beneath that bit, the numeric quantities that were supposed to catch an
agent taking a shortcut cannot do so, because the accepted estimators' own sampling error (up to 0.026 on Δ,
0.017 on recall levels) is larger than the gap to a pre-registered *wrong* method (`W10` at 0.004, which is in
fact a consistent estimator of the same quantity), and because the two mechanisms that were supposed to add
depth are numerically inert — ignoring censoring completely moves Δ by ≤0.009 and adding back the
"leaking" reviewed-and-released rows changes the answer by literally 0.0000. What remains is a single inverse
probability weight with a constant, two-valued, logged propensity: strictly easier than G24, structurally
identical to Task 03 (built, 3/3, "TOO EASY"), and precisely the design the project's own G01 gate stopped
with the note that restoring statistical content "duplicates G24" and that "the business decision is
insensitive to the population errors". Building this spends a build cycle and an uncontaminated baseline to
re-learn, in payments nouns, a conclusion already recorded in the repository.

---

## Findings by severity

### HIGH — blocks the build

| # | Finding | Evidence |
|---|---|---|
| H1 | **Label-free cheap solve.** Comparing gross transaction value captured in each model's top-`c_g` recovers `sign(Δ_g)` exactly in expectation and 15/15 in practice, using no outcome data at all. Forced by `v = base·mult^{Y*}` with `base ⟂ z` (`g31_sim.py:122-123`) | §A1 |
| H2 | **`W10_count_recall` is not a wrong method.** Value- and count-weighted recall have identical expectations here; W10 beats both accepted estimators against truth on all 9 graded quantities in all 4 worlds (max err 0.0037 vs 0.0256) | §B5, §D1 |
| H3 | **The delay/censoring leg is inert.** Setting the maturity horizon to 0 (or to the condemned 30 days) changes Δ by ≤0.0091, below the 0.010 adopt bar and below the accepted estimators' own noise. Forced by I3 + a ratio estimand | §B1 |
| H4 | **The selective-verification leg is inert.** Released rows have `Y*=0` and contribute 0 to a fraud-value ratio; `L4_inclReleased` is identical to `A1` to 4 dp in 4/4 worlds. `dgp_design.md:142-144` states the opposite | §B2 |
| H5 | **"Three mechanisms" is one mechanism.** All statistical content reduces to `1/q` on the logged bypass. The design's "central claim" that fixing any two leaves a biased answer is false as measured | §B3 |
| H6 | **No tolerance separates accepted from wrong.** Admitting A1/A3 requires ≥0.017 (levels) / ≥0.026 (Δ); at that tolerance W10 passes everything and W7 passes 2 of 6 level quantities | §D1 |
| H7 | **Decision leaked in the prompt.** The VP's email names marketplace, names the direction, and attributes it to a stakeholder. Combined with an "always v7" prior this yields the graded decision with zero analysis | §A4 |
| H8 | **Redundancy with an already-rejected design.** G01's gate recorded both of this design's failure modes verbatim ("decision insensitive to the population errors"; "restoring statistical content duplicates G24"). Task 03's stated question is G31's stated distinguishing claim, and Task 03 is built at 3/3 "TOO EASY" | §C1, §C2 |
| H9 | **No simulation evidence exists.** `estimand_and_identification.md:138` and `wrong_methods.md` both cite `simulation_results.md` for the load-bearing separation claim (|Δ| ≈ 0.10–0.12 vs spread 0.003–0.015). **That file does not exist.** `results/` contains only `gate_run.log`, showing the gate at world 8 of 20 in the first of five regimes. The measured accepted-estimator spread is 0.003–**0.021**, not 0.003–0.015 | `ls results/`, §B7 |

### MEDIUM — must be fixed before any build

| # | Finding | Evidence |
|---|---|---|
| M1 | `eval_block_rate ≡ block_rate + review_rate` exactly, in 5/5 regimes × 3 segments, so `1[s6 ≥ τ_v6] ≡ (band != ALLOW)` for 100.0000% of rows. `R_v6` needs no threshold; `W4`/`W9` return `recall_v6 = 1.000000` in all segments and are self-refuting rather than plausible | §B4 |
| M2 | Constant `v7\|v6\|v7` passes 4 of 5 regimes; the only lever that flips it is `gamma7["marketplace"]`, so hidden extracts are trivially correlated unless at least half are `v7_wins_everywhere` | §A2 |
| M3 | Complete-case and every censoring-only analysis get 2 of 3 segments right in 5/5 worlds; 21 of 30 wrong-method segment-decisions are correct | §A3 |
| M4 | Three pre-registered wrong methods (`W5`, `W7`, `W10`) produce the exactly correct decision string; `W7` does so on a marketplace Δ of +0.00017 against a 0.010 bar — luck, not separation | §A3 |
| M5 | The graded set collapses: `Δ` and `adopt` are functions of `R`; `R_v6`/`R_v7` share a denominator; the "eligible population count" is `COUNT(*)` = 438,000 in all three segments | §D2 |
| M6 | `maturity_days` has no ground truth (delay is capped at 120, so 120 is defensible; the reference uses a 99th-percentile convention). Grading it rewards a recipe and can fail a more correct analysis | §D3, §B9 |
| M7 | Accepted-estimator Δ noise (0.026) is 2.6× the adopt bar (0.010); the bar never binds because `|Δ|` was set at 10× it. At a realistic 0.5–1% prevalence the noise would plausibly exceed `|Δ|` in at least one segment | §B7, §B8 |
| M8 | `observed()` returns the full `spec` (`g31_sim.py:216`), including `a`, `gamma7`, `sigma6/7`, `q_*`, `eval_block_rate` and `delay_cap`. Every accepted estimator reads `q`, the budget and the 120-day cap straight from it. Nothing in the Phase-0 evidence shows the estimators work when those must be read out of documents — which is precisely the skill being claimed | `g31_estimators.py:20, 33, 66-67, 183` |
| M9 | The brief's headline figures (61% → 78%) correspond to no output of any estimator in the file (the legacy analysis yields 7.6–9.7% and 22.6–38.9%) | §E9 |
| M10 | Realism: 1.31M auths/year for a multi-vertical processor; 3.5–5.4% chargeback prevalence; flat 25% block-band bypass for 365 days across all segments; SLA auto-**decline** of unworked reviews; perfect investigators giving an exactly 0.000 release chargeback rate; no retries; no cardholder/BIN/merchant clustering; equal flat segment volumes including travel | §E |

### LOW — worth noting

| # | Finding |
|---|---|
| L1 | `_rank01` ranks each score over the full year, so a January score depends on December transactions — a look-ahead transform in the generator (`g31_sim.py:103-109`) |
| L2 | `wrong_methods.md` uses "W9" for two different things: the dropped candidate "use current review policy to reconstruct historical labels" and the shipped `W9_holdout_only`. Same paragraph |
| L3 | `delay` is drawn independent of `day`, so there is no seasonality, weekend batching or issuer-cycle structure in chargeback arrival |
| L4 | `high_prev` is the only regime that meaningfully changes the numbers; `tight_capacity` and `slow_cb_big_holdout` perturb mechanisms shown to be inert (§B1, §B2), so three of five regimes are near-duplicates of `visible` for every graded quantity |
| L5 | `A2_poststrat` and `A3_impute` both call `_unbiased_sample()`, so the claim that IPW is "not the only route" (`estimand_and_identification.md:172-175`) is not supported by the code: all four accepted families share one weighted sample |
| L6 | `domain_comparison.md:104` anticipates exactly the right risk ("the bypass holdout … is the single artefact that, if spotted, unlocks the task") and then asserts the design mitigates it via W3/W7/W9. Measured: W7 gets the right decision 5/5 and W9 returns 1.000 |

---

## What would have to change

Not a fix list — a statement of how large the required change is. To survive these findings the design would
need: (i) `v` correlated with `z` so value-weighting carries signal — which strengthens H1; (ii) a mechanism
that makes censoring non-ignorable, i.e. delay dependent on `Y*` or on score — which breaks I3 and the
identification proof; (iii) `eval_block_rate` decoupled from the band boundary; (iv) a second, independent bit
of gradeable signal so the answer is not one binary; (v) the marketplace hint removed from the brief; (vi)
prevalence and volume moved to realistic values, which costs the statistical power the design currently
relies on. Items (i) and (ii) are mutually antagonistic with the identification argument as written. That is
not a revision; that is a different task.
