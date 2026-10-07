# Real-distribution provenance — g36 (FY27 residential capacity procurement)

1. **Professional role.** Resource-planning analyst at a load-serving utility.
2. **Industry.** Electric utility / energy resource planning.
3. **Business decision.** Whether to procure additional firm capacity for the FY27 residential block,
   against 1,900 MW held, a regulator-required 10% reserve, and a resulting cap of 3.057 kW of mean
   peak-window demand per customer across 565,000 customers.
4. **Realistic inherited artifacts.** Interval (AMI) consumption data, tariff/time-of-use rate
   assignments and switch history, customer master data, the planning memo with the arithmetic, and
   the code that produced the current per-customer peak figure.
5. **Statistical/ML problem.** Population and exposure definition under a changing tariff mix: the
   per-customer peak-window figure depends on which customers are on which time-of-use schedule during
   which period, and tariff migration is not independent of consumption. The quantity the regulator's
   reserve applies to must be reconstructed on the right population and the right window.
6. **Why this happens in real organizations.** Time-of-use tariff rollouts change both *when*
   customers consume and *which* customers are on which schedule, and enrolment is typically voluntary
   or phased, so the enrolled population is selected. Capacity procurement is a regulated,
   high-consequence decision made on a single scalar derived from interval data, which puts all the
   weight on how that scalar is defined.
7. **Public sources.** The operational pattern — AMI interval data, phased or opt-in TOU enrolment,
   coincident-peak based capacity obligations with a regulator-set reserve margin — is standard
   utility resource-planning practice and is the direct reference point for this task's abstraction.
8. **What is synthetic.** The utility, customers, interval data and tariff parameters.
9. **What is preserved.** A regulator-fixed decision rule the analyst may not redefine, a scalar gate
   with an explicit arithmetic memo, and a tariff-mix change entangled with the quantity being measured.
10. **Why it belongs.** It is the suite's only regulated-utility task and its only capacity-constrained
    procurement decision, and it puts population definition rather than estimator choice at the centre.
