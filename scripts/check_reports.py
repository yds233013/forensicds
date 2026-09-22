#!/usr/bin/env python3
"""Summarise harbor check reports: per job, number of rubric criteria and any non-pass outcomes."""
import glob, json, sys

jobs = sys.argv[1:] or sorted({p.split("/")[1] for p in glob.glob("jobs/*/check_report.json") + glob.glob("jobs/*/*/check_report.json")})
for j in jobs:
    fs = glob.glob(f"jobs/{j}/check_report.json") + glob.glob(f"jobs/{j}/*/check_report.json")
    if not fs:
        print(f"{j:30s} NO REPORT"); continue
    r = json.load(open(fs[0]))
    for res in r.get("results", []):
        checks = res.get("checks", {})
        bad = {k: v.get("outcome") for k, v in checks.items() if v.get("outcome") not in ("pass", "not_applicable")}
        task = res.get("task_name") or res.get("task") or ""
        print(f"{j:30s} {str(task)[:40]:40s} criteria={len(checks):2d} non_pass={bad}")
