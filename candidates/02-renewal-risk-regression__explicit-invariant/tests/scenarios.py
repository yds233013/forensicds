"""Hidden generalization fixtures for Task 02 (never present in the agent's environment).

Every fixture keeps the same invariant - a training example may only use information that had been
loaded into the warehouse before 00:00 UTC on its prediction date - while changing the surface:
calendar and run date, account ids, which fields carry post-prediction outcome information, how
many legitimate changes happen before and after the cutoff, and the replication schedules that
make business timestamps differ from load timestamps.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    for k, v in over.items():
        if isinstance(v, dict):
            s[k].update(v)
        else:
            s[k] = v
    return s


HIDDEN_SPECS = [
    # A: outcome information leaks mainly through Customer Success data (health, NPS, sentiment) and
    #    competitor capture on losses, while reps rarely update opportunity stage/forecast. A repair that
    #    only reconstructs the CRM fields that leaked in the visible data, or only opportunities, fails.
    #    Different run date; a CRM outage at a different time; health batch loads at 04:00.
    _spec(name="hidden_a", seed=31337, extract_date="2025-12-10", first_account_date="2020-09-01", n_accounts=700,
          crm={"rep_update_prob_churn": 0.1, "rep_update_prob_renew": 0.15, "stale_close_prob": 0.05,
               "competitor_on_loss": 0.8, "partner_share": 0.05,
               "outages": [{"start": "2025-06-09 00:00:00", "end": "2025-06-14 00:00:00", "replay": "2025-06-14 05:40:00"}]},
          health={"churn_decline": 1.0, "sentiment_escalation": 0.85, "renewer_improve": 0.4, "sync_time": "04:00:00"}),
    # B: many legitimate changes before the cutoff (so creation-time values are wrong) and after it
    #    (renewer expansions, health improvements), more expansion pipeline, no outages. Different
    #    calendar (2024 run) and health batch time.
    _spec(name="hidden_b", seed=2718, extract_date="2024-09-20", first_account_date="2019-11-01", n_accounts=650,
          pre_cutoff_changes=[2, 6], late_opp_share=0.05, expansion_rate_per_year=0.9,
          crm={"renewer_amount_change": 0.9, "outages": [], "partner_share": 0.1},
          health={"renewer_improve": 0.5, "renewer_decline": 0.3, "sync_time": "02:15:00"}),
    # C: heavy late arrival. Two CRM replication outages at different dates, a large partner channel
    #    replicated weekly on Wednesdays, many renewal opportunities created close to the prediction date,
    #    and Customer Success health loaded with a two-day lag. Business timestamps (`changed_at`,
    #    `created_at`) and hard-coded knowledge of the visible outage or load schedule both give wrong answers.
    _spec(name="hidden_c", seed=1618, extract_date="2026-03-05", first_account_date="2021-01-15", n_accounts=750,
          late_opp_share=0.3,
          crm={"partner_share": 0.35, "partner_sync_weekday": 2, "partner_sync_time": "23:30:00",
               "outages": [{"start": "2025-04-21 00:00:00", "end": "2025-05-06 00:00:00", "replay": "2025-05-06 07:00:00"},
                           {"start": "2025-12-15 00:00:00", "end": "2025-12-29 00:00:00", "replay": "2026-01-02 09:30:00"}]},
          health={"sync_day_lag": 2, "sync_time": "00:45:00"}),
]
