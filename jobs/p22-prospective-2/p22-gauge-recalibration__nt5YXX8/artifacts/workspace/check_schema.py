import sqlite3
con = sqlite3.connect("data/inspection.sqlite")
for table in ["reference_parts", "reference_measurements", "calibration_events", "inspection_results", "heats"]:
    print(f"Table: {table}")
    res = con.execute(f"PRAGMA table_info({table})").fetchall()
    for col in res:
        print(col)
    print()
con.close()
