# v4 release note (Forecasting)

- **Model:** gradient-boosted trees on regional weather ensembles, holiday calendars and lagged settlement data.
- **Shadow from run day 5 January 2026; production from 6 April 2026.** v3 continues in shadow.
- **Automatic re-issue:** v4 re-runs all regions as soon as the 06Z weather model lands (usually 12:25-12:55 UK),
  so the forecast store always holds the freshest forecast. In testing this improved D+1 to D+3 accuracy by about
  25%.
- **Offline backtest (Jan 2024 to Dec 2025):** WAPE 11% better than v3.
