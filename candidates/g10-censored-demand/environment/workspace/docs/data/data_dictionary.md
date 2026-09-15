# Warehouse data dictionary (extract)

All timestamps are store local time (`YYYY-MM-DD HH:MM:SS`). Dates are `YYYY-MM-DD`.

| Table | Grain | Columns |
|---|---|---|
| `stores` | store | `store_id`, `store_name`, `delivery_slot` (`morning` / `afternoon`), `delivery_time` |
| `store_calendar` | store × date | `status` (`open` / `closed`), `open_time`, `close_time` (trading hours; NULL when closed) |
| `skus` | SKU | `sku_id`, `category`, `description` |
| `planogram` | store × SKU | `shelf_capacity` (units) |
| `promotions` | promotion | `sku_id`, `start_date`, `end_date` (inclusive; chain-wide), `mechanic` |
| `sales_hourly` | store × SKU × date × hour | `hour` (clock hour 0–23: sales from `hour:00` to before `hour+1:00`), `units`. Hours with no sales have no row. |
| `availability_events` | event | `store_id`, `sku_id`, `event_time`, `event_type` |
| `inventory_daily` | store × SKU × trading date | `on_hand_open` (shelf stock when the store opens, after any morning delivery), `delivered_units`, `delivered_at`, `on_hand_close` |
| `replenishment_orders` | store × SKU × trading date | `forecast_model`, `forecast_units`, `multiplier`, `order_up_to` |
| `forecasts` | model × store × SKU × date | `forecast_units` (day-ahead forecast of units for the day). v3 for all dates; v4 from the LEAN-26 go-live. |
| `programme_assignment` | store | `programme`, `arm` (`lean26` / `holdout`), `go_live_date`, `randomisation_block` |

**`availability_events.event_type`:**
- `out_of_stock`: recorded at the moment shelf stock reaches zero (the sale of the last unit);
- `back_in_stock`: recorded when a delivery puts stock back on an empty shelf.
