#!/usr/bin/env python3
"""Build-time only: reproduce lead_eval's operating history inside the workspace.

- lead_eval 1.4.2 monthly reports (as-of 2026-02-01 .. 2026-07-01), re-implemented here: the 1.x population (intake
  exploration holdout), with labels from CRM opportunities only (sales-led conversions; 1.x predates self-serve
  attribution in the lifecycle rollup), so the history is a snapshot of a slightly different outcome definition.
- lead_eval 2.0.x reports for 2026-08-01 and 2026-09-01: the actual workspace pipeline.
- Scheduler log and a RevOps inbound-conversion note computed from the data.
Deleted from the image after the build.
"""
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "src"))
from lead_eval.config import load_config  # noqa: E402
from lead_eval.metrics import compute_metrics  # noqa: E402
from lead_eval.pipeline import run_evaluation  # noqa: E402
from lead_eval.report import write_report  # noqa: E402

cfg = load_config(ROOT / "config/evaluation.toml")
con = sqlite3.connect(ROOT / "data/revops.db")
leads = pd.read_sql_query("SELECT lead_id, created_at, source, intake_status FROM leads", con, parse_dates=["created_at"])
scores = pd.read_sql_query("SELECT lead_id, score FROM lead_scores WHERE model_version='lsm-3.2'", con)
ev = pd.read_sql_query("SELECT lead_id, routed_at, routing_event_id, policy FROM routing_events", con)
conv = pd.read_sql_query("SELECT lead_id, closed_won_at, channel FROM conversions", con, parse_dates=["closed_won_at"])
first = ev.sort_values(["lead_id", "routed_at", "routing_event_id"]).drop_duplicates("lead_id")
holdout_ids = set(first.loc[first.policy == "exploration_holdout", "lead_id"])

history = []
for month in range(2, 8):
    as_of = date(2026, month, 1)
    a = pd.Timestamp(as_of)
    lo, hi = a - pd.Timedelta(days=240), a - pd.Timedelta(days=60)
    c = leads[(leads.intake_status == "accepted") & (leads.created_at >= lo) & (leads.created_at <= hi)
              & leads.lead_id.isin(holdout_ids)].merge(scores, on="lead_id")
    won = c.merge(conv[conv.channel == "sales_led"], on="lead_id", how="left")
    won = won[(won.closed_won_at - won.created_at) <= pd.Timedelta(days=60)]
    c["label"] = c.lead_id.isin(set(won.lead_id)).astype(int)
    m = compute_metrics(c, cfg.n_bins, cfg.target_conversion_rate)
    m.pop("by_source", None)  # added in 2.0.3
    write_report(ROOT / "reports", as_of, {"as_of": as_of.isoformat(), "model_version": "lsm-3.2", "code_version": "1.4.2",
                                           "window_start": str(lo), "matured_before": str(hi), **m})
    history.append((as_of, "1.4.2", m))
for as_of in (date(2026, 8, 1), date(2026, 9, 1)):
    r = run_evaluation(cfg, as_of)
    if as_of == date(2026, 8, 1):  # the August run predates 2.0.3 (by_source)
        r = {k: v for k, v in r.items() if k != "by_source"}
        r["code_version"] = "2.0.0"
        path = ROOT / "reports/model_monitoring/lead_score_eval_2026-08-01.json"
        rep = json.loads(path.read_text())
        rep.pop("by_source", None)
        rep["code_version"] = "2.0.0"
        path.write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")
    history.append((as_of, r["code_version"], r))

logs = ROOT / "logs"
logs.mkdir(exist_ok=True)
with open(logs / "scheduler_runs.csv", "w") as fh:
    fh.write("run_id,job,as_of,started_at,status,code_version,n_leads,roc_auc\n")
    for i, (as_of, ver, m) in enumerate(history, 1):
        fh.write(f"le-{1200 + i},lead_eval_monthly,{as_of},{as_of.replace(day=2)}T05:00:00Z,success,{ver},{m['n_leads']},{m['roc_auc']:.4f}\n")

# RevOps monthly inbound conversion (all accepted leads, 60-day conversion by creation month)
acc = leads[leads.intake_status == "accepted"].copy()
won = acc.merge(conv, on="lead_id", how="left")
won = won[(won.closed_won_at - won.created_at) <= pd.Timedelta(days=60)]
acc["won60"] = acc.lead_id.isin(set(won.lead_id))
acc["month"] = acc.created_at.dt.strftime("%Y-%m")
tab = acc[(acc.month >= "2026-01") & (acc.month <= "2026-06")].groupby("month").agg(leads=("lead_id", "size"), rate=("won60", "mean"))
lines = "\n".join(f"| {m} | {int(r.leads):,} | {r.rate:.1%} |" for m, r in tab.iterrows())
(ROOT / "notes/2026-09-03_revops_inbound_conversion.md").write_text(f"""# Inbound conversion - monthly check

From: RevOps Analytics (inbound funnel), 2026-09-03.

60-day closed-won rate of accepted inbound leads by creation month (all leads, from `conversions`):

| Creation month | Accepted leads | Converted within 60 days |
|----------------|---------------:|-------------------------:|
{lines}

June lead volume includes the webinar series. The router threshold moved from 0.30 to 0.22 on 2026-06-15; June
cohorts are the first with the lower threshold.
""")
dep = [
    "2025-02-17T09:12:00Z,lead_eval,1.0.0,First monthly lead-score evaluation,RA-401",
    "2025-03-03T08:00:00Z,lead-router,router-2025.03,Champion lsm-3.2 live for routing,RS-212",
    "2025-11-03T10:40:00Z,lead_eval,1.4.0,recommended_threshold in report,RA-455",
    "2026-01-12T11:05:00Z,lead_eval,1.4.2,Stable bin tie-breaking,RA-470",
    "2026-06-01T07:30:00Z,lead-scoring,lsm-3.3-shadow,Challenger scores logged in shadow mode,DS-133",
    "2026-06-01T09:00:00Z,marketing,webinar-series-2026-06,June webinar series (lead volume +60%),MKT-102",
    "2026-06-15T08:00:00Z,lead-router,router-2026.06,Threshold 0.30 -> 0.22 (SDR headcount +2); unworked leads from the last 14 days re-evaluated,RS-240",
    "2026-06-22T18:00:00Z,revops-data,lifecycle-v2,RevOps lifecycle v2 rollup (all accepted leads),RA-512",
    "2026-07-01T09:00:00Z,sdr-org,pod-3,Two SDRs onboarded (sdr.garcia, sdr.hale),SDR-40",
    "2026-07-06T10:22:00Z,lead_eval,2.0.0,Lifecycle v2 outcomes; evaluation population expanded,RA-512",
    "2026-08-11T13:48:00Z,lead_eval,2.0.3,by_source breakdown,RA-531",
]
(logs / "deployments.csv").write_text("deployed_at,service,version,summary,ticket\n" + "\n".join(dep) + "\n")
print(json.dumps([(str(a), v, round(m["roc_auc"], 4), m["n_leads"], m["recommended_threshold"]) for a, v, m in history]))
