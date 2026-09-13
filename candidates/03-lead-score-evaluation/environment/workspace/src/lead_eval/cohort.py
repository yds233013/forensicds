"""Evaluation cohort: one row per lead evaluated at the as-of date."""
from __future__ import annotations

from datetime import date

import pandas as pd

from lead_eval.config import Config
from lead_eval.sources import RevOps

COHORT_COLUMNS = ["lead_id", "created_at", "source", "score", "label"]


def evaluation_window(cfg: Config, as_of: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[window_start, matured_before]: leads created at or after window_start whose outcome window has fully
    closed by the as-of date (created_at + outcome_window_days <= as_of 00:00 UTC)."""
    as_of_ts = pd.Timestamp(as_of)
    matured_before = as_of_ts - pd.Timedelta(days=cfg.outcome_window_days)
    window_start = matured_before - pd.Timedelta(days=cfg.eval_window_days)
    return window_start, matured_before


def build_cohort(src: RevOps, cfg: Config, as_of: date) -> pd.DataFrame:
    window_start, matured_before = evaluation_window(cfg, as_of)
    leads = src.leads[src.leads["intake_status"] == "accepted"]
    leads = leads[(leads["created_at"] >= window_start) & (leads["created_at"] <= matured_before)]

    scores = src.scores[src.scores["model_version"] == cfg.champion_model][["lead_id", "score"]]
    outcomes = src.lifecycle[["lead_id", "converted_60d"]]

    cohort = (leads.merge(scores, on="lead_id", how="inner", validate="one_to_one")
                   .merge(outcomes, on="lead_id", how="left", validate="one_to_one"))
    cohort["label"] = cohort["converted_60d"].fillna(0).astype(int)
    return cohort.sort_values("lead_id").reset_index(drop=True)[COHORT_COLUMNS]
