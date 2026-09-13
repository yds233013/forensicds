"""Hidden generalization fixtures for Task 03 (never present in the agent's environment).

Each fixture keeps the evaluation design (exploration holdout assigned at intake, 60-day outcome, 180-day window,
champion score) and changes how the routed, worked and labelled populations are produced.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: smaller holdout (5%), three router versions inside the window, reps claim far more nurture leads and SDRs
    #    miss SLA more often. Worked-lead and per-protocol populations diverge strongly from the holdout.
    _spec(name="hidden_a", seed=7331, start_date="2024-10-01", extract_date="2025-10-04", as_of="2025-10-01",
          leads_per_day=95, holdout_pct=5, sla_breach_rate=0.12, claim_base=0.08, claim_demo_request=0.35,
          thresholds=[{"from": "2024-01-01", "threshold": 0.35, "version": "router-2024.09"},
                      {"from": "2025-03-10", "threshold": 0.26, "version": "router-2025.03"},
                      {"from": "2025-06-02", "threshold": 0.18, "version": "router-2025.06"}],
          campaigns=[{"source": "content_download", "from": "2025-04-01", "to": "2025-05-15", "extra_per_day": 25,
                      "intent_shift": -0.9}],
          challenger_from="2025-02-01"),
    # B: holdout paused for three weeks during an SDR capacity crunch, and a territory realignment re-routes a third
    #    of holdout leads after intake. Current routing state no longer identifies the intake assignment.
    _spec(name="hidden_b", seed=9090, start_date="2025-03-01", extract_date="2026-03-04", as_of="2026-03-01",
          holdout_pct=15, reassign_rate_holdout=0.35, reassign_rate_routed=0.2,
          holdout_pauses=[{"start": "2025-09-08 00:00:00", "end": "2025-09-29 00:00:00"}],
          thresholds=[{"from": "2024-01-01", "threshold": 0.28, "version": "router-2025.02"}],
          campaigns=[], challenger_from="2025-08-01"),
    # C: strong self-serve purchasing by unworked leads and many deals closing around day 60 (some on day 60 exactly,
    #    some just after); more rejected leads; more partner leads (midnight batch import); different calendar/mix.
    _spec(name="hidden_c", seed=2468, start_date="2026-01-05", extract_date="2027-01-06", as_of="2027-01-01",
          leads_per_day=70, reject_rate=0.14, unworked_conv_intercept=-3.4, unworked_conv_slope=1.0,
          late_close_share=0.35, late_close_days=[56, 80], sla_breach_rate=0.03,
          source_mix={"web_form": .22, "demo_request": .10, "content_download": .18, "webinar": .20, "partner_referral": .30},
          thresholds=[{"from": "2025-01-01", "threshold": 0.24, "version": "router-2026.01"}],
          campaigns=[{"source": "partner_referral", "from": "2026-07-01", "to": "2026-08-15", "extra_per_day": 20,
                      "intent_shift": 0.3}],
          challenger_from="2026-01-05"),
]
