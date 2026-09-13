"""Training/evaluation examples.

One example per decided contract renewal. Each renewal is scored once, `horizon_days` before its
renewal date (the prediction date), exactly as the production scoring job does. The label is
whether the customer churned at that renewal. See docs/model_card_renewal_risk.md.
"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from renewal_risk.config import Config
from renewal_risk.sources.warehouse import Warehouse

EXAMPLE_COLUMNS = ["contract_id", "account_id", "renewal_date", "prediction_date", "label", "split"]


def build_examples(wh: Warehouse, cfg: Config, as_of: date) -> pd.DataFrame:
    as_of_ts = pd.Timestamp(as_of)
    label_cutoff = pd.Timestamp(as_of - timedelta(days=cfg.label_grace_days))
    eval_start = label_cutoff - pd.Timedelta(days=cfg.eval_window_days)
    train_start = eval_start - pd.Timedelta(days=cfg.train_window_days)

    known = wh.renewal_outcomes[wh.renewal_outcomes["synced_at"] < as_of_ts][["contract_id", "outcome"]]
    ex = wh.contracts.merge(known, on="contract_id", how="inner")
    ex = ex[(ex["renewal_date"] > train_start) & (ex["renewal_date"] <= label_cutoff)].copy()
    ex["prediction_date"] = ex["renewal_date"] - pd.Timedelta(days=cfg.horizon_days)
    ex = ex[ex["start_date"] < ex["prediction_date"]]
    ex["label"] = (ex["outcome"] == "churned").astype(int)
    ex["split"] = (ex["renewal_date"] > eval_start).map({True: "eval", False: "train"})
    ex = ex.sort_values(["prediction_date", "contract_id"]).reset_index(drop=True)
    return ex[EXAMPLE_COLUMNS + ["seats", "arr_usd", "plan"]]
