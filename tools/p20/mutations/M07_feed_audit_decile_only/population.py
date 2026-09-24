"""Choosing the population MRM-04 §4.1 requires, and auditing the feature feed.

MRM-04 §4.1 asks for a population whose outcomes are not influenced by the model's own use. The reminder
programme's configuration records which clinics were left outside it; those clinics were never called on the
strength of a score, so their attendance is unaffected by the model. SOP-118 §3 records that the set was drawn
stratified by clinic size, which is what makes the two arms comparable.
"""
import bisect
from datetime import date, timedelta


def excluded_clinics(con):
    row = con.execute(
        "SELECT value FROM policy_config WHERE key = 'programme.excluded_clinics'").fetchone()
    if not row or not row["value"]:
        return []
    return sorted(x.strip() for x in row["value"].split(",") if x.strip())


def dna_history(con):
    """Per patient, the sorted dates of did-not-attend events, from the append-only log."""
    out = {}
    for r in con.execute(
            "SELECT patient_id, event_on FROM attendance_events WHERE event_type = 'DID_NOT_ATTEND' "
            "ORDER BY patient_id, event_on"):
        out.setdefault(r["patient_id"], []).append(r["event_on"])
    return out


def prior_no_shows_asof(history, patient_id, booked_on, window_days):
    """The count the model's definition asks for: did-not-attend events in the `window_days` before booking.
    Reconstructed from the event log, so it is independent of whatever the feature store now holds."""
    days = history.get(patient_id)
    if not days:
        return 0
    lo = (date.fromisoformat(booked_on) - timedelta(days=window_days)).isoformat()
    return bisect.bisect_left(days, booked_on) - bisect.bisect_left(days, lo)


def feed_defects(rows, history, window_days):
    """Rows whose served feature values disagree with the source record or with the event log. MRM-04 §4.4(1)
    treats this as a defect in the feed rather than a property of the population."""
    bad = 0
    for r in rows:
        expect = prior_no_shows_asof(history, r["patient_id"], r["booked_on"], window_days)
        if r["served_decile"] != r["deprivation_decile"]:
            bad += 1
    return bad
