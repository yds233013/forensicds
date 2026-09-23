"""G41 wrong-object panel and valid-route check, measured on the four graded extracts (research/dev only).

Every wrong object is a mathematically correct optimisation over a WRONG operational state. Labels are
fixed here before the numbers are read. The graded quantities are deterministic integers / exact costs,
so the tolerance is exact equality for the shortfall (0 units) and 0.01 for the cost (2 decimals).

    python tools/g41/panel.py
"""
from __future__ import annotations

import copy, json, os, sys
from datetime import timedelta
from pathlib import Path

T = Path("/Users/yashshah2311/forensicds/candidates/g41-service-parts-rebalancing")
sys.path.insert(0, str(T / "tests"))
import world, scenarios                                             # noqa: E402


def variant(w, *, ignore_alloc=False, quarantine_ok=False, consignment_ok=False, no_safety=False,
            cancelled_po_ok=False, no_dock=False, any_eta=False, no_transit=False, no_transfer=False,
            cancelled_jobs=False, horizon_need_by=False):
    v = copy.deepcopy(w)
    if ignore_alloc:
        for a in v["allocations"]:
            a["status"] = "CANCELLED"
    for s in v["stock"]:
        if quarantine_ok and s["status"] == "QUARANTINE":
            s["status"] = "AVAILABLE"
        if consignment_ok and s["status"] == "CONSIGNMENT":
            s["status"] = "AVAILABLE"
    if no_safety:
        v["safety"] = {k: 0 for k in v["safety"]}
    if cancelled_po_ok:
        for p in v["inbound"]:
            p["status"] = "CONFIRMED"
    if no_dock:
        v["spec"] = dict(v["spec"], dock_to_stock_days=0)
    if any_eta:
        for p in v["inbound"]:
            p["eta"] = v["t0"]
    if no_transit:
        for k in v["lanes"]:
            v["lanes"][k] = dict(v["lanes"][k], transit_days=0)
    if no_transfer:
        v["lanes"] = {}
    if cancelled_jobs:
        for j in v["jobs"]:
            j["status"] = "SCHEDULED"
    if horizon_need_by:
        end = v["t0"] + timedelta(days=v["spec"]["horizon_days"])
        for j in v["jobs"]:
            j["need_by"] = end
    return v


def pooled_netting(w):
    """'The network has enough': demand minus total ATP, pooled over depots, per part."""
    st = world.state(w); short = 0
    for part in {j["part"] for j in st["jobs"]}:
        dem = sum(j["qty"] for j in st["jobs"] if j["part"] == part)
        sup = sum(q for (d, p), q in st["atp"].items() if p == part) + sum(r["qty"] for r in st["inbound"] if r["part"] == part)
        short += max(0, dem - sup)
    return {"shortfall": short, "transfer_cost": None}


def feasible_but_costly(w):
    """Correct feasible set and correct shortfall, but the plan is not cost-minimal: lanes chosen by
    transit time (fastest first) rather than by cost."""
    v = copy.deepcopy(w)
    for k, ln in v["lanes"].items():
        v["lanes"][k] = dict(ln, cost_per_unit=float(ln["transit_days"]))
    t = world.optimum(v)                                  # optimal under the surrogate objective
    cost = 0.0
    for tr in t["transfers"]:
        cost += tr["qty"] * w["lanes"][(tr["from"], tr["to"])]["cost_per_unit"]
    return {"shortfall": t["shortfall"], "transfer_cost": round(cost, 2)}


WRONG = {
    "W01_on_hand_ignores_open_allocations": lambda w: world.optimum(variant(w, ignore_alloc=True)),
    "W02_quarantine_counted_as_available": lambda w: world.optimum(variant(w, quarantine_ok=True)),
    "W03_consignment_counted_as_available": lambda w: world.optimum(variant(w, consignment_ok=True)),
    "W04_safety_stock_shippable": lambda w: world.optimum(variant(w, no_safety=True)),
    "W05_cancelled_pos_counted": lambda w: world.optimum(variant(w, cancelled_po_ok=True)),
    "W06_no_dock_to_stock_delay": lambda w: world.optimum(variant(w, no_dock=True)),
    "W07_all_inbound_available_now": lambda w: world.optimum(variant(w, any_eta=True)),
    "W08_transfers_ignore_transit_time": lambda w: world.optimum(variant(w, no_transit=True)),
    "W09_no_transfers_local_only": lambda w: world.optimum(variant(w, no_transfer=True)),
    "W10_pooled_network_netting": pooled_netting,
    "W11_cancelled_jobs_in_demand": lambda w: world.optimum(variant(w, cancelled_jobs=True)),
    "W12_need_by_ignored_horizon_end": lambda w: world.optimum(variant(w, horizon_need_by=True)),
    "W13_on_hand_and_quarantine": lambda w: world.optimum(variant(w, ignore_alloc=True, quarantine_ok=True)),
    "W14_min_shortfall_but_fastest_lanes": feasible_but_costly,
}


def main():
    out = {}
    print(f"{'method':44s} " + "  ".join(f"{n:>22s}" for n in scenarios.ALL_NAMES))
    truths = {}
    for n in scenarios.ALL_NAMES:
        truths[n] = world.truth(world.build(scenarios.by_name(n)))
    print(f"{'TRUTH shortfall / cost':44s} " + "  ".join(
        f"{truths[n]['shortfall']:8d} /{truths[n]['transfer_cost']:11.2f}" for n in scenarios.ALL_NAMES))
    for m, fn in WRONG.items():
        row, rej = [], 0
        for n in scenarios.ALL_NAMES:
            w = world.build(scenarios.by_name(n)); t = truths[n]
            r = fn(w)
            ds = r["shortfall"] - t["shortfall"]
            dc = None if r.get("transfer_cost") is None else round(r["transfer_cost"] - t["transfer_cost"], 2)
            bad = (ds != 0) or (dc is not None and abs(dc) > 0.01)
            rej += bad
            row.append(f"{ds:+8d} /{('    n/a' if dc is None else f'{dc:+11.2f}')}")
        out[m] = {"rejected_on": rej, "n_fixtures": len(scenarios.ALL_NAMES)}
        print(f"{m:44s} " + "  ".join(row) + f"   rejected {rej}/{len(scenarios.ALL_NAMES)}")
    Path(os.path.dirname(os.path.abspath(__file__)), "panel_results.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
