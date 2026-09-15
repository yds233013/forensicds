# Forecast v4: model card (extract)

- **Owner:** Forecasting.
- **Target:** daily units sold per store-SKU.
- **Training:** at the LEAN-26 go-live, on each store-SKU's last 8 weeks of non-promotional sales with stockout days
  removed ("clean-day training"). The level is held until the next quarterly retrain.
- **Features:** weekday factors, promotion uplift by category (learned from recent promotions), trading hours, and a
  category season trend carried over from last year.
- **Validation:** holdout of recent weeks, MAPE against sales 19.8% vs v3 22.4%.
- **Deployment:** production forecast for LEAN-26 stores from go-live; runs for all stores.
