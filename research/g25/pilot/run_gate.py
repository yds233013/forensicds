#!/usr/bin/env python3
"""G25 Phase-0 gate: accepted estimators of the complete-judgment metric must pass; wrong handling of unjudged slots
must fail, with the frame-restriction trap at >= 2.5 tau (tournament-required fix).

usage: run_gate.py N_SEEDS OUT.json
"""
from __future__ import annotations

import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import g25_estimators as E
import g25_sim as S

QUANTS = ["A", "B", "delta"]
FLOOR = 0.008


def run(n_seeds):
    rows = []
    for rn in S.REGIMES:
        spec = S.regime(rn)
        for i in range(n_seeds):
            w = S.draw_world(spec, 4000 + 13 * i)
            t = S.truth(w)
            rec = {"regime": rn, "seed": 4000 + 13 * i, "truth": t, "methods": {}}
            for kind, panel in (("accepted", E.ACCEPTED), ("wrong", E.WRONG)):
                for m, f in panel.items():
                    r = f(w)
                    rec["methods"][m] = {"kind": kind, **{q: r[q] for q in QUANTS}, "decision": r["decision"]}
            rows.append(rec)
    return rows


def summarize(rows, n_cal):
    regimes = list(S.REGIMES)
    tau = {}
    print("=== accepted panel: error vs complete-judgment truth (calibration seeds)")
    for reg in regimes:
        cal = [r for r in rows if r["regime"] == reg][:n_cal]
        worst = {}
        for q in QUANTS:
            errs = {m: np.array([r["methods"][m][q] - r["truth"][q] for r in cal]) for m in E.ACCEPTED}
            worst[q] = max(float(np.sqrt((e ** 2).mean())) for e in errs.values())
            tau[f"{reg}|{q}"] = max(FLOOR, 3.5 * worst[q])
        print(f"  {reg:12s} worst accepted RMSE " + " ".join(f"{q}={worst[q]:.4f}" for q in QUANTS)
              + "  tau " + " ".join(f"{q}={tau[f'{reg}|{q}']:.4f}" for q in QUANTS))
    print("\n=== validation: pass rate (all quantities inside tau and decision correct)")
    val = {reg: [r for r in rows if r["regime"] == reg][n_cal:] for reg in regimes}
    names = list(rows[0]["methods"])
    print(f"{'method':24s} {'kind':9s} " + " ".join(f"{r[:11]:>13s}" for r in regimes) + "   min|err|/tau")
    for m in names:
        cells, kind, ratios = [], rows[0]["methods"][m]["kind"], []
        for reg in regimes:
            npass = 0
            for r in val[reg]:
                rr = max(abs(r["methods"][m][q] - r["truth"][q]) / tau[f"{reg}|{q}"] for q in QUANTS)
                ratios.append(rr)
                npass += rr <= 1 and r["methods"][m]["decision"] == r["truth"]["decision"]
            cells.append(f"{npass:2d}/{len(val[reg])}")
        print(f"{m:24s} {kind:9s} " + " ".join(f"{c:>13s}" for c in cells) + f"   {min(ratios):.2f}")
    print("\n=== decision margins (|truth delta - threshold| in units of accepted-panel sd of delta)")
    for reg in regimes:
        v = val[reg]
        sd = float(np.std([r["methods"]["global_mean"]["delta"] - r["truth"]["delta"] for r in v], ddof=1))
        marg = [abs(r["truth"]["delta"] - S.BASE["threshold"]) for r in v]
        print(f"  {reg:12s} truth delta {np.mean([r['truth']['delta'] for r in v]):+.4f}"
              f"  decision {v[0]['truth']['decision']:5s}  sd(delta err) {sd:.4f}  margin/sd {np.mean(marg) / sd:5.1f}")
    return tau


if __name__ == "__main__":
    n = int(sys.argv[1])
    rows = run(n)
    json.dump(rows, open(sys.argv[2], "w"))
    summarize(rows, n_cal=n // 2)
