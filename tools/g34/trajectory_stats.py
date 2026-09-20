"""Trajectory statistics for one G34 baseline trial.  Pure inspection; no model, no container.

    python tools/g34/trajectory_stats.py jobs/g34-gemini3flash-baseline-1
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

# Vocabulary that indicates the agent named the statistical object rather than stumbling onto it.
CONCEPT = {
    "competing_risks": r"competing[ _-]?risk",
    "cumulative_incidence": r"cumulative[ _-]?incidence|\bCIF\b|aalen|johansen",
    "kaplan_meier": r"kaplan[ _-]?meier|\bKM\b|life[ _-]?table",
    "censoring": r"censor",
    "crude_vs_net": r"crude[ _-]?risk|net[ _-]?risk",
    "telemetry_gap": r"telemetry|gap|outage|vibration",
    "cut_off": r"cut[ _-]?off|administrative",
}
DOCS = ["maintenance_sop", "event_dictionary", "aftermarket_planning_memo",
        "engineering_note", "analysis_contract", "installed_base_reliability", "README"]


def find_trial(job: Path):
    for d in sorted(job.iterdir()):
        if d.is_dir() and (d / "agent").exists():
            return d
    raise SystemExit("no trial dir")


def main(job_path):
    trial = find_trial(Path(job_path))
    d = json.loads((trial / "agent" / "trajectory.json").read_text())
    steps = d["steps"]
    blob = json.dumps(d).lower()

    src = Counter(s.get("source") for s in steps)
    tools = Counter()
    for s in steps:
        for tc in (s.get("tool_calls") or []):
            tools[tc.get("name") or tc.get("tool_name") or "?"] += 1

    print("=" * 70)
    print("trial        :", trial.name)
    print("agent        :", d["agent"]["name"], d["agent"]["version"], "/", d["agent"]["model_name"])
    print("steps        :", len(steps), dict(src))
    print("tool calls   :", sum(tools.values()), dict(tools))
    print("final_metrics:", json.dumps(d.get("final_metrics", {}))[:300])

    print("-" * 70)
    print("concept vocabulary present in the trajectory:")
    for name, pat in CONCEPT.items():
        n = len(re.findall(pat, blob, re.I))
        print("   %-22s %s (%d hits)" % (name, "YES" if n else "no", n))

    print("-" * 70)
    print("workspace documents referenced:")
    for doc in DOCS:
        n = blob.count(doc.lower())
        print("   %-34s %s (%d)" % (doc, "YES" if n else "no", n))


if __name__ == "__main__":
    main(sys.argv[1])
