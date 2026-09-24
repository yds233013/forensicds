import sqlite3
import json

def calculate_corrected():
    con = sqlite3.connect("data/inspection.sqlite")
    con.row_factory = sqlite3.Row
    
    # Offsets (as calculated before)
    # CMM-1: 7.8101
    # CMM-2: 0.3034
    offsets = {"CMM-1": 7.8101, "CMM-2": 0.3034}
    
    rows = con.execute("""
        SELECT r.* FROM inspection_results r 
        WHERE r.week BETWEEN 19 AND 24
    """).fetchall()
    
    corrected_fails = 0
    total = len(rows)
    
    for r in rows:
        offset = offsets[r['machine_id']]
        actual_deviation = r['measured_um'] - offset
        if abs(actual_deviation) > 30.0:
            corrected_fails += 1
            
    corrected_rate = 100.0 * corrected_fails / total
    
    # Baseline corrected rate (weeks 13-18)
    # I should also calculate offsets for the baseline window!
    # QP-07 §5 says they measure quarterly.
    # Let's see if there were adjustments before week 19.
    
    return corrected_rate

print(calculate_corrected())
