# G23: Readmission model labels built on encounters instead of care episodes (detailed design)

Status: generation-3 design. Not built. No model run. Fictional health system, hospitals, EHR vendors and measure.
Nothing here claims to reproduce a real regulatory specification; where the fictional measure resembles public
readmission-measure concepts (transfer combining, planned-readmission tables, discharge-alive eligibility), the
resemblance is generic and marked *to verify* before anyone describes it as matching a real specification.
Disposition and point-of-origin codes are "UB-04 style" (*to verify* against the real code sets; the build may use
fictional codes instead).

## Workspace sketch

```
/workspace
  README.md                                    repo purpose; `python -m readmit_eval run --quarter 2026Q2`
  CHANGELOG.md                                 eval job history; "2026-02: onboard St. Brendan's (H6) feed"
  readmit_eval/
    cli.py
    load.py                                    FAULTY: `pd.to_datetime(..., utc=True)` for every feed; H6 raw codes via map
    cohort.py                                  FAULTY: encounter = index stay; excludes died/AMA/hospice only
    labels.py                                  FAULTY: next inpatient encounter ≤ 30 days; planned = admit_type 'elective'
    metrics.py                                 rate, AUC, calibration by facility (formulas correct)
    report.py
  config/eval.toml                             quarters, paths, age threshold
  data/ehr_extract.duckdb                      ~240 MB
    encounters                                 212k inpatient + 96k ED/observation rows, 2025-01..2026-07
    patients, patient_xref                     138k EMPI patients; facility MRN → EMPI
    diagnoses, procedures                      principal/secondary dx and procedure groups
    deaths                                     EHR in-hospital + state death index linkage (complete through 2026-07-31)
    facilities                                 6 network hospitals: type, ehr_vendor, joined_network
    model_scores                               score at each inpatient discharge event (READMIT v3)
  ref/h6_disposition_map.csv                   H6 raw disposition text → network code (integration team)
  ref/h6_admit_source_map.csv                  H6 raw admit source text → network point-of-origin code
  ref/qm30r_planned_tables.csv                 always-planned procedure groups, always-planned dx groups,
                                               potentially-planned procedure groups, acute dx groups
  docs/quality/QM-30R_unplanned_readmission_v3.md   fictional network measure: eligibility, outcome, glossary
  docs/models/readmit_v3_model_card.md         prediction point, population, evaluation governance
  docs/data/ehr_extract_dictionary.md          tables, code sets, timestamp conventions ("UTC ISO-8601")
  docs/integration/2026-01_st_brendans_onboarding.md   Meridel EHR feed notes (local wall-clock times, text codes)
  docs/reviews/2025-11_model_review_notes.md   DS peer review recommending competing-risk treatment (attractor)
  reports/eval/2025Q1..2026Q1_eval.json         past eval outputs (faulty pipeline)
  reports/quality/network_readmission_dashboard_2025.csv   Quality dept rates (vendor-computed, different scope)
  notes/2026-08-12_cmo_email.md, notes/h6_case_mix_summary.md (generated)
  notebooks/q2_readmission_spike.ipynb         analyst notebook: H6 feature importance, "H6 sicker" narrative
  logs/eval_runs.jsonl, logs/feed_ingest_h6.log
```

## 1. Research question

When an ML evaluation label is defined on clinical episodes but the data arrive as facility encounters from
heterogeneous feeds, can an agent reconstruct the episode grain (cross-facility transfer chains with feed-specific code
and timestamp semantics), apply a clinical outcome definition with planned-readmission and death semantics, and show
that a jump in readmission rate and AUC is a label artefact — without dropping the new hospital or changing the
population?

## 2. Enterprise setting

Lakeshore Valley Health (LVH, fictional) runs six acute hospitals in one time zone (America/Chicago): H1 Lakeshore
General (tertiary; receives most transfers), H2 Valley Regional, H3 North Shore Community, H4 Riverbend, H5 LVH Cancer
& Specialty (oncology; frequent scheduled chemotherapy and transplant admissions), and H6 St. Brendan's Regional, a
rural hospital that joined on 2026-01-01 on a different EHR ("Meridel"). H1–H5 share an EHR with UTC ISO-8601
timestamps. The Clinical Analytics team evaluates READMIT v3, a 30-day unplanned-readmission risk model that scores
patients at discharge and drives transitional-care nurse outreach. A quarterly job produces the evaluation report
reviewed by the Chief Medical Officer.

## 3. Visible symptom (instruction memo)

From the CMO: the Q2-2026 evaluation shows the network 30-day readmission rate at 18.9% (14.8% in Q4-2025) and model
AUC rising from 0.71 to 0.78. St. Brendan's alone shows 31%. Transitional-care nurses are swamped with outreach lists.
Clinical leaders do not believe the patient population changed this much, and the analytics team is split between "St.
Brendan's patients are sicker" and "the model overfits St. Brendan's". The CMO needs trustworthy numbers.

Required: `python -m readmit_eval run --quarter 2026Q2` (and any quarter in the extract) writes
`out/episodes.parquet`, `out/index_outcomes.parquet` and `out/eval_metrics.json` in the formats in the data
dictionary's "evaluation outputs" section; the evaluation must follow the network readmission measure and the model
card; `data/` and `ref/` are authoritative and read-only; all six hospitals remain in scope; no special-casing of
hospitals, patients or dates; validate before handing over.

## 4. Source distribution inspiration

- Hospital readmission measures that combine inter-hospital transfers into one episode, exclude planned readmissions
  using procedure/diagnosis tables, and require discharge alive (general public-measure concepts, *to verify*).
- Health-system mergers that onboard a hospital on a different EHR with local-time timestamps and free-text code sets;
  interface mapping tables built by integration teams.
- Readmission-model evaluation practice: label construction at the episode grain, competing mortality, population
  definition governance.

## 5. Causal graph / ground truth

Generator (stdlib, seeded; all times generated as true instants, then rendered per feed):

1. **Patients** 138k; age, comorbidity burden `c ~ Gamma`. Latent 30-day unplanned readmission hazard depends on `c`,
   dx group, discharge disposition and facility-independent covariates. H6 case mix: older (+4.1 years), `c` +0.18 SD
   — real but small (true H6 unplanned readmission 17.9% vs network 15.1%).
2. **Acute stays** per patient; each stay may be a **transfer chain**:
   - H1–H5 community → H1 transfers: 2.4% of stays;
   - H6 → H1 transfers: 11.2% of H6 stays; 41% depart between 00:00 and 05:59 local (overnight ambulance transport);
   - H1 → H6 back-transfers (step-down closer to home): 1.6% of H1 stays with H6 origin; the H6 registration often
     precedes H1's discharge documentation by 0.5–3 h (negative gap);
   - chains of 3 (H6 → H1 → H6): 212 visible;
   - transfers to non-network acute hospitals (disposition "transfer to acute", no following encounter): 0.8%.
3. **Feed rendering**:
   - H1–H5: `admit_ts`, `discharge_ts` = `YYYY-MM-DDTHH:MM:SSZ`; disposition and point-of-origin numeric codes.
   - H6: naive local `YYYY-MM-DD HH:MM:SS`; raw text dispositions mapped by `ref/h6_disposition_map.csv`:
     "Transferred - Acute Care" → 02, "Discharged to Other Facility" → 70, "Skilled Nursing" → 03, "Rehab" → 62,
     "Home" → 01, "Home Health" → 06, "Hospice" → 50, "AMA" → 07, "Expired" → 20. H6 staff use
     "Discharged to Other Facility" for 58% of acute transfers to H1 (Meridel's default pick-list), and also for
     discharges to assisted living and to out-of-network rehab. H6 admit source raw text maps correctly.
   - Receiving hospitals record point of origin "transfer from a hospital" (code 4) for 97% of true transfers.
   - Generator never places H6 events in non-existent (spring-forward) or ambiguous (fall-back) local hours.
4. **Planned admissions**: H5 maintenance chemotherapy (always-planned dx group), transplant (always-planned proc),
   elective joint replacement (potentially-planned proc; planned unless principal dx acute), cardiac catheterisation
   for acute MI (potentially-planned proc with acute dx → unplanned). Admit type is unreliable: H5 registers 38% of
   chemo admissions as "urgent" (oncology clinic direct admits); H6 registers all direct admits "urgent".
5. **Deaths**: in-hospital (disposition 20) 2.1% of stays; post-discharge within 30 days without readmission 2.6% of
   eligible episodes; death index gives `death_date` only. 31 visible chains end in death at H1 after transfer from H6.
6. **Model**: READMIT v3 scores each inpatient discharge event. Its features include discharge disposition and
   facility; transfer-out encounters get high scores (disposition 02/70). Under encounter labels these are "readmitted"
   next day, which inflates AUC.
7. **Quality dashboard 2025**: vendor-computed, population "65+ with 30 days of continuous coverage" (coverage data
   not in the workspace), rates to one decimal, pre-H6 only.

Truth (visible): Q4-2025 network rate 14.2% (faulty 14.8% — H1–H5 transfers were already inflating it), Q2-2026 15.1%
(faulty 18.9%); H6 Q2 17.9% (faulty 31.4%); AUC Q2 0.718 (faulty 0.781).

## 6. Latent statistical/business invariant (oracle truth)

1. **Time**: every timestamp is an instant; H6 naive strings are America/Chicago wall-clock times. Calendar dates are
   America/Chicago dates.
2. **Episode**: order a patient's (EMPI) acute inpatient encounters by admission instant. Encounter `n` continues the
   episode of `n−1` iff the facilities differ, `date(admit_n) − date(discharge_{n−1}) ∈ {0, 1}` (overlaps allowed: an
   admission before the previous discharge counts as day 0), and the transfer is documented on either side:
   disposition of `n−1` is 02 (acute transfer) **or** point of origin of `n` is 4 (transfer from a hospital).
   Disposition 70 alone is not transfer evidence. Episode discharge = last encounter's discharge; episode facility =
   last encounter's facility; episode disposition = last encounter's disposition.
3. **Eligible index episode** (discharge date in the quarter): age ≥ 18 at admission; final disposition not 20
   (expired), 07 (AMA), 50/51 (hospice) and not 02 (transferred out with no continuing network encounter); principal dx
   of final encounter not in psychiatric/rehab groups (measure table).
4. **Outcome**: let `A` be the first acute inpatient **episode** of the patient admitted with
   `0 ≤ date(admit_A) − date(index_discharge) ≤ 30` that is not the index episode itself.
   - No `A` and death date within 30 days → `died_without_readmission`, label 0, **retained in the denominator**.
   - `A` exists and is planned (first encounter of `A`: always-planned procedure or always-planned dx, or
     potentially-planned procedure with non-acute principal dx) → `planned_readmission`, label 0.
   - `A` exists and is unplanned → `unplanned_readmission`, label 1.
   - Otherwise `none`, label 0.
   Only the first subsequent episode is considered.
5. **Score**: the model score at the discharge event of the episode's final encounter.
6. **Metrics**: rate = mean label over eligible index episodes, by quarter and discharging facility; AUC (Mann–Whitney
   with ties 0.5); calibration deciles; 30-day post-discharge death-without-readmission rate.

## 7. Grains and state variables

| Grain | Key | State |
|---|---|---|
| encounter | `encounter_id` | facility, instants, class, codes, dx/proc, score |
| episode | (EMPI, first encounter) | member encounters, final discharge, final facility/disposition |
| index episode | episode with eligible final discharge in quarter | outcome, label, score |
| patient timeline | EMPI | ordered episodes, death date |
| feed | facility × EHR vendor | timestamp format, code vocabulary |
| facility × quarter | | rates, AUC |

The trap grain: encounters are the natural unit in the extract, the score table and the faulty code. Episodes are a
derived state that must be carried consistently into eligibility, outcome search, score selection and metrics.

## 8. Evidence graph

| Artifact | Shows | Natural path? |
|---|---|---|
| CMO memo, past eval JSONs | rate/AUC jump at H6 onboarding | yes |
| analyst notebook | H6 feature importance, disposition importance; "H6 sicker" narrative | yes (attractor) |
| `h6_case_mix_summary.md` | H6 older and more comorbid (true, small) | yes (attractor) |
| `labels.py`, `cohort.py` | encounter-level labels; admit-type planned rule | yes |
| QM-30R measure | eligibility list; outcome = first subsequent admission, unplanned; glossary: transfer = admission to another acute hospital on the same or next day after discharge, documented as a transfer; "stays linked by transfer form one episode" | yes |
| `qm30r_planned_tables.csv` | three procedure/dx tables | yes |
| model card | prediction at discharge from the index stay; evaluation on the QM-30R population "for comparability with Quality"; secondary metric: post-discharge mortality | yes |
| model review notes | recommends excluding or censoring deaths as competing risk | medium (attractor) |
| data dictionary | "timestamps are UTC ISO-8601" (true for H1–H5 only); code sets | yes |
| H6 onboarding note | Meridel sends local wall-clock times; free-text dispositions mapped by integration; pick-list defaults listed | medium (must be found) |
| raw H6 rows | no `Z`; night transfers look like 2-day gaps after parsing; back-transfers appear to overlap | yes, if rows inspected |
| `h6_disposition_map.csv` | "Discharged to Other Facility" → 70 | yes (attractor: "70 means transfer at H6") |
| encounters with point of origin 4 at H1 after H6 70-dispositions | the receiving side documents the transfer | medium |
| `deaths` + dictionary | death index completeness through 2026-07-31 | medium |
| Quality dashboard 2025 | rates 0.4–0.9 pts different from any internal computation | medium (attractor: "match Quality") |
| `feed_ingest_h6.log` | parser warnings "naive timestamp assumed UTC" (INFO level, 14k lines) | low–medium |

## 9. Evidence authority hierarchy

| Conflict | Governs | Why |
|---|---|---|
| Data dictionary "UTC" vs H6 onboarding note + raw format | onboarding note + raw format | dictionary predates H6; strings without offset are not UTC instants |
| Model review notes (censor deaths) vs model card | model card | card is the governed evaluation definition; review notes are recommendations |
| QM-30R vs faulty code's planned rule | QM-30R tables | measure defines planned |
| H6 disposition map (70) vs receiving point of origin | either-side transfer documentation per glossary | map is a vocabulary translation; 70 is used for non-acute destinations too |
| Quality dashboard vs measure applied to model population | measure on model population | dashboard is a different population and coverage filter |
| Notebook narrative | none | analysis on the faulty labels |

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | H6 population sicker | case-mix summary true; H6 older | explains ~0.4 network pts, not 4.1; H6 "readmissions" are next-day admissions to H1 |
| H2 | Model overfits H6 | H6 facility and disposition features top importance; AUC jump | model unchanged since 2024; AUC jump comes from label construction |
| H3 | Label construction at wrong grain (transfers) | next-day H1 admissions with origin 4 | must be reconciled with codes and time |
| H4 | H6 feed timestamp/code problem | naive strings; parser warnings | alone explains little; interacts with H3 |
| H5 | Planned readmissions miscounted | H5 "urgent" chemo | pre-existing, affects all quarters |
| H6 | Deaths mishandled | review notes | small, but graded |

## 11. Why each wrong hypothesis is plausible

H1 has a true data summary and a clinical narrative (rural, older). H2 has a notebook with feature importances pointing
straight at H6. "Drop H6" is the natural response to both and yields a Q2 rate (14.9%) and AUC (0.714) close to history —
a believable fix. The Quality dashboard offers an external number an agent may try to match. The review notes give a
respectable statistical argument (competing risks) for excluding deaths.

## 12. Investigation path (expected 50–80 actions)

1. (1–8) Memo, README, past reports, run eval; reproduce 18.9%/0.781.
2. (9–14) Notebook, case-mix summary; rate by facility; H6 31.4%.
3. (15–22) Inspect H6 "readmissions": 62% are admissions to H1 on day 0–2 after H6 discharge. **Discovery 1**:
   transfers labelled as readmissions. Read QM-30R glossary.
4. (23–30) Implement transfer linking with disposition 02; H6 rate barely moves — most H6 transfers are coded 70.
   **Discovery 2**: H6 vocabulary; receiving point of origin.
5. (31–38) Many H6→H1 pairs still 2 days apart; inspect raw strings; onboarding note. **Discovery 3**: naive local
   times; dates shift for overnight departures. Also back-transfers appear to overlap.
6. (39–44) Chains of 3; transfer-out to non-network acute; death after transfer at H1. **Discovery 4**: eligibility
   and outcome must use episode final encounter.
7. (45–52) Planned rule: admit type vs tables; H5 urgent chemo. **Discovery 5**.
8. (53–58) Deaths: model card vs review notes. **Discovery 6**.
9. (59–64) Score selection at final discharge; metrics.
10. (65–80) Validate: episode audits (no episode spans > 1 non-transfer gap; every link has documentation; overlap
    cases), per-facility transfer-link counts pre/post H6, rates for H1–H5 before and after onboarding stable
    (≈14.2–14.6%), planned table coverage, death accounting, re-run previous quarters, determinism.

## 13. Natural wrong implementation

After Discovery 1 the natural repair (in `labels.py`):

```python
enc = enc.sort_values(["empi_id", "admit_ts"])
prev = enc.groupby("empi_id").shift()
is_transfer = (enc.admit_ts - prev.discharge_ts).between(pd.Timedelta(0), pd.Timedelta(hours=24)) \
              & (enc.facility_id == prev.facility_id)            # variant A: same-facility 24 h merge
# variant B: facility != prev facility, same 0–24 h window, prev.disposition_code == "02"
episode_id = (~is_transfer).cumsum()
```

Keeping `load.py`'s `utc=True` parse and the encounter-level cohort/labels downstream.

Numerically (visible, Q2-2026):
- **Variant A (same facility ≤ 24 h)** merges 1,140 genuine same-facility quick readmissions (true label 1 events
  become one stay) and links none of the cross-facility transfers: network 17.6%, H6 29.8%, AUC 0.772.
- **Variant B (cross-facility, 0–24 h elapsed, code 02)**: misses 58% of H6 transfers (coded 70), misses night
  departures whose parsed gap exceeds 24 h or whose parsed discharge is later than the next admission (H1 → H6 back-
  transfers become negative gaps), and misses H1–H5 transfers documented only by the receiving hospital's point of
  origin: network 16.0%, H6 22.6%, AUC 0.741.
- Both keep transferred-out encounters as index stays when the chain was not recognised, use the first encounter's
  score, treat `admit_type == 'elective'` as planned (H5 "urgent" chemo counted as unplanned: +0.3 pts), and ignore
  post-discharge deaths (secondary metric absent).
- Episode-table mismatches: A 3,900 encounters; B 1,760 encounters (visible).

The other natural first responses need no episode logic at all:
- **Drop H6** (filter `facility_id != 'H6'` in cohort and outcomes): Q2 14.9%, AUC 0.714. It looks like history, but
  it removes H1–H5 patients' real readmissions to H6 (−0.5 pts), keeps H1–H5 transfer inflation (+0.6 pts), and
  violates the scope requirement.
- **Exclude deaths**: denominator −2.6%, rate +0.4 pts, and the secondary mortality metric is undefined.

## 14. Second-order failure modes

| After rejecting… | Next repair | Still wrong |
|---|---|---|
| code-02-only transfers | treat H6 disposition 70 as transfer | links H6 "Other Facility" discharges (assisted living, out-of-network rehab) followed by next-day ED admissions at H1 — genuine readmissions (visible 140) |
| 70-as-transfer | receiving point of origin 4 only | misses 3% of transfers where the receiving side omitted origin but H6 coded 02 |
| elapsed-hours window | calendar-day window on **UTC** dates | H1–H5 evening discharges shift dates; H6 naive still wrong |
| UTC parse | shift H6 by a fixed −6 h | wrong for CDT months (from 2026-03-08; −5 h): 38% of visible H6 rows |
| fixed offset | `tz_localize('America/Chicago')` on the whole column after parsing H1–H5 as naive too | double-shifts H1–H5 |
| gap ≥ 0 requirement | allow overlaps but pair by `discharge_ts` order | back-transfer chains mis-ordered |
| chains of two | pairwise linking without transitive episode ids | H6 → H1 → H6 split into two episodes; final discharge wrong |
| encounter-level eligibility | exclude encounters with disposition 02 but keep encounter grain | chains ending in death at H1 still yield an eligible H6 "index" when not linked; receiving encounter's score not used |
| admit-type planned | tables but applied to *any* readmission in 30 days (not first) | index with planned chemo on day 5 and unplanned admission on day 20 becomes label 1 (visible 96) |
| outcome search over encounters | first subsequent **encounter** rather than episode | readmission that is itself a transfer chain counted correctly for the first index but the chain's second encounter then becomes the "first admission" for an overlapping index (visible 22) |
| everything | match Quality dashboard (restrict to 65+) | population change |
| everything | first encounter's score for the episode | AUC 0.709 vs 0.718 (outside tolerance) |

## 15. Correct repair properties

- Timestamp semantics per feed format (offset present vs naive local), DST-aware.
- Episode construction over all facilities, transitive, calendar-day window, either-side transfer documentation,
  overlap-tolerant ordering.
- Eligibility, outcome, planned classification and score selection at episode grain.
- Deaths retained, outcome category recorded, mortality secondary metric.
- All hospitals in scope; no facility-id, vendor-name or date special-casing.

## 16. Repair surfaces

| File | Why |
|---|---|
| `load.py` | feed-aware timestamp parsing; keep both disposition and point of origin |
| new `episodes.py` | episode builder (does not exist) |
| `cohort.py` | eligibility on episode final encounter |
| `labels.py` | first subsequent episode, planned tables, deaths |
| `metrics.py` | score at final discharge; mortality metric (formulas otherwise unchanged) |

## 17. Validation requirements

Insufficient: network rate back near 14–15%; AUC near 0.71; H6 rate "only moderately" above network; Quality
dashboard proximity.

Required at row/state grain:
- **Link audit**: every link has documentation on at least one side and a 0–1 calendar-day gap; sample 20 H6 → H1
  links with raw strings.
- **Non-link audit**: cross-facility pairs within 1 day that are *not* linked all lack documentation; review a sample
  of H6 "Other Facility" non-links.
- **Timestamp audit**: H6 events before and after 2026-03-08 convert with the right offset; no episode with an
  admission more than 3 h before the previous discharge.
- **Stability check**: H1–H5 rates before and after H6 onboarding under the new labels (should be flat, ~14.2–14.6%).
- **Outcome audit**: chains ending in death; planned-first-then-unplanned cases; transfer-out to non-network.
- **Score audit**: each index uses the final encounter's score.
- Re-run Q4-2025 and Q1-2026; determinism.

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface changes | Overfit caught | Same distribution |
|---|---|---|---|---|
| `hidden_a` (2025-04..2026-12) | timestamp semantics, calendar-day window | the local-time feed hospital has a different facility id and joins 2025-10-01, spanning both DST changes; 60% of its transfers depart 00:00–05:59; H1–H5 evening discharges dense near day 30 | `facility_id == 'H6'`; fixed −6 h; UTC dates | DST crossing and naive-format detection visible (2026-03-08) |
| `hidden_b` (2024-10..2025-12) | episode chains and documentation | joining hospital mostly **receives** back-transfers; "Other Facility" mostly non-acute; chains of 4; 2% transfers to non-network acute; receiving side omits origin 4 in 8% | "70 = transfer"; pairwise-only links; H6→H1 direction assumption | chains, back-transfers, non-network transfer and either-side documentation visible |
| `hidden_c` (2025-07..2026-06) | planned and deaths | oncology share doubled; potentially-planned procedures with acute dx common; planned-first-then-unplanned 3× visible rate; post-discharge mortality 5%; 90 death-after-transfer chains | admit-type rule; any-readmission rule; exclude deaths; ignore in-hospital death after transfer | all mechanisms visible |

Every fixture keeps six hospitals, one time zone, the same code sets and measure tables; it never places local events
in DST gap/fold hours.

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` | 1 |
| `alt_sql_duckdb` (gaps-and-islands episodes) | 1 |
| `alt_python_patient_timeline` (per-patient state machine) | 1 |
| `alt_zoneinfo_vs_pandas_tz` | 1 |
| `drop_new_hospital` | 0 |
| `merge_same_facility_24h` | 0 |
| `merge_cross_facility_24h_code02_utc` | 0 |
| `h6_70_as_transfer` | 0 |
| `origin4_only` | 0 |
| `utc_calendar_dates` | 0 |
| `fixed_offset_minus6` | 0 |
| `pairwise_links_no_chains` | 0 |
| `encounter_level_eligibility` | 0 |
| `planned_by_admit_type` | 0 |
| `planned_any_readmission` | 0 |
| `exclude_deaths` | 0 |
| `deaths_as_label1` (composite outcome) | 0 |
| `first_encounter_score` | 0 |
| `match_quality_65plus` | 0 |
| `overfit_facility_id_h6_tz` (correct logic but tz applied to `facility_id == 'H6'`) | visible 1, **hidden_a 0** |
| `overfit_h6_to_h1_direction` (links only from the new hospital to H1) | visible 0 on back-transfers (by design); if too rare visibly, **hidden_b 0** |
| `overfit_visible_planned_ids` (planned classification via lookup of visible encounter ids + admit type) | visible 1, **hidden_c 0** |
| `output_patch`, `edit_data`, `import_reference` | 0 |

## 20. Alternative valid implementations

- Detecting naive timestamps by string format, by `ehr_vendor`, or by `facilities` metadata: equivalent on all
  fixtures *only if* the facilities table marks the vendor in every fixture (it does); format detection is the robust
  choice and is what the reference uses.
- Episode ids: any stable id; verifier canonicalises by the set of member encounters.
- Overlap handling via admission ordering vs "merge overlapping intervals first": identical because non-transfer
  encounters never overlap (generator constraint).
- AUC via scikit-learn or Mann–Whitney: identical with ties = 0.5.

## 21. Verifier design

- Integrity of `data/` and `ref/`.
- Run the documented command for 2025Q4, 2026Q1, 2026Q2 twice as unprivileged user; determinism.
- `episodes.parquet`: exact partition of acute inpatient encounters into episodes (set equality per episode).
- `index_outcomes.parquet`: exact eligible index set per quarter; exact outcome category and label; score equals the
  final encounter's score.
- `eval_metrics.json`: rates per facility-quarter exact from counts (tolerance 1e-9); AUC within 1e-6; mortality
  metric exact.
- Hidden a/b/c: same checks vs generator truth.
- Reference: independent stdlib implementation (`zoneinfo`, no pandas); checked equal to generator truth.
- Binary reward.

## 22. Answer-key leakage audit

| Artifact | Leak? | Mitigation |
|---|---|---|
| QM-30R measure | states transfer glossary, eligibility, first-admission outcome, planned tables | clinical definitions only; nothing about feeds, time zones, H6 vocabulary, overlaps, chains, score selection or encounter vs episode data structures; a literal transcription with network codes and parsed UTC times reproduces variant B-like errors |
| Model card | prediction at discharge from index stay; QM-30R population; mortality secondary metric | does not say "retain deaths"; that follows only from the eligibility list plus governance statement |
| Review notes | recommends excluding/censoring deaths | wrong, attractor |
| Onboarding note | local wall-clock times; free-text mapping; pick-list default "Discharged to Other Facility" | facts; does not say 70 includes acute transfers explicitly (it lists the pick-list options and says staff select "the closest option") |
| Disposition map | 70 for "Other Facility" | correct translation; trap only if treated as clinical meaning |
| Quality dashboard | different population, unreproducible coverage filter | not an answer key |
| Past eval reports | faulty | not keys |
| Parser log | warns naive timestamps "assumed UTC" | pointer to one of six mechanisms (acceptable operational evidence) |
| Code | no episode concept, no tz helper, no planned tables loader, no death join, no unused branch | build review |

**Cheap-solve audit.**
- *One grep*: `grep -ri transfer docs` → glossary → variant B (fails).
- *One doc*: the measure is the most complete doc; transcribing it fails on H6 vocabulary, timestamps, chains and score.
- *One SQL*: `LAG` over encounters with `disposition = '02'` → variant B.
- *One filter*: drop H6 (fails scope and H1–H5 transfer inflation).
- *Helper*: none; `metrics.py` formulas are correct but contain no episode notion.
- *Old report*: Q4-2025 faulty rate 14.8% is itself inflated; matching history fails.
- *Restoring behaviour*: no pre-H6 code differs; nothing to restore.
- *Residual risk*: a strong clinical-informatics prior (transfers, planned tables, local time) plus reading the
  onboarding note could compress discovery; the remaining difficulty is consistent episode-grain propagation and the
  "Other Facility" / receiving-side reconciliation.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Transfer documented only by receiving side after a network discharge "home" (possible external intermediate stay) | generator never creates external intermediate stays within 1 day; either-side rule is from the glossary |
| Same-facility transfer between units | not generated (units are within one encounter) |
| Transfer day window elapsed vs calendar | glossary "same or next calendar day" |
| Overlapping admission before previous discharge | treated as day 0; onboarding note mentions registration before sending discharge is documented |
| Age at admission vs discharge | measure: at admission of index episode's first encounter; generator avoids 18th birthdays within stays |
| Death on the day of readmission | readmission counts (generator orders death after admission) |
| Death date only vs discharge date | within 30 days by calendar date difference 0–30 |
| Readmission to a non-network hospital | unobservable; measure scope is network hospitals |
| Planned tables use principal procedure of first encounter of readmission episode | measure text "the readmission's principal procedure"; for transfer-chain readmissions, first encounter is the admission — stated in the measure's footnote on transfers ("a transfer chain is one admission") |
| Observation/ED encounters | excluded (acute inpatient only), measure scope |
| DST ambiguity | never generated |
| Quarters with incomplete follow-up | death index through 2026-07-31 covers 2026Q2 + 30 days; instruction limits to quarters ≤ 2026Q2 |
| Episode index when index discharge and readmission episode overlap | impossible after episode construction |
| Rate denominator by facility | discharging (final) facility — measure states outcomes attributed to discharging hospital |

## 24. Expected trajectory length

55–80 actions, 20–35 minutes. The investigation must move from aggregate (facility rates) to raw H6 strings to code
vocabularies to episode chains to outcome definitions; three discoveries depend on inspecting rows after a first
repair "almost" works.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | G23 |
|---|---|
| cutoff inherited from code | the faulty code parses every feed as UTC and has no episode notion |
| summary implemented | planned tables, deaths and score selection absent |
| natural group/merge design correct | the natural gap-based merge is wrong in both same- and cross-facility forms |
| attractor optional | notebook, case-mix summary, disposition map and review notes are on the path |
| traps on unchosen paths | drop-H6, 24 h merge, code-02 linking and UTC dates are the defaults |
| one-customer check enough | one H6 → H1 pair looks fixed by variant B; night departures, back-transfers and 70-codes need population audits |

## 26. Comparison with Task 02

Task 02: features had to be rebuilt per example × cutoff; agents collapsed state to the entity. G23: labels must be
built per episode, whose membership depends on feed-specific semantics; agents are likely to collapse to encounters or
to pairwise links. G23 has more independent mechanisms (six) and a more explicit definition document, so recognition
will be easier than Task 02 but operationalisation is broader. The AUC is again an aggregate that several wrong
repairs make "look normal" (0.709–0.741).

## 27. Benchmark risks

- **Leakage/over-documentation**: a readmission measure must define transfers and planned readmissions; this is
  unavoidable domain realism and makes recognition easy. Headroom rests on the H6 feed semantics and episode
  propagation.
- **Realism**: a rural hospital defaulting to "Other Facility" and local-time feeds are plausible integration faults;
  night transfers at 41% may be high — calibrate to ~25–40%.
- **Clinical correctness claims**: all measure content is fictional; build docs must avoid naming real measures or
  claiming equivalence (*to verify* any wording that echoes public specs).
- **Gradability**: exact episode partition is safe given generator constraints; the either-side rule and overlap
  handling must be mirrored exactly in the reference.
- **Implementation cost**: medium-high (clinical code tables, feed rendering, model scores with realistic AUC).
- **Headroom**: medium-high if agents start from the drop-H6 or 24 h merge; lower for agents with strong healthcare
  data priors that read the onboarding note first.
- **Sensitivity**: synthetic PHI-like data must be clearly synthetic (no real names, MRN formats or facility names).
