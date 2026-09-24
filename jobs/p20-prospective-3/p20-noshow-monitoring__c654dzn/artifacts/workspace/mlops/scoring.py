import math
from datetime import datetime, timedelta

PRIOR_CAP = 3
CENTRES = {"lead_time_days": 21.0, "deprivation_decile": 5.5, "distance_km": 8.0}


def score(coef, prior_no_shows, lead_time_days, deprivation_decile, distance_km, age_band, appointment_type):
    z = (coef["intercept"]
         + coef["prior_no_shows_12m"] * min(prior_no_shows, PRIOR_CAP)
         + coef["lead_time_days_c"] * (lead_time_days - CENTRES["lead_time_days"])
         + coef["deprivation_decile_c"] * (deprivation_decile - CENTRES["deprivation_decile"])
         + coef["distance_km_c"] * (distance_km - CENTRES["distance_km"])
         + coef.get(f"age_{age_band}", 0.0)
         + coef.get(f"type_{appointment_type}", 0.0))
    if z < -35:
        return 0.0
    if z > 35:
        return 1.0
    return 1.0 / (1.0 + math.exp(-z))


def count_prior(events, pid, booked_on, window_days):
    if pid not in events:
        return 0
    booked_dt = datetime.strptime(booked_on, "%Y-%m-%d")
    start_dt = booked_dt - timedelta(days=window_days)
    count = 0
    for e_on in events[pid]:
        e_dt = datetime.strptime(e_on, "%Y-%m-%d")
        if start_dt <= e_dt < booked_dt:
            count += 1
    return count


def score_record_features_asof_window(coef, row, events, window_days):
    prior = count_prior(events, row["patient_id"], row["booked_on"], window_days)
    return score(coef, prior, row["lead_time_days"], row["deprivation_decile"],
                 row["distance_km"], row["age_band"], row["appointment_type"])


def score_feature_store_current(coef, row):
    return score(coef, row["prior_no_show_count"], row["lead_time_days"], row["deprivation_decile"],
                 row["distance_km"], row["age_band"], row["appointment_type"])
