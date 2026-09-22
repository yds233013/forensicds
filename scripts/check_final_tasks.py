#!/usr/bin/env python3
"""For each final task: confirm Oracle=1, Nop=0 and >=3 valid gemini trials, all on the SAME Harbor task checksum.

    python3 scripts/check_final_tasks.py            (reads scripts/final_tasks.json)
Exit code 1 if any check fails. Read-only; never runs an agent.
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
cfg = json.load(open(os.path.join(HERE, "final_tasks.json")))
ok = True
for t in cfg["tasks"]:
    rows = []
    for p in glob.glob(os.path.join(ROOT, "jobs", "*", "*", "result.json")):
        r = json.load(open(p))
        if (r.get("config", {}).get("task", {}) or {}).get("path") != t["path"]:
            continue
        lk = os.path.join(os.path.dirname(p), "lock.json")
        dg = ((json.load(open(lk)).get("task") or {}).get("digest") if os.path.exists(lk) else None) or ""
        # identity = Harbor's durable TrialLock task digest (excludes nothing Harbor considers task content);
        # fall back to the deprecated dirhash task_checksum, which also hashes git-ignored bytecode caches
        rows.append(dict(job=p.split(os.sep)[-3], trial=r.get("trial_name"), agent=(r.get("agent_info") or {}).get("name"),
                         reward=((r.get("verifier_result") or {}).get("rewards") or {}).get("reward"),
                         cs=(dg[7:23] if dg.startswith("sha256:") else (r.get("task_checksum") or "")[:16]), exc=r.get("exception_info")))
    base = [x for x in rows if x["trial"] in t["valid_trials"]]
    css = {x["cs"] for x in base}
    frozen_cs = css.pop() if len(css) == 1 else None
    orc = [x for x in rows if x["agent"] == "oracle" and x["cs"] == frozen_cs]
    nop = [x for x in rows if x["agent"] == "nop" and x["cs"] == frozen_cs]
    checks = {
        "3_valid_trials_found": len(base) == 3 and all(x["exc"] is None for x in base),
        "single_checksum_for_trials": frozen_cs is not None,
        "oracle_1_on_frozen": any(x["reward"] == 1.0 for x in orc),
        "nop_0_on_frozen": any(x["reward"] == 0.0 for x in nop),
        "rewards_match_record": sorted(x["reward"] for x in base) == sorted(t["rewards"]),
    }
    ok &= all(checks.values())
    print(f"{t['id']:8s} lock_digest={frozen_cs} rewards={[x['reward'] for x in base]} "
          + " ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in checks.items()))
sys.exit(0 if ok else 1)
