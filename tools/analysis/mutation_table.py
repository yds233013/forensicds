#!/usr/bin/env python3
"""Render a mutation-suite JSON report (tools/taskNN/shortcuts.py --report) as a Markdown table.

usage: mutation_table.py report/taskNN_mutations.json
"""
import json
import sys

rows = json.load(open(sys.argv[1]))
print("| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |")
print("|----------|--------------|---------:|-------:|------:|------:|-----------|")
for r in rows:
    vis = [f for f in r["failed"] if "hidden" not in f]
    hid = [f for f in r["failed"] if "hidden" in f]
    fixtures = sorted({f.split("[")[1].rstrip("]") for f in hid if "[" in f})
    caught = "—" if not r["failed"] else ("visible + " + "/".join(fixtures) if vis and hid else
                                          ("visible only" if vis else "hidden only: " + "/".join(fixtures)))
    print(f"| `{r['name']}` | {r['doc']} | {r['expected']} | **{r['reward']}** | {len(vis)} | {len(hid)} | {caught} |")
ok = sum(r["ok"] for r in rows)
print(f"\n{ok}/{len(rows)} cases as expected.")
