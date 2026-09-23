"""G44 pre-build screen: assay PPV under a two-stage testing workflow (research only, no model calls).

Builds whole laboratory months, computes the contract object exactly, and measures each labelled wrong
object against it. Gate in research/g44/concept.md.

    python tools/g44/sim.py [n_worlds]
"""
from __future__ import annotations

import hashlib
import random
import sys

LIMIT = 0.80          # contract: below this PPV the laboratory adds a second confirmatory step
AUDIT_N = 25          # systematic audit: one in AUDIT_N screen-negatives goes to the reference assay


def rng(seed, tag):
    return random.Random(int(hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()[:16], 16))


def build(seed, n_routine=18000, n_panel=2600, prev=None, sens=None, spec=None, enrich=0.35):
    d = rng(seed, "design")
    prev = prev if prev is not None else d.uniform(0.012, 0.050)
    sens = sens if sens is not None else d.uniform(0.90, 0.985)
    spec = spec if spec is not None else d.uniform(0.9915, 0.9985)

    # validation panel: enriched, truth known for every member by construction
    panel = []
    for i in range(n_panel):
        pos = d.random() < enrich
        screen = (d.random() < sens) if pos else (d.random() > spec)
        panel.append({"truth": pos, "screen": screen})

    # routine stream: truth exists but is observed only through the workflow
    routine = []
    neg_seen = 0
    for i in range(n_routine):
        pos = d.random() < prev
        screen = (d.random() < sens) if pos else (d.random() > spec)
        if screen:
            conf, weight = pos, 1.0                      # every screen-positive is confirmed
        else:
            neg_seen += 1
            if neg_seen % AUDIT_N == 0:                  # systematic 1-in-N audit of screen-negatives
                conf, weight = pos, float(AUDIT_N)
            else:
                conf, weight = None, None
        routine.append({"truth": pos, "screen": screen, "conf": conf, "weight": weight})
    return {"seed": seed, "panel": panel, "routine": routine, "prev": prev, "sens": sens, "spec": spec}


def panel_rates(w):
    tp = sum(1 for r in w["panel"] if r["truth"] and r["screen"])
    fn = sum(1 for r in w["panel"] if r["truth"] and not r["screen"])
    fp = sum(1 for r in w["panel"] if not r["truth"] and r["screen"])
    tn = sum(1 for r in w["panel"] if not r["truth"] and not r["screen"])
    return tp / (tp + fn), tn / (tn + fp), (tp, fn, fp, tn)


def truth(w):
    """Contract object: panel sensitivity and specificity transported to the routine prevalence, where
    prevalence comes from the confirmatory results under the known sampling design."""
    se, sp, _ = panel_rates(w)
    num = sum(r["weight"] for r in w["routine"] if r["conf"] is True)
    den = sum(r["weight"] for r in w["routine"] if r["conf"] is not None)
    prev = num / den
    ppv = se * prev / (se * prev + (1 - sp) * (1 - prev))
    return {"sensitivity": round(se, 6), "specificity": round(sp, 6), "prevalence": round(prev, 6),
            "ppv": round(ppv, 6), "decision": "remediate" if ppv < LIMIT else "accept"}


def wrongs(w, t):
    se, sp, (tp, fn, fp, tn) = panel_rates(w)
    R = w["routine"]
    out = {}
    out["W01_panel_ppv_quoted"] = tp / (tp + fp)
    conf = [r for r in R if r["conf"] is not None]
    cp = [r for r in conf if r["screen"]]
    out["W02_ppv_on_confirmed_specimens"] = sum(1 for r in cp if r["conf"]) / max(1, len(cp))
    sprate = sum(1 for r in R if r["screen"]) / len(R)
    f = lambda p: se * p / (se * p + (1 - sp) * (1 - p))
    out["W03_prevalence_is_screen_positive_rate"] = f(sprate)
    out["W04_prevalence_confirmed_pos_over_all"] = f(sum(1 for r in R if r["conf"] is True) / len(R))
    out["W05_audit_weights_ignored"] = f(sum(1 for r in conf if r["conf"]) / len(conf))
    out["W06_unconfirmed_negatives_are_true_negatives"] = f(sum(1 for r in R if r["conf"] is True) / len(R))
    # sensitivity/specificity from routine data, where unverified screen-negatives are taken as negative
    rtp = sum(1 for r in R if r["screen"] and r["conf"] is True)
    rfp = sum(1 for r in R if r["screen"] and r["conf"] is False)
    rfn = sum(1 for r in R if not r["screen"] and r["conf"] is True)
    rtn = sum(1 for r in R if not r["screen"]) - rfn
    rse, rsp = rtp / max(1, rtp + rfn), rtn / max(1, rtn + rfp)
    p = t["prevalence"]
    out["W07_rates_from_routine_data"] = rse * p / (rse * p + (1 - rsp) * (1 - p))
    out["W08_accuracy_substituted"] = (tp + tn) / (tp + tn + fp + fn)
    out["W09_npv_reported"] = (sp * (1 - p)) / (sp * (1 - p) + (1 - se) * p)
    out["W10_enrichment_applied_to_ppv"] = min(1.0, (tp / (tp + fp)) * (p / (tp + fn) * len(w["panel"])))
    return {k: round(v, 6) for k, v in out.items()}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    rows = []
    for i in range(n):
        w = build(44_000_003 + 7717 * i)
        t = truth(w)
        rows.append((w["seed"], t, wrongs(w, t)))
        print(f"seed {w['seed']}: prev {t['prevalence']:.4f}  se {t['sensitivity']:.3f}  sp {t['specificity']:.3f}"
              f"  PPV {t['ppv']:.4f}  {t['decision']}")
    names = sorted(rows[0][2])
    print()
    print(f"{'wrong object':46s} " + "".join(f"{i:>10d}" for i in range(len(rows))) + "   sep  flips")
    for nm in names:
        seps = flips = 0
        cells = []
        for _, t, wr in rows:
            dv = wr[nm] - t["ppv"]
            seps += abs(dv) > 0.001
            flips += ("remediate" if wr[nm] < LIMIT else "accept") != t["decision"]
            cells.append(f"{dv:+10.4f}")
        print(f"{nm:46s} " + "".join(cells) + f"  {seps:>4d}  {flips:>4d}")
    dec = {t["decision"] for _, t, _ in rows}
    print(f"\ndecisions: {sorted(dec)}  ({'VARIES' if len(dec) > 1 else 'CONSTANT - FAILS GATE 1'})")


if __name__ == "__main__":
    main()
