**To:** Resource Planning Analytics
**From:** VP Resource Planning
**Re:** FY27 residential capacity - do we procure?

We hold 1,900 MW of firm capacity for the residential block and the regulator requires a 10 %
reserve. Across 565,000 customers that caps mean peak-window demand at **3.057 kW per customer**.
The memo in `reports/` has the arithmetic.

The 2027 season is forecast materially warmer than anything in our recent record, and on the flat
tariff our own model puts us above that ceiling. The mandatory time-of-use tariff is supposed to be
the mitigation - Rates expect customers to move load out of the peak window.

Load Research ran a voluntary tariff pilot last season with a randomised control group. Rates read
that pilot as proof the tariff closes the gap. I am not yet convinced the pilot tells us what
happens once the tariff applies to everybody, in the weather we are actually forecast to get.

I need the expected mean peak-window load per customer for the 2027 season with the whole estate on
the tariff, and the procurement call that follows. Procurement lead time is nine months, so this is
decided now, on forecast. Start with `README.md`.

Requirements:

1. `cd /workspace && python -m capacity_forecast analyse --warehouse data/warehouse.sqlite --out out`
   must write `analysis_results.json` as specified in `docs/outputs/analysis_contract.md`.
2. The same command is re-run against each planning extract, so the method must hold in general: no
   special-casing of particular customers, segments, dates or values in this extract.
3. `data/warehouse.sqlite` is the system of record: do not modify it, and do not hand-edit outputs
   or reports.
4. Re-running on the same extract must give identical outputs.
5. Leave the outputs regenerated for this extract, and tell me briefly whether the incumbent
   forecast can be used for this decision as it stands.
