"""Analysis units for the XP-231 readout, per the pre-registered plan (docs/experiments/XP-231_plan.md).

Unit = workspace, analyzed in the arm it was assigned (first assignment log row; later rows from SDK retries or
cache incidents do not change it), whether or not its members saw or logged the experience. Population = eligible
workspaces (self-serve signup, not internal) assigned at least `outcome_window_days` before the analysis date.
Outcome = workspace activation: at least `min_active_users` distinct users with a core action in the workspace in
[assigned_at, assigned_at + window).

Exposure events are not used: the arms log exposures at different points (dashboard load vs checklist mount), so
exposed populations are not comparable, and the SDK's cached variant can differ from a workspace's assignment.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from xp_analysis.config import Config
from xp_analysis.sources import Product

UNIT_COLUMNS = ["unit_id", "stratum", "arm", "activated"]


def analysis_cutoff(cfg: Config, analysis_date: date) -> pd.Timestamp:
    """Units must have a complete outcome window before the analysis date."""
    return pd.Timestamp(analysis_date) - pd.Timedelta(days=cfg.outcome_window_days)


def build_units(src: Product, cfg: Config, analysis_date: date) -> pd.DataFrame:
    window = pd.Timedelta(days=cfg.outcome_window_days)
    a = src.assignments[src.assignments["unit_type"] == "workspace"]
    a = a.sort_values(["unit_id", "assigned_at", "assignment_id"], kind="mergesort").drop_duplicates("unit_id")
    a = a[a["assigned_at"] <= analysis_cutoff(cfg, analysis_date)]

    ws = src.workspaces.set_index("workspace_id")
    a = a[(a["unit_id"].map(ws["signup_channel"]) == "self_serve") & (a["unit_id"].map(ws["is_internal"]) == 0)]

    ev = src.events.merge(a[["unit_id", "assigned_at"]], left_on="workspace_id", right_on="unit_id")
    ev = ev[(ev["event_at"] >= ev["assigned_at"]) & (ev["event_at"] < ev["assigned_at"] + window)]
    active_users = ev.groupby("workspace_id")["user_id"].nunique()

    units = pd.DataFrame({
        "unit_id": a["unit_id"],
        "stratum": a["stratum"],
        "arm": a["variant"],
        "activated": (a["unit_id"].map(active_users).fillna(0) >= cfg.min_active_users).astype(int),
    })
    return units.sort_values("unit_id").reset_index(drop=True)[UNIT_COLUMNS]
