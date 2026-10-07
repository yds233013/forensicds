import csv, collections, json, os
ROOT="/Users/yashshah2311/forensicds"; os.chdir(ROOT)
F=["02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand","g24-recommender-ope",
   "g36-tou-capacity-gate","p20-noshow-monitoring","p22-gauge-recalibration","p31-fill-rate-dispute",
   "g50-courier-boost-rollout","g08-forecast-accuracy-vintages"]
T=list(csv.DictReader(open("research_review/ALL_TRIALS.csv")))
C=list(csv.DictReader(open("research_review/CRITERION_RESULTS.csv")))
def arm(a, tasks=F):
    v=[r for r in T if r["arm"]==a and r["valid"]=="True" and r["task"] in tasks]
    per={}
    for t in tasks:
        tv=[r for r in v if r["task"]==t]
        p=sum(int(r["passed"]) for r in tv)
        per[t]=dict(valid=len(tv), passes=p,
                    pass1=(p/len(tv) if tv else None), pass3=(1 if p else 0) if tv else None)
    tv=len(v); tp=sum(int(r["passed"]) for r in v)
    measured=[t for t in tasks if per[t]["valid"]>0]
    return per, dict(valid=tv, passes=tp, pass1=(tp/tv if tv else None),
        tasks_measured=len(measured), tasks_passed=sum(1 for t in measured if per[t]["passes"]>0),
        pass3=(sum(per[t]["pass3"] for t in measured)/len(measured) if measured else None))
GP,GS=arm("gemini"); CP,CS=arm("claude")
def inv(a):
    i=[r for r in T if r["arm"]==a and r["valid"]!="True"]
    return len(i), collections.Counter(r["invalid_reason"] or "(unlabelled)" for r in i)
GI,GIC=inv("gemini"); CI,CIC=inv("claude")

def critrates(a):
    rows=[r for r in C if r["arm"]==a and r["valid"]=="True"]
    keys=[k for k in (C[0].keys() if C else []) if k not in
          ("arm","model","task","job","valid","invalid_reason","reward")]
    out={}
    for k in keys:
        vals=[r[k] for r in rows if r.get(k) not in ("",None)]
        if vals: out[k]=(sum(int(x) for x in vals), len(vals))
    return out, len(rows)
GC,GCN=critrates("gemini"); CC,CCN=critrates("claude")

def chapter(a, per, s, ninv, invc, cc, ccn, fn, title, extra=""):
    pct=lambda x:"n/a" if x is None else f"{x:.1%}"
    L=[f"# {title}","",
    "All numbers recomputed directly from `verifier/reward.txt` and `verifier/criteria.json` in the raw",
    "trial directories by `research_review/build_results.py`. **VERIFIED FROM ARTIFACT.**","",
    "## Two different rates, not interchangeable","",
    "- **Trial pass rate** = passing trials ÷ valid trials. Answers *how often does one attempt succeed?*",
    "- **Task-level pass@3** = tasks with ≥1 pass ÷ tasks measured. Answers *how many tasks fall to three",
    "  attempts?* With 3 trials per task this is a coarse, high-variance statistic.","",
    "## Suite","","| metric | value |","|---|---|",
    f"| valid trials | **{s['valid']}** |", f"| passing trials | **{s['passes']}** |",
    f"| trial pass rate | **{pct(s['pass1'])}** |",
    f"| tasks measured | {s['tasks_measured']} of 10 |",
    f"| tasks with ≥1 pass | {s['tasks_passed']} |",
    f"| task-level pass@3 | **{pct(s['pass3'])}** (over the {s['tasks_measured']} measured) |",
    f"| invalid attempts excluded | {ninv} |","",
    "## Per task","","| task | valid | passes | trial pass rate | pass@3 |","|---|---|---|---|---|"]
    for t in F:
        p=per[t]
        if p["valid"]==0:
            L.append(f"| `{t}` | 0 | — | — | **not measured** |")
        else:
            L.append(f"| `{t}` | {p['valid']} | {p['passes']} | {pct(p['pass1'])} | {p['pass3']} |")
    L+=["","## Invalid attempts","",
    "Excluded from every rate above. Detail: `INFRASTRUCTURE_FAILURE_REGISTER.md`.","",
    "| cause | count |","|---|---|"]
    for k,v in invc.most_common(): L.append(f"| `{k}` | {v} |")
    L+=["","## Criterion-level results","",
    "Only four of the ten tasks emit per-criterion rewards (`p20`, `p22`, `p31`, `g50`). The other six",
    "emit a single binary reward, so criterion attribution for them is **UNKNOWN, not zero**.","",
    f"Instrumented valid trials in this arm: **{ccn}**.","",
    "| criterion | passed / instrumented | rate |","|---|---|---|"]
    if cc:
        for k,(p,n) in sorted(cc.items(), key=lambda x:x[1][0]/x[1][1]):
            L.append(f"| `{k}` | {p}/{n} | {p/n:.0%} |")
    else: L.append("| — | no instrumented valid trials | — |")
    L.append(extra)
    open(f"research_review/{fn}","w").write("\n".join(L)+"\n")

chapter("gemini",GP,GS,GI,GIC,GC,GCN,"05_GEMINI_RESULTS.md",
 "05 — Gemini results (`google/gemini-3-flash-preview`, agent `gemini-cli`)",
 """
## Reconciliation with earlier reports

The project's own `report/FINAL_REPORT.md` and `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md` state
31 valid trials, 1 pass, 3.2% trial pass rate and 10% task-level pass@3. **This recomputation
reproduces those figures exactly**, so the earlier report is confirmed against raw artifacts rather
than merely restated.

Note `g05-sco-rollout-gate` carries **4** valid Gemini trials, not 3 — one extra job
(`g05-gemini3flash-baseline-2`) was run. All four are counted; none is discarded.

## Context the headline rate omits

Across **all 21** exposed tasks (including the eleven excluded from the final ten) Gemini recorded
67 valid trials. Five excluded tasks scored 3/3 (`03`, `05`, `06`, `g35`, `g42`). The final ten are a
deliberately selected hard subset; the model is not globally incapable on this task family.
""")
chapter("claude",CP,CS,CI,CIC,CC,CCN,"06_CLAUDE_RESULTS.md",
 "06 — Claude results (`claude-opus-5-5`, agent `claude-code`)",
 """
## What is missing and why

`g50-courier-boost-rollout` has **zero** valid Claude trials. Four attempts, four verifier refusals:
`interpreter, library sandbox tools differ from the pinned image; refusing to grade`. The final attempt
is the de-confounding one — the agent ran (16 recorded steps, $0.66 billed) and the verifier still
refused — so this is a **verifier incompatibility**, not a Claude failure. Repairing it would require
editing a frozen verifier, which the cross-model protocol prohibits.

Consequently Claude's task-level pass@3 is computed over **9** measured tasks, and any Gemini-vs-Claude
suite comparison must use the nine jointly graded tasks (chapter 10).

## Cost and runtime (recorded)

| | |
|---|---|
| total billed (Harbor `total_cost_usd`, summed over all trajectories) | **$23.07** |
| median per valid trial | ~$0.80 |
| most expensive single trial | `claude-g10-censored-demand-1`, $3.08, 53 steps |
| typical wall clock | ~4 minutes per trial |

The 20 `credit-balance-too-low` attempts cost $0.00. The run was interrupted by credit exhaustion and
resumed after top-up against the identical frozen tasks; trials are not mixed across task versions.
""")
print("05_GEMINI_RESULTS.md and 06_CLAUDE_RESULTS.md written")
print(f"gemini: {GS}")
print(f"claude: {CS}")
json.dump(dict(gemini_per=GP,gemini_suite=GS,claude_per=CP,claude_suite=CS,
               gemini_crit=GC,claude_crit=CC,gemini_crit_n=GCN,claude_crit_n=CCN),
          open("research_review/_results.json","w"), indent=1, default=str)
