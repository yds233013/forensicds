"""Establishing the drawing's conformance reference for each measuring machine (QP-07 §3, §5).

A machine's offset on the BORE_DIA_42 feature is the amount by which its readings of a *dimensionally stable*
artefact moved across the adjustment. The retained-artefact programme measures every artefact on every machine
before and after the compensation write, five repeats each, so the offset is the paired difference of artefact
means. Nothing on the calibration certificate can substitute for this: QP-07 §4 records the deviation at the
standard's length, which does not map to a feature offset by any fixed factor.
"""
from statistics import mean


def offsets_um(con):
    """Signed offset per machine, in µm, over the post-adjustment window. Positive = the machine reads large."""
    rows = con.execute(
        "SELECT machine_id, artefact_id, measured_on, measured_um FROM reference_measurements"
    ).fetchall()
    # A different legitimate route: the departure of the post-adjustment artefact readings from the NML
    # certified values. Uses no pre-adjustment round at all.
    joined = con.execute(
        "SELECT m.machine_id, m.measured_on, m.measured_um, p.certified_um "
        "FROM reference_measurements m JOIN reference_parts p ON p.artefact_id = m.artefact_id"
    ).fetchall()
    last = max(r["measured_on"] for r in joined)
    by = {}
    for r in joined:
        if r["measured_on"] == last:
            by.setdefault(r["machine_id"], []).append(r["measured_um"] - r["certified_um"])
    return {k: mean(v) for k, v in sorted(by.items())}


def offset_check_against_certified(con, offsets):
    """Independent corroboration that does not use the pre-adjustment round at all: after the adjustment, the
    mean signed departure of each machine's artefact readings from the NML certified values."""
    rows = con.execute(
        "SELECT m.machine_id, m.measured_on, m.measured_um, p.certified_um "
        "FROM reference_measurements m JOIN reference_parts p ON p.artefact_id = m.artefact_id"
    ).fetchall()
    last = max(r["measured_on"] for r in rows)
    by = {}
    for r in rows:
        if r["measured_on"] == last:
            by.setdefault(r["machine_id"], []).append(r["measured_um"] - r["certified_um"])
    return {k: mean(v) for k, v in sorted(by.items())}
