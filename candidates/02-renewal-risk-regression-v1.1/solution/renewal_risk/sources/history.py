"""Point-in-time reconstruction of record state from append-only field history.

A training example must only see what the production scorer could have seen: the warehouse as
loaded before 00:00 UTC on the prediction date. For a history table (one row per tracked-field
change, including one row per field at record creation) the state of a record at a cutoff is,
for every field, the value of the latest change that had been loaded (`synced_at`) strictly
before the cutoff. A record whose creation had not been loaded yet does not exist at the cutoff.
"""
from __future__ import annotations

import pandas as pd


def state_as_of(history: pd.DataFrame, entity: str, requests: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """Return one row per request with columns `request_id`, `exists` and one column per field.

    history:  columns [entity, field, new_value, changed_at, synced_at]
    requests: columns [request_id, entity, cutoff]
    """
    req = requests[["request_id", entity, "cutoff"]].copy()
    req["cutoff"] = pd.to_datetime(req["cutoff"]).astype("datetime64[ns]")
    req = req.sort_values("cutoff", kind="stable")
    out = requests[["request_id"]].copy()

    history = history.assign(synced_at=pd.to_datetime(history["synced_at"]).astype("datetime64[ns]"))
    history = history.sort_values(["synced_at", "changed_at"], kind="stable")
    loaded = history[[entity, "synced_at"]]
    first = pd.merge_asof(req, loaded.rename(columns={"synced_at": "_seen"}), left_on="cutoff", right_on="_seen",
                          by=entity, direction="backward", allow_exact_matches=False)
    out = out.merge(first[["request_id", "_seen"]], on="request_id", how="left")
    out["exists"] = out.pop("_seen").notna()

    for field in fields:
        h = history.loc[history["field"] == field, [entity, "new_value", "synced_at"]]
        m = pd.merge_asof(req, h, left_on="cutoff", right_on="synced_at", by=entity, direction="backward",
                          allow_exact_matches=False)
        out = out.merge(m[["request_id", "new_value"]].rename(columns={"new_value": field}), on="request_id", how="left")
        out.loc[~out["exists"], field] = None
    return out
