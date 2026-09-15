"""Multi-seed, multi-regime tolerance pilot. usage: run_pilot.py [n_seeds] [procs]"""
import copy, json, sys, time
from multiprocessing import Pool
import numpy as np
import g10_world as G
import pilot_estimators as P

def regimes():
    v = copy.deepcopy(G.VISIBLE_SPEC)
    a = copy.deepcopy(v); a.update(name="hidden_a", alpha_scale=0.6, m_lean=1.05, afternoon_slot_stores=9,
        profiles={**v["profiles"], "weekday": [4, 5, 6, 7, 7, 7, 7, 7, 7, 7, 8, 8, 7, 6]})
    b = copy.deepcopy(v); b.update(name="hidden_b", m_pre=1.8, m_lean=1.45, m_holdout=1.8, holdout_stores=8,
        promo_share_post=0.12, competitor=None,
        categories={**v["categories"], "Breakfast cereals": (5.0, -0.26, 1.8), "Soft drinks": (3.0, +0.30, 2.2),
                    "Soups & broths": (3.0, 0.0, 2.0)})
    c = copy.deepcopy(v); c.update(name="hidden_c", alpha_scale=1.3, promo_share_pre=0.20, promo_share_post=0.15,
        v4_promo_under=0.7, profiles={**v["profiles"], "weekday": [1, 2, 3, 3, 4, 4, 4, 4, 5, 7, 12, 16, 15, 10]})
    return [v, a, b, c]

def job(args):
    spec, seed = args
    spec = copy.deepcopy(spec); spec["seed"] = seed
    t = time.time()
    w = G.generate(spec); X = P.arrays(w)
    ests, info = P.run_all(X)
    T = P.truth(X)
    rows = []
    cens_share = float(info["cens"].mean())
    lost_share = float(1 - X["F"]["sales"].sum() / X["F"]["demand"].sum())
    for m, e in ests.items():
        g = P.graded(X, e)
        for k, tv in T.items():
            v = g[k]
            err = v - tv if (k.startswith("cat") or k.startswith("bias")) else 100 * (v / tv - 1) if tv else 0.0
            rows.append((spec["name"], seed, m, k, float(tv), float(v), float(err)))
    return rows, (spec["name"], seed, cens_share, lost_share, round(time.time() - t))

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    base = int(sys.argv[3]) if len(sys.argv) > 3 else 7000
    jobs = [(r, base + 13 * i) for r in regimes() for i in range(n)]
    out, meta = [], []
    with Pool(procs) as pool:
        for rows, m in pool.imap_unordered(job, jobs):
            out += rows; meta.append(m); print("done", m, flush=True)
    json.dump({"rows": out, "meta": meta}, open(f"pilot_results_{n}seeds_base{base}.json", "w"))
