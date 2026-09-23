"""Readable dump of a Harbor trajectory for the scientific audit (read-only).

usage: python tools/audit/dump_trajectory.py <trial_dir> [--full] [--max-obs N]

Prints, per step: the agent's reasoning, its tool calls (command / file / query), and a truncated
observation. Designed so a reviewer can follow the scientific reasoning without reading raw JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def brief(x, n):
    s = x if isinstance(x, str) else json.dumps(x, default=str)
    s = s.replace("\\n", "\n")
    return s if len(s) <= n else s[:n] + f" …[{len(s)-n} more chars]"


def main():
    d = Path(sys.argv[1])
    full = "--full" in sys.argv
    max_obs = 900 if full else 420
    max_reason = 4000 if full else 1500
    traj = d / "agent" / "trajectory.json"
    if not traj.exists():
        traj = next(d.glob("*/agent/trajectory.json"), None)
    t = json.loads(Path(traj).read_text())
    print(f"### {traj}")
    fm = t.get("final_metrics") or {}
    print(f"### steps={len(t['steps'])} metrics={json.dumps(fm)[:300]}")
    for s in t["steps"]:
        src = s.get("source")
        if src == "user" and s.get("step_id") == "1":
            print("\n=== TASK INSTRUCTION ===\n" + brief(s.get("message", ""), 3000))
            continue
        if src != "agent":
            continue
        r = (s.get("reasoning_content") or "").strip()
        m = (s.get("message") or "").strip()
        tc = s.get("tool_calls")
        obs = s.get("observation")
        if not (r or m or tc):
            continue
        print(f"\n--- step {s.get('step_id')} ---")
        if r:
            print("REASONING: " + brief(r, max_reason))
        if m:
            print("SAYS: " + brief(m, 2500))
        if tc:
            try:
                calls = tc if isinstance(tc, list) else json.loads(tc.replace("'", '"'))
            except Exception:
                calls = None
            if calls:
                for c in calls:
                    fn = c.get("function_name")
                    args = c.get("arguments")
                    print(f"CALL {fn}: " + brief(args, 700))
            else:
                print("CALL: " + brief(tc, 700))
        if obs:
            print("OBS: " + brief(obs, max_obs))


if __name__ == "__main__":
    main()
