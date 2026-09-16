"""Parameterised off-policy evaluation for the G24 mutation suite (dev tool, never shipped to agents).

With VARIANT = {} this is a correct evaluation (slot-exact item-in-slot IPS on exploration decisions), written
independently of the reference solution's control flow. VARIANT["method"] switches to another accepted estimator or
to a natural wrong one; the remaining switches are overfits. The suite copies this file over `recs_eval/cli.py`.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import datetime
from pathlib import Path

VARIANT: dict = {}

CFG = {
    "method": "slot_ips",
    "grouping": None,          # None -> implied by method; ttl | identical_slate | session | serve
    "hardcoded_launch": None,
    "hardcoded_m": None,
    "hardcoded_theta": None,
}

POLICIES = ("v6", "v7", "v7_pd")
SLOTS = 5
SLOT_COLS = [f"slot_{k}" for k in range(1, SLOTS + 1)]
DEVICES = ("web", "mobile", "tv")


def _ts(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").timestamp()


def load(db: Path, ttl: int, grouping: str):
    con = sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)
    rows = con.execute(
        f"SELECT serve_id, session_id, device, surface, served_at, stream, ab_arm, {', '.join(SLOT_COLS)}, "
        f"propensity, candidate_count FROM rec_serves ORDER BY session_id, surface, served_at").fetchall()
    decisions, s2d = [], {}
    cur_key = cur_start = None
    cur_slate = None
    for r in rows:
        serve_id, session_id, device, surface, served_at, stream, ab_arm = r[:7]
        slate = list(r[7:12])
        prop, K = r[12], r[13]
        ts = _ts(served_at)
        key = (session_id, surface)
        if grouping == "serve":
            new = True
        elif grouping == "session":
            new = key != cur_key
        elif grouping == "identical_slate":
            new = key != cur_key or slate != cur_slate
        else:
            new = key != cur_key or ts - cur_start > ttl
        if new:
            cur_key, cur_start, cur_slate = key, ts, slate
            decisions.append({"decision_id": serve_id, "stream": stream, "ab_arm": ab_arm, "device": device,
                              "decided_at": served_at, "slate": slate, "propensity": prop, "K": K, "serves": 0})
        decisions[-1]["serves"] += 1
        s2d[serve_id] = len(decisions) - 1
    clicks, first_serve_clicks = {}, {}
    for serve_id, position in con.execute("SELECT serve_id, position FROM click_events"):
        di = s2d.get(serve_id)
        if di is None:
            continue
        clicks[(di, int(position))] = 1
        if decisions[di]["decision_id"] == serve_id:
            first_serve_clicks[(di, int(position))] = 1
    cands = {}
    for row in con.execute("SELECT serve_id, item_id, score_v6, score_v7, score_v7_pd, filter_reason "
                           "FROM rec_candidates"):
        di = s2d.get(row[0])
        if di is not None:
            cands.setdefault(di, []).append(row)
    con.close()
    return decisions, clicks, first_serve_clicks, cands


def target_slates(cands: dict, prefilter: bool):
    out = {}
    for di, rows in cands.items():
        pool = rows if prefilter else [r for r in rows if r[5] is None]
        m = CFG["hardcoded_m"] or len([r for r in rows if r[5] is None])
        slates = {p: [r[1] for r in sorted(pool, key=lambda r: -r[col])[:SLOTS]]
                  for p, col in (("v6", 2), ("v7", 3), ("v7_pd", 4))}
        out[di] = {"m": m, "slates": slates}
    return out


def theta_hat(decisions, clicks, pooled: bool):
    if CFG["hardcoded_theta"]:
        return {d: list(CFG["hardcoded_theta"]) for d in DEVICES}
    num = {d: [0.0] * SLOTS for d in DEVICES}
    den = {d: 0 for d in DEVICES}
    for di, d in enumerate(decisions):
        if d["stream"] != "explore_shuffle":
            continue
        den[d["device"]] += 1
        for k in range(SLOTS):
            num[d["device"]][k] += clicks.get((di, k + 1), 0)
    if pooled:
        tot = [sum(num[d][k] for d in DEVICES) for k in range(SLOTS)]
        n = sum(den.values())
        curve = [(tot[k] / n) / max(tot[0] / n, 1e-9) for k in range(SLOTS)]
        return {d: curve for d in DEVICES}
    out = {}
    for d in DEVICES:
        rate = [num[d][k] / max(den[d], 1) for k in range(SLOTS)]
        out[d] = [r / max(rate[0], 1e-9) for r in rate]
    return out


def reward_model(decisions, clicks, th):
    num, den = {}, {}
    tot_c = tot_e = 0.0
    for di, d in enumerate(decisions):
        if d["stream"] != "explore_shuffle":
            continue
        for k in range(SLOTS):
            it = d["slate"][k]
            num[it] = num.get(it, 0.0) + clicks.get((di, k + 1), 0)
            den[it] = den.get(it, 0.0) + th[d["device"]][k]
            tot_c += clicks.get((di, k + 1), 0)
            tot_e += th[d["device"]][k]
    prior = tot_c / max(tot_e, 1e-9)
    return {it: (num[it] + 8.0 * prior) / (den[it] + 8.0) for it in num}, prior


def contributions(decisions, clicks, first_clicks, targets, method):
    """Per-decision contribution for each policy on the randomized stream."""
    per = {p: [] for p in POLICIES}
    pooled = method == "pooled_theta"
    th = theta_hat(decisions, clicks, pooled) if method in ("pbm_ips", "pooled_theta", "dr", "dm_only") else None
    rhat = prior = None
    if method in ("dr", "dm_only"):
        rhat, prior = reward_model(decisions, clicks, th)
    use_clicks = first_clicks if method == "keep_first_serve" else clicks
    for di, d in enumerate(decisions):
        if d["stream"] != "explore_shuffle" or di not in targets:
            continue
        m = targets[di]["m"]
        if method == "weight_K":
            m = d["K"]
        elif method == "clipped_weights":
            m = min(m, 10)
        for p in POLICIES:
            tgt = targets[di]["slates"][p]
            if method in ("pbm_ips", "pooled_theta"):
                y = 0.0
                pos = {it: k for k, it in enumerate(tgt)}
                for k in range(SLOTS):
                    if use_clicks.get((di, k + 1)) and d["slate"][k] in pos:
                        y += (m / SLOTS) * th[d["device"]][pos[d["slate"][k]]] / max(th[d["device"]][k], 1e-9)
            elif method == "item_anywhere":
                tset = set(tgt)
                y = (m / SLOTS) * sum(use_clicks.get((di, k + 1), 0) for k in range(SLOTS) if d["slate"][k] in tset)
            elif method == "dm_only":
                y = sum(th[d["device"]][k] * rhat.get(tgt[k], prior) for k in range(min(SLOTS, len(tgt))))
            elif method == "dr":
                y = sum(th[d["device"]][k] * rhat.get(tgt[k], prior) for k in range(min(SLOTS, len(tgt))))
                for k in range(SLOTS):
                    if k < len(tgt) and d["slate"][k] == tgt[k]:
                        y += m * (use_clicks.get((di, k + 1), 0) - th[d["device"]][k] * rhat.get(tgt[k], prior))
            elif method == "slot_replay":
                # per-slot replay on exploration: clicks where the logged title matches the target, no propensity;
                # normalised per slot afterwards by the match rate (see replay_normalise)
                y = [use_clicks.get((di, k + 1), 0) if k < len(tgt) and d["slate"][k] == tgt[k] else 0
                     for k in range(SLOTS)]
            elif method == "logged_propensity_snips":
                tset = set(tgt)
                w = 1.0 / max(d["propensity"], 1e-4)
                y = SLOTS * w * sum(use_clicks.get((di, k + 1), 0) for k in range(SLOTS) if d["slate"][k] in tset)
            else:                                   # slot_ips, snips, weight_K, serves_as_units, clipped, prefilter
                y = sum(m for k in range(SLOTS)
                        if k < len(tgt) and d["slate"][k] == tgt[k] and use_clicks.get((di, k + 1)))
            per[p].append(y)
    if method == "slot_replay":
        idx = [di for di, d in enumerate(decisions) if d["stream"] == "explore_shuffle" and di in targets]
        for p in POLICIES:
            rate = [0.0] * SLOTS
            for di in idx:
                tgt = targets[di]["slates"][p]
                for k in range(SLOTS):
                    rate[k] += 1.0 if k < len(tgt) and decisions[di]["slate"][k] == tgt[k] else 0.0
            rate = [r / len(idx) for r in rate]
            per[p] = [sum(y[k] / max(rate[k], 1e-9) for k in range(SLOTS)) for y in per[p]]
    if method == "logged_propensity_snips":
        norm = sum(1.0 / max(d["propensity"], 1e-4) for di, d in enumerate(decisions)
                   if d["stream"] == "explore_shuffle" and di in targets)
        n = len(per["v6"])
        per = {p: [y * n / norm for y in v] for p, v in per.items()}
    return per


def summarise(per):
    n = len(per["v6"])
    out = {}
    for p in POLICIES:
        mean = sum(per[p]) / n
        var = sum((y - mean) ** 2 for y in per[p]) / (n - 1)
        out[p] = {"value": mean, "se": math.sqrt(var / n), "lift": 0.0, "lift_se": 0.0}
    for p in ("v7", "v7_pd"):
        diffs = [a - b for a, b in zip(per[p], per["v6"])]
        mean = sum(diffs) / n
        var = sum((x - mean) ** 2 for x in diffs) / (n - 1)
        out[p]["lift"], out[p]["lift_se"] = mean, math.sqrt(var / n)
    return out


def snips_normalise(per, targets, decisions):
    idx = [di for di, d in enumerate(decisions) if d["stream"] == "explore_shuffle" and di in targets]
    for p in POLICIES:
        hits = [sum(targets[di]["m"] for k in range(SLOTS)
                    if k < len(targets[di]["slates"][p]) and decisions[di]["slate"][k] == targets[di]["slates"][p][k])
                for di in idx]
        denom = (sum(hits) / len(hits)) / SLOTS
        per[p] = [y / max(denom, 1e-9) for y in per[p]]
    return per


def replay_prod(decisions, clicks, targets):
    """The deployed gate: replay on production responses, clicks per matched impression, scaled to five slots."""
    out = {}
    for p in POLICIES:
        c = n = 0
        for di, d in enumerate(decisions):
            if d["stream"] != "prod_rank" or di not in targets:
                continue
            tset = set(targets[di]["slates"][p])
            for k in range(SLOTS):
                if d["slate"][k] in tset:
                    n += 1
                    c += clicks.get((di, k + 1), 0)
        ctr = c / max(n, 1)
        out[p] = {"value": SLOTS * ctr, "se": SLOTS * math.sqrt(max(ctr * (1 - ctr), 1e-12) / max(n, 1)),
                  "lift": 0.0, "lift_se": 0.0}
    for p in ("v7", "v7_pd"):
        out[p]["lift"] = out[p]["value"] - out["v6"]["value"]
        out[p]["lift_se"] = math.sqrt(out[p]["se"] ** 2 + out["v6"]["se"] ** 2)
    return out


def onpolicy_values(decisions, clicks, res):
    for p, pred in (("v6", lambda d: d["stream"] == "prod_rank" and d["ab_arm"] != "v7"),
                    ("v7", lambda d: d["ab_arm"] == "v7")):
        ys = [sum(clicks.get((di, k + 1), 0) for k in range(SLOTS)) for di, d in enumerate(decisions) if pred(d)]
        if len(ys) > 2:
            mean = sum(ys) / len(ys)
            var = sum((y - mean) ** 2 for y in ys) / (len(ys) - 1)
            res[p]["value"], res[p]["se"] = mean, math.sqrt(var / len(ys))
    return res


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
    if CFG["hardcoded_launch"]:
        launch = CFG["hardcoded_launch"]
    else:
        ok = [p for p in ("v7", "v7_pd") if res[p]["lift"] - 1.96 * res[p]["lift_se"] > 0]
        launch = max(ok, key=lambda p: res[p]["value"]) if ok else "v6"
    (out_dir / "launch.json").write_text(json.dumps({"launch": launch}, indent=2) + "\n")


def ttl_from_config() -> int:
    for line in Path("serving/config/serving.yaml").read_text().splitlines():
        if line.strip().startswith("ttl_seconds:"):
            return int(line.split(":", 1)[1].strip())
    return 600


def main(argv=None):
    ap = argparse.ArgumentParser(prog="recs_eval")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("ope")
    r.add_argument("--logs", default="data/logs.sqlite")
    r.add_argument("--out", default="out/ope")
    a = ap.parse_args(argv)
    CFG.update(VARIANT)
    method = CFG["method"]
    grouping = CFG["grouping"] or {
        "serves_as_units": "serve", "merge_identical_slates": "identical_slate",
        "session_only_grouping": "session"}.get(method, "ttl")
    decisions, clicks, first_clicks, cands = load(Path(a.logs), ttl_from_config(), grouping)
    targets = target_slates(cands, prefilter=(method == "target_prefilter"))
    if method == "replay_prod":
        res = replay_prod(decisions, clicks, targets)
    else:
        per = contributions(decisions, clicks, first_clicks, targets, method)
        if method == "snips":
            per = snips_normalise(per, targets, decisions)
        res = summarise(per)
        if method == "onpolicy_mix":
            res = onpolicy_values(decisions, clicks, res)
    write_outputs(Path(a.out), decisions, clicks, targets, res)


if __name__ == "__main__":
    main()
