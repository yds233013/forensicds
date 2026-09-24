"""Rescoring noshow-v3.1 from the coefficients published in the model registry.

The registry records the feature definitions the model was fitted on: `prior_no_shows_12m` is the count of
did-not-attend events in a rolling window before booking, capped, and the continuous features are centred.
"""
PRIOR_CAP = 3
CENTRES = {"lead_time_days": 21.0, "deprivation_decile": 5.5, "distance_km": 8.0}


def score(coef, prior_no_shows, lead_time_days, deprivation_decile, distance_km, age_band, appointment_type):
    z = (coef["intercept"]
         + coef["prior_no_shows_12m"] * min(prior_no_shows, PRIOR_CAP)
         + coef["lead_time_days_c"] * (lead_time_days - CENTRES["lead_time_days"])
         + coef["deprivation_decile_c"] * (deprivation_decile - CENTRES["deprivation_decile"])
         + coef["distance_km_c"] * (distance_km - CENTRES["distance_km"])
         + coef[f"age_{age_band}"]
         + coef[f"type_{appointment_type}"])
    if z < -35:
        return 0.0
    if z > 35:
        return 1.0
    import math
    return 1.0 / (1.0 + math.exp(-z))


def score_feature_store_current(coef, row):
    """The feature store as it now stands: the values it served, with the no-show count recomputed over the
    window currently configured."""
    return score(coef, row["prior_no_show_count"], row["lead_time_days"], row["deprivation_decile"],
                 row["distance_km"], row["age_band"], row["appointment_type"])


def score_record_features_asof_window(coef, row, history, window_days):
    """Rescore from source record and event history using the window the model was defined on."""
    from datetime import datetime, timedelta
    booked_on = datetime.strptime(row["booked_on"], "%Y-%m-%d")
    window_start = (booked_on - timedelta(days=window_days)).strftime("%Y-%m-%d")
    
    prior_no_shows = 0
    for event_on in history.get(row["patient_id"], []):
        if window_start <= event_on < row["booked_on"]:
            prior_no_shows += 1
            
    return score(coef, prior_no_shows, row["lead_time_days"], row["deprivation_decile"],
                 row["distance_km"], row["age_band"], row["appointment_type"])
