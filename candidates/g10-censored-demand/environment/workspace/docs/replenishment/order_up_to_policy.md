# Store replenishment: order-up-to policy

Owner: Replenishment Systems.

- **Delivery:** each store receives one DC delivery a day in its delivery slot (`stores.delivery_slot`):
  - `morning` stores are replenished at 06:00, before opening;
  - `afternoon` stores are replenished at 14:00, during trading.
- **Delivery quantity:** the delivery tops the store's stock of each SKU up to its **order-up-to level** for the day.
  If stock on hand is already at or above that level, nothing is delivered. Unsold stock stays on the shelf for the
  next day.
- **Order-up-to level** = `ceil(multiplier × production forecast for the day)`, capped at the SKU's shelf capacity in
  that store (`planogram.shelf_capacity`).
- **Production forecast:** the forecast the store orders from (`replenishment_orders.forecast_model`):
  - `v3` before LEAN-26;
  - `v4` in LEAN-26 stores from go-live;
  - `v3` in holdout stores.
- **Multipliers** (`replenishment_orders.multiplier`):
  - 1.8 before LEAN-26;
  - 1.25 in LEAN-26 stores after go-live;
  - 1.8 in holdout stores.
- **Order inputs:** orders are computed overnight from the forecast and the recorded stock position. Nothing observed
  during the delivery day changes them.
