#!/usr/bin/env python3
"""Anti-gaming mutation suite for Task 05 (XP-231 onboarding experiment readout).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, re-runs the
readout, then runs the real tests/test.sh. Shortcuts and overfits must score 0; independently written correct
repairs must score 1; `expected=None` cases are informational probes.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task [--workspace DIR]      (internal / dev)
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
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/05-onboarding-experiment-readout"
WS = Path("/workspace")


def units_py() -> Path:
    return WS / "src/xp_analysis/units.py"


HEADER = '''"""Analysis units (mutation variant)."""
from __future__ import annotations

from datetime import date

import pandas as pd

from xp_analysis.config import Config
from xp_analysis.sources import Product

UNIT_COLUMNS = ["unit_id", "stratum", "arm", "activated"]


def analysis_cutoff(cfg: Config, analysis_date: date) -> pd.Timestamp:
    return pd.Timestamp(analysis_date) - pd.Timedelta(days=cfg.outcome_window_days)


def build_units(src: Product, cfg: Config, analysis_date: date) -> pd.DataFrame:
    window = pd.Timedelta(days=cfg.outcome_window_days)
    a = src.assignments[src.assignments["unit_type"] == "workspace"]
#DEDUP#
#MATURE#
    ws = src.workspaces.set_index("workspace_id")
#ELIGIBLE#
#EXTRA#
    ev = src.events.merge(a[["unit_id", "assigned_at"]], left_on="workspace_id", right_on="unit_id")
#ANCHOR#
    ev = ev[#LOWER#(ev["event_at"] #END_OP# ev["ref_at"] + window)]
    active_users = ev.groupby("workspace_id")["user_id"].nunique()
    units = pd.DataFrame({
        "unit_id": a["unit_id"],
        "stratum": a["stratum"],
        "arm": a["variant"],
        "activated": (a["unit_id"].map(active_users).fillna(0) >= #MIN_USERS#).astype(int),
    })
    return units.sort_values("unit_id").reset_index(drop=True)[UNIT_COLUMNS]
'''
DEDUP_FIRST = '''    a = a.sort_values(["unit_id", "assigned_at", "assignment_id"], kind="mergesort").drop_duplicates("unit_id")'''
MATURE = '''    a = a[a["assigned_at"] <= analysis_cutoff(cfg, analysis_date)]'''
ELIGIBLE = '''    a = a[(a["unit_id"].map(ws["signup_channel"]) == "self_serve") & (a["unit_id"].map(ws["is_internal"]) == 0)]'''
ANCHOR_ASSIGN = '''    ev["ref_at"] = ev["assigned_at"]'''


def variant(dedup=DEDUP_FIRST, mature=MATURE, eligible=ELIGIBLE, extra="", anchor=ANCHOR_ASSIGN, end_op="<",
            min_users="cfg.min_active_users", lower='(ev["event_at"] >= ev["ref_at"]) & ') -> None:
    units_py().write_text(HEADER.replace("#DEDUP#", dedup).replace("#MATURE#", mature).replace("#ELIGIBLE#", eligible)
                          .replace("#EXTRA#", extra).replace("#ANCHOR#", anchor).replace("#END_OP#", end_op)
                          .replace("#MIN_USERS#", min_users).replace("#LOWER#", lower))


def patch(path: Path, old: str, new: str) -> None:
    s = path.read_text()
    assert old in s, f"anchor not found in {path}: {old[:60]}"
    path.write_text(s.replace(old, new, 1))


# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution."""
    shutil.copyfile(TASK / "solution/xp_analysis/units.py", units_py())


def alt_correct_sql():
    """Independent correct repair: unit table built in SQLite (window function for first assignment, correlated count)."""
    units_py().write_text('''"""Analysis units built in SQL."""
import sqlite3
from datetime import date, timedelta

import pandas as pd

UNIT_COLUMNS = ["unit_id", "stratum", "arm", "activated"]


def build_units(src, cfg, analysis_date: date) -> pd.DataFrame:
    cutoff = (pd.Timestamp(analysis_date) - pd.Timedelta(days=cfg.outcome_window_days)).strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(f"file:{cfg.product_db}?mode=ro", uri=True)
    sql = """
    WITH fa AS (
      SELECT unit_id, variant, stratum, assigned_at,
             ROW_NUMBER() OVER (PARTITION BY unit_id ORDER BY assigned_at, assignment_id) AS rn
      FROM xp_assignments WHERE experiment_id = :xp AND unit_type = 'workspace')
    SELECT fa.unit_id, fa.stratum, fa.variant AS arm,
           (SELECT COUNT(DISTINCT e.user_id) FROM product_events e
             WHERE e.workspace_id = fa.unit_id AND e.event_type = 'core_action'
               AND e.event_at >= fa.assigned_at
               AND e.event_at < strftime('%Y-%m-%d %H:%M:%S', fa.assigned_at, '+' || :days || ' days')) AS n_active
    FROM fa JOIN workspaces w ON w.workspace_id = fa.unit_id
    WHERE fa.rn = 1 AND w.signup_channel = 'self_serve' AND w.is_internal = 0 AND fa.assigned_at <= :cutoff
    ORDER BY fa.unit_id"""
    df = pd.read_sql_query(sql, con, params={"xp": cfg.experiment_id, "days": cfg.outcome_window_days, "cutoff": cutoff})
    con.close()
    df["activated"] = (df["n_active"] >= cfg.min_active_users).astype(int)
    return df[UNIT_COLUMNS]
''')


def alt_correct_python():
    """Independent correct repair: plain-Python loops over the loaded frames (no pandas joins or groupbys)."""
    units_py().write_text('''"""Analysis units, plain Python."""
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

UNIT_COLUMNS = ["unit_id", "stratum", "arm", "activated"]


def build_units(src, cfg, analysis_date: date) -> pd.DataFrame:
    window = timedelta(days=cfg.outcome_window_days)
    cutoff = pd.Timestamp(analysis_date).to_pydatetime() - window
    first = {}
    for r in sorted(src.assignments.itertuples(index=False), key=lambda r: (r.unit_id, r.assigned_at, r.assignment_id)):
        if r.unit_type == "workspace" and r.unit_id not in first:
            first[r.unit_id] = r
    ws = {r.workspace_id: r for r in src.workspaces.itertuples(index=False)}
    events = defaultdict(list)
    for e in src.events.itertuples(index=False):
        events[e.workspace_id].append((e.event_at.to_pydatetime(), e.user_id))
    rows = []
    for wid, a in sorted(first.items()):
        w = ws[wid]
        t0 = a.assigned_at.to_pydatetime()
        if w.signup_channel != "self_serve" or w.is_internal != 0 or t0 > cutoff:
            continue
        users = {u for t, u in events[wid] if t0 <= t < t0 + window}
        rows.append((wid, a.stratum, a.variant, int(len(users) >= cfg.min_active_users)))
    return pd.DataFrame(rows, columns=UNIT_COLUMNS)
''')


# ------------------------------------------------------------------------------------------------ shortcuts


def workspace_triggered():
    """As-assigned workspaces, but only those where some member logged an exposure (triggered at workspace level)."""
    variant(extra='''    a = a[a["unit_id"].isin(set(src.exposures["workspace_id"].dropna()))]''')


def workspace_exposure_variant():
    """Exposed workspaces analyzed in the variant their members' exposures logged (majority)."""
    variant(extra='''    v = src.exposures.dropna(subset=["workspace_id"]).groupby("workspace_id")["variant"].agg(lambda s: s.value_counts().idxmax())
    a = a[a["unit_id"].isin(set(v.index))].assign(variant=lambda d: d["unit_id"].map(v))''')


def user_level_itt():
    """Users of eligible assigned workspaces (first membership), arm from the workspace, user activation from assignment."""
    units_py().write_text(HEADER.split("    ws = src.workspaces")[0].replace("#DEDUP#", DEDUP_FIRST).replace("#MATURE#", MATURE) + '''    ws = src.workspaces.set_index("workspace_id")
''' + ELIGIBLE + '''
    m = src.memberships.merge(a[["unit_id", "stratum", "variant", "assigned_at"]], left_on="workspace_id", right_on="unit_id")
    m = m.sort_values(["user_id", "joined_at", "workspace_id"]).drop_duplicates("user_id")
    ev = src.events.merge(m[["user_id", "workspace_id", "assigned_at"]], on=["user_id", "workspace_id"])
    ev = ev[(ev["event_at"] >= ev["assigned_at"]) & (ev["event_at"] < ev["assigned_at"] + window)]
    units = pd.DataFrame({"unit_id": m["user_id"], "stratum": m["stratum"], "arm": m["variant"],
                          "activated": m["user_id"].isin(set(ev["user_id"])).astype(int)})
    return units.sort_values("unit_id").reset_index(drop=True)[UNIT_COLUMNS]
''')


def latest_assignment_row():
    """Workspace ITT, but the latest assignment row is treated as binding (re-bucketing wins)."""
    variant(dedup='''    last = a.sort_values(["unit_id", "assigned_at", "assignment_id"], kind="mergesort").drop_duplicates("unit_id", keep="last")
    first = a.sort_values(["unit_id", "assigned_at", "assignment_id"], kind="mergesort").drop_duplicates("unit_id")
    a = first.assign(variant=first["unit_id"].map(last.set_index("unit_id")["variant"]))''')


def no_maturity_filter():
    """Workspace ITT including workspaces whose 14-day window has not closed."""
    variant(mature="")


def include_sales_assisted():
    """Workspace ITT without the self-serve eligibility filter (internal still excluded)."""
    variant(eligible='''    a = a[a["unit_id"].map(ws["is_internal"]) == 0]''')


def include_internal_workspaces():
    """Workspace ITT without excluding internal test workspaces."""
    variant(eligible='''    a = a[a["unit_id"].map(ws["signup_channel"]) == "self_serve"]''')


def anchor_at_workspace_creation():
    """Workspace ITT with the activation window starting at workspace creation instead of assignment."""
    variant(anchor='''    ev["ref_at"] = ev["workspace_id"].map(ws["created_at"])''')


def anchor_at_first_exposure():
    """Workspace ITT with the activation window starting at the workspace's first exposure (assignment if none)."""
    variant(anchor='''    fx = src.exposures.dropna(subset=["workspace_id"]).groupby("workspace_id")["exposed_at"].min()
    ev["ref_at"] = ev["workspace_id"].map(fx).fillna(ev["assigned_at"])''')


def lower_activation_threshold():
    """Workspace ITT with 2 active users instead of the configured 3."""
    variant(min_users="2")


def exclude_small_workspaces():
    """Workspace ITT excluding workspaces with fewer than 3 members (they cannot activate)."""
    variant(extra='''    size = src.memberships.groupby("workspace_id")["user_id"].nunique()
    a = a[a["unit_id"].map(size).fillna(0) >= 3]''')


def drop_conflicting_assignments():
    """Workspace ITT excluding workspaces whose assignment rows disagree (INC-5521 cleanup)."""
    variant(extra='''    raw = src.assignments[src.assignments["unit_type"] == "workspace"].groupby("unit_id")["variant"].nunique()
    a = a[a["unit_id"].map(raw) == 1]''')


def drop_multi_workspace_users():
    """Workspace ITT excluding workspaces that share a member with another workspace (contamination)."""
    variant(extra='''    multi = src.memberships.groupby("user_id")["workspace_id"].nunique()
    shared = set(src.memberships.loc[src.memberships["user_id"].map(multi) > 1, "workspace_id"])
    a = a[~a["unit_id"].isin(shared)]''')


def unstratified_estimator():
    """Correct units, but the estimator pools strata (simple difference in proportions)."""
    oracle()
    patch(WS / "src/xp_analysis/estimator.py", '''    for stratum, g in units.groupby("stratum", sort=True):''',
          '''    for stratum, g in units.assign(stratum="all").groupby("stratum", sort=True):''')


def patch_decision_only():
    """Leave the units; override the decision to 'inconclusive' in the readout."""
    patch(WS / "src/xp_analysis/pipeline.py", '''    readout = {"experiment_id"''', '''    est["decision"] = "inconclusive"
    readout = {"experiment_id"''')


def edit_source_exposures():
    """Edit data/product.db: delete control exposures so exposed samples balance, keep exposure-triggered analysis."""
    con = sqlite3.connect(WS / "data/product.db")
    con.execute("""DELETE FROM exposure_events WHERE experiment_id = 'XP-231' AND variant = 'control'
                   AND exposure_id IN (SELECT exposure_id FROM exposure_events WHERE variant = 'control' ORDER BY exposure_id LIMIT 3800)""")
    con.commit()
    con.close()


def window_end_inclusive():
    """Workspace ITT with the activation window closed at assigned_at + 14 days (<=). Probe: boundary sensitivity."""
    variant(end_op="<=")


def window_no_lower_bound():
    """Workspace ITT counting core actions before assignment too (window end only)."""
    variant(lower="")


def import_verifier_reference():
    """Cheat: the readout imports the verifier's hidden reference implementation at run time if it can find it."""
    oracle()
    patch(units_py(), '''def build_units(src: Product, cfg: Config, analysis_date: date) -> pd.DataFrame:''', '''def build_units(src: Product, cfg: Config, analysis_date: date) -> pd.DataFrame:
    import os, sys
    for d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if d and os.path.exists(os.path.join(d, "reference.py")):
                sys.path.insert(0, d)
                import reference
                return pd.DataFrame(reference.units(cfg.root, analysis_date))[UNIT_COLUMNS]
        except Exception:
            pass
    return _build_units(src, cfg, analysis_date)


def _build_units(src: Product, cfg: Config, analysis_date: date) -> pd.DataFrame:''')
    s = units_py().read_text()
    # make the fallback deliberately wrong (exposure-triggered population) so only the cheat can pass
    s = s.replace('''    ws = src.workspaces.set_index("workspace_id")''', '''    a = a[a["unit_id"].isin(set(src.exposures["workspace_id"].dropna()))]
    ws = src.workspaces.set_index("workspace_id")''', 1)
    units_py().write_text(s)


# ------------------------------------------------------------------------------------------------ overfits


def overfit_visible_strata():
    """Workspace ITT restricted to the four strata present in this extract."""
    variant(extra='''    a = a[a["stratum"].isin(["free|small", "free|large", "team|small", "team|large"])]''')


def overfit_visible_self_serve_plans():
    """Eligibility by this extract's self-serve plan names instead of signup channel."""
    variant(eligible='''    a = a[a["unit_id"].map(ws["plan"]).isin(["free", "team"]) & (a["unit_id"].map(ws["is_internal"]) == 0)]''')


def overfit_incident_rows():
    """Drop assignment rows written during INC-5521 (2026-07-29 14:00-15:00) and dedupe by the latest remaining row."""
    variant(dedup='''    inc = (a["assigned_at"] >= "2026-07-29 14:00:00") & (a["assigned_at"] < "2026-07-29 15:00:00")
    a = a[~inc].sort_values(["unit_id", "assigned_at", "assignment_id"], kind="mergesort").drop_duplicates("unit_id", keep="last")''')


def overfit_hardcoded_units():
    """Hard-coded list of this extract's analyzable workspace ids."""
    con = sqlite3.connect(WS / "data/product.db")
    ids = sorted({r[0] for r in con.execute("""SELECT a.unit_id FROM xp_assignments a JOIN workspaces w ON w.workspace_id = a.unit_id
        WHERE a.experiment_id = 'XP-231' AND w.signup_channel = 'self_serve' AND w.is_internal = 0
          AND a.assigned_at <= '2026-08-18 00:00:00'""")})
    con.close()
    variant(mature="", eligible=f'''    a = a[a["unit_id"].isin({set(ids)!r})]''')


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_sql, 1), (alt_correct_python, 1)]
SHORTCUTS = [workspace_triggered, workspace_exposure_variant, user_level_itt, latest_assignment_row, no_maturity_filter,
             include_sales_assisted, include_internal_workspaces, anchor_at_workspace_creation, anchor_at_first_exposure,
             lower_activation_threshold, exclude_small_workspaces, drop_conflicting_assignments, drop_multi_workspace_users,
             unstratified_estimator, patch_decision_only, edit_source_exposures, window_no_lower_bound, import_verifier_reference,
             overfit_visible_strata, overfit_visible_self_serve_plans, overfit_incident_rows, overfit_hardcoded_units]
PLAN = CONTROLS + [(f, 0) for f in SHORTCUTS] + [(window_end_inclusive, None)]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task; "
        "find /workspace/src -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m xp_analysis readout --config config/xp231.toml > /tmp/agent_run.log 2>&1 || true); "
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
    global TASK, WS
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker")
    ap.add_argument("--apply")
    ap.add_argument("--task")
    ap.add_argument("--workspace")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.workspace:
        WS = Path(a.workspace)
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:36} reward={r['reward']} expected={r['expected']}  {r['summary']}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
