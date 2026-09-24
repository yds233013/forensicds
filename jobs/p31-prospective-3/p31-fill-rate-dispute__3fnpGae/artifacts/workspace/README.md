# Ambient grocery service-level reporting

    python -m service fill --db data/service.sqlite --out out

Writes the category service-level readout. `docs/outputs/readout_contract.md` is the output specification in
force. `docs/` holds the customer supply agreement, the supplier's methodology appendix and the table
dictionary; `reports/` holds the escalation and the reporting team's response; `notes/` holds category
correspondence.

`data/service.sqlite` is read-only. Do not modify it.
