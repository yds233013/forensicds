# Buy-plan process (v4): category baselines

Owner: Supply Planning.

Each quarter Planning sets category buys from **baseline demand**. Baseline demand is what customers want on an
ordinary trading day, without promotions, and before any availability constraint. It is the demand the buy has to
cover, not what happened to sell.

- **Category baseline for a period:** sum over the category's store-SKUs of each store-SKU's average daily
  unconstrained demand on its non-promotional trading days in the period. Using averages per store-SKU keeps SKU mix
  changes out of the trend.
- **Quarterly action:** compare the latest period's baseline with the previous period's:

  | Baseline change | Action |
  |---|---|
  | ≤ −5% | `reduce` (cut next quarter's buy) |
  | ≥ +5% | `increase` |
  | otherwise | `maintain` |

- **Delisting reviews:** SKUs in `reduce` categories with falling baselines are put forward for range review.

For this review the periods are before and after the LEAN-26 go-live.
