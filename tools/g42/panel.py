"""G42 wrong-object panel against the real generator (research/dev only).

Every wrong object is a correct computation over a wrong construction of the numerator, the
denominator or the aggregation. Labels are fixed in research/g42/concept_v2_exposure_denominator.md
before any number is read. Grading is exact (rate to 4 dp), so separation is strict inequality.

    python tools/g42/panel.py [seed ...]
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

T = Path(__file__).resolve().parents[2] / "candidates/g42-contractor-safety-rate"
sys.path.insert(0, str(T / "environment/build"))
import world  # noqa: E402

PER = None


def panel(w):
    global PER
    spec = w["spec"]
    PER = spec["rate_basis"]
    lim = spec["rate_limit"]
    inw = lambda d: world.in_window(w, d)
    typ = {x["id"]: x["type"] for x in w["workers"]}
    home = {x["id"]: x["home"] for x in w["workers"]}
    worked = [r for r in w["shifts"] if r["kind"] == "WORKED" and inw(r["date"])]
    rec = [c for c in w["cases"] if c["cls"] == "RECORDABLE" and inw(c["occurred"])]
    H = sum(r["hours"] for r in worked)
    t = world.truth(w)

    def rate(h, n):
        return round(PER * n / h, 4) if h else 0.0

    out = {
        "W01_payroll_hours_include_paid_nonwork":
            rate(sum(r["hours"] for r in w["shifts"] if inw(r["date"])), len(rec)),
        "W02_scheduled_hours": rate(sum(r["scheduled"] for r in worked), len(rec)),
        "W03_agency_hours_dropped_cases_kept":
            rate(sum(r["hours"] for r in worked if typ[r["worker"]] == "EMPLOYEE"), len(rec)),
        "W04_agency_excluded_entirely":
            rate(sum(r["hours"] for r in worked if typ[r["worker"]] == "EMPLOYEE"),
                 len([c for c in rec if typ[c["worker"]] == "EMPLOYEE"])),
        "W05_first_aid_counted":
            rate(H, len([c for c in w["cases"] if c["cls"] in ("RECORDABLE", "FIRST_AID") and inw(c["occurred"])])),
        "W06_under_review_counted":
            rate(H, len([c for c in w["cases"] if c["cls"] in ("RECORDABLE", "UNDER_REVIEW") and inw(c["occurred"])])),
        "W07_cases_by_record_date":
            rate(H, len([c for c in w["cases"] if c["cls"] == "RECORDABLE" and inw(c["recorded"])])),
        "W08_one_case_per_event": rate(H, len({c["event"] for c in rec})),
        "W09_headcount_x_2000": rate(2000.0 * len({r["worker"] for r in worked}), len(rec)),
        "W10_mean_of_site_rates": round(sum(t["rate_by_site"].values()) / len(t["rate_by_site"]), 4),
        "W12_calendar_year_window":
            rate(sum(r["hours"] for r in w["shifts"] if r["kind"] == "WORKED" and r["date"].year == w["t1"].year - 1),
                 len([c for c in w["cases"] if c["cls"] == "RECORDABLE" and c["occurred"].year == w["t1"].year - 1])),
    }
    # W11 is a site-level error: hours and cases attributed to the worker's home site.
    worst = 0.0
    for s in w["sites"]:
        h = sum(r["hours"] for r in worked if home[r["worker"]] == s["id"])
        n = len([c for c in rec if home[c["worker"]] == s["id"]])
        if h and t["rate_by_site"].get(s["id"]) is not None:
            worst = max(worst, abs(PER * n / h - t["rate_by_site"][s["id"]]))
    out["W11_home_site_attribution_worst_site"] = round(worst, 4)
    return t, out, lim


def main():
    seeds = [int(x) for x in sys.argv[1:]] or [world.VISIBLE_SPEC["seed"]]
    rows = []
    for s in seeds:
        spec = dict(world.VISIBLE_SPEC, seed=s, name=f"seed{s}")
        w = world.build(spec)
        t, out, lim = panel(w)
        rows.append((s, t, out, lim))
        print(f"seed {s:>10}: hours {t['hours_worked']:11.0f}  cases {t['recordable_cases']:3d}  "
              f"rate {t['rate']:6.3f}  {t['decision']}")
    names = sorted(rows[0][2])
    print()
    print(f"{'wrong object':46s} " + "".join(f"{i:>9d}" for i in range(len(rows))) + "   sep  flips")
    summary = {}
    for nm in names:
        seps = flips = 0
        cells = []
        for _, t, out, lim in rows:
            if nm.startswith("W11"):
                dv = out[nm]                       # already an absolute site-level error
                seps += dv > 0.0001
                cells.append(f"{dv:+9.3f}")
                continue
            dv = out[nm] - t["rate"]
            seps += abs(dv) > 0.0001
            flips += ("suspend" if out[nm] > lim else "clear") != t["decision"]
            cells.append(f"{dv:+9.3f}")
        summary[nm] = {"separated_on": seps, "decision_flips": flips, "n": len(rows)}
        print(f"{nm:46s} " + "".join(cells) + f"  {seps:>4d}  {flips:>4d}")
    Path(os.path.dirname(os.path.abspath(__file__)), "panel_results.json").write_text(
        json.dumps(summary, indent=1) + "\n")
    dec = {t["decision"] for _, t, _, _ in rows}
    print(f"\ndecisions: {sorted(dec)}  ({'VARIES' if len(dec) > 1 else 'CONSTANT'})")


if __name__ == "__main__":
    main()
