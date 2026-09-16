"""Replay a candidate ranker on logged responses (offline gate, release 1.4).

For every logged response with a candidate list, the ranker's top five titles are compared with the titles that were
actually shown. Slots where the candidate ranker agrees with the log are scored with the logged outcome.
"""
from __future__ import annotations

import pandas as pd

from recs_eval import logs

SLOTS = 5
MODEL_SCORES = {"v6": "score_v6", "v7": "score_v7", "v7_pd": "score_v7_pd"}


def target_slates(cand: pd.DataFrame) -> pd.DataFrame:
    """Top five titles per response for each ranker, after the rules layer's suppressions."""
    cand = cand[cand["filter_reason"].isna()]
    out = []
    for policy, col in MODEL_SCORES.items():
        top = (cand.sort_values(["serve_id", col], ascending=[True, False])
                   .groupby("serve_id").head(SLOTS).copy())
        top["position"] = top.groupby("serve_id").cumcount() + 1
        top["policy"] = policy
        out.append(top[["serve_id", "policy", "position", "item_id"]])
    return pd.concat(out, ignore_index=True)


def matched(imp: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Impressions whose title the candidate ranker would also have shown somewhere in the row."""
    keys = targets[["serve_id", "policy", "item_id"]].drop_duplicates()
    return imp.merge(keys, on=["serve_id", "item_id"], how="inner")
