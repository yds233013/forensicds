"""G31 Phase-0 gate runner (research only; no model, no task files).

Pre-registered before the first run, applying the improved criterion recommended in
research/g05/G05_O1_adjudication.md (analytic invalidity + joint pass probability +
deterministic failure on the graded fixture) rather than an unmeasurable per-regime rate.
"""
from __future__ import annotations
import json, sys, time
import numpy as np
import g31_sim as S
import g31_estimators as E

QUANT = [f"recall_{m}.{g}" for g in S.SEGMENTS for m in ("v6", "v7")] + [f"delta.{g}" for g in S.SEGMENTS]
REGIME_BLOCK = {"visible": 100000, "high_prev": 200000, "slow_cb_big_holdout": 300000, "tight_capacity": 400000,
                "v7_wins_everywhere": 500000}


def run(regime, n, offset, tag):
    spec = S.regime(regime)
    out = []
    for i in range(n):
        seed = REGIME_BLOCK[regime] + offset + 17 * i
        w = S.draw_world(spec, seed)
        ob = S.observed(w)
        tr = S.truth(w)
        row = {"regime": regime, "seed": seed, "truth": {k: tr[k] for k in QUANT},
               "truth_decision": tr["decision"], "methods": {}}
        for nm, fn in list(E.ACCEPTED.items()) + list(E.WRONG.items()):
            try:
                r = fn(ob)
                row["methods"][nm] = {"q": {k: r[k] for k in QUANT}, "decision": r["decision"],
                                      "kind": "accepted" if nm in E.ACCEPTED else "wrong"}
            except Exception as exc:                      # a crashing method still counts as failing
                row["methods"][nm] = {"q": {k: float("nan") for k in QUANT}, "decision": "ERROR",
                                      "kind": "accepted" if nm in E.ACCEPTED else "wrong", "error": str(exc)}
        out.append(row)
        print(f"  {tag} {regime} {i+1}/{n} seed={seed}", flush=True)
    return out


if __name__ == "__main__":
    which = sys.argv[1]
    n_cal, n_val = int(sys.argv[2]), int(sys.argv[3])
    t0 = time.time()
    res = {"calibration": run(which, n_cal, 0, "cal"), "validation": run(which, n_val, 90001, "val")}
    json.dump(res, open(f"results/gate_{which}.json", "w"))
    print(f"{which} done in {time.time()-t0:.0f}s")
