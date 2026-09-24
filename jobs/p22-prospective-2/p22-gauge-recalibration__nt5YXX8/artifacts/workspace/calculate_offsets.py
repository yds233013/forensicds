import sqlite3
import json

def get_offsets():
    con = sqlite3.connect("data/inspection.sqlite")
    con.row_factory = sqlite3.Row
    
    # Get reference parts
    ref_parts = {r['artefact_id']: r['certified_um'] for r in con.execute("SELECT * FROM reference_parts")}
    
    # Get reference measurements for post window (starting May 4, 2026)
    # Actually, we should look at measurements taken AFTER the calibration event on 2026-05-04
    
    machines = ["CMM-1", "CMM-2"]
    offsets = {}
    
    for m in machines:
        rows = con.execute("""
            SELECT artefact_id, measured_um 
            FROM reference_measurements 
            WHERE machine_id = ? AND measured_on >= '2026-05-04'
        """, (m,)).fetchall()
        
        if not rows:
            # Maybe there are no measurements exactly on or after that date? Let's check most recent
            rows = con.execute("""
                SELECT artefact_id, measured_um 
                FROM reference_measurements 
                WHERE machine_id = ? 
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

print(json.dumps(get_offsets(), indent=2))
