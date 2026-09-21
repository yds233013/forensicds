"""G37 deep-round prototypes C2, C7, C9 (compact). Same pre-registered window definitions as analyze_c1.py:
VALID_BOUND = max p99(|err|/SE_REF) over valid methods and fixtures; detect = p01(|err|/SE_REF);
WRONG_BOUND(m) = second-best fixture; ratio >= 3 required. SE_REF = RMSE of the first valid method.

    python research/g37/sim/proto_others.py [draws]
"""
from __future__ import annotations

import json, math, sys
from pathlib import Path

import numpy as np


def deming(sxx, syy, sxy, delta):
    t = syy - delta * sxx
    return (t + math.sqrt(t * t + 4 * delta * sxy * sxy)) / (2 * sxy)


# =============================================================================== C2 assay method transfer
# latent lot potency X (%LC); old HPLC O = X + e (dup), new UPLC N = 100 + c + b(X-100) + e (dup)
# bridge: 40 retained lots in duplicate on both; production: 60 lots/yr pre (old dup mean), 60 post (new dup mean)
C2_FIX = {
    "visible":  dict(seed=1, mu_pre=100.0, s_pre=1.0, mu_post=100.3, s_post=1.0, c=+0.8, b=1.04, so=1.2, sn=1.5),
    "hidden_a": dict(seed=2, mu_pre=100.0, s_pre=1.0, mu_post=101.2, s_post=1.4, c=-0.5, b=0.97, so=1.0, sn=0.8),
    "hidden_b": dict(seed=3, mu_pre=99.8, s_pre=0.9, mu_post=99.8, s_post=0.9, c=+1.2, b=1.06, so=1.2, sn=1.8),
}
C2_N = dict(bridge=40, lots=60)


def c2_draw(f, rng):
    xb = f["mu_pre"] + rng.standard_normal(C2_N["bridge"]) * f["s_pre"]
    Ob = xb[:, None] + rng.standard_normal((len(xb), 2)) * f["so"]
    Nb = (100 + f["c"] + f["b"] * (xb - 100))[:, None] + rng.standard_normal((len(xb), 2)) * f["sn"]
    xp = f["mu_post"] + rng.standard_normal(C2_N["lots"]) * f["s_post"]
    Np = (100 + f["c"] + f["b"] * (xp - 100))[:, None] + rng.standard_normal((len(xp), 2)) * f["sn"]
    T = xp.std()                                   # finite population of released lots
    mu = xp.mean()
    return dict(Ob=Ob, Nb=Nb, Np=Np.mean(axis=1)), {"sd": T, "ppk": min(105 - mu, mu - 95) / (3 * T), "mu": mu}


def _c2_parts(D):
    so2 = np.mean(np.var(D["Ob"], axis=1, ddof=1)); sn2 = np.mean(np.var(D["Nb"], axis=1, ddof=1))
    o, n = D["Ob"].mean(1), D["Nb"].mean(1)
    return so2, sn2, o, n, np.var(o, ddof=1), np.var(n, ddof=1), np.cov(o, n)[0, 1]


def _c2_out(D, a, b, sn2, div=2):
    mu = (D["Np"].mean() - a) / b
    sd = math.sqrt(max((np.var(D["Np"], ddof=1) - sn2 / div) / b ** 2, 1e-9))
    return {"sd": sd, "ppk": min(105 - mu, mu - 95) / (3 * sd), "mu": mu}


def c2_methods():
    def dem(D):
        so2, sn2, o, n, sxx, syy, sxy = _c2_parts(D); b = deming(sxx, syy, sxy, sn2 / so2); return _c2_out(D, n.mean() - b * o.mean(), b, sn2)
    def mom(D):
        so2, sn2, o, n, sxx, syy, sxy = _c2_parts(D); b = sxy / (sxx - so2 / 2); return _c2_out(D, n.mean() - b * o.mean(), b, sn2)
    def rawm(D):
        mu, sd = D["Np"].mean(), np.std(D["Np"], ddof=1); return {"sd": sd, "ppk": min(105 - mu, mu - 95) / (3 * sd), "mu": mu}
    def nodeconv(D):
        so2, sn2, o, n, sxx, syy, sxy = _c2_parts(D); b = deming(sxx, syy, sxy, sn2 / so2); return _c2_out(D, n.mean() - b * o.mean(), b, 0.0)
    def ols(D):
        so2, sn2, o, n, sxx, syy, sxy = _c2_parts(D); b = sxy / sxx; return _c2_out(D, n.mean() - b * o.mean(), b, sn2)
    def perrep(D):
        so2, sn2, o, n, sxx, syy, sxy = _c2_parts(D); b = deming(sxx, syy, sxy, sn2 / so2); return _c2_out(D, n.mean() - b * o.mean(), b, sn2, div=1)
    def wrongscale(D):
        so2, sn2, o, n, sxx, syy, sxy = _c2_parts(D); b = deming(sxx, syy, sxy, sn2 / so2)
        mu = (D["Np"].mean() - (n.mean() - b * o.mean())) / b; sd = math.sqrt(max(np.var(D["Np"], ddof=1) / b ** 2 - sn2 / 2, 1e-9))
        return {"sd": sd, "ppk": min(105 - mu, mu - 95) / (3 * sd), "mu": mu}
    def offset_only(D):
        so2, sn2, o, n, *_ = _c2_parts(D); return _c2_out(D, n.mean() - o.mean(), 1.0, sn2)
    return {"V_deming": ("valid", dem), "V_moments": ("valid", mom), "W_raw": ("wrong", rawm),
            "W_no_deconvolution": ("wrong", nodeconv), "W_ols": ("wrong", ols), "W_per_replicate_divisor": ("wrong", perrep),
            "X_wrong_scale_deconv": ("wrong", wrongscale), "W_offset_only": ("wrong", offset_only)}


# =============================================================================== C7 inspection-model migration
# latent defect prevalence p; camera: sens/spec; audit of A units: camera + expert gold on all camera positives and a
# 10 % random sample of camera negatives (verification bias). Production: P units camera-inspected.
C7_FIX = {
    "visible":  dict(seed=7, p=0.0035, se=0.93, sp=0.9960),
    "hidden_a": dict(seed=8, p=0.0075, se=0.88, sp=0.9985),
    "hidden_b": dict(seed=9, p=0.0030, se=0.95, sp=0.9940),
}
C7_N = dict(audit=8000, prod=250000, verify_neg=0.10)


def c7_draw(f, rng):
    A, P = C7_N["audit"], C7_N["prod"]
    y = rng.random(A) < f["p"]
    cam = np.where(y, rng.random(A) < f["se"], rng.random(A) > f["sp"])
    ver = cam | (rng.random(A) < C7_N["verify_neg"])
    yp = rng.random(P) < f["p"]
    camp = np.where(yp, rng.random(P) < f["se"], rng.random(P) > f["sp"])
    return dict(y=y, cam=cam, ver=ver, qprod=camp.mean()), {"p": yp.mean()}


def c7_methods():
    w = 1 / C7_N["verify_neg"]
    def rg(D, weighted=True):
        y, cam, ver = D["y"], D["cam"], D["ver"]
        wt = np.where(cam, 1.0, w if weighted else 1.0) * ver
        se = (wt * (y & cam)).sum() / max((wt * y).sum(), 1e-9)
        sp = (wt * (~y & ~cam)).sum() / max((wt * ~y).sum(), 1e-9)
        return {"p": (D["qprod"] - (1 - sp)) / (se + sp - 1)}
    def ppv(D):   # PPV from audit applied to production positives (verification-weighted NPV too)
        y, cam, ver = D["y"], D["cam"], D["ver"]
        ppv = (y & cam).sum() / cam.sum(); fom = (y & ~cam & ver).sum() / max((~cam & ver).sum(), 1)
        return {"p": D["qprod"] * ppv + (1 - D["qprod"]) * fom}
    return {"V_rogan_gladen_weighted": ("valid", lambda D: rg(D, True)), "V_ppv_npv": ("valid", ppv),
            "W_raw_rate": ("wrong", lambda D: {"p": D["qprod"]}),
            "W_rogan_gladen_unweighted_verification_bias": ("wrong", lambda D: rg(D, False)),
            "W_ppv_only_ignore_missed": ("wrong", lambda D: {"p": D["qprod"] * (D["y"] & D["cam"]).sum() / D["cam"].sum()})}


# =============================================================================== C9 CD-SEM fleet matching
# wafers randomly dispatched to 4 tools; wafer-mean CD Y = X + d_tool + e (tool repeatability s_t);
# golden wafer: 10 measurements per tool (commutable here). Target: latent wafer-to-wafer SD of X.
C9_FIX = {
    "visible":  dict(seed=21, sw=1.00, d=(0.0, 0.6, -0.4, 1.1), s=(0.35, 0.35, 0.40, 0.70)),
    "hidden_a": dict(seed=22, sw=1.45, d=(0.0, -0.8, 0.3, 0.9), s=(0.30, 0.45, 0.35, 0.60)),
    "hidden_b": dict(seed=23, sw=0.85, d=(0.0, 0.5, 0.5, -1.0), s=(0.40, 0.40, 0.30, 0.90)),
}
C9_N = dict(wafers=600, golden=10)


def c9_draw(f, rng):
    W = C9_N["wafers"]; x = 45.0 + rng.standard_normal(W) * f["sw"]; t = rng.integers(0, 4, W)
    d, s = np.array(f["d"]), np.array(f["s"])
    y = x + d[t] + rng.standard_normal(W) * s[t]
    g = 45.0 + d[:, None] + rng.standard_normal((4, C9_N["golden"])) * s[:, None]
    return dict(y=y, t=t, g=g), {"sd": x.std()}


def c9_methods():
    def within_tool(D):   # tool as fixed effect (random dispatch) + repeatability from golden replicates
        y, t, g = D["y"], D["t"], D["g"]
        r = np.concatenate([y[t == k] - y[t == k].mean() for k in range(4)])
        rep = np.array([np.var(g[k], ddof=1) for k in range(4)])
        nk = np.array([(t == k).sum() for k in range(4)])
        return {"sd": math.sqrt(max(np.var(r, ddof=4) - (nk * rep).sum() / nk.sum(), 1e-9))}
    def golden_offsets(D):  # offsets from golden wafer, repeatability from golden
        y, t, g = D["y"], D["t"], D["g"]
        off = g.mean(1) - g.mean(1)[0]; rep = np.array([np.var(g[k], ddof=1) for k in range(4)])
        z = y - off[t]; return {"sd": math.sqrt(max(np.var(z, ddof=1) - rep[t].mean(), 1e-9))}
    def raw(D): return {"sd": float(np.std(D["y"], ddof=1))}
    def offsets_no_deconv(D):
        y, t = D["y"], D["t"]; r = np.concatenate([y[t == k] - y[t == k].mean() for k in range(4)]); return {"sd": float(np.std(r, ddof=4))}
    def deconv_no_offsets(D):
        g = D["g"]; rep = np.array([np.var(g[k], ddof=1) for k in range(4)])
        return {"sd": math.sqrt(max(np.var(D["y"], ddof=1) - rep[D["t"]].mean(), 1e-9))}
    def ref_tool_only(D):
        y, t, g = D["y"], D["t"], D["g"]; return {"sd": math.sqrt(max(np.var(y[t == 0], ddof=1) - np.var(g[0], ddof=1), 1e-9))}
    def pooled_rep(D):     # one pooled repeatability for all tools
        y, t, g = D["y"], D["t"], D["g"]
        r = np.concatenate([y[t == k] - y[t == k].mean() for k in range(4)])
        return {"sd": math.sqrt(max(np.var(r, ddof=4) - np.mean([np.var(g[k], ddof=1) for k in range(4)]), 1e-9))}
    return {"V_within_tool_anova": ("valid", within_tool), "V_golden_offsets": ("valid", golden_offsets),
            "W_raw_pooled": ("wrong", raw), "W_offsets_no_deconvolution": ("wrong", offsets_no_deconv),
            "W_deconvolution_no_offsets": ("wrong", deconv_no_offsets), "V_reference_tool_only": ("valid", ref_tool_only),
            "X_pooled_repeatability_unweighted": ("wrong", pooled_rep)}


# =============================================================================== runner
def evaluate(name, fixtures, drawfn, methods, quants, draws):
    res = {}
    for fx, f in fixtures.items():
        rng = np.random.default_rng(f["seed"]); errs = {m: {q: [] for q in quants} for m in methods}
        for _ in range(draws):
            D, T = drawfn(f, rng)
            for m, (_, fn) in methods.items():
                r = fn(D)
                for q in quants:
                    errs[m][q].append(r[q] - T[q])
        first_valid = next(m for m, (k, _) in methods.items() if k == "valid")
        se = {q: float(np.sqrt(np.mean(np.square(errs[first_valid][q])))) for q in quants}
        res[fx] = {"se": se, "m": {m: {"p99": max(float(np.percentile(np.abs(errs[m][q]) / se[q], 99)) for q in quants),
                                       "p01": max(float(np.percentile(np.abs(errs[m][q]) / se[q], 1)) for q in quants),
                                       "bias": {q: float(np.mean(errs[m][q]) / se[q]) for q in quants}}
                                   for m in methods}}
    VB = max(res[fx]["m"][m]["p99"] for fx in res for m, (k, _) in methods.items() if k == "valid")
    wb = {m: sorted((res[fx]["m"][m]["p01"] for fx in res), reverse=True)[1] for m, (k, _) in methods.items() if k != "valid"}
    WBm = min(wb, key=wb.get)
    print("\n== %s ==  SE_REF %s" % (name, {fx: {q: round(v, 5) for q, v in res[fx]["se"].items()} for fx in res}))
    print("  VALID_BOUND %.2f   WRONG_BOUND %.2f (%s)   ratio %.2f" % (VB, wb[WBm], WBm, wb[WBm] / VB))
    for m in sorted(wb, key=wb.get):
        print("   %-45s WB %6.2f  per-fixture p01 %s  bias %s" % (m, wb[m], " ".join("%.1f" % res[fx]["m"][m]["p01"] for fx in res),
              " ".join("%+.1f" % list(res[fx]["m"][m]["bias"].values())[-1] for fx in res)))
    return {"VALID_BOUND": VB, "WRONG_BOUND": wb[WBm], "hardest": WBm, "ratio": wb[WBm] / VB, "detail": res, "wb": wb}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    out = {"C2": evaluate("C2 assay transfer", C2_FIX, c2_draw, c2_methods(), ("sd", "ppk", "mu"), n),
           "C7": evaluate("C7 inspection migration", C7_FIX, c7_draw, c7_methods(), ("p",), n),
           "C9": evaluate("C9 CD-SEM fleet", C9_FIX, c9_draw, c9_methods(), ("sd",), n)}
    Path(__file__).with_name("proto_results.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
