#!/usr/bin/env python3
"""Anti-gaming mutation suite for Task 04 (retention metrics semantic layer).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, rebuilds the
layer, then runs the real tests/test.sh. Shortcuts and overfits must score 0; independently written correct
repairs must score 1.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task      (internal, inside the container)
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
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/04-retention-metrics-regression"
WS = Path("/workspace")
MODELS = WS / "semantic/models"
CQ = MODELS / "03_customer_quarter.sql"
BUILD = WS / "src/metrics_layer/build.py"

TEMPLATE = """-- customer_quarter (mutation variant)
DROP TABLE IF EXISTS customer_quarter;
CREATE TABLE customer_quarter AS
SELECT b.quarter, b.account_id, b.start_arr, b.end_arr,
       {movement} AS movement,
       {in_cohort} AS in_cohort,
       {segment} AS segment
FROM arr_boundaries b
JOIN src.crm_accounts a ON a.account_id = b.account_id
WHERE (b.start_arr > 0 OR b.end_arr > 0){where};
"""
PRIOR_LINE = "EXISTS (SELECT 1 FROM stg_recurring_lines l WHERE l.account_id = b.account_id AND l.start_date < b.start_date)"
MOV_OK = f"""CASE WHEN b.start_arr > 0 AND b.end_arr = 0 THEN 'churned'
                 WHEN b.start_arr > 0 AND b.end_arr > b.start_arr THEN 'expanded'
                 WHEN b.start_arr > 0 AND b.end_arr < b.start_arr THEN 'contracted'
                 WHEN b.start_arr > 0 THEN 'retained'
                 WHEN {{prior}} THEN 'reactivated'
                 ELSE 'new' END"""
COH_OK = "CASE WHEN b.start_arr > 0 THEN 1 ELSE 0 END"
SEG_OK = """CASE WHEN b.start_arr <= 0 THEN NULL WHEN b.start_arr < 25000 THEN 'SMB'
                 WHEN b.start_arr < 100000 THEN 'Mid-Market' ELSE 'Enterprise' END"""


def cq_variant(movement: str | None = None, in_cohort: str = COH_OK, segment: str = SEG_OK, where: str = "",
               prior: str = PRIOR_LINE) -> None:
    movement = movement or MOV_OK.replace("{prior}", prior)
    CQ.write_text(TEMPLATE.format(movement=movement, in_cohort=in_cohort, segment=segment, where=where))


def patch(path: Path, old: str, new: str) -> None:
    s = path.read_text()
    assert old in s, f"anchor not found in {path}: {old[:60]}"
    path.write_text(s.replace(old, new, 1))


def bug_movement(existing: str) -> str:
    """Workspace 2.0 movement logic with a different 'existing customer' predicate."""
    return f"""CASE WHEN NOT ({existing}) THEN 'new' WHEN b.end_arr = 0 THEN 'churned'
                 WHEN b.end_arr > b.start_arr THEN 'expanded' WHEN b.end_arr < b.start_arr THEN 'contracted'
                 ELSE 'retained' END"""


def existing_variant(existing: str) -> None:
    cq_variant(movement=bug_movement(existing), in_cohort=f"CASE WHEN {existing} THEN 1 ELSE 0 END",
               segment=f"CASE WHEN NOT ({existing}) THEN NULL ELSE {SEG_OK} END")


AFTER_MODELS = """    con.commit()
    cfg.board_dir.mkdir(parents=True, exist_ok=True)"""

# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution."""
    shutil.copyfile(TASK / "solution/semantic/models/03_customer_quarter.sql", CQ)


def alt_correct_sql():
    """Independent correct repair: customer spells from first/last line dates via window CTEs, segment via lookup table."""
    CQ.write_text("""-- customer_quarter: lifecycle per (quarter, account), customer status from ARR (alternative formulation)
DROP TABLE IF EXISTS customer_quarter;
CREATE TABLE customer_quarter AS
WITH first_line AS (
  SELECT account_id, MIN(start_date) AS first_start FROM stg_recurring_lines GROUP BY account_id
),
seg(name, lo, hi) AS (VALUES ('SMB', 0.005, 25000), ('Mid-Market', 25000, 100000), ('Enterprise', 100000, 1e18)),
base AS (
  SELECT b.*, f.first_start FROM arr_boundaries b JOIN first_line f USING (account_id)
  WHERE b.start_arr + b.end_arr > 0
)
SELECT quarter, account_id, start_arr, end_arr,
       CASE WHEN start_arr = 0 AND first_start < start_date THEN 'reactivated'
            WHEN start_arr = 0 THEN 'new'
            WHEN end_arr = 0 THEN 'churned'
            WHEN end_arr = start_arr THEN 'retained'
            WHEN end_arr > start_arr THEN 'expanded'
            ELSE 'contracted' END AS movement,
       (start_arr > 0) AS in_cohort,
       (SELECT name FROM seg WHERE base.start_arr >= seg.lo AND base.start_arr < seg.hi) AS segment
FROM base;
""")


def alt_correct_python():
    """Independent correct repair: customer_quarter classified in Python inside the build (no SQL CASE logic)."""
    CQ.write_text("""DROP TABLE IF EXISTS customer_quarter;
CREATE TABLE customer_quarter (quarter TEXT, account_id TEXT, start_arr REAL, end_arr REAL, movement TEXT,
                               in_cohort INTEGER, segment TEXT);
""")
    patch(BUILD, """        con.executescript(model.read_text())
""", """        con.executescript(model.read_text())
        if model.stem == "03_customer_quarter":
            _classify(con)
""")
    patch(BUILD, '''def build(cfg: Config, as_of: date) -> None:''', '''def _classify(con) -> None:
    first = dict(con.execute("SELECT account_id, MIN(start_date) FROM stg_recurring_lines GROUP BY account_id"))
    rows = []
    for q, s, acc, a0, a1 in con.execute("SELECT quarter, start_date, account_id, start_arr, end_arr FROM arr_boundaries"):
        if a0 <= 0 and a1 <= 0:
            continue
        if a0 > 0:
            mv = "churned" if a1 <= 0 else ("expanded" if a1 > a0 else "contracted" if a1 < a0 else "retained")
            seg = "SMB" if a0 < 25000 else ("Mid-Market" if a0 < 100000 else "Enterprise")
        else:
            mv, seg = ("reactivated" if first[acc] < s else "new"), None
        rows.append((q, acc, a0, a1, mv, int(a0 > 0), seg))
    con.executemany("INSERT INTO customer_quarter VALUES (?,?,?,?,?,?,?)", rows)


def build(cfg: Config, as_of: date) -> None:''')


# ------------------------------------------------------------------------------------------------ shortcuts


def exclude_abm_target_accounts():
    """Keep CRM-based cohort, but treat ABM target-list accounts without starting ARR as new logos."""
    existing_variant("(a.created_at < b.start_date AND NOT (a.source = 'abm_target_list' AND b.start_arr = 0))")


def first_contract_signed_before_quarter():
    """Existing customer = first contract signed before the quarter (booking date instead of CRM creation)."""
    existing_variant("(SELECT MIN(c.signed_at) FROM src.contracts c WHERE c.account_id = b.account_id) < b.start_date")


def crm_contract_type_new_business():
    """New logo = has a new_business contract whose lines start in the quarter (Sales Ops contract categories)."""
    existing_variant("""NOT EXISTS (SELECT 1 FROM src.contracts c JOIN src.subscription_lines sl USING (contract_id)
                           WHERE c.account_id = b.account_id AND c.contract_type = 'new_business'
                             AND sl.start_date >= b.start_date AND sl.start_date < b.end_date)""")


def cohort_fixed_movement_unchanged():
    """Cohort = ARR on S (NRR/GRR/logo churn fixed) but lifecycle movement and segment logic left as in 2.0."""
    patch(CQ, "CASE WHEN a.created_at < b.start_date THEN 1 ELSE 0 END AS in_cohort",
          "CASE WHEN b.start_arr > 0 THEN 1 ELSE 0 END AS in_cohort")


def no_reactivation_category():
    """Cohort, movements and segments by ARR, but every account without starting ARR is 'new'."""
    cq_variant(prior="0")


def segment_from_ending_arr():
    """Correct cohort and movements; segment assigned from ending ARR (falling back to starting ARR for churned)."""
    cq_variant(segment="""CASE WHEN b.start_arr <= 0 THEN NULL
                 WHEN COALESCE(NULLIF(b.end_arr, 0), b.start_arr) < 25000 THEN 'SMB'
                 WHEN COALESCE(NULLIF(b.end_arr, 0), b.start_arr) < 100000 THEN 'Mid-Market' ELSE 'Enterprise' END""")


def tenure_based_cohort():
    """Existing customer = any recurring line started before the quarter (win-backs join the cohort)."""
    existing_variant(PRIOR_LINE)


def renewal_grace_period():
    """ARR-based cohort, plus accounts whose last line ended within 45 days before S (late renewals kept in cohort)."""
    grace = ("EXISTS (SELECT 1 FROM stg_recurring_lines l WHERE l.account_id = b.account_id "
             "AND l.end_date <= b.start_date AND l.end_date >= date(b.start_date, '-45 days'))")
    existing_variant(f"(b.start_arr > 0 OR {grace})")


def drop_precreated_accounts():
    """Keep 2.0 logic but drop rows for accounts created before the quarter with no starting ARR."""
    patch(CQ, "WHERE b.start_arr > 0 OR b.end_arr > 0;",
          "WHERE (b.start_arr > 0 OR b.end_arr > 0) AND NOT (a.created_at < b.start_date AND b.start_arr = 0);")


def published_snapshot_arr():
    """Reconcile to the FP&A workbook: ignore lines signed after quarter end + 12 days, with ARR-based cohort."""
    oracle()
    patch(MODELS / "02_arr_boundaries.sql",
          "JOIN stg_recurring_lines l ON l.start_date <= q.end_date AND l.end_date > q.start_date",
          "JOIN stg_recurring_lines l ON l.start_date <= q.end_date AND l.end_date > q.start_date\n"
          "JOIN src.contracts c ON c.contract_id = l.contract_id AND c.signed_at <= date(q.end_date, '+12 days')")


def quarter_end_last_day():
    """Correct classification, but ending ARR measured on the last day of the quarter instead of E."""
    oracle()
    s = (MODELS / "02_arr_boundaries.sql").read_text()
    s = s.replace("l.start_date <= q.end_date AND q.end_date < l.end_date",
                  "l.start_date <= date(q.end_date, '-1 day') AND date(q.end_date, '-1 day') < l.end_date")
    (MODELS / "02_arr_boundaries.sql").write_text(s)


def scale_nrr_to_published():
    """Leave the model; scale NRR in retention_quarterly toward the published level before export."""
    patch(BUILD, AFTER_MODELS, """    con.execute("UPDATE retention_quarterly SET nrr = nrr * 0.93")
""" + AFTER_MODELS)


def restore_published_quarters():
    """Leave the model; overwrite published quarters' metrics with the FP&A workbook values before export."""
    patch(BUILD, AFTER_MODELS, """    import csv as _csv
    for r in _csv.DictReader(open(cfg.analytics_db.parent.parent / "reports/finance/retention_workbook_published.csv")):
        con.execute("UPDATE retention_quarterly SET cohort_customers=?, starting_arr=?, nrr=?, grr=?, logo_churn_rate=? "
                    "WHERE quarter=?", (r["cohort_customers"], r["starting_arr"], r["nrr"], r["grr"], r["logo_churn_rate"], r["quarter"]))
""" + AFTER_MODELS)


def edit_warehouse_created_at():
    """Edit data/warehouse.db: set CRM created_at to the account's first subscription start (2.0 logic then 'works')."""
    con = sqlite3.connect(WS / "data/warehouse.db")
    con.execute("""UPDATE crm_accounts SET created_at = (SELECT MIN(start_date) || ' 00:00:00' FROM subscription_lines s
                   WHERE s.account_id = crm_accounts.account_id) WHERE account_id IN (SELECT account_id FROM subscription_lines)""")
    con.commit()
    con.close()


def segment_boundaries_inclusive():
    """Correct cohort and movements; segment thresholds inclusive (SMB <= 25,000, Mid-Market <= 100,000)."""
    cq_variant(segment="""CASE WHEN b.start_arr <= 0 THEN NULL WHEN b.start_arr <= 25000 THEN 'SMB'
                 WHEN b.start_arr <= 100000 THEN 'Mid-Market' ELSE 'Enterprise' END""")


def reactivation_requires_ended_spell():
    """Reactivated only if an earlier recurring line ended strictly before S (a line ending on S does not count)."""
    cq_variant(prior="EXISTS (SELECT 1 FROM stg_recurring_lines l WHERE l.account_id = b.account_id "
                     "AND l.start_date < b.start_date AND l.end_date < b.start_date)")


def import_verifier_reference():
    """Cheat: the build replaces customer_quarter with the verifier's hidden reference implementation if it can find it."""
    patch(BUILD, AFTER_MODELS, """    import os, sys
    for _d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if _d and os.path.exists(os.path.join(_d, "reference.py")):
                sys.path.insert(0, _d)
                import reference
                res = reference.compute(cfg.analytics_db.parent.parent, as_of, cfg.n_quarters)
                con.execute("DELETE FROM customer_quarter")
                con.executemany("INSERT INTO customer_quarter (quarter, account_id, start_arr, end_arr, movement, in_cohort, segment) "
                                "VALUES (?,?,?,?,?,?,?)", [(r["quarter"], r["account_id"], r["start_arr"], r["end_arr"], r["movement"],
                                                            int(r["start_arr"] > 0), r["segment"]) for r in res["customer_quarter"]])
                for m in ("04_retention_quarterly", "05_retention_by_segment"):
                    con.executescript((cfg.models_dir / f"{m}.sql").read_text())
                break
        except Exception:
            pass
""" + AFTER_MODELS)


# ------------------------------------------------------------------------------------------------ overfits


def overfit_reactivation_lookback_540d():
    """Reactivated only if a prior line ended within 540 days before S (visible win-back gaps are shorter)."""
    cq_variant(prior="EXISTS (SELECT 1 FROM stg_recurring_lines l WHERE l.account_id = b.account_id "
                     "AND l.start_date < b.start_date AND l.end_date >= date(b.start_date, '-540 days'))")


def overfit_reactivation_from_quarter_snapshots():
    """Reactivated if the account had ARR on an earlier quarter start date (misses spells between boundaries)."""
    cq_variant(prior="""EXISTS (WITH RECURSIVE qs(d) AS (SELECT '2015-01-01' UNION ALL
                                    SELECT date(d, '+3 months') FROM qs WHERE d < '2030-01-01')
                         SELECT 1 FROM qs JOIN stg_recurring_lines l ON l.start_date <= qs.d AND qs.d < l.end_date
                         WHERE l.account_id = b.account_id AND qs.d < b.start_date)""")


def overfit_visible_quarters_only():
    """Correct logic for the eight visible reporting quarters; 2.0 logic elsewhere."""
    vis = "b.quarter BETWEEN '2024-Q3' AND '2026-Q2'"
    cq_variant(movement=f"CASE WHEN {vis} THEN ({MOV_OK.replace('{prior}', PRIOR_LINE)}) ELSE ({bug_movement('a.created_at < b.start_date')}) END",
               in_cohort=f"CASE WHEN {vis} THEN ({COH_OK}) ELSE (a.created_at < b.start_date) END",
               segment=f"CASE WHEN {vis} THEN ({SEG_OK}) ELSE (CASE WHEN a.created_at < b.start_date THEN {SEG_OK.replace('WHEN b.start_arr <= 0 THEN NULL ', '')} END) END")


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_sql, 1), (alt_correct_python, 1)]
SHORTCUTS = [exclude_abm_target_accounts, first_contract_signed_before_quarter, crm_contract_type_new_business,
             cohort_fixed_movement_unchanged, no_reactivation_category, segment_from_ending_arr, tenure_based_cohort,
             renewal_grace_period, drop_precreated_accounts, published_snapshot_arr, quarter_end_last_day,
             scale_nrr_to_published, restore_published_quarters, edit_warehouse_created_at,
             segment_boundaries_inclusive, reactivation_requires_ended_spell, import_verifier_reference,
             overfit_reactivation_lookback_540d, overfit_reactivation_from_quarter_snapshots, overfit_visible_quarters_only]
PLAN = CONTROLS + [(f, 0) for f in SHORTCUTS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task; "
        "find /workspace/src -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m metrics_layer build --config config/metrics_layer.toml > /tmp/agent_run.log 2>&1 || true); "
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
    global TASK
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker")
    ap.add_argument("--apply")
    ap.add_argument("--task")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--report")
    ap.add_argument("--workspace", help="apply to a local workspace instead of /workspace (dev)")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.workspace:
        global WS, MODELS, CQ, BUILD
        WS = Path(a.workspace)
        MODELS, CQ, BUILD = WS / "semantic/models", WS / "semantic/models/03_customer_quarter.sql", WS / "src/metrics_layer/build.py"
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:44} reward={r['reward']} expected={r['expected']}  {r['summary']}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
