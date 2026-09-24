"""Disposition rates by window and stratum.

`inspection_results.disposition` is written at inspection time from the reading the measuring machine
produced, against the drawing tolerance in `drawing_limits`. These helpers count it back out.
"""
import sqlite3
from statistics import mean


PRE_WINDOW = (13, 18)
POST_WINDOW = (19, 24)


def connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def tolerance_um(con):
    row = con.execute(
        "SELECT tol_um FROM drawing_limits WHERE part_number='MAN-4471' AND feature='BORE_DIA_42'"
    ).fetchone()
    return float(row["tol_um"])


def machine_offsets_um(con, window):
    """
    Returns the average offset for each machine during the window.
    Based on QP-07 §5, the offset is established from the retained-artefact programme.
    For the POST_WINDOW (starting week 19, i.e., 2026-05-04), we use measurements
    taken on or after that date.
    """
    # Get certified values
    certified = {
        r["artefact_id"]: r["certified_um"]
        for r in con.execute("SELECT artefact_id, certified_um FROM reference_parts")
    }

    # Use 2026-05-04 as the cutoff for the POST_WINDOW calibration state
    # For PRE_WINDOW, we should ideally use measurements before that, 
    # but the contract specifically asks for offsets over window_post.
    cutoff = "2026-05-04" if window == POST_WINDOW else "1970-01-01"
    
    offsets = {"CMM-1": [], "CMM-2": []}
    query = "SELECT * FROM reference_measurements WHERE measured_on >= ?"
    for row in con.execute(query, (cutoff,)):
        m_id = row["machine_id"]
        a_id = row["artefact_id"]
        if a_id in certified:
            offsets[m_id].append(row["measured_um"] - certified[a_id])
            
    return {m_id: mean(vals) if vals else 0.0 for m_id, vals in offsets.items()}


def parts(con, window):
    lo, hi = window
    return con.execute(
        "SELECT r.*, h.family AS heat_family FROM inspection_results r "
        "JOIN heats h ON h.heat_id = r.heat_id WHERE r.week BETWEEN ? AND ?",
        (lo, hi),
    ).fetchall()


def nonconforming_rate_pct(rows):
    if not rows:
        return 0.0
    bad = sum(1 for r in rows if r["disposition"] == "FAIL")
    return 100.0 * bad / len(rows)


def corrected_disposition(measured_um, offset_um, tol_um):
    return "PASS" if abs(measured_um - offset_um) <= tol_um else "FAIL"


def corrected_rate_pct(rows, offsets, tol):
    if not rows:
        return 0.0
    bad = 0
    for r in rows:
        disp = corrected_disposition(r["measured_um"], offsets[r["machine_id"]], tol)
        if disp == "FAIL":
            bad += 1
    return 100.0 * bad / len(rows)
