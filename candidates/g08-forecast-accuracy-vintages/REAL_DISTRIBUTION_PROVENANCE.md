# Real-distribution provenance — g08 (forecast accuracy mart)

1. **Professional role.** Analytics engineer / data scientist owning a forecast-accuracy mart.
2. **Industry.** Energy/commodity trading analytics.
3. **Business decision.** Whether to retire forecast model v3 in favour of v4, on the strength of the
   monthly accuracy pack the model board reviews.
4. **Realistic inherited artifacts.** Forecast submissions with origin timestamps, an actuals series
   that is restated after the fact, the accuracy mart that replaced the previous notebook, the
   September accuracy review built from the mart, and the mart's transformation code.
5. **Statistical/ML problem.** Vintage-correct accuracy measurement. A forecast must be scored against
   the actuals as they stood when the forecast was made, or against a consistently defined vintage;
   scoring against the latest restated actuals mixes forecast error with revision history and is not
   comparable across models whose forecasts were made at different times.
6. **Why this happens in real organizations.** Using revised data rather than the data available at
   forecast time exaggerates apparent forecast performance and gives a misleading picture of real-time
   behaviour; for revisable series a pooled accuracy statistic reflects both forecast performance and
   how far the outcomes have been revised. The specific failure — "scoring a day-one forecast using
   current field values instead of the values as of day one" — is described as the single most common
   reason a backtest overstates accuracy.
7. **Public sources.**
   - *Revision Risk in Real-Time Macroeconomic Forecasting*: https://arxiv.org/pdf/2607.05882
   - *Forecasting in the Fog: Real-Time versus Revised-Data Evidence*: https://arxiv.org/pdf/2608.09033
   - ORM Tech, *How to Backtest a Sales Forecast Model Before You Trust It*: https://orm-tech.com/blog/how-to-backtest-a-sales-forecast-model
   - *Forecasting: theory and practice*: https://arxiv.org/pdf/2012.03854
8. **What is synthetic.** The trading desk, series, forecasts and restatement process.
9. **What is preserved.** A bitemporal actuals table with restatements, forecasts with origin
   timestamps, a mart migration as the plausible cause of a reporting change, and a comparison between
   two models whose forecast origins differ.
10. **Why it belongs.** It is the suite's data-vintage / as-of reconstruction task — a distinctively
    data-engineering-adjacent scientific failure that no other final task covers — and it is the only
    final task whose mechanism lives in the *temporal semantics of the evidence table* rather than in
    the estimator or the population.
