#!/usr/bin/env python3
"""Build-time only: reproduce the renewal-risk operating history inside the workspace.

1. v2.3 (Q3 2025 retrain, as of 2025-08-15): trained on correct point-in-time features (the daily
   snapshot tables still existed), v2.3 model spec. Report + model kept for monitoring.
2. v2.4 (Q1 2026 retrain, as of 2026-02-15): the actual workspace pipeline run.
3. Production scoring 2025-09-01..2026-05-17: each day's due renewals scored with the live model on
   the information available that day (what the production job saw), and live performance
   monitoring on decided renewals.
4. Experiment notes and Sales feedback filled from those results.
Deleted from the image after the build.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(sys.argv[1])
BUILD = Path(__file__).resolve().parent
sys.path.insert(0, str(BUILD))
sys.path.insert(0, str(ROOT / "src"))
import pit_reference as pit  # noqa: E402
from renewal_risk.config import load_config  # noqa: E402
from renewal_risk.model.evaluate import evaluate  # noqa: E402
from renewal_risk.pipeline import run_training  # noqa: E402
from renewal_risk.reporting import write_report  # noqa: E402

cfg = load_config(ROOT / "config/pipeline.toml")
data = pit.load(ROOT)
accounts = pd.DataFrame([{"account_id": a, "segment": v["segment"]} for a, v in data["accounts"].items()])
F = pit.FEATURE_COLUMNS

# ---------------------------------------------------------------- v2.3
F23 = [c for c in F if c != "open_expansion_opps"]          # v2.3 feature set (expansion feature added in v2.4)
ex23 = pit.build_examples(data, date(2025, 8, 15), train_window_days=730)  # v2.3: 2-year training window
f23 = pit.build_features(data, ex23)
df23 = pd.DataFrame([{**e, **f23[e["contract_id"]]} for e in ex23])
tr = df23[df23.split == "train"]
v23 = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(C=0.5, max_iter=2000))])
v23.fit(tr[F23].to_numpy(float), tr.label)
ev = df23[df23.split == "eval"].reset_index(drop=True)
p23 = ev[["contract_id", "account_id", "prediction_date", "label"]].copy()
p23["score"] = v23.predict_proba(ev[F23].to_numpy(float))[:, 1]
m23 = evaluate(p23.merge(accounts, on="account_id"), 10)
write_report(ROOT / "reports", date(2025, 8, 15), {
    "model_version": "renewal-risk-v2.3", "code_version": "2.3.4", "as_of": "2025-08-15", "n_train": int(len(tr)),
    "train_churn_rate": round(float(tr.label.mean()), 6), "feature_columns": F23, **m23})
(ROOT / "artifacts/model").mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- v2.4 (actual pipeline)
r24 = run_training(cfg, date(2026, 2, 15))
v24 = joblib.load(ROOT / "artifacts/model/renewal_risk.joblib")

# ---------------------------------------------------------------- production scoring history
import sqlite3  # noqa: E402
_con = sqlite3.connect(ROOT / "data/warehouse.db")
outcome = {c: o for c, o in _con.execute("SELECT contract_id, outcome FROM renewal_outcomes WHERE decided_at < '2026-08-10 00:00:00'")}
_con.close()
rows = []
day = date(2025, 9, 1)
while day <= date(2026, 5, 17):
    if date(2026, 2, 1) <= day < date(2026, 3, 2):   # scoring paused between snapshot removal and v2.4 go-live
        day += timedelta(days=1)
        continue
    due = (day + timedelta(days=90)).isoformat()
    batch = [dict(contract_id=c, account_id=a, renewal_date=r, prediction_date=day.isoformat(), label=None, split="live",
                  seats=s, arr_usd=arr, plan=pl)
             for c, a, st, r, s, arr, pl in data["contracts"] if r == due and st < day.isoformat()]
    if batch:
        fx = pit.build_features(data, batch)
        live24 = day >= date(2026, 3, 2)
        cols = F if live24 else F23
        X = np.array([[fx[b["contract_id"]][c] for c in cols] for b in batch], dtype=float)
        model, version = (v24, "renewal-risk-v2.4") if live24 else (v23, "renewal-risk-v2.3")
        scores = model.predict_proba(X)[:, 1]
        for b, s in zip(batch, scores):
            rows.append(dict(score_date=day.isoformat(), contract_id=b["contract_id"], account_id=b["account_id"],
                             renewal_date=b["renewal_date"], model_version=version, score=round(float(s), 6)))
    day += timedelta(days=1)
scores = pd.DataFrame(rows)
mon = ROOT / "reports/monitoring"
mon.mkdir(parents=True, exist_ok=True)
scores.to_csv(mon / "production_scores.csv", index=False)

scores["outcome"] = scores["contract_id"].map(outcome)
decided = scores[scores["outcome"].notna()].copy()
decided["label"] = (decided["outcome"] == "churned").astype(int)
live = {}
for version, g in decided.groupby("model_version"):
    low = g[g.score < g.score.quantile(0.3)]
    live[version] = {
        "score_dates": [g.score_date.min(), g.score_date.max()], "n_decided": int(len(g)),
        "churn_rate": round(float(g.label.mean()), 4), "roc_auc": round(float(roc_auc_score(g.label, g.score)), 4),
        "mean_score": round(float(g.score.mean()), 4),
        "churn_rate_in_lowest_30pct_scores": round(float(low.label.mean()), 4),
    }
(mon / "live_performance_2026-08-10.json").write_text(json.dumps({
    "generated_at": "2026-08-10T06:00:00Z",
    "definition": "production scores joined to renewal outcomes decided by 2026-08-10; one score per renewal",
    "models": live}, indent=2) + "\n")
v3, v4 = live["renewal-risk-v2.3"], live["renewal-risk-v2.4"]
(mon / "live_performance_2026-08-10.md").write_text(f"""# Live performance - renewal-risk (2026-08-10)

Production scores joined to decided renewals. One score per renewal (score date = renewal - 90 days).

| Model | Score dates | Decided renewals | Churn rate | Live ROC AUC | Mean score | Churn rate in lowest 30% of scores |
|-------|-------------|-----------------:|-----------:|-------------:|-----------:|-----------------------------------:|
| v2.3 | {v3['score_dates'][0]} - {v3['score_dates'][1]} | {v3['n_decided']} | {v3['churn_rate']:.1%} | {v3['roc_auc']:.3f} | {v3['mean_score']:.3f} | {v3['churn_rate_in_lowest_30pct_scores']:.1%} |
| v2.4 | {v4['score_dates'][0]} - {v4['score_dates'][1]} | {v4['n_decided']} | {v4['churn_rate']:.1%} | {v4['roc_auc']:.3f} | {v4['mean_score']:.3f} | {v4['churn_rate_in_lowest_30pct_scores']:.1%} |

Offline evaluation at training time: v2.3 ROC AUC {m23['roc_auc']:.3f} (as of 2025-08-15); v2.4 ROC AUC {r24['roc_auc']:.3f} (as of 2026-02-15).
Note: v2.4 live sample covers renewals due June-mid August only.
""")

# ---------------------------------------------------------------- notes
m23_ntrain = int(len(tr))
(ROOT / "notes/experiments").mkdir(parents=True, exist_ok=True)
(ROOT / "notes/experiments/2026-02-16_v2.4_retrain.md").write_text(f"""# v2.4 retrain notes (as of 2026-02-15)

Author: revenue data science. Ticket RA-DS-298 / RA-DS-311 / RA-DS-305 / RA-DS-307.

## What changed vs v2.3
- CRM and CS features now read the CRM v3 objects (snapshot tables are gone). v3 data looks much
  cleaner than the snapshots: no duplicate daily rows, no gaps on weekends.
- `class_weight = "balanced"`: churners are ~{r24['train_churn_rate']:.0%} of training examples; the unweighted model
  under-ranked small churners.
- Quantile winsorization instead of hand-set caps (usage outliers from API-heavy customers).
- 3-year training window (was 2): {r24['n_train']} training examples.
- New feature `open_expansion_opps`.
- scikit-learn 1.5.2.

## Results
| | v2.3 (2025-08-15) | v2.4 (2026-02-15) |
|---|---|---|
| ROC AUC | {m23['roc_auc']:.3f} | {r24['roc_auc']:.3f} |
| PR AUC | {m23['pr_auc']:.3f} | {r24['pr_auc']:.3f} |
| Brier | {m23['brier']:.3f} | {r24['brier']:.3f} |
| Eval examples | {m23['n_eval']} | {r24['n_eval']} |
| Training examples | {m23_ntrain} | {r24['n_train']} |

Big jump, consistent across segments. Balanced weights + the longer window explain part of it; the new
expansion-pipeline feature and cleaner CRM data probably the rest. Calibration is looser than v2.3 (expected with class
weighting). Promote after CS review.
""")
low24 = decided[(decided.model_version == "renewal-risk-v2.4") & (decided.label == 1)].sort_values("score").head(6)
lines = "\n".join(f"| {r.account_id} | {r.renewal_date} | {r.score:.3f} |" for r in low24.itertuples())
(ROOT / "notes/sales").mkdir(parents=True, exist_ok=True)
(ROOT / "notes/sales/2026-08-07_renewal_risk_feedback.md").write_text(f"""# Renewal-risk scores - feedback from Sales & CS (Q2/Q3 renewals)

From: RevOps (renewals desk), 2026-08-07. To: Revenue Data Science.

Since the new model went live in March we have been prioritizing save plays by the risk score. It
isn't working. Accounts the model marked as safe are churning, and the "high risk" list is full of
accounts that were never in danger. The CSMs have stopped trusting it; a few regions went back to
their own spreadsheets.

Some of the churned accounts that the model rated among the safest when they were scored:

| Account | Renewal date | Score at T-90 |
|---------|--------------|---------------|
{lines}

The v2.4 launch deck said the model was far better than the old one. What happened? We need scores
we can use for the Q4 renewal cohort - the retrain is due now.
""")
print(json.dumps({"v2.3_offline_auc": m23["roc_auc"], "v2.4_offline_auc": r24["roc_auc"], "live": live}, indent=1))
