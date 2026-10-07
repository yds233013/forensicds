# Real-distribution provenance — g50 (Boost courier-incentive national rollout)

1. **Professional role.** Finance-facing decision scientist re-deriving an experiment readout.
2. **Industry.** On-demand delivery marketplace.
3. **Business decision.** Whether the July investment committee approves Boost for national rollout
   on every eligible order, against a £0.19-per-boosted-order incentive cost and a £12.70 cost per
   late delivery — a 1.4961 pp break-even on the late-delivery rate.
4. **Realistic inherited artifacts.** An operational warehouse (orders, zones, markets, courier
   shifts, experiment assignment, experiment configuration by phase, incentive ledger, ops events),
   the incumbent `northline_eval` package that produced the published readout, the readout itself, a
   dispatch-queue design note, an experiment plan, metric definitions, and the rollout decision memo.
5. **Statistical/ML problem.** Interference / unit of intervention. Boost is randomised per order in
   phase 2, but a boosted offer pre-empts an unboosted offer in the same market-hour courier queue, so
   the arm contrast measures redistribution of a shared resource rather than the effect of turning the
   incentive on for everyone. The market-level phase-1 soak is the design that identifies the rollout
   quantity, and it is the design the incumbent analyst rejected as underpowered.
6. **Why this happens in real organizations.** Treatment applied to one unit affects outcomes for
   units connected through the platform — a SUTVA violation. The empirical magnitudes are large and
   documented: Blake and Coey (2014) show interference among bidders made an auction experiment's
   treatment-effect estimate wrong by a factor of two, and Fradkin (2019) finds a marketplace
   experiment on search/recommendation can overestimate the true effect by 50%. Platforms respond with
   cluster or switchback designs precisely because per-unit randomisation does not answer the rollout
   question when the resource is shared.
7. **Public sources.**
   - *Interference, Bias, and Variance in Two-Sided Marketplace Experimentation* (WWW '22): https://dl.acm.org/doi/fullHtml/10.1145/3485447.3512063 · https://arxiv.org/pdf/2104.12222
   - *Experimental Design in Two-Sided Platforms: An Analysis of Bias*: https://arxiv.org/pdf/2002.05670
   - Statsig, *Marketplace experimentation: Two-sided platforms*: https://www.statsig.com/perspectives/marketplace-experimentation-platforms
8. **What is synthetic.** The company, markets, orders, couriers and every generator parameter. The
   queue mechanism is an imposed model, not a measured property of any real platform.
9. **What is preserved.** The two-phase design that real platforms actually run (a market-level soak
   followed by order-level randomisation), the incumbent's *correct* estimate of the wrong quantity,
   a capacity check that cannot fail because the arms share one courier pool, and a decision rule with
   an explicit monetary break-even.
10. **Why it belongs.** It is the suite's interference / unit-of-intervention task, and the only one
    whose verifier re-executes the agent's own command against five independently generated worlds,
    including one in which the monetary break-even is binding. See the report's G50 case study for
    what the task can and cannot claim to measure.
