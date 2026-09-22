# Family C — hierarchical aggregation / composition (before simulation)

| id | incident | target object | hierarchy / composition | traps | CS attack | SEM | verdict |
|---|---|---|---|---|---|---|---|
| **C1 rolled throughput yield** | the quality KPI says 94 % yield; the plant loses 25 % of starts to rework or scrap | starts-weighted RTY = Σ_f S_f Π_s FPY_fs / Σ_f S_f, with FPY = first-pass good / units in | families × steps; rework loops | rework-inclusive step yields; product of pooled step yields; mean instead of product; unweighted families | "product of dashboard yields" fails when rework is material | pinned (RTY defined by the Six-Sigma programme) | **top-12** |
| **C2 hierarchical forecast accuracy** | the vendor claims 92 % accuracy; stores see far worse | 1 − Σ\|F−A\| / Σ A at SKU-store-week grain over active SKUs | SKU × store × week | aggregate-level WAPE (errors cancel); mean MAPE; discontinued included | "WAPE at the total level" fails | pinned by the replenishment contract | **top-12** |
| **C3 like-for-like conversion** | conversion "fell 1.2 pp"; new low-conversion stores dilute it | Δ = Σtrans/Σtraffic (TY) − same (LY), over the comparable set (open ≥ 13 months, not closed, remodel closure ≤ 2 weeks) | store × period; openings, closures, remodels | all stores; store-average; wrong cutoff; relative vs pp | "compare totals" fails with openings | pinned by retail LFL convention | **top-12** |
| **C4 recall under deployment mix** | the fraud model's "90 % recall" won't hold next quarter | Σ_s w_s·recall_s, with w_s ∝ t_s·r_s (forecast transaction share × fraud rate) | segment mix shift | pooled eval recall; weighting by transactions, not fraud | "pooled recall" fails with mix shift | pinned: expected share of next quarter's fraud caught | **top-12** |
| C5 supplier PPM across plants | corporate PPM disputes | Σ defects / Σ parts | plants | average PPM | one aggregate | pinned | reject: one aggregate (CS) |
| C6 delivery on-time across carriers | carrier scorecards | Σ on-time / Σ deliveries | carrier × region | unweighted | one aggregate | pinned | reject: CS |
| C7 hospital mortality standardisation | ranking dispute | indirect standardisation | case mix | needs a risk model | — | low | reject: model noise + SEM |
| C8 support first-contact resolution | FCR disputes | resolved-first-contact / issues | ticket chains | per ticket vs issue | chain-linking | medium | reject: SEM (issue definition) |
| C9 ad ROAS across campaigns | attribution war | Σ revenue / Σ spend | attribution windows | window choice | — | **low** | reject: SEM |
| C10 price-volume-mix bridge | finance PVM | price effect under a fixed base | product × period | Laspeyres vs Paasche | — | **medium**: conventions differ | reject (SEM) unless pinned; possible later |
| C11 manufacturing yield across lines (simple ratio) | — | Σ good / Σ in | lines | unweighted | one aggregate | pinned | reject: CS |
