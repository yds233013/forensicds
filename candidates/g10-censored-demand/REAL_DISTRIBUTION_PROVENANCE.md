# Real-distribution provenance — g10 (Q3 demand review under LEAN-26)

1. **Professional role.** Demand scientist in a planning organisation.
2. **Industry.** Multi-category retail / distribution.
3. **Business decision.** The Q3 buy plan across eight categories, and whether to extend the LEAN-26
   inventory-reduction programme.
4. **Realistic inherited artifacts.** Sales/orders history, inventory snapshots, stockout and
   availability records, the LEAN-26 programme configuration and go-live dates, the published category
   review recommending cuts in all eight categories, and the baseline-generating code.
5. **Statistical/ML problem.** Demand estimation under informative censoring: observed sales
   understate latent demand exactly where availability was constrained, and the constraint was itself
   introduced by the programme whose effect is being measured.
6. **Why this happens in real organizations.** When a product stocks out, observed sales understate
   true demand; models trained on censored sales systematically underestimate demand, which lowers
   reorder quantities, causes more stockouts, and closes a self-reinforcing loop. The literature
   describes this explicitly as a "vicious cycle" of demand underestimation, and notes that without
   stockout annotation models process censored signals as if they were accurate observations. An
   inventory-reduction programme is the canonical real trigger: it manufactures the censoring and then
   the censored series is used to justify further cuts.
7. **Public sources.**
   - *FreshRetailNet-50K: A Stockout-Annotated Censored Demand Dataset*: https://arxiv.org/abs/2505.16319
   - *Demand forecasting under lost sales stock policies*, Int. J. Forecasting: https://www.sciencedirect.com/science/article/abs/pii/S0169207023000961
   - *A Reproducible, Leakage-Free Pipeline for Censored Demand Forecasting*: https://doi.org/10.3390/inventions11050089
8. **What is synthetic.** The retailer, categories, SKUs, demand process and programme parameters.
9. **What is preserved.** The multi-system evidence requirement (sales alone cannot reveal the
   censoring; inventory and availability records are needed), the seasonal sanity check that makes the
   published conclusion suspicious rather than obviously wrong (ice cream down in summer), and the
   coupling between the intervention and the observation process.
10. **Why it belongs.** It is the suite's canonical informative-censoring task and covers the
    supply-chain/procurement blueprint. The censoring is endogenous to the decision being taken,
    which is what makes it a scientific rather than a bookkeeping problem.
