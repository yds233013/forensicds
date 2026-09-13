#!/usr/bin/env python3
"""Objective evidence for a Task 02 trial: evidence-touch index from the ATIF trajectory, plus a diff of
the final /workspace artifact against the frozen task workspace and a warehouse integrity digest.

usage: task02_evidence.py <trial_dir>
Writes <trial_dir>/analysis/{touches.json, diff.patch, changed_files.txt, integrity.json} and prints a summary.
Touches record what tool-call arguments referenced (files read, strings in commands), not understanding.
"""
import difflib
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "candidates/02-renewal-risk-regression"
ORIG = TASK / "environment/workspace"
GENERATED = ("data/", "artifacts/", "reports/", "notes/", "logs/training")

PATTERNS = {
    "instruction_notes_sales": r"notes/sales",
    "monitoring": r"reports/monitoring|live_performance|production_scores",
    "eval_reports": r"model_evaluation|eval_20",
    "readme": r"README",
    "model_card": r"model_card",
    "feature_dictionary": r"feature_dictionary",
    "data_dictionary": r"warehouse_data_dictionary",
    "crm_v3_migration_note": r"crm_v3_migration",
    "inc1874_note": r"inc1874",
    "runbook": r"retraining_runbook",
    "experiment_note": r"notes/experiments|v2\.4_retrain",
    "changelog": r"CHANGELOG",
    "deployments": r"deployments\.csv",
    "scheduler_log": r"training_runs\.csv",
    "config": r"pipeline\.toml",
    "src_warehouse": r"sources/warehouse\.py|warehouse\.py",
    "src_pipeline_signals": r"pipeline_signals",
    "src_health": r"features/health|health\.py",
    "src_examples": r"examples\.py",
    "src_usage_support_contract": r"usage\.py|support\.py|contract\.py",
    "src_train_eval": r"train\.py|evaluate\.py|transforms\.py",
    "src_scoring": r"scoring\.py",
    "tbl_crm_opportunities": r"crm_opportunities\b",
    "tbl_opp_history": r"crm_opportunity_field_history",
    "tbl_cs_health": r"cs_account_health\b",
    "tbl_health_history": r"cs_account_health_history",
    "tbl_sync_log": r"warehouse_sync_log",
    "mentions_synced_at": r"synced_at",
    "mentions_changed_at": r"changed_at",
    "mentions_lead_source_partner": r"lead_source|partner",
    "mentions_expansion": r"expansion",
    "mentions_class_weight": r"class_weight",
    "mentions_merge_asof": r"merge_asof",
    "run_pipeline": r"-m renewal_risk run|renewal_risk run",
    "run_features_only": r"renewal_risk features",
    "run_score": r"renewal_risk score",
    "leak_words": r"leak|point.in.time|as.of|future|lookahead|look-ahead",
    "hardcoded_dates_2025_11": r"2025-11-0[3-9]|2025-11-1[0-8]",
}


def text_of(c):
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    return "\n".join(p.get("text") or "" for p in c if isinstance(p, dict))


def touches(traj: dict) -> dict:
    hits = {k: [] for k in PATTERNS}
    writes, tools = [], {}
    for st in traj.get("steps", []):
        for tc in st.get("tool_calls") or []:
            fn = tc.get("function_name", "")
            tools[fn] = tools.get(fn, 0) + 1
            a = json.dumps(tc.get("arguments") or {}, ensure_ascii=False)
            for k, pat in PATTERNS.items():
                if re.search(pat, a, re.I) and st["step_id"] not in hits[k]:
                    hits[k].append(st["step_id"])
            if re.search(r"write|replace|edit", fn, re.I):
                args = tc.get("arguments") or {}
                writes.append((st["step_id"], fn, args.get("file_path") or args.get("path")))
    return dict(agent_steps=sum(1 for s in traj["steps"] if s.get("source") == "agent"), tools=tools, touches=hits,
                file_writes=writes, final_metrics=traj.get("final_metrics"))


def files(base: Path) -> dict:
    return {p.relative_to(base).as_posix(): p for p in base.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and not p.relative_to(base).as_posix().startswith(GENERATED)
            and p.suffix not in (".pyc", ".db", ".joblib")}


def main():
    trial = Path(sys.argv[1])
    out = trial / "analysis"
    out.mkdir(exist_ok=True)
    traj = json.loads((trial / "agent/trajectory.json").read_text())
    t = touches(traj)
    (out / "touches.json").write_text(json.dumps(t, indent=2))

    ws = next(p for p in (trial / "artifacts").rglob("workspace") if (p / "src/renewal_risk").is_dir())
    before, after = files(ORIG), files(ws)
    lines, changed = [], []
    for rel in sorted(set(before) | set(after)):
        b = before[rel].read_text(errors="replace").splitlines(keepends=True) if rel in before else []
        a = after[rel].read_text(errors="replace").splitlines(keepends=True) if rel in after else []
        if a != b:
            changed.append(("added" if rel not in before else "removed" if rel not in after else "modified", rel))
            lines.extend(difflib.unified_diff(b, a, f"a/{rel}", f"b/{rel}"))
    (out / "diff.patch").write_text("".join(lines))
    (out / "changed_files.txt").write_text("\n".join(f"{s}\t{r}" for s, r in changed) + "\n")

    sys.path.insert(0, str(TASK / "tests"))
    import world
    pristine = Path(tempfile.mkdtemp())
    world.build(world.VISIBLE_SPEC, pristine)
    same = world.sqlite_logical_digest(ws / "data/warehouse.db") == world.sqlite_logical_digest(pristine / "data/warehouse.db")
    (out / "integrity.json").write_text(json.dumps({"warehouse_unmodified": same}))

    print(f"agent steps {t['agent_steps']}  tools {t['tools']}")
    for k, v in t["touches"].items():
        print(f"  {k:30} {('first@' + str(v[0])) if v else '-':>10}  {v[:10]}")
    print("file writes:", t["file_writes"])
    print("changed files:", changed)
    print("warehouse unmodified:", same)


if __name__ == "__main__":
    main()
