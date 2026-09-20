**To:** Reliability Analytics
**From:** Director, Reliability & Aftermarket
**Re:** FY27 critical-assembly build — which number do we commit on?

Aftermarket Planning want the expanded spare-assembly build and the higher field-service cover
level. Their case is the 55.2% in `reports/installed_base_reliability_2026Q2.md`, which clears the
28% trigger in the FY27 procurement rule by a wide margin.

Operations do not accept it. Their point is that most of our assemblies are swapped out at the
scheduled overhaul, or leave with the unit, long before anything fails in service — so a figure
above half cannot describe what we will actually be paying for next year.

Engineering are looking at the same extract for the overhaul-interval review and are comfortable
with a number in that range, which has muddied the argument rather than settled it.

I need the figure the procurement rule is actually written on, and the recommendation that follows
from it. Start with `README.md`.

Requirements:

1. `cd /workspace && python -m fleet_reliability analyse --warehouse data/warehouse.sqlite --out out`
   must write `analysis_results.json` as specified in `docs/outputs/analysis_contract.md`.
2. The same command is re-run against each quarterly extract, so the method must hold in general:
   no special-casing of particular units, sites, models, dates or values in this extract.
3. `data/warehouse.sqlite` is the system of record: do not modify it, and do not hand-edit outputs
   or reports.
4. Re-running on the same extract must give identical outputs.
5. Leave the outputs regenerated for this extract, and tell me briefly why the published figure
   should not go to the FY27 committee as it stands.
