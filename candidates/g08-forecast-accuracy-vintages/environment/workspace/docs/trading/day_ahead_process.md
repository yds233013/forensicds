# Day-ahead process

Owner: Trading Operations.

1. **06:00 UK time:** each forecasting model issues its forecast set (currently delivery days D+1 to D+7) for every region
   and portfolio.
2. Forecasts may be re-issued during the morning when input data is refreshed; a re-issue can cover all regions or a
   single region.
3. **11:00 UK time, gate closure:** the position builder locks the forecast set for the run day from the forecasts
   issued so far. The locked D+1 volumes go to the day-ahead auction; later delivery days go to the week-ahead hedge book.
4. Forecasts issued after gate closure do not change the day's positions. They are kept in the forecast store for
   review.

Shadow models go through exactly the same steps, including the lock, so they can be assessed as if they were in
production. Only the production model's locked set is traded.

UK time is Europe/London (GMT in winter, BST in summer).
