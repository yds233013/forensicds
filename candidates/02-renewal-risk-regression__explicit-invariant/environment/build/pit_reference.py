"""Independent reference for Task 02: examples and point-in-time features.

Pure Python + sqlite3; shares no code with the workspace package. Implements the documented
example definition and feature dictionary with every feature computed from information that
had been loaded into the warehouse (`synced_at`) before 00:00 UTC on the prediction date.
"""
from __future__ import annotations

import bisect
import math
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

HORIZON_DAYS = 90
LABEL_GRACE_DAYS = 30
EVAL_WINDOW_DAYS = 270
TRAIN_WINDOW_DAYS = 1095
DAYS_PER_MONTH = 30.4375

CONTRACT = ["arr_usd_log", "seats_licensed", "plan_enterprise", "tenure_months", "prior_renewals"]
USAGE = ["active_user_ratio_4w", "active_user_trend_12w", "api_calls_4w_log", "logins_per_active_user_4w"]
SUPPORT = ["tickets_90d", "sev1_tickets_180d", "open_tickets_at_prediction"]
PIPELINE = ["has_renewal_opp", "renewal_stage_ordinal", "forecast_commit", "forecast_best_case", "forecast_omitted",
            "renewal_amount_ratio", "days_to_opp_close", "competitor_flagged", "open_expansion_opps"]
HEALTH = ["health_score", "health_red", "nps_last", "csm_sentiment_negative"]
FEATURE_COLUMNS = CONTRACT + USAGE + SUPPORT + PIPELINE + HEALTH
POINT_IN_TIME_SENSITIVE = PIPELINE + HEALTH

STAGE_ORDINAL = {"Closed Lost": 0, "Qualification": 1, "Discovery": 2, "Proposal": 3, "Negotiation": 4,
                 "Verbal": 5, "Closed Won": 6}
CLOSED = {"Closed Won", "Closed Lost"}


def _ts(day: date) -> str:
    return f"{day.isoformat()} 00:00:00"


class History:
    """Append-only field history -> state of an entity as loaded before a cutoff."""

    def __init__(self, rows):
        self.by_entity: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        for entity, field, new_value, changed_at, synced_at in rows:
            self.by_entity[entity].append((synced_at, changed_at, field, new_value))
        self.keys: dict[str, list[str]] = {}
        for entity, events in self.by_entity.items():
            events.sort(key=lambda e: (e[0], e[1]))  # load order, then commit order within a load
            self.keys[entity] = [e[0] for e in events]

    def state(self, entity: str, cutoff: str) -> dict | None:
        events = self.by_entity.get(entity)
        if not events:
            return None
        k = bisect.bisect_left(self.keys[entity], cutoff)  # events with synced_at < cutoff
        if k == 0:
            return None
        state: dict[str, str] = {}
        for _synced, _changed, field, value in events[:k]:
            state[field] = value
        return state


def load(root: Path):
    con = sqlite3.connect(f"file:{Path(root) / 'data/warehouse.db'}?mode=ro", uri=True)
    q = lambda sql: con.execute(sql).fetchall()  # noqa: E731
    data = dict(
        accounts={a: dict(segment=s, created=c) for a, s, c in q("SELECT account_id, segment, created_date FROM accounts")},
        contracts=q("SELECT contract_id, account_id, start_date, renewal_date, seats, arr_usd, plan FROM contracts"),
        outcomes=q("SELECT contract_id, account_id, outcome, synced_at FROM renewal_outcomes"),
        usage=q("SELECT account_id, week_start, active_users, api_calls, logins FROM usage_weekly"),
        tickets=q("SELECT account_id, opened_at, severity, closed_at FROM support_tickets"),
        opps=q("SELECT opportunity_id, account_id, contract_id, opportunity_type FROM crm_opportunities"),
        opp_hist=History(q("SELECT opportunity_id, field, new_value, changed_at, synced_at FROM crm_opportunity_field_history")),
        health_hist=History(q("SELECT account_id, field, new_value, changed_at, synced_at FROM cs_account_health_history")),
    )
    con.close()
    return data


def build_examples(data, as_of: date, train_window_days: int = TRAIN_WINDOW_DAYS) -> list[dict]:
    as_of_ts = _ts(as_of)
    label_cutoff = as_of - timedelta(days=LABEL_GRACE_DAYS)
    eval_start = label_cutoff - timedelta(days=EVAL_WINDOW_DAYS)
    train_start = eval_start - timedelta(days=train_window_days)
    outcome = {c: o for c, _a, o, s in data["outcomes"] if s < as_of_ts}
    out = []
    for cid, acc, start, renewal, seats, arr, plan in data["contracts"]:
        if cid not in outcome:
            continue
        r = date.fromisoformat(renewal)
        if not (train_start < r <= label_cutoff):
            continue
        p = r - timedelta(days=HORIZON_DAYS)
        if not date.fromisoformat(start) < p:
            continue
        out.append(dict(contract_id=cid, account_id=acc, renewal_date=renewal, prediction_date=p.isoformat(),
                        label=int(outcome[cid] == "churned"), split="eval" if r > eval_start else "train",
                        seats=seats, arr_usd=arr, plan=plan))
    out.sort(key=lambda e: (e["prediction_date"], e["contract_id"]))
    return out


def build_features(data, examples: list[dict]) -> dict[str, dict]:
    usage = defaultdict(list)
    for acc, wk, active, api, logins in data["usage"]:
        usage[acc].append((wk, active, api, logins))
    for v in usage.values():
        v.sort()
    tickets = defaultdict(list)
    for acc, opened, sev, closed in data["tickets"]:
        tickets[acc].append((opened, sev, closed))
    renewed = defaultdict(list)
    for _c, acc, o, s in data["outcomes"]:
        if o == "renewed":
            renewed[acc].append(s)
    renewal_opp = {}
    expansions = defaultdict(list)
    for oid, acc, cid, typ in data["opps"]:
        if typ == "renewal":
            renewal_opp[cid] = oid
        elif typ == "expansion":
            expansions[acc].append(oid)

    feats = {}
    for ex in examples:
        p = date.fromisoformat(ex["prediction_date"])
        cut = _ts(p)
        acc = ex["account_id"]
        f = {}
        # contract
        f["arr_usd_log"] = math.log1p(ex["arr_usd"])
        f["seats_licensed"] = float(ex["seats"])
        f["plan_enterprise"] = int(ex["plan"] == "Enterprise")
        f["tenure_months"] = (p - date.fromisoformat(data["accounts"][acc]["created"])).days / DAYS_PER_MONTH
        f["prior_renewals"] = sum(1 for s in renewed[acc] if s < cut)
        # usage: weeks that closed strictly before the prediction date
        weeks = [w for w in usage[acc] if date.fromisoformat(w[0]) + timedelta(days=7) < p]
        last4, last12 = weeks[-4:], weeks[-12:]
        if last4:
            f["active_user_ratio_4w"] = (sum(w[1] for w in last4) / len(last4)) / ex["seats"]
            f["api_calls_4w_log"] = math.log1p(sum(w[2] for w in last4))
            f["logins_per_active_user_4w"] = sum(w[3] for w in last4) / max(1, sum(w[1] for w in last4))
        else:
            f["active_user_ratio_4w"] = f["api_calls_4w_log"] = f["logins_per_active_user_4w"] = 0.0
        if len(last12) >= 3:
            ys = [w[1] / ex["seats"] for w in last12]
            xs = list(range(len(ys)))
            xm, ym = sum(xs) / len(xs), sum(ys) / len(ys)
            f["active_user_trend_12w"] = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / sum((x - xm) ** 2 for x in xs)
        else:
            f["active_user_trend_12w"] = 0.0
        # support
        t90 = t180 = still_open = 0
        cut_dt = datetime.fromisoformat(cut)
        for opened, sev, closed in tickets[acc]:
            if opened >= cut:
                continue
            age = cut_dt - datetime.fromisoformat(opened)
            if age <= timedelta(days=90):
                t90 += 1
            if age <= timedelta(days=180) and sev == "sev1":
                t180 += 1
            if closed is None or closed >= cut:
                still_open += 1
        f["tickets_90d"], f["sev1_tickets_180d"], f["open_tickets_at_prediction"] = t90, t180, still_open
        # renewal opportunity state as loaded before the prediction date
        state = data["opp_hist"].state(renewal_opp[ex["contract_id"]], cut) if ex["contract_id"] in renewal_opp else None
        if state is None:
            f.update(has_renewal_opp=0, renewal_stage_ordinal=-1, forecast_commit=0, forecast_best_case=0,
                     forecast_omitted=0, renewal_amount_ratio=1.0, days_to_opp_close=90, competitor_flagged=0)
        else:
            f["has_renewal_opp"] = 1
            f["renewal_stage_ordinal"] = STAGE_ORDINAL[state["stage"]]
            f["forecast_commit"] = int(state["forecast_category"] == "Commit")
            f["forecast_best_case"] = int(state["forecast_category"] == "Best Case")
            f["forecast_omitted"] = int(state["forecast_category"] == "Omitted")
            f["renewal_amount_ratio"] = float(state["amount_usd"]) / ex["arr_usd"]
            f["days_to_opp_close"] = (date.fromisoformat(state["close_date"]) - p).days
            f["competitor_flagged"] = int(bool(state.get("competitor")))
        open_exp = 0
        for oid in expansions[acc]:
            s = data["opp_hist"].state(oid, cut)
            if s is not None and s["stage"] not in CLOSED:
                open_exp += 1
        f["open_expansion_opps"] = open_exp
        # customer success health as loaded before the prediction date
        h = data["health_hist"].state(acc, cut) or {}
        f["health_score"] = float(h["health_score"]) if h.get("health_score") else 50.0
        f["health_red"] = int(h.get("health_color") == "Red")
        f["nps_last"] = float(h["nps_last"]) if h.get("nps_last") else 0.0
        f["csm_sentiment_negative"] = int(h.get("csm_sentiment") == "Negative")
        feats[ex["contract_id"]] = f
    return feats


def compute(root: Path, as_of: date):
    data = load(root)
    examples = build_examples(data, as_of)
    return examples, build_features(data, examples), data


def auc(labels, scores) -> float:
    """ROC AUC via the Mann-Whitney statistic with average ranks for ties."""
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
    pos = sum(1 for _s, y in pairs if y == 1)
    neg = n - pos
    rank_sum = sum(r for r, (_s, y) in zip(ranks, pairs) if y == 1)
    return (rank_sum - pos * (pos + 1) / 2.0) / (pos * neg)
