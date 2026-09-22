# Natural-path audit (from panel results; no additional simulation)

| id | first natural move | after discovering the first issue | reaches the object? | steps needed |
|---|---|---|---|---|
| A1 | LP on list prices (W01) | add minimums as constraints (W03 — **valid**) | yes, in one step | **1**: "commitments are sunk" plus the yield ranking, which rarely binds (W04 coincides 91 %) |
| A2 | per-depot gap on on-hand (W10) | ATP + transfers; ignore lead times (W03) | often coincides (65 %) | 2–3, but the later steps are frequently inactive |
| A3 | rank by margin (W03) | LP with lines only (W01) | adding the shared paint constraint completes it | 2 |
| A4 | commit mean usage (W03) | newsvendor quantile on the hourly profile | pooling regions coincides 61 % | 2–3 |
| B1 | average plant OEEs (W01) | pooled sums | cavities / PPT / scrap must each be found | 3–4 |
| B2 | reported picks / paid hours (W08) | convert units | site-level conversion, direct hours | 3 |
| B3 | nameplate − average (W09, dashboard) | kVA→kW, redundancy, derate, peak, reserved | each is one engineering fact | 5 single-fact steps; each is one line once known |
| B4 | mean unit CF (W03) | pooled energy / capacity-hours | DC/AC, COD, derate | 3 |
| C1 | product of dashboard yields (W01) | FPY | starts weighting (weak) | 2 |
| C2 | vendor's total-level WAPE (W01) | SKU-store-week grain | active population | 2; both are single definitions |
| C3 | all stores (W01) | comparable set | cutoff and remodel rules | 2 |
| C4 | pooled eval recall (W01) | reweight | fraud vs transaction weights (weak) | 2 |

**Pattern.** B and C concepts are sequences of *single-fact corrections*. Once each fact is found, it
is one line. This is the "find one denominator → change one line" shape the brief warns against,
repeated.
