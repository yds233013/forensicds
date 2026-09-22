#!/usr/bin/env python3
"""Build report/data/results.json from raw Harbor job outputs (read-only; never runs a model).

Pilot pool = every measured task; final set = scripts/final_tasks.json. Trial validity: a trial counts if it is a
gemini-cli run on the frozen task, its job name does not contain 'INVALID', it raised no exception, and it is not in
final_tasks.json:invalid_trials.
"""
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(ROOT, "scripts", "final_tasks.json")))
invalid = cfg.get("invalid_trials", {})
PILOT = {  # id -> (path, display name, generation)
    "task01": ("candidates/01-revenue-reconciliation", "Revenue reconciliation", "gen1"),
    "task02": ("candidates/02-renewal-risk-regression", "Renewal-risk point-in-time features", "gen1"),
    "task03": ("candidates/03-lead-score-evaluation", "Lead-score evaluation", "gen1"),
    "task04": ("candidates/04-retention-metrics-regression", "Retention metrics", "gen1"),
    "task05": ("candidates/05-onboarding-experiment-readout", "Onboarding experiment readout", "gen1"),
    "task06": ("candidates/06-usage-statement-close", "Usage statement close", "gen2"),
    "g05": ("candidates/g05-sco-rollout-gate", "Staggered rollout causal gate", "gen3"),
    "g08": ("candidates/g08-forecast-accuracy-vintages", "Forecast accuracy vintages", "gen3"),
    "g10": ("candidates/g10-censored-demand", "Censored (lost) demand", "gen3"),
    "g24": ("candidates/g24-recommender-ope", "Recommender off-policy evaluation", "gen3"),
    "g34": ("candidates/g34-fleet-reliability-gate", "Competing-risks fleet reliability", "gen3"),
    "g35": ("candidates/g35-dispatch-priority-gate", "Marketplace interference", "gen3"),
}
EXCLUDED = {"g36": "contaminated by verifier definition defect (F8); development-only",
            "g37": "research-only DROP (no tolerance window)", "g38": "research-only DROP (no tolerance window)"}

rows = []
for p in glob.glob(os.path.join(ROOT, "jobs", "*", "*", "result.json")):
    r = json.load(open(p)); job = p.split(os.sep)[-3]
    lk = os.path.join(os.path.dirname(p), "lock.json")
    dg = ((json.load(open(lk)).get("task") or {}).get("digest") if os.path.exists(lk) else None) or ""
    rows.append(dict(path=(r.get("config", {}).get("task", {}) or {}).get("path"), job=job, trial=r.get("trial_name"),
                     agent=(r.get("agent_info") or {}).get("name"),
                     model=((r.get("agent_info") or {}).get("model_info") or {}).get("name"),
                     reward=((r.get("verifier_result") or {}).get("rewards") or {}).get("reward"),
                     cost=(r.get("agent_result") or {}).get("cost_usd") or 0.0, exc=r.get("exception_info"),
                     checksum=(dg[7:23] if dg.startswith("sha256:") else (r.get("task_checksum") or "")[:16])))

out = {"pilot": {}, "final": [t["id"] for t in cfg["tasks"]], "excluded": EXCLUDED, "costs": {}}
tot_model = 0.0
for tid, (path, name, gen) in PILOT.items():
    g = [x for x in rows if x["path"] == path and x["agent"] == "gemini-cli"]
    tot_model += sum(x["cost"] for x in g)
    valid = [x for x in g if "INVALID" not in x["job"] and x["exc"] is None and x["trial"] not in invalid]
    ft = next((t for t in cfg["tasks"] if t["id"] == tid), None)
    if ft:
        valid = [x for x in valid if x["trial"] in ft["valid_trials"]]
    valid = sorted(valid, key=lambda x: x["trial"])
    succ = sum(1 for x in valid if x["reward"] == 1.0)
    out["pilot"][tid] = dict(path=path, name=name, generation=gen, trials=[dict(trial=x["trial"], job=x["job"], reward=x["reward"],
                             cost_usd=round(x["cost"], 6), checksum=x["checksum"]) for x in valid],
                             n_valid=len(valid), successes=succ, pass_at_3=int(succ > 0),
                             invalid_runs=len(g) - len(valid), model_cost_usd=round(sum(x["cost"] for x in g), 4))
fin = [out["pilot"][t] for t in out["final"]]
out["final_summary"] = dict(tasks=len(fin), trials=sum(t["n_valid"] for t in fin), successful_trials=sum(t["successes"] for t in fin),
                            tasks_with_pass3=sum(t["pass_at_3"] for t in fin))
out["final_summary"]["trial_success_rate"] = out["final_summary"]["successful_trials"] / out["final_summary"]["trials"]
out["final_summary"]["task_pass_at_3"] = out["final_summary"]["tasks_with_pass3"] / out["final_summary"]["tasks"]
pil = list(out["pilot"].values())
out["pilot_summary"] = dict(tasks=len(pil), trials=sum(t["n_valid"] for t in pil), successful_trials=sum(t["successes"] for t in pil),
                            tasks_with_pass3=sum(t["pass_at_3"] for t in pil))
checks = [x for x in rows if x["agent"] == "claude-code"]
out["costs"] = dict(gemini_all_runs_usd=round(tot_model, 4),
                    gemini_excluded_g36_usd=round(sum(x["cost"] for x in rows if x["agent"] == "gemini-cli" and x["path"] and "g36" in x["path"]), 4),
                    gemini_task02_ablation_usd=round(sum(x["cost"] for x in rows if x["agent"] == "gemini-cli" and x["path"] and "explicit-invariant" in x["path"]), 4),
                    harbor_check_usd=round(sum(x["cost"] for x in checks), 4))
os.makedirs(os.path.join(ROOT, "report", "data"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "report", "data", "results.json"), "w"), indent=1)
print(json.dumps(out["final_summary"], indent=1)); print(json.dumps(out["pilot_summary"])); print(json.dumps(out["costs"]))
for tid, t in out["pilot"].items():
    print(f"{tid:7s} {t['successes']}/{t['n_valid']} pass@3={t['pass_at_3']} invalid_runs={t['invalid_runs']} cost=${t['model_cost_usd']}")
