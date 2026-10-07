# Northline — Boost programme analysis workspace

Boost is the courier incentive Operations piloted this spring. The programme readout in
`reports/boost_readout_2026-06.md` recommends national rollout. Finance has asked for the recommendation
to be re-derived before the July investment committee.

- `data/northline.sqlite` — operational warehouse (read-only).
- `docs/` — programme brief, metric definitions, experiment plan, dispatch and supply notes, the rollout
  memo that carries the decision rule, the data dictionary, and the output contract.
- `northline_eval/` — the analysis package the programme readout was produced with.
- `reports/` — the published readout.
- `notebooks/analyst_note.md` — the analyst's working note.

Re-run the published numbers with:

    python -m northline_eval readout --db data/northline.sqlite --out out
