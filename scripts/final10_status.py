#!/usr/bin/env python3
"""Development funnel + final-suite status, generated from research/final10_development/ledger.json
and report/data/results.json. Read-only."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open(os.path.join(ROOT, "research", "final10_development", "ledger.json")))
C = L["concepts"]
n = lambda c: c.get("n_concepts", 1)
tot = sum(n(c) for c in C)
sim = sum(n(c) for c in C if c["stage"] in ("minimal_sim", "separation_gate", "counterexample", "built", "validated", "frozen", "baselined", "final"))
built = sum(n(c) for c in C if c.get("built"))
frozen = sum(n(c) for c in C if c.get("frozen"))
based = sum(n(c) for c in C if c.get("baseline"))
fin = [c for c in C if c.get("final")]
rej = [c for c in C if not c.get("built") and not c.get("final")]
print(f"concepts considered      {tot}")
print(f"  simulated / screened   {sim}")
print(f"  rejected pre-build     {sum(n(c) for c in rej)}")
print(f"tasks built              {built}")
print(f"tasks frozen             {frozen}")
print(f"tasks baselined          {based}")
print(f"excluded after baseline  {sum(1 for c in C if c.get('baseline') and not c.get('final'))}"
      f"  (F8: {sum(1 for c in C if c.get('f8'))})")
print(f"FINAL SUITE              {len(fin)}: {', '.join(c['id'] for c in fin)}")
p = os.path.join(ROOT, "report", "data", "results.json")
if os.path.exists(p):
    R = json.load(open(p)); f = R["final_summary"]
    print(f"\nmeasured: {f['successful_trials']}/{f['trials']} trials, "
          f"{f['tasks_with_pass3']}/{f['tasks']} tasks pass@3 = {100*f['task_pass_at_3']:.0f}%"
          f"  ({'OK' if f['task_pass_at_3'] < 0.30 else 'OVER'} vs 30% bar)")
    ids = set(R["final"]) ^ {c["id"] for c in fin}
    if ids:
        print(f"WARNING: ledger/final_tasks mismatch: {ids}")
