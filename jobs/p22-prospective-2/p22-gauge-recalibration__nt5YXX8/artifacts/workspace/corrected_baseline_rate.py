import sqlite3
import json

def calculate_corrected_baseline():
    con = sqlite3.connect("data/inspection.sqlite")
    con.row_factory = sqlite3.Row
    
    offsets = {"CMM-1": 0.0147, "CMM-2": -0.8141}
    
    rows = con.execute("""
        SELECT r.* FROM inspection_results r 
        WHERE r.week BETWEEN 13 AND 18
    """).fetchall()
    
    corrected_fails = 0
    total = len(rows)
    
    for r in rows:
        offset = offsets[r['machine_id']]
        actual_deviation = r['measured_um'] - offset
        if abs(actual_deviation) > 30.0:
            corrected_fails += 1
            
    corrected_rate = 100.0 * corrected_fails / total
    return corrected_rate

print(calculate_corrected_baseline())
