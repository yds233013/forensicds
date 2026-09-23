"""G44 v2 pre-build screen: assay PPV transported to the client's deployment population.

The v1 design was rejected in screening: because every routine screen-positive is confirmed, the
routine PPV is directly countable, so the "transport" object was one defensible estimator among two
that disagree - identifiable but not gradable (principle 16).

v2 fixes the object. The contract is written on the PPV the CLIENT's screening programme would see, at
a prevalence the contract states (their population is not the laboratory's), and it requires the
performance to be demonstrated on the laboratory's own runs rather than on the vendor's panel. So:

    sensitivity, specificity  <- the laboratory's routine data, under the known audit sampling design
    PPV                       <- transported to the contract prevalence

Neither number is directly countable, and the audit weights are load-bearing: screen-negatives are
confirmed at 1-in-N, so unweighted counts understate false negatives by a factor of N.

    python tools/g44/sim2.py [n_worlds]
"""
from __future__ import annotations

import hashlib
import random
import sys

LIMIT = 0.80
AUDIT_N = 10
CLIENT_PREV = 0.0075          # stated in the client's contract (their screening programme)


def rng(seed, tag):
    return random.Random(int(hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()[:16], 16))


def build(seed, n_routine=45000, n_panel=2600, prev=None, sens=None, spec=None, enrich=0.35,
          client_prev=CLIENT_PREV):
    d = rng(seed, "design")
    prev = prev if prev is not None else d.uniform(0.02, 0.06)          # the laboratory's own mix
    sens = sens if sens is not None else d.uniform(0.90, 0.99)
    spec = spec if spec is not None else d.uniform(0.9955, 0.9995)
    panel = []
    for _ in range(n_panel):
        pos = d.random() < enrich
        screen = (d.random() < sens * 1.02) if pos else (d.random() > min(0.9999, spec * 1.002))
        panel.append({"truth": pos, "screen": screen})                  # vendor lot: slightly better
    routine, neg_seen = [], 0
    for _ in range(n_routine):
        pos = d.random() < prev
        screen = (d.random() < sens) if pos else (d.random() > spec)
        if screen:
            conf, weight = pos, 1.0
        else:
            neg_seen += 1
            if neg_seen % AUDIT_N == 0:
                conf, weight = pos, float(AUDIT_N)
            else:
                conf, weight = None, None
        routine.append({"truth": pos, "screen": screen, "conf": conf, "weight": weight})
    return {"seed": seed, "panel": panel, "routine": routine, "client_prev": client_prev,
            "prev": prev, "sens": sens, "spec": spec}


def ppv(se, sp, p):
    return se * p / (se * p + (1 - sp) * (1 - p))


def truth(w):
    R = w["routine"]
    tp = sum(r["weight"] for r in R if r["screen"] and r["conf"] is True)
    fp = sum(r["weight"] for r in R if r["screen"] and r["conf"] is False)
    fn = sum(r["weight"] for r in R if not r["screen"] and r["conf"] is True)
    tn = sum(r["weight"] for r in R if not r["screen"] and r["conf"] is False)
    se, sp = tp / (tp + fn), tn / (tn + fp)
    v = ppv(se, sp, w["client_prev"])
    return {"sensitivity": round(se, 6), "specificity": round(sp, 6), "ppv": round(v, 6),
            "decision": "remediate" if v < LIMIT else "accept"}


def wrongs(w, t):
    R, P = w["routine"], w["panel"]
    p = w["client_prev"]
    out = {}
    # panel rates and panel PPV
    ptp = sum(1 for r in P if r["truth"] and r["screen"]); pfn = sum(1 for r in P if r["truth"] and not r["screen"])
    pfp = sum(1 for r in P if not r["truth"] and r["screen"]); ptn = sum(1 for r in P if not r["truth"] and not r["screen"])
    pse, psp = ptp / (ptp + pfn), ptn / (ptn + pfp)
    out["W01_vendor_panel_ppv_quoted"] = ptp / (ptp + pfp)
    out["W02_vendor_panel_rates_transported"] = ppv(pse, psp, p)
    # the laboratory's own observed PPV, at its own mix rather than the client's
    sp_rows = [r for r in R if r["screen"]]
    out["W03_laboratory_own_ppv"] = sum(1 for r in sp_rows if r["conf"]) / len(sp_rows)
    # audit weights ignored
    u = lambda cond: sum(1 for r in R if cond(r))
    tp = u(lambda r: r["screen"] and r["conf"] is True); fp = u(lambda r: r["screen"] and r["conf"] is False)
    fn = u(lambda r: not r["screen"] and r["conf"] is True); tn = u(lambda r: not r["screen"] and r["conf"] is False)
    out["W04_audit_weights_ignored"] = ppv(tp / max(1, tp + fn), tn / max(1, tn + fp), p)
    # unaudited screen-negatives treated as confirmed negatives
    tn_all = u(lambda r: not r["screen"]) - fn
    out["W05_unaudited_negatives_are_true_negatives"] = ppv(tp / max(1, tp + fn), tn_all / max(1, tn_all + fp), p)
    # transported at the laboratory's own prevalence instead of the client's
    out["W06_transported_at_laboratory_prevalence"] = ppv(t["sensitivity"], t["specificity"],
                                                          sum(r["weight"] for r in R if r["conf"] is True) /
                                                          sum(r["weight"] for r in R if r["conf"] is not None))
    out["W07_npv_reported"] = (t["specificity"] * (1 - p)) / (t["specificity"] * (1 - p) +
                                                              (1 - t["sensitivity"]) * p)
    out["W08_accuracy_substituted"] = (ptp + ptn) / len(P)
    out["W09_sensitivity_and_specificity_swapped"] = ppv(t["specificity"], t["sensitivity"], p)
    out["W10_prevalence_odds_not_applied"] = t["sensitivity"] / (t["sensitivity"] + (1 - t["specificity"]))
    return {k: round(v, 6) for k, v in out.items()}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    rows = []
    for i in range(n):
        w = build(44_100_007 + 8123 * i)
        t = truth(w)
        rows.append((w["seed"], t, wrongs(w, t)))
        print(f"seed {w['seed']}: se {t['sensitivity']:.4f}  sp {t['specificity']:.5f}  "
              f"PPV@{w['client_prev']:.4f} {t['ppv']:.4f}  {t['decision']}")
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
