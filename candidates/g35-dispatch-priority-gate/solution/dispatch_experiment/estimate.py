"""Effect estimates for the priority-dispatch pilot.

Three distinct objects are produced from the same experiment:

* the DIRECT effect, treated minus control inside the half-saturated dispatch pools;
* the SPILLOVER on merchants without priority, half-saturated pools versus unsaturated pools;
* the FULL-ROLLOUT policy effect, the contrast between pools where every merchant was offered
  priority and pools where none was.

The pooled treated-versus-control comparison is a valid estimate of a mixed-saturation direct
effect. It is not the rollout contrast, because a priority merchant's gain is partly taken from the
merchants beside it in the same courier pool.
"""
from __future__ import annotations


def _weighted(pairs):
    num = sum(y * w for y, w in pairs)
    den = sum(w for _, w in pairs)
    return num / den if den else 0.0


def _arm(blocks, saturation):
    """Demand-weighted fulfilment across every block assigned this saturation."""
    num = den = 0.0
    for b in blocks:
        if abs(b["assigned_saturation"] - saturation) > 1e-9:
            continue
        num += sum(r["orders_delivered"] for r in b["rows"])
        den += sum(r["orders_requested"] for r in b["rows"])
    return num / den if den else 0.0


def policy_effect_full(blocks):
    """Effect of offering priority to every merchant, versus offering it to none."""
    return _arm(blocks, 1.0) - _arm(blocks, 0.0)


def _half_split(blocks):
    t_num = t_den = c_num = c_den = 0.0
    for b in blocks:
        if abs(b["assigned_saturation"] - 0.5) > 1e-9:
            continue
        for r in b["rows"]:
            if r["assigned_priority"]:
                t_num += r["orders_delivered"]
                t_den += r["orders_requested"]
            else:
                c_num += r["orders_delivered"]
                c_den += r["orders_requested"]
    return (t_num / t_den if t_den else 0.0), (c_num / c_den if c_den else 0.0)


def direct_effect_50(blocks):
    """Own-treatment effect at the experiment's half-saturated exposure."""
    t, c = _half_split(blocks)
    return t - c


def spillover_50(blocks):
    """Effect on merchants WITHOUT priority of their pool being half saturated."""
    _, c = _half_split(blocks)
    return c - _arm(blocks, 0.0)


def block_fulfilment(blocks):
    out = {}
    for b in blocks:
        req = sum(r["orders_requested"] for r in b["rows"])
        deliv = sum(r["orders_delivered"] for r in b["rows"])
        out[b["block_id"]] = (deliv / req if req else 0.0, req)
    return out
