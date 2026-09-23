"""G42 v2 pre-build screen: recordable incident rate for a client access requirement.

Research only, no model calls. Builds whole worlds, computes the contractual rate exactly, and
measures each labelled wrong object against it. Gate in research/g42/concept_v2_exposure_denominator.md.

    python tools/g42/sim2.py [n_worlds]
"""
from __future__ import annotations

import hashlib
import random
import sys
from datetime import date, timedelta

LIMIT = 1.50                 # client access requirement on the trailing-12-month recordable rate
PER = 200_000.0
T1 = date(2026, 7, 1)        # window end (exclusive); window is the trailing 12 months
T0 = date(2025, 7, 1)


def rng(seed, tag):
    return random.Random(int(hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()[:16], 16))


def build(seed):
    d = rng(seed, "design")
    n_sites = 30
    sites = []
    for i in range(n_sites):
        # extremely skewed: a couple of major sites, a tail of small ones
        crew = max(3, int(d.lognormvariate(3.0, 1.05)))
        sites.append({"id": f"SITE-{i:02d}", "region": f"REG-{i % 3}", "crew": crew,
                      "hazard": d.lognormvariate(-0.2, 0.7)})
    workers = []
    wid = 0
    for s in sites:
        for _ in range(s["crew"]):
            wid += 1
            kind = "AGENCY" if d.random() < 0.28 else "EMPLOYEE"
            workers.append({"id": f"W{4000+wid}", "home": s["id"], "kind": kind,
                            "start": T0 - timedelta(days=d.randint(0, 900)) if d.random() < 0.8
                                     else T0 + timedelta(days=d.randint(0, 300)),
                            "end": None if d.random() < 0.88 else T0 + timedelta(days=d.randint(60, 360)),
                            "multi": d.random() < 0.18})
    return {"seed": seed, "sites": sites, "workers": workers,
            "hours_rate": d.uniform(0.93, 1.06), "case_rate": d.uniform(0.55, 2.4)}


def shifts(w):
    """Shift records: worked hours by (worker, site, date), plus paid non-work hours."""
    out = []
    for wk in w["workers"]:
        d = rng(f"{w['seed']}:{wk['id']}", "shift")
        day = T0
        while day < T1:
            if wk["start"] <= day and (wk["end"] is None or day < wk["end"]) and day.weekday() < 5:
                site = wk["home"]
                if wk["multi"] and d.random() < 0.35:
                    site = d.choice([s["id"] for s in w["sites"]])
                worked = 8.0 + (2.5 if d.random() < 0.22 else 0.0)        # overtime
                kind = "WORKED"
                if d.random() < 0.09:
                    kind, worked = d.choice(["PTO", "HOLIDAY", "TRAINING", "TRAVEL"]), 8.0
                out.append({"worker": wk["id"], "site": site, "date": day, "hours": worked * w["hours_rate"],
                            "kind": kind, "scheduled": 8.0})
            day += timedelta(days=1)
    return out


def cases(w):
    """Incident cases: several may share one event; classification and occurrence vs record date."""
    out = []
    ev = 0
    for s in w["sites"]:
        d = rng(f"{w['seed']}:{s['id']}", "case")
        n_ev = max(0, int(d.gauss(s["crew"] * 0.022 * s["hazard"] * w["case_rate"], 0.9)))
        pool = [x for x in w["workers"] if x["home"] == s["id"]] or w["workers"]
        for _ in range(n_ev):
            ev += 1
            occurred = T0 + timedelta(days=d.randint(-60, 364))            # some occur before the window
            recorded = occurred + timedelta(days=d.randint(0, 45))
            hurt = d.sample(pool, min(len(pool), 2 if d.random() < 0.15 else 1))
            for p in hurt:
                u = d.random()
                cls = ("FIRST_AID" if u < 0.42 else
                       "UNDER_REVIEW" if u < 0.52 else
                       "NOT_WORK_RELATED" if u < 0.58 else "RECORDABLE")
                site = s["id"] if not p["multi"] or d.random() < 0.6 else d.choice([x["id"] for x in w["sites"]])
                out.append({"event": f"EV-{ev}", "worker": p["id"], "site": site, "occurred": occurred,
                            "recorded": recorded, "cls": cls})
    return out


def in_window(day):
    return T0 <= day < T1


# --------------------------------------------------------------------------------- the contract object
def truth(w, sh, cs):
    hours = sum(r["hours"] for r in sh if r["kind"] == "WORKED" and in_window(r["date"]))
    rec = [c for c in cs if c["cls"] == "RECORDABLE" and in_window(c["occurred"])]
    rate = PER * len(rec) / hours if hours else 0.0
    by_site = {}
    for s in w["sites"]:
        h = sum(r["hours"] for r in sh if r["kind"] == "WORKED" and in_window(r["date"]) and r["site"] == s["id"])
        n = len([c for c in rec if c["site"] == s["id"]])
        by_site[s["id"]] = round(PER * n / h, 4) if h else None
    return {"rate": round(rate, 4), "cases": len(rec), "hours": round(hours, 2), "by_site": by_site,
            "decision": "suspend" if rate > LIMIT else "clear"}


def wrongs(w, sh, cs, t):
    home = {x["id"]: x["home"] for x in w["workers"]}
    kind = {x["id"]: x["kind"] for x in w["workers"]}
    W = {}

    def rate(hours, n):
        return round(PER * n / hours, 4) if hours else 0.0

    worked = [r for r in sh if r["kind"] == "WORKED" and in_window(r["date"])]
    rec = [c for c in cs if c["cls"] == "RECORDABLE" and in_window(c["occurred"])]
    H = sum(r["hours"] for r in worked)

    W["W01_payroll_hours_include_paid_nonwork"] = rate(
        sum(r["hours"] for r in sh if in_window(r["date"])), len(rec))
    W["W02_scheduled_hours"] = rate(sum(r["scheduled"] for r in worked), len(rec))
    W["W03_agency_hours_dropped_cases_kept"] = rate(
        sum(r["hours"] for r in worked if kind[r["worker"]] == "EMPLOYEE"), len(rec))
    W["W04_agency_excluded_entirely"] = rate(
        sum(r["hours"] for r in worked if kind[r["worker"]] == "EMPLOYEE"),
        len([c for c in rec if kind[c["worker"]] == "EMPLOYEE"]))
    W["W05_first_aid_counted"] = rate(H, len([c for c in cs if c["cls"] in ("RECORDABLE", "FIRST_AID")
                                              and in_window(c["occurred"])]))
    W["W06_under_review_counted"] = rate(H, len([c for c in cs if c["cls"] in ("RECORDABLE", "UNDER_REVIEW")
                                                 and in_window(c["occurred"])]))
    W["W07_cases_by_record_date"] = rate(H, len([c for c in cs if c["cls"] == "RECORDABLE"
                                                 and in_window(c["recorded"])]))
    W["W08_one_case_per_event"] = rate(H, len({c["event"] for c in rec}))
    W["W09_headcount_x_2000"] = rate(2000.0 * len({r["worker"] for r in worked}), len(rec))
    site_rates = [v for v in t["by_site"].values() if v is not None]
    W["W10_mean_of_site_rates"] = round(sum(site_rates) / len(site_rates), 4) if site_rates else 0.0
    W["W11_home_site_attribution"] = t["rate"]            # company total unchanged; see site-level check
    W["W13_per_100_workers"] = round(100.0 * len(rec) / max(1, len({r["worker"] for r in worked})), 4)
    return W


def site_attribution_error(w, sh, cs, t):
    """W11 is a site-level error: how far does home-site attribution move a site's rate?"""
    home = {x["id"]: x["home"] for x in w["workers"]}
    rec = [c for c in cs if c["cls"] == "RECORDABLE" and in_window(c["occurred"])]
    worked = [r for r in sh if r["kind"] == "WORKED" and in_window(r["date"])]
    worst = 0.0
    for s in w["sites"]:
        h = sum(r["hours"] for r in worked if home[r["worker"]] == s["id"])
        n = len([c for c in rec if home[c["worker"]] == s["id"]])
        alt = PER * n / h if h else None
        true = t["by_site"][s["id"]]
        if alt is not None and true is not None:
            worst = max(worst, abs(alt - true))
    return round(worst, 4)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rows = []
    for i in range(n):
        seed = 42_000_017 + 6151 * i
        w = build(seed)
        sh, cs = shifts(w), cases(w)
        t = truth(w, sh, cs)
        rows.append((seed, t, wrongs(w, sh, cs, t), site_attribution_error(w, sh, cs, t)))
        print(f"seed {seed}: hours {t['hours']:10.0f}  cases {t['cases']:3d}  rate {t['rate']:6.3f}  {t['decision']}"
              f"   (worst site-attribution error {rows[-1][3]:.3f})")
    names = sorted(rows[0][2])
    print()
    print(f"{'wrong object':46s} " + "".join(f"{i:>9d}" for i in range(len(rows))) + "   sep  flips")
    for nm in names:
        seps = flips = 0
        cells = []
        for _, t, wr, _ in rows:
            dv = wr[nm] - t["rate"]
            if abs(dv) > 0.01:
                seps += 1
            if ("suspend" if wr[nm] > LIMIT else "clear") != t["decision"]:
                flips += 1
            cells.append(f"{dv:+9.3f}")
        print(f"{nm:46s} " + "".join(cells) + f"  {seps:>4d}  {flips:>4d}")
    dec = {t["decision"] for _, t, _, _ in rows}
    print(f"\ndecisions across worlds: {sorted(dec)}  ({'VARIES' if len(dec) > 1 else 'CONSTANT - FAILS GATE 1'})")


if __name__ == "__main__":
    main()
