"""G35 remaining gates: coherent-but-wrong, cheap-solve panel, constant decision, leakage probes.

Research/dev only.  No model call, no container, no network.
    python research/g35/gates.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulation import REGIMES, SATURATIONS, est_f1, truth_f1, world_f1   # noqa: E402


def _wmean(y, w):
    return float((y * w).sum() / w.sum()) if w.sum() > 0 else float("nan")


def coherent_wrong(w, t):
    """Wrong analyses that satisfy every obvious internal-consistency check.

    Each returns (value_reported_as_policy_effect, coherence_report).  The coherence report is the
    set of identities a reviewer would check; all of them hold.
    """
    dem, pi, A, Y = w["dem"], w["pi"], w["assigned"], w["Y"]
    d_b = dem.sum(axis=1)
    y_b = np.divide((Y * dem).sum(axis=1), d_b, out=np.zeros_like(d_b), where=d_b > 0)
    out = {}

    m0, m50 = pi == 0.0, pi == 0.5
    y0 = _wmean(y_b[m0], d_b[m0])
    wt, wc = dem[m50] * A[m50], dem[m50] * (~A[m50])
    yT = _wmean(Y[m50], wt)
    yC = _wmean(Y[m50], wc)
    direct = yT - yC
    spill = yC - y0
    total50 = _wmean(y_b[m50], d_b[m50]) - y0

    # CW1: the whole mixed experiment, correctly measured, reported as the rollout effect.
    # Coherence: total50 == 0.5*direct + spill, to numerical precision.  It does hold.
    out["CW1_total_at_50_as_policy"] = dict(
        value=total50,
        identity_lhs=total50, identity_rhs=0.5 * direct + spill,
        note="decomposition of the 50% arm is exact; the object is simply the wrong saturation")

    # CW2: direct + spillover summed into a 'total impact' figure.
    out["CW2_direct_plus_spillover"] = dict(
        value=direct + spill,
        identity_lhs=(direct + spill) - spill, identity_rhs=direct,
        note="components are individually correct; the composition is not the policy contrast")

    # CW3: demand-weighted treated mean minus demand-weighted control mean, with treated and control
    # order counts reconciling exactly to the platform total.
    t_all, c_all = dem * A, dem * (~A)
    out["CW3_reconciled_naive"] = dict(
        value=_wmean(Y, t_all) - _wmean(Y, c_all),
        identity_lhs=float(t_all.sum() + c_all.sum()), identity_rhs=float(dem.sum()),
        note="treated + control orders reconcile to the platform total exactly")
    return out, dict(direct=direct, spillover=spill, total50=total50, y0=y0)


CHEAP = {}


def cheap(name):
    def deco(f):
        CHEAP[name] = f
        return f
    return deco


@cheap("C5_constant_launch")
def _c5(w, t):
    return 1.0


@cheap("C6_constant_hold")
def _c6(w, t):
    return -1.0


@cheap("C4_published_dashboard")
def _c4(w, t):
    """The number on the experiment dashboard: pooled treated-vs-control lift."""
    return est_f1(w)["W1_naive_ab"]


@cheap("C7_largest_markets_only")
def _c7(w, t):
    dem, pi = w["dem"], w["pi"]
    d_b = dem.sum(axis=1)
    big = d_b >= np.quantile(d_b, 0.75)
    y_b = np.divide((w["Y"] * dem).sum(axis=1), d_b, out=np.zeros_like(d_b), where=d_b > 0)
    a, b = big & (pi == 1.0), big & (pi == 0.0)
    return _wmean(y_b[a], d_b[a]) - _wmean(y_b[b], d_b[b])


@cheap("C10_one_saturation_level")
def _c10(w, t):
    """Only the 25% arm exists in this analysis: direct effect there, called the policy effect."""
    dem, pi, A, Y = w["dem"], w["pi"], w["assigned"], w["Y"]
    m = pi == 0.25
    return _wmean(Y[m], dem[m] * A[m]) - _wmean(Y[m], dem[m] * (~A[m]))


@cheap("C17_market_size_correlate")
def _c17(w, t):
    """Does market size alone predict the decision?  Correlate block size with block outcome."""
    dem = w["dem"]
    d_b = dem.sum(axis=1)
    y_b = np.divide((w["Y"] * dem).sum(axis=1), d_b, out=np.zeros_like(d_b), where=d_b > 0)
    return float(np.corrcoef(np.log(d_b + 1), y_b)[0, 1])


@cheap("C3_treatshare_outcome_corr")
def _c3(w, t):
    """Correlation between assigned saturation and block outcome, rescaled as if it were an effect."""
    dem, pi = w["dem"], w["pi"]
    d_b = dem.sum(axis=1)
    y_b = np.divide((w["Y"] * dem).sum(axis=1), d_b, out=np.zeros_like(d_b), where=d_b > 0)
    b = np.polyfit(pi, y_b, 1)[0]
    return float(b)


@cheap("C16_treatment_counts")
def _c16(w, t):
    return float(w["assigned"].sum() / max(w["assigned"].size, 1))


def main():
    print("=" * 100)
    print("COHERENT-BUT-WRONG GATE  (G34 lesson: internal consistency is not validation)")
    print("=" * 100)
    for sp in REGIMES:
        t = truth_f1(sp, n_mc=20)
        w = world_f1(sp)
        cw, parts = coherent_wrong(w, t)
        print("\n%-24s tau_policy=%.4f  gate=%.3f  truth=%s" % (
            sp.name, t["tau_policy"], sp.gate, t["decision"]))
        print("   measured components: direct(50%%)=%.4f  spillover(50%%)=%.4f  total(50%%)=%.4f"
              % (parts["direct"], parts["spillover"], parts["total50"]))
        for k, v in cw.items():
            d = "launch" if v["value"] >= sp.gate else "hold"
            ok = abs(v["identity_lhs"] - v["identity_rhs"]) < 1e-6 * max(1.0, abs(v["identity_rhs"]))
            print("   %-28s value=%+.4f err=%+.4f decision=%-7s identity_holds=%s"
                  % (k, v["value"], v["value"] - t["tau_policy"], d + ("*" if d != t["decision"] else ""),
                     "YES" if ok else "no"))
    print("\n   * = wrong decision.  identity_holds=YES means the analysis passes the obvious")
    print("     internal-consistency check a reviewer would run, while still being wrong.")

    print()
    print("=" * 100)
    print("CHEAP-SOLVE PANEL")
    print("=" * 100)
    truths = [truth_f1(sp, n_mc=20) for sp in REGIMES]
    worlds = [world_f1(sp) for sp in REGIMES]
    print("%-30s %s   %s" % ("shortcut", "".join("%12s" % s.name[:11] for s in REGIMES), "decisions"))
    for name, f in CHEAP.items():
        vals, decs = [], ""
        for sp, t, w in zip(REGIMES, truths, worlds):
            v = f(w, t)
            vals.append(v)
            d = "launch" if v >= sp.gate else "hold"
            decs += "L" if d == "launch" else "h"
        right = sum(1 for sp, t, v in zip(REGIMES, truths, vals)
                    if (("launch" if v >= sp.gate else "hold") == t["decision"]))
        print("%-30s %s   %s  %d/4 decisions" % (
            name, "".join("%12.4f" % v for v in vals), decs, right))
    print("\n   truth decisions: %s" % "".join("L" if t["decision"] == "launch" else "h" for t in truths))
    print("   A shortcut is dangerous only if it reaches 4/4 AND lands inside a plausible tolerance")
    print("   on the graded effect sizes; decisions alone are 1 of several graded facts.")


if __name__ == "__main__":
    main()
