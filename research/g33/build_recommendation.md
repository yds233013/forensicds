# G33 build recommendation

# **C. DROP.**

Not REDESIGN. The defect is in the relationship between entity resolution and the class of estimand it can
affect, not in the parameters, and the fix collides with Task 01.

## 1. Kill criteria fired

| | Criterion | Evidence |
|---|---|---|
| **K4** | raw/current IDs produce essentially correct downstream metrics | raw shipment codes: mean abs error **0.027** on a truth of 0.16–0.33; four cheap heuristics land within **0.004** |
| **K9** | constant business decision works across regimes | constant `within_limit` correct in **54/60** worlds across all five regimes, including the one built to flip it |
| **K12** | entity errors do not materially affect the downstream result | identity-reconstruction errors move top-1 share by **0.6–8%**; only coarse grain errors move it (65–78%) |
| **K8** (partial) | one wrong grain dominates so strongly that no investigation is needed | grain choice accounts for essentially all of the separation |
| **K6 / K8 dilemma** | — | the grain must be documented (or competent analysts defensibly disagree), and documenting it hands over the only bit that matters |

Independently: the truth straddles the 25% board limit as a function of seed (5 breach / 7 within_limit
across 12 visible worlds), so a frozen fixture's decision would be an artefact of seed choice.

## 2. The generalisable finding

**Entity-resolution error changes a statistic materially only when the statistic depends on the
within-entity versus between-entity decomposition.** Churn-versus-expansion, revenue restatement and
retention are of that type: merging two customers converts a churn plus a new logo into an expansion, so a
single wrong merge moves the headline number. Concentration ratios, rate averages and shares are **not** of
that type: they aggregate over many units with amount weights, so errors that touch a few units partly
cancel and cannot move the aggregate unless they touch the largest unit — which they almost never do
(measured: 1 of 6 worlds).

The consequence is a trap for benchmark design:

- pick a **within-vs-between** estimand and the task is genuinely sensitive — but that is Task 01's ground
  (**K5**);
- pick any other estimand and the entity work stops mattering (**K12**), leaving only the grain choice,
  which is one documented bit (**K8**).

I chose concentration specifically to escape Task 01, and it escaped by becoming insensitive. That is not a
parameter failure. Two further rounds of tuning — forcing the top node to be the merged one, forcing it to
be fragmented across codes — would be tuning around a kill criterion, which the brief forbids and which is
what I would be doing if I recommended B.

## 3. What would have to be true to revisit this

Not a to-do list; a precondition. Any future attempt must **demonstrate before building the generator** that
its chosen estimand satisfies:

1. an entity error confined to non-top units moves the graded quantity by more than the decision margin;
2. the correct decision flips across regimes, so a constant answer fails;
3. the analytical grain is *not* the dominant source of separation — identity reconstruction within the
   grain must carry at least as much;
4. the estimand is demonstrably not a revenue/retention decomposition, i.e. not Task 01.

Conditions 1 and 3 are in tension with 4. Until someone shows an estimand satisfying all four, this line
should stay closed.

## 4. Cost of the finding

No model run, no API spend, no candidate directory. Roughly one generator, eleven wrong methods, ten cheap
heuristics and five diagnostics — all local numpy, seconds per world.

## 5. Process note: the two-gate rule worked

G31's lesson was that a statistical gate cannot see a solver that bypasses the statistics. This turn the
cheap-solve panel was written **alongside** the generator rather than after it, and it fired on the first
run — `C_constant_within`, `C_line_counts_raw_code` and `C_post_rework_only` were all visible in the first
combined output. The statistical gate on its own would have looked *good*: three valid families agreeing to
four decimals, and four wrong methods rejected at large margins.

One additional check earned its place and should become standard: an earlier draft of this generator
resolved registry splits by a material-group parity rule that no artefact exposed — the graded truth would
have required a convention the solver could not observe. It was caught by asking, before running anything,
"for each graded fact, what evidence would a real analyst have?" That question should be a required gate
item, not an optional one.

## 6. Benchmark position

The measured pool stands at 1/5 = 20% task-level pass@3. G33 would have added cost and no capability. Two
consecutive design rejections (G31, G33) are not a bad outcome — both were rejected before implementation,
each for a specific measured reason, at a cost of local compute only.

**Recommendation: DROP G33. Do not start G34 without explicit authorisation.**
