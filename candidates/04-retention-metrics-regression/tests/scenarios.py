"""Hidden generalization fixtures for Task 04 (never present in the agent's environment).

Each fixture keeps the handbook definitions and changes how customers, prospects, win-backs, contract timing and
segments arise in the data, so that only the definitions - not properties of the visible extract - give the right
cohorts, movements and segments.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(s.get(k), dict):
            s[k].update(v)
        else:
            s[k] = v
    return s


HIDDEN_SPECS = [
    # A: win-back heavy company with no ABM program. Many former customers return after long gaps (up to ~2.5 years)
    #    and many first contracts are 1- or 3-month terms that end between quarter boundaries. Outbound reps pre-create
    #    most accounts long before contracts.
    _spec(name="hidden_a", seed=8181, start_date="2020-01-01", extract_date="2025-11-12", as_of="2025-11-12",
          abm=None, outbound_precreate_share=0.65, outbound_lead_days=[60, 400], reactivation_prob=0.7,
          reactivation_gap_days=[30, 900], short_term_share=0.35, annual_churn_prob=0.18, big_deal=None,
          price_increase={"from": "2024-01-01", "uplift": 0.05}, line_split_from="2030-01-01"),
    # B: renewals signed long before the new term starts, frequent renewal gaps that straddle quarter ends, an ABM
    #    program that starts earlier with shorter lead times, a large expansion in a different quarter.
    _spec(name="hidden_b", seed=4242, start_date="2020-07-01", extract_date="2026-02-20", as_of="2026-02-20",
          early_signing_days=[30, 160], renewal_gap_prob=0.45, abm={"from": "2024-01-01", "prospects_per_month": 70,
          "convert_share": 0.35, "lead_months": [1, 6]}, big_deal={"date": "2025-05-19", "arr": 800_000},
          inbound_lead_days=[20, 90]),
    # C: larger customers (many cross segment thresholds, some start a quarter at exactly 25,000.00 or 100,000.00 ARR),
    #    heavy CRM contract-type mislabelling, different calendar.
    _spec(name="hidden_c", seed=1357, start_date="2021-10-01", extract_date="2027-05-02", as_of="2027-05-02",
          arr_scale=2.6, upsell_prob=0.55, downsell_prob=0.25, contract_type_mislabel=0.4, new_customers_per_month=18,
          abm={"from": "2026-01-01", "prospects_per_month": 40, "convert_share": 0.3, "lead_months": [3, 9]},
          price_increase={"from": "2026-04-01", "uplift": 0.09}, big_deal=None,
          boundary_arr_accounts={"per_value": 5, "values": [25000.0, 100000.0], "from": "2025-03-15", "to": "2026-12-01"}),
]
