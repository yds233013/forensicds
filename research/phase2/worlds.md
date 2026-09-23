# Phase 2 — three candidate enterprise worlds

A **world** is a persistent fictional organisation: one set of systems of record, one document estate,
one cast of teams, one calendar of real events (migrations, incidents, policy changes, reorganisations).
An **incident** is a dated situation inside that world. Incidents share the organisation, not a trick.

Rules that keep a world from collapsing into one puzzle:
1. **Independent mechanisms.** No two incidents in a world may turn on the same scientific mechanism.
2. **Independent systems.** Each incident's discriminating evidence must come from a different
   subsystem than the last one's, so an agent cannot learn "always check table X".
3. **Shared but non-decisive context.** The world's documents (org chart, calendar, definitions) are
   reused; the *decisive* facts are local to each incident.
4. **Dated consistency.** A migration that happened in March is in March for every incident, and an
   incident set before it must not see it. This is what makes a world worth building: the point-in-time
   structure is reused, not re-invented.
5. **No cross-incident answer leakage.** An incident's resolution may not be documented anywhere an
   agent working a later incident can read.

---

## WORLD 1 — **Meridian Retail Group** (grocery, convenience, rapid delivery)

~900 supermarkets, ~1,400 convenience stores, a 40-site rapid-delivery arm, own-brand manufacturing,
national distribution. Familiar because the phase-1 suite already borrowed two incidents from this
sector — the world is proposed precisely because it can carry many more without repeating them.

**Systems of record.** EPOS transactions and baskets · loyalty scheme · planogram and range · price
and promotion registry · inventory and replenishment · DC and route logistics · supplier contracts and
inbound quality · labour scheduling and time-and-attendance · store estate and refit register ·
e-commerce/rapid-delivery order stack · media and CRM campaign registry · finance semantic layer ·
forecasting service with vintaged outputs · experiment registry.

**Document estate.** Metric handbook · category-management SOP · promo governance policy · supplier
quality agreement · labour rules and union agreement · refit programme brief · pricing policy ·
data-catalogue · ADRs · incident log · weekly trading reports · board packs.

**Candidate incident families (12):** promotional incrementality and cannibalisation · price
elasticity from endogenous price changes · range-rationalisation lost-sales estimate · rapid-delivery
contribution margin under allocated capacity · courier/picker labour standard vs actual · supplier
quality scorecard under a changed inspection frame · own-brand switching after a recipe change ·
store-refit uplift under staggered scheduling · availability metric drift after a scan-instrumentation
change · hierarchical forecast reconciliation for the buy plan · loyalty-scheme cohort attrition under
identity merges · shrink/waste attribution after a self-checkout rollout.

---

## WORLD 2 — **Halcyon Health Partners** (outpatient network, diagnostics lab, home care)

38 outpatient clinics, a central diagnostics laboratory, a home-care arm, contracts with three
insurers and one public payer. Regulated reporting, coded activity, referral pathways.

**Systems of record.** Patient administration (referrals, appointments, attendance) · clinical coding
and diagnosis registry · laboratory information system (orders, results, confirmatory testing,
QC/calibration log) · scheduling and rota · claims and remittance · device/sensor telemetry for home
monitoring · quality-registry submissions · patient-reported outcomes · staffing agency invoices ·
capacity/estates data.

**Document estate.** Payer contract schedules with quality measures and thresholds · coding guidance
and its revision history · laboratory SOPs, method-validation reports and calibration certificates ·
clinical pathway definitions · quality-registry specification with a dated definition change ·
staffing policy · incident log · monthly quality packs.

**Candidate incident families (11):** readmission/return-visit rate rise after a coding-guidance change
· diagnostic assay performance under partial verification · no-show model degraded after a reminder
policy change (performative) · case-mix-adjusted length-of-stay comparison between sites · clinic
capacity sizing under peak-coincidence vs average demand · home-monitoring adherence metric after a
firmware change · referral-to-treatment interval under censoring and queue jumping · agency-staffing
cost per contact with changing skill mix · lab turnaround-time target under a specimen-routing change ·
payer quality-measure denominator attribution · outcome measure validity when the proxy changed.

---

## WORLD 3 — **Lattice Financial** (consumer lending, payments, fraud, collections)

A mid-size consumer fintech: instalment lending, a card programme, an acquiring/payments rail, and an
in-house collections operation. Champion/challenger model governance, regulated model risk, a
credit-risk committee with written thresholds.

**Systems of record.** Applications and decision logs (with policy versions and score cut-offs) ·
bureau pulls with as-of stamps · originations and account ledgers · repayment and delinquency history ·
card authorisations, settlements, chargebacks and disputes · fraud screening decisions and manual
review queues · collections contact and treatment log · pricing/limit policy registry · model registry
with training snapshots · A/B and champion-challenger registry · funding and cost-of-risk finance
layer.

**Document estate.** Credit policy and its dated amendments · model risk-management standard (validation
requirements) · fraud review SOP with sampling design · chargeback timing rules from the network ·
collections treatment playbook · pricing committee minutes with thresholds · data dictionary with
bureau attribute vintages · incident log (an outage, a bureau format change, a rail migration).

**Candidate incident families (12):** limit-increase policy under selective labels · fraud threshold
under performative feedback and missing labels on blocked traffic · chargeback-rate measurement under
network timing rules · collections treatment effect under selection into treatment · scorecard
degradation from bureau attribute redefinition · authorisation-rate drop with issuer-mix shift
(Simpson) · IFRS9/expected-loss staging under a changed definition of default · pricing elasticity of
APR under committee-driven (endogenous) rate changes · early-payment/attrition behaviour after a fee
change · dispute-win-rate model evaluated on the wrong operational population · funding cost
allocation to product margin (economic object) · model-monitoring drift alarm caused by an upstream
feature backfill.
