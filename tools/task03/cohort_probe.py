import sqlite3, sys, math
from datetime import datetime, timedelta
db = sys.argv[1]; as_of = datetime.fromisoformat(sys.argv[2] if len(sys.argv) > 2 else "2026-09-01")
con = sqlite3.connect(db)
F = "%Y-%m-%d %H:%M:%S"
leads = {l: dict(created=datetime.strptime(c, F), src=s) for l, c, s, st in con.execute("select lead_id, created_at, source, intake_status from leads") if st == "accepted"}
score = dict(con.execute("select lead_id, score from lead_scores where model_version='lsm-3.2'"))
init, latest = {}, {}
for lid, t, pol in con.execute("select lead_id, routed_at, policy from routing_events order by routed_at, routing_event_id"):
    init.setdefault(lid, pol); latest[lid] = pol
worked = {l for (l,) in con.execute("select distinct lead_id from sdr_activities where activity_at < ?", (as_of.strftime(F),))}
conv = {}
for lid, t in con.execute("select lead_id, closed_won_at from conversions"):
    conv[lid] = datetime.strptime(t, F)
def auc(rows):
    rows = sorted(rows); n = len(rows); ranks = [0]*n; i = 0
    while i < n:
        j = i
        while j+1 < n and rows[j+1][0] == rows[i][0]: j += 1
        for k in range(i, j+1): ranks[k] = (i+j)/2+1
        i = j+1
    pos = sum(y for _, y in rows); neg = n-pos
    return (sum(r for r, (_, y) in zip(ranks, rows) if y) - pos*(pos+1)/2)/(pos*neg)
start = as_of - timedelta(days=240)
base = [l for l, d in leads.items() if d["created"] >= start and d["created"] + timedelta(days=60) <= as_of]
lab = lambda l: int(l in conv and conv[l] - leads[l]["created"] <= timedelta(days=60))
for name, pop in [("all matured (v2 bug)", base), ("holdout ITT initial (correct)", [l for l in base if init[l]=="exploration_holdout"]),
                  ("worked only", [l for l in base if l in worked]), ("holdout per-protocol", [l for l in base if init[l]=="exploration_holdout" and l in worked]),
                  ("holdout latest policy", [l for l in base if latest[l]=="exploration_holdout"])]:
    rows = [(score[l], lab(l)) for l in pop]
    print(f"{name:32} n={len(pop):6d} pos={sum(y for _,y in rows):5d} rate={sum(y for _,y in rows)/len(rows):.3f} auc={auc(rows):.4f}")
