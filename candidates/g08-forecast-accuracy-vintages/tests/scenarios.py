"""Hidden extracts for G08 (never present in the agent's environment).

Every fixture keeps the documented semantics (KPI definition, settlement process, day-ahead gate, forecast store,
portfolio membership, close log) and changes the calendar, which models exist, how often each documented situation
occurs and where it falls relative to KPI closes and gate closures.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    settlement = s["settlement"]
    settlement.update(over.pop("settlement", {}))
    s.update(over)
    s["settlement"] = settlement
    s["artifacts"] = False
    return s


HIDDEN_SPECS = [
    # A "close boundaries": earlier calendar; settlement-agent outages that push Initial Settlement past two closes;
    #   four times the withdrawals with many straddling closes (gap at close, withdrawn after close); data corrections
    #   clustered just before and just after closes; December and February closes slip (February by four working days)
    #   and the as-of falls after February's nominal close but before its actual close.
    _spec(name="hidden_a", seed=11101, delivery_start="2024-10-20", extract_at="2026-03-24T06:00:00",
          first_kpi_month="2024-12", as_of="2026-03-20T09:00:00Z",
          portfolios=[("2024-01-01", {"RESI": ["DOM"], "BUSINESS": ["SME_NHH", "SME_HH", "IC_HH", "UMS"]}),
                      ("2025-05-01", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH", "UMS"], "IC": ["IC_HH"]})],
          models=[{**VISIBLE_SPEC["models"][0], "first_run": "2024-11-15", "production_to": "2025-08-31"},
                  {**VISIBLE_SPEC["models"][1], "first_run": "2025-06-02", "production_from": "2025-09-01"}],
          close={"wd": 12, "hour": 17, "slips": {"2025-12": 2, "2026-02": 4}},
          settlement={"withdraw": 0.04, "late_is": 0.03, "dc": {"IS": 0.05, "R1": 0.02},
                      "outages": [{"regions": ["SOUTH", "WEST"], "run_type": "IS", "from": "2025-11-17", "to": "2025-11-28",
                                   "publish_local": "2025-12-19T12:10:00"},
                                  {"regions": ["LONDON"], "run_type": "IS", "from": "2026-01-19", "to": "2026-01-30",
                                   "publish_local": "2026-02-20T10:25:00"}],
                      "boundary_cases": {"withdrawn_after_close": 25, "gap_at_close": 25, "dc_after_close": 25,
                                         "is_after_close": 25, "dc_before_close": 25}},
          migration_month="2099-01"),
    # B "portfolio & issuing": autumn/winter/spring calendar (other DST dates); horizons 1..10; restructures that take
    #   effect in the middle of a month, a new EV portfolio for a new settlement class, and unmetered supplies moving
    #   portfolio; three times the scoped pre-gate and gate-miss re-issues; v4's automatic re-issue sometimes lands
    #   before the gate.
    _spec(name="hidden_b", seed=22202, delivery_start="2026-08-20", extract_at="2027-06-25T06:00:00",
          first_kpi_month="2026-10", as_of="2027-06-25T06:00:00Z", horizons=10,
          classes={**VISIBLE_SPEC["classes"],
                   "EV_HH": {"base": 260.0, "season": 0.12, "sat": 1.10, "sun": 1.12, "gamma": -0.003, "est_share": 0.0,
                             "start": "2027-01-11"}},
          portfolios=[("2025-01-01", {"RESI": ["DOM"], "SME": ["SME_NHH", "UMS"], "IC": ["SME_HH", "IC_HH"]}),
                      ("2026-12-15", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH", "UMS"], "IC": ["IC_HH"]}),
                      ("2027-01-11", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH", "UMS"], "IC": ["IC_HH"], "EV": ["EV_HH"]}),
                      ("2027-04-15", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH"], "IC": ["IC_HH", "UMS"], "EV": ["EV_HH"]})],
          models=[{**VISIBLE_SPEC["models"][0], "first_run": "2026-09-01", "production_to": "2027-01-31", "review_reissue": 0.03},
                  {**VISIBLE_SPEC["models"][1], "first_run": "2026-09-01", "production_from": "2027-02-01", "auto_pregate": 0.3}],
          issuing={"sched_fail": 0.02, "no_pregate": 0.004, "partial_pregate": 0.09, "gate_miss": 0.09, "gate_miss_partial": 0.6},
          close={"wd": 12, "hour": 17, "slips": {"2027-03": 1}},
          settlement={"outages": [], "boundary_cases": {"withdrawn_after_close": 2, "gap_at_close": 2, "dc_after_close": 2,
                                                        "is_after_close": 2, "dc_before_close": 2}},
          migration_month="2099-01"),
    # C "revision regime & models": three models (v5 in shadow); R1 published nine working days after delivery, so it is
    #   known at most closes; frequent R1/R2 data corrections, correction chains, withdrawn corrections and dispute runs;
    #   no automatic re-issues.
    _spec(name="hidden_c", seed=33303, delivery_start="2025-12-01", extract_at="2026-11-20T06:00:00",
          first_kpi_month="2026-01", as_of="2026-11-20T06:00:00Z",
          portfolios=[("2025-01-01", {"RESI": ["DOM"], "SME": ["SME_NHH", "SME_HH", "UMS"], "IC": ["IC_HH"]})],
          models=[{**VISIBLE_SPEC["models"][0], "first_run": "2025-12-15", "production_to": "2026-06-30"},
                  {**VISIBLE_SPEC["models"][1], "first_run": "2025-12-15", "production_from": "2026-07-01", "auto_reissue": 0.0},
                  {"model": "v5", "first_run": "2026-05-04", "production_from": None, "production_to": None,
                   "description": "Hierarchical temporal fusion model (shadow)", "a": 0.80, "u0": 0.023, "uh": 0.0017,
                   "auto_reissue": 0.0, "auto_pregate": 0.0, "review_reissue": 0.02}],
          close={"wd": 12, "hour": 17, "slips": {"2026-08": 1}},
          settlement={"wd": {"IS": 7, "R1": 9, "R2": 40, "RF": 200}, "withdraw": 0.015,
                      "dc": {"IS": 0.04, "R1": 0.06, "R2": 0.05}, "dc_chain": 0.25, "dc_withdrawn": 0.15, "df": 0.02,
                      "outages": [], "boundary_cases": {"withdrawn_after_close": 4, "gap_at_close": 4, "dc_after_close": 4,
                                                        "is_after_close": 4, "dc_before_close": 4}},
          migration_month="2099-01"),
]
