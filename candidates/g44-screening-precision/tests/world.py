"""Deterministic generator for the Kestrel Screening fraud-review warehouse (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/warehouse.sqlite

Kestrel screens card-not-present authorisations for merchants. Every FLAG goes to the review queue, and
the quality programme sends a systematic 1-in-N sample of PASS transactions to the same queue. Reviews
raised any other way (a chargeback arriving, a merchant escalation) also land in the table and are not
part of the sample.

The labels therefore exist under a known but uneven design: flagged transactions are labelled with
certainty, passed transactions at a known fraction, and ad-hoc reviews at no defined rate at all.
"""
from __future__ import annotations

import copy
import hashlib
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

CHANNELS = ("WEB", "MOBILE_APP", "CALL_CENTRE")
SOURCES = ("QUEUE_FLAGGED", "QUALITY_SAMPLE", "AD_HOC")
OUTCOMES = ("FRAUD", "LEGITIMATE", "PENDING")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 7714403,
    "window_start": "2026-04-01",
    "window_end": "2026-07-01",          # exclusive
    "n_txn": 45000,
    "quality_sample_n": 10,              # one in N passed transactions goes to the quality queue
    "fraud_rate": 0.038,                 # Kestrel's own book across merchants
    "sensitivity": 0.955,
    "specificity": 0.9978,
    "pending_share": 0.03,               # reviews not yet adjudicated at extract time
    "ad_hoc_per_1000": 7.0,              # chargeback-driven and escalation reviews
    "ad_hoc_fraud_share": 0.55,          # ad-hoc reviews are heavily enriched for fraud
    "panel_size": 2600,
    "panel_fraud_share": 0.35,           # the published benchmark panel is enriched
    "contract_fraud_rate": 0.0075,       # Northwater Retail's own rate, stated in the contract
    "precision_floor": 0.80,
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def build(spec: dict) -> dict:
    d = _rng(spec["seed"], "design")
    t0 = date.fromisoformat(spec["window_start"])
    t1 = date.fromisoformat(spec["window_end"])
    days = (t1 - t0).days

    txns, reviews = [], []
    pass_seen = 0
    for i in range(spec["n_txn"]):
        fraud = d.random() < spec["fraud_rate"]
        flag = (d.random() < spec["sensitivity"]) if fraud else (d.random() > spec["specificity"])
        t = {"id": f"TXN-{700000 + i}", "at": t0 + timedelta(days=d.randrange(days)),
             "amount": round(d.lognormvariate(4.2, 0.9), 2), "channel": d.choice(CHANNELS),
             "score": round(d.uniform(0.70, 0.999) if flag else d.uniform(0.0, 0.72), 4),
             "decision": "FLAG" if flag else "PASS", "fraud": fraud}
        txns.append(t)
        if flag:
            reviews.append({"txn": t, "source": "QUEUE_FLAGGED"})
        else:
            pass_seen += 1
            if pass_seen % spec["quality_sample_n"] == 0:
                reviews.append({"txn": t, "source": "QUALITY_SAMPLE"})

    # ad-hoc reviews: raised by a chargeback or a merchant escalation, mostly on passed transactions,
    # and enriched for fraud. They are reviews, not sample members.
    n_adhoc = int(spec["ad_hoc_per_1000"] * spec["n_txn"] / 1000.0)
    already = {id(r["txn"]) for r in reviews}
    passed = [t for t in txns if t["decision"] == "PASS" and id(t) not in already]
    fraud_pool = [t for t in passed if t["fraud"]]
    clean_pool = [t for t in passed if not t["fraud"]]
    for k in range(n_adhoc):
        want_fraud = d.random() < spec["ad_hoc_fraud_share"]
        pool = fraud_pool if (want_fraud and fraud_pool) else clean_pool
        if not pool:
            continue
        t = pool.pop(d.randrange(len(pool)))
        reviews.append({"txn": t, "source": "AD_HOC"})

    out = []
    for j, r in enumerate(reviews):
        pending = d.random() < spec["pending_share"]
        out.append({"id": f"REV-{300000 + j}", "txn": r["txn"]["id"], "source": r["source"],
                    "at": r["txn"]["at"] + timedelta(days=d.randint(1, 9)),
                    "outcome": "PENDING" if pending else ("FRAUD" if r["txn"]["fraud"] else "LEGITIMATE"),
                    "_fraud": r["txn"]["fraud"], "_decision": r["txn"]["decision"], "_pending": pending})

    # the published benchmark panel: an enriched case set the vendor's marketing quotes
    panel = []
    for i in range(spec["panel_size"]):
        fraud = d.random() < spec["panel_fraud_share"]
        flag = (d.random() < min(0.999, spec["sensitivity"] * 1.02)) if fraud \
            else (d.random() > min(0.9999, spec["specificity"] * 1.002))
        panel.append({"id": f"PNL-{90000 + i}", "fraud": fraud, "decision": "FLAG" if flag else "PASS"})

    return {"spec": spec, "t0": t0, "t1": t1, "txns": txns, "reviews": out, "panel": panel}


# ------------------------------------------------------------------------- the contract quantities
def truth(w: dict) -> dict:
    """Screen performance on Kestrel's own traffic under the sampling design, then the precision the
    contract is written on: the merchant's own fraud rate, not Kestrel's."""
    spec = w["spec"]
    N = spec["quality_sample_n"]
    tp = fp = fn = tn = 0.0
    for r in w["reviews"]:
        if r["source"] == "AD_HOC" or r["_pending"]:
            continue                                     # not sample members; not adjudicated
        weight = 1.0 if r["source"] == "QUEUE_FLAGGED" else float(N)
        if r["_decision"] == "FLAG":
            tp += weight if r["_fraud"] else 0.0
            fp += 0.0 if r["_fraud"] else weight
        else:
            fn += weight if r["_fraud"] else 0.0
            tn += 0.0 if r["_fraud"] else weight
    se = tp / (tp + fn) if (tp + fn) else 0.0
    sp = tn / (tn + fp) if (tn + fp) else 0.0
    p = spec["contract_fraud_rate"]
    denom = se * p + (1.0 - sp) * (1.0 - p)
    ppv = se * p / denom if denom else 0.0
    observed = tp / (tp + fp) if (tp + fp) else 0.0
    flagged = sum(1 for t in w["txns"] if t["decision"] == "FLAG")
    adj = sum(1 for r in w["reviews"] if r["source"] != "AD_HOC" and not r["_pending"])
    return {"window_start": w["t0"].isoformat(), "window_end": w["t1"].isoformat(),
            "flagged_transactions": flagged, "adjudicated_sample_reviews": adj,
            "sensitivity": round(se, 6), "specificity": round(sp, 6),
            "observed_precision": round(observed, 6), "contract_precision": round(ppv, 6),
            "decision": "remediate" if ppv < spec["precision_floor"] else "accept"}


def write_sqlite(w: dict, out_dir: str) -> str:
    spec = w["spec"]
    p = _rng(spec["seed"], "presentation")
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db = os.path.join(data_dir, "warehouse.sqlite")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    c = con.cursor()
    c.execute("CREATE TABLE transactions (txn_id TEXT PRIMARY KEY, authorized_at TEXT, amount REAL, "
              "channel TEXT, screen_score REAL, screen_decision TEXT)")
    c.execute("CREATE TABLE reviews (review_id TEXT PRIMARY KEY, txn_id TEXT, reviewed_at TEXT, "
              "review_source TEXT, outcome TEXT)")
    c.execute("CREATE TABLE benchmark_panel (case_id TEXT PRIMARY KEY, label TEXT, screen_decision TEXT)")
    c.execute("CREATE TABLE contract_terms (key TEXT, value TEXT)")

    txn_rows = [(t["id"], t["at"].isoformat(), t["amount"], t["channel"], t["score"], t["decision"])
                for t in w["txns"]]
    rev_rows = [(r["id"], r["txn"], r["at"].isoformat(), r["source"], r["outcome"]) for r in w["reviews"]]
    pnl_rows = [(x["id"], "FRAUD" if x["fraud"] else "LEGITIMATE", x["decision"]) for x in w["panel"]]
    for rows in (txn_rows, rev_rows, pnl_rows):
        p.shuffle(rows)
    c.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?)", txn_rows)
    c.executemany("INSERT INTO reviews VALUES (?,?,?,?,?)", rev_rows)
    c.executemany("INSERT INTO benchmark_panel VALUES (?,?,?)", pnl_rows)
    c.executemany("INSERT INTO contract_terms VALUES (?,?)", [
        ("window_start", w["t0"].isoformat()),
        ("window_end", w["t1"].isoformat()),
        ("merchant", "Northwater Retail"),
        ("merchant_fraud_rate", f"{spec['contract_fraud_rate']:.4f}"),
        ("precision_floor", f"{spec['precision_floor']:.2f}"),
        ("quality_sample_one_in", str(spec["quality_sample_n"])),
        ("review_source_values", " | ".join(SOURCES)),
        ("outcome_values", " | ".join(OUTCOMES)),
        ("screen_decision_values", "FLAG (sent to the review queue) | PASS (authorised)"),
    ])
    con.commit()
    con.close()
    return db


def db_digest(db_path: str) -> str:
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for t in ("transactions", "reviews", "benchmark_panel", "contract_terms"):
        for row in con.execute("SELECT * FROM %s ORDER BY 1" % t):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()[:16]


def main(argv):
    out = argv[1]
    spec = copy.deepcopy(VISIBLE_SPEC)
    if len(argv) > 2 and argv[2] != "visible":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import scenarios
        spec = scenarios.by_name(argv[2])
    w = build(spec)
    db = write_sqlite(w, out)
    print(f"{spec['name']}: {db} digest={db_digest(db)}")


if __name__ == "__main__":
    main(sys.argv)
