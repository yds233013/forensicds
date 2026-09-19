# G31 hidden-regime plan

Four hidden regimes, each preserving the scientific invariant (three missingness mechanisms, identification via
the logged bypass) while changing superficial statistics enough that a visible-data overfit fails. Implemented as
`REGIMES` in `g31_sim.py`; **no Harbor fixtures exist and none will be generated in this turn.**

The invariant every regime preserves:

> The labelled population is shaped by the incumbent model's own decisions; the estimand is defined over the full
> eligible population; the logged bypass plus the maturity horizon is what makes it recoverable.

| Regime | What changes | What stays fixed | What it defeats |
|---|---|---|---|
| **visible** | baseline | — | — |
| **A. `high_prev`** | fraud prevalence roughly doubles in every segment (`a` shifted +0.7) | observation mechanism, bypass rates, capacity, delays, which segment v7 loses in | hard-coded fraud rates; any analysis that calibrated a constant to the visible book |
| **B. `slow_cb_big_holdout`** | chargeback lag lengthens substantially (`delay_mu` +0.5 to +0.6, so marketplace moves from ≈ 87 to well past 120 days) **and** the bypass programme is enlarged (`q_block` 0.25 → 0.35, `q_review` 0.12 → 0.18) | prevalence, capacity, segment ordering | a hard-coded maturity horizon; a hard-coded bypass weight. Both move at once, so a method that hard-codes either is caught |
| **C. `tight_capacity`** | review capacity falls sharply (0.55/0.40/0.70 → 0.30/0.20/0.45) and the segment mix changes (ecom 1.5×, marketplace 0.7×, travel 0.8×) | prevalence, delays, bypass rates | anything that leans on investigator determinations — the verified-label pool shrinks by roughly half, so `W4_reviewed_only` degrades further while correct methods are untouched |
| **D. `v7_wins_everywhere`** | the challenger's nuisance loading is removed in marketplace (`gamma7` 0.95 → 0.15) and its noise drops, so **v7 is genuinely better in all three segments** | everything about the observation process | **a constant decision.** The correct answer flips from `v7 \| v6 \| v7` to `v7 \| v7 \| v7` |

## Why regime D is the load-bearing one

Without it, "recommend v7 in ecom and travel, v6 in marketplace" is a fixed string that a lucky or over-fitted
agent could emit. Regime D makes the correct per-segment answer depend on the data rather than on the scenario,
and it is the regime that a hard-coded answer cannot survive.

A fifth regime worth considering if the task is built — **a policy-version change** partway through the window,
where the bypass rate and review thresholds are revised and both versions appear in the decision log. This would
force the analyst to join decisions to the policy version in force at the time rather than to the current policy.
It is held back for now because it adds a second reconstruction problem on top of the statistical one and risks
tipping the task toward Task 02's territory. It should be adopted only if the simulation shows the base design is
too easy, which on present evidence it is not.

## Transfer requirement

A correct method must recover the estimand in **all** regimes without re-tuning: no hard-coded maturity horizon,
no hard-coded bypass probability, no hard-coded segment ordering, no hard-coded decision. Each of the four
accepted families satisfies this by construction — `maturity_days()` estimates the horizon from mature cohorts,
and the bypass probability is read from the policy table rather than assumed.

The per-regime results are in `simulation_results.md`.
