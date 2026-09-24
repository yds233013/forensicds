You are the process data scientist for Building 2 at Kelvin Works.

First-pass yield on the MAN-4471 bore has fallen from 97.0% to 92.8% since week 19. Purchasing has drafted a
supplier nonconformance against the bar-stock supplier on the strength of the week-24 quality report in
`reports/`, and wants to escalate it to a change of supplier. Brendale have declined the draft claim, so the
escalation has to be restated in the form Schedule 3 §3.2 of the supply quality agreement requires.

Your job is to produce that restatement, and the recommendation that follows from it. Work out what has
actually changed and how much of the change each candidate cause accounts for, then apply the agreement's own
rule. The `quality` package in `/workspace` is what produced the report; repair it where it is wrong and re-run
it so the numbers are reproducible.

`docs/outputs/readout_contract.md` (revision 2) specifies exactly what `out/readout.json` and
`out/part_dispositions.csv` must contain. `docs/` also holds the drawing extract, the works procedure QP-07,
the supply quality agreement and the table dictionary. `data/inspection.sqlite` is read-only.

Leave the repaired package in place, with `python -m quality report --db data/inspection.sqlite --out out`
producing the outputs. Your recommendation will be reviewed against the evidence in the workspace, so the
numbers you report must be the ones the evidence supports.
