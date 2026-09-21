# G37 domain tournament — measurement-system change

Screening rules:
- **(R1) Reject** if the difficulty is essentially "subtract the offset".
- **(R2) Reject** if one calibration table hands over the answer.
- **(R3) Reject** if the measurement correction has a negligible effect on the business quantity.
- **(R4) Reject** if the business metric is *defined* on the measured values, making "latent" the
  wrong target (a semantic trap for G36-type F8).

Scores are 1–5, higher = better.

| # | concept | business incident | old system | new system | latent quantity | bridge / calibration evidence | error structure | decision | why a DS/statistician owns it | natural naive analysis | correct object | execution difficulty | cheap-solve risk | semantic risk | distinct from pool |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **C1** | in-line thickness gauge replaced at a precision-shim supplier; the dashboard Ppk drops from 1.6 to 1.0, and Quality prepares a customer notification plus a capital request | manual contact micrometer (reference method per drawing) | automated dual-scan laser station | true part thickness; overall latent σ, μ → Ppk | 3-day parallel run (both gauges, same parts, from 2 coils); old-gauge check re-measurements; new-gauge dual scans; vendor block certificate (steel blocks; **not commutable** with coated parts) | both noisy, error variances differ; new gauge has scale ≠ 1 and an offset *on parts*; the bridge covers a **narrow** range (2 coils) | notify customer iff latent Ppk < 1.33 (supply agreement) | MSA/SPC statistics, not ETL | raw post Ppk; vendor offset; bridge mean offset; OLS calibration; Ppk on mapped readings | latent μ, σ via an errors-in-variables bridge plus variance deconvolution with the correct error variance | high: error variances from replicate structures, EIV slope, deconvolution with the right divisor, the right scale, overall vs within | low if the docs give no mapping; the vendor certificate is a *trap*, not an answer | low: reference scale and Ppk pinned by drawing/contract | new: no pool task has observed ≠ latent |
| **C2** | pharma QC potency assay moved HPLC → UPLC; CPV chart shows capability collapse; site files a deviation | HPLC, duplicates | UPLC, duplicates | true lot potency distribution | CLSI EP09-style comparison: 40 retained lots on both, in duplicate | both noisy, response factor b ≈ 1.03; assay SD ≈ lot SD | CPV escalation iff Ppk < 1.33 | yes (CMC statistics) | observed Ppk; Deming is textbook | latent lot SD | high | medium: EP09 names Deming | **medium**: release decisions are *defined on measured results*; "capability should include analytical variability" is a live industry position (R4 risk) | new |
| C3 | warehouse scale replacement changes the billed dimensional-weight mix | old floor scale | new scale | true parcel weight | test weights | error ≪ parcel variation; mostly offset | billing adjustment | weak (metrology/finance) | offset | offset | trivial | high (R1) | low | — | **REJECT R1, R3** |
| C4 | residential smart-meter swap changes a consumption KPI | electromechanical meter | smart meter | true kWh | meter accuracy class | class-1 error ≪ consumption variance | tariff design | weak | none | none | negligible | high | low | — | **REJECT R3** |
| C5 | fleet fuel-sensor retrofit: a fuel-efficiency programme claims 7 % savings | tank probe | flow meter | true fuel per km | fuel-card purchases (noisy, weekly) | three noisy measures (triple collocation) | continue programme iff savings ≥ 5 % | yes | raw before/after | latent mean ratio | medium | medium | medium: savings target is internal | overlaps G05 (causal pre/post) | **REJECT R3**: the business quantity is a **mean**, and zero-mean noise does not bias means; only scale matters, which reduces to R1 |
| C6 | remote BP-monitoring cuff swap: "uncontrolled hypertension" share jumps | cuff A | cuff B | true BP distribution; share > 140/90 | paired readings | both noisy + within-person variability | payer quality score | yes | raw share | latent share | high | low | **high**: HEDIS-style measures are defined on *readings* (R4); clinical | new | **REJECT R4** |
| **C7** | visual-inspection migration (human → camera model): shipped-defect rate "doubles"; supplier chargeback threatened | human inspectors | camera classifier | true defect prevalence | audit: 2,000 units classified by both, gold-standard teardown on a stratified subsample | misclassification (sens/spec), each differing | chargeback iff p > 0.50 % | yes | raw rate | Rogan–Gladen / latent class with verification-bias correction | medium-high | **medium-high**: once sens/spec are estimated, one formula | low-medium | partly overlaps G24/G36 (IPW-style reweighting of the audit) | keep for deep round |
| C8 | stack NOx analyser replaced; emissions trend jumps | CEMS A | CEMS B | true emissions | RATA tests | bias + noise | permit compliance | weak (regulatory procedure) | — | regulation prescribes the bias-adjustment factor | low | **high** (R2: the regulation hands over the method) | high (R4) | — | **REJECT R2, R4** |
| **C9** | CD-SEM fleet: a new tool added; wafer-to-wafer CD variation "increases"; lithography escalates | 3 matched tools | + 1 new tool with its own scale/offset | true wafer-mean CD; latent wafer-to-wafer SD | golden-wafer matching across tools + tool-to-tool re-measures | multi-tool bias/scale + repeatability; tool dispatch | yield trigger iff σ > 1.2 nm | yes | raw pooled SD | latent SD with tool effects removed | high | low | medium (budget provenance weak) | risk: dispatch confounding is selection (G36 ground) | keep for deep round |
| C10 | grain-elevator moisture meter swap changes discount revenue | meter A | meter B | true moisture share > 15.5 % | USDA air-oven reference on samples | the reference is precise | drying capacity | moderate | raw share | latent share | low once the oven is used | **high** (R2: a precise oven reference makes OLS-on-reference correct) | low | — | **REJECT R2** |

## Ranking (sum over execution difficulty, low cheap-solve, low semantic risk, threshold provenance, distinctness, correction materiality)
| rank | concept | total /30 | verdict |
|---|---|---|---|
| 1 | **C1** in-line gauge / latent Ppk | 26 | deep round |
| 2 | **C9** CD-SEM fleet matching | 20 | deep round |
| 3 | **C7** inspection-model migration | 19 | deep round |
| 4 | **C2** assay method transfer | 18 | deep round |
| — | C5 | — | reject R3 |
| — | C6 | — | reject R4 |
| — | C3, C4 | — | reject R1 / R3 |
| — | C8, C10 | — | reject R2 (C8 also R4) |

The ranking is **not** a selection. Selection comes only after the quantitative gates in the deep round.
