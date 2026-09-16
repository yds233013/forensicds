"""Generator truth for the G24 verifier (standard library).

Everything here comes from the generator's own state, never from an estimator:
  - the decision table (one row per decision x slot, with the click outcome);
  - the counterfactual slate each policy would have served for every decision whose candidates were logged;
  - exact policy values (expectations over all decisions in the extract) and lifts;
  - SE_ref: the standard error of the least efficient accepted estimator (slot-exact item-in-slot IPS), computed
    analytically from the generator's own quantities, so tolerances carry no simulation noise.
"""
from __future__ import annotations

import math

POLICIES = ("v6", "v7", "v7_pd")
SLOTS = 5


def expected(w) -> dict:
    items = w.items
    rows = {}
    slates = {}
    meta = {}
    for d in w.decisions:
        did = d["serve_id"]          # the documented decision id: the serve that created the decision
        for k in range(len(d["served"])):
            rows[(did, k + 1)] = {
                "stream": d["stream"], "device": d["device"],
                "decided_at": d["decided_at"].strftime("%Y-%m-%d %H:%M:%S"),
                "item_id": items[d["pool"][d["served"][k]]]["item_id"], "clicked": d["clicks"][k],
                "serve_id": d["serve_id"], "session_id": d["session_id"],
            }
        meta[did] = {"stream": d["stream"], "serve_id": d["serve_id"], "m": d["m"],
                                  "logged_candidates": d["logged_candidates"]}
        if d["logged_candidates"]:
            for p in POLICIES:
                for k, j in enumerate(d["target"][p]):
                    slates[(did, p, k + 1)] = items[d["pool"][j]]["item_id"]

    n = len(w.decisions)
    values = {p: sum(d["value"][p] for d in w.decisions) / n for p in POLICIES}
    lifts = {p: values[p] - values["v6"] for p in ("v7", "v7_pd")}

    # analytic SE of slot-exact item-in-slot IPS on the exploration decisions
    expl = [d for d in w.decisions if d["stream"] == "explore_shuffle"]
    ne = len(expl)
    se, se_lift = {}, {}
    for p in POLICIES:
        ex = ex2 = 0.0
        for d in expl:
            th = w.theta[d["device"]]
            v = [th[k] * d["r"][j] for k, j in enumerate(d["target"][p])]
            ex += sum(v)
            m = d["m"]
            ex2 += m * sum(v) + m / (m - 1) * (sum(v) ** 2 - sum(x * x for x in v))
        mu = ex / ne
        se[p] = math.sqrt(max(ex2 / ne - mu * mu, 0.0) / ne)
    for p in ("v7", "v7_pd"):
        ex = ex2 = 0.0
        for d in expl:
            th = w.theta[d["device"]]
            vt = {q: [th[k] * d["r"][j] for k, j in enumerate(d["target"][q])] for q in (p, "v6")}
            agree = sum(th[k] * d["r"][j] for k, (j, j6) in enumerate(zip(d["target"][p], d["target"]["v6"]))
                        if j == j6)
            diff = sum(vt[p]) - sum(vt["v6"])
            ex += diff
            ex2 += d["m"] * (sum(vt[p]) + sum(vt["v6"]) - 2 * agree) + diff ** 2
        mu = ex / ne
        se_lift[p] = math.sqrt(max(ex2 / ne - mu * mu, 0.0) / ne)

    ok = [p for p in ("v7", "v7_pd") if lifts[p] > 0]
    launch = max(ok, key=lambda p: values[p]) if ok else "v6"
    return {"rows": rows, "slates": slates, "meta": meta, "values": values, "lifts": lifts,
            "se": se, "se_lift": se_lift, "launch": launch, "n_decisions": n, "n_exploration": ne}
