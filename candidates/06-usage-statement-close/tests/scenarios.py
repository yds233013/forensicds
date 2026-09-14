"""Hidden extracts for Task 06 (never present in the agent's environment).

Every fixture keeps the documented semantics (contract §4, billing schedule, vendor delivery documentation, data
catalog) and changes the calendar, volumes, and how often each documented delivery behaviour occurs.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    s.setdefault("northwind_headroom", None)
    return s


HIDDEN_SPECS = [
    # A: earlier calendar; a us-east connectivity loss in the middle of a month with a longer resend window; far more
    #    out-of-order corrections, voids and collector retries; streaming cutover in December; rate change in January.
    _spec(name="hidden_a", seed=11001, world_start="2025-10-01", extract_at="2026-03-05T18:00:00", statement_month="2026-02",
          cutover="2025-12-08T00:00:00", late_runs={}, n_customers=22, amendments={}, northwind_headroom=None,
          rate_changes={"2026-01": 1.06}, out_of_order_share=0.4, void_share=0.012, retry_share=0.012,
          outages=[{"collector": "us-east", "start": "2026-01-12T03:00:00", "end": "2026-01-14T20:00:00",
                    "replay_hours": 10, "flush_hours": 5}]),
    # B: mixed issuing history (batch, streaming, batch, streaming), so some months were already adjusted and are
    #    corrected again; many corrections long after the window; an allowance amendment; an outage across a month end;
    #    extract taken shortly after the close.
    _spec(name="hidden_b", seed=22002, world_start="2026-06-01", extract_at="2026-12-04T10:00:00", statement_month="2026-11",
          policies={"2026-06": "batch", "2026-07": "v2", "2026-08": "v2", "2026-09": "batch", "2026-10": "v2"},
          late_runs={"2026-09": "2026-10-06T11:00:00"}, n_customers=26, amendments={"#4": "2026-09", "#9": "2026-10"},
          northwind_headroom=None, rate_changes={"2026-08": 1.04, "2026-11": 1.10}, late_revision_share=0.01,
          late_revision_days=[30, 70], very_late_share=0.004, very_late_days=[20, 60], second_revision_share=0.5,
          outages=[{"collector": "ap-south", "start": "2026-10-30T20:00:00", "end": "2026-11-01T06:00:00",
                    "replay_hours": 4, "flush_hours": 2}]),
    # C: year boundary; a third meter; a customer that stops using the platform in December; a us-east connectivity
    #    loss that ends exactly at the close, so buffered records land on the close and records sent before the close are
    #    resent after it; the extract is taken ten days after the close, so many records and corrections arrive after it.
    _spec(name="hidden_c", seed=33003, world_start="2026-09-01", extract_at="2027-02-14T00:00:00", statement_month="2027-01",
          cutover="2026-11-02T00:00:00", late_runs={}, n_customers=30, amendments={}, northwind_headroom=None,
          meters={**VISIBLE_SPEC["meters"], "egress_gb": {"level": 12.0, "sigma": 0.9, "r1": "0.0900", "r2": "0.0700",
                                                            "tier1_share": 0.2}},
          rate_changes={"2027-01": 1.07}, churn={"3": "2026-12-20T00:00:00"}, late_share=0.03,
          outages=[{"collector": "us-east", "start": "2027-01-31T19:00:00", "end": "2027-02-04T00:00:00",
                    "replay_hours": 6, "flush_hours": 4, "flush_at_end_share": 0.3}],
          revision_share=0.05),
]
