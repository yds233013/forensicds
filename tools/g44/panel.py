"""G44 wrong-object panel against the real generator (research/dev only).

Each wrong object is a correct computation over a wrong construction of the screen's performance or of
the population the contract is written on. Labels are fixed in research/g44/concept.md before any
number is read. Grading is exact to 4 dp on the contract precision.

    python tools/g44/panel.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

T = Path(__file__).resolve().parents[2] / "candidates/g44-screening-precision"
sys.path.insert(0, str(T / "environment/build"))
import scenarios  # noqa: E402
import world  # noqa: E402


def ppv(se, sp, p):
    d = se * p + (1 - sp) * (1 - p)
    return se * p / d if d else 0.0


def panel(w):
    spec = w["spec"]
    N = spec["quality_sample_n"]
    p = spec["contract_fraud_rate"]
    R = w["reviews"]
    t = world.truth(w)

    def counts(rows, weighted=True, treat_unsampled_as_clean=False):
        tp = fp = fn = tn = 0.0
        for r in rows:
            wt = (float(N) if r["source"] == "QUALITY_SAMPLE" else 1.0) if weighted else 1.0
            if r["_decision"] == "FLAG":
                tp += wt if r["_fraud"] else 0.0
                fp += 0.0 if r["_fraud"] else wt
            else:
                fn += wt if r["_fraud"] else 0.0
                tn += 0.0 if r["_fraud"] else wt
        if treat_unsampled_as_clean:
            passed = sum(1 for x in w["txns"] if x["decision"] == "PASS")
            tn = passed - fn
        return tp, fp, fn, tn

    def rates(c):
        tp, fp, fn, tn = c
        return (tp / (tp + fn) if tp + fn else 0.0), (tn / (tn + fp) if tn + fp else 0.0)

    sample = [r for r in R if r["source"] != "AD_HOC" and not r["_pending"]]
    out = {}
    # panel: the published benchmark case set
    ptp = sum(1 for x in w["panel"] if x["fraud"] and x["decision"] == "FLAG")
    pfn = sum(1 for x in w["panel"] if x["fraud"] and x["decision"] == "PASS")
    pfp = sum(1 for x in w["panel"] if not x["fraud"] and x["decision"] == "FLAG")
    ptn = sum(1 for x in w["panel"] if not x["fraud"] and x["decision"] == "PASS")
    out["W01_benchmark_panel_precision"] = ptp / (ptp + pfp)
    out["W02_benchmark_panel_rates_transported"] = ppv(ptp / (ptp + pfn), ptn / (ptn + pfp), p)
    out["W03_own_traffic_precision"] = t["observed_precision"]
    se, sp = rates(counts(sample, weighted=False))
    out["W04_sample_weights_ignored"] = ppv(se, sp, p)
    allrev = [r for r in R if not r["_pending"]]
    se, sp = rates(counts(allrev))
    out["W05_ad_hoc_reviews_included"] = ppv(se, sp, p)
    pend = [r for r in R if r["source"] != "AD_HOC"]
    tp = fp = fn = tn = 0.0
    for r in pend:                                   # pending treated as legitimate
        wt = float(N) if r["source"] == "QUALITY_SAMPLE" else 1.0
        fraud = r["_fraud"] and not r["_pending"]
        if r["_decision"] == "FLAG":
            tp += wt if fraud else 0.0
            fp += 0.0 if fraud else wt
        else:
            fn += wt if fraud else 0.0
            tn += 0.0 if fraud else wt
    out["W06_pending_counted_as_legitimate"] = ppv(tp / (tp + fn), tn / (tn + fp), p)
    se, sp = rates(counts(sample, treat_unsampled_as_clean=True))
    out["W07_unsampled_passes_are_true_negatives"] = ppv(se, sp, p)
    # transported at Kestrel's own book rate rather than the merchant's
    own = (sum(float(N) if r["source"] == "QUALITY_SAMPLE" else 1.0 for r in sample if r["_fraud"]) /
           sum(float(N) if r["source"] == "QUALITY_SAMPLE" else 1.0 for r in sample))
    out["W08_transported_at_own_book_rate"] = ppv(t["sensitivity"], t["specificity"], own)
    out["W09_npv_reported"] = ppv(t["specificity"], t["sensitivity"], 1 - p) if False else (
        t["specificity"] * (1 - p)) / (t["specificity"] * (1 - p) + (1 - t["sensitivity"]) * p)
    out["W10_sensitivity_and_specificity_swapped"] = ppv(t["specificity"], t["sensitivity"], p)
    out["W11_prevalence_omitted_from_transport"] = t["sensitivity"] / (t["sensitivity"] + (1 - t["specificity"]))
    out["W12_flag_rate_used_as_prevalence"] = ppv(t["sensitivity"], t["specificity"],
                                                  sum(1 for x in w["txns"] if x["decision"] == "FLAG") / len(w["txns"]))
    return t, {k: round(v, 6) for k, v in out.items()}, spec["precision_floor"]


def main():
    rows = []
    for n in scenarios.ALL_NAMES:
        w = world.build(scenarios.by_name(n))
        t, out, lim = panel(w)
        rows.append((n, t, out, lim))
        print(f"{n:9s}: se {t['sensitivity']:.4f}  sp {t['specificity']:.5f}  own {t['observed_precision']:.4f}  "
              f"contract {t['contract_precision']:.4f}  {t['decision']}")
    names = sorted(rows[0][2])
    summary = {}
    print()
    print(f"{'wrong object':46s} " + "".join(f"{n:>11s}" for n, *_ in rows) + "   sep  flips")
    for nm in names:
        seps = flips = 0
        cells = []
        for _, t, out, lim in rows:
            dv = out[nm] - t["contract_precision"]
            seps += abs(dv) > 0.0001
            flips += ("remediate" if out[nm] < lim else "accept") != t["decision"]
            cells.append(f"{dv:+11.4f}")
        summary[nm] = {"separated_on": seps, "decision_flips": flips, "n": len(rows)}
        print(f"{nm:46s} " + "".join(cells) + f"  {seps:>4d}  {flips:>4d}")
    Path(os.path.dirname(os.path.abspath(__file__)), "panel_results.json").write_text(
        json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
