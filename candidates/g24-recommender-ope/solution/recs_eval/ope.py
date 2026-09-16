"""Off-policy evaluation of candidate rankers on the home-row logs (repaired evaluation).

What the logs actually contain, and what that implies:

* A response is cached per (session, surface) for `serving/config/serving.yaml: cache.ttl_seconds`.  Requests inside
  the TTL re-serve the stored ranking under a new serve_id, so a *decision* is a group of serves that starts with a
  cache miss.  Reload counts respond to how good the slate was, so serves must not be used as the unit.
* The exploration stream shuffles the retrieved pool uniformly and the business-rules layer then drops ineligible
  titles from the ordered list.  A uniform ordering of K titles with the ineligible ones deleted is a uniform
  ordering of the m eligible titles, so
      P(title i shown in slot k) = 1/m      for every eligible title and slot.
  The logged `propensity` field is the ordered-slate probability over the *pre-filter* pool (1/(K...(K-4))): it
  answers a different question and is not used here.
* Clicks depend on the slot, so a click observed in slot k' is only evidence for a target slate that puts that title
  in slot k'.  The slot-exact estimator below needs no examination model at all.

Estimator: item-in-slot inverse propensity scoring on exploration decisions,
      V(pi) = mean over exploration decisions of  sum_k m * click_k * 1[served_k == pi_k],
which is unbiased for the expected clicks per decision, with paired standard errors for the lifts.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path

POLICIES = ("v6", "v7", "v7_pd")
SLOTS = 5
SLOT_COLS = [f"slot_{k}" for k in range(1, SLOTS + 1)]


def load(db: Path, ttl_seconds: int):
    con = sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    serves = con.execute(
        f"SELECT serve_id, session_id, user_id, device, surface, served_at, stream, ab_arm, "
        f"{', '.join(SLOT_COLS)}, propensity, candidate_count FROM rec_serves ORDER BY session_id, surface, served_at"
    ).fetchall()

    # decisions: a serve starts a new decision when it falls outside the TTL of the current group's first serve
    decisions, serve_to_decision = [], {}
    cur_key, cur_start = None, None
    for s in serves:
        key = (s["session_id"], s["surface"])
        ts = _ts(s["served_at"])
        if key != cur_key or ts - cur_start > ttl_seconds:
            cur_key, cur_start = key, ts
            decisions.append({"decision_id": s["serve_id"], "serve_ids": [], "stream": s["stream"],
                              "ab_arm": s["ab_arm"], "device": s["device"], "decided_at": s["served_at"],
                              "slate": [s[c] for c in SLOT_COLS], "candidate_count": s["candidate_count"]})
        decisions[-1]["serve_ids"].append(s["serve_id"])
        serve_to_decision[s["serve_id"]] = len(decisions) - 1

    # outcomes: binary per (decision, slot), merged over the decision's renders
    clicks = {}
    for row in con.execute("SELECT serve_id, position FROM click_events"):
        di = serve_to_decision.get(row[0])
        if di is not None:
            clicks[(di, int(row[1]))] = 1

    # candidates: eligible pool and model scores, logged once per decision by the ranker
    cands = {}
    for row in con.execute("SELECT serve_id, item_id, score_v6, score_v7, score_v7_pd, filter_reason "
                           "FROM rec_candidates"):
        di = serve_to_decision.get(row[0])
        if di is not None:
            cands.setdefault(di, []).append(row)
    con.close()
    return decisions, clicks, cands


def _ts(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()


def target_slates(cands: dict) -> dict:
    """Counterfactual slate per policy: the top five *eligible* titles by that model's score.

    The eligibility filter sits downstream of ranking, so a candidate policy's slate is filtered the same way.
    """
    out = {}
    for di, rows in cands.items():
        eligible = [r for r in rows if r[5] is None]
        m = len(eligible)
        slates = {}
        for p, col in (("v6", 2), ("v7", 3), ("v7_pd", 4)):
            slates[p] = [r[1] for r in sorted(eligible, key=lambda r: -r[col])[:SLOTS]]
        out[di] = {"m": m, "slates": slates}
    return out


def evaluate(decisions, clicks, targets):
    """Slot-exact item-in-slot IPS over the exploration decisions, with paired lift standard errors."""
    per = {p: [] for p in POLICIES}
    for di, d in enumerate(decisions):
        if d["stream"] != "explore_shuffle" or di not in targets:
            continue
        m = targets[di]["m"]
        for p in POLICIES:
            tgt = targets[di]["slates"][p]
            y = 0.0
            for k in range(SLOTS):
                if k < len(tgt) and d["slate"][k] == tgt[k] and clicks.get((di, k + 1)):
                    y += m
            per[p].append(y)
    n = len(per["v6"])
    out = {}
    for p in POLICIES:
        mean = sum(per[p]) / n
        var = sum((y - mean) ** 2 for y in per[p]) / (n - 1)
        out[p] = {"value": mean, "se": math.sqrt(var / n)}
    for p in ("v7", "v7_pd"):
        diffs = [a - b for a, b in zip(per[p], per["v6"])]
        mean = sum(diffs) / n
        var = sum((x - mean) ** 2 for x in diffs) / (n - 1)
        out[p]["lift"] = mean
        out[p]["lift_se"] = math.sqrt(var / n)
    out["v6"]["lift"] = 0.0
    out["v6"]["lift_se"] = 0.0
    return out, n


def write_outputs(out_dir: Path, decisions, clicks, targets, res):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "decisions.csv", "w", newline="") as fh:
        fh.write("decision_id,stream,device,decided_at,position,item_id,clicked\n")
        for di, d in enumerate(decisions):
            for k in range(SLOTS):
                fh.write(f"{d['decision_id']},{d['stream']},{d['device']},{d['decided_at']},{k + 1},"
                         f"{d['slate'][k]},{clicks.get((di, k + 1), 0)}\n")
    with open(out_dir / "target_slates.csv", "w", newline="") as fh:
        fh.write("decision_id,policy,position,item_id\n")
        for di, t in sorted(targets.items()):
            for p in POLICIES:
                for k, item in enumerate(t["slates"][p]):
                    fh.write(f"{decisions[di]['decision_id']},{p},{k + 1},{item}\n")
    with open(out_dir / "policy_values.csv", "w", newline="") as fh:
        fh.write("policy,value,ci_low,ci_high,lift_vs_v6,lift_ci_low,lift_ci_high\n")
        for p in POLICIES:
            r = res[p]
            fh.write(f"{p},{r['value']!r},{r['value'] - 1.96 * r['se']!r},{r['value'] + 1.96 * r['se']!r},"
                     f"{r['lift']!r},{r['lift'] - 1.96 * r['lift_se']!r},{r['lift'] + 1.96 * r['lift_se']!r}\n")
    qualifies = [p for p in ("v7", "v7_pd") if res[p]["lift"] - 1.96 * res[p]["lift_se"] > 0]
    launch = max(qualifies, key=lambda p: res[p]["value"]) if qualifies else "v6"
    (out_dir / "launch.json").write_text(json.dumps({"launch": launch}, indent=2) + "\n")


def run(db: Path, out_dir: Path, ttl_seconds: int) -> None:
    decisions, clicks, cands = load(db, ttl_seconds)
    targets = target_slates(cands)
    res, _n = evaluate(decisions, clicks, targets)
    write_outputs(out_dir, decisions, clicks, targets, res)
