"""G39 search — minimal structural-separation simulations for the top-12 concepts (RESEARCH ONLY).

PRE-REGISTERED (written before any run):
  * Every graded quantity is a deterministic functional of the visible evidence. Truth = valid route V1.
  * Error unit: |est - truth| / scale(q), where scale is |truth| unless a natural denominator is declared
    (A2 shortfall: total demand; C3 LFL change: LY conversion level). No pseudo-sampling uncertainty.
  * TOL = 0.5 % of scale: reporting precision (3 significant figures) and legitimate rounding conventions
    (integer cores, minutes vs hours) — justified per concept in separation.md.
  * VALID_BOUND = max(TOL, p99 of valid-route disagreement).
  * detect(m, regime) = p05 over worlds of the error (the error a method shows in >= 95 % of worlds).
  * WRONG_BOUND(m) = the second-largest detect over regimes (>= 2 regimes);  WRONG_BOUND = min over wrong methods.
  * ratio = WRONG_BOUND / VALID_BOUND; pass >= 3, prefer >= 5, strong >= 10.
  * coincidence rate = share of worlds where a wrong method lands within TOL (counterexample indicator).
Wrong objects are labelled before scoring; a method found to be algebraically valid is RE-LABELLED and disclosed.

    python research/g39_search/sim/g39_sims.py [worlds_per_regime]
"""
from __future__ import annotations

import itertools, json, math, sys
from collections import deque
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

TOL = 0.005
U = lambda rng, a, b, n=None: rng.uniform(a, b, n)


# =================================================================================== A1 take-or-pay allocation
def a1_gen(rng, r):
    K = 5; p = U(rng, 8, 14, K); cap = U(rng, 2000, 6000, K); y = U(rng, .85, .99, K)
    m = np.zeros(K); m[:3] = U(rng, .3, .8, 3) * cap[:3]
    if r == "yield_trap":
        k = int(np.argmin(p)); p[k] = 7.5; y[k] = 0.72
    G0, Gu = (y * m).sum(), (y * cap).sum()
    D = {"above": G0 + .4 * (Gu - G0), "below": .7 * G0, "tight": G0 + .95 * (Gu - G0),
         "yield_trap": G0 + .5 * (Gu - G0), "mixed": U(rng, .6 * G0, G0 + .9 * (Gu - G0))}[r]
    return dict(p=p, cap=cap, y=y, m=m, D=D)


def a1_V1(W):
    p, cap, y, m, D = W["p"], W["cap"], W["y"], W["m"], W["D"]; K = len(p)
    c = np.r_[np.zeros(K), p]
    A = np.vstack([np.hstack([np.eye(K), -np.eye(K)]), np.r_[-y, np.zeros(K)][None, :]])
    b = np.r_[np.zeros(K), -D]
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, cap[k]) for k in range(K)] + [(m[k], None) for k in range(K)], method="highs")
    return {"cost": res.fun}


def _a1_greedy(W, rank="py", yield_cap=True, commit_good=False, ignore_yield=False, ignore_cap=False):
    p, cap, m, D = W["p"], W["cap"], W["m"], W["D"]; y = np.ones_like(p) if ignore_yield else W["y"]
    base = (p * m).sum(); free = m.sum() if commit_good else (y * m).sum()
    if D <= free:
        return base
    R = D - free; key = p / y if rank == "py" else p; cost = base
    for k in np.argsort(key):
        avail = np.inf if ignore_cap else ((cap[k] - m[k]) * (y[k] if yield_cap else 1.0))
        take = min(R, avail); cost += take * p[k] / y[k]; R -= take
        if R <= 1e-9:
            break
    return cost


A1 = dict(gen=a1_gen, regimes=["above", "below", "tight", "yield_trap", "mixed"], q=("cost",),
          valid={"V1_lp_epigraph": a1_V1, "V2_sunk_then_merit_order": lambda W: {"cost": _a1_greedy(W)}},
          relabel_valid={},
          wrong={
              "W01_lp_ignore_commitments": lambda W: {"cost": _a1_lp_plain(W)[0]},
              "W02_optimise_then_pay_minimums": lambda W: {"cost": float((W["p"] * np.maximum(_a1_lp_plain(W)[1], W["m"])).sum())},
              "W03_force_x_ge_m": lambda W: {"cost": _a1_lp_force(W)},
              "W04_rank_by_price_not_price_per_good": lambda W: {"cost": _a1_greedy(W, rank="p")},
              "W05_ignore_yield_entirely": lambda W: {"cost": _a1_greedy(W, ignore_yield=True)},
              "W06_commitments_counted_as_good_units": lambda W: {"cost": _a1_greedy(W, commit_good=True)},
              "W07_dashboard_avg_price_over_avg_yield": lambda W: {"cost": float(W["p"].mean() / W["y"].mean() * W["D"])},
              "W08_proportional_to_usable_capacity": lambda W: {"cost": _a1_prop(W)},
              "W09_cheapest_ignore_capacity": lambda W: {"cost": _a1_greedy(W, ignore_cap=True)},
              "W10_incremental_cost_only": lambda W: {"cost": _a1_greedy(W) - float((W["p"] * W["m"]).sum())},
              "W11_gross_capacity_as_good": lambda W: {"cost": _a1_greedy(W, yield_cap=False)},
              "W12_pay_commitments_and_rebuy": lambda W: {"cost": float((W["p"] * W["m"]).sum()) + _a1_lp_plain(W)[0]},
          })


def _a1_lp_plain(W):
    p, cap, y, D = W["p"], W["cap"], W["y"], W["D"]
    res = linprog(p, A_ub=-y[None, :], b_ub=[-D], bounds=[(0, c) for c in cap], method="highs")
    return res.fun, res.x


def _a1_lp_force(W):
    p, cap, y, m, D = W["p"], W["cap"], W["y"], W["m"], W["D"]
    res = linprog(p, A_ub=-y[None, :], b_ub=[-D], bounds=[(m[k], cap[k]) for k in range(len(p))], method="highs")
    return res.fun


def _a1_prop(W):
    p, cap, y, m, D = W["p"], W["cap"], W["y"], W["m"], W["D"]
    x = cap * D / (y * cap).sum()
    return float((p * np.maximum(x, m)).sum())


# =================================================================================== A2 ATP rebalancing
def a2_gen(rng, r):
    J = 6; oh = U(rng, 50, 400, J)
    al = oh * (U(rng, .4, .7, J) if r == "high_alloc" else U(rng, .1, .5, J))
    d = U(rng, 80, 350, J)
    T = rng.choice([2, 2, 5] if r == "urgent" else [2, 5, 10], J)
    inb = []
    for j in range(J):
        n = rng.integers(0, 3)
        inb.append([(U(rng, 50, 200), (U(rng, 8, 20) if r == "late_inbound" else U(rng, 1, 20))) for _ in range(n)])
    L = rng.integers(3, 8, (J, J)) if r == "urgent" else rng.integers(1, 8, (J, J))
    L = np.triu(L, 1); L = L + L.T
    if r == "surplus_far":
        oh[:2] *= 3; L[:2, 2:] = np.maximum(L[:2, 2:], 5); L[2:, :2] = L[:2, 2:].T
    return dict(oh=oh, al=al, d=d, T=T, inb=inb, L=L)


def _maxflow(cap_s, cap_t, arcs):
    """Edmonds-Karp on source -> donors -> receivers -> sink. arcs: set of (i, j) with infinite capacity."""
    I, J = len(cap_s), len(cap_t); n = 2 + I + J; S, Tn = 0, n - 1
    C = np.zeros((n, n))
    for i in range(I):
        C[S, 1 + i] = cap_s[i]
    for j in range(J):
        C[1 + I + j, Tn] = cap_t[j]
    for i, j in arcs:
        C[1 + i, 1 + I + j] = 1e18
    flow = 0.0
    while True:
        par = [-1] * n; par[S] = S; q = deque([S])
        while q and par[Tn] < 0:
            u = q.popleft()
            for v in range(n):
                if par[v] < 0 and C[u, v] > 1e-12:
                    par[v] = u; q.append(v)
        if par[Tn] < 0:
            return flow
        v, f = Tn, np.inf
        while v != S:
            f = min(f, C[par[v], v]); v = par[v]
        v = Tn
        while v != S:
            C[par[v], v] -= f; C[v, par[v]] += f; v = par[v]
        flow += f


def _a2_parts(W, use_alloc=True, inbound="timely", donor_keep=True, donor_inbound=False, lt=True):
    oh, al, d, T, inb, L = W["oh"], W["al"], W["d"], W["T"], W["inb"], W["L"]; J = len(d)
    free = oh - (al if use_alloc else 0)
    tin = np.array([sum(q for q, e in inb[j] if (inbound == "all" or (inbound == "timely" and e <= T[j]) or (inbound == "14" and e <= 14))) for j in range(J)])
    N = np.maximum(0, d - free - tin)
    own = np.maximum(0, d - tin) if donor_keep else np.zeros(J)
    trans = np.maximum(0, free - own) + (np.array([sum(q for q, e in inb[j]) for j in range(J)]) if donor_inbound else 0)
    arcs = {(i, j) for i in range(J) for j in range(J) if i != j and trans[i] > 0 and N[j] > 0 and (not lt or L[i, j] <= T[j])}
    return N, trans, arcs


def a2_V1(W):
    N, trans, arcs = _a2_parts(W); arcs = sorted(arcs); J = len(N)
    if not arcs:
        return {"shortfall": float(N.sum())}
    c = -np.ones(len(arcs))
    A = []; b = []
    for i in range(J):
        A.append([1.0 if a[0] == i else 0.0 for a in arcs]); b.append(trans[i])
    for j in range(J):
        A.append([1.0 if a[1] == j else 0.0 for a in arcs]); b.append(N[j])
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, None)] * len(arcs), method="highs")
    return {"shortfall": float(N.sum() + res.fun)}


def a2_V2(W):
    N, trans, arcs = _a2_parts(W); return {"shortfall": float(N.sum() - _maxflow(trans, N, arcs))}


def _a2_generic(W, **kw):
    N, trans, arcs = _a2_parts(W, **kw); return {"shortfall": float(N.sum() - _maxflow(trans, N, arcs))}


def _a2_greedy_nearest(W):
    N, trans, arcs = _a2_parts(W); N = N.copy(); trans = trans.copy(); L = W["L"]
    for j in np.argsort(-N):
        for i in sorted([i for i, jj in arcs if jj == j], key=lambda i: L[i, j]):
            t = min(trans[i], N[j]); trans[i] -= t; N[j] -= t
    return {"shortfall": float(N.sum())}


def _a2_pooled(W):
    oh, al, d, T, inb = W["oh"], W["al"], W["d"], W["T"], W["inb"]
    tin = sum(sum(q for q, e in inb[j] if e <= T[j]) for j in range(len(d)))
    return {"shortfall": float(max(0, d.sum() - (oh - al).sum() - tin))}


A2 = dict(gen=a2_gen, regimes=["balanced", "high_alloc", "late_inbound", "urgent", "surplus_far"], q=("shortfall",),
          scale=lambda W, T: float(W["d"].sum()),
          valid={"V1_lp_transport": a2_V1, "V2_edmonds_karp": a2_V2}, relabel_valid={},
          wrong={
              "W01_on_hand_not_atp": lambda W: _a2_generic(W, use_alloc=False),
              "W02_all_inbound_counted": lambda W: _a2_generic(W, inbound="all"),
              "W03_ignore_lead_time": lambda W: _a2_generic(W, lt=False),
              "W04_network_netting": _a2_pooled,
              "W05_no_transfers": lambda W: {"shortfall": float(_a2_parts(W)[0].sum())},
              "W06_donor_keeps_nothing": lambda W: _a2_generic(W, donor_keep=False),
              "W07_allocated_subtracted_twice": lambda W: _a2_generic(dict(W, al=2 * W["al"])),
              "W08_donor_inbound_transferable": lambda W: _a2_generic(W, donor_inbound=True),
              "W09_greedy_nearest_donor": _a2_greedy_nearest,
              "W10_dashboard_raw_on_hand_gap": lambda W: {"shortfall": float(np.maximum(0, W["d"] - W["oh"]).sum())},
              "W11_inbound_14_day_horizon": lambda W: _a2_generic(W, inbound="14"),
          })


# =================================================================================== A3 shared-bottleneck product mix
def a3_gen(rng, r):
    h = np.r_[U(rng, .5, 1.5, 2), U(rng, .5, 1.5)]            # P1, P2 on line A; P3 on line B
    g = U(rng, .3, 1.0, 3); c = U(rng, 20, 80, 3); u = U(rng, 200, 800, 3)
    pm = U(rng, .25, .35, 2) if r == "maint_heavy" else U(rng, .05, .2, 2)
    if r == "margin_trap":
        k = int(np.argmax(c)); g[k] = 1.3
    paint = (U(rng, 1.5, 2.5) if r == "line_binding" else U(rng, .35, .6)) * (g * u).sum()
    if r == "both":
        paint = .6 * (g * u).sum()
    lineA = 720 * (1 - pm[0]) * (.9 if r == "both" else 1.0); lineB = 720 * (1 - pm[1])
    return dict(h=h, g=g, c=c, u=u, lineA=lineA, lineB=lineB, paint=paint, pm=pm)


def _a3_rows(W, paint=True, nominal=False, caps=True):
    h, g, u = W["h"], W["g"], W["u"]; A = []; b = []
    A.append([h[0], h[1], 0]); b.append(720 if nominal else W["lineA"])
    A.append([0, 0, h[2]]); b.append(720 if nominal else W["lineB"])
    if paint:
        A.append(list(g)); b.append(W["paint"])
    if caps:
        for k in range(3):
            row = [0, 0, 0]; row[k] = 1; A.append(row); b.append(u[k])
    return np.array(A, float), np.array(b, float)


def _a3_lp(W, **kw):
    A, b = _a3_rows(W, **kw)
    res = linprog(-W["c"], A_ub=A, b_ub=b, bounds=[(0, None)] * 3, method="highs")
    return float(-res.fun), res.x


def a3_V2(W):
    A, b = _a3_rows(W); A = np.vstack([A, -np.eye(3)]); b = np.r_[b, np.zeros(3)]; best = -np.inf
    for rows in itertools.combinations(range(len(b)), 3):
        M = A[list(rows)]
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        x = np.linalg.solve(M, b[list(rows)])
        if np.all(A @ x <= b + 1e-7):
            best = max(best, float(W["c"] @ x))
    return {"margin": best}


def _a3_greedy(W, key):
    A, b = _a3_rows(W); x = np.zeros(3); rem = b.copy()
    for k in np.argsort(-key):
        col = A[:, k]; lim = min(rem[i] / col[i] for i in range(len(b)) if col[i] > 0)
        x[k] = max(lim, 0); rem -= col * x[k]
    return {"margin": float(W["c"] @ x)}


def _a3_split_paint(W):
    """Each line gets half of the paint shop and optimises locally."""
    h, g, c, u = W["h"], W["g"], W["c"], W["u"]
    ra = linprog(-c[:2], A_ub=[[h[0], h[1]], [g[0], g[1]]], b_ub=[W["lineA"], W["paint"] / 2], bounds=[(0, u[0]), (0, u[1])], method="highs")
    q3 = min(u[2], W["lineB"] / h[2], (W["paint"] / 2) / g[2])
    return {"margin": float(-ra.fun + c[2] * q3)}


def _a3_lines_then_scale(W):
    m, x = _a3_lp(W, paint=False); use = W["g"] @ x; s = min(1.0, W["paint"] / use) if use > 0 else 1
    return {"margin": float(W["c"] @ (x * s))}


A3 = dict(gen=a3_gen, regimes=["paint_binding", "line_binding", "both", "margin_trap", "maint_heavy"], q=("margin",),
          valid={"V1_lp": lambda W: {"margin": _a3_lp(W)[0]}, "V2_vertex_enumeration": a3_V2}, relabel_valid={},
          wrong={
              "W01_ignore_shared_paint": lambda W: {"margin": _a3_lp(W, paint=False)[0]},
              "W02_nominal_calendar_hours": lambda W: {"margin": _a3_lp(W, nominal=True)[0]},
              "W03_greedy_margin_per_unit": lambda W: _a3_greedy(W, W["c"]),
              "W04_greedy_margin_per_line_hour": lambda W: _a3_greedy(W, W["c"] / W["h"]),
              "W05_greedy_margin_per_paint_hour": lambda W: _a3_greedy(W, W["c"] / W["g"]),
              "W06_ignore_demand_caps": lambda W: {"margin": _a3_lp(W, caps=False)[0]},
              "W07_split_paint_equally_by_line": _a3_split_paint,
              "W08_lines_optimal_then_scale_to_paint": _a3_lines_then_scale,
              "W09_nominal_hours_and_no_paint": lambda W: {"margin": _a3_lp(W, paint=False, nominal=True)[0]},
              "W10_demand_caps_as_targets": lambda W: {"margin": float(W["c"] @ W["u"])},
          })


# =================================================================================== A4 cloud commitment purchase
def a4_gen(rng, r):
    H = 720; t = np.arange(H); dem = []; E = []; Eexp = []
    for reg in range(2):
        base = U(rng, 200, 600); amp = U(rng, .1, .5) * base
        prof = base + amp * np.sin(2 * np.pi * (t % 24) / 24) + .15 * base * (((t // 24) % 7) < 5)
        if r == "peaky":
            prof = prof + (rng.random(H) < .03) * U(rng, .5, 1.0) * base
        if r == "growth":
            prof = prof * (1 + .3 * t / H)
        prof = prof * (1 + .05 * rng.standard_normal(H))
        if r == "regional":
            prof = prof * (3.0 if reg == 0 else 0.3)
        dem.append(np.maximum(prof, 0)); e = int(U(rng, .1, .3) * base / 2); E.append(e); Eexp.append(int(e * U(rng, .3, .8)))
    disc = U(rng, .3, .6) if r != "half_discount" else .5
    od = .048; pc = od * (1 - disc)
    return dict(dem=dem, E=E, Eexp=Eexp, od=od, pc=pc, H=H)


def _a4_resid(W, reg, ignore_existing=False, ignore_expiry=False):
    H = W["H"]; E = np.full(H, W["E"][reg], float)
    if not ignore_expiry:
        E[H // 2:] -= W["Eexp"][reg]
    return np.maximum(0, W["dem"][reg] - (0 if ignore_existing else 2 * E))


def _a4_cost(r, Q, W, unit=2):
    return W["H"] * unit * Q * W["pc"] + W["od"] * np.maximum(0, r - unit * Q).sum()


def _a4_marginal(r, W, unit=2, thresh=None):
    Q = 0; th = W["pc"] / W["od"] if thresh is None else thresh
    while True:
        frac = np.mean(np.clip(r - unit * Q, 0, unit)) / unit     # share of the next core used, averaged over hours
        if frac < th:
            return Q
        Q += 1


def _a4_brute(r, W):
    qs = np.arange(0, int(r.max() / 2) + 2)
    return int(qs[np.argmin([_a4_cost(r, q, W) for q in qs])])


def a4_V1(W):
    return {"cores": float(sum(_a4_marginal(_a4_resid(W, g), W) for g in range(2)))}


def a4_V2(W):
    return {"cores": float(sum(_a4_brute(_a4_resid(W, g), W) for g in range(2)))}


A4 = dict(gen=a4_gen, regimes=["diurnal", "peaky", "growth", "regional", "half_discount"], q=("cores",),
          valid={"V1_marginal_core": a4_V1, "V2_brute_force": a4_V2}, relabel_valid={},
          wrong={
              "W01_vcpu_core_confusion": lambda W: {"cores": float(sum(_a4_marginal(_a4_resid(W, g), W, unit=1) for g in range(2)))},
              "W02_pool_regions": lambda W: {"cores": float(_a4_marginal(_a4_resid(W, 0) + _a4_resid(W, 1), W))},
              "W03_mean_usage": lambda W: {"cores": float(sum(round(_a4_resid(W, g).mean() / 2) for g in range(2)))},
              "W04_peak_usage": lambda W: {"cores": float(sum(round(_a4_resid(W, g).max() / 2) for g in range(2)))},
              "W05_daily_average_profile": lambda W: {"cores": float(sum(_a4_marginal(np.repeat(_a4_resid(W, g).reshape(-1, 24).mean(1), 24), W) for g in range(2)))},
              "W06_ignore_existing_commitments": lambda W: {"cores": float(sum(_a4_marginal(_a4_resid(W, g, ignore_existing=True), W) for g in range(2)))},
              "W07_ignore_expiry": lambda W: {"cores": float(sum(_a4_marginal(_a4_resid(W, g, ignore_expiry=True), W) for g in range(2)))},
              "W08_inverted_breakeven": lambda W: {"cores": float(sum(_a4_marginal(_a4_resid(W, g), W, thresh=1 - W["pc"] / W["od"]) for g in range(2)))},
              "W09_median_usage": lambda W: {"cores": float(sum(round(np.median(_a4_resid(W, g)) / 2) for g in range(2)))},
              "W10_floor_minimum_usage": lambda W: {"cores": float(sum(round(_a4_resid(W, g).min() / 2) for g in range(2)))},
              "W11_last_7_days_only": lambda W: {"cores": float(sum(_a4_marginal(_a4_resid(W, g)[-168:], W) for g in range(2)))},
          })


# =================================================================================== B1 fleet OEE
def b1_gen(rng, r):
    P = 8; out = []
    for i in range(P):
        lines = rng.integers(1, 7) if r == "size_skew" else 3
        cal = 720.0 * lines
        planned = U(rng, 40, 400 if r == "maint_skew" else 160) * lines
        unplanned = U(rng, 20, 100) * lines
        ppt = cal - planned; run = ppt - unplanned
        k = int(rng.choice([1, 2, 4])) if r == "multi_cavity" else int(rng.choice([1, 1, 2]))
        nprod = rng.integers(2, 4)
        ict = U(rng, 10, 150, nprod) if r == "mix_skew" else U(rng, 20, 90, nprod)
        share = rng.dirichlet(np.ones(nprod)); perf = U(rng, .75, .95); scrap = U(rng, .01, .08, nprod)
        total = share * run * 3600 / ict * perf; good = total * (1 - scrap)
        out.append(dict(cal=cal, planned=planned, unplanned=unplanned, ict=ict, total=total, good=good, k=k,
                        strokes_reported=k > 1))
    return {"plants": out}


def _b1_oee(pl, parts=True, denom="ppt", good=True, ict_mode="product"):
    n = pl["good"] if good else pl["total"]
    if not parts:
        n = n / pl["k"]
    ict = pl["ict"] if ict_mode == "product" else (np.full_like(pl["ict"], pl["ict"].mean()) if ict_mode == "mean" else np.full_like(pl["ict"], pl["ict"].min()))
    num = (n * ict).sum() / 3600
    den = {"ppt": pl["cal"] - pl["planned"], "cal": pl["cal"], "run": pl["cal"] - pl["planned"] - pl["unplanned"]}[denom]
    return num, den


def b1_V1(W):
    num = sum(_b1_oee(p)[0] for p in W["plants"]); den = sum(_b1_oee(p)[1] for p in W["plants"]); return {"oee": num / den}


def b1_V2(W):
    """Loss-tree route: per-plant availability x performance x quality, then PPT-weighted."""
    tot = 0; w = 0
    for p in W["plants"]:
        ppt = p["cal"] - p["planned"]; run = ppt - p["unplanned"]
        A = run / ppt; Pf = (p["total"] * p["ict"]).sum() / 3600 / run; Q = (p["good"] * p["ict"]).sum() / (p["total"] * p["ict"]).sum()
        tot += ppt * A * Pf * Q; w += ppt
    return {"oee": tot / w}


def _b1_fleet(W, **kw):
    num = sum(_b1_oee(p, **kw)[0] for p in W["plants"]); den = sum(_b1_oee(p, **kw)[1] for p in W["plants"]); return {"oee": num / den}


def _b1_mean(W, stat=np.mean, weight=None):
    v = np.array([_b1_oee(p)[0] / _b1_oee(p)[1] for p in W["plants"]])
    if weight == "parts":
        w = np.array([p["good"].sum() for p in W["plants"]]); return {"oee": float((v * w).sum() / w.sum())}
    return {"oee": float(stat(v))}


def _b1_product_of_fleet_factors(W):
    A, Pf, Q = [], [], []
    for p in W["plants"]:
        ppt = p["cal"] - p["planned"]; run = ppt - p["unplanned"]
        A.append(run / ppt); Pf.append((p["total"] * p["ict"]).sum() / 3600 / run); Q.append(p["good"].sum() / p["total"].sum())
    return {"oee": float(np.mean(A) * np.mean(Pf) * np.mean(Q))}


def _b1_reported_counts(W):
    """Uses the plant's reported count field as parts (strokes for multi-cavity plants)."""
    num = 0; den = 0
    for p in W["plants"]:
        a, b = _b1_oee(p, parts=not p["strokes_reported"]); num += a; den += b
    return {"oee": num / den}


B1 = dict(gen=b1_gen, regimes=["uniform", "multi_cavity", "size_skew", "mix_skew", "maint_skew"], q=("oee",),
          valid={"V1_row_level_sums": b1_V1, "V2_loss_tree_ppt_weighted": b1_V2}, relabel_valid={},
          wrong={
              "W01_mean_of_plant_oee": _b1_mean,
              "W02_calendar_denominator_teep": lambda W: _b1_fleet(W, denom="cal"),
              "W03_total_parts_incl_scrap": lambda W: _b1_fleet(W, good=False),
              "W04_reported_strokes_as_parts": _b1_reported_counts,
              "W05_product_of_mean_factors": _b1_product_of_fleet_factors,
              "W06_run_time_denominator": lambda W: _b1_fleet(W, denom="run"),
              "W07_parts_weighted_plant_oee": lambda W: _b1_mean(W, weight="parts"),
              "W08_plant_average_cycle_time": lambda W: _b1_fleet(W, ict_mode="mean"),
              "W09_median_plant_oee": lambda W: _b1_mean(W, stat=np.median),
              "W10_fastest_cycle_time_for_all": lambda W: _b1_fleet(W, ict_mode="min"),
          })


# =================================================================================== B2 warehouse labour hours
def b2_gen(rng, r):
    S = 6; sites = []
    for s in range(S):
        utype = ["units", "lines", "cases"][s % 3] if r != "uniform_units" else "units"
        upl = U(rng, 1.2, 3.5) if r != "lines_heavy" else U(rng, 2.5, 6.0); pack = U(rng, 6, 24)
        units = U(rng, 40000, 400000) if r == "size_skew" else U(rng, 80000, 200000)
        uph = U(rng, 60, 180); direct = units / uph
        share = U(rng, .6, .75) if r == "indirect_heavy" else U(rng, .75, .9)
        paid = direct / share
        reported = {"units": units, "lines": units / upl, "cases": units / pack}[utype]
        fc = units * U(rng, .8, 1.3) / 4
        sites.append(dict(utype=utype, upl=upl, pack=pack, units=units, direct=direct, paid=paid, reported=reported, fc=fc))
    return {"sites": sites}


def _b2_units(s, mode):
    if mode == "raw":
        return s["reported"]
    if mode == "no_cases":
        return s["reported"] * (s["upl"] if s["utype"] == "lines" else 1)
    if mode == "net_upl":
        return None
    return s["reported"] * {"units": 1, "lines": s["upl"], "cases": s["pack"]}[s["utype"]]


def b2_V1(W):
    return {"hours": float(sum(s["fc"] * s["direct"] / _b2_units(s, "ok") for s in W["sites"]))}


def b2_V2(W):
    """Rate route: per-site productive UPH, weekly hours = forecast / UPH, via weekly totals."""
    tot = 0.0
    for s in W["sites"]:
        wk_units = _b2_units(s, "ok") / 4; wk_hours = s["direct"] / 4; tot += s["fc"] / (wk_units / wk_hours)
    return {"hours": tot}


def _b2(W, units="ok", hours="direct", pooled=False, share=None, stat=None):
    S = W["sites"]
    U_ = [(_b2_units(s, units) if units != "net_upl" else s["reported"] * ({"units": 1, "lines": np.mean([x["upl"] for x in S]), "cases": s["pack"]}[s["utype"]])) for s in S]
    Hh = [(s["paid"] * share if share else s[hours]) for s in S]
    if pooled:
        return {"hours": float(sum(s["fc"] for s in S) * sum(Hh) / sum(U_))}
    if stat == "mean_uph":
        uph = np.mean([u / h for u, h in zip(U_, Hh)]); return {"hours": float(sum(s["fc"] for s in S) / uph)}
    return {"hours": float(sum(s["fc"] * h / u for s, u, h in zip(S, U_, Hh)))}


B2 = dict(gen=b2_gen, regimes=["mixed_units", "lines_heavy", "size_skew", "indirect_heavy", "uniform_units"], q=("hours",),
          valid={"V1_site_hours_per_unit": b2_V1, "V2_weekly_uph_route": b2_V2}, relabel_valid={},
          wrong={
              "W01_picks_as_units": lambda W: _b2(W, units="raw"),
              "W02_paid_hours": lambda W: _b2(W, hours="paid"),
              "W03_network_average_rate": lambda W: _b2(W, pooled=True),
              "W04_network_units_per_line": lambda W: _b2(W, units="net_upl"),
              "W05_cases_not_converted": lambda W: _b2(W, units="no_cases"),
              "W06_mean_of_site_uph": lambda W: _b2(W, stat="mean_uph"),
              "W07_assumed_85pct_productive": lambda W: _b2(W, share=.85),
              "W08_paid_hours_and_raw_picks": lambda W: _b2(W, units="raw", hours="paid"),
              "W09_network_rate_raw_picks": lambda W: _b2(W, units="raw", pooled=True),
              "W10_network_rate_paid_hours": lambda W: _b2(W, hours="paid", pooled=True),
          })


# =================================================================================== B3 data-centre headroom
def b3_gen(rng, r):
    H = 8; halls = []
    for h in range(H):
        topo = rng.choice(["2N", "N+1"]) if r != "all_2N" else "2N"
        n = int(rng.integers(2, 7)); kva = U(rng, 250, 750); pf = .9
        inst = n * kva * pf; usable = .8 * (inst / 2 if topo == "2N" else inst * (n - 1) / n)
        util = U(rng, .75, 1.05) if r == "hot_halls" else U(rng, .3, .7)
        avg = util * usable; peak = avg * (U(rng, 1.3, 1.6) if r == "peaky" else U(rng, 1.1, 1.3))
        reserved = usable * (U(rng, .1, .3) if r == "reserved_heavy" else U(rng, 0, .1))
        halls.append(dict(topo=topo, n=n, kva=kva, pf=pf, avg=avg, peak=peak, reserved=reserved))
    return {"halls": halls}


def _b3_usable(h, pf=True, redundancy="own", derate=True):
    inst = h["n"] * h["kva"] * (h["pf"] if pf else 1.0)
    topo = h["topo"] if redundancy == "own" else redundancy
    u = inst if topo == "none" else (inst / 2 if topo == "2N" else inst * (h["n"] - 1) / h["n"])
    return u * (.8 if derate else 1.0)


def b3_V1(W):
    return {"headroom": float(sum(max(0, _b3_usable(h) - h["peak"] - h["reserved"]) for h in W["halls"]))}


def b3_V2(W):
    """Module-level route: usable kW per module path, summed hall by hall with explicit clipping."""
    tot = 0.0
    for h in W["halls"]:
        mod_kw = h["kva"] * h["pf"] * .8
        usable = mod_kw * (h["n"] / 2 if h["topo"] == "2N" else h["n"] - 1)
        tot += usable - h["peak"] - h["reserved"] if usable > h["peak"] + h["reserved"] else 0.0
    return {"headroom": tot}


def _b3(W, load="peak", reserved=True, pooled=False, **kw):
    vals = [_b3_usable(h, **kw) - h[load] - (h["reserved"] if reserved else 0) for h in W["halls"]]
    return {"headroom": float(sum(vals) if pooled else sum(max(0, v) for v in vals))}


B3 = dict(gen=b3_gen, regimes=["mixed", "all_2N", "hot_halls", "peaky", "reserved_heavy"], q=("headroom",),
          valid={"V1_hall_usable_minus_peak": b3_V1, "V2_module_path_route": b3_V2}, relabel_valid={},
          wrong={
              "W01_kva_as_kw": lambda W: _b3(W, pf=False),
              "W02_ignore_redundancy": lambda W: _b3(W, redundancy="none"),
              "W03_all_halls_2N": lambda W: _b3(W, redundancy="2N"),
              "W04_all_halls_N+1": lambda W: _b3(W, redundancy="N+1"),
              "W05_ignore_derate": lambda W: _b3(W, derate=False),
              "W06_average_not_peak_load": lambda W: _b3(W, load="avg"),
              "W07_ignore_reserved": lambda W: _b3(W, reserved=False),
              "W08_pooled_across_halls": lambda W: _b3(W, pooled=True),
              "W09_dashboard_nameplate_minus_average": lambda W: _b3(W, pf=False, redundancy="none", derate=False, load="avg", reserved=False),
              "W10_derate_but_pooled_average": lambda W: _b3(W, load="avg", pooled=True),
          })


# =================================================================================== B4 fleet capacity factor
def b4_gen(rng, r):
    units = []
    for i in range(12):
        solar = i % 2 == 0
        cap = U(rng, 20, 150); dcac = U(rng, 1.2, 1.35) if solar else 1.0
        derate = (U(rng, .8, .95) if (not solar and (rng.random() < (.8 if r == "derates" else .3))) else 1.0)
        eff = cap * derate                                  # AC MW (solar) or permitted MW (wind)
        cod_frac = (U(rng, .2, .9) if rng.random() < (.6 if r == "new_builds" else .2) else 1.0)
        hours = 8760 * cod_frac
        cf = U(rng, .18, .28) if solar else U(rng, .28, .42)
        if r == "size_skew":
            cap *= U(rng, .2, 3.0); eff = cap * derate
        E = cf * eff * hours
        units.append(dict(solar=solar, ac=cap, dc=cap * dcac, derate=derate, eff=eff, hours=hours, E=E, rated=cap))
    return {"units": units}


def b4_V1(W):
    u = W["units"]; return {"cf": sum(x["E"] for x in u) / sum(x["eff"] * x["hours"] for x in u)}


def b4_V2(W):
    """Capacity-hours-weighted average of unit CFs (algebraic route)."""
    u = W["units"]; w = [x["eff"] * x["hours"] for x in u]; cf = [x["E"] / (x["eff"] * x["hours"]) for x in u]
    return {"cf": float(np.dot(w, cf) / sum(w))}


def _b4(W, cap="eff", hours="cod", mode="pooled"):
    u = W["units"]
    c = [x["dc"] if (cap == "dc" and x["solar"]) else (x["rated"] if cap in ("rated", "dc") else x["eff"]) for x in u]
    hh = [8760.0 if hours == "full" else x["hours"] for x in u]
    if mode == "mean":
        return {"cf": float(np.mean([x["E"] / (ci * hi) for x, ci, hi in zip(u, c, hh)]))}
    if mode == "capw":
        cfs = [x["E"] / (ci * hi) for x, ci, hi in zip(u, c, hh)]; return {"cf": float(np.dot(c, cfs) / sum(c))}
    return {"cf": float(sum(x["E"] for x in u) / sum(ci * hi for ci, hi in zip(c, hh)))}


B4 = dict(gen=b4_gen, regimes=["mixed", "new_builds", "derates", "size_skew", "solar_heavy"], q=("cf",),
          valid={"V1_energy_over_capacity_hours": b4_V1, "V2_weighted_unit_cf": b4_V2}, relabel_valid={},
          wrong={
              "W01_dc_nameplate_for_solar": lambda W: _b4(W, cap="dc"),
              "W02_full_year_hours": lambda W: _b4(W, hours="full"),
              "W03_mean_of_unit_cf": lambda W: _b4(W, mode="mean"),
              "W04_original_rating_ignore_derate": lambda W: _b4(W, cap="rated"),
              "W05_capacity_weighted_unit_cf": lambda W: _b4(W, mode="capw"),
              "W06_dc_and_full_year": lambda W: _b4(W, cap="dc", hours="full"),
              "W07_mean_cf_full_year": lambda W: _b4(W, hours="full", mode="mean"),
              "W08_rated_and_full_year": lambda W: _b4(W, cap="rated", hours="full"),
              "W09_mean_cf_dc": lambda W: _b4(W, cap="dc", mode="mean"),
              "W10_capw_full_year": lambda W: _b4(W, hours="full", mode="capw"),
          })
# solar_heavy: identical generator; the regime label only reruns with a different seed stream (documented honestly)


# =================================================================================== C1 rolled throughput yield
def c1_gen(rng, r):
    fams = []
    for f in range(3):
        starts = U(rng, 500, 40000) if r == "family_skew" else U(rng, 5000, 15000)
        S = 5; fpy = U(rng, .80, .95, S) if r == "low_fpy" else U(rng, .90, .995, S)
        if r == "family_skew" and f == 0:
            fpy = U(rng, .75, .85, S)
        rw = U(rng, .8, .95, S) if r == "rework_heavy" else (U(rng, .1, .3, S) if r == "scrap_heavy" else U(rng, .5, .9, S))
        rows = []; units = starts
        for s in range(S):
            passed = units * fpy[s]; fail = units - passed; rework_ok = fail * rw[s]; scrap = fail - rework_ok
            rows.append(dict(units_in=units, passed_first=passed, rework_ok=rework_ok, scrapped=scrap)); units = passed + rework_ok
        fams.append(dict(starts=starts, rows=rows, completions=units))
    return {"fams": fams}


def c1_V1(W):
    num = sum(f["starts"] * np.prod([x["passed_first"] / x["units_in"] for x in f["rows"]]) for f in W["fams"])
    return {"rty": num / sum(f["starts"] for f in W["fams"])}


def c1_V2(W):
    """Unit-flow route: expected first-pass completions per family by propagating first-pass flow step by step."""
    tot = 0.0
    for f in W["fams"]:
        flow = f["starts"]
        for x in f["rows"]:
            flow = flow * (x["passed_first"] / x["units_in"])
        tot += flow
    return {"rty": tot / sum(f["starts"] for f in W["fams"])}


def _c1(W, step="fpy", combine="prod", wmode="starts", pool=False):
    F = W["fams"]
    def sy(x):
        return {"fpy": x["passed_first"] / x["units_in"], "reported": (x["passed_first"] + x["rework_ok"]) / x["units_in"],
                "no_scrap": 1 - x["scrapped"] / x["units_in"]}[step]
    if pool:
        S = len(F[0]["rows"]); ys = []
        for s in range(S):
            num = sum(f["rows"][s]["passed_first"] for f in F); den = sum(f["rows"][s]["units_in"] for f in F); ys.append(num / den)
        return {"rty": float(np.prod(ys))}
    vals = []
    for f in F:
        ys = [sy(x) for x in f["rows"]]
        vals.append({"prod": np.prod(ys), "mean": np.mean(ys), "min": np.min(ys)}[combine])
    w = {"starts": [f["starts"] for f in F], "equal": [1] * len(F), "completions": [f["completions"] for f in F]}[wmode]
    return {"rty": float(np.dot(w, vals) / sum(w))}


C1 = dict(gen=c1_gen, regimes=["uniform", "low_fpy", "family_skew", "rework_heavy", "scrap_heavy"], q=("rty",),
          valid={"V1_product_of_fpy": c1_V1, "V2_first_pass_flow": c1_V2}, relabel_valid={},
          wrong={
              "W01_product_of_reported_yields": lambda W: _c1(W, step="reported"),
              "W02_final_yield_completions_over_starts": lambda W: {"rty": sum(f["completions"] for f in W["fams"]) / sum(f["starts"] for f in W["fams"])},
              "W03_mean_step_fpy": lambda W: _c1(W, combine="mean"),
              "W04_unweighted_family_mean": lambda W: _c1(W, wmode="equal"),
              "W05_pooled_step_fpy_then_product": lambda W: _c1(W, pool=True),
              "W06_completions_weighted": lambda W: _c1(W, wmode="completions"),
              "W07_min_step_fpy": lambda W: _c1(W, combine="min"),
              "W08_ignore_rework_count_only_scrap": lambda W: _c1(W, step="no_scrap"),
              "W09_mean_of_reported_yields": lambda W: _c1(W, step="reported", combine="mean"),
              "W10_reported_unweighted": lambda W: _c1(W, step="reported", wmode="equal"),
          })


# =================================================================================== C2 hierarchical forecast accuracy
def c2_gen(rng, r):
    K, S, Wk = 40, 10, 8
    lam = np.exp(rng.normal(1.5 if r != "intermittent" else 0.0, 1.0 if r != "skewed_volume" else 1.8, K))[:, None, None] * U(rng, .5, 1.5, S)[None, :, None]
    A = rng.poisson(np.broadcast_to(lam, (K, S, Wk))).astype(float)
    bias = U(rng, -.3, .3, S)[None, :, None] if r == "store_bias" else 0.0
    F = np.maximum(0, lam * (1 + bias) * np.exp(.35 * rng.standard_normal((K, S, Wk))))
    disc = rng.random(K) < (.3 if r == "discontinued_heavy" else .1)
    A[disc, :, :] = 0.0
    return dict(A=A, F=F, disc=disc)


def c2_V1(W):
    a = ~W["disc"]; A, F = W["A"][a], W["F"][a]; return {"acc": 1 - np.abs(F - A).sum() / A.sum()}


def c2_V2(W):
    """Decomposed route: per-store absolute-error and actual totals, then combined."""
    a = ~W["disc"]; err = 0.0; act = 0.0
    for s in range(W["A"].shape[1]):
        e = np.abs(W["F"][a, s, :] - W["A"][a, s, :]); err += e.sum(); act += W["A"][a, s, :].sum()
    return {"acc": 1 - err / act}


def _c2(W, grain="ksw", include_disc=False, metric="wape"):
    a = np.ones(len(W["disc"]), bool) if include_disc else ~W["disc"]; A, F = W["A"][a], W["F"][a]
    if grain == "kw":
        A, F = A.sum(1), F.sum(1)
    elif grain == "sw":
        A, F = A.sum(0), F.sum(0)
    elif grain == "ksm":
        A, F = A.sum(2), F.sum(2)
    if metric == "wape":
        return {"acc": float(1 - np.abs(F - A).sum() / A.sum())}
    if metric == "fwape":
        return {"acc": float(1 - np.abs(F - A).sum() / F.sum())}
    if metric == "mape":
        m = A > 0; return {"acc": float(1 - np.mean(np.abs(F[m] - A[m]) / A[m]))}
    if metric == "smape":
        d = (np.abs(A) + np.abs(F)); m = d > 0; return {"acc": float(1 - np.mean(2 * np.abs(F[m] - A[m]) / d[m]))}
    if metric == "sku_mean":
        e = np.abs(F - A).sum((1, 2)); s = A.sum((1, 2)); m = s > 0; return {"acc": float(1 - np.mean(e[m] / s[m]))}
    if metric == "nonzero":
        m = A > 0; return {"acc": float(1 - np.abs(F[m] - A[m]).sum() / A[m].sum())}


C2 = dict(gen=c2_gen, regimes=["smooth", "intermittent", "store_bias", "discontinued_heavy", "skewed_volume"], q=("acc",),
          valid={"V1_row_level_wape": c2_V1, "V2_store_decomposed": c2_V2}, relabel_valid={},
          wrong={
              "W01_sku_week_aggregate": lambda W: _c2(W, grain="kw"),
              "W02_store_week_aggregate": lambda W: _c2(W, grain="sw"),
              "W03_mean_mape_nonzero": lambda W: _c2(W, metric="mape"),
              "W04_include_discontinued": lambda W: _c2(W, include_disc=True),
              "W05_mean_of_sku_wape": lambda W: _c2(W, metric="sku_mean"),
              "W06_forecast_weighted": lambda W: _c2(W, metric="fwape"),
              "W07_monthly_grain": lambda W: _c2(W, grain="ksm"),
              "W08_smape": lambda W: _c2(W, metric="smape"),
              "W09_exclude_zero_actual_rows": lambda W: _c2(W, metric="nonzero"),
              "W10_include_discontinued_sku_week": lambda W: _c2(W, grain="kw", include_disc=True),
          })


# =================================================================================== C3 like-for-like conversion
def c3_gen(rng, r):
    N = 120; st = []
    for i in range(N):
        open_m = int(rng.integers(-60, -14)) if rng.random() > (.35 if r == "many_new_stores" else .1) else int(rng.integers(-13, 6))
        closed = rng.random() < (.12 if r == "closures" else .03)
        remodel = int(rng.integers(3, 10)) if rng.random() < (.25 if r == "remodel_wave" else .05) else 0
        base = U(rng, .15, .35); new = open_m > -13
        traffic_ly = 0.0 if open_m > -12 else U(rng, 20000, 90000)
        traffic_ty = U(rng, 20000, 90000) * (0 if closed else 1) * (1 - remodel / 52)
        conv_ly = base; conv_ty = base * U(rng, .96, 1.04) - (.06 if new else 0)
        if r == "traffic_shift" and not new:
            traffic_ty *= (2.0 if base < .22 else 0.8)
        st.append(dict(open_m=open_m, closed=closed, remodel=remodel, tr_ly=traffic_ly, tr_ty=traffic_ty,
                       tx_ly=traffic_ly * conv_ly, tx_ty=traffic_ty * conv_ty))
    return {"stores": st}


def _c3_comp(s, cutoff=-13, remodel_rule=True, closed_rule=True):
    return s["open_m"] <= cutoff and (not closed_rule or not s["closed"]) and (not remodel_rule or s["remodel"] <= 2) and s["tr_ly"] > 0


def c3_V1(W):
    C = [s for s in W["stores"] if _c3_comp(s)]
    return {"delta": sum(s["tx_ty"] for s in C) / sum(s["tr_ty"] for s in C) - sum(s["tx_ly"] for s in C) / sum(s["tr_ly"] for s in C)}


def c3_V2(W):
    """Traffic-share route: Δ = Σ w_ty·conv_ty − Σ w_ly·conv_ly with within-period traffic shares."""
    C = [s for s in W["stores"] if _c3_comp(s)]
    wty = np.array([s["tr_ty"] for s in C]); wly = np.array([s["tr_ly"] for s in C])
    cty = np.array([s["tx_ty"] / s["tr_ty"] for s in C]); cly = np.array([s["tx_ly"] / s["tr_ly"] for s in C])
    return {"delta": float((wty / wty.sum()) @ cty - (wly / wly.sum()) @ cly)}


def _c3(W, pop="comp", agg="pooled", **kw):
    S = W["stores"]
    C = [s for s in S if (_c3_comp(s, **kw) if pop == "comp" else True)]
    ty = [s for s in C if s["tr_ty"] > 0]; ly = [s for s in C if s["tr_ly"] > 0]
    if agg == "store_mean":
        both = [s for s in C if s["tr_ty"] > 0 and s["tr_ly"] > 0]
        return {"delta": float(np.mean([s["tx_ty"] / s["tr_ty"] - s["tx_ly"] / s["tr_ly"] for s in both]))}
    if agg == "ly_weights":
        both = [s for s in C if s["tr_ty"] > 0 and s["tr_ly"] > 0]; w = np.array([s["tr_ly"] for s in both])
        return {"delta": float(w @ np.array([s["tx_ty"] / s["tr_ty"] - s["tx_ly"] / s["tr_ly"] for s in both]) / w.sum())}
    cty = sum(s["tx_ty"] for s in ty) / sum(s["tr_ty"] for s in ty); cly = sum(s["tx_ly"] for s in ly) / sum(s["tr_ly"] for s in ly)
    if agg == "relative":
        return {"delta": float((cty / cly - 1) * cly)}      # reported as a relative change, re-expressed on the pp scale
    return {"delta": float(cty - cly)}


C3 = dict(gen=c3_gen, regimes=["stable", "many_new_stores", "remodel_wave", "traffic_shift", "closures"], q=("delta",),
          scale=lambda W, T: 0.01,                       # absolute error measured against 1 pp of conversion
          valid={"V1_pooled_comparable": c3_V1, "V2_traffic_share_route": c3_V2}, relabel_valid={},
          wrong={
              "W01_all_stores": lambda W: _c3(W, pop="all"),
              "W02_store_average_change": lambda W: _c3(W, agg="store_mean"),
              "W03_ly_traffic_weights_both_periods": lambda W: _c3(W, agg="ly_weights"),
              "W04_include_remodels": lambda W: _c3(W, remodel_rule=False),
              "W05_include_closed": lambda W: _c3(W, closed_rule=False),
              "W06_cutoff_12_months": lambda W: _c3(W, cutoff=-12),
              "W07_cutoff_24_months": lambda W: _c3(W, cutoff=-24),
              "W08_all_stores_store_average": lambda W: _c3(W, pop="all", agg="store_mean"),
              "W09_no_exclusions_but_cutoff": lambda W: _c3(W, remodel_rule=False, closed_rule=False),
              "W10_relative_change_as_pp": lambda W: _c3(W, agg="relative"),
          })


# =================================================================================== C4 recall under deployment mix
def c4_gen(rng, r):
    S = 6
    n = U(rng, 50, 2000, S); rec = U(rng, .5, .95, S); d = np.round(n * rec); n = np.round(n)
    T_eval = U(rng, 1e5, 1e6, S)
    shift = {"uniform": .0, "mild_shift": .3, "big_shift": 1.0, "rate_shift": .2, "segment_growth": .5}[r]
    t = T_eval * np.exp(shift * rng.standard_normal(S)); t = t / t.sum()
    r_eval = n / T_eval
    r_tgt = r_eval * (np.exp(.8 * rng.standard_normal(S)) if r == "rate_shift" else np.exp(.1 * rng.standard_normal(S)))
    if r == "segment_growth":
        t[0] *= 4; t = t / t.sum()
    return dict(n=n, d=d, T_eval=T_eval, t=t, r_eval=r_eval, r_tgt=r_tgt)


def c4_V1(W):
    w = W["t"] * W["r_tgt"]; w = w / w.sum(); return {"recall": float(w @ (W["d"] / W["n"]))}


def c4_V2(W):
    """Expected-count route: forecast fraud counts per segment x recall, summed, over total forecast fraud."""
    fraud = 1e6 * W["t"] * W["r_tgt"]; return {"recall": float((fraud * W["d"] / W["n"]).sum() / fraud.sum())}


def _c4w(W, w):
    w = np.asarray(w, float); return {"recall": float((w / w.sum()) @ (W["d"] / W["n"]))}


C4 = dict(gen=c4_gen, regimes=["uniform", "mild_shift", "big_shift", "rate_shift", "segment_growth"], q=("recall",),
          valid={"V1_fraud_share_weights": c4_V1, "V2_expected_count_route": c4_V2}, relabel_valid={},
          wrong={
              "W01_pooled_eval_recall": lambda W: {"recall": float(W["d"].sum() / W["n"].sum())},
              "W02_unweighted_segment_mean": lambda W: _c4w(W, np.ones(len(W["n"]))),
              "W03_weight_by_target_transactions": lambda W: _c4w(W, W["t"]),
              "W04_weight_by_eval_transactions": lambda W: _c4w(W, W["T_eval"]),
              "W05_weight_by_target_fraud_rate_only": lambda W: _c4w(W, W["r_tgt"]),
              "W06_target_mix_eval_rates": lambda W: _c4w(W, W["t"] * W["r_eval"]),
              "W07_eval_mix_target_rates": lambda W: _c4w(W, W["T_eval"] * W["r_tgt"]),
              "W08_harmonic_mean_recall": lambda W: {"recall": float(len(W["n"]) / np.sum(W["n"] / W["d"]))},
              "W09_median_segment_recall": lambda W: {"recall": float(np.median(W["d"] / W["n"]))},
              "W10_sqrt_fraud_weights": lambda W: _c4w(W, np.sqrt(W["t"] * W["r_tgt"])),
          })

CONCEPTS = {"A1_take_or_pay": A1, "A2_atp_rebalancing": A2, "A3_shared_bottleneck_mix": A3, "A4_cloud_commitment": A4,
            "B1_fleet_oee": B1, "B2_labour_hours": B2, "B3_dc_power_headroom": B3, "B4_capacity_factor": B4,
            "C1_rolled_throughput_yield": C1, "C2_forecast_accuracy": C2, "C3_like_for_like": C3, "C4_recall_deployment_mix": C4}


def run(worlds=60):
    out = {}
    for ci, (name, C) in enumerate(CONCEPTS.items()):
        vk = list(C["valid"]); V1 = C["valid"][vk[0]]
        res = {"valid": {}, "wrong": {}, "regimes": C["regimes"]}
        errs = {m: {r: [] for r in C["regimes"]} for m in list(C["valid"])[1:] + list(C["wrong"])}
        for ri, r in enumerate(C["regimes"]):
            rng = np.random.default_rng(1000 * ci + ri)
            for _ in range(worlds):
                W = C["gen"](rng, r); T = V1(W)
                sc = {q: (C["scale"](W, T) if "scale" in C else abs(T[q])) or 1e-12 for q in C["q"]}
                for m, fn in list(C["valid"].items())[1:] + list(C["wrong"].items()):
                    try:
                        e = max(abs(fn(W)[q] - T[q]) / sc[q] for q in C["q"])
                    except Exception:
                        e = float("nan")
                    errs[m][r].append(e)
        for m in list(C["valid"])[1:]:
            allv = np.concatenate([errs[m][r] for r in C["regimes"]]); res["valid"][m] = {"p99": float(np.nanpercentile(allv, 99)), "max": float(np.nanmax(allv))}
        VB = max([TOL] + [v["p99"] for v in res["valid"].values()])
        for m in C["wrong"]:
            det = {r: float(np.nanpercentile(errs[m][r], 5)) for r in C["regimes"]}
            med = {r: float(np.nanmedian(errs[m][r])) for r in C["regimes"]}
            coin = float(np.nanmean(np.concatenate([np.array(errs[m][r]) <= TOL for r in C["regimes"]])))
            res["wrong"][m] = {"detect_p05": det, "median": med, "wrong_bound": sorted(det.values(), reverse=True)[1], "coincidence": coin}
        wb_m = min(res["wrong"], key=lambda k: res["wrong"][k]["wrong_bound"])
        res.update(VALID_BOUND=VB, WRONG_BOUND=res["wrong"][wb_m]["wrong_bound"], hardest=wb_m, ratio=res["wrong"][wb_m]["wrong_bound"] / VB)
        out[name] = res
        print("%-28s VB %.4f  WB %.4f (%s)  ratio %6.2f" % (name, VB, res["WRONG_BOUND"], wb_m, res["ratio"]))
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    Path(__file__).with_name("g39_results.json").write_text(json.dumps(run(n), indent=1) + "\n")
