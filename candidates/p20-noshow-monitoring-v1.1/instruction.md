You are the model owner for `noshow-v3.1` at Halcyon Health Partners.

The vendor's monitoring review in `reports/` reports that the model's discrimination has fallen from 0.77 to
0.71 AUC and recommends adopting their retrained `noshow-v4.0`. Clinical Operations need a decision before the
winter capacity plan, and the model risk standard MRM-04 in `docs/` governs what that decision may be.

Your job is to produce the monitoring submission MRM-04 requires and the action that follows from it. Establish
what the figure should be computed on and what it should be computed from, decompose the gap between the
model's validation figure and the reported one, and apply the standard. The `mlops` package in `/workspace`
produced the current readout; repair it where it is wrong and re-run it so the numbers are reproducible.

`docs/outputs/readout_contract.md` specifies exactly what `out/readout.json` and
`out/evaluation_population.csv` must contain. `docs/` also holds MRM-04, the reminder-programme SOP and the
table dictionary. `data/appointments.sqlite` is read-only.

Leave the repaired package in place, with `python -m mlops monitor --db data/appointments.sqlite --out out`
producing the outputs. Your submission will be reviewed against the evidence in the workspace, so the figures
you report must be the ones the evidence supports.
