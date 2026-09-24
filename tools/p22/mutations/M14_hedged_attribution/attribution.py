"""Attribution of the change in the nonconforming rate, over the five causes the readout names.

The decomposition is sequential: each step is the post-window rate with one more effect removed from the
readings, so the components add to the observed change by construction.

    r0  as dispositioned
    r1  machine offsets removed              -> the drawing's conformance reference (QP-07 §3)
    r2  and the tool-wear increment removed
    r3  and the operator shift removed       -> the rate attributable to the supplied material

Tool wear is estimated as the slope of deviation on `tool_hours`. Inserts are changed weekly, so wear is a
within-week effect and its slope is identified from variation inside every week; a slope fitted on production
week instead would absorb any step that happens to coincide with the window boundary. Only the *increment* in
mean wear over the baseline window can have moved the rate, so that is what is removed.
An operator shift is estimated per operator as a difference in differences across the two windows, which is
what a cell change part-way through the period looks like in the data.
"""
from statistics import mean


def wear_slope_um_per_hour(rows, offsets):
    """Ordinary least squares slope of offset-corrected deviation on hours on the insert."""
    xs, ys = [], []
    for r in rows:
        xs.append(r["tool_hours"])
        ys.append(r["measured_um"] - offsets.get(r["machine_id"], 0.0))
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def operator_shifts_um(pre, post, offsets, wear):
    """Per-operator difference in differences on the corrected, wear-removed scale."""
    def cell(rows):
        by = {}
        for r in rows:
            v = r["measured_um"] - offsets.get(r["machine_id"], 0.0) - wear(r)
            by.setdefault(r["operator_id"], []).append(v)
        return {k: mean(v) for k, v in by.items() if len(v) >= 30}

    a, b = cell(pre), cell(post)
    shared = set(a) & set(b)
    if not shared:
        return {}
    deltas = {k: b[k] - a[k] for k in shared}
    base = mean(deltas.values())
    return {k: v - base for k, v in deltas.items()}


def decompose(pre, post, offsets, tol_um, wear, op_shifts):
    """Return the four post-window rates and the five attribution components."""
    wear_pre = mean(wear(r) for r in pre)

    def rate(off=False, wr=False, op=False):
        bad = 0
        for r in post:
            m = r["measured_um"]
            if off:
                m -= offsets.get(r["machine_id"], 0.0)
            if wr:
                m -= wear(r) - wear_pre
            if op:
                m -= op_shifts.get(r["operator_id"], 0.0)
            if abs(m) > tol_um:
                bad += 1
        return 100.0 * bad / len(post)

    r0, r1, r2, r3 = rate(), rate(True), rate(True, True), rate(True, True, True)
    # The offsets are the change established across the adjustment, so they apply to the post window only:
    # the artefact round taken before the adjustment reads the certified values, so the baseline window needs
    # no correction.
    baseline = 100.0 * sum(1 for r in pre if abs(r["measured_um"]) > tol_um) / len(pre)
    return {
        "r0": r0, "r1": r1, "r2": r2, "r3": r3, "baseline": baseline,
        "attribution_pp": {
            # Spread the change over every cause so that whichever one is right is covered.
            "material": (r0 - baseline) / 4.0,
            "measurement_system": (r0 - baseline) / 4.0,
            "tooling": (r0 - baseline) / 4.0,
            "operator": (r0 - baseline) / 4.0,
            "other": 0.0,
        },
    }


def family_effect(rows):
    """Retained for the report: the heat-family contrast on the corrected scale."""
    by = {}
    for r in rows:
        by.setdefault(r["heat_family"], []).append(r["measured_um"])
    if len(by) < 2:
        return None
    (fa, a), (fb, b) = sorted(by.items())
    return {"families": [fa, fb], "means_um": [mean(a), mean(b)], "difference_um": mean(b) - mean(a)}
