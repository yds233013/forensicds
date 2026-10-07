"""Cross-model analysis: Claude (crossmodel_logs/claude) vs Gemini (jobs/) on the frozen final ten.

Applies the SAME extraction and coding rules to both arms. Produces:
  CLAUDE_CROSSMODEL_RESULTS.json   (Claude arm filled in beside the Gemini baseline)
  CLAUDE_TRAJECTORY_ANALYSIS.csv   (one row per valid Claude trial)
  CLAUDE_VS_GEMINI.md              (the comparison tables)
  report/analysis/crossmodel_*.svg (plots)

Run after scripts/run_claude_crossmodel.sh. Reads logs only; never touches a task.
"""
import csv, glob, json, os, re, statistics as st, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_trajectories as EX          # reuse the identical signal patterns

FINAL10 = ["02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand",
 "g24-recommender-ope","g36-tou-capacity-gate","p20-noshow-monitoring",
 "p22-gauge-recalibration","p31-fill-rate-dispute","g50-courier-boost-rollout",
 "g08-forecast-accuracy-vintages"]

# Pre-registered in CLAUDE_CROSSMODEL_EVAL.md §6, identical to the Gemini arm.
MECH = {
 "02-renewal-risk-regression": r"point-?in-?time|leak|look-?ahead|as-?of|future information|overwritten|snapshot",
 "g05-sco-rollout-gate": r"stagger|wave|cohort|not-?yet-?treated|already-?treated|event.?time|two-?way fixed",
 "g10-censored-demand": r"censor|stockout|lost (sales|demand)|availability|latent demand",
 "g24-recommender-ope": r"logging policy|off-?policy|propensity|importance (weight|sampling)|exposure|direct match|selection bias",
 "g36-tou-capacity-gate": r"tariff|time-?of-?use|tou|enrol|migrat|coincident|population",
 "p20-noshow-monitoring": r"feedback|reminder programme|vintage|as-?served|feature (feed|store)|drift",
 "p22-gauge-recalibration": r"calibrat|gauge|measurement system|cmm|offset|bias",
 "p31-fill-rate-dispute": r"denominator|aggregat|definition|line[- ]item|order level|case level|substitut|return",
 "g08-forecast-accuracy-vintages": r"vintage|restat|as-?of|revision|snapshot|point-?in-?time",
}
DOWNSTREAM = ["quantitative_result","quantitative_results","decision"]

def harvest(root, agent):
    """Collect valid trials for one arm, using the shared extractor."""
    rows = []
    for cfg in sorted(glob.glob(f"{root}/*/config.json")):
        j = os.path.dirname(cfg); jn = os.path.basename(j)
        try: c = json.load(open(cfg))
        except Exception: continue
        ag = c.get("agents") or []
        if not ag or ag[0].get("name") != agent: continue
        invalid = "__INVALID" in jn
        tasks = c.get("tasks") or []
        task = os.path.basename(tasks[0]["path"]) if tasks else "?"
        if task not in FINAL10: continue
        for tr in sorted(glob.glob(j + "/*/")):
            rf = os.path.join(tr, "verifier", "reward.txt")
            if not os.path.exists(rf): continue
            rec = dict(job=jn, trial=os.path.basename(tr.rstrip("/")), task=task,
                       reward=open(rf).read().strip(), invalid=invalid,
                       model=(ag[0].get("model_name") or ""))
            for f, k in (("criteria.json","criteria"),("reward.json","reward_json")):
                p = os.path.join(tr,"verifier",f)
                if os.path.exists(p):
                    try: rec[k] = json.load(open(p))
                    except Exception: pass
            p = os.path.join(tr,"verifier","criteria_notes.txt")
            if os.path.exists(p): rec["criteria_notes"] = open(p).read()[:4000]
            tj = os.path.join(tr,"agent","trajectory.json")
            if os.path.exists(tj):
                try: rec.update(EX.summarise(tj))
                except Exception as e: rec["traj_error"] = repr(e)
            rows.append(rec)
    return rows

def code(r):
    """Apply the pre-registered coding rules. Returns the trajectory-analysis row."""
    sig = r.get("signals") or {}
    blob = " ".join(filter(None,[r.get("first_reasoning"),r.get("mid_reasoning"),r.get("last_reasoning")]))
    crit = r.get("criteria") or {}
    def c(*names):
        for n in names:
            if n in crit: return bool(crit[n])
        return None
    mech = bool(re.search(MECH[r["task"]], blob, re.I)) if r["task"] in MECH else None
    revised = sig.get("revision",0) > 0
    downstream_ok = None
    if crit:
        vals=[crit[k] for k in DOWNSTREAM if k in crit]
        downstream_ok = (all(vals) if vals else None)
    propagated = ("unobservable" if not crit else
                  ("yes" if revised and downstream_ok else ("no" if revised else "n/a-no-revision")))
    passed = r["reward"] not in ("0","0.0")
    # first consequential error, from the criterion pattern (same rule both arms)
    if passed: fce="none"
    elif not crit: fce="unobservable-binary-reward"
    elif not c("evidence_reconstruction"): fce="evidence_reconstruction"
    elif not c("scientific_object"): fce="scientific_object"
    elif not c("quantitative_result","quantitative_results"): fce="quantitative_result"
    elif not c("uncertainty"): fce="uncertainty"
    elif not c("identification"): fce="identification"
    elif not c("decision"): fce="decision"
    else: fce="other"
    borderline = []
    if mech and not passed and sig.get("revision",0)==0: borderline.append("mechanism-named-but-no-revision")
    if crit and downstream_ok is None: borderline.append("no-downstream-criterion")
    return dict(
        model=r.get("model"), task=r["task"], job=r["job"], trial=r["trial"], reward=r["reward"],
        passed=int(passed),
        governing_evidence_inspected=int(sig.get("read_policy_doc",0)>0),
        anomaly_noticed=int(sig.get("notice_anomaly",0)>0),
        correct_mechanism_recognised=("" if mech is None else int(mech)),
        identification_engaged=int(sig.get("identification",0)>0),
        useful_diagnostic=int(sig.get("diagnostic_test",0)+sig.get("competing_hypotheses",0)>0),
        contradiction_engaged=int(sig.get("competing_hypotheses",0)>0),
        revision_attempted=int(revised), revision_propagated=propagated,
        correct_scientific_object=("" if c("scientific_object") is None else int(c("scientific_object"))),
        correct_quantity=("" if c("quantitative_result","quantitative_results") is None
                          else int(c("quantitative_result","quantitative_results"))),
        estimator_implementation=("" if c("estimator_implementation") is None else int(c("estimator_implementation"))),
        independent_validation=("" if c("independent_validation") is None else int(c("independent_validation"))),
        uncertainty=("" if c("uncertainty") is None else int(c("uncertainty"))),
        final_decision=("" if c("decision") is None else int(c("decision"))),
        first_consequential_error=fce,
        failure_side=("n/a" if passed else "model"),
        steps=r.get("steps"), tool_calls=r.get("n_tool_calls"),
        completion_tokens=r.get("completion_tokens"), prompt_tokens=r.get("prompt_tokens"),
        borderline=";".join(borderline),
    )

def rates(rows):
    v=[r for r in rows if not r["invalid"]]
    if not v: return None
    coded=[code(r) for r in v]
    n=len(coded)
    num=lambda k: [c[k] for c in coded if c[k] != ""]
    mean=lambda k: (sum(num(k))/len(num(k)) if num(k) else None)
    return dict(valid=n, passes=sum(c["passed"] for c in coded),
        recognition=mean("correct_mechanism_recognised"), revision=mean("revision_attempted"),
        anomaly=mean("anomaly_noticed"), governing=mean("governing_evidence_inspected"),
        correct_quantity=mean("correct_quantity"), correct_decision=mean("final_decision"),
        correct_object=mean("correct_scientific_object"),
        fce=collections.Counter(c["first_consequential_error"] for c in coded),
        coded=coded)

if __name__ == "__main__":
    gem = harvest("jobs","gemini-cli")
    cla = harvest("crossmodel_logs/claude","claude-code")
    print(f"gemini trials found: {len(gem)} ({sum(1 for r in gem if not r['invalid'])} valid)")
    print(f"claude trials found: {len(cla)} ({sum(1 for r in cla if not r['invalid'])} valid)")
    if not [r for r in cla if not r["invalid"]]:
        print("\nNo valid Claude trials. Nothing to compare. "
              "Run scripts/run_claude_crossmodel.sh first (it gates on credential rotation).")
        sys.exit(0)
    G, C = rates(gem), rates(cla)
    with open("CLAUDE_TRAJECTORY_ANALYSIS.csv","w",newline="") as fh:
        w=csv.DictWriter(fh, fieldnames=list(C["coded"][0]))
        w.writeheader(); w.writerows(C["coded"])
    print("wrote CLAUDE_TRAJECTORY_ANALYSIS.csv")
    res=json.load(open("CLAUDE_CROSSMODEL_RESULTS.json"))
    res["status"]="COMPLETE"; res.pop("blocker",None)
    byt=lambda rows: {t:[r for r in rows if r["task"]==t and not r["invalid"]] for t in FINAL10}
    gt, ct = byt(gem), byt(cla)
    res["claude_results"]={}
    for t in FINAL10:
        v=ct[t]; p=sum(1 for r in v if r["reward"] not in ("0","0.0"))
        res["claude_results"][t]=dict(valid_trials=len(v), passes=p,
            pass_at_1=(round(p/len(v),4) if v else None), pass_at_3=(1 if p else 0) if v else None)
    tv=sum(len(ct[t]) for t in FINAL10); tp=sum(res["claude_results"][t]["passes"] for t in FINAL10)
    p3=[res["claude_results"][t]["pass_at_3"] for t in FINAL10 if ct[t]]
    res["claude_results"]["_suite"]=dict(total_valid_trials=tv, total_passes=tp,
        aggregate_trial_pass_rate=(round(tp/tv,4) if tv else None),
        task_level_pass_at_3=(round(sum(p3)/len(p3),4) if p3 else None),
        model=C["coded"][0]["model"], agent="claude-code")
    res["behavioural_comparison"]={k:{"gemini":G[k],"claude":C[k]} for k in
        ("recognition","revision","anomaly","governing","correct_quantity","correct_decision","correct_object")}
    res["first_consequential_error"]={"gemini":dict(G["fce"]),"claude":dict(C["fce"])}
    json.dump(res, open("CLAUDE_CROSSMODEL_RESULTS.json","w"), indent=1, default=str)
    print("wrote CLAUDE_CROSSMODEL_RESULTS.json")
    pct=lambda x: "n/a" if x is None else f"{x:.0%}"
    L=["# Claude vs Gemini on the frozen ForensicDS final ten","",
       f"Claude: `{res['claude_results']['_suite']['model']}` via `claude-code`. "
       f"Gemini: `google/gemini-3-flash-preview` via `gemini-cli`. Identical tasks, identical verifiers, "
       "identical coding rules (pre-registered in `CLAUDE_CROSSMODEL_EVAL.md` §6).","",
       "## Per task","",
       "| task | Gemini passes/valid | Claude passes/valid | Gemini pass@3 | Claude pass@3 |","|---|---|---|---|---|"]
    for t in FINAL10:
        g=res["gemini_baseline"][t]; c=res["claude_results"][t]
        L.append(f"| `{t}` | {g['passes']}/{g['valid_trials']} | {c['passes']}/{c['valid_trials']} "
                 f"| {g['pass_at_3']} | {c['pass_at_3']} |")
    gs=res["gemini_baseline"]["_suite"]; cs=res["claude_results"]["_suite"]
    L += ["", "## Suite", "",
        "| metric | Gemini | Claude |","|---|---|---|",
        f"| valid trials | {gs['total_valid_trials']} | {cs['total_valid_trials']} |",
        f"| passes | {gs['total_passes']} | {cs['total_passes']} |",
        f"| aggregate trial pass rate | {gs['aggregate_trial_pass_rate']:.1%} | {cs['aggregate_trial_pass_rate']:.1%} |",
        f"| task-level pass@3 | {gs['task_level_pass_at_3']:.0%} | {cs['task_level_pass_at_3']:.0%} |",
        "", "## Behaviour (same coding rules both arms)", "",
        "| measure | Gemini | Claude |","|---|---|---|"]
    for k,lab in (("governing","read the governing document"),("anomaly","noticed an anomaly"),
                  ("recognition","named the correct mechanism"),("revision","revised"),
                  ("correct_object","correct scientific object"),("correct_quantity","correct quantity"),
                  ("correct_decision","correct decision")):
        L.append(f"| {lab} | {pct(G[k])} | {pct(C[k])} |")
    L += ["","## First consequential error","","| stage | Gemini | Claude |","|---|---|---|"]
    for k in sorted(set(G["fce"])|set(C["fce"])):
        L.append(f"| {k} | {G['fce'].get(k,0)} | {C['fce'].get(k,0)} |")
    L += ["","Three trials per task. These are small-sample counts, not statistically precise estimates; "
          "no significance claim is made from them."]
    open("CLAUDE_VS_GEMINI.md","w").write("\n".join(L)+"\n")
    print("wrote CLAUDE_VS_GEMINI.md")
