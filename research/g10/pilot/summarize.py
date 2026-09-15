"""Summarise pilot: tolerances from correct estimators, separation of wrong estimators. usage: summarize.py results.json"""
import json, sys
from collections import defaultdict
import numpy as np

R = json.load(open(sys.argv[1]))
rows = R["rows"]
CORRECT = {"C1_nb_offset_posterior", "C2_nb_common_alpha", "C3_em_gamma_poisson", "C4_nb_4week_season"}
def group(k):
    if k.startswith("cat_change"): return "cat_change (pp)"
    if k.startswith("bias"): return "bias (pp)"
    if k.startswith("total"): return "total (%) " + k.split("::")[1]
    return "lost (%) " + k.split("::")[1]
err = defaultdict(list)          # (method, metric) -> list of (regime, seed, err)
for reg, seed, m, k, tv, v, e in rows:
    err[(m, k)].append((reg, seed, e, tv))
metrics = sorted({k for _, _, _, k, *_ in rows})
methods = sorted({m for _, _, m, *_ in rows})
print("== correct-estimator spread (max |error| over methods x seeds x regimes) ==")
spread = {}
for k in metrics:
    vals = [abs(e) for m in CORRECT for _, _, e, _ in err[(m, k)]]
    spread[k] = max(vals)
g_spread = defaultdict(float)
for k, s in spread.items():
    g_spread[group(k)] = max(g_spread[group(k)], s)
for g, s in sorted(g_spread.items()):
    print(f"  {g:40} max|err|={s:.2f}")
# proposed tolerances: 1.5 x correct spread, floor
def tol_for(k):
    s = spread[k]
    if k.startswith("cat_change"): return max(1.5 * s, 2.0)
    if k.startswith("bias"): return max(1.5 * s, 0.5)
    if k.startswith("total"): return max(1.5 * s, 1.5)
    return max(1.5 * s, 6.0)
print("\n== per wrong method: worlds caught (any graded metric beyond 1.5x its tolerance) and closest metrics ==")
worlds = sorted({(reg, seed) for reg, seed, *_ in rows})
for m in methods:
    if m in CORRECT: continue
    caught = 0; weakest = []
    for (reg, seed) in worlds:
        ratios = []
        for k in metrics:
            e = [x for x in err[(m, k)] if x[0] == reg and x[1] == seed][0][2]
            ratios.append((abs(e) / tol_for(k), k, e))
        best = max(ratios)
        if best[0] >= 1.5: caught += 1
        weakest.append((best[0], reg, seed, best[1], best[2]))
    worst = min(weakest)
    print(f"  {m:32} caught {caught}/{len(worlds)}  weakest world: {worst[1]} s{worst[2]} max ratio {worst[0]:.2f} on {worst[3]} (err {worst[4]:+.2f})")
print("\n== correct estimators pass (all metrics within tolerance) ==")
for m in sorted(CORRECT):
    fails = 0
    for (reg, seed) in worlds:
        ok = all(abs([x for x in err[(m, k)] if x[0] == reg and x[1] == seed][0][2]) <= tol_for(k) for k in metrics)
        fails += not ok
    print(f"  {m:32} pass {len(worlds)-fails}/{len(worlds)}")
print("\n== intermediate plausible success: category changes within tolerance but caught elsewhere ==")
for m in methods:
    if m in CORRECT: continue
    ok_cat = sum(all(abs([x for x in err[(m, k)] if x[0]==reg and x[1]==seed][0][2]) <= tol_for(k) for k in metrics if k.startswith("cat")) for reg, seed in worlds)
    ok_tot = sum(all(abs([x for x in err[(m, k)] if x[0]==reg and x[1]==seed][0][2]) <= tol_for(k) for k in metrics if k.startswith("total")) for reg, seed in worlds)
    print(f"  {m:32} category trends within tol in {ok_cat}/{len(worlds)} worlds; totals within tol in {ok_tot}/{len(worlds)}")
print("\n== regime meta (regime, seed, censored-day share, lost share, seconds) ==")
for mm in sorted(R["meta"]): print("  ", mm)
print("\n== truth category changes by regime (seed-mean) ==")
tc = defaultdict(list)
for reg, seed, m, k, tv, v, e in rows:
    if m == "C1_nb_offset_posterior" and k.startswith("cat"): tc[(reg, k)].append(tv)
for (reg, k), v in sorted(tc.items()): print(f"  {reg:9} {k[12:]:30} {np.mean(v):+6.1f} (min {min(v):+.1f}, max {max(v):+.1f})")
json.dump({k: tol_for(k) for k in metrics}, open("proposed_tolerances.json", "w"), indent=1)
