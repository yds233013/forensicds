#!/usr/bin/env python3
"""Render a Harbor ATIF trajectory as a readable, step-numbered timeline.

usage: atif_timeline.py <trajectory.json> [--obs-chars N] [--msg-chars N] > timeline.txt

Each agent step prints: step id, timestamp, the agent's message/reasoning excerpt, every tool
call (function name + key arguments such as command or file path) and a truncated observation.
Nothing is summarized or inferred; this is a lossy *view* of the raw trajectory for review.
"""
import argparse
import json
import sys
from pathlib import Path


def text_of(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(p.get("text") or "" for p in content if isinstance(p, dict))
    return str(content)


def clip(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n] + f" …[+{len(s) - n} chars]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trajectory", type=Path)
    ap.add_argument("--obs-chars", type=int, default=900)
    ap.add_argument("--msg-chars", type=int, default=1200)
    args = ap.parse_args()
    traj = json.loads(args.trajectory.read_text())
    agent = traj.get("agent", {})
    print(f"# agent={agent.get('name')} {agent.get('version')} model={agent.get('model_name')} "
          f"steps={len(traj.get('steps', []))}")
    fm = traj.get("final_metrics") or {}
    print(f"# final_metrics: {json.dumps(fm)}\n")
    for st in traj.get("steps", []):
        sid, src, ts = st.get("step_id"), st.get("source"), (st.get("timestamp") or "")[:19]
        msg = text_of(st.get("message"))
        reasoning = st.get("reasoning_content") or ""
        print(f"=== step {sid} [{src}] {ts}")
        if src == "user" and msg:
            print(clip(msg, 400))
        if reasoning:
            print("  [reasoning] " + clip(reasoning, args.msg_chars).replace("\n", "\n  "))
        if src == "agent" and msg:
            print("  [message] " + clip(msg, args.msg_chars).replace("\n", "\n  "))
        results = {r.get("source_call_id"): r for r in ((st.get("observation") or {}).get("results") or [])}
        for tc in st.get("tool_calls") or []:
            a = tc.get("arguments") or {}
            key = {k: a[k] for k in ("command", "file_path", "absolute_path", "path", "dir_path", "pattern",
                                     "old_string", "new_string", "content", "description") if k in a}
            shown = {k: clip(str(v), 700) for k, v in (key or a).items()}
            print(f"  -> {tc.get('function_name')} {json.dumps(shown, ensure_ascii=False)}")
            r = results.pop(tc.get("tool_call_id"), None)
            if r is not None:
                print("     <- " + clip(text_of(r.get("content")), args.obs_chars).replace("\n", "\n        "))
        for r in results.values():
            print("     <- " + clip(text_of(r.get("content")), args.obs_chars).replace("\n", "\n        "))


if __name__ == "__main__":
    sys.exit(main())
