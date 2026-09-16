#!/usr/bin/env python3
"""G24 Phase-0 gate: correct estimators must pass, every natural wrong method must fail, across regimes and seeds.

usage: run_gate.py PHASE N_SEEDS OUT.json      PHASE = cal | val
       run_gate.py summarize CAL.json VAL.json
"""
from __future__ import annotations

import json, sys, time
from collections import defaultdict

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import g24_sim as S
import pilot_estimators as E

BASE_SEED = {"cal": 3000, "val": 8000}


def run(phase: str, n_seeds: int, out_path: str):
    res = []
    for rname in S.REGIMES:
        spec = S.regime(rname)
        for i in range(n_seeds):
            seed = BASE_SEED[phase] + 17 * i
            t0 = time.time()
            w = S.draw_world(spec, seed)
            truth = S.truth(w)
            rec = {"regime": rname, "seed": seed, "truth": truth, "true_decision": S.true_decision(w), "methods": {}}
            for kind, panel in (("correct", E.PANEL_CORRECT), ("wrong", E.PANEL_WRONG)):
                for name, fn in panel.items():
                    r = fn(w)
                    rec["methods"][name] = {
                        "kind": kind,
                        "value": {p: r["value"][p] for p in E.POLICIES},
                        "lift": {p: r["lift"][p] for p in ("v7", "v7_pd")},
                        "lift_se": {p: r["lift_se"][p] for p in ("v7", "v7_pd")},
                        "se": {p: r["se"][p] for p in E.POLICIES},
                        "decision": E.decision_from(r),
                    }
            res.append(rec)
            print(f"{rname} {seed} {time.time() - t0:.1f}s truth={ {k: round(v, 4) for k, v in truth.items()} }", flush=True)
            json.dump(res, open(out_path, "w"))


def tolerances(cal):
    """Pre-registered rule: tau = 3.5 x SE of the least efficient accepted estimator (slot-exact IPS), per regime.

    3.5 rather than 3.0 because a reward requires 20 graded quantities (5 per extract x 4 extracts) to be inside at
    once: at 3 sigma an unbiased oracle fails ~5% of the time, at 3.5 sigma ~1%.
    """
    se_v, se_l = defaultdict(list), defaultdict(list)
    for rec in cal:
        m = rec["methods"]["slot_ips"]
        for p in E.POLICIES:
            se_v[(rec["regime"], p)].append(m["se"][p])
        for p in ("v7", "v7_pd"):
            se_l[(rec["regime"], p)].append(m["lift_se"][p])
    tau = {"value": {f"{r}|{p}": round(3.5 * float(np.mean(v)), 5) for (r, p), v in se_v.items()},
           "lift": {f"{r}|{p}": round(3.5 * float(np.mean(v)), 5) for (r, p), v in se_l.items()}}
    return tau


def grade(rec, tau):
    """Per world: which methods stay inside tolerance on every value and lift, and get the decision right."""
    out = {}
    for name, m in rec["methods"].items():
        ok_v = max(abs(m["value"][p] - rec["truth"][p]) / tau["value"][f"{rec['regime']}|{p}"] for p in E.POLICIES)
        ok_l = max(abs(m["lift"][p] - (rec["truth"][p] - rec["truth"]["v6"])) / tau["lift"][f"{rec['regime']}|{p}"]
                   for p in ("v7", "v7_pd"))
        out[name] = {"kind": m["kind"], "worst_ratio": max(ok_v, ok_l),
                     "decision_ok": m["decision"] == rec["true_decision"],
                     "pass": max(ok_v, ok_l) <= 1.0 and m["decision"] == rec["true_decision"]}
    return out


def summarize(cal_path, val_path):
    cal, val = json.load(open(cal_path)), json.load(open(val_path))
    tau = tolerances(cal)
    print(json.dumps(tau, indent=1))
    per = defaultdict(lambda: defaultdict(list))
    for rec in val:
        for name, g in grade(rec, tau).items():
            per[name][rec["regime"]].append(g)
    print(f"\n{'method':26} {'kind':8} {'worlds pass':>11}  per-regime pass (visible/tv_heavy/no_launch/v7_wins), worst ratio")
    for name, byreg in per.items():
        allg = [g for gs in byreg.values() for g in gs]
        npass = sum(g["pass"] for g in allg)
        detail = " ".join(f"{r[:3]}:{sum(g['pass'] for g in gs)}/{len(gs)}({max(g['worst_ratio'] for g in gs):.1f})"
                          for r, gs in byreg.items())
        dec = sum(g["decision_ok"] for g in allg)
        print(f"{name:26} {allg[0]['kind']:8} {npass:>4}/{len(allg):<5} dec {dec}/{len(allg)}  {detail}")
    json.dump(tau, open(val_path.replace(".json", "_tolerances.json"), "w"), indent=1)


if __name__ == "__main__":
    if sys.argv[1] == "summarize":
        summarize(sys.argv[2], sys.argv[3])
    else:
        run(sys.argv[1], int(sys.argv[2]), sys.argv[3])
