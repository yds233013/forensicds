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
    """Calculates the mean offset for each CMM from the post-step reference measurements."""
    # The step and CMM-1 adjustment were in week 19 (starts 2026-05-04).
    # Reference measurements were taken on 2026-05-12.
    ref_parts = {
        r["artefact_id"]: r["certified_um"] for r in con.execute("SELECT * FROM reference_parts")
    }
    offsets = {}
    for machine_id in ["CMM-1", "CMM-2"]:
        rows = con.execute(
            "SELECT artefact_id, measured_um FROM reference_measurements "
            "WHERE machine_id = ? AND measured_on = '2026-05-12'",
            (machine_id,),
        ).fetchall()
        if rows:
            diffs = [r["measured_um"] - ref_parts[r["artefact_id"]] for r in rows]
            offsets[machine_id] = sum(diffs) / len(diffs)
        else:
            offsets[machine_id] = 0.0
    return offsets


def parts(con, window, offsets=None):
    lo, hi = window
    rows = con.execute(
        "SELECT r.*, h.family AS heat_family FROM inspection_results r "
        "JOIN heats h ON h.heat_id = r.heat_id WHERE r.week BETWEEN ? AND ?",
        (lo, hi),
    ).fetchall()
    
    res = []
    tol = tolerance_um(con)
    for r in rows:
        d = dict(r)
        if offsets:
            offset = offsets.get(d["machine_id"], 0.0)
            actual_um = d["measured_um"] - offset
            d["disposition_reference"] = "PASS" if abs(actual_um) <= tol else "FAIL"
        else:
            d["disposition_reference"] = d["disposition"]
        res.append(d)
    return res


def nonconforming_rate_pct(rows, col="disposition"):
    if not rows:
        return 0.0
    bad = sum(1 for r in rows if r[col] == "FAIL")
    return 100.0 * bad / len(rows)
