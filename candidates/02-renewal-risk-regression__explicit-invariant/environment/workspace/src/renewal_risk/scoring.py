"""Production scoring: score renewals due `horizon_days` after the score date."""
from __future__ import annotations

import logging
from datetime import date, timedelta

import joblib
import pandas as pd

from renewal_risk.config import Config
from renewal_risk.features.build import build_features
from renewal_risk.model.train import predict
from renewal_risk.sources.warehouse import load_warehouse

log = logging.getLogger("renewal_risk.scoring")


def score_renewals(cfg: Config, score_date: date) -> pd.DataFrame:
    wh = load_warehouse(cfg.warehouse_db)
    due = pd.Timestamp(score_date + timedelta(days=cfg.horizon_days))
    decided = set(wh.renewal_outcomes["contract_id"])
    ex = wh.contracts[(wh.contracts["renewal_date"] == due) & ~wh.contracts["contract_id"].isin(decided)].copy()
    ex["prediction_date"] = pd.Timestamp(score_date)
    feats = build_features(ex.reset_index(drop=True), wh)
    model = joblib.load(cfg.artifacts_dir / "model" / "renewal_risk.joblib")
    out = ex[["contract_id", "account_id"]].reset_index(drop=True)
    out["score_date"] = score_date.isoformat()
    out["score"] = predict(model, feats) if len(feats) else []
    path = cfg.artifacts_dir / "scores" / f"scores_{score_date.isoformat()}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    log.info("scored %d renewals due %s -> %s", len(out), due.date(), path)
    return out
