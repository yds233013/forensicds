"""Readable dump of a prospective trial's trajectory for the frozen trajectory analysis.

    python tools/bench/read_trajectory.py <trial-dir> [--full]

Prints the ordered steps with the tool calls, the commands and the model's own text, truncated unless --full.
Read-only; changes nothing.
"""
import json
import sys
import pathlib


def short(s, n=700):
    s = str(s).replace("\n", "\n    ")
    return s if len(s) <= n else s[:n] + f" …[+{len(s)-n} chars]"


def main(d, full=False):
    p = pathlib.Path(d) / "agent" / "trajectory.json"
    t = json.load(open(p))
    steps = t.get("steps") or []
    print(f"# {d}")
    print(f"# agent={t.get('agent')} session={t.get('session_id')} steps={len(steps)}")
    fm = t.get("final_metrics") or {}
    if fm:
        print(f"# final_metrics: {json.dumps(fm)[:400]}")
    print()
    lim = 100000 if full else 1400
    for i, s in enumerate(steps, 1):
        kind = s.get("type") or s.get("role") or "?"
        print(f"--- step {i} [{kind}]")
        for k in ("text", "content", "thought", "message"):
            if s.get(k):
                print(f"  {k}: {short(s[k], lim)}")
        for k in ("tool", "tool_name", "name"):
            if s.get(k):
                print(f"  tool: {s[k]}")
        for k in ("args", "arguments", "input", "command"):
            if s.get(k):
                print(f"  {k}: {short(s[k], lim)}")
        for k in ("result", "output", "response", "observation"):
            if s.get(k):
                print(f"  {k}: {short(s[k], lim)}")
        extra = {k: v for k, v in s.items()
                 if k not in ("type", "role", "text", "content", "thought", "message", "tool", "tool_name",
                              "name", "args", "arguments", "input", "command", "result", "output", "response",
                              "observation")}
        if extra:
            print(f"  other: {short(json.dumps(extra, default=str), 300)}")


if __name__ == "__main__":
    main(sys.argv[1], "--full" in sys.argv)
