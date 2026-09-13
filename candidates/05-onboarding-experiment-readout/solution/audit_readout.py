"""Oracle helper: audit the XP-231 readout.

--diagnose: exposure logging and sample ratio by arm, disagreement between exposure variant and workspace assignment,
assignment log duplicates, and the effect under exposure-triggered vs as-assigned workspace units.
Otherwise: assert the pipeline's unit table equals an independent SQL construction of the plan's units.
"""
import csv
import sqlite3
import sys

con = sqlite3.connect("file:data/product.db?mode=ro", uri=True)
analysis_date = sys.argv[sys.argv.index("--analysis-date") + 1] if "--analysis-date" in sys.argv else "2026-09-01"
SQL = """
WITH first_assignment AS (
  SELECT unit_id, variant, stratum, assigned_at,
         ROW_NUMBER() OVER (PARTITION BY unit_id ORDER BY assigned_at, assignment_id) AS rn
  FROM xp_assignments WHERE experiment_id = 'XP-231' AND unit_type = 'workspace'
), units AS (
  SELECT f.unit_id, f.variant, f.stratum, f.assigned_at FROM first_assignment f
  JOIN workspaces w ON w.workspace_id = f.unit_id
  WHERE f.rn = 1 AND w.signup_channel = 'self_serve' AND w.is_internal = 0
    AND datetime(f.assigned_at, '+14 days') <= datetime(:d)
)
SELECT u.unit_id, u.stratum, u.variant,
       CASE WHEN (SELECT COUNT(DISTINCT e.user_id) FROM product_events e
                  WHERE e.workspace_id = u.unit_id AND e.event_type = 'core_action'
                    AND e.event_at >= u.assigned_at AND e.event_at < datetime(u.assigned_at, '+14 days')) >= 3
            THEN 1 ELSE 0 END
FROM units u ORDER BY u.unit_id
"""
if "--diagnose" in sys.argv:
    q = lambda s, *p: con.execute(s, p).fetchall()  # noqa: E731
    print("exposed users by variant:", q("SELECT variant, COUNT(DISTINCT user_id) FROM exposure_events WHERE experiment_id='XP-231' GROUP BY variant"))
    print("assigned workspaces by first variant:", q("""SELECT variant, COUNT(*) FROM (SELECT unit_id, variant, ROW_NUMBER() OVER
        (PARTITION BY unit_id ORDER BY assigned_at, assignment_id) rn FROM xp_assignments WHERE experiment_id='XP-231') WHERE rn=1 GROUP BY variant"""))
    print("workspaces with >1 assignment rows / with conflicting variants:", q("""SELECT SUM(n > 1), SUM(v > 1) FROM
        (SELECT unit_id, COUNT(*) n, COUNT(DISTINCT variant) v FROM xp_assignments WHERE experiment_id='XP-231' GROUP BY unit_id)"""))
    print("exposures whose variant differs from the workspace's first assignment:", q("""SELECT COUNT(*) FROM exposure_events x JOIN
        (SELECT unit_id, variant FROM (SELECT unit_id, variant, ROW_NUMBER() OVER (PARTITION BY unit_id ORDER BY assigned_at, assignment_id) rn
         FROM xp_assignments WHERE experiment_id='XP-231') WHERE rn=1) a ON a.unit_id = x.workspace_id
        WHERE x.experiment_id='XP-231' AND x.variant <> a.variant"""))
    rows = con.execute(SQL, {"d": analysis_date + " 00:00:00"}).fetchall()
    for arm in ("control", "treatment"):
        r = [x for x in rows if x[2] == arm]
        print(f"as-assigned workspaces {arm}: n={len(r)} activation={sum(x[3] for x in r) / len(r):.4f}")
    sys.exit(0)
want = [(u, s, v, str(a)) for u, s, v, a in con.execute(SQL, {"d": analysis_date + " 00:00:00"})]
got = [tuple(r.values()) for r in csv.DictReader(open("artifacts/XP-231_units.csv"))]
print("audit:", "units match SQL construction" if got == want else f"MISMATCH ({len(got)} vs {len(want)} rows)")
sys.exit(0 if got == want else 1)
