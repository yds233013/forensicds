import numpy as np, sys

T = 96
WAVES = [(28, 40, 0.080), (38, 60, 0.065), (48, 80, 0.050), (58, 100, 0.040), (70, 116, 0.030)]

def gen(seed, reg_season_amp=0.0, kappa=0.05):
    rng = np.random.default_rng(seed)
    # regions: build store list with R4 composition from design
    stores = []  # (wave_idx or -1, region)
    r4_counts = {0: 2, 1: 3, 2: 52, 3: 15, 4: 18, -1: 5}
    sizes = {0: 40, 1: 60, 2: 80, 3: 100, 4: 116, -1: 24}
    other = [0, 1, 2, 4, 5]
    for w, n in sizes.items():
        for i in range(n):
            if i < r4_counts[w]:
                stores.append((w, 3))
            else:
                stores.append((w, other[rng.integers(5)]))
    S = len(stores)
    wave = np.array([s[0] for s in stores]); region = np.array([s[1] for s in stores])
    planned = np.array([WAVES[w][0] if w >= 0 else 10**6 for w in wave])
    slip = np.where((wave >= 0) & (rng.random(S) < 0.15), rng.integers(1, 5, S), 0)
    actual = planned + slip
    A = np.array([WAVES[w][2] if w >= 0 else 0 for w in wave])
    m = np.exp(rng.normal(0, 0.25, S))
    t = np.arange(1, T + 1)
    e = t[None, :] - actual[:, None]
    tau = np.where(e >= 0, A[:, None] * m[:, None] * (1 - np.exp(-(e + 1) / 16)), 0.0)
    # install dip weeks
    u = rng.random(S)
    dip = np.zeros((S, T)); noncomp = np.zeros((S, T), bool)
    for s in range(S):
        if wave[s] < 0: continue
        g = actual[s]
        weeks = [g - 1] if u[s] < 0.7 else ([g - 2] if u[s] < 0.9 else [g - 1, g - 2])
        for wk in weeks:
            dip[s, wk - 1] = -rng.uniform(0.04, 0.07); noncomp[s, wk - 1] = True
    other_cl = rng.random((S, T)) < 0.05
    pert = np.where(other_cl, rng.normal(-0.02, 0.02, (S, T)), 0)
    noncomp |= other_cl
    # competitor exposure
    overlap = np.zeros(S); tclose = np.full(S, 10**6)
    r4 = np.where(region == 3)[0]
    for s in r4:
        if wave[s] == 2:
            if rng.random() < 50 / 52: overlap[s] = np.clip(rng.normal(0.66, 0.15), 0.1, 1); tclose[s] = 48
        elif wave[s] in (3, 4, -1):
            if rng.random() < 12 / 38: overlap[s] = np.clip(rng.normal(0.60, 0.15), 0.1, 1); tclose[s] = 48
    for reg, tc in ((1, 22), (5, 66)):
        idx = np.where(region == reg)[0]
        for s in idx:
            if rng.random() < 0.3: overlap[s] = rng.uniform(0.2, 1.0); tclose[s] = tc
    ramp = np.clip((t[None, :] - tclose[:, None] + 1) / 3, 0, 1)
    comp = kappa * overlap[:, None] * ramp
    alpha = rng.normal(0, 0.1, S)
    delta = 0.03 * np.sin(2 * np.pi * t / 52) + 0.0003 * t
    phase = rng.uniform(0, 2 * np.pi, 6)
    rs = reg_season_amp * np.sin(2 * np.pi * t[None, :] / 52 + phase[region][:, None])
    eps = np.zeros((S, T)); sd = 0.028; phi = 0.5
    eps[:, 0] = rng.normal(0, sd, S)
    for k in range(1, T):
        eps[:, k] = phi * eps[:, k - 1] + rng.normal(0, sd * np.sqrt(1 - phi**2), S)
    y = alpha[:, None] + delta[None, :] + rs + tau + dip + pert + comp + eps
    return dict(S=S, wave=wave, region=region, planned=planned, actual=actual, tau=tau, noncomp=noncomp,
                y=y, overlap=overlap, tclose=tclose, ramp=ramp)

def fe_fit(y, g1, g2, X, n1, n2, iters=300):
    """y = a[g1] + b[g2] + X beta ; alternating projections."""
    a = np.zeros(n1); b = np.zeros(n2); beta = np.zeros(X.shape[1]) if X is not None else None
    c1 = np.bincount(g1, minlength=n1); c2 = np.bincount(g2, minlength=n2)
    for _ in range(iters):
        xb = X @ beta if X is not None else 0
        r = y - b[g2] - xb
        a = np.bincount(g1, r, n1) / np.maximum(c1, 1)
        r = y - a[g1] - xb
        b = np.bincount(g2, r, n2) / np.maximum(c2, 1)
        if X is not None:
            r = y - a[g1] - b[g2]
            beta = np.linalg.lstsq(X, r, rcond=None)[0]
    return a, b, beta

def estimators(d):
    S = d['S']; y = d['y']; T_ = T
    sid = np.repeat(np.arange(S), T_); tt = np.tile(np.arange(T_), S)
    Y = y.ravel(); out = {}
    # house static TWFE, planned timing, all weeks
    D = (tt[None, :] + 1 >= d['planned'][sid]).astype(float).ravel()
    def demean(v):
        v = v.copy()
        for _ in range(200):
            v -= (np.bincount(sid, v, S) / T_)[sid]
            v -= (np.bincount(tt, v, T_) / S)[tt]
        return v
    Dt = demean(D); Yt = demean(Y)
    out['twfe_static'] = (Dt @ Yt) / (Dt @ Dt)
    # truth
    e_act = (tt + 1) - d['actual'][sid]
    comp_ok = ~d['noncomp'].ravel()
    wave_s = d['wave'][sid]
    tgt = (e_act >= 0) & (e_act <= 25) & comp_ok & (wave_s >= 0)
    truth = {w: d['tau'].ravel()[tgt & (wave_s == w)].mean() for w in range(5)}
    truth['all'] = d['tau'].ravel()[tgt].mean()
    out['truth'] = truth
    # CS g-1 house panel (planned timing, all weeks)
    cs = {}; num = 0; den = 0
    for w in range(5):
        g = WAVES[w][0]; tr = np.where(d['wave'] == w)[0]
        vals = []
        for k in range(26):
            tk = g + k
            if tk > T_: break
            ctrl = np.where(d['planned'] > tk)[0]
            att = (y[tr, tk - 1] - y[tr, g - 2]).mean() - (y[ctrl, tk - 1] - y[ctrl, g - 2]).mean()
            vals.append(att)
        cs[w] = np.mean(vals); num += np.sum(vals) * len(tr); den += len(vals) * len(tr)
    cs['all'] = num / den; out['cs_gm1_house'] = cs
    # imputation variants on correct panel
    untreated = ((e_act < 0) | (wave_s < 0)) & comp_ok
    region_s = d['region'][sid]
    xexp = (d['overlap'][:, None] * d['ramp']).ravel()
    xstep = (d['overlap'][:, None] * (np.arange(1, T_ + 1)[None, :] >= d['tclose'][:, None])).ravel()
    def impute(g2, n2, X):
        idx = untreated
        a, b, beta = fe_fit(Y[idx], sid[idx], g2[idx], X[idx] if X is not None else None, S, n2)
        pred = a[sid] + b[g2] + (X @ beta if X is not None else 0)
        te = Y - pred
        res = {w: te[tgt & (wave_s == w)].mean() for w in range(5)}
        res['all'] = te[tgt].mean(); return res
    out['imp_noconf'] = impute(tt, T_, None)
    out['imp_exposure_ramp'] = impute(tt, T_, xexp[:, None])
    out['imp_exposure_step'] = impute(tt, T_, xstep[:, None])
    rw = region_s * T_ + tt
    out['imp_regionweek'] = impute(rw, 6 * T_, None)
    out['imp_regionweek_exposure'] = impute(rw, 6 * T_, xexp[:, None])
    return out

if __name__ == '__main__':
    amp = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    nseed = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    keys = ['twfe_static', 'cs_gm1_house', 'imp_noconf', 'imp_exposure_ramp', 'imp_exposure_step', 'imp_regionweek', 'imp_regionweek_exposure']
    errs = {k: [] for k in keys}; tw = []; truths = []
    for seed in range(nseed):
        o = estimators(gen(seed, reg_season_amp=amp))
        tr = o['truth']; truths.append(tr['all'])
        tw.append(o['twfe_static'])
        for k in keys[1:]:
            errs[k].append([o[k][w] - tr[w] for w in [0, 1, 2, 3, 4, 'all']])
    print(f'region-season amp={amp}  truth overall mean={np.mean(truths):.4f}')
    print(f'static TWFE (house) mean={np.mean(tw):+.4f} sd={np.std(tw):.4f}')
    print('error vs truth: mean (sd) for W1..W5, overall')
    for k in keys[1:]:
        a = np.array(errs[k])
        print(f'{k:26s}', ' '.join(f'{m:+.4f}({s:.4f})' for m, s in zip(a.mean(0), a.std(0))))
