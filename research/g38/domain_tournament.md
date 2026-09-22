# G38 domain tournament — threshold-triggered intervention + regression to the mean

## Rejection rules (from the brief)
- **T1** a control group alone solves it
- **T2** one obvious DiD solves it
- **T3** the fix is merely "drop the trigger period"
- **T4** randomised
- **T5** one mean comparison solves it
- **T6** RTM is the only phenomenon: no persistent-vs-transient separation needed
- **T7** the task reduces to "don't compare the extreme period with the next"

| # | unit | stochastic outcome (exposure) | trigger statistic / window | intervention | business claim | target estimand | untreated comparison available | RTM source | persistent heterogeneity | season/trend | decision | naive analysis | correct families | cheap-solve risk | G05 overlap | semantic risk | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **R1 supplier SDP** | supplier (≈ 600) | defects / parts received | rolling-3-month ppm > 1,500 | 6-month Supplier Development Programme | "ppm fell 45 % for enrolled suppliers" | ATT: defects averted per enrollee, 6 months | pre-programme history (same rule applied retroactively); never-enrolled suppliers | monthly lot-quality shocks + Poisson noise on small suppliers | large (process capability differs by supplier) | mild seasonality | expand SDP funding | pre/post on enrollees | state-space / EB latent risk; historical pseudo-episode calibration | low | low: selection on the outcome, not timing/trends | low: pinned ATT | **carry → rank 1** |
| R2 warehouse pick errors | warehouse (≈ 60) | errors / picks | rolling-4-week rate > target | "quality blitz" retraining | "errors down 30 %" | ATT | other warehouses | staffing shocks | moderate | peak season | expand blitz | pre/post | as R1 | low | low | low | **carry → rank 3** (only 60 units: identifiability risk) |
| R3 delivery depots late rate | depot (≈ 250) | late / deliveries (huge exposure) | rolling-4-week late % > 8 % | route re-planning squad | "late % down 3 pp" | ATT | other depots | weather/staffing shocks (serially correlated) | moderate | strong seasonality, holiday peak | expand squad | pre/post; DiD vs other depots | as R1 | low | **medium**: weather shocks are common → DiD-able | low | **carry → rank 2** |
| R4 stores abnormal shrink | store | shrink $ / sales | quarterly shrink % > 2 % | loss-prevention programme | "shrink fell 30 %" | ATT | other stores | inventory-count noise | large | seasonality | expand LP | pre/post | as R1 | medium | low | **high**: shrink is measured by periodic counts; the count-timing artefact is a measurement problem, not RTM (overlaps G37) | reject: semantic, G37-adjacent |
| R5 support-heavy accounts | account | tickets / seats | tickets/seat > p95 over 1 month | CSM intervention | "tickets down 40 %" | ATT | other accounts | incident spikes | moderate | product releases | expand CSM | pre/post | as R1 | medium | **medium**: release shocks are common → DiD | medium: seats change | reject **T6-ish** (spikes are one-off; persistent component weak) |
| R6 hospital readmissions | ward/clinic | readmissions / discharges | rolling-quarter rate > national | QI collaborative | "readmissions down 20 %" | ATT | other hospitals | small counts | moderate | trends from policy (HRRP) | fund QI | pre/post | as R1 | low | **high**: secular policy trends dominate → G05 | medium | reject: G05 overlap, clinical realism burden |
| R7 cloud-service incidents | service | incidents / requests | weekly error-rate SLO breach | reliability sprint | "incidents down 50 %" | ATT | other services | bursty incidents | moderate | deploy cadence | fund sprints | pre/post | as R1 | medium | low | medium: incidents are heavy-tailed, non-Poisson | reject: heavy tails would put legitimate error inside the noise (G37 lesson) |
| R8 low-conversion territories | territory | wins / opportunities | quarterly conversion < 15 % | sales coaching | "conversion up 5 pp" | ATT | other territories | small opportunity counts | moderate | quarter-end effects | expand coaching | pre/post | as R1 | medium | medium | medium: opportunity definition drift | reject: few territories, very noisy (weak window) |
| R9 fraud merchants chargebacks | merchant | chargebacks / transactions | monthly chargeback ratio > 1 % (card-network rule) | monitoring programme | "ratio fell below 1 %" | ATT | other merchants | fraud bursts | large | seasonality | keep programme | pre/post | as R1 | medium | low | **high**: merchants exit/terminate after enrolment (survivorship) + adversarial behaviour | reject: survivorship dominates |
| R10 fleet depots maintenance cost | depot | cost $ / vehicle-miles | quarterly cost/mile > budget | maintenance audit | "cost down 18 %" | ATT | other depots | lumpy repairs (heavy-tailed $) | moderate | fuel/price trends | expand audits | pre/post | as R1 | medium | medium | medium | reject: heavy-tailed $ outcome (same as R7) |
| R11 energy sites abnormal kWh | site | kWh / degree-days | monthly kWh/DD > p90 | energy audit | "consumption down 12 %" | ATT | other sites | weather-normalisation error | moderate | weather | expand audits | pre/post | as R1 | medium | **high**: weather normalisation = G36-style regime transport | reject: G36 overlap |
| R12 supplier late delivery | supplier | late / deliveries | rolling-3-month OTD < 90 % | expediting programme | "OTD up 6 pp" | ATT | other suppliers | freight shocks (common across suppliers) | moderate | peak season | expand expediting | pre/post; DiD | as R1 | low | **medium**: freight shocks common → DiD | low | reject: common shocks make DiD nearly sufficient (T2) |

## Ranking of carried concepts
| rank | concept | reason |
|---|---|---|
| 1 | **R1 supplier SDP** | largest realistic unit count; exposure varies by 100× (Poisson noise is part of the transient); the trigger is a real SQM policy; shocks are supplier-specific, not common (DiD cannot absorb them) |
| 2 | R3 delivery depots | realistic, but common weather shocks invite DiD (G05) |
| 3 | R2 warehouses | realistic, but only ~60 units |

The top three are prototyped on one simulator with domain-specific scales (`top_designs.md`). The
full gate suite runs on the leader.
