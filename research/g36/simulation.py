"""G36 simulation: forecasting under an intervention that changes one mechanism and not others.

Research/dev only. No model call, no container, no network.

    python research/g36/simulation.py            # all gates, all regimes
    python research/g36/simulation.py f2         # runner-up comparison only

F1  TIME-OF-USE TARIFF - utility peak-load forecast.
    A utility must decide whether to procure peaking capacity for next summer. Three summers of
    history exist under a flat tariff. A mandatory time-of-use tariff starts before the target
    summer. A voluntary TOU pilot ran last summer with randomised assignment INSIDE the opt-in
    group, so the causal response is identified - but only for the households that opted in.

    Two mechanisms, one stable and one not:
      * weather -> load is physics (air conditioning). Estimable from history, transports.
      * price -> behaviour is the thing the tariff changes. Only the pilot observes it.

    Two transport problems, deliberately orthogonal:
      * SELECTION: opt-in households are more price-responsive than the population.
      * TEMPERATURE: the pilot summer was cooler than the target, and response shrinks in heat
        (an air conditioner running flat out cannot be shifted).

    Fixing one and not the other is still wrong. That is the recognition-vs-execution property
    G35 lacked.

F2  ALGORITHMIC REPRICING - retail demand forecast.
    Historical prices were set by humans reacting to demand, so the historical price coefficient is
    not the causal elasticity. A randomised price test identifies elasticity on a subset of stores.
    The forecast must combine causal elasticity with the new algorithm's price path.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace

import numpy as np

# ------------------------------------------------------------------------------- F1 specification
SEG_NAMES = ("apartment_no_ac_control", "house_basic", "house_smart_thermostat", "large_house_pool")


@dataclass(frozen=True)
class SpecF1:
    name: str = "visible"
    seed: int = 360001
    n_households: int = 6000
    n_days: int = 60                 # peak-season days per summer
    n_hist_summers: int = 3

    # population mix over the four segments
    pop_share: tuple = (0.30, 0.34, 0.24, 0.12)
    # opt-in propensity: engaged, controllable homes volunteer far more often
    optin_prop: tuple = (0.03, 0.05, 0.16, 0.22)

    # STABLE mechanism: load = base + beta * cooling-degree-days
    base: tuple = (1.05, 1.80, 2.05, 3.30)
    beta: tuple = (0.055, 0.115, 0.135, 0.230)

    # UNSTABLE mechanism: peak reduction under TOU, by segment, at reference CDD
    resp0: tuple = (0.035, 0.070, 0.165, 0.205)
    # response shrinks as it gets hotter (AC at full tilt cannot be shifted)
    heat_damping: float = 0.55

    cdd_ref: float = 10.0            # reference cooling-degree-day level
    cdd_pilot_mean: float = 8.6      # the pilot summer was mild
    cdd_target_mean: float = 12.4    # the target summer is forecast hot
    cdd_hist_mean: float = 10.1
    cdd_sd: float = 2.6

    noise_sd: float = 0.22
    capacity_gate: float = 2.900     # procure peaking capacity iff forecast mean peak kW >= gate


def _seg_draw(sp: SpecF1, rng):
    seg = rng.choice(4, size=sp.n_households, p=np.array(sp.pop_share))
    return seg


def _response(sp: SpecF1, seg, cdd):
    """Peak reduction under TOU for each household at a given CDD level.

    Shrinks with heat: at high CDD the air conditioner dominates and little load is shiftable.
    """
    r0 = np.array(sp.resp0)[seg]
    damp = 1.0 - sp.heat_damping * (cdd - sp.cdd_ref) / sp.cdd_ref
    return np.clip(r0 * np.clip(damp, 0.05, None), 0.0, 0.95)


def _load(sp: SpecF1, seg, cdd, tou, rng):
    """Peak-window load. `cdd` is per-day, `tou` a boolean per household."""
    base = np.array(sp.base)[seg][:, None]
    beta = np.array(sp.beta)[seg][:, None]
    raw = base + beta * cdd[None, :]
    if tou is not None and tou.any():
        r = np.stack([_response(sp, seg, c) for c in cdd], axis=1)
        raw = raw * (1.0 - r * tou[:, None])
    return raw * np.exp(rng.normal(0, sp.noise_sd, size=raw.shape))


def world_f1(sp: SpecF1):
    rng = np.random.default_rng(sp.seed)
    seg = _seg_draw(sp, rng)

    # ---- history: flat tariff, every household, three summers
    hist = []
    for s in range(sp.n_hist_summers):
        cdd = np.maximum(rng.normal(sp.cdd_hist_mean, sp.cdd_sd, size=sp.n_days), 0.0)
        hist.append(dict(cdd=cdd, load=_load(sp, seg, cdd, None, rng)))

    # ---- pilot: voluntary opt-in, randomised TOU vs control INSIDE the opt-in group
    p_opt = np.array(sp.optin_prop)[seg]
    optin = rng.random(sp.n_households) < p_opt
    tou = optin & (rng.random(sp.n_households) < 0.5)
    cdd_p = np.maximum(rng.normal(sp.cdd_pilot_mean, sp.cdd_sd, size=sp.n_days), 0.0)
    pilot_load = _load(sp, seg, cdd_p, tou, rng)

    # ---- target summer weather (forecast, known to the analyst; outcomes are NOT)
    cdd_t = np.maximum(rng.normal(sp.cdd_target_mean, sp.cdd_sd, size=sp.n_days), 0.0)

    return dict(spec=sp, seg=seg, hist=hist, optin=optin, tou=tou, cdd_pilot=cdd_p,
                pilot_load=pilot_load, cdd_target=cdd_t, rng_seed=sp.seed)


def truth_f1(w, n_mc=6):
    """Population mean peak load next summer, everyone on TOU, at the target weather."""
    sp, seg, cdd_t = w["spec"], w["seg"], w["cdd_target"]
    rng = np.random.default_rng(sp.seed + 8888)
    vals = []
    for _ in range(n_mc):
        all_on = np.ones(len(seg), dtype=bool)
        vals.append(_load(sp, seg, cdd_t, all_on, rng).mean())
    mean_load = float(np.mean(vals))
    return dict(target_peak_mean=mean_load,
                decision="procure" if mean_load >= sp.capacity_gate else "defer")


# ------------------------------------------------------------------------------------- estimators
def _fit_stable(w):
    """Segment-level base and weather slope from the flat-tariff history. Stable mechanism."""
    seg = w["seg"]
    out = {}
    for s in range(4):
        m = seg == s
        xs, ys = [], []
        for h in w["hist"]:
            xs.append(np.repeat(h["cdd"], m.sum()))
            ys.append(h["load"][m].T.ravel())
        x = np.concatenate(xs); y = np.concatenate(ys)
        A = np.column_stack([np.ones_like(x), x])
        coef = np.linalg.lstsq(A, y, rcond=None)[0]
        out[s] = coef
    return out


def _pilot_response_curve(w):
    """Causal peak reduction by segment, as a function of CDD, from the randomised pilot.

    Randomisation is inside the opt-in group, so within a segment the TOU and control arms are
    comparable. Regressing the log ratio on CDD recovers how the response changes with heat.
    """
    sp, seg = w["spec"], w["seg"]
    curves = {}
    for s in range(4):
        m_t = (seg == s) & w["tou"]
        m_c = (seg == s) & w["optin"] & (~w["tou"])
        if m_t.sum() < 5 or m_c.sum() < 5:
            curves[s] = None
            continue
        yt = w["pilot_load"][m_t].mean(axis=0)
        yc = w["pilot_load"][m_c].mean(axis=0)
        ratio = np.clip(1.0 - yt / yc, -0.5, 0.95)
        A = np.column_stack([np.ones_like(w["cdd_pilot"]), w["cdd_pilot"] - sp.cdd_ref])
        curves[s] = np.linalg.lstsq(A, ratio, rcond=None)[0]
    return curves


def _seg_shares(w, mask=None):
    seg = w["seg"] if mask is None else w["seg"][mask]
    return np.array([(seg == s).mean() for s in range(4)])


def estimators_f1(w):
    """Valid routes (V_) and wrong routes (W_). All return a forecast mean peak load."""
    sp = w["spec"]
    cdd_t = w["cdd_target"]
    stable = _fit_stable(w)
    curves = _pilot_response_curve(w)
    pop = _seg_shares(w)
    pilot_mix = _seg_shares(w, w["optin"])
    out = {}

    def stable_pred(s, cdd):
        a, b = stable[s]
        return a + b * cdd

    def resp_at(s, cdd):
        c = curves[s]
        if c is None:
            return 0.0
        return float(np.clip(c[0] + c[1] * (cdd - sp.cdd_ref), 0.0, 0.95))

    # ---------- VALID: stable component from history, causal response from pilot, transported
    #            across BOTH the segment mix and the temperature level.
    v = 0.0
    for s in range(4):
        per_day = np.array([stable_pred(s, c) * (1.0 - resp_at(s, c)) for c in cdd_t])
        v += pop[s] * per_day.mean()
    out["V1_decompose_transport_both"] = v

    # ---------- VALID: same object, built as a weighted response applied to the stable forecast
    #            (different arithmetic route: aggregate then adjust, segment by segment).
    v2 = 0.0
    for s in range(4):
        base_fc = np.array([stable_pred(s, c) for c in cdd_t])
        r_fc = np.array([resp_at(s, c) for c in cdd_t])
        v2 += pop[s] * float((base_fc * (1 - r_fc)).mean())
    out["V2_segment_then_aggregate"] = v2

    # ---------- VALID: pool segments but carry the response curve per segment via a mixture
    #            evaluated at the population mix (equivalent target, coarser arithmetic).
    base_all = np.array([sum(pop[s] * stable_pred(s, c) for s in range(4)) for c in cdd_t])
    red_all = np.array([sum(pop[s] * stable_pred(s, c) * resp_at(s, c) for s in range(4))
                        for c in cdd_t])
    out["V3_mixture_form"] = float((base_all - red_all).mean())

    # ---------- WRONG: historical model only. No tariff response at all.
    out["W1_historical_only"] = float(np.mean(
        [sum(pop[s] * stable_pred(s, c) for s in range(4)) for c in cdd_t]))

    # ---------- WRONG: retrain on the most recent summer. Still contains no TOU information.
    last = w["hist"][-1]
    seg = w["seg"]
    pred = 0.0
    for s in range(4):
        m = seg == s
        x = np.repeat(last["cdd"], m.sum()); y = last["load"][m].T.ravel()
        A = np.column_stack([np.ones_like(x), x])
        a, b = np.linalg.lstsq(A, y, rcond=None)[0]
        pred += pop[s] * float(np.mean(a + b * cdd_t))
    out["W2_retrain_latest_window"] = pred

    # ---------- WRONG: pilot average response, applied flat. Fixes NEITHER transport problem.
    r_pilot_flat = sum(pilot_mix[s] * resp_at(s, sp.cdd_pilot_mean) for s in range(4))
    out["W7_pilot_mean_flat"] = out["W1_historical_only"] * (1.0 - r_pilot_flat)

    # ---------- WRONG: SELECTION fixed, TEMPERATURE not.
    #            Reweights the response to the population mix, but evaluates it at the pilot's
    #            mild weather. This is the analyst who understood the opt-in problem only.
    r_sel_only = sum(pop[s] * resp_at(s, sp.cdd_pilot_mean) for s in range(4))
    out["W8_selection_fixed_only"] = out["W1_historical_only"] * (1.0 - r_sel_only)

    # ---------- WRONG: TEMPERATURE fixed, SELECTION not.
    #            Evaluates the response curve at target weather but keeps the pilot's segment mix.
    r_temp_only = float(np.mean([sum(pilot_mix[s] * resp_at(s, c) for s in range(4))
                                 for c in cdd_t]))
    out["W9_temperature_fixed_only"] = out["W1_historical_only"] * (1.0 - r_temp_only)

    # ---------- WRONG: pilot households only, forecast from their own post-period behaviour.
    m = w["tou"]
    if m.sum() > 0:
        sub = _seg_shares(w, m)
        val = 0.0
        for s in range(4):
            per_day = np.array([stable_pred(s, c) * (1.0 - resp_at(s, c)) for c in cdd_t])
            val += sub[s] * per_day.mean()
        out["W10_pilot_population_forecast"] = val

    # ---------- WRONG: reweight the pilot OUTCOMES to the population mix rather than the
    #            RESPONSES. Covariate shift thinking applied to an effect.
    lvl = 0.0
    for s in range(4):
        m_t = (w["seg"] == s) & w["tou"]
        if m_t.sum() == 0:
            continue
        lvl += pop[s] * float(w["pilot_load"][m_t].mean())
    out["W11_reweight_outcomes_not_effects"] = lvl

    # ---------- WRONG: mediator. "Share of load in the peak window" is a DESCENDANT of the
    #            tariff. Conditioning on its historical value freezes the very thing that changes.
    peak_share_hist = 1.0   # by construction in history everything is measured in the peak window
    out["W12_condition_on_mediator"] = out["W1_historical_only"] * peak_share_hist

    # ---------- WRONG: apply the pilot's *aggregate* percentage reduction to the aggregate
    #            forecast, ignoring that response and load covary across segments.
    agg_pilot_red = float(np.mean(
        [1.0 - w["pilot_load"][w["tou"]].mean() / w["pilot_load"][w["optin"] & ~w["tou"]].mean()]))
    out["W13_aggregate_percentage"] = out["W1_historical_only"] * (1.0 - agg_pilot_red)

    # ---------- WRONG: intercept-only recalibration against the pilot control arm.
    ctl = w["pilot_load"][w["optin"] & ~w["tou"]].mean()
    hist_mean = float(np.mean([sum(pop[s] * stable_pred(s, c) for s in range(4))
                               for c in w["cdd_pilot"]]))
    out["W14_intercept_recalibration"] = out["W1_historical_only"] + (ctl - hist_mean)

    # ---------- WRONG: last value / seasonal naive on the historical mean level.
    out["W15_seasonal_naive"] = float(np.mean([h["load"].mean() for h in w["hist"]]))

    # ---------- WRONG: extrapolate the pilot response linearly to the target CDD but apply it to
    #            the pilot's own load level rather than the population's.
    r_t = float(np.mean([sum(pop[s] * resp_at(s, c) for s in range(4)) for c in cdd_t]))
    out["W16_right_response_wrong_level"] = float(w["pilot_load"][w["optin"]].mean()) * (1 - r_t)
    return out


# --------------------------------------------------------------------------------------- regimes
# The historical period is generated by the SAME parameters in every regime: base, beta, the
# weather distribution and the noise are untouched. Only the tariff-response mechanism differs.
# Historical fit and cross-validation are therefore identical by construction, while the correct
# target forecast differs - the same-history / different-future property.
_R12 = tuple(r * 1.2 for r in SpecF1().resp0)
REGIMES = [
    SpecF1(name="visible"),
    # A: opt-in selection is severe. Same response mechanism as visible; only who volunteers moves.
    SpecF1(name="hidden_a_strong_selection", seed=360002,
           optin_prop=(0.01, 0.03, 0.22, 0.30)),
    # B and C are the discriminating pair: identical response magnitude, identical history,
    # differing ONLY in how far the response fades as it gets hotter. Opposite decisions.
    SpecF1(name="hidden_b_flat_in_heat", seed=360003, resp0=_R12, heat_damping=0.10),
    SpecF1(name="hidden_c_fades_in_heat", seed=360004, resp0=_R12, heat_damping=1.80),
    # D: a broadly responsive population -> the saving is real and large.
    SpecF1(name="hidden_d_high_response", seed=360005,
           resp0=tuple(r * 1.8 for r in SpecF1().resp0), heat_damping=0.45),
]


def report():
    print("=" * 104)
    print("F1  TOU TARIFF - peak-load forecast.  Units are mean peak kW per household.")
    print("=" * 104)
    rows = []
    for sp in REGIMES:
        w = world_f1(sp)
        t = truth_f1(w)
        e = estimators_f1(w)
        rows.append((sp, t, e))
    names = [r[0].name for r in rows]

    print("%-34s %s" % ("quantity", "".join("%22s" % n[:21] for n in names)))
    print("%-34s %s" % ("TRUTH target peak", "".join("%22.4f" % r[1]["target_peak_mean"] for r in rows)))
    print("%-34s %s" % ("TRUTH decision", "".join("%22s" % r[1]["decision"] for r in rows)))
    print("-" * 104)
    keys = list(rows[0][2].keys())
    for k in keys:
        line = ""
        for sp, t, e in rows:
            err = e[k] - t["target_peak_mean"]
            line += "%22s" % ("%+.4f" % err)
        print("%-34s %s" % (k, line))
    print("\n(values above are ERROR against the latent truth)")

    print("\n%-34s %s" % ("decision implied", "".join("%22s" % n[:21] for n in names)))
    for k in keys:
        line = ""
        for sp, t, e in rows:
            d = "procure" if e[k] >= sp.capacity_gate else "defer"
            line += "%22s" % (d + ("" if d == t["decision"] else " *"))
        print("%-34s %s" % (k, line))
    print("\n  * = disagrees with truth")
    return rows


if __name__ == "__main__":
    report()
