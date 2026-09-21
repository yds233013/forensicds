"""G36 world generator: residential peak load before and after a time-of-use tariff.

Standard library only, on purpose: the verifier imports this module inside an isolated virtualenv
containing pytest and nothing else, so it cannot depend on numpy or pandas.

Two mechanisms, one stable and one not.

  * STABLE - weather drives air-conditioning load. A tariff does not change physics, so the
    per-segment relationship between cooling-degree-days and peak-window load estimated on the
    flat-tariff history transports unchanged into the tariff regime.

  * UNSTABLE - price drives behaviour. Only the pilot observes it. Two independent facts stop the
    pilot's answer carrying over to the estate:
      (1) households that volunteered for the pilot are far more responsive than the estate, and
      (2) the response shrinks as it gets hotter, because an air conditioner running flat out
          cannot be shifted, and the pilot summer was milder than the target summer is forecast
          to be.
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

SEGMENTS = ("APT_ELECTRIC", "HOUSE_STANDARD", "HOUSE_SMART_HVAC", "HOUSE_LARGE_POOL")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 36100217,
    "n_households": 6000,
    "n_days": 45,
    "n_hist_summers": 2,
    "hist_start_year": 2024,
    "pilot_year": 2026,
    "target_year": 2027,
    "season_start_md": (6, 15),

    # estate composition
    "pop_share": (0.30, 0.34, 0.24, 0.12),
    # who volunteers: controllable, engaged homes volunteer far more often
    "optin_prop": (0.03, 0.05, 0.16, 0.22),

    # STABLE mechanism: peak-window kW = base + beta * cooling-degree-days
    "base": (1.05, 1.80, 2.05, 3.30),
    "beta": (0.055, 0.115, 0.135, 0.230),

    # UNSTABLE mechanism: fractional peak reduction under the tariff, at reference CDD
    "resp0": (0.0245, 0.0490, 0.1155, 0.1435),
    "heat_damping": 0.55,

    "cdd_ref": 10.0,
    "cdd_hist_mean": 10.1,
    "cdd_pilot_mean": 8.6,
    "cdd_target_mean": 12.4,
    "cdd_sd": 2.6,

    "noise_sd": 0.22,
    # Per-customer ceiling implied by the utility's firm capacity position. Derived in
    # research/g36/threshold_provenance.md from historical load, customer count and the
    # regulator's reserve margin - never from any target-regime quantity.
    "capacity_gate": 3.057,
    "resp_scale": 0.70,
}


def _season_dates(sp, year):
    m, d = sp["season_start_md"]
    start = date(year, m, d)
    return [start + timedelta(days=i) for i in range(sp["n_days"])]


def _draw_cdd(rng, sp, mean):
    return [max(rng.gauss(mean, sp["cdd_sd"]), 0.0) for _ in range(sp["n_days"])]


def response_at(sp, seg_idx, cdd):
    """Fractional peak reduction under the tariff for a segment at a given CDD level."""
    damp = 1.0 - sp["heat_damping"] * (cdd - sp["cdd_ref"]) / sp["cdd_ref"]
    return max(0.0, min(0.95, sp["resp0"][seg_idx] * max(damp, 0.05)))


def _load_median(sp, seg_idx, cdd, on_tariff):
    """Median peak-window load. The generator draws observations around THIS."""
    m = sp["base"][seg_idx] + sp["beta"][seg_idx] * cdd
    if on_tariff:
        m *= (1.0 - response_at(sp, seg_idx, cdd))
    return m


def _load_expected(sp, seg_idx, cdd, on_tariff):
    """EXPECTED peak-window load - what the utility must actually serve, and the target quantity.

    An observation is median * exp(N(0, sigma)), whose expectation is median * exp(sigma^2/2).
    Truth must carry that factor; the generator must not. Applying it in one shared helper made all
    three independent estimator families look biased by +2.45% against the truth, which is how the
    error was caught - three genuinely independent methods agreeing on a bias is evidence about the
    truth, not about the methods.
    """
    return _load_median(sp, seg_idx, cdd, on_tariff) * math.exp(0.5 * sp["noise_sd"] ** 2)


def build(spec):
    sp = dict(spec)
    rng = random.Random(sp["seed"])

    seg = []
    cum, r = [], 0.0
    for s in sp["pop_share"]:
        r += s
        cum.append(r)
    for _ in range(sp["n_households"]):
        u = rng.random()
        seg.append(next(i for i, c in enumerate(cum) if u <= c or i == 3))

    # ---- historical summers, flat tariff, whole estate
    hist = []
    for k in range(sp["n_hist_summers"]):
        year = sp["hist_start_year"] + k
        dates = _season_dates(sp, year)
        cdd = _draw_cdd(rng, sp, sp["cdd_hist_mean"])
        rows = []
        for h in range(sp["n_households"]):
            s = seg[h]
            for di in range(sp["n_days"]):
                mu = _load_median(sp, s, cdd[di], False)
                rows.append(mu * math.exp(rng.gauss(0.0, sp["noise_sd"])))
        hist.append({"year": year, "dates": dates, "cdd": cdd, "load": rows})

    # ---- pilot summer: voluntary enrolment, randomised arm INSIDE the opt-in group
    enrolled, arm = [], []
    for h in range(sp["n_households"]):
        e = rng.random() < sp["optin_prop"][seg[h]]
        enrolled.append(e)
        arm.append((1 if rng.random() < 0.5 else 0) if e else None)
    pdates = _season_dates(sp, sp["pilot_year"])
    pcdd = _draw_cdd(rng, sp, sp["cdd_pilot_mean"])
    pilot_rows = []
    for h in range(sp["n_households"]):
        if not enrolled[h]:
            continue
        s = seg[h]
        for di in range(sp["n_days"]):
            mu = _load_median(sp, s, pcdd[di], arm[h] == 1)
            pilot_rows.append((h, di, mu * math.exp(rng.gauss(0.0, sp["noise_sd"]))))

    # ---- target summer: forecast weather only. Outcomes do not exist at decision time.
    tdates = _season_dates(sp, sp["target_year"])
    tcdd = _draw_cdd(rng, sp, sp["cdd_target_mean"])

    return {"spec": sp, "seg": seg, "hist": hist, "enrolled": enrolled, "arm": arm,
            "pilot_dates": pdates, "pilot_cdd": pcdd, "pilot_rows": pilot_rows,
            "target_dates": tdates, "target_cdd": tcdd}


def truth(world_obj):
    """Population mean peak-window load next summer with the whole estate on the tariff.

    Computed from expectations, not sampled, so it is exact for this estate and this forecast
    weather. It is a property of evidence the analyst holds, not a hidden generator constant.
    """
    sp, seg = world_obj["spec"], world_obj["seg"]
    n = len(seg)
    tcdd = world_obj["target_cdd"]
    tot = 0.0
    for h in range(n):
        s = seg[h]
        acc = 0.0
        for c in tcdd:
            acc += _load_expected(sp, s, c, True)
        tot += acc / len(tcdd)
    mean_load = tot / n

    # counterfactual: the same estate and weather with nobody on the tariff
    tot0 = 0.0
    for h in range(n):
        s = seg[h]
        acc = 0.0
        for c in tcdd:
            acc += _load_expected(sp, s, c, False)
        tot0 += acc / len(tcdd)

    shares = [sum(1 for x in seg if x == i) / n for i in range(4)]
    cdd_mean = sum(tcdd) / len(tcdd)
    return {
        "target_peak_mean": mean_load,
        "target_peak_mean_no_tariff": tot0 / n,
        "estate_shares": shares,
        "target_cdd_mean": cdd_mean,
        "response_at_target_cdd": [response_at(sp, i, cdd_mean) for i in range(4)],
        "decision": "procure" if mean_load >= sp["capacity_gate"] else "defer",
    }


def write_sqlite(world_obj, out_dir):
    sp, seg = world_obj["spec"], world_obj["seg"]
    db = os.path.join(out_dir, "warehouse.sqlite")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    c = con.cursor()
    c.execute("CREATE TABLE customer_master (household_id TEXT PRIMARY KEY, segment_code TEXT, "
              "service_zone TEXT, meter_installed_on TEXT)")
    c.execute("CREATE TABLE weather_daily (service_date TEXT PRIMARY KEY, "
              "cooling_degree_days REAL, source TEXT)")
    c.execute("CREATE TABLE peak_window_load (household_id TEXT, service_date TEXT, peak_kw REAL)")
    c.execute("CREATE TABLE tou_pilot_enrolment (household_id TEXT, enrolled_on TEXT, "
              "assigned_arm TEXT)")
    c.execute("CREATE TABLE weather_forecast_2027 (service_date TEXT PRIMARY KEY, "
              "cooling_degree_days_forecast REAL, issued_on TEXT)")
    c.execute("CREATE TABLE extract_meta (key TEXT, value TEXT)")

    p = random.Random(sp["seed"] + 4242)
    hid = ["H%07d" % (1000000 + i) for i in range(sp["n_households"])]
    shuffled = list(range(sp["n_households"]))
    p.shuffle(shuffled)
    hid = [hid[i] for i in shuffled]        # identifier order carries no segment signal
    zones = ["Z%02d" % (1 + p.randrange(12)) for _ in range(sp["n_households"])]

    cm = [(hid[h], SEGMENTS[seg[h]], zones[h],
           (date(2019, 1, 1) + timedelta(days=p.randrange(2000))).isoformat())
          for h in range(sp["n_households"])]
    p.shuffle(cm)
    c.executemany("INSERT INTO customer_master VALUES (?,?,?,?)", cm)

    wx, load = [], []
    for hs in world_obj["hist"]:
        for di, d in enumerate(hs["dates"]):
            wx.append((d.isoformat(), round(hs["cdd"][di], 3), "station_actual"))
        for h in range(sp["n_households"]):
            off = h * sp["n_days"]
            for di, d in enumerate(hs["dates"]):
                load.append((hid[h], d.isoformat(), round(hs["load"][off + di], 4)))
    for di, d in enumerate(world_obj["pilot_dates"]):
        wx.append((d.isoformat(), round(world_obj["pilot_cdd"][di], 3), "station_actual"))
    for h, di, v in world_obj["pilot_rows"]:
        load.append((hid[h], world_obj["pilot_dates"][di].isoformat(), round(v, 4)))

    enrol = []
    for h in range(sp["n_households"]):
        if world_obj["enrolled"][h]:
            enrol.append((hid[h], (date(sp["pilot_year"], 4, 1) +
                                   timedelta(days=p.randrange(45))).isoformat(),
                          "treatment" if world_obj["arm"][h] == 1 else "control"))
    fc = [(d.isoformat(), round(world_obj["target_cdd"][di], 3),
           date(sp["target_year"], 4, 15).isoformat())
          for di, d in enumerate(world_obj["target_dates"])]

    p.shuffle(load); p.shuffle(enrol); p.shuffle(wx)
    c.executemany("INSERT INTO weather_daily VALUES (?,?,?)", wx)
    c.executemany("INSERT INTO peak_window_load VALUES (?,?,?)", load)
    c.executemany("INSERT INTO tou_pilot_enrolment VALUES (?,?,?)", enrol)
    c.executemany("INSERT INTO weather_forecast_2027 VALUES (?,?,?)", fc)
    c.executemany("INSERT INTO extract_meta VALUES (?,?)", [
        ("peak_window", "17:00-21:00 local"),
        ("load_units", "average kW across the peak window"),
        ("history_regime", "flat residential tariff"),
        ("pilot_regime", "voluntary time-of-use pilot, arm assigned at random among enrolments"),
        ("target_regime", "mandatory time-of-use tariff for all residential customers"),
        ("target_season", "%d-06-15 plus %d days" % (sp["target_year"], sp["n_days"] - 1)),
    ])
    con.commit()
    con.close()
    return db


def db_digest(db_path):
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for t in ("customer_master", "weather_daily", "peak_window_load", "tou_pilot_enrolment",
              "weather_forecast_2027", "extract_meta"):
        for row in con.execute("SELECT * FROM %s ORDER BY 1,2" % t):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()[:16]


def main(argv):
    out = argv[1]
    data = os.path.join(out, "data")
    os.makedirs(data, exist_ok=True)
    w = build(VISIBLE_SPEC)
    db = write_sqlite(w, data)
    sys.stderr.write("wrote %s digest=%s\n" % (db, db_digest(db)))


if __name__ == "__main__":
    main(sys.argv)
