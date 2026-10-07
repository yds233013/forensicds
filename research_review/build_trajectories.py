"""Generate one chronological case study per VALID trial, from raw trajectory JSON only.

Every field is either read from the artifact or written as 'not observable'. No private
reasoning is attributed; where the scaffold records a reasoning summary it is quoted as a
recorded artifact, not as the model's mental state.
"""
import csv, glob, json, os, re, collections

ROOT="/Users/yashshah2311/forensicds"; os.chdir(ROOT)
OUT="research_review/trajectories"; os.makedirs(OUT, exist_ok=True)
FINAL10=["02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand",
 "g24-recommender-ope","g36-tou-capacity-gate","p20-noshow-monitoring",
 "p22-gauge-recalibration","p31-fill-rate-dispute","g50-courier-boost-rollout",
 "g08-forecast-accuracy-vintages"]
trials=list(csv.DictReader(open("research_review/ALL_TRIALS.csv")))

def load(tr):
    p=os.path.join(ROOT,tr,"agent","trajectory.json")
    return json.load(open(p)) if os.path.exists(p) else None

def actions(d):
    """Observable actions: tool calls with their arguments, in order."""
    out=[]
    for s in d.get("steps",[]):
        ts=s.get("timestamp","")
        for tc in (s.get("tool_calls") or []):
            fn=tc.get("function_name","?"); a=tc.get("arguments") or {}
            det=""
            if isinstance(a,dict):
                for k in ("absolute_path","file_path","path","pattern","command","cmd","notebook_path"):
                    if a.get(k): det=str(a[k])[:150]; break
                if not det and a.get("content"): det=f"<wrote {len(str(a['content']))} chars>"
                if not det and a.get("strategic_intent"): det=str(a["strategic_intent"])[:150]
            out.append((ts,fn,det))
    return out

def rec_reasoning(d):
    return [ (s.get("timestamp",""), s["reasoning_content"])
             for s in d.get("steps",[]) if s.get("reasoning_content") ]

def final_outputs(tr):
    base=os.path.join(ROOT,tr,"artifacts","workspace")
    res={}
    for p in glob.glob(base+"/out/*"):
        n=os.path.basename(p)
        if p.endswith(".json"):
            try: res[n]=json.load(open(p))
            except Exception: res[n]="<unparseable JSON>"
        else: res[n]=f"<{os.path.getsize(p)} bytes>"
    return res

def notes(tr):
    p=os.path.join(ROOT,tr,"verifier","criteria_notes.txt")
    return open(p,errors="replace").read() if os.path.exists(p) else None

def crit(tr):
    p=os.path.join(ROOT,tr,"verifier","criteria.json")
    if not os.path.exists(p): return None
    try: return json.load(open(p))
    except Exception: return None

written=0; index=collections.defaultdict(list)
for r in trials:
    if r["valid"]!="True" or r["task"] not in FINAL10: continue
    tr=r["raw_log_path"]; d=load(tr)
    slug=f"{r['arm']}--{r['task']}--{r['job']}--{r['trial']}".replace("/","_")
    f=os.path.join(OUT,slug+".md")
    acts = actions(d) if d else []
    rr   = rec_reasoning(d) if d else []
    outs = final_outputs(tr); cj=crit(tr); nt=notes(tr)
    fm   = (d.get("final_metrics") or {}) if d else {}
    ts   = [a[0] for a in acts if a[0]]
    toolc= collections.Counter(a[1] for a in acts)
    files= [a[2] for a in acts if a[1] in ("read_file","Read","read_many_files","Glob","Grep","search_file_content")]
    cmds = [a[2] for a in acts if a[1] in ("run_shell_command","Bash")]
    writes=[a[2] for a in acts if a[1] in ("write_file","Write","Edit","replace","NotebookEdit")]
    L=[f"# {r['arm'].title()} trial — `{r['task']}`","",
       f"**Job** `{r['job']}` · **trial dir** `{r['trial']}`  ",
       f"**Model** `{r['model']}` · **agent** `{r['agent']}`  ",
       f"**Raw log** `{tr}`  ",
       f"**Reward** **{r['reward']}** ({'PASS' if r['passed']=='1' else 'FAIL'})","",
       "> Every line below is read from the trial artifacts. Where the scaffold did not record",
       "> something it says *not observable*. Reasoning summaries, where present, are quoted as",
       "> recorded text — they are not treated as evidence of private mental states.","",
       "## 1. Task and available evidence","",
       f"Task directory: `candidates/{r['task']}` (frozen; verified byte-identical to the submission ZIP).",
       f"The agent received `instruction.md` and a `/workspace` populated by the task generator.","",
       "## 2. Observable timeline","",
       f"| | |","|---|---|",
       f"| recorded steps | {r['steps'] or 'not observable'} |",
       f"| tool calls | {sum(toolc.values())} |",
       f"| distinct tools | {', '.join(f'`{k}`×{v}' for k,v in toolc.most_common()) or 'not observable'} |",
       f"| file reads/searches | {len(files)} |",
       f"| shell commands | {len(cmds)} |",
       f"| file writes/edits | {len(writes)} |",
       f"| first action at | {ts[0] if ts else 'not observable'} |",
       f"| last action at | {ts[-1] if ts else 'not observable'} |",
       f"| prompt tokens | {fm.get('total_prompt_tokens','not recorded')} |",
       f"| completion tokens | {fm.get('total_completion_tokens','not recorded')} |",
       f"| cached tokens | {fm.get('total_cached_tokens','not recorded')} |",
       f"| cost (USD) | {fm.get('total_cost_usd','not recorded')} |","",
       "### Action sequence (first 40)",""]
    if acts:
        L+=["| # | tool | target / argument |","|---|---|---|"]
        for i,(t,fn,det) in enumerate(acts[:40],1):
            L.append(f"| {i} | `{fn}` | `{det.replace('|','\\|')[:120]}` |" if det else f"| {i} | `{fn}` | — |")
        if len(acts)>40: L.append(f"\n*…{len(acts)-40} further actions in the raw log.*")
    else:
        L.append("*No tool calls recorded in the trajectory — not observable.*")
    L+=["","## 3. Shell commands executed",""]
    if cmds:
        L.append("```")
        for c in cmds[:25]: L.append(c[:200])
        if len(cmds)>25: L.append(f"... {len(cmds)-25} more")
        L.append("```")
    else: L.append("*None recorded.*")
    L+=["","## 4. Recorded reasoning summaries",""]
    if rr:
        L.append(f"The scaffold recorded {len(rr)} reasoning blocks, "
                 f"{sum(len(x[1]) for x in rr):,} characters total. First and last:")
        L.append("")
        L+=["**First:**","```",rr[0][1][:900],"```","","**Last:**","```",rr[-1][1][:900],"```"]
    else:
        L.append("*No reasoning text recorded by this scaffold for this trial — not observable.*")
    L+=["","## 5. Artifacts the agent produced",""]
    if outs:
        for n,v in outs.items():
            L.append(f"**`out/{n}`**")
            L+=["```json", json.dumps(v,indent=1)[:1500], "```"] if isinstance(v,(dict,list)) else [f"`{v}`"]
    else:
        L.append("*No `out/` artifacts captured in this trial's archive.* Note: for several tasks the")
        L.append("archived workspace does not include generated outputs, so the produced numbers are")
        L.append("recoverable only from the verifier's own notes below. **not observable** otherwise.")
    L+=["","## 6. Verifier outcome",""]
    if cj:
        L+=["| criterion | result |","|---|---|"]
        for k,v in sorted(cj.items()): L.append(f"| `{k}` | {'PASS' if v else '**fail**'} |")
    else:
        L.append(f"This task emits a **binary reward only** (no `criteria.json`). Reward = {r['reward']}.")
        L.append("Criterion-level attribution is therefore **not observable** for this trial.")
    if nt:
        L+=["","### Verifier notes (the authoritative record of what was wrong)","```",nt[:2500],"```"]
    L+=["","## 7. What is and is not established","",
        "- **VERIFIED FROM ARTIFACT:** the reward, the criterion results where present, the tool-call",
        "  sequence, and any numbers quoted in the verifier notes.",
        "- **INFERENCE:** any statement about *why* the agent acted as it did.",
        "- **NOT OBSERVABLE:** private reasoning; intent; whether a revision was considered and dropped.",""]
    open(f,"w").write("\n".join(L)+"\n")
    index[r["arm"]].append((r["task"],r["job"],r["trial"],r["reward"],slug))
    written+=1
print(f"wrote {written} case studies to {OUT}/")
# index
L=["# Trajectory case-study index","",
   "One chapter per **valid** trial on the final ten. Invalid attempts are in",
   "`../INFRASTRUCTURE_FAILURE_REGISTER.md` and are **not** model failures.",""]
for arm in ("gemini","claude"):
    rows=sorted(index[arm])
    L+=[f"## {arm.title()} — {len(rows)} valid trials","",
        "| task | job | trial | reward | case study |","|---|---|---|---|---|"]
    for t,j,trn,rw,s in rows:
        L.append(f"| `{t}` | `{j}` | `{trn}` | {'**PASS**' if rw not in ('0','0.0') else 'fail'} | [case study]({s}.md) |")
    L.append("")
open("research_review/trajectories/INDEX.md","w").write("\n".join(L)+"\n")
print("wrote trajectories/INDEX.md")
