"""G50 Northline Boost world generator. Deterministic, stdlib + numpy only.

Writes an operational SQLite warehouse plus the pre-period metric extract. The latent quantities the
verifier grades (the rollout contrast, the control-arm contamination, the courier-supply response) are
produced by counterfactual re-simulation of the same market-hours, never by a reference estimator.
"""
import json, os, sqlite3, sys
from datetime import date, datetime, timedelta
import numpy as np

EPOCH = date(2026, 4, 6)          # a Monday
HOURS = (10, 22)
DOW = np.array([0.88, 0.86, 0.92, 1.02, 1.24, 1.34, 1.16])
HOD = np.array([0.55, 0.72, 1.05, 1.32, 1.05, 0.78, 0.70, 0.85, 1.28, 1.42, 1.10, 0.68])

VISIBLE_SPEC = dict(
    name="visible", seed=515001,
    n_markets=20, holdout_markets=4, pre_weeks=4, soak_weeks=4, exp_weeks=6,
    promise_min=38.0, base_lambda=13.0, couriers_per_order=0.46,
    queue_min_per_slot=1.10, base_accept_min=2.2, delta_accept_min=0.22,
    prep_mean=14.0, prep_sd=4.0, travel_mean=13.0, travel_sd=6.0,
    beta_supply=0.030, eta_density=0.50, gamma_idle=0.060, scale_sd=0.42,
    p_ramp=(0.25, 0.55), cancel_rate=0.018,
    incentive_per_boost_gbp=0.19,
    # v2: persistent market-level service level and a common seasonal movement, both on travel minutes.
    market_offset_sd=2.6,          # persistent between-market differences in travel time
    week_drift_min=1.30,           # common movement across the window, peak-to-trough, in minutes
    p_scheduled=0.045, p_corporate=0.028,
)

MARKET_NAMES = ["Ashford","Bellhaven","Carrow","Draycott","Elsmere","Fenwick","Gorsely","Harlow",
                "Inglewood","Jarrow","Kelvedon","Lymington","Marden","Netherby","Oakworth","Penhale",
                "Quarrend","Rushmere","Salterton","Thornbury"]
REGIONS = ["North","North","Midlands","Midlands","South","South","West","West","North","Midlands",
           "South","West","North","Midlands","South","West","North","Midlands","South","West"]


def _mk(spec):
    rng = np.random.default_rng(spec["seed"])
    M, HO = spec["n_markets"], spec["holdout_markets"]
    PW, SW, EW = spec["pre_weeks"], spec["soak_weeks"], spec["exp_weeks"]
    W = PW + SW + EW
    h0, h1 = HOURS; H = h1 - h0
    scale = np.exp(rng.normal(0, spec["scale_sd"], M)).clip(0.45, 2.6)
    beta = np.abs(rng.normal(spec["beta_supply"], spec["beta_supply"] * 0.22, M))
    gamma = np.abs(rng.normal(spec["gamma_idle"], spec["gamma_idle"] * 0.22, M))
    mkt_off = rng.normal(0.0, spec["market_offset_sd"], M)          # persistent, all weeks
    enrolled = np.arange(M - HO); holdout = np.arange(M - HO, M)
    perm = rng.permutation(enrolled); soak_t = set(perm[: len(enrolled) // 2].tolist())
    S = np.zeros((M, W))
    for m in range(M):
        for w in range(W):
            if w < PW:
                S[m, w] = 0.0
            elif w < PW + SW:
                S[m, w] = 1.0 if m in soak_t else 0.0
            elif m in holdout:
                S[m, w] = 0.0
            else:
                S[m, w] = spec["p_ramp"][0] if w < PW + SW + 2 else spec["p_ramp"][1]
    idx = [(m, w, d, hi, spec["base_lambda"] * scale[m] * DOW[d] * HOD[hi])
           for m in range(M) for w in range(W) for d in range(7) for hi in range(H)]
    mh = np.array(idx); N = rng.poisson(mh[:, 4]); keep = N > 0
    mh, N = mh[keep], N[keep]
    m_ix, w_ix, d_ix, h_ix = (mh[:, i].astype(int) for i in range(4))
    lam = mh[:, 4]
    Smh = S[m_ix, w_ix]
    Kb = np.maximum(1.0, spec["couriers_per_order"] * lam)
    # Common seasonal movement over the window: a gentle rise then fall, identical in every market.
    wk_shift = spec["week_drift_min"] * np.sin(np.pi * np.arange(W) / max(W - 1, 1))
    o = np.repeat(np.arange(len(N)), N); n = len(o)
    u = rng.random(n)
    prep = rng.normal(spec["prep_mean"], spec["prep_sd"], n).clip(5, None)
    trav = (rng.normal(spec["travel_mean"], spec["travel_sd"], n)
            + mkt_off[m_ix][o] + wk_shift[w_ix][o]).clip(3, None)
    minute = rng.random(n) * 60.0
    soak_h = (w_ix >= PW) & (w_ix < PW + SW)
    exp_mh = w_ix >= PW + SW
    boosted = np.where(soak_h[o], Smh[o] > 0.5, rng.random(n) < Smh[o])
    cancelled = rng.random(n) < spec["cancel_rate"]
    # Order channel is a property of the order and is recorded in every period, so eligibility is
    # observable outside the experiment window too.
    cu = rng.random(n)
    channel = np.where(cu < spec["p_scheduled"], "scheduled",
                       np.where(cu < spec["p_scheduled"] + spec["p_corporate"], "corporate", "standard"))
    excluded = channel != "standard"
    start = np.zeros(len(N), dtype=np.int64); start[1:] = np.cumsum(N)[:-1]

    def sim(bv, Sv):
        K = np.maximum(1.0, Kb * (1.0 + beta[m_ix] * Sv))
        key = (~bv).astype(float) + u * 0.5
        srt = np.lexsort((key, o)); pos = np.empty(n)
        pos[srt] = np.arange(n) - np.repeat(start, N)
        acc = (spec["base_accept_min"] - np.where(bv, spec["delta_accept_min"], 0.0)
               + pos / K[o] * spec["queue_min_per_slot"])
        dens = K[o] / Kb[o] - 1.0
        tv = trav * (1.0 - spec["eta_density"] * dens) * (1.0 + gamma[m_ix][o] * Sv[o])
        total = acc + prep + tv
        return total, acc, (total > spec["promise_min"]), K

    total, acc, late, Kact = sim(boosted, Smh)
    enr_mh = np.isin(m_ix, enrolled)
    prog_mh = (w_ix >= PW) & enr_mh          # programme window: phase 1 soak + phase 2
    Sone = np.where(prog_mh, 1.0, Smh)
    Szero = np.where(prog_mh, 0.0, Smh)
    _, _, late_all, Kall = sim(np.ones(n, bool), Sone)
    _, _, late_none, Knone = sim(np.zeros(n, bool), Szero)
    return dict(spec=spec, rng=rng, M=M, W=W, H=H, PW=PW, SW=SW, EW=EW, scale=scale,
                sim=sim, u=u, prep=prep, trav=trav, beta=beta, gamma=gamma, start=start,
                enrolled=enrolled, holdout=holdout, soak_t=soak_t, S=S,
                N=N, m_ix=m_ix, w_ix=w_ix, d_ix=d_ix, h_ix=h_ix, lam=lam, Smh=Smh, Kb=Kb,
                Kact=Kact, Kall=Kall, Knone=Knone, o=o, n=n, minute=minute,
                total=total, acc=acc, late=late, late_all=late_all, late_none=late_none,
                boosted=boosted, cancelled=cancelled, excluded=excluded, channel=channel,
                mkt_off=mkt_off, wk_shift=wk_shift,
                soak_h=soak_h, exp_mh=exp_mh, enr_mh=enr_mh, prog_mh=prog_mh)


def build(spec):
    return _mk(spec)


def metric_population(w):
    """Delivered, Boost-eligible (standard-channel) orders. The reporting population everywhere."""
    return (~w["cancelled"]) & (~w["excluded"])


def _graded_mask(w):
    """Phase-2 enrolled-market orders in the metric population (the arm-contrast population)."""
    o = w["o"]
    return w["exp_mh"][o] & w["enr_mh"][o] & metric_population(w)


def truth(w):
    """The business estimand, plus the quantities the verifier needs.

    Business estimand (docs/rollout_decision_memo.md): the change in the estate-wide, order-weighted
    late-delivery rate over the programme window if Boost were on for every eligible order in every
    enrolled market versus none, with each market weighted by its share of the estate's orders in the
    three weeks BEFORE the programme. Pre-programme weights are used so that the quantity is a weighted
    average of market-level effects and cannot be moved by a treatment-induced change in order mix.
    """
    o = w["o"]
    m_of = w["m_ix"][o]
    w_of = w["w_ix"][o]
    pop = metric_population(w)
    late, la, ln = w["late"], w["late_all"], w["late_none"]
    win = w["prog_mh"][o] & pop                      # programme window, enrolled markets
    pre = (w_of < w["PW"]) & pop                     # pre-programme weeks, every market

    # pre-programme order shares over the enrolled markets
    counts = {m: float((pre & (m_of == m)).sum()) for m in w["enrolled"]}
    tot = sum(counts.values())

    effect = 0.0
    per_market = {}
    for m in w["enrolled"]:
        sel = win & (m_of == m)
        d = (la[sel].mean() - ln[sel].mean()) * 100.0
        per_market[int(m)] = round(float(d), 4)
        effect += (counts[m] / tot) * d

    g = _graded_mask(w)
    b = w["boosted"]
    naive = (late[g & b].mean() - late[g & ~b].mean()) * 100.0

    # courier-hours response, measured where Boost was set at the market level (phase 1), per order
    m_ix = w["m_ix"]
    soak = w["soak_h"] & np.isin(m_ix, w["enrolled"])
    on_m = np.array(sorted(w["soak_t"]))
    off_m = np.array([i for i in w["enrolled"] if i not in w["soak_t"]])
    on = soak & np.isin(m_ix, on_m); off = soak & np.isin(m_ix, off_m)
    supply = ((w["Kact"][on].sum() / w["N"][on].sum())
              / (w["Kact"][off].sum() / w["N"][off].sum()) - 1.0) * 100.0

    spec = w["spec"]
    break_even = spec["incentive_per_boost_gbp"] / LATE_ORDER_COST_GBP * 100.0
    decision = "roll_out" if effect <= -break_even else "do_not_roll_out"
    return dict(
        rollout_effect_pp=round(float(effect), 4),
        naive_order_level_ate_pp=round(float(naive), 4),
        courier_supply_response_pct=round(float(supply), 4),
        graded_orders=int(g.sum()),
        programme_window_orders=int(win.sum()),
        break_even_pp=round(float(break_even), 4),
        decision=decision,
        late_rate_pct=round(float(late[g].mean() * 100), 4),
        per_market_effect_pp=per_market,
    )


LATE_ORDER_COST_GBP = 12.70          # service credit 2.50 + 10.20 expected retention cost




def _ts(d0, w, dow, hour, minute):
    dt = datetime.combine(d0 + timedelta(days=int(w) * 7 + int(dow)), datetime.min.time())
    return (dt + timedelta(hours=int(hour), minutes=float(minute))).strftime("%Y-%m-%d %H:%M:%S")


def write_sqlite(w, out_dir, db_name="northline.sqlite"):
    spec = w["spec"]
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    path = os.path.join(out_dir, "data", db_name)
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path); cur = con.cursor()
    cur.executescript("""
    CREATE TABLE markets (market_id TEXT PRIMARY KEY, market_name TEXT, region TEXT,
                          launched_on TEXT, zone_count INTEGER);
    CREATE TABLE zones (zone_id TEXT PRIMARY KEY, market_id TEXT, zone_name TEXT);
    CREATE TABLE orders (order_id TEXT PRIMARY KEY, zone_id TEXT, placed_at TEXT, order_channel TEXT,
                         promised_minutes REAL, accepted_after_sec REAL,
                         delivered_after_min REAL, status TEXT);
    CREATE TABLE experiment_assignment (order_id TEXT PRIMARY KEY, experiment_id TEXT, arm TEXT);
    CREATE TABLE courier_shifts (shift_id TEXT PRIMARY KEY, courier_id TEXT, market_id TEXT,
                                 shift_date TEXT, hour_start INTEGER, online_minutes REAL);
    CREATE TABLE experiment_config (experiment_id TEXT, market_id TEXT, week_start TEXT, phase TEXT,
                                    randomisation_unit TEXT, boost_share_target REAL, status TEXT);
    CREATE TABLE market_week_baseline (market_id TEXT, week_start TEXT, orders INTEGER,
                                       late_orders INTEGER, median_delivered_min REAL);
    CREATE TABLE incentive_ledger (market_id TEXT, week_start TEXT, boosted_orders INTEGER,
                                   incentive_spend_gbp REAL);
    CREATE TABLE ops_events (event_id TEXT, event_date TEXT, market_id TEXT, event_type TEXT, note TEXT);
    """)
    M = w["M"]; mids = [f"MKT-{i+1:03d}" for i in range(M)]
    cur.executemany("INSERT INTO markets VALUES (?,?,?,?,?)",
                    [(mids[i], MARKET_NAMES[i], REGIONS[i],
                      (EPOCH - timedelta(days=400 + 17 * i)).isoformat(), 3 + (i % 3))
                     for i in range(M)])
    zones = {}
    zrows = []
    for i in range(M):
        for z in range(3 + (i % 3)):
            zid = f"Z-{i+1:03d}{chr(65+z)}"
            zones.setdefault(i, []).append(zid)
            zrows.append((zid, mids[i], f"{MARKET_NAMES[i]} {chr(65+z)}"))
    cur.executemany("INSERT INTO zones VALUES (?,?,?)", zrows)

    o = w["o"]; n = w["n"]; rng = np.random.default_rng(spec["seed"] + 7)
    zpick = rng.random(n)
    orows = []; arows = []
    m_of = w["m_ix"][o]; w_of = w["w_ix"][o]; d_of = w["d_ix"][o]; h_of = w["h_ix"][o]
    late = w["late"]; total = w["total"]; acc = w["acc"]
    for i in range(n):
        mi = int(m_of[i]); zs = zones[mi]
        zid = zs[int(zpick[i] * len(zs))]
        oid = f"O-{i+1:08d}"
        placed = _ts(EPOCH, w_of[i], d_of[i], HOURS[0] + h_of[i], w["minute"][i])
        ch = str(w["channel"][i])
        if w["cancelled"][i]:
            orows.append((oid, zid, placed, ch, spec["promise_min"], None, None, "cancelled"))
        else:
            orows.append((oid, zid, placed, ch, spec["promise_min"], round(float(acc[i] * 60), 1),
                          round(float(total[i]), 2), "delivered"))
        if w["exp_mh"][o[i]] and w["enr_mh"][o[i]]:
            arm = "excluded" if w["excluded"][i] else ("boost" if w["boosted"][i] else "control")
            arows.append((oid, "EXP-BOOST-01", arm))
    cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", orows)
    cur.executemany("INSERT INTO experiment_assignment VALUES (?,?,?)", arows)

    # courier shifts: realise Kact couriers per market-hour as courier-hour rows
    srows = []; sid = 0
    Kact = w["Kact"]
    for j in range(len(w["N"])):
        mi = int(w["m_ix"][j]); k = int(round(float(Kact[j])))
        dstr = (EPOCH + timedelta(days=int(w["w_ix"][j]) * 7 + int(w["d_ix"][j]))).isoformat()
        hour = HOURS[0] + int(w["h_ix"][j])
        for c in range(k):
            sid += 1
            srows.append((f"S-{sid:08d}", f"C-{mi+1:02d}{(c % 400)+1:04d}", mids[mi], dstr, hour, 60.0))
    cur.executemany("INSERT INTO courier_shifts VALUES (?,?,?,?,?,?)", srows)

    crows = []
    for mi in range(M):
        for wk in range(w["W"]):
            s = float(w["S"][mi, wk])
            if wk < w["PW"]:
                phase, unit, status = "pre", "none", "not_running"
            elif wk < w["PW"] + w["SW"]:
                phase, unit = "phase1_soak", "market"
                status = "running" if mi in w["enrolled"] else "not_enrolled"
            else:
                phase, unit = "phase2_order_randomised", "order"
                status = "running" if mi in w["enrolled"] else "holdout"
            crows.append(("EXP-BOOST-01", mids[mi],
                          (EPOCH + timedelta(days=wk * 7)).isoformat(), phase, unit,
                          round(s, 3), status))
    cur.executemany("INSERT INTO experiment_config VALUES (?,?,?,?,?,?,?)", crows)

    # pre-period baseline table, market-week grain
    brows = []
    mp = metric_population(w)
    for mi in range(M):
        for wk in range(w["PW"]):
            sel = (m_of == mi) & (w_of == wk) & mp
            if sel.sum() == 0:
                continue
            brows.append((mids[mi], (EPOCH + timedelta(days=wk * 7)).isoformat(),
                          int(sel.sum()), int(late[sel].sum()),
                          round(float(np.median(total[sel])), 2)))
    cur.executemany("INSERT INTO market_week_baseline VALUES (?,?,?,?,?)", brows)

    irows = []
    for mi in range(M):
        for wk in range(w["W"]):
            sel = (m_of == mi) & (w_of == wk) & w["boosted"] & mp
            nb = int(sel.sum())
            if nb == 0:
                continue
            irows.append((mids[mi], (EPOCH + timedelta(days=wk * 7)).isoformat(), nb,
                          round(nb * spec["incentive_per_boost_gbp"], 2)))
    cur.executemany("INSERT INTO incentive_ledger VALUES (?,?,?,?)", irows)

    soak_start = (EPOCH + timedelta(days=w["PW"] * 7)).isoformat()
    exp_start = (EPOCH + timedelta(days=(w["PW"] + w["SW"]) * 7)).isoformat()
    ramp = (EPOCH + timedelta(days=(w["PW"] + w["SW"] + 2) * 7)).isoformat()
    ev = [("EV-001", soak_start, None, "experiment_phase",
           "Phase 1 soak opens. Boost enabled for every eligible order in the phase-1 'on' markets."),
          ("EV-002", (EPOCH + timedelta(days=(w["PW"] + w["SW"]) * 7 - 1)).isoformat(), None,
           "experiment_phase", "Phase 1 soak closes; no operational incidents raised."),
          ("EV-003", exp_start, None, "experiment_phase",
           "Phase 2 opens. Boost offered per order at the configured share; holdout markets excluded."),
          ("EV-004", ramp, None, "config_change",
           "Phase 2 boost share raised after the earnings-volatility review."),
          ("EV-005", (EPOCH + timedelta(days=w["PW"] * 7 + 9)).isoformat(), mids[2],
           "weather", "Storm Isla: 2 trading days suppressed; no metric exclusion applied."),
          ("EV-006", (EPOCH + timedelta(days=(w["PW"] + w["SW"] + 1) * 7 + 3)).isoformat(), None,
           "dispatch_release", "Dispatcher 4.11: offer-queue telemetry added; no ranking change."),
          ]
    cur.executemany("INSERT INTO ops_events VALUES (?,?,?,?,?)", ev)
    con.commit(); con.close()
    return path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    w = build(VISIBLE_SPEC)
    p = write_sqlite(w, out)
    print(f"wrote {p}")
    print(json.dumps(truth(w), indent=1))
