"""Independent reference for Task 05 (pure Python + sqlite3; shares no code with the workspace package).

Analysis per the XP-231 pre-registered plan: unit = workspace, as randomized (first assignment log row binding);
population = eligible (self-serve, non-internal) workspaces assigned at least 14 days before the analysis date;
outcome = at least 3 distinct users with a core_action in the workspace in [assigned_at, assigned_at + 14 days);
estimator = stratified difference in proportions, stratum weights N_h / N, Neyman variance, 95% CI with z = 1.96.
"""
from __future__ import annotations

import math
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

F = "%Y-%m-%d %H:%M:%S"
XP = "XP-231"
WINDOW = timedelta(days=14)
MIN_USERS = 3
Z = 1.96


def units(root: Path, analysis_date: date) -> list[dict]:
    con = sqlite3.connect(f"file:{Path(root) / 'data/product.db'}?mode=ro", uri=True)
    cutoff = datetime.combine(analysis_date, datetime.min.time())
    first = {}
    for _aid, unit, variant, stratum, at in con.execute(
            "SELECT assignment_id, unit_id, variant, stratum, assigned_at FROM xp_assignments "
            "WHERE experiment_id = ? AND unit_type = 'workspace' ORDER BY unit_id, assigned_at, assignment_id", (XP,)):
        first.setdefault(unit, (variant, stratum, datetime.strptime(at, F)))
    ws = {w: (ch, internal) for w, ch, internal in con.execute("SELECT workspace_id, signup_channel, is_internal FROM workspaces")}
    core = defaultdict(list)
    for wid, uid, t in con.execute("SELECT workspace_id, user_id, event_at FROM product_events WHERE event_type = 'core_action'"):
        core[wid].append((datetime.strptime(t, F), uid))
    con.close()
    rows = []
    for wid, (variant, stratum, at) in first.items():
        ch, internal = ws[wid]
        if ch != "self_serve" or internal:
            continue
        if at + WINDOW > cutoff:
            continue
        active = {uid for t, uid in core[wid] if at <= t < at + WINDOW}
        rows.append(dict(unit_id=wid, stratum=stratum, arm=variant, activated=int(len(active) >= MIN_USERS)))
    rows.sort(key=lambda r: r["unit_id"])
    return rows


def readout(rows: list[dict]) -> dict:
    by = defaultdict(lambda: {"control": [], "treatment": []})
    for r in rows:
        by[r["stratum"]][r["arm"]].append(r["activated"])
    n_total = len(rows)
    effect, var, strata = 0.0, 0.0, []
    for h in sorted(by):
        y1, y0 = by[h]["treatment"], by[h]["control"]
        n1, n0 = len(y1), len(y0)
        p1, p0 = sum(y1) / n1, sum(y0) / n0
        s1 = sum((y - p1) ** 2 for y in y1) / (n1 - 1)
        s0 = sum((y - p0) ** 2 for y in y0) / (n0 - 1)
        w = (n1 + n0) / n_total
        effect += w * (p1 - p0)
        var += w * w * (s1 / n1 + s0 / n0)
        strata.append(dict(stratum=h, n_control=n0, n_treatment=n1, rate_control=p0, rate_treatment=p1,
                           effect=p1 - p0, weight=w))
    se = math.sqrt(var)
    lo, hi = effect - Z * se, effect + Z * se
    nc = sum(1 for r in rows if r["arm"] == "control")
    nt = n_total - nc
    exp = n_total / 2
    chi2 = ((nc - exp) ** 2 + (nt - exp) ** 2) / exp
    return dict(
        n_units_control=nc, n_units_treatment=nt,
        rate_control=sum(r["activated"] for r in rows if r["arm"] == "control") / nc,
        rate_treatment=sum(r["activated"] for r in rows if r["arm"] == "treatment") / nt,
        effect=effect, se=se, ci_low=lo, ci_high=hi,
        decision="ship" if lo > 0 else ("rollback" if hi < 0 else "inconclusive"),
        srm_p_value=math.erfc(math.sqrt(chi2 / 2)), strata=strata)
