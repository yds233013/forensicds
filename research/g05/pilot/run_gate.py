#!/usr/bin/env python3
"""G05 v2 Phase-0 gate: accepted estimators must pass, every natural wrong analysis must fail, across regimes and seeds.

usage: run_gate.py PHASE N_SEEDS OUT.json [REGIME]      PHASE = cal | val
       run_gate.py summarize CAL1.json,CAL2.json,... VAL1.json,... OUT_TOL.json
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import g05_estimators as E
import g05_sim as S

BASE_SEED = {"cal": 5000, "val": 9000}
REGIME_BLOCK = 100000            # round 6: disjoint seed block per regime (regimes do not share noise)
QUANTS = ["wave.W1", "wave.W2", "wave.W3", "wave.W4", "kit.full", "kit.compact", "gate", "pooled"]
GRADED = {"A_wave_gate": ["wave.W1", "wave.W2", "wave.W3", "wave.W4", "gate"],
          "B_wave_kit_gate": ["wave.W1", "wave.W2", "wave.W3", "wave.W4", "kit.full", "kit.compact", "gate"]}


def flat(r):
    return {**{f"wave.{k}": v for k, v in r["wave"].items()}, **{f"kit.{k}": v for k, v in r["kit"].items()},
            "gate": float(r["gate"]), "pooled": float(r["pooled"])}


def run(phase, n_seeds, out_path, only=None):
    res = []
    methods = {**{k: ("accepted", f) for k, f in E.ACCEPTED.items()}, **{k: ("wrong", f) for k, f in E.WRONG.items()},
               **{k: ("wrong", f) for k, f in E.UNDECIDED.items()},
               **{k: ("wrong", f) for k, f in E.VARIANTS_OF_WRONG.items()}}
    for ri, rname in enumerate(S.REGIMES):
        if only and rname != only:
            continue
        spec = S.regime(rname)
        for i in range(n_seeds):
            seed = BASE_SEED[phase] + REGIME_BLOCK * (ri + 1) + 17 * i
            t0 = time.time()
            w = S.draw_world(spec, seed)
            tr = S.truth(w)
            rec = {"regime": rname, "seed": seed, "truth": flat(tr), "decision": tr["decision"], "hurdle": spec["gate"],
                   "methods": {}}
            for name, (kind, fn) in methods.items():
                r = fn(w)
                rec["methods"][name] = {"kind": kind, "est": flat(r)}
            res.append(rec)
            print(f"{phase} {rname} {seed} {time.time() - t0:.1f}s gate={tr['gate']:.4f} {tr['decision']}", flush=True)
    json.dump(res, open(out_path, "w"))


def tolerances(cal):
    """Pre-registered: tau_q = 3.5 x sd (across calibration worlds) of the error of the least efficient accepted
    estimator for quantity q, per regime."""
    errs = defaultdict(list)
    for rec in cal:
        for m, d in rec["methods"].items():
            if d["kind"] != "accepted":
                continue
            for q in QUANTS:
                errs[(rec["regime"], m, q)].append(d["est"][q] - rec["truth"][q])
    tau, sd = {}, {}
    for reg in S.REGIMES:
        for q in QUANTS:
            sds = {m: float(np.sqrt(np.mean(np.square(errs[(reg, m, q)])))) for m in E.ACCEPTED}
            worst = max(sds, key=sds.get)
            sd[f"{reg}|{q}"] = {"rmse_by_method": sds, "least_efficient": worst}
            tau[f"{reg}|{q}"] = 3.5 * sds[worst]
    return tau, sd


def _load(paths):
    out = []
    for p in paths.split(","):
        out += json.load(open(p))
    return out


def summarize(cal_path, val_path, out_tol):
    cal, val = _load(cal_path), _load(val_path)
    tau, sd = tolerances(cal)
    json.dump({"tau": tau, "rmse": sd}, open(out_tol, "w"), indent=1)
    names = list(val[0]["methods"])
    for gname, graded in GRADED.items():
        print(f"\n=== graded set {gname}: {graded} + decision")
        print(f"{'method':24s} {'kind':9s} " + " ".join(f"{r[:14]:>16s}" for r in S.REGIMES) + "   total")
        for m in names:
            row, tot, kind = [], 0, val[0]["methods"][m]["kind"]
            for reg in S.REGIMES:
                recs = [r for r in val if r["regime"] == reg]
                npass, worst = 0, 0.0
                for r in recs:
                    est = r["methods"][m]["est"]
                    ratios = [abs(est[q] - r["truth"][q]) / tau[f"{reg}|{q}"] for q in graded]
                    dec = "continue" if est["gate"] >= r["hurdle"] else "stop"
                    ok = max(ratios) <= 1 and dec == r["decision"]
                    npass += ok
                    worst = max(worst, max(ratios))
                tot += npass
                row.append(f"{npass:2d}/{len(recs)} w{worst:5.1f}")
            print(f"{m:24s} {kind:9s} " + " ".join(f"{c:>16s}" for c in row) + f"   {tot}/{len(val)}")
    print("\n=== tolerances (visible) and margins")
    for reg in S.REGIMES:
        recs = [r for r in val if r["regime"] == reg]
        gsd = sd[f"{reg}|gate"]["rmse_by_method"][sd[f"{reg}|gate"]["least_efficient"]]
        margins = [(r["truth"]["gate"] - r["hurdle"]) / gsd for r in recs]
        print(reg, {q: round(tau[f"{reg}|{q}"], 4) for q in QUANTS},
              f"gate margin/sd min {min(margins, key=abs):+.1f} range [{min(margins):+.1f},{max(margins):+.1f}]",
              "least efficient:", {q: sd[f"{reg}|{q}"]["least_efficient"] for q in ("wave.W1", "gate")})


if __name__ == "__main__":
    if sys.argv[1] == "summarize":
        summarize(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        run(sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
