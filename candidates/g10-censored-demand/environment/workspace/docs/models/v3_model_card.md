# Forecast v3: model card (extract)

- **Owner:** Forecasting.
- **Method:** moving average of each store-SKU's non-promotional sales over the last 28 days, adjusted by weekday
  factors, trading hours and a promotion uplift by category.
- **Refresh:** nightly.
- **Deployment:** production forecast for all stores before LEAN-26; holdout stores after go-live.
