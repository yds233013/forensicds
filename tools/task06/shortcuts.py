#!/usr/bin/env python3
"""Anti-gaming mutation suite for Task 06 (usage statement close).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, runs the close job,
then runs the real tests/test.sh (sandboxed pipeline). Shortcuts and overfits must score 0; independently written
correct repairs must score 1.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task [--workspace DIR] [--tools DIR]   (internal / dev)
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/06-usage-statement-close"
WS = Path("/workspace")
TOOLS = HERE


def install_variant(**variant) -> None:
    src = (TOOLS / "variant_pipeline.py").read_text()
    src = src.replace("VARIANT: dict = {}", f"VARIANT: dict = {variant!r}", 1)
    (WS / "jobs/close_month.py").write_text(src)


def oracle_files(normalize=True, mart=True, assemble=True) -> None:
    sol = TASK / "solution"
    if normalize:
        shutil.copyfile(sol / "metering/normalize.py", WS / "metering/normalize.py")
    if mart:
        shutil.copyfile(sol / "metering/usage_mart.py", WS / "metering/usage_mart.py")
    if assemble:
        shutil.copyfile(sol / "statements/assemble.py", WS / "statements/assemble.py")
        shutil.copyfile(sol / "statements/ledger.py", WS / "statements/ledger.py")
        subprocess.run([sys.executable, str(sol / "jobs_close_month.patch.py"), str(WS)], check=True)


# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution (all three components)."""
    oracle_files()


def alt_correct_plain_python():
    """Independent correct close: plain-Python fold over deliveries, no pandas."""
    install_variant()


def alt_correct_sqlite():
    """Independent correct close: SQLite window functions for record identity, current revision and billed totals."""
    shutil.copyfile(TOOLS / "alt_sqlite.py", WS / "jobs/close_month.py")


# ------------------------------------------------------------------------------------------------ shortcuts


def event_time_only():
    """Bill all September usage in the extract by event month (records fixed); no close cutoff, no adjustments."""
    install_variant(cutoff="extract", adjustments="none")


def processing_time_dedupe_fixed():
    """Keep receipt-window statements (the ADR design) but fix record identity: redeliveries and revisions handled."""
    install_variant(cutoff="receipt_window", mart="received")


def dedupe_all_by_event_id():
    """Treat every later delivery of an event id as a redelivery (keep the first received); everything else correct."""
    install_variant(dedupe="event_first")


def sum_all_deliveries():
    """No redelivery handling: every delivery counts; everything else correct."""
    install_variant(dedupe="none", current="sum_all")


def ignore_corrections():
    """Replays removed, but corrections and voids ignored (first revision is kept)."""
    install_variant(current="first_rev")


def latest_received_revision():
    """Current record = the revision received last (not the highest rev)."""
    install_variant(current="last_received")


def window_end_attribution():
    """Usage attributed to the month of window_end."""
    install_variant(attribution="window_end")


def no_adjustments():
    """Correct September usage lines; earlier months are not adjusted."""
    install_variant(adjustments="none")


def adjustments_at_statement_rates():
    """Adjustments rated with the statement month's rate card instead of the service month's."""
    install_variant(adjustments="statement_rates")


def adjustments_linear():
    """Adjustments priced linearly at the service month's Tier 1 rate (ignores allowance and tiers)."""
    install_variant(adjustments="linear")


def adjustments_from_extract_knowledge():
    """Adjustments computed from all records in the extract (ignores the close for earlier months)."""
    install_variant(adjust_knowledge="extract")


def adjust_against_usage_lines_only():
    """Billed-to-date taken from issued usage lines only (earlier adjustment lines ignored)."""
    install_variant(billed="usage_lines_only")


def reissue_prior_months():
    """Rebill July and August as fresh usage lines at close knowledge instead of adjusting what was billed."""
    install_variant(adjustments="reissue")


def mart_left_on_receipt_month():
    """Statement correct, but the usage mart still groups by receipt month."""
    install_variant(mart="received")


def fix_normalize_only():
    """Partial fix: record identity only (oracle normalize), mart and statement unchanged."""
    oracle_files(mart=False, assemble=False)


def fix_statement_only():
    """Partial fix: statement assembly and ledger (oracle), but the 24 h redelivery filter and receipt-month mart remain."""
    oracle_files(normalize=False, mart=False, assemble=True)
    nz = WS / "metering/normalize.py"
    sol = (TASK / "solution/metering/normalize.py").read_text()
    helper = sol[sol.index("def current_records"):]
    nz.write_text(nz.read_text() + "\n\n" + helper)


def fix_normalize_and_mart_only():
    """Partial fix: record identity and event-month mart (oracle), statement still assembled from receipt windows."""
    oracle_files(assemble=False)


def northwind_manual_credit():
    """Symptom patch: current pipeline plus hand-computed credits for Northwind's August overage."""
    (WS / "jobs/close_month.py").write_text((WS / "jobs/close_month.py").read_text().replace(
        "    lines = assemble_statement(usage, cards, args.month, close_hours)\n",
        "    lines = assemble_statement(usage, cards, args.month, close_hours)\n"
        "    import pandas as _pd\n"
        "    lines = _pd.concat([lines, _pd.DataFrame([\n"
        "        [args.month, 'cus_northwind', 'api_requests_k', 'adjustment', '2026-08', '-6408.552', '-497.60'],\n"
        "        [args.month, 'cus_northwind', 'compute_credits', 'adjustment', '2026-08', '-454.241', '-678.70']],\n"
        "        columns=lines.columns)], ignore_index=True)\n"))


def output_only_patch():
    """Run a correct close once, then leave the original job in place (outputs are regenerated by the verifier)."""
    oracle_files()
    subprocess.run([sys.executable, "-m", "jobs.close_month", "--month", "2026-09"], cwd=WS, check=True,
                   capture_output=True)
    shutil.copyfile(TASK / "environment/workspace/metering/normalize.py", WS / "metering/normalize.py")
    shutil.copyfile(TASK / "environment/workspace/metering/usage_mart.py", WS / "metering/usage_mart.py")
    shutil.copyfile(TASK / "environment/workspace/statements/assemble.py", WS / "statements/assemble.py")
    shutil.copyfile(TASK / "environment/workspace/jobs/close_month.py", WS / "jobs/close_month.py")


def source_data_mutation():
    """Correct code, but repeated deliveries are deleted from raw/landing first."""
    oracle_files()
    seen = set()
    for part in sorted((WS / "raw/landing").glob("received_date=*/*.jsonl.gz")):
        keep = []
        with gzip.open(part, "rt") as fh:
            for line in fh:
                r = json.loads(line)["record"]
                k = (r["event_id"], r["rev"])
                if k in seen:
                    continue
                seen.add(k)
                keep.append(line)
        with gzip.open(part, "wt") as fh:
            fh.writelines(keep)


# ------------------------------------------------------------------------------------------------ overfits


def overfit_record_last_receipt():
    """Repeated deliveries collapsed keeping the most recent receipt (a record resent after the close drops out of it)."""
    install_variant(dedupe="record_last")


def overfit_close_boundary_inclusive():
    """Records received exactly at the close counted in the closing statement (received_at <= close)."""
    install_variant(close_inclusive=True)


def overfit_hardcoded_close_times():
    """Close cutoffs hard-coded for the months in this extract (other months fall back to the calendar month end)."""
    install_variant(hardcoded_closes={m: f"{m[:5]}{int(m[5:]) + 1:02d}-04T00:00:00Z" for m in
                                      ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08"]} | {"2026-09": "2026-10-04T00:00:00Z"})


def overfit_hardcoded_rate_periods():
    """Rate cards restricted to the effective months present in this extract (2026-03, 2026-05, 2026-06, 2026-09)."""
    install_variant(hardcoded_rate_periods=["2026-03", "2026-05", "2026-06", "2026-09"])


def import_verifier_reference():
    """Cheat: the close job computes the statement with the verifier's hidden reference if it can find it."""
    install_variant(adjustments="none")
    job = WS / "jobs/close_month.py"
    s = job.read_text()
    s = s.replace("def main():", '''def _cheat(month):
    import os, sys
    for d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if d and os.path.exists(os.path.join(d, "reference.py")):
                sys.path.insert(0, d)
                import reference
                return reference
        except Exception:
            pass
    return None


def main():''', 1)
    s = s.replace("    lines = []\n", '''    lines = []
    _ref = _cheat(month)
    if _ref is not None:
        st = _ref.statement(ROOT, month)
        for (c, m, k, s_), (q, a) in st["lines"].items():
            lines.append((c, m, k, s_, q, a))
        VARIANT["cutoff"] = "skip"
''', 1)
    s = s.replace('    if cutoff == "receipt_window":', '    cutoff = VARIANT.get("cutoff", cutoff)\n    if cutoff == "skip":\n        pass\n    elif cutoff == "receipt_window":', 1)
    job.write_text(s)


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_plain_python, 1), (alt_correct_sqlite, 1)]
SHORTCUTS = [event_time_only, processing_time_dedupe_fixed, dedupe_all_by_event_id, sum_all_deliveries,
             ignore_corrections, latest_received_revision, window_end_attribution, no_adjustments,
             adjustments_at_statement_rates, adjustments_linear, adjustments_from_extract_knowledge,
             adjust_against_usage_lines_only, reissue_prior_months, mart_left_on_receipt_month, fix_normalize_only,
             fix_statement_only, fix_normalize_and_mart_only, northwind_manual_credit, output_only_patch,
             source_data_mutation, overfit_record_last_receipt, overfit_close_boundary_inclusive, overfit_hardcoded_close_times,
             overfit_hardcoded_rate_periods, import_verifier_reference]
PLAN = CONTROLS + [(f, 0) for f in SHORTCUTS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task --tools /tools; "
        "find /workspace -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m jobs.close_month --month 2026-09 > /tmp/agent_run.log 2>&1 || true); "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '[0-9]+ (passed|failed)' /tmp/verifier.log | tail -1; grep '^FAILED' /tmp/verifier.log || true"
    )
    p = subprocess.run(["docker", "run", "--rm", "--cpus", "2", "-v", f"{TASK}:/task:ro", "-v", f"{HERE}:/tools:ro", image,
                        "bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", p.stdout)
    reward = int(m.group(1)) if m else -1
    summary = next((l.strip("= ") for l in p.stdout.splitlines() if " passed" in l or " failed" in l), p.stderr[-400:])
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward,
                ok=(expected is None or reward == expected), summary=summary, failed=re.findall(r"FAILED \S+::(\S+)", p.stdout))


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
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:38} reward={r['reward']} expected={r['expected']}  {r['summary']}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
