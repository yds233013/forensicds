"""Independent reference for Task 03 (pure Python + sqlite3; shares no code with the workspace package).

Evaluation population (from the model card, router design and evaluation definition): accepted leads whose
60-day outcome window closed by the as-of date, created within the 180-day window, that were assigned to the
exploration holdout at intake (initial routing decision), whether or not an SDR reached them. Label: closed-won
within 60 days of creation. Score: champion intake score.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

F = "%Y-%m-%d %H:%M:%S"
CHAMPION = "lsm-3.2"
OUTCOME_DAYS = 60
WINDOW_DAYS = 180
N_BINS = 10
TARGET = 0.08


def cohort(root: Path, as_of: date) -> list[dict]:
    con = sqlite3.connect(f"file:{Path(root) / 'data/revops.db'}?mode=ro", uri=True)
    as_of_dt = datetime.combine(as_of, datetime.min.time())
    matured_before = as_of_dt - timedelta(days=OUTCOME_DAYS)
    window_start = matured_before - timedelta(days=WINDOW_DAYS)
    initial = {}
    for lid, _t, _eid, policy in con.execute("SELECT lead_id, routed_at, routing_event_id, policy FROM routing_events "
                                             "ORDER BY lead_id, routed_at, routing_event_id"):
        initial.setdefault(lid, policy)
    score = dict(con.execute("SELECT lead_id, score FROM lead_scores WHERE model_version = ?", (CHAMPION,)))
    conv = defaultdict(list)
    for lid, t in con.execute("SELECT lead_id, closed_won_at FROM conversions"):
        conv[lid].append(datetime.strptime(t, F))
    rows = []
    for lid, created, source, status in con.execute("SELECT lead_id, created_at, source, intake_status FROM leads"):
        if status != "accepted":
            continue
        c = datetime.strptime(created, F)
        if not (window_start <= c <= matured_before):
            continue
        if initial.get(lid) != "exploration_holdout":
            continue
        label = int(any(t - c <= timedelta(days=OUTCOME_DAYS) for t in conv[lid]))
        rows.append(dict(lead_id=lid, created_at=created, source=source, score=score[lid], label=label))
    con.close()
    rows.sort(key=lambda r: r["lead_id"])
    return rows


def auc(labels: list[int], scores: list[float]) -> float:
    pairs = sorted(zip(scores, labels))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2.0 + 1
        i = j + 1
    pos = sum(y for _s, y in pairs)
    return (sum(r for r, (_s, y) in zip(ranks, pairs) if y) - pos * (pos + 1) / 2.0) / (pos * (n - pos))


def metrics(rows: list[dict]) -> dict:
    n = len(rows)
    y = [r["label"] for r in rows]
    overall = sum(y) / n
    ordered = sorted(rows, key=lambda r: (r["score"], r["lead_id"]))
    size, extra = divmod(n, N_BINS)
    bins, start = [], 0
    for i in range(N_BINS):
        k = size + (1 if i < extra else 0)
        bins.append(ordered[start:start + k])
        start += k
    cal = [dict(bin=i + 1, n=len(b), min_score=min(r["score"] for r in b), max_score=max(r["score"] for r in b),
                mean_score=sum(r["score"] for r in b) / len(b), conversion_rate=sum(r["label"] for r in b) / len(b))
           for i, b in enumerate(bins)]
    rec = None
    for row in reversed(cal):
        if row["conversion_rate"] >= TARGET:
            rec = row["min_score"]
        else:
            break
    by_source = defaultdict(list)
    for r in rows:
        by_source[r["source"]].append(r["label"])
    return dict(n_leads=n, n_converted=sum(y), conversion_rate=overall, roc_auc=auc(y, [r["score"] for r in rows]),
                top_decile_conversion_rate=cal[-1]["conversion_rate"], top_decile_lift=cal[-1]["conversion_rate"] / overall,
                calibration=cal, recommended_threshold=rec,
                by_source={s: dict(n=len(v), conversion_rate=sum(v) / len(v)) for s, v in by_source.items()})
