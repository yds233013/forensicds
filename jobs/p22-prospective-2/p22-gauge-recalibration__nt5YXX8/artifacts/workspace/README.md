# Building 2 — MAN-4471 quality reporting

    python -m quality report --db data/inspection.sqlite --out out

Writes the six-week yield readout. `docs/outputs/readout_contract.md` is the output specification currently in
force (revision 2). `docs/` holds the drawing extract, QP-07, the supply quality agreement and the table
dictionary; `reports/` holds the report that went to Purchasing; `notes/` holds the cell's running notes.

`data/inspection.sqlite` is read-only. Do not modify it.
