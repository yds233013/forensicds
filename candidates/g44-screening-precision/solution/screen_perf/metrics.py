"""Screen performance from weighted review evidence, and the precision the contract is written on."""
from __future__ import annotations

import pandas as pd


def weighted_confusion(df: pd.DataFrame) -> dict:
    flag = df["screen_decision"] == "FLAG"
    pos = df["outcome"] == "FRAUD"
    w = df["weight"]
    return {"tp": float(w[flag & pos].sum()), "fp": float(w[flag & ~pos].sum()),
            "fn": float(w[~flag & pos].sum()), "tn": float(w[~flag & ~pos].sum())}


def rates(c: dict) -> tuple:
    se = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 0.0
    sp = c["tn"] / (c["tn"] + c["fp"]) if (c["tn"] + c["fp"]) else 0.0
    return se, sp


def precision(c: dict) -> float:
    return c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 0.0


def precision_at_rate(se: float, sp: float, prevalence: float) -> float:
    """Precision the same screen would show in a population with this fraud rate.

    Detection performance (sensitivity, specificity) is a property of the screen; precision is not -
    it depends on how much fraud is in the traffic the screen sees.
    """
    d = se * prevalence + (1.0 - sp) * (1.0 - prevalence)
    return se * prevalence / d if d else 0.0
