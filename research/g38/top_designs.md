# Top designs — one simulator, three enterprise scales (existing runs only)

Code: `sim/g38_sim.py` (SCALES). Results: `sim/g38_R1_supplier.json` (200 draws/fixture), and
`g38_R2_warehouse.json` / `g38_R3_depot.json` (100 draws/fixture). All use the same 5 regimes, the
same trigger policy and the same pre-registered window definitions (`sim/analyze_g38.py`).

| | R1 supplier SDP | R2 warehouse quality blitz | R3 depot route squad |
|---|---|---|---|
| units | 600 suppliers | 60 warehouses | 250 depots |
| exposure | median 60k parts/month, spread ×100 | 400k picks/month, spread ×3 | 900k deliveries/month, spread ×2.5 |
| enrollees per fixture | 84–115 | 16–22 | 24–61 |
| SE_REF(Q1), per enrollee | 32–60 defects | 50–328 | 45–458 |
| **VALID_BOUND** | 5.67 | 9.16 | 7.89 |
| **WRONG_BOUND** | 0.02 | 0.02 | 0.03 |
| **ratio** | **0.00** | **0.00** | **0.00** |

All three fail. Smaller unit counts (R2, R3) make it worse, because the irreducible
per-enrollee counterfactual noise averages over fewer enrollees. R1 is the strongest and is the
design analysed in full.
