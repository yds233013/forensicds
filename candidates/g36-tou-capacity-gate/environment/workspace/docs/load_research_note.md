# Load Research note - peak-window demand and temperature

**Owner:** Load Research

## The weather relationship

Peak-window demand rises close to linearly with cooling degree days within the summer season. The
slope differs substantially by premises type: a large detached home with central air and a pool runs
several times the incremental load of an apartment on the same day.

This relationship is a property of the building stock and its equipment. It is estimated from the
flat-tariff seasons in `peak_window_load` and we have not seen it move in the years we have measured
it.

## Scope for shifting

Field observations from the pilot and from earlier demand-response programmes suggest the amount of
load a customer can actually move out of the peak window is **not the same on every day**. On mild
days a large share of peak-window consumption is discretionary - pool filtration, laundry, water
heating, pre-cooling - and can be rescheduled. On the hottest days the air conditioner is running
close to continuously simply to hold the thermostat setpoint, and there is much less left that can
be moved without the customer losing comfort.

We have not published a coefficient for this. The pilot season's daily data is the best evidence we
have on it.

## Seasonal forecast for 2027

`weather_forecast_2027` carries the issued seasonal outlook. The 2027 peak season is forecast
materially warmer than the seasons in our historical record.
