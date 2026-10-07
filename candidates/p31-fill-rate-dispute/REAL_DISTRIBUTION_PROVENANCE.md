# Real-distribution provenance — p31 (ambient-grocery fill-rate dispute)

1. **Professional role.** Demand-science analyst supporting Commercial and Legal.
2. **Industry.** Grocery retail / FMCG supply chain.
3. **Business decision.** Rebuild the published service-level metric, review the team's bonus gate,
   and take a position on a £1.8m contractual claim that turns on whether an account-level floor was
   breached.
4. **Realistic inherited artifacts.** Order, shipment and delivery tables; the published quarterly
   service-level report; the counterparty's own quarterly report showing a materially different
   number for the same category and period; the supply agreement defining the floor; shortfall
   tickets from three key accounts; the reporting code.
5. **Statistical/ML problem.** Metric reconstruction and reconciliation: bridging two defensible
   computations of the same KPI across aggregation level, denominator definition, and the treatment
   of returns/substitutions, then applying a contractual threshold at the right unit.
6. **Why this happens in real organizations.** There is no universal fill-rate or OTIF standard;
   each retailer defines it differently. Disputes turn on whether "in full" applies at order,
   line-item or case level, on request date versus promise date, and on how partial fills and
   substitutions count. Walmart computes OTIF at case level and charges 3% of COGS on the
   non-compliant portion; the documented consequence is that "brands reporting a healthy 97% fill
   rate are often shocked to see OTIF scores in the 80s and chargebacks arriving anyway" — which is
   precisely this task's 97.7% versus 91.5% gap.
7. **Public sources.**
   - inymbus, *What Is OTIF?*: https://blog.inymbus.com/what-is-otif-on-time-in-full-explained
   - Fulfyld, *What Does OTIF Mean Retail: chargebacks*: https://www.fulfyld.com/knowledge/what-does-otif-mean-retail/
   - Wikipedia, *DIFOT*: https://en.wikipedia.org/wiki/DIFOT
   - ABC Supply Chain, *OTIF / DIFOT / Fill Rate formulas*: https://abcsupplychain.com/otif-fill-rate-difot/
8. **What is synthetic.** The retailer, supplier, accounts, order data and claim value.
9. **What is preserved.** Two independently defensible metric definitions that disagree by roughly
   six points, a contract that fixes one of them, a bonus gate that depends on the other, and a
   counterparty with an incentive to use the definition that favours it. The decomposition the task
   grades (`bridge_pp` by aggregation, denominator and returns treatment) is the reconciliation a
   real commercial dispute actually requires.
10. **Why it belongs.** It is the suite's clearest case where the scientific object is *defined by a
    contract* rather than chosen by the analyst, and where the right answer requires reconciling two
    numbers rather than producing one. No other task makes definition reconciliation the primary work.
