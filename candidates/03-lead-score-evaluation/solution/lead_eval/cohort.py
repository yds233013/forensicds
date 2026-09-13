"""Evaluation cohort: one row per lead evaluated at the as-of date.

The score estimates conversion *if a lead is worked by SDRs*, and the router decides which leads get worked
from that same score. Outcomes of leads the router sent to nurture are outcomes of not being worked, so
including them rewards the model for its own routing decisions. The only leads worked independently of score
are the exploration holdout, selected at random at intake. The evaluation population is therefore the
exploration holdout as assigned at intake (initial routing decision), including holdout leads that SDRs did not
reach, restricted to accepted leads in the evaluation window whose outcome window has closed.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from lead_eval.config import Config
from lead_eval.sources import RevOps

COHORT_COLUMNS = ["lead_id", "created_at", "source", "score", "label"]
HOLDOUT_POLICY = "exploration_holdout"


def evaluation_window(cfg: Config, as_of: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[window_start, matured_before]: leads created at or after window_start whose outcome window has fully
    closed by the as-of date (created_at + outcome_window_days <= as_of 00:00 UTC)."""
    as_of_ts = pd.Timestamp(as_of)
    matured_before = as_of_ts - pd.Timedelta(days=cfg.outcome_window_days)
    window_start = matured_before - pd.Timedelta(days=cfg.eval_window_days)
    return window_start, matured_before


def intake_assignment(routing_events: pd.DataFrame) -> pd.DataFrame:
    """One row per lead: the policy of its first routing decision."""
    ev = routing_events.sort_values(["lead_id", "routed_at", "routing_event_id"], kind="mergesort")
    return ev.drop_duplicates("lead_id", keep="first")[["lead_id", "policy"]].rename(columns={"policy": "intake_policy"})


def build_cohort(src: RevOps, cfg: Config, as_of: date) -> pd.DataFrame:
    window_start, matured_before = evaluation_window(cfg, as_of)
    leads = src.leads[src.leads["intake_status"] == "accepted"]
    leads = leads[(leads["created_at"] >= window_start) & (leads["created_at"] <= matured_before)]

    holdout = intake_assignment(src.routing_events)
    holdout = holdout[holdout["intake_policy"] == HOLDOUT_POLICY][["lead_id"]]
    leads = leads.merge(holdout, on="lead_id", how="inner", validate="one_to_one")

    scores = src.scores[src.scores["model_version"] == cfg.champion_model][["lead_id", "score"]]
    outcomes = src.lifecycle[["lead_id", "converted_60d"]]
    cohort = (leads.merge(scores, on="lead_id", how="inner", validate="one_to_one")
                   .merge(outcomes, on="lead_id", how="left", validate="one_to_one"))
    cohort["label"] = cohort["converted_60d"].fillna(0).astype(int)
    return cohort.sort_values("lead_id").reset_index(drop=True)[COHORT_COLUMNS]
