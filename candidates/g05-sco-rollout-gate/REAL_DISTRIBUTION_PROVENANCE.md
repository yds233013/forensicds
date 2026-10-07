# Real-distribution provenance — g05 (SCO 2.0 tranche-2 capital gate)

1. **Professional role.** Decision scientist in FP&A preparing a capital-committee paper.
2. **Industry.** Grocery/general-merchandise retail.
3. **Business decision.** Whether to release tranche 2 (waves 5–6) of a self-checkout conversion
   programme, against the gate figure the business case specifies.
4. **Realistic inherited artifacts.** Store-week operational data, the wave/rollout schedule, the
   business case defining the gate, the incumbent analysis that produced the current gate figure, and
   the finance memo.
5. **Statistical/ML problem.** Identification under staggered adoption. Stores convert in waves, so a
   naive before/after or two-way fixed-effects comparison mixes cohorts with different exposure
   lengths and different counterfactual trends, and the comparison group at any date includes
   not-yet-treated and already-treated stores.
6. **Why this happens in real organizations.** Phased capital rollouts are the normal way retailers
   deploy store estate changes — wave by wave, with the early waves chosen for readiness rather than at
   random. The gate figure then has to be computed from exactly the design that produced the data, and
   the standard two-way fixed-effects estimator is not generally the right one when adoption is
   staggered and effects vary with exposure length.
7. **Public sources.** The staggered-adoption identification literature is the direct reference point
   for the estimator choice; the operational pattern (wave-based store conversion with readiness-based
   sequencing and a tranche gate) is standard retail capital practice.
8. **What is synthetic.** The retailer, stores, waves, transaction data and effect parameters.
9. **What is preserved.** Wave sequencing that is not random, a gate defined in the business case
   rather than by the analyst, and an incumbent estimate that is internally coherent and wrong for a
   design reason rather than a coding reason.
10. **Why it belongs.** It is the suite's staggered-adoption identification task. Together with g50 it
    covers the experimentation/identification axis from two different directions — g05 where adoption
    timing is the problem, g50 where the unit of intervention is.
