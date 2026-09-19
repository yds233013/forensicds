# G31 data-generating process

Research only. Code: `g31_sim.py`. No task files, no model.

## 1. The world

A payments processor, one year of authorisation attempts, three merchant segments
(`ecom_cnp`, `marketplace`, `travel`). An incumbent risk model **v6** is in production and drove every historical
decision. A challenger **v7** has been scored offline on the same pre-decision features.

Scale in the pilot: 1,200 attempts/day/segment × 365 days ≈ **1.31 M rows per world**.

## 2. Variables, by role

| Variable | Meaning | Role |
|---|---|---|
| `day` | day of the authorisation | PRE-DECISION, OBSERVED |
| `segment` | merchant segment | PRE-DECISION, OBSERVED |
| `z` | latent fraud propensity index | **LATENT** (never in any artefact) |
| `w` | nuisance feature correlated with nothing causal | **LATENT** |
| `Y*` | would this attempt incur a fraud chargeback **if allowed to settle** | **LATENT**, SELECTIVELY OBSERVED |
| `v` | transaction value | PRE-DECISION, OBSERVED |
| `s6` | incumbent score | PRE-DECISION, OBSERVED (drove policy) |
| `s7` | challenger score | PRE-DECISION, OBSERVED (never drove anything) |
| `band` | BLOCK / REVIEW / ALLOW from the v6 policy | POST-DECISION, OBSERVED |
| `holdout` | logged bypass flag | POST-DECISION, OBSERVED, **randomised** |
| `reviewed` | worked by an investigator | POST-DECISION, OBSERVED, **selected on s6** |
| `review_fraud` | investigator determination | POST-DECISION, SELECTIVELY OBSERVED |
| `settled` | did the authorisation complete | POST-DECISION, DERIVED |
| `chargeback` | fraud chargeback visible at the extract | POST-DECISION, DELAYED + SELECTIVELY OBSERVED |
| `cb_day` | day the chargeback posted | DELAYED, right-censored at the extract |

## 3. Structural equations

```
z  ~ N(0, 1)                                       latent propensity
w  ~ N(0, 1)                                       nuisance feature
Y* ~ Bernoulli( sigmoid( a_g + b·z ) )             latent outcome,  b = 3.4
v  ~ LogNormal( mu_g, 0.8 ) · (fraud_mult_g if Y*=1)

r6 = z + N(0, sigma6_g) + gamma6_g · w             incumbent index
r7 = z + N(0, sigma7_g) + gamma7_g · w             challenger index
s6 = rank01(r6),  s7 = rank01(r7)                  calibrated score columns

band = BLOCK   if s6 >= t_block_g                  t set so BLOCK = top 1.0-1.2%
       REVIEW  if t_rev_g <= s6 < t_block_g        REVIEW = next 2.4-3.8%
       ALLOW   otherwise

holdout ~ Bernoulli( q_block_g  if band = BLOCK
                     q_review_g if band = REVIEW )  q_block = 0.25, q_review = 0.12

reviewed = top (review_capacity_g) fraction of non-holdout REVIEW rows, ordered by s6 descending
released = reviewed AND Y* = 0                     investigators release what they judge legitimate

settled  = (band = ALLOW) OR holdout OR released

delay ~ round( LogNormal( delay_mu_g, delay_sd_g ) ), capped at 120 days
chargeback_visible = settled AND Y*=1 AND (day + delay <= extract_day)
```

`gamma7_marketplace = 0.95` is the single parameter that makes the challenger **worse in one segment**: in
marketplace, v7 loads heavily on a nuisance feature that carries no fraud signal. Elsewhere v7 is simply less
noisy than v6 (`sigma7 < sigma6`).

## 4. Data-flow graph

```
                 z  (latent propensity)                 w (nuisance)
                 │                                       │
        ┌────────┼───────────────┬──────────────┐        │
        ▼        ▼               ▼              ▼        ▼
       Y*       r6 ─► s6        value v        r7 ◄──────┘
        │        │                              │
        │        ▼                              │  (scored offline, drove nothing)
        │    POLICY: band = BLOCK / REVIEW / ALLOW
        │        │
        │        ├──► holdout ~ Bern(q_band)  ────────┐   RANDOMISED
        │        ├──► reviewed = top-k by s6 ───┐     │   SELECTED ON s6
        │        │                              │     │
        │        ▼                              ▼     ▼
        │     settled  ◄──────────── released ◄─┘   (holdout forces settle)
        │        │
        └────────┼──► chargeback (only if settled AND Y*=1)
                 │            │
                 │            ▼
                 │        + delay ──► right-censored at extract_day
                 ▼
        review_fraud (only if reviewed; equals Y*)
```

**The load-bearing feature of this graph:** `s6` sits on the path from `z` to *every* observation mechanism.
The incumbent model determined who was blocked, who was queued, who was worked, and therefore whose outcome is
knowable at all. The population with labels is a **v6-shaped** population, and v7 is being judged on it.

## 5. The three missingness mechanisms, and why each repair is insufficient alone

| # | Mechanism | Rows affected | Repair | What it still leaves broken |
|---|---|---|---|---|
| 1 | **Structural non-observation.** A blocked authorisation never settles, so `Y*` can never be realised | BLOCK band (~1%) minus its holdout | use the bypass holdout, weight by `1/q_block` | maturity, and the review band |
| 2 | **Selective verification.** The review queue is worked top-down by `s6` under capacity; unworked rows are declined at SLA and yield nothing | REVIEW band (~3%) | use the review-band holdout, weight by `1/q_review`; **do not** treat investigator labels as representative | maturity, and the block band |
| 3 | **Delay / right-censoring.** Chargebacks arrive over 1–120 days with segment-specific lag | every settled row | maturity horizon per segment, estimated from fully mature cohorts | selection, in both bands above |

Fixing any two of the three still leaves a biased answer. That is the design's central claim, and it is the thing
the simulation gate tests (`W3` fixes 3 only, `W9` fixes 1+2 only but on the wrong population, `W7` attempts 1+2+3
with the wrong weight).

## 6. Positivity

Positivity holds where it must and fails where it should, and the failure is informative:

- **Holdout:** `q_block = 0.25`, `q_review = 0.12`, strictly positive everywhere in BLOCK and REVIEW. This is what
  makes the estimand identifiable at all.
- **Review determinations:** `P(reviewed | s6, band)` is **0** below the capacity cutoff inside the review band.
  Investigator labels therefore cannot, on their own, identify anything about the lower part of the band — a real
  positivity violation that an analyst must notice rather than paper over. This is what makes `W4_reviewed_only`
  wrong for a reason, not merely noisy.
- **Maturity:** `P(resolved | day)` is 0 for the most recent cohorts and 1 for old ones, and depends on nothing
  else. Restricting to resolved rows is therefore a random restriction with respect to `Y*`.

## 7. What is deliberately absent

- **No treatment effect.** Blocking does not change `Y*`; it only prevents it from being realised. `Y*` is a
  property of the attempt, fixed before any decision. This keeps the task away from G05.
- **No label noise in the investigator determination.** `review_fraud = Y*` exactly. The problem is *who* gets
  reviewed, not whether the review is right. Adding investigator error would add a second unidentified quantity
  for no scientific gain.
- **No feedback of v7 into the data.** v7 never drove a decision, so there is no logging-policy reconstruction
  problem. This keeps the task away from G24.
- **No score drift over time.** The policy is stationary in the visible regime; a policy-version change is held
  back as a possible hidden regime rather than baked into the base world.

## 8. Realism caveats, stated plainly

- **Fraud prevalence in the pilot is 3.5–5.4%**, which is at the very top of what a real processor would see and
  reflects a deliberately high-risk book. It is set this high for statistical power in a 1.3 M-row pilot world. If
  the task is built, prevalence should be reduced toward 1–2% and volume raised to compensate, or the estimand
  should move to a wider operating point. **This is an open item, not a settled parameter.**
- **A 25% bypass rate on the block band** is high but defensible: the block band is ~1% of volume, so the bypass
  is ~0.25% of all authorisations, and a risk team that intends to keep comparing models at the operating point
  has to buy that measurement somehow. The task documents must make the programme's sizing rationale explicit so
  that it reads as policy rather than as a convenience.
- **Investigators release exactly the legitimate cases** (`released = reviewed AND Y*=0`). This is a
  simplification; it makes the reviewed-and-released rows a deterministic function of `Y*`, which is precisely why
  the accepted estimators must exclude them rather than use their chargeback outcomes.
