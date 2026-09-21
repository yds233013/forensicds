# Planning extract dictionary

| table | column | meaning |
|---|---|---|
| `customer_master` | `household_id`, `segment_code`, `service_zone`, `meter_installed_on` | every residential premises currently served |
| `weather_daily` | `service_date`, `cooling_degree_days` | measured cooling degree days, all seasons in the extract |
| `peak_window_load` | `household_id`, `service_date`, `peak_kw` | mean kW across the 17:00-21:00 window |
| `tou_pilot_enrolment` | `household_id`, `enrolled_on`, `assigned_arm` | rows exist only for customers who enrolled in the pilot; `assigned_arm` is `treatment` or `control` |
| `weather_forecast_2027` | `service_date`, `cooling_degree_days_forecast`, `issued_on` | the issued seasonal outlook for the target season |
| `extract_meta` | `key`, `value` | window definition, units, and which regime each season was under |

## Segment codes

| code | premises |
|---|---|
| `APT_ELECTRIC` | apartment, electric heating and cooling |
| `HOUSE_STANDARD` | detached house, standard central air |
| `HOUSE_SMART_HVAC` | detached house with a controllable thermostat |
| `HOUSE_LARGE_POOL` | large detached house with pool plant |

## Seasons in the extract

2024 and 2025 are flat-tariff seasons covering every customer. 2026 is the pilot season and contains
only enrolled customers. There is no 2027 load: that season has not happened.
