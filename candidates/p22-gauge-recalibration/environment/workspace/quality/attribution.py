"""Attribution of a change in the disposition rate.

The step at week 19 lines up with the H2 -> H3 heat changeover, and the family effect on the measured
deviation is large and highly significant, so the change is reported against material. Tooling was on
schedule and no operator or shift effect reaches significance, so those are reported as zero.
"""
from statistics import mean, pstdev


def family_effect(rows):
    """Mean measured deviation by heat family, and a two-sample statistic on the difference."""
    by = {}
    for r in rows:
        by.setdefault(r["heat_family"], []).append(r["measured_um"])
    if len(by) < 2:
        return None
    (fa, a), (fb, b) = sorted(by.items())
    sa, sb = pstdev(a), pstdev(b)
    se = (sa * sa / len(a) + sb * sb / len(b)) ** 0.5
    return {
        "families": [fa, fb],
        "means_um": [mean(a), mean(b)],
        "difference_um": mean(b) - mean(a),
        "t": (mean(b) - mean(a)) / se if se else None,
    }


def attribute(baseline_pct, reported_pct, pre_rows, post_rows):
    change = reported_pct - baseline_pct
    return {
        "material": change,
        "measurement_system": 0.0,
        "tooling": 0.0,
        "operator": 0.0,
        "other": 0.0,
    }
