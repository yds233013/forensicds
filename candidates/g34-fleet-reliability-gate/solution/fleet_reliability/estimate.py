"""Service-life estimation.

Two different questions are asked of the same service histories and they are not the same
statistical object.

Aftermarket asks what actually happens to a unit's ORIGINAL assembly under the current maintenance
programme: it either fails in service, or is exchanged at the scheduled overhaul, or leaves with
the unit, or is still running at 36 months. Those are four mutually exclusive outcomes of the same
units and they must sum to one. An overhaul or a retirement is not an incomplete record - it is a
different outcome, and it removes the original assembly from the population that can still fail.

Engineering asks how long an assembly lasts in service. There the overhaul and the retirement are
exactly what makes a record incomplete: the assembly was taken out before it could fail, and the
SOP says that removal is scheduled on age and on site economics rather than on the condition of
the assembly, so following units until their record ends recovers the assembly life.

A telemetry outage is not a removal. The unit keeps running and keeps its original assembly, so it
stays in the population throughout.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

OUTCOMES = ("UNPL_FAIL", "PM_OVHL", "ASSET_RET")


def outcome_shares(df: pd.DataFrame, horizon: float) -> dict:
    """Share of the installed base whose original assembly meets each outcome by `horizon`.

    Walks the service histories in age order, keeping the running share of units still carrying
    their original assembly and attributing each removal to its own outcome.
    """
    t = df["exit_age"].to_numpy(float)
    kind = df["wo_type"].to_numpy(object)
    order = np.argsort(t)
    t, kind = t[order], kind[order]

    n = len(t)
    still = 1.0
    acc = {o: 0.0 for o in OUTCOMES}
    i = 0
    while i < n and t[i] <= horizon:
        q = t[i]
        j = i
        while j < n and t[j] == q:
            j += 1
        at_risk = n - i
        removed = 0
        for o in OUTCOMES:
            d = int((kind[i:j] == o).sum())
            if d:
                acc[o] += still * d / at_risk
                removed += d
        still *= 1.0 - removed / at_risk
        i = j
    acc["still_original"] = still
    return acc


def assembly_life_failure_rate(df: pd.DataFrame, horizon: float) -> float:
    """Engineering's quantity: failure of the assembly by `horizon`, with removals that took the
    assembly out before it could fail treated as incomplete records."""
    t = df["exit_age"].to_numpy(float)
    failed = (df["wo_type"].to_numpy(object) == "UNPL_FAIL")
    order = np.argsort(t)
    t, failed = t[order], failed[order]
    n = len(t)
    surviving = 1.0
    i = 0
    while i < n and t[i] <= horizon:
        q = t[i]
        j = i
        while j < n and t[j] == q:
            j += 1
        d = int(failed[i:j].sum())
        surviving *= 1.0 - d / (n - i)
        i = j
    return 1.0 - surviving


def at_risk(df: pd.DataFrame, age: float) -> int:
    return int((df["exit_age"] > age).sum())
