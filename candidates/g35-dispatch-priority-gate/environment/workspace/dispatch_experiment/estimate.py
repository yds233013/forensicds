"""Effect estimates for the priority-dispatch pilot.

Current readout: pooled treated-versus-control comparison across the whole pilot, demand weighted.
"""
from __future__ import annotations


def pooled_treated_vs_control(blocks):
    """Demand-weighted fulfilment of priority merchants minus everyone else."""
    nt = dt = nc = dc = 0.0
    for b in blocks:
        for r in b["rows"]:
            req = r["orders_requested"]
            if req <= 0:
                continue
            y = r["orders_delivered"] / req
            if r["assigned_priority"]:
                nt += y * req
                dt += req
            else:
                nc += y * req
                dc += req
    return nt / dt - nc / dc


def block_fulfilment(blocks):
    out = {}
    for b in blocks:
        req = sum(r["orders_requested"] for r in b["rows"])
        deliv = sum(r["orders_delivered"] for r in b["rows"])
        out[b["block_id"]] = (deliv / req if req else 0.0, req)
    return out
