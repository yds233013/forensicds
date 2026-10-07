# Real-distribution provenance — p22 (MAN-4471 bore yield step)

1. **Professional role.** Process data scientist / quality engineer embedded in a machining plant.
2. **Industry.** Precision metal manufacturing (automotive/aerospace tier supplier).
3. **Business decision.** Whether to raise a formal supplier nonconformance against the bar-stock
   supplier and escalate to a change of supplier, restated in the form the supply quality agreement's
   Schedule 3 §3.2 requires. A wrong escalation means a contractual claim against an innocent supplier
   and the cost of requalifying a new one.
4. **Realistic inherited artifacts.** An inspection database (part-level CMM measurements across two
   gauges, operators, heat lots, tooling changes), the `quality` Python package that produced the
   published weekly report, the week-24 quality report itself, the drawing with the tolerance, QP-07
   (the plant's calibration procedure), the supply quality agreement, a table dictionary, and plant
   notes. This is the normal contents of a quality engineer's inherited folder.
5. **Statistical/ML problem.** Measurement-system analysis versus process change: decomposing an
   observed nonconforming-rate step into measurement bias, material, tooling and operator components,
   on a stratified population, then applying a contractual threshold.
6. **Why this happens in real organizations.** Calibration adjusts instrument *bias* against a
   traceable standard; Gauge R&R addresses *consistency*; the two are different checks and a gauge can
   be perfectly calibrated and still fail R&R. A control chart built on an unvalidated or newly
   re-zeroed gauge shows false out-of-control signals that look exactly like a process shift, and
   triggers adjustments that add variation rather than remove it. A yield step that coincides with a
   recalibration event is therefore a routine and expensive misattribution.
7. **Public sources.**
   - MoreSteam, *Measurement System Analysis*: https://www.moresteam.com/toolbox/measurement-system-analysis
   - Micro Precision, *Gauge R&R vs. Calibration*: https://microprecision.com/blog/gauge-rr-vs-calibration/
   - SPC for Excel, *Five Common Mistakes with Gage R&R Studies*: https://www.spcforexcel.com/knowledge/measurement-systems-analysis-gage-rr/five-common-mistakes-gagerr/
   - 1factory, *A Guide to Gage R&R*: https://www.1factory.com/quality-academy/guide-gage-r-and-r.html
8. **What is synthetic.** The company, part number, supplier, measurements and the generator's
   parameters. All measurement values are simulated.
9. **What is preserved.** The artifact surface (CMM records with gauge and operator identifiers, a
   calibration log, heat-lot genealogy, tooling-change events), the contractual form the answer must
   take, the requirement to attribute a rate change across named causes, and the fact that the
   measurement-system explanation and the material explanation are both locally consistent with the
   headline number.
10. **Why it belongs.** It is the only task in the suite where the *instrument* rather than the
    process or the population is the source of the wrong conclusion, and the decision is contractual
    rather than statistical. It also carries the suite's cleanest demonstration of procedure-level
    overfitting (see the report's §21): all three Gemini trials produced a fully correct visible-world
    attribution and still scored 0, because their attribution code had no path that could assign the
    change to tooling when a sibling world made tooling the driver.
