"""Deterministic generator for the Meridian Retail Group ambient-grocery service-level extract (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/service.sqlite

Two organisations measure "fill rate" on the same order book and get different numbers. The difference is
entirely definitional and decomposes exactly into four steps, each a single change:

    M0  line fill at CONFIRMED quantity, window on requested delivery date, returns excluded,
        customer-cancelled lines excluded                                  <- the customer supply agreement
    M1  the same, at REQUESTED quantity                                    <- denominator
    M2  the same, with returns netted off delivered quantity               <- returns treatment
    M3  the same, windowed on DESPATCH date                                <- date window
    M4  the same, aggregated at ORDER level                                <- aggregation  = the supplier's figure

Three things vary across extracts, and they are what make this a control rather than another
"the-published-number-is-wrong" task:

  * whether the incumbent reporting code actually implements the agreement (`incumbent_defect`);
  * how material the lines amended after confirmation are (`amended_share`), which is the point Schedule 4 of
    the agreement leaves unagreed;
  * the size of the genuine account-level tail.
"""
from __future__ import annotations

import copy
import hashlib
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

CHANNELS = ("MULTIPLE", "WHOLESALE", "CONVENIENCE", "ONLINE")
RETURN_REASONS = ("QUALITY", "OVER_DELIVERY", "NOT_ORDERED", "DAMAGE_IN_TRANSIT")
SKUS = tuple(f"AMB-{n:04d}" for n in range(1, 61))

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 3170428,
    "period_start": "2026-04-06",
    "weeks": 14,
    "report_weeks": 13,        # the reporting period; week 14 orders sit outside it
    "n_accounts": 22,
    "tail_accounts": 3,                 # accounts given materially worse allocation
    "orders_per_week": 190,
    "lines_per_order": (3, 14),
    "requested_qty": (6, 240),
    # Allocation: the share of lines the supplier confirmed short of the request, and how short.
    "short_confirm_share": 0.22,
    "short_confirm_frac": (0.70, 0.97),
    "tail_short_confirm_share": 0.62,
    "tail_short_confirm_frac": (0.35, 0.85),
    # Delivery against the confirmation.
    "under_deliver_share": 0.017,
    "under_deliver_frac": (0.6, 0.97),
    "tail_under_deliver_share": 0.072,
    "cancelled_share": 0.035,           # lines the customer cancelled before despatch
    "amended_share": 0.02,              # lines the customer amended after confirmation
    "returns_share": 0.055,
    "return_frac": (0.1, 0.5),
    "null_confirm_share": 0.0,          # lines with no confirmation recorded; the incumbent code has a
                                        # latent defect that only bites when this is non-zero
    "despatch_offset_days": (-3, 2),    # despatch relative to requested delivery date
    "tickets_per_tail_account": (9, 22),
    "returns_driven_ticket_share": 0.40,
    "service_floor_pct": 95.0,          # agreement: account-level floor
    "bonus_gate_pct": 96.0,             # reporting team's gate on the category figure
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def build(spec: dict) -> dict:
    d = _rng(spec["seed"], "design")
    start = date.fromisoformat(spec["period_start"])

    accounts = []
    for i in range(spec["n_accounts"]):
        accounts.append({"account_id": f"ACC-{i + 1:03d}",
                         "name": f"Account {i + 1}",
                         "channel": CHANNELS[i % len(CHANNELS)],
                         "is_tail": i < spec["tail_accounts"]})
    tail_ids = [a["account_id"] for a in accounts if a["is_tail"]]

    lines, returns, grns = [], [], []
    lid = 0
    for wk in range(spec["weeks"]):
        for _ in range(spec["orders_per_week"]):
            acc = accounts[d.randrange(len(accounts))]
            oid = f"ORD-{wk:02d}{d.randrange(100000, 999999)}"
            rdd = start + timedelta(days=7 * wk + d.randrange(5))
            desp = rdd + timedelta(days=d.randint(*spec["despatch_offset_days"]))
            for _ in range(d.randint(*spec["lines_per_order"])):
                lid += 1
                req = d.randint(*spec["requested_qty"])
                tail = acc["is_tail"]
                sh_share = spec["tail_short_confirm_share"] if tail else spec["short_confirm_share"]
                sh_frac = spec["tail_short_confirm_frac"] if tail else spec["short_confirm_frac"]
                if d.random() < sh_share:
                    conf = max(1, int(round(req * d.uniform(*sh_frac))))
                else:
                    conf = req
                null_conf = d.random() < spec["null_confirm_share"]
                ud_share = spec["tail_under_deliver_share"] if tail else spec["under_deliver_share"]
                if d.random() < ud_share:
                    deliv = max(0, int(round(conf * d.uniform(*spec["under_deliver_frac"]))))
                else:
                    deliv = conf
                cancelled = d.random() < spec["cancelled_share"]
                amended = (not cancelled) and d.random() < spec["amended_share"]
                # An amendment moves the quantity the customer wants after the supplier confirmed. Schedule 4
                # does not say which figure the metric is measured against.
                amended_qty = max(1, int(round(conf * d.uniform(0.4, 0.9)))) if amended else None
                if cancelled:
                    deliv = 0
                lines.append({
                    "line_id": f"L{lid:07d}", "order_id": oid, "account_id": acc["account_id"],
                    "sku": SKUS[d.randrange(len(SKUS))],
                    "requested_qty": req,
                    "confirmed_qty": None if null_conf else conf,
                    "delivered_qty": deliv,
                    "requested_delivery_date": rdd.isoformat(),
                    "despatch_date": None if cancelled else desp.isoformat(),
                    "cancelled_by_customer": 1 if cancelled else 0,
                    "amended_qty": amended_qty,
                    "_conf_effective": conf,
                })
                if not cancelled and d.random() < spec["returns_share"]:
                    q = max(1, int(round(deliv * d.uniform(*spec["return_frac"]))))
                    returns.append({"line_id": f"L{lid:07d}", "return_qty": min(q, deliv),
                                    "reason_code": RETURN_REASONS[d.randrange(len(RETURN_REASONS))],
                                    "returned_on": (desp + timedelta(days=d.randint(2, 21))).isoformat()})
                if not cancelled:
                    grns.append({"line_id": f"L{lid:07d}", "received_qty": deliv,
                                 "received_on": (desp + timedelta(days=d.randint(0, 3))).isoformat()})

    # Shortfall tickets from the three accounts that were allocated worst. A share of them are really returns.
    t = _rng(spec["seed"], "tickets")
    tickets = []
    by_acc = {}
    for ln in lines:
        by_acc.setdefault(ln["account_id"], []).append(ln)
    ret_ids = {r["line_id"] for r in returns}
    n = 0
    for aid in tail_ids:
        for _ in range(t.randint(*spec["tickets_per_tail_account"])):
            n += 1
            pool = by_acc[aid]
            if t.random() < spec["returns_driven_ticket_share"]:
                cands = [x for x in pool if x["line_id"] in ret_ids] or pool
                claim = "GOODS_REJECTED"
            else:
                cands = [x for x in pool
                         if x["delivered_qty"] < (x["_conf_effective"] or 0)] or pool
                claim = "SHORT_DELIVERY"
            ln = cands[t.randrange(len(cands))]
            tickets.append({"ticket_id": f"TCK-{n:05d}", "account_id": aid, "line_id": ln["line_id"],
                            "raised_on": ln["requested_delivery_date"], "claim_type": claim})

    return {"spec": spec, "accounts": accounts, "lines": lines, "returns": returns,
            "grns": grns, "tickets": tickets, "tail_ids": tail_ids}


# --------------------------------------------------------------------------- the two metrics and the bridge
def _in_window(ln, on_despatch, lo, hi):
    """Whether a line falls in the reporting period. The agreement windows on requested delivery date; the
    supplier's appendix windows on despatch date, which moves lines at the period edges in and out."""
    key = ln["despatch_date"] if on_despatch else ln["requested_delivery_date"]
    return key is not None and lo <= key < hi


def _metric(lines, returns, *, denominator, net_returns, on_despatch, unit_weighted, amended_basis,
            period):
    """One fill-rate definition, parameterised over the four things the two organisations disagree about.

    denominator     "confirmed" or "requested"
    net_returns     subtract returned quantity from delivered quantity
    on_despatch     window the period on despatch date rather than requested delivery date
    unit_weighted   measure units delivered against units targeted (case fill) rather than counting lines
    amended_basis   "confirmed" or "amended": which quantity an amended line is measured against
    """
    ret = {}
    for r in returns:
        ret[r["line_id"]] = ret.get(r["line_id"], 0) + r["return_qty"]

    lo, hi = period
    flat = [ln for ln in lines
            if not ln["cancelled_by_customer"] and _in_window(ln, on_despatch, lo, hi)]

    def target(ln):
        if denominator == "requested":
            return ln["requested_qty"]
        if ln["amended_qty"] is not None and amended_basis == "amended":
            return ln["amended_qty"]
        # A line with no confirmation recorded has nothing to measure against and cannot be shown to be
        # filled, so the agreement counts it as unfilled.
        return ln["confirmed_qty"]

    def filled(ln):
        tgt = target(ln)
        if tgt is None:
            return False
        got = ln["delivered_qty"] - (ret.get(ln["line_id"], 0) if net_returns else 0)
        return got >= tgt

    if not flat:
        return None
    if unit_weighted:
        num = den = 0
        for ln in flat:
            tgt = target(ln)
            if tgt is None:
                continue
            got = ln["delivered_qty"] - (ret.get(ln["line_id"], 0) if net_returns else 0)
            num += min(max(got, 0), tgt)
            den += tgt
        return 100.0 * num / den if den else None
    return 100.0 * sum(1 for x in flat if filled(x)) / len(flat)


CONTRACT = dict(denominator="confirmed", net_returns=False, on_despatch=False, unit_weighted=False)
SUPPLIER = dict(denominator="requested", net_returns=True, on_despatch=True, unit_weighted=True)


def period_of(w):
    start = date.fromisoformat(w["spec"]["period_start"])
    return (start.isoformat(), (start + timedelta(days=7 * w["spec"]["report_weeks"])).isoformat())


def contract_rate(w, amended_basis="confirmed", lines=None):
    return _metric(lines if lines is not None else w["lines"], w["returns"],
                   amended_basis=amended_basis, period=period_of(w), **CONTRACT)


def supplier_rate(w, amended_basis="confirmed"):
    return _metric(w["lines"], w["returns"], amended_basis=amended_basis, period=period_of(w), **SUPPLIER)


def bridge(w, amended_basis="confirmed"):
    """The four single-change steps from the contractual definition to the supplier's, which add to the gap."""
    step = dict(CONTRACT)
    per = period_of(w)
    out, prev = {}, _metric(w["lines"], w["returns"], amended_basis=amended_basis, period=per, **step)
    for name, key, val in (("aggregation", "unit_weighted", True),
                           ("denominator", "denominator", "requested"),
                           ("returns_treatment", "net_returns", True),
                           ("date_window", "on_despatch", True)):
        step[key] = val
        cur = _metric(w["lines"], w["returns"], amended_basis=amended_basis, period=per, **step)
        out[name] = cur - prev
        prev = cur
    out["other"] = 0.0
    return out


def published_rate(w):
    """What the reporting team published.

    Their code counts the denominator with `COUNT(confirmed_qty)`, which skips lines where no confirmation was
    recorded. Schedule 2 section 7.2 says such a line is not filled and is not to be excluded. The defect is in
    the code on every extract; it only changes the published figure where lines without a confirmation exist,
    which is what makes "is the incumbent right?" a question about this extract rather than about the code in
    the abstract."""
    kept = [ln for ln in w["lines"] if ln["confirmed_qty"] is not None]
    return contract_rate(w, lines=kept)


def account_rates(w):
    by = {}
    for ln in w["lines"]:
        by.setdefault(ln["account_id"], []).append(ln)
    return {a: contract_rate(w, lines=v) for a, v in sorted(by.items())}


def truth(w) -> dict:
    spec = w["spec"]
    c_conf = contract_rate(w, "confirmed")
    c_amend = contract_rate(w, "amended")
    pub = published_rate(w)
    accts = account_rates(w)
    below = sorted(a for a, v in accts.items() if v is not None and v < spec["service_floor_pct"])

    # Each consequence is settled separately: where the two readings Schedule 4 admits agree, the consequence
    # follows; where they disagree, it does not follow from the evidence available.
    def settle(f):
        a, b = f(c_conf), f(c_amend)
        return ("yes" if a else "no") if a == b else "not_determinable"

    gate = settle(lambda v: v >= spec["bonus_gate_pct"])
    payable = settle(lambda v: v < spec["service_floor_pct"])
    ambiguity_material = "not_determinable" in (gate, payable)

    # Is the published figure the figure the agreement defines? Where Schedule 4 is material the agreement does
    # not define a single figure, so the question cannot be settled either.
    incumbent_ok = abs(pub - c_conf) <= 0.05
    if ambiguity_material:
        verdict = "not_determinable_from_available_evidence"
    elif incumbent_ok:
        verdict = "incumbent_correct"
    else:
        verdict = "incumbent_incorrect"

    ret_ids = {r["line_id"] for r in w["returns"]}
    tk = w["tickets"]
    ret_share = 100.0 * sum(1 for t in tk if t["line_id"] in ret_ids) / len(tk) if tk else None

    return {
        "fill_rate_contract_pct": c_conf,
        # Schedule 4 leaves the basis for lines amended after confirmation unagreed, so the contractual rate is
        # a range wherever those lines are material. Where they are not, the range collapses.
        "fill_rate_contract_low_pct": min(c_conf, c_amend),
        "fill_rate_contract_high_pct": max(c_conf, c_amend),
        "fill_rate_contract_amended_basis_pct": c_amend,
        "fill_rate_supplier_definition_pct": supplier_rate(w, "confirmed"),
        "published_rate_pct": pub,
        "bridge_pp": bridge(w, "confirmed"),
        "account_fill_pct": {a: accts[a] for a in w["tail_ids"]},
        "accounts_below_floor": len(below),
        "accounts_below_floor_ids": below,
        "returns_driven_ticket_share_pct": ret_share,
        "incumbent_verdict": verdict,
        "governing_definition": "contract_line_fill_confirmed",
        "bonus_gate_met": gate,
        "supplier_claim_payable": payable,
        "ambiguity_material": ambiguity_material,
        "n_lines": len(w["lines"]),
    }


def latent_check(w) -> dict:
    """Cross-derivation from the customers' own goods-receipt confirmations, which are a different system:
    the contractual rate recomputed from received quantity rather than despatched quantity."""
    got = {g["line_id"]: g["received_qty"] for g in w["grns"]}
    lines = []
    for ln in w["lines"]:
        c = dict(ln)
        c["delivered_qty"] = got.get(ln["line_id"], 0 if ln["cancelled_by_customer"] else ln["delivered_qty"])
        lines.append(c)
    return {"contract_rate_from_grn_pct": contract_rate(w, lines=lines)}


# --------------------------------------------------------------------------- output
SCHEMA = """
CREATE TABLE accounts (account_id TEXT PRIMARY KEY, name TEXT, channel TEXT, service_floor_pct REAL);
CREATE TABLE order_lines (
    line_id TEXT PRIMARY KEY, order_id TEXT, account_id TEXT, sku TEXT,
    requested_qty INTEGER, confirmed_qty INTEGER, delivered_qty INTEGER,
    requested_delivery_date TEXT, despatch_date TEXT, cancelled_by_customer INTEGER,
    amended_qty INTEGER);
CREATE TABLE returns (line_id TEXT, return_qty INTEGER, reason_code TEXT, returned_on TEXT);
CREATE TABLE goods_receipts (line_id TEXT PRIMARY KEY, received_qty INTEGER, received_on TEXT);
CREATE TABLE shortfall_tickets (ticket_id TEXT PRIMARY KEY, account_id TEXT, line_id TEXT, raised_on TEXT,
    claim_type TEXT);
CREATE TABLE published_metrics (period_start TEXT, period_end TEXT, metric TEXT, value REAL, source TEXT,
    published_on TEXT);
CREATE INDEX ix_lines_acc ON order_lines(account_id);
CREATE INDEX ix_returns ON returns(line_id);
"""


def write_sqlite(w, out_dir: str) -> str:
    spec = w["spec"]
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "service.sqlite")
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    p = _rng(spec["seed"], "presentation")

    con.executemany("INSERT INTO accounts VALUES (?,?,?,?)",
                    [(a["account_id"], a["name"], a["channel"], spec["service_floor_pct"])
                     for a in w["accounts"]])
    lines = list(w["lines"])
    p.shuffle(lines)
    con.executemany("INSERT INTO order_lines VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [(l["line_id"], l["order_id"], l["account_id"], l["sku"], l["requested_qty"],
                      l["confirmed_qty"], l["delivered_qty"], l["requested_delivery_date"],
                      l["despatch_date"], l["cancelled_by_customer"], l["amended_qty"]) for l in lines])
    rets = list(w["returns"])
    p.shuffle(rets)
    con.executemany("INSERT INTO returns VALUES (?,?,?,?)",
                    [(r["line_id"], r["return_qty"], r["reason_code"], r["returned_on"]) for r in rets])
    con.executemany("INSERT INTO goods_receipts VALUES (?,?,?)",
                    [(g["line_id"], g["received_qty"], g["received_on"]) for g in w["grns"]])
    con.executemany("INSERT INTO shortfall_tickets VALUES (?,?,?,?,?)",
                    [(t["ticket_id"], t["account_id"], t["line_id"], t["raised_on"], t["claim_type"])
                     for t in w["tickets"]])
    lo, hi = period_of(w)
    con.executemany("INSERT INTO published_metrics VALUES (?,?,?,?,?,?)", [
        (lo, hi, "category_fill_rate_pct", round(published_rate(w), 2), "MRG demand science", hi),
        (lo, hi, "category_fill_rate_pct", round(supplier_rate(w), 2), "Brendale Ambient (supplier report)",
         hi),
    ])
    con.commit()
    con.close()
    return path


def db_digest(db_path: str) -> str:
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for (name,) in sorted(con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()):
        h.update(name.encode())
        for row in con.execute(f"SELECT * FROM {name}"):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()


def generate(spec):
    return build(spec)


def main(argv):
    out = argv[1] if len(argv) > 1 else "/workspace"
    name = argv[2] if len(argv) > 2 else "visible"
    if name == "visible":
        spec = copy.deepcopy(VISIBLE_SPEC)
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import scenarios
        spec = scenarios.by_name(name)
    w = build(spec)
    print(write_sqlite(w, out))


if __name__ == "__main__":
    main(sys.argv)
