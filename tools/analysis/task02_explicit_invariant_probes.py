#!/usr/bin/env python3
"""Minimal-correction probes for the Task 02 explicit-invariant trials (analysis only; never applied to the task).
Each probe copies a trial's submitted src/, applies the named minimal edits, and re-runs task02_rerun_agent_code.py
against the visible and hidden extracts. Run from the repo root."""
import os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
J = Path("jobs/task02-gemini3flash-explicit-invariant")
def src_of(t): return next(p for p in (J / f"02-renewal-risk-regression__expl__{t}/artifacts").rglob("workspace") if (p/"src/renewal_risk").is_dir()) / "src"
def rep(p, o, n):
    s = p.read_text(); assert o in s, (p, o[:60]); p.write_text(s.replace(o, n, 1))
def make(t, fixes):
    d = Path(tempfile.mkdtemp()); tri = d / "trial"; ws = tri / "artifacts/workspace"
    shutil.copytree(src_of(t), ws / "src", ignore=shutil.ignore_patterns("__pycache__"))
    pkg = ws / "src/renewal_risk"
    for f in fixes: f(pkg)
    return tri
def no_ticket_filter(pkg):
    s = (pkg/"features/support.py").read_text()
    s2 = re.sub(r'\s*&\s*\(m\["synced_at"\] < m\["prediction_date"\]\)', '', s)
    s2 = re.sub(r'\n\s*m = m\[m\["synced_at"\] < m\["prediction_date"\]\]', '', s2)
    assert s2 != s; (pkg/"features/support.py").write_text(s2)
def t2_existence(pkg):
    p = pkg/"features/pipeline_signals.py"
    rep(p, '''    exists = ex_opp["synced_at"].notna() & (ex_opp["synced_at"] < ex_opp["prediction_date"])''',
        '''    _first = wh.opportunity_history.groupby("opportunity_id")["synced_at"].min()
    exists = ex_opp["opportunity_id"].map(_first).lt(ex_opp["prediction_date"]).fillna(False)''')
    rep(p, '''    opps_static = opps[opps["synced_at"] < examples["prediction_date"].max()][''', '''    opps_static = opps[[True] * len(opps)][''')
def t3_index(pkg):
    for f in ["features/health.py", "features/pipeline_signals.py"]:
        p = pkg / f; s = p.read_text()
        s = s.replace('''    ex = examples[["contract_id", "account_id", "prediction_date"]].sort_values("prediction_date")''',
                      '''    ex = examples[["contract_id", "account_id", "prediction_date"]].sort_values("prediction_date").reset_index()''')
        s = s.replace('''        val = m["new_value"]''', '''        val = m.set_index("index")["new_value"].reindex(examples.index)''')
        s = s.replace('''    renewal_cases = m[exists][["contract_id", "opportunity_id", "prediction_date"]].sort_values("prediction_date")''',
                      '''    renewal_cases = m[exists][["contract_id", "opportunity_id", "prediction_date"]].sort_values("prediction_date").reset_index()''')
        s = s.replace('''        val = res["new_value"] # Preserves index''', '''        val = res.set_index("index")["new_value"].reindex(m.index)''')
        p.write_text(s)
probes = {
  "j5oNxeF as submitted": ("j5oNxeF", []),
  "j5oNxeF - ticket synced_at filter removed": ("j5oNxeF", [no_ticket_filter]),
  "6LSZCFK - ticket filter removed": ("6LSZCFK", [no_ticket_filter]),
  "6LSZCFK - ticket filter removed + existence by first history load": ("6LSZCFK", [no_ticket_filter, t2_existence]),
  "95Q6LAG - ticket filter removed": ("95Q6LAG", [no_ticket_filter]),
  "95Q6LAG - ticket filter removed + merge_asof index alignment fixed": ("95Q6LAG", [no_ticket_filter, t3_index]),
}
for label, (t, fixes) in probes.items():
    tri = make(t, fixes)
    print("#####", label, flush=True)
    r = subprocess.run([sys.executable, "tools/analysis/task02_rerun_agent_code.py", str(tri)], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr[-800:], flush=True)
