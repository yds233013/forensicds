#!/usr/bin/env python3
"""Anti-gaming mutation suite for G08 (forecast accuracy under settlement vintages).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, runs the build,
then runs the real tests/test.sh (sandboxed pipeline). Correct implementations must score 1; natural wrong repairs,
partial repairs, patches, cheats and overfits must score 0. Overfits must additionally pass every visible-extract
check and fail only hidden-extract checks.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task [--workspace DIR] [--tools DIR]   (internal / dev)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/g08-forecast-accuracy-vintages"
WS = Path("/workspace")
TOOLS = HERE
AS_OF = "2026-09-22T06:00:00Z"


def install(src_name: str, variant: dict | None = None) -> None:
    src = (TOOLS / src_name).read_text()
    if variant is not None:
        src = src.replace("VARIANT: dict = {}", f"VARIANT: dict = {variant!r}", 1)
    (WS / "fcaccuracy/cli.py").write_text(src)


def install_variant(**variant) -> None:
    install("variant_mart.py", variant)


def oracle_files(mart=True, kpi=True) -> None:
    sol = TASK / "solution/fcaccuracy"
    if mart:
        shutil.copyfile(sol / "mart.py", WS / "fcaccuracy/mart.py")
    if kpi:
        shutil.copyfile(sol / "kpi.py", WS / "fcaccuracy/kpi.py")


def visible_facts() -> dict:
    con = sqlite3.connect(WS / "data/warehouse.sqlite")
    closes = dict(con.execute("SELECT kpi_month, closed_at FROM kpi_close_log"))
    memb = [tuple(r) for r in con.execute("SELECT portfolio, settlement_class, effective_from, effective_to FROM portfolio_membership")]
    con.close()
    return {"closes": closes, "membership": memb}


# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution (pandas repair of mart.py and kpi.py)."""
    oracle_files()


def alt_correct_plain_python():
    """Independent correct mart: plain Python over sqlite3 (variant pipeline with no switches)."""
    install_variant()


def alt_correct_sqlite_windows():
    """Independent correct mart: the vintage logic in one SQLite query with window functions."""
    install("alt_sqlite.py")


def alt_correct_event_replay():
    """Independent correct mart: chronological replay of status events and forecast issues."""
    install("alt_replay.py")


# ------------------------------------------------------------------------------------------------ natural wrong repairs (actual)


def actual_latest_current():
    """Actual = today's latest settlement run of any type (settled_volumes_latest); everything else correct."""
    install_variant(actual="latest_current")


def actual_first_published_estimate():
    """Actual = the first published volume (EST, next morning); everything else correct."""
    install_variant(actual="est_first")


def actual_is_current_status():
    """Actual = Initial Settlement run with current status 'published'; everything else correct."""
    install_variant(actual="is_current_status")


def actual_is_scheduled_run():
    """Actual = the scheduled Initial Settlement run (dedupe re-runs by reason); everything else correct."""
    install_variant(actual="is_scheduled")


def actual_latest_any_type_at_close():
    """Actual = latest run of any settlement type published and valid at the KPI close; everything else correct."""
    install_variant(actual="latest_any_at_close")


def actual_corrections_any_type():
    """Actual = IS at close, but any data-correction run valid at close overrides (R1/R2 corrections too)."""
    install_variant(actual="dc_any_type")


def actual_published_by_close_current_status():
    """Actual = IS published by the close whose current status is 'published' (status not reconstructed)."""
    install_variant(actual="is_pub_le_close_current_status")


def actual_latest_is_published_by_close():
    """Actual = latest IS published by the close, status ignored (withdrawal notices not checked)."""
    install_variant(actual="is_latest_published_by_close")


def actual_status_by_effective_time():
    """Actual = IS whose status at the close is reconstructed on effective_from (settlement effect) instead of recorded_at."""
    install_variant(actual="status_by_effective_time")


def actual_loaded_at_as_knowledge_time():
    """Actual = IS valid at close, but knowledge time taken from warehouse loaded_at."""
    install_variant(actual="loaded_at")


def actual_one_global_cutoff():
    """Actual = IS as it stood at --as-of, for every month (one global vintage)."""
    install_variant(actual="is_at_asof")


def actual_at_forecast_creation():
    """Actual = IS as known when the forecast was issued (targets frozen at forecast creation)."""
    install_variant(actual="at_forecast_creation")


def drop_revised_periods():
    """Days with any Initial Settlement re-run or correction are treated as unsettled; everything else correct."""
    install_variant(drop_revised=True)


def unsettled_fallback_to_latest():
    """Forecasts without a charge basis at close are scored against today's latest settled volume."""
    install_variant(unsettled="fallback_latest")


def unsettled_dropped():
    """Forecasts without a charge basis at close are dropped instead of reported as unsettled."""
    install_variant(unsettled="drop")


# ------------------------------------------------------------------------------------------------ natural wrong repairs (forecast / grain / KPI)


def forecast_latest_issue():
    """Forecast = latest issue for the run day (post-gate re-issues included); everything else correct."""
    install_variant(gate="none")


def forecast_gate_in_utc():
    """Forecast = latest issue before 11:00 UTC (gate not converted from UK time); everything else correct."""
    install_variant(gate="utc")


def forecast_issue_grain_lock():
    """Forecast = values of the latest pre-gate issue for the run day only (scoped re-issues drop other regions)."""
    install_variant(lock_grain="issue")


def forecast_scheduled_only():
    """Forecast = the 06:00 scheduled issue only; everything else correct."""
    install_variant(gate="scheduled_only")


def mapping_current_dimension():
    """Portfolio classes from the current dim_portfolio; everything else correct."""
    install_variant(mapping="current")


def mapping_by_run_date():
    """Portfolio classes effective on the forecast run day instead of the delivery day; everything else correct."""
    install_variant(mapping="run_date")


def kpi_month_by_run_date():
    """KPI month (and close) from the forecast run month; everything else correct."""
    install_variant(kpi_month="run")


def head_to_head_production_periods():
    """Examples and KPI correct; head-to-head over each model's production period instead of common forecasts."""
    install_variant(pairing="production_periods")


# ------------------------------------------------------------------------------------------------ partial repairs and patches


def partial_actuals_only():
    """Partial: charge basis at close fixed; forecast selection, mapping, KPI month and comparison as deployed."""
    install_variant(gate="none", lock_grain="issue", mapping="current", kpi_month="run", pairing="production_periods")


def partial_actuals_and_forecasts():
    """Partial: charge basis and forecast lock fixed; current portfolio mapping and run-month KPI remain."""
    install_variant(mapping="current", kpi_month="run", pairing="production_periods")


def partial_everything_but_mapping():
    """Partial: all fixed except portfolio mapping (current dimension)."""
    install_variant(mapping="current")


def metric_only_patch():
    """Patch: KPI aggregation and head-to-head repaired (oracle kpi.py); examples still built by the deployed query."""
    oracle_files(mart=False, kpi=True)


def output_only_patch():
    """Patch: run a correct build once, then restore the deployed code (outputs are regenerated by the verifier)."""
    oracle_files()
    subprocess.run([sys.executable, "-m", "fcaccuracy", "build", "--as-of", AS_OF], cwd=WS, check=True, capture_output=True)
    shutil.copyfile(TASK / "environment/workspace/fcaccuracy/mart.py", WS / "fcaccuracy/mart.py")
    shutil.copyfile(TASK / "environment/workspace/fcaccuracy/kpi.py", WS / "fcaccuracy/kpi.py")


def warehouse_edit():
    """Cheat: correct code, but reconciliation runs are deleted from data/warehouse.sqlite first."""
    oracle_files()
    con = sqlite3.connect(WS / "data/warehouse.sqlite")
    con.execute("DELETE FROM settlement_volumes WHERE run_id IN (SELECT run_id FROM settlement_runs WHERE run_type IN ('R1','R2','RF','DF'))")
    con.execute("DELETE FROM settlement_runs WHERE run_type IN ('R1','R2','RF','DF')")
    con.commit()
    con.close()


def import_verifier_reference():
    """Cheat: the mart returns the verifier's hidden reference if it can import it; otherwise the deployed semantics."""
    install_variant(actual="latest_current", gate="none", lock_grain="issue", mapping="current", kpi_month="run",
                    pairing="production_periods", unsettled="drop")
    cli = WS / "fcaccuracy/cli.py"
    s = cli.read_text()
    s = s.replace("def compute(db: Path, as_of: str) -> dict:\n", '''def compute(db: Path, as_of: str) -> dict:
    import os, sys
    for d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if d and os.path.exists(os.path.join(d, "reference.py")):
                sys.path.insert(0, d)
                import reference
                res = reference.expected(db, as_of)
                res["as_of"] = as_of
                return res
        except Exception:
            pass
''', 1)
    cli.write_text(s)


# ------------------------------------------------------------------------------------------------ overfits (visible pass, hidden fail)


def overfit_hardcoded_close_timestamps():
    """Correct logic, but KPI close instants hard-coded from this extract's close log."""
    install_variant(hardcoded_closes=visible_facts()["closes"])


def overfit_hardcoded_portfolio_membership():
    """Correct logic, but portfolio membership hard-coded from this extract."""
    install_variant(hardcoded_membership=visible_facts()["membership"])


def overfit_hardcoded_model_pair():
    """Correct logic, but only models v3 and v4 are evaluated."""
    install_variant(hardcoded_models=["v3", "v4"])


def overfit_hardcoded_horizons():
    """Correct logic, but only horizons 1..7 are evaluated."""
    install_variant(hardcoded_horizons=[1, 2, 3, 4, 5, 6, 7])


def overfit_hardcoded_as_of():
    """Correct logic, but the as-of instant is fixed to this extract's."""
    install_variant(hardcoded_as_of=AS_OF)


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_plain_python, 1), (alt_correct_sqlite_windows, 1),
            (alt_correct_event_replay, 1)]
WRONG = [actual_latest_current, actual_first_published_estimate, actual_is_current_status, actual_is_scheduled_run,
         actual_latest_any_type_at_close, actual_corrections_any_type, actual_published_by_close_current_status,
         actual_latest_is_published_by_close, actual_status_by_effective_time, actual_loaded_at_as_knowledge_time, actual_one_global_cutoff,
         actual_at_forecast_creation, drop_revised_periods, unsettled_fallback_to_latest, unsettled_dropped,
         forecast_latest_issue, forecast_gate_in_utc, forecast_issue_grain_lock, forecast_scheduled_only,
         mapping_current_dimension, mapping_by_run_date, kpi_month_by_run_date, head_to_head_production_periods,
         partial_actuals_only, partial_actuals_and_forecasts, partial_everything_but_mapping, metric_only_patch,
         output_only_patch, warehouse_edit, import_verifier_reference]
OVERFITS = [overfit_hardcoded_close_timestamps, overfit_hardcoded_portfolio_membership, overfit_hardcoded_model_pair,
            overfit_hardcoded_horizons, overfit_hardcoded_as_of]
PLAN = CONTROLS + [(f, 0) for f in WRONG] + [(f, "overfit") for f in OVERFITS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task --tools /tools; "
        "find /workspace -name __pycache__ -prune -exec rm -rf {} +; "
        f"(cd /workspace && python -m fcaccuracy build --as-of {AS_OF} > /tmp/agent_run.log 2>&1 || true); "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '[0-9]+ (passed|failed)' /tmp/verifier.log | tail -1; grep -E '^(FAILED|PASSED)' /tmp/verifier.log || true"
    )
    p = subprocess.run(["docker", "run", "--rm", "--cpus", "2", "--memory", "4g", "-v", f"{TASK}:/task:ro", "-v", f"{HERE}:/tools:ro",
                        image, "bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", p.stdout)
    reward = int(m.group(1)) if m else -1
    summary = next((l.strip("= ") for l in p.stdout.splitlines() if " passed" in l or " failed" in l), p.stderr[-400:])
    failed = re.findall(r"FAILED \S+::(\S+)", p.stdout)
    if expected == "overfit":
        ok = reward == 0 and failed and all(t.startswith("test_hidden_") for t in failed)
    else:
        ok = reward == expected
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward, ok=bool(ok),
                summary=summary, failed=failed)


def main():
    global TASK, WS, TOOLS
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker")
    ap.add_argument("--apply")
    ap.add_argument("--task")
    ap.add_argument("--workspace")
    ap.add_argument("--tools")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.workspace:
        WS = Path(a.workspace)
    if a.tools:
        TOOLS = Path(a.tools)
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:44} reward={r['reward']} expected={r['expected']}  {r['summary']}"
                  f"  failed={','.join(r['failed'][:6])}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
