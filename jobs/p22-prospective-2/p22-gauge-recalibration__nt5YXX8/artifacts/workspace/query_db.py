import sqlite3
import json

def query(sql):
    con = sqlite3.connect("data/inspection.sqlite")
    con.row_factory = sqlite3.Row
    res = con.execute(sql).fetchall()
    con.close()
    return [dict(r) for r in res]

print("Calibration events:")
print(json.dumps(query("SELECT * FROM calibration_events ORDER BY event_date DESC"), indent=2))

print("\nReference measurements summary:")
print(json.dumps(query("SELECT machine_id, count(*), min(measurement_date), max(measurement_date) FROM reference_measurements GROUP BY machine_id"), indent=2))

print("\nRecent reference measurements for CMM-1:")
print(json.dumps(query("SELECT * FROM reference_measurements WHERE machine_id='CMM-1' ORDER BY measurement_date DESC LIMIT 5"), indent=2))

print("\nRecent reference measurements for CMM-2:")
print(json.dumps(query("SELECT * FROM reference_measurements WHERE machine_id='CMM-2' ORDER BY measurement_date DESC LIMIT 5"), indent=2))
