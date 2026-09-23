"""Screen performance from the review evidence."""
from __future__ import annotations

import pandas as pd


def confusion(df: pd.DataFrame, label_col: str = "outcome", positive: str = "FRAUD") -> dict:
    flag = df["screen_decision"] == "FLAG"
    pos = df[label_col] == positive
    return {"tp": int((flag & pos).sum()), "fp": int((flag & ~pos).sum()),
            "fn": int((~flag & pos).sum()), "tn": int((~flag & ~pos).sum())}


def rates(c: dict) -> tuple:
    se = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) else 0.0
    sp = c["tn"] / (c["tn"] + c["fp"]) if (c["tn"] + c["fp"]) else 0.0
    return se, sp


def precision(c: dict) -> float:
    return c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) else 0.0
