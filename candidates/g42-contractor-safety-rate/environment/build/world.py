"""Deterministic generator for the Meridian Industrial Services safety warehouse (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/warehouse.sqlite

The same module builds the hidden extracts and the exact truth for the verifier. Design draws (crews,
shifts, incidents) and presentation draws (row order, identifiers) use separate streams.

What the contract rate is computed on, and what the warehouse actually holds:
  * hours come from shift entries, which include paid time that is not hours worked (PTO, holiday,
    training, travel) alongside worked time and overtime;
  * agency workers sit in the same shift table with a different worker type; the standard puts both
    their hours and their cases on the host employer's rate;
  * a case is recordable only once it is classified so - first aid and cases still under review are
    not - and it belongs to the period in which the incident OCCURRED, not the one it was entered in;
  * one event can injure more than one worker, which is more than one case;
  * hours belong to the site where the shift was worked; a case belongs to the site of the incident.
"""
from __future__ import annotations

import copy
import hashlib
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

REGIONS = ("GULF", "MIDWEST", "NORTHEAST")
HOUR_TYPES = ("WORKED", "PTO", "HOLIDAY", "TRAINING", "TRAVEL")
CLASSES = ("RECORDABLE", "FIRST_AID", "UNDER_REVIEW", "NOT_WORK_RELATED")
BODY = ("hand", "back", "eye", "knee", "shoulder", "foot", "head")
AGENCIES = ("Corville Staffing", "Baytown Labor Partners", "Northline Crew Services")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 6102447,
    "window_end": "2026-07-01",          # exclusive; the window is the trailing 12 months
    "window_months": 12,
    "rate_basis": 200000,
    "rate_limit": 1.50,                  # client access requirement
    "n_sites": 30,
    "crew_mu": 3.0, "crew_sigma": 1.05,
    "agency_share": 0.28,
    "multi_site_share": 0.18,
    "overtime_share": 0.22,
    "nonwork_share": 0.09,               # share of shift entries that are paid but not worked
    "case_rate": 1.35,
    "hazard_sigma": 0.7,
    "late_entry_days": 45,
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def build(spec: dict) -> dict:
    d = _rng(spec["seed"], "design")
    t1 = date.fromisoformat(spec["window_end"])
    t0 = date(t1.year - 1, t1.month, t1.day)

    sites = []
    for i in range(spec["n_sites"]):
        crew = max(3, int(d.lognormvariate(spec["crew_mu"], spec["crew_sigma"])))
        sites.append({"id": f"SITE-{i:02d}", "region": REGIONS[i % len(REGIONS)], "crew": crew,
                      "hazard": d.lognormvariate(-0.2, spec["hazard_sigma"])})

    workers, wid = [], 0
    for s in sites:
        for _ in range(s["crew"]):
            wid += 1
            workers.append({
                "id": f"W{40000 + wid}", "home": s["id"],
                "type": "AGENCY" if d.random() < spec["agency_share"] else "EMPLOYEE",
                "agency": d.choice(AGENCIES),
                "hired": t0 - timedelta(days=d.randint(1, 1400)) if d.random() < 0.8
                         else t0 + timedelta(days=d.randint(0, 300)),
                "left": None if d.random() < 0.88 else t0 + timedelta(days=d.randint(60, 360)),
                "multi": d.random() < spec["multi_site_share"]})

    shifts = []
    site_ids = [s["id"] for s in sites]
    for wk in workers:
        r = _rng(f"{spec['seed']}:{wk['id']}", "shift")
        day = t0
        while day < t1:
            on = wk["hired"] <= day and (wk["left"] is None or day < wk["left"]) and day.weekday() < 5
            if on:
                site = wk["home"]
                if wk["multi"] and r.random() < 0.35:
                    site = r.choice(site_ids)
                kind, hours = "WORKED", 8.0 + (r.uniform(1.0, 4.0) if r.random() < spec["overtime_share"] else 0.0)
                if r.random() < spec["nonwork_share"]:
                    kind, hours = r.choice(HOUR_TYPES[1:]), 8.0
                shifts.append({"worker": wk["id"], "site": site, "date": day,
                               "hours": round(hours, 2), "kind": kind, "scheduled": 8.0})
            day += timedelta(days=1)

    cases, ev = [], 0
    for s in sites:
        r = _rng(f"{spec['seed']}:{s['id']}", "case")
        n_ev = max(0, int(r.gauss(s["crew"] * 0.022 * s["hazard"] * spec["case_rate"], 0.9)))
        pool = [x for x in workers if x["home"] == s["id"]] or workers
        for _ in range(n_ev):
            ev += 1
            occurred = t0 + timedelta(days=r.randint(-60, (t1 - t0).days - 1))
            recorded = occurred + timedelta(days=r.randint(0, spec["late_entry_days"]))
            # A serious event (a release, a struck-by, a fall) tends to injure more than one worker
            # and to injure them beyond first aid; a nuisance event is usually one worker, first aid.
            serious = r.random() < 0.22
            n_hurt = (2 if r.random() < 0.55 else 3) if serious else 1
            hurt = r.sample(pool, min(len(pool), n_hurt))
            for p in hurt:
                u = r.random()
                if serious:
                    cls = "RECORDABLE" if u < 0.72 else ("UNDER_REVIEW" if u < 0.86 else "FIRST_AID")
                else:
                    cls = ("FIRST_AID" if u < 0.52 else "UNDER_REVIEW" if u < 0.62 else
                           "NOT_WORK_RELATED" if u < 0.70 else "RECORDABLE")
                site = s["id"] if (not p["multi"] or r.random() < 0.6) else r.choice(site_ids)
                cases.append({"event": f"EV-{ev:05d}", "worker": p["id"], "site": site,
                              "occurred": occurred, "recorded": recorded, "cls": cls,
                              "body": r.choice(BODY)})

    return {"spec": spec, "t0": t0, "t1": t1, "sites": sites, "workers": workers,
            "shifts": shifts, "cases": cases}


# ------------------------------------------------------------------------- the contract quantities
def in_window(w, day) -> bool:
    return w["t0"] <= day < w["t1"]


def truth(w: dict) -> dict:
    """Recordable incident rate per 200,000 hours worked over the trailing twelve months."""
    spec = w["spec"]
    worked = [r for r in w["shifts"] if r["kind"] == "WORKED" and in_window(w, r["date"])]
    rec = [c for c in w["cases"] if c["cls"] == "RECORDABLE" and in_window(w, c["occurred"])]
    hours = round(sum(r["hours"] for r in worked), 2)
    rate = round(spec["rate_basis"] * len(rec) / hours, 4) if hours else 0.0
    by_site = {}
    for s in w["sites"]:
        h = round(sum(r["hours"] for r in worked if r["site"] == s["id"]), 2)
        if h <= 0:
            continue
        n = len([c for c in rec if c["site"] == s["id"]])
        by_site[s["id"]] = round(spec["rate_basis"] * n / h, 4)
    return {"hours_worked": hours, "recordable_cases": len(rec), "rate": rate,
            "rate_by_site": dict(sorted(by_site.items())),
            "decision": "suspend" if rate > spec["rate_limit"] else "clear",
            "window_start": w["t0"].isoformat(), "window_end": w["t1"].isoformat()}


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
    c.execute("CREATE TABLE sites (site_id TEXT PRIMARY KEY, region TEXT, client TEXT)")
    c.execute("CREATE TABLE workers (worker_id TEXT PRIMARY KEY, home_site_id TEXT, worker_type TEXT, "
              "agency_name TEXT, hired_on TEXT, left_on TEXT)")
    c.execute("CREATE TABLE shift_entries (entry_id TEXT PRIMARY KEY, worker_id TEXT, site_id TEXT, "
              "work_date TEXT, hours REAL, hour_type TEXT, scheduled_hours REAL)")
    c.execute("CREATE TABLE incident_cases (case_id TEXT PRIMARY KEY, event_id TEXT, worker_id TEXT, "
              "site_id TEXT, occurred_on TEXT, recorded_on TEXT, classification TEXT, body_part TEXT)")
    c.execute("CREATE TABLE contract_terms (key TEXT, value TEXT)")

    labels = list(range(500000, 500000 + 900000))
    p.shuffle(labels)
    it = iter(labels)
    site_rows = [(s["id"], s["region"], f"{s['region'].title()} Operator {i % 4 + 1}")
                 for i, s in enumerate(w["sites"])]
    worker_rows = [(x["id"], x["home"], x["type"], x["agency"] if x["type"] == "AGENCY" else None,
                    x["hired"].isoformat(), x["left"].isoformat() if x["left"] else None)
                   for x in w["workers"]]
    shift_rows = [(f"SE-{next(it)}", r["worker"], r["site"], r["date"].isoformat(), r["hours"],
                   r["kind"], r["scheduled"]) for r in w["shifts"]]
    case_rows = [(f"CASE-{next(it)}", c0["event"], c0["worker"], c0["site"], c0["occurred"].isoformat(),
                  c0["recorded"].isoformat(), c0["cls"], c0["body"]) for c0 in w["cases"]]
    for rows in (site_rows, worker_rows, shift_rows, case_rows):
        p.shuffle(rows)
    c.executemany("INSERT INTO sites VALUES (?,?,?)", site_rows)
    c.executemany("INSERT INTO workers VALUES (?,?,?,?,?,?)", worker_rows)
    c.executemany("INSERT INTO shift_entries VALUES (?,?,?,?,?,?,?)", shift_rows)
    c.executemany("INSERT INTO incident_cases VALUES (?,?,?,?,?,?,?,?)", case_rows)
    c.executemany("INSERT INTO contract_terms VALUES (?,?)", [
        ("reporting_window_end", w["t1"].isoformat()),
        ("reporting_window_months", str(spec["window_months"])),
        ("rate_basis_hours", str(spec["rate_basis"])),
        ("rate_limit", f"{spec['rate_limit']:.2f}"),
        ("hour_type_values", " | ".join(HOUR_TYPES)),
        ("classification_values", " | ".join(CLASSES)),
        ("worker_type_values", "EMPLOYEE | AGENCY (supervised by Meridian on site)"),
    ])
    con.commit()
    con.close()
    return db


def db_digest(db_path: str) -> str:
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for t in ("sites", "workers", "shift_entries", "incident_cases", "contract_terms"):
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
