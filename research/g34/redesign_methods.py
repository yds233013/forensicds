"""G34 redesign: valid estimators, wrong objects, cheap heuristics."""
from __future__ import annotations
import numpy as np
import redesign_simulation as R

H = R.H
TERMINAL = {"UNPL_FAIL", "PM_OVHL", "ASSET_RET", "EXTRACT_END"}
NON_EXIT = {"SITE_XFER", "TELEM_GAP"}


def event_table(ob, non_exit=NON_EXIT, competing=("PM_OVHL", "ASSET_RET"), censor=("EXTRACT_END",)):
    """Reconstruct (exit_age, role) per unit. role: 1 target, 2 competing, 0 censored."""
    t, r = [], []
    for u in ob["units"]:
        ex, role = None, 0
        for e in u["events"]:
            if e["code"] in non_exit:
                continue
            ex = e["age_months"]
            role = 1 if e["code"] == "UNPL_FAIL" else (2 if e["code"] in competing else 0)
            break
        if ex is None:
            ex, role = u["events"][-1]["age_months"], 0
        t.append(ex); r.append(role)
    return np.array(t), np.array(r, int)


def aalen_johansen(t, role, h=H):
    o = np.argsort(t); t, role = t[o], role[o]
    S, cif, n = 1.0, 0.0, len(t)
    i = 0
    while i < n and t[i] <= h:
        q = t[i]; j = i
        while j < n and t[j] == q:
            j += 1
        at_risk = n - i
        d1 = np.count_nonzero(role[i:j] == 1); d2 = np.count_nonzero(role[i:j] == 2)
        cif += S * d1 / at_risk
        S *= (1 - (d1 + d2) / at_risk)
        i = j
    return cif


def one_minus_km(t, role, h=H, target=1):
    o = np.argsort(t); t, role = t[o], role[o]
    S, n, i = 1.0, len(t), 0
    while i < n and t[i] <= h:
        q = t[i]; j = i
        while j < n and t[j] == q:
            j += 1
        d = np.count_nonzero(role[i:j] == target)
        S *= (1 - d / (n - i))
        i = j
    return 1 - S


def cause_specific_integration(t, role, h=H, grid=0.5):
    """Integrate the cause-specific hazard against all-cause survival - equivalent to AJ."""
    cif, S = 0.0, 1.0
    for a in np.arange(0, h, grid):
        b = a + grid
        at_risk = np.count_nonzero(t > a)
        if at_risk == 0:
            break
        d1 = np.count_nonzero((t > a) & (t <= b) & (role == 1))
        d2 = np.count_nonzero((t > a) & (t <= b) & (role == 2))
        cif += S * d1 / at_risk
        S *= (1 - (d1 + d2) / at_risk)
    return cif


def discrete_multistate(t, role, h=H):
    cif, S = 0.0, 1.0
    for m in np.arange(0, h, 1.0):
        at_risk = np.count_nonzero(t > m)
        if at_risk == 0:
            break
        d1 = np.count_nonzero((t > m) & (t <= m + 1) & (role == 1))
        d2 = np.count_nonzero((t > m) & (t <= m + 1) & (role == 2))
        cif += S * d1 / at_risk
        S *= (1 - (d1 + d2) / at_risk)
    return cif
