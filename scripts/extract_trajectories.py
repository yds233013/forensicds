"""Extract a structured trajectory-analysis dataset from every valid Gemini trial.

Hard evidence only: tool calls, files touched, commands run, step/token counts, final workspace
artifacts, verifier criteria. Reasoning text is summarised into keyword signals plus the first and
last reasoning blocks, so a human can classify without re-reading 3 MB per trial.
"""
import json, glob, os, re, collections, sys

OUT = "report/analysis"
os.makedirs(OUT, exist_ok=True)

# signals looked for in reasoning/messages. Each is a professional move we care about.
SIGNALS = {
 "reproduce_incumbent": r"reproduc|re-?run the (incumbent|existing|current)|match the report|confirm the (headline|reported)",
 "read_policy_doc":     r"agreement|memo|contract|schedule 3|policy|protocol|sla|definition",
 "notice_anomaly":      r"discrepanc|inconsisten|doesn'?t match|does not match|anomal|surpris|unexpected|odd\b",
 "competing_hypotheses":r"hypothes|alternative explanation|could be either|two possible|candidate cause|competing",
 "diagnostic_test":     r"let me (check|test|verify)|to test this|sanity check|cross-?check|compare against",
 "population_redef":    r"population|eligib|cohort|denominator|inclusion criteri|filter to",
 "estimand_language":   r"estimand|causal|counterfactual|what we actually want|the quantity|target quantity",
 "identification":      r"identif|confound|selection bias|endogen|randomi[sz]|assignment",
 "censoring":           r"censor|truncat|stockout|right-?censor|survival",
 "leakage":             r"leak|look-?ahead|future information|as-?of|vintage|restat",
 "interference":        r"interferen|sutva|spillover|shared (pool|capacity)|cannibali",
 "unit_of_analysis":    r"unit of (analysis|inference|randomi)|cluster|pseudoreplicat|per-?user vs|level of",
 "calibration":         r"calibrat|reliability diagram|brier|isotonic|platt",
 "uncertainty":         r"confidence interval|standard error|bootstrap|uncertaint|\bci\b|p-?value",
 "validation":          r"holdout|cross-?validat|out-?of-?sample|backtest|independent (check|validation)",
 "revision":            r"i was wrong|revise|reconsider|actually|on reflection|that'?s not right|need to redo|instead of",
 "gave_up_early":       r"good enough|proceed with|accept this|move on|due to time|simplif",
 "decision_mapping":    r"threshold|break-?even|decision rule|recommend|roll out|do not roll",
}
SIG_RE = {k: re.compile(v, re.I) for k, v in SIGNALS.items()}

def walk_calls(steps):
    for s in steps:
        for tc in (s.get("tool_calls") or []):
            yield s, tc

def summarise(path):
    d = json.load(open(path))
    steps = d.get("steps", [])
    agent = d.get("agent", {})
    fm = d.get("final_metrics", {})
    reasoning, messages = [], []
    tools = collections.Counter()
    files_read, cmds = [], []
    for s in steps:
        if s.get("reasoning_content"): reasoning.append(s["reasoning_content"])
        if s.get("message"): messages.append(s["message"])
        for _, tc in walk_calls([s]):
            fn = tc.get("function_name", "?")
            tools[fn] += 1
            a = tc.get("arguments") or {}
            if not isinstance(a, dict): continue
            for k in ("absolute_path", "file_path", "path"):
                if a.get(k): files_read.append(str(a[k]))
            for k in ("command", "cmd"):
                if a.get(k): cmds.append(str(a[k])[:400])
            if a.get("pattern"): files_read.append("glob:" + str(a["pattern"]))
    blob = "\n".join(reasoning + messages)
    sig = {k: len(r.findall(blob)) for k, r in SIG_RE.items()}
    return dict(
        agent=agent.get("name"), model=agent.get("model_name"), version=agent.get("version"),
        steps=len(steps), llm_steps=sum(1 for s in steps if s.get("source") == "agent"),
        prompt_tokens=fm.get("total_prompt_tokens"), completion_tokens=fm.get("total_completion_tokens"),
        cached_tokens=fm.get("total_cached_tokens"),
        tools=dict(tools.most_common()), n_tool_calls=sum(tools.values()),
        distinct_files=sorted(set(files_read)), n_file_ops=len(files_read),
        commands=cmds[:60], n_commands=len(cmds),
        signals=sig, reasoning_chars=len(" ".join(reasoning)),
        first_reasoning=(reasoning[0][:1200] if reasoning else ""),
        last_reasoning=(reasoning[-1][:1200] if reasoning else ""),
        mid_reasoning=(reasoning[len(reasoning)//2][:1200] if reasoning else ""),
    )

def main():
    rows = []
    for cfg in sorted(glob.glob("jobs/*/config.json")):
        j = os.path.dirname(cfg); jn = os.path.basename(j)
        c = json.load(open(cfg))
        ag = c.get("agents") or []
        if not ag or ag[0].get("name") != "gemini-cli": continue
        invalid = "__INVALID" in jn
        tasks = c.get("tasks") or []
        task = os.path.basename(tasks[0]["path"]) if tasks else "?"
        for tr in sorted(glob.glob(j + "/*/")):
            trn = os.path.basename(tr.rstrip("/"))
            rf = os.path.join(tr, "verifier", "reward.txt")
            if not os.path.exists(rf): continue
            reward = open(rf).read().strip()
            tj = os.path.join(tr, "agent", "trajectory.json")
            rec = dict(job=jn, trial=trn, task=task, reward=reward, invalid=invalid,
                       has_traj=os.path.exists(tj))
            # verifier criterion detail where the task emits it
            for f, key in (("criteria.json", "criteria"), ("reward.json", "reward_json")):
                p = os.path.join(tr, "verifier", f)
                if os.path.exists(p):
                    try: rec[key] = json.load(open(p))
                    except Exception: pass
            p = os.path.join(tr, "verifier", "criteria_notes.txt")
            if os.path.exists(p): rec["criteria_notes"] = open(p).read()[:4000]
            # the agent's final artifacts
            arts = glob.glob(os.path.join(tr, "artifacts", "workspace", "out", "*"))
            rec["final_out"] = sorted(os.path.basename(a) for a in arts)
            for a in arts:
                if a.endswith(".json"):
                    try: rec["final_json"] = json.load(open(a))
                    except Exception: rec["final_json"] = "unparseable"
            if rec["has_traj"]:
                try: rec.update(summarise(tj))
                except Exception as e: rec["traj_error"] = repr(e)
            rows.append(rec)
    
    json.dump(rows, open(f"{OUT}/trajectories.json", "w"), indent=1, default=str)
    valid = [r for r in rows if not r["invalid"]]
    print(f"trials extracted: {len(rows)}  valid: {len(valid)}  with trajectory: {sum(1 for r in valid if r['has_traj'])}")
    print(f"with criterion detail: {sum(1 for r in valid if 'criteria' in r)}")
    print(f"wrote {OUT}/trajectories.json")


if __name__ == "__main__":
    main()
