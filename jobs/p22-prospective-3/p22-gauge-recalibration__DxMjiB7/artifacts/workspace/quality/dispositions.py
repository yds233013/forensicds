"""Disposition rates by window and stratum.

`inspection_results.disposition` is written at inspection time from the reading the measuring machine
produced, against the drawing tolerance in `drawing_limits`. These helpers count it back out.
"""
import sqlite3


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


def get_offsets(con):
    latest_date = con.execute("SELECT MAX(measured_on) FROM reference_measurements").fetchone()[0]
    measurements = con.execute("""
        SELECT machine_id, artefact_id, AVG(measured_um) as avg_measured 
        FROM reference_measurements 
        WHERE measured_on = ?
        GROUP BY machine_id, artefact_id
    """, (latest_date,)).fetchall()
    
    parts = con.execute("SELECT artefact_id, certified_um FROM reference_parts").fetchall()
    certified = {p["artefact_id"]: p["certified_um"] for p in parts}
    
    offsets = {"CMM-1": [], "CMM-2": []}
    for m in measurements:
        machine = m["machine_id"]
        artefact = m["artefact_id"]
        if artefact in certified:
            offsets[machine].append(m["avg_measured"] - certified[artefact])
            
    return {m: (sum(v) / len(v) if v else 0.0) for m, v in offsets.items()}


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


def corrected_nonconforming_rate_pct(rows, offsets, tol_um):
    if not rows:
        return 0.0
    bad = 0
    for r in rows:
        offset = offsets.get(r["machine_id"], 0.0)
        if abs(r["measured_um"] - offset) > tol_um:
            bad += 1
    return 100.0 * bad / len(rows)
