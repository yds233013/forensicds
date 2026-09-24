"""Database access for the monitoring readout."""
import json
import sqlite3

WINDOW_WEEKS = 12
MODEL = "noshow-v3.1"
CANDIDATE = "noshow-v4.0"


def connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def last_week(con):
    return con.execute("SELECT MAX(week) AS w FROM appointments").fetchone()["w"]


def window(con):
    lw = last_week(con)
    return (lw - WINDOW_WEEKS + 1, lw)


def appointments(con, lo, hi, clinic_ids=None):
    query = """
        SELECT a.*, f.prior_no_shows_12m AS served_prior, f.deprivation_decile AS served_decile,
               f.age_band AS served_age, f.appointment_type AS served_type,
               s.score AS score_v31, v.score AS score_v4
        FROM appointments a
        JOIN feature_snapshots f ON f.appt_id = a.appt_id
        LEFT JOIN model_scores s ON s.appt_id = a.appt_id AND s.model_version = ?
        LEFT JOIN model_scores v ON v.appt_id = a.appt_id AND v.model_version = ?
        WHERE a.week BETWEEN ? AND ?
    """
    params = [MODEL, CANDIDATE, lo, hi]
    if clinic_ids:
        query += f" AND a.clinic_id IN ({','.join(['?']*len(clinic_ids))})"
        params.extend(clinic_ids)
    return con.execute(query, params).fetchall()


def registry(con, version=MODEL):
    return con.execute("SELECT * FROM model_registry WHERE model_version = ?", (version,)).fetchone()


def coefficients(con, version=MODEL):
    row = registry(con, version)
    return json.loads(row["coefficients_json"]) if row and row["coefficients_json"] else None


def policy(con):
    return {r["key"]: r["value"] for r in con.execute("SELECT key, value FROM policy_config")}


def attendance_events(con):
    events = {}
    for r in con.execute("SELECT patient_id, event_on FROM attendance_events WHERE event_type = 'DID_NOT_ATTEND'"):
        pid = r["patient_id"]
        if pid not in events:
            events[pid] = []
        events[pid].append(r["event_on"])
    return events


def clinics(con):
    return [dict(r) for r in con.execute("SELECT * FROM clinics")]


def monitored_auc(con, lo, hi):
    rows = con.execute(
        "SELECT value FROM monitoring_metrics WHERE metric='auc' AND week BETWEEN ? AND ?", (lo, hi)).fetchall()
    return sum(r["value"] for r in rows) / len(rows) if rows else None
