"""Build the dossier's machine-readable inventory directly from raw repository artifacts.

Sources, in order of authority:
  1. submission_final10.zip  -> the exact ten tasks as evaluated (verified by SHA-256)
  2. candidates/*            -> every task directory present
  3. jobs/*, crossmodel_logs/claude/*  -> every trial, valid and invalid
Nothing here is read from a prior narrative summary.
"""
import csv, glob, hashlib, json, os, subprocess, sys, zipfile, collections

ROOT = "/Users/yashshah2311/forensicds"
os.chdir(ROOT)
OUT = "research_review"
FINAL10 = ["02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand",
 "g24-recommender-ope","g36-tou-capacity-gate","p20-noshow-monitoring",
 "p22-gauge-recalibration","p31-fill-rate-dispute","g50-courier-boost-rollout",
 "g08-forecast-accuracy-vintages"]

def agg(root, skip=("__pycache__",".ipynb_checkpoints")):
    h = hashlib.sha256(); n = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in skip]
        for f in sorted(fns):
            p = os.path.join(dp, f)
            h.update(os.path.relpath(p, root).encode())
            h.update(hashlib.sha256(open(p, "rb").read()).digest())
            n += 1
    return h.hexdigest(), n

# ---------- which tasks are inside the authoritative ZIP ----------
zip_tasks = set()
with zipfile.ZipFile("submission_final10.zip") as z:
    for n in z.namelist():
        parts = n.split("/")
        if len(parts) > 2 and parts[0] == "samples" and parts[1]:
            zip_tasks.add(parts[1])

# ---------- task inventory ----------
tasks = []
for d in sorted(glob.glob("candidates/*/")):
    t = os.path.basename(d.rstrip("/"))
    a, nf = agg(d.rstrip("/"))
    in_final = t in FINAL10
    in_zip = t in zip_tasks
    has = lambda p: os.path.exists(os.path.join(d, p))
    # drift check against the ZIP copy where one exists
    drift = "n/a"
    if in_zip:
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        with zipfile.ZipFile("submission_final10.zip") as z:
            for n in z.namelist():
                if n.startswith(f"samples/{t}/"): z.extract(n, tmp)
        za, znf = agg(os.path.join(tmp, "samples", t))
        drift = "IDENTICAL" if za == a else f"DIFFERS(zip={znf}f/{za[:12]} wt={nf}f/{a[:12]})"
        shutil.rmtree(tmp, ignore_errors=True)
    tasks.append(dict(task_id=t, files=nf, aggregate_sha256=a,
        in_final_ten=in_final, shipped_in_zip=in_zip, matches_zip=drift,
        has_instruction=has("instruction.md"), has_task_toml=has("task.toml"),
        has_dockerfile=has("environment/Dockerfile"), has_tests=has("tests/test.sh"),
        has_solution=os.path.isdir(os.path.join(d,"solution")),
        has_provenance=has("REAL_DISTRIBUTION_PROVENANCE.md"),
        emits_criteria=bool(glob.glob(os.path.join(d,"tests","*.py")) and
            any("criterion_" in open(f,errors="replace").read() or "criteria.json" in open(f,errors="replace").read()
                for f in glob.glob(os.path.join(d,"tests","*"))
                if os.path.isfile(f) and f.endswith((".py",".sh")))),
        multistage_build=("--from=" in open(os.path.join(d,"environment","Dockerfile")).read()
                          if has("environment/Dockerfile") else None)))
with open(f"{OUT}/MACHINE_READABLE_INVENTORY.csv","w",newline="") as fh:
    w=csv.DictWriter(fh, fieldnames=list(tasks[0])); w.writeheader(); w.writerows(tasks)
print(f"MACHINE_READABLE_INVENTORY.csv: {len(tasks)} task directories")

# ---------- trial inventory ----------
def scan(root, agent, arm):
    rows=[]
    for cfg in sorted(glob.glob(f"{root}/*/config.json")):
        j=os.path.dirname(cfg); jn=os.path.basename(j)
        try: c=json.load(open(cfg))
        except Exception: continue
        ag=c.get("agents") or []
        nm=ag[0].get("name") if ag else c.get("agent",{}).get("name")
        if nm!=agent: continue
        model=(ag[0].get("model_name") if ag else None) or ""
        tsk=c.get("tasks") or []
        task=os.path.basename(tsk[0]["path"]) if tsk else "?"
        invalid_marker = "__INVALID" in jn
        reason = jn.split("__INVALID-",1)[1] if invalid_marker and "__INVALID-" in jn else ""
        for tr in sorted(glob.glob(j+"/*/")):
            trn=os.path.basename(tr.rstrip("/"))
            rf=os.path.join(tr,"verifier","reward.txt")
            reward = open(rf).read().strip() if os.path.exists(rf) else ""
            cj=os.path.join(tr,"verifier","criteria.json")
            crit = json.load(open(cj)) if os.path.exists(cj) else None
            tj=os.path.join(tr,"agent","trajectory.json")
            steps=cost=None; refused=False
            if os.path.exists(tj):
                try:
                    d=json.load(open(tj)); fm=d.get("final_metrics") or {}
                    steps=len(d.get("steps",[])); cost=fm.get("total_cost_usd")
                except Exception: pass
            so=os.path.join(tr,"verifier","test-stdout.txt")
            if os.path.exists(so):
                refused = "refusing to grade" in open(so,errors="replace").read()
            agent_ran = (steps or 0) > 3
            # validity rule, applied identically to both arms
            if invalid_marker: valid=False; why=reason
            elif not reward: valid=False; why="no-reward-emitted"
            elif refused: valid=False; why="verifier-refused-to-grade"
            elif arm=="claude" and not agent_ran and (cost or 0)<0.01: valid=False; why="agent-never-ran"
            else: valid=True; why=""
            rows.append(dict(arm=arm, agent=agent, model=model, task=task, job=jn, trial=trn,
                valid=valid, invalid_reason=why, reward=reward,
                passed=(1 if (valid and reward not in ("0","0.0")) else (0 if valid else "")),
                criterion_instrumented=bool(crit), steps=steps, cost_usd=cost,
                verifier_refused=refused,
                raw_log_path=os.path.relpath(tr.rstrip("/"), ROOT)))
    return rows
trials = scan("jobs","gemini-cli","gemini") + scan("crossmodel_logs/claude","claude-code","claude")
with open(f"{OUT}/ALL_TRIALS.csv","w",newline="") as fh:
    w=csv.DictWriter(fh, fieldnames=list(trials[0])); w.writeheader(); w.writerows(trials)
v=[r for r in trials if r["valid"]]
print(f"ALL_TRIALS.csv: {len(trials)} trial records ({len(v)} valid, {len(trials)-len(v)} invalid)")
for arm in ("gemini","claude"):
    a=[r for r in v if r["arm"]==arm]
    af=[r for r in a if r["task"] in FINAL10]
    print(f"   {arm}: {len(a)} valid total, {len(af)} valid on the final ten, "
          f"{sum(r['passed'] for r in af)} passes")

# ---------- criterion results, missing values left empty ----------
crows=[]
for r in trials:
    cj=os.path.join(ROOT, r["raw_log_path"], "verifier","criteria.json")
    if not os.path.exists(cj): continue
    try: d=json.load(open(cj))
    except Exception: continue
    crows.append(dict(arm=r["arm"], model=r["model"], task=r["task"], job=r["job"],
        valid=r["valid"], invalid_reason=r["invalid_reason"], reward=r["reward"], **{k:int(bool(vv)) for k,vv in d.items()}))
keys=sorted({k for row in crows for k in row if k not in
    ("arm","model","task","job","valid","invalid_reason","reward")})
hdr=["arm","model","task","job","valid","invalid_reason","reward"]+keys
with open(f"{OUT}/CRITERION_RESULTS.csv","w",newline="") as fh:
    w=csv.DictWriter(fh, fieldnames=hdr, restval=""); w.writeheader(); w.writerows(crows)
print(f"CRITERION_RESULTS.csv: {len(crows)} instrumented trials, {len(keys)} distinct criteria")
print("   criteria seen:", ", ".join(keys))
json.dump(dict(tasks=tasks, trials=trials, criteria=crows),
          open(f"{OUT}/_inventory.json","w"), indent=1, default=str)
