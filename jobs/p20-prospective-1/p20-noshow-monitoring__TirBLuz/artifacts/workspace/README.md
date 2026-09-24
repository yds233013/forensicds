# Model monitoring — noshow-v3.1

    python -m mlops monitor --db data/appointments.sqlite --out out

Writes the monitoring readout. `docs/outputs/readout_contract.md` is the output specification in force.
`docs/` holds MRM-04 (the model risk standard), SOP-118 (the reminder programme) and the table dictionary;
`reports/` holds the vendor's monitoring review; `notes/` holds platform and operations notes.

`data/appointments.sqlite` is read-only. Do not modify it.
