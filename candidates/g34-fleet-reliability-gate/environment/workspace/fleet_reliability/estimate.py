"""Service-life estimation.

House method since the 2024 reliability review: for each outcome we follow units from
commissioning and stop following a unit when something other than that outcome ends its record,
which is the standard way to handle an incomplete service history.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _life_table(exit_age: np.ndarray, is_event: np.ndarray, horizon: float) -> float:
    """Probability of the event by `horizon`, following units until their record ends."""
    order = np.argsort(exit_age)
    t, e = exit_age[order], is_event[order]
    surviving, n = 1.0, len(t)
    i = 0
    while i < n and t[i] <= horizon:
        q = t[i]
        j = i
        while j < n and t[j] == q:
            j += 1
        d = int(e[i:j].sum())
        surviving *= 1.0 - d / (n - i)
        i = j
    return 1.0 - surviving


def outcome_rate(df: pd.DataFrame, wo_type: str, horizon: float) -> float:
    return _life_table(df["exit_age"].to_numpy(), (df["wo_type"] == wo_type).to_numpy(), horizon)


def at_risk(df: pd.DataFrame, age: float) -> int:
    return int((df["exit_age"] > age).sum())
