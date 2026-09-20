"""G34 pre-check: does each candidate survival core materially move a business estimand?
Minimal DGP, run BEFORE committing to a design (the G33 lesson).

Fix applied after the first run: a unit whose latent failure or preventive replacement would
have occurred BEFORE monitoring begins was never in the fleet at monitoring start. Keeping such
rows produces impossible records (exit < entry) and corrupts every risk set.
"""
import numpy as np, collections

A, B = 18.0, 30.0            # decision window: extend overhaul interval from 18 to 30 months


def km(entry, exit_, ev, a=A, b=B):
    """Left-truncated Kaplan-Meier for cause 1; returns 1 - S(b)/S(a)."""
    m = (ev == 1) & (exit_ > a) & (exit_ <= b)
    if not m.any():
        return 0.0
    t = np.unique(exit_[m])
    d = np.array([np.count_nonzero((exit_ == x) & (ev == 1)) for x in t])
    n_at = np.array([np.count_nonzero((entry < x) & (exit_ >= x)) for x in t])
    return 1 - float(np.prod(1 - d / np.maximum(n_at, 1)))


def world(seed, n=9000, cbm_frac=0.0, pm_age=18.0, mon_start=36.0, study_len=24.0,
          shape=2.3, scale=34.0):
    rng = np.random.default_rng(seed)
    comm = rng.uniform(0, mon_start + study_len, n)
    frail = rng.lognormal(0, 0.45, n)
    Tf = scale * rng.weibull(shape, n) / frail ** (1 / shape)
    Tpm = pm_age + rng.exponential(3.0, n)
    if cbm_frac > 0:                       # condition-based: a fraction of impending failures pre-empted
        pre = rng.random(n) < cbm_frac
        Tpm = np.where(pre, np.maximum(2.0, Tf - rng.exponential(2.5, n)), Tpm)
    entry = np.maximum(0.0, mon_start - comm)
    Tadmin = (mon_start + study_len) - comm
    # a unit is in the observed fleet only if it was still in service when monitoring began
    in_fleet = (Tf > entry) & (Tpm > entry) & (Tadmin > entry)
    exit_ = np.minimum(np.minimum(Tf, Tpm), Tadmin)
    cause = np.where((Tf <= Tpm) & (Tf <= Tadmin), 1, np.where(Tpm <= Tadmin, 2, 0))
    return dict(comm=comm, Tf=Tf, Tpm=Tpm, entry=entry, exit=exit_, cause=cause,
                fleet=in_fleet, mon_start=mon_start)


def truth(w):
    """NET probability of unplanned failure in (18,30] given failure-free at 18."""
    return float(np.mean(w["Tf"][w["Tf"] > A] <= B))


def methods(w):
    m = w["fleet"]
    entry, exit_, ev, comm = w["entry"][m], w["exit"][m], w["cause"][m], w["comm"][m]
    o = {}
    o["V1_km_lefttrunc"] = km(entry, exit_, ev)
    o["W1_no_truncation"] = km(np.zeros_like(entry), exit_, ev)
    dur = exit_ - entry
    o["W2_monitoring_clock"] = km(np.zeros_like(dur), dur, ev)
    pt = np.clip(np.minimum(exit_, B) - np.maximum(entry, A), 0, None).sum()
    nf = np.count_nonzero((ev == 1) & (exit_ > A) & (exit_ <= B))
    o["W3_naive_rate"] = 1 - float(np.exp(-(nf / max(pt, 1e-9)) * (B - A)))
    mat = comm >= w["mon_start"]
    o["W4_mature_only"] = km(entry[mat], exit_[mat], ev[mat]) if mat.sum() > 50 else float("nan")
    o["W5_pm_as_event"] = km(entry, exit_, np.where(ev == 2, 1, ev))
    keep = ev == 1
    o["W6_drop_censored"] = float(np.mean((exit_[keep] > A) & (exit_[keep] <= B))) if keep.any() else float("nan")
    inw = (exit_ > A)
    o["W7_raw_event_fraction"] = float(np.mean((ev[inw] == 1) & (exit_[inw] <= B))) if inw.any() else float("nan")
    return o


if __name__ == "__main__":
    for cbm, tag in ((0.0, "age-based PM (independent of condition)"),
                     (0.5, "condition-based PM (half of failures pre-empted)")):
        rows, ts = collections.defaultdict(list), []
        for s in range(20):
            w = world(s, cbm_frac=cbm)
            ts.append(truth(w))
            for k, v in methods(w).items():
                rows[k].append(v)
        t = float(np.mean(ts))
        print(f"--- {tag}:  truth = {t:.4f}   (fleet n ~ {int(np.mean([world(s,cbm_frac=cbm)['fleet'].sum() for s in range(3)]))})")
        for k, v in rows.items():
            v = np.array(v, float)
            print(f"      {k:24} mean={np.nanmean(v):.4f}  rel.err={(np.nanmean(v)-t)/t:+.3f}  sd={np.nanstd(v):.4f}")
        print()
