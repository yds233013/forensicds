"""Compute every reported metric from the raw job artefacts. Single source of truth for the report."""
import json, glob, os, collections, statistics as st

FINAL10 = ["02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand",
 "g24-recommender-ope","g36-tou-capacity-gate","p20-noshow-monitoring",
 "p22-gauge-recalibration","p31-fill-rate-dispute","g08-forecast-accuracy-vintages",
 "g50-courier-boost-rollout"]
ABLATION = "02-renewal-risk-regression__explicit-invariant"
V11 = "p20-noshow-monitoring-v1.1"

rows = json.load(open("report/analysis/trajectories.json"))
valid = [r for r in rows if not r["invalid"]]
inval = [r for r in rows if r["invalid"]]

def isp(r): return r["reward"] not in ("0", "0.0")

by = collections.defaultdict(list)
for r in valid: by[r["task"]].append(r)

out = {"per_task": {}, "suite": {}, "invalid_trials": []}
for jn in sorted({r["job"] for r in inval}):
    out["invalid_trials"].append(jn)

print("=== PER-TASK METRICS (final ten) ===")
print(f"{'task':34s} {'valid':>5s} {'pass':>4s} {'pass@1':>7s} {'pass@3':>7s} {'steps':>6s} {'tools':>6s} {'tok':>9s}")
tv = tp = 0; p3 = []
for t in FINAL10:
    v = by.get(t, [])
    p = sum(1 for r in v if isp(r))
    if not v:
        print(f"{t:34s} {'--- no trials yet ---'}"); out["per_task"][t] = None; continue
    med = lambda k: st.median([r.get(k) or 0 for r in v])
    pass3 = 1 if p > 0 else 0
    p3.append(pass3); tv += len(v); tp += p
    out["per_task"][t] = dict(valid=len(v), passes=p, pass1=p/len(v), pass3=pass3,
                              median_steps=med("steps"), median_tool_calls=med("n_tool_calls"),
                              median_completion_tokens=med("completion_tokens"),
                              median_prompt_tokens=med("prompt_tokens"))
    print(f"{t:34s} {len(v):5d} {p:4d} {p/len(v):7.1%} {pass3:7d} {med('steps'):6.0f} "
          f"{med('n_tool_calls'):6.0f} {med('completion_tokens'):9.0f}")

print(f"\n=== SUITE ===")
out["suite"] = dict(
    tasks=len(FINAL10), tasks_with_trials=len(p3),
    total_valid_trials=tv, total_passes=tp,
    aggregate_pass1=(tp/tv if tv else None),
    task_level_pass3=(sum(p3)/len(p3) if p3 else None),
    invalid_trial_jobs=len(out["invalid_trials"]),
)
for k, v in out["suite"].items(): print(f"  {k}: {v}")

print(f"\n=== WHOLE POOL (all 21 exposed tasks, for context) ===")
allp = sum(1 for r in valid if isp(r))
print(f"  valid trials {len(valid)}  passes {allp}  aggregate pass@1 {allp/len(valid):.1%}")
print(f"  invalid (infrastructure) trial directories excluded: {len(inval)}")

print(f"\n=== ABLATION / VERSION ===")
for t in (ABLATION, V11):
    v = by.get(t, [])
    if v:
        p = sum(1 for r in v if isp(r))
        print(f"  {t}: {len(v)} valid, {p} pass, pass@3={1 if p else 0}")
        out["per_task"][t] = dict(valid=len(v), passes=p, pass3=1 if p else 0)
    else:
        print(f"  {t}: no trials recorded yet")

print(f"\n=== CRITERION-LEVEL (tasks that emit it) ===")
crit_tot = collections.Counter(); crit_pass = collections.Counter()
for r in valid:
    c = r.get("criteria") or {}
    for k, val in c.items():
        crit_tot[k] += 1
        if val: crit_pass[k] += 1
for k in sorted(crit_tot, key=lambda x: crit_pass[x]/crit_tot[x]):
    print(f"  {k:26s} {crit_pass[k]}/{crit_tot[k]} pass  ({crit_pass[k]/crit_tot[k]:.0%})")
out["criteria"] = {k: dict(passed=crit_pass[k], total=crit_tot[k]) for k in crit_tot}

json.dump(out, open("report/analysis/metrics.json", "w"), indent=1)
print("\nwrote report/analysis/metrics.json")
