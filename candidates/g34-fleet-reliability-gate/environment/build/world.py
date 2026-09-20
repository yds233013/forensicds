"""Deterministic generator for the Meridian Pumps aftermarket warehouse (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/warehouse.sqlite

The same module is used by the verifier to build hidden warehouses and exact truth. Design draws
(commissioning, frailty, latent times) and presentation draws (row order, identifiers) use separate
streams so the design can be held fixed.
"""
from __future__ import annotations

import copy
import hashlib
import math
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

MODELS = ("MP-220", "MP-340", "MP-360", "MP-480")
SITES = ("ALDERGROVE", "BRAYFORD", "CALDWELL", "DUNMORE", "EASTPORT", "FAIRLEA", "GRANSTON", "HOLLOWAY")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 5140929,
    "n_units": 9000,
    "history_months": 84,          # commissioning window, months before the extract cut-off
    "cut_off": "2026-07-31",
    "wb_shape": 2.2,               # latent assembly failure time, Weibull in months
    "wb_scale": 40.0,
    "frailty_sd": 0.40,
    "overhaul_age": 24.0,          # maintenance SOP interval
    "overhaul_slack": 7.0,         # waits for the site's next planned shutdown window
    "retire_shape": 1.6,
    "retire_scale": 70.0,
    "gap_precede_share": 0.55,     # share of impending failures preceded by a telemetry gap
    "gap_lead_mean": 3.0,          # months between gap onset and failure
    "gap_background": 0.10,        # background gap rate, unrelated to condition
    "gap_len_mean": 4.0,
    "horizon": 36,
    "gate": 0.28,
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _weibull(rng, shape, scale):
    u = rng.random()
    while u <= 0.0 or u >= 1.0:
        u = rng.random()
    return scale * (-math.log(1.0 - u)) ** (1.0 / shape)


def _months_to_date(anchor: date, months: float) -> date:
    return anchor + timedelta(days=int(round(months * 30.4375)))


def build(spec: dict) -> dict:
    """Latent world. Every time is an AGE IN MONTHS since commissioning."""
    d = _rng(spec["seed"], "design")
    cut = date.fromisoformat(spec["cut_off"])
    n = spec["n_units"]

    units = []
    for i in range(n):
        age_at_cut = d.random() * spec["history_months"]
        commissioned = _months_to_date(cut, -age_at_cut)
        frail = math.exp(d.gauss(0.0, spec["frailty_sd"]))
        t_fail = _weibull(d, spec["wb_shape"], spec["wb_scale"]) / (frail ** (1.0 / spec["wb_shape"]))
        t_ovhl = spec["overhaul_age"] + d.expovariate(1.0 / spec["overhaul_slack"])
        t_ret = _weibull(d, spec["retire_shape"], spec["retire_scale"])
        t_adm = age_at_cut

        terminal = min(t_fail, t_ovhl, t_ret, t_adm)
        if terminal == t_fail:
            code = "UNPL_FAIL"
        elif terminal == t_ovhl:
            code = "PM_OVHL"
        elif terminal == t_ret:
            code = "ASSET_RET"
        else:
            code = None                      # still in service at the cut-off

        # telemetry gaps: a vibration channel usually degrades with the bearing it monitors
        gaps = []
        if code == "UNPL_FAIL" and d.random() < spec["gap_precede_share"]:
            lead = min(d.expovariate(1.0 / spec["gap_lead_mean"]), terminal * 0.9)
            gaps.append((max(0.2, terminal - lead), terminal))
        if d.random() < spec["gap_background"]:
            s0 = d.random() * max(terminal - 0.5, 0.5)
            gaps.append((s0, min(s0 + d.expovariate(1.0 / spec["gap_len_mean"]), terminal)))

        units.append({
            "i": i, "commissioned": commissioned, "age_at_cut": age_at_cut,
            "t_fail": t_fail, "t_ovhl": t_ovhl, "t_ret": t_ret, "t_adm": t_adm,
            "terminal": terminal, "code": code, "gaps": gaps,
            "model": MODELS[d.randrange(len(MODELS))], "site": SITES[d.randrange(len(SITES))],
        })
    return {"spec": spec, "cut": cut, "units": units}


def truth(world: dict) -> dict:
    """Exact quantities from the latent world (never shipped)."""
    spec, H = world["spec"], float(world["spec"]["horizon"])
    u = world["units"]
    n = float(len(u))
    q1 = sum(1 for x in u if x["t_fail"] <= H and x["t_fail"] < x["t_ovhl"] and x["t_fail"] < x["t_ret"]) / n
    q2 = sum(1 for x in u if x["t_fail"] <= H) / n
    cif_o = sum(1 for x in u if x["t_ovhl"] <= H and x["t_ovhl"] < x["t_fail"] and x["t_ovhl"] < x["t_ret"]) / n
    cif_r = sum(1 for x in u if x["t_ret"] <= H and x["t_ret"] < x["t_fail"] and x["t_ret"] < x["t_ovhl"]) / n
    surv = sum(1 for x in u if min(x["t_fail"], x["t_ovhl"], x["t_ret"]) > H) / n
    return {
        "q1_crude_failure_36": q1, "q2_net_failure_36": q2,
        "cif_failure_36": q1, "cif_overhaul_36": cif_o, "cif_retirement_36": cif_r,
        "survival_36": surv,
        "decision": "expanded" if q1 > spec["gate"] else "baseline",
    }


def write_sqlite(world: dict, out_dir: str) -> str:
    spec, cut = world["spec"], world["cut"]
    p = _rng(spec["seed"], "presentation")
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db = os.path.join(data_dir, "warehouse.sqlite")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    c = con.cursor()
    c.execute("CREATE TABLE asset_register (unit_id TEXT PRIMARY KEY, serial_no TEXT, model_code TEXT,"
              " site_id TEXT, commissioned_on TEXT)")
    c.execute("CREATE TABLE work_orders (wo_id TEXT PRIMARY KEY, unit_id TEXT, wo_date TEXT, wo_type TEXT,"
              " component TEXT, note TEXT)")
    c.execute("CREATE TABLE telemetry_status (unit_id TEXT, channel TEXT, gap_start TEXT, gap_end TEXT)")
    c.execute("CREATE TABLE extract_meta (key TEXT, value TEXT)")

    # identifiers carry no information: shuffled label pool, unrelated to generation order
    labels = list(range(100000, 100000 + len(world["units"]) * 7))
    p.shuffle(labels)
    assets, wos, tel = [], [], []
    for k, x in enumerate(world["units"]):
        uid = "U%06d" % labels[k]
        serial = "SN-%s-%05d" % (x["model"].split("-")[1], labels[k + len(world["units"])] % 100000)
        assets.append((uid, serial, x["model"], x["site"], x["commissioned"].isoformat()))
        if x["code"] is not None:
            wo_date = _months_to_date(x["commissioned"], x["terminal"])
            note = {"UNPL_FAIL": "assembly seized in service; unplanned stop",
                    "PM_OVHL": "scheduled overhaul; critical assembly exchanged for a new unit",
                    "ASSET_RET": "unit withdrawn from the fleet"}[x["code"]]
            wos.append(("W%07d" % labels[k + 2 * len(world["units"])], uid, wo_date.isoformat(),
                        x["code"], "CRITICAL_ASSEMBLY" if x["code"] != "ASSET_RET" else "", note))
        for gi, (g0, g1) in enumerate(x["gaps"]):
            gs = _months_to_date(x["commissioned"], g0)
            ge = _months_to_date(x["commissioned"], g1)
            open_gap = (x["code"] is None and g1 >= x["age_at_cut"] - 0.05)
            tel.append((uid, "VIB-%d" % (1 + gi), gs.isoformat(), None if open_gap else ge.isoformat()))

    p.shuffle(assets); p.shuffle(wos); p.shuffle(tel)     # no generation-order leakage anywhere
    c.executemany("INSERT INTO asset_register VALUES (?,?,?,?,?)", assets)
    c.executemany("INSERT INTO work_orders VALUES (?,?,?,?,?,?)", wos)
    c.executemany("INSERT INTO telemetry_status VALUES (?,?,?,?)", tel)
    c.executemany("INSERT INTO extract_meta VALUES (?,?)", [
        ("extract_cut_off", cut.isoformat()),
        ("extract_scope", "all units commissioned before the cut-off, whatever their current status"),
        ("work_order_scope", "closed work orders only; open orders are excluded"),
        ("telemetry_scope", "channel outage windows; an open window has no end date"),
    ])
    con.commit(); con.close()
    return db


def db_digest(db_path: str) -> str:
    """Content digest, independent of SQLite page layout."""
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for t in ("asset_register", "work_orders", "telemetry_status", "extract_meta"):
        for row in con.execute("SELECT * FROM %s ORDER BY 1,2" % t):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()[:16]


def main(argv):
    out = argv[1]
    spec = copy.deepcopy(VISIBLE_SPEC)
    if len(argv) > 2 and argv[2] != "visible":
        import scenarios
        spec = scenarios.by_name(argv[2])
    w = build(spec)
    db = write_sqlite(w, out)
    sys.stderr.write("wrote %s  digest=%s\n" % (db, db_digest(db)))


if __name__ == "__main__":
    main(sys.argv)
