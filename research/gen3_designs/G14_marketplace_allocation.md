# G14: Marketplace refunds, promotion funding and seller economics (detailed design)

Status: generation-3 design. Not built. No model run. Fictional marketplace, sellers and systems.

## Workspace sketch

```
/workspace
  README.md                                     repo purpose, owners, `python -m seller_econ close --month YYYY-MM`
  CHANGELOG.md                                  seller_econ 1.x entries (neutral)
  seller_econ/
    cli.py
    extract.py                                  FAULTY by omission: loads list price, order-level discount totals,
                                                refund headers, recorded fees, ledger month totals
    allocate.py                                 FAULTY: top-down allocation of discounts/refunds/fee refunds
    statement.py                                assembles seller × month columns and take rate (definitions correct)
    platform_pnl.py                             platform P&L from ledger (correct)
    reconcile.py                                "seller totals tie to ledger" (tautological under top-down)
  config/close.toml                             paths, month attribution timezone (UTC)
  data/orders/orders.parquet                    410k orders (placed_at, buyer region, shipping charged)
  data/orders/order_lines.parquet               1.02M lines (seller, category, qty, list price, item markdown,
                                                recorded referral fee, line_origin, replaces_line_id, buyer_charged)
  data/orders/order_promotions.parquet          96k (order_id, promo_id, discount_minor)
  data/promotions/promotions.parquet            2,300 promotions (scope, funding_type, platform_share_bps,
                                                seller_id, eligible categories, value type)
  data/refunds/refunds.parquet                  58k refund events (order_id, processed_at, reason)
  data/refunds/refund_lines.parquet             71k (refund_id, order_line_id, component, refund_qty, refund_minor)
  data/fees/fee_schedule.csv                    effective-dated category rate_bps and per-unit cap
  data/ledger/gl_daily_summary.csv              daily GL summaries by account (payments subledger postings)
  data/sellers/sellers.csv                      1,180 sellers (tier, tenure, reserve flag)
  docs/data_catalog.md                          output schema (seller_month columns), month attribution, table grains
  docs/order_service_dictionary.md              order/line/refund fields; `line_origin`, `buyer_charged`
  docs/seller_terms/seller_services_agreement.md    SSA excerpts: definitions, promotions, fees, refunds
  docs/seller_terms/promotion_programs.md       campaign types and funding descriptions for sellers
  docs/finance/gl_account_guide.md              GL accounts and posting cadence
  docs/releases/2026-05-20_home_fee_cap.md      Home category cap $25 → $30 from 2026-06-01
  reports/seller_statements/2026-07/seller_month.csv    current (faulty) output
  reports/finance/platform_pnl_2026-07.csv, tieout_2026-07.md   ties exactly
  inbox/SS-7741_loomhaven_escalation.eml, SS-7802_brightwick.eml, SS-7810_casa_ordell.eml
  inbox/attachments/{loomhaven,brightwick,casa_ordell}_payout_statements_2026Q2.csv   weekly payouts (cash basis)
  inbox/support_macros_export.csv              seller support macros (~60)
  notebooks/seller_margin_deep_dive.ipynb       Seller Success analyst notebook (attractor; see §8)
  logs/close_runs.jsonl, logs/deployments.csv
```

Period: 2025-07..2026-08. Sizes: ~180 MB Parquet; GL summary 14k rows.

## 1. Research question

When a shared order-level economic quantity (discounts, refunds, fee refunds) must be attributed to sellers, and every
candidate allocation ties to the platform ledger in total, can an agent reconstruct the allocation semantics from
contracts *and* from system behaviour visible in the data (refund amounts, recorded fees), and validate at the line
grain rather than at the ledger total?

## 2. Enterprise setting

Tessellate (fictional) is a home-and-living marketplace. One buyer order can contain lines from several sellers.
Promotions are item-level (seller markdowns), order-level coupons funded by the platform, by one seller, or co-funded
by both. The platform charges a category referral fee with a per-unit cap. Returns and partial refunds are processed
by the returns service against original order lines. Damaged deliveries are re-shipped as new, uncharged lines.

The Marketplace Finance analytics team owns `seller_econ`, which produces the monthly seller economics statement
(`seller_month`): what each seller sold, the promotion cost it bore, refund reversals, fees, fee refunds, net proceeds
and take rate. Seller Success uses it for account reviews; the seller portal "profitability" tile reads it.

## 3. Visible symptom (instruction memo)

From the VP Marketplace: three of our ten largest sellers (Loomhaven Textiles, Brightwick Home, Casa Ordell) show
negative net proceeds margin for May–July in the seller economics statement. Their account managers are pushing them
to cut promotions, and Loomhaven has escalated, saying their payouts do not look loss-making. Finance says the platform
P&L ties to the ledger to the cent, and the seller statement reconciles to the ledger. The VP needs to know whether
these sellers are really losing money and wants a statement she can trust.

Required: `python -m seller_econ close --month 2026-08` writes `out/seller_month.csv` (all months through the close
month, schema in `docs/data_catalog.md`) and `out/platform_pnl.csv`; statements must reflect the seller agreement and
what actually happened on each order; `data/` is authoritative; no special-casing sellers, promotions, categories or
dates; validate before handing over.

## 4. Source distribution inspiration

- Marketplace seller statements and settlement reports (per-item proceeds, promotion rebates, referral fees with
  minimums/maximums, refund administration). Order-level discount apportionment to items is a standard e-commerce
  concern for returns and tax.
- Top-down allocation of GL totals by a driver is a common analytics shortcut; it ties to the GL by construction.
- Co-funded promotions and funding-source accounting (platform marketing expense vs seller-borne discount) are ordinary
  marketplace finance practice. No specific company's terms are reproduced; any resemblance of the fee mechanics to a
  real marketplace is generic (*to verify* if a reviewer claims otherwise).

## 5. Causal graph / ground truth

Generator (stdlib, seeded):

1. **Sellers** 1,180; categories Home (rate 12%, cap $25/unit → $30/unit from 2026-06-01), Furniture (8%, cap $60),
   Textiles (15%, no cap), Lighting (12%, cap $40), Decor (15%, no cap).
2. **Orders** 410k; lines 1.02M; 31% of orders multi-seller; 27% of lines carry an item markdown
   (`item_discount_minor`, mean 18%).
3. **Order-level promotions** on 22% of orders:
   - platform-funded sitewide/category campaigns (47% of promo orders; e.g. "Home Refresh Week 20%");
   - seller-funded shop coupons (35%; eligible only on that seller's lines in eligible categories; fixed or percent);
   - co-funded campaigns (18%; `platform_share_bps` 3000–7000).
   Checkout computes `discount_minor` per order-promotion, then apportions it across **eligible lines in proportion to
   net item price (list × qty − item markdown)**, cents by largest remainder (ties → lower line number). The
   apportionment is not stored.
4. **Seller proceeds basis** of a line = net item price − seller-borne share of apportioned order-level discounts.
   Platform-funded discount does not reduce it; co-funded reduces it by the seller share
   (`allocated − round_half_up(allocated × platform_share_bps / 10000)`).
5. **Referral fee at sale** (recorded `referral_fee_minor`): `min(round_half_up(rate × fee_basis), cap × qty)` with
   `fee_basis` = seller proceeds basis, using the schedule in effect at `placed_at`.
6. **Refunds** (6.9% of charged lines): the returns service computes buyer cash per line from the stored checkout
   apportionment — `refund_minor` for a full-line item refund equals buyer-paid for the line exactly (net price − all
   apportioned discounts). Partial refunds: quantity refunds (`refund_qty > 0`) and amount-only concessions
   (`refund_qty = 0`, e.g. "keep it, 30% back"). 11% of refunded lines have two or more refund events. 18% of refund
   events include a `shipping` component (platform revenue; never a seller cost).
7. **Seller refund reversal** per event = `round_half_up(seller_proceeds_basis × refund_item_minor / buyer_paid_line)`.
   When a line carried platform-funded discount, the reversal exceeds the buyer's cash refund.
8. **Fee refund** per event = `fee(retained before event) − fee(retained after event)`, where
   `fee(retained) = min(round_half_up(rate × basis × (1 − cumulative refunded fraction)), cap × (qty − cumulative refund_qty))`
   with rate and cap in effect **at the sale**. Full refund returns the full recorded fee. Partial refunds on
   cap-bound lines usually return 0.
9. **Re-shipments** (0.9% of lines; 12 visible chains of reship-of-reship): new line, same seller and SKU,
   `line_origin = 'reship'`, `replaces_line_id`, `buyer_charged = false`, `list_price_minor` copied for inventory
   valuation, `referral_fee_minor = 0`. Refunds always reference the **original charged line**.
10. **Ledger** (`gl_daily_summary`): daily summaries per account — 4000 referral fees, 4010 fee refunds,
    6100 platform-funded promotions (incl. platform share of co-funded), 4100 shipping revenue, 4110 shipping refunds,
    2100 seller payable (posted in **weekly settlement batches**: sale proceeds at `delivered_at + 7d`, reversals and fee
    refunds on refund `processed_at`), 2110 seller reserves (10% hold for flagged sellers, released after 30 days).
11. **Real events used as attractors**: Loomhaven, Brightwick and Casa Ordell join most platform campaigns and run many
    shop coupons; carrier change in April raises rug return rates by ~2 points (real); Home cap change 2026-06-01 (real).
    The three sellers sell high-price items often basketed with cheap, frequently returned accessories from other sellers.

Truth for the three sellers (May–July net proceeds margin): Loomhaven +7.9%, Brightwick +6.4%, Casa Ordell +8.6%.
Faulty report: −4.1%, −2.2%, −0.9%.

## 6. Latent statistical/business invariant (oracle truth)

For each seller `s` and month `m`, all in integer cents:

- `item_sales` = Σ net item price over `buyer_charged` lines of `s` with `placed_at` in `m` (UTC).
- `seller_promotion_cost` = −Σ seller-borne share of order-level discounts apportioned to those lines (§5.3–5.4).
- `refund_reversals` = −Σ seller refund reversal (§5.7) over item-component refund events on `s`'s original lines with
  `processed_at` in `m`; shipping components excluded.
- `referral_fees` = −Σ recorded `referral_fee_minor` of those sale lines.
- `referral_fee_refunds` = +Σ fee refunds (§5.8) of refund events processed in `m`.
- `net_proceeds` = sum of the above; `take_rate` = (fees − fee refunds) / (item_sales + refund_reversals + promotion cost),
  per the existing catalog definition.

Allocation invariants: order-level discounts are apportioned only to eligible lines, by net item price; funding source
determines who bears the apportioned amount; refunds are attributed through `order_line_id` to charged lines;
reversals are proportional to the refunded fraction of buyer-paid; fee refunds follow the cap and the sale-date schedule.

## 7. Grains and state variables

| Grain | Key | State |
|---|---|---|
| order | `order_id` | promotions applied, sellers present |
| order-promotion | (`order_id`, `promo_id`) | `discount_minor`, eligibility set |
| order line | `order_line_id` | net price, apportioned discount per promo, funding split, fee basis, recorded fee, origin |
| refund event × line | (`refund_id`, `order_line_id`, component) | refund qty, amount, cumulative refunded fraction, cumulative qty |
| line × refund sequence | ordered events | retained basis/qty → fee(retained) |
| fee schedule | (category, effective_from) | rate, cap |
| seller × month | (`seller_id`, month) | graded statement |
| settlement batch | (week) | ledger 2100/2110 postings |

The trap grain is **line × cumulative refund state**: pro-rata fee refunds are stateless; the correct fee refund
depends on the line's retained state before and after each event.

## 8. Evidence graph

| Artifact | Shows | Natural path? |
|---|---|---|
| memo + escalation emails | negative margins; Loomhaven says payouts disagree | yes |
| `reports/finance/tieout_2026-07.md` | platform P&L and seller totals tie to GL | yes (attractor: "ties so it's right") |
| `allocate.py` | top-down: month GL totals and order-level totals spread by list-price share | yes |
| `promotions.parquet` | `funding_type`, `platform_share_bps`, `seller_id`, eligible categories | yes |
| SSA excerpt | definitions of Net Item Price, Seller Proceeds; "Platform-funded promotions do not reduce Seller Proceeds"; "Referral Fees are calculated on Seller Proceeds per unit subject to the maximum in the Fee Schedule"; "on a refund we credit the Referral Fee attributable to the refunded amount" | yes |
| `promotion_programs.md` | campaign types; co-funded "reimbursement share" | medium |
| `order_lines.parquet` recorded fees | fees reproduce `min(rate × (net − seller-borne), cap × qty)` only with the right basis and apportionment | medium (must be tested) |
| `refund_lines.parquet` | full-line refunds reveal buyer-paid per line → apportionment basis, eligibility, rounding | medium (key discovery) |
| order service dictionary | `line_origin`, `replaces_line_id`, `buyer_charged`; "refunds reference the order line that was charged" | yes |
| fee schedule + release note | effective-dated caps | yes (attractor: "fee config error") |
| GL guide + daily summaries | account totals, weekly settlement for 2100 | medium |
| payout statements (3 sellers, weekly) | cash settlements incl. reserves, "promotion reimbursement" lines, refund debits larger than buyer refunds | medium (on the escalation path) |
| support macros | one macro explains that a platform-funded discount is recovered on refund; another that "the fee cap continues to apply to the units you keep" | low–medium |
| analyst notebook | Seller Success recomputes margins pro rata by list price *excluding shipping* and finds Loomhaven "only" at +1.2%; concludes promos are the problem | yes (attractor: second wrong allocation with plausible number) |

## 9. Evidence authority hierarchy

| Conflict | Governs | Justification |
|---|---|---|
| Top-down report vs line data | line data | GL totals are allocation-invariant; the tie proves nothing about sellers |
| SSA vs analyst notebook | SSA | contract defines Seller Proceeds and funding |
| SSA "attributable" wording vs pro-rata reading | recorded fees + GL 4010 + macro | the fee actually charged is a capped function of basis; the amount "attributable" to a refund is the fee no longer justified by retained units; the GL fee-refund totals (booked by payments) match only this reading |
| Apportionment basis: SSA silent vs checkout behaviour | refund amounts | the returns service refunds exactly buyer-paid per line; that is the system-of-record apportionment |
| Fee schedule current vs at sale | at sale | SSA: fees "in effect when the order is placed"; release note effective date |
| Payout statements vs seller_month | neither is the other | payouts are cash, weekly, with reserves and delivery-lagged settlement; they validate funding and reversal semantics for three sellers over a quarter, not accrual seller-months |
| Seller claims | not authority | seller-perceived margins exclude their own coupon costs |

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | Real margin problem from heavy promotions | top promo participants; seller coupons real; notebook says so | most of their promo exposure is platform-funded |
| H2 | Fee configuration error (cap change) | June Home fees up; release note | recorded fees match schedule at sale; effect small and positive-margin |
| H3 | Refund spike (carrier change) | rug returns +2 pts | explains ~1 pt of margin |
| H4 | Allocation of discounts/refunds/fee refunds wrong | top-down code; multi-seller baskets | must be proven at line level |
| H5 | Reships inflating/deflating | reship lines have prices | small, and mostly inflate |

## 11. Why each wrong hypothesis is plausible

H1 is the business story already in motion and endorsed by a notebook with a believable number. H2 has a dated
release and a visible June step in fees. H3 is real and on the same product lines. H5 is visibly wrong in code
(`list_price_minor` summed for reship lines) and an agent that fixes it sees numbers move and may stop.

## 12. Investigation path (expected 45–70 actions)

1. (1–8) Memo, emails, tie-out, catalog, run close, reproduce negative margins.
2. (9–14) Read `allocate.py`: top-down. Recognise the tie is tautological. **Discovery 1**.
3. (15–20) Promotions: funding types. Remove platform-funded share from sellers. Loomhaven now positive.
   Many agents may stop here (§14).
4. (21–28) Build bottom-up line table; join refund lines by `order_line_id`; reships found via dictionary. **Discovery 2**.
5. (29–38) Test apportionment against full-line refund amounts: list-price pro rata matches 61% of cases, net-price
   over all lines 78%, net-price over eligible lines 99.7% (the rest are cent residuals). **Discovery 3** (eligibility,
   basis, rounding).
6. (39–44) Test fee basis against recorded fees: including platform-funded discount in basis reproduces 100%.
7. (45–52) Refund reversals: payout statement refund debits exceed buyer refunds on campaign items; macro explains.
   Implement proportional reversal; exclude shipping component. **Discovery 4**.
8. (53–60) Fee refunds: pro rata vs GL 4010 by month — off by $3–6k/month; cap-bound partial refunds; sequential
   events; sale-date cap. **Discovery 5**.
9. (61–70) Validate: line-level identities (Σ apportioned = order discount; Σ line proceeds + platform promo = ...),
   GL 4010/6100/4110 monthly ties, 2100 weekly batch ties after settlement timing and reserves (optional, hard),
   three sellers' quarterly payouts reconcile within reserve balance, full-refund exactness, determinism.

## 13. Natural wrong implementation

After Discovery 1–2, the natural bottom-up design:

```python
lines = order_lines[order_lines.buyer_charged]
promo = order_promotions.merge(promotions)
share = lines.list_price_minor * lines.qty / lines.groupby("order_id")[...].transform("sum")   # all lines, list price
lines["seller_promo"] = (promo_discount_by_order * share).where(funding != "platform") * seller_share
refunds = refund_lines.merge(lines, on="order_line_id")
refunds["reversal"] = refunds.refund_minor                          # cash amount, all components
refunds["fee_refund"] = refunds.referral_fee_minor * refunds.refund_minor / refunds.buyer_paid   # pro rata
```

Visible consequences:
- seller-funded shop coupons spread onto other sellers' lines in multi-seller orders (eligibility): 14% of
  seller-funded discount lands on non-participating sellers;
- list vs net price basis shifts co-funded/seller cost toward marked-down items;
- shipping refunds (18% of events) debited to sellers;
- reversals short by the platform-funded share on campaign items;
- fee refunds overstated on cap-bound partial refunds by $41k over 14 months; GL 4010 mismatch per month $2.1k–6.3k;
- Loomhaven May–July margin +2.7% (truth +7.9%); 7,940 of 12,600 seller-months outside tolerance.

Headline totals: platform-funded promotions tie to GL 6100 (funding handled), GMV ties, total fees tie; only 4010
and 4110-related seller totals do not.

The *first* natural repair (before any bottom-up rebuild) is smaller still: keep `allocate.py` top-down but filter
`funding_type != 'platform'` from the promotion pool. Loomhaven becomes +3.9%, the three sellers turn positive, the
tie-out still ties, and the escalation appears resolved. This is the strongest attractor in the design.

## 14. Second-order failure modes

| After rejecting… | Next repair | Still wrong |
|---|---|---|
| funding filter on top-down | bottom-up, list-price pro rata (above) | eligibility, basis, shipping, reversal gross-up, fee cap |
| list-price basis | net-price pro rata across **all** lines of the order | seller-funded coupons spread to other sellers; platform category campaigns spread to ineligible categories |
| all-lines pro rata | eligible-lines, net price, but quantity-weighted for fixed coupons | fails full-refund exactness on multi-unit lines |
| cash reversal | reversal = refund cash + *entire* platform-funded discount of the line | over-reverses on partial refunds |
| pro-rata fee refunds | "fee refund = min(pro rata, cap × refunded qty)" | wrong on amount-only concessions and on sequential events |
| stateless fee refunds | cumulative state but **current** schedule cap | Home lines sold before 2026-06-01 and refunded after: 1,180 visible events |
| everything | reships excluded from sales but refunds joined on `(order_id, sku)` choosing the latest line | refunds after reship land on the zero-basis reship line → reversal 0, fee refund 0 |
| everything | calibrate to payouts (scale seller reversals so the 3 sellers' quarterly payouts tie) | payouts include reserves and settlement lag; forcing a tie distorts other months and other sellers |
| everything | month by `delivered_at`/settlement to match GL 2100 | catalog month attribution is `placed_at`/`processed_at` |

## 15. Correct repair properties

- Bottom-up at line and refund-event grain; no allocation of GL totals.
- Order-level discount apportioned across eligible lines by net item price; funding split per promotion.
- Refunds attributed via `order_line_id`; item component only; proportional reversal of seller proceeds basis.
- Fee refunds from retained-state recomputation with the sale-date schedule.
- Reship lines contribute nothing to sales/fees; refunds never attach to them.
- Platform P&L unchanged and still tying; seller fee refunds sum to GL 4010, platform promo to 6100.
- No hard-coded sellers, promo codes, categories, caps or dates.

## 16. Repair surfaces

| File | Why |
|---|---|
| `extract.py` | load line markdowns, `line_origin`, `buyer_charged`, promotion eligibility/funding, refund lines with components, fee schedule |
| `allocate.py` | replace top-down with apportionment + funding split + reversals |
| new `fees.py` (or inside allocate) | stateful fee refund computation with effective-dated schedule |
| `reconcile.py` | must reconcile bottom-up sums to GL accounts (currently tautological); not graded directly but needed for the agent's validation |
| `statement.py` | unchanged definitions; input shape changes from month totals to line facts |

## 17. Validation requirements

Insufficient on their own: GL ties for GMV, fees and platform promotions (true after the funding filter); the three
sellers turning positive; the notebook's margin range.

Required at line/event grain:
- **Apportionment identity**: Σ apportioned discount per order-promotion equals `discount_minor`; zero on ineligible lines.
- **Full-refund exactness**: for every full-line item refund, buyer-paid computed from the apportionment equals
  `refund_minor` (≈9,000 visible cases; should be 100%).
- **Fee reproduction**: recomputed sale fee equals recorded fee on all charged lines (validates basis and schedule).
- **Fee refund totals** equal GL 4010 per month; shipping refunds equal 4110.
- **Refund-to-line audit**: no refund on a reship line; every refund line maps to a charged line.
- **Three-seller payout reconciliation** over Q2 within reserve balance and in-transit settlements (optional but on the
  escalation path).

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface changes | Overfit caught | Same distribution |
|---|---|---|---|---|
| `hidden_a` (2024-01..2024-12) | eligibility, basis, funding split | co-funded campaigns dominate (45%); fixed-amount seller coupons in 3-seller orders; markdowns on 45% of lines; different category eligibility sets; no cap changes | promo-code prefix funding rules; list-price allocation tuned to visible; hard-coded "Home Refresh" eligibility | same promo fields and funding types as visible |
| `hidden_b` (2025-03..2026-02) | fee refunds with caps | Furniture and Lighting caps bind on 40% of lines; two cap changes (Lighting 2025-09, Furniture 2026-01); 25% multi-event refunds mixing qty and amount-only; refunds crossing cap changes | pro-rata fee refunds; current cap; hard-coded 2026-06-01; stateless min(prorata, cap) | cap change and multi-event refunds visible |
| `hidden_c` (2025-10..2026-09) | refund lineage, reships, shipping | reship rate 4%, reship-of-reship chains 3 deep, refunds of the original line after two reships, shipping components on 40% of events, multi-seller orders where only one seller reships | `(order_id, sku)` joins; "latest line" heuristics; hard-coded reship count; shipping to seller | chains and shipping components visible (12 chains) |

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` (top-down) | 0 |
| `oracle` | 1 |
| `alt_duckdb_sql` (window functions for largest remainder and cumulative refund state) | 1 |
| `alt_python_event_replay` (per-line state machine) | 1 |
| `alt_rounding_banker` (half-even everywhere) | 1 (within tolerance) |
| `topdown_funding_filter` | 0 |
| `listprice_prorata_all_lines` | 0 |
| `netprice_prorata_all_lines` | 0 |
| `eligible_qty_weighted` | 0 |
| `cash_reversal` | 0 |
| `reversal_plus_full_platform_discount` | 0 |
| `shipping_to_seller` | 0 |
| `fee_refund_prorata` | 0 |
| `fee_refund_min_prorata_cap` | 0 |
| `fee_refund_current_cap` | 0 |
| `refund_join_order_sku` | 0 |
| `reship_as_sale` | 0 |
| `partial_funding_and_basis_only` / `partial_fees_only` | 0 |
| `payout_calibrated_scaling` | 0 |
| `overfit_visible_promo_ids_eligibility` (lookup table of visible promotions) | visible 1, **hidden_a 0** |
| `overfit_cap_change_date_hardcoded` | visible 1, **hidden_b 0** |
| `overfit_single_reship_hop` | visible 0 on 12 chains (by design; if chains prove too rare, hidden_c catches it) |
| `output_patch`, `edit_data`, `import_reference` | 0 |

## 20. Alternative valid implementations

- Rounding: any consistent half-up/half-even/largest-remainder variant passes within the per-cell tolerance (§21).
- Computing reversal via "refunded quantity share" for quantity refunds vs "refunded amount share": identical when
  refund cash equals per-unit buyer-paid × qty (generator ensures).
- Apportioning across all promotions jointly vs sequentially per promotion: generator applies at most one order-level
  promotion per eligibility set per order; stacking of a platform campaign and a shop coupon on disjoint or overlapping
  lines is apportioned independently (each on net item price, not after the other) — visible has 2,100 stacked orders
  where full refunds disambiguate; alternatives that stack sequentially fail full-refund exactness, so this is evidenced.
- SQL vs Python, any file layout.

## 21. Verifier design

- Integrity of `data/`; run close twice as unprivileged user; determinism.
- `seller_month.csv`: exact row set (seller × month with any activity); for each money cell,
  |agent − truth| ≤ 1 cent × (number of rounding events in that cell) + 1 cent. Rounding-event counts come from the
  generator (apportioned lines, co-funded splits, reversals, fee refunds). Build-time check: every wrong mutation exceeds
  tolerance in ≥ 50 visible cells and ≥ 20 cells per hidden fixture.
- `take_rate`: within 1e-4 when denominator > $100.
- `platform_pnl.csv`: exact tie to GL (regression guard).
- Seller-level GL consistency: Σ fee refunds = 4010 per month (± rounding tolerance).
- Hidden a/b/c: same checks against generator truth. Reference implementation `tests/reference.py` (stdlib,
  Fractions for exact arithmetic before rounding).
- Binary reward.

## 22. Answer-key leakage audit

| Artifact | Leak? | Mitigation |
|---|---|---|
| SSA excerpt | states funding principle, fee basis wording, "attributable" fee refund | no apportionment method, no eligibility rule, no reversal formula, no statement of cap retention; "attributable" admits pro rata |
| promotion programs doc | co-funded share meaning | no allocation |
| order service dictionary | `line_origin`, "refunds reference the charged line" | a join fact; the reship trap is small by itself |
| refund amounts | reveal per-line buyer-paid on refunded lines (6.9%) | not the seller statement; must be generalised to all lines; do not reveal reversals or fee refunds |
| recorded fees | reveal fee basis | intended evidence; do not reveal fee refunds |
| GL daily summary | monthly/daily totals for 4010, 6100, 4110; weekly 2100 | total-level only; cross-seller allocation invariant |
| payout statements | 3 sellers, weekly cash | reserves, settlement lag and batch netting prevent seller-month transcription; not present in hidden fixtures |
| support macros | two example explanations | examples, not formulas; 58 other macros are unrelated |
| notebook | wrong allocation, plausible number | attractor |
| code | no eligibility/markdown/fee schedule loading, no refund-line join, no reship handling, no unused helper | build review |

**Cheap-solve audit.**
- *One grep*: `grep -ri funding` → funding filter (fails).
- *One doc*: the SSA gives principles only. It says nothing about eligibility or the apportionment basis, so
  transcribing it yields the funding split and the fee basis and nothing else.
- *One SQL*: join refund_lines to lines and group by seller-month — misses reversal gross-up, shipping, fee state.
- *One filter*: `buyer_charged` / `funding_type` filters fix two of six mechanisms.
- *Helper*: none.
- *Old report*: pre-2025 statements are not in the workspace (the report was always top-down).
- *Restoring behaviour*: nothing to restore; the report was never bottom-up.
- *Residual risk*: an agent that reconciles to GL 4010 and runs full-refund exactness as a hypothesis test can discover
  every mechanism from data; that is intended reasoning, but it gives a strong feedback loop, reducing headroom.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Apportionment basis and eligibility | full-line refund exactness (system-of-record behaviour) |
| Rounding | tolerance; not graded exactly |
| Stacked promotions | independent apportionment evidenced by stacked full refunds |
| Co-funded share rounding | tolerance |
| Fee basis includes platform-funded discount? | recorded fees reproduce only this basis |
| Fee refund on amount-only concession | retained basis falls, qty unchanged; GL 4010 matches only this; macro example |
| Cap for refunds after schedule change | SSA "in effect when the order is placed"; GL 4010 |
| Refund exceeding buyer-paid | never generated |
| Refund month vs sale month | catalog (existing, unchanged) |
| Seller reserves in statement? | catalog: statement is accrual; reserves are cash timing (GL guide) |
| Shipping refunds | order service dictionary: shipping charged by platform; GL 4110 |
| Reship-of-reship refunds | refunds reference charged line; 12 visible chains |
| Take rate with zero denominator | existing statement code emits empty; unchanged |
| Negative net proceeds seller-months | allowed |

## 24. Expected trajectory length

45–70 actions. The first satisfying stopping point (funding filter; margins turn positive; tie-out ties) arrives
around action 20. Passing requires five further discoveries, three of which (basis/eligibility, fee refund state,
reversal gross-up) come from hypothesis tests against data rather than documents.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | G14 |
|---|---|
| target cutoff in faulty code | faulty code is top-down; no line-level scaffolding at all |
| adjustment summary implemented | nothing reusable: no refund-line join, no schedule lookup |
| natural group/merge/subtract correct | natural pro rata by price is wrong on eligibility, basis, reversals and fee caps |
| attractor optional | the tie-out and the funding filter are on the path; the notebook offers a second plausible allocation |
| traps on unchosen paths | pro rata, cash reversal and stateless fee refunds are the default implementations |
| one-customer check enough | Loomhaven turning positive is satisfied by wrong repairs; errors are spread across non-escalating sellers |

## 26. Comparison with Task 02

Task 02 required per-example × cutoff state; G14 requires per-line × refund-sequence state for fees and per-order
eligibility state for apportionment. Both have aggregate metrics that several wrong repairs satisfy. G14 is less
statistical and more accounting-exact; its evidence is more discoverable through data consistency tests (full-refund
exactness, recorded fees, GL 4010), which a disciplined agent can exploit. Expected difficulty: comparable to slightly
below Task 02 for strong agents, above it for agents that stop at the first positive margin.

## 27. Benchmark risks

- **Headroom**: the data gives exact hypothesis tests. An agent that thinks to test apportionment against refunds can
  converge. Mitigation is only that the first stopping point is very attractive. Honest estimate: moderate headroom.
- **Overlap**: Task 07 design (allocation) and Task 06 (financial statements). The mechanism (funding, eligibility,
  stateful fee refunds) is distinct; the "totals tie" attractor repeats Task 07's idea.
- **Realism**: per-unit caps with retained-state fee refunds are plausible but not universal; some marketplaces refund
  fees pro rata or keep an admin fee. The SSA must be explicit enough to make the capped reading the contract, which
  pushes toward leakage.
- **Gradability**: tolerance-based cents are safe; exactness of generator arithmetic (Fractions) must be mirrored.
- **Implementation cost**: medium. Order/refund simulation is straightforward; GL weekly settlement and reserves add
  work but are not graded.
- **Scoring note**: G14 scored 57 in `gen3_scoring.md` (lowest of the top 15); this design raises natural-wrong-path
  strength but not statistical depth.
