"""Feature set of the renewal-risk model (order matters: it is the model's column order).

Definitions: docs/feature_dictionary.md. Each builder returns one row per example (`contract_id`)
with the columns of its group.
"""
from __future__ import annotations

CONTRACT = ["arr_usd_log", "seats_licensed", "plan_enterprise", "tenure_months", "prior_renewals"]
USAGE = ["active_user_ratio_4w", "active_user_trend_12w", "api_calls_4w_log", "logins_per_active_user_4w"]
SUPPORT = ["tickets_90d", "sev1_tickets_180d", "open_tickets_at_prediction"]
PIPELINE = ["has_renewal_opp", "renewal_stage_ordinal", "forecast_commit", "forecast_best_case", "forecast_omitted",
            "renewal_amount_ratio", "days_to_opp_close", "competitor_flagged", "open_expansion_opps"]
HEALTH = ["health_score", "health_red", "nps_last", "csm_sentiment_negative"]

FEATURE_COLUMNS = CONTRACT + USAGE + SUPPORT + PIPELINE + HEALTH
