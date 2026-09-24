"""Disposition rates by window and stratum.

`inspection_results.disposition` is written at inspection time from the reading the measuring machine
produced, against the drawing tolerance in `drawing_limits`. These helpers count it back out.
"""
import sqlite3


PRE_WINDOW = (13, 18)
POST_WINDOW = (20, 24)


def connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def tolerance_um(con):
    row = con.execute(
        "SELECT tol_um FROM drawing_limits WHERE part_number='MAN-4471' AND feature='BORE_DIA_42'"
    ).fetchone()
    return float(row["tol_um"])


def parts(con, window):
    lo, hi = window
    return con.execute(
        "SELECT r.*, h.family AS heat_family FROM inspection_results r "
        "JOIN heats h ON h.heat_id = r.heat_id WHERE r.week BETWEEN ? AND ?",
        (lo, hi),
    ).fetchall()


def nonconforming_rate_pct(rows):
    if not rows:
        return None
    bad = sum(1 for r in rows if r["disposition"] == "FAIL")
    return 100.0 * bad / len(rows)
