"""Apply tolerances fixed on calibration seeds to validation seeds. usage: validate.py cal.json val.json"""
import json, sys
from collections import defaultdict

CORRECT = {"C1_nb_offset_posterior", "C2_nb_common_alpha", "C3_em_gamma_poisson", "C4_nb_4week_season"}
cal = json.load(open(sys.argv[1]))["rows"]
val = json.load(open(sys.argv[2]))["rows"]

def is_pp(k): return k.startswith("cat") or k.startswith("bias")
spread = defaultdict(float)
for reg, seed, m, k, tv, v, e in cal:
    if m in CORRECT: spread[k] = max(spread[k], abs(e))
def tol(k):
    s = spread[k]
    if k.startswith("cat_change"): return round(max(1.5 * s, 1.5), 2)
    if k.startswith("bias"): return round(max(1.5 * s, 0.5), 2)
    if k.startswith("total"): return round(max(1.5 * s, 1.5), 2)
    return round(max(1.5 * s, 6.0), 2)
TOL = {k: tol(k) for k in spread}
def action(x): return "reduce" if x <= -5 else "increase" if x >= 5 else "maintain"

by = defaultdict(dict)   # (reg, seed, m) -> {k: (tv, v, e)}
for reg, seed, m, k, tv, v, e in val:
    by[(reg, seed, m)][k] = (tv, v, e)
methods = sorted({m for (_, _, m) in by})
worlds = sorted({(r, s) for (r, s, _) in by})
seeds = sorted({s for (_, s) in worlds})
print("tolerances (fixed on calibration seeds):")
for k in sorted(TOL): print(f"  {k:48} {TOL[k]}")
print("\nvalidation seeds:", seeds)
for m in methods:
    passed_worlds = 0; action_ok = 0; action_n = 0; worst_ratio = (0, None)
    seed_reward = {}
    for (reg, seed) in worlds:
        d = by[(reg, seed, m)]
        ratios = [(abs(e) / TOL[k], k) for k, (tv, v, e) in d.items()]
        acts = [(action(v), action(tv)) for k, (tv, v, e) in d.items() if k.startswith("cat") and min(abs(tv - 5), abs(tv + 5)) >= 2.0]
        acts_ok = all(a == b for a, b in acts)
        action_ok += sum(a == b for a, b in acts); action_n += len(acts)
        ok = max(ratios)[0] <= 1.0 and acts_ok
        passed_worlds += ok
        seed_reward[seed] = seed_reward.get(seed, True) and ok
        if max(ratios)[0] > worst_ratio[0]: worst_ratio = (max(ratios)[0], max(ratios)[1], reg, seed)
        if m not in CORRECT:
            r = max(ratios)
    rewards = sum(seed_reward.values())
    per_reg = {}
    for reg, seed in worlds:
        r = max(abs(e) / TOL[k] for k, (tv, v, e) in by[(reg, seed, m)].items())
        per_reg[reg] = min(per_reg.get(reg, 1e9), r)
    min_catch = min(max(abs(e) / TOL[k] for k, (tv, v, e) in by[(reg, seed, m)].items()) for reg, seed in worlds)
    tag = "CORRECT" if m in CORRECT else "wrong  "
    print(f"{tag} {m:32} worlds passed {passed_worlds}/{len(worlds)}  reward(all 4 regimes) {rewards}/{len(seeds)}  "
          f"action accuracy {action_ok}/{action_n}  " + (f"max ratio {worst_ratio[0]:.2f} ({worst_ratio[1]}, {worst_ratio[2]})" if m in CORRECT else f"weakest-world max ratio {min_catch:.2f}; per regime min {dict((k, round(v, 2)) for k, v in sorted(per_reg.items()))}"))
json.dump(TOL, open("tolerances_from_calibration.json", "w"), indent=1)
