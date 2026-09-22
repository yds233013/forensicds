#!/usr/bin/env python3
"""Summarise every Harbor trial under jobs/ (read-only; never runs a model).

    python3 scripts/summarize_results.py [--jobs jobs] [--csv out.csv] [--model-only]

For each trial: task path, job, trial name, agent, model, reward, cost, exception, task checksum.
Job directories whose name contains 'INVALID' are reported but flagged invalid.
"""
from __future__ import annotations

import argparse, csv, glob, json, os, sys


def trials(jobs_dir):
    for p in sorted(glob.glob(os.path.join(jobs_dir, "*", "*", "result.json"))):
        job = p.split(os.sep)[-3]
        try:
            r = json.load(open(p))
        except Exception as e:                        # noqa: BLE001
            yield {"job": job, "trial": p.split(os.sep)[-2], "error": f"unreadable: {e}"}
            continue
        cfg = r.get("config", {}) or {}
        ag = (r.get("agent_info") or {}); ar = (r.get("agent_result") or {})
        vr = (r.get("verifier_result") or {}).get("rewards") or {}
        exc = r.get("exception_info")
        yield {"task": (cfg.get("task") or {}).get("path") or (r.get("task_id") or {}).get("path"),
               "job": job, "trial": r.get("trial_name"), "agent": ag.get("name"),
               "model": (ag.get("model_info") or {}).get("name"), "reward": vr.get("reward"),
               "cost_usd": ar.get("cost_usd"), "exception": (exc or {}).get("exception_type") if isinstance(exc, dict) else exc,
               "task_checksum": (r.get("task_checksum") or "")[:16], "invalid_job": "INVALID" in job,
               "started_at": r.get("started_at")}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--jobs", default="jobs"); ap.add_argument("--csv")
    ap.add_argument("--model-only", action="store_true"); a = ap.parse_args()
    rows = list(trials(a.jobs))
    if a.model_only:
        rows = [r for r in rows if r.get("agent") == "gemini-cli"]
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r})); w.writeheader(); w.writerows(rows)
    by = {}
    for r in rows:
        by.setdefault((r.get("task"), r.get("agent")), []).append(r)
    for (task, agent), rs in sorted(by.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        valid = [r for r in rs if not r.get("invalid_job") and r.get("exception") is None]
        rew = [r.get("reward") for r in valid]
        cost = sum((r.get("cost_usd") or 0) for r in rs)
        print(f"{str(task):52s} {str(agent):11s} trials={len(rs):2d} valid={len(valid):2d} "
              f"rewards={rew} cost=${cost:.4f} jobs={sorted({r['job'] for r in rs})}")


if __name__ == "__main__":
    main()
