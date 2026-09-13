#!/usr/bin/env python3
"""Objective evidence-touch index for a Harbor ATIF trajectory (Task 01).

usage: evidence_touches.py <trajectory.json> [--json]

For each evidence item, lists the agent step ids whose tool-call ARGUMENTS reference it (file
paths read/listed/edited, or strings inside shell commands). This records what the agent
*touched*, not what it understood; interpretation is done by a human reviewer against the
timeline. Matching is case-insensitive on the patterns below.
"""
import argparse
import json
import re
from pathlib import Path

EVIDENCE = {
    "readme": r"workspace/README\.md|\bREADME\.md",
    "finance_tieout": r"close_tieout|reports/finance",
    "billing_revenue_export": r"billing_recognized_revenue",
    "revenue_policy": r"revenue_recognition_policy",
    "identity_standard": r"account_identity_standard",
    "data_dictionary": r"data_dictionary",
    "runbook": r"month_end_close_runbook",
    "announce_migration_wave": r"enterprise_contract_migration",
    "announce_price": r"growth_plan_list_price",
    "announce_fx": r"treasury_fx",
    "announce_sla": r"sla_credits|inc2291",
    "announce_realignment": r"territory_realignment",
    "deployments_log": r"deployments\.csv",
    "scheduler_log": r"revrec_runs\.csv",
    "pipeline_log": r"logs/pipeline",
    "changelog": r"CHANGELOG",
    "crm_export": r"crm_accounts_export",
    "migration_register": r"account_migrations",
    "billing_db": r"billing\.db",
    "warehouse_db": r"analytics\.db",
    "src_accounts": r"accounts\.py",
    "src_recognition": r"recognition\.py",
    "src_fx": r"revrec/fx\.py|\bfx\.py",
    "src_pipeline": r"pipeline\.py",
    "src_extract": r"extract\.py",
    "src_publish": r"publish\.py",
    "src_checks": r"checks\.py",
    "config_pipeline": r"pipeline\.toml",
    "config_dashboard": r"dashboard\.toml",
    "run_pipeline": r"-m revrec|revrec run",
    "sql_billing_accounts": r"billing_accounts",
    "mentions_duplicat": r"duplicat|drop_duplicates|\.duplicated\(",
    "mentions_cardinality": r"value_counts|groupby\(.*size|count\(\*\).*group by|having count|nunique|validate=",
    "mentions_successor": r"successor",
    "mentions_link_type": r"billing_link_type|legacy",
    "mentions_is_current": r"is_current",
    "mentions_july": r"2026-07",
    "mentions_august": r"2026-08",
}
WRITE_TOOLS = re.compile(r"write|replace|edit", re.I)


def args_text(tc) -> str:
    return json.dumps(tc.get("arguments") or {}, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trajectory", type=Path)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    traj = json.loads(a.trajectory.read_text())
    hits = {k: [] for k in EVIDENCE}
    writes, tools = [], {}
    for st in traj.get("steps", []):
        for tc in st.get("tool_calls") or []:
            fn = tc.get("function_name", "")
            tools[fn] = tools.get(fn, 0) + 1
            text = args_text(tc)
            for k, pat in EVIDENCE.items():
                if re.search(pat, text, re.I) and st["step_id"] not in hits[k]:
                    hits[k].append(st["step_id"])
            if WRITE_TOOLS.search(fn):
                path = (tc.get("arguments") or {}).get("file_path") or (tc.get("arguments") or {}).get("path")
                writes.append((st["step_id"], fn, path))
    n_agent = sum(1 for s in traj.get("steps", []) if s.get("source") == "agent")
    result = {"agent_steps": n_agent, "tool_counts": tools, "touches": hits, "file_writes": writes,
              "final_metrics": traj.get("final_metrics")}
    if a.json:
        print(json.dumps(result, indent=2))
        return
    print(f"agent steps: {n_agent}   tool calls: {tools}")
    for k, v in hits.items():
        print(f"  {k:26} {'first@'+str(v[0]) if v else '-':>10}  steps={v[:12]}{'…' if len(v) > 12 else ''}")
    print("file writes/edits:")
    for s, fn, p in writes:
        print(f"  step {s}: {fn} {p}")


if __name__ == "__main__":
    main()
