"""Analysis units and outcomes for an experiment readout."""
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
    exp = src.exposures[src.exposures["exposed_at"] <= analysis_cutoff(cfg, analysis_date)]
    first = exp.sort_values(["user_id", "exposed_at", "exposure_id"], kind="mergesort").drop_duplicates("user_id")

    # eligibility (plan): self-serve workspaces, no internal test workspaces
    ws = src.workspaces.set_index("workspace_id")
    first = first[(first["workspace_id"].map(ws["signup_channel"]) == "self_serve")
                  & (first["workspace_id"].map(ws["is_internal"]) == 0)]

    # stratum as logged by the assignment service
    a = src.assignments.sort_values(["unit_id", "assigned_at", "assignment_id"], kind="mergesort").drop_duplicates("unit_id")
    first = first.assign(stratum=first["workspace_id"].map(a.set_index("unit_id")["stratum"]))

    # user activation: a core action within the outcome window after first exposure
    ev = src.events.merge(first[["user_id", "workspace_id", "exposed_at"]], on=["user_id", "workspace_id"])
    ev = ev[(ev["event_at"] >= ev["exposed_at"]) & (ev["event_at"] < ev["exposed_at"] + window)]
    active = set(ev["user_id"])

    units = pd.DataFrame({
        "unit_id": first["user_id"],
        "stratum": first["stratum"],
        "arm": first["variant"],
        "activated": first["user_id"].isin(active).astype(int),
    })
    return units.sort_values("unit_id").reset_index(drop=True)[UNIT_COLUMNS]
