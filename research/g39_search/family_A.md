# Family A — decision optimisation under business constraints (written before any simulation)

Legend:
- **DS?** Would a data scientist own it? The optimiser must sit downstream of substantial data work.
- **CS** initial cheap-solve attack; **SEM** semantic sharpness.

| id | incident | target object (math) | DS work before the optimiser | structural traps | CS attack | SEM | verdict |
|---|---|---|---|---|---|---|---|
| **A1 take-or-pay supplier allocation** | demand fell; procurement's plan buys from the "cheapest" supplier while paying for unused take-or-pay minimums | min Σ_k p_k·max(x_k, m_k) s.t. Σ_k y_k x_k ≥ D_good, x_k ≤ cap_k | reconstruct first-pass yields from receiving/inspection records; commitments from contracts; demand in good units | sunk commitments (zero marginal cost); ranking by p/y, not p; gross vs good units | "cheapest price" and "fill by price" both fail when commitments or yields bind | pinned: cash cost for the quarter | **top-12** |
| **A2 depot rebalancing with ATP + lead time** | stock-outs despite "network surplus" | min shortfall = Σ N_j − maxflow over feasible arcs (L_ij ≤ need-by_j) using ATP (on-hand − allocated + timely inbound) | ATP reconstruction from on-hand, allocations and PO ETAs | allocated stock; late inbound; infeasible lead times; pooled netting | network netting ("we have surplus") fails whenever lead times or allocations bind | pinned | **top-12** |
| **A3 shared-bottleneck product mix** | line managers each maximise margin; the shared paint shop overloads | max Σ c_p q_p s.t. line hours, shared paint hours, demand caps | line availability from calendar − planned maintenance; paint hours per unit from routings | margin/unit vs margin/bottleneck-hour; ignoring the shared resource; nominal hours | "rank by margin" fails when paint binds | pinned | **top-12** (DS-ownership risk: OR flavour) |
| **A4 cloud commitment purchase** | FinOps must buy 1-year commitments; the dashboard recommends "average usage" | per region: argmin_Q Σ_h [2Q·p_c + p_od·max(0, d_h − 2E_h − 2Q)], integer cores | hourly usage reconstruction, existing commitments + expiry, core/vCPU units, regional scope | vCPU vs core; regional non-poolability; expiring commitments; the quantile, not the mean | "commit the mean/min" fails unless the discount ≈ 50 % on a symmetric profile | pinned | **top-12** |
| A5 staffing allocation across call centres | SLA breaches after a reallocation | Erlang-C staffing min cost s.t. service level | arrival-rate estimation (noisy) | occupancy vs service level | — | medium | reject: stochastic arrivals bring sampling noise back (G38 lesson) |
| A6 promotion budget allocation | marketing budget split | max response Σ f_k(b_k) | response-curve estimation | saturation | — | medium | reject: estimated curves = estimator noise |
| A7 maintenance scheduling with correlated failure | common-mode outages | min risk-weighted downtime | failure-rate estimation | correlated components | — | low | reject: stochastic, semantic |
| A8 regional fleet allocation with EV range eligibility | EVs assigned to ineligible routes | max covered routes s.t. eligibility | range derivation from telematics | eligibility sets | eligibility filter + greedy | pinned | reject: one filter solves (CS) |
| A9 MOQ-constrained purchasing | overstock | min cost s.t. MOQ lots | — | lot rounding | MOQ rounding one line | pinned | reject: trivial after recognition (D9) |
| A10 warehouse slotting | picker travel | min travel | velocity estimation | — | — | — | reject: pure OR |
| A11 hospital staffed vs licensed beds allocation | ED boarding | max placements s.t. staffed beds | staffing roster | licensed vs staffed | one field | pinned | reject: one-field fix (moved to B-style thinking) |
| A12 battery dispatch | revenue shortfall | max arbitrage s.t. state of charge | price forecast | SoC | — | — | reject: OR + forecast noise |
