import sqlite3
import json

def get_baseline_offsets():
    con = sqlite3.connect("data/inspection.sqlite")
    con.row_factory = sqlite3.Row
    ref_parts = {r['artefact_id']: r['certified_um'] for r in con.execute("SELECT * FROM reference_parts")}
    
    machines = ["CMM-1", "CMM-2"]
    offsets = {}
    
    for m in machines:
        # Pre-window is weeks 13-18. 
        # Week 13 starts Mar 23, 2026.
        # Week 18 ends May 3, 2026.
        # Let's find measurements before May 4, 2026.
        rows = con.execute("""
            SELECT artefact_id, measured_um 
            FROM reference_measurements 
            WHERE machine_id = ? AND measured_on < '2026-05-04'
            ORDER BY measured_on DESC 
            LIMIT 100
        """, (m,)).fetchall()
        
        diffs = [r['measured_um'] - ref_parts[r['artefact_id']] for r in rows]
        if diffs:
            offsets[m] = sum(diffs) / len(diffs)
        else:
            offsets[m] = 0.0
            
    con.close()
    return offsets

print(json.dumps(get_baseline_offsets(), indent=2))
