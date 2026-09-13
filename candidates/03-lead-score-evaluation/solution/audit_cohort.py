"""Oracle helper: independent SQL audit of the evaluation cohort and a comparison of candidate populations.

--diagnose prints AUC and size for the populations one might evaluate; otherwise checks artifacts/eval_cohort.csv
against a SQL construction of the intake exploration-holdout cohort with labels recomputed from conversions.
"""
import sqlite3
import sys

import pandas as pd
from sklearn.metrics import roc_auc_score

AS_OF = sys.argv[sys.argv.index("--as-of") + 1] if "--as-of" in sys.argv else "2026-09-01"
con = sqlite3.connect("file:data/revops.db?mode=ro", uri=True)
base = pd.read_sql_query(f"""
WITH intake AS (
  SELECT lead_id, policy, ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY routed_at, routing_event_id) AS rn
  FROM routing_events),
latest AS (
  SELECT lead_id, policy, ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY routed_at DESC, routing_event_id DESC) AS rn
  FROM routing_events)
SELECT l.lead_id, s.score,
       i.policy AS intake_policy, t.policy AS latest_policy,
       EXISTS (SELECT 1 FROM sdr_activities a WHERE a.lead_id = l.lead_id AND a.activity_at < '{AS_OF} 00:00:00') AS worked,
       EXISTS (SELECT 1 FROM conversions c WHERE c.lead_id = l.lead_id
               AND julianday(c.closed_won_at) - julianday(l.created_at) <= 60) AS label
FROM leads l
JOIN lead_scores s ON s.lead_id = l.lead_id AND s.model_version = 'lsm-3.2'
JOIN intake i ON i.lead_id = l.lead_id AND i.rn = 1
JOIN latest t ON t.lead_id = l.lead_id AND t.rn = 1
WHERE l.intake_status = 'accepted'
  AND julianday(l.created_at) >= julianday('{AS_OF}') - 240
  AND julianday(l.created_at) + 60 <= julianday('{AS_OF}')
""", con)

pops = {"all matured leads": base, "worked leads": base[base.worked == 1],
        "intake holdout (all)": base[base.intake_policy == "exploration_holdout"],
        "intake holdout, worked only": base[(base.intake_policy == "exploration_holdout") & (base.worked == 1)]}
if "--diagnose" in sys.argv:
    for name, p in pops.items():
        print(f"{name:30} n={len(p):6d} conversion={p.label.mean():.3f} auc={roc_auc_score(p.label, p.score):.4f}")
    sys.exit(0)

want = pops["intake holdout (all)"].set_index("lead_id")
got = pd.read_csv("artifacts/eval_cohort.csv").set_index("lead_id")
problems = []
if set(got.index) != set(want.index) or got.index.duplicated().any():
    problems.append(f"cohort membership differs: missing={len(set(want.index) - set(got.index))} extra={len(set(got.index) - set(want.index))}")
else:
    if (got.loc[want.index, "label"] != want["label"]).any():
        problems.append("labels differ")
    if (abs(got.loc[want.index, "score"] - want["score"]) > 1e-9).any():
        problems.append("scores differ")
print("audit:", problems or "cohort matches SQL construction")
sys.exit(1 if problems else 0)
